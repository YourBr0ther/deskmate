"""
Repository for room-related database operations.

This module provides:
- Object management operations
- Spatial queries and collision detection
- Storage operations
- State management
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.orm import selectinload

from app.models.room_objects import GridObject, ObjectState, StorageItem
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RoomObjectRepository(BaseRepository[GridObject]):
    """Repository for room object operations."""

    def __init__(self):
        super().__init__(GridObject)

    async def get_all_with_states(self, session: AsyncSession) -> List[GridObject]:
        """Get all objects with their states eagerly loaded."""
        return await self.get_all(session, load_relationships=["states"])

    async def get_by_id_with_states(self, session: AsyncSession, object_id: str) -> Optional[GridObject]:
        """Get object by ID with states eagerly loaded."""
        return await self.get_by_id(session, object_id, load_relationships=["states"])

    async def check_collision(
        self,
        session: AsyncSession,
        x: int,
        y: int,
        width: int,
        height: int,
        exclude_id: Optional[str] = None
    ) -> bool:
        """
        Check if position collides with existing solid objects.

        Args:
            session: Database session
            x: X coordinate
            y: Y coordinate
            width: Object width
            height: Object height
            exclude_id: Object ID to exclude from collision check

        Returns:
            True if collision detected, False otherwise
        """
        try:
            stmt = select(GridObject).where(GridObject.is_solid == True)

            if exclude_id:
                stmt = stmt.where(GridObject.id != exclude_id)

            result = await session.execute(stmt)
            objects = result.scalars().all()

            for obj in objects:
                # Check if rectangles overlap
                if (x < obj.position_x + obj.size_width and
                    x + width > obj.position_x and
                    y < obj.position_y + obj.size_height and
                    y + height > obj.position_y):
                    logger.debug(f"Collision detected with object {obj.id} at ({obj.position_x}, {obj.position_y})")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking collision at ({x}, {y}): {e}")
            raise

    async def get_solid_objects(self, session: AsyncSession) -> List[GridObject]:
        """Get all solid objects for pathfinding."""
        try:
            stmt = select(GridObject).where(GridObject.is_solid == True)
            result = await session.execute(stmt)
            objects = result.scalars().all()

            logger.debug(f"Retrieved {len(objects)} solid objects")
            return list(objects)

        except Exception as e:
            logger.error(f"Error getting solid objects: {e}")
            raise

    async def get_objects_by_type(self, session: AsyncSession, object_type: str) -> List[GridObject]:
        """Get all objects of a specific type."""
        try:
            stmt = select(GridObject).where(GridObject.object_type == object_type)
            result = await session.execute(stmt)
            objects = result.scalars().all()

            logger.debug(f"Retrieved {len(objects)} objects of type {object_type}")
            return list(objects)

        except Exception as e:
            logger.error(f"Error getting objects by type {object_type}: {e}")
            raise

    async def get_movable_objects(self, session: AsyncSession) -> List[GridObject]:
        """Get all movable objects."""
        try:
            stmt = select(GridObject).where(GridObject.is_movable == True)
            result = await session.execute(stmt)
            objects = result.scalars().all()

            logger.debug(f"Retrieved {len(objects)} movable objects")
            return list(objects)

        except Exception as e:
            logger.error(f"Error getting movable objects: {e}")
            raise


class ObjectStateRepository(BaseRepository[ObjectState]):
    """Repository for object state operations."""

    def __init__(self):
        super().__init__(ObjectState)

    async def get_states_for_object(self, session: AsyncSession, object_id: str) -> List[ObjectState]:
        """Get all states for a specific object."""
        try:
            stmt = select(ObjectState).where(ObjectState.object_id == object_id)
            result = await session.execute(stmt)
            states = result.scalars().all()

            logger.debug(f"Retrieved {len(states)} states for object {object_id}")
            return list(states)

        except Exception as e:
            logger.error(f"Error getting states for object {object_id}: {e}")
            raise

    async def get_state(
        self,
        session: AsyncSession,
        object_id: str,
        state_key: str
    ) -> Optional[ObjectState]:
        """Get a specific state for an object."""
        try:
            stmt = select(ObjectState).where(
                and_(
                    ObjectState.object_id == object_id,
                    ObjectState.state_key == state_key
                )
            )
            result = await session.execute(stmt)
            state = result.scalar_one_or_none()

            return state

        except Exception as e:
            logger.error(f"Error getting state {state_key} for object {object_id}: {e}")
            raise

    async def set_state(
        self,
        session: AsyncSession,
        object_id: str,
        state_key: str,
        state_value: str,
        updated_by: str = "user"
    ) -> ObjectState:
        """Set or update an object's state."""
        try:
            # Check if state already exists
            existing_state = await self.get_state(session, object_id, state_key)

            if existing_state:
                # Update existing state
                existing_state.state_value = state_value
                existing_state.updated_by = updated_by
                return await self.update(session, existing_state)
            else:
                # Create new state
                new_state = ObjectState(
                    object_id=object_id,
                    state_key=state_key,
                    state_value=state_value,
                    updated_by=updated_by
                )
                return await self.create(session, new_state)

        except Exception as e:
            logger.error(f"Error setting state {state_key}={state_value} for object {object_id}: {e}")
            raise


class StorageItemRepository(BaseRepository[StorageItem]):
    """Repository for storage item operations."""

    def __init__(self):
        super().__init__(StorageItem)

    async def get_all_ordered_by_stored_date(self, session: AsyncSession) -> List[StorageItem]:
        """Get all storage items ordered by storage date (newest first)."""
        try:
            stmt = select(StorageItem).order_by(StorageItem.stored_at.desc())
            result = await session.execute(stmt)
            items = result.scalars().all()

            logger.debug(f"Retrieved {len(items)} storage items")
            return list(items)

        except Exception as e:
            logger.error(f"Error getting storage items: {e}")
            raise

    async def increment_usage_count(self, session: AsyncSession, item_id: str) -> Optional[StorageItem]:
        """Increment the usage count for a storage item."""
        try:
            item = await self.get_by_id(session, item_id)
            if item:
                item.usage_count += 1
                return await self.update(session, item)
            return None

        except Exception as e:
            logger.error(f"Error incrementing usage count for item {item_id}: {e}")
            raise