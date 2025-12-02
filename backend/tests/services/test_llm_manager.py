"""
Tests for LLM Manager service.

Tests cover:
- Model selection and switching
- Nano-GPT completions (streaming and non-streaming)
- Ollama completions (streaming and non-streaming)
- Connection testing
- Error handling and retries
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from typing import List

from app.services.llm_manager import (
    LLMManager,
    LLMProvider,
    LLMModel,
    ChatMessage,
    LLMResponse,
)
from app.exceptions import ServiceError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def llm_manager():
    """Create a fresh LLM manager instance."""
    with patch.dict('os.environ', {
        'NANO_GPT_API_KEY': 'test-api-key',
        'OLLAMA_BASE_URL': 'http://localhost:11434'
    }):
        manager = LLMManager()
        yield manager


@pytest.fixture
def sample_messages():
    """Sample chat messages for testing."""
    return [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="Hello, how are you?"),
    ]


# ============================================================================
# Initialization Tests
# ============================================================================

class TestLLMManagerInitialization:
    """Tests for LLM manager initialization."""

    def test_default_provider_is_ollama(self, llm_manager):
        """Default provider should be Ollama."""
        assert llm_manager.current_provider == LLMProvider.OLLAMA

    def test_default_model_is_llama3(self, llm_manager):
        """Default model should be llama3:latest."""
        assert llm_manager.current_model == "llama3:latest"

    def test_nano_gpt_models_available(self, llm_manager):
        """Nano-GPT models should be in available models."""
        assert "gpt-4o-mini" in llm_manager.available_models
        assert "gpt-4o" in llm_manager.available_models
        assert "claude-3.5-sonnet" in llm_manager.available_models

    def test_ollama_models_available(self, llm_manager):
        """Ollama models should be in available models."""
        assert "llama3:latest" in llm_manager.available_models
        assert "llava:latest" in llm_manager.available_models

    def test_api_key_loaded(self, llm_manager):
        """API key should be loaded from environment."""
        assert llm_manager.nano_gpt_api_key == "test-api-key"

    def test_ollama_url_loaded(self, llm_manager):
        """Ollama URL should be loaded from environment."""
        assert llm_manager.ollama_base_url == "http://localhost:11434"


# ============================================================================
# Model Selection Tests
# ============================================================================

class TestModelSelection:
    """Tests for model selection and switching."""

    @pytest.mark.asyncio
    async def test_set_valid_nano_gpt_model(self, llm_manager):
        """Setting a valid Nano-GPT model should succeed."""
        result = await llm_manager.set_model("gpt-4o-mini")

        assert result is True
        assert llm_manager.current_model == "gpt-4o-mini"
        assert llm_manager.current_provider == LLMProvider.NANO_GPT

    @pytest.mark.asyncio
    async def test_set_valid_ollama_model(self, llm_manager):
        """Setting a valid Ollama model should succeed."""
        result = await llm_manager.set_model("llava:latest")

        assert result is True
        assert llm_manager.current_model == "llava:latest"
        assert llm_manager.current_provider == LLMProvider.OLLAMA

    @pytest.mark.asyncio
    async def test_set_invalid_model_fails(self, llm_manager):
        """Setting an invalid model should fail."""
        result = await llm_manager.set_model("nonexistent-model")

        assert result is False
        # Model should remain unchanged
        assert llm_manager.current_model == "llama3:latest"

    @pytest.mark.asyncio
    async def test_get_available_models(self, llm_manager):
        """Should return all available models."""
        models = await llm_manager.get_available_models()

        assert len(models) >= 6
        assert all(isinstance(m, LLMModel) for m in models.values())


# ============================================================================
# Nano-GPT Completion Tests
# ============================================================================

class TestNanoGPTCompletion:
    """Tests for Nano-GPT chat completions."""

    @pytest.mark.asyncio
    async def test_successful_completion(self, llm_manager, sample_messages):
        """Successful completion should return proper response."""
        await llm_manager.set_model("gpt-4o-mini")

        mock_response = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {"content": "Hello! I'm doing well, thanks!"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"total_tokens": 50}
        }

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 200
            mock_post.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            response = await llm_manager.chat_completion(sample_messages)

            assert response.content == "Hello! I'm doing well, thanks!"
            assert response.provider == LLMProvider.NANO_GPT
            assert response.tokens_used == 50

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_error(self, sample_messages):
        """Missing API key should raise ServiceError."""
        with patch.dict('os.environ', {'NANO_GPT_API_KEY': ''}, clear=True):
            manager = LLMManager()
            manager.nano_gpt_api_key = None
            await manager.set_model("gpt-4o-mini")

            with pytest.raises(ServiceError) as exc_info:
                await manager.chat_completion(sample_messages)

            assert "API key not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_error_raises_service_error(self, llm_manager, sample_messages):
        """API errors should raise ServiceError with details."""
        await llm_manager.set_model("gpt-4o-mini")

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 401
            mock_post.__aenter__.return_value.text = AsyncMock(return_value="Unauthorized")
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            with pytest.raises(ServiceError) as exc_info:
                await llm_manager.chat_completion(sample_messages)

            assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stream_raises_error_for_non_streaming(self, llm_manager, sample_messages):
        """Calling chat_completion with stream=True should raise error."""
        with pytest.raises(ValueError) as exc_info:
            await llm_manager.chat_completion(sample_messages, stream=True)

        assert "Use chat_completion_stream" in str(exc_info.value)


# ============================================================================
# Nano-GPT Streaming Tests
# ============================================================================

class TestNanoGPTStreaming:
    """Tests for Nano-GPT streaming completions."""

    @pytest.mark.asyncio
    async def test_successful_streaming(self, llm_manager, sample_messages):
        """Streaming should yield chunks correctly."""
        await llm_manager.set_model("gpt-4o-mini")

        chunks = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"!"}}]}\n\n',
            b'data: [DONE]\n\n',
        ]

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 200

            # Create async iterator for content
            async def async_chunks():
                for chunk in chunks:
                    yield chunk

            mock_post.__aenter__.return_value.content = async_chunks()
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            result_chunks = []
            async for chunk in llm_manager.chat_completion_stream(sample_messages):
                result_chunks.append(chunk)

            assert "".join(result_chunks) == "Hello world!"


# ============================================================================
# Ollama Completion Tests
# ============================================================================

class TestOllamaCompletion:
    """Tests for Ollama chat completions."""

    @pytest.mark.asyncio
    async def test_successful_completion(self, llm_manager, sample_messages):
        """Successful Ollama completion should return proper response."""
        mock_response = {
            "model": "llama3:latest",
            "message": {"role": "assistant", "content": "Hello! How can I help?"},
            "done": True
        }

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 200
            mock_post.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            response = await llm_manager.chat_completion(sample_messages)

            assert response.content == "Hello! How can I help?"
            assert response.provider == LLMProvider.OLLAMA
            assert response.model == "llama3:latest"

    @pytest.mark.asyncio
    async def test_ollama_api_error(self, llm_manager, sample_messages):
        """Ollama API errors should raise ServiceError."""
        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 500
            mock_post.__aenter__.return_value.text = AsyncMock(return_value="Internal error")
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            with pytest.raises(ServiceError) as exc_info:
                await llm_manager.chat_completion(sample_messages)

            assert "500" in str(exc_info.value)


# ============================================================================
# Ollama Streaming Tests
# ============================================================================

class TestOllamaStreaming:
    """Tests for Ollama streaming completions."""

    @pytest.mark.asyncio
    async def test_successful_streaming(self, llm_manager, sample_messages):
        """Streaming should yield chunks correctly."""
        chunks = [
            b'{"message":{"content":"Hello"},"done":false}\n',
            b'{"message":{"content":" there"},"done":false}\n',
            b'{"message":{"content":"!"},"done":true}\n',
        ]

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 200

            async def async_chunks():
                for chunk in chunks:
                    yield chunk

            mock_post.__aenter__.return_value.content = async_chunks()
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            result_chunks = []
            async for chunk in llm_manager.chat_completion_stream(sample_messages):
                result_chunks.append(chunk)

            assert "".join(result_chunks) == "Hello there!"


# ============================================================================
# Connection Test Tests
# ============================================================================

class TestConnectionTests:
    """Tests for provider connection testing."""

    @pytest.mark.asyncio
    async def test_nano_gpt_connection_success(self, llm_manager):
        """Successful Nano-GPT connection test."""
        mock_response = {
            "data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4o"}]
        }

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value.status = 200
            mock_get.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.__aenter__.return_value.get = MagicMock(return_value=mock_get)
            MockSession.return_value = mock_session

            result = await llm_manager.test_connection(LLMProvider.NANO_GPT)

            assert result["success"] is True
            assert result["provider"] == "nano_gpt"
            assert "gpt-4o-mini" in result["available_models"]

    @pytest.mark.asyncio
    async def test_nano_gpt_connection_no_api_key(self):
        """Nano-GPT connection should fail without API key."""
        with patch.dict('os.environ', {'NANO_GPT_API_KEY': ''}, clear=True):
            manager = LLMManager()
            manager.nano_gpt_api_key = None

            result = await manager.test_connection(LLMProvider.NANO_GPT)

            assert result["success"] is False
            assert "API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_ollama_connection_success(self, llm_manager):
        """Successful Ollama connection test."""
        mock_response = {
            "models": [{"name": "llama3:latest"}, {"name": "llava:latest"}]
        }

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value.status = 200
            mock_get.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.__aenter__.return_value.get = MagicMock(return_value=mock_get)
            MockSession.return_value = mock_session

            result = await llm_manager.test_connection(LLMProvider.OLLAMA)

            assert result["success"] is True
            assert result["provider"] == "ollama"
            assert "llama3:latest" in result["available_models"]

    @pytest.mark.asyncio
    async def test_ollama_connection_failure(self, llm_manager):
        """Ollama connection should handle failures."""
        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value.status = 503
            mock_session.__aenter__.return_value.get = MagicMock(return_value=mock_get)
            MockSession.return_value = mock_session

            result = await llm_manager.test_connection(LLMProvider.OLLAMA)

            assert result["success"] is False
            assert "503" in result["error"]

    @pytest.mark.asyncio
    async def test_default_provider_connection(self, llm_manager):
        """Should test current provider if none specified."""
        mock_response = {"models": [{"name": "llama3:latest"}]}

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value.status = 200
            mock_get.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.__aenter__.return_value.get = MagicMock(return_value=mock_get)
            MockSession.return_value = mock_session

            # Current provider is Ollama by default
            result = await llm_manager.test_connection()

            assert result["provider"] == "ollama"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_timeout_error(self, llm_manager, sample_messages):
        """Timeout should raise ServiceError."""
        import asyncio

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.side_effect = asyncio.TimeoutError()
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            await llm_manager.set_model("gpt-4o-mini")

            with pytest.raises(ServiceError) as exc_info:
                await llm_manager.chat_completion(sample_messages)

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_network_error(self, llm_manager, sample_messages):
        """Network errors should raise ServiceError."""
        import aiohttp

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.side_effect = aiohttp.ClientError("Connection refused")
            mock_session.__aenter__.return_value.post = MagicMock(return_value=mock_post)
            MockSession.return_value = mock_session

            with pytest.raises(ServiceError):
                await llm_manager.chat_completion(sample_messages)

    @pytest.mark.asyncio
    async def test_unsupported_provider(self, llm_manager, sample_messages):
        """Unsupported provider should raise ValueError."""
        llm_manager.current_provider = "invalid_provider"

        with pytest.raises(ValueError) as exc_info:
            await llm_manager.chat_completion(sample_messages)

        assert "Unsupported provider" in str(exc_info.value)


# ============================================================================
# Message Formatting Tests
# ============================================================================

class TestMessageFormatting:
    """Tests for message formatting."""

    @pytest.mark.asyncio
    async def test_messages_converted_to_api_format(self, llm_manager, sample_messages):
        """Messages should be converted to API format."""
        await llm_manager.set_model("gpt-4o-mini")

        captured_payload = None

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()

            async def capture_post(url, json, **kwargs):
                nonlocal captured_payload
                captured_payload = json
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "choices": [{"message": {"content": "test"}}],
                    "usage": {"total_tokens": 10}
                })
                return mock_response

            mock_session.__aenter__.return_value.post = capture_post
            MockSession.return_value = mock_session

            await llm_manager.chat_completion(sample_messages)

            assert captured_payload is not None
            assert "messages" in captured_payload
            assert len(captured_payload["messages"]) == 2
            assert captured_payload["messages"][0]["role"] == "system"
            assert captured_payload["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_temperature_parameter(self, llm_manager, sample_messages):
        """Temperature parameter should be passed correctly."""
        await llm_manager.set_model("gpt-4o-mini")

        captured_payload = None

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()

            async def capture_post(url, json, **kwargs):
                nonlocal captured_payload
                captured_payload = json
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "choices": [{"message": {"content": "test"}}],
                    "usage": {"total_tokens": 10}
                })
                return mock_response

            mock_session.__aenter__.return_value.post = capture_post
            MockSession.return_value = mock_session

            await llm_manager.chat_completion(sample_messages, temperature=0.9)

            assert captured_payload["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_max_tokens_parameter(self, llm_manager, sample_messages):
        """Max tokens parameter should be passed when provided."""
        await llm_manager.set_model("gpt-4o-mini")

        captured_payload = None

        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()

            async def capture_post(url, json, **kwargs):
                nonlocal captured_payload
                captured_payload = json
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "choices": [{"message": {"content": "test"}}],
                    "usage": {"total_tokens": 10}
                })
                return mock_response

            mock_session.__aenter__.return_value.post = capture_post
            MockSession.return_value = mock_session

            await llm_manager.chat_completion(sample_messages, max_tokens=100)

            assert captured_payload["max_tokens"] == 100
