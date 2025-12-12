"""Input handler for translating Pygame events to game actions."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from deskmate.game.game_state import GameState


class ActionType(Enum):
    """Types of game actions."""

    MOVE_TO = auto()
    CLICK_OBJECT = auto()
    SEND_CHAT = auto()
    TOGGLE_CHAT = auto()
    UPDATE_CHAT_INPUT = auto()
    DROP_OBJECT = auto()


@dataclass
class GameAction:
    """Represents a game action to be processed."""

    action_type: ActionType
    x: float = 0.0
    y: float = 0.0
    text: str = ""

    @classmethod
    def move_to(cls, x: float, y: float) -> "GameAction":
        """Create a move-to action."""
        return cls(action_type=ActionType.MOVE_TO, x=x, y=y)

    @classmethod
    def click_object(cls, x: float, y: float) -> "GameAction":
        """Create a click-object action."""
        return cls(action_type=ActionType.CLICK_OBJECT, x=x, y=y)

    @classmethod
    def send_chat(cls, text: str) -> "GameAction":
        """Create a send-chat action."""
        return cls(action_type=ActionType.SEND_CHAT, text=text)

    @classmethod
    def toggle_chat(cls) -> "GameAction":
        """Create a toggle-chat action."""
        return cls(action_type=ActionType.TOGGLE_CHAT)

    @classmethod
    def update_chat_input(cls, text: str) -> "GameAction":
        """Create an update-chat-input action."""
        return cls(action_type=ActionType.UPDATE_CHAT_INPUT, text=text)

    @classmethod
    def drop_object(cls) -> "GameAction":
        """Create a drop-object action."""
        return cls(action_type=ActionType.DROP_OBJECT)


class InputHandler:
    """Handles input events and converts them to game actions."""

    def __init__(self) -> None:
        """Initialize the input handler."""
        self.chat_panel_rect: pygame.Rect | None = None

    def set_chat_panel_rect(self, rect: pygame.Rect) -> None:
        """Set the chat panel rectangle for input handling."""
        self.chat_panel_rect = rect

    def process(
        self, events: list[pygame.event.Event], game_state: "GameState"
    ) -> list[GameAction]:
        """Process Pygame events and return game actions."""
        actions: list[GameAction] = []

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    action = self._handle_left_click(event.pos, game_state)
                    if action:
                        actions.append(action)
                elif event.button == 3:  # Right click
                    # Right click to drop held object
                    if game_state.companion.held_object:
                        actions.append(GameAction.drop_object())

            elif event.type == pygame.KEYDOWN:
                action = self._handle_keydown(event, game_state)
                if action:
                    actions.append(action)

        return actions

    def _handle_left_click(
        self, pos: tuple[int, int], game_state: "GameState"
    ) -> GameAction | None:
        """Handle left mouse click."""
        x, y = pos

        # Check if clicking in chat panel area
        if self.chat_panel_rect and self.chat_panel_rect.collidepoint(x, y):
            # Activate chat input if clicking in chat area
            if not game_state.chat_input_active:
                return GameAction.toggle_chat()
            return None

        # If chat is active, clicking outside deactivates it
        if game_state.chat_input_active:
            return GameAction.toggle_chat()

        # Check if clicking on an object
        obj = game_state.room.get_object_at(x, y)
        if obj and not obj.is_held:
            return GameAction.click_object(float(x), float(y))

        # Otherwise, move to clicked position
        return GameAction.move_to(float(x), float(y))

    def _handle_keydown(
        self, event: pygame.event.Event, game_state: "GameState"
    ) -> GameAction | None:
        """Handle keyboard input."""
        # Toggle chat with Enter or T key when not already chatting
        if not game_state.chat_input_active:
            if event.key in (pygame.K_RETURN, pygame.K_t):
                return GameAction.toggle_chat()
            # D key to drop object
            if event.key == pygame.K_d and game_state.companion.held_object:
                return GameAction.drop_object()
            return None

        # Chat input mode
        if event.key == pygame.K_RETURN:
            # Send message
            if game_state.chat_input_text.strip():
                text = game_state.chat_input_text
                return GameAction.send_chat(text)
            else:
                # Empty input, toggle chat off
                return GameAction.toggle_chat()

        elif event.key == pygame.K_ESCAPE:
            # Cancel chat
            return GameAction.toggle_chat()

        elif event.key == pygame.K_BACKSPACE:
            # Delete character
            if game_state.chat_input_text:
                new_text = game_state.chat_input_text[:-1]
                return GameAction.update_chat_input(new_text)

        elif event.unicode and event.unicode.isprintable():
            # Add character
            new_text = game_state.chat_input_text + event.unicode
            return GameAction.update_chat_input(new_text)

        return None
