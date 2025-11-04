#!/usr/bin/env python3
"""
DeskMate Monitoring Service

This service monitors the health and performance of all DeskMate components
and provides alerting for failures or performance issues.
"""

import asyncio
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
import json

import httpx
import psutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import schedule
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app for monitoring API
app = FastAPI(title="DeskMate Monitoring Service", version="1.0.0")


class ServiceStatus(BaseModel):
    name: str
    status: str
    response_time_ms: Optional[float] = None
    last_check: datetime
    last_error: Optional[str] = None
    uptime_percentage: float
    consecutive_failures: int = 0


class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int


class AlertRule(BaseModel):
    name: str
    condition: str
    threshold: float
    enabled: bool = True
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None


class MonitoringService:
    def __init__(self):
        self.services: Dict[str, ServiceStatus] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.alert_rules: List[AlertRule] = []
        self.is_running = False

        # Configuration
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
        self.services_to_monitor = {
            'backend': 'http://backend:8000/health',
            'frontend': 'http://frontend/',
            'postgres': 'http://backend:8000/health',  # Through backend health check
            'qdrant': 'http://backend:8000/health',    # Through backend health check
        }

        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.alert_email = os.getenv('ALERT_EMAIL')

        # Initialize alert rules
        self._initialize_alert_rules()

        logger.info("Monitoring service initialized")

    def _initialize_alert_rules(self):
        """Initialize default alert rules."""
        default_rules = [
            AlertRule(name="High CPU Usage", condition="cpu_percent", threshold=85.0),
            AlertRule(name="High Memory Usage", condition="memory_percent", threshold=90.0),
            AlertRule(name="Low Disk Space", condition="disk_usage_percent", threshold=90.0),
            AlertRule(name="Service Down", condition="service_down", threshold=1.0),
            AlertRule(name="High Response Time", condition="response_time_ms", threshold=5000.0),
        ]
        self.alert_rules = default_rules
        logger.info(f"Initialized {len(self.alert_rules)} alert rules")

    async def check_service_health(self, service_name: str, url: str) -> ServiceStatus:
        """Check the health of a specific service."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    status = "healthy"
                    error = None
                else:
                    status = "unhealthy"
                    error = f"HTTP {response.status_code}"

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = "unhealthy"
            error = str(e)

        # Update or create service status
        current_time = datetime.now()

        if service_name in self.services:
            previous = self.services[service_name]
            consecutive_failures = previous.consecutive_failures + 1 if status == "unhealthy" else 0

            # Calculate uptime percentage (simple rolling average)
            if status == "healthy":
                uptime_percentage = min(100.0, previous.uptime_percentage + 0.1)
            else:
                uptime_percentage = max(0.0, previous.uptime_percentage - 1.0)
        else:
            consecutive_failures = 1 if status == "unhealthy" else 0
            uptime_percentage = 100.0 if status == "healthy" else 0.0

        service_status = ServiceStatus(
            name=service_name,
            status=status,
            response_time_ms=round(response_time, 2),
            last_check=current_time,
            last_error=error,
            uptime_percentage=round(uptime_percentage, 2),
            consecutive_failures=consecutive_failures
        )

        self.services[service_name] = service_status
        return service_status

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = memory.available / 1024 / 1024

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / 1024 / 1024 / 1024

        # Network usage
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv

        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=round(cpu_percent, 1),
            memory_percent=round(memory_percent, 1),
            memory_available_mb=round(memory_available_mb, 1),
            disk_usage_percent=round(disk_usage_percent, 1),
            disk_free_gb=round(disk_free_gb, 1),
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv
        )

        # Keep only last 1440 entries (24 hours at 1-minute intervals)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1440:
            self.metrics_history.pop(0)

        return metrics

    async def send_alert(self, subject: str, message: str):
        """Send an email alert."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.alert_email]):
            logger.warning("Email configuration incomplete, cannot send alert")
            return

        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email
            msg['Subject'] = f"DeskMate Alert: {subject}"

            body = f"""
DeskMate Monitoring Alert

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
DeskMate Monitoring Service
            """

            msg.attach(MimeText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def check_alert_rules(self, metrics: SystemMetrics):
        """Check if any alert rules are triggered."""
        current_time = datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Check cooldown period
            if rule.last_triggered:
                time_since_last = current_time - rule.last_triggered
                if time_since_last < timedelta(minutes=rule.cooldown_minutes):
                    continue

            triggered = False
            alert_message = ""

            # Check different condition types
            if rule.condition == "cpu_percent" and metrics.cpu_percent > rule.threshold:
                triggered = True
                alert_message = f"High CPU usage detected: {metrics.cpu_percent}% (threshold: {rule.threshold}%)"

            elif rule.condition == "memory_percent" and metrics.memory_percent > rule.threshold:
                triggered = True
                alert_message = f"High memory usage detected: {metrics.memory_percent}% (threshold: {rule.threshold}%)"

            elif rule.condition == "disk_usage_percent" and metrics.disk_usage_percent > rule.threshold:
                triggered = True
                alert_message = f"Low disk space detected: {metrics.disk_usage_percent}% used (threshold: {rule.threshold}%)"

            elif rule.condition == "service_down":
                unhealthy_services = [s for s in self.services.values() if s.status == "unhealthy"]
                if len(unhealthy_services) >= rule.threshold:
                    triggered = True
                    service_names = ", ".join([s.name for s in unhealthy_services])
                    alert_message = f"Services down: {service_names}"

            elif rule.condition == "response_time_ms":
                slow_services = [s for s in self.services.values()
                               if s.response_time_ms and s.response_time_ms > rule.threshold]
                if slow_services:
                    triggered = True
                    service_details = ", ".join([f"{s.name}: {s.response_time_ms}ms" for s in slow_services])
                    alert_message = f"Slow response times detected: {service_details} (threshold: {rule.threshold}ms)"

            if triggered:
                rule.last_triggered = current_time
                await self.send_alert(rule.name, alert_message)
                logger.warning(f"Alert triggered: {rule.name} - {alert_message}")

    async def monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Starting monitoring loop")

        while self.is_running:
            try:
                # Check all services
                tasks = []
                for service_name, url in self.services_to_monitor.items():
                    task = self.check_service_health(service_name, url)
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)

                # Collect system metrics
                metrics = self.collect_system_metrics()

                # Check alert rules
                await self.check_alert_rules(metrics)

                # Log status summary
                healthy_count = sum(1 for s in self.services.values() if s.status == "healthy")
                total_count = len(self.services)
                logger.info(f"Health check completed: {healthy_count}/{total_count} services healthy")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait for next check
            await asyncio.sleep(self.check_interval)

    async def start_monitoring(self):
        """Start the monitoring service."""
        self.is_running = True
        await self.monitoring_loop()

    def stop_monitoring(self):
        """Stop the monitoring service."""
        self.is_running = False


