"""Tests for the Conversation domain model."""

import pytest

from deskmate.domain.conversation import Conversation, Message, MessageRole


class TestMessage:
    """Tests for Message class."""

    def test_message_creation(self) -> None:
        """Test message is created with role and content."""
        msg = Message(role=MessageRole.USER, content="Hello")

        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_to_ollama_format_user(self) -> None:
        """Test converting user message to Ollama format."""
        msg = Message(role=MessageRole.USER, content="Hi")
        result = msg.to_ollama_format()

        assert result == {"role": "user", "content": "Hi"}

    def test_to_ollama_format_assistant(self) -> None:
        """Test converting assistant message to Ollama format."""
        msg = Message(role=MessageRole.ASSISTANT, content="Hello!")
        result = msg.to_ollama_format()

        assert result == {"role": "assistant", "content": "Hello!"}

    def test_to_ollama_format_system(self) -> None:
        """Test converting system message to Ollama format."""
        msg = Message(role=MessageRole.SYSTEM, content="You are helpful.")
        result = msg.to_ollama_format()

        assert result == {"role": "system", "content": "You are helpful."}


class TestConversation:
    """Tests for Conversation class."""

    def test_conversation_starts_empty(self, conversation: Conversation) -> None:
        """Test conversation starts with no messages."""
        assert len(conversation.messages) == 0

    def test_add_user_message(self, conversation: Conversation) -> None:
        """Test adding a user message."""
        conversation.add_user_message("Hello")

        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[0].content == "Hello"

    def test_add_assistant_message(self, conversation: Conversation) -> None:
        """Test adding an assistant message."""
        conversation.add_assistant_message("Hi there!")

        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == MessageRole.ASSISTANT

    def test_add_system_message(self, conversation: Conversation) -> None:
        """Test adding a system message."""
        conversation.add_system_message("Be helpful.")

        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == MessageRole.SYSTEM

    def test_get_last_message(self, conversation: Conversation) -> None:
        """Test getting the last message."""
        conversation.add_user_message("First")
        conversation.add_assistant_message("Second")

        last = conversation.get_last_message()
        assert last is not None
        assert last.content == "Second"

    def test_get_last_message_empty(self, conversation: Conversation) -> None:
        """Test getting last message from empty conversation."""
        last = conversation.get_last_message()
        assert last is None

    def test_to_ollama_messages(self, conversation: Conversation) -> None:
        """Test converting to Ollama message format."""
        conversation.add_system_message("Be helpful.")
        conversation.add_user_message("Hello")
        conversation.add_assistant_message("Hi!")

        messages = conversation.to_ollama_messages()

        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

    def test_clear_keeps_system_messages(self, conversation: Conversation) -> None:
        """Test that clear() keeps system messages."""
        conversation.add_system_message("Be helpful.")
        conversation.add_user_message("Hello")
        conversation.add_assistant_message("Hi!")

        conversation.clear()

        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == MessageRole.SYSTEM

    def test_clear_all_removes_everything(self, conversation: Conversation) -> None:
        """Test that clear_all() removes all messages."""
        conversation.add_system_message("Be helpful.")
        conversation.add_user_message("Hello")

        conversation.clear_all()

        assert len(conversation.messages) == 0


class TestConversationHistoryLimit:
    """Tests for conversation history limiting."""

    def test_trims_old_messages(self) -> None:
        """Test that old messages are trimmed when exceeding max."""
        conv = Conversation(max_history=5)

        for i in range(10):
            conv.add_user_message(f"Message {i}")

        assert len(conv.messages) == 5
        # Should have the most recent messages
        assert conv.messages[-1].content == "Message 9"

    def test_preserves_system_messages_when_trimming(self) -> None:
        """Test that system messages are preserved when trimming."""
        conv = Conversation(max_history=5)
        conv.add_system_message("System prompt")

        for i in range(10):
            conv.add_user_message(f"Message {i}")

        # System message should still be there
        system_msgs = [m for m in conv.messages if m.role == MessageRole.SYSTEM]
        assert len(system_msgs) == 1
        assert system_msgs[0].content == "System prompt"
