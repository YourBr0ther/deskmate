"""
LLM Manager for handling multiple LLM providers.

Supports:
- Nano-GPT API (https://nano-gpt.com/api)
- Ollama (local models)
- Model selection and switching
- Response streaming
- Error handling and retries
"""

import logging
import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    NANO_GPT = "nano_gpt"
    OLLAMA = "ollama"


@dataclass
class LLMModel:
    """Model configuration for LLM providers."""
    id: str
    name: str
    provider: LLMProvider
    description: str
    max_tokens: int = 4096
    context_window: int = 8192
    supports_streaming: bool = True
    cost_per_token: float = 0.0


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM response structure."""
    content: str
    model: str
    provider: LLMProvider
    tokens_used: int = 0
    finish_reason: str = "stop"
    error: Optional[str] = None


class LLMManager:
    """Manages multiple LLM providers and model selection."""

    def __init__(self):
        self.current_provider = LLMProvider.OLLAMA
        self.current_model = "llama3:latest"
        self.nano_gpt_api_key = os.getenv("NANO_GPT_API_KEY")
        self.nano_gpt_base_url = "https://nano-gpt.com/api/v1"
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Available models configuration
        self.available_models = {
            # Nano-GPT models
            "gpt-4o-mini": LLMModel(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider=LLMProvider.NANO_GPT,
                description="Fast, efficient model for general tasks",
                max_tokens=4096,
                context_window=128000,
                cost_per_token=0.000150
            ),
            "gpt-4o": LLMModel(
                id="gpt-4o",
                name="GPT-4o",
                provider=LLMProvider.NANO_GPT,
                description="Advanced reasoning and complex tasks",
                max_tokens=4096,
                context_window=128000,
                cost_per_token=0.005
            ),
            "claude-3.5-sonnet": LLMModel(
                id="claude-3.5-sonnet",
                name="Claude 3.5 Sonnet",
                provider=LLMProvider.NANO_GPT,
                description="Excellent for creative and analytical tasks",
                max_tokens=4096,
                context_window=200000,
                cost_per_token=0.003
            ),

            # Ollama models (local) - using actually available models
            "llama3:latest": LLMModel(
                id="llama3:latest",
                name="Llama 3 Latest",
                provider=LLMProvider.OLLAMA,
                description="Llama 3 model for general tasks",
                max_tokens=2048,
                context_window=8192
            ),
            "llava:latest": LLMModel(
                id="llava:latest",
                name="LLaVA Latest",
                provider=LLMProvider.OLLAMA,
                description="Vision-language model",
                max_tokens=2048,
                context_window=8192
            ),
            "dolphin-mixtral:latest": LLMModel(
                id="dolphin-mixtral:latest",
                name="Dolphin Mixtral",
                provider=LLMProvider.OLLAMA,
                description="Dolphin-trained Mixtral model",
                max_tokens=2048,
                context_window=8192
            )
        }

    async def get_available_models(self) -> Dict[str, LLMModel]:
        """Get all available models across providers."""
        return self.available_models

    async def set_model(self, model_id: str) -> bool:
        """
        Set the current model and provider.

        Args:
            model_id: ID of the model to use

        Returns:
            True if model was set successfully
        """
        if model_id not in self.available_models:
            logger.error(f"Unknown model: {model_id}")
            return False

        model = self.available_models[model_id]
        self.current_model = model_id
        self.current_provider = model.provider

        logger.info(f"Switched to model: {model.name} ({model.provider.value})")
        return True

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate non-streaming chat completion using current model.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse
        """
        if stream:
            raise ValueError("Use chat_completion_stream for streaming responses")

        if self.current_provider == LLMProvider.NANO_GPT:
            return await self._nano_gpt_completion(messages, temperature, max_tokens)
        elif self.current_provider == LLMProvider.OLLAMA:
            return await self._ollama_completion(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.current_provider}")

    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming chat completion using current model.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            AsyncGenerator yielding response chunks
        """
        if self.current_provider == LLMProvider.NANO_GPT:
            async for chunk in self._nano_gpt_stream(messages, temperature, max_tokens):
                yield chunk
        elif self.current_provider == LLMProvider.OLLAMA:
            async for chunk in self._ollama_stream(messages, temperature, max_tokens):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {self.current_provider}")

    async def _nano_gpt_completion(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int]
    ) -> LLMResponse:
        """Generate completion using Nano-GPT API."""
        if not self.nano_gpt_api_key:
            return LLMResponse(
                content="",
                model=self.current_model,
                provider=LLMProvider.NANO_GPT,
                error="Nano-GPT API key not configured"
            )

        # Convert messages to API format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": self.current_model,
            "messages": api_messages,
            "temperature": temperature,
            "stream": False
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.nano_gpt_api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.nano_gpt_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data.get("usage", {}).get("total_tokens", 0)

                        return LLMResponse(
                            content=content,
                            model=self.current_model,
                            provider=LLMProvider.NANO_GPT,
                            tokens_used=tokens_used
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Nano-GPT API error {response.status}: {error_text}")
                        return LLMResponse(
                            content="",
                            model=self.current_model,
                            provider=LLMProvider.NANO_GPT,
                            error=f"API error: {response.status}"
                        )

        except asyncio.TimeoutError:
            logger.error("Nano-GPT API timeout")
            return LLMResponse(
                content="",
                model=self.current_model,
                provider=LLMProvider.NANO_GPT,
                error="Request timeout"
            )
        except Exception as e:
            logger.error(f"Nano-GPT API error: {e}")
            return LLMResponse(
                content="",
                model=self.current_model,
                provider=LLMProvider.NANO_GPT,
                error=str(e)
            )

    async def _nano_gpt_stream(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion using Nano-GPT API."""
        if not self.nano_gpt_api_key:
            yield f"data: {json.dumps({'error': 'Nano-GPT API key not configured'})}\n\n"
            return

        # Convert messages to API format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": self.current_model,
            "messages": api_messages,
            "temperature": temperature,
            "stream": True
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.nano_gpt_api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.nano_gpt_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    data_str = line_str[6:]
                                    if data_str != '[DONE]':
                                        try:
                                            data = json.loads(data_str)
                                            if 'choices' in data and len(data['choices']) > 0:
                                                delta = data['choices'][0].get('delta', {})
                                                if 'content' in delta:
                                                    yield delta['content']
                                        except json.JSONDecodeError:
                                            continue
                    else:
                        error_text = await response.text()
                        yield f"Error: {response.status} - {error_text}"

        except Exception as e:
            logger.error(f"Nano-GPT streaming error: {e}")
            yield f"Error: {str(e)}"

    async def _ollama_completion(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int]
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        # Convert messages to Ollama format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": self.current_model,
            "messages": api_messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["message"]["content"]

                        return LLMResponse(
                            content=content,
                            model=self.current_model,
                            provider=LLMProvider.OLLAMA,
                            tokens_used=0  # Ollama doesn't provide token count
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error {response.status}: {error_text}")
                        return LLMResponse(
                            content="",
                            model=self.current_model,
                            provider=LLMProvider.OLLAMA,
                            error=f"API error: {response.status}"
                        )

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return LLMResponse(
                content="",
                model=self.current_model,
                provider=LLMProvider.OLLAMA,
                error=str(e)
            )

    async def _ollama_stream(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion using Ollama."""
        # Convert messages to Ollama format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": self.current_model,
            "messages": api_messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                line_str = line.decode('utf-8').strip()
                                if line_str:
                                    try:
                                        data = json.loads(line_str)
                                        if 'message' in data and 'content' in data['message']:
                                            content = data['message']['content']
                                            if content:
                                                yield content
                                        if data.get('done', False):
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    else:
                        error_text = await response.text()
                        yield f"Error: {response.status} - {error_text}"

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"Error: {str(e)}"

    async def test_connection(self, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """
        Test connection to LLM provider.

        Args:
            provider: Provider to test (defaults to current)

        Returns:
            Test result with status and info
        """
        test_provider = provider or self.current_provider

        if test_provider == LLMProvider.NANO_GPT:
            return await self._test_nano_gpt()
        elif test_provider == LLMProvider.OLLAMA:
            return await self._test_ollama()
        else:
            return {"success": False, "error": f"Unknown provider: {test_provider}"}

    async def _test_nano_gpt(self) -> Dict[str, Any]:
        """Test Nano-GPT API connection."""
        if not self.nano_gpt_api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "provider": "nano_gpt"
            }

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.nano_gpt_api_key}",
                    "Content-Type": "application/json"
                }

                async with session.get(
                    f"{self.nano_gpt_base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        available_models = [model["id"] for model in data.get("data", [])]
                        return {
                            "success": True,
                            "provider": "nano_gpt",
                            "available_models": available_models
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API returned status {response.status}",
                            "provider": "nano_gpt"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "nano_gpt"
            }

    async def _test_ollama(self) -> Dict[str, Any]:
        """Test Ollama connection."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        available_models = [model["name"] for model in data.get("models", [])]
                        return {
                            "success": True,
                            "provider": "ollama",
                            "available_models": available_models
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API returned status {response.status}",
                            "provider": "ollama"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "ollama"
            }


# Global LLM manager instance
llm_manager = LLMManager()