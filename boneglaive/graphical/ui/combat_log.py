#!/usr/bin/env python3
"""
Combat Log UI Component
Displays scrolling log of game actions and events.
"""
import pygame
from typing import List, Dict, Optional

# Colors - matching ASCII version color scheme
COLOR_BG = (30, 34, 42)
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

LOG_WIDTH_BASE = 920  # Horizontal bar spanning game board width
LOG_HEIGHT_BASE = 90  # Maximum height fitting below map
LOG_PADDING_BASE = 8
LINE_HEIGHT_BASE = 16  # Tighter line spacing

# Pre-compile regex patterns for performance (don't recompile every frame!)
import re
DAMAGE_PATTERN = re.compile(r'#DAMAGE_(\d+)#')
HEAL_PATTERN = re.compile(r'#HEAL_(\d+)#')


class CombatLog:
    """Combat log UI component showing recent game events."""

    def __init__(self, font, layout=None):
        self.layout = layout
        self.font = font
        self.messages: List[Dict] = []
        self.max_messages = 200  # Expanded log capacity
        self.scroll_offset = 0
        self.auto_scroll = True
        self.last_synced_timestamp = 0.0  # Track last message timestamp to avoid duplicates

        # Cache background panel surface (create once, reuse every frame)
        self._cached_panel = None
        self._cached_panel_size = None

    def _get_scaled_dimensions(self):
        """Get scaled dimensions based on layout."""
        if self.layout:
            # Combat log scales with game board width
            log_width = self.layout.game_board_width
            scale = self.layout.get_font_scale()
            log_height = int(LOG_HEIGHT_BASE * scale)
            padding = int(LOG_PADDING_BASE * scale)
            line_height = int(LINE_HEIGHT_BASE * scale)
        else:
            log_width = LOG_WIDTH_BASE
            log_height = LOG_HEIGHT_BASE
            padding = LOG_PADDING_BASE
            line_height = LINE_HEIGHT_BASE

        return {
            'log_width': log_width,
            'log_height': log_height,
            'padding': padding,
            'line_height': line_height,
        }

    def add_message(self, text: str, msg_type: str = "system", player: Optional[int] = None):
        """
        Add a message to the log.

        Args:
            text: Message text
            msg_type: Type of message (system, combat, ability, movement, error)
            player: Player number associated with message
        """
        # PERFORMANCE FIX: Wrap text once when adding message, not every frame
        dims = self._get_scaled_dimensions()
        wrapped_lines = self._wrap_text(text, dims['log_width'] - dims['padding'] * 2 - 5)

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

        # Only add messages newer than our last synced timestamp
        # This prevents duplicates when called every frame (60 times per second)
        new_messages = [msg for msg in recent if msg.get('timestamp', 0) > self.last_synced_timestamp]

        for msg in new_messages:
            msg_type_str = msg['type'].value if hasattr(msg['type'], 'value') else str(msg['type'])
            # Process message text to add damage/heal placeholders (matching ASCII version)
            processed_text = self._process_message_placeholders(msg['text'], msg['type'])

            self.add_message(
                text=processed_text,
                msg_type=msg_type_str,
                player=msg.get('player')
            )

            # Update last synced timestamp
            self.last_synced_timestamp = msg.get('timestamp', 0)

    def clear(self):
        """Clear all messages."""
        self.messages.clear()
        self.scroll_offset = 0
        self.last_synced_timestamp = 0.0  # Reset timestamp when clearing

    def _process_message_placeholders(self, text: str, msg_type) -> str:
        """
        Process message text to add damage/heal placeholders (matching ASCII version).

        Args:
            text: Original message text
            msg_type: Message type (from MessageType enum)

        Returns:
            Processed text with #DAMAGE_X# and #HEAL_X# placeholders
        """
        import re
        from boneglaive.utils.message_log import MessageType

        # Convert to MessageType if needed
        if isinstance(msg_type, str):
            try:
                msg_type = MessageType(msg_type)
            except:
                return text

        # Special handling for damage numbers - highlight them in magenta
        # Look for combat or ability messages containing damage info
        if (msg_type == MessageType.COMBAT or msg_type == MessageType.ABILITY) and 'damage' in text:
            # Find the damage number in the text
            # Pattern to match "for X damage" or "suffers X [type] damage" where X is a number
            damage_match = re.search(r'for (\d+) damage', text)
            if not damage_match:
                damage_match = re.search(r'suffers (\d+) (?:\w+ )?damage', text)

            if damage_match:
                damage_num = damage_match.group(1)

                # Replace with the placeholder
                if f"for {damage_num} damage" in text:
                    text = text.replace(f"for {damage_num} damage", f"for #DAMAGE_{damage_num}# damage")
                elif f"suffers {damage_num}" in text:
                    # Handle "suffers X radiation damage" pattern
                    text = re.sub(f"suffers {damage_num} (\\w+ )?damage", f"suffers #DAMAGE_{damage_num}# \\1damage", text)

        # Special handling for healing numbers - highlight them in white
        # Look for healing messages (typical format: "X heals Y for Z HP" or "healing for Z HP")
        heal_match = re.search(r'heals .+ for (\d+) HP', text)
        if heal_match:
            heal_num = heal_match.group(1)
            # Replace the healing number with a placeholder
            text = text.replace(f"for {heal_num} HP", f"for #HEAL_{heal_num}# HP")
        else:
            # Also check for "healing for Z HP" format used by skills like Autoclave
            heal_match = re.search(r'healing for (\d+) HP', text)
            if heal_match:
                heal_num = heal_match.group(1)
                # Replace the healing number with a placeholder
                text = text.replace(f"for {heal_num} HP", f"for #HEAL_{heal_num}# HP")

        return text

    def scroll_up(self, lines: int = 1):
        """Scroll up in the log."""
        self.scroll_offset = min(self.scroll_offset + lines, max(0, len(self.messages) - 10))
        self.auto_scroll = False

    def scroll_down(self, lines: int = 1):
        """Scroll down in the log."""
        self.scroll_offset = max(self.scroll_offset - lines, 0)
        if self.scroll_offset == 0:
            self.auto_scroll = True

    def draw(self, surface: pygame.Surface, x: int, y: int, height: int = None, width: int = None):
        """
        Draw the combat log (horizontal layout below map).

        Args:
            surface: Surface to draw on
            x, y: Position to draw at (top-left)
            height: Optional custom height (uses scaled LOG_HEIGHT if None)
            width: Optional custom width (uses scaled LOG_WIDTH if None)
        """
        if not self.messages:
            return

        # Get scaled dimensions
        dims = self._get_scaled_dimensions()

        # Use custom dimensions if provided, otherwise use scaled defaults
        log_height = height if height is not None else dims['log_height']
        log_width = width if width is not None else dims['log_width']
        log_padding = dims['padding']
        line_height = dims['line_height']

        # Draw background panel using cached surface
        panel_rect = pygame.Rect(x, y, log_width, log_height)

        # Create or reuse cached panel surface
        if self._cached_panel is None or self._cached_panel_size != (log_width, log_height):
            self._cached_panel = pygame.Surface((log_width, log_height), pygame.SRCALPHA)
            self._cached_panel.fill((*COLOR_BG, 220))
            self._cached_panel_size = (log_width, log_height)

        surface.blit(self._cached_panel, (panel_rect.x, panel_rect.y))

        # Draw border
        pygame.draw.rect(surface, (100, 100, 100), panel_rect, 2)

        # Horizontal layout: show recent messages (fit as many as possible)
        max_lines = (log_height - log_padding * 2) // line_height  # Calculate based on height

        # Get most recent messages (truncate text to fit width)
        recent_messages = self.messages[-10:]  # Last 10 messages

        # Draw messages bottom to top (most recent at bottom)
        text_y = y + log_height - log_padding - line_height
        messages_drawn = 0

        for message in reversed(recent_messages):
            if messages_drawn >= max_lines:
                break

            # Get color for message
            color = self._get_message_color(message)

            # Get text and check for special number placeholders
            text = message['text']
            max_width = log_width - (log_padding * 2)

            # Check for damage or heal number placeholders (using pre-compiled patterns)
            damage_match = DAMAGE_PATTERN.search(text)
            heal_match = HEAL_PATTERN.search(text)

            if damage_match:
                # Split text around damage number
                damage_num = damage_match.group(1)
                parts = text.split(f'#DAMAGE_{damage_num}#')

                # Render parts with different colors
                pos_x = x + log_padding

                # First part (before damage)
                if parts[0]:
                    part_surface = self.font.render(parts[0], True, color)
                    surface.blit(part_surface, (pos_x, text_y))
                    pos_x += part_surface.get_width()

                # Damage number in magenta
                damage_surface = self.font.render(damage_num, True, COLOR_TEXT_DAMAGE)
                surface.blit(damage_surface, (pos_x, text_y))
                pos_x += damage_surface.get_width()

                # Remaining part (after damage)
                if len(parts) > 1 and parts[1]:
                    remaining_surface = self.font.render(parts[1], True, color)
                    surface.blit(remaining_surface, (pos_x, text_y))

            elif heal_match:
                # Split text around heal number
                heal_num = heal_match.group(1)
                parts = text.split(f'#HEAL_{heal_num}#')

                # Render parts with different colors
                pos_x = x + log_padding

                # First part (before heal)
                if parts[0]:
                    part_surface = self.font.render(parts[0], True, color)
                    surface.blit(part_surface, (pos_x, text_y))
                    pos_x += part_surface.get_width()

                # Heal number in white
                heal_surface = self.font.render(heal_num, True, COLOR_TEXT_HEAL)
                surface.blit(heal_surface, (pos_x, text_y))
                pos_x += heal_surface.get_width()

                # Remaining part (after heal)
                if len(parts) > 1 and parts[1]:
                    remaining_surface = self.font.render(parts[1], True, color)
                    surface.blit(remaining_surface, (pos_x, text_y))

            else:
                # No special numbers, render normally
                text_surface = self.font.render(text, True, color)

                # If text is too wide, truncate with ellipsis
                if text_surface.get_width() > max_width:
                    while text and self.font.render(text + "...", True, color).get_width() > max_width:
                        text = text[:-1]
                    text += "..."
                    text_surface = self.font.render(text, True, color)

                # Draw message
                surface.blit(text_surface, (x + log_padding, text_y))

            text_y -= line_height
            messages_drawn += 1

    def _get_message_color(self, message: Dict) -> tuple:
        """Get color for a message based on its type, player, and content (matching ASCII version)."""
        msg_type = message['type']
        player = message.get('player')
        text = message['text']

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
        if msg_type == 'error':
            return COLOR_TEXT_ERROR  # Red for errors

        # Player-specific colors for combat/ability messages
        # (matches ASCII: use player color for messages with attacker info or ability usage)
        if player is not None and (msg_type == 'combat' or msg_type == 'ability'):
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
