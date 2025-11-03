"""
SQLAlchemy models for room objects and spatial data.

This module defines the database schemas for:
- GridObjects: Physical objects in the room
- ObjectStates: Dynamic states of objects
- StorageItems: Objects in storage closet
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from app.db.base import Base


class GridObject(Base):
    """
    Physical objects that exist in the room grid.

    This includes both large hardcoded furniture and small movable objects.
    """
    __tablename__ = "grid_objects"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., 'bed', 'lamp_001'
    name = Column(String, nullable=False)  # e.g., 'Bed', 'Table Lamp'
    description = Column(Text)  # For LLM context
    object_type = Column(String, nullable=False)  # 'furniture', 'decoration', 'tool'

    # Grid positioning
    position_x = Column(Integer, nullable=False)  # Grid X coordinate
    position_y = Column(Integer, nullable=False)  # Grid Y coordinate
    size_width = Column(Integer, nullable=False, default=1)  # Grid cells wide
    size_height = Column(Integer, nullable=False, default=1)  # Grid cells tall

    # Physical properties
    is_solid = Column(Boolean, default=True)  # Blocks movement
    is_interactive = Column(Boolean, default=True)  # Can be clicked/used
    is_movable = Column(Boolean, default=False)  # Can be dragged around

    # Visual representation
    sprite_name = Column(String)  # e.g., 'lamp_icon.png'
    color_scheme = Column(String)  # e.g., 'purple', 'orange'
    render_priority = Column(Integer, default=0)  # Drawing order

    # Metadata
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, default='system')  # 'system', 'user', 'assistant'
    last_moved_at = Column(DateTime)

    # Relationships
    states = relationship("ObjectState", back_populates="object", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.object_type,
            "position": {"x": self.position_x, "y": self.position_y},
            "size": {"width": self.size_width, "height": self.size_height},
            "properties": {
                "solid": self.is_solid,
                "interactive": self.is_interactive,
                "movable": self.is_movable
            },
            "sprite": self.sprite_name,
            "color": self.color_scheme,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }


class ObjectState(Base):
    """
    Dynamic states of objects (open/closed, on/off, etc.).

    Stores key-value pairs for object properties that can change.
    """
    __tablename__ = "object_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(String, ForeignKey('grid_objects.id'), nullable=False)
    state_key = Column(String, nullable=False)  # e.g., 'open', 'power', 'color'
    state_value = Column(String, nullable=False)  # e.g., 'true', 'on', 'red'

    # Metadata
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String, default='system')  # Who changed this state

    # Relationships
    object = relationship("GridObject", back_populates="states")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "key": self.state_key,
            "value": self.state_value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by
        }


class StorageItem(Base):
    """
    Objects stored in the virtual storage closet.

    These are small objects that aren't currently placed in the room.
    """
    __tablename__ = "storage_items"

    id = Column(String, primary_key=True)  # e.g., 'mug_001', 'book_007'
    name = Column(String, nullable=False)
    description = Column(Text)
    object_type = Column(String, nullable=False)

    # Physical properties (for when placed in room)
    default_size_width = Column(Integer, default=1)
    default_size_height = Column(Integer, default=1)
    is_solid = Column(Boolean, default=True)
    is_interactive = Column(Boolean, default=True)

    # Visual properties
    sprite_name = Column(String)
    color_scheme = Column(String)

    # Storage metadata
    stored_at = Column(DateTime, default=func.now())
    created_by = Column(String, default='user')  # Who created this object
    usage_count = Column(Integer, default=0)  # How many times placed in room

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.object_type,
            "default_size": {"width": self.default_size_width, "height": self.default_size_height},
            "properties": {
                "solid": self.is_solid,
                "interactive": self.is_interactive,
                "movable": True  # Storage items are always movable
            },
            "sprite": self.sprite_name,
            "color": self.color_scheme,
            "stored_at": self.stored_at.isoformat() if self.stored_at else None,
            "created_by": self.created_by,
            "usage_count": self.usage_count
        }


class RoomLayout(Base):
    """
    Room configuration and layout settings.

    Stores room dimensions, themes, and global settings.
    """
    __tablename__ = "room_layouts"

    id = Column(String, primary_key=True)  # e.g., 'default', 'bedroom', 'office'
    name = Column(String, nullable=False)
    description = Column(Text)

    # Grid dimensions
    grid_width = Column(Integer, default=64)
    grid_height = Column(Integer, default=16)
    cell_width = Column(Integer, default=20)  # Pixels
    cell_height = Column(Integer, default=30)  # Pixels

    # Visual theme
    background_color = Column(String, default='#1a1a1a')
    grid_color = Column(String, default='#374151')
    wall_positions = Column(JSON)  # Array of wall cell positions

    # Metadata
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=False)  # Only one active layout

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "grid_size": {"width": self.grid_width, "height": self.grid_height},
            "cell_size": {"width": self.cell_width, "height": self.cell_height},
            "theme": {
                "background": self.background_color,
                "grid": self.grid_color
            },
            "walls": self.wall_positions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }