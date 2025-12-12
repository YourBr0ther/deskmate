"""Main application module with game loop."""

import pygame

from deskmate.core.config import get_settings, Settings
from deskmate.game.game_state import GameState
from deskmate.game.input_handler import InputHandler
from deskmate.rendering.renderer import Renderer


class App:
    """Main application class that runs the game loop."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the application."""
        self.settings = settings or get_settings()
        self.running = False

        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption(self.settings.display.title)

        # Create display
        self.screen = pygame.display.set_mode(
            (self.settings.display.width, self.settings.display.height)
        )
        self.clock = pygame.time.Clock()

        # Initialize game components
        self.game_state = GameState(self.settings)
        self.input_handler = InputHandler()
        self.renderer = Renderer(self.screen, self.settings)

        # Wire up chat panel rect for input handling
        self.input_handler.set_chat_panel_rect(self.renderer.get_chat_panel_rect())

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True

        while self.running:
            # Calculate delta time in seconds
            dt = self.clock.tick(self.settings.display.fps) / 1000.0

            # Process input
            events = pygame.event.get()
            actions = self.input_handler.process(events, self.game_state)

            # Check for quit
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Update game state
            self.game_state.update(dt, actions)

            # Render
            self.renderer.draw(self.game_state)
            pygame.display.flip()

        self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources."""
        self.game_state.shutdown()
        pygame.quit()


def create_app(settings: Settings | None = None) -> App:
    """Factory function to create an App instance."""
    return App(settings)
