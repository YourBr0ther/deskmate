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

from app.services.llm_manager import llm_manager, ChatMessage
from app.services.assistant_service import assistant_service

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
                "provider": llm_manager.current_provider.value
            },
            "timestamp": datetime.now().isoformat()
        }, websocket)

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
            else:
                await connection_manager.send_personal_message({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {message_type}"},
                    "timestamp": datetime.now().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def handle_chat_message(websocket: WebSocket, data: Dict[str, Any]):
    """Handle incoming chat message."""
    try:
        user_message = data.get("message", "").strip()
        if not user_message:
            await connection_manager.send_personal_message({
                "type": "error",
                "data": {"message": "Empty message"},
                "timestamp": datetime.now().isoformat()
            }, websocket)
            return

        # Get conversation context (could be enhanced with memory later)
        system_prompt = """You are a virtual AI companion living in a room environment.
You can move around, interact with objects, and have conversations.
Be friendly, helpful, and engaging. Keep responses concise but warm."""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_message)
        ]

        # Don't echo user message - frontend already added it

        # Send "typing" indicator
        await connection_manager.send_personal_message({
            "type": "assistant_typing",
            "data": {"typing": True},
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Generate streaming response
        full_response = ""
        async for chunk in llm_manager.chat_completion_stream(
            messages=messages,
            temperature=0.7
        ):
            if chunk:
                full_response += chunk
                await connection_manager.send_personal_message({
                    "type": "chat_stream",
                    "data": {
                        "content": chunk,
                        "full_content": full_response
                    },
                    "timestamp": datetime.now().isoformat()
                }, websocket)

        # Stop typing indicator (frontend will mark last message as complete)
        await connection_manager.send_personal_message({
            "type": "assistant_typing",
            "data": {"typing": False},
            "timestamp": datetime.now().isoformat()
        }, websocket)

    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        await connection_manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Failed to process chat: {str(e)}"},
            "timestamp": datetime.now().isoformat()
        }, websocket)


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