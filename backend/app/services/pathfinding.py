"""
A* Pathfinding Algorithm for DeskMate Assistant

This module implements A* pathfinding for the assistant to navigate around
furniture and obstacles in the room grid.
"""

import heapq
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathNode:
    """A node in the pathfinding grid."""
    x: int
    y: int
    g_cost: int = 0  # Distance from start
    h_cost: int = 0  # Heuristic distance to goal
    f_cost: int = 0  # Total cost (g + h)
    parent: Optional['PathNode'] = None

    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class PathfindingService:
    """Service for calculating optimal paths through the room grid."""

    def __init__(self, grid_width: int = 64, grid_height: int = 16):
        self.grid_width = grid_width
        self.grid_height = grid_height

    def find_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        assistant_size: Tuple[int, int] = (1, 1)
    ) -> List[Tuple[int, int]]:
        """
        Find the shortest path from start to goal using A* algorithm.

        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            obstacles: Set of obstacle positions that block movement
            assistant_size: Size of the assistant (width, height) in grid cells

        Returns:
            List of (x, y) positions from start to goal, or empty list if no path
        """
        logger.info(f"Finding path from {start} to {goal}")

        # Validate inputs
        if not self._is_valid_position(start) or not self._is_valid_position(goal):
            logger.warning(f"Invalid start {start} or goal {goal} position")
            return []

        if start == goal:
            return [start]

        # Check if goal is reachable (not blocked by obstacles)
        if self._is_position_blocked(goal, obstacles, assistant_size):
            logger.warning(f"Goal position {goal} is blocked")
            return []

        open_set = []
        closed_set = set()

        start_node = PathNode(start[0], start[1])
        start_node.h_cost = self._manhattan_distance(start, goal)
        start_node.f_cost = start_node.h_cost

        heapq.heappush(open_set, start_node)
        open_dict = {(start[0], start[1]): start_node}

        while open_set:
            current_node = heapq.heappop(open_set)
            current_pos = (current_node.x, current_node.y)

            # Remove from open dict
            if current_pos in open_dict:
                del open_dict[current_pos]

            closed_set.add(current_pos)

            # Check if we reached the goal
            if current_pos == goal:
                path = self._reconstruct_path(current_node)
                logger.info(f"Path found with {len(path)} steps")
                return path

            # Check all neighboring cells
            for neighbor_pos in self._get_neighbors(current_pos):
                if neighbor_pos in closed_set:
                    continue

                if not self._is_valid_position(neighbor_pos):
                    continue

                if self._is_position_blocked(neighbor_pos, obstacles, assistant_size):
                    continue

                tentative_g_cost = current_node.g_cost + 1

                # Check if this neighbor is already in open set
                if neighbor_pos in open_dict:
                    neighbor_node = open_dict[neighbor_pos]
                    if tentative_g_cost < neighbor_node.g_cost:
                        # Found a better path to this neighbor
                        neighbor_node.g_cost = tentative_g_cost
                        neighbor_node.f_cost = neighbor_node.g_cost + neighbor_node.h_cost
                        neighbor_node.parent = current_node
                        heapq.heapify(open_set)  # Re-heapify since we changed a value
                else:
                    # New neighbor
                    neighbor_node = PathNode(
                        neighbor_pos[0],
                        neighbor_pos[1],
                        g_cost=tentative_g_cost,
                        h_cost=self._manhattan_distance(neighbor_pos, goal),
                        parent=current_node
                    )
                    heapq.heappush(open_set, neighbor_node)
                    open_dict[neighbor_pos] = neighbor_node

        logger.warning(f"No path found from {start} to {goal}")
        return []

    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within grid bounds."""
        x, y = pos
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height

    def _is_position_blocked(
        self,
        pos: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        assistant_size: Tuple[int, int]
    ) -> bool:
        """
        Check if position is blocked by obstacles considering assistant size.

        Args:
            pos: Position to check (x, y)
            obstacles: Set of obstacle positions
            assistant_size: Size of assistant (width, height)
        """
        x, y = pos
        width, height = assistant_size

        # Check all cells the assistant would occupy
        for dx in range(width):
            for dy in range(height):
                check_pos = (x + dx, y + dy)
                if check_pos in obstacles:
                    return True
                if not self._is_valid_position(check_pos):
                    return True
        return False

    def _get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all valid neighboring positions (4-directional movement)."""
        x, y = pos
        neighbors = [
            (x + 1, y),     # Right
            (x - 1, y),     # Left
            (x, y + 1),     # Down
            (x, y - 1),     # Up
        ]

        # Could add diagonal movement here if desired:
        # neighbors.extend([
        #     (x + 1, y + 1), (x - 1, y + 1),
        #     (x + 1, y - 1), (x - 1, y - 1)
        # ])

        return neighbors

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _reconstruct_path(self, goal_node: PathNode) -> List[Tuple[int, int]]:
        """Reconstruct the path from goal node back to start."""
        path = []
        current = goal_node

        while current:
            path.append((current.x, current.y))
            current = current.parent

        path.reverse()
        return path

    def get_reachable_positions(
        self,
        start: Tuple[int, int],
        obstacles: Set[Tuple[int, int]],
        assistant_size: Tuple[int, int] = (1, 1),
        max_distance: Optional[int] = None
    ) -> Set[Tuple[int, int]]:
        """
        Get all positions reachable from start position.

        Args:
            start: Starting position
            obstacles: Set of obstacle positions
            assistant_size: Size of assistant
            max_distance: Maximum distance to search (None for unlimited)

        Returns:
            Set of all reachable positions
        """
        reachable = set()
        visited = set()
        queue = [(start, 0)]  # (position, distance)

        while queue:
            pos, distance = queue.pop(0)

            if pos in visited:
                continue

            if max_distance is not None and distance > max_distance:
                continue

            visited.add(pos)

            if not self._is_position_blocked(pos, obstacles, assistant_size):
                reachable.add(pos)

                # Add neighbors to queue
                for neighbor in self._get_neighbors(pos):
                    if neighbor not in visited and self._is_valid_position(neighbor):
                        queue.append((neighbor, distance + 1))

        return reachable


# Global service instance
pathfinding_service = PathfindingService()