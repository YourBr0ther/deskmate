"""
Assistant service for managing AI assistant state and movement.

This service handles:
- Assistant position tracking and updates
- Movement pathfinding and execution
- State persistence in database
- Action logging and history
"""

import logging
from typing import List, Tuple, Optional, Dict, Any, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from datetime import datetime

from app.models.assistant import AssistantState, AssistantActionLog
from app.models.room_objects import GridObject
from app.services.multi_room_pathfinding import multi_room_pathfinding_service
from app.repositories.assistant_repository import (
    AssistantStateRepository,
    AssistantActionLogRepository
)
from app.repositories.room_repository import RoomObjectRepository
from app.db.connection_manager import get_db_session

logger = logging.getLogger(__name__)


class AssistantService:
    """Service for managing the AI assistant."""

    def __init__(self):
        self.assistant_repo = AssistantStateRepository()
        self.action_log_repo = AssistantActionLogRepository()
        self.room_repo = RoomObjectRepository()

    async def get_assistant_state(self, session: AsyncSession = None) -> AssistantState:
        """Get current assistant state, creating default if needed."""
        if session is None:
            # Legacy compatibility - create session automatically
            async with get_db_session() as session:
                return await self.assistant_repo.get_default_assistant(session)
        return await self.assistant_repo.get_default_assistant(session)

    async def update_assistant_position(
        self,
        session: AsyncSession,
        x: int,
        y: int,
        facing: Optional[str] = None,
        action: str = "idle"
    ) -> Dict[str, Any]:
        """
        Update assistant position in database.

        Args:
            session: Database session
            x: New X coordinate
            y: New Y coordinate
            facing: New facing direction
            action: Current action

        Returns:
            Updated assistant state dictionary
        """
        assistant = await self.assistant_repo.get_default_assistant(session)

        # Update position
        old_position = {"x": assistant.position_x, "y": assistant.position_y}
        updated_assistant = await self.assistant_repo.update_position(session, x, y, facing, action)

        # Log the movement
        await self.action_log_repo.log_action(
            session,
            action_type="move",
            action_data={"from": old_position, "to": {"x": x, "y": y}, "facing": facing},
            position_before=old_position,
            position_after={"x": x, "y": y},
            success=True
        )

        logger.info(f"Assistant moved from {old_position} to ({x}, {y})")
        return updated_assistant.to_dict()

    async def move_assistant_to(
        self,
        session: AsyncSession,
        target_x: int,
        target_y: int,
        validate_path: bool = True
    ) -> Dict[str, Any]:
        """
        Move assistant to target position using pathfinding.

        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            validate_path: Whether to validate path is possible

        Returns:
            Movement result with path and status
        """
        try:
            # Get current assistant state
            assistant = await self.get_assistant_state(session)
            start_pos = (assistant.position_x, assistant.position_y)
            target_pos = (target_x, target_y)

            # Get room obstacles
            obstacles = await self._get_room_obstacles(session)

            if validate_path:
                # Find path using multi-room pathfinding
                path_result = multi_room_pathfinding_service.find_multi_room_path(
                    db=session,
                    floor_plan_id=assistant.current_floor_plan_id or "studio_apartment",
                    start_pos=(float(assistant.position_x), float(assistant.position_y)),
                    start_room_id=assistant.current_room_id or "main_room",
                    goal_pos=(float(target_x), float(target_y)),
                    goal_room_id=assistant.current_room_id or "main_room"
                )
                path = path_result.get("path", [])

                if not path:
                    await self.action_log_repo.log_action(
                        session,
                        action_type="move",
                        action_data={"target": target_pos, "reason": "no_path"},
                        position_before={"x": assistant.position_x, "y": assistant.position_y},
                        success=False,
                        error_message="No path found to target position"
                    )
                    return {
                        "success": False,
                        "error": "No path found to target position",
                        "current_position": {"x": assistant.position_x, "y": assistant.position_y},
                        "target_position": {"x": target_x, "y": target_y}
                    }
            else:
                # Direct movement without pathfinding
                path = [start_pos, target_pos]

            # Calculate facing direction based on movement
            if len(path) > 1:
                # Handle PathPoint objects or tuples
                p1 = path[1]
                p0 = path[0]
                dx = (p1.x if hasattr(p1, 'x') else p1[0]) - (p0.x if hasattr(p0, 'x') else p0[0])
                dy = (p1.y if hasattr(p1, 'y') else p1[1]) - (p0.y if hasattr(p0, 'y') else p0[1])
                facing = self._calculate_facing(dx, dy)
            else:
                facing = assistant.facing_direction

            # Update assistant state with movement
            assistant = await self.assistant_repo.get_default_assistant(session)
            assistant.start_movement(target_x, target_y, path)
            await self.assistant_repo.update(session, assistant)

            # For now, complete movement immediately
            # In future, this could be animated over time
            result = await self.update_assistant_position(session, target_x, target_y, facing, "idle")

            return {
                "success": True,
                "path": path,
                "assistant_state": result,
                "path_length": len(path)
            }

        except Exception as e:
            logger.error(f"Error moving assistant: {e}")
            await self.action_log_repo.log_action(
                session,
                action_type="move",
                action_data={"target": target_pos},
                success=False,
                error_message=str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def sit_on_furniture(self, session: AsyncSession, furniture_id: str) -> Dict[str, Any]:
        """
        Make assistant sit on specified furniture.

        Args:
            furniture_id: ID of furniture to sit on

        Returns:
            Action result
        """
        try:
            # Get furniture object
            furniture = await self.room_repo.get_by_id(session, furniture_id)

            if not furniture:
                return {"success": False, "error": f"Furniture {furniture_id} not found"}

            if furniture.object_type != "furniture":
                return {"success": False, "error": f"Object {furniture_id} is not furniture"}

            # Calculate sitting position (adjacent to furniture)
            sit_x = furniture.position_x - 1  # Sit to the left of furniture
            sit_y = furniture.position_y

            # Move to sitting position
            move_result = await self.move_assistant_to(session, sit_x, sit_y)

            if move_result["success"]:
                # Update action to sitting
                assistant = await self.get_assistant_state(session)
                assistant.set_action("sitting", furniture_id)
                await self.assistant_repo.update(session, assistant)

                await self.action_log_repo.log_action(
                    session,
                    action_type="sit",
                    action_data={"furniture_id": furniture_id},
                    position_after={"x": sit_x, "y": sit_y},
                    success=True
                )

                return {
                    "success": True,
                    "action": "sitting",
                    "furniture": furniture_id,
                    "position": {"x": sit_x, "y": sit_y}
                }

            return move_result

        except Exception as e:
            logger.error(f"Error sitting on furniture: {e}")
            return {"success": False, "error": str(e)}

    async def get_reachable_positions(self, session: AsyncSession) -> Set[Tuple[int, int]]:
        """Get all positions reachable by the assistant."""
        assistant = await self.get_assistant_state(session)
        start_pos = (assistant.position_x, assistant.position_y)
        obstacles = await self._get_room_obstacles(session)

        # Note: pathfinding_service needs to be imported if this method is used
        # For now, return empty set as this method needs pathfinding service integration
        return set()

    async def update_assistant_state(self, session: AsyncSession, assistant_state: AssistantState) -> AssistantState:
        """
        Update assistant state in database.

        Args:
            session: Database session
            assistant_state: Modified assistant state object

        Returns:
            Updated assistant state
        """
        # Merge the updated state
        assistant_state.updated_at = func.now()
        updated_state = await self.assistant_repo.update(session, assistant_state)

        logger.info(f"Updated assistant state: mode={updated_state.mode}, action={updated_state.current_action}")
        return updated_state

    async def record_user_interaction(self, session: AsyncSession = None) -> None:
        """Record that user has interacted with the assistant."""
        if session is None:
            # Legacy compatibility - create session automatically
            async with get_db_session() as session:
                await self.assistant_repo.record_user_interaction(session)
                return
        else:
            await self.assistant_repo.record_user_interaction(session)

    async def set_assistant_mode(self, session: AsyncSession, mode: str) -> Dict[str, Any]:
        """
        Set assistant mode (active/idle).

        Args:
            session: Database session
            mode: New mode ('active' or 'idle')

        Returns:
            Result of mode change
        """
        try:
            assistant = await self.assistant_repo.get_default_assistant(session)
            old_mode = assistant.mode

            updated_assistant = await self.assistant_repo.set_mode(session, mode)

            await self.action_log_repo.log_action(
                session,
                action_type="mode_change",
                action_data={"from_mode": old_mode, "to_mode": mode},
                success=True,
                triggered_by="system"
            )

            logger.info(f"Assistant mode changed from {old_mode} to {mode}")

            return {
                "success": True,
                "old_mode": old_mode,
                "new_mode": mode,
                "assistant_state": updated_assistant.to_dict()
            }

        except Exception as e:
            logger.error(f"Error setting assistant mode: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_energy_level(self, session: AsyncSession, energy_delta: float) -> None:
        """
        Update assistant energy level.

        Args:
            session: Database session
            energy_delta: Change in energy (positive or negative)
        """
        assistant = await self.assistant_repo.update_energy_level(session, energy_delta)
        logger.debug(f"Assistant energy updated by {energy_delta} to {assistant.energy_level}")

    async def get_inactivity_duration(self, session: AsyncSession) -> float:
        """
        Get duration in minutes since last user interaction.

        Args:
            session: Database session

        Returns:
            Minutes since last user interaction
        """
        assistant = await self.get_assistant_state(session)
        if not assistant.last_user_interaction:
            return 0.0

        now = datetime.utcnow()
        time_diff = now - assistant.last_user_interaction
        return time_diff.total_seconds() / 60.0

    async def _get_room_obstacles(self, session: AsyncSession) -> Set[Tuple[int, int]]:
        """Get all obstacle positions in the room."""
        obstacles = set()
        solid_objects = await self.room_repo.get_solid_objects(session)

        for obj in solid_objects:
            for x in range(obj.position_x, obj.position_x + obj.size_width):
                for y in range(obj.position_y, obj.position_y + obj.size_height):
                    obstacles.add((x, y))

        return obstacles

    def _calculate_facing(self, dx: int, dy: int) -> str:
        """Calculate facing direction from movement delta."""
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    # _log_action method removed - now handled by action_log_repo directly


# Global service instance
assistant_service = AssistantService()