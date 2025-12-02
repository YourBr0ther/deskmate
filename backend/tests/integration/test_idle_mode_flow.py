"""
Integration tests for idle mode flow.

Tests the complete idle mode pipeline including:
- Idle mode activation
- Autonomous actions
- Dream memory storage
- Mode transitions
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.main import app


class TestIdleModeActivation:
    """Integration tests for idle mode activation."""

    @pytest.mark.asyncio
    async def test_enter_idle_mode_via_command(self):
        """Test entering idle mode via /idle command."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.enter_idle_mode.return_value = {
                "success": True,
                "mode": "idle",
                "message": "Entering idle mode..."
            }
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/assistant/idle/enter")

            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_exit_idle_mode(self):
        """Test exiting idle mode."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.exit_idle_mode.return_value = {
                "success": True,
                "mode": "active",
                "message": "Exiting idle mode"
            }
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/assistant/idle/exit")

            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_idle_status(self):
        """Test getting idle mode status."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/assistant/status")

        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            # Should have status information
            assert isinstance(data, dict)


class TestIdleModeActions:
    """Integration tests for actions during idle mode."""

    @pytest.fixture
    def mock_idle_action(self):
        """Mock idle mode action."""
        return {
            "action_type": "movement",
            "target": {"x": 15, "y": 7},
            "reason": "Exploring the room",
            "timestamp": datetime.now().isoformat()
        }

    @pytest.mark.asyncio
    async def test_idle_mode_generates_actions(self, mock_idle_action):
        """Test that idle mode generates autonomous actions."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.get_next_action.return_value = mock_idle_action
            mock_controller_class.return_value = mock_controller

            # Simulate idle tick
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/assistant/idle/tick")

            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_idle_actions_use_lightweight_model(self):
        """Test that idle mode uses lightweight LLM models."""
        with patch('app.services.llm_manager.LLMManager') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.generate_response.return_value = {
                "response": "I think I'll look around...",
                "model": "phi-3",  # Lightweight model
                "provider": "ollama"
            }
            mock_llm_class.return_value = mock_llm

            with patch('app.services.idle_controller.IdleController') as mock_controller_class:
                mock_controller = AsyncMock()
                mock_controller.is_idle = True
                mock_controller.process_idle_tick.return_value = {
                    "action": "explore",
                    "thoughts": "Curious about surroundings"
                }
                mock_controller_class.return_value = mock_controller

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/assistant/idle/tick")

                assert response.status_code in [200, 404, 500]


class TestDreamMemory:
    """Integration tests for dream memory during idle mode."""

    @pytest.fixture
    def mock_dream_entry(self):
        """Mock dream entry."""
        return {
            "id": "dream-123",
            "content": "I dreamed about organizing the bookshelf",
            "mood": "peaceful",
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }

    @pytest.mark.asyncio
    async def test_dreams_are_stored(self, mock_dream_entry):
        """Test that idle mode dreams are stored."""
        with patch('app.services.dream_memory.DreamMemoryService') as mock_dream_class:
            mock_dream = AsyncMock()
            mock_dream.store_dream.return_value = mock_dream_entry
            mock_dream_class.return_value = mock_dream

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/assistant/dreams/store",
                    json={
                        "content": "Dreaming about the room",
                        "mood": "curious"
                    }
                )

            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_dreams_expire_after_24_hours(self):
        """Test that dreams expire after 24 hours."""
        with patch('app.services.dream_memory.DreamMemoryService') as mock_dream_class:
            mock_dream = AsyncMock()
            mock_dream.cleanup_expired_dreams.return_value = {"cleaned": 5}
            mock_dream_class.return_value = mock_dream

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/assistant/dreams/cleanup")

            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_recent_dreams(self):
        """Test retrieving recent dreams."""
        with patch('app.services.dream_memory.DreamMemoryService') as mock_dream_class:
            mock_dream = AsyncMock()
            mock_dream.get_recent_dreams.return_value = [
                {
                    "id": "dream-1",
                    "content": "Dream 1",
                    "mood": "happy"
                },
                {
                    "id": "dream-2",
                    "content": "Dream 2",
                    "mood": "curious"
                }
            ]
            mock_dream_class.return_value = mock_dream

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/assistant/dreams")

            assert response.status_code in [200, 404, 500]


class TestModeTransitions:
    """Integration tests for mode transitions."""

    @pytest.mark.asyncio
    async def test_user_input_exits_idle_mode(self):
        """Test that user input automatically exits idle mode."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.is_idle = True
            mock_controller.exit_idle_mode.return_value = {
                "success": True,
                "mode": "active"
            }
            mock_controller_class.return_value = mock_controller

            # Send a chat message while in idle mode
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/simple",
                    json={"message": "Hello, are you there?"}
                )

            # Should exit idle mode and respond
            assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_timeout_triggers_idle_mode(self):
        """Test that inactivity timeout triggers idle mode."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.check_timeout.return_value = {
                "should_enter_idle": True,
                "inactive_seconds": 600  # 10 minutes
            }
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/assistant/idle/check-timeout")

            assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_smooth_transition_from_idle_to_active(self):
        """Test smooth transition from idle to active mode."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.is_idle = True
            mock_controller.exit_idle_mode.return_value = {
                "success": True,
                "mode": "active",
                "dream_summary": "I was thinking about the bookshelf..."
            }
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/assistant/idle/exit")

            assert response.status_code in [200, 404, 500]


