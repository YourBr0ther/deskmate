"""Model selector dropdown UI component."""

import pygame


class ModelSelector:
    """
    Dropdown selector for choosing Ollama models.
    """

    # Colors
    BG_COLOR = (40, 44, 52)
    HOVER_COLOR = (50, 54, 62)
    SELECTED_COLOR = (60, 100, 150)
    BORDER_COLOR = (80, 84, 92)
    TEXT_COLOR = (220, 220, 230)
    LABEL_COLOR = (150, 150, 160)
    DROPDOWN_BG = (35, 38, 45)

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        font: pygame.font.Font,
    ) -> None:
        """Initialize the model selector."""
        self.x = x
        self.y = y
        self.width = width
        self.height = 28
        self.font = font

        self.models: list[str] = []
        self.selected_index: int = 0
        self.is_open: bool = False
        self.hover_index: int = -1

        # Dropdown dimensions
        self.max_visible_items = 6
        self.item_height = 24

        # Rects
        self.button_rect = pygame.Rect(x, y, width, self.height)
        self.dropdown_rect = pygame.Rect(0, 0, 0, 0)  # Updated when opened

    def set_models(self, models: list[str], current_model: str) -> None:
        """Set the available models and select the current one."""
        self.models = models if models else ["(no models)"]

        # Find and select current model
        self.selected_index = 0
        for i, model in enumerate(self.models):
            if model == current_model:
                self.selected_index = i
                break

    def get_selected_model(self) -> str | None:
        """Get the currently selected model name."""
        if not self.models or self.models[0] == "(no models)":
            return None
        return self.models[self.selected_index]

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Handle pygame events.

        Returns:
            The newly selected model name if changed, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            if self.is_open:
                # Check if clicked on a dropdown item
                if self.dropdown_rect.collidepoint(pos):
                    relative_y = pos[1] - self.dropdown_rect.y
                    clicked_index = relative_y // self.item_height

                    if 0 <= clicked_index < len(self.models):
                        if self.models[clicked_index] != "(no models)":
                            old_index = self.selected_index
                            self.selected_index = clicked_index
                            self.is_open = False

                            if old_index != clicked_index:
                                return self.models[clicked_index]

                # Close dropdown if clicked outside
                self.is_open = False

            elif self.button_rect.collidepoint(pos):
                # Toggle dropdown
                self.is_open = not self.is_open
                if self.is_open:
                    self._update_dropdown_rect()

        elif event.type == pygame.MOUSEMOTION and self.is_open:
            pos = event.pos
            if self.dropdown_rect.collidepoint(pos):
                relative_y = pos[1] - self.dropdown_rect.y
                self.hover_index = relative_y // self.item_height
            else:
                self.hover_index = -1

        return None

    def _update_dropdown_rect(self) -> None:
        """Update the dropdown rectangle based on models."""
        num_items = min(len(self.models), self.max_visible_items)
        dropdown_height = num_items * self.item_height

        self.dropdown_rect = pygame.Rect(
            self.x,
            self.y + self.height + 2,
            self.width,
            dropdown_height,
        )

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the model selector."""
        # Draw label
        label = self.font.render("Model:", True, self.LABEL_COLOR)
        screen.blit(label, (self.x, self.y - 18))

        # Draw button
        pygame.draw.rect(screen, self.BG_COLOR, self.button_rect, border_radius=4)
        pygame.draw.rect(screen, self.BORDER_COLOR, self.button_rect, 1, border_radius=4)

        # Draw selected model text
        if self.models:
            text = self.models[self.selected_index]
            # Truncate if too long
            max_text_width = self.width - 30
            while self.font.size(text)[0] > max_text_width and len(text) > 3:
                text = text[:-4] + "..."

            text_surface = self.font.render(text, True, self.TEXT_COLOR)
            screen.blit(text_surface, (self.x + 8, self.y + 6))

        # Draw dropdown arrow
        arrow_x = self.x + self.width - 18
        arrow_y = self.y + self.height // 2
        if self.is_open:
            # Up arrow
            points = [(arrow_x, arrow_y + 3), (arrow_x + 8, arrow_y + 3), (arrow_x + 4, arrow_y - 3)]
        else:
            # Down arrow
            points = [(arrow_x, arrow_y - 3), (arrow_x + 8, arrow_y - 3), (arrow_x + 4, arrow_y + 3)]
        pygame.draw.polygon(screen, self.TEXT_COLOR, points)

        # Draw dropdown if open
        if self.is_open:
            self._draw_dropdown(screen)

    def _draw_dropdown(self, screen: pygame.Surface) -> None:
        """Draw the dropdown list."""
        # Background
        pygame.draw.rect(screen, self.DROPDOWN_BG, self.dropdown_rect, border_radius=4)
        pygame.draw.rect(screen, self.BORDER_COLOR, self.dropdown_rect, 1, border_radius=4)

        # Items
        for i, model in enumerate(self.models[: self.max_visible_items]):
            item_rect = pygame.Rect(
                self.dropdown_rect.x + 2,
                self.dropdown_rect.y + i * self.item_height + 2,
                self.dropdown_rect.width - 4,
                self.item_height - 2,
            )

            # Highlight
            if i == self.hover_index:
                pygame.draw.rect(screen, self.HOVER_COLOR, item_rect, border_radius=2)
            elif i == self.selected_index:
                pygame.draw.rect(screen, self.SELECTED_COLOR, item_rect, border_radius=2)

            # Text
            text = model
            max_text_width = self.width - 16
            while self.font.size(text)[0] > max_text_width and len(text) > 3:
                text = text[:-4] + "..."

            text_surface = self.font.render(text, True, self.TEXT_COLOR)
            screen.blit(
                text_surface,
                (item_rect.x + 6, item_rect.y + (self.item_height - text_surface.get_height()) // 2),
            )

    def get_rect(self) -> pygame.Rect:
        """Get the full interactive area (button + dropdown if open)."""
        if self.is_open:
            return self.button_rect.union(self.dropdown_rect)
        return self.button_rect
