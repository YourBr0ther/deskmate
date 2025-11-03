import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app


@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac