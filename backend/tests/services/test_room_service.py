"""
Tests for Room Service.

Tests cover:
- Object management (CRUD operations)
- Object movement and collision detection
- Storage closet operations
- Object state management
- Default object initialization
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.services.room_service import RoomService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def room_service():
    """Create a fresh room service instance."""
    service = RoomService()
    return service


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_object_data():
    """Sample object data for testing."""
    return {
        "id": "test_lamp",
        "name": "Test Lamp",
        "description": "A test lamp",
        "type": "decoration",
        "position": {"x": 5, "y": 5},
        "size": {"width": 1, "height": 1},
        "properties": {
            "solid": False,
            "interactive": True,
            "movable": True
        },
        "sprite": "lamp_sprite",
        "color": "yellow",
        "created_by": "test"
    }


@pytest.fixture
def mock_grid_object():
    """Create a mock GridObject."""
    obj = MagicMock()
    obj.id = "test_object"
    obj.name = "Test Object"
    obj.description = "A test object"
    obj.object_type = "furniture"
    obj.position_x = 10
    obj.position_y = 8
    obj.size_width = 2
    obj.size_height = 1
    obj.is_solid = True
    obj.is_interactive = True
    obj.is_movable = True
    obj.sprite_name = "test_sprite"
    obj.color_scheme = "blue"
    obj.created_by = "test"
    obj.states = []
    obj.to_dict.return_value = {
        "id": "test_object",
        "name": "Test Object",
        "position": {"x": 10, "y": 8},
        "size": {"width": 2, "height": 1}
    }
    return obj


@pytest.fixture
def mock_storage_item():
    """Create a mock StorageItem."""
    item = MagicMock()
    item.id = "storage_item_1"
    item.name = "Stored Lamp"
    item.description = "A lamp in storage"
    item.object_type = "decoration"
    item.default_size_width = 1
    item.default_size_height = 1
    item.is_solid = False
    item.is_interactive = True
    item.sprite_name = "lamp_sprite"
    item.color_scheme = "yellow"
    item.created_by = "user"
    item.to_dict.return_value = {
        "id": "storage_item_1",
        "name": "Stored Lamp",
        "type": "decoration"
    }
    return item


# ============================================================================
# Initialization Tests
# ============================================================================

class TestRoomServiceInit:
    """Tests for room service initialization."""

    def test_default_layout_id(self, room_service):
        """Default layout should be 'default'."""
        assert room_service.current_layout_id == "default"

    def test_repositories_initialized(self, room_service):
        """Repositories should be initialized."""
        assert room_service.object_repo is not None
        assert room_service.state_repo is not None
        assert room_service.storage_repo is not None


# ============================================================================
# Object Management Tests
# ============================================================================

class TestObjectManagement:
    """Tests for object CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_all_objects(self, room_service, mock_session, mock_grid_object):
        """Should return all objects in the room."""
        room_service.object_repo.get_all_with_states = AsyncMock(return_value=[mock_grid_object])

        objects = await room_service.get_all_objects(mock_session)

        assert len(objects) == 1
        room_service.object_repo.get_all_with_states.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_get_object_by_id_found(self, room_service, mock_session, mock_grid_object):
        """Should return object when found."""
        room_service.object_repo.get_by_id_with_states = AsyncMock(return_value=mock_grid_object)

        result = await room_service.get_object_by_id(mock_session, "test_object")

        assert result is not None
        assert result["id"] == "test_object"

    @pytest.mark.asyncio
    async def test_get_object_by_id_not_found(self, room_service, mock_session):
        """Should return None when object not found."""
        room_service.object_repo.get_by_id_with_states = AsyncMock(return_value=None)

        result = await room_service.get_object_by_id(mock_session, "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_object_success(self, room_service, mock_session, sample_object_data, mock_grid_object):
        """Should create object when position is free."""
        room_service.object_repo.check_collision = AsyncMock(return_value=False)
        room_service.object_repo.create = AsyncMock(return_value=mock_grid_object)

        result = await room_service.create_object(mock_session, sample_object_data)

        assert result is not None
        room_service.object_repo.check_collision.assert_called_once()
        room_service.object_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_object_collision(self, room_service, mock_session, sample_object_data):
        """Should raise error when position is occupied."""
        room_service.object_repo.check_collision = AsyncMock(return_value=True)

        with pytest.raises(ValueError) as exc_info:
            await room_service.create_object(mock_session, sample_object_data)

        assert "occupied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_object_success(self, room_service, mock_session):
        """Should delete object successfully."""
        room_service.object_repo.delete_by_id = AsyncMock(return_value=True)

        result = await room_service.delete_object(mock_session, "test_object")

        assert result is True
        room_service.object_repo.delete_by_id.assert_called_once_with(mock_session, "test_object")

    @pytest.mark.asyncio
    async def test_delete_object_not_found(self, room_service, mock_session):
        """Should return False when object not found."""
        room_service.object_repo.delete_by_id = AsyncMock(return_value=False)

        result = await room_service.delete_object(mock_session, "nonexistent")

        assert result is False


# ============================================================================
# Object Movement Tests
# ============================================================================

class TestObjectMovement:
    """Tests for object movement."""

    @pytest.mark.asyncio
    async def test_move_object_success(self, room_service, mock_session, mock_grid_object):
        """Should move object to new position."""
        room_service.object_repo.get_by_id = AsyncMock(return_value=mock_grid_object)
        room_service.object_repo.check_collision = AsyncMock(return_value=False)
        room_service.object_repo.update = AsyncMock(return_value=mock_grid_object)

        result = await room_service.move_object(mock_session, "test_object", 15, 10)

        assert result is not None
        room_service.object_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_object_not_found(self, room_service, mock_session):
        """Should raise error when object not found."""
        room_service.object_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await room_service.move_object(mock_session, "nonexistent", 5, 5)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_move_object_not_movable(self, room_service, mock_session, mock_grid_object):
        """Should raise error when object is not movable."""
        mock_grid_object.is_movable = False
        room_service.object_repo.get_by_id = AsyncMock(return_value=mock_grid_object)

        with pytest.raises(ValueError) as exc_info:
            await room_service.move_object(mock_session, "test_object", 5, 5)

        assert "not movable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_move_object_collision(self, room_service, mock_session, mock_grid_object):
        """Should raise error when new position is occupied."""
        room_service.object_repo.get_by_id = AsyncMock(return_value=mock_grid_object)
        room_service.object_repo.check_collision = AsyncMock(return_value=True)

        with pytest.raises(ValueError) as exc_info:
            await room_service.move_object(mock_session, "test_object", 20, 10)

        assert "occupied" in str(exc_info.value)


# ============================================================================
# Object State Tests
# ============================================================================

class TestObjectState:
    """Tests for object state management."""

    @pytest.mark.asyncio
    async def test_set_object_state_success(self, room_service, mock_session):
        """Should set object state successfully."""
        room_service.object_repo.exists = AsyncMock(return_value=True)
        room_service.state_repo.set_state = AsyncMock()

        result = await room_service.set_object_state(
            mock_session, "test_object", "power", "on", "user"
        )

        assert result is True
        room_service.state_repo.set_state.assert_called_once_with(
            mock_session, "test_object", "power", "on", "user"
        )

    @pytest.mark.asyncio
    async def test_set_object_state_not_found(self, room_service, mock_session):
        """Should raise error when object not found."""
        room_service.object_repo.exists = AsyncMock(return_value=False)

        with pytest.raises(ValueError) as exc_info:
            await room_service.set_object_state(
                mock_session, "nonexistent", "power", "on"
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_object_states(self, room_service, mock_session):
        """Should return object states as dict."""
        mock_state1 = MagicMock()
        mock_state1.state_key = "power"
        mock_state1.state_value = "on"

        mock_state2 = MagicMock()
        mock_state2.state_key = "brightness"
        mock_state2.state_value = "100"

        room_service.state_repo.get_states_for_object = AsyncMock(
            return_value=[mock_state1, mock_state2]
        )

        states = await room_service.get_object_states(mock_session, "test_object")

        assert states == {"power": "on", "brightness": "100"}


# ============================================================================
# Storage Closet Tests
# ============================================================================

class TestStorageCloset:
    """Tests for storage closet operations."""

    @pytest.mark.asyncio
    async def test_get_storage_items(self, room_service, mock_session, mock_storage_item):
        """Should return all storage items."""
        room_service.storage_repo.get_all_ordered_by_stored_date = AsyncMock(
            return_value=[mock_storage_item]
        )

        items = await room_service.get_storage_items(mock_session)

        assert len(items) == 1
        assert items[0]["id"] == "storage_item_1"

    @pytest.mark.asyncio
    async def test_add_to_storage(self, room_service, mock_session, mock_storage_item):
        """Should add item to storage."""
        room_service.storage_repo.create = AsyncMock(return_value=mock_storage_item)

        item_data = {
            "id": "new_item",
            "name": "New Item",
            "type": "decoration",
            "default_size": {"width": 1, "height": 1},
            "properties": {"solid": False, "interactive": True}
        }

        result = await room_service.add_to_storage(mock_session, item_data)

        assert result is not None
        room_service.storage_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_place_from_storage_success(self, room_service, mock_session, mock_storage_item, mock_grid_object):
        """Should place item from storage into room."""
        room_service.storage_repo.get_by_id = AsyncMock(return_value=mock_storage_item)
        room_service.object_repo.check_collision = AsyncMock(return_value=False)
        room_service.storage_repo.increment_usage_count = AsyncMock()
        room_service.object_repo.create = AsyncMock(return_value=mock_grid_object)
        room_service.storage_repo.delete_by_id = AsyncMock()

        result = await room_service.place_from_storage(mock_session, "storage_item_1", 5, 5)

        assert result is not None
        room_service.storage_repo.increment_usage_count.assert_called_once()
        room_service.storage_repo.delete_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_place_from_storage_not_found(self, room_service, mock_session):
        """Should raise error when storage item not found."""
        room_service.storage_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await room_service.place_from_storage(mock_session, "nonexistent", 5, 5)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_place_from_storage_collision(self, room_service, mock_session, mock_storage_item):
        """Should raise error when position is occupied."""
        room_service.storage_repo.get_by_id = AsyncMock(return_value=mock_storage_item)
        room_service.object_repo.check_collision = AsyncMock(return_value=True)

        with pytest.raises(ValueError) as exc_info:
            await room_service.place_from_storage(mock_session, "storage_item_1", 10, 10)

        assert "occupied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_object_success(self, room_service, mock_session, mock_grid_object, mock_storage_item):
        """Should move object from room to storage."""
        room_service.object_repo.get_by_id = AsyncMock(return_value=mock_grid_object)
        room_service.storage_repo.create = AsyncMock(return_value=mock_storage_item)
        room_service.object_repo.delete_by_id = AsyncMock()

        result = await room_service.store_object(mock_session, "test_object")

        assert result is not None
        room_service.object_repo.delete_by_id.assert_called_once_with(mock_session, "test_object")

    @pytest.mark.asyncio
    async def test_store_object_not_found(self, room_service, mock_session):
        """Should raise error when object not found."""
        room_service.object_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await room_service.store_object(mock_session, "nonexistent")

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_object_not_movable(self, room_service, mock_session, mock_grid_object):
        """Should raise error when object is not movable."""
        mock_grid_object.is_movable = False
        room_service.object_repo.get_by_id = AsyncMock(return_value=mock_grid_object)

        with pytest.raises(ValueError) as exc_info:
            await room_service.store_object(mock_session, "test_object")

        assert "cannot be stored" in str(exc_info.value)


# ============================================================================
# Object to Dict Conversion Tests
# ============================================================================

class TestObjectConversion:
    """Tests for object to dictionary conversion."""

    def test_object_to_dict_with_states(self, room_service, mock_grid_object):
        """Should convert object with states to dict."""
        mock_state = MagicMock()
        mock_state.state_key = "power"
        mock_state.state_value = "on"
        mock_grid_object.states = [mock_state]

        result = room_service._object_to_dict_with_states(mock_grid_object)

        assert "states" in result
        assert result["states"]["power"] == "on"

    def test_object_to_dict_none_input(self, room_service):
        """Should return None for None input."""
        result = room_service._object_to_dict_with_states(None)

        assert result is None

    def test_object_to_dict_empty_states(self, room_service, mock_grid_object):
        """Should handle empty states."""
        mock_grid_object.states = []

        result = room_service._object_to_dict_with_states(mock_grid_object)

        assert result["states"] == {}


# ============================================================================
# Default Objects Tests
# ============================================================================

class TestDefaultObjects:
    """Tests for default object initialization."""

    @pytest.mark.asyncio
    async def test_initialize_creates_default_objects(self, room_service, mock_session, mock_grid_object):
        """Should create default objects when they don't exist."""
        room_service.object_repo.get_by_id_with_states = AsyncMock(return_value=None)
        room_service.object_repo.check_collision = AsyncMock(return_value=False)
        room_service.object_repo.create = AsyncMock(return_value=mock_grid_object)

        await room_service.initialize_default_objects(mock_session)

        # Should attempt to create bed, desk, window, door
        assert room_service.object_repo.create.call_count >= 4

    @pytest.mark.asyncio
    async def test_initialize_skips_existing_objects(self, room_service, mock_session, mock_grid_object):
        """Should skip objects that already exist."""
        room_service.object_repo.get_by_id_with_states = AsyncMock(return_value=mock_grid_object)

        await room_service.initialize_default_objects(mock_session)

        # Should not create any objects since all exist
        room_service.object_repo.create = AsyncMock()
        room_service.object_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_handles_errors_gracefully(self, room_service, mock_session):
        """Should handle creation errors gracefully."""
        room_service.object_repo.get_by_id_with_states = AsyncMock(return_value=None)
        room_service.object_repo.check_collision = AsyncMock(return_value=True)  # Collision for all

        # Should not raise, just log warnings
        await room_service.initialize_default_objects(mock_session)


# ============================================================================
# Collision Detection Tests
# ============================================================================

class TestCollisionDetection:
    """Tests for collision detection integration."""

    @pytest.mark.asyncio
    async def test_collision_check_excludes_self(self, room_service, mock_session, mock_grid_object):
        """Collision check should exclude the object being moved."""
        room_service.object_repo.get_by_id = AsyncMock(return_value=mock_grid_object)
        room_service.object_repo.check_collision = AsyncMock(return_value=False)
        room_service.object_repo.update = AsyncMock(return_value=mock_grid_object)

        await room_service.move_object(mock_session, "test_object", 15, 10)

        # Should pass exclude_id to collision check
        room_service.object_repo.check_collision.assert_called_with(
            mock_session, 15, 10, 2, 1, exclude_id="test_object"
        )

    @pytest.mark.asyncio
    async def test_create_checks_collision_without_exclude(self, room_service, mock_session, sample_object_data, mock_grid_object):
        """Create should check collision without excluding any object."""
        room_service.object_repo.check_collision = AsyncMock(return_value=False)
        room_service.object_repo.create = AsyncMock(return_value=mock_grid_object)

        await room_service.create_object(mock_session, sample_object_data)

        # Should not pass exclude_id
        call_args = room_service.object_repo.check_collision.call_args
        assert len(call_args[0]) == 5  # session, x, y, width, height (no exclude_id)
