"""
Integration tests for WebSocket communication.
Tests the full WebSocket pipeline including Brain Council integration.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
import asyncio
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import websockets

from app.main import app
from app.api.websocket import websocket_manager
from app.services.brain_council import BrainCouncil
from app.services.assistant_service import assistant_service
from app.services.room_service import room_service


@pytest.fixture
def test_client():
    """Create test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def mock_websocket():
    """Create a mock WebSocket connection."""
    mock_ws = Mock(spec=WebSocket)
    mock_ws.send_text = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.receive_json = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_brain_council_response():
    """Mock Brain Council response for testing."""
    return {
        "response": "I'll move to the lamp and turn it on for you!",
        "actions": [
            {
                "type": "move",
                "target": {"x": 15, "y": 5},
                "parameters": {"reason": "Moving to lamp"}
            },
            {
                "type": "interact",
                "target": "lamp_001",
                "parameters": {"action": "turn_on", "reason": "Activating lamp"}
            }
        ],
        "mood": "helpful",
        "expression": "happy.png"
    }


class TestWebSocketConnection:
    """Test basic WebSocket connection and management."""

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, mock_websocket):
        """Test WebSocket connection and disconnection."""

        # Test connection
        await websocket_manager.connect(mock_websocket)
        assert len(websocket_manager.active_connections) == 1

        # Test disconnection
        websocket_manager.disconnect(mock_websocket)
        assert len(websocket_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_multiple_websocket_connections(self, mock_websocket):
        """Test handling multiple WebSocket connections."""

        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws1.send_json = AsyncMock()

        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        # Connect multiple clients
        await websocket_manager.connect(mock_ws1)
        await websocket_manager.connect(mock_ws2)

        assert len(websocket_manager.active_connections) == 2

        # Test broadcasting to all connections
        message = {"type": "broadcast", "content": "Hello all"}
        await websocket_manager.broadcast(message)

        mock_ws1.send_json.assert_called_with(message)
        mock_ws2.send_json.assert_called_with(message)

        # Disconnect clients
        websocket_manager.disconnect(mock_ws1)
        websocket_manager.disconnect(mock_ws2)
        assert len(websocket_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_connection_error_handling(self, mock_websocket):
        """Test error handling during WebSocket communication."""

        await websocket_manager.connect(mock_websocket)

        # Mock send error
        mock_websocket.send_json.side_effect = Exception("Connection lost")

        # Should handle error gracefully
        message = {"type": "test", "content": "test message"}
        await websocket_manager.send_personal_message(message, mock_websocket)

        # Connection should be removed on error
        assert len(websocket_manager.active_connections) == 0


class TestWebSocketMessageHandling:
    """Test WebSocket message processing."""

    @pytest.mark.asyncio
    async def test_chat_message_processing(self, mock_websocket, mock_brain_council_response):
        """Test processing of chat messages through WebSocket."""

        await websocket_manager.connect(mock_websocket)

        chat_message = {
            "type": "chat",
            "content": "Turn on the lamp",
            "persona_name": "Alice"
        }

        with patch.object(BrainCouncil, 'process_user_message', return_value=mock_brain_council_response):

            await websocket_manager.handle_message(chat_message, mock_websocket)

            # Verify response was sent back
            mock_websocket.send_json.assert_called()
            response_call = mock_websocket.send_json.call_args[0][0]

            assert response_call["type"] == "chat_response"
            assert response_call["content"] == mock_brain_council_response["response"]
            assert response_call["actions"] == mock_brain_council_response["actions"]

    @pytest.mark.asyncio
    async def test_assistant_move_message(self, mock_websocket):
        """Test assistant movement messages."""

        await websocket_manager.connect(mock_websocket)

        move_message = {
            "type": "assistant_move",
            "x": 20,
            "y": 10
        }

        with patch.object(assistant_service, 'move_assistant', return_value=True) as mock_move:

            await websocket_manager.handle_message(move_message, mock_websocket)

            # Verify assistant service was called
            mock_move.assert_called_with(20, 10)

            # Verify confirmation was sent
            mock_websocket.send_json.assert_called()
            response_call = mock_websocket.send_json.call_args[0][0]
            assert response_call["type"] == "assistant_moved"

    @pytest.mark.asyncio
    async def test_status_request_message(self, mock_websocket):
        """Test status request messages."""

        await websocket_manager.connect(mock_websocket)

        status_message = {
            "type": "status_request"
        }

        mock_assistant_state = {
            "position": {"x": 32, "y": 8},
            "mood": "neutral",
            "status": "idle",
            "energy": 0.8
        }

        mock_room_state = {
            "objects": [],
            "grid_size": {"width": 64, "height": 16}
        }

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state):

            await websocket_manager.handle_message(status_message, mock_websocket)

            # Verify status was sent
            mock_websocket.send_json.assert_called()
            response_call = mock_websocket.send_json.call_args[0][0]

            assert response_call["type"] == "status_update"
            assert response_call["assistant"] == mock_assistant_state
            assert response_call["room"] == mock_room_state

    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, mock_websocket):
        """Test handling of invalid messages."""

        await websocket_manager.connect(mock_websocket)

        # Test malformed message
        invalid_messages = [
            {"content": "Missing type field"},
            {"type": "unknown_type", "content": "Unknown message type"},
            None,
            "not a dictionary",
            {}
        ]

        for invalid_message in invalid_messages:
            await websocket_manager.handle_message(invalid_message, mock_websocket)

            # Should send error response
            if mock_websocket.send_json.called:
                response_call = mock_websocket.send_json.call_args[0][0]
                assert response_call["type"] == "error"


