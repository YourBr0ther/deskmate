"""
Tests for Assistant API endpoints.

Tests cover:
- GET /assistant/state - Get assistant state
- PUT /assistant/position - Update position
- POST /assistant/move - Move with pathfinding
- POST /assistant/sit - Sit on furniture
- GET /assistant/mode - Get mode
- PUT /assistant/mode - Set mode
- POST /assistant/pick-up - Pick up object
- POST /assistant/put-down - Put down object
- GET /assistant/holding - Get holding status
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_assistant_state():
    """Create a mock assistant state."""
    state = MagicMock()
    state.id = 1
    state.position_x = 5
    state.position_y = 5
    state.mode = "active"
    state.energy_level = 1.0
    state.last_user_interaction = datetime.utcnow()
    state.current_action = "idle"
    state.holding_object_id = None
    state.current_room_id = "main_room"
    state.current_floor_plan_id = "studio_apartment"
    state.to_dict.return_value = {
        "id": 1,
        "position": {"x": 5, "y": 5},
        "mode": "active",
        "energy": 1.0,
        "action": "idle"
    }
    return state


# ============================================================================
# GET /assistant/state Tests
# ============================================================================

class TestGetAssistantState:
    """Tests for GET /assistant/state endpoint."""

    @pytest.mark.asyncio
    async def test_get_state_success(self, client, mock_assistant_state):
        """Should return assistant state."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            response = await client.get("/assistant/state")

            assert response.status_code == 200
            data = response.json()
            assert "position" in data

    @pytest.mark.asyncio
    async def test_get_state_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(side_effect=Exception("Test error"))

            response = await client.get("/assistant/state")

            assert response.status_code == 500


# ============================================================================
# PUT /assistant/position Tests
# ============================================================================

class TestUpdatePosition:
    """Tests for PUT /assistant/position endpoint."""

    @pytest.mark.asyncio
    async def test_update_position_success(self, client, mock_assistant_state):
        """Should update position successfully."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.update_assistant_position = AsyncMock(
                return_value=mock_assistant_state.to_dict()
            )

            response = await client.put(
                "/assistant/position",
                json={"x": 10, "y": 8}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_position_missing_coordinates(self, client):
        """Should return 400 for missing coordinates."""
        response = await client.put(
            "/assistant/position",
            json={"x": 10}  # Missing y
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_position_out_of_bounds(self, client):
        """Should return 400 for out of bounds position."""
        response = await client.put(
            "/assistant/position",
            json={"x": 100, "y": 8}  # x > 63
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_position_with_facing(self, client, mock_assistant_state):
        """Should accept facing parameter."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.update_assistant_position = AsyncMock(
                return_value=mock_assistant_state.to_dict()
            )

            response = await client.put(
                "/assistant/position",
                json={"x": 10, "y": 8, "facing": "left"}
            )

            assert response.status_code == 200


# ============================================================================
# POST /assistant/move Tests
# ============================================================================

class TestMoveAssistant:
    """Tests for POST /assistant/move endpoint."""

    @pytest.mark.asyncio
    async def test_move_success(self, client):
        """Should move assistant successfully."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.move_assistant_to = AsyncMock(return_value={
                "success": True,
                "path": [(5, 5), (7, 5), (10, 8)]
            })

            response = await client.post(
                "/assistant/move",
                json={"target": {"x": 10, "y": 8}}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_move_missing_target(self, client):
        """Should return 400 for missing target."""
        response = await client.post(
            "/assistant/move",
            json={}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_move_out_of_bounds(self, client):
        """Should return 400 for out of bounds target."""
        response = await client.post(
            "/assistant/move",
            json={"target": {"x": 100, "y": 8}}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_move_with_validate_path_false(self, client):
        """Should accept validate_path parameter."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.move_assistant_to = AsyncMock(return_value={
                "success": True,
                "path": [(5, 5), (10, 8)]
            })

            response = await client.post(
                "/assistant/move",
                json={"target": {"x": 10, "y": 8}, "validate_path": False}
            )

            assert response.status_code == 200


# ============================================================================
# POST /assistant/sit Tests
# ============================================================================

