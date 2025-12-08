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
COLOR_TEXT_PLAYER1 = (100, 150, 255)
COLOR_TEXT_PLAYER2 = (255, 100, 100)

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
        message = {
            'text': text,
            'type': msg_type,
            'player': player
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

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw the combat log.

        Args:
            surface: Surface to draw on
            x, y: Position to draw at (top-left)
        """
        if not self.messages:
            return

        # Draw background panel
        panel_rect = pygame.Rect(x, y, LOG_WIDTH, LOG_HEIGHT)
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((*COLOR_BG, 200))
        surface.blit(panel_surface, (panel_rect.x, panel_rect.y))

        # Draw border
        pygame.draw.rect(surface, (100, 100, 100), panel_rect, 2)

        # Draw title
        title_text = self.font.render("Combat Log", True, (255, 255, 255))
        surface.blit(title_text, (x + LOG_PADDING, y + 5))

        # Calculate visible messages
        max_visible_lines = (LOG_HEIGHT - 35) // LINE_HEIGHT
        start_idx = max(0, len(self.messages) - max_visible_lines - self.scroll_offset)
        end_idx = len(self.messages) - self.scroll_offset
        visible_messages = self.messages[start_idx:end_idx]

        # Draw messages from bottom up
        text_y = y + LOG_HEIGHT - LOG_PADDING - LINE_HEIGHT
        for message in reversed(visible_messages):
            if text_y < y + 30:  # Don't draw over title
                break

            # Choose color based on message type
            color = self._get_message_color(message)

            # Render and draw text
            text = message['text']
            # Truncate if too long
            if len(text) > 45:
                text = text[:42] + "..."

            text_surface = self.font.render(text, True, color)
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
