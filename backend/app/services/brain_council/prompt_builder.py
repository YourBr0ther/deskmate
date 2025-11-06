"""
Prompt Builder - Centralized prompt construction for Brain Council.

This builder:
- Constructs prompts for LLM interaction
- Maintains consistency in prompt formatting
- Handles different prompt types (reasoning, analysis, etc.)
- Manages context integration and formatting
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import ReasoningContext
from app.utils.coordinate_system import (
    Position, ROOM_WIDTH, ROOM_HEIGHT, INTERACTION_DISTANCE, NEARBY_DISTANCE
)

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Centralized prompt construction for Brain Council operations.

    Provides standardized prompt building for different types of
    reasoning and analysis tasks within the Brain Council system.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_council_prompt(
        self,
        context: ReasoningContext,
        include_memory_context: bool = True
    ) -> str:
        """
        Build a comprehensive Brain Council prompt.

        Args:
            context: The reasoning context
            include_memory_context: Whether to include conversation memory

        Returns:
            Complete prompt for Brain Council reasoning
        """
        try:
            prompt_parts = []

            # System introduction
            prompt_parts.append(self._build_system_introduction())

            # User message section
            prompt_parts.append(self._build_user_message_section(context.user_message))

            # Persona context if available
            if context.persona_context:
                prompt_parts.append(self._build_persona_section(context.persona_context))

            # Current context section
            prompt_parts.append(self._build_current_context_section(context))

            # Spatial environment section
            prompt_parts.append(self._build_spatial_section(context))

            # Memory context if available and requested
            if include_memory_context and context.conversation_context:
                prompt_parts.append(self._build_memory_section(context.conversation_context))

            # Council perspectives section
            prompt_parts.append(self._build_council_perspectives_section())

            # Response format section
            prompt_parts.append(self._build_response_format_section())

            return "\n\n".join(prompt_parts)

        except Exception as e:
            self.logger.error(f"Error building council prompt: {e}")
            return self._build_fallback_prompt(context.user_message)

    def build_reasoner_prompt(
        self,
        reasoner_name: str,
        context: ReasoningContext,
        specific_instructions: Optional[str] = None
    ) -> str:
        """
        Build a specialized prompt for individual reasoners.

        Args:
            reasoner_name: Name of the reasoner
            context: The reasoning context
            specific_instructions: Optional specific instructions for this reasoner

        Returns:
            Prompt tailored for the specific reasoner
        """
        try:
            prompt_parts = []

            # Reasoner-specific introduction
            prompt_parts.append(self._build_reasoner_introduction(reasoner_name))

            # Context relevant to this reasoner
            prompt_parts.append(self._build_reasoner_context(reasoner_name, context))

            # Specific instructions if provided
            if specific_instructions:
                prompt_parts.append(f"SPECIFIC INSTRUCTIONS:\n{specific_instructions}")

            # Reasoner-specific analysis request
            prompt_parts.append(self._build_reasoner_analysis_request(reasoner_name))

            return "\n\n".join(prompt_parts)

        except Exception as e:
            self.logger.error(f"Error building reasoner prompt for {reasoner_name}: {e}")
            return f"Analyze the user message '{context.user_message}' from the perspective of {reasoner_name}."

    def _build_system_introduction(self) -> str:
        """Build the system introduction section."""
        return """You are the Brain Council for a virtual AI companion. Process this user request using 5 council perspectives to generate a contextual response that integrates with the room environment."""

    def _build_user_message_section(self, user_message: str) -> str:
        """Build the user message section."""
        return f'USER MESSAGE: "{user_message}"'

    def _build_persona_section(self, persona_context: Dict[str, Any]) -> str:
        """Build the persona context section."""
        persona_name = persona_context.get('name', 'Default')
        personality = persona_context.get('personality', 'Friendly AI assistant')
        creator = persona_context.get('creator', 'Unknown')

        return f"""ACTIVE PERSONA: {persona_name}
