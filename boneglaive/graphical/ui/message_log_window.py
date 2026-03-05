#!/usr/bin/env python3
"""
Expanded Message Log Window
Full-screen scrollable message history viewer.
"""
import pygame
from typing import List, Dict, Optional

# Colors - matching bone/industrial theme
COLOR_BG_TOP = (42, 42, 47)  # Panel top
COLOR_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_BORDER = (90, 84, 79)  # Metal border
COLOR_TEXT_SYSTEM = (200, 200, 200)  # Gray - default/system messages
COLOR_TEXT_COMBAT = (255, 200, 100)  # Orange - combat messages (deprecated, use player colors)
COLOR_TEXT_ABILITY = (200, 150, 255)  # Light purple - ability messages (deprecated, use player colors)
COLOR_TEXT_MOVEMENT = (150, 200, 150)  # Light green - movement messages (deprecated, use player colors)
COLOR_TEXT_ERROR = (255, 100, 100)  # Red - error messages
COLOR_TEXT_WARNING = (255, 255, 100)  # Yellow - warnings and debuffs
COLOR_TEXT_DEATH = (150, 50, 50)  # Dark red - death messages
COLOR_TEXT_WRETCH = (255, 100, 100)  # Bright red - wretch messages
COLOR_TEXT_DOMINION = (255, 100, 255)  # Bright magenta - Dominion upgrade messages
COLOR_TEXT_DAMAGE = (200, 100, 255)  # Magenta - damage numbers
COLOR_TEXT_HEAL = (255, 255, 255)  # White - healing numbers
COLOR_TEXT_PLAYER1 = (100, 255, 100)  # Green - Player 1 messages
COLOR_TEXT_PLAYER2 = (100, 150, 255)  # Blue - Player 2 messages
COLOR_SCROLLBAR = (80, 80, 80)
COLOR_SCROLLBAR_HANDLE = (120, 120, 120)

LINE_HEIGHT = 20
PADDING = 20
SCROLLBAR_WIDTH = 12

# Pre-compile regex patterns for performance
import re
DAMAGE_PATTERN = re.compile(r'#DAMAGE_(\d+)#')
HEAL_PATTERN = re.compile(r'#HEAL_(\d+)#')


class MessageLogWindow:
    """Expanded message log window with full message history."""

    def __init__(self, font, small_font, layout=None):
        self.layout = layout
        self.font = font
        self.small_font = small_font
        self.visible = False
        self.messages: List[Dict] = []
        self.scroll_offset = 0  # Number of lines scrolled from bottom
        self.max_visible_lines = 30

        # Cache overlay surface (only when visible)
        self._cached_overlay = None
        self._cached_overlay_size = None

    def show(self, messages: List[Dict]):
        """
        Show the window with message history.

        Args:
            messages: List of message dicts from CombatLog
        """
        self.visible = True
        self.messages = messages.copy()
        self.scroll_offset = 0  # Start at bottom

    def hide(self):
        """Hide the window."""
        self.visible = False
        # Clear cached overlay to free memory when not visible
        self._cached_overlay = None
        self._cached_overlay_size = None

    def handle_scroll(self, direction: int):
        """
        Scroll the message log.

        Args:
            direction: -1 for up, 1 for down
        """
        # Count total wrapped lines
        total_lines = sum(len(msg['wrapped_lines']) for msg in self.messages)

        if direction < 0:  # Scroll up
            self.scroll_offset = min(self.scroll_offset + 3, max(0, total_lines - self.max_visible_lines))
        else:  # Scroll down
            self.scroll_offset = max(0, self.scroll_offset - 3)

    def _get_message_color(self, msg_type: str, player: Optional[int], text: str = "") -> tuple:
        """Get color for message based on type, player, and content (matching ASCII version)."""
        # Content-based colors (highest priority - matches ASCII logic from message_log.py)
        # Check for critical event messages first
        if " perishes!" in text or "perishes from falling debris!" in text:
            return COLOR_TEXT_DEATH  # Dark red for death messages
        elif " retches!" in text:
            return COLOR_TEXT_WRETCH  # Bright red for retching messages
        elif "DOMINION:" in text or "absorbs power from the fallen" in text:
            return COLOR_TEXT_DOMINION  # Bright magenta for Dominion upgrades

        # Check for debuff/warning messages
        elif ("movement reduced" in text or "debuff" in text.lower() or
              ("penalty" in text.lower() and "due to Stasiality" not in text) or
              "displaced from" in text or "collides with" in text or
              ("immobilized" in text and "immune to" not in text) or
              ("trapped in" in text and "due to Stasiality" not in text) or
              "slogs through" in text):
            return COLOR_TEXT_WARNING  # Yellow for debuffs and negative effects

        # Error messages
        if msg_type == "error":
            return COLOR_TEXT_ERROR  # Red for errors

        # Player-specific colors for combat/ability messages
        # (matches ASCII: use player color for messages with attacker info or ability usage)
        if player is not None and (msg_type == "combat" or msg_type == "ability"):
            if player == 1:
                return COLOR_TEXT_PLAYER1
            elif player == 2:
                return COLOR_TEXT_PLAYER2

        # Chat messages (player messages without combat/ability type)
        if player == 1:
            return COLOR_TEXT_PLAYER1
        elif player == 2:
            return COLOR_TEXT_PLAYER2

        # Default to gray for system messages
        return COLOR_TEXT_SYSTEM

    def draw(self, surface: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the expanded message log window."""
        if not self.visible:
            return

        # Calculate window dimensions (80% of screen)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Draw semi-transparent overlay (cached)
        if self._cached_overlay is None or self._cached_overlay_size != (screen_width, screen_height):
            self._cached_overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            self._cached_overlay.fill((0, 0, 0, 180))
            self._cached_overlay_size = (screen_width, screen_height)

        surface.blit(self._cached_overlay, (0, 0))

        # Draw window background with gradient
        from .menu_components import draw_gradient_rect
        window_rect = pygame.Rect(window_x, window_y, window_width, window_height)
        draw_gradient_rect(surface, window_rect, COLOR_BG_TOP, COLOR_BG_BOTTOM)
        pygame.draw.rect(surface, COLOR_BORDER, window_rect, 3, border_radius=8)

        # Draw title
        title_text = self.font.render("Message Log (ESC to close, Arrow Keys to scroll)", True, (255, 255, 255))
        title_x = window_x + (window_width - title_text.get_width()) // 2
        surface.blit(title_text, (title_x, window_y + PADDING))

        # Calculate content area
        content_y = window_y + PADDING + 40
        content_height = window_height - PADDING * 2 - 40
        content_width = window_width - PADDING * 2 - SCROLLBAR_WIDTH - 10
        self.max_visible_lines = content_height // LINE_HEIGHT

        # Flatten all messages into lines with their colors
        all_lines = []
        for msg in self.messages:
            color = self._get_message_color(msg['type'], msg.get('player'), msg['text'])
            # Store original text for placeholder detection
            for line in msg['wrapped_lines']:
                all_lines.append({'text': line, 'color': color, 'original_text': msg['text']})

        # Calculate visible range (scroll from bottom)
        total_lines = len(all_lines)
        start_line = max(0, total_lines - self.max_visible_lines - self.scroll_offset)
        end_line = total_lines - self.scroll_offset
        visible_lines = all_lines[start_line:end_line]

        # Draw messages with special handling for damage/heal numbers
        y = content_y

        for line_data in visible_lines:
            text = line_data['text']
            color = line_data['color']

            # Check for damage or heal number placeholders (using pre-compiled patterns)
            damage_match = DAMAGE_PATTERN.search(text)
            heal_match = HEAL_PATTERN.search(text)

            pos_x = window_x + PADDING

            if damage_match:
                # Split text around damage number
                damage_num = damage_match.group(1)
                parts = text.split(f'#DAMAGE_{damage_num}#')

                # First part (before damage)
                if parts[0]:
                    part_surface = self.small_font.render(parts[0], True, color)
                    surface.blit(part_surface, (pos_x, y))
                    pos_x += part_surface.get_width()

                # Damage number in magenta
                damage_surface = self.small_font.render(damage_num, True, COLOR_TEXT_DAMAGE)
                surface.blit(damage_surface, (pos_x, y))
                pos_x += damage_surface.get_width()

                # Remaining part (after damage)
                if len(parts) > 1 and parts[1]:
                    remaining_surface = self.small_font.render(parts[1], True, color)
                    surface.blit(remaining_surface, (pos_x, y))

            elif heal_match:
                # Split text around heal number
                heal_num = heal_match.group(1)
                parts = text.split(f'#HEAL_{heal_num}#')

                # First part (before heal)
                if parts[0]:
                    part_surface = self.small_font.render(parts[0], True, color)
                    surface.blit(part_surface, (pos_x, y))
                    pos_x += part_surface.get_width()

                # Heal number in white
                heal_surface = self.small_font.render(heal_num, True, COLOR_TEXT_HEAL)
                surface.blit(heal_surface, (pos_x, y))
                pos_x += heal_surface.get_width()

                # Remaining part (after heal)
                if len(parts) > 1 and parts[1]:
                    remaining_surface = self.small_font.render(parts[1], True, color)
                    surface.blit(remaining_surface, (pos_x, y))

            else:
                # No special numbers, render normally
                text_surface = self.small_font.render(text, True, color)
                surface.blit(text_surface, (pos_x, y))

            y += LINE_HEIGHT

            if y > window_y + window_height - PADDING:
                break

        # Draw scrollbar if needed
        if total_lines > self.max_visible_lines:
            scrollbar_x = window_x + window_width - PADDING - SCROLLBAR_WIDTH
            scrollbar_y = content_y
            scrollbar_height = content_height

            # Scrollbar track
            pygame.draw.rect(surface, COLOR_SCROLLBAR,
                           (scrollbar_x, scrollbar_y, SCROLLBAR_WIDTH, scrollbar_height))

            # Scrollbar handle
            handle_height = max(20, int(scrollbar_height * (self.max_visible_lines / total_lines)))
            scroll_ratio = self.scroll_offset / (total_lines - self.max_visible_lines)
            handle_y = scrollbar_y + int((scrollbar_height - handle_height) * (1 - scroll_ratio))

            pygame.draw.rect(surface, COLOR_SCROLLBAR_HANDLE,
                           (scrollbar_x, handle_y, SCROLLBAR_WIDTH, handle_height))

        # Draw instructions at bottom
        instructions = self.small_font.render("Use UP/DOWN arrows to scroll", True, (150, 150, 150))
        instr_x = window_x + (window_width - instructions.get_width()) // 2
        surface.blit(instructions, (instr_x, window_y + window_height - PADDING - 20))
