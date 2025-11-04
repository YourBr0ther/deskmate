from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional
import psutil
import os
import asyncio
import time

from app.db.database import check_postgres_health
from app.db.qdrant import qdrant_manager

router = APIRouter()


class ServiceHealth(BaseModel):
    status: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None


class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    uptime_seconds: float


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, ServiceHealth]
    system: SystemMetrics


class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, ServiceHealth]
    system: SystemMetrics
    dependencies: Dict[str, Any]
    performance: Dict[str, float]


async def check_service_health(service_name: str, check_func) -> ServiceHealth:
    """Check health of a service with timing and error handling."""
    start_time = time.time()
    try:
        healthy = await check_func()
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            status="healthy" if healthy else "unhealthy",
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            last_error=str(e)
        )


def get_system_metrics() -> SystemMetrics:
    """Get current system resource metrics."""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)

    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_available_mb = memory.available / 1024 / 1024

    # Disk usage for the root partition
    disk = psutil.disk_usage('/')
    disk_usage_percent = (disk.used / disk.total) * 100
    disk_free_gb = disk.free / 1024 / 1024 / 1024

    # System uptime
    uptime_seconds = time.time() - psutil.boot_time()

    return SystemMetrics(
        cpu_percent=round(cpu_percent, 1),
        memory_percent=round(memory_percent, 1),
        memory_available_mb=round(memory_available_mb, 1),
        disk_usage_percent=round(disk_usage_percent, 1),
        disk_free_gb=round(disk_free_gb, 1),
        uptime_seconds=round(uptime_seconds, 1)
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check",
    description="Quick health check of API and essential services"
)
async def health_check() -> HealthResponse:
    """Basic health check endpoint for load balancers and monitoring."""
    # Check services in parallel
    postgres_task = check_service_health("postgres", check_postgres_health)
    qdrant_task = check_service_health("qdrant", qdrant_manager.health_check)

    postgres_health, qdrant_health = await asyncio.gather(postgres_task, qdrant_task)

    # API health (always healthy if we reach this point)
    api_health = ServiceHealth(status="healthy", response_time_ms=0.0)

    services = {
        "api": api_health,
        "postgres": postgres_health,
        "qdrant": qdrant_health
    }

    # Overall health determination
    all_healthy = all(service.status == "healthy" for service in services.values())
    overall_status = "healthy" if all_healthy else "degraded"

    # Get system metrics
    system_metrics = get_system_metrics()

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="0.1.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        services=services,
        system=system_metrics
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Health Check",
    description="Comprehensive health check with detailed metrics and diagnostics"
)
async def detailed_health_check() -> DetailedHealthResponse:
    """Detailed health check with comprehensive system information."""

    # Get basic health data
    basic_health = await health_check()

    # Additional dependency checks
    dependencies = {
        "python_version": f"{psutil.PROCFS_PATH}",
        "pid": os.getpid(),
        "working_directory": os.getcwd(),
        "environment_variables": {
            "DATABASE_URL": "configured" if os.getenv("DATABASE_URL") else "missing",
            "QDRANT_URL": "configured" if os.getenv("QDRANT_URL") else "missing",
            "NANO_GPT_API_KEY": "configured" if os.getenv("NANO_GPT_API_KEY") else "missing",
        }
    }

    # Performance metrics
    performance = {
        "startup_time": time.time(),  # Would be better to track actual startup time
        "total_requests": 0,  # Would need request counter middleware
        "average_response_time": 0.0,  # Would need response time tracking
    }

    return DetailedHealthResponse(
        status=basic_health.status,
        timestamp=basic_health.timestamp,
        version=basic_health.version,
        environment=basic_health.environment,
        services=basic_health.services,
        system=basic_health.system,
        dependencies=dependencies,
        performance=performance
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Simple liveness check for Kubernetes/Docker health probes"
)
async def liveness_check():
    """Minimal liveness check for container orchestrators."""
    return {"status": "alive", "timestamp": datetime.now()}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Readiness check ensuring all dependencies are available"
)
async def readiness_check():
    """Readiness check for container orchestrators."""
    # Check critical dependencies
    postgres_healthy = await check_postgres_health()
    qdrant_healthy = await qdrant_manager.health_check()

    if not (postgres_healthy and qdrant_healthy):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies not ready"
        )

    return {
        "status": "ready",
        "timestamp": datetime.now(),
        "services": {
            "postgres": "ready",
            "qdrant": "ready"
        }
    }