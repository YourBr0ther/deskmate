"""Speech bubble UI component for companion dialogue."""

import pygame


class SpeechBubble:
    """
    Speech bubble that appears above the companion when speaking.

    Displays the AI's response in a comic-style speech bubble.
    """

    # Colors
    BG_COLOR = (255, 255, 255)
    BORDER_COLOR = (60, 60, 70)
    TEXT_COLOR = (30, 30, 40)

    def __init__(self, font: pygame.font.Font, max_width: int = 250) -> None:
        """Initialize the speech bubble."""
        self.font = font
        self.max_width = max_width
        self.padding = 12
        self.tail_height = 10

    def draw(
        self, screen: pygame.Surface, text: str, position: tuple[int, int]
    ) -> None:
        """
        Draw the speech bubble at the given position.

        Args:
            screen: Surface to draw on
            text: Text to display
            position: (x, y) position for the bubble tail (usually companion head)
        """
        if not text:
            return

        # Wrap text to fit max width
        lines = self._wrap_text(text)

        # Calculate bubble dimensions
        line_height = self.font.get_linesize()
        text_height = len(lines) * line_height
        text_width = max(self.font.size(line)[0] for line in lines)

        bubble_width = text_width + self.padding * 2
        bubble_height = text_height + self.padding * 2

        # Position bubble above the position point
        bubble_x = position[0] - bubble_width // 2
        bubble_y = position[1] - bubble_height - self.tail_height

        # Keep bubble on screen
        bubble_x = max(10, min(screen.get_width() - bubble_width - 10, bubble_x))
        bubble_y = max(10, bubble_y)

        # Draw bubble background
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        pygame.draw.rect(screen, self.BG_COLOR, bubble_rect, border_radius=8)
        pygame.draw.rect(screen, self.BORDER_COLOR, bubble_rect, 2, border_radius=8)

        # Draw tail (triangle pointing down)
        tail_x = position[0]
        tail_points = [
            (tail_x - 8, bubble_y + bubble_height - 2),
            (tail_x + 8, bubble_y + bubble_height - 2),
            (tail_x, bubble_y + bubble_height + self.tail_height),
        ]
        pygame.draw.polygon(screen, self.BG_COLOR, tail_points)
        pygame.draw.lines(screen, self.BORDER_COLOR, False, tail_points[1:], 2)
        pygame.draw.lines(screen, self.BORDER_COLOR, False, tail_points[:2], 2)

        # Draw text
        y = bubble_y + self.padding
        for line in lines:
            text_surface = self.font.render(line, True, self.TEXT_COLOR)
            text_x = bubble_x + self.padding
            screen.blit(text_surface, (text_x, y))
            y += line_height

    def _wrap_text(self, text: str) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split(" ")
        lines = []
        current_line = ""
        content_width = self.max_width - self.padding * 2

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.font.size(test_line)[0] <= content_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # Handle words longer than max width
                if self.font.size(word)[0] > content_width:
                    # Truncate with ellipsis
                    current_line = word[:15] + "..."
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        # Limit to 4 lines max for speech bubble
        if len(lines) > 4:
            lines = lines[:3]
            lines.append(lines[-1][:20] + "..." if len(lines[-1]) > 20 else lines[-1])

        return lines if lines else [""]
