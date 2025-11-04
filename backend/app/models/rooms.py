"""
SQLAlchemy models for multi-room system with continuous coordinates.

This module defines the database schemas for:
- Rooms: Individual rooms within a floor plan
- FloorPlans: Complete floor plan templates with multiple rooms
- Walls: Architectural elements that define room boundaries
- Doorways: Connections between rooms
- FurnitureItems: Objects with continuous positioning
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from app.db.base import Base


class FloorPlan(Base):
    """
    A complete floor plan template containing multiple rooms.

    This represents an entire house, apartment, or office layout
    with rooms, walls, doorways, and default furniture placement.
    """
    __tablename__ = "floor_plans"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., 'two_bedroom_apartment'
    name = Column(String, nullable=False)  # e.g., 'Two Bedroom Apartment'
    description = Column(Text)  # Description for users
    category = Column(String, nullable=False)  # 'apartment', 'house', 'office'

    # Floor plan dimensions (in pixels)
    width = Column(Integer, nullable=False)  # Total width in pixels
    height = Column(Integer, nullable=False)  # Total height in pixels
    scale = Column(Float, default=1.0)  # Pixels per unit (foot/meter)
    units = Column(String, default='feet')  # 'feet' or 'meters'

    # Visual styling
    background_image = Column(String)  # Floor texture/pattern
    background_color = Column(String, default='#f5f5f5')
    wall_color = Column(String, default='#333333')
    wall_thickness = Column(Integer, default=8)  # Wall thickness in pixels

    # Metadata
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, default='system')
    is_template = Column(Boolean, default=True)  # Template vs user-created
    is_active = Column(Boolean, default=False)  # Currently active floor plan
    version = Column(String, default='1.0')

    # Relationships
    rooms = relationship("Room", back_populates="floor_plan", cascade="all, delete-orphan")
    walls = relationship("Wall", back_populates="floor_plan", cascade="all, delete-orphan")
    doorways = relationship("Doorway", back_populates="floor_plan", cascade="all, delete-orphan")
    furniture = relationship("FurnitureItem", back_populates="floor_plan", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "dimensions": {
                "width": self.width,
                "height": self.height,
                "scale": self.scale,
                "units": self.units
            },
            "styling": {
                "background_image": self.background_image,
                "background_color": self.background_color,
                "wall_color": self.wall_color,
                "wall_thickness": self.wall_thickness
            },
            "metadata": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "created_by": self.created_by,
                "is_template": self.is_template,
                "is_active": self.is_active,
                "version": self.version
            },
            "rooms": [room.to_dict() for room in self.rooms],
            "walls": [wall.to_dict() for wall in self.walls],
            "doorways": [doorway.to_dict() for doorway in self.doorways],
            "furniture": [item.to_dict() for item in self.furniture]
        }


class Room(Base):
    """
    Individual room within a floor plan.

    Defines a named area with boundaries and room-specific properties.
    """
    __tablename__ = "rooms"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., 'living_room_1'
    floor_plan_id = Column(String, ForeignKey('floor_plans.id'), nullable=False)
    name = Column(String, nullable=False)  # e.g., 'Living Room', 'Master Bedroom'
    room_type = Column(String, nullable=False)  # 'bedroom', 'kitchen', 'living_room', etc.

    # Room boundaries (rectangular for now)
    bounds_x = Column(Float, nullable=False)  # Top-left X coordinate
    bounds_y = Column(Float, nullable=False)  # Top-left Y coordinate
    bounds_width = Column(Float, nullable=False)  # Room width
    bounds_height = Column(Float, nullable=False)  # Room height

    # Room properties
    floor_color = Column(String, default='#e5e5e5')  # Floor color/texture
    floor_material = Column(String, default='hardwood')  # hardwood, carpet, tile, etc.
    lighting_level = Column(Float, default=0.8)  # 0.0 to 1.0
    temperature = Column(Float, default=72.0)  # Temperature in Fahrenheit

    # Accessibility and navigation
    is_accessible = Column(Boolean, default=True)  # Can assistant enter this room
    entry_points = Column(JSON)  # List of doorway IDs that connect to this room

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Relationships
    floor_plan = relationship("FloorPlan", back_populates="rooms")
    furniture = relationship("FurnitureItem", back_populates="room")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "floor_plan_id": self.floor_plan_id,
            "name": self.name,
            "type": self.room_type,
            "bounds": {
                "x": self.bounds_x,
                "y": self.bounds_y,
                "width": self.bounds_width,
                "height": self.bounds_height
            },
            "properties": {
                "floor_color": self.floor_color,
                "floor_material": self.floor_material,
                "lighting_level": self.lighting_level,
                "temperature": self.temperature
            },
            "accessibility": {
                "is_accessible": self.is_accessible,
                "entry_points": self.entry_points or []
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this room's boundaries."""
        return (self.bounds_x <= x <= self.bounds_x + self.bounds_width and
                self.bounds_y <= y <= self.bounds_y + self.bounds_height)


