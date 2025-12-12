"""Tests for the Companion domain model."""

import pytest

from deskmate.domain.companion import Companion, CompanionState, Direction
from deskmate.domain.object import GameObject


class TestCompanion:
    """Tests for Companion class."""

    def test_companion_initializes_with_position(self) -> None:
        """Test that companion starts at given position."""
        companion = Companion(x=100.0, y=200.0)
        assert companion.x == 100.0
        assert companion.y == 200.0

    def test_companion_starts_idle(self) -> None:
        """Test that companion starts in idle state."""
        companion = Companion(x=0.0, y=0.0)
        assert companion.state == CompanionState.IDLE
        assert not companion.is_moving
        assert not companion.is_holding

    def test_companion_can_set_target(self) -> None:
        """Test setting movement target."""
        companion = Companion(x=0.0, y=0.0)
        companion.set_target(100.0, 100.0)

        assert companion.target_x == 100.0
        assert companion.target_y == 100.0
        assert companion.is_moving

    def test_companion_can_clear_target(self) -> None:
        """Test clearing movement target."""
        companion = Companion(x=0.0, y=0.0)
        companion.set_target(100.0, 100.0)
        companion.clear_target()

        assert companion.target_x is None
        assert companion.target_y is None
        assert not companion.is_moving


class TestCompanionPickup:
    """Tests for companion pickup functionality."""

    def test_pickup_holdable_object(
        self, companion: Companion, holdable_object: GameObject
    ) -> None:
        """Test picking up a holdable object."""
        result = companion.pickup(holdable_object)

        assert result is True
        assert companion.held_object == holdable_object
        assert companion.is_holding
        assert holdable_object.is_held

    def test_cannot_pickup_heavy_object(
        self, companion: Companion, heavy_object: GameObject
    ) -> None:
        """Test that heavy objects cannot be picked up."""
        result = companion.pickup(heavy_object)

        assert result is False
        assert companion.held_object is None
        assert not companion.is_holding
        assert not heavy_object.is_held

    def test_cannot_pickup_when_holding(
        self, companion: Companion, holdable_object: GameObject
    ) -> None:
        """Test that companion can't pick up when already holding."""
        other_object = GameObject(id="other", name="Other", x=0.0, y=0.0)

        companion.pickup(holdable_object)
        result = companion.pickup(other_object)

        assert result is False
        assert companion.held_object == holdable_object


class TestCompanionDrop:
    """Tests for companion drop functionality."""

    def test_drop_held_object(
        self, companion: Companion, holdable_object: GameObject
    ) -> None:
        """Test dropping a held object."""
        companion.pickup(holdable_object)
        dropped = companion.drop()

        assert dropped == holdable_object
        assert companion.held_object is None
        assert not companion.is_holding
        assert not holdable_object.is_held

    def test_dropped_object_at_companion_position(
        self, companion: Companion, holdable_object: GameObject
    ) -> None:
        """Test that dropped object is placed at companion position."""
        companion.x = 150.0
        companion.y = 250.0
        companion.pickup(holdable_object)
        dropped = companion.drop()

        assert dropped is not None
        assert dropped.x == 150.0
        assert dropped.y == 250.0

    def test_drop_when_not_holding(self, companion: Companion) -> None:
        """Test drop returns None when not holding anything."""
        result = companion.drop()
        assert result is None


class TestCompanionMovement:
    """Tests for companion movement."""

    def test_move_towards_target(self, companion: Companion) -> None:
        """Test moving towards target position."""
        companion.set_target(200.0, 100.0)
        companion.move_towards_target(speed=100.0, dt=1.0)

        # Should have moved 100 pixels towards target
        assert companion.x == 200.0  # Direct horizontal movement
        assert companion.y == 100.0

    def test_stops_at_target(self, companion: Companion) -> None:
        """Test that companion stops when reaching target."""
        companion.set_target(105.0, 100.0)  # Very close target
        companion.move_towards_target(speed=100.0, dt=1.0)

        assert companion.x == 105.0
        assert companion.y == 100.0
        assert not companion.is_moving

    def test_direction_updates_when_moving_left(self, companion: Companion) -> None:
        """Test direction updates when moving left."""
        companion.x = 200.0
        companion.set_target(100.0, 100.0)  # Target to the left
        companion.move_towards_target(speed=50.0, dt=0.1)

        assert companion.direction == Direction.LEFT

    def test_direction_updates_when_moving_right(self, companion: Companion) -> None:
        """Test direction updates when moving right."""
        companion.set_target(200.0, 100.0)  # Target to the right
        companion.move_towards_target(speed=50.0, dt=0.1)

        assert companion.direction == Direction.RIGHT


class TestCompanionSpeech:
    """Tests for companion speech functionality."""

    def test_say_sets_speech(self, companion: Companion) -> None:
        """Test that say() sets speech state."""
        companion.say("Hello!")

        assert companion.speaking is True
        assert companion.current_speech == "Hello!"

    def test_stop_speaking_clears_speech(self, companion: Companion) -> None:
        """Test that stop_speaking() clears speech state."""
        companion.say("Hello!")
        companion.stop_speaking()

        assert companion.speaking is False
        assert companion.current_speech == ""


class TestCompanionStateTransitions:
    """Tests for companion state transitions."""

    def test_state_walking_when_moving(self, companion: Companion) -> None:
        """Test state changes to walking when moving."""
        companion.set_target(200.0, 100.0)
        companion.move_towards_target(speed=50.0, dt=0.1)

        assert companion.state == CompanionState.WALKING

    def test_state_idle_when_stopped(self, companion: Companion) -> None:
        """Test state changes to idle when stopped."""
        companion.set_target(105.0, 100.0)  # Close target
        companion.move_towards_target(speed=100.0, dt=1.0)

        assert companion.state == CompanionState.IDLE

    def test_state_holding_idle(
        self, companion: Companion, holdable_object: GameObject
    ) -> None:
        """Test holding idle state."""
        companion.pickup(holdable_object)

        assert companion.state == CompanionState.HOLDING_IDLE

    def test_state_holding_walking(
        self, companion: Companion, holdable_object: GameObject
    ) -> None:
        """Test holding walking state."""
        companion.pickup(holdable_object)
        companion.set_target(200.0, 100.0)
        companion.move_towards_target(speed=50.0, dt=0.1)

        assert companion.state == CompanionState.HOLDING_WALKING
