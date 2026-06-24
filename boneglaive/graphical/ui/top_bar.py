#!/usr/bin/env python3
"""
Top Bar UI Component
Displays player info, turn count, GP score, and current mode.
"""
import pygame
import time
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

        # Animation state (gp_pulse_time read by _draw_gp_score)
        self.gp_pulse_time = 0

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

        # Calculate section positions (use dynamic panel widths)
        from boneglaive.graphical.renderer import LEFT_PANEL_WIDTH, GAME_BOARD_WIDTH

        left_section_start = SECTION_PADDING
        # Center GP with the game board (left panel + half of game board width)
        game_board_center = LEFT_PANEL_WIDTH + (GAME_BOARD_WIDTH // 2)
        # Right section scales with resolution
        # Draw center section (GP score - centered with game board)
        self._draw_gp_score(surface, game_board_center)

    def _draw_gp_score(self, surface: pygame.Surface, center_x: int):
        """Draw GP score display centered at given x position."""
        # Scale spacing values
        y_offset = scale_manager.scale(5, 'y')
        y = TEXT_PADDING + y_offset

        # Check for pulse animation
        pulse_alpha = 0
        if self.gp_pulse_time > 0:
            elapsed = time.time() - self.gp_pulse_time
            if elapsed < 0.5:
                pulse_alpha = int(255 * (1 - elapsed / 0.5))

        # Scale text dimensions
        max_text_width = scale_manager.scale(40, 'x')
        max_text_height = scale_manager.scale(25, 'y')
        max_sep_width = scale_manager.scale(20, 'x')

        # Pre-render all components to calculate total width for centering
        label = render_fitted_text(
            "GP:",
            max_width=max_text_width,
            max_height=max_text_height,
            color=COLOR_TEXT_DIM,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        p1_text = render_fitted_text(
            str(self.player1_gp),
            max_width=max_text_width,
            max_height=max_text_height,
            color=COLOR_PLAYER1,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        sep = render_fitted_text(
            "|",
            max_width=max_sep_width,
            max_height=max_text_height,
            color=COLOR_TEXT_DIM,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        p2_text = render_fitted_text(
            str(self.player2_gp),
            max_width=max_text_width,
            max_height=max_text_height,
            color=COLOR_PLAYER2,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        # Calculate total width with scaled spacing
        element_spacing = scale_manager.scale(5, 'x')
        total_width = (label.get_width() + element_spacing + p1_text.get_width() + element_spacing +
                      sep.get_width() + element_spacing + p2_text.get_width())

        # Start x position to center the entire GP display
        x = center_x - (total_width // 2)

        # Draw "GP:" label
        surface.blit(label, (x, y))
        x += label.get_width() + element_spacing

        # Draw Player 1 score (with pulse if active)
        glow_padding = scale_manager.scale(8)
        glow_offset = scale_manager.scale(4)
        glow_radius = scale_manager.scale(3)

        if pulse_alpha > 0 and self.current_player == 1:
            glow_surface = pygame.Surface(
                (p1_text.get_width() + glow_padding, p1_text.get_height() + glow_padding),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, (*COLOR_PLAYER1, pulse_alpha),
                           glow_surface.get_rect(), border_radius=glow_radius)
            surface.blit(glow_surface, (x - glow_offset, y - glow_offset))
        surface.blit(p1_text, (x, y))
        x += p1_text.get_width() + element_spacing

        # Draw separator
        surface.blit(sep, (x, y))
        x += sep.get_width() + element_spacing

        # Draw Player 2 score (with pulse if active)
        if pulse_alpha > 0 and self.current_player == 2:
            glow_surface = pygame.Surface(
                (p2_text.get_width() + glow_padding, p2_text.get_height() + glow_padding),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, (*COLOR_PLAYER2, pulse_alpha),
                           glow_surface.get_rect(), border_radius=glow_radius)
            surface.blit(glow_surface, (x - glow_offset, y - glow_offset))
        surface.blit(p2_text, (x, y))
