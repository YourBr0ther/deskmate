#!/usr/bin/env python3
"""
Simple alerting system for DeskMate

This is a lightweight alerting system that can work independently
of Prometheus/Grafana for basic monitoring and alerting.
"""

import asyncio
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional
import argparse

import httpx
import psutil


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Alert:
    def __init__(self, name: str, condition: str, threshold: float,
                 severity: str = "warning", cooldown_minutes: int = 15):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.severity = severity
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered: Optional[datetime] = None
        self.consecutive_triggers = 0

    def should_trigger(self) -> bool:
        """Check if alert should trigger based on cooldown."""
        if self.last_triggered is None:
            return True

        time_since_last = datetime.now() - self.last_triggered
        return time_since_last >= timedelta(minutes=self.cooldown_minutes)

    def trigger(self):
        """Mark alert as triggered."""
        self.last_triggered = datetime.now()
        self.consecutive_triggers += 1

    def reset(self):
        """Reset alert state."""
        self.consecutive_triggers = 0


class SimpleAlerting:
    def __init__(self):
        # Configuration from environment
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.alert_email = os.getenv('ALERT_EMAIL')

        # Services to monitor
        self.services = {
            'backend': 'http://backend:8000/health',
            'frontend': 'http://frontend:80/',
            'postgres': 'http://backend:8000/health',
            'qdrant': 'http://backend:8000/health',
        }

        # Alert definitions
        self.alerts = [
            Alert("High CPU Usage", "cpu_percent", 85.0, "warning", 15),
            Alert("Critical CPU Usage", "cpu_percent", 95.0, "critical", 5),
            Alert("High Memory Usage", "memory_percent", 90.0, "warning", 15),
            Alert("Critical Memory Usage", "memory_percent", 95.0, "critical", 5),
            Alert("Low Disk Space", "disk_usage_percent", 85.0, "warning", 30),
            Alert("Critical Disk Space", "disk_usage_percent", 95.0, "critical", 10),
            Alert("Service Down", "service_down", 1, "critical", 5),
            Alert("High Response Time", "response_time", 5000, "warning", 10),
        ]

        # State tracking
        self.service_states = {}
        self.system_metrics = {}

    async def check_service_health(self, service_name: str, url: str) -> Dict:
        """Check health of a service."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000

                return {
                    'name': service_name,
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'error': None
                }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'name': service_name,
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'status_code': None,
                'error': str(e)
            }

    def collect_system_metrics(self) -> Dict:
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_usage_percent': disk_usage_percent,
                'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024,
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    async def send_alert(self, alert: Alert, message: str, metrics: Dict = None):
        """Send an alert via email."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.alert_email]):
            logger.warning("Email configuration incomplete, logging alert instead")
            logger.warning(f"ALERT: {alert.name} - {message}")
            return

        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email

            # Subject with severity indicator
            severity_emoji = "🚨" if alert.severity == "critical" else "⚠️"
            msg['Subject'] = f"{severity_emoji} DeskMate Alert: {alert.name}"

            # Email body
            body = f"""
DeskMate Monitoring Alert

Alert: {alert.name}
Severity: {alert.severity.upper()}
Condition: {alert.condition}
Threshold: {alert.threshold}

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Consecutive Triggers: {alert.consecutive_triggers}
"""

            if metrics:
                body += f"""
Current System Metrics:
- CPU Usage: {metrics.get('cpu_percent', 'N/A')}%
- Memory Usage: {metrics.get('memory_percent', 'N/A')}%
- Disk Usage: {metrics.get('disk_usage_percent', 'N/A')}%
- Memory Available: {metrics.get('memory_available_gb', 'N/A'):.1f} GB
- Disk Free: {metrics.get('disk_free_gb', 'N/A'):.1f} GB
"""

            body += """
---
DeskMate Simple Alerting System
            """

            msg.attach(MimeText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert sent: {alert.name} ({alert.severity})")

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def check_alerts(self, service_states: Dict, metrics: Dict):
        """Check all alert conditions."""
        for alert in self.alerts:
            if not alert.should_trigger():
                continue

            triggered = False
            message = ""

            # Check system metric alerts
            if alert.condition == "cpu_percent":
                current_value = metrics.get('cpu_percent', 0)
                if current_value > alert.threshold:
                    triggered = True
                    message = f"CPU usage is {current_value:.1f}% (threshold: {alert.threshold}%)"

            elif alert.condition == "memory_percent":
                current_value = metrics.get('memory_percent', 0)
                if current_value > alert.threshold:
                    triggered = True
                    message = f"Memory usage is {current_value:.1f}% (threshold: {alert.threshold}%)"

            elif alert.condition == "disk_usage_percent":
                current_value = metrics.get('disk_usage_percent', 0)
                if current_value > alert.threshold:
                    triggered = True
                    message = f"Disk usage is {current_value:.1f}% (threshold: {alert.threshold}%)"

            # Check service alerts
            elif alert.condition == "service_down":
                unhealthy_services = [name for name, state in service_states.items()
                                    if state.get('status') == 'unhealthy']
                if len(unhealthy_services) >= alert.threshold:
                    triggered = True
                    message = f"Services down: {', '.join(unhealthy_services)}"

            elif alert.condition == "response_time":
                slow_services = [name for name, state in service_states.items()
                               if state.get('response_time_ms', 0) > alert.threshold]
                if slow_services:
                    triggered = True
                    service_times = [f"{name}: {service_states[name]['response_time_ms']:.0f}ms"
                                   for name in slow_services]
                    message = f"Slow response times: {', '.join(service_times)} (threshold: {alert.threshold}ms)"

            if triggered:
                alert.trigger()
                await self.send_alert(alert, message, metrics)
                logger.warning(f"Alert triggered: {alert.name} - {message}")
            else:
                alert.reset()

    async def run_check_cycle(self):
        """Run one complete check cycle."""
        logger.info("Starting check cycle")

        # Check all services
        service_tasks = []
        for service_name, url in self.services.items():
            task = self.check_service_health(service_name, url)
            service_tasks.append(task)

        service_results = await asyncio.gather(*service_tasks, return_exceptions=True)

        # Update service states
        for result in service_results:
            if isinstance(result, dict):
                self.service_states[result['name']] = result

        # Collect system metrics
        self.system_metrics = self.collect_system_metrics()

        # Check alerts
        await self.check_alerts(self.service_states, self.system_metrics)

        # Log summary
        healthy_count = sum(1 for state in self.service_states.values()
                          if state.get('status') == 'healthy')
        total_count = len(self.service_states)
        logger.info(f"Check cycle completed: {healthy_count}/{total_count} services healthy")

    async def run_monitoring_loop(self):
        """Run the main monitoring loop."""
        logger.info(f"Starting monitoring loop (check interval: {self.check_interval}s)")

        while True:
            try:
                await self.run_check_cycle()
            except Exception as e:
                logger.error(f"Error in check cycle: {e}")

            await asyncio.sleep(self.check_interval)

    def get_status(self) -> Dict:
        """Get current status for API or CLI."""
        return {
            'timestamp': datetime.now().isoformat(),
            'services': self.service_states,
            'system_metrics': self.system_metrics,
            'alerts': [
                {
                    'name': alert.name,
                    'condition': alert.condition,
                    'threshold': alert.threshold,
                    'severity': alert.severity,
                    'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None,
                    'consecutive_triggers': alert.consecutive_triggers
                }
                for alert in self.alerts
            ]
        }


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='DeskMate Simple Alerting System')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--status', action='store_true', help='Show current status')
    args = parser.parse_args()

    alerting = SimpleAlerting()

    if args.status:
        # Just run one check and show status
        await alerting.run_check_cycle()
        status = alerting.get_status()
        print(json.dumps(status, indent=2, default=str))
        return

    if args.once:
        # Run one check cycle and exit
        await alerting.run_check_cycle()
        logger.info("Single check completed")
        return

    # Run continuous monitoring
    try:
        await alerting.run_monitoring_loop()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")


if __name__ == "__main__":
    asyncio.run(main())