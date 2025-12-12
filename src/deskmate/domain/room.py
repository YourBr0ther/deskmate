"""Room domain model - pure Python, no Pygame dependency."""

from dataclasses import dataclass, field

from deskmate.domain.object import GameObject


@dataclass
class WalkableArea:
    """Rectangular walkable area bounds."""

    min_x: int
    max_x: int
    min_y: int
    max_y: int

    def contains(self, x: float, y: float) -> bool:
        """Check if a point is within the walkable area."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def clamp(self, x: float, y: float) -> tuple[float, float]:
        """Clamp a point to be within the walkable area."""
        clamped_x = max(self.min_x, min(self.max_x, x))
        clamped_y = max(self.min_y, min(self.max_y, y))
        return clamped_x, clamped_y


@dataclass
class Room:
    """Represents a room/environment."""

    name: str
    width: int
    height: int
    walkable_area: WalkableArea
    objects: list[GameObject] = field(default_factory=list)
    background_path: str | None = None

    def add_object(self, obj: GameObject) -> None:
        """Add an object to the room."""
        self.objects.append(obj)

    def remove_object(self, obj: GameObject) -> None:
        """Remove an object from the room."""
        if obj in self.objects:
            self.objects.remove(obj)

    def get_object_at(self, x: float, y: float) -> GameObject | None:
        """Get the object at a given position, if any."""
        for obj in self.objects:
            if not obj.is_held and obj.contains_point(x, y):
                return obj
        return None

    def get_object_by_id(self, obj_id: str) -> GameObject | None:
        """Get an object by its ID."""
        for obj in self.objects:
            if obj.id == obj_id:
                return obj
        return None

    def get_nearby_objects(
        self, x: float, y: float, radius: float = 100
    ) -> list[GameObject]:
        """Get objects within a certain radius of a point."""
        nearby = []
        for obj in self.objects:
            if not obj.is_held and obj.distance_to(x, y) <= radius:
                nearby.append(obj)
        return nearby

    def is_walkable(self, x: float, y: float) -> bool:
        """Check if a position is walkable."""
        return self.walkable_area.contains(x, y)

    def clamp_to_walkable(self, x: float, y: float) -> tuple[float, float]:
        """Clamp a position to the walkable area."""
        return self.walkable_area.clamp(x, y)
