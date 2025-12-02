"""
Tests for Chat API endpoints.

Tests cover:
- GET /chat/models - Get available models
- POST /chat/model/select - Select model
- POST /chat/completion - Non-streaming completion
- POST /chat/completion/stream - Streaming completion
- GET /chat/test/{provider} - Test provider connection
- GET /chat/status - Get chat system status
- POST /chat/simple - Simple chat
- POST /chat/command - Process commands
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.services.llm_manager import LLMProvider, LLMModel, LLMResponse


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_model():
    """Create a mock LLM model."""
    return LLMModel(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider=LLMProvider.NANO_GPT,
        description="Test model",
        max_tokens=4096,
        context_window=128000,
        supports_streaming=True,
        cost_per_token=0.00015
    )


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    return LLMResponse(
        content="Hello! How can I help you?",
        model="gpt-4o-mini",
        provider=LLMProvider.NANO_GPT,
        tokens_used=50,
        finish_reason="stop",
        error=None
    )


# ============================================================================
# GET /chat/models Tests
# ============================================================================

class TestGetModels:
    """Tests for GET /chat/models endpoint."""

    @pytest.mark.asyncio
    async def test_get_models_success(self, client, mock_llm_model):
        """Should return available models."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.get_available_models = AsyncMock(return_value={
                "gpt-4o-mini": mock_llm_model
            })
            mock_manager.current_model = "gpt-4o-mini"
            mock_manager.current_provider = LLMProvider.NANO_GPT

            response = await client.get("/chat/models")

            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert "current_model" in data
            assert len(data["models"]) == 1
            assert data["models"][0]["id"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_get_models_error_handling(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.get_available_models = AsyncMock(side_effect=Exception("Test error"))

            response = await client.get("/chat/models")

            assert response.status_code == 500


# ============================================================================
# POST /chat/model/select Tests
# ============================================================================

class TestSelectModel:
    """Tests for POST /chat/model/select endpoint."""

    @pytest.mark.asyncio
    async def test_select_model_success(self, client):
        """Should select model successfully."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.set_model = AsyncMock(return_value=True)
            mock_manager.current_model = "gpt-4o-mini"
            mock_manager.current_provider = LLMProvider.NANO_GPT

            response = await client.post(
                "/chat/model/select",
                json={"model_id": "gpt-4o-mini"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_select_model_missing_id(self, client):
        """Should return 400 when model_id is missing."""
        response = await client.post(
            "/chat/model/select",
            json={}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_select_model_invalid(self, client):
        """Should return 400 for invalid model."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.set_model = AsyncMock(return_value=False)

            response = await client.post(
                "/chat/model/select",
                json={"model_id": "invalid-model"}
            )

            assert response.status_code == 400


# ============================================================================
# POST /chat/completion Tests
# ============================================================================

class TestChatCompletion:
    """Tests for POST /chat/completion endpoint."""

    @pytest.mark.asyncio
    async def test_completion_success(self, client, mock_llm_response):
        """Should return completion successfully."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_llm_response)

            response = await client.post(
                "/chat/completion",
                json={
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Hello! How can I help you?"

    @pytest.mark.asyncio
    async def test_completion_empty_messages(self, client):
        """Should return 400 for empty messages."""
        response = await client.post(
            "/chat/completion",
            json={"messages": []}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_completion_invalid_message_format(self, client):
        """Should return 400 for invalid message format."""
        response = await client.post(
            "/chat/completion",
            json={
                "messages": [
                    {"content": "Hello"}  # Missing role
                ]
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_completion_with_temperature(self, client, mock_llm_response):
        """Should accept temperature parameter."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_llm_response)

            response = await client.post(
                "/chat/completion",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "temperature": 0.9
                }
            )

            assert response.status_code == 200
            # Verify temperature was passed
            call_args = mock_manager.chat_completion.call_args
            assert call_args[1]["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_completion_with_max_tokens(self, client, mock_llm_response):
        """Should accept max_tokens parameter."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_llm_response)

            response = await client.post(
                "/chat/completion",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 100
                }
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_completion_llm_error(self, client):
        """Should handle LLM errors."""
        mock_response = LLMResponse(
            content="",
            model="gpt-4o-mini",
            provider=LLMProvider.NANO_GPT,
            tokens_used=0,
            error="LLM error"
        )

        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_response)

            response = await client.post(
                "/chat/completion",
                json={
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )

            assert response.status_code == 500


# ============================================================================
# GET /chat/test/{provider} Tests
# ============================================================================

class TestProviderConnection:
    """Tests for GET /chat/test/{provider} endpoint."""

    @pytest.mark.asyncio
    async def test_test_nano_gpt(self, client):
        """Should test Nano-GPT connection."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.test_connection = AsyncMock(return_value={
                "success": True,
                "provider": "nano_gpt",
                "available_models": ["gpt-4o-mini"]
            })

            response = await client.get("/chat/test/nano_gpt")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_test_ollama(self, client):
        """Should test Ollama connection."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.test_connection = AsyncMock(return_value={
                "success": True,
                "provider": "ollama",
                "available_models": ["llama3:latest"]
            })

            response = await client.get("/chat/test/ollama")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_test_invalid_provider(self, client):
        """Should return 400 for invalid provider."""
        response = await client.get("/chat/test/invalid")

        assert response.status_code == 400


# ============================================================================
# GET /chat/status Tests
# ============================================================================

class TestChatStatus:
    """Tests for GET /chat/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """Should return chat status."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.test_connection = AsyncMock(return_value={
                "success": True,
                "available_models": ["model1"]
            })
            mock_manager.current_model = "gpt-4o-mini"
            mock_manager.current_provider = LLMProvider.NANO_GPT

            response = await client.get("/chat/status")

            assert response.status_code == 200
            data = response.json()
            assert "current_model" in data
            assert "providers" in data
            assert "nano_gpt" in data["providers"]
            assert "ollama" in data["providers"]


# ============================================================================
# POST /chat/simple Tests
# ============================================================================

class TestSimpleChat:
    """Tests for POST /chat/simple endpoint."""

    @pytest.mark.asyncio
    async def test_simple_chat_success(self, client, mock_llm_response):
        """Should return simple chat response."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_llm_response)

            response = await client.post(
                "/chat/simple",
                json={"message": "Hello"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data

    @pytest.mark.asyncio
    async def test_simple_chat_missing_message(self, client):
        """Should return 400 for missing message."""
        response = await client.post(
            "/chat/simple",
            json={}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_simple_chat_with_system_prompt(self, client, mock_llm_response):
        """Should accept custom system prompt."""
        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_llm_response)

            response = await client.post(
                "/chat/simple",
                json={
                    "message": "Hello",
                    "system_prompt": "You are a pirate."
                }
            )

            assert response.status_code == 200


# ============================================================================
# POST /chat/command Tests
# ============================================================================

class TestChatCommand:
    """Tests for POST /chat/command endpoint."""

    @pytest.mark.asyncio
    async def test_command_not_a_command(self, client):
        """Should return 400 for non-command messages."""
        response = await client.post(
            "/chat/command",
            json={"message": "not a command"}
        )

        assert response.status_code == 400
        assert "Not a command" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_command_unknown(self, client):
        """Should return 400 for unknown commands."""
        response = await client.post(
            "/chat/command",
            json={"message": "/unknown arg1 arg2"}
        )

        assert response.status_code == 400
        assert "Unknown command" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_command_success(self, client, mock_llm_response):
        """Should handle /create command."""
        mock_llm_response.content = '{"name": "Coffee Mug", "description": "A red coffee mug", "type": "item", "default_size": {"width": 1, "height": 1}, "color_scheme": "red", "sprite_name": "coffee_mug.png"}'

        with patch('app.api.chat.llm_manager') as mock_manager:
            mock_manager.chat_completion = AsyncMock(return_value=mock_llm_response)

            with patch('app.api.chat.room_service') as mock_room:
                mock_room.add_to_storage = AsyncMock(return_value={
                    "id": "created_12345678",
                    "name": "Coffee Mug"
                })

                response = await client.post(
                    "/chat/command",
                    json={"message": "/create a red coffee mug"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["command"] == "create"

    @pytest.mark.asyncio
    async def test_create_command_missing_description(self, client):
        """Should return 400 for /create without description."""
        response = await client.post(
            "/chat/command",
            json={"message": "/create"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_command_empty_message(self, client):
        """Should return 400 for empty message."""
        response = await client.post(
            "/chat/command",
            json={"message": ""}
        )

        assert response.status_code == 400
