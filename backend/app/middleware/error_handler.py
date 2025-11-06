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

from app.exceptions import DeskMateError, create_error_from_exception, ErrorSeverity, ErrorCategory

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

        except DeskMateError as e:
            # Log the error using the error's own logging method
            e.log_error(logger_context)
            return create_error_response(e, correlation_id)

        except Exception as e:
            # Convert generic exceptions to DeskMate errors
            context = {
                "endpoint": request.url.path,
                "method": request.method,
                "correlation_id": correlation_id
            }

            deskmate_error = create_error_from_exception(e, context)
            # Set severity to HIGH for unexpected exceptions
            deskmate_error.severity = ErrorSeverity.HIGH
            deskmate_error.log_error(logger_context)
            return create_error_response(deskmate_error, correlation_id, include_debug=True)


def create_error_response(
    exception: DeskMateError,
    correlation_id: str,
    include_debug: bool = False
) -> JSONResponse:
    """Create standardized error response."""

    # Determine HTTP status code based on exception type
    status_code = get_status_code_for_exception(exception)

    # Build error response using exception's to_dict method
    error_dict = exception.to_dict()
    error_response = {
        "status": "error",
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": correlation_id,
        "error": error_dict
    }

    # Add debug information in development
    if include_debug:
        error_response["debug"] = {
            "severity": exception.severity.value,
            "category": exception.category.value,
            "recoverable": exception.recoverable
        }

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def get_status_code_for_exception(exception: DeskMateError) -> int:
    """Determine appropriate HTTP status code for exception category and severity."""
    # Map error categories to HTTP status codes
    if exception.category == ErrorCategory.VALIDATION:
        return 400  # Bad Request
    elif exception.category == ErrorCategory.RESOURCE:
        return 503 if exception.severity == ErrorSeverity.HIGH else 500
    elif exception.category == ErrorCategory.EXTERNAL:
        return 503  # Service Unavailable
    elif exception.category == ErrorCategory.BUSINESS:
        return 422  # Unprocessable Entity
    elif exception.category == ErrorCategory.SYSTEM:
        if exception.severity == ErrorSeverity.CRITICAL:
            return 500  # Internal Server Error
        else:
            return 503  # Service Unavailable
    else:
        return 500  # Internal Server Error


class ErrorResponseSchema:
    """Schema for standardized error responses."""

    @staticmethod
    def validation_error(message: str, field: str = None, value: Any = None) -> Dict[str, Any]:
        """Create validation error response."""
        from app.exceptions import ValidationError

        error = ValidationError(message, field=field, value=value)
        return {
            "status": "error",
            "error": error.to_dict()
        }

    @staticmethod
    def not_found_error(resource: str, identifier: str = None) -> Dict[str, Any]:
        """Create not found error response."""
        from app.exceptions import ResourceError

        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"

        details = {"resource": resource}
        if identifier:
            details["identifier"] = identifier

        error = ResourceError(
            message=message,
            resource_type=resource,
            operation="lookup",
            details=details,
            user_message=f"{resource.capitalize()} not found."
        )
        return {
            "status": "error",
            "error": error.to_dict()
        }

    @staticmethod
    def service_unavailable_error(service: str, message: str = None) -> Dict[str, Any]:
        """Create service unavailable error response."""
        from app.exceptions import ServiceError

        if not message:
            message = f"{service} is currently unavailable"

        error = ServiceError(message=message, service=service)
        return {
            "status": "error",
            "error": error.to_dict()
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