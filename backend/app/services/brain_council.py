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
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.assistant_service import assistant_service
from app.services.room_service import room_service
from app.services.llm_manager import llm_manager, ChatMessage
from app.services.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)


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

        except Exception as e:
            logger.error(f"ERROR in Brain Council process_user_message: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            # Return safe fallback
            return {
                "response": "I'm having trouble processing that request right now.",
                "actions": [],
                "mood": "confused",
                "reasoning": f"Brain Council error: {str(e)}"
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
                    "mood": assistant_state.mood
                },
                "room": {
                    "objects": objects,
                    "object_states": object_states,
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "assistant": {"position": {"x": 32, "y": 8}, "facing": "right", "action": "idle", "mood": "neutral"},
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

                # Calculate distance from assistant
                assistant_pos = context["assistant"]["position"]
                distance = abs(obj_x - assistant_pos["x"]) + abs(obj_y - assistant_pos["y"])

                if distance <= 10:  # Within reasonable "view" distance
                    states = context["room"]["object_states"].get(obj["id"], {})
                    state_desc = ", ".join([f"{k}:{v}" for k, v in states.items()]) if states else "default"
                    visible_objects.append(f"- {obj['name']} ({obj['id']}) at ({obj_x}, {obj_y}) - {state_desc}")
            except KeyError as e:
                logger.error(f"KeyError processing object {obj.get('id', 'unknown')}: {e}")
                logger.error(f"Object structure: {obj}")
                continue
            except Exception as e:
                logger.error(f"Error processing object {obj.get('id', 'unknown')}: {e}")
                continue

        prompt = f"""
You are the Brain Council for a virtual AI companion. Process this user request using 5 council perspectives:

USER MESSAGE: "{user_message}"

{persona_info}

CURRENT CONTEXT:
Assistant Position: ({context["assistant"]["position"]["x"]}, {context["assistant"]["position"]["y"]})
Assistant Status: {context["assistant"]["action"]}, facing {context["assistant"]["facing"]}, mood: {context["assistant"]["mood"]}

VISIBLE OBJECTS:
{chr(10).join(visible_objects) if visible_objects else "- No objects in immediate vicinity"}

COUNCIL PERSPECTIVES:

1. PERSONALITY CORE: How should the assistant respond based on the active persona? What tone, style, and personality traits should be expressed?

2. MEMORY KEEPER: What relevant context from past interactions should inform this response? Any patterns or preferences to remember?

3. SPATIAL REASONER: What objects are visible and reachable? What movement or positioning would make sense? Are there spatial constraints?

4. ACTION PLANNER: What specific actions could the assistant take? Should it move, interact with objects, or change states? What's physically possible?

5. VALIDATOR: Do the proposed actions make sense? Are they safe and appropriate? Any conflicts or issues?

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
            "type": "move|interact|state_change",
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

            return response.strip()
        except Exception as e:
            logger.error(f"Error querying council: {e}")
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


# Global instance
brain_council = BrainCouncil()