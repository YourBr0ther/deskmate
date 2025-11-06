"""
Action Reasoner - Proposes possible actions and movements.

This reasoner focuses on:
- Analyzing user intent and determining appropriate actions
- Proposing movement, interaction, and manipulation actions
- Considering action sequences and priorities
- Matching user requests to available capabilities
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import re

from ..base import BaseReasoner, ReasoningContext, ReasoningResult
from app.utils.coordinate_system import (
    Position, distance, can_interact,
    ROOM_WIDTH, ROOM_HEIGHT, INTERACTION_DISTANCE
)

logger = logging.getLogger(__name__)


class ActionReasoner(BaseReasoner):
    """
    Reasoner responsible for action planning and movement suggestions.

    Analyzes user requests and environmental context to propose appropriate
    actions including movement, object interaction, and state changes.
    """

    def __init__(self):
        super().__init__("action_planner")

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Analyze user request and propose appropriate actions.

        Args:
            context: The reasoning context

        Returns:
            ReasoningResult with action planning analysis
        """
        try:
            user_message = context.user_message
            assistant_state = context.assistant_state
            room_state = context.room_state
            persona_context = context.persona_context

            # Analyze user intent
            intent_analysis = self._analyze_user_intent(user_message)

            # Get assistant position and capabilities
            assistant_position = Position(
                assistant_state["position"]["x"],
                assistant_state["position"]["y"]
            )

            # Propose actions based on intent and environment
            proposed_actions = self._propose_actions(
                intent_analysis, assistant_position, assistant_state, room_state
            )

            # Prioritize actions
            prioritized_actions = self._prioritize_actions(proposed_actions, intent_analysis)

            # Generate action reasoning
            reasoning = self._build_action_reasoning(
                intent_analysis, proposed_actions, prioritized_actions
            )

            metadata = {
                "detected_intent": intent_analysis,
                "proposed_actions_count": len(proposed_actions),
                "high_priority_actions": len([a for a in proposed_actions if a.get("priority") == "high"]),
                "action_categories": list(set(a.get("category", "unknown") for a in proposed_actions))
            }

            return self._create_result(
                reasoning=reasoning,
                confidence=0.9,
                metadata=metadata
            )

        except Exception as e:
            return self._handle_error(e, "action planning")

    def _analyze_user_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Analyze user message to determine intent and desired actions.

        Args:
            user_message: User's message to analyze

        Returns:
            Dictionary containing intent analysis
        """
        try:
            message_lower = user_message.lower()

            # Define intent patterns
            intent_patterns = {
                "movement": {
                    "keywords": ["go", "move", "walk", "travel", "come", "head", "position"],
                    "patterns": [r"go to", r"move to", r"walk to", r"come here", r"go over"],
                    "confidence_boost": 0.3
                },
                "object_interaction": {
                    "keywords": ["use", "activate", "turn", "press", "click", "touch", "interact"],
                    "patterns": [r"turn on", r"turn off", r"open", r"close", r"activate"],
                    "confidence_boost": 0.4
                },
                "object_manipulation": {
                    "keywords": ["pick", "grab", "take", "get", "put", "place", "drop", "set"],
                    "patterns": [r"pick up", r"put down", r"place on", r"set down"],
                    "confidence_boost": 0.5
                },
                "exploration": {
                    "keywords": ["look", "see", "explore", "find", "search", "show", "what"],
                    "patterns": [r"look at", r"show me", r"what's", r"where is"],
                    "confidence_boost": 0.2
                },
                "conversation": {
                    "keywords": ["tell", "say", "explain", "describe", "talk", "chat"],
                    "patterns": [r"tell me", r"how are you", r"what do you think"],
                    "confidence_boost": 0.1
                },
                "expression": {
                    "keywords": ["feel", "mood", "emotion", "expression", "happy", "sad"],
                    "patterns": [r"how do you feel", r"change your", r"be happy"],
                    "confidence_boost": 0.3
                }
            }

            # Score each intent category
            intent_scores = {}
            detected_objects = self._extract_mentioned_objects(user_message)
            detected_locations = self._extract_mentioned_locations(user_message)

            for intent_type, intent_data in intent_patterns.items():
                score = 0.0

                # Check for keywords
                keyword_matches = sum(1 for keyword in intent_data["keywords"] if keyword in message_lower)
                score += keyword_matches * 0.2

                # Check for patterns
                pattern_matches = sum(1 for pattern in intent_data["patterns"]
                                    if re.search(pattern, message_lower))
                score += pattern_matches * intent_data["confidence_boost"]

                # Boost score for object mentions in relevant intents
                if detected_objects and intent_type in ["object_interaction", "object_manipulation", "exploration"]:
                    score += 0.2

                # Boost score for location mentions in movement intent
                if detected_locations and intent_type == "movement":
                    score += 0.3

                intent_scores[intent_type] = min(score, 1.0)  # Cap at 1.0

            # Determine primary intent
            primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "conversation"
            primary_confidence = intent_scores.get(primary_intent, 0.1)

            # Get secondary intents
            secondary_intents = [
                intent for intent, score in intent_scores.items()
                if intent != primary_intent and score > 0.3
            ]

            return {
                "primary_intent": primary_intent,
                "primary_confidence": primary_confidence,
                "secondary_intents": secondary_intents,
                "all_intent_scores": intent_scores,
                "mentioned_objects": detected_objects,
                "mentioned_locations": detected_locations,
                "action_urgency": self._assess_action_urgency(user_message),
                "requires_response": True  # Most user messages require a response
            }

        except Exception as e:
            logger.warning(f"Error analyzing user intent: {e}")
            return {
                "primary_intent": "conversation",
                "primary_confidence": 0.5,
                "secondary_intents": [],
                "all_intent_scores": {},
                "mentioned_objects": [],
                "mentioned_locations": [],
                "action_urgency": "normal",
                "requires_response": True
            }

    def _extract_mentioned_objects(self, message: str) -> List[str]:
        """Extract object names mentioned in the message."""
        try:
            # Common object names and synonyms
            object_keywords = [
                "book", "chair", "desk", "table", "lamp", "computer", "screen", "monitor",
                "door", "window", "bed", "couch", "sofa", "plant", "light", "switch",
                "phone", "keyboard", "mouse", "bottle", "cup", "glass", "remote", "tv",
                "television", "radio", "clock", "picture", "painting", "mirror"
            ]

            message_lower = message.lower()
            found_objects = []

            for obj_name in object_keywords:
                if obj_name in message_lower:
                    found_objects.append(obj_name)

            return found_objects[:5]  # Return up to 5 objects

        except Exception:
            return []

    def _extract_mentioned_locations(self, message: str) -> List[str]:
        """Extract location references from the message."""
        try:
            location_patterns = [
                r"over there", r"here", r"there", r"near", r"beside", r"next to",
                r"center", r"middle", r"corner", r"edge", r"side", r"front", r"back",
                r"left", r"right", r"up", r"down", r"north", r"south", r"east", r"west"
            ]

            message_lower = message.lower()
            found_locations = []

            for pattern in location_patterns:
                if re.search(pattern, message_lower):
                    found_locations.append(pattern.replace("r", "").strip("'"))

            return found_locations[:3]  # Return up to 3 location references

        except Exception:
            return []

    def _assess_action_urgency(self, message: str) -> str:
        """Assess the urgency of the requested action."""
        try:
            message_lower = message.lower()

            urgent_indicators = ["now", "immediately", "quickly", "urgent", "asap", "right now", "hurry"]
            casual_indicators = ["maybe", "perhaps", "when you can", "sometime", "eventually"]

            if any(indicator in message_lower for indicator in urgent_indicators):
                return "high"
            elif any(indicator in message_lower for indicator in casual_indicators):
                return "low"
            else:
                return "normal"

        except Exception:
            return "normal"

    def _propose_actions(self, intent_analysis: Dict[str, Any],
                        assistant_position: Position,
                        assistant_state: Dict[str, Any],
                        room_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Propose specific actions based on intent and environment.

        Args:
            intent_analysis: Results from intent analysis
            assistant_position: Current assistant position
            assistant_state: Current assistant state
            room_state: Current room state

        Returns:
            List of proposed action dictionaries
        """
        try:
            proposed_actions = []
            primary_intent = intent_analysis["primary_intent"]
            mentioned_objects = intent_analysis["mentioned_objects"]
            mentioned_locations = intent_analysis["mentioned_locations"]

            # Get available objects
            room_objects = room_state.get("objects", [])

            if primary_intent == "movement":
                movement_actions = self._propose_movement_actions(
                    assistant_position, mentioned_locations, room_objects
                )
                proposed_actions.extend(movement_actions)

            elif primary_intent == "object_interaction":
                interaction_actions = self._propose_interaction_actions(
                    assistant_position, mentioned_objects, room_objects, room_state
                )
                proposed_actions.extend(interaction_actions)

            elif primary_intent == "object_manipulation":
                manipulation_actions = self._propose_manipulation_actions(
                    assistant_position, mentioned_objects, room_objects, assistant_state
                )
                proposed_actions.extend(manipulation_actions)

            elif primary_intent == "exploration":
                exploration_actions = self._propose_exploration_actions(
                    assistant_position, mentioned_objects, room_objects
                )
                proposed_actions.extend(exploration_actions)

            elif primary_intent == "expression":
                expression_actions = self._propose_expression_actions(intent_analysis)
                proposed_actions.extend(expression_actions)

            # Add general fallback actions if no specific actions proposed
            if not proposed_actions:
                proposed_actions.extend(self._propose_fallback_actions(assistant_position, room_objects))

            return proposed_actions[:10]  # Return up to 10 actions

        except Exception as e:
            logger.warning(f"Error proposing actions: {e}")
            return []

    def _propose_movement_actions(self, current_pos: Position,
                                mentioned_locations: List[str],
                                room_objects: List[Dict]) -> List[Dict[str, Any]]:
        """Propose movement actions."""
        actions = []

        # Movement to specific locations mentioned
        if mentioned_locations:
            for location in mentioned_locations:
                target_pos = self._interpret_location_reference(location, current_pos, room_objects)
                if target_pos:
                    actions.append({
                        "type": "move",
                        "target": target_pos.to_dict(),
                        "parameters": {},
                        "category": "movement",
                        "priority": "high",
                        "reasoning": f"Move to {location} as requested"
                    })

        # Movement toward objects for better interaction
        for obj in room_objects[:3]:  # Check first 3 objects
            try:
                obj_pos = self._get_object_position(obj)
                if obj_pos and distance(current_pos, obj_pos) > INTERACTION_DISTANCE:
                    # Move closer to object for potential interaction
                    approach_pos = self._calculate_approach_position(obj_pos)
                    actions.append({
                        "type": "move",
                        "target": approach_pos.to_dict(),
                        "parameters": {"approach_object": obj.get("id")},
                        "category": "movement",
                        "priority": "medium",
                        "reasoning": f"Move closer to {obj.get('name', 'object')} for interaction"
                    })
            except Exception:
                continue

        return actions

    def _propose_interaction_actions(self, current_pos: Position,
                                   mentioned_objects: List[str],
                                   room_objects: List[Dict],
                                   room_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Propose object interaction actions."""
        actions = []
        object_states = room_state.get("object_states", {})

        for obj in room_objects:
            try:
                obj_pos = self._get_object_position(obj)
                if not obj_pos or not can_interact(current_pos, obj_pos):
                    continue

                obj_name = obj.get("name", "").lower()
                obj_id = obj.get("id")

                # Check if this object was mentioned
                mentioned = any(name in obj_name for name in mentioned_objects)

                if mentioned or not mentioned_objects:  # Include if mentioned or no specific objects mentioned
                    # Propose appropriate interactions based on object states
                    states = object_states.get(obj_id, {})

                    if "power" in states:
                        current_power = states["power"]
                        new_power = "off" if current_power == "on" else "on"
                        actions.append({
                            "type": "interact",
                            "target": obj_id,
                            "parameters": {"interaction": "activate"},
                            "category": "interaction",
                            "priority": "high" if mentioned else "medium",
                            "reasoning": f"Toggle power on {obj.get('name')} (currently {current_power})"
                        })

                    if "open" in states:
                        current_state = states["open"]
                        new_state = "closed" if current_state == "open" else "open"
                        actions.append({
                            "type": "interact",
                            "target": obj_id,
                            "parameters": {"interaction": "activate"},
                            "category": "interaction",
                            "priority": "high" if mentioned else "medium",
                            "reasoning": f"{new_state.capitalize()} {obj.get('name')} (currently {current_state})"
                        })

                    # General examination
                    actions.append({
                        "type": "interact",
                        "target": obj_id,
                        "parameters": {"interaction": "examine"},
                        "category": "interaction",
                        "priority": "medium",
                        "reasoning": f"Examine {obj.get('name')} for details"
                    })

            except Exception:
                continue

        return actions

    def _propose_manipulation_actions(self, current_pos: Position,
                                    mentioned_objects: List[str],
                                    room_objects: List[Dict],
                                    assistant_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Propose object manipulation actions."""
        actions = []
        holding_object_id = assistant_state.get("holding_object_id")

        if holding_object_id:
            # Propose put down actions
            actions.append({
                "type": "put_down",
                "target": None,  # Default position
                "parameters": {},
                "category": "manipulation",
                "priority": "high",
                "reasoning": "Put down currently held object at current location"
            })

            # Propose placing on surfaces
            for obj in room_objects:
                if obj.get("properties", {}).get("surface", False):
                    try:
                        obj_pos = self._get_object_position(obj)
                        if obj_pos and can_interact(current_pos, obj_pos):
                            actions.append({
                                "type": "put_down",
                                "target": obj_pos.to_dict(),
                                "parameters": {"surface": obj.get("id")},
                                "category": "manipulation",
                                "priority": "medium",
                                "reasoning": f"Place held object on {obj.get('name')}"
                            })
                    except Exception:
                        continue

        else:
            # Propose pick up actions for movable objects
            for obj in room_objects:
                if not obj.get("properties", {}).get("movable", False):
                    continue

                try:
                    obj_pos = self._get_object_position(obj)
                    if not obj_pos or not can_interact(current_pos, obj_pos):
                        continue

                    obj_name = obj.get("name", "").lower()
                    mentioned = any(name in obj_name for name in mentioned_objects)

                    actions.append({
                        "type": "pick_up",
                        "target": obj.get("id"),
                        "parameters": {},
                        "category": "manipulation",
                        "priority": "high" if mentioned else "medium",
                        "reasoning": f"Pick up {obj.get('name')}"
                    })

                except Exception:
                    continue

        return actions

    def _propose_exploration_actions(self, current_pos: Position,
                                   mentioned_objects: List[str],
                                   room_objects: List[Dict]) -> List[Dict[str, Any]]:
        """Propose exploration actions."""
        actions = []

        # Examine nearby objects
        for obj in room_objects:
            try:
                obj_pos = self._get_object_position(obj)
                if obj_pos and can_interact(current_pos, obj_pos):
                    actions.append({
                        "type": "interact",
                        "target": obj.get("id"),
                        "parameters": {"interaction": "examine"},
                        "category": "exploration",
                        "priority": "medium",
                        "reasoning": f"Examine {obj.get('name')} to learn more about it"
                    })
            except Exception:
                continue

        # Movement for exploration
        exploration_points = [
            Position(ROOM_WIDTH * 0.25, ROOM_HEIGHT * 0.25),  # Southwest
            Position(ROOM_WIDTH * 0.75, ROOM_HEIGHT * 0.25),  # Southeast
            Position(ROOM_WIDTH * 0.75, ROOM_HEIGHT * 0.75),  # Northeast
            Position(ROOM_WIDTH * 0.25, ROOM_HEIGHT * 0.75),  # Northwest
            Position(ROOM_WIDTH * 0.5, ROOM_HEIGHT * 0.5),    # Center
        ]

        for i, point in enumerate(exploration_points):
            if distance(current_pos, point) > 100:  # Only suggest if not already close
                actions.append({
                    "type": "move",
                    "target": point.to_dict(),
                    "parameters": {"exploration": True},
                    "category": "exploration",
                    "priority": "low",
                    "reasoning": f"Explore different area of the room (point {i+1})"
                })

        return actions[:5]  # Return up to 5 exploration actions

    def _propose_expression_actions(self, intent_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Propose expression change actions."""
        actions = []

        # Analyze message for emotional content
        message = intent_analysis.get("user_message", "").lower()

        if any(word in message for word in ["happy", "joy", "excited", "good"]):
            actions.append({
                "type": "expression",
                "target": "happy",
                "parameters": {},
                "category": "expression",
                "priority": "medium",
                "reasoning": "Express happiness in response to positive message"
            })

        elif any(word in message for word in ["sad", "sorry", "bad", "upset"]):
            actions.append({
                "type": "expression",
                "target": "concerned",
                "parameters": {},
                "category": "expression",
                "priority": "medium",
                "reasoning": "Express concern in response to negative sentiment"
            })

        else:
            # Default to neutral or content expression
            actions.append({
                "type": "expression",
                "target": "content",
                "parameters": {},
                "category": "expression",
                "priority": "low",
                "reasoning": "Maintain content expression during conversation"
            })

        return actions

    def _propose_fallback_actions(self, current_pos: Position,
                                room_objects: List[Dict]) -> List[Dict[str, Any]]:
        """Propose fallback actions when no specific intent is detected."""
        actions = []

        # Simple greeting gesture
        actions.append({
            "type": "expression",
            "target": "friendly",
            "parameters": {},
            "category": "expression",
            "priority": "low",
            "reasoning": "Maintain friendly expression during conversation"
        })

        return actions

    def _prioritize_actions(self, proposed_actions: List[Dict[str, Any]],
                          intent_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize the proposed actions based on intent and context."""
        try:
            priority_order = {"high": 3, "medium": 2, "low": 1}
            urgency = intent_analysis.get("action_urgency", "normal")

            # Apply urgency modifier
            urgency_modifier = {"high": 1.2, "normal": 1.0, "low": 0.8}
            modifier = urgency_modifier.get(urgency, 1.0)

            for action in proposed_actions:
                base_priority = priority_order.get(action.get("priority", "low"), 1)
                action["calculated_priority"] = base_priority * modifier

            # Sort by calculated priority (descending)
            return sorted(proposed_actions, key=lambda x: x.get("calculated_priority", 0), reverse=True)

        except Exception as e:
            logger.warning(f"Error prioritizing actions: {e}")
            return proposed_actions

    def _get_object_position(self, obj: Dict[str, Any]) -> Optional[Position]:
        """Extract position from object data."""
        try:
            position_data = obj.get("position", {})
            if isinstance(position_data, dict):
                return Position.from_dict(position_data)
            else:
                return None
        except Exception:
            return None

    def _interpret_location_reference(self, location: str, current_pos: Position,
                                    room_objects: List[Dict]) -> Optional[Position]:
        """Interpret location references into specific coordinates."""
        try:
            location_lower = location.lower()

            # Predefined location mappings
            location_map = {
                "center": Position(ROOM_WIDTH / 2, ROOM_HEIGHT / 2),
                "middle": Position(ROOM_WIDTH / 2, ROOM_HEIGHT / 2),
                "corner": Position(ROOM_WIDTH * 0.2, ROOM_HEIGHT * 0.2),  # Default to one corner
                "left": Position(ROOM_WIDTH * 0.2, current_pos.y),
                "right": Position(ROOM_WIDTH * 0.8, current_pos.y),
                "front": Position(current_pos.x, ROOM_HEIGHT * 0.2),
                "back": Position(current_pos.x, ROOM_HEIGHT * 0.8)
            }

            return location_map.get(location_lower)

        except Exception:
            return None

    def _calculate_approach_position(self, target_pos: Position) -> Position:
        """Calculate a good position to approach an object."""
        # Simple approach: position 50 pixels away from object toward room center
        center = Position(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)
        dx = center.x - target_pos.x
        dy = center.y - target_pos.y

        # Normalize and scale to approach distance
        length = (dx*dx + dy*dy) ** 0.5
        if length > 0:
            approach_distance = 50
            approach_x = target_pos.x + (dx / length) * approach_distance
            approach_y = target_pos.y + (dy / length) * approach_distance

            # Keep within room bounds
            approach_x = max(0, min(ROOM_WIDTH, approach_x))
            approach_y = max(0, min(ROOM_HEIGHT, approach_y))

            return Position(approach_x, approach_y)

        return target_pos

    def _build_action_reasoning(self, intent_analysis: Dict[str, Any],
                              proposed_actions: List[Dict[str, Any]],
                              prioritized_actions: List[Dict[str, Any]]) -> str:
        """Build the action reasoning explanation."""
        reasoning_parts = []

        # Intent analysis summary
        primary_intent = intent_analysis["primary_intent"]
        confidence = intent_analysis["primary_confidence"]
        reasoning_parts.append(f"User intent analyzed as '{primary_intent}' (confidence: {confidence:.1f}).")

        # Secondary intents
        secondary = intent_analysis.get("secondary_intents", [])
        if secondary:
            reasoning_parts.append(f"Secondary intents detected: {', '.join(secondary)}.")

        # Mentioned objects/locations
        objects = intent_analysis.get("mentioned_objects", [])
        locations = intent_analysis.get("mentioned_locations", [])

        if objects:
            reasoning_parts.append(f"User mentioned objects: {', '.join(objects)}.")
        if locations:
            reasoning_parts.append(f"Location references: {', '.join(locations)}.")

        # Action proposals summary
        if proposed_actions:
            action_count = len(proposed_actions)
            categories = list(set(a.get("category", "general") for a in proposed_actions))
            reasoning_parts.append(f"Proposed {action_count} possible actions across categories: {', '.join(categories)}.")

            # Highlight top priority actions
            high_priority = [a for a in prioritized_actions if a.get("priority") == "high"]
            if high_priority:
                top_actions = [a.get("reasoning", "action") for a in high_priority[:3]]
                reasoning_parts.append(f"Top priority actions: {'; '.join(top_actions)}.")
        else:
            reasoning_parts.append("No specific actions proposed - maintaining conversational response.")

        # Urgency assessment
        urgency = intent_analysis.get("action_urgency", "normal")
        if urgency != "normal":
            reasoning_parts.append(f"Action urgency assessed as {urgency}.")

        return " ".join(reasoning_parts)