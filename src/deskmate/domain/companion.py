"""Companion domain model - pure Python, no Pygame dependency."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deskmate.domain.object import GameObject


class CompanionState(Enum):
    """Companion animation/behavior state."""

    IDLE = auto()
    WALKING = auto()
    HOLDING_IDLE = auto()
    HOLDING_WALKING = auto()


class Direction(Enum):
    """Facing direction."""

    LEFT = auto()
    RIGHT = auto()


@dataclass
class Companion:
    """Represents the companion character."""

    x: float
    y: float
    state: CompanionState = CompanionState.IDLE
    direction: Direction = Direction.RIGHT
    held_object: "GameObject | None" = None
    target_x: float | None = None
    target_y: float | None = None
    speaking: bool = False
    current_speech: str = ""

    @property
    def is_moving(self) -> bool:
        """Check if companion is currently moving."""
        return self.target_x is not None and self.target_y is not None

    @property
    def is_holding(self) -> bool:
        """Check if companion is holding something."""
        return self.held_object is not None

    def set_target(self, x: float, y: float) -> None:
        """Set movement target position."""
        self.target_x = x
        self.target_y = y

    def clear_target(self) -> None:
        """Clear the movement target."""
        self.target_x = None
        self.target_y = None

    def pickup(self, obj: "GameObject") -> bool:
        """
        Attempt to pick up an object.

        Returns True if successful, False if object can't be held
        or companion is already holding something.
        """
        if self.held_object is not None:
            return False
        if not obj.can_be_held:
            return False

        self.held_object = obj
        obj.is_held = True
        self._update_state()
        return True

    def drop(self) -> "GameObject | None":
        """
        Drop the currently held object.

        Returns the dropped object, or None if nothing was held.
        The object is placed at the companion's current position.
        """
        if self.held_object is None:
            return None

        obj = self.held_object
        obj.x = self.x
        obj.y = self.y
        obj.is_held = False
        self.held_object = None
        self._update_state()
        return obj

    def say(self, message: str) -> None:
        """Set the companion to speak a message."""
        self.speaking = True
        self.current_speech = message

    def stop_speaking(self) -> None:
        """Stop the companion from speaking."""
        self.speaking = False
        self.current_speech = ""

    def _update_state(self) -> None:
        """Update the companion's animation state based on current status."""
        if self.is_holding:
            self.state = (
                CompanionState.HOLDING_WALKING if self.is_moving else CompanionState.HOLDING_IDLE
            )
        else:
            self.state = CompanionState.WALKING if self.is_moving else CompanionState.IDLE

    def update_direction(self, target_x: float) -> None:
        """Update facing direction based on target."""
        if target_x < self.x:
            self.direction = Direction.LEFT
        elif target_x > self.x:
            self.direction = Direction.RIGHT

    def move_towards_target(self, speed: float, dt: float) -> None:
        """
        Move towards the target position.

        Args:
            speed: Movement speed in pixels per second
            dt: Delta time in seconds
        """
        if self.target_x is None or self.target_y is None:
            return

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = (dx**2 + dy**2) ** 0.5

        # Normalize and scale by speed
        move_distance = speed * dt

        if move_distance >= distance or distance <= 5:
            # Close enough or would overshoot, snap to target
            self.x = self.target_x
            self.y = self.target_y
            self.clear_target()
            self._update_state()
            return

        self.x += (dx / distance) * move_distance
        self.y += (dy / distance) * move_distance
        self.update_direction(self.target_x)
        self._update_state()
