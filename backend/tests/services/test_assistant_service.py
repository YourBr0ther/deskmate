"""
Tests for Assistant Service.

Tests cover:
- Assistant state retrieval and updates
- Position updates and movement
- Mode changes (active/idle)
- Energy level management
- Inactivity tracking
- Furniture interaction
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.assistant_service import AssistantService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def assistant_service():
    """Create a fresh assistant service instance."""
    service = AssistantService()
    return service


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_assistant_state():
    """Create a mock AssistantState."""
    state = MagicMock()
    state.id = 1
    state.position_x = 5
    state.position_y = 5
    state.facing_direction = "right"
    state.current_action = "idle"
    state.mode = "active"
    state.energy_level = 1.0
    state.last_user_interaction = datetime.utcnow()
    state.current_room_id = "main_room"
    state.current_floor_plan_id = "studio_apartment"
    state.to_dict.return_value = {
        "id": 1,
        "position": {"x": 5, "y": 5},
        "facing": "right",
        "action": "idle",
        "mode": "active",
        "energy": 1.0
    }
    state.start_movement = MagicMock()
    state.set_action = MagicMock()
    return state


@pytest.fixture
def mock_furniture():
    """Create a mock furniture object."""
    furniture = MagicMock()
    furniture.id = "desk"
    furniture.name = "Desk"
    furniture.object_type = "furniture"
    furniture.position_x = 10
    furniture.position_y = 8
    furniture.size_width = 2
    furniture.size_height = 1
    furniture.is_solid = True
    return furniture


# ============================================================================
# Initialization Tests
# ============================================================================

class TestAssistantServiceInit:
    """Tests for assistant service initialization."""

    def test_repositories_initialized(self, assistant_service):
        """Repositories should be initialized."""
        assert assistant_service.assistant_repo is not None
        assert assistant_service.action_log_repo is not None
        assert assistant_service.room_repo is not None


# ============================================================================
# State Retrieval Tests
# ============================================================================

class TestGetAssistantState:
    """Tests for assistant state retrieval."""

    @pytest.mark.asyncio
    async def test_get_state_with_session(self, assistant_service, mock_session, mock_assistant_state):
        """Should get assistant state with provided session."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )

        result = await assistant_service.get_assistant_state(mock_session)

        assert result == mock_assistant_state
        assistant_service.assistant_repo.get_default_assistant.assert_called_once_with(mock_session)


# ============================================================================
# Position Update Tests
# ============================================================================

class TestPositionUpdate:
    """Tests for position updates."""

    @pytest.mark.asyncio
    async def test_update_position_success(self, assistant_service, mock_session, mock_assistant_state):
        """Should update position successfully."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.update_position = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.action_log_repo.log_action = AsyncMock()

        result = await assistant_service.update_assistant_position(
            mock_session, 10, 8, "left", "walking"
        )

        assert result is not None
        assistant_service.assistant_repo.update_position.assert_called_once()
        assistant_service.action_log_repo.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_position_logs_movement(self, assistant_service, mock_session, mock_assistant_state):
        """Should log the movement action."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.update_position = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.action_log_repo.log_action = AsyncMock()

        await assistant_service.update_assistant_position(mock_session, 10, 8)

        # Check the log was called with move action
        call_args = assistant_service.action_log_repo.log_action.call_args
        assert call_args[1]["action_type"] == "move"
        assert call_args[1]["success"] is True


# ============================================================================
# Movement Tests
# ============================================================================

