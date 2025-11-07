"""
FastAPI dependencies for database session management.

This module provides:
- Proper dependency injection for database sessions
- Automatic transaction management
- Error handling and rollback
- Connection pooling and resilience patterns
"""

import logging
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection_manager import get_db_session

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides database sessions.

    This dependency:
    - Manages database connections using the connection manager
    - Provides automatic transaction management
    - Handles rollback on exceptions
    - Uses connection pooling and retry logic

    Usage in FastAPI endpoints:
        @app.get("/api/data")
        async def get_data(db: AsyncSession = Depends(get_db)):
            # Use db session here
            result = await db.execute(select(Model))
            return result.scalars().all()
    """
    async for session in get_db_session():
        try:
            yield session
        except Exception as e:
            logger.error(f"Database transaction error: {e}")
            await session.rollback()
            raise
        else:
            # Commit is handled automatically by the connection manager
            pass


# Type alias for cleaner imports
DatabaseSession = Depends(get_db)