"""
Mock fixtures for LLM providers (Nano-GPT and Ollama).

Provides:
- MockLLMResponse: Standard response object
- mock_nano_gpt_response: Fixture for Nano-GPT API responses
- mock_ollama_response: Fixture for Ollama API responses
- mock_streaming_response: Fixture for streaming responses
- mock_aiohttp_session: Fixture for mocking aiohttp ClientSession
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, AsyncGenerator
from dataclasses import dataclass


@dataclass
class MockLLMResponse:
    """Standard mock LLM response."""
    content: str = "This is a mock response from the LLM."
    model: str = "gpt-4o-mini"
    tokens_used: int = 50
    finish_reason: str = "stop"


# Standard responses for different scenarios
MOCK_RESPONSES = {
    "greeting": "Hello! I'm your AI assistant. How can I help you today?",
    "action": '{"action": "move", "target": {"x": 10, "y": 5}, "response": "I\'ll move over there."}',
    "error": "I apologize, but I encountered an issue processing your request.",
    "council": json.dumps({
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
    })
}


@pytest.fixture
def mock_nano_gpt_response():
    """Create a mock Nano-GPT API response."""
    def _create_response(
        content: str = MOCK_RESPONSES["greeting"],
        model: str = "gpt-4o-mini",
        tokens: int = 50,
        status: int = 200
    ) -> Dict[str, Any]:
        if status == 200:
            return {
                "id": "chatcmpl-mock123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": tokens - 20,
                    "total_tokens": tokens
                }
            }
        else:
            return {"error": {"message": "API error", "code": status}}

    return _create_response


@pytest.fixture
def mock_ollama_response():
    """Create a mock Ollama API response."""
    def _create_response(
        content: str = MOCK_RESPONSES["greeting"],
        model: str = "llama3:latest",
        done: bool = True
    ) -> Dict[str, Any]:
        return {
            "model": model,
            "created_at": "2024-01-01T00:00:00Z",
            "message": {
                "role": "assistant",
                "content": content
            },
            "done": done,
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": 20,
            "eval_count": 30
        }

    return _create_response


@pytest.fixture
def mock_streaming_chunks():
    """Create mock streaming response chunks."""
    def _create_chunks(
        content: str = MOCK_RESPONSES["greeting"],
        provider: str = "nano_gpt"
    ) -> List[bytes]:
        words = content.split()
        chunks = []

        if provider == "nano_gpt":
            for i, word in enumerate(words):
                chunk_data = {
                    "id": "chatcmpl-mock123",
                    "object": "chat.completion.chunk",
                    "created": 1234567890,
                    "model": "gpt-4o-mini",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": word + (" " if i < len(words) - 1 else "")},
                            "finish_reason": None if i < len(words) - 1 else "stop"
                        }
                    ]
                }
                chunks.append(f"data: {json.dumps(chunk_data)}\n\n".encode())
            chunks.append(b"data: [DONE]\n\n")

        elif provider == "ollama":
            for i, word in enumerate(words):
                chunk_data = {
                    "model": "llama3:latest",
                    "message": {
                        "role": "assistant",
                        "content": word + (" " if i < len(words) - 1 else "")
                    },
                    "done": i == len(words) - 1
                }
                chunks.append(json.dumps(chunk_data).encode() + b"\n")

        return chunks

    return _create_chunks


class MockAiohttpResponse:
    """Mock aiohttp response object."""

    def __init__(
        self,
        status: int = 200,
        json_data: Dict[str, Any] = None,
        text_data: str = None,
        streaming_chunks: List[bytes] = None
    ):
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data or ""
        self._streaming_chunks = streaming_chunks or []
        self._chunk_index = 0

    async def json(self) -> Dict[str, Any]:
        return self._json_data

    async def text(self) -> str:
        return self._text_data

    @property
    def content(self):
        """Return async iterator for streaming."""
        return self

    def __aiter__(self):
        return self

    async def __anext__(self) -> bytes:
        if self._chunk_index >= len(self._streaming_chunks):
            raise StopAsyncIteration
        chunk = self._streaming_chunks[self._chunk_index]
        self._chunk_index += 1
        return chunk

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockAiohttpSession:
    """Mock aiohttp ClientSession."""

    def __init__(self, responses: Dict[str, MockAiohttpResponse] = None):
        self._responses = responses or {}
        self._default_response = MockAiohttpResponse()
        self._requests = []

    def add_response(self, url_pattern: str, response: MockAiohttpResponse):
        """Add a response for a URL pattern."""
        self._responses[url_pattern] = response

    def set_default_response(self, response: MockAiohttpResponse):
        """Set default response for unmatched URLs."""
        self._default_response = response

    def get_requests(self) -> List[Dict]:
        """Get list of recorded requests."""
        return self._requests

    def _find_response(self, url: str) -> MockAiohttpResponse:
        """Find matching response for URL."""
        for pattern, response in self._responses.items():
            if pattern in url:
                return response
        return self._default_response

    async def post(self, url: str, **kwargs) -> MockAiohttpResponse:
        """Mock POST request."""
        self._requests.append({"method": "POST", "url": url, **kwargs})
        return self._find_response(url)

    async def get(self, url: str, **kwargs) -> MockAiohttpResponse:
        """Mock GET request."""
        self._requests.append({"method": "GET", "url": url, **kwargs})
        return self._find_response(url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session."""
    return MockAiohttpSession()


@pytest.fixture
def mock_llm_manager(mock_nano_gpt_response, mock_ollama_response):
    """Create a fully mocked LLM manager."""
    with patch("app.services.llm_manager.aiohttp.ClientSession") as mock_session:
        session = MockAiohttpSession()

        # Add Nano-GPT responses
        session.add_response(
            "nano-gpt.com/api/v1/chat/completions",
            MockAiohttpResponse(
                status=200,
                json_data=mock_nano_gpt_response()
            )
        )

        # Add Ollama responses
        session.add_response(
            "localhost:11434/api/chat",
            MockAiohttpResponse(
                status=200,
                json_data=mock_ollama_response()
            )
        )

        # Add model list responses
        session.add_response(
            "nano-gpt.com/api/v1/models",
            MockAiohttpResponse(
                status=200,
                json_data={"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4o"}]}
            )
        )

        session.add_response(
            "localhost:11434/api/tags",
            MockAiohttpResponse(
                status=200,
                json_data={"models": [{"name": "llama3:latest"}]}
            )
        )

        mock_session.return_value = session
        yield session


@pytest.fixture
def mock_nano_gpt_api_key():
    """Mock Nano-GPT API key."""
    with patch.dict("os.environ", {"NANO_GPT_API_KEY": "test-api-key-12345"}):
        yield "test-api-key-12345"


@pytest.fixture
def mock_ollama_url():
    """Mock Ollama base URL."""
    with patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}):
        yield "http://localhost:11434"
