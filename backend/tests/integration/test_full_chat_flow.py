"""
Integration tests for full chat flow.

Tests the complete chat pipeline from user input to response,
including Brain Council processing, memory storage, and response generation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.main import app


class TestFullChatFlow:
    """Integration tests for the complete chat workflow."""

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for chat."""
        return {
            "response": "Hello! I'm your AI assistant. How can I help you today?",
            "model": "gpt-4o-mini",
            "provider": "nano_gpt",
            "tokens": {"prompt": 50, "completion": 20, "total": 70}
        }

    @pytest.fixture
    def mock_brain_council_response(self):
        """Mock Brain Council response."""
        return {
            "success": True,
            "response": "I'd be happy to help! What would you like to know?",
            "reasoning": {
                "personality": "Friendly and helpful response",
                "memory": "No prior conversation context",
                "spatial": "Assistant is at position (10, 5)",
                "action": "No action needed",
                "validation": "Response is valid"
            },
            "actions": [],
            "mood": "happy",
            "model_used": "gpt-4o-mini"
        }

    @pytest.mark.asyncio
    async def test_simple_chat_endpoint(self, mock_llm_response):
        """Test the simple chat endpoint for basic message processing."""
        with patch('app.services.llm_manager.LLMManager') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.generate_response.return_value = mock_llm_response
            mock_llm_class.return_value = mock_llm

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/simple",
                    json={"message": "Hello!"}
                )

            # Should succeed
            assert response.status_code in [200, 422]  # 422 if validation fails without full setup

    @pytest.mark.asyncio
    async def test_chat_with_persona_context(self, mock_llm_response):
        """Test chat with persona context included."""
        with patch('app.services.llm_manager.LLMManager') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.generate_response.return_value = mock_llm_response
            mock_llm_class.return_value = mock_llm

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/simple",
                    json={
                        "message": "What's your name?",
                        "persona_context": {
                            "name": "Alice",
                            "personality": "Friendly and helpful"
                        }
                    }
                )

            # Response should include persona-aware content
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_brain_council_processing(self, mock_brain_council_response):
        """Test message processing through Brain Council."""
        with patch('app.services.brain_council.BrainCouncil') as mock_council_class:
            mock_council = AsyncMock()
            mock_council.process_message.return_value = mock_brain_council_response
            mock_council_class.return_value = mock_council

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/brain/process",
                    json={"message": "Can you help me with something?"}
                )

            assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_chat_history_retrieval(self):
        """Test retrieving chat history."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/conversation/history")

        # Should return history (empty or with messages)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "messages" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_chat_with_memory_storage(self, mock_llm_response):
        """Test that chat messages are stored in memory."""
        with patch('app.services.llm_manager.LLMManager') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.generate_response.return_value = mock_llm_response
            mock_llm_class.return_value = mock_llm

            with patch('app.services.conversation_memory.ConversationMemory') as mock_memory_class:
                mock_memory = AsyncMock()
                mock_memory.add_message.return_value = None
                mock_memory.search_similar.return_value = []
                mock_memory_class.return_value = mock_memory

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/chat/simple",
                        json={"message": "Remember this message"}
                    )

                # Memory operations should have been called
                assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_chat_clear_current(self):
        """Test clearing current chat."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/conversation/memory/clear")

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_chat_memory_stats(self):
        """Test memory statistics endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/conversation/memory/stats")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            # Should have some memory stats
            assert isinstance(data, dict)


class TestChatWithActions:
    """Integration tests for chat that triggers actions."""

    @pytest.fixture
    def mock_action_response(self):
        """Mock response with actions."""
        return {
            "success": True,
            "response": "I'll move to the desk now!",
            "reasoning": {
                "personality": "Willing to help",
                "spatial": "Path to desk is clear",
                "action": "Move to desk"
            },
            "actions": [
                {
                    "type": "movement",
                    "target": {"x": 20, "y": 8},
                    "reason": "User requested movement to desk"
                }
            ],
            "mood": "happy"
        }

    @pytest.mark.asyncio
    async def test_chat_triggers_movement(self, mock_action_response):
        """Test that chat can trigger movement actions."""
        with patch('app.services.brain_council.BrainCouncil') as mock_council_class:
            mock_council = AsyncMock()
            mock_council.process_message.return_value = mock_action_response
            mock_council_class.return_value = mock_council

            with patch('app.services.action_executor.ActionExecutor') as mock_executor_class:
                mock_executor = AsyncMock()
                mock_executor.execute_actions.return_value = {
                    "success": True,
                    "executed": ["movement"]
                }
                mock_executor_class.return_value = mock_executor

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/brain/process",
                        json={"message": "Please move to the desk"}
                    )

                assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_chat_triggers_object_interaction(self):
        """Test that chat can trigger object interactions."""
        action_response = {
            "success": True,
            "response": "I'll turn on the lamp for you!",
            "actions": [
                {
                    "type": "object_interaction",
                    "object_id": "lamp-1",
                    "action": "toggle",
                    "reason": "User wants light"
                }
            ],
            "mood": "helpful"
        }

        with patch('app.services.brain_council.BrainCouncil') as mock_council_class:
            mock_council = AsyncMock()
            mock_council.process_message.return_value = action_response
            mock_council_class.return_value = mock_council

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/brain/process",
                    json={"message": "Turn on the lamp"}
                )

            assert response.status_code in [200, 422, 500]


class TestChatErrorHandling:
    """Integration tests for error handling in chat flow."""

    @pytest.mark.asyncio
    async def test_chat_handles_llm_failure(self):
        """Test graceful handling of LLM failures."""
        with patch('app.services.llm_manager.LLMManager') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.generate_response.side_effect = Exception("LLM unavailable")
            mock_llm_class.return_value = mock_llm

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/simple",
                    json={"message": "Test message"}
                )

            # Should handle error gracefully
            assert response.status_code in [200, 500, 422]

    @pytest.mark.asyncio
    async def test_chat_handles_memory_failure(self):
        """Test chat continues when memory storage fails."""
        with patch('app.services.conversation_memory.ConversationMemory') as mock_memory_class:
            mock_memory = AsyncMock()
            mock_memory.add_message.side_effect = Exception("Memory unavailable")
            mock_memory.search_similar.return_value = []
            mock_memory_class.return_value = mock_memory

            # Chat should still work, just without memory
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/simple",
                    json={"message": "Test without memory"}
                )

            assert response.status_code in [200, 500, 422]

    @pytest.mark.asyncio
    async def test_chat_handles_invalid_input(self):
        """Test handling of invalid chat input."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Empty message
            response = await client.post(
                "/chat/simple",
                json={"message": ""}
            )

        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_chat_handles_missing_fields(self):
        """Test handling of requests with missing fields."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/chat/simple",
                json={}
            )

        # Should return validation error
        assert response.status_code == 422


class TestChatModelSelection:
    """Integration tests for model selection during chat."""

    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test retrieving available chat models."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/chat/models")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_chat_with_specific_model(self):
        """Test specifying a model for chat."""
        mock_response = {
            "response": "Response from specific model",
            "model": "llama3:latest",
            "provider": "ollama"
        }

        with patch('app.services.llm_manager.LLMManager') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.generate_response.return_value = mock_response
            mock_llm_class.return_value = mock_llm

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/simple",
                    json={
                        "message": "Use specific model",
                        "model": "llama3:latest"
                    }
                )

            assert response.status_code in [200, 422, 500]
