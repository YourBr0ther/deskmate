"""Pytest configuration and fixtures."""

import pytest

from deskmate.domain.companion import Companion
from deskmate.domain.conversation import Conversation
from deskmate.domain.object import GameObject
from deskmate.domain.room import Room, WalkableArea


@pytest.fixture
def walkable_area() -> WalkableArea:
    """Create a test walkable area."""
    return WalkableArea(min_x=0, max_x=800, min_y=0, max_y=600)


@pytest.fixture
def room(walkable_area: WalkableArea) -> Room:
    """Create a test room."""
    return Room(
        name="Test Room",
        width=800,
        height=600,
        walkable_area=walkable_area,
    )


@pytest.fixture
def companion() -> Companion:
    """Create a test companion."""
    return Companion(x=100.0, y=100.0)


@pytest.fixture
def holdable_object() -> GameObject:
    """Create a holdable test object."""
    return GameObject(
        id="test_ball",
        name="Test Ball",
        x=200.0,
        y=200.0,
        can_be_held=True,
    )


@pytest.fixture
def heavy_object() -> GameObject:
    """Create a non-holdable test object."""
    return GameObject(
        id="test_rock",
        name="Heavy Rock",
        x=300.0,
        y=300.0,
        can_be_held=False,
    )


@pytest.fixture
def conversation() -> Conversation:
    """Create a test conversation."""
    return Conversation(max_history=10)
