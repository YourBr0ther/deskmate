from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

from app.db.database import check_postgres_health
from app.db.qdrant import qdrant_manager

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API and connected services are healthy"
)
async def health_check() -> HealthResponse:
    # Check PostgreSQL
    postgres_healthy = await check_postgres_health()
    
    # Check Qdrant
    qdrant_healthy = await qdrant_manager.health_check()
    
    # Overall health
    all_healthy = postgres_healthy and qdrant_healthy
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(),
        version="0.1.0",
        services={
            "api": "healthy",
            "postgres": "healthy" if postgres_healthy else "unhealthy",
            "qdrant": "healthy" if qdrant_healthy else "unhealthy"
        }
    )