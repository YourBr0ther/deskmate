"""Chat panel UI component."""

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from deskmate.game.game_state import GameState


class ChatPanel:
    """
    Chat panel for displaying conversation and text input.

    Displays message history and provides a text input box.
    """

    # Colors
    BG_COLOR = (30, 32, 40, 230)  # Semi-transparent dark
    BORDER_COLOR = (60, 64, 72)
    USER_COLOR = (100, 180, 255)  # Blue for user
    ASSISTANT_COLOR = (180, 255, 180)  # Green for AI
    INPUT_BG_COLOR = (40, 44, 52)
    INPUT_ACTIVE_COLOR = (50, 54, 62)
    INPUT_TEXT_COLOR = (220, 220, 230)
    CURSOR_COLOR = (255, 255, 255)
    WAITING_COLOR = (255, 200, 100)  # Orange for waiting

    def __init__(self, rect: pygame.Rect, font: pygame.font.Font) -> None:
        """Initialize the chat panel."""
        self.rect = rect
        self.font = font
        self.scroll_offset = 0
        self.max_scroll = 0

        # Create surfaces
        self.surface = pygame.Surface(rect.size, pygame.SRCALPHA)

        # Input box dimensions
        self.input_height = 32
        self.input_rect = pygame.Rect(
            4,
            rect.height - self.input_height - 4,
            rect.width - 8,
            self.input_height,
        )

        # Message area
        self.message_area_height = rect.height - self.input_height - 16

        # Cursor blink
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def draw(self, screen: pygame.Surface, game_state: "GameState") -> None:
        """Draw the chat panel."""
        self.surface.fill(self.BG_COLOR)

        # Draw border
        pygame.draw.rect(
            self.surface, self.BORDER_COLOR, pygame.Rect(0, 0, self.rect.width, self.rect.height), 2
        )

        # Draw title
        title = self.font.render("Chat", True, (150, 150, 160))
        self.surface.blit(title, (8, 4))

        # Draw messages
        self._draw_messages(game_state)

        # Draw input box
        self._draw_input_box(game_state)

        # Draw waiting indicator
        if game_state.chat_state.name == "WAITING_FOR_RESPONSE":
            self._draw_waiting_indicator()

        # Blit to screen
        screen.blit(self.surface, self.rect.topleft)

    def _draw_messages(self, game_state: "GameState") -> None:
        """Draw the message history."""
        messages = game_state.conversation.messages
        y = 28  # Start below title
        max_y = self.message_area_height

        # Calculate line wrapping width
        wrap_width = self.rect.width - 16

        for msg in messages:
            if msg.role.name == "SYSTEM":
                continue  # Don't display system messages

            # Choose color based on role
            if msg.role.name == "USER":
                color = self.USER_COLOR
                prefix = "You: "
            else:
                color = self.ASSISTANT_COLOR
                prefix = "AI: "

            # Wrap text
            lines = self._wrap_text(prefix + msg.content, wrap_width)

            for line in lines:
                if y > max_y:
                    break
                text_surface = self.font.render(line, True, color)
                self.surface.blit(text_surface, (8, y))
                y += self.font.get_linesize()

            y += 4  # Space between messages

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def _draw_input_box(self, game_state: "GameState") -> None:
        """Draw the text input box."""
        # Background color based on active state
        bg_color = self.INPUT_ACTIVE_COLOR if game_state.chat_input_active else self.INPUT_BG_COLOR

        pygame.draw.rect(self.surface, bg_color, self.input_rect, border_radius=4)
        pygame.draw.rect(self.surface, self.BORDER_COLOR, self.input_rect, 1, border_radius=4)

        # Draw text
        text = game_state.chat_input_text
        if not text and not game_state.chat_input_active:
            # Placeholder text
            placeholder = self.font.render(
                "Press T or Enter to chat...", True, (100, 100, 110)
            )
            self.surface.blit(
                placeholder, (self.input_rect.x + 8, self.input_rect.y + 6)
            )
        else:
            text_surface = self.font.render(text, True, self.INPUT_TEXT_COLOR)
            self.surface.blit(
                text_surface, (self.input_rect.x + 8, self.input_rect.y + 6)
            )

            # Draw cursor if active
            if game_state.chat_input_active:
                self.cursor_timer += 0.016
                if self.cursor_timer > 0.5:
                    self.cursor_timer = 0
                    self.cursor_visible = not self.cursor_visible

                if self.cursor_visible:
                    cursor_x = self.input_rect.x + 8 + text_surface.get_width() + 2
                    cursor_y = self.input_rect.y + 6
                    pygame.draw.line(
                        self.surface,
                        self.CURSOR_COLOR,
                        (cursor_x, cursor_y),
                        (cursor_x, cursor_y + self.font.get_linesize() - 4),
                        2,
                    )

    def _draw_waiting_indicator(self) -> None:
        """Draw a waiting for response indicator."""
        text = self.font.render("Thinking...", True, self.WAITING_COLOR)
        x = self.input_rect.x + self.input_rect.width - text.get_width() - 8
        y = self.input_rect.y - 20
        self.surface.blit(text, (x, y))
