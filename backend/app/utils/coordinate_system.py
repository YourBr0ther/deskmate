"""
Unified Coordinate System for DeskMate

This module provides a single, consistent pixel-based coordinate system
to replace the previous dual grid/pixel system. All spatial calculations
throughout DeskMate now use pixel coordinates exclusively.

Constants:
- ROOM_WIDTH: 1920 pixels (standard room width)
- ROOM_HEIGHT: 480 pixels (standard room height)
- CELL_SIZE: 30 pixels (for backward compatibility with grid-based calculations)

Key principles:
1. All coordinates are in pixels (float values allowed)
2. Origin (0,0) is at top-left corner
3. X increases rightward, Y increases downward
4. All spatial functions operate on pixel coordinates
"""

import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass

# Room dimensions in pixels (standardized across entire application)
ROOM_WIDTH = 1920
ROOM_HEIGHT = 480

# Grid compatibility (for legacy calculations)
GRID_WIDTH = 64
GRID_HEIGHT = 16
CELL_SIZE = 30  # pixels per grid cell

# Distance thresholds in pixels
INTERACTION_DISTANCE = 80.0  # Distance for object interaction
NEARBY_DISTANCE = 150.0      # Distance for "nearby" object detection
MOVEMENT_PRECISION = 5.0     # Precision for movement calculations


@dataclass
class Position:
    """Represents a position in pixel coordinates."""
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Union[int, float]]) -> "Position":
        """Create Position from dictionary."""
        return cls(float(data["x"]), float(data["y"]))

    def distance_to(self, other: "Position") -> float:
        """Calculate Euclidean distance to another position."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def manhattan_distance_to(self, other: "Position") -> float:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def is_within_bounds(self) -> bool:
        """Check if position is within room bounds."""
        return 0 <= self.x <= ROOM_WIDTH and 0 <= self.y <= ROOM_HEIGHT

    def clamp_to_bounds(self) -> "Position":
        """Clamp position to room bounds."""
        return Position(
            max(0, min(ROOM_WIDTH, self.x)),
            max(0, min(ROOM_HEIGHT, self.y))
        )


@dataclass
class Size:
    """Represents size in pixels."""
    width: float
    height: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format."""
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: Dict[str, Union[int, float]]) -> "Size":
        """Create Size from dictionary."""
        return cls(float(data["width"]), float(data["height"]))


@dataclass
class BoundingBox:
    """Represents a rectangular area in pixel coordinates."""
    position: Position
    size: Size

    @property
    def left(self) -> float:
        return self.position.x

    @property
    def right(self) -> float:
        return self.position.x + self.size.width

    @property
    def top(self) -> float:
        return self.position.y

    @property
    def bottom(self) -> float:
        return self.position.y + self.size.height

    @property
    def center(self) -> Position:
        """Get center position of the bounding box."""
        return Position(
            self.position.x + self.size.width / 2,
            self.position.y + self.size.height / 2
        )

    def contains_point(self, point: Position) -> bool:
        """Check if a point is within this bounding box."""
        return (self.left <= point.x < self.right and
                self.top <= point.y < self.bottom)

    def overlaps_with(self, other: "BoundingBox") -> bool:
        """Check if this bounding box overlaps with another."""
        return (self.left < other.right and
                self.right > other.left and
                self.top < other.bottom and
                self.bottom > other.top)

    def distance_to_point(self, point: Position) -> float:
        """Calculate minimum distance from point to this bounding box."""
        if self.contains_point(point):
            return 0.0

        # Calculate distance to closest edge
        dx = max(0, max(self.left - point.x, point.x - self.right))
        dy = max(0, max(self.top - point.y, point.y - self.bottom))

        return math.sqrt(dx*dx + dy*dy)


