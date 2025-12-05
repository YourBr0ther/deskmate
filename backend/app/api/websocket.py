"""
WebSocket endpoints for real-time chat and assistant updates.

Provides:
- Real-time chat with streaming LLM responses
- Assistant state updates
- Room state synchronization
- Connection management with reconnection support
"""

from typing import Dict, Any, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
import asyncio
import time
from datetime import datetime

from app.config import config
from app.services.llm_manager import llm_manager, ChatMessage
from app.services.assistant_service import assistant_service
from app.services.brain_council import brain_council
from app.services.room_service import room_service
from app.services.conversation_memory import conversation_memory
from app.services.action_executor import action_executor
from app.services.idle_controller import idle_controller
from app.exceptions import (
    ConnectionError, BusinessLogicError, ActionExecutionError,
    ResourceError, ServiceError, create_error_from_exception, ErrorSeverity,
    DatabaseError, AIServiceError, BrainCouncilError
)
from app.services.dream_memory import dream_memory

logger = logging.getLogger(__name__)

router = APIRouter()


async def handle_websocket_error(
    e: Exception,
    websocket: WebSocket,
    context: str,
    error_message: str = "An error occurred"
) -> None:
    """Helper function to handle WebSocket errors consistently."""
    if isinstance(e, (ResourceError, ServiceError, BusinessLogicError, ConnectionError)):
        e.log_error({"context": context})
        user_message = e.user_message
    else:
        # Convert unknown exceptions to proper DeskMate errors
        error = create_error_from_exception(e, {"context": context})
        error.log_error()
        user_message = error_message

    try:
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": user_message},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as send_error:
        logger.error(f"Failed to send error message to WebSocket: {send_error}")


