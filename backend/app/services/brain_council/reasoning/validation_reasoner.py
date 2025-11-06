"""
Validation Reasoner - Ensures actions are safe and feasible.

This reasoner focuses on:
- Validating proposed actions for safety and feasibility
- Checking physical constraints and limitations
- Ensuring actions align with persona characteristics
- Filtering out impossible or inappropriate actions
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from ..base import BaseReasoner, ReasoningContext, ReasoningResult
from app.utils.coordinate_system import (
    Position, Size, BoundingBox, distance, can_interact,
    ROOM_WIDTH, ROOM_HEIGHT, INTERACTION_DISTANCE, NEARBY_DISTANCE
)

logger = logging.getLogger(__name__)


class ValidationReasoner(BaseReasoner):
    """
    Reasoner responsible for validating proposed actions for safety and feasibility.

    Ensures that all proposed actions are physically possible, safe to execute,
    and align with the assistant's persona and current capabilities.
    """

    def __init__(self):
        super().__init__("validator")

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Validate proposed actions for safety and feasibility.

        Args:
            context: The reasoning context

        Returns:
            ReasoningResult with validation analysis
        """
        try:
            assistant_state = context.assistant_state
            room_state = context.room_state
            persona_context = context.persona_context

            # Get assistant position and state
            assistant_position = Position(
                assistant_state["position"]["x"],
                assistant_state["position"]["y"]
            )

            # Note: In a real implementation, this would receive proposed actions
            # from other reasoners. For now, we'll validate common action patterns.
            validation_analysis = await self._perform_validation_analysis(
                assistant_position, assistant_state, room_state, persona_context
            )

            # Generate validation reasoning
            reasoning = self._build_validation_reasoning(validation_analysis, assistant_state)

            metadata = {
                "validation_checks_performed": len(validation_analysis["checks"]),
                "safety_issues_found": len(validation_analysis["safety_concerns"]),
                "feasibility_issues": len(validation_analysis["feasibility_issues"]),
                "persona_constraints": len(validation_analysis["persona_considerations"])
            }

            return self._create_result(
                reasoning=reasoning,
                confidence=0.95,
                metadata=metadata
            )

        except Exception as e:
            return self._handle_error(e, "action validation")

    async def _perform_validation_analysis(self, assistant_position: Position,
                                         assistant_state: Dict[str, Any],
                                         room_state: Dict[str, Any],
                                         persona_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive validation analysis.

        Args:
            assistant_position: Current assistant position
            assistant_state: Current assistant state
            room_state: Current room state
            persona_context: Active persona information

        Returns:
            Validation analysis results
        """
        try:
            analysis = {
                "checks": [],
                "safety_concerns": [],
                "feasibility_issues": [],
                "persona_considerations": [],
                "valid_actions": [],
                "blocked_actions": []
            }

            # Spatial validation checks
            spatial_validation = self._validate_spatial_constraints(
                assistant_position, room_state, assistant_state
            )
            analysis["checks"].append("spatial_constraints")
            analysis.update(spatial_validation)

            # Object interaction validation
            interaction_validation = self._validate_interaction_possibilities(
                assistant_position, room_state, assistant_state
            )
            analysis["checks"].append("interaction_possibilities")
            analysis["valid_actions"].extend(interaction_validation["valid_interactions"])
            analysis["blocked_actions"].extend(interaction_validation["blocked_interactions"])

            # Object manipulation validation
            manipulation_validation = self._validate_manipulation_possibilities(
                assistant_position, room_state, assistant_state
            )
            analysis["checks"].append("manipulation_possibilities")
            analysis["valid_actions"].extend(manipulation_validation["valid_manipulations"])
            analysis["blocked_actions"].extend(manipulation_validation["blocked_manipulations"])

            # Persona alignment validation
            if persona_context:
                persona_validation = self._validate_persona_alignment(
                    persona_context, assistant_state
                )
                analysis["checks"].append("persona_alignment")
                analysis["persona_considerations"].extend(persona_validation["considerations"])

            # Safety validation
            safety_validation = self._validate_safety_constraints(
                assistant_position, room_state, assistant_state
            )
            analysis["checks"].append("safety_constraints")
            analysis["safety_concerns"].extend(safety_validation["concerns"])

            return analysis

        except Exception as e:
            logger.warning(f"Error performing validation analysis: {e}")
            return {
                "checks": [],
                "safety_concerns": [],
                "feasibility_issues": [],
                "persona_considerations": [],
                "valid_actions": [],
                "blocked_actions": []
            }

    def _validate_spatial_constraints(self, assistant_position: Position,
                                    room_state: Dict[str, Any],
                                    assistant_state: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate spatial movement constraints."""
        try:
            feasibility_issues = []
            safety_concerns = []

            # Check room boundaries
            margin = 30  # Minimum margin from edges
            if assistant_position.x < margin:
                safety_concerns.append("Close to left room boundary - limited leftward movement")
            if assistant_position.x > ROOM_WIDTH - margin:
                safety_concerns.append("Close to right room boundary - limited rightward movement")
            if assistant_position.y < margin:
                safety_concerns.append("Close to top room boundary - limited upward movement")
            if assistant_position.y > ROOM_HEIGHT - margin:
                safety_concerns.append("Close to bottom room boundary - limited downward movement")

            # Check for object obstacles
            objects = room_state.get("objects", [])
            nearby_obstacles = 0

            for obj in objects:
                if not obj.get("properties", {}).get("solid", True):
                    continue  # Skip non-solid objects

                try:
                    obj_pos = self._get_object_position(obj)
                    if obj_pos and distance(assistant_position, obj_pos) < 80:
                        nearby_obstacles += 1
                except Exception:
                    continue

            if nearby_obstacles > 3:
                feasibility_issues.append(f"Movement constrained by {nearby_obstacles} nearby solid objects")

            return {
                "feasibility_issues": feasibility_issues,
                "safety_concerns": safety_concerns
            }

        except Exception as e:
            logger.warning(f"Error validating spatial constraints: {e}")
            return {"feasibility_issues": [], "safety_concerns": []}

    def _validate_interaction_possibilities(self, assistant_position: Position,
                                          room_state: Dict[str, Any],
                                          assistant_state: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Validate object interaction possibilities."""
        try:
            valid_interactions = []
            blocked_interactions = []

            objects = room_state.get("objects", [])
            object_states = room_state.get("object_states", {})

            for obj in objects:
                try:
                    obj_pos = self._get_object_position(obj)
                    if not obj_pos:
                        continue

                    obj_id = obj.get("id")
                    obj_name = obj.get("name", "unknown")
                    dist = distance(assistant_position, obj_pos)

                    # Check interaction distance
                    if can_interact(assistant_position, obj_pos):
                        # Validate specific interactions based on object properties
                        obj_properties = obj.get("properties", {})
                        states = object_states.get(obj_id, {})

                        interaction_types = []

                        # Always allow examination
                        interaction_types.append("examine")

                        # Check for state-based interactions
                        if "power" in states:
                            interaction_types.append("toggle_power")

                        if "open" in states:
                            interaction_types.append("toggle_open")

                        if obj_properties.get("interactive", True):
                            interaction_types.append("general_interact")

                        valid_interactions.append({
                            "object_id": obj_id,
                            "object_name": obj_name,
                            "distance": int(dist),
                            "interaction_types": interaction_types,
                            "reason": "Within interaction range"
                        })

                    else:
                        # Too far for interaction
                        blocked_interactions.append({
                            "object_id": obj_id,
                            "object_name": obj_name,
                            "distance": int(dist),
                            "required_distance": int(INTERACTION_DISTANCE),
                            "reason": "Too far for direct interaction - movement required"
                        })

                except Exception:
                    continue

            return {
                "valid_interactions": valid_interactions,
                "blocked_interactions": blocked_interactions
            }

        except Exception as e:
            logger.warning(f"Error validating interaction possibilities: {e}")
            return {"valid_interactions": [], "blocked_interactions": []}

    def _validate_manipulation_possibilities(self, assistant_position: Position,
                                           room_state: Dict[str, Any],
                                           assistant_state: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Validate object manipulation possibilities."""
        try:
            valid_manipulations = []
            blocked_manipulations = []

            holding_object_id = assistant_state.get("holding_object_id")
            objects = room_state.get("objects", [])

            if holding_object_id:
                # Validate put down possibilities
                held_object = next((obj for obj in objects if obj.get("id") == holding_object_id), None)

                if held_object:
                    # Can put down at current location if space is clear
                    collision_check = self._check_collision_at_position_sync(
                        assistant_position, held_object, objects, exclude_id=holding_object_id
                    )

                    if not collision_check["has_collision"]:
                        valid_manipulations.append({
                            "action": "put_down",
                            "object_id": holding_object_id,
                            "target_position": assistant_position.to_dict(),
                            "reason": "Can place held object at current location"
                        })
                    else:
                        blocked_manipulations.append({
                            "action": "put_down",
                            "object_id": holding_object_id,
                            "target_position": assistant_position.to_dict(),
                            "reason": f"Cannot place at current location: {collision_check['reason']}"
                        })

                    # Check surface placement possibilities
                    for obj in objects:
                        if obj.get("properties", {}).get("surface", False):
                            try:
                                obj_pos = self._get_object_position(obj)
                                if obj_pos and can_interact(assistant_position, obj_pos):
                                    valid_manipulations.append({
                                        "action": "put_down",
                                        "object_id": holding_object_id,
                                        "target_surface": obj.get("id"),
                                        "reason": f"Can place on {obj.get('name')}"
                                    })
                            except Exception:
                                continue

            else:
                # Validate pick up possibilities
                for obj in objects:
                    if not obj.get("properties", {}).get("movable", False):
                        continue

                    try:
                        obj_pos = self._get_object_position(obj)
                        if not obj_pos:
                            continue

                        if can_interact(assistant_position, obj_pos):
                            valid_manipulations.append({
                                "action": "pick_up",
                                "object_id": obj.get("id"),
                                "object_name": obj.get("name"),
                                "reason": "Object is movable and within reach"
                            })
                        else:
                            dist = distance(assistant_position, obj_pos)
                            blocked_manipulations.append({
                                "action": "pick_up",
                                "object_id": obj.get("id"),
                                "object_name": obj.get("name"),
                                "distance": int(dist),
                                "reason": "Movable object but too far to reach"
                            })

                    except Exception:
                        continue

            return {
                "valid_manipulations": valid_manipulations,
                "blocked_manipulations": blocked_manipulations
            }

        except Exception as e:
            logger.warning(f"Error validating manipulation possibilities: {e}")
            return {"valid_manipulations": [], "blocked_manipulations": []}

    def _validate_persona_alignment(self, persona_context: Dict[str, Any],
                                   assistant_state: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate actions against persona characteristics."""
        try:
            considerations = []

            personality = persona_context.get("personality", "").lower()
            persona_name = persona_context.get("name", "Assistant")

            # Check personality constraints
            if any(trait in personality for trait in ["calm", "peaceful", "zen"]):
                considerations.append("Persona prefers calm, deliberate actions over hasty movements")

            if any(trait in personality for trait in ["energetic", "enthusiastic", "lively"]):
                considerations.append("Persona supports active engagement and dynamic interactions")

            if any(trait in personality for trait in ["careful", "cautious", "thoughtful"]):
                considerations.append("Persona requires careful validation of actions before execution")

            if any(trait in personality for trait in ["playful", "fun", "mischievous"]):
                considerations.append("Persona allows for creative and playful interactions")

            if any(trait in personality for trait in ["professional", "formal", "serious"]):
                considerations.append("Persona requires professional and appropriate behavior")

            # Current mood alignment
            current_mood = assistant_state.get("mood", "neutral")
            if current_mood in ["sad", "tired", "low_energy"]:
                considerations.append("Current mood suggests preference for low-energy actions")
            elif current_mood in ["excited", "energetic", "happy"]:
                considerations.append("Current mood supports active and engaging actions")

            return {"considerations": considerations}

        except Exception as e:
            logger.warning(f"Error validating persona alignment: {e}")
            return {"considerations": []}

    def _validate_safety_constraints(self, assistant_position: Position,
                                   room_state: Dict[str, Any],
                                   assistant_state: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate general safety constraints."""
        try:
            concerns = []

            # Check for potentially unsafe object states
            objects = room_state.get("objects", [])
            object_states = room_state.get("object_states", {})

            for obj in objects:
                try:
                    obj_pos = self._get_object_position(obj)
                    if not obj_pos or not can_interact(assistant_position, obj_pos):
                        continue

                    obj_id = obj.get("id")
                    obj_name = obj.get("name", "unknown")
                    states = object_states.get(obj_id, {})

                    # Check for potentially unsafe states
                    if states.get("power") == "on" and "warning" in obj_name.lower():
                        concerns.append(f"Caution: {obj_name} is powered on and may require careful handling")

                    if states.get("temperature", "normal") in ["hot", "very_hot"]:
                        concerns.append(f"Safety concern: {obj_name} is hot - avoid direct contact")

                except Exception:
                    continue

            # Check for overcrowding (too many objects in interaction range)
            nearby_objects = 0
            for obj in objects:
                try:
                    obj_pos = self._get_object_position(obj)
                    if obj_pos and distance(assistant_position, obj_pos) < INTERACTION_DISTANCE:
                        nearby_objects += 1
                except Exception:
                    continue

            if nearby_objects > 5:
                concerns.append("Dense object environment - exercise caution when moving or manipulating objects")

            # Check assistant state for safety considerations
            holding_object_id = assistant_state.get("holding_object_id")
            if holding_object_id:
                concerns.append("Currently holding object - ensure safe placement before other actions")

            return {"concerns": concerns}

        except Exception as e:
            logger.warning(f"Error validating safety constraints: {e}")
            return {"concerns": []}

    def _check_collision_at_position_sync(self, position: Position, obj: Dict[str, Any],
                                         all_objects: List[Dict], exclude_id: str) -> Dict[str, Any]:
        """Check if placing an object at a position would cause collisions."""
        try:
            obj_size = obj.get("size", {"width": 30, "height": 30})
            placing_box = BoundingBox(position, Size.from_dict(obj_size))

            for other_obj in all_objects:
                if other_obj.get("id") == exclude_id:
                    continue

                if not other_obj.get("properties", {}).get("solid", True):
                    continue

                other_pos = self._get_object_position(other_obj)
                if not other_pos:
                    continue

                other_size = other_obj.get("size", {"width": 30, "height": 30})
                other_box = BoundingBox(other_pos, Size.from_dict(other_size))

                if placing_box.overlaps_with(other_box):
                    return {
                        "has_collision": True,
                        "reason": f"would overlap with {other_obj.get('name', 'object')}"
                    }

            return {"has_collision": False, "reason": "no collisions detected"}

        except Exception as e:
            return {"has_collision": True, "reason": f"collision check failed: {str(e)}"}

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

    def _build_validation_reasoning(self, validation_analysis: Dict[str, Any],
                                  assistant_state: Dict[str, Any]) -> str:
        """Build the validation reasoning explanation."""
        reasoning_parts = []

        # Validation checks summary
        checks_performed = validation_analysis.get("checks", [])
        if checks_performed:
            reasoning_parts.append(f"Performed {len(checks_performed)} validation checks: {', '.join(checks_performed)}.")

        # Safety concerns
        safety_concerns = validation_analysis.get("safety_concerns", [])
        if safety_concerns:
            reasoning_parts.append(f"Safety considerations: {len(safety_concerns)} items requiring attention.")
            if len(safety_concerns) <= 2:
                reasoning_parts.append(f"Specific concerns: {'; '.join(safety_concerns)}.")

        # Feasibility issues
        feasibility_issues = validation_analysis.get("feasibility_issues", [])
        if feasibility_issues:
            reasoning_parts.append(f"Feasibility constraints: {'; '.join(feasibility_issues)}.")

        # Valid actions summary
        valid_actions = validation_analysis.get("valid_actions", [])
        if valid_actions:
            interaction_count = len([a for a in valid_actions if isinstance(a, dict) and "interaction_types" in a])
            manipulation_count = len([a for a in valid_actions if isinstance(a, dict) and "action" in a])

            if interaction_count > 0:
                reasoning_parts.append(f"Validated {interaction_count} possible object interactions.")

            if manipulation_count > 0:
                reasoning_parts.append(f"Validated {manipulation_count} possible object manipulations.")

        # Blocked actions
        blocked_actions = validation_analysis.get("blocked_actions", [])
        if blocked_actions:
            reasoning_parts.append(f"Identified {len(blocked_actions)} actions currently not feasible due to constraints.")

        # Persona considerations
        persona_considerations = validation_analysis.get("persona_considerations", [])
        if persona_considerations:
            reasoning_parts.append("Persona alignment considerations noted for appropriate response style.")

        # Overall validation status
        total_concerns = len(safety_concerns) + len(feasibility_issues)
        if total_concerns == 0:
            reasoning_parts.append("All proposed actions appear safe and feasible for execution.")
        elif total_concerns <= 2:
            reasoning_parts.append("Minor constraints identified but actions generally viable with adjustments.")
        else:
            reasoning_parts.append("Multiple constraints require careful consideration before action execution.")

        return " ".join(reasoning_parts)