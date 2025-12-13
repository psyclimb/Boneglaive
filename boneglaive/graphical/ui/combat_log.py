#!/usr/bin/env python3
"""
Combat Log UI Component
Displays scrolling log of game actions and events.
"""
import pygame
from typing import List, Dict, Optional

# Colors
COLOR_BG = (30, 34, 42)
COLOR_TEXT_SYSTEM = (200, 200, 200)
COLOR_TEXT_COMBAT = (255, 200, 100)
COLOR_TEXT_ABILITY = (200, 150, 255)
COLOR_TEXT_MOVEMENT = (150, 200, 150)
COLOR_TEXT_ERROR = (255, 100, 100)
COLOR_TEXT_PLAYER1 = (100, 255, 100)  # Green
COLOR_TEXT_PLAYER2 = (100, 150, 255)  # Blue

LOG_WIDTH = 270  # Fits in 280px panel with padding
LOG_HEIGHT = 180  # Slightly shorter
LOG_PADDING = 8
LINE_HEIGHT = 16  # Tighter line spacing


class CombatLog:
    """Combat log UI component showing recent game events."""

    def __init__(self, font):
        self.font = font
        self.messages: List[Dict] = []
        self.max_messages = 50
        self.scroll_offset = 0
        self.auto_scroll = True

    def add_message(self, text: str, msg_type: str = "system", player: Optional[int] = None):
        """
        Add a message to the log.

        Args:
            text: Message text
            msg_type: Type of message (system, combat, ability, movement, error)
            player: Player number associated with message
        """
        # PERFORMANCE FIX: Wrap text once when adding message, not every frame
        wrapped_lines = self._wrap_text(text, LOG_WIDTH - LOG_PADDING * 2 - 5)

        message = {
            'text': text,
            'type': msg_type,
            'player': player,
            'wrapped_lines': wrapped_lines  # Cache wrapped text
        }

        self.messages.append(message)

        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            self.scroll_offset = 0

    def add_messages_from_game_log(self, game_message_log, count: int = 10):
        """
        Fetch recent messages from the game's message log system.

        Args:
            game_message_log: boneglaive.utils.message_log.MessageLog instance
            count: Number of recent messages to fetch
        """
        if not game_message_log:
            return

        # Get recent messages
        recent = game_message_log.get_recent_messages(count=count)

        # Check if we need to add new messages
        # (avoid duplicates by checking timestamps or message text)
        for msg in recent:
            # Simple deduplication: check if message text already in recent messages
            if not any(m['text'] == msg['text'] for m in self.messages[-5:]):
                msg_type_str = msg['type'].value if hasattr(msg['type'], 'value') else str(msg['type'])
                self.add_message(
                    text=msg['text'],
                    msg_type=msg_type_str,
                    player=msg.get('player')
                )

    def clear(self):
        """Clear all messages."""
        self.messages.clear()
        self.scroll_offset = 0

    def scroll_up(self, lines: int = 1):
        """Scroll up in the log."""
        self.scroll_offset = min(self.scroll_offset + lines, max(0, len(self.messages) - 10))
        self.auto_scroll = False

    def scroll_down(self, lines: int = 1):
        """Scroll down in the log."""
        self.scroll_offset = max(self.scroll_offset - lines, 0)
        if self.scroll_offset == 0:
            self.auto_scroll = True

    def draw(self, surface: pygame.Surface, x: int, y: int, height: int = None):
        """
        Draw the combat log.

        Args:
            surface: Surface to draw on
            x, y: Position to draw at (top-left)
            height: Optional custom height (uses LOG_HEIGHT if None)
        """
        if not self.messages:
            return

        # Use custom height if provided, otherwise use default
        log_height = height if height is not None else LOG_HEIGHT

        # Draw background panel
        panel_rect = pygame.Rect(x, y, LOG_WIDTH, log_height)
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((*COLOR_BG, 200))
        surface.blit(panel_surface, (panel_rect.x, panel_rect.y))

        # Draw border
        pygame.draw.rect(surface, (100, 100, 100), panel_rect, 2)

        # Draw title
        title_text = self.font.render("Combat Log", True, (255, 255, 255))
        surface.blit(title_text, (x + LOG_PADDING, y + 5))

        # PERFORMANCE FIX: Use cached wrapped lines instead of wrapping every frame
        wrapped_messages = []
        for message in self.messages:
            # Use pre-wrapped lines from cache (added in add_message)
            wrapped_lines = message.get('wrapped_lines', [message['text']])
            wrapped_messages.append({
                'lines': wrapped_lines,
                'type': message['type'],
                'player': message.get('player')
            })

        # Calculate which wrapped messages to show
        max_visible_lines = (log_height - 35) // LINE_HEIGHT

        # Flatten wrapped messages into lines (oldest to newest)
        all_lines = []
        for wrapped_msg in wrapped_messages:
            for line in wrapped_msg['lines']:
                all_lines.append({
                    'text': line,
                    'type': wrapped_msg['type'],
                    'player': wrapped_msg['player']
                })

        # Apply scroll offset and limit (show most recent at bottom)
        # When scroll_offset is 0, show the most recent messages
        total_lines = len(all_lines)
        if total_lines <= max_visible_lines:
            visible_lines = all_lines
        else:
            # Show most recent lines, offset from the end
            start_idx = max(0, total_lines - max_visible_lines - self.scroll_offset)
            end_idx = total_lines - self.scroll_offset
            visible_lines = all_lines[start_idx:end_idx]

        # Draw lines from bottom up (most recent at bottom)
        text_y = y + log_height - LOG_PADDING - LINE_HEIGHT
        for line_data in reversed(visible_lines):
            if text_y < y + 30:  # Don't draw over title
                break

            # Choose color based on message type
            color = self._get_message_color(line_data)

            # Render and draw text
            text_surface = self.font.render(line_data['text'], True, color)
            surface.blit(text_surface, (x + LOG_PADDING, text_y))

            text_y -= LINE_HEIGHT

        # Draw scroll indicator if not at bottom
        if self.scroll_offset > 0:
            indicator_text = self.font.render(f"^ {self.scroll_offset} more ^", True, (150, 150, 150))
            surface.blit(indicator_text, (x + LOG_WIDTH // 2 - 50, y + 5))

    def _get_message_color(self, message: Dict) -> tuple:
        """Get color for a message based on its type and player."""
        msg_type = message['type']
        player = message.get('player')

        # Player-specific colors
        if player == 1:
            return COLOR_TEXT_PLAYER1
        elif player == 2:
            return COLOR_TEXT_PLAYER2

        # Type-based colors
        if msg_type == 'combat':
            return COLOR_TEXT_COMBAT
        elif msg_type == 'ability':
            return COLOR_TEXT_ABILITY
        elif msg_type == 'movement':
            return COLOR_TEXT_MOVEMENT
        elif msg_type == 'error':
            return COLOR_TEXT_ERROR
        else:
            return COLOR_TEXT_SYSTEM

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width pixels.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels

        Returns:
            List of wrapped lines
        """
        if not text:
            return [""]

        # Estimate characters per line based on font size
        # For 16px font, roughly 8-10 pixels per character
        approx_chars_per_line = max_width // 8

        # If text fits on one line, return it
        test_surface = self.font.render(text, True, (255, 255, 255))
        if test_surface.get_width() <= max_width:
            return [text]

        # Wrap text by words
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            # Test if adding this word would exceed width
            test_line = current_line + (" " if current_line else "") + word
            test_surface = self.font.render(test_line, True, (255, 255, 255))

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                # Word doesn't fit, start new line
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, truncate it
                    current_line = word[:approx_chars_per_line-3] + "..."
                    lines.append(current_line)
                    current_line = ""

        # Add last line
        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def handle_scroll(self, direction: int):
        """
        Handle scroll wheel input.

        Args:
            direction: 1 for up, -1 for down
        """
        if direction > 0:
            self.scroll_up(3)
        else:
            self.scroll_down(3)
