#!/usr/bin/env python3
"""
Game Over Window UI Component
Modal window displayed when the game ends (victory or defeat).
"""
import pygame
from typing import Optional, Callable

# Colors - matching bone/industrial theme
COLOR_OVERLAY = (0, 0, 0, 200)  # Dark semi-transparent overlay
COLOR_WINDOW_BG_TOP = (42, 42, 47)  # Panel top
COLOR_WINDOW_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_WINDOW_BORDER = (90, 84, 79)  # Metal border
COLOR_TITLE_BG_TOP = (50, 50, 55)  # Title bar gradient top
COLOR_TITLE_BG_BOTTOM = (38, 38, 43)  # Title bar gradient bottom
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_VICTORY = (100, 200, 100)  # Green for victory
COLOR_DEFEAT = (200, 100, 100)   # Red for defeat
COLOR_PLAYER1 = (100, 255, 100)  # Green for player 1 (UI text color)
COLOR_PLAYER2 = (100, 150, 255)  # Blue for player 2 (UI text color)
COLOR_BUTTON_TOP = (74, 74, 79)  # Button gradient top
COLOR_BUTTON_BOTTOM = (50, 50, 55)  # Button gradient bottom
COLOR_BUTTON_HOVER_TOP = (90, 74, 79)  # Button hover gradient top
COLOR_BUTTON_HOVER_BOTTOM = (64, 48, 53)  # Button hover gradient bottom
COLOR_BORDER_HOVER = (184, 168, 149)  # Bone border on hover
COLOR_BORDER_GLOW = (255, 170, 119)  # Orange glow

# Minimized bar dimensions
MINIMIZED_BAR_HEIGHT = 70
MINIMIZED_BUTTON_WIDTH = 145
MINIMIZED_BUTTON_HEIGHT = 40
MINIMIZED_BUTTON_SPACING = 10


class GameOverWindow:
    """Modal window shown when game ends with victory or defeat."""

    def __init__(self, font, small_font, large_font, layout=None):
        self.layout = layout
        self.font = font
        self.small_font = small_font
        self.large_font = large_font
        self.visible = False
        self.minimized = False  # Toggle between full window and compact bar

        # Game over state
        self.is_victory = False
        self.winner_name = ""
        self.winner_gp = 0
        self.loser_name = ""
        self.loser_gp = 0
        self.winner_player = 1  # Track which player won (1 or 2)

        # Button state
        self.hovered_button = None  # "menu", "exit", or "minimize"
        self.buttons = {}  # {name: pygame.Rect}

        # Cache overlay surface (performance)
        self._overlay_cache = None

        # Callbacks
        self.on_return_to_menu: Optional[Callable] = None
        self.on_exit_game: Optional[Callable] = None

    def show(self, is_victory: bool, winner_name: str, winner_gp: int,
             loser_name: str, loser_gp: int, winner_player: int = 1):
        """
        Show the game over window.

        Args:
            is_victory: True if local player won, False if lost
            winner_name: Name of winning player
            winner_gp: GP score of winner
            loser_name: Name of losing player
            loser_gp: GP score of loser
            winner_player: Which player won (1 or 2)
        """
        self.visible = True
        self.minimized = False  # Start in full window mode
        self.is_victory = is_victory
        self.winner_name = winner_name
        self.winner_gp = winner_gp
        self.loser_name = loser_name
        self.loser_gp = loser_gp
        self.winner_player = winner_player
        self.hovered_button = None

    def hide(self):
        """Hide the game over window."""
        self.visible = False
        self.minimized = False
        self.hovered_button = None

    def toggle_minimize(self):
        """Toggle between full window and minimized bar."""
        self.minimized = not self.minimized
        self.hovered_button = None  # Reset hover state on toggle

    def handle_mouse_motion(self, mouse_pos: tuple):
        """Handle mouse motion events."""
        if not self.visible:
            return

        # Check button hovers
        self.hovered_button = None
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                self.hovered_button = button_name
                break

    def handle_mouse_click(self, mouse_pos: tuple) -> Optional[str]:
        """
        Handle mouse click events.

        Returns:
            Action string ("menu" or "exit") or None
        """
        if not self.visible:
            return None

        # Check button clicks
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                return button_name

        return None

    def handle_key(self, key: int) -> Optional[str]:
        """
        Handle keyboard input.

        Args:
            key: Pygame key constant

        Returns:
            Action string ("menu", "exit", or "minimize") or None
        """
        if not self.visible:
            return None

        # R = toggle minimize
        if key == pygame.K_r:
            return "minimize"
        # ESC or M = return to menu
        elif key == pygame.K_ESCAPE or key == pygame.K_m:
            return "menu"
        # Q or X = exit
        elif key == pygame.K_q or key == pygame.K_x:
            return "exit"

        return None

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the game over window (full or minimized)."""
        if not self.visible:
            return

        if self.minimized:
            self._draw_minimized(screen, screen_width, screen_height)
        else:
            self._draw_full_window(screen, screen_width, screen_height)

    def _draw_full_window(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the full game over window."""
        from .menu_components import draw_gradient_rect, draw_glow_rect

        # Draw semi-transparent overlay
        if self._overlay_cache is None or self._overlay_cache.get_size() != (screen_width, screen_height):
            self._overlay_cache = pygame.Surface((screen_width, screen_height))
            self._overlay_cache.set_alpha(200)
            self._overlay_cache.fill((0, 0, 0))
        screen.blit(self._overlay_cache, (0, 0))

        # Calculate scaled dimensions
        scale = self.layout.get_font_scale() if self.layout else 1.0
        window_width = int(600 * scale)
        window_height = int(400 * scale)
        button_width = int(175 * scale)  # Smaller to fit 3 buttons
        button_height = int(60 * scale)
        button_spacing = int(10 * scale)  # Tighter spacing
        
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2
        window_rect = pygame.Rect(window_x, window_y, window_width, window_height)

        # Draw window background with gradient
        draw_gradient_rect(screen, window_rect, COLOR_WINDOW_BG_TOP, COLOR_WINDOW_BG_BOTTOM)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, window_rect, 2, border_radius=5)

        # Draw title bar with gradient
        title_rect = pygame.Rect(window_x, window_y, window_width, 60)
        title_color = COLOR_VICTORY if self.is_victory else COLOR_DEFEAT
        draw_gradient_rect(screen, title_rect, COLOR_TITLE_BG_TOP, COLOR_TITLE_BG_BOTTOM)
        pygame.draw.rect(screen, title_color, title_rect, 3, border_radius=5)

        # Draw title text
        title_text = "VICTORY!" if self.is_victory else "DEFEAT"
        title_surface = self.large_font.render(title_text, True, title_color)
        title_x = window_x + (window_width - title_surface.get_width()) // 2
        title_y = window_y + (60 - title_surface.get_height()) // 2
        screen.blit(title_surface, (title_x, title_y))

        # Draw game results
        content_y = window_y + 80

        # Winner info - use player-specific color
        winner_color = COLOR_PLAYER1 if self.winner_player == 1 else COLOR_PLAYER2
        winner_text = f"{self.winner_name} wins with {self.winner_gp} GP!"
        winner_surface = self.font.render(winner_text, True, winner_color)
        winner_x = window_x + (window_width - winner_surface.get_width()) // 2
        screen.blit(winner_surface, (winner_x, content_y))

        # Loser info
        content_y += 40
        loser_text = f"{self.loser_name}: {self.loser_gp} GP"
        loser_surface = self.small_font.render(loser_text, True, COLOR_TEXT_DIM)
        loser_x = window_x + (window_width - loser_surface.get_width()) // 2
        screen.blit(loser_surface, (loser_x, content_y))

        # Flavor text
        content_y += 50
        if self.is_victory:
            flavor = "A tactical triumph! Your strategic prowess is unmatched."
        else:
            flavor = "Defeat, but not dishonor. Study your opponent's tactics."
        flavor_surface = self.small_font.render(flavor, True, COLOR_TEXT_DIM)
        flavor_x = window_x + (window_width - flavor_surface.get_width()) // 2
        screen.blit(flavor_surface, (flavor_x, content_y))

        # Draw buttons (3 buttons: menu, minimize, exit)
        button_y = window_y + window_height - 100
        total_button_width = button_width * 3 + button_spacing * 2
        button_x_offset = (window_width - total_button_width) // 2

        # Return to Menu button
        menu_button_x = window_x + button_x_offset
        menu_button_rect = pygame.Rect(menu_button_x, button_y, button_width, button_height)
        self.buttons["menu"] = menu_button_rect

        if self.hovered_button == "menu":
            draw_gradient_rect(screen, menu_button_rect, COLOR_BUTTON_HOVER_TOP, COLOR_BUTTON_HOVER_BOTTOM)
            pygame.draw.rect(screen, COLOR_BORDER_HOVER, menu_button_rect, 2, border_radius=5)
        else:
            draw_gradient_rect(screen, menu_button_rect, COLOR_BUTTON_TOP, COLOR_BUTTON_BOTTOM)
            pygame.draw.rect(screen, COLOR_WINDOW_BORDER, menu_button_rect, 2, border_radius=5)

        menu_text = "Menu (M)"
        menu_surface = self.font.render(menu_text, True, COLOR_TEXT)
        menu_text_x = menu_button_x + (button_width - menu_surface.get_width()) // 2
        menu_text_y = button_y + (button_height - menu_surface.get_height()) // 2
        screen.blit(menu_surface, (menu_text_x, menu_text_y))

        # Minimize button (middle)
        minimize_button_x = menu_button_x + button_width + button_spacing
        minimize_button_rect = pygame.Rect(minimize_button_x, button_y, button_width, button_height)
        self.buttons["minimize"] = minimize_button_rect

        if self.hovered_button == "minimize":
            draw_gradient_rect(screen, minimize_button_rect, COLOR_BUTTON_HOVER_TOP, COLOR_BUTTON_HOVER_BOTTOM)
            pygame.draw.rect(screen, COLOR_BORDER_HOVER, minimize_button_rect, 2, border_radius=5)
        else:
            draw_gradient_rect(screen, minimize_button_rect, COLOR_BUTTON_TOP, COLOR_BUTTON_BOTTOM)
            pygame.draw.rect(screen, COLOR_WINDOW_BORDER, minimize_button_rect, 2, border_radius=5)

        minimize_text = "Minimize (R)"
        minimize_surface = self.font.render(minimize_text, True, COLOR_TEXT)
        minimize_text_x = minimize_button_x + (button_width - minimize_surface.get_width()) // 2
        minimize_text_y = button_y + (button_height - minimize_surface.get_height()) // 2
        screen.blit(minimize_surface, (minimize_text_x, minimize_text_y))

        # Exit Game button
        exit_button_x = minimize_button_x + button_width + button_spacing
        exit_button_rect = pygame.Rect(exit_button_x, button_y, button_width, button_height)
        self.buttons["exit"] = exit_button_rect

        if self.hovered_button == "exit":
            draw_gradient_rect(screen, exit_button_rect, COLOR_BUTTON_HOVER_TOP, COLOR_BUTTON_HOVER_BOTTOM)
            pygame.draw.rect(screen, COLOR_BORDER_HOVER, exit_button_rect, 2, border_radius=5)
        else:
            draw_gradient_rect(screen, exit_button_rect, COLOR_BUTTON_TOP, COLOR_BUTTON_BOTTOM)
            pygame.draw.rect(screen, COLOR_WINDOW_BORDER, exit_button_rect, 2, border_radius=5)

        exit_text = "Exit (Q)"
        exit_surface = self.font.render(exit_text, True, COLOR_TEXT)
        exit_text_x = exit_button_x + (button_width - exit_surface.get_width()) // 2
        exit_text_y = button_y + (button_height - exit_surface.get_height()) // 2
        screen.blit(exit_surface, (exit_text_x, exit_text_y))

    def _draw_minimized(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw compact minimized bar at top of screen."""
        from .menu_components import draw_gradient_rect

        # Calculate bar dimensions using layout if available
        if self.layout:
            # Position bar in game board area, below top bar
            bar_width = self.layout.game_board_width - 20
            bar_x = self.layout.left_panel_width + 10
            bar_y = self.layout.top_bar_height + 20
        else:
            # Fallback to hardcoded values
            bar_width = 900
            bar_x = 290
            bar_y = 70

        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, MINIMIZED_BAR_HEIGHT)

        # Draw bar background with gradient and border
        draw_gradient_rect(screen, bar_rect, COLOR_WINDOW_BG_TOP, COLOR_WINDOW_BG_BOTTOM, alpha=240)
        title_color = COLOR_VICTORY if self.is_victory else COLOR_DEFEAT
        pygame.draw.rect(screen, title_color, bar_rect, 3, border_radius=5)

        # Draw result text on left side
        text_x = bar_x + 20
        text_y = bar_y + 10

        # Winner text
        winner_color = COLOR_PLAYER1 if self.winner_player == 1 else COLOR_PLAYER2
        winner_text = f"{self.winner_name} WINS! ({self.winner_gp} GP)"
        winner_surface = self.font.render(winner_text, True, winner_color)
        screen.blit(winner_surface, (text_x, text_y))

        # Draw compact buttons on right side
        button_y = bar_y + 15
        button_x = bar_x + bar_width - (MINIMIZED_BUTTON_WIDTH * 3 + MINIMIZED_BUTTON_SPACING * 2 + 20)

        # Draw 3 compact buttons
        button_configs = [
            ("menu", "Menu", button_x),
            ("minimize", "Expand", button_x + MINIMIZED_BUTTON_WIDTH + MINIMIZED_BUTTON_SPACING),
            ("exit", "Exit", button_x + (MINIMIZED_BUTTON_WIDTH + MINIMIZED_BUTTON_SPACING) * 2)
        ]

        for button_name, text, x in button_configs:
            button_rect = pygame.Rect(x, button_y, MINIMIZED_BUTTON_WIDTH, MINIMIZED_BUTTON_HEIGHT)
            self.buttons[button_name] = button_rect

            if self.hovered_button == button_name:
                draw_gradient_rect(screen, button_rect, COLOR_BUTTON_HOVER_TOP, COLOR_BUTTON_HOVER_BOTTOM)
                pygame.draw.rect(screen, COLOR_BORDER_HOVER, button_rect, 2, border_radius=3)
            else:
                draw_gradient_rect(screen, button_rect, COLOR_BUTTON_TOP, COLOR_BUTTON_BOTTOM)
                pygame.draw.rect(screen, COLOR_WINDOW_BORDER, button_rect, 2, border_radius=3)

            text_surface = self.small_font.render(text, True, COLOR_TEXT)
            text_x = x + (MINIMIZED_BUTTON_WIDTH - text_surface.get_width()) // 2
            text_y = button_y + (MINIMIZED_BUTTON_HEIGHT - text_surface.get_height()) // 2
            screen.blit(text_surface, (text_x, text_y))
