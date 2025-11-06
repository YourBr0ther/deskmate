"""Simplified exception hierarchy for DeskMate application.

This module defines a streamlined set of domain-specific exceptions that provide
clear error context with minimal complexity.
"""

from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for better error classification."""
    LOW = "low"          # Minor issues that don't affect functionality
    MEDIUM = "medium"    # Issues that may affect some functionality
    HIGH = "high"        # Critical issues that affect core functionality
    CRITICAL = "critical" # System-wide failures


class ErrorCategory(Enum):
    """Error categories for better error organization."""
    VALIDATION = "validation"   # Input validation errors
    RESOURCE = "resource"       # Database, API, external resource errors
    BUSINESS = "business"       # Business logic errors
    SYSTEM = "system"           # System/infrastructure errors
    EXTERNAL = "external"       # External service errors


class DeskMateError(Exception):
    """Base exception for all DeskMate-specific errors.

    Simplified base class that focuses on essential error information
    without excessive nesting or wrapping.
    """

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recoverable: bool = True
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or self._generate_user_friendly_message()
        self.recoverable = recoverable

        super().__init__(message)

    def _generate_user_friendly_message(self) -> str:
        """Generate user-friendly error message based on category and context."""
        if self.category == ErrorCategory.VALIDATION:
            field = self.details.get("field")
            if field:
                return f"Please check your {field} and try again."
            return "Please check your input and try again."
        elif self.category == ErrorCategory.RESOURCE:
            resource_type = self.details.get("resource_type", "service")
            if self.severity == ErrorSeverity.HIGH:
                return f"The {resource_type} is currently unavailable. Please try again later."
            else:
                return f"Having trouble connecting to {resource_type}. Please try again in a moment."
        elif self.category == ErrorCategory.BUSINESS:
            operation = self.details.get("operation", "action")
            return f"Unable to complete {operation}. Please try a different approach or try again later."
        elif self.category == ErrorCategory.EXTERNAL:
            service = self.details.get("service", "external service")
            return f"{service.replace('_', ' ').title()} is temporarily unavailable. Please try again."
        elif self.category == ErrorCategory.SYSTEM:
            if self.severity == ErrorSeverity.CRITICAL:
                return "System maintenance in progress. Please contact support if this persists."
            else:
                return "Temporary system issue. Please try again in a moment."
        else:
            return "Something went wrong. Our team has been notified."

    @property
    def error_code(self) -> str:
        """Generate consistent error code."""
        return f"{self.category.value.upper()}_{self.severity.value.upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "message": self.message,
            "user_message": self.user_message,
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "details": self.details
        }

    def log_error(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with appropriate level based on severity and record metrics."""
        log_context = {
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "details": self.details
        }
        if context:
            log_context.update(context)

        # Record error metrics
        try:
            from app.logging_config import log_error_metrics
            log_error_metrics(self.category, self.severity)
        except ImportError:
            # Fallback if logging_config is not available
            pass

        # Log with appropriate level
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(self.message, extra=log_context)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(self.message, extra=log_context)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(self.message, extra=log_context)
        else:
            logger.info(self.message, extra=log_context)


class ValidationError(DeskMateError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        # Generate context-aware user message
        user_message = None
        if field and "password" in field.lower():
            user_message = "Please check your password and try again."
        elif field and "email" in field.lower():
            user_message = "Please enter a valid email address."
        elif field and "username" in field.lower():
            user_message = "Please enter a valid username."
        elif field:
            user_message = f"Please check the {field.replace('_', ' ')} field."

        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details,
            user_message=user_message,
            **kwargs
        )


class ResourceError(DeskMateError):
    """Raised when database or external resource operations fail."""

    def __init__(
        self,
        message: str,
        resource_type: str = "database",
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["resource_type"] = resource_type
        if operation:
            details["operation"] = operation

        # Determine if this is recoverable based on resource type
        recoverable = resource_type not in ["critical_database", "auth_service"]

        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH if not recoverable else ErrorSeverity.MEDIUM,
            details=details,
            recoverable=recoverable,
            **kwargs
        )


