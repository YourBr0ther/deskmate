"""Conversation domain model - pure Python, no Pygame dependency."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class MessageRole(Enum):
    """Role of a message sender."""

    USER = auto()
    ASSISTANT = auto()
    SYSTEM = auto()


@dataclass
class Message:
    """A single message in the conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_ollama_format(self) -> dict[str, str]:
        """Convert to Ollama API message format."""
        role_map = {
            MessageRole.USER: "user",
            MessageRole.ASSISTANT: "assistant",
            MessageRole.SYSTEM: "system",
        }
        return {"role": role_map[self.role], "content": self.content}


@dataclass
class Conversation:
    """Manages conversation history."""

    messages: list[Message] = field(default_factory=list)
    max_history: int = 50

    def add_message(self, role: MessageRole, content: str) -> Message:
        """Add a new message to the conversation."""
        message = Message(role=role, content=content)
        self.messages.append(message)

        # Trim old messages if we exceed max history
        # Keep system messages and trim oldest non-system messages
        if len(self.messages) > self.max_history:
            # Separate system and non-system messages
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]

            # Keep last N non-system messages
            keep_count = self.max_history - len(system_msgs)
            other_msgs = other_msgs[-keep_count:] if keep_count > 0 else []

            self.messages = system_msgs + other_msgs

        return message

    def add_user_message(self, content: str) -> Message:
        """Add a user message."""
        return self.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str) -> Message:
        """Add an assistant message."""
        return self.add_message(MessageRole.ASSISTANT, content)

    def add_system_message(self, content: str) -> Message:
        """Add a system message."""
        return self.add_message(MessageRole.SYSTEM, content)

    def get_last_message(self) -> Message | None:
        """Get the most recent message."""
        return self.messages[-1] if self.messages else None

    def get_messages_for_context(self, include_system: bool = True) -> list[Message]:
        """Get messages suitable for sending to the AI."""
        if include_system:
            return self.messages.copy()
        return [m for m in self.messages if m.role != MessageRole.SYSTEM]

    def to_ollama_messages(self) -> list[dict[str, str]]:
        """Convert conversation to Ollama API format."""
        return [msg.to_ollama_format() for msg in self.messages]

    def clear(self) -> None:
        """Clear all messages except system messages."""
        self.messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]

    def clear_all(self) -> None:
        """Clear all messages including system messages."""
        self.messages = []