class ConnectionManager:
    """Manages WebSocket connections with improved error resilience."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_health: Dict[WebSocket, Dict[str, Any]] = {}
        self.max_failures_per_connection = 3
        self.failure_reset_time = 300  # 5 minutes

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection and cleanup health tracking."""
        self.active_connections.discard(websocket)
        self.connection_health.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    def _is_connection_unhealthy(self, websocket: WebSocket) -> bool:
        """Check if a connection has too many recent failures."""
        if websocket not in self.connection_health:
            return False

        health = self.connection_health[websocket]

        # Reset failure count if enough time has passed
        if time.time() - health.get("last_failure", 0) > self.failure_reset_time:
            health["failures"] = 0
            return False

        return health.get("failures", 0) >= self.max_failures_per_connection

    def get_health_stats(self) -> Dict[str, Any]:
        """Get connection health statistics."""
        total_connections = len(self.active_connections)
        unhealthy_connections = sum(1 for ws in self.active_connections if self._is_connection_unhealthy(ws))

        return {
            "total_connections": total_connections,
            "healthy_connections": total_connections - unhealthy_connections,
            "unhealthy_connections": unhealthy_connections,
            "failure_reset_time": self.failure_reset_time,
            "max_failures_per_connection": self.max_failures_per_connection
        }

    async def send_personal_message(self, message: dict, websocket: WebSocket, max_retries: int = 2):
        """Send message to specific connection with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                await websocket.send_text(json.dumps(message))
                # Reset failure count on successful send
                if websocket in self.connection_health:
                    self.connection_health[websocket]["failures"] = 0
                return
            except Exception as e:
                # Track connection failures
                if websocket not in self.connection_health:
                    self.connection_health[websocket] = {"failures": 0, "last_failure": time.time()}

                self.connection_health[websocket]["failures"] += 1
                self.connection_health[websocket]["last_failure"] = time.time()

                if attempt < max_retries:
                    logger.warning(f"WebSocket send failed (attempt {attempt + 1}/{max_retries + 1}), retrying: {e}")
                    await asyncio.sleep(0.1)  # Brief delay before retry
                    continue
                else:
                    # Only disconnect after max retries and if too many failures
                    failure_count = self.connection_health[websocket]["failures"]
                    if failure_count >= self.max_failures_per_connection:
                        logger.error(f"WebSocket connection has {failure_count} failures, disconnecting")
                        self.disconnect(websocket)
                    else:
                        # Log error but don't disconnect yet
                        error = ConnectionError(
                            f"Failed to send personal message after {max_retries + 1} attempts: {str(e)}",
                            connection_type="websocket",
                            details={"message_type": message.get("type"), "attempt": attempt + 1}
                        )
                        error.log_error()
                    break

    async def broadcast(self, message: dict, exclude_failed: bool = True):
        """Broadcast message to all connections with improved error handling."""
        failed_connections = set()
        successful_sends = 0

        for connection in self.active_connections.copy():
            # Skip connections with too many recent failures if exclude_failed is True
            if exclude_failed and self._is_connection_unhealthy(connection):
                continue

            try:
                await connection.send_text(json.dumps(message))
                successful_sends += 1

                # Reset failure count on successful broadcast
                if connection in self.connection_health:
                    self.connection_health[connection]["failures"] = 0

            except Exception as e:
                # Track failure but don't immediately disconnect
                if connection not in self.connection_health:
                    self.connection_health[connection] = {"failures": 0, "last_failure": time.time()}

                self.connection_health[connection]["failures"] += 1
                self.connection_health[connection]["last_failure"] = time.time()

                failure_count = self.connection_health[connection]["failures"]
                if failure_count >= self.max_failures_per_connection:
                    failed_connections.add(connection)
                    logger.warning(f"Connection marked for removal due to {failure_count} failures")
                else:
                    logger.debug(f"Broadcast failed for connection (failure {failure_count}): {e}")

        # Remove only consistently failed connections
        for connection in failed_connections:
            self.disconnect(connection)

        logger.debug(f"Broadcast completed: {successful_sends}/{len(self.active_connections)} successful sends")


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time communication.

    Message Types:
    - chat_message: User sends chat message
    - assistant_move: Move assistant request
    - get_state: Request current state
    - ping: Connection keep-alive
    """
    await connection_manager.connect(websocket)

    try:
        # Initialize conversation memory for this session
        conversation_id = await conversation_memory.initialize_conversation()
        logger.info(f"Initialized conversation memory: {conversation_id}")

        # Send initial state (handle DB connection issues gracefully)
        try:
            assistant_state = await assistant_service.get_assistant_state()
            await connection_manager.send_personal_message({
                "type": "assistant_state",
                "data": assistant_state.to_dict(),
                "timestamp": datetime.now().isoformat()
            }, websocket)
        except ResourceError as e:
            e.log_error({"context": "websocket_initial_state"})
            # Send a default state
            await connection_manager.send_personal_message({
                "type": "assistant_state",
                "data": {
                    "position": {"x": 32, "y": 8},
                    "status": {"action": "idle", "mood": "neutral"},
                    "id": "assistant"
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)
        except Exception as e:
            # Convert unknown exceptions to proper DeskMate errors
            error = create_error_from_exception(e, {"context": "websocket_initial_state"})
            error.log_error()
            # Send a default state
            await connection_manager.send_personal_message({
                "type": "assistant_state",
                "data": {
                    "position": {"x": 32, "y": 8},
                    "status": {"action": "idle", "mood": "neutral"},
                    "id": "assistant"
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)

        await connection_manager.send_personal_message({
            "type": "connection_established",
            "data": {
                "message": "Connected to DeskMate",
                "current_model": llm_manager.current_model,
                "provider": llm_manager.current_provider.value,
                "conversation_id": conversation_id
            },
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Note: Chat history will be loaded when persona is selected via API
        # Don't send history on initial WebSocket connection since no persona is selected yet

        # Set up idle mode change notifications
        def mode_change_callback(new_mode: str):
            asyncio.create_task(connection_manager.broadcast({
                "type": "mode_change",
                "data": {
                    "new_mode": new_mode,
                    "message": f"Assistant entered {new_mode} mode"
                },
                "timestamp": datetime.now().isoformat()
            }))

        idle_controller.add_mode_change_callback(mode_change_callback)

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            message_data = message.get("data", {})

            logger.info(f"Received WebSocket message: {message_type}")

            if message_type == "chat_message":
                await handle_chat_message(websocket, message_data)
            elif message_type == "assistant_move":
                await handle_assistant_move(websocket, message_data)
            elif message_type == "get_state":
                await handle_get_state(websocket)
            elif message_type == "ping":
                await handle_ping(websocket)
            elif message_type == "model_change":
                await handle_model_change(websocket, message_data)
            elif message_type == "clear_chat":
                await handle_clear_chat(websocket, message_data)
            elif message_type == "request_chat_history":
                await handle_request_chat_history(websocket, message_data)
            elif message_type == "idle_command":
                await handle_idle_command(websocket, message_data)
            else:
                await connection_manager.send_personal_message({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {message_type}"},
                    "timestamp": datetime.now().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
        connection_manager.disconnect(websocket)
    except Exception as e:
        # Convert unknown exceptions to proper DeskMate errors
        error = create_error_from_exception(e, {
            "context": "websocket_connection_handler",
            "connection_id": id(websocket)
        })
        error.severity = ErrorSeverity.HIGH
        error.log_error()
        connection_manager.disconnect(websocket)


async def handle_chat_message(websocket: WebSocket, data: Dict[str, Any]):
    """Handle incoming chat message with Brain Council integration."""
    try:
        # Input validation
        if not isinstance(data, dict):
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Invalid message format"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        user_message = data.get("message", "")
        if not isinstance(user_message, str):
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Message must be a string"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        user_message = user_message.strip()
        if not user_message:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Empty message"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        # Limit message length for safety
        if len(user_message) > config.security.max_message_length:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Message too long (max {config.security.max_message_length:,} characters)"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        # Send "thinking" indicator
        await connection_manager.send_personal_message({
            "type": "assistant_typing",
            "data": {"typing": True},
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Get persona context (if available)
        persona_context = data.get("persona_context")
        persona_name = persona_context.get("name") if persona_context else None

        # Record user interaction to reset idle timer
        await assistant_service.record_user_interaction()

        # Handle special commands
        if user_message.lower().strip() == "/idle":
            # Switch to idle mode immediately
            await idle_controller.force_idle_mode()

            await connection_manager.send_personal_message({
                "type": "mode_change",
                "data": {
                    "new_mode": "idle",
                    "message": "Assistant has entered idle mode"
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)

            # Send assistant typing indicator off
            await connection_manager.send_personal_message({
                "type": "assistant_typing",
                "data": {"typing": False},
                "timestamp": datetime.now().isoformat()
            }, websocket)

            # Broadcast state update
            await broadcast_assistant_update()
            return

        # Store user message in conversation memory
        await conversation_memory.add_user_message(user_message, persona_name)

        # Process through Brain Council
        logger.info(f"WebSocket: About to call brain_council.process_user_message with message: {user_message[:50]}...")
        try:
            council_decision = await brain_council.process_user_message(
                user_message=user_message,
                persona_context=persona_context
            )
            logger.info("WebSocket: Brain Council completed successfully")
        except Exception as brain_error:
            logger.error(f"WebSocket: Brain Council failed with error: {brain_error}")
            logger.error(f"WebSocket: Error type: {type(brain_error)}")
            import traceback
            logger.error(f"WebSocket: Full traceback: {traceback.format_exc()}")
            raise brain_error

        # Stream the response
        response_text = council_decision.get("response", "I'm not sure how to respond to that.")

        # Simulate streaming for better UX
        words = response_text.split()
        current_response = ""

        for i, word in enumerate(words):
            current_response += word + " "
            is_last_word = i == len(words) - 1
            await connection_manager.send_personal_message({
                "type": "chat_stream",
                "data": {
                    "content": word + " ",
                    "full_content": current_response.strip(),
                    "done": is_last_word  # Signals stream completion to frontend
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)
            # Small delay for natural typing feel
            await asyncio.sleep(0.05)

        # Store assistant response in conversation memory
        actions = council_decision.get("actions", [])
        await conversation_memory.add_assistant_message(
            response_text,
            persona_name,
            actions if actions else None
        )

        # Execute any actions the council decided on
        await execute_council_actions(actions, websocket)

        # Update assistant mood if changed
        new_mood = council_decision.get("mood")
        if new_mood:
            await update_assistant_mood(new_mood)

        # Stop typing indicator
        await connection_manager.send_personal_message({
            "type": "assistant_typing",
            "data": {"typing": False},
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Send reasoning info for debugging (optional)
        if council_decision.get("reasoning"):
            logger.info(f"Council reasoning: {council_decision['reasoning']}")

    except BrainCouncilError as e:
        logger.error(f"Brain Council error handling chat message: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "I'm having trouble processing that request right now."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except AIServiceError as e:
        logger.error(f"AI service error handling chat message: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "I'm experiencing technical difficulties with my AI systems."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {
            "context": "handle_chat_message",
            "message_content": data.get("message", "")[:100] if isinstance(data, dict) else str(data)[:100]
        })
        logger.error(f"Unexpected error handling chat message: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                    exc_info=True)

        # Send error to client
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Failed to process chat message."},
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Stop typing indicator on error
        await connection_manager.send_personal_message({
            "type": "assistant_typing",
            "data": {"typing": False},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def execute_council_actions(actions: List[Dict[str, Any]], websocket: WebSocket):
    """Execute actions decided by the Brain Council using the action executor."""
    if not actions:
        return

    try:
        # Create a broadcast callback function for the action executor
        async def broadcast_callback(message: Dict[str, Any]):
            await connection_manager.broadcast(message)

        # Execute actions through the action executor
        logger.info(f"Executing {len(actions)} Brain Council actions")
        results = await action_executor.execute_actions(actions, broadcast_callback)

        # Log execution results
        logger.info(f"Action execution complete: {results['executed']} succeeded, {results['failed']} failed")

        # Send execution summary to the specific websocket
        if results["failed"] > 0:
            failed_actions = [r for r in results["action_results"] if not r.get("success", False)]
            for failed in failed_actions:
                logger.warning(f"Action failed: {failed}")

    except ActionExecutionError as e:
        logger.error(f"Action execution error: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "execute_council_actions"})
        logger.error(f"Unexpected error executing council actions: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details},
                    exc_info=True)


async def update_assistant_mood(new_mood: str):
    """Update the assistant's mood."""
    try:
        # This would be implemented in assistant_service if needed
        logger.info(f"Assistant mood updated to: {new_mood}")
    except DatabaseError as e:
        logger.error(f"Database error updating assistant mood: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "update_assistant_mood"})
        logger.error(f"Unexpected error updating assistant mood: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})


async def handle_assistant_move(websocket: WebSocket, data: Dict[str, Any]):
    """Handle assistant movement request."""
    try:
        target_x = data.get("x")
        target_y = data.get("y")

        if target_x is None or target_y is None:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Target position required"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        # Move assistant
        result = await assistant_service.move_assistant_to(target_x, target_y)

        if result["success"]:
            # Broadcast updated assistant state
            assistant_state = await assistant_service.get_assistant_state()
            await connection_manager.broadcast({
                "type": "assistant_state",
                "data": assistant_state.to_dict(),
                "timestamp": datetime.now().isoformat()
            })
        else:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": result.get("error", "Movement failed")},
                "timestamp": datetime.now().isoformat()
            }, websocket)

    except ActionExecutionError as e:
        logger.error(f"Action execution error handling assistant move: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Movement failed. Unable to reach that location."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "handle_assistant_move"})
        logger.error(f"Unexpected error handling assistant move: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to move assistant: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def handle_get_state(websocket: WebSocket):
    """Send current assistant and room state."""
    try:
        assistant_state = await assistant_service.get_assistant_state()

        await connection_manager.send_personal_message({
            "type": "state_update",
            "data": {
                "assistant": assistant_state.to_dict(),
                "model": llm_manager.current_model,
                "provider": llm_manager.current_provider.value
            },
            "timestamp": datetime.now().isoformat()
        }, websocket)

    except DatabaseError as e:
        logger.error(f"Database error getting state: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Unable to retrieve current state."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "handle_get_state"})
        logger.error(f"Unexpected error getting state: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to get state: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def handle_ping(websocket: WebSocket):
    """Handle ping message for connection keep-alive."""
    await connection_manager.send_personal_message({
        "type": "pong",
        "data": {"timestamp": datetime.now().isoformat()},
        "timestamp": datetime.now().isoformat()
    }, websocket)


async def handle_model_change(websocket: WebSocket, data: Dict[str, Any]):
    """Handle model selection change."""
    try:
        model_id = data.get("model_id")
        if not model_id:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Model ID required"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        success = await llm_manager.set_model(model_id)
        if success:
            # Send confirmation to requesting client only (no broadcast to avoid loops)
            await connection_manager.send_personal_message({
                "type": "model_changed",
                "data": {
                    "model": llm_manager.current_model,
                    "provider": llm_manager.current_provider.value
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)
        else:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Failed to change to model: {model_id}"},
                "timestamp": datetime.now().isoformat()
            }, websocket)

    except AIServiceError as e:
        logger.error(f"AI service error changing model: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Failed to change AI model."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "handle_model_change"})
        logger.error(f"Unexpected error changing model: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to change model: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def handle_clear_chat(websocket: WebSocket, data: Dict[str, Any]):
    """Handle chat clearing request."""
    try:
        clear_type = data.get("clear_type", "current")  # "current", "all", "persona"
        persona_name = data.get("persona_name")

        success = False
        message = ""

        if clear_type == "current":
            # Clear only current conversation
            success = await conversation_memory.clear_current_conversation()
            message = "Current chat cleared"
        elif clear_type == "all":
            # Clear all conversation memory including vector database
            success = await conversation_memory.clear_all_memory()
            message = "All conversation memory cleared (including database)"
        elif clear_type == "persona" and persona_name:
            # Clear memory for specific persona
            success = await conversation_memory.clear_persona_memory(persona_name)
            message = f"Cleared memory for persona: {persona_name}"
        else:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Invalid clear_type or missing persona_name"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        if success:
            await connection_manager.send_personal_message({
                "type": "chat_cleared",
                "data": {
                    "message": message,
                    "clear_type": clear_type,
                    "persona_name": persona_name
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)
        else:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Failed to clear chat: {clear_type}"},
                "timestamp": datetime.now().isoformat()
            }, websocket)

    except DatabaseError as e:
        logger.error(f"Database error clearing chat: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Failed to clear chat history."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "handle_clear_chat"})
        logger.error(f"Unexpected error clearing chat: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to clear chat: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def handle_idle_command(websocket: WebSocket, data: Dict[str, Any]):
    """Handle idle mode commands."""
    try:
        command = data.get("command", "")

        if command == "force_idle":
            # Force assistant into idle mode
            await idle_controller.force_idle_mode()

            await connection_manager.send_personal_message({
                "type": "mode_change",
                "data": {
                    "new_mode": "idle",
                    "message": "Assistant forced into idle mode"
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)

        elif command == "force_active":
            # Force assistant back to active mode
            await idle_controller.force_active_mode()

            await connection_manager.send_personal_message({
                "type": "mode_change",
                "data": {
                    "new_mode": "active",
                    "message": "Assistant returned to active mode"
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)

        elif command == "get_status":
            # Get idle controller status
            status = await idle_controller.get_status()

            await connection_manager.send_personal_message({
                "type": "idle_status",
                "data": status,
                "timestamp": datetime.now().isoformat()
            }, websocket)

        elif command == "get_dreams":
            # Get recent dreams
            limit = data.get("limit", 10)
            hours_back = data.get("hours_back", 24)
            recent_dreams = await dream_memory.get_recent_dreams(limit, hours_back)

            await connection_manager.send_personal_message({
                "type": "dreams",
                "data": {
                    "dreams": recent_dreams,
                    "limit": limit,
                    "hours_back": hours_back
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)

        else:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Unknown idle command: {command}"},
                "timestamp": datetime.now().isoformat()
            }, websocket)

        # Broadcast state update after command
        await broadcast_assistant_update()

    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "handle_idle_command"})
        logger.error(f"Unexpected error handling idle command: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to execute idle command: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def handle_request_chat_history(websocket: WebSocket, data: Dict[str, Any]):
    """Handle chat history request for a specific persona."""
    try:
        persona_name = data.get("persona_name")

        if not persona_name:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Persona name is required"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        # Initialize conversation memory for this persona
        conversation_id = await conversation_memory.initialize_conversation(
            persona_name=persona_name,
            load_history=True
        )

        # Get chat history
        messages = await conversation_memory.get_chat_history_for_frontend(limit=50)

        # Convert to frontend format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": f"msg_{msg['id']}",
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "model": msg.get("model")
            })

        # Send chat history
        await connection_manager.send_personal_message({
            "type": "chat_history_loaded",
            "data": {
                "messages": formatted_messages,
                "count": len(formatted_messages),
                "persona_name": persona_name,
                "conversation_id": conversation_id
            },
            "timestamp": datetime.now().isoformat()
        }, websocket)

        logger.info(f"Loaded {len(formatted_messages)} messages for persona: {persona_name}")

    except DatabaseError as e:
        logger.error(f"Database error loading chat history: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Failed to load chat history."},
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "handle_request_chat_history"})
        logger.error(f"Unexpected error loading chat history: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to load chat history: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


# Utility function to broadcast assistant updates
async def broadcast_assistant_update():
    """Broadcast assistant state update to all connections."""
    try:
        assistant_state = await assistant_service.get_assistant_state()
        await connection_manager.broadcast({
            "type": "assistant_state",
            "data": assistant_state.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
    except DatabaseError as e:
        logger.error(f"Database error broadcasting assistant update: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details})
    except Exception as e:
        # Wrap unknown exceptions for better error tracking
        wrapped_exception = wrap_exception(e, {"context": "broadcast_assistant_update"})
        logger.error(f"Unexpected error broadcasting assistant update: {wrapped_exception.message}",
                    extra={"error_code": wrapped_exception.error_code, "details": wrapped_exception.details})


# Export for use in other modules
__all__ = ["connection_manager", "broadcast_assistant_update"]