"""
Custom exception hierarchy for DeskMate application.

This module defines domain-specific exceptions that provide better error context
and enable more precise error handling throughout the application.
"""

from typing import Optional, Dict, Any
import traceback


class DeskMateBaseException(Exception):
    """Base exception for all DeskMate-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "type": self.__class__.__name__
        }


class ValidationError(DeskMateBaseException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class DatabaseError(DeskMateBaseException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class AIServiceError(DeskMateBaseException):
    """Raised when AI service operations fail."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if service:
            details["service"] = service
        if model:
            details["model"] = model

        super().__init__(
            message=message,
            error_code="AI_SERVICE_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class BrainCouncilError(AIServiceError):
    """Raised when Brain Council processing fails."""

    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        council_member: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if step:
            details["step"] = step
        if council_member:
            details["council_member"] = council_member

        super().__init__(
            message=message,
            service="brain_council",
            **{k: v for k, v in kwargs.items() if k != "details"},
            details=details
        )
        self.error_code = "BRAIN_COUNCIL_ERROR"


class ActionExecutionError(DeskMateBaseException):
    """Raised when action execution fails."""

    def __init__(
        self,
        message: str,
        action_type: Optional[str] = None,
        target: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if action_type:
            details["action_type"] = action_type
        if target:
            details["target"] = target

        super().__init__(
            message=message,
            error_code="ACTION_EXECUTION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class PathfindingError(ActionExecutionError):
    """Raised when pathfinding operations fail."""

    def __init__(
        self,
        message: str,
        start_pos: Optional[tuple] = None,
        end_pos: Optional[tuple] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if start_pos:
            details["start_position"] = start_pos
        if end_pos:
            details["end_position"] = end_pos

        super().__init__(
            message=message,
            action_type="movement",
            **{k: v for k, v in kwargs.items() if k != "details"},
            details=details
        )
        self.error_code = "PATHFINDING_ERROR"


class ObjectInteractionError(ActionExecutionError):
    """Raised when object interaction fails."""

    def __init__(
        self,
        message: str,
        object_id: Optional[str] = None,
        interaction_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if object_id:
            details["object_id"] = object_id
        if interaction_type:
            details["interaction_type"] = interaction_type

        super().__init__(
            message=message,
            action_type="object_interaction",
            target=object_id,
            **{k: v for k, v in kwargs.items() if k != "details"},
            details=details
        )
        self.error_code = "OBJECT_INTERACTION_ERROR"


class WebSocketError(DeskMateBaseException):
    """Raised when WebSocket operations fail."""

    def __init__(
        self,
        message: str,
        message_type: Optional[str] = None,
        client_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if message_type:
            details["message_type"] = message_type
        if client_id:
            details["client_id"] = client_id

        super().__init__(
            message=message,
            error_code="WEBSOCKET_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class PersonaError(DeskMateBaseException):
    """Raised when persona operations fail."""

    def __init__(
        self,
        message: str,
        persona_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if persona_name:
            details["persona_name"] = persona_name
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code="PERSONA_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class ConfigurationError(DeskMateBaseException):
    """Raised when configuration errors occur."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_file:
            details["config_file"] = config_file

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


def wrap_exception(original_exception: Exception, context: Optional[Dict[str, Any]] = None) -> DeskMateBaseException:
    """
    Wrap a generic exception in an appropriate DeskMate exception.

    This function analyzes the original exception and context to determine
    the most appropriate DeskMate exception type to wrap it with.
    """
    context = context or {}

    # Database-related exceptions
    if any(db_term in str(original_exception).lower() for db_term in
           ["database", "connection", "postgresql", "qdrant", "sql"]):
        return DatabaseError(
            message=f"Database operation failed: {str(original_exception)}",
            details=context,
            original_exception=original_exception
        )

    # AI service exceptions
    if any(ai_term in str(original_exception).lower() for ai_term in
           ["openai", "model", "token", "api", "llm", "embedding"]):
        return AIServiceError(
            message=f"AI service error: {str(original_exception)}",
            details=context,
            original_exception=original_exception
        )

    # Validation exceptions
    if any(val_term in str(original_exception).lower() for val_term in
           ["validation", "invalid", "required", "missing"]):
        return ValidationError(
            message=f"Validation failed: {str(original_exception)}",
            details=context,
            original_exception=original_exception
        )

    # WebSocket exceptions
    if any(ws_term in str(original_exception).lower() for ws_term in
           ["websocket", "connection closed", "client disconnected"]):
        return WebSocketError(
            message=f"WebSocket error: {str(original_exception)}",
            details=context,
            original_exception=original_exception
        )

    # Generic fallback
    return DeskMateBaseException(
        message=f"Unexpected error: {str(original_exception)}",
        error_code="UNKNOWN_ERROR",
        details=context,
        original_exception=original_exception
    )