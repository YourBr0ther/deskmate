"""
Brain Council - Refactored multi-perspective AI reasoning system for DeskMate.

This is the main Brain Council service that integrates all reasoner components
while maintaining backward compatibility with the existing API.

The service now uses:
- Individual reasoner components for better separation of concerns
- Coordinated reasoning flow through CouncilCoordinator
- Centralized prompt building and response parsing
- Parallel execution for improved performance
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .council_coordinator import CouncilCoordinator
from .prompt_builder import PromptBuilder, prompt_builder
from .response_parser import ResponseParser, response_parser
from .base import ReasoningContext, CouncilDecision

# Delayed imports to avoid circular dependencies and database issues
# These will be imported when needed
from app.utils.coordinate_system import ROOM_WIDTH, ROOM_HEIGHT
from app.exceptions import (
    BusinessLogicError, ResourceError, ServiceError,
    ValidationError, create_error_from_exception, ErrorSeverity
)

logger = logging.getLogger(__name__)


class BrainCouncil:
    """
    Refactored Brain Council with improved architecture.

    This version maintains the same public API while internally using
    the new reasoner component architecture for better maintainability,
    testability, and performance.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.coordinator = CouncilCoordinator()
        self.prompt_builder = prompt_builder
        self.response_parser = response_parser

        # Feature flags for gradual rollout
        self.use_new_architecture = True  # Set to True to enable new architecture
        self.enable_parallel_reasoning = True  # Enable parallel reasoner execution

        self.logger.info("Brain Council initialized with refactored architecture")

    async def process_user_message(
        self,
        user_message: str,
        persona_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process user message through Brain Council reasoning.

        Maintains backward compatibility while using the new reasoner architecture.

        Args:
            user_message: User's message to process
            persona_context: Active persona information

        Returns:
            Dictionary with response, actions, mood, and reasoning
        """
        try:
            self.logger.info(f"Processing user message: {user_message[:50]}...")

            if self.use_new_architecture:
                return await self._process_with_new_architecture(user_message, persona_context)
            else:
                return await self._process_with_legacy_method(user_message, persona_context)

        except BusinessLogicError as e:
            e.log_error({"step": "process_user_message"})
            return self._create_error_response(e.user_message, e.message)
        except ServiceError as e:
            e.log_error({"step": "process_user_message"})
            return self._create_error_response(e.user_message, e.message)
        except ResourceError as e:
            e.log_error({"step": "process_user_message"})
            return self._create_error_response(e.user_message, e.message)
        except Exception as e:
            error = create_error_from_exception(e, {
                "step": "process_user_message",
                "user_message_length": len(user_message) if user_message else 0
            })
            error.severity = ErrorSeverity.HIGH
            error.log_error()
            return self._create_error_response(
                "I'm having trouble processing that request right now.",
                error.message
            )

    async def _process_with_new_architecture(
        self,
        user_message: str,
        persona_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process using the new reasoner component architecture.

        Args:
            user_message: User's message to process
            persona_context: Active persona information

        Returns:
            Dictionary with response, actions, mood, and reasoning
        """
        try:
            # Gather context
            assistant_state = await self._gather_assistant_state()
            room_state = await self._gather_room_state()

            # Process through coordinator
            decision = await self.coordinator.process_user_message(
                user_message=user_message,
                assistant_state=assistant_state,
                room_state=room_state,
                persona_context=persona_context
            )

            # Convert to legacy format for backward compatibility
            return self._convert_decision_to_legacy_format(decision)

        except Exception as e:
            self.logger.error(f"Error in new architecture processing: {e}")
            # Fallback to legacy method
            self.logger.info("Falling back to legacy processing method")
            return await self._process_with_legacy_method(user_message, persona_context)

    async def _process_with_legacy_method(
        self,
        user_message: str,
        persona_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Fallback processing using the legacy method.

        This maintains the original Brain Council logic as a safety net
        while the new architecture is being stabilized.

        Args:
            user_message: User's message to process
            persona_context: Active persona information

        Returns:
            Dictionary with response, actions, mood, and reasoning
        """
        try:
            self.logger.info("Using legacy Brain Council processing method")

            # Gather current context (same as before)
            context = await self._gather_legacy_context()

            # Build council prompt using new prompt builder but legacy format
            council_prompt = self._build_legacy_council_prompt(
                user_message, context, persona_context
            )

            # Get council reasoning using existing LLM integration
            council_response = await self._query_council_legacy(
                council_prompt, user_message, persona_context
            )

            # Parse response using new parser but expect legacy format
            decision_dict = self._parse_legacy_response(council_response)

            return decision_dict

        except Exception as e:
            self.logger.error(f"Error in legacy processing: {e}")
            return self._create_error_response(
                "I understand what you're asking, but I'm having trouble processing the details right now.",
                str(e)
            )

    async def _gather_assistant_state(self) -> Dict[str, Any]:
        """Gather current assistant state for new architecture."""
        try:
            from app.services.assistant_service import assistant_service
            assistant_state = await assistant_service.get_assistant_state()
            return {
                "position": {
                    "x": assistant_state.position_x,
                    "y": assistant_state.position_y
                },
                "facing": assistant_state.facing_direction,
                "action": assistant_state.current_action,
                "mood": assistant_state.mood,
                "holding_object_id": assistant_state.holding_object_id
            }
        except Exception as e:
            self.logger.warning(f"Error gathering assistant state: {e}")
            return {
                "position": {"x": ROOM_WIDTH / 2, "y": ROOM_HEIGHT / 2},
                "facing": "right",
                "action": "idle",
                "mood": "neutral",
                "holding_object_id": None
            }

    async def _gather_room_state(self) -> Dict[str, Any]:
        """Gather current room state for new architecture."""
        try:
            from app.services.room_service import room_service
            objects = await room_service.get_all_objects()
            object_states = {}

            for obj in objects:
                states = await room_service.get_object_states(obj["id"])
                object_states[obj["id"]] = states

            return {
                "objects": objects,
                "object_states": object_states,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Error gathering room state: {e}")
            return {
                "objects": [],
                "object_states": {},
                "timestamp": datetime.now().isoformat()
            }

    async def _gather_legacy_context(self) -> Dict[str, Any]:
        """Gather context using legacy method (fallback)."""
        try:
            from app.services.assistant_service import assistant_service
            from app.services.room_service import room_service
            # This is the original context gathering logic
            assistant_state = await assistant_service.get_assistant_state()
            objects = await room_service.get_all_objects()

            object_states = {}
            for obj in objects:
                states = await room_service.get_object_states(obj["id"])
                object_states[obj["id"]] = states

            return {
                "assistant": {
                    "position": {
                        "x": assistant_state.position_x,
                        "y": assistant_state.position_y
                    },
                    "facing": assistant_state.facing_direction,
                    "action": assistant_state.current_action,
                    "mood": assistant_state.mood,
                    "holding_object_id": assistant_state.holding_object_id
                },
                "room": {
                    "objects": objects,
                    "object_states": object_states,
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.warning(f"Error gathering legacy context: {e}")
            return self._get_fallback_context()

    def _get_fallback_context(self) -> Dict[str, Any]:
        """Return fallback context when database operations fail."""
        return {
            "assistant": {
                "position": {"x": ROOM_WIDTH / 2, "y": ROOM_HEIGHT / 2},
                "facing": "right",
                "action": "idle",
                "mood": "neutral",
                "holding_object_id": None
            },
            "room": {
                "objects": [],
                "object_states": {},
                "timestamp": datetime.now().isoformat()
            }
        }

    def _build_legacy_council_prompt(
        self,
        user_message: str,
        context: Dict[str, Any],
        persona_context: Optional[Dict] = None
    ) -> str:
        """Build council prompt using legacy format but new prompt builder."""
        try:
            # Create a ReasoningContext for the new prompt builder
            reasoning_context = ReasoningContext(
                user_message=user_message,
                assistant_state=context["assistant"],
                room_state=context["room"],
                persona_context=persona_context,
                timestamp=datetime.now()
            )

            # Use new prompt builder
            return self.prompt_builder.build_council_prompt(reasoning_context)

        except Exception as e:
            self.logger.warning(f"Error building prompt with new builder, using fallback: {e}")
            # Fallback to simplified prompt
            return f"""You are the Brain Council for a virtual AI companion.

USER MESSAGE: "{user_message}"

Respond in JSON format with:
{{
    "response": "natural response to user",
    "actions": [],
    "mood": "neutral",
    "reasoning": "decision explanation"
}}"""

    async def _query_council_legacy(
        self,
        prompt: str,
        user_message: str = "",
        persona_context: Optional[Dict] = None
    ) -> str:
        """Query LLM using legacy method."""
        try:
            from app.services.conversation_memory import conversation_memory
            from app.services.llm_manager import llm_manager, ChatMessage
            # Get conversation context (same as original)
            persona_name = persona_context.get("name") if persona_context else None
            context_messages = await conversation_memory.get_conversation_context(
                current_message=user_message,
                persona_name=persona_name
            )

            # Build enhanced prompt with memory context
            enhanced_prompt = prompt
            if len(context_messages) > conversation_memory.recent_context_size:
                memory_context = f"""

RELEVANT CONVERSATION HISTORY:
{chr(10).join([f"{msg.role.upper()}: {msg.content}" for msg in context_messages[:-conversation_memory.recent_context_size]])}

RECENT CONVERSATION:
{chr(10).join([f"{msg.role.upper()}: {msg.content}" for msg in context_messages[-conversation_memory.recent_context_size:]])}"""
                enhanced_prompt += memory_context

            # Query LLM
            messages = [
                ChatMessage(role="system", content="You are the Brain Council reasoning system for a virtual AI companion. Always respond in valid JSON format."),
                ChatMessage(role="user", content=enhanced_prompt)
            ]

            response = ""
            async for chunk in llm_manager.chat_completion_stream(messages=messages, temperature=0.3):
                if chunk:
                    response += chunk

            return response.strip()

        except Exception as e:
            self.logger.error(f"Error querying council: {e}")
            return '{"response": "I\'m having trouble processing that request right now.", "actions": [], "mood": "confused", "reasoning": "LLM query error"}'

    def _parse_legacy_response(self, response: str) -> Dict[str, Any]:
        """Parse response using new parser but return legacy format."""
        try:
            # Use new parser to get structured decision
            decision = self.response_parser.parse_council_response(response)

            # Convert to legacy format
            return self._convert_decision_to_legacy_format(decision)

        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            return {
                "response": "I understand what you're asking, but I'm having trouble organizing my thoughts right now.",
                "actions": [],
                "mood": "confused",
                "reasoning": f"Response parsing error: {str(e)}"
            }

    def _convert_decision_to_legacy_format(self, decision: CouncilDecision) -> Dict[str, Any]:
        """Convert CouncilDecision to legacy format for backward compatibility."""
        return {
            "response": decision.response,
            "actions": decision.actions,
            "mood": decision.mood,
            "reasoning": decision.reasoning,
            "council_reasoning": decision.council_reasoning,
            "confidence": decision.confidence,
            "metadata": decision.metadata
        }

    def _create_error_response(self, user_message: str, error_details: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "response": user_message,
            "actions": [],
            "mood": "confused",
            "reasoning": f"Error in processing: {error_details}"
        }

    async def process_idle_reasoning(self, idle_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process autonomous reasoning for idle mode.

        This method maintains the existing idle mode functionality
        while potentially using new architecture components in the future.

        Args:
            idle_context: Context including position, energy, objects, recent dreams, goals

        Returns:
            Dictionary with response, actions, and reasoning
        """
        try:
            self.logger.info("Processing idle reasoning")

            # For now, maintain existing idle logic
            # Future enhancement: could use specialized idle reasoners

            assistant_position = idle_context.get("assistant_position", {"x": ROOM_WIDTH / 2, "y": ROOM_HEIGHT / 2})
            energy = idle_context.get("assistant_energy", 1.0)
            objects = idle_context.get("room_objects", [])

            # Simple idle decision making
            if energy < 0.3:
                return {
                    "response": "Resting to restore energy.",
                    "actions": [{"type": "rest", "target": None, "parameters": {}}],
                    "reasoning": "Low energy level requires rest"
                }

            # Basic exploration
            return {
                "response": "Observing the room thoughtfully.",
                "actions": [{"type": "expression", "target": "contemplative", "parameters": {}}],
                "reasoning": "Idle observation and reflection"
            }

        except Exception as e:
            self.logger.error(f"Error in idle reasoning: {e}")
            return {
                "response": "Continuing to rest and observe the room.",
                "actions": [{"type": "rest", "target": None, "parameters": {}}],
                "reasoning": f"Idle reasoning error: {str(e)}"
            }


# Global instance (maintaining backward compatibility)
brain_council = BrainCouncil()