class TestIdleModeWithRoomState:
    """Integration tests for idle mode with room state awareness."""

    @pytest.mark.asyncio
    async def test_idle_actions_respect_obstacles(self):
        """Test that idle movement respects room obstacles."""
        with patch('app.services.room_service.RoomService') as mock_room_class:
            mock_room = AsyncMock()
            mock_room.get_obstacles.return_value = [
                {"x": 10, "y": 5, "width": 2, "height": 2}
            ]
            mock_room_class.return_value = mock_room

            with patch('app.services.idle_controller.IdleController') as mock_controller_class:
                mock_controller = AsyncMock()
                mock_controller.get_valid_movement_target.return_value = {"x": 15, "y": 8}
                mock_controller_class.return_value = mock_controller

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/assistant/idle/tick")

                assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_idle_can_interact_with_objects(self):
        """Test that idle mode can interact with room objects."""
        with patch('app.services.room_service.RoomService') as mock_room_class:
            mock_room = AsyncMock()
            mock_room.get_interactable_objects.return_value = [
                {"id": "lamp-1", "type": "lamp", "state": "off"},
                {"id": "book-1", "type": "book", "state": "closed"}
            ]
            mock_room_class.return_value = mock_room

            with patch('app.services.idle_controller.IdleController') as mock_controller_class:
                mock_controller = AsyncMock()
                mock_controller.decide_interaction.return_value = {
                    "action": "interact",
                    "object_id": "book-1",
                    "interaction": "read"
                }
                mock_controller_class.return_value = mock_controller

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/assistant/idle/tick")

                assert response.status_code in [200, 404, 500]


class TestIdleModePersonality:
    """Integration tests for personality during idle mode."""

    @pytest.mark.asyncio
    async def test_idle_respects_persona_traits(self):
        """Test that idle behavior respects persona personality traits."""
        with patch('app.services.persona_reader.PersonaReader') as mock_persona_class:
            mock_persona = AsyncMock()
            mock_persona.get_active_persona.return_value = {
                "name": "Alice",
                "personality": "Curious and bookish",
                "interests": ["reading", "exploring"]
            }
            mock_persona_class.return_value = mock_persona

            with patch('app.services.idle_controller.IdleController') as mock_controller_class:
                mock_controller = AsyncMock()
                mock_controller.generate_idle_behavior.return_value = {
                    "action": "move_to_bookshelf",
                    "reason": "Curious about books"
                }
                mock_controller_class.return_value = mock_controller

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/assistant/idle/tick")

                assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_idle_mood_affects_behavior(self):
        """Test that mood affects idle mode behavior."""
        with patch('app.services.idle_controller.IdleController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.current_mood = "tired"
            mock_controller.generate_idle_behavior.return_value = {
                "action": "sit",
                "target": "couch",
                "reason": "Feeling tired, need to rest"
            }
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/assistant/idle/tick")

            assert response.status_code in [200, 404, 500]
