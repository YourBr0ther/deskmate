"""
Base repository classes providing common database operations.

This module provides:
- Generic CRUD operations
- Transaction management
- Error handling patterns
- Query optimization
"""

import logging
from typing import Type, TypeVar, Generic, List, Optional, Dict, Any, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload

from app.db.base import Base

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """Base repository providing common database operations."""

    def __init__(self, model: Type[T]):
        self.model = model

    async def get_by_id(
        self,
        session: AsyncSession,
        id_value: Any,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Get a single entity by ID.

        Args:
            session: Database session
            id_value: Primary key value
            load_relationships: List of relationship attributes to eagerly load

        Returns:
            Entity instance or None if not found
        """
        try:
            stmt = select(self.model).where(self.model.id == id_value)

            if load_relationships:
                for rel in load_relationships:
                    stmt = stmt.options(selectinload(getattr(self.model, rel)))

            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

            if entity:
                logger.debug(f"Retrieved {self.model.__name__} with id {id_value}")

            return entity

        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id_value}: {e}")
            raise

    async def get_all(
        self,
        session: AsyncSession,
        load_relationships: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all entities with optional pagination.

        Args:
            session: Database session
            load_relationships: List of relationship attributes to eagerly load
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of entity instances
        """
        try:
            stmt = select(self.model)

            if load_relationships:
                for rel in load_relationships:
                    stmt = stmt.options(selectinload(getattr(self.model, rel)))

            if offset:
                stmt = stmt.offset(offset)

            if limit:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            entities = result.scalars().all()

            logger.debug(f"Retrieved {len(entities)} {self.model.__name__} entities")
            return list(entities)

        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise

    async def create(self, session: AsyncSession, entity: T) -> T:
        """
        Create a new entity.

        Args:
            session: Database session
            entity: Entity instance to create

        Returns:
            Created entity with updated fields (e.g., generated ID)
        """
        try:
            session.add(entity)
            await session.flush()  # Get ID without committing
            await session.refresh(entity)

            logger.debug(f"Created {self.model.__name__} with id {entity.id}")
            return entity

        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    async def create_from_dict(self, session: AsyncSession, data: Dict[str, Any]) -> T:
        """
        Create entity from dictionary data.

        Args:
            session: Database session
            data: Dictionary containing entity data

        Returns:
            Created entity
        """
        try:
            entity = self.model(**data)
            return await self.create(session, entity)

        except Exception as e:
            logger.error(f"Error creating {self.model.__name__} from dict: {e}")
            raise

    async def update(self, session: AsyncSession, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            session: Database session
            entity: Updated entity instance

        Returns:
            Updated entity
        """
        try:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)

            logger.debug(f"Updated {self.model.__name__} with id {entity.id}")
            return entity

        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise

    async def update_by_id(
        self,
        session: AsyncSession,
        id_value: Any,
        update_data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update entity by ID using dictionary data.

        Args:
            session: Database session
            id_value: Primary key value
            update_data: Dictionary of fields to update

        Returns:
            Updated entity or None if not found
        """
        try:
            stmt = (
                update(self.model)
                .where(self.model.id == id_value)
                .values(**update_data)
                .returning(self.model)
            )

            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

            if entity:
                logger.debug(f"Updated {self.model.__name__} with id {id_value}")

            return entity

        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} by id {id_value}: {e}")
            raise

    async def delete_by_id(self, session: AsyncSession, id_value: Any) -> bool:
        """
        Delete entity by ID.

        Args:
            session: Database session
            id_value: Primary key value

        Returns:
            True if entity was deleted, False if not found
        """
        try:
            stmt = delete(self.model).where(self.model.id == id_value)
            result = await session.execute(stmt)

            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Deleted {self.model.__name__} with id {id_value}")

            return deleted

        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} by id {id_value}: {e}")
            raise

    async def count(self, session: AsyncSession) -> int:
        """
        Count total number of entities.

        Args:
            session: Database session

        Returns:
            Total count of entities
        """
        try:
            stmt = select(func.count(self.model.id))
            result = await session.execute(stmt)
            count = result.scalar()

            logger.debug(f"Counted {count} {self.model.__name__} entities")
            return count

        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise

    async def exists(self, session: AsyncSession, id_value: Any) -> bool:
        """
        Check if entity exists by ID.

        Args:
            session: Database session
            id_value: Primary key value

        Returns:
            True if entity exists, False otherwise
        """
        try:
            stmt = select(func.count(self.model.id)).where(self.model.id == id_value)
            result = await session.execute(stmt)
            count = result.scalar()

            exists = count > 0
            logger.debug(f"{self.model.__name__} with id {id_value} exists: {exists}")

            return exists

        except Exception as e:
            logger.error(f"Error checking if {self.model.__name__} exists with id {id_value}: {e}")
            raise