class TestSitOnFurniture:
    """Tests for POST /assistant/sit endpoint."""

    @pytest.mark.asyncio
    async def test_sit_success(self, client):
        """Should sit on furniture successfully."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.sit_on_furniture = AsyncMock(return_value={
                "success": True,
                "action": "sitting",
                "furniture": "desk"
            })

            response = await client.post(
                "/assistant/sit",
                json={"furniture_id": "desk"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_sit_missing_furniture_id(self, client):
        """Should return 400 for missing furniture_id."""
        response = await client.post(
            "/assistant/sit",
            json={}
        )

        assert response.status_code == 400


# ============================================================================
# Mode Endpoints Tests
# ============================================================================

class TestModeEndpoints:
    """Tests for mode-related endpoints."""

    @pytest.mark.asyncio
    async def test_get_mode_success(self, client, mock_assistant_state):
        """Should return assistant mode."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)
            mock_service.get_inactivity_duration = AsyncMock(return_value=5.0)

            response = await client.get("/assistant/mode")

            assert response.status_code == 200
            data = response.json()
            assert "mode" in data
            assert data["mode"] == "active"

    @pytest.mark.asyncio
    async def test_set_mode_active(self, client):
        """Should set mode to active."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.set_assistant_mode = AsyncMock(return_value={
                "success": True,
                "new_mode": "active"
            })

            response = await client.put(
                "/assistant/mode",
                json={"mode": "active"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_mode_idle(self, client):
        """Should set mode to idle."""
        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.set_assistant_mode = AsyncMock(return_value={
                "success": True,
                "new_mode": "idle"
            })

            response = await client.put(
                "/assistant/mode",
                json={"mode": "idle"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_mode_invalid(self, client):
        """Should return 400 for invalid mode."""
        response = await client.put(
            "/assistant/mode",
            json={"mode": "invalid"}
        )

        assert response.status_code == 400


# ============================================================================
# Object Manipulation Tests
# ============================================================================

class TestPickUpObject:
    """Tests for POST /assistant/pick-up endpoint."""

    @pytest.mark.asyncio
    async def test_pick_up_success(self, client):
        """Should pick up object successfully."""
        with patch('app.api.assistant.action_executor') as mock_executor:
            mock_executor.execute_single_action = AsyncMock(return_value={
                "success": True,
                "action_type": "pick_up"
            })

            response = await client.post("/assistant/pick-up/lamp")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pick_up_failure(self, client):
        """Should return 400 when pick up fails."""
        with patch('app.api.assistant.action_executor') as mock_executor:
            mock_executor.execute_single_action = AsyncMock(return_value={
                "success": False,
                "error": "Object not found"
            })

            response = await client.post("/assistant/pick-up/nonexistent")

            assert response.status_code == 400


class TestPutDownObject:
    """Tests for POST /assistant/put-down endpoint."""

    @pytest.mark.asyncio
    async def test_put_down_success(self, client, mock_assistant_state):
        """Should put down object successfully."""
        mock_assistant_state.holding_object_id = "lamp"

        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            with patch('app.api.assistant.action_executor') as mock_executor:
                mock_executor.execute_single_action = AsyncMock(return_value={
                    "success": True,
                    "action_type": "put_down"
                })

                response = await client.post("/assistant/put-down")

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_put_down_not_holding(self, client, mock_assistant_state):
        """Should return 400 when not holding anything."""
        mock_assistant_state.holding_object_id = None

        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            response = await client.post("/assistant/put-down")

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_put_down_with_position(self, client, mock_assistant_state):
        """Should accept target position."""
        mock_assistant_state.holding_object_id = "lamp"

        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            with patch('app.api.assistant.action_executor') as mock_executor:
                mock_executor.execute_single_action = AsyncMock(return_value={
                    "success": True
                })

                response = await client.post(
                    "/assistant/put-down",
                    json={"position": {"x": 10, "y": 8}}
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_put_down_position_out_of_bounds(self, client, mock_assistant_state):
        """Should return 400 for out of bounds position."""
        mock_assistant_state.holding_object_id = "lamp"

        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            response = await client.post(
                "/assistant/put-down",
                json={"position": {"x": 100, "y": 8}}
            )

            assert response.status_code == 400


class TestGetHoldingStatus:
    """Tests for GET /assistant/holding endpoint."""

    @pytest.mark.asyncio
    async def test_holding_nothing(self, client, mock_assistant_state):
        """Should return null when not holding anything."""
        mock_assistant_state.holding_object_id = None

        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            response = await client.get("/assistant/holding")

            assert response.status_code == 200
            data = response.json()
            assert data["holding_object_id"] is None

    @pytest.mark.asyncio
    async def test_holding_object(self, client, mock_assistant_state):
        """Should return object info when holding something."""
        mock_assistant_state.holding_object_id = "lamp"

        with patch('app.api.assistant.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            with patch('app.api.assistant.room_service') as mock_room:
                mock_room.get_all_objects = AsyncMock(return_value=[
                    {"id": "lamp", "name": "Desk Lamp"}
                ])

                response = await client.get("/assistant/holding")

                assert response.status_code == 200
                data = response.json()
                assert data["holding_object_id"] == "lamp"
                assert data["holding_object_name"] == "Desk Lamp"


# ============================================================================
# Idle Mode Endpoints Tests
# ============================================================================

class TestIdleEndpoints:
    """Tests for idle mode endpoints."""

    @pytest.mark.asyncio
    async def test_get_idle_status(self, client):
        """Should return idle controller status."""
        with patch('app.api.assistant.idle_controller') as mock_idle:
            mock_idle.get_status = AsyncMock(return_value={
                "is_running": True,
                "current_mode": "active",
                "action_count": 0
            })

            response = await client.get("/assistant/idle/status")

            assert response.status_code == 200
            data = response.json()
            assert "is_running" in data

    @pytest.mark.asyncio
    async def test_force_idle_mode(self, client):
        """Should force idle mode."""
        with patch('app.api.assistant.idle_controller') as mock_idle:
            mock_idle.force_idle_mode = AsyncMock()

            response = await client.post("/assistant/idle/force")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["new_mode"] == "idle"

    @pytest.mark.asyncio
    async def test_force_active_mode(self, client):
        """Should force active mode."""
        with patch('app.api.assistant.idle_controller') as mock_idle:
            mock_idle.force_active_mode = AsyncMock()

            response = await client.post("/assistant/idle/activate")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["new_mode"] == "active"


# ============================================================================
# Dreams Endpoints Tests
# ============================================================================

class TestDreamsEndpoints:
    """Tests for dreams-related endpoints."""

    @pytest.mark.asyncio
    async def test_get_dreams(self, client):
        """Should return recent dreams."""
        with patch('app.api.assistant.dream_memory') as mock_dreams:
            mock_dreams.get_recent_dreams = AsyncMock(return_value=[
                {"action": "move", "content": "Explored the room"}
            ])

            response = await client.get("/assistant/dreams?limit=10&hours_back=24")

            assert response.status_code == 200
            data = response.json()
            assert "dreams" in data
            assert "count" in data

    @pytest.mark.asyncio
    async def test_get_dreams_limit_exceeded(self, client):
        """Should return 400 when limit exceeds maximum."""
        response = await client.get("/assistant/dreams?limit=200")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_search_dreams(self, client):
        """Should search dreams."""
        with patch('app.api.assistant.dream_memory') as mock_dreams:
            mock_dreams.search_relevant_dreams = AsyncMock(return_value=[
                {"action": "interact", "content": "Turned on lamp"}
            ])

            response = await client.get("/assistant/dreams/search?query=lamp&limit=5")

            assert response.status_code == 200
            data = response.json()
            assert "dreams" in data

    @pytest.mark.asyncio
    async def test_search_dreams_short_query(self, client):
        """Should return 400 for short query."""
        response = await client.get("/assistant/dreams/search?query=a")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_dream_stats(self, client):
        """Should return dream statistics."""
        with patch('app.api.assistant.dream_memory') as mock_dreams:
            mock_dreams.get_dream_statistics = AsyncMock(return_value={
                "total_dreams": 10,
                "action_breakdown": {"move": 5, "interact": 5}
            })

            response = await client.get("/assistant/dreams/stats")

            assert response.status_code == 200


# ============================================================================
# Assistant Switching Tests
# ============================================================================

class TestAssistantSwitching:
    """Tests for assistant switching endpoints."""

    @pytest.mark.asyncio
    async def test_switch_to_persona(self, client):
        """Should switch to persona-based assistant."""
        response = await client.post(
            "/assistant/switch",
            json={"assistant_id": "persona-Alice"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["persona_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_switch_invalid_assistant(self, client):
        """Should return 400 for invalid assistant ID."""
        response = await client.post(
            "/assistant/switch",
            json={"assistant_id": "invalid-format"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_switch_missing_id(self, client):
        """Should return 400 for missing assistant ID."""
        response = await client.post(
            "/assistant/switch",
            json={}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_current_assistant(self, client):
        """Should return current assistant info."""
        response = await client.get("/assistant/current")

        assert response.status_code == 200
        data = response.json()
        # Could be None if not set
        assert "id" in data or "status" in data
