"""Object sprite for rendering game objects."""

import pygame

from deskmate.domain.object import GameObject


class ObjectSprite:
    """
    Sprite representation of a game object.

    Uses placeholder graphics (colored shapes) that can be replaced
    with actual sprites later.
    """

    def __init__(self, obj: GameObject) -> None:
        """Initialize the object sprite."""
        self.obj_id = obj.id
        self.x = obj.x
        self.y = obj.y
        self.width = obj.width
        self.height = obj.height
        self.can_be_held = obj.can_be_held

        # Get color and shape from the object
        self.color = obj.color
        self.shape = obj.shape

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

        elif self.shape == "diamond":
            # Draw diamond shape
            center_x = self.width // 2
            center_y = self.height // 2
            points = [
                (center_x, 2),  # Top
                (self.width - 2, center_y),  # Right
                (center_x, self.height - 2),  # Bottom
                (2, center_y),  # Left
            ]
            pygame.draw.polygon(self.surface, self.color, points)
            # Add highlight
            highlight_points = [
                (center_x, 6),
                (center_x + 8, center_y - 4),
                (center_x, center_y),
                (center_x - 8, center_y - 4),
            ]
            highlight_color = tuple(min(255, c + 50) for c in self.color)
            pygame.draw.polygon(self.surface, highlight_color, highlight_points)

        else:  # rect (default)
            pygame.draw.rect(
                self.surface, self.color, pygame.Rect(2, 2, self.width - 4, self.height - 4)
            )
            # Add subtle border/depth
            darker_color = tuple(max(0, c - 40) for c in self.color)
            pygame.draw.rect(
                self.surface, darker_color, pygame.Rect(2, 2, 4, self.height - 4)
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
