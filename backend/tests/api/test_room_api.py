"""
Tests for Room API endpoints.

Tests cover:
- GET /room/objects - Get all room objects
- GET /room/objects/{object_id} - Get specific object
- POST /room/objects - Create new object
- PUT /room/objects/{object_id}/move - Move object
- DELETE /room/objects/{object_id} - Delete object
- PUT /room/objects/{object_id}/state - Set object state
- GET /room/objects/{object_id}/states - Get object states
- GET /room/storage - Get storage items
- POST /room/storage - Add to storage
- POST /room/storage/{item_id}/place - Place from storage
- POST /room/objects/{object_id}/store - Store object
- POST /room/initialize - Initialize room
- GET /room/layout - Get room layout
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_room_object():
    """Create a mock room object."""
    return {
        "id": "desk_001",
        "name": "Desk",
        "object_type": "furniture",
        "position_x": 10,
        "position_y": 8,
        "size_width": 3,
        "size_height": 2,
        "is_solid": True,
        "is_movable": False,
        "states": {"power": "off"}
    }


@pytest.fixture
def mock_storage_item():
    """Create a mock storage item."""
    return {
        "id": "lamp_storage_001",
        "name": "Table Lamp",
        "object_type": "decoration",
        "in_storage": True,
        "size_width": 1,
        "size_height": 1
    }


# ============================================================================
# GET /room/objects Tests
# ============================================================================

class TestGetRoomObjects:
    """Tests for GET /room/objects endpoint."""

    @pytest.mark.asyncio
    async def test_get_objects_success(self, client, mock_room_object):
        """Should return all room objects."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_all_objects = AsyncMock(return_value=[mock_room_object])

            response = await client.get("/room/objects")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "desk_001"

    @pytest.mark.asyncio
    async def test_get_objects_empty(self, client):
        """Should return empty list when no objects."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_all_objects = AsyncMock(return_value=[])

            response = await client.get("/room/objects")

            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_objects_error_handling(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_all_objects = AsyncMock(side_effect=Exception("DB error"))

            response = await client.get("/room/objects")

            assert response.status_code == 500


# ============================================================================
# GET /room/objects/{object_id} Tests
# ============================================================================

class TestGetObject:
    """Tests for GET /room/objects/{object_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_object_success(self, client, mock_room_object):
        """Should return specific object."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_object_by_id = AsyncMock(return_value=mock_room_object)

            response = await client.get("/room/objects/desk_001")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "desk_001"
            assert data["name"] == "Desk"

    @pytest.mark.asyncio
    async def test_get_object_not_found(self, client):
        """Should return 404 for nonexistent object."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_object_by_id = AsyncMock(return_value=None)

            response = await client.get("/room/objects/nonexistent")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_object_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_object_by_id = AsyncMock(side_effect=Exception("DB error"))

            response = await client.get("/room/objects/desk_001")

            assert response.status_code == 500


# ============================================================================
# POST /room/objects Tests
# ============================================================================

class TestCreateObject:
    """Tests for POST /room/objects endpoint."""

    @pytest.mark.asyncio
    async def test_create_object_success(self, client, mock_room_object):
        """Should create new object."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.create_object = AsyncMock(return_value=mock_room_object)

            response = await client.post(
                "/room/objects",
                json={
                    "name": "Desk",
                    "object_type": "furniture",
                    "position_x": 10,
                    "position_y": 8
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Desk"

    @pytest.mark.asyncio
    async def test_create_object_invalid_data(self, client):
        """Should return 400 for invalid data."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.create_object = AsyncMock(
                side_effect=ValueError("Invalid object data")
            )

            response = await client.post(
                "/room/objects",
                json={"name": ""}
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_object_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.create_object = AsyncMock(side_effect=Exception("DB error"))

            response = await client.post(
                "/room/objects",
                json={"name": "Test"}
            )

            assert response.status_code == 500


# ============================================================================
# PUT /room/objects/{object_id}/move Tests
# ============================================================================

class TestMoveObject:
    """Tests for PUT /room/objects/{object_id}/move endpoint."""

    @pytest.mark.asyncio
    async def test_move_object_success(self, client, mock_room_object):
        """Should move object to new position."""
        mock_room_object["position_x"] = 15
        mock_room_object["position_y"] = 10

        with patch('app.api.room.room_service') as mock_service:
            mock_service.move_object = AsyncMock(return_value=mock_room_object)

            response = await client.put(
                "/room/objects/desk_001/move",
                json={"x": 15, "y": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["position_x"] == 15
            assert data["position_y"] == 10

    @pytest.mark.asyncio
    async def test_move_object_missing_coordinates(self, client):
        """Should return 400 when coordinates missing."""
        response = await client.put(
            "/room/objects/desk_001/move",
            json={"x": 15}  # Missing y
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_move_object_collision(self, client):
        """Should return 400 for collision."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.move_object = AsyncMock(
                side_effect=ValueError("Position blocked by another object")
            )

            response = await client.put(
                "/room/objects/desk_001/move",
                json={"x": 10, "y": 10}
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_move_object_out_of_bounds(self, client):
        """Should return 400 for out of bounds."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.move_object = AsyncMock(
                side_effect=ValueError("Position out of bounds")
            )

            response = await client.put(
                "/room/objects/desk_001/move",
                json={"x": 100, "y": 100}
            )

            assert response.status_code == 400


# ============================================================================
# DELETE /room/objects/{object_id} Tests
# ============================================================================

class TestDeleteObject:
    """Tests for DELETE /room/objects/{object_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_object_success(self, client):
        """Should delete object successfully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.delete_object = AsyncMock(return_value=True)

            response = await client.delete("/room/objects/desk_001")

            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_delete_object_not_found(self, client):
        """Should return 404 for nonexistent object."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.delete_object = AsyncMock(return_value=False)

            response = await client.delete("/room/objects/nonexistent")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_object_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.delete_object = AsyncMock(side_effect=Exception("DB error"))

            response = await client.delete("/room/objects/desk_001")

            assert response.status_code == 500


# ============================================================================
# PUT /room/objects/{object_id}/state Tests
# ============================================================================

class TestSetObjectState:
    """Tests for PUT /room/objects/{object_id}/state endpoint."""

    @pytest.mark.asyncio
    async def test_set_state_success(self, client):
        """Should set object state."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.set_object_state = AsyncMock(return_value=True)

            response = await client.put(
                "/room/objects/lamp_001/state",
                json={"key": "power", "value": "on"}
            )

            assert response.status_code == 200
            assert "updated" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_set_state_with_updated_by(self, client):
        """Should accept updated_by parameter."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.set_object_state = AsyncMock(return_value=True)

            response = await client.put(
                "/room/objects/lamp_001/state",
                json={"key": "power", "value": "on", "updated_by": "assistant"}
            )

            assert response.status_code == 200
            mock_service.set_object_state.assert_called_once()
            call_args = mock_service.set_object_state.call_args
            assert call_args[0][4] == "assistant"

    @pytest.mark.asyncio
    async def test_set_state_missing_key(self, client):
        """Should return 400 when key missing."""
        response = await client.put(
            "/room/objects/lamp_001/state",
            json={"value": "on"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_set_state_missing_value(self, client):
        """Should return 400 when value missing."""
        response = await client.put(
            "/room/objects/lamp_001/state",
            json={"key": "power"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_set_state_failed(self, client):
        """Should return 400 when update fails."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.set_object_state = AsyncMock(return_value=False)

            response = await client.put(
                "/room/objects/lamp_001/state",
                json={"key": "power", "value": "on"}
            )

            assert response.status_code == 400


# ============================================================================
# GET /room/objects/{object_id}/states Tests
# ============================================================================

class TestGetObjectStates:
    """Tests for GET /room/objects/{object_id}/states endpoint."""

    @pytest.mark.asyncio
    async def test_get_states_success(self, client):
        """Should return object states."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_object_states = AsyncMock(return_value={
                "power": "off",
                "brightness": "50"
            })

            response = await client.get("/room/objects/lamp_001/states")

            assert response.status_code == 200
            data = response.json()
            assert data["power"] == "off"
            assert data["brightness"] == "50"

    @pytest.mark.asyncio
    async def test_get_states_empty(self, client):
        """Should return empty dict when no states."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_object_states = AsyncMock(return_value={})

            response = await client.get("/room/objects/desk_001/states")

            assert response.status_code == 200
            assert response.json() == {}


# ============================================================================
# GET /room/storage Tests
# ============================================================================

class TestGetStorageItems:
    """Tests for GET /room/storage endpoint."""

    @pytest.mark.asyncio
    async def test_get_storage_success(self, client, mock_storage_item):
        """Should return storage items."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_storage_items = AsyncMock(return_value=[mock_storage_item])

            response = await client.get("/room/storage")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["in_storage"] is True

    @pytest.mark.asyncio
    async def test_get_storage_empty(self, client):
        """Should return empty list when storage empty."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.get_storage_items = AsyncMock(return_value=[])

            response = await client.get("/room/storage")

            assert response.status_code == 200
            assert response.json() == []


# ============================================================================
# POST /room/storage Tests
# ============================================================================

class TestAddToStorage:
    """Tests for POST /room/storage endpoint."""

    @pytest.mark.asyncio
    async def test_add_to_storage_success(self, client, mock_storage_item):
        """Should add item to storage."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.add_to_storage = AsyncMock(return_value=mock_storage_item)

            response = await client.post(
                "/room/storage",
                json={"name": "Table Lamp", "object_type": "decoration"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Table Lamp"

    @pytest.mark.asyncio
    async def test_add_to_storage_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.add_to_storage = AsyncMock(side_effect=Exception("DB error"))

            response = await client.post(
                "/room/storage",
                json={"name": "Test Item"}
            )

            assert response.status_code == 500


# ============================================================================
# POST /room/storage/{item_id}/place Tests
# ============================================================================

class TestPlaceFromStorage:
    """Tests for POST /room/storage/{item_id}/place endpoint."""

    @pytest.mark.asyncio
    async def test_place_success(self, client, mock_room_object):
        """Should place item from storage."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.place_from_storage = AsyncMock(return_value=mock_room_object)

            response = await client.post(
                "/room/storage/lamp_001/place",
                json={"x": 20, "y": 5}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_place_missing_coordinates(self, client):
        """Should return 400 when coordinates missing."""
        response = await client.post(
            "/room/storage/lamp_001/place",
            json={"x": 20}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_place_collision(self, client):
        """Should return 400 for collision."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.place_from_storage = AsyncMock(
                side_effect=ValueError("Position already occupied")
            )

            response = await client.post(
                "/room/storage/lamp_001/place",
                json={"x": 10, "y": 8}
            )

            assert response.status_code == 400


# ============================================================================
# POST /room/objects/{object_id}/store Tests
# ============================================================================

class TestStoreObject:
    """Tests for POST /room/objects/{object_id}/store endpoint."""

    @pytest.mark.asyncio
    async def test_store_object_success(self, client, mock_storage_item):
        """Should store object in storage."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.store_object = AsyncMock(return_value=mock_storage_item)

            response = await client.post("/room/objects/lamp_001/store")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_store_object_not_movable(self, client):
        """Should return 400 for non-movable objects."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.store_object = AsyncMock(
                side_effect=ValueError("Object is not movable")
            )

            response = await client.post("/room/objects/wall_001/store")

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_store_object_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.store_object = AsyncMock(side_effect=Exception("DB error"))

            response = await client.post("/room/objects/lamp_001/store")

            assert response.status_code == 500


# ============================================================================
# POST /room/initialize Tests
# ============================================================================

class TestInitializeRoom:
    """Tests for POST /room/initialize endpoint."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, client):
        """Should initialize room."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.initialize_default_objects = AsyncMock()

            response = await client.post("/room/initialize")

            assert response.status_code == 200
            assert "initialized" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_initialize_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.room.room_service') as mock_service:
            mock_service.initialize_default_objects = AsyncMock(
                side_effect=Exception("Init error")
            )

            response = await client.post("/room/initialize")

            assert response.status_code == 500


# ============================================================================
# GET /room/layout Tests
# ============================================================================

class TestGetRoomLayout:
    """Tests for GET /room/layout endpoint."""

    @pytest.mark.asyncio
    async def test_get_layout_success(self, client):
        """Should return room layout."""
        response = await client.get("/room/layout")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "grid_size" in data
        assert data["grid_size"]["width"] == 64
        assert data["grid_size"]["height"] == 16

    @pytest.mark.asyncio
    async def test_get_layout_has_theme(self, client):
        """Should include theme information."""
        response = await client.get("/room/layout")

        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "background" in data["theme"]
        assert "grid" in data["theme"]