class TestWebSocketBrainCouncilIntegration:
    """Test integration between WebSocket and Brain Council."""

    @pytest.mark.asyncio
    async def test_brain_council_full_pipeline(self, mock_websocket):
        """Test complete pipeline from WebSocket to Brain Council and back."""

        await websocket_manager.connect(mock_websocket)

        chat_message = {
            "type": "chat",
            "content": "I want to relax on the bed",
            "persona_name": "Alice"
        }

        mock_assistant_state = {
            "position": {"x": 32, "y": 8},
            "mood": "neutral",
            "status": "idle"
        }

        mock_room_state = {
            "objects": [
                {
                    "id": "bed",
                    "name": "Bed",
                    "position": {"x": 5, "y": 10},
                    "type": "furniture",
                    "interactive": True
                }
            ]
        }

        mock_brain_response = {
            "response": "I'll help you relax! Let me move to the bed.",
            "actions": [
                {
                    "type": "move",
                    "target": {"x": 7, "y": 11},
                    "parameters": {"reason": "Moving to bed"}
                },
                {
                    "type": "interact",
                    "target": "bed",
                    "parameters": {"action": "sit", "reason": "Sitting on bed"}
                }
            ],
            "mood": "caring",
            "expression": "gentle.png"
        }

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(BrainCouncil, 'process_user_message', return_value=mock_brain_response):

            await websocket_manager.handle_message(chat_message, mock_websocket)

            # Verify response contains all Brain Council outputs
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "chat_response"
            assert response["content"] == mock_brain_response["response"]
            assert response["actions"] == mock_brain_response["actions"]
            assert response["mood"] == mock_brain_response["mood"]
            assert response["expression"] == mock_brain_response["expression"]

    @pytest.mark.asyncio
    async def test_brain_council_error_handling(self, mock_websocket):
        """Test WebSocket handling of Brain Council errors."""

        await websocket_manager.connect(mock_websocket)

        chat_message = {
            "type": "chat",
            "content": "Test message",
            "persona_name": "Alice"
        }

        with patch.object(BrainCouncil, 'process_user_message', side_effect=Exception("Brain Council failed")):

            await websocket_manager.handle_message(chat_message, mock_websocket)

            # Should send error response
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "error"
            assert "error" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_typing_indicator_integration(self, mock_websocket):
        """Test typing indicator during Brain Council processing."""

        await websocket_manager.connect(mock_websocket)

        chat_message = {
            "type": "chat",
            "content": "Complex request requiring thinking",
            "persona_name": "Alice"
        }

        # Mock slow Brain Council processing
        async def slow_brain_council(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "response": "I've thought about it carefully...",
                "actions": [],
                "mood": "thoughtful"
            }

        with patch.object(BrainCouncil, 'process_user_message', side_effect=slow_brain_council):

            await websocket_manager.handle_message(chat_message, mock_websocket)

            # Should have sent typing indicator and then response
            assert mock_websocket.send_json.call_count >= 2

            # First call should be typing indicator
            first_call = mock_websocket.send_json.call_args_list[0][0][0]
            assert first_call["type"] == "typing"
            assert first_call["isTyping"] is True

            # Last call should be the response
            last_call = mock_websocket.send_json.call_args_list[-1][0][0]
            assert last_call["type"] == "chat_response"


