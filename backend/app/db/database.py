import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

from app.db.qdrant import qdrant_manager
# Import models to register them with SQLAlchemy
from app.models import room_objects, assistant, rooms

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://deskmate:deskmate@localhost:5432/deskmate")

engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

from app.db.base import Base


async def init_db():
    logger.info("Initializing database connections...")

    # Initialize Qdrant
    await qdrant_manager.connect()

    # Test PostgreSQL connection and create tables
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection successful")

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

    except Exception as e:
        logger.error(f"PostgreSQL connection or table creation failed: {e}")


async def check_postgres_health() -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()