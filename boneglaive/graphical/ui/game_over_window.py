#!/usr/bin/env python3
"""
Game Over Window UI Component
Modal window displayed when the game ends (victory or defeat).
"""
import pygame
from typing import Optional, Callable

# Colors
COLOR_OVERLAY = (0, 0, 0, 200)  # Dark semi-transparent overlay
COLOR_WINDOW_BG = (30, 34, 42)
COLOR_WINDOW_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_VICTORY = (100, 200, 100)  # Green for victory
COLOR_DEFEAT = (200, 100, 100)   # Red for defeat
COLOR_PLAYER1 = (100, 255, 100)  # Green for player 1 (UI text color)
COLOR_PLAYER2 = (100, 150, 255)  # Blue for player 2 (UI text color)
COLOR_BUTTON_BG = (50, 54, 62)
COLOR_BUTTON_HOVER = (70, 74, 82)
COLOR_BUTTON_BORDER = (120, 120, 120)

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
BUTTON_WIDTH = 175  # Smaller to fit 3 buttons in window
BUTTON_HEIGHT = 60
BUTTON_SPACING = 10  # Tighter spacing for 3 buttons

# Minimized bar dimensions (fits in center game board area: 920px wide)
MINIMIZED_BAR_HEIGHT = 70
MINIMIZED_BUTTON_WIDTH = 145
MINIMIZED_BUTTON_HEIGHT = 40
MINIMIZED_BUTTON_SPACING = 10