class Wall(Base):
    """
    Walls that define room boundaries and architectural structure.

    Walls can be exterior (building boundaries) or interior (room dividers).
    """
    __tablename__ = "walls"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., 'wall_living_north'
    floor_plan_id = Column(String, ForeignKey('floor_plans.id'), nullable=False)
    name = Column(String)  # Optional name for the wall

    # Wall geometry (line segment)
    start_x = Column(Float, nullable=False)  # Starting X coordinate
    start_y = Column(Float, nullable=False)  # Starting Y coordinate
    end_x = Column(Float, nullable=False)    # Ending X coordinate
    end_y = Column(Float, nullable=False)    # Ending Y coordinate

    # Wall properties
    wall_type = Column(String, default='interior')  # 'interior' or 'exterior'
    thickness = Column(Float, default=8.0)  # Wall thickness in pixels
    material = Column(String, default='drywall')  # Wall material
    color = Column(String, default='#333333')  # Wall color

    # Structural properties
    is_load_bearing = Column(Boolean, default=False)
    can_have_doorways = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Relationships
    floor_plan = relationship("FloorPlan", back_populates="walls")
    doorways = relationship("Doorway", back_populates="wall")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "floor_plan_id": self.floor_plan_id,
            "name": self.name,
            "geometry": {
                "start": {"x": self.start_x, "y": self.start_y},
                "end": {"x": self.end_x, "y": self.end_y}
            },
            "properties": {
                "type": self.wall_type,
                "thickness": self.thickness,
                "material": self.material,
                "color": self.color
            },
            "structural": {
                "is_load_bearing": self.is_load_bearing,
                "can_have_doorways": self.can_have_doorways
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def length(self) -> float:
        """Calculate the length of this wall."""
        return ((self.end_x - self.start_x) ** 2 + (self.end_y - self.start_y) ** 2) ** 0.5

    def intersects_line(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check if this wall intersects with another line segment."""
        # Implementation of line-line intersection
        # Using the standard line intersection algorithm
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        A = (self.start_x, self.start_y)
        B = (self.end_x, self.end_y)
        C = (x1, y1)
        D = (x2, y2)

        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


class Doorway(Base):
    """
    Doorways that connect rooms and allow movement between them.

    Doorways are openings in walls that the assistant can pass through.
    """
    __tablename__ = "doorways"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., 'door_living_kitchen'
    floor_plan_id = Column(String, ForeignKey('floor_plans.id'), nullable=False)
    wall_id = Column(String, ForeignKey('walls.id'), nullable=False)
    name = Column(String)  # Optional name for the doorway

    # Doorway position on the wall (as percentage from start to end)
    position_on_wall = Column(Float, nullable=False)  # 0.0 to 1.0
    width = Column(Float, default=80.0)  # Doorway width in pixels

    # Connected rooms
    room_a_id = Column(String, nullable=False)  # First connected room
    room_b_id = Column(String, nullable=False)  # Second connected room

    # Doorway properties
    doorway_type = Column(String, default='open')  # 'open', 'door', 'archway'
    has_door = Column(Boolean, default=False)  # Physical door present
    door_state = Column(String, default='open')  # 'open', 'closed', 'locked'

    # Access control
    is_accessible = Column(Boolean, default=True)  # Can assistant pass through
    requires_interaction = Column(Boolean, default=False)  # Must click to pass

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Relationships
    floor_plan = relationship("FloorPlan", back_populates="doorways")
    wall = relationship("Wall", back_populates="doorways")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "floor_plan_id": self.floor_plan_id,
            "wall_id": self.wall_id,
            "name": self.name,
            "position": {
                "position_on_wall": self.position_on_wall,
                "width": self.width
            },
            "connections": {
                "room_a": self.room_a_id,
                "room_b": self.room_b_id
            },
            "properties": {
                "type": self.doorway_type,
                "has_door": self.has_door,
                "door_state": self.door_state
            },
            "accessibility": {
                "is_accessible": self.is_accessible,
                "requires_interaction": self.requires_interaction
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def get_world_position(self) -> Tuple[float, float]:
        """Calculate the world position of this doorway based on its wall."""
        if self.wall:
            # Calculate position along the wall
            wall_vector_x = self.wall.end_x - self.wall.start_x
            wall_vector_y = self.wall.end_y - self.wall.start_y

            position_x = self.wall.start_x + (wall_vector_x * self.position_on_wall)
            position_y = self.wall.start_y + (wall_vector_y * self.position_on_wall)

            return (position_x, position_y)
        return (0.0, 0.0)

    def connects_rooms(self, room1_id: str, room2_id: str) -> bool:
        """Check if this doorway connects the specified rooms."""
        return ((self.room_a_id == room1_id and self.room_b_id == room2_id) or
                (self.room_a_id == room2_id and self.room_b_id == room1_id))


class FurnitureItem(Base):
    """
    Furniture and objects with continuous positioning.

    This replaces the old GridObject system with pixel-based positioning.
    """
    __tablename__ = "furniture_items"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., 'couch_living_001'
    floor_plan_id = Column(String, ForeignKey('floor_plans.id'), nullable=False)
    room_id = Column(String, ForeignKey('rooms.id'), nullable=True)  # Can be null for cross-room items
    name = Column(String, nullable=False)  # e.g., 'Sectional Sofa'
    description = Column(Text)  # For LLM context
    furniture_type = Column(String, nullable=False)  # 'furniture', 'decoration', 'appliance'

    # Continuous positioning
    position_x = Column(Float, nullable=False)  # X coordinate in pixels
    position_y = Column(Float, nullable=False)  # Y coordinate in pixels
    rotation = Column(Float, default=0.0)  # Rotation in degrees (0-360)

    # Size and shape
    width = Column(Float, nullable=False)  # Width in pixels
    height = Column(Float, nullable=False)  # Height in pixels
    shape = Column(String, default='rectangle')  # 'rectangle', 'circle', 'polygon'
    shape_data = Column(JSON)  # Additional shape data for complex shapes

    # Physical properties
    is_solid = Column(Boolean, default=True)  # Blocks movement
    is_interactive = Column(Boolean, default=True)  # Can be clicked/used
    is_movable = Column(Boolean, default=False)  # Can be dragged around
    z_index = Column(Integer, default=0)  # Rendering order

    # Visual representation
    sprite_name = Column(String)  # e.g., 'couch_sectional.svg'
    color_scheme = Column(String)  # Primary color
    material = Column(String)  # 'wood', 'metal', 'fabric', etc.
    style = Column(String)  # 'modern', 'traditional', 'industrial', etc.

    # Functional properties
    can_sit_on = Column(Boolean, default=False)  # Assistant can sit on this
    can_place_items_on = Column(Boolean, default=False)  # Can hold other objects
    storage_capacity = Column(Integer, default=0)  # Number of items it can store

    # State management
    current_states = Column(JSON)  # Dynamic states (on/off, open/closed, etc.)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, default='system')
    last_moved_at = Column(DateTime)
    last_interacted_at = Column(DateTime)

    # Relationships
    floor_plan = relationship("FloorPlan", back_populates="furniture")
    room = relationship("Room", back_populates="furniture")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "floor_plan_id": self.floor_plan_id,
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "type": self.furniture_type,
            "position": {
                "x": self.position_x,
                "y": self.position_y,
                "rotation": self.rotation
            },
            "geometry": {
                "width": self.width,
                "height": self.height,
                "shape": self.shape,
                "shape_data": self.shape_data
            },
            "properties": {
                "solid": self.is_solid,
                "interactive": self.is_interactive,
                "movable": self.is_movable,
                "z_index": self.z_index
            },
            "visual": {
                "sprite": self.sprite_name,
                "color": self.color_scheme,
                "material": self.material,
                "style": self.style
            },
            "functional": {
                "can_sit_on": self.can_sit_on,
                "can_place_items_on": self.can_place_items_on,
                "storage_capacity": self.storage_capacity
            },
            "states": self.current_states or {},
            "metadata": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "created_by": self.created_by,
                "last_moved_at": self.last_moved_at.isoformat() if self.last_moved_at else None,
                "last_interacted_at": self.last_interacted_at.isoformat() if self.last_interacted_at else None
            }
        }

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Get the bounding box of this furniture item (x1, y1, x2, y2)."""
        # For now, assume rectangular bounding box
        # TODO: Handle rotation and complex shapes
        x1 = self.position_x
        y1 = self.position_y
        x2 = self.position_x + self.width
        y2 = self.position_y + self.height
        return (x1, y1, x2, y2)

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this furniture item."""
        x1, y1, x2, y2 = self.get_bounding_box()
        return x1 <= x <= x2 and y1 <= y <= y2

    def intersects_with(self, other: 'FurnitureItem') -> bool:
        """Check if this furniture item intersects with another."""
        x1, y1, x2, y2 = self.get_bounding_box()
        ox1, oy1, ox2, oy2 = other.get_bounding_box()

        return not (x2 < ox1 or x1 > ox2 or y2 < oy1 or y1 > oy2)