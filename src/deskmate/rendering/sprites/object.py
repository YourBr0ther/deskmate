"""Object sprite for rendering game objects."""

import pygame

from deskmate.domain.object import GameObject


class ObjectSprite:
    """
    Sprite representation of a game object.

    Uses placeholder graphics (colored shapes) that can be replaced
    with actual sprites later.
    """

    # Colors for different object types (based on sprite_name or id)
    OBJECT_COLORS = {
        "ball": (255, 100, 100),  # Red
        "book": (100, 150, 255),  # Blue
        "plant": (100, 200, 100),  # Green
        "default": (200, 200, 100),  # Yellow
    }

    OBJECT_SHAPES = {
        "ball": "circle",
        "book": "rect",
        "plant": "plant",
        "default": "rect",
    }

    def __init__(self, obj: GameObject) -> None:
        """Initialize the object sprite."""
        self.obj_id = obj.id
        self.x = obj.x
        self.y = obj.y
        self.width = obj.width
        self.height = obj.height
        self.can_be_held = obj.can_be_held

        # Determine color and shape
        self.color = self.OBJECT_COLORS.get(obj.id, self.OBJECT_COLORS["default"])
        self.shape = self.OBJECT_SHAPES.get(obj.id, self.OBJECT_SHAPES["default"])

        # Create the surface
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw_shape()

    def _draw_shape(self) -> None:
        """Draw the object shape on the surface."""
        self.surface.fill((0, 0, 0, 0))

        if self.shape == "circle":
            center = (self.width // 2, self.height // 2)
            radius = min(self.width, self.height) // 2 - 2
            pygame.draw.circle(self.surface, self.color, center, radius)
            # Add highlight
            highlight_pos = (center[0] - radius // 3, center[1] - radius // 3)
            pygame.draw.circle(
                self.surface, (255, 255, 255), highlight_pos, radius // 4
            )

        elif self.shape == "plant":
            # Draw pot
            pot_color = (180, 120, 80)
            pot_rect = pygame.Rect(8, self.height - 20, self.width - 16, 20)
            pygame.draw.rect(self.surface, pot_color, pot_rect)

            # Draw plant leaves
            leaf_color = self.color
            # Center leaf
            pygame.draw.ellipse(
                self.surface, leaf_color, pygame.Rect(14, 5, 20, 35)
            )
            # Side leaves
            pygame.draw.ellipse(
                self.surface, leaf_color, pygame.Rect(4, 15, 18, 25)
            )
            pygame.draw.ellipse(
                self.surface, leaf_color, pygame.Rect(26, 15, 18, 25)
            )

        else:  # rect (book, default)
            pygame.draw.rect(
                self.surface, self.color, pygame.Rect(2, 2, self.width - 4, self.height - 4)
            )
            # Add book spine detail
            if self.shape == "rect" and self.obj_id == "book":
                spine_color = tuple(max(0, c - 40) for c in self.color)
                pygame.draw.rect(
                    self.surface, spine_color, pygame.Rect(2, 2, 6, self.height - 4)
                )

        # Draw border if can be held
        if self.can_be_held:
            border_color = (255, 255, 255, 100)
            pygame.draw.rect(
                self.surface, border_color, pygame.Rect(0, 0, self.width, self.height), 1
            )

    def update(self, obj: GameObject) -> None:
        """Update sprite based on object state."""
        self.x = obj.x
        self.y = obj.y

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the sprite to the screen."""
        screen.blit(self.surface, (int(self.x), int(self.y)))

        # Draw interaction hint for holdable objects
        if self.can_be_held:
            # Small indicator that object can be picked up
            indicator_rect = pygame.Rect(
                int(self.x) + self.width - 8,
                int(self.y) - 4,
                8,
                8,
            )
            pygame.draw.rect(screen, (255, 255, 100), indicator_rect, border_radius=2)