class GameOverWindow:
    """Modal window shown when game ends with victory or defeat."""

    def __init__(self, font, small_font, large_font):
        self.font = font
        self.small_font = small_font
        self.large_font = large_font
        self.visible = False
        self.minimized = False  # NEW: Toggle between full window and compact bar

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

    def _draw_minimized(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw compact minimized bar at top of screen."""
        # No dark overlay in minimized mode - player can see battlefield

        # Calculate bar dimensions (fits in center game board area)
        # Screen layout: LEFT_PANEL (280px) | GAME_BOARD (920px) | RIGHT_PANEL (280px)
        # Top bar is 50px tall, so position bar below it
        LEFT_PANEL_WIDTH = 280
        GAME_BOARD_WIDTH = 920
        TOP_BAR_HEIGHT = 50

        bar_width = GAME_BOARD_WIDTH - 20  # 900px (leave 10px margins)
        bar_x = LEFT_PANEL_WIDTH + 10  # 290px (start after left panel with margin)
        bar_y = TOP_BAR_HEIGHT + 20  # 70px (below top bar with spacing)
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, MINIMIZED_BAR_HEIGHT)

        # Draw bar background
        pygame.draw.rect(screen, COLOR_WINDOW_BG, bar_rect)
        title_color = COLOR_VICTORY if self.is_victory else COLOR_DEFEAT
        pygame.draw.rect(screen, title_color, bar_rect, 3)

        # Draw result text on left side of bar
        text_x = bar_x + 20
        text_y = bar_y + 15

        # Title (VICTORY/DEFEAT)
        title_text = "VICTORY!" if self.is_victory else "DEFEAT"
        title_surface = self.font.render(title_text, True, title_color)
        screen.blit(title_surface, (text_x, text_y))

        # Winner info
        winner_color = COLOR_PLAYER1 if self.winner_player == 1 else COLOR_PLAYER2
        winner_text = f"{self.winner_name}: {self.winner_gp} GP"
        winner_surface = self.small_font.render(winner_text, True, winner_color)
        screen.blit(winner_surface, (text_x + 120, text_y + 5))

        # Loser info
        loser_text = f"| {self.loser_name}: {self.loser_gp} GP"
        loser_surface = self.small_font.render(loser_text, True, COLOR_TEXT_DIM)
        screen.blit(loser_surface, (text_x + 120 + winner_surface.get_width() + 10, text_y + 5))

        # Draw buttons on right side of bar
        button_x_start = bar_x + bar_width - (MINIMIZED_BUTTON_WIDTH * 3 + MINIMIZED_BUTTON_SPACING * 2 + 20)
        button_y = bar_y + (MINIMIZED_BAR_HEIGHT - MINIMIZED_BUTTON_HEIGHT) // 2

        self.buttons = {}  # Reset buttons dict

        # Show Details button
        details_button_rect = pygame.Rect(button_x_start, button_y, MINIMIZED_BUTTON_WIDTH, MINIMIZED_BUTTON_HEIGHT)
        self.buttons["minimize"] = details_button_rect
        details_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "minimize" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, details_bg_color, details_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, details_button_rect, 2)
        details_text = "Show Details (R)"
        details_surface = self.small_font.render(details_text, True, COLOR_TEXT)
        details_text_x = button_x_start + (MINIMIZED_BUTTON_WIDTH - details_surface.get_width()) // 2
        details_text_y = button_y + (MINIMIZED_BUTTON_HEIGHT - details_surface.get_height()) // 2
        screen.blit(details_surface, (details_text_x, details_text_y))

        # Menu button
        menu_button_x = button_x_start + MINIMIZED_BUTTON_WIDTH + MINIMIZED_BUTTON_SPACING
        menu_button_rect = pygame.Rect(menu_button_x, button_y, MINIMIZED_BUTTON_WIDTH, MINIMIZED_BUTTON_HEIGHT)
        self.buttons["menu"] = menu_button_rect
        menu_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "menu" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, menu_bg_color, menu_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, menu_button_rect, 2)
        menu_text = "Menu (M)"
        menu_surface = self.small_font.render(menu_text, True, COLOR_TEXT)
        menu_text_x = menu_button_x + (MINIMIZED_BUTTON_WIDTH - menu_surface.get_width()) // 2
        menu_text_y = button_y + (MINIMIZED_BUTTON_HEIGHT - menu_surface.get_height()) // 2
        screen.blit(menu_surface, (menu_text_x, menu_text_y))

        # Exit button
        exit_button_x = menu_button_x + MINIMIZED_BUTTON_WIDTH + MINIMIZED_BUTTON_SPACING
        exit_button_rect = pygame.Rect(exit_button_x, button_y, MINIMIZED_BUTTON_WIDTH, MINIMIZED_BUTTON_HEIGHT)
        self.buttons["exit"] = exit_button_rect
        exit_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "exit" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, exit_bg_color, exit_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, exit_button_rect, 2)
        exit_text = "Exit (Q)"
        exit_surface = self.small_font.render(exit_text, True, COLOR_TEXT)
        exit_text_x = exit_button_x + (MINIMIZED_BUTTON_WIDTH - exit_surface.get_width()) // 2
        exit_text_y = button_y + (MINIMIZED_BUTTON_HEIGHT - exit_surface.get_height()) // 2
        screen.blit(exit_surface, (exit_text_x, exit_text_y))

    def _draw_full_window(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw full game over window with overlay."""
        # Draw semi-transparent overlay
        if self._overlay_cache is None or self._overlay_cache.get_size() != (screen_width, screen_height):
            self._overlay_cache = pygame.Surface((screen_width, screen_height))
            self._overlay_cache.set_alpha(200)
            self._overlay_cache.fill((0, 0, 0))
        screen.blit(self._overlay_cache, (0, 0))

        # Calculate window position (centered)
        window_x = (screen_width - WINDOW_WIDTH) // 2
        window_y = (screen_height - WINDOW_HEIGHT) // 2
        window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Draw window background
        pygame.draw.rect(screen, COLOR_WINDOW_BG, window_rect)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, window_rect, 2)

        # Draw title bar
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 60)
        title_color = COLOR_VICTORY if self.is_victory else COLOR_DEFEAT
        pygame.draw.rect(screen, COLOR_TITLE_BG, title_rect)
        pygame.draw.rect(screen, title_color, title_rect, 3)

        # Draw title text
        title_text = "VICTORY!" if self.is_victory else "DEFEAT"
        title_surface = self.large_font.render(title_text, True, title_color)
        title_x = window_x + (WINDOW_WIDTH - title_surface.get_width()) // 2
        title_y = window_y + (60 - title_surface.get_height()) // 2
        screen.blit(title_surface, (title_x, title_y))

        # Draw game results
        content_y = window_y + 80

        # Winner info - use player-specific color
        winner_color = COLOR_PLAYER1 if self.winner_player == 1 else COLOR_PLAYER2
        winner_text = f"{self.winner_name} wins with {self.winner_gp} GP!"
        winner_surface = self.font.render(winner_text, True, winner_color)
        winner_x = window_x + (WINDOW_WIDTH - winner_surface.get_width()) // 2
        screen.blit(winner_surface, (winner_x, content_y))

        # Loser info
        content_y += 40
        loser_text = f"{self.loser_name}: {self.loser_gp} GP"
        loser_surface = self.small_font.render(loser_text, True, COLOR_TEXT_DIM)
        loser_x = window_x + (WINDOW_WIDTH - loser_surface.get_width()) // 2
        screen.blit(loser_surface, (loser_x, content_y))

        # Flavor text
        content_y += 50
        if self.is_victory:
            flavor = "A tactical triumph! Your strategic prowess is unmatched."
        else:
            flavor = "Defeat, but not dishonor. Study your opponent's tactics."
        flavor_surface = self.small_font.render(flavor, True, COLOR_TEXT_DIM)
        flavor_x = window_x + (WINDOW_WIDTH - flavor_surface.get_width()) // 2
        screen.blit(flavor_surface, (flavor_x, content_y))

        # Draw buttons (3 equal-width buttons)
        button_y = window_y + WINDOW_HEIGHT - 100

        # Calculate button layout for 3 equal buttons
        # 3 * BUTTON_WIDTH + 2 * BUTTON_SPACING = 3*175 + 2*10 = 545px
        total_button_width = BUTTON_WIDTH * 3 + BUTTON_SPACING * 2
        button_x_start = window_x + (WINDOW_WIDTH - total_button_width) // 2

        self.buttons = {}  # Reset buttons dict

        # Minimize button
        minimize_button_x = button_x_start
        minimize_button_rect = pygame.Rect(minimize_button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["minimize"] = minimize_button_rect

        minimize_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "minimize" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, minimize_bg_color, minimize_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, minimize_button_rect, 2)

        minimize_text = "Minimize (R)"
        minimize_surface = self.small_font.render(minimize_text, True, COLOR_TEXT)
        minimize_text_x = minimize_button_x + (BUTTON_WIDTH - minimize_surface.get_width()) // 2
        minimize_text_y = button_y + (BUTTON_HEIGHT - minimize_surface.get_height()) // 2
        screen.blit(minimize_surface, (minimize_text_x, minimize_text_y))

        # Menu button
        menu_button_x = minimize_button_x + BUTTON_WIDTH + BUTTON_SPACING
        menu_button_rect = pygame.Rect(menu_button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["menu"] = menu_button_rect

        menu_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "menu" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, menu_bg_color, menu_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, menu_button_rect, 2)

        menu_text = "Menu (M)"
        menu_surface = self.small_font.render(menu_text, True, COLOR_TEXT)
        menu_text_x = menu_button_x + (BUTTON_WIDTH - menu_surface.get_width()) // 2
        menu_text_y = button_y + (BUTTON_HEIGHT - menu_surface.get_height()) // 2
        screen.blit(menu_surface, (menu_text_x, menu_text_y))

        # Exit button
        exit_button_x = menu_button_x + BUTTON_WIDTH + BUTTON_SPACING
        exit_button_rect = pygame.Rect(exit_button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["exit"] = exit_button_rect

        exit_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "exit" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, exit_bg_color, exit_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, exit_button_rect, 2)

        exit_text = "Exit (Q)"
        exit_surface = self.small_font.render(exit_text, True, COLOR_TEXT)
        exit_text_x = exit_button_x + (BUTTON_WIDTH - exit_surface.get_width()) // 2
        exit_text_y = button_y + (BUTTON_HEIGHT - exit_surface.get_height()) // 2
        screen.blit(exit_surface, (exit_text_x, exit_text_y))
