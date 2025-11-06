"""
Base interfaces and data structures for Brain Council reasoner components.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ReasoningContext:
    """Context data passed to reasoners."""
    user_message: str
    assistant_state: Dict[str, Any]
    room_state: Dict[str, Any]
    persona_context: Optional[Dict[str, Any]] = None
    conversation_context: Optional[List[Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ReasoningResult:
    """Result from a single reasoner."""
    reasoner_name: str
    reasoning: str
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if this reasoning result is valid."""
        return self.error is None and self.reasoning.strip() != ""


@dataclass
class CouncilDecision:
    """Final decision from the Brain Council."""
    response: str
    actions: List[Dict[str, Any]]
    mood: str
    reasoning: str
    council_reasoning: Dict[str, str]
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class BaseReasoner(ABC):
    """Base class for all Brain Council reasoners."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Process the reasoning context and return analysis.

        Args:
            context: The reasoning context with all relevant information

        Returns:
            ReasoningResult with the reasoner's analysis
        """
        pass

    def _create_result(self, reasoning: str, confidence: float = 1.0,
                      metadata: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None) -> ReasoningResult:
        """Helper to create a reasoning result."""
        return ReasoningResult(
            reasoner_name=self.name,
            reasoning=reasoning,
            confidence=confidence,
            metadata=metadata or {},
            error=error
        )

    def _handle_error(self, e: Exception, context: str = "") -> ReasoningResult:
        """Handle errors and return a result with error information."""
        error_msg = f"Error in {self.name}: {str(e)}"
        if context:
            error_msg += f" (Context: {context})"

        self.logger.error(error_msg, exc_info=True)

        return self._create_result(
            reasoning=f"Unable to provide reasoning due to error: {str(e)}",
            confidence=0.0,
            error=error_msg
        )


class ReasonerFactory:
    """Factory for creating and managing reasoner instances."""

    _reasoners: Dict[str, BaseReasoner] = {}

    @classmethod
    def register_reasoner(cls, name: str, reasoner: BaseReasoner) -> None:
        """Register a reasoner instance."""
        cls._reasoners[name] = reasoner
        logger.info(f"Registered reasoner: {name}")

    @classmethod
    def get_reasoner(cls, name: str) -> Optional[BaseReasoner]:
        """Get a reasoner by name."""
        return cls._reasoners.get(name)

    @classmethod
    def get_all_reasoners(cls) -> Dict[str, BaseReasoner]:
        """Get all registered reasoners."""
        return cls._reasoners.copy()

    @classmethod
    def clear_reasoners(cls) -> None:
        """Clear all registered reasoners (useful for testing)."""
        cls._reasoners.clear()