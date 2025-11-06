"""Database connection manager with resilience patterns.

Provides:
- Connection pooling with retry logic
- Circuit breaker pattern for database failures
- Health monitoring and automatic recovery
- Graceful degradation for non-critical operations
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, AsyncGenerator, Callable, TypeVar, Awaitable
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import ResourceError, ErrorSeverity

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class ConnectionHealth:
    """Database connection health metrics."""
    is_healthy: bool
    last_check: float
    consecutive_failures: int
    last_error: Optional[str] = None
    response_time_ms: Optional[float] = None


class DatabaseCircuitBreaker:
    """Circuit breaker for database operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = SQLAlchemyError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt = 0

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() < self.next_attempt:
                raise ResourceError(
                    "Database circuit breaker is OPEN - too many recent failures",
                    resource_type="database",
                    operation="circuit_breaker_protection"
                )
            else:
                self.state = CircuitState.HALF_OPEN

        try:
            result = await func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise ResourceError(
                f"Database operation failed: {str(e)}",
                resource_type="database",
                operation="database_query"
            ) from e

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt = time.time() + self.recovery_timeout


class DatabaseConnectionManager:
    """Manages database connections with resilience patterns."""

    def __init__(self, database_url: str, **engine_kwargs):
        self.database_url = database_url
        self.engine_kwargs = engine_kwargs

        # Connection management
        self.engine = None
        self.session_factory = None

        # Health monitoring
        self.health = ConnectionHealth(
            is_healthy=False,
            last_check=0,
            consecutive_failures=0
        )

        # Circuit breaker
        self.circuit_breaker = DatabaseCircuitBreaker()

        # Configuration
        self.health_check_interval = 30  # seconds
        self.max_retry_attempts = 3
        self.retry_delay = 1.0  # seconds

        logger.info("Database connection manager initialized")

    async def initialize(self) -> None:
        """Initialize database engine and connection pool."""
        try:
            # Create engine with proper settings for resilience
            self.engine = create_async_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Validates connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=False,          # Disable SQL logging in production
                **self.engine_kwargs
            )

            # Create session factory
            self.session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Initial health check
            await self._health_check()

            logger.info("Database connection manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database connection manager: {e}")
            raise ResourceError(
                "Failed to initialize database connections",
                resource_type="critical_database",
                operation="initialization"
            ) from e

    async def _health_check(self) -> bool:
        """Perform database health check."""
        start_time = time.time()

        try:
            if not self.engine:
                raise ResourceError("Database engine not initialized", resource_type="database")

            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            # Health check successful
            response_time = (time.time() - start_time) * 1000
            self.health = ConnectionHealth(
                is_healthy=True,
                last_check=time.time(),
                consecutive_failures=0,
                response_time_ms=response_time
            )

            logger.debug(f"Database health check passed ({response_time:.2f}ms)")
            return True

        except Exception as e:
            # Health check failed
            self.health = ConnectionHealth(
                is_healthy=False,
                last_check=time.time(),
                consecutive_failures=self.health.consecutive_failures + 1,
                last_error=str(e)
            )

            logger.warning(f"Database health check failed: {e}")
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """Get current database health status."""
        # Perform health check if it's been too long
        if time.time() - self.health.last_check > self.health_check_interval:
            await self._health_check()

        return {
            "healthy": self.health.is_healthy,
            "last_check": self.health.last_check,
            "consecutive_failures": self.health.consecutive_failures,
            "last_error": self.health.last_error,
            "response_time_ms": self.health.response_time_ms,
            "circuit_breaker_state": self.circuit_breaker.state.value
        }

    @asynccontextmanager
    async def get_session(self, retries: int = None) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with retry logic and circuit breaker protection."""
        if retries is None:
            retries = self.max_retry_attempts

        if not self.session_factory:
            raise ResourceError(
                "Database connection manager not initialized",
                resource_type="critical_database",
                operation="get_session"
            )

        session = None
        last_exception = None

        for attempt in range(retries + 1):
            try:
                async def create_session():
                    return self.session_factory()

                # Use circuit breaker protection
                session = await self.circuit_breaker.call(create_session)

                # Yield the session
                yield session

                # If we get here, the operation was successful
                await session.commit()
                return

            except Exception as e:
                last_exception = e

                if session:
                    try:
                        await session.rollback()
                    except Exception:
                        pass  # Rollback failed, but we're already in error state

                if attempt < retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{retries + 1}), "
                                 f"retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Database operation failed after {retries + 1} attempts: {e}")

            finally:
                if session:
                    try:
                        await session.close()
                    except Exception as e:
                        logger.warning(f"Error closing database session: {e}")
                    session = None

        # If we get here, all retries failed
        if last_exception:
            if isinstance(last_exception, ResourceError):
                raise
            else:
                raise ResourceError(
                    f"Database operation failed after {retries + 1} attempts: {str(last_exception)}",
                    resource_type="database",
                    operation="session_management"
                ) from last_exception

    async def execute_with_fallback(
        self,
        operation: Callable[[AsyncSession], Awaitable[T]],
        fallback: Optional[Callable[[], Awaitable[T]]] = None,
        critical: bool = False
    ) -> T:
        """Execute database operation with optional fallback for non-critical operations."""
        try:
            async with self.get_session() as session:
                return await operation(session)

        except ResourceError as e:
            if critical or not fallback:
                # Re-raise for critical operations or when no fallback available
                e.severity = ErrorSeverity.HIGH if critical else ErrorSeverity.MEDIUM
                raise

            logger.warning(f"Database operation failed, using fallback: {e.message}")
            return await fallback()

    async def close(self) -> None:
        """Close database connections and cleanup."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")


# Global connection manager instance
db_manager: Optional[DatabaseConnectionManager] = None


async def init_db_manager(database_url: str, **kwargs) -> None:
    """Initialize the global database connection manager."""
    global db_manager
    db_manager = DatabaseConnectionManager(database_url, **kwargs)
    await db_manager.initialize()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session from the global connection manager."""
    if not db_manager:
        raise ResourceError(
            "Database connection manager not initialized",
            resource_type="critical_database",
            operation="get_session"
        )

    async with db_manager.get_session() as session:
        yield session


async def get_db_health() -> Dict[str, Any]:
    """Get database health status from the global connection manager."""
    if not db_manager:
        return {"healthy": False, "error": "Database manager not initialized"}

    return await db_manager.get_health_status()


async def execute_db_operation_with_fallback(
    operation: Callable[[AsyncSession], Awaitable[T]],
    fallback: Optional[Callable[[], Awaitable[T]]] = None,
    critical: bool = False
) -> T:
    """Execute database operation with fallback support."""
    if not db_manager:
        raise ResourceError(
            "Database connection manager not initialized",
            resource_type="critical_database"
        )

    return await db_manager.execute_with_fallback(operation, fallback, critical)