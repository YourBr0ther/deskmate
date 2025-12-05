"""
Room navigation service for managing assistant movement and room transitions.

This service coordinates multi-room navigation, doorway transitions,
and maintains assistant state during movement across rooms.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.assistant import AssistantState, AssistantActionLog
from app.models.rooms import FloorPlan, Room, Doorway
from app.services.multi_room_pathfinding import multi_room_pathfinding_service, RoomGraph
from app.db.database import get_db

logger = logging.getLogger(__name__)


class RoomNavigationService:
    """Service for managing assistant navigation across multiple rooms."""

    def __init__(self):
        self.active_navigation = {}  # Track active navigation sessions
        self.transition_callbacks = []  # Callbacks for room transitions

    async def navigate_to_position(
        self,
        db: Session,
        assistant_id: str,
        target_x: float,
        target_y: float,
        target_room_id: Optional[str] = None,
        user_initiated: bool = True
    ) -> Dict[str, Any]:
        """
        Navigate assistant to target position, handling room transitions.

        Args:
            db: Database session
            assistant_id: Assistant identifier
            target_x: Target X coordinate
            target_y: Target Y coordinate
            target_room_id: Target room (if different from current)
            user_initiated: Whether navigation was triggered by user

        Returns:
            Navigation result with path and status
        """
        logger.info(f"Navigating assistant {assistant_id} to ({target_x}, {target_y}) in room {target_room_id}")

        # Get assistant current state
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()
        if not assistant:
            return {"success": False, "error": "Assistant not found"}

        # Get current floor plan
        if not assistant.current_floor_plan_id:
            return {"success": False, "error": "No active floor plan"}

        # Determine target room
        if not target_room_id:
            target_room_id = assistant.current_room_id

        if not target_room_id:
            return {"success": False, "error": "No target room specified"}

        # Validate target room exists
        target_room = db.query(Room).filter(
            Room.id == target_room_id,
            Room.floor_plan_id == assistant.current_floor_plan_id
        ).first()

        if not target_room:
            return {"success": False, "error": f"Target room {target_room_id} not found"}

        # Check if target position is within room bounds
        if not self._is_position_in_room(target_x, target_y, target_room):
            logger.warning(f"Target position ({target_x}, {target_y}) is outside room {target_room_id} bounds")
            # Adjust position to nearest valid position within room
            target_x, target_y = self._clamp_to_room_bounds(target_x, target_y, target_room)

        # Find path using multi-room pathfinding
        current_pos = (assistant.position_x, assistant.position_y)
        current_room = assistant.current_room_id

        path_result = multi_room_pathfinding_service.find_multi_room_path(
            db=db,
            floor_plan_id=assistant.current_floor_plan_id,
            start_pos=current_pos,
            start_room_id=current_room,
            goal_pos=(target_x, target_y),
            goal_room_id=target_room_id
        )

        if not path_result["path"]:
            return {"success": False, "error": "No path found to target position"}

        # Open any doors that need to be opened
        doors_opened = []
        for doorway_id in path_result["doorways_to_open"]:
            door_result = await self._open_door(db, doorway_id)
            doors_opened.append(door_result)

        # Start navigation
        navigation_id = f"{assistant_id}_{datetime.now().timestamp()}"
        navigation_session = {
            "id": navigation_id,
            "assistant_id": assistant_id,
            "path": path_result["path"],
            "room_transitions": path_result["room_transitions"],
            "current_step": 0,
            "target_position": (target_x, target_y),
            "target_room_id": target_room_id,
            "user_initiated": user_initiated,
            "start_time": datetime.now(),
            "estimated_duration": path_result["estimated_duration"]
        }

        self.active_navigation[navigation_id] = navigation_session

        # Update assistant state
        assistant.start_movement(
            target_x=target_x,
            target_y=target_y,
            path=path_result["path"],
            target_room_id=target_room_id
        )
        db.commit()

        # Log action
        self._log_navigation_action(
            db, assistant_id, "navigation_started",
            {
                "target": {"x": target_x, "y": target_y, "room_id": target_room_id},
                "path_length": len(path_result["path"]),
                "room_transitions": len(path_result["room_transitions"]),
                "estimated_duration": path_result["estimated_duration"]
            },
            "user" if user_initiated else "autonomous"
        )

        # Start async movement execution
        asyncio.create_task(self._execute_navigation(db, navigation_session))

        return {
            "success": True,
            "navigation_id": navigation_id,
            "path": path_result["path"],
            "room_transitions": path_result["room_transitions"],
            "doors_opened": doors_opened,
            "estimated_duration": path_result["estimated_duration"],
            "total_distance": path_result["total_distance"]
        }

    async def _execute_navigation(self, db: Session, navigation_session: Dict[str, Any]):
        """Execute navigation path with room transitions."""
        navigation_id = navigation_session["id"]
        assistant_id = navigation_session["assistant_id"]
        path = navigation_session["path"]
        room_transitions = navigation_session["room_transitions"]

        try:
            logger.info(f"Executing navigation {navigation_id} with {len(path)} waypoints")

            # Execute each step in the path
            for i, waypoint in enumerate(path):
                if navigation_id not in self.active_navigation:
                    logger.info(f"Navigation {navigation_id} was cancelled")
                    return

                # Check for room transitions
                for transition in room_transitions:
                    if self._is_at_doorway(waypoint, transition["doorway_position"]):
                        await self._handle_room_transition(db, assistant_id, transition)

                # Move to waypoint
                await self._move_to_waypoint(db, assistant_id, waypoint)

                # Update navigation progress (check existence to avoid race condition)
                if navigation_id in self.active_navigation:
                    self.active_navigation[navigation_id]["current_step"] = i + 1

                # Small delay for smooth movement visualization
                await asyncio.sleep(0.1)

            # Complete navigation
            await self._complete_navigation(db, navigation_id)

        except Exception as e:
            logger.error(f"Error executing navigation {navigation_id}: {e}")
            await self._cancel_navigation(db, navigation_id, str(e))

    async def _move_to_waypoint(self, db: Session, assistant_id: str, waypoint: Dict[str, Any]):
        """Move assistant to a specific waypoint."""
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()
        if not assistant:
            return

        # Update position
        assistant.update_position(
            x=waypoint["x"],
            y=waypoint["y"],
            room_id=waypoint["room_id"]
        )

        # Calculate facing direction based on movement
        if assistant.target_x and assistant.target_y:
            dx = waypoint["x"] - assistant.position_x
            dy = waypoint["y"] - assistant.position_y

            if abs(dx) > abs(dy):
                facing = "right" if dx > 0 else "left"
            else:
                facing = "down" if dy > 0 else "up"

            assistant.facing_direction = facing

        db.commit()

        # Notify subscribers of position update
        await self._notify_position_update(assistant_id, waypoint)

    async def _handle_room_transition(self, db: Session, assistant_id: str, transition: Dict[str, Any]):
        """Handle transition between rooms through doorway."""
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()
        if not assistant:
            return

        from_room = transition["from_room"]
        to_room = transition["to_room"]
        doorway_id = transition["doorway_id"]

        logger.info(f"Transitioning assistant {assistant_id} from {from_room} to {to_room} via {doorway_id}")

        # Update assistant room
        assistant.change_room(to_room)
        db.commit()

        # Log room transition
        self._log_navigation_action(
            db, assistant_id, "room_transition",
            {
                "from_room": from_room,
                "to_room": to_room,
                "doorway_id": doorway_id,
                "position": transition["doorway_position"]
            },
            "autonomous"
        )

        # Broadcast room transition via WebSocket
        await self._notify_room_transition(assistant_id, from_room, to_room, doorway_id)

        # Notify callbacks
        for callback in self.transition_callbacks:
            try:
                await callback(assistant_id, from_room, to_room, doorway_id)
            except Exception as e:
                logger.error(f"Error in transition callback: {e}")

    async def _notify_room_transition(self, assistant_id: str, from_room: str, to_room: str, doorway_id: str):
        """Notify clients of room transition via WebSocket."""
        try:
            # Delayed import to avoid circular dependency
            from app.api.websocket import connection_manager

            message = {
                "type": "room_transition",
                "data": {
                    "assistant_id": assistant_id,
                    "from_room": from_room,
                    "to_room": to_room,
                    "doorway_id": doorway_id,
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }

            await connection_manager.broadcast(message)
            logger.debug(f"Broadcast room transition for assistant {assistant_id}: {from_room} -> {to_room}")
        except Exception as e:
            logger.error(f"Failed to broadcast room transition: {e}")

    async def _open_door(self, db: Session, doorway_id: str) -> Dict[str, Any]:
        """Open a door if it's closed."""
        doorway = db.query(Doorway).filter(Doorway.id == doorway_id).first()
        if not doorway:
            return {"success": False, "error": f"Doorway {doorway_id} not found"}

        if not doorway.has_door:
            return {"success": True, "message": "No door to open"}

        if doorway.door_state == "open":
            return {"success": True, "message": "Door already open"}

        if doorway.door_state == "locked":
            return {"success": False, "error": "Door is locked"}

        # Open the door
        doorway.door_state = "open"
        db.commit()

        logger.info(f"Opened door {doorway_id}")
        return {"success": True, "message": f"Opened door {doorway.name or doorway_id}"}

    async def _complete_navigation(self, db: Session, navigation_id: str):
        """Complete navigation and clean up."""
        # Use pop() which is atomic - avoids race condition between check and delete
        session = self.active_navigation.pop(navigation_id, None)
        if not session:
            return

        assistant_id = session["assistant_id"]

        # Update assistant state
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()
        if assistant:
            assistant.complete_movement()
            db.commit()

        # Log completion
        self._log_navigation_action(
            db, assistant_id, "navigation_completed",
            {
                "navigation_id": navigation_id,
                "final_position": session["target_position"],
                "final_room": session["target_room_id"],
                "duration": (datetime.now() - session["start_time"]).total_seconds()
            },
            "system"
        )

        logger.info(f"Navigation {navigation_id} completed")

    async def _cancel_navigation(self, db: Session, navigation_id: str, reason: str = "user_cancelled"):
        """Cancel active navigation."""
        # Use pop() which is atomic - avoids race condition between check and delete
        session = self.active_navigation.pop(navigation_id, None)
        if not session:
            return

        assistant_id = session["assistant_id"]

        # Update assistant state
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()
        if assistant:
            assistant.is_moving = False
            assistant.target_x = None
            assistant.target_y = None
            assistant.target_room_id = None
            assistant.movement_path = None
            assistant.current_action = "idle"
            db.commit()

        # Log cancellation
        self._log_navigation_action(
            db, assistant_id, "navigation_cancelled",
            {"navigation_id": navigation_id, "reason": reason},
            "system"
        )

        logger.info(f"Navigation {navigation_id} cancelled: {reason}")

    def _is_position_in_room(self, x: float, y: float, room: Room) -> bool:
        """Check if position is within room bounds."""
        return (room.bounds_x <= x <= room.bounds_x + room.bounds_width and
                room.bounds_y <= y <= room.bounds_y + room.bounds_height)

    def _clamp_to_room_bounds(self, x: float, y: float, room: Room) -> Tuple[float, float]:
        """Clamp position to room bounds with padding."""
        padding = 20  # pixels from edge

        clamped_x = max(room.bounds_x + padding,
                       min(x, room.bounds_x + room.bounds_width - padding))
        clamped_y = max(room.bounds_y + padding,
                       min(y, room.bounds_y + room.bounds_height - padding))

        return clamped_x, clamped_y

    def _is_at_doorway(self, waypoint: Dict[str, Any], doorway_pos: Tuple[float, float], threshold: float = 30.0) -> bool:
        """Check if waypoint is at doorway position."""
        distance = ((waypoint["x"] - doorway_pos[0])**2 + (waypoint["y"] - doorway_pos[1])**2)**0.5
        return distance <= threshold

    def _log_navigation_action(
        self,
        db: Session,
        assistant_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        triggered_by: str
    ):
        """Log navigation action to database."""
        try:
            log_entry = AssistantActionLog(
                assistant_id=assistant_id,
                action_type=action_type,
                action_data=action_data,
                triggered_by=triggered_by,
                success=True
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging navigation action: {e}")

    async def _notify_position_update(self, assistant_id: str, position: Dict[str, Any]):
        """Notify clients of assistant position update via WebSocket."""
        try:
            # Delayed import to avoid circular dependency
            from app.api.websocket import connection_manager

            message = {
                "type": "position_update",
                "data": {
                    "assistant_id": assistant_id,
                    "position": position,
                    "timestamp": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }

            await connection_manager.broadcast(message)
            logger.debug(f"Broadcast position update for assistant {assistant_id}: {position}")
        except Exception as e:
            logger.error(f"Failed to broadcast position update: {e}")

    def add_transition_callback(self, callback):
        """Add callback for room transitions."""
        self.transition_callbacks.append(callback)

    def get_active_navigation(self, assistant_id: str) -> Optional[Dict[str, Any]]:
        """Get active navigation session for assistant."""
        for session in self.active_navigation.values():
            if session["assistant_id"] == assistant_id:
                return session
        return None

    def cancel_navigation(self, navigation_id: str) -> bool:
        """Cancel navigation by ID."""
        # Use pop() which is atomic - avoids race condition between check and delete
        return self.active_navigation.pop(navigation_id, None) is not None


# Global service instance
room_navigation_service = RoomNavigationService()