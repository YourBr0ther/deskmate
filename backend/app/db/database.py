import logging
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.qdrant import qdrant_manager
from app.db.connection_manager import init_db_manager, get_db_session, get_db_health
from app.db.base import Base
from app.exceptions import ResourceError

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
        await init_db_manager(database_url, echo=False)
        logger.info("Database connection manager initialized")

        # Create database tables
        async with get_db_session() as session:
            # Use the engine from the connection manager to create tables
            from app.db.connection_manager import db_manager
            if db_manager and db_manager.engine:
                async with db_manager.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created/verified")

        # Initialize Qdrant
        await qdrant_manager.connect()
        logger.info("All database connections initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise ResourceError(
            "Failed to initialize database connections",
            resource_type="critical_database",
            operation="initialization"
        ) from e


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