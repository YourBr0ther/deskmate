"""
Repository for assistant-related database operations.

This module provides:
- Assistant state management
- Action logging
- Position tracking
- Movement history
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.sql import func

from app.models.assistant import AssistantState, AssistantActionLog
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AssistantStateRepository(BaseRepository[AssistantState]):
    """Repository for assistant state operations."""

    def __init__(self):
        super().__init__(AssistantState)

    async def get_default_assistant(self, session: AsyncSession) -> AssistantState:
        """
        Get the default assistant state, creating it if it doesn't exist.

        Returns:
            Default assistant state
        """
        try:
            assistant = await self.get_by_id(session, "default")

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
                assistant = await self.create(session, assistant)
                logger.info("Created default assistant state")

            return assistant

        except Exception as e:
            logger.error(f"Error getting default assistant: {e}")
            raise

    async def update_position(
        self,
        session: AsyncSession,
        x: int,
        y: int,
        facing: Optional[str] = None,
        action: str = "idle"
    ) -> AssistantState:
        """
        Update assistant position and state.

        Args:
            session: Database session
            x: New X coordinate
            y: New Y coordinate
            facing: New facing direction
            action: Current action

        Returns:
            Updated assistant state
        """
        try:
            assistant = await self.get_default_assistant(session)

            # Update position
            assistant.update_position(x, y, facing)
            assistant.set_action(action)

            return await self.update(session, assistant)

        except Exception as e:
            logger.error(f"Error updating assistant position to ({x}, {y}): {e}")
            raise

    async def record_user_interaction(self, session: AsyncSession) -> AssistantState:
        """
        Record that user has interacted with the assistant.

        Returns:
            Updated assistant state
        """
        try:
            assistant = await self.get_default_assistant(session)

            assistant.last_user_interaction = func.now()
            # If in idle mode, switch back to active
            if assistant.mode == "idle":
                assistant.mode = "active"
                logger.info("Assistant returned to active mode due to user interaction")

            return await self.update(session, assistant)

        except Exception as e:
            logger.error(f"Error recording user interaction: {e}")
            raise

    async def set_mode(self, session: AsyncSession, mode: str) -> AssistantState:
        """
        Set assistant mode (active/idle).

        Args:
            session: Database session
            mode: New mode ('active' or 'idle')

        Returns:
            Updated assistant state
        """
        try:
            assistant = await self.get_default_assistant(session)

            assistant.mode = mode
            if mode == "active":
                assistant.last_user_interaction = func.now()
            elif mode == "idle":
                assistant.current_action = "thinking"

            return await self.update(session, assistant)

        except Exception as e:
            logger.error(f"Error setting assistant mode to {mode}: {e}")
            raise

    async def update_energy_level(self, session: AsyncSession, energy_delta: float) -> AssistantState:
        """
        Update assistant energy level.

        Args:
            session: Database session
            energy_delta: Change in energy (positive or negative)

        Returns:
            Updated assistant state
        """
        try:
            assistant = await self.get_default_assistant(session)

            assistant.energy_level = max(0.0, min(1.0, assistant.energy_level + energy_delta))
            return await self.update(session, assistant)

        except Exception as e:
            logger.error(f"Error updating energy level by {energy_delta}: {e}")
            raise


class AssistantActionLogRepository(BaseRepository[AssistantActionLog]):
    """Repository for assistant action log operations."""

    def __init__(self):
        super().__init__(AssistantActionLog)

    async def log_action(
        self,
        session: AsyncSession,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None,
        position_before: Optional[Dict[str, Any]] = None,
        position_after: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        triggered_by: str = "user"
    ) -> AssistantActionLog:
        """
        Log an assistant action.

        Args:
            session: Database session
            action_type: Type of action performed
            action_data: Additional action data
            position_before: Position before action
            position_after: Position after action
            success: Whether action was successful
            error_message: Error message if action failed
            triggered_by: Who/what triggered the action

        Returns:
            Created action log entry
        """
        try:
            log_entry = AssistantActionLog(
                action_type=action_type,
                action_data=action_data or {},
                position_before=position_before,
                position_after=position_after,
                success=success,
                error_message=error_message,
                triggered_by=triggered_by
            )

            return await self.create(session, log_entry)

        except Exception as e:
            logger.error(f"Error logging action {action_type}: {e}")
            # Don't raise here as logging shouldn't break the main operation
            return None

    async def get_recent_actions(
        self,
        session: AsyncSession,
        limit: int = 50,
        action_type: Optional[str] = None
    ) -> List[AssistantActionLog]:
        """
        Get recent assistant actions.

        Args:
            session: Database session
            limit: Maximum number of actions to return
            action_type: Filter by specific action type

        Returns:
            List of recent actions
        """
        try:
            stmt = select(AssistantActionLog).order_by(desc(AssistantActionLog.created_at))

            if action_type:
                stmt = stmt.where(AssistantActionLog.action_type == action_type)

            if limit:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            actions = result.scalars().all()

            logger.debug(f"Retrieved {len(actions)} recent actions")
            return list(actions)

        except Exception as e:
            logger.error(f"Error getting recent actions: {e}")
            raise

    async def get_failed_actions(self, session: AsyncSession, limit: int = 20) -> List[AssistantActionLog]:
        """
        Get recent failed actions for debugging.

        Args:
            session: Database session
            limit: Maximum number of failed actions to return

        Returns:
            List of failed actions
        """
        try:
            stmt = (
                select(AssistantActionLog)
                .where(AssistantActionLog.success == False)
                .order_by(desc(AssistantActionLog.created_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            failed_actions = result.scalars().all()

            logger.debug(f"Retrieved {len(failed_actions)} failed actions")
            return list(failed_actions)

        except Exception as e:
            logger.error(f"Error getting failed actions: {e}")
            raise