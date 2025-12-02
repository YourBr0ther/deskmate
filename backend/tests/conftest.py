"""
Pytest configuration and fixtures for DeskMate backend tests.

This module provides:
- Async HTTP client for API testing
- Mock fixtures for LLM, database, and vector DB
- Common test utilities
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Generator, AsyncGenerator

# Set test environment
os.environ["TESTING"] = "true"
os.environ["NANO_GPT_API_KEY"] = "test-api-key-12345"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

from app.main import app

# Import fixtures from fixtures package
from tests.fixtures.mock_llm import *
from tests.fixtures.mock_database import *
from tests.fixtures.mock_qdrant import *


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API endpoints.

    Usage:
        async def test_endpoint(client):
            response = await client.get("/health")
            assert response.status_code == 200
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """
    Synchronous test client for simpler tests.

    Usage:
        def test_endpoint(sync_client):
            response = sync_client.get("/health")
            assert response.status_code == 200
    """
    with TestClient(app) as tc:
        yield tc


# ============================================================================
# Application State Fixtures
# ============================================================================

@pytest.fixture
def mock_app_state():
    """
    Mock application state for testing.

    Returns a dict with common state values.
    """
    return {
        "assistant_position": {"x": 5, "y": 5},
        "current_room": "living_room",
        "is_idle": False,
        "current_persona": "Alice",
        "current_model": "llama3:latest"
    }


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock(return_value={"type": "chat", "content": "Hello"})
    ws.close = AsyncMock()
    ws.accept = AsyncMock()
    return ws


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def clean_test_environment():
    """Provide a clean test environment with controlled variables."""
    test_env = {
        "TESTING": "true",
        "NANO_GPT_API_KEY": "test-api-key-12345",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "QDRANT_URL": "http://localhost:6333",
    }
    with patch.dict(os.environ, test_env, clear=False):
        yield test_env


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "What's the weather like?"},
    ]


@pytest.fixture
def sample_brain_council_response():
    """Sample Brain Council response for testing."""
    return {
        "council_response": {
            "personality": "Character maintains cheerful demeanor",
            "memory": "User previously asked about the weather",
            "spatial": "Assistant is at position (5, 5), near the desk",
            "action": "Suggest moving to the window",
            "validation": "Action is valid and possible"
        },
        "final_response": "I'd be happy to help with that!",
        "suggested_actions": [
            {"type": "move", "target": {"x": 10, "y": 8}},
            {"type": "expression", "value": "happy"}
        ]
    }


@pytest.fixture
def sample_room_state():
    """Sample room state for testing."""
    return {
        "id": "living_room",
        "name": "Living Room",
        "width": 64,
        "height": 16,
        "objects": [
            {"id": 1, "name": "desk", "x": 10, "y": 8, "width": 2, "height": 1},
            {"id": 2, "name": "chair", "x": 12, "y": 8, "width": 1, "height": 1},
            {"id": 3, "name": "lamp", "x": 10, "y": 7, "width": 1, "height": 1},
        ],
        "assistant": {"x": 5, "y": 5, "expression": "default"}
    }


# ============================================================================
# Marker Registrations (for pytest.ini)
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may require database/services)")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "llm: Tests requiring LLM mocking")
    config.addinivalue_line("markers", "database: Tests requiring database fixtures")
    config.addinivalue_line("markers", "qdrant: Tests requiring Qdrant vector DB")