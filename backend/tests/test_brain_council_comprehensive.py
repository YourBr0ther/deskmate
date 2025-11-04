"""
Comprehensive tests for the Brain Council system.
Tests the multi-perspective AI reasoning and action generation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
from datetime import datetime

from app.services.brain_council import BrainCouncil
from app.services.assistant_service import assistant_service
from app.services.room_service import room_service
from app.services.llm_manager import llm_manager, ChatMessage
from app.services.conversation_memory import conversation_memory


@pytest.fixture
def brain_council():
    """Create a BrainCouncil instance for testing."""
    return BrainCouncil()


@pytest.fixture
def mock_assistant_state():
    """Mock assistant state."""
    return {
        "position": {"x": 32, "y": 8},
        "facing": "right",
        "current_action": "idle",
        "mood": "neutral",
        "expression": "neutral.png",
        "mode": "active",
        "energy": 0.8,
        "holding_object_id": None,
        "sitting_on_object_id": None,
        "status": "idle"
    }


@pytest.fixture
def mock_room_state():
    """Mock room state with objects."""
    return {
        "objects": [
            {
                "id": "lamp_001",
                "name": "Desk Lamp",
                "position": {"x": 15, "y": 5},
                "size": {"width": 1, "height": 1},
                "type": "item",
                "description": "A bright desk lamp that can be turned on and off",
                "state": "off",
                "movable": True,
                "interactive": True,
            },
            {
                "id": "bed",
                "name": "Bed",
                "position": {"x": 5, "y": 10},
                "size": {"width": 4, "height": 2},
                "type": "furniture",
                "description": "A comfortable bed for sleeping",
                "state": "made",
                "movable": False,
                "interactive": True,
            },
        ],
        "grid_size": {"width": 64, "height": 16}
    }


@pytest.fixture
def mock_persona_context():
    """Mock persona context."""
    return {
        "name": "Alice",
        "personality": "Friendly and helpful AI assistant",
        "description": "A cheerful companion who loves to help with tasks",
        "expressions": {
            "happy": "happy.png",
            "neutral": "neutral.png",
            "confused": "confused.png"
        }
    }


@pytest.fixture
def mock_memory_context():
    """Mock memory context."""
    return [
        {
            "content": "User asked about the lamp earlier",
            "timestamp": datetime.now().isoformat(),
            "relevance": 0.8
        },
        {
            "content": "Assistant moved to the desk recently",
            "timestamp": datetime.now().isoformat(),
            "relevance": 0.6
        }
    ]


class TestBrainCouncilBasic:
    """Test basic Brain Council functionality."""

    @pytest.mark.asyncio
    async def test_council_initialization(self, brain_council):
        """Test that Brain Council initializes correctly."""
        assert brain_council is not None
        assert hasattr(brain_council, 'process_user_message')
        assert hasattr(brain_council, 'analyze_context')

    @pytest.mark.asyncio
    async def test_process_simple_message(self, brain_council, mock_assistant_state,
                                        mock_room_state, mock_persona_context):
        """Test processing a simple user message."""

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=create_mock_council_response()):

            result = await brain_council.process_user_message(
                "Hello, how are you?",
                persona_context=mock_persona_context
            )

            assert "response" in result
            assert "actions" in result
            assert "mood" in result
            assert isinstance(result["actions"], list)

    @pytest.mark.asyncio
    async def test_process_movement_request(self, brain_council, mock_assistant_state,
                                          mock_room_state, mock_persona_context):
        """Test processing a movement request."""

        mock_response = create_mock_council_response(
            actions=[{
                "type": "move",
                "target": {"x": 20, "y": 10},
                "parameters": {"reason": "Moving to requested position"}
            }],
            mood="neutral"
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "Move to position 20, 10",
                persona_context=mock_persona_context
            )

            assert len(result["actions"]) > 0
            movement_action = next((a for a in result["actions"] if a["type"] == "move"), None)
            assert movement_action is not None
            assert movement_action["target"]["x"] == 20
            assert movement_action["target"]["y"] == 10

    @pytest.mark.asyncio
    async def test_process_object_interaction(self, brain_council, mock_assistant_state,
                                            mock_room_state, mock_persona_context):
        """Test processing object interaction requests."""

        mock_response = create_mock_council_response(
            actions=[{
                "type": "interact",
                "target": "lamp_001",
                "parameters": {"action": "turn_on", "reason": "User requested lamp activation"}
            }],
            mood="helpful"
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "Turn on the lamp",
                persona_context=mock_persona_context
            )

            assert len(result["actions"]) > 0
            interaction_action = next((a for a in result["actions"] if a["type"] == "interact"), None)
            assert interaction_action is not None
            assert interaction_action["target"] == "lamp_001"
            assert interaction_action["parameters"]["action"] == "turn_on"


class TestBrainCouncilMemoryIntegration:
    """Test Brain Council integration with memory system."""

    @pytest.mark.asyncio
    async def test_memory_retrieval_in_reasoning(self, brain_council, mock_assistant_state,
                                                mock_room_state, mock_persona_context,
                                                mock_memory_context):
        """Test that Brain Council retrieves and uses memory context."""

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=mock_memory_context) as mock_memory, \
             patch.object(llm_manager, 'chat_completion', return_value=create_mock_council_response()) as mock_llm:

            await brain_council.process_user_message(
                "What did we talk about earlier?",
                persona_context=mock_persona_context
            )

            # Verify memory was searched
            mock_memory.assert_called_once()

            # Verify LLM was called with memory context
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0]
            messages = call_args[0]

            # Check that memory context was included in the prompt
            prompt_content = json.dumps(messages)
            assert "lamp earlier" in prompt_content

    @pytest.mark.asyncio
    async def test_memory_context_affects_actions(self, brain_council, mock_assistant_state,
                                                 mock_room_state, mock_persona_context):
        """Test that memory context influences action decisions."""

        # Memory suggesting user prefers certain lamp state
        memory_context = [
            {
                "content": "User always turns on the lamp when working",
                "timestamp": datetime.now().isoformat(),
                "relevance": 0.9
            }
        ]

        mock_response = create_mock_council_response(
            actions=[{
                "type": "interact",
                "target": "lamp_001",
                "parameters": {"action": "turn_on", "reason": "Based on user's past preference"}
            }],
            mood="thoughtful"
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=memory_context), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "I'm going to start working",
                persona_context=mock_persona_context
            )

            # Should suggest turning on lamp based on memory
            lamp_action = next((a for a in result["actions"]
                              if a["type"] == "interact" and a["target"] == "lamp_001"), None)
            assert lamp_action is not None


class TestBrainCouncilSpatialReasoning:
    """Test Brain Council spatial reasoning capabilities."""

    @pytest.mark.asyncio
    async def test_spatial_awareness_in_actions(self, brain_council, mock_assistant_state,
                                               mock_room_state, mock_persona_context):
        """Test that spatial reasoning affects action planning."""

        # Assistant is far from lamp, should suggest movement first
        distant_assistant = {**mock_assistant_state, "position": {"x": 50, "y": 1}}

        mock_response = create_mock_council_response(
            actions=[
                {
                    "type": "move",
                    "target": {"x": 16, "y": 5},
                    "parameters": {"reason": "Moving closer to lamp before interaction"}
                },
                {
                    "type": "interact",
                    "target": "lamp_001",
                    "parameters": {"action": "turn_on", "reason": "Activating lamp as requested"}
                }
            ],
            mood="focused"
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=distant_assistant), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "Turn on the lamp",
                persona_context=mock_persona_context
            )

            actions = result["actions"]
            assert len(actions) >= 2

            # First action should be movement
            assert actions[0]["type"] == "move"

            # Second action should be interaction
            assert actions[1]["type"] == "interact"

    @pytest.mark.asyncio
    async def test_object_visibility_reasoning(self, brain_council, mock_assistant_state,
                                             mock_room_state, mock_persona_context):
        """Test reasoning about object visibility and accessibility."""

        # Add object that might be out of reach
        extended_room_state = {
            **mock_room_state,
            "objects": mock_room_state["objects"] + [
                {
                    "id": "high_shelf",
                    "name": "High Shelf",
                    "position": {"x": 60, "y": 2},
                    "size": {"width": 2, "height": 1},
                    "type": "furniture",
                    "description": "A high shelf, difficult to reach",
                    "state": "empty",
                    "movable": False,
                    "interactive": True,
                }
            ]
        }

        mock_response = create_mock_council_response(
            actions=[],
            mood="confused",
            response="I can see the high shelf, but it's too far and high for me to reach safely."
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=extended_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "Get something from the high shelf",
                persona_context=mock_persona_context
            )

            # Should recognize limitations and not propose impossible actions
            assert result["mood"] == "confused"
            assert len(result["actions"]) == 0
            assert "too far" in result["response"] or "can't reach" in result["response"]


class TestBrainCouncilValidation:
    """Test Brain Council action validation."""

    @pytest.mark.asyncio
    async def test_action_validation_prevents_impossible_moves(self, brain_council,
                                                             mock_assistant_state,
                                                             mock_room_state,
                                                             mock_persona_context):
        """Test that validator prevents impossible movements."""

        # Mock response that tries to move outside grid bounds
        mock_response = create_mock_council_response(
            actions=[{
                "type": "move",
                "target": {"x": 100, "y": 100},  # Outside 64x16 grid
                "parameters": {"reason": "Invalid move outside bounds"}
            }],
            mood="confused"
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "Move way outside the room",
                persona_context=mock_persona_context
            )

            # Validator should have filtered out impossible action
            valid_moves = [a for a in result["actions"]
                          if a["type"] == "move" and
                          0 <= a["target"]["x"] < 64 and
                          0 <= a["target"]["y"] < 16]

            # Should either have no invalid moves or have been corrected
            assert len(valid_moves) == len([a for a in result["actions"] if a["type"] == "move"])

    @pytest.mark.asyncio
    async def test_personality_consistency_validation(self, brain_council,
                                                    mock_assistant_state,
                                                    mock_room_state):
        """Test that personality core maintains character consistency."""

        # Friendly persona should not generate hostile responses
        friendly_persona = {
            "name": "Sunny",
            "personality": "Always cheerful and optimistic, never gets angry",
            "description": "A bright and positive AI companion"
        }

        mock_response = create_mock_council_response(
            mood="happy",
            response="I'd be happy to help you with that! Let me move over there."
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "You're useless!",  # Potentially hostile input
                persona_context=friendly_persona
            )

            # Should maintain positive personality despite hostile input
            assert result["mood"] in ["happy", "neutral", "confused"]
            assert "happy" in result["response"] or "help" in result["response"]


class TestBrainCouncilErrorHandling:
    """Test Brain Council error handling and resilience."""

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self, brain_council, mock_assistant_state,
                                                 mock_room_state, mock_persona_context):
        """Test graceful handling of LLM failures."""

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', side_effect=Exception("LLM connection failed")):

            result = await brain_council.process_user_message(
                "Hello",
                persona_context=mock_persona_context
            )

            # Should return a fallback response
            assert "response" in result
            assert "actions" in result
            assert "error" in result["response"] or "sorry" in result["response"]
            assert result["actions"] == []

    @pytest.mark.asyncio
    async def test_handles_malformed_llm_response(self, brain_council, mock_assistant_state,
                                                 mock_room_state, mock_persona_context):
        """Test handling of malformed LLM responses."""

        # Mock LLM returning invalid JSON
        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value="invalid json response"):

            result = await brain_council.process_user_message(
                "Hello",
                persona_context=mock_persona_context
            )

            # Should handle gracefully and return fallback
            assert isinstance(result, dict)
            assert "response" in result
            assert "actions" in result


class TestBrainCouncilComplexScenarios:
    """Test complex multi-step scenarios."""

    @pytest.mark.asyncio
    async def test_multi_step_task_planning(self, brain_council, mock_assistant_state,
                                          mock_room_state, mock_persona_context):
        """Test planning complex multi-step tasks."""

        mock_response = create_mock_council_response(
            actions=[
                {
                    "type": "move",
                    "target": {"x": 15, "y": 5},
                    "parameters": {"reason": "Moving to lamp"}
                },
                {
                    "type": "interact",
                    "target": "lamp_001",
                    "parameters": {"action": "turn_on", "reason": "Turning on light"}
                },
                {
                    "type": "move",
                    "target": {"x": 7, "y": 11},
                    "parameters": {"reason": "Moving to bed"}
                },
                {
                    "type": "interact",
                    "target": "bed",
                    "parameters": {"action": "sit", "reason": "Sitting down"}
                }
            ],
            mood="focused",
            response="I'll turn on the lamp and then sit on the bed for you."
        )

        with patch.object(assistant_service, 'get_assistant_state', return_value=mock_assistant_state), \
             patch.object(room_service, 'get_room_state', return_value=mock_room_state), \
             patch.object(conversation_memory, 'search_relevant_memories', return_value=[]), \
             patch.object(llm_manager, 'chat_completion', return_value=mock_response):

            result = await brain_council.process_user_message(
                "Turn on the lamp and then sit on the bed",
                persona_context=mock_persona_context
            )

            actions = result["actions"]
            assert len(actions) == 4

            # Check action sequence makes sense
            assert actions[0]["type"] == "move"  # Move to lamp
            assert actions[1]["type"] == "interact"  # Turn on lamp
            assert actions[2]["type"] == "move"  # Move to bed
            assert actions[3]["type"] == "interact"  # Sit on bed


def create_mock_council_response(actions=None, mood="neutral", response="I understand."):
    """Helper to create mock council responses."""
    if actions is None:
        actions = []

    return {
        "personality_core": {
            "mood": mood,
            "emotional_reasoning": "Based on user request",
            "tone": "friendly"
        },
        "memory_keeper": {
            "relevant_memories": [],
            "context": "No specific memories retrieved"
        },
        "spatial_reasoner": {
            "visible_objects": ["lamp_001", "bed"],
            "reachable_objects": ["lamp_001"],
            "current_observations": "Room appears normal"
        },
        "action_planner": {
            "proposals": actions
        },
        "validator": {
            "selected_actions": actions,
            "confidence": 0.8,
            "validation_reasoning": "Actions appear valid",
            "potential_issues": []
        },
        "response_message": response
    }