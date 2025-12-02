"""
Tests for Idle Controller.

Tests cover:
- Idle loop management (start/stop)
- Mode detection and transitions
- Action timing with exponential backoff
- Autonomous action execution
- Callback notifications
- Status reporting
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.idle_controller import IdleController


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def idle_controller():
    """Create a fresh idle controller instance."""
    with patch('app.services.idle_controller.config') as mock_config:
        mock_config.idle.inactivity_timeout_minutes = 10
        mock_config.idle.action_interval_seconds = 60
        mock_config.idle.max_action_interval_seconds = 300
        mock_config.idle.max_consecutive_actions = 5
        mock_config.idle.idle_models = ["phi-3:latest", "gemma:2b"]

        controller = IdleController()
        yield controller


@pytest.fixture
def mock_assistant_state():
    """Create a mock assistant state."""
    state = MagicMock()
    state.mode = "active"
    state.position_x = 5
    state.position_y = 5
    state.energy_level = 1.0
    state.last_user_interaction = datetime.utcnow()
    state.current_action = "idle"
    state.to_dict.return_value = {
        "mode": "active",
        "position": {"x": 5, "y": 5},
        "energy": 1.0
    }
    return state


# ============================================================================
# Initialization Tests
# ============================================================================

class TestIdleControllerInit:
    """Tests for idle controller initialization."""

    def test_initial_state(self, idle_controller):
        """Should have correct initial state."""
        assert idle_controller.is_running is False
        assert idle_controller.idle_task is None
        assert idle_controller.action_count == 0
        assert idle_controller.last_action_time is None

    def test_empty_callbacks_list(self, idle_controller):
        """Should start with empty callbacks list."""
        assert idle_controller.mode_change_callbacks == []


# ============================================================================
# Start/Stop Tests
# ============================================================================

class TestStartStop:
    """Tests for starting and stopping the idle controller."""

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, idle_controller):
        """Starting should set is_running to True."""
        with patch.object(idle_controller, '_idle_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.return_value = None
            with patch('app.services.idle_controller.dream_memory') as mock_dream:
                mock_dream.start_cleanup_task = AsyncMock()

                await idle_controller.start()

                assert idle_controller.is_running is True

                # Cleanup
                idle_controller.is_running = False
                if idle_controller.idle_task:
                    idle_controller.idle_task.cancel()

    @pytest.mark.asyncio
    async def test_start_creates_idle_task(self, idle_controller):
        """Starting should create the idle loop task."""
        with patch.object(idle_controller, '_idle_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.return_value = None
            with patch('app.services.idle_controller.dream_memory') as mock_dream:
                mock_dream.start_cleanup_task = AsyncMock()

                await idle_controller.start()

                assert idle_controller.idle_task is not None

                # Cleanup
                idle_controller.is_running = False
                idle_controller.idle_task.cancel()

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(self, idle_controller):
        """Stopping should clear is_running flag."""
        idle_controller.is_running = True
        idle_controller.idle_task = asyncio.create_task(asyncio.sleep(10))

        with patch('app.services.idle_controller.dream_memory') as mock_dream:
            mock_dream.stop_cleanup_task = AsyncMock()

            await idle_controller.stop()

            assert idle_controller.is_running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, idle_controller):
        """Stopping should cancel the idle task."""
        idle_controller.is_running = True
        idle_controller.idle_task = asyncio.create_task(asyncio.sleep(10))

        with patch('app.services.idle_controller.dream_memory') as mock_dream:
            mock_dream.stop_cleanup_task = AsyncMock()

            await idle_controller.stop()

            assert idle_controller.idle_task.cancelled() or idle_controller.idle_task.done()


# ============================================================================
# Callback Tests
# ============================================================================

class TestCallbacks:
    """Tests for mode change callbacks."""

    def test_add_callback(self, idle_controller):
        """Should add callback to list."""
        callback = MagicMock()
        idle_controller.add_mode_change_callback(callback)

        assert callback in idle_controller.mode_change_callbacks

    def test_remove_callback(self, idle_controller):
        """Should remove callback from list."""
        callback = MagicMock()
        idle_controller.mode_change_callbacks.append(callback)

        idle_controller.remove_mode_change_callback(callback)

        assert callback not in idle_controller.mode_change_callbacks

    def test_remove_nonexistent_callback(self, idle_controller):
        """Should handle removing nonexistent callback."""
        callback = MagicMock()

        # Should not raise
        idle_controller.remove_mode_change_callback(callback)

    @pytest.mark.asyncio
    async def test_notify_mode_change(self, idle_controller):
        """Should notify all callbacks of mode change."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        idle_controller.mode_change_callbacks = [callback1, callback2]

        await idle_controller._notify_mode_change("idle")

        callback1.assert_called_once_with("idle")
        callback2.assert_called_once_with("idle")

    @pytest.mark.asyncio
    async def test_notify_handles_callback_error(self, idle_controller):
        """Should handle errors in callbacks gracefully."""
        callback1 = MagicMock(side_effect=Exception("Callback error"))
        callback2 = MagicMock()
        idle_controller.mode_change_callbacks = [callback1, callback2]

        # Should not raise
        await idle_controller._notify_mode_change("idle")

        # Second callback should still be called
        callback2.assert_called_once()


