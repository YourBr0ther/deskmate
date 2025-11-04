"""
Idle Controller - Manages autonomous behavior when user is inactive.

The Idle Controller handles:
- Inactivity detection and automatic mode switching
- Autonomous action generation and execution
- Integration with Brain Council for idle reasoning
- Action timing with exponential backoff
- Energy management for sustainable idle behavior

When the user is inactive for the configured timeout period, the assistant
switches to idle mode and begins performing autonomous actions at a slower
pace using lightweight LLM models.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import random

from app.config import config
from app.services.assistant_service import assistant_service
from app.services.brain_council import brain_council
from app.services.dream_memory import dream_memory
from app.services.llm_manager import llm_manager
from app.services.action_executor import action_executor
from app.services.room_service import room_service

logger = logging.getLogger(__name__)


class IdleController:
    """Manages autonomous behavior and idle mode transitions."""

    def __init__(self):
        self.is_running = False
        self.idle_task: Optional[asyncio.Task] = None
        self.action_count = 0
        self.last_action_time: Optional[datetime] = None
        self.current_interval = config.idle.action_interval_seconds
        self.mode_change_callbacks: List[Callable[[str], None]] = []

    async def start(self):
        """Start the idle controller."""
        if not self.is_running:
            self.is_running = True
            await dream_memory.start_cleanup_task()
            self.idle_task = asyncio.create_task(self._idle_loop())
            logger.info("Idle controller started")

    async def stop(self):
        """Stop the idle controller."""
        self.is_running = False

        if self.idle_task and not self.idle_task.done():
            self.idle_task.cancel()
            try:
                await self.idle_task
            except asyncio.CancelledError:
                pass

        await dream_memory.stop_cleanup_task()
        logger.info("Idle controller stopped")

    def add_mode_change_callback(self, callback: Callable[[str], None]):
        """Add callback to be notified when mode changes."""
        self.mode_change_callbacks.append(callback)

    def remove_mode_change_callback(self, callback: Callable[[str], None]):
        """Remove mode change callback."""
        if callback in self.mode_change_callbacks:
            self.mode_change_callbacks.remove(callback)

    async def _notify_mode_change(self, new_mode: str):
        """Notify all callbacks of mode change."""
        for callback in self.mode_change_callbacks:
            try:
                callback(new_mode)
            except Exception as e:
                logger.error(f"Error in mode change callback: {e}")

    async def force_idle_mode(self):
        """Force the assistant into idle mode immediately."""
        assistant_state = await assistant_service.get_assistant_state()
        if assistant_state and assistant_state.mode != "idle":
            assistant_state.mode = "idle"
            await assistant_service.update_assistant_state(assistant_state)

            # Reset action timing
            self.action_count = 0
            self.current_interval = config.idle.action_interval_seconds
            self.last_action_time = None

            await self._notify_mode_change("idle")
            logger.info("Forced assistant into idle mode")

    async def force_active_mode(self):
        """Force the assistant back to active mode."""
        assistant_state = await assistant_service.get_assistant_state()
        if assistant_state and assistant_state.mode != "active":
            assistant_state.mode = "active"
            assistant_state.last_user_interaction = datetime.utcnow()
            await assistant_service.update_assistant_state(assistant_state)

            # Reset action timing
            self.action_count = 0
            self.current_interval = config.idle.action_interval_seconds

            await self._notify_mode_change("active")
            logger.info("Forced assistant into active mode")

    async def _idle_loop(self):
        """Main loop for idle mode management."""
        while self.is_running:
            try:
                assistant_state = await assistant_service.get_assistant_state()
                if not assistant_state:
                    await asyncio.sleep(10)
                    continue

                current_time = datetime.utcnow()

                # Check if we should switch to idle mode
                if assistant_state.mode == "active":
                    if self._should_enter_idle_mode(assistant_state, current_time):
                        await self._enter_idle_mode(assistant_state)

                # If in idle mode, perform autonomous actions
                elif assistant_state.mode == "idle":
                    if self._should_perform_action(current_time):
                        await self._perform_autonomous_action(assistant_state)

                # Sleep for a short interval before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in idle loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def _should_enter_idle_mode(self, assistant_state, current_time: datetime) -> bool:
        """Check if assistant should enter idle mode."""
        if not assistant_state.last_user_interaction:
            return False

        time_since_interaction = current_time - assistant_state.last_user_interaction
        timeout_threshold = timedelta(minutes=config.idle.inactivity_timeout_minutes)

        return time_since_interaction >= timeout_threshold

    def _should_perform_action(self, current_time: datetime) -> bool:
        """Check if it's time to perform an autonomous action."""
        if self.last_action_time is None:
            return True

        time_since_action = current_time - self.last_action_time
        return time_since_action.total_seconds() >= self.current_interval

    async def _enter_idle_mode(self, assistant_state):
        """Transition assistant to idle mode."""
        assistant_state.mode = "idle"
        assistant_state.current_action = "thinking"
        await assistant_service.update_assistant_state(assistant_state)

        # Reset action timing
        self.action_count = 0
        self.current_interval = config.idle.action_interval_seconds
        self.last_action_time = None

        await self._notify_mode_change("idle")
        logger.info("Assistant entered idle mode")

        # Store a dream about entering idle mode
        await dream_memory.store_dream(
            action_type="mode_change",
            content="Entered idle mode due to user inactivity",
            action_data={"from_mode": "active", "to_mode": "idle"},
            room_state=await room_service.get_room_state(),
            assistant_position={"x": assistant_state.position_x, "y": assistant_state.position_y},
            reasoning="No user interaction for configured timeout period"
        )

    async def _perform_autonomous_action(self, assistant_state):
        """Perform an autonomous action while in idle mode."""
        try:
            # Get current room state and recent dreams for context
            room_state = await room_service.get_room_state()
            recent_dreams = await dream_memory.get_recent_dreams(limit=5, hours_back=2)

            # Use idle-specific Brain Council reasoning
            reasoning_result = await self._get_idle_reasoning(
                assistant_state, room_state, recent_dreams
            )

            if not reasoning_result or not reasoning_result.get("actions"):
                # No action needed, just wait
                await self._update_action_timing()
                return

            # Execute the chosen action
            action = reasoning_result["actions"][0]  # Take first action
            success = await self._execute_idle_action(action, assistant_state, room_state)

            # Store the action as a dream
            await dream_memory.store_dream(
                action_type=action.get("type", "unknown"),
                content=reasoning_result.get("response", f"Performed {action.get('type')} action"),
                action_data=action,
                room_state=room_state,
                assistant_position={"x": assistant_state.position_x, "y": assistant_state.position_y},
                success=success,
                reasoning=reasoning_result.get("reasoning", "Autonomous idle action")
            )

            # Update action timing
            await self._update_action_timing()

            logger.info(f"Performed autonomous action: {action.get('type')} (success: {success})")

        except Exception as e:
            logger.error(f"Error performing autonomous action: {e}")
            await self._update_action_timing()

    async def _get_idle_reasoning(
        self,
        assistant_state,
        room_state: Dict[str, Any],
        recent_dreams: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get reasoning for autonomous action using lightweight model."""
        try:
            # Switch to lightweight model for idle mode
            original_model = llm_manager.current_model
            try:
                # Try to use a lightweight Ollama model
                available_models = await llm_manager.get_available_models()
                idle_model = None

                for model in config.idle.idle_models:
                    if model in available_models:
                        idle_model = model
                        break

                if idle_model:
                    llm_manager.current_model = idle_model
                    llm_manager.current_provider = "ollama"

                # Create simplified context for idle reasoning
                idle_context = {
                    "mode": "idle",
                    "assistant_position": {"x": assistant_state.position_x, "y": assistant_state.position_y},
                    "assistant_energy": assistant_state.energy_level,
                    "room_objects": room_state.get("objects", []),
                    "recent_dreams": [d.get("content", "") for d in recent_dreams[-3:]],
                    "action_count": self.action_count,
                    "goals": ["explore room", "interact with objects", "maintain energy", "be curious"]
                }

                # Use Brain Council with idle-specific prompt
                result = await brain_council.process_idle_reasoning(idle_context)
                return result

            finally:
                # Restore original model
                llm_manager.current_model = original_model

        except Exception as e:
            logger.error(f"Error in idle reasoning: {e}")
            return None

    async def _execute_idle_action(
        self,
        action: Dict[str, Any],
        assistant_state,
        room_state: Dict[str, Any]
    ) -> bool:
        """Execute an autonomous action and return success status."""
        try:
            action_type = action.get("type")

            if action_type == "move":
                target = action.get("target", {})
                if isinstance(target, dict) and "x" in target and "y" in target:
                    result = await action_executor.execute_move_action(
                        target["x"], target["y"]
                    )
                    return result.get("success", False)

            elif action_type == "interact":
                object_id = action.get("target")
                if object_id:
                    result = await action_executor.execute_interact_action(object_id)
                    return result.get("success", False)

            elif action_type == "state_change":
                # Simple mood or expression change
                mood = action.get("parameters", {}).get("mood")
                if mood:
                    assistant_state.mood = mood
                    await assistant_service.update_assistant_state(assistant_state)
                    return True

            elif action_type == "rest":
                # Restore some energy
                assistant_state.energy_level = min(1.0, assistant_state.energy_level + 0.1)
                assistant_state.current_action = "resting"
                await assistant_service.update_assistant_state(assistant_state)
                return True

            return False

        except Exception as e:
            logger.error(f"Error executing idle action: {e}")
            return False

    async def _update_action_timing(self):
        """Update timing for next action with exponential backoff."""
        self.last_action_time = datetime.utcnow()
        self.action_count += 1

        # Implement exponential backoff with jitter
        if self.action_count >= config.idle.max_consecutive_actions:
            # Take a longer break after several actions
            self.current_interval = min(
                config.idle.max_action_interval_seconds,
                self.current_interval * 1.5
            )
            self.action_count = 0
        else:
            # Add some randomness to prevent predictable behavior
            jitter = random.uniform(0.8, 1.2)
            self.current_interval = min(
                config.idle.max_action_interval_seconds,
                int(config.idle.action_interval_seconds * jitter)
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get current idle controller status."""
        assistant_state = await assistant_service.get_assistant_state()

        return {
            "is_running": self.is_running,
            "current_mode": assistant_state.mode if assistant_state else "unknown",
            "action_count": self.action_count,
            "current_interval": self.current_interval,
            "last_action_time": self.last_action_time.isoformat() if self.last_action_time else None,
            "time_until_next_action": None if not self.last_action_time else max(
                0,
                self.current_interval - (datetime.utcnow() - self.last_action_time).total_seconds()
            )
        }


# Global idle controller instance
idle_controller = IdleController()