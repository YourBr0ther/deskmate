"""Game object domain model - pure Python, no Pygame dependency."""

from dataclasses import dataclass


@dataclass
class GameObject:
    """Represents an interactable object in the room."""

    id: str
    name: str
    x: float
    y: float
    width: int = 32
    height: int = 32
    can_be_held: bool = True
    is_held: bool = False
    sprite_name: str | None = None
    color: tuple[int, int, int] = (200, 200, 100)  # RGB color
    shape: str = "rect"  # circle, rect, diamond, plant

    @property
    def center_x(self) -> float:
        """Get the center X position."""
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        """Get the center Y position."""
        return self.y + self.height / 2

    def contains_point(self, px: float, py: float) -> bool:
        """Check if a point is within this object's bounds."""
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

    def distance_to(self, x: float, y: float) -> float:
        """Calculate distance from object center to a point."""
        dx = self.center_x - x
        dy = self.center_y - y
        return (dx**2 + dy**2) ** 0.5