class TestWebSocketActionExecution:
    """Test action execution through WebSocket integration."""

    @pytest.mark.asyncio
    async def test_action_execution_broadcast(self, mock_websocket):
        """Test that action execution results are broadcast to all clients."""

        # Connect multiple clients
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.send_json = AsyncMock()

        await websocket_manager.connect(mock_ws1)
        await websocket_manager.connect(mock_ws2)

        # One client sends a message that triggers actions
        chat_message = {
            "type": "chat",
            "content": "Turn on the lamp",
            "persona_name": "Alice"
        }

        mock_brain_response = {
            "response": "Turning on the lamp!",
            "actions": [
                {
                    "type": "interact",
                    "target": "lamp_001",
                    "parameters": {"action": "turn_on"}
                }
            ],
            "mood": "helpful"
        }

        with patch.object(BrainCouncil, 'process_user_message', return_value=mock_brain_response):

            await websocket_manager.handle_message(chat_message, mock_ws1)

            # Both clients should receive updates
            assert mock_ws1.send_json.call_count > 0
            assert mock_ws2.send_json.call_count > 0

            # Both should receive action execution updates
            ws2_calls = [call[0][0] for call in mock_ws2.send_json.call_args_list]
            action_updates = [call for call in ws2_calls if call.get("type") == "action_executed"]
            assert len(action_updates) > 0

    @pytest.mark.asyncio
    async def test_assistant_state_updates(self, mock_websocket):
        """Test that assistant state changes are broadcast."""

        await websocket_manager.connect(mock_websocket)

        # Simulate assistant state change
        new_state = {
            "position": {"x": 15, "y": 5},
            "mood": "happy",
            "expression": "smile.png",
            "current_action": "interacting"
        }

        await websocket_manager.broadcast_assistant_update(new_state)

        # Should broadcast to all connected clients
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]

        assert response["type"] == "assistant_update"
        assert response["state"] == new_state

    @pytest.mark.asyncio
    async def test_room_state_updates(self, mock_websocket):
        """Test that room state changes are broadcast."""

        await websocket_manager.connect(mock_websocket)

        # Simulate room state change
        room_update = {
            "object_id": "lamp_001",
            "property": "state",
            "value": "on",
            "timestamp": "2023-01-01T12:00:00Z"
        }

        await websocket_manager.broadcast_room_update(room_update)

        # Should broadcast to all connected clients
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]

        assert response["type"] == "room_update"
        assert response["update"] == room_update


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""

    @pytest.mark.asyncio
    async def test_message_processing_performance(self, mock_websocket):
        """Test that messages are processed within reasonable time limits."""

        import time

        await websocket_manager.connect(mock_websocket)

        simple_message = {
            "type": "status_request"
        }

        mock_assistant_state = {"position": {"x": 32, "y": 8}, "mood": "neutral"}
        mock_room_state = {"objects": [], "grid_size": {"width": 64, "height": 16}}

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state):

            start_time = time.time()
            await websocket_manager.handle_message(simple_message, mock_websocket)
            processing_time = time.time() - start_time

            assert processing_time < 0.5  # Should process quickly

    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, mock_websocket):
        """Test handling multiple concurrent WebSocket messages."""

        await websocket_manager.connect(mock_websocket)

        messages = [
            {"type": "status_request"},
            {"type": "assistant_move", "x": 10, "y": 5},
            {"type": "status_request"},
        ]

        with patch.object(assistant_service, 'get_assistant_state', return_value={"position": {"x": 32, "y": 8}}), \
             patch.object(room_service, 'get_room_state', return_value={"objects": []}), \
             patch.object(assistant_service, 'move_assistant', return_value=True):

            # Process messages concurrently
            tasks = [websocket_manager.handle_message(msg, mock_websocket) for msg in messages]
            await asyncio.gather(*tasks)

            # All messages should be processed
            assert mock_websocket.send_json.call_count >= len(messages)

    @pytest.mark.asyncio
    async def test_large_broadcast_performance(self):
        """Test broadcasting to many connected clients."""

        import time

        # Connect many mock clients
        clients = []
        for i in range(50):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            clients.append(mock_ws)
            await websocket_manager.connect(mock_ws)

        large_message = {
            "type": "broadcast_test",
            "data": "x" * 1000  # 1KB message
        }

        start_time = time.time()
        await websocket_manager.broadcast(large_message)
        broadcast_time = time.time() - start_time

        # Should broadcast to all clients quickly
        assert broadcast_time < 1.0

        # Verify all clients received the message
        for client in clients:
            client.send_json.assert_called_with(large_message)

        # Cleanup
        for client in clients:
            websocket_manager.disconnect(client)


