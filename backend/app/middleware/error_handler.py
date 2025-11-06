"""
Error handling middleware for DeskMate backend.

This middleware provides centralized error handling and consistent error responses
across all API endpoints.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions import DeskMateBaseException, wrap_exception

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors consistently across the application."""

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Add correlation ID to logger context
        logger_context = {"correlation_id": correlation_id, "endpoint": request.url.path}

        try:
            response = await call_next(request)
            return response

        except DeskMateBaseException as e:
            logger.error(
                f"DeskMate error in {request.url.path}: {e.message}",
                extra=logger_context | {"error_code": e.error_code, "details": e.details}
            )
            return create_error_response(e, correlation_id)

        except Exception as e:
            # Wrap generic exceptions in DeskMate exceptions
            context = {
                "endpoint": request.url.path,
                "method": request.method,
                "correlation_id": correlation_id
            }

            wrapped_exception = wrap_exception(e, context)
            logger.error(
                f"Unexpected error in {request.url.path}: {str(e)}",
                extra=logger_context | {"original_exception": str(e)},
                exc_info=True
            )
            return create_error_response(wrapped_exception, correlation_id, include_debug=True)


def create_error_response(
    exception: DeskMateBaseException,
    correlation_id: str,
    include_debug: bool = False
) -> JSONResponse:
    """Create standardized error response."""

    # Determine HTTP status code based on exception type
    status_code = get_status_code_for_exception(exception)

    # Build error response
    error_response = {
        "status": "error",
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": correlation_id,
        "error": {
            "message": exception.message,
            "code": exception.error_code,
            "type": exception.__class__.__name__
        }
    }

    # Add details if present
    if exception.details:
        error_response["error"]["details"] = exception.details

    # Add debug information in development
    if include_debug and exception.original_exception:
        error_response["debug"] = {
            "original_exception": str(exception.original_exception),
            "original_type": type(exception.original_exception).__name__
        }

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def get_status_code_for_exception(exception: DeskMateBaseException) -> int:
    """Determine appropriate HTTP status code for exception type."""
    from app.exceptions import (
        ValidationError, DatabaseError, AIServiceError, BrainCouncilError,
        ActionExecutionError, WebSocketError, PersonaError, ConfigurationError
    )

    if isinstance(exception, ValidationError):
        return 400  # Bad Request
    elif isinstance(exception, (DatabaseError, AIServiceError, BrainCouncilError)):
        return 503  # Service Unavailable
    elif isinstance(exception, ActionExecutionError):
        return 422  # Unprocessable Entity
    elif isinstance(exception, WebSocketError):
        return 400  # Bad Request
    elif isinstance(exception, PersonaError):
        return 404  # Not Found
    elif isinstance(exception, ConfigurationError):
        return 500  # Internal Server Error
    else:
        return 500  # Internal Server Error


class ErrorResponseSchema:
    """Schema for standardized error responses."""

    @staticmethod
    def validation_error(message: str, field: str = None, value: Any = None) -> Dict[str, Any]:
        """Create validation error response."""
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        return {
            "status": "error",
            "error": {
                "message": message,
                "code": "VALIDATION_ERROR",
                "type": "ValidationError",
                "details": details
            }
        }

    @staticmethod
    def not_found_error(resource: str, identifier: str = None) -> Dict[str, Any]:
        """Create not found error response."""
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"

        details = {"resource": resource}
        if identifier:
            details["identifier"] = identifier

        return {
            "status": "error",
            "error": {
                "message": message,
                "code": "NOT_FOUND_ERROR",
                "type": "NotFoundError",
                "details": details
            }
        }

    @staticmethod
    def service_unavailable_error(service: str, message: str = None) -> Dict[str, Any]:
        """Create service unavailable error response."""
        if not message:
            message = f"{service} is currently unavailable"

        return {
            "status": "error",
            "error": {
                "message": message,
                "code": "SERVICE_UNAVAILABLE",
                "type": "ServiceUnavailableError",
                "details": {"service": service}
            }
        }

    @staticmethod
    def success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
        """Create standardized success response."""
        response = {"status": "success"}

        if message:
            response["message"] = message

        if data is not None:
            response["data"] = data

        return response


# Helper function to get correlation ID from request
def get_correlation_id(request: Request) -> Optional[str]:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", None)