# ============================================================================
# Mode Transition Tests
# ============================================================================

class TestModeTransitions:
    """Tests for mode transitions."""

    @pytest.mark.asyncio
    async def test_force_idle_mode(self, idle_controller, mock_assistant_state):
        """Should force assistant into idle mode."""
        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)
            mock_service.update_assistant_state = AsyncMock()

            await idle_controller.force_idle_mode()

            assert mock_assistant_state.mode == "idle"
            mock_service.update_assistant_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_idle_resets_timing(self, idle_controller, mock_assistant_state):
        """Forcing idle should reset action timing."""
        idle_controller.action_count = 5
        idle_controller.last_action_time = datetime.utcnow()
        idle_controller.current_interval = 200

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)
            mock_service.update_assistant_state = AsyncMock()

            await idle_controller.force_idle_mode()

            assert idle_controller.action_count == 0
            assert idle_controller.last_action_time is None

    @pytest.mark.asyncio
    async def test_force_active_mode(self, idle_controller, mock_assistant_state):
        """Should force assistant into active mode."""
        mock_assistant_state.mode = "idle"

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)
            mock_service.update_assistant_state = AsyncMock()

            await idle_controller.force_active_mode()

            assert mock_assistant_state.mode == "active"
            mock_service.update_assistant_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_active_updates_interaction_time(self, idle_controller, mock_assistant_state):
        """Forcing active should update last interaction time."""
        mock_assistant_state.mode = "idle"
        mock_assistant_state.last_user_interaction = datetime.utcnow() - timedelta(hours=1)

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)
            mock_service.update_assistant_state = AsyncMock()

            await idle_controller.force_active_mode()

            # Interaction time should be updated to now
            assert mock_assistant_state.last_user_interaction is not None


# ============================================================================
# Mode Detection Tests
# ============================================================================

class TestModeDetection:
    """Tests for idle mode detection."""

    def test_should_enter_idle_after_timeout(self, idle_controller, mock_assistant_state):
        """Should return True when timeout exceeded."""
        mock_assistant_state.last_user_interaction = datetime.utcnow() - timedelta(minutes=15)

        result = idle_controller._should_enter_idle_mode(
            mock_assistant_state, datetime.utcnow()
        )

        assert result is True

    def test_should_not_enter_idle_before_timeout(self, idle_controller, mock_assistant_state):
        """Should return False when timeout not exceeded."""
        mock_assistant_state.last_user_interaction = datetime.utcnow() - timedelta(minutes=5)

        result = idle_controller._should_enter_idle_mode(
            mock_assistant_state, datetime.utcnow()
        )

        assert result is False

    def test_should_not_enter_idle_no_interaction(self, idle_controller, mock_assistant_state):
        """Should return False when no previous interaction."""
        mock_assistant_state.last_user_interaction = None

        result = idle_controller._should_enter_idle_mode(
            mock_assistant_state, datetime.utcnow()
        )

        assert result is False


# ============================================================================
# Action Timing Tests
# ============================================================================

class TestActionTiming:
    """Tests for action timing logic."""

    def test_should_perform_action_first_time(self, idle_controller):
        """Should perform action when no previous action."""
        idle_controller.last_action_time = None

        result = idle_controller._should_perform_action(datetime.utcnow())

        assert result is True

    def test_should_perform_action_after_interval(self, idle_controller):
        """Should perform action after interval passed."""
        idle_controller.last_action_time = datetime.utcnow() - timedelta(seconds=120)
        idle_controller.current_interval = 60

        result = idle_controller._should_perform_action(datetime.utcnow())

        assert result is True

    def test_should_not_perform_action_before_interval(self, idle_controller):
        """Should not perform action before interval passed."""
        idle_controller.last_action_time = datetime.utcnow() - timedelta(seconds=30)
        idle_controller.current_interval = 60

        result = idle_controller._should_perform_action(datetime.utcnow())

        assert result is False

    @pytest.mark.asyncio
    async def test_update_action_timing(self, idle_controller):
        """Should update timing after action."""
        idle_controller.action_count = 0
        idle_controller.last_action_time = None

        with patch('app.services.idle_controller.config') as mock_config:
            mock_config.idle.action_interval_seconds = 60
            mock_config.idle.max_action_interval_seconds = 300
            mock_config.idle.max_consecutive_actions = 5

            await idle_controller._update_action_timing()

            assert idle_controller.last_action_time is not None
            assert idle_controller.action_count == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_after_max_actions(self, idle_controller):
        """Should increase interval after max consecutive actions."""
        idle_controller.action_count = 4  # Will become 5, triggering backoff
        idle_controller.current_interval = 60

        with patch('app.services.idle_controller.config') as mock_config:
            mock_config.idle.action_interval_seconds = 60
            mock_config.idle.max_action_interval_seconds = 300
            mock_config.idle.max_consecutive_actions = 5

            await idle_controller._update_action_timing()

            # Interval should increase
            assert idle_controller.current_interval > 60
            # Action count should reset
            assert idle_controller.action_count == 0