class TestMoveAssistant:
    """Tests for pathfinding-based movement."""

    @pytest.mark.asyncio
    async def test_move_success_without_validation(self, assistant_service, mock_session, mock_assistant_state):
        """Should move directly without path validation."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.update = AsyncMock(return_value=mock_assistant_state)
        assistant_service.assistant_repo.update_position = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.action_log_repo.log_action = AsyncMock()
        assistant_service.room_repo.get_solid_objects = AsyncMock(return_value=[])

        result = await assistant_service.move_assistant_to(
            mock_session, 10, 8, validate_path=False
        )

        assert result["success"] is True
        assert "path" in result

    @pytest.mark.asyncio
    async def test_move_with_pathfinding(self, assistant_service, mock_session, mock_assistant_state):
        """Should use pathfinding when validation is enabled."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.update = AsyncMock(return_value=mock_assistant_state)
        assistant_service.assistant_repo.update_position = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.action_log_repo.log_action = AsyncMock()
        assistant_service.room_repo.get_solid_objects = AsyncMock(return_value=[])

        # Mock pathfinding service
        with patch('app.services.assistant_service.multi_room_pathfinding_service') as mock_pathfinding:
            mock_pathfinding.find_multi_room_path.return_value = {
                "path": [(5, 5), (7, 5), (10, 8)],
                "success": True
            }

            result = await assistant_service.move_assistant_to(
                mock_session, 10, 8, validate_path=True
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_move_no_path_found(self, assistant_service, mock_session, mock_assistant_state):
        """Should return error when no path is found."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.room_repo.get_solid_objects = AsyncMock(return_value=[])
        assistant_service.action_log_repo.log_action = AsyncMock()

        with patch('app.services.assistant_service.multi_room_pathfinding_service') as mock_pathfinding:
            mock_pathfinding.find_multi_room_path.return_value = {"path": [], "success": False}

            result = await assistant_service.move_assistant_to(
                mock_session, 100, 100, validate_path=True
            )

            assert result["success"] is False
            assert "No path found" in result["error"]

    @pytest.mark.asyncio
    async def test_move_handles_exception(self, assistant_service, mock_session, mock_assistant_state):
        """Should handle exceptions gracefully."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            side_effect=Exception("Database error")
        )
        assistant_service.action_log_repo.log_action = AsyncMock()

        result = await assistant_service.move_assistant_to(mock_session, 10, 8)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Furniture Interaction Tests
# ============================================================================

class TestSitOnFurniture:
    """Tests for sitting on furniture."""

    @pytest.mark.asyncio
    async def test_sit_success(self, assistant_service, mock_session, mock_assistant_state, mock_furniture):
        """Should sit on furniture successfully."""
        assistant_service.room_repo.get_by_id = AsyncMock(return_value=mock_furniture)
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.update = AsyncMock(return_value=mock_assistant_state)
        assistant_service.assistant_repo.update_position = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.action_log_repo.log_action = AsyncMock()
        assistant_service.room_repo.get_solid_objects = AsyncMock(return_value=[])

        result = await assistant_service.sit_on_furniture(mock_session, "desk")

        assert result["success"] is True
        assert result["action"] == "sitting"

    @pytest.mark.asyncio
    async def test_sit_furniture_not_found(self, assistant_service, mock_session):
        """Should return error when furniture not found."""
        assistant_service.room_repo.get_by_id = AsyncMock(return_value=None)

        result = await assistant_service.sit_on_furniture(mock_session, "nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_sit_not_furniture(self, assistant_service, mock_session, mock_furniture):
        """Should return error when object is not furniture."""
        mock_furniture.object_type = "decoration"
        assistant_service.room_repo.get_by_id = AsyncMock(return_value=mock_furniture)

        result = await assistant_service.sit_on_furniture(mock_session, "lamp")

        assert result["success"] is False
        assert "not furniture" in result["error"]


# ============================================================================
# Mode Management Tests
# ============================================================================

class TestModeManagement:
    """Tests for mode changes."""

    @pytest.mark.asyncio
    async def test_set_mode_success(self, assistant_service, mock_session, mock_assistant_state):
        """Should change mode successfully."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.set_mode = AsyncMock(return_value=mock_assistant_state)
        assistant_service.action_log_repo.log_action = AsyncMock()

        result = await assistant_service.set_assistant_mode(mock_session, "idle")

        assert result["success"] is True
        assert result["new_mode"] == "idle"

    @pytest.mark.asyncio
    async def test_set_mode_logs_change(self, assistant_service, mock_session, mock_assistant_state):
        """Should log mode change."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )
        assistant_service.assistant_repo.set_mode = AsyncMock(return_value=mock_assistant_state)
        assistant_service.action_log_repo.log_action = AsyncMock()

        await assistant_service.set_assistant_mode(mock_session, "idle")

        call_args = assistant_service.action_log_repo.log_action.call_args
        assert call_args[1]["action_type"] == "mode_change"

    @pytest.mark.asyncio
    async def test_set_mode_handles_error(self, assistant_service, mock_session):
        """Should handle errors gracefully."""
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await assistant_service.set_assistant_mode(mock_session, "idle")

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Energy Management Tests
# ============================================================================

class TestEnergyManagement:
    """Tests for energy level management."""

    @pytest.mark.asyncio
    async def test_update_energy_positive(self, assistant_service, mock_session, mock_assistant_state):
        """Should increase energy level."""
        assistant_service.assistant_repo.update_energy_level = AsyncMock(
            return_value=mock_assistant_state
        )

        await assistant_service.update_energy_level(mock_session, 0.2)

        assistant_service.assistant_repo.update_energy_level.assert_called_once_with(
            mock_session, 0.2
        )

    @pytest.mark.asyncio
    async def test_update_energy_negative(self, assistant_service, mock_session, mock_assistant_state):
        """Should decrease energy level."""
        assistant_service.assistant_repo.update_energy_level = AsyncMock(
            return_value=mock_assistant_state
        )

        await assistant_service.update_energy_level(mock_session, -0.1)

        assistant_service.assistant_repo.update_energy_level.assert_called_once_with(
            mock_session, -0.1
        )


# ============================================================================
# Inactivity Tracking Tests
# ============================================================================

class TestInactivityTracking:
    """Tests for inactivity duration tracking."""

    @pytest.mark.asyncio
    async def test_inactivity_duration_calculation(self, assistant_service, mock_session, mock_assistant_state):
        """Should calculate inactivity duration correctly."""
        # Set last interaction to 5 minutes ago
        mock_assistant_state.last_user_interaction = datetime.utcnow() - timedelta(minutes=5)
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )

        duration = await assistant_service.get_inactivity_duration(mock_session)

        # Should be approximately 5 minutes (allow for test execution time)
        assert 4.9 <= duration <= 5.1

    @pytest.mark.asyncio
    async def test_inactivity_no_previous_interaction(self, assistant_service, mock_session, mock_assistant_state):
        """Should return 0 if no previous interaction."""
        mock_assistant_state.last_user_interaction = None
        assistant_service.assistant_repo.get_default_assistant = AsyncMock(
            return_value=mock_assistant_state
        )

        duration = await assistant_service.get_inactivity_duration(mock_session)

        assert duration == 0.0

    @pytest.mark.asyncio
    async def test_record_user_interaction(self, assistant_service, mock_session):
        """Should record user interaction."""
        assistant_service.assistant_repo.record_user_interaction = AsyncMock()

        await assistant_service.record_user_interaction(mock_session)

        assistant_service.assistant_repo.record_user_interaction.assert_called_once_with(mock_session)


