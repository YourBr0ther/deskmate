"""
Multi-room pathfinding service for continuous coordinate navigation.

This module implements pathfinding across multiple rooms using doorway transitions
and continuous pixel-based coordinates instead of the old grid-based system.
"""

import heapq
import math
from typing import List, Tuple, Optional, Set, Dict, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
import logging

from app.models.rooms import FloorPlan, Room, Wall, Doorway, FurnitureItem
from app.models.assistant import AssistantState

logger = logging.getLogger(__name__)


@dataclass
class PathPoint:
    """A point in the pathfinding space with continuous coordinates."""
    x: float
    y: float
    room_id: str
    g_cost: float = 0.0  # Distance from start
    h_cost: float = 0.0  # Heuristic distance to goal
    f_cost: float = 0.0  # Total cost (g + h)
    parent: Optional['PathPoint'] = None
    is_doorway: bool = False
    doorway_id: Optional[str] = None

    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return (abs(self.x - other.x) < 1.0 and
                abs(self.y - other.y) < 1.0 and
                self.room_id == other.room_id)

    def __hash__(self):
        return hash((round(self.x), round(self.y), self.room_id))


@dataclass
class RoomGraph:
    """Graph representation of rooms and doorway connections."""
    rooms: Dict[str, Room]
    doorways: Dict[str, Doorway]
    connections: Dict[str, List[str]]  # room_id -> list of connected room_ids
    doorway_positions: Dict[str, Tuple[float, float]]  # doorway_id -> (x, y)


