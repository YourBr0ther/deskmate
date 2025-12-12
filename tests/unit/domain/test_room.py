"""Tests for the Room domain model."""

import pytest

from deskmate.domain.object import GameObject
from deskmate.domain.room import Room, WalkableArea


class TestWalkableArea:
    """Tests for WalkableArea class."""

    def test_contains_point_inside(self, walkable_area: WalkableArea) -> None:
        """Test that point inside area returns True."""
        assert walkable_area.contains(400.0, 300.0) is True

    def test_contains_point_on_boundary(self, walkable_area: WalkableArea) -> None:
        """Test that point on boundary returns True."""
        assert walkable_area.contains(0.0, 0.0) is True
        assert walkable_area.contains(800.0, 600.0) is True

    def test_contains_point_outside(self, walkable_area: WalkableArea) -> None:
        """Test that point outside area returns False."""
        assert walkable_area.contains(-10.0, 300.0) is False
        assert walkable_area.contains(810.0, 300.0) is False
        assert walkable_area.contains(400.0, -10.0) is False
        assert walkable_area.contains(400.0, 610.0) is False

    def test_clamp_point_inside(self, walkable_area: WalkableArea) -> None:
        """Test clamping a point already inside."""
        x, y = walkable_area.clamp(400.0, 300.0)
        assert x == 400.0
        assert y == 300.0

    def test_clamp_point_outside(self, walkable_area: WalkableArea) -> None:
        """Test clamping a point outside."""
        x, y = walkable_area.clamp(-50.0, 700.0)
        assert x == 0.0
        assert y == 600.0


class TestRoom:
    """Tests for Room class."""

    def test_room_initializes(self, room: Room) -> None:
        """Test room initialization."""
        assert room.name == "Test Room"
        assert room.width == 800
        assert room.height == 600
        assert len(room.objects) == 0

    def test_add_object(self, room: Room, holdable_object: GameObject) -> None:
        """Test adding object to room."""
        room.add_object(holdable_object)
        assert len(room.objects) == 1
        assert holdable_object in room.objects

    def test_remove_object(self, room: Room, holdable_object: GameObject) -> None:
        """Test removing object from room."""
        room.add_object(holdable_object)
        room.remove_object(holdable_object)
        assert len(room.objects) == 0

    def test_get_object_at(self, room: Room, holdable_object: GameObject) -> None:
        """Test getting object at position."""
        room.add_object(holdable_object)

        # Point within object bounds
        obj = room.get_object_at(
            holdable_object.x + 10, holdable_object.y + 10
        )
        assert obj == holdable_object

    def test_get_object_at_empty(self, room: Room) -> None:
        """Test getting object at position with no object."""
        obj = room.get_object_at(100.0, 100.0)
        assert obj is None

    def test_get_object_at_skips_held(
        self, room: Room, holdable_object: GameObject
    ) -> None:
        """Test that held objects are not returned."""
        room.add_object(holdable_object)
        holdable_object.is_held = True

        obj = room.get_object_at(
            holdable_object.x + 10, holdable_object.y + 10
        )
        assert obj is None

    def test_get_object_by_id(self, room: Room, holdable_object: GameObject) -> None:
        """Test getting object by ID."""
        room.add_object(holdable_object)

        obj = room.get_object_by_id("test_ball")
        assert obj == holdable_object

    def test_get_object_by_id_not_found(self, room: Room) -> None:
        """Test getting non-existent object by ID."""
        obj = room.get_object_by_id("nonexistent")
        assert obj is None

    def test_get_nearby_objects(self, room: Room) -> None:
        """Test getting nearby objects."""
        obj1 = GameObject(id="near", name="Near", x=50.0, y=50.0)
        obj2 = GameObject(id="far", name="Far", x=500.0, y=500.0)
        room.add_object(obj1)
        room.add_object(obj2)

        nearby = room.get_nearby_objects(0.0, 0.0, radius=100)

        assert obj1 in nearby
        assert obj2 not in nearby

    def test_get_nearby_excludes_held(self, room: Room) -> None:
        """Test that held objects are excluded from nearby."""
        obj = GameObject(id="held", name="Held", x=50.0, y=50.0)
        obj.is_held = True
        room.add_object(obj)

        nearby = room.get_nearby_objects(0.0, 0.0, radius=100)

        assert obj not in nearby

    def test_is_walkable(self, room: Room) -> None:
        """Test walkability check."""
        assert room.is_walkable(400.0, 300.0) is True
        assert room.is_walkable(-10.0, 300.0) is False

    def test_clamp_to_walkable(self, room: Room) -> None:
        """Test clamping to walkable area."""
        x, y = room.clamp_to_walkable(-50.0, 700.0)
        assert x == 0.0
        assert y == 600.0
