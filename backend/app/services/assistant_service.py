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
from app.services.pathfinding import pathfinding_service
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AssistantService:
    """Service for managing the AI assistant."""

    async def get_db_session(self) -> AsyncSession:
        """Get database session."""
        return AsyncSessionLocal()

    async def get_assistant_state(self) -> AssistantState:
        """Get current assistant state, creating default if needed."""
        async with await self.get_db_session() as session:
            stmt = select(AssistantState).where(AssistantState.id == "default")
            result = await session.execute(stmt)
            assistant = result.scalar_one_or_none()

            if not assistant:
                # Create default assistant state
                assistant = AssistantState(
                    id="default",
                    position_x=32,
                    position_y=8,
                    facing_direction="right",
                    current_action="idle",
                    mood="neutral"
                )
                session.add(assistant)
                await session.commit()
                await session.refresh(assistant)
                logger.info("Created default assistant state")

            return assistant

    async def update_assistant_position(
        self,
        x: int,
        y: int,
        facing: Optional[str] = None,
        action: str = "idle"
    ) -> Dict[str, Any]:
        """
        Update assistant position in database.

        Args:
            x: New X coordinate
            y: New Y coordinate
            facing: New facing direction
            action: Current action

        Returns:
            Updated assistant state dictionary
        """
        async with await self.get_db_session() as session:
            stmt = select(AssistantState).where(AssistantState.id == "default")
            result = await session.execute(stmt)
            assistant = result.scalar_one_or_none()

            if not assistant:
                assistant = await self.get_assistant_state()

            # Update position
            old_position = {"x": assistant.position_x, "y": assistant.position_y}
            assistant.update_position(x, y, facing)
            assistant.set_action(action)

            await session.commit()
            await session.refresh(assistant)

            # Log the movement
            await self._log_action(
                action_type="move",
                action_data={"from": old_position, "to": {"x": x, "y": y}, "facing": facing},
                position_before=old_position,
                position_after={"x": x, "y": y},
                success=True
            )

            logger.info(f"Assistant moved from {old_position} to ({x}, {y})")
            return assistant.to_dict()

    async def move_assistant_to(
        self,
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
            assistant = await self.get_assistant_state()
            start_pos = (assistant.position_x, assistant.position_y)
            target_pos = (target_x, target_y)

            # Get room obstacles
            obstacles = await self._get_room_obstacles()

            if validate_path:
                # Find path using A* algorithm
                path = pathfinding_service.find_path(start_pos, target_pos, obstacles)

                if not path:
                    await self._log_action(
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
                dx = path[1][0] - path[0][0]
                dy = path[1][1] - path[0][1]
                facing = self._calculate_facing(dx, dy)
            else:
                facing = assistant.facing_direction

            # Update assistant state with movement
            async with await self.get_db_session() as session:
                stmt = select(AssistantState).where(AssistantState.id == "default")
                result = await session.execute(stmt)
                assistant = result.scalar_one_or_none()

                assistant.start_movement(target_x, target_y, path)
                await session.commit()

            # For now, complete movement immediately
            # In future, this could be animated over time
            result = await self.update_assistant_position(target_x, target_y, facing, "idle")

            return {
                "success": True,
                "path": path,
                "assistant_state": result,
                "path_length": len(path)
            }

        except Exception as e:
            logger.error(f"Error moving assistant: {e}")
            await self._log_action(
                action_type="move",
                action_data={"target": target_pos},
                success=False,
                error_message=str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def sit_on_furniture(self, furniture_id: str) -> Dict[str, Any]:
        """
        Make assistant sit on specified furniture.

        Args:
            furniture_id: ID of furniture to sit on

        Returns:
            Action result
        """
        try:
            # Get furniture object
            async with await self.get_db_session() as session:
                stmt = select(GridObject).where(GridObject.id == furniture_id)
                result = await session.execute(stmt)
                furniture = result.scalar_one_or_none()

                if not furniture:
                    return {"success": False, "error": f"Furniture {furniture_id} not found"}

                if furniture.object_type != "furniture":
                    return {"success": False, "error": f"Object {furniture_id} is not furniture"}

                # Calculate sitting position (adjacent to furniture)
                sit_x = furniture.position_x - 1  # Sit to the left of furniture
                sit_y = furniture.position_y

                # Move to sitting position
                move_result = await self.move_assistant_to(sit_x, sit_y)

                if move_result["success"]:
                    # Update action to sitting
                    assistant = await self.get_assistant_state()
                    assistant.set_action("sitting", furniture_id)

                    async with await self.get_db_session() as session:
                        session.add(assistant)
                        await session.commit()

                    await self._log_action(
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

    async def get_reachable_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions reachable by the assistant."""
        assistant = await self.get_assistant_state()
        start_pos = (assistant.position_x, assistant.position_y)
        obstacles = await self._get_room_obstacles()

        return pathfinding_service.get_reachable_positions(start_pos, obstacles)

    async def _get_room_obstacles(self) -> Set[Tuple[int, int]]:
        """Get all obstacle positions in the room."""
        obstacles = set()

        async with await self.get_db_session() as session:
            stmt = select(GridObject).where(GridObject.is_solid == True)
            result = await session.execute(stmt)
            solid_objects = result.scalars().all()

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

    async def _log_action(
        self,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None,
        position_before: Optional[Dict[str, Any]] = None,
        position_after: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        triggered_by: str = "user"
    ):
        """Log an assistant action."""
        try:
            async with await self.get_db_session() as session:
                log_entry = AssistantActionLog(
                    action_type=action_type,
                    action_data=action_data or {},
                    position_before=position_before,
                    position_after=position_after,
                    success=success,
                    error_message=error_message,
                    triggered_by=triggered_by
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"Error logging action: {e}")


# Global service instance
assistant_service = AssistantService()