class MultiRoomPathfindingService:
    """Service for pathfinding across multiple rooms with doorway transitions."""

    def __init__(self, movement_speed: float = 100.0):
        self.movement_speed = movement_speed  # pixels per second
        self.assistant_size = (40.0, 40.0)  # width, height in pixels
        self.doorway_threshold = 50.0  # distance to activate doorway transition

    def find_multi_room_path(
        self,
        db: Session,
        floor_plan_id: str,
        start_pos: Tuple[float, float],
        start_room_id: str,
        goal_pos: Tuple[float, float],
        goal_room_id: str
    ) -> Dict[str, Any]:
        """
        Find path between rooms using doorway transitions.

        Returns:
            Dict containing path, room transitions, and navigation metadata
        """
        logger.info(f"Finding multi-room path from {start_room_id}:{start_pos} to {goal_room_id}:{goal_pos}")

        # Build room graph
        room_graph = self._build_room_graph(db, floor_plan_id)

        # Get furniture obstacles for each room
        room_obstacles = self._get_room_obstacles(db, floor_plan_id)

        # If same room, use single-room pathfinding
        if start_room_id == goal_room_id:
            path = self._find_single_room_path(
                start_pos, goal_pos, start_room_id,
                room_obstacles.get(start_room_id, []),
                room_graph.rooms[start_room_id]
            )
            return {
                "path": path,
                "room_transitions": [],
                "doorways_to_open": [],
                "estimated_duration": self._estimate_path_duration(path),
                "total_distance": self._calculate_path_distance(path)
            }

        # Find room sequence using breadth-first search
        room_sequence = self._find_room_sequence(room_graph, start_room_id, goal_room_id)
        if not room_sequence:
            logger.warning(f"No path found between rooms {start_room_id} and {goal_room_id}")
            return {"path": [], "room_transitions": [], "doorways_to_open": [], "estimated_duration": 0, "total_distance": 0}

        # Build multi-room path
        return self._build_multi_room_path(
            room_graph, room_obstacles, room_sequence,
            start_pos, goal_pos
        )

    def _build_room_graph(self, db: Session, floor_plan_id: str) -> RoomGraph:
        """Build a graph representation of rooms and their connections."""
        # Get all rooms
        rooms = {r.id: r for r in db.query(Room).filter(Room.floor_plan_id == floor_plan_id).all()}

        # Get all doorways
        doorways = {d.id: d for d in db.query(Doorway).filter(Doorway.floor_plan_id == floor_plan_id).all()}

        # Build connection graph
        connections = {room_id: [] for room_id in rooms.keys()}
        doorway_positions = {}

        for doorway in doorways.values():
            if doorway.is_accessible:
                # Add bidirectional connection
                if doorway.room_a_id in connections:
                    connections[doorway.room_a_id].append(doorway.room_b_id)
                if doorway.room_b_id in connections:
                    connections[doorway.room_b_id].append(doorway.room_a_id)

                # Store doorway world position
                doorway_positions[doorway.id] = doorway.get_world_position()

        return RoomGraph(rooms, doorways, connections, doorway_positions)

    def _get_room_obstacles(self, db: Session, floor_plan_id: str) -> Dict[str, List[Tuple[float, float, float, float]]]:
        """Get furniture obstacles for each room as bounding rectangles."""
        obstacles = {}

        furniture_items = db.query(FurnitureItem).filter(
            FurnitureItem.floor_plan_id == floor_plan_id,
            FurnitureItem.is_solid == True
        ).all()

        for item in furniture_items:
            if item.room_id not in obstacles:
                obstacles[item.room_id] = []

            # Convert furniture to bounding rectangle (x1, y1, x2, y2)
            x1 = item.position_x - item.width / 2
            y1 = item.position_y - item.height / 2
            x2 = item.position_x + item.width / 2
            y2 = item.position_y + item.height / 2

            obstacles[item.room_id].append((x1, y1, x2, y2))

        return obstacles

    def _find_room_sequence(self, room_graph: RoomGraph, start_room: str, goal_room: str) -> List[str]:
        """Use BFS to find sequence of rooms to traverse."""
        if start_room == goal_room:
            return [start_room]

        queue = [(start_room, [start_room])]
        visited = {start_room}

        while queue:
            current_room, path = queue.pop(0)

            for connected_room in room_graph.connections.get(current_room, []):
                if connected_room == goal_room:
                    return path + [connected_room]

                if connected_room not in visited:
                    visited.add(connected_room)
                    queue.append((connected_room, path + [connected_room]))

        return []  # No path found

    def _find_single_room_path(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        room_id: str,
        obstacles: List[Tuple[float, float, float, float]],
        room: Room
    ) -> List[Dict[str, Any]]:
        """Find path within a single room using A* with continuous coordinates."""
        # Use simplified A* for continuous space
        # For now, implement direct line path with obstacle avoidance

        path_points = []

        # Check if direct path is clear
        if self._is_path_clear(start, goal, obstacles):
            path_points = [
                {"x": start[0], "y": start[1], "room_id": room_id},
                {"x": goal[0], "y": goal[1], "room_id": room_id}
            ]
        else:
            # Implement more sophisticated pathfinding around obstacles
            path_points = self._navigate_around_obstacles(start, goal, room_id, obstacles, room)

        return path_points

    def _is_path_clear(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        obstacles: List[Tuple[float, float, float, float]]
    ) -> bool:
        """Check if a straight line path intersects with any obstacles."""
        # Expand assistant size for collision detection
        expand_x, expand_y = self.assistant_size[0] / 2, self.assistant_size[1] / 2

        for x1, y1, x2, y2 in obstacles:
            # Expand obstacle bounds
            expanded_obstacle = (x1 - expand_x, y1 - expand_y, x2 + expand_x, y2 + expand_y)

            if self._line_intersects_rectangle(start, end, expanded_obstacle):
                return False

        return True

    def _line_intersects_rectangle(
        self,
        line_start: Tuple[float, float],
        line_end: Tuple[float, float],
        rect: Tuple[float, float, float, float]
    ) -> bool:
        """Check if line segment intersects with rectangle."""
        x1, y1 = line_start
        x2, y2 = line_end
        rx1, ry1, rx2, ry2 = rect

        # Check if line endpoints are inside rectangle
        if rx1 <= x1 <= rx2 and ry1 <= y1 <= ry2:
            return True
        if rx1 <= x2 <= rx2 and ry1 <= y2 <= ry2:
            return True

        # Check line intersection with rectangle edges
        def line_intersects_line(x1, y1, x2, y2, x3, y3, x4, y4):
            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                return False

            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

            return 0 <= t <= 1 and 0 <= u <= 1

        # Check intersection with each rectangle edge
        edges = [
            (rx1, ry1, rx2, ry1),  # top
            (rx2, ry1, rx2, ry2),  # right
            (rx2, ry2, rx1, ry2),  # bottom
            (rx1, ry2, rx1, ry1)   # left
        ]

        for edge in edges:
            if line_intersects_line(x1, y1, x2, y2, *edge):
                return True

        return False

    def _navigate_around_obstacles(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        room_id: str,
        obstacles: List[Tuple[float, float, float, float]],
        room: Room
    ) -> List[Dict[str, Any]]:
        """Navigate around obstacles using corner-based waypoints."""
        # Simple obstacle avoidance: find corners of obstacles and use as waypoints
        waypoints = [start]

        # Get obstacle corners as potential waypoints
        corner_points = []
        expand_x, expand_y = self.assistant_size[0] / 2, self.assistant_size[1] / 2

        for x1, y1, x2, y2 in obstacles:
            # Add corners with buffer for assistant size
            corners = [
                (x1 - expand_x, y1 - expand_y),  # top-left
                (x2 + expand_x, y1 - expand_y),  # top-right
                (x2 + expand_x, y2 + expand_y),  # bottom-right
                (x1 - expand_x, y2 + expand_y)   # bottom-left
            ]
            corner_points.extend(corners)

        # Simple pathfinding: try to connect start -> corners -> goal
        current_pos = start
        remaining_corners = set(corner_points)

        while current_pos != goal:
            best_corner = None
            best_score = float('inf')

            # Find best intermediate waypoint
            for corner in remaining_corners:
                if self._is_path_clear(current_pos, corner, obstacles):
                    # Score based on distance to goal
                    score = math.sqrt((corner[0] - goal[0])**2 + (corner[1] - goal[1])**2)
                    if score < best_score:
                        best_score = score
                        best_corner = corner

            if best_corner:
                waypoints.append(best_corner)
                current_pos = best_corner
                remaining_corners.remove(best_corner)
            else:
                # Try direct path to goal
                if self._is_path_clear(current_pos, goal, obstacles):
                    waypoints.append(goal)
                    break
                else:
                    # Fallback: add goal even if path not clear (let physics handle collision)
                    waypoints.append(goal)
                    break

        # Convert waypoints to path format
        return [{"x": x, "y": y, "room_id": room_id} for x, y in waypoints]

    def _build_multi_room_path(
        self,
        room_graph: RoomGraph,
        room_obstacles: Dict[str, List[Tuple[float, float, float, float]]],
        room_sequence: List[str],
        start_pos: Tuple[float, float],
        goal_pos: Tuple[float, float]
    ) -> Dict[str, Any]:
        """Build complete path across multiple rooms."""
        full_path = []
        room_transitions = []
        doorways_to_open = []

        current_pos = start_pos

        for i in range(len(room_sequence)):
            current_room = room_sequence[i]

            if i == len(room_sequence) - 1:
                # Last room - go to final goal
                target_pos = goal_pos
            else:
                # Find doorway to next room
                next_room = room_sequence[i + 1]
                doorway = self._find_doorway_between_rooms(room_graph, current_room, next_room)

                if not doorway:
                    logger.error(f"No doorway found between {current_room} and {next_room}")
                    break

                target_pos = room_graph.doorway_positions[doorway.id]

                # Record room transition
                room_transitions.append({
                    "from_room": current_room,
                    "to_room": next_room,
                    "doorway_id": doorway.id,
                    "doorway_position": target_pos,
                    "requires_interaction": doorway.requires_interaction
                })

                # Check if door needs to be opened
                if doorway.has_door and doorway.door_state == "closed":
                    doorways_to_open.append(doorway.id)

            # Find path within current room
            room_obstacles_list = room_obstacles.get(current_room, [])
            room_path = self._find_single_room_path(
                current_pos, target_pos, current_room,
                room_obstacles_list, room_graph.rooms[current_room]
            )

            # Add to full path (skip first point if not the start to avoid duplicates)
            if i == 0:
                full_path.extend(room_path)
            else:
                full_path.extend(room_path[1:])  # Skip first point to avoid duplicate

            current_pos = target_pos

        return {
            "path": full_path,
            "room_transitions": room_transitions,
            "doorways_to_open": doorways_to_open,
            "estimated_duration": self._estimate_path_duration(full_path),
            "total_distance": self._calculate_path_distance(full_path)
        }

    def _find_doorway_between_rooms(self, room_graph: RoomGraph, room1: str, room2: str) -> Optional[Doorway]:
        """Find doorway connecting two specific rooms."""
        for doorway in room_graph.doorways.values():
            if doorway.connects_rooms(room1, room2) and doorway.is_accessible:
                return doorway
        return None

    def _estimate_path_duration(self, path: List[Dict[str, Any]]) -> float:
        """Estimate time to complete path in seconds."""
        if len(path) < 2:
            return 0.0

        total_distance = self._calculate_path_distance(path)
        return total_distance / self.movement_speed

    def _calculate_path_distance(self, path: List[Dict[str, Any]]) -> float:
        """Calculate total distance of path in pixels."""
        if len(path) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i + 1]
            distance = math.sqrt((p2["x"] - p1["x"])**2 + (p2["y"] - p1["y"])**2)
            total_distance += distance

        return total_distance

    def check_doorway_proximity(
        self,
        assistant_pos: Tuple[float, float],
        room_graph: RoomGraph,
        current_room_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if assistant is near any doorways for automatic room transition."""
        for doorway in room_graph.doorways.values():
            if (doorway.room_a_id == current_room_id or doorway.room_b_id == current_room_id):
                doorway_pos = room_graph.doorway_positions[doorway.id]
                distance = math.sqrt(
                    (assistant_pos[0] - doorway_pos[0])**2 +
                    (assistant_pos[1] - doorway_pos[1])**2
                )

                if distance <= self.doorway_threshold:
                    # Determine target room
                    target_room = doorway.room_b_id if doorway.room_a_id == current_room_id else doorway.room_a_id

                    return {
                        "doorway": doorway,
                        "target_room": target_room,
                        "distance": distance,
                        "can_transition": doorway.is_accessible and doorway.door_state != "locked"
                    }

        return None


# Global service instance
multi_room_pathfinding_service = MultiRoomPathfindingService()