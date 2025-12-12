"""Main renderer that orchestrates drawing."""

from typing import TYPE_CHECKING

import pygame

from deskmate.core.config import Settings
from deskmate.rendering.sprites.companion import CompanionSprite
from deskmate.rendering.sprites.object import ObjectSprite
from deskmate.rendering.ui.chat_panel import ChatPanel
from deskmate.rendering.ui.model_selector import ModelSelector
from deskmate.rendering.ui.speech_bubble import SpeechBubble

if TYPE_CHECKING:
    from deskmate.game.game_state import GameState


class Renderer:
    """Main renderer that orchestrates all drawing operations."""

    # Colors
    BG_COLOR = (40, 44, 52)  # Dark background
    WALKABLE_COLOR = (60, 64, 72)  # Slightly lighter for walkable area
    GRID_COLOR = (50, 54, 62)

    def __init__(self, screen: pygame.Surface, settings: Settings) -> None:
        """Initialize the renderer."""
        self.screen = screen
        self.settings = settings

        # Initialize fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, settings.chat.font_size)
        self.title_font = pygame.font.Font(None, 24)

        # Create UI components
        chat_rect = pygame.Rect(
            settings.chat.panel_x,
            settings.chat.panel_y,
            settings.chat.panel_width,
            settings.chat.panel_height,
        )
        self.chat_panel = ChatPanel(chat_rect, self.font)

        # Model selector (top left, below room title)
        self.model_selector = ModelSelector(
            x=20,
            y=60,
            width=180,
            font=self.font,
        )

        # Sprite cache
        self.companion_sprite: CompanionSprite | None = None
        self.object_sprites: dict[str, ObjectSprite] = {}

        # Speech bubble
        self.speech_bubble = SpeechBubble(self.font)

    def draw(self, game_state: "GameState") -> None:
        """Draw the entire game state."""
        # Clear screen
        self.screen.fill(self.BG_COLOR)

        # Draw room background/walkable area
        self._draw_room(game_state)

        # Draw objects
        self._draw_objects(game_state)

        # Draw companion
        self._draw_companion(game_state)

        # Draw speech bubble if speaking
        if game_state.companion.speaking:
            self.speech_bubble.draw(
                self.screen,
                game_state.companion.current_speech,
                (int(game_state.companion.x), int(game_state.companion.y) - 60),
            )

        # Draw chat panel
        self.chat_panel.draw(self.screen, game_state)

        # Draw room title
        self._draw_room_title(game_state)

        # Draw model selector
        self._draw_model_selector(game_state)

        # Draw held object indicator
        if game_state.companion.held_object:
            self._draw_held_indicator(game_state)

    def _draw_room(self, game_state: "GameState") -> None:
        """Draw the room background and walkable area."""
        room = game_state.room

        # Draw walkable area
        walkable = room.walkable_area
        walkable_rect = pygame.Rect(
            walkable.min_x,
            walkable.min_y,
            walkable.max_x - walkable.min_x,
            walkable.max_y - walkable.min_y,
        )
        pygame.draw.rect(self.screen, self.WALKABLE_COLOR, walkable_rect)

        # Draw grid lines for visual reference
        for x in range(walkable.min_x, walkable.max_x, 50):
            pygame.draw.line(
                self.screen,
                self.GRID_COLOR,
                (x, walkable.min_y),
                (x, walkable.max_y),
                1,
            )
        for y in range(walkable.min_y, walkable.max_y, 50):
            pygame.draw.line(
                self.screen,
                self.GRID_COLOR,
                (walkable.min_x, y),
                (walkable.max_x, y),
                1,
            )

        # Draw walkable area border
        pygame.draw.rect(self.screen, (80, 84, 92), walkable_rect, 2)

    def _draw_objects(self, game_state: "GameState") -> None:
        """Draw all objects in the room."""
        for obj in game_state.room.objects:
            if obj.is_held:
                continue  # Don't draw held objects in their original position

            # Get or create sprite
            if obj.id not in self.object_sprites:
                self.object_sprites[obj.id] = ObjectSprite(obj)

            sprite = self.object_sprites[obj.id]
            sprite.update(obj)
            sprite.draw(self.screen)

    def _draw_companion(self, game_state: "GameState") -> None:
        """Draw the companion."""
        companion = game_state.companion

        # Create sprite if needed
        if self.companion_sprite is None:
            self.companion_sprite = CompanionSprite(companion)

        self.companion_sprite.update(companion)
        self.companion_sprite.draw(self.screen)

        # Draw movement target indicator
        if companion.target_x is not None and companion.target_y is not None:
            pygame.draw.circle(
                self.screen,
                (100, 200, 100),
                (int(companion.target_x), int(companion.target_y)),
                5,
                2,
            )

    def _draw_room_title(self, game_state: "GameState") -> None:
        """Draw the room title."""
        title_text = self.title_font.render(
            game_state.room.name, True, (150, 150, 160)
        )
        self.screen.blit(title_text, (20, 20))

    def _draw_held_indicator(self, game_state: "GameState") -> None:
        """Draw indicator for held object."""
        obj = game_state.companion.held_object
        if not obj:
            return

        # Draw small icon/text near companion
        text = self.font.render(f"Holding: {obj.name}", True, (200, 200, 100))
        x = int(game_state.companion.x) - text.get_width() // 2
        y = int(game_state.companion.y) + 40
        self.screen.blit(text, (x, y))

    def _draw_model_selector(self, game_state: "GameState") -> None:
        """Draw the model selector dropdown."""
        # Update models list if we have an Ollama service
        if game_state.available_models:
            current_model = ""
            if game_state.ollama_service:
                current_model = game_state.ollama_service.get_model()
            self.model_selector.set_models(game_state.available_models, current_model)

        self.model_selector.draw(self.screen)

    def get_chat_panel_rect(self) -> pygame.Rect:
        """Get the chat panel rectangle for input handling."""
        return self.chat_panel.rect

    def get_model_selector(self) -> ModelSelector:
        """Get the model selector for event handling."""
        return self.model_selector