class CoordinateSystem:
    """
    Unified coordinate system utilities using pixel-based calculations exclusively.

    All methods in this class work with pixel coordinates. This replaces the
    previous dual grid/pixel system with a single, consistent approach.
    """

    @staticmethod
    def calculate_distance(pos1: Union[Position, Dict[str, float]],
                         pos2: Union[Position, Dict[str, float]]) -> float:
        """Calculate Euclidean distance between two positions."""
        if isinstance(pos1, dict):
            pos1 = Position.from_dict(pos1)
        if isinstance(pos2, dict):
            pos2 = Position.from_dict(pos2)

        return pos1.distance_to(pos2)

    @staticmethod
    def is_within_interaction_distance(pos1: Union[Position, Dict[str, float]],
                                     pos2: Union[Position, Dict[str, float]]) -> bool:
        """Check if two positions are within interaction distance."""
        distance = CoordinateSystem.calculate_distance(pos1, pos2)
        return distance <= INTERACTION_DISTANCE

    @staticmethod
    def is_nearby(pos1: Union[Position, Dict[str, float]],
                  pos2: Union[Position, Dict[str, float]]) -> bool:
        """Check if two positions are nearby (for visibility/awareness)."""
        distance = CoordinateSystem.calculate_distance(pos1, pos2)
        return distance <= NEARBY_DISTANCE

    @staticmethod
    def find_nearest_valid_position(target: Position,
                                   obstacles: List[BoundingBox]) -> Position:
        """
        Find the nearest valid position to target that doesn't collide with obstacles.
        """
        # If target is already valid, return it
        if CoordinateSystem.is_position_valid(target, obstacles):
            return target

        # Search in expanding rings around the target
        search_radius = 10.0
        max_search_radius = 200.0
        step_size = 5.0

        while search_radius <= max_search_radius:
            # Check positions in a circle around target
            for angle in range(0, 360, 15):  # Check every 15 degrees
                rad = math.radians(angle)
                test_pos = Position(
                    target.x + search_radius * math.cos(rad),
                    target.y + search_radius * math.sin(rad)
                )

                if (test_pos.is_within_bounds() and
                    CoordinateSystem.is_position_valid(test_pos, obstacles)):
                    return test_pos

            search_radius += step_size

        # Fallback: return center of room
        return Position(ROOM_WIDTH / 2, ROOM_HEIGHT / 2)

    @staticmethod
    def is_position_valid(position: Position,
                         obstacles: List[BoundingBox]) -> bool:
        """Check if a position is valid (within bounds and not colliding)."""
        if not position.is_within_bounds():
            return False

        # Check collision with obstacles
        point_box = BoundingBox(position, Size(1, 1))
        for obstacle in obstacles:
            if obstacle.overlaps_with(point_box):
                return False

        return True

    @staticmethod
    def get_objects_within_distance(center: Position,
                                  objects: List[Dict[str, Any]],
                                  distance: float) -> List[Dict[str, Any]]:
        """Get all objects within specified distance from center position."""
        nearby_objects = []

        for obj in objects:
            obj_pos = Position.from_dict(obj.get("position", {"x": 0, "y": 0}))

            if CoordinateSystem.calculate_distance(center, obj_pos) <= distance:
                nearby_objects.append(obj)

        return nearby_objects

    @staticmethod
    def get_interaction_candidates(assistant_pos: Union[Position, Dict[str, float]],
                                 objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get objects that are within interaction distance of the assistant."""
        if isinstance(assistant_pos, dict):
            assistant_pos = Position.from_dict(assistant_pos)

        return CoordinateSystem.get_objects_within_distance(
            assistant_pos, objects, INTERACTION_DISTANCE
        )

    @staticmethod
    def get_nearby_objects(assistant_pos: Union[Position, Dict[str, float]],
                         objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get objects that are nearby (for awareness/visibility)."""
        if isinstance(assistant_pos, dict):
            assistant_pos = Position.from_dict(assistant_pos)

        return CoordinateSystem.get_objects_within_distance(
            assistant_pos, objects, NEARBY_DISTANCE
        )


class LegacyGridConverter:
    """
    Utilities for converting between legacy grid coordinates and pixel coordinates.

    This class should only be used during the transition period for backward
    compatibility. New code should use pixel coordinates exclusively.
    """

    @staticmethod
    def grid_to_pixels(grid_x: int, grid_y: int) -> Position:
        """Convert grid coordinates to pixel coordinates."""
        return Position(
            float(grid_x * CELL_SIZE),
            float(grid_y * CELL_SIZE)
        )

    @staticmethod
    def pixels_to_grid(pixel_x: float, pixel_y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to grid coordinates (rounded)."""
        return (
            int(round(pixel_x / CELL_SIZE)),
            int(round(pixel_y / CELL_SIZE))
        )

    @staticmethod
    def is_legacy_grid_coordinate(pos: Dict[str, Any]) -> bool:
        """
        Detect if coordinates appear to be legacy grid-based.

        This is a heuristic check used during transition period.
        """
        x, y = pos.get("x", 0), pos.get("y", 0)

        # Check if values are small integers that fit grid dimensions
        return (isinstance(x, int) and isinstance(y, int) and
                0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT)

    @staticmethod
    def normalize_position(pos: Dict[str, Any]) -> Position:
        """
        Normalize a position to pixel coordinates, handling legacy grid coordinates.

        This method detects legacy grid coordinates and converts them to pixels.
        For new pixel coordinates, it returns them unchanged.
        """
        if LegacyGridConverter.is_legacy_grid_coordinate(pos):
            # Convert from grid to pixels
            return LegacyGridConverter.grid_to_pixels(pos["x"], pos["y"])
        else:
            # Already in pixel coordinates
            return Position.from_dict(pos)


# Convenience functions for common operations
def distance(pos1: Union[Position, Dict[str, float]],
            pos2: Union[Position, Dict[str, float]]) -> float:
    """Calculate distance between two positions."""
    return CoordinateSystem.calculate_distance(pos1, pos2)


def is_nearby(pos1: Union[Position, Dict[str, float]],
             pos2: Union[Position, Dict[str, float]]) -> bool:
    """Check if two positions are nearby."""
    return CoordinateSystem.is_nearby(pos1, pos2)


def can_interact(pos1: Union[Position, Dict[str, float]],
                pos2: Union[Position, Dict[str, float]]) -> bool:
    """Check if two positions are within interaction distance."""
    return CoordinateSystem.is_within_interaction_distance(pos1, pos2)


def clamp_to_room(pos: Union[Position, Dict[str, float]]) -> Position:
    """Clamp position to room bounds."""
    if isinstance(pos, dict):
        pos = Position.from_dict(pos)
    return pos.clamp_to_bounds()


def create_bounding_box(position: Union[Position, Dict[str, float]],
                       size: Union[Size, Dict[str, float]]) -> BoundingBox:
    """Create a bounding box from position and size."""
    if isinstance(position, dict):
        position = Position.from_dict(position)
    if isinstance(size, dict):
        size = Size.from_dict(size)
    return BoundingBox(position, size)