"""
Brain Council - Multi-perspective AI reasoning system for DeskMate.

The Brain Council uses 5 specialized council members to process user requests
and generate contextual responses that integrate with the room environment:

1. Personality Core - Maintains character consistency with selected persona
2. Memory Keeper - Retrieves relevant context from conversations and events
3. Spatial Reasoner - Understands room layout, object positions, and visibility
4. Action Planner - Proposes possible actions (movement, object interaction)
5. Validator - Ensures actions make sense and are physically possible

The council returns structured responses that drive both chat and room actions.
"""

import logging
import json
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.services.assistant_service import assistant_service
from app.services.room_service import room_service
from app.services.llm_manager import llm_manager, ChatMessage
from app.services.conversation_memory import conversation_memory
from app.exceptions import (
    BrainCouncilError, DatabaseError, AIServiceError,
    ValidationError, wrap_exception
)

logger = logging.getLogger(__name__)


class CoordinateSystem:
    """Utility class for handling different coordinate systems."""

    # Grid system constants (legacy)
    GRID_WIDTH = 64
    GRID_HEIGHT = 16
    GRID_CELL_SIZE = 30  # pixels per cell

    # Open plan constants (new system)
    DEFAULT_FLOOR_WIDTH = 1300  # pixels
    DEFAULT_FLOOR_HEIGHT = 600  # pixels

    @staticmethod
    def is_grid_coordinate(x: float, y: float) -> bool:
        """Check if coordinates appear to be grid-based (small integers)."""
        return (
            isinstance(x, int) and isinstance(y, int) and
            0 <= x < CoordinateSystem.GRID_WIDTH and
            0 <= y < CoordinateSystem.GRID_HEIGHT
        )

    @staticmethod
    def calculate_distance(pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate distance between two positions, handling both coordinate systems."""
        x1, y1 = pos1.get("x", 0), pos1.get("y", 0)
        x2, y2 = pos2.get("x", 0), pos2.get("y", 0)

        # Use Euclidean distance for both systems
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    @staticmethod
    def get_interaction_distance_threshold(assistant_pos: Dict[str, float]) -> float:
        """Get distance threshold for interaction based on coordinate system."""
        x, y = assistant_pos.get("x", 0), assistant_pos.get("y", 0)

        if CoordinateSystem.is_grid_coordinate(x, y):
            # Grid system: 2 cells distance
            return 2.0
        else:
            # Pixel system: 80 pixels distance (about 2.5 grid cells)
            return 80.0

    @staticmethod
    def get_nearby_distance_threshold(assistant_pos: Dict[str, float]) -> float:
        """Get distance threshold for nearby objects based on coordinate system."""
        x, y = assistant_pos.get("x", 0), assistant_pos.get("y", 0)

        if CoordinateSystem.is_grid_coordinate(x, y):
            # Grid system: 5 cells distance
            return 5.0
        else:
            # Pixel system: 150 pixels distance (about 5 grid cells)
            return 150.0

    @staticmethod
    def describe_coordinate_system(assistant_pos: Dict[str, float]) -> str:
        """Describe which coordinate system is being used."""
        x, y = assistant_pos.get("x", 0), assistant_pos.get("y", 0)

        if CoordinateSystem.is_grid_coordinate(x, y):
            return f"grid-based coordinates (64x16 cells, assistant at cell {int(x)},{int(y)})"
        else:
            return f"pixel-based coordinates (open floor plan, assistant at {int(x)},{int(y)} pixels)"


class BrainCouncil:
    """Multi-perspective AI reasoning system for contextual responses."""

    async def process_user_message(
        self,
        user_message: str,
        persona_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process user message through Brain Council reasoning.

        Returns:
        {
            "response": "text response to user",
            "actions": [
                {
                    "type": "move" | "interact" | "state_change",
                    "target": "object_id or coordinates",
                    "parameters": {...}
                }
            ],
            "mood": "happy" | "confused" | "excited" etc,
            "reasoning": "explanation of decision process"
        }
        """
        try:
            logger.info(f"Brain Council processing message: {user_message[:50]}...")

            # Gather current context
            logger.info("Step 1: Gathering context...")
            context = await self._gather_context()
            logger.info("Step 1: Context gathered successfully")

            # Build council prompt with full environmental awareness
            logger.info("Step 2: Building council prompt...")
            council_prompt = await self._build_council_prompt(
                user_message, context, persona_context
            )
            logger.info("Step 2: Council prompt built successfully")

            # Get council reasoning
            logger.info("Step 3: Querying council (LLM)...")
            council_response = await self._query_council(council_prompt, user_message, persona_context)
            logger.info("Step 3: Council query completed")

            # Parse and validate council decision
            logger.info("Step 4: Parsing council response...")
            decision = await self._parse_council_response(council_response)
            logger.info("Step 4: Council response parsed successfully")

            return decision

        except BrainCouncilError as e:
            logger.error(f"Brain Council error in process_user_message: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            return {
                "response": "I'm having trouble processing that request right now.",
                "actions": [],
                "mood": "confused",
                "reasoning": f"Processing error: {e.message}"
            }
        except AIServiceError as e:
            logger.error(f"AI service error in process_user_message: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            return {
                "response": "I'm experiencing technical difficulties with my AI systems.",
                "actions": [],
                "mood": "confused",
                "reasoning": f"AI service error: {e.message}"
            }
        except DatabaseError as e:
            logger.error(f"Database error in process_user_message: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            return {
                "response": "I'm having trouble accessing my memory right now.",
                "actions": [],
                "mood": "confused",
                "reasoning": f"Memory error: {e.message}"
            }
        except Exception as e:
            # Wrap unknown exceptions for better error tracking
            wrapped_exception = wrap_exception(e, {
                "step": "process_user_message",
                "user_message_length": len(user_message) if user_message else 0
            })
            logger.error(f"Unexpected error in Brain Council process_user_message: {wrapped_exception.message}",
                        extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                        exc_info=True)
            return {
                "response": "I'm having trouble processing that request right now.",
                "actions": [],
                "mood": "confused",
                "reasoning": f"Unexpected error: {wrapped_exception.message}"
            }

    async def _gather_context(self) -> Dict[str, Any]:
        """Gather current room and assistant state."""
        try:
            logger.info("Brain Council gathering context...")

            # Get assistant state
            logger.info("Fetching assistant state...")
            assistant_state = await assistant_service.get_assistant_state()
            logger.info(f"Assistant state type: {type(assistant_state)}")
            logger.info(f"Assistant state attributes: {dir(assistant_state)}")

            if hasattr(assistant_state, 'position_x'):
                logger.info(f"Assistant position_x: {assistant_state.position_x}")
            else:
                logger.error("Assistant state missing position_x attribute!")
                logger.info(f"Assistant state dict: {assistant_state.__dict__ if hasattr(assistant_state, '__dict__') else 'No __dict__'}")

            # Get all room objects
            logger.info("Fetching room objects...")
            objects = await room_service.get_all_objects()

            # Get object states
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
        except DatabaseError as e:
            logger.error(f"Database error gathering context: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            # Return fallback with sensible default position for open-plan system
            return {
                "assistant": {
                    "position": {"x": 650, "y": 300},  # Center of typical floor plan
                    "facing": "right",
                    "action": "idle",
                    "mood": "neutral",
                    "holding_object_id": None
                },
                "room": {"objects": [], "object_states": {}, "timestamp": datetime.now().isoformat()}
            }
        except Exception as e:
            # Wrap unknown exceptions for better error tracking
            wrapped_exception = wrap_exception(e, {"step": "gather_context"})
            logger.error(f"Unexpected error gathering context: {wrapped_exception.message}",
                        extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                        exc_info=True)
            # Return fallback with sensible default position for open-plan system
            return {
                "assistant": {
                    "position": {"x": 650, "y": 300},  # Center of typical floor plan
                    "facing": "right",
                    "action": "idle",
                    "mood": "neutral",
                    "holding_object_id": None
                },
                "room": {"objects": [], "object_states": {}, "timestamp": datetime.now().isoformat()}
            }

    async def _build_council_prompt(
        self,
        user_message: str,
        context: Dict[str, Any],
        persona_context: Optional[Dict] = None
    ) -> str:
        """Build the Brain Council reasoning prompt."""

        persona_info = ""
        if persona_context:
            persona_info = f"""
ACTIVE PERSONA: {persona_context.get('name', 'Default')}
Personality: {persona_context.get('personality', 'Friendly AI assistant')}
Creator: {persona_context.get('creator', 'Unknown')}
"""

        # Create spatial awareness description
        visible_objects = []
        for obj in context["room"]["objects"]:
            try:
                # Safely extract position - handle both nested and flat formats
                if isinstance(obj.get("position"), dict):
                    obj_x = obj["position"]["x"]
                    obj_y = obj["position"]["y"]
                elif "position_x" in obj and "position_y" in obj:
                    # Fallback for flat format
                    obj_x = obj["position_x"]
                    obj_y = obj["position_y"]
                else:
                    logger.warning(f"Object {obj.get('id', 'unknown')} has invalid position format: {obj}")
                    continue

                # Calculate distance from assistant using coordinate-aware method
                assistant_pos = context["assistant"]["position"]
                obj_pos = {"x": obj_x, "y": obj_y}
                distance = CoordinateSystem.calculate_distance(assistant_pos, obj_pos)
                view_threshold = CoordinateSystem.get_nearby_distance_threshold(assistant_pos)

                if distance <= view_threshold:  # Within reasonable "view" distance
                    states = context["room"]["object_states"].get(obj["id"], {})
                    state_desc = ", ".join([f"{k}:{v}" for k, v in states.items()]) if states else "default"

                    # Add movability information
                    is_movable = obj.get("properties", {}).get("movable", False)
                    movable_desc = " [MOVABLE]" if is_movable else ""

                    visible_objects.append(f"- {obj['name']} ({obj['id']}) at ({obj_x}, {obj_y}) - {state_desc}{movable_desc}")
            except KeyError as e:
                # Wrap KeyError as ValidationError for better error tracking
                validation_error = ValidationError(
                    f"Invalid object structure for object {obj.get('id', 'unknown')}: missing required field {str(e)}",
                    details={"object_structure": obj, "missing_field": str(e)}
                )
                logger.error(f"Object validation error: {validation_error.message}",
                           extra={"error_code": validation_error.error_code, "details": validation_error.details})
                continue
            except Exception as e:
                # Wrap unknown exceptions for better error tracking
                wrapped_exception = wrap_exception(e, {
                    "step": "object_processing",
                    "object_id": obj.get('id', 'unknown'),
                    "object_structure": obj
                })
                logger.error(f"Error processing object {obj.get('id', 'unknown')}: {wrapped_exception.message}",
                           extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
                continue

        prompt = f"""
You are the Brain Council for a virtual AI companion. Process this user request using 5 council perspectives:

USER MESSAGE: "{user_message}"

{persona_info}

CURRENT CONTEXT:
Assistant Position: ({context["assistant"]["position"]["x"]}, {context["assistant"]["position"]["y"]})
Assistant Status: {context["assistant"]["action"]}, facing {context["assistant"]["facing"]}, mood: {context["assistant"]["mood"]}
Holding: {context["assistant"]["holding_object_id"] or "nothing"}
Coordinate System: {CoordinateSystem.describe_coordinate_system(context["assistant"]["position"])}

VISIBLE OBJECTS:
{chr(10).join(visible_objects) if visible_objects else "- No objects in immediate vicinity"}

COUNCIL PERSPECTIVES:

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
   - Do all actions align with the persona and make logical sense?

RESPOND IN JSON FORMAT:
{{
    "council_reasoning": {{
        "personality_core": "personality-based response analysis",
        "memory_keeper": "relevant context and patterns",
        "spatial_reasoner": "spatial analysis and object awareness",
        "action_planner": "proposed actions and movements",
        "validator": "validation of proposed actions"
    }},
    "response": "natural conversational response to user",
    "actions": [
        {{
            "type": "move|interact|state_change|pick_up|put_down|expression",
            "target": "coordinates or object_id",
            "parameters": {{"key": "value"}}
        }}
    ],
    "mood": "emotional state after interaction",
    "reasoning": "brief explanation of decision"
}}

Focus on creating natural, contextual responses that integrate the virtual environment.
"""
        return prompt

    async def _query_council(self, prompt: str, user_message: str = "", persona_context: Optional[Dict] = None) -> str:
        """Query the LLM with the council prompt using conversation memory."""
        try:
            # Get conversation context including relevant memories
            persona_name = persona_context.get("name") if persona_context else None
            context_messages = await conversation_memory.get_conversation_context(
                current_message=user_message,
                persona_name=persona_name
            )

            # Add conversation context to the prompt if we have memories
            memory_context = ""
            if len(context_messages) > conversation_memory.recent_context_size:
                retrieved_count = len(context_messages) - conversation_memory.recent_context_size
                memory_context = f"""

RELEVANT CONVERSATION HISTORY (Retrieved from memory):
{chr(10).join([f"{msg.role.upper()}: {msg.content}" for msg in context_messages[:-conversation_memory.recent_context_size]])}

RECENT CONVERSATION:
{chr(10).join([f"{msg.role.upper()}: {msg.content}" for msg in context_messages[-conversation_memory.recent_context_size:]])}

The Memory Keeper has access to {retrieved_count} relevant past messages and {conversation_memory.recent_context_size} recent messages."""

            enhanced_prompt = prompt + memory_context

            messages = [
                ChatMessage(role="system", content="You are the Brain Council reasoning system for a virtual AI companion. Always respond in valid JSON format. Use the conversation history to inform your Memory Keeper perspective."),
                ChatMessage(role="user", content=enhanced_prompt)
            ]

            response = ""
            async for chunk in llm_manager.chat_completion_stream(messages=messages, temperature=0.3):
                if chunk:
                    response += chunk

            logger.info(f"Brain Council raw LLM response: {response[:200]}...")
            return response.strip()
        except AIServiceError as e:
            logger.error(f"AI service error querying council: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            return '{"response": "I\'m experiencing technical difficulties with my AI systems.", "actions": [], "mood": "confused", "reasoning": "AI service error"}'
        except Exception as e:
            # Wrap unknown exceptions for better error tracking
            wrapped_exception = wrap_exception(e, {"step": "query_council"})
            logger.error(f"Unexpected error querying council: {wrapped_exception.message}",
                        extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                        exc_info=True)
            return '{"response": "I\'m having trouble processing that request right now.", "actions": [], "mood": "confused", "reasoning": "System error"}'

    async def _parse_council_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate the council response."""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                # Extract JSON portion
                start = response.find("{")
                end = response.rfind("}") + 1
                response = response[start:end]

            decision = json.loads(response)

            # Validate required fields
            required_fields = ["response", "actions", "mood"]
            for field in required_fields:
                if field not in decision:
                    decision[field] = self._get_default_value(field)

            # Validate actions format
            if not isinstance(decision["actions"], list):
                decision["actions"] = []

            return decision

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing council response: {e}")
            logger.error(f"Raw response: {response}")
            logger.error(f"Attempted to parse: {response[start:end] if 'start' in locals() and 'end' in locals() else 'No JSON extraction'}")

            # Return safe fallback
            return {
                "response": "I understand what you're asking, but I'm having trouble processing the details right now.",
                "actions": [],
                "mood": "neutral",
                "reasoning": "Failed to parse council decision"
            }

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields."""
        defaults = {
            "response": "I'm not sure how to respond to that.",
            "actions": [],
            "mood": "neutral",
            "reasoning": "Default response"
        }
        return defaults.get(field, "")

    async def process_idle_reasoning(self, idle_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process autonomous reasoning for idle mode using simplified council.

        Args:
            idle_context: Context including position, energy, objects, recent dreams, goals

        Returns:
            {
                "response": "description of autonomous action",
                "actions": [{"type": "action_type", "target": "target", "parameters": {...}}],
                "reasoning": "why this action was chosen"
            }
        """
        try:
            logger.info("Brain Council processing idle reasoning...")

            # Build simplified idle prompt
            idle_prompt = self._build_idle_prompt(idle_context)

            # Get reasoning using lightweight model
            response = await self._query_idle_council(idle_prompt)

            # Parse response
            decision = await self._parse_council_response(response)

            return decision

        except BrainCouncilError as e:
            logger.error(f"Brain Council error in idle reasoning: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            return {
                "response": "Continuing to rest and observe the room.",
                "actions": [{"type": "rest", "target": None, "parameters": {}}],
                "reasoning": f"Idle reasoning error: {e.message}"
            }
        except Exception as e:
            # Wrap unknown exceptions for better error tracking
            wrapped_exception = wrap_exception(e, {"step": "idle_reasoning"})
            logger.error(f"Unexpected error in idle reasoning: {wrapped_exception.message}",
                        extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                        exc_info=True)
            return {
                "response": "Continuing to rest and observe the room.",
                "actions": [{"type": "rest", "target": None, "parameters": {}}],
                "reasoning": f"Unexpected error: {wrapped_exception.message}"
            }

    def _build_idle_prompt(self, context: Dict[str, Any]) -> str:
        """Build simplified prompt for idle mode reasoning."""
        position = context.get("assistant_position", {"x": 32, "y": 8})
        energy = context.get("assistant_energy", 1.0)
        objects = context.get("room_objects", [])
        recent_dreams = context.get("recent_dreams", [])
        goals = context.get("goals", [])
        action_count = context.get("action_count", 0)

        # Get nearby objects for spatial awareness using coordinate-aware distance
        nearby_objects = []
        for obj in objects:
            obj_pos = obj.get("position", {})
            if obj_pos:  # Only process objects with valid positions
                distance = CoordinateSystem.calculate_distance(position, obj_pos)
                nearby_threshold = CoordinateSystem.get_nearby_distance_threshold(position)
                if distance <= nearby_threshold:
                    nearby_objects.append(f"{obj.get('name', 'object')} at ({obj_pos.get('x')}, {obj_pos.get('y')})")

        prompt = f"""You are an AI assistant in idle mode, thinking and acting autonomously while the user is away.

CURRENT SITUATION:
- Position: ({position['x']}, {position['y']})
- Energy Level: {energy:.1f}/1.0
- Actions Taken: {action_count}
- Nearby Objects: {', '.join(nearby_objects[:5]) if nearby_objects else 'none'}

RECENT AUTONOMOUS ACTIONS:
{chr(10).join(f"- {dream}" for dream in recent_dreams[-3:]) if recent_dreams else "- None yet"}

CURRENT GOALS:
{chr(10).join(f"- {goal}" for goal in goals)}

IDLE MODE GUIDELINES:
- Take simple, low-energy actions
- Explore the room gradually
- Interact with interesting objects
- Rest when energy is low
- Be curious but not disruptive
- Actions should be realistic and character-appropriate

Choose ONE simple action to take right now. Options:
- move: Move to a nearby location {"x": X, "y": Y}
- interact: Interact with an object by ID
- state_change: Change mood or expression
- rest: Restore energy and think

Respond in JSON format:
{{
    "response": "What I'm doing (in character)",
    "actions": [{{
        "type": "action_type",
        "target": "coordinates or object_id or null",
        "parameters": {{}}
    }}],
    "reasoning": "Why I chose this action"
}}"""

        return prompt

    async def _query_idle_council(self, prompt: str) -> str:
        """Query LLM with idle-specific prompt."""
        try:
            messages = [
                ChatMessage(role="system", content="You are an autonomous AI assistant in idle mode. Respond in JSON format only."),
                ChatMessage(role="user", content=prompt)
            ]

            response = ""
            async for chunk in llm_manager.chat_completion_stream(messages=messages, temperature=0.4):
                if chunk:
                    response += chunk

            logger.info(f"Idle Council raw response: {response[:200]}...")
            return response.strip()

        except AIServiceError as e:
            logger.error(f"AI service error querying idle council: {e.message}", extra={"error_code": e.error_code, "details": e.details})
            return '{"response": "Observing the room quietly.", "actions": [{"type": "rest", "target": null}], "reasoning": "AI service error in idle mode"}'
        except Exception as e:
            # Wrap unknown exceptions for better error tracking
            wrapped_exception = wrap_exception(e, {"step": "query_idle_council"})
            logger.error(f"Unexpected error querying idle council: {wrapped_exception.message}",
                        extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                        exc_info=True)
            return '{"response": "Observing the room quietly.", "actions": [{"type": "rest", "target": null}], "reasoning": "System error in idle mode"}'


# Global instance
brain_council = BrainCouncil()