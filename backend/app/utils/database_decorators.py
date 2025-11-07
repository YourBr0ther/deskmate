"""
Database transaction decorators for service methods.

Provides decorators for automatic transaction management, error handling,
and retry logic for database operations.
"""

import logging
import asyncio
from functools import wraps
from typing import Callable, TypeVar, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.connection_manager import get_db_session
from app.exceptions import ResourceError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def transactional(
    rollback_on_error: bool = True,
    retry_attempts: int = 0,
    retry_delay: float = 0.5
):
    """
    Decorator for automatic transaction management in service methods.

    Args:
        rollback_on_error: Whether to rollback on exceptions
        retry_attempts: Number of retry attempts for transient failures
        retry_delay: Delay between retry attempts in seconds

    Usage:
        @transactional(retry_attempts=3)
        async def my_service_method(self, session: AsyncSession, ...):
            # Your database operations here
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # If session is already provided, use it directly
            if 'session' in kwargs and isinstance(kwargs['session'], AsyncSession):
                return await func(*args, **kwargs)

            # If first positional arg after self is AsyncSession, use it
            if len(args) > 1 and isinstance(args[1], AsyncSession):
                return await func(*args, **kwargs)

            # Otherwise, create a new session and inject it
            attempt = 0
            last_exception = None

            while attempt <= retry_attempts:
                try:
                    async with get_db_session() as session:
                        try:
                            # Inject session as second argument (after self)
                            if args and hasattr(args[0], '__class__'):  # Method call
                                result = await func(args[0], session, *args[1:], **kwargs)
                            else:  # Function call
                                result = await func(session, *args, **kwargs)

                            # Transaction is automatically committed by the context manager
                            return result

                        except Exception as e:
                            if rollback_on_error:
                                await session.rollback()
                            raise

                except (SQLAlchemyError, ResourceError) as e:
                    last_exception = e
                    attempt += 1

                    if attempt <= retry_attempts:
                        logger.warning(f"Database operation failed (attempt {attempt}/{retry_attempts + 1}), "
                                     f"retrying in {retry_delay}s: {e}")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Database operation failed after {retry_attempts + 1} attempts: {e}")
                        raise

                except Exception as e:
                    # Don't retry non-database errors
                    logger.error(f"Non-database error in transactional method: {e}")
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def read_only(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for read-only database operations.

    Provides a session but doesn't perform any transaction management.
    Suitable for queries that don't modify data.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        # If session is already provided, use it directly
        if 'session' in kwargs and isinstance(kwargs['session'], AsyncSession):
            return await func(*args, **kwargs)

        # If first positional arg after self is AsyncSession, use it
        if len(args) > 1 and isinstance(args[1], AsyncSession):
            return await func(*args, **kwargs)

        # Create a read-only session
        async with get_db_session() as session:
            try:
                # Inject session as second argument (after self)
                if args and hasattr(args[0], '__class__'):  # Method call
                    return await func(args[0], session, *args[1:], **kwargs)
                else:  # Function call
                    return await func(session, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in read-only database operation: {e}")
                raise

    return wrapper


def with_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Simple decorator that provides a database session if not already present.

    Does not perform any transaction management - leaves that to the
    connection manager's context manager.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        # If session is already provided, use it directly
        if 'session' in kwargs and isinstance(kwargs['session'], AsyncSession):
            return await func(*args, **kwargs)

        # If first positional arg after self is AsyncSession, use it
        if len(args) > 1 and isinstance(args[1], AsyncSession):
            return await func(*args, **kwargs)

        # Provide a session
        async with get_db_session() as session:
            # Inject session as second argument (after self)
            if args and hasattr(args[0], '__class__'):  # Method call
                return await func(args[0], session, *args[1:], **kwargs)
            else:  # Function call
                return await func(session, *args, **kwargs)

    return wrapper