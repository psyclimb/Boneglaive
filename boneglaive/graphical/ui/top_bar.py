#!/usr/bin/env python3
"""
Top Bar UI Component
Displays player info, turn count, GP score, and current mode.
"""
import pygame
import time
from typing import Optional
from .font_utils import render_fitted_text

# Colors - matching bone/industrial theme
COLOR_BG_TOP = (42, 42, 47)  # Panel top
COLOR_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_PLAYER1 = (100, 255, 100)  # Green
COLOR_PLAYER2 = (100, 150, 255)  # Blue
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_ACCENT = (255, 200, 100)
COLOR_BORDER = (90, 84, 79)  # Metal border

# Import scaling utilities
from .scale_utils import scale_manager

# Scale bar dimensions based on resolution
TOP_BAR_HEIGHT = scale_manager.scale(60, 'y')
SECTION_PADDING = scale_manager.scale(20)
TEXT_PADDING = scale_manager.scale(15)


class TopBar:
    """Top bar UI component showing game state information."""

    def __init__(self, font, small_font, large_font):
        self.font = font
        self.small_font = small_font
        self.large_font = large_font

        # Game state
        self.current_player = 1
        self.turn_number = 1
        self.player1_gp = 0
        self.player2_gp = 0
        self.current_mode = "SELECT"
        self.player1_name = "Player 1"
        self.player2_name = "Player 2"

        # Network state
        self.is_network_game = False
        self.is_your_turn = True

        # Animation state
        self.turn_pulse_time = 0
        self.gp_pulse_time = 0
        self.mode_transition_time = 0

    def update(self, game, current_mode: str = "SELECT"):
        """
        Update top bar with current game state.

        Args:
            game: Game instance from engine
            current_mode: Current action mode (SELECT, MOVE, ATTACK, SKILL)
        """
        if not game:
            return

        self.current_player = game.current_player
        self.turn_number = game.turn
        self.player1_gp = game.player1_gp
        self.player2_gp = game.player2_gp
        self.current_mode = current_mode.upper() if current_mode else ""

        # Get player names
        self.player1_name = game.get_player_name(1)
        self.player2_name = game.get_player_name(2)

    def set_network_state(self, is_network: bool, is_your_turn: bool):
        """Set network multiplayer state."""
        self.is_network_game = is_network
        self.is_your_turn = is_your_turn

    def trigger_turn_pulse(self):
        """Trigger turn change pulse animation."""
        self.turn_pulse_time = time.time()

    def trigger_gp_pulse(self):
        """Trigger GP score change pulse animation."""
        self.gp_pulse_time = time.time()

    def draw(self, surface: pygame.Surface, screen_width: int):
        """
        Draw the top bar.

        Args:
            surface: Surface to draw on
            screen_width: Width of screen
        """
        # Draw background with gradient
        from .menu_components import draw_gradient_rect
        bg_rect = pygame.Rect(0, 0, screen_width, TOP_BAR_HEIGHT)
        draw_gradient_rect(surface, bg_rect, COLOR_BG_TOP, COLOR_BG_BOTTOM, alpha=240)

        # Draw border at bottom
        pygame.draw.line(surface, COLOR_BORDER, (0, TOP_BAR_HEIGHT - 1),
                        (screen_width, TOP_BAR_HEIGHT - 1), 2)

        # Draw player indicator line at bottom
        player_color = COLOR_PLAYER1 if self.current_player == 1 else COLOR_PLAYER2
        pygame.draw.line(surface, player_color, (0, TOP_BAR_HEIGHT - 3),
                        (screen_width, TOP_BAR_HEIGHT - 3), 1)

        # Calculate section positions
        left_section_start = SECTION_PADDING
        # Center GP with the game board (280px left panel + 920px game board / 2)
        # Game board center = 280 + (920 / 2) = 280 + 460 = 740
        game_board_center = 280 + (920 // 2)
        right_section_start = screen_width - 300

        # Draw left section (empty - turn moved to left panel above motor, player moved to right panel)
        # No longer drawing anything in the top bar left section

        # Draw center section (GP score - centered with game board)
        self._draw_gp_score(surface, game_board_center)

        # Draw right section (Network status / System icons)
        if self.is_network_game:
            self._draw_network_status(surface, right_section_start)

    def _draw_player_info(self, surface: pygame.Surface, x: int):
        """Draw current player indicator."""
        y = TEXT_PADDING

        # Get player color and name
        player_color = COLOR_PLAYER1 if self.current_player == 1 else COLOR_PLAYER2
        player_name = self.player1_name if self.current_player == 1 else self.player2_name

        # Draw player name
        text = render_fitted_text(
            player_name.upper(),
            max_width=190,
            max_height=35,
            color=player_color,
            base_font_size=32,
            min_font_size=24,
            max_font_size=36
        )
        surface.blit(text, (x, y))

    def _draw_turn_info(self, surface: pygame.Surface, x: int):
        """Draw turn counter."""
        y = TEXT_PADDING + 5

        # Check for pulse animation
        pulse_alpha = 0
        if self.turn_pulse_time > 0:
            elapsed = time.time() - self.turn_pulse_time
            if elapsed < 0.5:  # Pulse for 0.5 seconds
                pulse_alpha = int(255 * (1 - elapsed / 0.5))

        # Draw turn text
        turn_text = render_fitted_text(
            f"TURN {self.turn_number}",
            max_width=120,
            max_height=25,
            color=COLOR_TEXT,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        # Draw pulse glow if active
        if pulse_alpha > 0:
            glow_surface = pygame.Surface(
                (turn_text.get_width() + 10, turn_text.get_height() + 10),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, (*COLOR_ACCENT, pulse_alpha),
                           glow_surface.get_rect(), border_radius=5)
            surface.blit(glow_surface, (x - 5, y - 5))

        surface.blit(turn_text, (x, y))

    def _draw_gp_score(self, surface: pygame.Surface, center_x: int):
        """Draw GP score display centered at given x position."""
        y = TEXT_PADDING + 5

        # Check for pulse animation
        pulse_alpha = 0
        if self.gp_pulse_time > 0:
            elapsed = time.time() - self.gp_pulse_time
            if elapsed < 0.5:
                pulse_alpha = int(255 * (1 - elapsed / 0.5))

        # Pre-render all components to calculate total width for centering
        label = render_fitted_text(
            "GP:",
            max_width=40,
            max_height=25,
            color=COLOR_TEXT_DIM,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        p1_text = render_fitted_text(
            str(self.player1_gp),
            max_width=40,
            max_height=25,
            color=COLOR_PLAYER1,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        sep = render_fitted_text(
            "|",
            max_width=20,
            max_height=25,
            color=COLOR_TEXT_DIM,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        p2_text = render_fitted_text(
            str(self.player2_gp),
            max_width=40,
            max_height=25,
            color=COLOR_PLAYER2,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        # Calculate total width
        total_width = (label.get_width() + 5 + p1_text.get_width() + 5 +
                      sep.get_width() + 5 + p2_text.get_width())

        # Start x position to center the entire GP display
        x = center_x - (total_width // 2)

        # Draw "GP:" label
        surface.blit(label, (x, y))
        x += label.get_width() + 5

        # Draw Player 1 score (with pulse if active)
        if pulse_alpha > 0 and self.current_player == 1:
            glow_surface = pygame.Surface(
                (p1_text.get_width() + 8, p1_text.get_height() + 8),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, (*COLOR_PLAYER1, pulse_alpha),
                           glow_surface.get_rect(), border_radius=3)
            surface.blit(glow_surface, (x - 4, y - 4))
        surface.blit(p1_text, (x, y))
        x += p1_text.get_width() + 5

        # Draw separator
        surface.blit(sep, (x, y))
        x += sep.get_width() + 5

        # Draw Player 2 score (with pulse if active)
        if pulse_alpha > 0 and self.current_player == 2:
            glow_surface = pygame.Surface(
                (p2_text.get_width() + 8, p2_text.get_height() + 8),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, (*COLOR_PLAYER2, pulse_alpha),
                           glow_surface.get_rect(), border_radius=3)
            surface.blit(glow_surface, (x - 4, y - 4))
        surface.blit(p2_text, (x, y))

    def _draw_mode_indicator(self, surface: pygame.Surface, x: int):
        """Draw current action mode."""
        y = TEXT_PADDING + 5

        # Mode display text
        mode_text = render_fitted_text(
            f"MODE: {self.current_mode}",
            max_width=190,
            max_height=25,
            color=COLOR_ACCENT,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        # Center horizontally in allocated space
        text_rect = mode_text.get_rect(center=(x + 100, y + mode_text.get_height() // 2))
        surface.blit(mode_text, text_rect)

    def _draw_network_status(self, surface: pygame.Surface, x: int):
        """Draw network multiplayer status."""
        y = TEXT_PADDING + 5

        if self.is_your_turn:
            # Draw "YOUR TURN" with pulse
            status_text = render_fitted_text(
                "YOUR TURN",
                max_width=150,
                max_height=25,
                color=COLOR_ACCENT,
                base_font_size=20,
                min_font_size=16,
                max_font_size=24
            )

            # Pulsing glow effect
            pulse = abs((time.time() * 2) % 2 - 1)  # 0 to 1 to 0
            glow_alpha = int(100 + 155 * pulse)
            glow_surface = pygame.Surface(
                (status_text.get_width() + 20, status_text.get_height() + 10),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, (*COLOR_ACCENT, glow_alpha),
                           glow_surface.get_rect(), border_radius=5)
            surface.blit(glow_surface, (x - 10, y - 5))

            surface.blit(status_text, (x, y))
        else:
            # Draw "WAITING..." dimmed
            status_text = render_fitted_text(
                "WAITING...",
                max_width=150,
                max_height=25,
                color=COLOR_TEXT_DIM,
                base_font_size=20,
                min_font_size=16,
                max_font_size=24
            )
            surface.blit(status_text, (x, y))
