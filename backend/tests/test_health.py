import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_health_check_returns_200(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_response_structure(client: AsyncClient):
    response = await client.get("/health")
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data
    
    # Check field types
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "0.1.0"
    
    # Check services
    assert "api" in data["services"]
    assert "postgres" in data["services"]
    assert "qdrant" in data["services"]
    
    # Check timestamp is valid
    datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_api_service_always_healthy(client: AsyncClient):
    response = await client.get("/health")
    data = response.json()
    
    # API service should always be healthy if we can reach it
    assert data["services"]["api"] == "healthy"