# Global monitoring service instance
monitoring_service = MonitoringService()


@app.get("/health")
async def health_check():
    """Health check for the monitoring service itself."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "uptime": time.time(),
        "services_monitored": len(monitoring_service.services)
    }


@app.get("/status")
async def get_status():
    """Get current status of all monitored services."""
    return {
        "timestamp": datetime.now(),
        "services": monitoring_service.services,
        "metrics": monitoring_service.metrics_history[-1] if monitoring_service.metrics_history else None
    }


@app.get("/metrics")
async def get_metrics(hours: int = 1):
    """Get system metrics for the specified number of hours."""
    if hours > 24:
        hours = 24

    entries_needed = hours * 60  # 1 entry per minute
    recent_metrics = monitoring_service.metrics_history[-entries_needed:] if monitoring_service.metrics_history else []

    return {
        "timestamp": datetime.now(),
        "period_hours": hours,
        "data_points": len(recent_metrics),
        "metrics": recent_metrics
    }


@app.get("/alerts")
async def get_alerts():
    """Get current alert rules configuration."""
    return {
        "timestamp": datetime.now(),
        "alert_rules": monitoring_service.alert_rules
    }


@app.post("/alerts/{rule_name}/toggle")
async def toggle_alert_rule(rule_name: str):
    """Toggle an alert rule on/off."""
    for rule in monitoring_service.alert_rules:
        if rule.name == rule_name:
            rule.enabled = not rule.enabled
            return {"message": f"Alert rule '{rule_name}' {'enabled' if rule.enabled else 'disabled'}"}

    raise HTTPException(status_code=404, detail="Alert rule not found")


async def main():
    """Main function to start the monitoring service."""
    logger.info("Starting DeskMate Monitoring Service")

    # Start monitoring in background
    monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())

    # Start FastAPI server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring service")
        monitoring_service.stop_monitoring()
        monitoring_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())