# ============================================================================
# State Update Tests
# ============================================================================

class TestStateUpdate:
    """Tests for general state updates."""

    @pytest.mark.asyncio
    async def test_update_state(self, assistant_service, mock_session, mock_assistant_state):
        """Should update assistant state."""
        assistant_service.assistant_repo.update = AsyncMock(return_value=mock_assistant_state)

        result = await assistant_service.update_assistant_state(mock_session, mock_assistant_state)

        assert result == mock_assistant_state
        assistant_service.assistant_repo.update.assert_called_once()


# ============================================================================
# Helper Method Tests
# ============================================================================

class TestHelperMethods:
    """Tests for helper methods."""

    def test_calculate_facing_right(self, assistant_service):
        """Should calculate right facing correctly."""
        facing = assistant_service._calculate_facing(5, 2)
        assert facing == "right"

    def test_calculate_facing_left(self, assistant_service):
        """Should calculate left facing correctly."""
        facing = assistant_service._calculate_facing(-5, 2)
        assert facing == "left"

    def test_calculate_facing_down(self, assistant_service):
        """Should calculate down facing correctly."""
        facing = assistant_service._calculate_facing(2, 5)
        assert facing == "down"

    def test_calculate_facing_up(self, assistant_service):
        """Should calculate up facing correctly."""
        facing = assistant_service._calculate_facing(2, -5)
        assert facing == "up"

    @pytest.mark.asyncio
    async def test_get_room_obstacles(self, assistant_service, mock_session):
        """Should get room obstacles as coordinate set."""
        mock_obj = MagicMock()
        mock_obj.position_x = 5
        mock_obj.position_y = 5
        mock_obj.size_width = 2
        mock_obj.size_height = 2

        assistant_service.room_repo.get_solid_objects = AsyncMock(return_value=[mock_obj])

        obstacles = await assistant_service._get_room_obstacles(mock_session)

        # Should include all cells occupied by the object
        assert (5, 5) in obstacles
        assert (5, 6) in obstacles
        assert (6, 5) in obstacles
        assert (6, 6) in obstacles