class TestWebSocketRealWorld:
    """Test real-world WebSocket usage scenarios."""

    @pytest.mark.asyncio
    async def test_user_session_simulation(self, mock_websocket):
        """Simulate a complete user session through WebSocket."""

        await websocket_manager.connect(mock_websocket)

        # User sends initial greeting
        greeting = {
            "type": "chat",
            "content": "Hello, how are you?",
            "persona_name": "Alice"
        }

        mock_brain_response = {
            "response": "Hello! I'm doing well, thank you for asking!",
            "actions": [],
            "mood": "happy",
            "expression": "smile.png"
        }

        with patch.object(BrainCouncil, 'process_user_message', return_value=mock_brain_response):
            await websocket_manager.handle_message(greeting, mock_websocket)

        # User requests status
        status_request = {"type": "status_request"}

        mock_assistant_state = {
            "position": {"x": 32, "y": 8},
            "mood": "happy",
            "status": "idle",
            "energy": 0.8
        }

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value={"objects": []}):
            await websocket_manager.handle_message(status_request, mock_websocket)

        # User requests assistant movement
        move_request = {
            "type": "assistant_move",
            "x": 20,
            "y": 10
        }

        with patch.object(assistant_service, 'move_assistant', return_value=True):
            await websocket_manager.handle_message(move_request, mock_websocket)

        # Verify all interactions were handled
        assert mock_websocket.send_json.call_count >= 3

    @pytest.mark.asyncio
    async def test_connection_resilience(self, mock_websocket):
        """Test WebSocket connection resilience and recovery."""

        await websocket_manager.connect(mock_websocket)

        # Simulate connection error during message send
        mock_websocket.send_json.side_effect = [
            None,  # First call succeeds
            Exception("Connection lost"),  # Second call fails
        ]

        # Send two messages
        message1 = {"type": "status_request"}
        message2 = {"type": "status_request"}

        with patch.object(assistant_service, 'get_assistant_state', return_value={"position": {"x": 32, "y": 8}}), \
             patch.object(room_service, 'get_room_state', return_value={"objects": []}):

            await websocket_manager.handle_message(message1, mock_websocket)
            await websocket_manager.handle_message(message2, mock_websocket)

        # Connection should be removed after error
        assert len(websocket_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_memory_integration(self, mock_websocket):
        """Test WebSocket integration with conversation memory."""

        await websocket_manager.connect(mock_websocket)

        chat_message = {
            "type": "chat",
            "content": "Remember that I like bright lighting",
            "persona_name": "Alice"
        }

        mock_brain_response = {
            "response": "I'll remember that you prefer bright lighting!",
            "actions": [],
            "mood": "attentive"
        }

        with patch.object(BrainCouncil, 'process_user_message', return_value=mock_brain_response) as mock_brain, \
             patch('app.services.conversation_memory.conversation_memory.store_memory_from_text') as mock_store:

            await websocket_manager.handle_message(chat_message, mock_websocket)

            # Verify Brain Council was called
            mock_brain.assert_called_once()

            # Verify message was sent back
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]
            assert response["type"] == "chat_response"