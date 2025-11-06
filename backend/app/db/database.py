import logging
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.qdrant import qdrant_manager
from app.db.connection_manager import init_db_manager, get_db_session, get_db_health
from app.db.base import Base
from app.exceptions import ResourceError

# Temporary compatibility layer for AsyncSessionLocal
# This should be replaced with proper get_db_session usage in the future
def AsyncSessionLocal():
    """Factory function that returns an async context manager for database sessions."""
    return get_db_session()

# Import models to register them with SQLAlchemy
from app.models import room_objects, assistant, rooms

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://deskmate:deskmate@localhost:5432/deskmate")


async def init_db():
    """Initialize database connections with improved error handling."""
    logger.info("Initializing database connections...")

    try:
        # Initialize the database connection manager
        database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        logger.info(f"Using database URL: {database_url.replace('deskmate:deskmate', 'deskmate:****')}")

        await init_db_manager(database_url, echo=False)
        logger.info("Database connection manager initialized")

        # Test basic database connection first
        try:
            async with get_db_session() as session:
                # Simple query to test connection
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
        except Exception as db_test_error:
            logger.error(f"Database connection test failed: {db_test_error}")
            # Continue without database for now
            logger.warning("Continuing without database connection...")

        # Create database tables
        try:
            async with get_db_session() as session:
                # Use the engine from the connection manager to create tables
                from app.db.connection_manager import db_manager
                if db_manager and db_manager.engine:
                    async with db_manager.engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created/verified")
        except Exception as table_error:
            logger.error(f"Table creation failed: {table_error}")
            logger.warning("Continuing without table creation...")

        # Initialize Qdrant
        try:
            await qdrant_manager.connect()
            logger.info("Qdrant connection successful")
        except Exception as qdrant_error:
            logger.error(f"Qdrant connection failed: {qdrant_error}")
            logger.warning("Continuing without Qdrant...")

        logger.info("Database initialization completed (with possible warnings)")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Don't raise exception for now, allow startup to continue
        logger.warning("Continuing startup without full database initialization...")


async def check_postgres_health() -> bool:
    """Check PostgreSQL database health using the connection manager."""
    try:
        health_status = await get_db_health()
        return health_status.get("healthy", False)
    except Exception:
        return False


async def get_db():
    """Get database session using the resilient connection manager."""
    async with get_db_session() as session:
        yield session