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
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class RoomService:
    """Service for managing room objects and spatial interactions."""

    def __init__(self):
        self.current_layout_id = "default"

    async def get_db_session(self) -> AsyncSession:
        """Get a database session."""
        return AsyncSessionLocal()

    # Object Management
    async def get_all_objects(self) -> List[Dict[str, Any]]:
        """Get all objects currently in the room."""
        async with await self.get_db_session() as session:
            stmt = select(GridObject).options(selectinload(GridObject.states))
            result = await session.execute(stmt)
            objects = result.scalars().all()

            return [self._object_to_dict_with_states(obj) for obj in objects]

    async def get_object_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific object by ID."""
        async with await self.get_db_session() as session:
            stmt = select(GridObject).options(selectinload(GridObject.states)).where(GridObject.id == object_id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()

            return self._object_to_dict_with_states(obj) if obj else None

    async def create_object(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new object in the room."""
        async with await self.get_db_session() as session:
            # Check for collision
            position = object_data["position"]
            size = object_data["size"]

            if await self._check_collision(session, position["x"], position["y"], size["width"], size["height"]):
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

            session.add(obj)
            await session.commit()
            await session.refresh(obj)

            logger.info(f"Created object {obj.id} at ({obj.position_x}, {obj.position_y})")
            return obj.to_dict()

    async def move_object(self, object_id: str, new_x: int, new_y: int) -> Dict[str, Any]:
        """Move an object to a new position."""
        async with await self.get_db_session() as session:
            # Get object
            stmt = select(GridObject).where(GridObject.id == object_id)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()

            if not obj:
                raise ValueError(f"Object {object_id} not found")

            if not obj.is_movable:
                raise ValueError(f"Object {object_id} is not movable")

            # Check collision at new position
            if await self._check_collision(session, new_x, new_y, obj.size_width, obj.size_height, exclude_id=object_id):
                raise ValueError(f"Position ({new_x}, {new_y}) is occupied")

            # Update position
            obj.position_x = new_x
            obj.position_y = new_y
            obj.last_moved_at = func.now()

            await session.commit()
            await session.refresh(obj)

            logger.info(f"Moved object {object_id} to ({new_x}, {new_y})")
            return obj.to_dict()

    async def delete_object(self, object_id: str) -> bool:
        """Remove an object from the room."""
        async with await self.get_db_session() as session:
            stmt = delete(GridObject).where(GridObject.id == object_id)
            result = await session.execute(stmt)
            await session.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted object {object_id}")
            return deleted

    # Object State Management
    async def set_object_state(self, object_id: str, state_key: str, state_value: str, updated_by: str = "user") -> bool:
        """Set or update an object's state."""
        async with await self.get_db_session() as session:
            # Check if object exists
            obj_stmt = select(GridObject).where(GridObject.id == object_id)
            obj_result = await session.execute(obj_stmt)
            if not obj_result.scalar_one_or_none():
                raise ValueError(f"Object {object_id} not found")

            # Check if state already exists
            state_stmt = select(ObjectState).where(
                ObjectState.object_id == object_id,
                ObjectState.state_key == state_key
            )
            state_result = await session.execute(state_stmt)
            existing_state = state_result.scalar_one_or_none()

            if existing_state:
                # Update existing state
                existing_state.state_value = state_value
                existing_state.updated_by = updated_by
            else:
                # Create new state
                new_state = ObjectState(
                    object_id=object_id,
                    state_key=state_key,
                    state_value=state_value,
                    updated_by=updated_by
                )
                session.add(new_state)

            await session.commit()
            logger.info(f"Set {object_id}.{state_key} = {state_value}")
            return True

    async def get_object_states(self, object_id: str) -> Dict[str, str]:
        """Get all states for an object."""
        async with await self.get_db_session() as session:
            stmt = select(ObjectState).where(ObjectState.object_id == object_id)
            result = await session.execute(stmt)
            states = result.scalars().all()

            return {state.state_key: state.state_value for state in states}

    # Storage Closet Management
    async def get_storage_items(self) -> List[Dict[str, Any]]:
        """Get all items in storage closet."""
        async with await self.get_db_session() as session:
            stmt = select(StorageItem).order_by(StorageItem.stored_at.desc())
            result = await session.execute(stmt)
            items = result.scalars().all()

            return [item.to_dict() for item in items]

    async def add_to_storage(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to storage closet."""
        async with await self.get_db_session() as session:
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

            session.add(item)
            await session.commit()
            await session.refresh(item)

            logger.info(f"Added {item.id} to storage")
            return item.to_dict()

    async def place_from_storage(self, item_id: str, x: int, y: int) -> Dict[str, Any]:
        """Place an item from storage into the room."""
        async with await self.get_db_session() as session:
            # Get storage item
            storage_stmt = select(StorageItem).where(StorageItem.id == item_id)
            storage_result = await session.execute(storage_stmt)
            storage_item = storage_result.scalar_one_or_none()

            if not storage_item:
                raise ValueError(f"Storage item {item_id} not found")

            # Check collision
            if await self._check_collision(session, x, y, storage_item.default_size_width, storage_item.default_size_height):
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
            storage_item.usage_count += 1
            session.add(grid_obj)
            await session.delete(storage_item)

            await session.commit()
            await session.refresh(grid_obj)

            logger.info(f"Placed {item_id} from storage at ({x}, {y})")
            return grid_obj.to_dict()

    async def store_object(self, object_id: str) -> Dict[str, Any]:
        """Move an object from the room to storage."""
        async with await self.get_db_session() as session:
            # Get object
            obj_stmt = select(GridObject).where(GridObject.id == object_id)
            obj_result = await session.execute(obj_stmt)
            obj = obj_result.scalar_one_or_none()

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
            session.add(storage_item)
            await session.delete(obj)

            await session.commit()
            await session.refresh(storage_item)

            logger.info(f"Stored object {object_id}")
            return storage_item.to_dict()

    # Collision Detection
    async def _check_collision(self, session: AsyncSession, x: int, y: int, width: int, height: int, exclude_id: Optional[str] = None) -> bool:
        """Check if position collides with existing objects."""
        stmt = select(GridObject)
        if exclude_id:
            stmt = stmt.where(GridObject.id != exclude_id)

        result = await session.execute(stmt)
        objects = result.scalars().all()

        for obj in objects:
            # Check if rectangles overlap
            if (x < obj.position_x + obj.size_width and
                x + width > obj.position_x and
                y < obj.position_y + obj.size_height and
                y + height > obj.position_y and
                obj.is_solid):
                return True

        return False

    def _object_to_dict_with_states(self, obj: GridObject) -> Dict[str, Any]:
        """Convert object to dict including states."""
        if not obj:
            return None

        result = obj.to_dict()
        result["states"] = {state.state_key: state.state_value for state in obj.states}
        return result

    # Initialize default objects
    async def initialize_default_objects(self):
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
                existing = await self.get_object_by_id(obj_data["id"])
                if not existing:
                    await self.create_object(obj_data)
                    logger.info(f"Created default object: {obj_data['id']}")
            except Exception as e:
                logger.warning(f"Could not create default object {obj_data['id']}: {e}")


# Global service instance
room_service = RoomService()