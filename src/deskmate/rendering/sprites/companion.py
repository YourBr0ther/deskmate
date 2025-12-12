"""Companion sprite with animation support."""

import pygame

from deskmate.domain.companion import Companion, CompanionState, Direction


class CompanionSprite:
    """
    Sprite representation of the companion.

    Uses placeholder graphics (colored shapes) that can be replaced
    with actual sprite sheets later.
    """

    # Colors for different states
    COLORS = {
        CompanionState.IDLE: (100, 180, 255),  # Blue
        CompanionState.WALKING: (100, 220, 255),  # Lighter blue
        CompanionState.HOLDING_IDLE: (180, 100, 255),  # Purple
        CompanionState.HOLDING_WALKING: (220, 100, 255),  # Lighter purple
    }

    def __init__(self, companion: Companion) -> None:
        """Initialize the companion sprite."""
        self.width = 40
        self.height = 60
        self.x = companion.x
        self.y = companion.y
        self.state = companion.state
        self.direction = companion.direction

        # Animation
        self.animation_frame = 0
        self.animation_timer = 0.0
        self.frame_duration = 0.15  # seconds per frame

        # Create the surface
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._update_surface()

    def update(self, companion: Companion) -> None:
        """Update sprite based on companion state."""
        state_changed = self.state != companion.state
        self.x = companion.x
        self.y = companion.y
        self.state = companion.state
        self.direction = companion.direction

        # Update animation
        if companion.is_moving:
            self.animation_timer += 0.016  # Approximate frame time
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 4

        if state_changed or companion.is_moving:
            self._update_surface()

    def _update_surface(self) -> None:
        """Redraw the sprite surface."""
        self.surface.fill((0, 0, 0, 0))  # Clear with transparency

        color = self.COLORS.get(self.state, (100, 180, 255))

        # Draw body (rounded rectangle approximation)
        body_rect = pygame.Rect(5, 15, 30, 40)
        pygame.draw.rect(self.surface, color, body_rect, border_radius=8)

        # Draw head (circle)
        head_center = (20, 12)
        pygame.draw.circle(self.surface, color, head_center, 10)

        # Draw eyes
        eye_color = (40, 40, 50)
        if self.direction == Direction.RIGHT:
            pygame.draw.circle(self.surface, eye_color, (23, 10), 3)
            pygame.draw.circle(self.surface, (255, 255, 255), (24, 9), 1)
        else:
            pygame.draw.circle(self.surface, eye_color, (17, 10), 3)
            pygame.draw.circle(self.surface, (255, 255, 255), (16, 9), 1)

        # Draw legs with walking animation
        leg_color = tuple(max(0, c - 30) for c in color)
        if self.state in (CompanionState.WALKING, CompanionState.HOLDING_WALKING):
            # Animated legs
            offset = [0, 3, 0, -3][self.animation_frame]
            pygame.draw.rect(
                self.surface, leg_color, pygame.Rect(8, 52 + offset, 8, 8)
            )
            pygame.draw.rect(
                self.surface, leg_color, pygame.Rect(24, 52 - offset, 8, 8)
            )
        else:
            # Standing legs
            pygame.draw.rect(self.surface, leg_color, pygame.Rect(8, 52, 8, 8))
            pygame.draw.rect(self.surface, leg_color, pygame.Rect(24, 52, 8, 8))

        # Draw held item indicator (small square)
        if self.state in (CompanionState.HOLDING_IDLE, CompanionState.HOLDING_WALKING):
            item_color = (255, 220, 100)
            if self.direction == Direction.RIGHT:
                pygame.draw.rect(
                    self.surface, item_color, pygame.Rect(32, 25, 8, 8)
                )
            else:
                pygame.draw.rect(
                    self.surface, item_color, pygame.Rect(0, 25, 8, 8)
                )

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the sprite to the screen."""
        # Flip horizontally if facing left
        surface = self.surface
        if self.direction == Direction.LEFT:
            surface = pygame.transform.flip(self.surface, True, False)

        # Center the sprite on the companion position
        rect = surface.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(surface, rect)
