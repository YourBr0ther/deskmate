"""
Room service for managing objects, storage, and spatial data.

This service handles:
- Object placement and movement
- Storage closet operations
- Object state changes
- Collision detection
- Database persistence
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload

from app.models.room_objects import GridObject, ObjectState, StorageItem, RoomLayout
from app.repositories.room_repository import (
    RoomObjectRepository,
    ObjectStateRepository,
    StorageItemRepository
)

logger = logging.getLogger(__name__)


class RoomService:
    """Service for managing room objects and spatial interactions."""

    def __init__(self):
        self.current_layout_id = "default"
        self.object_repo = RoomObjectRepository()
        self.state_repo = ObjectStateRepository()
        self.storage_repo = StorageItemRepository()

    # Object Management
    async def get_all_objects(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get all objects currently in the room."""
        objects = await self.object_repo.get_all_with_states(session)
        return [self._object_to_dict_with_states(obj) for obj in objects]

    async def get_object_by_id(self, session: AsyncSession, object_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific object by ID."""
        obj = await self.object_repo.get_by_id_with_states(session, object_id)
        return self._object_to_dict_with_states(obj) if obj else None

    async def create_object(self, session: AsyncSession, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new object in the room."""
        # Check for collision
        position = object_data["position"]
        size = object_data["size"]

        if await self.object_repo.check_collision(session, position["x"], position["y"], size["width"], size["height"]):
            raise ValueError(f"Position ({position['x']}, {position['y']}) is occupied")

        # Create object
        obj = GridObject(
            id=object_data["id"],
            name=object_data["name"],
            description=object_data.get("description", ""),
            object_type=object_data["type"],
            position_x=position["x"],
            position_y=position["y"],
            size_width=size["width"],
            size_height=size["height"],
            is_solid=object_data.get("properties", {}).get("solid", True),
            is_interactive=object_data.get("properties", {}).get("interactive", True),
            is_movable=object_data.get("properties", {}).get("movable", False),
            sprite_name=object_data.get("sprite"),
            color_scheme=object_data.get("color"),
            created_by=object_data.get("created_by", "user")
        )

        created_obj = await self.object_repo.create(session, obj)
        logger.info(f"Created object {created_obj.id} at ({created_obj.position_x}, {created_obj.position_y})")
        return created_obj.to_dict()

    async def move_object(self, session: AsyncSession, object_id: str, new_x: int, new_y: int) -> Dict[str, Any]:
        """Move an object to a new position."""
        # Get object
        obj = await self.object_repo.get_by_id(session, object_id)

        if not obj:
            raise ValueError(f"Object {object_id} not found")

        if not obj.is_movable:
            raise ValueError(f"Object {object_id} is not movable")

        # Check collision at new position
        if await self.object_repo.check_collision(session, new_x, new_y, obj.size_width, obj.size_height, exclude_id=object_id):
            raise ValueError(f"Position ({new_x}, {new_y}) is occupied")

        # Update position
        obj.position_x = new_x
        obj.position_y = new_y
        obj.last_moved_at = func.now()

        updated_obj = await self.object_repo.update(session, obj)
        logger.info(f"Moved object {object_id} to ({new_x}, {new_y})")
        return updated_obj.to_dict()

    async def delete_object(self, session: AsyncSession, object_id: str) -> bool:
        """Remove an object from the room."""
        deleted = await self.object_repo.delete_by_id(session, object_id)
        if deleted:
            logger.info(f"Deleted object {object_id}")
        return deleted

    # Object State Management
    async def set_object_state(self, session: AsyncSession, object_id: str, state_key: str, state_value: str, updated_by: str = "user") -> bool:
        """Set or update an object's state."""
        # Check if object exists
        if not await self.object_repo.exists(session, object_id):
            raise ValueError(f"Object {object_id} not found")

        # Set the state
        await self.state_repo.set_state(session, object_id, state_key, state_value, updated_by)
        logger.info(f"Set {object_id}.{state_key} = {state_value}")
        return True

    async def get_object_states(self, session: AsyncSession, object_id: str) -> Dict[str, str]:
        """Get all states for an object."""
        states = await self.state_repo.get_states_for_object(session, object_id)
        return {state.state_key: state.state_value for state in states}

    # Storage Closet Management
    async def get_storage_items(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get all items in storage closet."""
        items = await self.storage_repo.get_all_ordered_by_stored_date(session)
        return [item.to_dict() for item in items]

    async def add_to_storage(self, session: AsyncSession, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to storage closet."""
        item = StorageItem(
            id=item_data["id"],
            name=item_data["name"],
            description=item_data.get("description", ""),
            object_type=item_data["type"],
            default_size_width=item_data.get("default_size", {}).get("width", 1),
            default_size_height=item_data.get("default_size", {}).get("height", 1),
            is_solid=item_data.get("properties", {}).get("solid", True),
            is_interactive=item_data.get("properties", {}).get("interactive", True),
            sprite_name=item_data.get("sprite"),
            color_scheme=item_data.get("color"),
            created_by=item_data.get("created_by", "user")
        )

        created_item = await self.storage_repo.create(session, item)
        logger.info(f"Added {created_item.id} to storage")
        return created_item.to_dict()

    async def place_from_storage(self, session: AsyncSession, item_id: str, x: int, y: int) -> Dict[str, Any]:
        """Place an item from storage into the room."""
        # Get storage item
        storage_item = await self.storage_repo.get_by_id(session, item_id)

        if not storage_item:
            raise ValueError(f"Storage item {item_id} not found")

        # Check collision
        if await self.object_repo.check_collision(session, x, y, storage_item.default_size_width, storage_item.default_size_height):
            raise ValueError(f"Position ({x}, {y}) is occupied")

        # Create grid object from storage item
        grid_obj = GridObject(
            id=storage_item.id,
            name=storage_item.name,
            description=storage_item.description,
            object_type=storage_item.object_type,
            position_x=x,
            position_y=y,
            size_width=storage_item.default_size_width,
            size_height=storage_item.default_size_height,
            is_solid=storage_item.is_solid,
            is_interactive=storage_item.is_interactive,
            is_movable=True,  # Items from storage are always movable
            sprite_name=storage_item.sprite_name,
            color_scheme=storage_item.color_scheme,
            created_by=storage_item.created_by
        )

        # Update usage count and remove from storage
        await self.storage_repo.increment_usage_count(session, item_id)
        created_grid_obj = await self.object_repo.create(session, grid_obj)
        await self.storage_repo.delete_by_id(session, item_id)

        logger.info(f"Placed {item_id} from storage at ({x}, {y})")
        return created_grid_obj.to_dict()

    async def store_object(self, session: AsyncSession, object_id: str) -> Dict[str, Any]:
        """Move an object from the room to storage."""
        # Get object
        obj = await self.object_repo.get_by_id(session, object_id)

        if not obj:
            raise ValueError(f"Object {object_id} not found")

        if not obj.is_movable:
            raise ValueError(f"Object {object_id} cannot be stored")

        # Create storage item
        storage_item = StorageItem(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            object_type=obj.object_type,
            default_size_width=obj.size_width,
            default_size_height=obj.size_height,
            is_solid=obj.is_solid,
            is_interactive=obj.is_interactive,
            sprite_name=obj.sprite_name,
            color_scheme=obj.color_scheme,
            created_by=obj.created_by
        )

        # Remove from room and add to storage
        created_storage_item = await self.storage_repo.create(session, storage_item)
        await self.object_repo.delete_by_id(session, object_id)

        logger.info(f"Stored object {object_id}")
        return created_storage_item.to_dict()


    def _object_to_dict_with_states(self, obj: GridObject) -> Dict[str, Any]:
        """Convert object to dict including states."""
        if not obj:
            return None

        result = obj.to_dict()
        result["states"] = {state.state_key: state.state_value for state in obj.states}
        return result

    # Initialize default objects
    async def initialize_default_objects(self, session: AsyncSession):
        """Create the default hardcoded room objects."""
        default_objects = [
            {
                "id": "bed",
                "name": "Bed",
                "description": "A comfortable bed for sleeping",
                "type": "furniture",
                "position": {"x": 50, "y": 12},
                "size": {"width": 8, "height": 4},
                "properties": {"solid": True, "interactive": True, "movable": False},
                "color": "purple",
                "created_by": "system"
            },
            {
                "id": "desk",
                "name": "Desk",
                "description": "A wooden desk for working",
                "type": "furniture",
                "position": {"x": 10, "y": 2},
                "size": {"width": 6, "height": 3},
                "properties": {"solid": True, "interactive": True, "movable": False},
                "color": "orange",
                "created_by": "system"
            },
            {
                "id": "window",
                "name": "Window",
                "description": "A window overlooking the outside",
                "type": "furniture",
                "position": {"x": 30, "y": 0},
                "size": {"width": 8, "height": 1},
                "properties": {"solid": False, "interactive": True, "movable": False},
                "color": "blue",
                "created_by": "system"
            },
            {
                "id": "door",
                "name": "Door",
                "description": "The room entrance door",
                "type": "furniture",
                "position": {"x": 0, "y": 8},
                "size": {"width": 1, "height": 3},
                "properties": {"solid": False, "interactive": True, "movable": False},
                "color": "amber",
                "created_by": "system"
            }
        ]

        for obj_data in default_objects:
            try:
                existing = await self.get_object_by_id(session, obj_data["id"])
                if not existing:
                    await self.create_object(session, obj_data)
                    logger.info(f"Created default object: {obj_data['id']}")
            except Exception as e:
                logger.warning(f"Could not create default object {obj_data['id']}: {e}")


# Global service instance
room_service = RoomService()