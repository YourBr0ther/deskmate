"""
SQLAlchemy model for the assistant state and tracking.

This module defines the database schema for the AI assistant including
position, status, mood, and activity tracking for multi-room environments
with continuous coordinate positioning.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from app.db.base import Base


class AssistantState(Base):
    """
    Current state of the AI assistant.

    Tracks position, mood, activity, and other dynamic properties
    that change as the assistant moves and interacts across multiple rooms.
    """
    __tablename__ = "assistant_state"

    # Primary key (single assistant for now)
    id = Column(String, primary_key=True, default="default")

    # Multi-room positioning
    current_floor_plan_id = Column(String, nullable=True)  # Current floor plan
    current_room_id = Column(String, nullable=True)  # Current room within floor plan
    position_x = Column(Float, nullable=False, default=650.0)  # Continuous X coordinate (pixels)
    position_y = Column(Float, nullable=False, default=300.0)  # Continuous Y coordinate (pixels)
    facing_direction = Column(String, default="right")  # "up", "down", "left", "right"
    facing_angle = Column(Float, default=0.0)  # Precise facing angle in degrees (0-360)

    # Movement state
    is_moving = Column(Boolean, default=False)
    target_x = Column(Float, nullable=True)  # Target position when moving
    target_y = Column(Float, nullable=True)
    target_room_id = Column(String, nullable=True)  # Target room for cross-room movement
    movement_path = Column(JSON, nullable=True)  # Current path being followed
    movement_speed = Column(Float, default=100.0)  # Pixels per second

    # Activity and status
    current_action = Column(String, default="idle")  # "idle", "walking", "sitting", "talking"
    mood = Column(String, default="neutral")  # "happy", "sad", "neutral", "excited", "tired"
    expression = Column(String, default="default")  # Current facial expression
    energy_level = Column(Float, default=1.0)  # 0.0 to 1.0

    # Interaction state
    holding_object_id = Column(String, nullable=True)  # ID of object being held
    sitting_on_object_id = Column(String, nullable=True)  # ID of furniture being sat on
    interacting_with_object_id = Column(String, nullable=True)  # ID of object being used

    # Mode and behavior
    mode = Column(String, default="active")  # "active", "idle", "sleeping"
    attention_level = Column(Float, default=1.0)  # How responsive to user
    last_user_interaction = Column(DateTime, default=func.now())

    # Goals and memory
    current_goals = Column(JSON, default=list)  # List of current objectives
    working_memory = Column(JSON, default=list)  # Recent actions and thoughts

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_moved_at = Column(DateTime, nullable=True)
    last_action_at = Column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "location": {
                "floor_plan_id": self.current_floor_plan_id,
                "room_id": self.current_room_id,
                "position": {"x": self.position_x, "y": self.position_y},
                "facing": self.facing_direction,
                "facing_angle": self.facing_angle
            },
            "movement": {
                "is_moving": self.is_moving,
                "target": {
                    "x": self.target_x,
                    "y": self.target_y,
                    "room_id": self.target_room_id
                } if self.target_x is not None else None,
                "path": self.movement_path,
                "speed": self.movement_speed
            },
            "status": {
                "action": self.current_action,
                "mood": self.mood,
                "expression": self.expression,
                "energy": self.energy_level,
                "mode": self.mode,
                "attention": self.attention_level
            },
            "interaction": {
                "holding": self.holding_object_id,
                "sitting_on": self.sitting_on_object_id,
                "interacting_with": self.interacting_with_object_id
            },
            "goals": self.current_goals,
            "working_memory": self.working_memory,
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "last_moved_at": self.last_moved_at.isoformat() if self.last_moved_at else None,
                "last_action_at": self.last_action_at.isoformat() if self.last_action_at else None,
                "last_user_interaction": self.last_user_interaction.isoformat() if self.last_user_interaction else None
            }
        }

    def update_position(self, x: float, y: float, room_id: Optional[str] = None,
                       facing: Optional[str] = None, facing_angle: Optional[float] = None):
        """Update assistant position and related timestamps."""
        self.position_x = x
        self.position_y = y
        if room_id:
            self.current_room_id = room_id
        if facing:
            self.facing_direction = facing
        if facing_angle is not None:
            self.facing_angle = facing_angle
        self.last_moved_at = func.now()
        self.updated_at = func.now()

    def start_movement(self, target_x: float, target_y: float, path: list,
                      target_room_id: Optional[str] = None):
        """Start movement to target position with given path."""
        self.is_moving = True
        self.target_x = target_x
        self.target_y = target_y
        self.target_room_id = target_room_id
        self.movement_path = path
        self.current_action = "walking"
        self.updated_at = func.now()

    def complete_movement(self):
        """Complete movement and update position to target."""
        if self.target_x is not None and self.target_y is not None:
            self.update_position(self.target_x, self.target_y, self.target_room_id)

        self.is_moving = False
        self.target_x = None
        self.target_y = None
        self.target_room_id = None
        self.movement_path = None
        self.current_action = "idle"

    def change_room(self, new_room_id: str, new_floor_plan_id: Optional[str] = None):
        """Move assistant to a different room."""
        self.current_room_id = new_room_id
        if new_floor_plan_id:
            self.current_floor_plan_id = new_floor_plan_id
        self.updated_at = func.now()

    def get_position(self) -> Tuple[float, float]:
        """Get current position as tuple."""
        return (self.position_x, self.position_y)

    def get_distance_to(self, x: float, y: float) -> float:
        """Calculate distance to a point."""
        dx = self.position_x - x
        dy = self.position_y - y
        return (dx * dx + dy * dy) ** 0.5

    def is_near(self, x: float, y: float, threshold: float = 50.0) -> bool:
        """Check if assistant is near a specific position."""
        return self.get_distance_to(x, y) <= threshold

    def set_action(self, action: str, object_id: Optional[str] = None):
        """Set current action and related object interaction."""
        self.current_action = action
        self.last_action_at = func.now()
        self.updated_at = func.now()

        if action == "sitting" and object_id:
            self.sitting_on_object_id = object_id
        elif action == "holding" and object_id:
            self.holding_object_id = object_id
        elif action == "interacting" and object_id:
            self.interacting_with_object_id = object_id
        elif action == "idle":
            # Clear interaction states when idle
            self.sitting_on_object_id = None
            self.interacting_with_object_id = None

    def set_mood(self, mood: str, expression: Optional[str] = None):
        """Update mood and optionally expression."""
        self.mood = mood
        if expression:
            self.expression = expression
        self.updated_at = func.now()


class AssistantActionLog(Base):
    """
    Log of assistant actions for debugging and analysis.

    Tracks all actions taken by the assistant for review and improvement.
    """
    __tablename__ = "assistant_action_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assistant_id = Column(String, default="default")  # FK to assistant_state

    # Action details
    action_type = Column(String, nullable=False)  # "move", "interact", "speak", etc.
    action_data = Column(JSON)  # Specific action parameters

    # Context
    position_before = Column(JSON)  # Position before action
    position_after = Column(JSON)   # Position after action
    room_state = Column(JSON)       # Snapshot of room state

    # Outcome
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # How long action took

    # Metadata
    triggered_by = Column(String, default="autonomous")  # "user", "autonomous", "system"
    reasoning = Column(Text, nullable=True)  # AI reasoning for action

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "assistant_id": self.assistant_id,
            "action": {
                "type": self.action_type,
                "data": self.action_data,
                "success": self.success,
                "error": self.error_message,
                "duration_ms": self.duration_ms
            },
            "context": {
                "position_before": self.position_before,
                "position_after": self.position_after,
                "room_state": self.room_state,
                "triggered_by": self.triggered_by,
                "reasoning": self.reasoning
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }