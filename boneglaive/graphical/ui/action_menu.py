#!/usr/bin/env python3
"""
Action Menu UI Component
Displays action buttons for Move, Attack, Execute, etc.
"""
import pygame
from typing import Optional, Tuple, Callable, Set
from .font_utils import render_fitted_text
from .loto_system import LOTORenderer, LOTOChecker

# Colors
COLOR_BG = (30, 34, 42)
COLOR_BG_HOVER = (50, 54, 62)
COLOR_BG_ACTIVE = (60, 100, 140)
COLOR_BG_DISABLED = (40, 40, 40)
COLOR_BORDER = (100, 100, 100)
COLOR_BORDER_HOVER = (150, 150, 150)
COLOR_BORDER_ACTIVE = (100, 150, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DISABLED = (120, 120, 120)
COLOR_HOTKEY = (255, 200, 100)
COLOR_EXECUTE = (100, 255, 100)
COLOR_DANGER = (255, 100, 100)

BUTTON_WIDTH = 264  # Fits in 280px panel
BUTTON_HEIGHT = 40  # Slightly smaller
BUTTON_SPACING = 6  # Tighter spacing
MENU_PADDING = 8


class ActionButton:
    """Individual action button."""

    def __init__(self, action: str, hotkey: str, label: str, icon: str = None):
        self.action = action  # "move", "attack", "execute", "respawn", "concede"
        self.hotkey = hotkey
        self.label = label
        self.icon = icon
        self.rect = None
        self.hovered = False
        self.enabled = True
        self.active = False  # Current active mode
        self.blocked_actions = set()  # LOTO: Set of blocked action types

    def draw(self, surface: pygame.Surface, x: int, y: int, font, small_font, loto_renderer: Optional[LOTORenderer] = None):
        """Draw the action button."""
        self.rect = pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT)

        # Determine background color
        if not self.enabled:
            bg_color = COLOR_BG_DISABLED
        elif self.active:
            bg_color = COLOR_BG_ACTIVE
        elif self.hovered:
            bg_color = COLOR_BG_HOVER
        else:
            bg_color = COLOR_BG

        # Special coloring for execute and concede buttons
        if self.action == "execute" and self.enabled and not self.active:
            bg_color = (*COLOR_EXECUTE, 80) if self.hovered else (*COLOR_EXECUTE, 40)
        elif self.action == "concede":
            bg_color = (*COLOR_DANGER, 60) if self.hovered else (*COLOR_DANGER, 30)

        # Draw background
        pygame.draw.rect(surface, bg_color, self.rect)

        # Draw border
        border_color = COLOR_BORDER_HOVER if self.hovered else COLOR_BORDER
        if self.active:
            border_color = COLOR_BORDER_ACTIVE

        border_width = 3 if (self.hovered or self.active) else 2
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw hotkey in top-left corner
        text_color = COLOR_TEXT_DISABLED if not self.enabled else COLOR_HOTKEY
        hotkey_text = render_fitted_text(
            f"[{self.hotkey}]",
            max_width=50,
            max_height=20,
            color=text_color,
            base_font_size=16,
            min_font_size=12,
            max_font_size=16
        )
        surface.blit(hotkey_text, (x + 8, y + 5))

        # Draw label text (centered)
        text_color = COLOR_TEXT_DISABLED if not self.enabled else COLOR_TEXT
        label_text = render_fitted_text(
            self.label,
            max_width=BUTTON_WIDTH - 20,
            max_height=BUTTON_HEIGHT - 10,
            color=text_color,
            base_font_size=20,
            min_font_size=14,
            max_font_size=22
        )
        label_rect = label_text.get_rect(center=(x + BUTTON_WIDTH // 2, y + BUTTON_HEIGHT // 2))
        surface.blit(label_text, label_rect)

        # Draw LOTO overlay if action is blocked
        if loto_renderer and self.blocked_actions:
            loto_renderer.draw_loto_overlay(surface, self.rect, self.blocked_actions, scale=0.6)

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if position is inside this button."""
        if self.rect:
            return self.rect.collidepoint(pos)
        return False


class ActionMenu:
    """Action menu component with quick action buttons."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font

        # Create action buttons
        self.buttons = [
            ActionButton("attack", "A", "ATTACK"),
            ActionButton("respawn", "R", "RESPAWN"),
            ActionButton("help", "H", "HELP"),
            ActionButton("execute", "E", "EXECUTE TURN"),
            ActionButton("concede", "C", "CONCEDE"),
        ]

        self.hovered_button: Optional[ActionButton] = None
        self.current_mode = None  # Current action mode (move, attack, skill)

        # State
        self.has_actions_queued = False
        self.has_respawns_available = False

        # LOTO system
        self.loto_renderer = LOTORenderer()

    def update(self, game, selected_unit, current_mode: str, has_actions: bool):
        """
        Update action menu state.

        Args:
            game: Game instance
            selected_unit: Currently selected unit (game unit, not animated unit)
            current_mode: Current action mode string
            has_actions: Whether any units have queued actions
        """
        self.current_mode = current_mode.lower() if current_mode else None
        self.has_actions_queued = has_actions

        # Check for available respawns
        if game:
            ready_units = [du for du in game.dead_units
                          if du.player == game.current_player and du.ready_for_respawn]
            self.has_respawns_available = len(ready_units) > 0
        else:
            self.has_respawns_available = False

        # Check for LOTO blocked actions on selected unit
        blocked_actions = set()
        if selected_unit:
            blocked_actions = LOTOChecker.get_blocked_actions(selected_unit)

        # Update button states
        for button in self.buttons:
            if button.action == "attack":
                button.enabled = selected_unit is not None
                button.active = (self.current_mode == "attack")
                # Check if attack is blocked (e.g., during gaussian recharge)
                if selected_unit and LOTOChecker.is_action_blocked(selected_unit, 'attack'):
                    button.blocked_actions = blocked_actions
                    button.enabled = False
                else:
                    button.blocked_actions = set()
            elif button.action == "respawn":
                button.enabled = self.has_respawns_available
                button.active = (self.current_mode == "respawn")
                button.blocked_actions = set()
            elif button.action == "help":
                button.enabled = True
                button.active = False
                button.blocked_actions = set()
            elif button.action == "execute":
                button.enabled = self.has_actions_queued
                button.active = False
                button.blocked_actions = set()
            elif button.action == "concede":
                button.enabled = True
                button.active = False
                button.blocked_actions = set()

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw the action menu.

        Args:
            surface: Surface to draw on
            x, y: Position (top-left)
        """
        current_y = y + MENU_PADDING

        # Draw each button
        for button in self.buttons:
            button.draw(surface, x + MENU_PADDING, current_y, self.font, self.small_font, self.loto_renderer)
            current_y += BUTTON_HEIGHT + BUTTON_SPACING

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Update hovered button based on mouse position."""
        self.hovered_button = None
        for button in self.buttons:
            button.hovered = button.contains_point(mouse_pos)
            if button.hovered:
                self.hovered_button = button

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle click on action menu.

        Returns:
            Action string if a button was clicked and is enabled, None otherwise
        """
        for button in self.buttons:
            if button.contains_point(mouse_pos):
                if button.enabled:
                    return button.action
        return None

    def handle_hotkey(self, key: int) -> Optional[str]:
        """
        Handle hotkey press.

        Args:
            key: pygame key constant

        Returns:
            Action string if hotkey matches enabled button, None otherwise
        """
        # Map pygame keys to hotkey strings
        key_map = {
            pygame.K_m: 'M',
            pygame.K_a: 'A',
            pygame.K_r: 'R',
            pygame.K_h: 'H',
            pygame.K_e: 'E',
            pygame.K_c: 'C',
        }

        hotkey_str = key_map.get(key)
        if not hotkey_str:
            return None

        # Find button with matching hotkey
        for button in self.buttons:
            if button.hotkey == hotkey_str and button.enabled:
                return button.action

        return None

    def get_height(self) -> int:
        """Calculate total height needed for this component."""
        num_buttons = len(self.buttons)
        return (MENU_PADDING * 2 +
                num_buttons * BUTTON_HEIGHT +
                (num_buttons - 1) * BUTTON_SPACING)
