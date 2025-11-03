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
from datetime import datetime

from app.config import config
from app.services.llm_manager import llm_manager, ChatMessage
from app.services.assistant_service import assistant_service
from app.services.brain_council import brain_council
from app.services.room_service import room_service
from app.services.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections."""
        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)

        # Remove failed connections
        for connection in disconnected:
            self.disconnect(connection)


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
        except Exception as e:
            logger.warning(f"Could not get assistant state: {e}")
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
        logger.error(f"Unexpected WebSocket error: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
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
            await connection_manager.send_personal_message({
                "type": "chat_stream",
                "data": {
                    "content": word + " ",
                    "full_content": current_response.strip()
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

    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Send error to client
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to process chat: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Stop typing indicator on error
        await connection_manager.send_personal_message({
            "type": "assistant_typing",
            "data": {"typing": False},
            "timestamp": datetime.now().isoformat()
        }, websocket)


async def execute_council_actions(actions: List[Dict[str, Any]], websocket: WebSocket):
    """Execute actions decided by the Brain Council."""
    for action in actions:
        try:
            action_type = action.get("type")
            target = action.get("target")
            parameters = action.get("parameters", {})

            if action_type == "move":
                # Move assistant to target coordinates
                if isinstance(target, str) and "," in target:
                    # Parse coordinates - handle both "x,y" and "(x, y)" formats
                    target_clean = target.strip("()").strip()  # Remove parentheses if present
                    coords = target_clean.split(",")
                    x, y = int(coords[0].strip()), int(coords[1].strip())
                elif isinstance(target, dict):
                    x, y = target.get("x"), target.get("y")
                else:
                    continue

                logger.info(f"Executing move action to coordinates ({x}, {y})")
                result = await assistant_service.move_assistant_to(x, y)
                if result.get("success"):
                    logger.info(f"Movement successful - broadcasting assistant state update")
                    # Broadcast assistant state update
                    assistant_state = await assistant_service.get_assistant_state()
                    await connection_manager.broadcast({
                        "type": "assistant_state",
                        "data": assistant_state.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    logger.warning(f"Movement failed: {result.get('error', 'Unknown error')}")

            elif action_type == "interact":
                # Interact with an object
                object_id = target
                interaction_type = parameters.get("interaction", "activate")

                if interaction_type == "activate":
                    # Toggle object state
                    objects = await room_service.get_all_objects()
                    target_obj = next((obj for obj in objects if obj["id"] == object_id), None)

                    if target_obj:
                        # Toggle common states
                        current_states = await room_service.get_object_states(object_id)

                        if "power" in current_states:
                            new_state = "off" if current_states["power"] == "on" else "on"
                            await room_service.set_object_state(object_id, "power", new_state, "assistant")
                        elif "open" in current_states:
                            new_state = "closed" if current_states["open"] == "open" else "open"
                            await room_service.set_object_state(object_id, "open", new_state, "assistant")

            elif action_type == "state_change":
                # Change object or room state
                object_id = target
                state_key = parameters.get("state_key")
                state_value = parameters.get("state_value")

                if object_id and state_key and state_value:
                    await room_service.set_object_state(object_id, state_key, state_value, "assistant")

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            import traceback
            logger.error(f"Action execution traceback: {traceback.format_exc()}")


async def update_assistant_mood(new_mood: str):
    """Update the assistant's mood."""
    try:
        # This would be implemented in assistant_service if needed
        logger.info(f"Assistant mood updated to: {new_mood}")
    except Exception as e:
        logger.error(f"Error updating assistant mood: {e}")


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

    except Exception as e:
        logger.error(f"Error handling assistant move: {e}")
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

    except Exception as e:
        logger.error(f"Error getting state: {e}")
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

    except Exception as e:
        logger.error(f"Error changing model: {e}")
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

    except Exception as e:
        logger.error(f"Error clearing chat: {e}")
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to clear chat: {str(e)}"},
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
    except Exception as e:
        logger.error(f"Error broadcasting assistant update: {e}")


# Export for use in other modules
__all__ = ["connection_manager", "broadcast_assistant_update"]