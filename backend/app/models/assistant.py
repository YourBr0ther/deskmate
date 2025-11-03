"""
SQLAlchemy model for the assistant state and tracking.

This module defines the database schema for the AI assistant including
position, status, mood, and activity tracking.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from app.db.base import Base


class AssistantState(Base):
    """
    Current state of the AI assistant.

    Tracks position, mood, activity, and other dynamic properties
    that change as the assistant moves and interacts.
    """
    __tablename__ = "assistant_state"

    # Primary key (single assistant for now)
    id = Column(String, primary_key=True, default="default")

    # Position and movement
    position_x = Column(Integer, nullable=False, default=32)  # Grid X coordinate
    position_y = Column(Integer, nullable=False, default=8)   # Grid Y coordinate
    facing_direction = Column(String, default="right")  # "up", "down", "left", "right"

    # Movement state
    is_moving = Column(Boolean, default=False)
    target_x = Column(Integer, nullable=True)  # Target position when moving
    target_y = Column(Integer, nullable=True)
    movement_path = Column(JSON, nullable=True)  # Current path being followed
    movement_speed = Column(Float, default=1.0)  # Cells per second

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
            "position": {"x": self.position_x, "y": self.position_y},
            "facing": self.facing_direction,
            "movement": {
                "is_moving": self.is_moving,
                "target": {"x": self.target_x, "y": self.target_y} if self.target_x is not None else None,
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

    def update_position(self, x: int, y: int, facing: Optional[str] = None):
        """Update assistant position and related timestamps."""
        self.position_x = x
        self.position_y = y
        if facing:
            self.facing_direction = facing
        self.last_moved_at = func.now()
        self.updated_at = func.now()

    def start_movement(self, target_x: int, target_y: int, path: list):
        """Start movement to target position with given path."""
        self.is_moving = True
        self.target_x = target_x
        self.target_y = target_y
        self.movement_path = path
        self.current_action = "walking"
        self.updated_at = func.now()

    def complete_movement(self):
        """Complete movement and update position to target."""
        if self.target_x is not None and self.target_y is not None:
            self.update_position(self.target_x, self.target_y)

        self.is_moving = False
        self.target_x = None
        self.target_y = None
        self.movement_path = None
        self.current_action = "idle"

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