Personality: {personality}
Creator: {creator}"""

    def _build_current_context_section(self, context: ReasoningContext) -> str:
        """Build the current context section."""
        assistant_state = context.assistant_state
        position = assistant_state["position"]

        assistant_pos = Position(position["x"], position["y"])

        context_lines = [
            "CURRENT CONTEXT:",
            f"Assistant Position: ({int(assistant_pos.x)}, {int(assistant_pos.y)}) pixels",
            f"Room Dimensions: {ROOM_WIDTH}x{ROOM_HEIGHT} pixels",
            f"Assistant Status: {assistant_state.get('action', 'idle')}, facing {assistant_state.get('facing', 'right')}, mood: {assistant_state.get('mood', 'neutral')}",
            f"Holding: {assistant_state.get('holding_object_id') or 'nothing'}",
            "Coordinate System: Unified pixel-based positioning (origin at top-left)"
        ]

        return "\n".join(context_lines)

    def _build_spatial_section(self, context: ReasoningContext) -> str:
        """Build the spatial environment section."""
        try:
            assistant_state = context.assistant_state
            room_state = context.room_state

            assistant_pos = Position(
                assistant_state["position"]["x"],
                assistant_state["position"]["y"]
            )

            visible_objects = []
            objects = room_state.get("objects", [])
            object_states = room_state.get("object_states", {})

            for obj in objects[:10]:  # Limit to first 10 objects for prompt length
                try:
                    # Extract position using unified format
                    obj_position = obj.get("position", {})
                    if isinstance(obj_position, dict):
                        obj_pos = Position.from_dict(obj_position)
                    elif "position_x" in obj and "position_y" in obj:
                        obj_pos = Position(obj["position_x"], obj["position_y"])
                    else:
                        continue

                    # Check if object is nearby
                    obj_distance = assistant_pos.distance_to(obj_pos)
                    if obj_distance <= NEARBY_DISTANCE:
                        states = object_states.get(obj["id"], {})
                        state_desc = ", ".join([f"{k}:{v}" for k, v in states.items()]) if states else "default"

                        # Add movability information
                        is_movable = obj.get("properties", {}).get("movable", False)
                        movable_desc = " [MOVABLE]" if is_movable else ""

                        visible_objects.append(
                            f"- {obj['name']} ({obj['id']}) at ({int(obj_pos.x)}, {int(obj_pos.y)}) "
                            f"distance: {int(obj_distance)}px - {state_desc}{movable_desc}"
                        )

                except Exception as e:
                    self.logger.warning(f"Error processing object {obj.get('id', 'unknown')}: {e}")
                    continue

            objects_section = "\n".join(visible_objects) if visible_objects else "- No objects in immediate vicinity"

            return f"VISIBLE OBJECTS:\n{objects_section}"

        except Exception as e:
            self.logger.warning(f"Error building spatial section: {e}")
            return "VISIBLE OBJECTS:\n- Unable to analyze spatial environment"

    def _build_memory_section(self, conversation_context: List[Any]) -> str:
        """Build the memory context section."""
        try:
            if not conversation_context:
                return ""

            # Separate recent from retrieved memories
            from app.services.conversation_memory import conversation_memory
            recent_size = getattr(conversation_memory, 'recent_context_size', 20)

            recent_messages = conversation_context[-recent_size:] if len(conversation_context) > recent_size else conversation_context
            retrieved_messages = conversation_context[:-recent_size] if len(conversation_context) > recent_size else []

            memory_parts = []

            if retrieved_messages:
                memory_parts.append("RELEVANT CONVERSATION HISTORY (Retrieved from memory):")
                for msg in retrieved_messages[:5]:  # Limit to 5 retrieved messages
                    content = getattr(msg, 'content', str(msg))[:100]  # Limit content length
                    role = getattr(msg, 'role', 'unknown').upper()
                    memory_parts.append(f"{role}: {content}")

            if recent_messages:
                memory_parts.append("RECENT CONVERSATION:")
                for msg in recent_messages[-10:]:  # Limit to last 10 recent messages
                    content = getattr(msg, 'content', str(msg))[:100]
                    role = getattr(msg, 'role', 'unknown').upper()
                    memory_parts.append(f"{role}: {content}")

            if retrieved_messages:
                memory_parts.append(f"The Memory Keeper has access to {len(retrieved_messages)} relevant past messages and {len(recent_messages)} recent messages.")

            return "\n".join(memory_parts)

        except Exception as e:
            self.logger.warning(f"Error building memory section: {e}")
            return "CONVERSATION CONTEXT:\n- Unable to retrieve conversation history"

    def _build_council_perspectives_section(self) -> str:
        """Build the council perspectives section."""
        return """COUNCIL PERSPECTIVES:

1. PERSONALITY CORE: How should the assistant respond based on the active persona? What tone, style, and personality traits should be expressed?

2. MEMORY KEEPER: What relevant context from past interactions should inform this response? Any patterns or preferences to remember?

3. SPATIAL REASONER: Analyze the spatial environment and object relationships:
   - What objects are visible and within interaction range?
   - Which objects are movable and could be picked up?
   - What surfaces or locations could objects be placed on?
   - Are there any spatial constraints or obstacles?
   - How would object manipulation affect the room layout?

4. ACTION PLANNER: What specific actions could the assistant take? Consider:
   - Movement: Should it move to a different location?
   - Object Interaction: Activate, examine, or use nearby objects?
   - Object Manipulation: Pick up movable objects or put down held items?
   - State Changes: Modify object properties (power, open/closed, etc.)?
   What's physically possible given distance and object properties?

5. VALIDATOR: Validate all proposed actions for safety and feasibility:
   - Are movement actions possible given obstacles and room boundaries?
   - Is the assistant close enough for object interactions?
   - For pick up: Is the object movable and assistant not already holding something?
   - For put down: Is the target location free of collisions and within reach?
   - Do all actions align with the persona and make logical sense?"""

    def _build_response_format_section(self) -> str:
        """Build the response format section."""
        return """RESPOND IN JSON FORMAT:
{
    "council_reasoning": {
        "personality_core": "personality-based response analysis",
        "memory_keeper": "relevant context and patterns",
        "spatial_reasoner": "spatial analysis and object awareness",
        "action_planner": "proposed actions and movements",
        "validator": "validation of proposed actions"
    },
    "response": "natural conversational response to user",
    "actions": [
        {
            "type": "move|interact|state_change|pick_up|put_down|expression",
            "target": "coordinates or object_id",
            "parameters": {"key": "value"}
        }
    ],
    "mood": "emotional state after interaction",
    "reasoning": "brief explanation of decision"
}

Focus on creating natural, contextual responses that integrate the virtual environment."""

    def _build_reasoner_introduction(self, reasoner_name: str) -> str:
        """Build introduction for specific reasoner."""
        introductions = {
            "personality_core": "You are the Personality Core of the Brain Council, responsible for maintaining character consistency and determining appropriate response tone and style.",
            "memory_keeper": "You are the Memory Keeper of the Brain Council, responsible for retrieving relevant context from past interactions and identifying conversation patterns.",
            "spatial_reasoner": "You are the Spatial Reasoner of the Brain Council, responsible for analyzing the room environment, object positions, and spatial relationships.",
            "action_planner": "You are the Action Planner of the Brain Council, responsible for proposing specific actions and movements based on user intent and environmental context.",
            "validator": "You are the Validator of the Brain Council, responsible for ensuring all proposed actions are safe, feasible, and appropriate."
        }

        return introductions.get(reasoner_name, f"You are the {reasoner_name} component of the Brain Council.")

    def _build_reasoner_context(self, reasoner_name: str, context: ReasoningContext) -> str:
        """Build context section for specific reasoner."""
        try:
            if reasoner_name == "personality_core":
                return self._build_persona_section(context.persona_context) if context.persona_context else "No active persona - use default friendly assistant personality."

            elif reasoner_name == "memory_keeper":
                return self._build_memory_section(context.conversation_context) if context.conversation_context else "No conversation history available."

            elif reasoner_name == "spatial_reasoner":
                return self._build_spatial_section(context)

            elif reasoner_name in ["action_planner", "validator"]:
                # Both need full context
                parts = [
                    self._build_current_context_section(context),
                    self._build_spatial_section(context)
                ]
                return "\n\n".join(parts)

            else:
                return f"USER MESSAGE: {context.user_message}"

        except Exception as e:
            self.logger.warning(f"Error building context for {reasoner_name}: {e}")
            return f"USER MESSAGE: {context.user_message}"

    def _build_reasoner_analysis_request(self, reasoner_name: str) -> str:
        """Build analysis request for specific reasoner."""
        requests = {
            "personality_core": "Analyze the personality requirements for the response. Consider persona traits, appropriate tone, and character consistency. Provide reasoning for your recommendations.",
            "memory_keeper": "Analyze relevant conversation context and patterns. Identify key information from past interactions that should inform the current response.",
            "spatial_reasoner": "Analyze the spatial environment and object relationships. Identify interaction opportunities, movement possibilities, and spatial constraints.",
            "action_planner": "Analyze user intent and propose appropriate actions. Consider movement, object interaction, manipulation, and state changes that align with the request.",
            "validator": "Validate all aspects for safety and feasibility. Check physical constraints, interaction distances, object properties, and persona alignment."
        }

        return requests.get(reasoner_name, "Provide your analysis of the situation.")

    def _build_fallback_prompt(self, user_message: str) -> str:
        """Build a simple fallback prompt when the main prompt fails."""
        return f"""You are an AI assistant. Respond to this user message in a helpful and contextual way:

USER MESSAGE: "{user_message}"

Provide a natural response that acknowledges the user's request."""


# Global instance for easy access
prompt_builder = PromptBuilder()