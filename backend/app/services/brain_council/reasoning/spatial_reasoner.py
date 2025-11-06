"""
Spatial Reasoner - Understands room layout, object positions, and visibility.

This reasoner focuses on:
- Analyzing spatial environment and object relationships
- Identifying visible and interactive objects
- Understanding room layout and constraints
- Assessing spatial possibilities for movement and interaction
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

from ..base import BaseReasoner, ReasoningContext, ReasoningResult
from app.utils.coordinate_system import (
    Position, Size, BoundingBox, distance, is_nearby, can_interact,
    ROOM_WIDTH, ROOM_HEIGHT, INTERACTION_DISTANCE, NEARBY_DISTANCE
)

logger = logging.getLogger(__name__)


class SpatialReasoner(BaseReasoner):
    """
    Reasoner responsible for spatial analysis and environmental understanding.

    Analyzes the room environment, object positions, and spatial relationships
    to inform movement and interaction decisions.
    """

    def __init__(self):
        super().__init__("spatial_reasoner")

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Analyze spatial environment and object relationships.

        Args:
            context: The reasoning context

        Returns:
            ReasoningResult with spatial analysis
        """
        try:
            assistant_state = context.assistant_state
            room_state = context.room_state

            # Get assistant position
            assistant_position = Position(
                assistant_state["position"]["x"],
                assistant_state["position"]["y"]
            )

            # Analyze room environment
            spatial_analysis = self._analyze_room_environment(
                assistant_position, room_state
            )

            # Analyze object relationships
            object_analysis = self._analyze_object_relationships(
                assistant_position, room_state
            )

            # Analyze spatial constraints and possibilities
            constraints = self._analyze_spatial_constraints(
                assistant_position, room_state, assistant_state
            )

            # Generate spatial reasoning
            reasoning = self._build_spatial_reasoning(
                spatial_analysis, object_analysis, constraints, assistant_state
            )

            metadata = {
                "assistant_position": assistant_position.to_dict(),
                "visible_objects_count": len(spatial_analysis["visible_objects"]),
                "interactive_objects_count": len(spatial_analysis["interactive_objects"]),
                "movable_objects_count": len(spatial_analysis["movable_objects"]),
                "spatial_constraints": constraints
            }

            return self._create_result(
                reasoning=reasoning,
                confidence=0.95,
                metadata=metadata
            )

        except Exception as e:
            return self._handle_error(e, "spatial analysis")

    def _analyze_room_environment(self, assistant_pos: Position,
                                room_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the overall room environment.

        Args:
            assistant_pos: Current assistant position
            room_state: Current room state information

        Returns:
            Analysis of room environment
        """
        try:
            objects = room_state.get("objects", [])
            object_states = room_state.get("object_states", {})

            visible_objects = []
            interactive_objects = []
            movable_objects = []
            surface_objects = []

            for obj in objects:
                try:
                    # Get object position and properties
                    obj_position = self._get_object_position(obj)
                    if not obj_position:
                        continue

                    obj_properties = obj.get("properties", {})
                    obj_name = obj.get("name", "unknown")
                    obj_id = obj.get("id", "unknown")

                    # Calculate distance
                    dist = distance(assistant_pos, obj_position)

                    # Check visibility (nearby objects are visible)
                    if is_nearby(assistant_pos, obj_position):
                        obj_info = {
                            "id": obj_id,
                            "name": obj_name,
                            "position": obj_position.to_dict(),
                            "distance": int(dist),
                            "properties": obj_properties,
                            "states": object_states.get(obj_id, {})
                        }
                        visible_objects.append(obj_info)

                        # Check if interactive
                        if can_interact(assistant_pos, obj_position):
                            interactive_objects.append(obj_info)

                        # Check if movable
                        if obj_properties.get("movable", False):
                            movable_objects.append(obj_info)

                        # Check if surface (for placing objects)
                        if obj_properties.get("surface", False):
                            surface_objects.append(obj_info)

                except Exception as e:
                    logger.warning(f"Error analyzing object {obj.get('id', 'unknown')}: {e}")
                    continue

            return {
                "visible_objects": visible_objects,
                "interactive_objects": interactive_objects,
                "movable_objects": movable_objects,
                "surface_objects": surface_objects,
                "total_objects_in_room": len(objects)
            }

        except Exception as e:
            logger.warning(f"Error analyzing room environment: {e}")
            return {
                "visible_objects": [],
                "interactive_objects": [],
                "movable_objects": [],
                "surface_objects": [],
                "total_objects_in_room": 0
            }

    def _analyze_object_relationships(self, assistant_pos: Position,
                                    room_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze relationships between objects in the room.

        Args:
            assistant_pos: Current assistant position
            room_state: Current room state information

        Returns:
            Analysis of object relationships
        """
        try:
            objects = room_state.get("objects", [])
            object_clusters = []
            isolated_objects = []

            # Group nearby objects into clusters
            processed_objects = set()

            for i, obj in enumerate(objects):
                if obj.get("id") in processed_objects:
                    continue

                obj_pos = self._get_object_position(obj)
                if not obj_pos:
                    continue

                cluster = [obj]
                processed_objects.add(obj.get("id"))

                # Find nearby objects
                for j, other_obj in enumerate(objects):
                    if i == j or other_obj.get("id") in processed_objects:
                        continue

                    other_pos = self._get_object_position(other_obj)
                    if not other_pos:
                        continue

                    # Objects within 150 pixels are considered "nearby"
                    if distance(obj_pos, other_pos) < 150:
                        cluster.append(other_obj)
                        processed_objects.add(other_obj.get("id"))

                if len(cluster) > 1:
                    cluster_center = self._calculate_cluster_center(cluster)
                    cluster_distance = distance(assistant_pos, cluster_center)
                    object_clusters.append({
                        "objects": cluster,
                        "center": cluster_center.to_dict(),
                        "distance_from_assistant": int(cluster_distance),
                        "object_count": len(cluster)
                    })
                else:
                    isolated_objects.extend(cluster)

            return {
                "object_clusters": object_clusters,
                "isolated_objects": isolated_objects,
                "clustered_object_count": sum(cluster["object_count"] for cluster in object_clusters),
                "isolated_object_count": len(isolated_objects)
            }

        except Exception as e:
            logger.warning(f"Error analyzing object relationships: {e}")
            return {
                "object_clusters": [],
                "isolated_objects": [],
                "clustered_object_count": 0,
                "isolated_object_count": 0
            }

    def _analyze_spatial_constraints(self, assistant_pos: Position,
                                   room_state: Dict[str, Any],
                                   assistant_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze spatial constraints and movement possibilities.

        Args:
            assistant_pos: Current assistant position
            room_state: Current room state information
            assistant_state: Current assistant state

        Returns:
            Analysis of spatial constraints
        """
        try:
            constraints = {}

            # Room boundary constraints
            distance_to_edges = {
                "left": assistant_pos.x,
                "right": ROOM_WIDTH - assistant_pos.x,
                "top": assistant_pos.y,
                "bottom": ROOM_HEIGHT - assistant_pos.y
            }
            constraints["room_boundaries"] = distance_to_edges

            # Find the direction with most free space
            max_space = max(distance_to_edges.values())
            free_direction = [k for k, v in distance_to_edges.items() if v == max_space][0]
            constraints["most_free_space_direction"] = free_direction

            # Object obstacles
            objects = room_state.get("objects", [])
            nearby_obstacles = []

            for obj in objects:
                if not obj.get("properties", {}).get("solid", True):
                    continue  # Skip non-solid objects

                obj_pos = self._get_object_position(obj)
                if not obj_pos:
                    continue

                dist = distance(assistant_pos, obj_pos)
                if dist < 100:  # Within 100 pixels is considered "nearby"
                    nearby_obstacles.append({
                        "id": obj.get("id"),
                        "name": obj.get("name"),
                        "distance": int(dist),
                        "direction": self._calculate_direction(assistant_pos, obj_pos)
                    })

            constraints["nearby_obstacles"] = nearby_obstacles

            # Holding object constraints
            holding_object_id = assistant_state.get("holding_object_id")
            if holding_object_id:
                constraints["holding_object"] = {
                    "object_id": holding_object_id,
                    "affects_movement": False,  # Holding objects don't typically affect movement
                    "affects_interaction": True  # But may affect ability to pick up other objects
                }

            # Available interaction zones
            interaction_zones = self._identify_interaction_zones(assistant_pos, room_state)
            constraints["interaction_zones"] = interaction_zones

            return constraints

        except Exception as e:
            logger.warning(f"Error analyzing spatial constraints: {e}")
            return {}

    def _get_object_position(self, obj: Dict[str, Any]) -> Optional[Position]:
        """
        Extract position from object data.

        Args:
            obj: Object data dictionary

        Returns:
            Position object or None if invalid
        """
        try:
            position_data = obj.get("position", {})
            if isinstance(position_data, dict):
                return Position.from_dict(position_data)
            elif "position_x" in obj and "position_y" in obj:
                return Position(obj["position_x"], obj["position_y"])
            else:
                return None
        except (ValueError, TypeError, KeyError):
            return None

    def _calculate_cluster_center(self, objects: List[Dict[str, Any]]) -> Position:
        """
        Calculate the center point of a cluster of objects.

        Args:
            objects: List of object dictionaries

        Returns:
            Center position of the cluster
        """
        try:
            positions = []
            for obj in objects:
                pos = self._get_object_position(obj)
                if pos:
                    positions.append(pos)

            if not positions:
                return Position(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)

            avg_x = sum(pos.x for pos in positions) / len(positions)
            avg_y = sum(pos.y for pos in positions) / len(positions)
            return Position(avg_x, avg_y)

        except Exception:
            return Position(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)

    def _calculate_direction(self, from_pos: Position, to_pos: Position) -> str:
        """
        Calculate direction from one position to another.

        Args:
            from_pos: Starting position
            to_pos: Target position

        Returns:
            Direction string
        """
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y

        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def _identify_interaction_zones(self, assistant_pos: Position,
                                  room_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify areas where the assistant can interact with objects.

        Args:
            assistant_pos: Current assistant position
            room_state: Room state information

        Returns:
            List of interaction zones
        """
        try:
            zones = []
            objects = room_state.get("objects", [])

            for obj in objects:
                obj_pos = self._get_object_position(obj)
                if not obj_pos:
                    continue

                dist = distance(assistant_pos, obj_pos)
                if dist <= INTERACTION_DISTANCE:
                    zones.append({
                        "object_id": obj.get("id"),
                        "object_name": obj.get("name"),
                        "distance": int(dist),
                        "interaction_type": "immediate",
                        "actions_possible": self._determine_possible_actions(obj)
                    })
                elif dist <= NEARBY_DISTANCE:
                    zones.append({
                        "object_id": obj.get("id"),
                        "object_name": obj.get("name"),
                        "distance": int(dist),
                        "interaction_type": "requires_movement",
                        "actions_possible": self._determine_possible_actions(obj)
                    })

            return zones[:10]  # Return up to 10 closest interaction zones

        except Exception as e:
            logger.warning(f"Error identifying interaction zones: {e}")
            return []

    def _determine_possible_actions(self, obj: Dict[str, Any]) -> List[str]:
        """
        Determine what actions are possible with an object.

        Args:
            obj: Object dictionary

        Returns:
            List of possible action types
        """
        actions = []
        properties = obj.get("properties", {})

        # Basic interactions
        actions.append("examine")

        # Conditional interactions
        if properties.get("movable", False):
            actions.extend(["pick_up", "move"])

        if properties.get("interactive", True):
            actions.append("interact")

        if properties.get("surface", False):
            actions.append("place_on")

        # State-based interactions
        if "power" in obj.get("states", {}):
            actions.append("toggle_power")

        if "open" in obj.get("states", {}):
            actions.append("toggle_open")

        return actions

    def _build_spatial_reasoning(self, spatial_analysis: Dict[str, Any],
                               object_analysis: Dict[str, Any],
                               constraints: Dict[str, Any],
                               assistant_state: Dict[str, Any]) -> str:
        """
        Build the spatial reasoning explanation.

        Args:
            spatial_analysis: Results from spatial analysis
            object_analysis: Results from object relationship analysis
            constraints: Spatial constraints analysis
            assistant_state: Current assistant state

        Returns:
            Detailed spatial reasoning
        """
        reasoning_parts = []

        # Position and environment overview
        visible_count = len(spatial_analysis["visible_objects"])
        interactive_count = len(spatial_analysis["interactive_objects"])

        if visible_count > 0:
            reasoning_parts.append(f"Environment analysis: {visible_count} objects visible, {interactive_count} within interaction range.")
        else:
            reasoning_parts.append("Environment analysis: Open space with no objects in immediate vicinity.")

        # Object interaction opportunities
        if interactive_count > 0:
            interactive_objects = spatial_analysis["interactive_objects"]
            object_names = [obj["name"] for obj in interactive_objects[:3]]
            reasoning_parts.append(f"Immediate interaction possible with: {', '.join(object_names)}{'...' if len(interactive_objects) > 3 else ''}.")

        # Movable objects
        movable_count = len(spatial_analysis["movable_objects"])
        if movable_count > 0:
            reasoning_parts.append(f"Found {movable_count} movable objects that could be picked up or rearranged.")

        # Object clustering
        cluster_count = len(object_analysis["object_clusters"])
        if cluster_count > 0:
            reasoning_parts.append(f"Objects are organized in {cluster_count} clusters around the room.")

        # Spatial constraints and movement
        boundaries = constraints.get("room_boundaries", {})
        if boundaries:
            min_distance = min(boundaries.values())
            if min_distance < 100:
                reasoning_parts.append("Close to room boundary - limited movement space in some directions.")

        free_direction = constraints.get("most_free_space_direction")
        if free_direction:
            reasoning_parts.append(f"Most open space available toward the {free_direction}.")

        # Obstacles
        obstacles = constraints.get("nearby_obstacles", [])
        if obstacles:
            reasoning_parts.append(f"Movement may be constrained by {len(obstacles)} nearby solid objects.")

        # Holding object effects
        holding_info = constraints.get("holding_object")
        if holding_info:
            reasoning_parts.append("Currently holding an object - this affects interaction possibilities.")

        # Interaction zones summary
        interaction_zones = constraints.get("interaction_zones", [])
        immediate_zones = [zone for zone in interaction_zones if zone["interaction_type"] == "immediate"]
        if immediate_zones:
            reasoning_parts.append(f"Ready for immediate interaction with {len(immediate_zones)} objects.")

        if not reasoning_parts:
            reasoning_parts.append("Room environment is clear with ample space for movement and activities.")

        return " ".join(reasoning_parts)