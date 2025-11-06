"""
Test suite for the refactored Brain Council system.

Tests the new modular architecture with individual reasoners,
coordinator, prompt builder, and response parser.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.brain_council.base import ReasoningContext, ReasoningResult, CouncilDecision
from app.services.brain_council.reasoning.personality_reasoner import PersonalityReasoner
from app.services.brain_council.reasoning.memory_reasoner import MemoryReasoner
from app.services.brain_council.reasoning.spatial_reasoner import SpatialReasoner
from app.services.brain_council.reasoning.action_reasoner import ActionReasoner
from app.services.brain_council.reasoning.validation_reasoner import ValidationReasoner
from app.services.brain_council.council_coordinator import CouncilCoordinator
from app.services.brain_council.prompt_builder import PromptBuilder
from app.services.brain_council.response_parser import ResponseParser
from app.services.brain_council.brain_council import BrainCouncil


class TestReasoningContext:
    """Test the ReasoningContext data structure."""

    def test_context_creation(self):
        """Test creating a reasoning context."""
        context = ReasoningContext(
            user_message="Hello!",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "happy"},
            room_state={"objects": [], "object_states": {}},
            persona_context={"name": "Alice", "personality": "Friendly"}
        )

        assert context.user_message == "Hello!"
        assert context.assistant_state["mood"] == "happy"
        assert context.persona_context["name"] == "Alice"
        assert context.timestamp is not None

    def test_context_defaults(self):
        """Test context creation with defaults."""
        context = ReasoningContext(
            user_message="Test",
            assistant_state={},
            room_state={}
        )

        assert context.user_message == "Test"
        assert context.persona_context is None
        assert context.conversation_context is None
        assert isinstance(context.timestamp, datetime)


class TestPersonalityReasoner:
    """Test the PersonalityReasoner component."""

    @pytest.fixture
    def reasoner(self):
        return PersonalityReasoner()

    @pytest.fixture
    def context_with_persona(self):
        return ReasoningContext(
            user_message="How are you feeling today?",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}},
            persona_context={
                "name": "Alice",
                "personality": "Friendly, energetic, and helpful",
                "creator": "TestUser"
            }
        )

    @pytest.fixture
    def context_without_persona(self):
        return ReasoningContext(
            user_message="Hello there!",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}}
        )

    @pytest.mark.asyncio
    async def test_reasoning_with_persona(self, reasoner, context_with_persona):
        """Test personality reasoning with active persona."""
        result = await reasoner.reason(context_with_persona)

        assert result.is_valid
        assert result.reasoner_name == "personality_core"
        assert "Alice" in result.reasoning
        assert "friendly" in result.reasoning.lower()
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_reasoning_without_persona(self, reasoner, context_without_persona):
        """Test personality reasoning without persona."""
        result = await reasoner.reason(context_without_persona)

        assert result.is_valid
        assert result.reasoner_name == "personality_core"
        assert "default" in result.reasoning.lower()
        assert result.confidence > 0.5

    def test_sentiment_analysis(self, reasoner):
        """Test message sentiment analysis."""
        # Test positive sentiment
        positive_sentiment = reasoner._analyze_message_sentiment("I love this amazing feature!")
        assert positive_sentiment == "excited"

        # Test negative sentiment
        negative_sentiment = reasoner._analyze_message_sentiment("This is terrible and awful")
        assert negative_sentiment == "negative"

        # Test question
        question_sentiment = reasoner._analyze_message_sentiment("What can you do for me?")
        assert question_sentiment == "curious"

        # Test neutral
        neutral_sentiment = reasoner._analyze_message_sentiment("Please move to the center")
        assert neutral_sentiment == "neutral"

    def test_response_style_determination(self, reasoner):
        """Test response style determination."""
        persona_context = {"personality": "Friendly and energetic assistant"}

        # Test with excited user
        style = reasoner._determine_response_style(persona_context, "excited", {"mood": "happy"})
        assert "enthusiasm" in style.lower()

        # Test with negative user
        style = reasoner._determine_response_style(persona_context, "negative", {"mood": "neutral"})
        assert "empathy" in style.lower()


class TestMemoryReasoner:
    """Test the MemoryReasoner component."""

    @pytest.fixture
    def reasoner(self):
        return MemoryReasoner()

    @pytest.fixture
    def context_with_conversation(self):
        mock_messages = [
            Mock(role="user", content="Hello"),
            Mock(role="assistant", content="Hi there!"),
            Mock(role="user", content="How are you?")
        ]

        return ReasoningContext(
            user_message="What's your favorite color?",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}},
            conversation_context=mock_messages
        )

    @pytest.mark.asyncio
    async def test_reasoning_with_conversation_history(self, reasoner, context_with_conversation):
        """Test memory reasoning with conversation history."""
        result = await reasoner.reason(context_with_conversation)

        assert result.is_valid
        assert result.reasoner_name == "memory_keeper"
        assert "conversation" in result.reasoning.lower()
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_reasoning_without_conversation(self, reasoner):
        """Test memory reasoning without conversation history."""
        context = ReasoningContext(
            user_message="Hello",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}}
        )

        result = await reasoner.reason(context)

        assert result.is_valid
        assert result.reasoner_name == "memory_keeper"
        assert "new" in result.reasoning.lower() or "limited" in result.reasoning.lower()
        assert result.confidence < 0.8

    def test_topic_extraction(self, reasoner):
        """Test recent topic extraction."""
        messages = [
            Mock(content="Let's talk about movement and objects"),
            Mock(content="I want to pick up that book"),
            Mock(content="How do you feel about that?")
        ]

        topics = reasoner._extract_recent_topics(messages)
        assert "movement" in topics
        assert "objects" in topics
        assert "feelings" in topics


class TestSpatialReasoner:
    """Test the SpatialReasoner component."""

    @pytest.fixture
    def reasoner(self):
        return SpatialReasoner()

    @pytest.fixture
    def context_with_objects(self):
        objects = [
            {
                "id": "obj1",
                "name": "desk",
                "position": {"x": 120, "y": 180},
                "size": {"width": 60, "height": 40},
                "properties": {"solid": True, "interactive": True}
            },
            {
                "id": "obj2",
                "name": "book",
                "position": {"x": 130, "y": 190},
                "size": {"width": 20, "height": 15},
                "properties": {"solid": True, "movable": True}
            }
        ]

        return ReasoningContext(
            user_message="Look around",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": objects, "object_states": {}},
        )

    @pytest.mark.asyncio
    async def test_spatial_reasoning_with_nearby_objects(self, reasoner, context_with_objects):
        """Test spatial reasoning with nearby objects."""
        result = await reasoner.reason(context_with_objects)

        assert result.is_valid
        assert result.reasoner_name == "spatial_reasoner"
        assert "visible" in result.reasoning.lower()
        assert result.metadata["visible_objects_count"] >= 1
        assert result.confidence > 0.9

    @pytest.mark.asyncio
    async def test_spatial_reasoning_empty_room(self, reasoner):
        """Test spatial reasoning in empty room."""
        context = ReasoningContext(
            user_message="Look around",
            assistant_state={"position": {"x": 500, "y": 300}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}},
        )

        result = await reasoner.reason(context)

        assert result.is_valid
        assert result.reasoner_name == "spatial_reasoner"
        assert "no objects" in result.reasoning.lower() or "clear" in result.reasoning.lower()
        assert result.metadata["visible_objects_count"] == 0


class TestActionReasoner:
    """Test the ActionReasoner component."""

    @pytest.fixture
    def reasoner(self):
        return ActionReasoner()

    @pytest.fixture
    def movement_context(self):
        return ReasoningContext(
            user_message="Please move to the center of the room",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}},
        )

    @pytest.mark.asyncio
    async def test_action_reasoning_movement_intent(self, reasoner, movement_context):
        """Test action reasoning with movement intent."""
        result = await reasoner.reason(movement_context)

        assert result.is_valid
        assert result.reasoner_name == "action_planner"
        assert "movement" in result.reasoning.lower()
        assert result.metadata["detected_intent"]["primary_intent"] == "movement"
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_intent_analysis(self, reasoner):
        """Test user intent analysis."""
        # Test movement intent
        movement_analysis = reasoner._analyze_user_intent("Go to the corner of the room")
        assert movement_analysis["primary_intent"] == "movement"
        assert movement_analysis["primary_confidence"] > 0.5

        # Test interaction intent
        interaction_analysis = reasoner._analyze_user_intent("Turn on the lamp please")
        assert interaction_analysis["primary_intent"] == "object_interaction"
        assert movement_analysis["primary_confidence"] > 0.5

        # Test conversation intent
        conversation_analysis = reasoner._analyze_user_intent("How are you feeling today?")
        assert conversation_analysis["primary_intent"] == "conversation"


class TestValidationReasoner:
    """Test the ValidationReasoner component."""

    @pytest.fixture
    def reasoner(self):
        return ValidationReasoner()

    @pytest.fixture
    def context_with_constraints(self):
        # Assistant near room boundary
        return ReasoningContext(
            user_message="Move around",
            assistant_state={"position": {"x": 20, "y": 30}, "mood": "neutral", "holding_object_id": None},
            room_state={"objects": [], "object_states": {}},
        )

    @pytest.mark.asyncio
    async def test_validation_with_constraints(self, reasoner, context_with_constraints):
        """Test validation reasoning with spatial constraints."""
        result = await reasoner.reason(context_with_constraints)

        assert result.is_valid
        assert result.reasoner_name == "validator"
        assert result.metadata["validation_checks_performed"] > 0
        assert result.confidence > 0.9


class TestPromptBuilder:
    """Test the PromptBuilder component."""

    @pytest.fixture
    def prompt_builder(self):
        return PromptBuilder()

    @pytest.fixture
    def sample_context(self):
        return ReasoningContext(
            user_message="Hello, how are you?",
            assistant_state={"position": {"x": 100, "y": 200}, "mood": "neutral"},
            room_state={"objects": [], "object_states": {}},
            persona_context={"name": "Alice", "personality": "Friendly assistant"}
        )

    def test_council_prompt_building(self, prompt_builder, sample_context):
        """Test building a complete council prompt."""
        prompt = prompt_builder.build_council_prompt(sample_context)

        assert "Brain Council" in prompt
        assert "Hello, how are you?" in prompt
        assert "Alice" in prompt
        assert "COUNCIL PERSPECTIVES" in prompt
        assert "JSON FORMAT" in prompt

    def test_reasoner_prompt_building(self, prompt_builder, sample_context):
        """Test building reasoner-specific prompts."""
        personality_prompt = prompt_builder.build_reasoner_prompt(
            "personality_core", sample_context
        )

        assert "Personality Core" in personality_prompt
        assert "character consistency" in personality_prompt.lower()

        memory_prompt = prompt_builder.build_reasoner_prompt(
            "memory_keeper", sample_context
        )

        assert "Memory Keeper" in memory_prompt
        assert "context" in memory_prompt.lower()


class TestResponseParser:
    """Test the ResponseParser component."""

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_valid_json_parsing(self, parser):
        """Test parsing valid JSON responses."""
        valid_response = '''```json
{
    "council_reasoning": {
        "personality_core": "Friendly response appropriate",
        "memory_keeper": "No previous context",
        "spatial_reasoner": "Clear room environment",
        "action_planner": "Simple greeting response",
        "validator": "All actions are safe"
    },
    "response": "Hello! I'm doing well, thank you for asking.",
    "actions": [
        {"type": "expression", "target": "happy", "parameters": {}}
    ],
    "mood": "happy",
    "reasoning": "Responding positively to friendly greeting"
}
```'''

        decision = parser.parse_council_response(valid_response)

        assert isinstance(decision, CouncilDecision)
        assert decision.response == "Hello! I'm doing well, thank you for asking."
        assert len(decision.actions) == 1
        assert decision.actions[0]["type"] == "expression"
        assert decision.mood == "happy"
        assert decision.confidence > 0.5

    def test_malformed_json_parsing(self, parser):
        """Test parsing malformed JSON responses."""
        malformed_response = '''I want to help you with that. Here's my response:
{
    "response": "I understand what you're asking",
    "actions": [{"type": "expression", "target": "thoughtful"}],
    "mood": "helpful"
    // missing closing brace'''

        decision = parser.parse_council_response(malformed_response)

        assert isinstance(decision, CouncilDecision)
        assert decision.response  # Should have some response
        assert decision.confidence < 0.7  # Lower confidence for malformed

    def test_no_json_parsing(self, parser):
        """Test parsing responses with no JSON."""
        text_response = "I understand what you're asking. Let me help you with that."

        decision = parser.parse_council_response(text_response)

        assert isinstance(decision, CouncilDecision)
        assert decision.response  # Should extract meaningful response
        assert decision.confidence < 0.5  # Low confidence for fallback


class TestCouncilCoordinator:
    """Test the CouncilCoordinator integration."""

    @pytest.fixture
    def coordinator(self):
        return CouncilCoordinator()

    @pytest.mark.asyncio
    async def test_coordinator_initialization(self, coordinator):
        """Test that coordinator initializes all reasoners."""
        from app.services.brain_council.base import ReasonerFactory
        reasoners = ReasonerFactory.get_all_reasoners()

        assert len(reasoners) == 5
        assert "personality_core" in reasoners
        assert "memory_keeper" in reasoners
        assert "spatial_reasoner" in reasoners
        assert "action_planner" in reasoners
        assert "validator" in reasoners

    @pytest.mark.asyncio
    @patch('app.services.brain_council.council_coordinator.conversation_memory')
    async def test_full_processing_flow(self, mock_memory, coordinator):
        """Test complete processing flow through coordinator."""
        # Mock conversation memory
        mock_memory.get_conversation_context.return_value = []

        assistant_state = {"position": {"x": 100, "y": 200}, "mood": "neutral"}
        room_state = {"objects": [], "object_states": {}}
        persona_context = {"name": "Alice", "personality": "Friendly"}

        decision = await coordinator.process_user_message(
            user_message="Hello there!",
            assistant_state=assistant_state,
            room_state=room_state,
            persona_context=persona_context
        )

        assert isinstance(decision, CouncilDecision)
        assert decision.response
        assert isinstance(decision.actions, list)
        assert decision.mood
        assert decision.confidence > 0.0


class TestBrainCouncilIntegration:
    """Test the complete Brain Council integration."""

    @pytest.fixture
    def brain_council(self):
        return BrainCouncil()

    @pytest.mark.asyncio
    @patch('app.services.brain_council.brain_council.assistant_service')
    @patch('app.services.brain_council.brain_council.room_service')
    @patch('app.services.brain_council.brain_council.conversation_memory')
    async def test_full_integration(self, mock_memory, mock_room, mock_assistant, brain_council):
        """Test complete Brain Council integration."""
        # Setup mocks
        mock_assistant_state = Mock()
        mock_assistant_state.position_x = 100
        mock_assistant_state.position_y = 200
        mock_assistant_state.facing_direction = "right"
        mock_assistant_state.current_action = "idle"
        mock_assistant_state.mood = "neutral"
        mock_assistant_state.holding_object_id = None

        mock_assistant.get_assistant_state.return_value = mock_assistant_state
        mock_room.get_all_objects.return_value = []
        mock_memory.get_conversation_context.return_value = []

        # Test processing
        result = await brain_council.process_user_message(
            user_message="Hello! How are you today?",
            persona_context={"name": "Alice", "personality": "Friendly assistant"}
        )

        # Verify result format (backward compatibility)
        assert isinstance(result, dict)
        assert "response" in result
        assert "actions" in result
        assert "mood" in result
        assert "reasoning" in result
        assert isinstance(result["actions"], list)

    def test_backward_compatibility_structure(self, brain_council):
        """Test that the refactored Brain Council maintains API compatibility."""
        # Verify the brain_council instance has expected methods
        assert hasattr(brain_council, 'process_user_message')
        assert hasattr(brain_council, 'process_idle_reasoning')

        # Verify it's the right class
        assert isinstance(brain_council, BrainCouncil)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])