class ServiceError(DeskMateError):
    """Raised when external service operations fail."""

    def __init__(
        self,
        message: str,
        service: str,
        model: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["service"] = service
        if model:
            details["model"] = model

        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=f"{service} service is temporarily unavailable. Please try again.",
            **kwargs
        )


class BusinessLogicError(DeskMateError):
    """Raised when business logic validation or processing fails."""

    def __init__(
        self,
        message: str,
        operation: str,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["operation"] = operation

        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message="Unable to complete that action right now. Please try a different approach.",
            **kwargs
        )


class PathfindingError(BusinessLogicError):
    """Raised when pathfinding operations fail."""

    def __init__(
        self,
        message: str,
        start_pos: Optional[tuple] = None,
        end_pos: Optional[tuple] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if start_pos:
            details["start_position"] = start_pos
        if end_pos:
            details["end_position"] = end_pos

        super().__init__(
            message=message,
            operation="pathfinding",
            details=details,
            user_message="Unable to move to that location. Please try a different spot.",
            **kwargs
        )


class ObjectInteractionError(BusinessLogicError):
    """Raised when object interaction fails."""

    def __init__(
        self,
        message: str,
        object_id: Optional[str] = None,
        interaction_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if object_id:
            details["object_id"] = object_id
        if interaction_type:
            details["interaction_type"] = interaction_type

        super().__init__(
            message=message,
            operation="object_interaction",
            details=details,
            user_message="Unable to interact with that object right now.",
            **kwargs
        )


class ConnectionError(DeskMateError):
    """Raised when connection operations fail."""

    def __init__(
        self,
        message: str,
        connection_type: str = "websocket",
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["connection_type"] = connection_type

        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message="Connection issue detected. Reconnecting...",
            recoverable=True,
            **kwargs
        )


class PersonaError(ResourceError):
    """Raised when persona operations fail."""

    def __init__(
        self,
        message: str,
        persona_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if persona_name:
            details["persona_name"] = persona_name

        super().__init__(
            message=message,
            resource_type="persona",
            operation=operation,
            details=details,
            user_message="Persona not found or unable to load.",
            **kwargs
        )


class ConfigurationError(DeskMateError):
    """Raised when configuration errors occur."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            user_message="System configuration issue detected. Please contact support.",
            recoverable=False,
            **kwargs
        )


def create_error_from_exception(
    original_exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    default_category: ErrorCategory = ErrorCategory.SYSTEM
) -> DeskMateError:
    """
    Create an appropriate DeskMate error from a generic exception.

    This is a simplified replacement for wrap_exception that creates
    clean errors without excessive wrapping.
    """
    context = context or {}
    error_str = str(original_exception).lower()

    # Log the original exception for debugging
    logger.debug(f"Converting exception to DeskMateError: {original_exception}",
                extra={"original_type": type(original_exception).__name__,
                      "context": context})

    # Database/Resource errors
    if any(term in error_str for term in ["database", "connection", "postgresql", "qdrant", "sql"]):
        return ResourceError(
            message=f"Database operation failed: {str(original_exception)}",
            resource_type="database",
            details=context
        )

    # External service errors
    if any(term in error_str for term in ["api", "service", "timeout", "connection refused"]):
        return ServiceError(
            message=f"External service error: {str(original_exception)}",
            service=context.get("service", "unknown"),
            details=context
        )

    # Validation errors
    if any(term in error_str for term in ["validation", "invalid", "required", "missing"]):
        return ValidationError(
            message=str(original_exception),
            details=context
        )

    # Connection errors
    if any(term in error_str for term in ["websocket", "connection closed", "disconnected"]):
        return ConnectionError(
            message=str(original_exception),
            details=context
        )

    # Generic system error - don't wrap, just convert
    return DeskMateError(
        message=str(original_exception),
        category=default_category,
        severity=ErrorSeverity.MEDIUM,
        details=context
    )


# Backward compatibility aliases during transition
DeskMateBaseException = DeskMateError
DatabaseError = ResourceError
AIServiceError = ServiceError
BrainCouncilError = BusinessLogicError
ActionExecutionError = BusinessLogicError
WebSocketError = ConnectionError

# Backward compatibility alias for wrap_exception
wrap_exception = create_error_from_exception