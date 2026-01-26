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
        self.has_upgrade_points = False  # Special flag for upgrade button glow

    def draw(self, surface: pygame.Surface, x: int, y: int, font, small_font, loto_renderer: Optional[LOTORenderer] = None) -> Optional[dict]:
        """Draw the action button. Returns particle data if upgrade button has points available."""
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

        # Draw upgrade points glow effect (gold pulsating) - GLOW ONLY, particles come later
        upgrade_glow_data = None
        if self.action == "upgrade" and self.has_upgrade_points:
            import math
            import time
            import random

            # Pulsating glow effect
            time_val = time.time()
            pulse = (math.sin(time_val * 3) + 1) / 2  # 0 to 1 pulsating

            # Darker gold color with lower alpha for subtler effect
            gold_color = (180, 140, 40)  # Darker, more bronze-gold
            glow_alpha = int(40 + pulse * 40)  # 40 to 80 alpha (much subtler)

            # Create glow surface with per-pixel alpha
            glow_surface = pygame.Surface((BUTTON_WIDTH + 20, BUTTON_HEIGHT + 20), pygame.SRCALPHA)

            # Draw multiple expanding glows for layered effect
            for i in range(3):
                offset = 10 - i * 3
                alpha = glow_alpha // (i + 1)
                glow_rect = pygame.Rect(offset, offset,
                                       BUTTON_WIDTH + (i * 2),
                                       BUTTON_HEIGHT + (i * 2))
                pygame.draw.rect(glow_surface, (*gold_color, alpha), glow_rect, border_radius=4)

            # Blit glow surface
            surface.blit(glow_surface, (x - 10, y - 10), special_flags=pygame.BLEND_RGBA_ADD)

            # Store data for particle drawing later (after text)
            upgrade_glow_data = {
                'time_val': time_val,
                'pulse': pulse,
                'gold_color': gold_color,
                'x': x,
                'y': y
            }

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

        # Return particle data to be drawn later (after all buttons)
        return upgrade_glow_data

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
            ActionButton("execute", "E", "EXECUTE TURN"),
            ActionButton("upgrade", "U", "UPGRADE"),
            ActionButton("help", "H", "HELP"),
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
            elif button.action == "upgrade":
                # Check if current player has upgrade points available
                if game:
                    if game.current_player == 1:
                        button.has_upgrade_points = game.player1_upgrade_points > 0
                    else:
                        button.has_upgrade_points = game.player2_upgrade_points > 0
                else:
                    button.has_upgrade_points = False
                button.enabled = True
                button.active = False
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

        # Draw each button and collect particle data
        particle_data_list = []
        for button in self.buttons:
            particle_data = button.draw(surface, x + MENU_PADDING, current_y, self.font, self.small_font, self.loto_renderer)
            if particle_data:
                particle_data_list.append(particle_data)
            current_y += BUTTON_HEIGHT + BUTTON_SPACING

        # Draw all particles AFTER all buttons (so they appear on top)
        for particle_data in particle_data_list:
            import random
            import math
            time_val = particle_data['time_val']
            pulse = particle_data['pulse']
            gold_color = particle_data['gold_color']
            px = particle_data['x']
            py = particle_data['y']

            # Draw particles
            # Use button position as seed for consistent but pseudo-random particle positions
            random.seed(int(time_val * 10) + px + py)
            num_particles = 8
            for i in range(num_particles):
                # Calculate particle position around button
                angle = (time_val + i * (3.14159 * 2 / num_particles)) % (3.14159 * 2)
                distance = 30 + pulse * 10
                particle_x = px + BUTTON_WIDTH // 2 + int(math.cos(angle) * distance)
                particle_y = py + BUTTON_HEIGHT // 2 + int(math.sin(angle) * distance)

                # Particle size varies with pulse
                particle_size = int(2 + pulse * 2)
                particle_alpha = int(60 + pulse * 50)  # 60 to 110 alpha (subtler particles)

                # Draw particle
                particle_surf = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*gold_color, particle_alpha),
                                 (particle_size, particle_size), particle_size)
                surface.blit(particle_surf, (particle_x - particle_size, particle_y - particle_size),
                           special_flags=pygame.BLEND_RGBA_ADD)

            # Reset random seed to not affect other random calls
            random.seed()

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