# ============================================================================
# Status Tests
# ============================================================================

class TestStatus:
    """Tests for status reporting."""

    @pytest.mark.asyncio
    async def test_get_status_structure(self, idle_controller, mock_assistant_state):
        """Should return status with expected structure."""
        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            status = await idle_controller.get_status()

            assert "is_running" in status
            assert "current_mode" in status
            assert "action_count" in status
            assert "current_interval" in status
            assert "last_action_time" in status
            assert "time_until_next_action" in status

    @pytest.mark.asyncio
    async def test_get_status_running_state(self, idle_controller, mock_assistant_state):
        """Should report running state correctly."""
        idle_controller.is_running = True
        idle_controller.action_count = 3

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            status = await idle_controller.get_status()

            assert status["is_running"] is True
            assert status["action_count"] == 3

    @pytest.mark.asyncio
    async def test_get_status_calculates_time_until_next(self, idle_controller, mock_assistant_state):
        """Should calculate time until next action."""
        idle_controller.last_action_time = datetime.utcnow() - timedelta(seconds=30)
        idle_controller.current_interval = 60

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.get_assistant_state = AsyncMock(return_value=mock_assistant_state)

            status = await idle_controller.get_status()

            # Should be approximately 30 seconds remaining
            assert status["time_until_next_action"] is not None
            assert 25 <= status["time_until_next_action"] <= 35


# ============================================================================
# Idle Action Tests
# ============================================================================

class TestIdleActions:
    """Tests for autonomous action execution."""

    @pytest.mark.asyncio
    async def test_execute_move_action(self, idle_controller, mock_assistant_state):
        """Should execute move action."""
        action = {"type": "move", "target": {"x": 10, "y": 8}}

        with patch('app.services.idle_controller.action_executor') as mock_executor:
            mock_executor.execute_move_action = AsyncMock(return_value={"success": True})

            result = await idle_controller._execute_idle_action(
                action, mock_assistant_state, {}
            )

            assert result is True
            mock_executor.execute_move_action.assert_called_once_with(10, 8)

    @pytest.mark.asyncio
    async def test_execute_interact_action(self, idle_controller, mock_assistant_state):
        """Should execute interact action."""
        action = {"type": "interact", "target": "lamp"}

        with patch('app.services.idle_controller.action_executor') as mock_executor:
            mock_executor.execute_interact_action = AsyncMock(return_value={"success": True})

            result = await idle_controller._execute_idle_action(
                action, mock_assistant_state, {}
            )

            assert result is True
            mock_executor.execute_interact_action.assert_called_once_with("lamp")

    @pytest.mark.asyncio
    async def test_execute_rest_action(self, idle_controller, mock_assistant_state):
        """Should execute rest action and restore energy."""
        mock_assistant_state.energy_level = 0.5
        action = {"type": "rest"}

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.update_assistant_state = AsyncMock()

            result = await idle_controller._execute_idle_action(
                action, mock_assistant_state, {}
            )

            assert result is True
            assert mock_assistant_state.energy_level == 0.6

    @pytest.mark.asyncio
    async def test_execute_state_change_action(self, idle_controller, mock_assistant_state):
        """Should execute mood change action."""
        action = {"type": "state_change", "parameters": {"mood": "happy"}}

        with patch('app.services.idle_controller.assistant_service') as mock_service:
            mock_service.update_assistant_state = AsyncMock()

            result = await idle_controller._execute_idle_action(
                action, mock_assistant_state, {}
            )

            assert result is True
            assert mock_assistant_state.mood == "happy"

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, idle_controller, mock_assistant_state):
        """Should return False for unknown action type."""
        action = {"type": "unknown_action"}

        result = await idle_controller._execute_idle_action(
            action, mock_assistant_state, {}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_action_handles_error(self, idle_controller, mock_assistant_state):
        """Should handle errors gracefully."""
        action = {"type": "move", "target": {"x": 10, "y": 8}}

        with patch('app.services.idle_controller.action_executor') as mock_executor:
            mock_executor.execute_move_action = AsyncMock(
                side_effect=Exception("Execution error")
            )

            result = await idle_controller._execute_idle_action(
                action, mock_assistant_state, {}
            )

            assert result is False
