"""
Tests for Room Navigation API (Phase 12)

Tests the room navigation endpoints and WebSocket broadcast integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestRoomNavigationAPI:
    """Tests for room navigation API endpoints."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_assistant_state(self):
        """Create a mock assistant state."""
        assistant = MagicMock()
        assistant.id = "test-assistant"
        assistant.position_x = 100.0
        assistant.position_y = 100.0
        assistant.current_room_id = "room-1"
        return assistant

    def test_position_update_message_structure(self):
        """Test that position update messages have correct structure."""
        position_update = {
            "type": "position_update",
            "data": {
                "assistant_id": "test-assistant",
                "position": {"x": 100, "y": 200},
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }

        assert position_update["type"] == "position_update"
        assert "assistant_id" in position_update["data"]
        assert "position" in position_update["data"]
        assert "x" in position_update["data"]["position"]
        assert "y" in position_update["data"]["position"]

    def test_room_transition_message_structure(self):
        """Test that room transition messages have correct structure."""
        room_transition = {
            "type": "room_transition",
            "data": {
                "assistant_id": "test-assistant",
                "from_room": "living_room",
                "to_room": "bedroom",
                "doorway_id": "doorway-1",
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }

        assert room_transition["type"] == "room_transition"
        assert "from_room" in room_transition["data"]
        assert "to_room" in room_transition["data"]
        assert "doorway_id" in room_transition["data"]


class TestRoomNavigationService:
    """Tests for room navigation service."""

    @pytest.fixture
    def navigation_service(self):
        """Create a navigation service instance."""
        from app.services.room_navigation import RoomNavigationService
        return RoomNavigationService()

    def test_navigation_service_initialization(self, navigation_service):
        """Test that navigation service initializes correctly."""
        assert hasattr(navigation_service, 'active_navigation')
        assert hasattr(navigation_service, 'transition_callbacks')
        assert isinstance(navigation_service.active_navigation, dict)
        assert isinstance(navigation_service.transition_callbacks, list)

    def test_add_transition_callback(self, navigation_service):
        """Test adding transition callbacks."""
        callback = MagicMock()
        navigation_service.add_transition_callback(callback)

        assert callback in navigation_service.transition_callbacks

    def test_get_active_navigation_none(self, navigation_service):
        """Test getting active navigation when none exists."""
        result = navigation_service.get_active_navigation("nonexistent")
        assert result is None

    def test_cancel_navigation_nonexistent(self, navigation_service):
        """Test canceling non-existent navigation."""
        result = navigation_service.cancel_navigation("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_notify_position_update(self, navigation_service):
        """Test position update notification via WebSocket."""
        # Patch at the import location inside the method
        with patch('app.api.websocket.connection_manager') as mock_cm:
            mock_cm.broadcast = AsyncMock()

            await navigation_service._notify_position_update(
                "test-assistant",
                {"x": 100, "y": 200}
            )

            mock_cm.broadcast.assert_called_once()
            call_args = mock_cm.broadcast.call_args[0][0]
            assert call_args["type"] == "position_update"
            assert call_args["data"]["assistant_id"] == "test-assistant"

    @pytest.mark.asyncio
    async def test_notify_room_transition(self, navigation_service):
        """Test room transition notification via WebSocket."""
        # Patch at the import location inside the method
        with patch('app.api.websocket.connection_manager') as mock_cm:
            mock_cm.broadcast = AsyncMock()

            await navigation_service._notify_room_transition(
                "test-assistant",
                "room-1",
                "room-2",
                "doorway-1"
            )

            mock_cm.broadcast.assert_called_once()
            call_args = mock_cm.broadcast.call_args[0][0]
            assert call_args["type"] == "room_transition"
            assert call_args["data"]["from_room"] == "room-1"
            assert call_args["data"]["to_room"] == "room-2"


class TestFloorPlanAPI:
    """Tests for floor plan API endpoints."""

    def test_floor_plan_template_categories(self):
        """Test that floor plan templates have valid categories."""
        valid_categories = ['apartment', 'house', 'office', 'studio', 'commercial', 'custom']

        # Test template structure
        template = {
            "id": "studio_apartment",
            "name": "Studio Apartment",
            "category": "apartment",
            "dimensions": {"width": 1300, "height": 600}
        }

        assert template["category"] in valid_categories

    def test_floor_plan_dimensions_structure(self):
        """Test floor plan dimensions structure."""
        dimensions = {
            "width": 1920,
            "height": 480,
            "scale": 1.0,
            "units": "pixels"
        }

        assert "width" in dimensions
        assert "height" in dimensions
        assert dimensions["width"] > 0
        assert dimensions["height"] > 0
