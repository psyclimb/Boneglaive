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
COLOR_BUTTON_BG = (50, 54, 62)
COLOR_BUTTON_HOVER = (70, 74, 82)
COLOR_BUTTON_BORDER = (120, 120, 120)

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 60
BUTTON_SPACING = 20


class GameOverWindow:
    """Modal window shown when game ends with victory or defeat."""

    def __init__(self, font, small_font, large_font):
        self.font = font
        self.small_font = small_font
        self.large_font = large_font
        self.visible = False

        # Game over state
        self.is_victory = False
        self.winner_name = ""
        self.winner_gp = 0
        self.loser_name = ""
        self.loser_gp = 0

        # Button state
        self.hovered_button = None  # "menu" or "exit"
        self.buttons = {}  # {name: pygame.Rect}

        # Cache overlay surface (performance)
        self._overlay_cache = None

        # Callbacks
        self.on_return_to_menu: Optional[Callable] = None
        self.on_exit_game: Optional[Callable] = None

    def show(self, is_victory: bool, winner_name: str, winner_gp: int,
             loser_name: str, loser_gp: int):
        """
        Show the game over window.

        Args:
            is_victory: True if local player won, False if lost
            winner_name: Name of winning player
            winner_gp: GP score of winner
            loser_name: Name of losing player
            loser_gp: GP score of loser
        """
        self.visible = True
        self.is_victory = is_victory
        self.winner_name = winner_name
        self.winner_gp = winner_gp
        self.loser_name = loser_name
        self.loser_gp = loser_gp
        self.hovered_button = None

    def hide(self):
        """Hide the game over window."""
        self.visible = False
        self.hovered_button = None

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
            Action string ("menu" or "exit") or None
        """
        if not self.visible:
            return None

        # ESC or M = return to menu
        if key == pygame.K_ESCAPE or key == pygame.K_m:
            return "menu"
        # Q or X = exit
        elif key == pygame.K_q or key == pygame.K_x:
            return "exit"

        return None

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the game over window."""
        if not self.visible:
            return

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

        # Winner info
        winner_text = f"{self.winner_name} wins with {self.winner_gp} GP!"
        winner_surface = self.font.render(winner_text, True, COLOR_VICTORY)
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

        # Draw buttons
        button_y = window_y + WINDOW_HEIGHT - 100
        button_x_offset = (WINDOW_WIDTH - (BUTTON_WIDTH * 2 + BUTTON_SPACING)) // 2

        # Return to Menu button
        menu_button_x = window_x + button_x_offset
        menu_button_rect = pygame.Rect(menu_button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["menu"] = menu_button_rect

        menu_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "menu" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, menu_bg_color, menu_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, menu_button_rect, 2)

        menu_text = "Return to Menu (M)"
        menu_surface = self.font.render(menu_text, True, COLOR_TEXT)
        menu_text_x = menu_button_x + (BUTTON_WIDTH - menu_surface.get_width()) // 2
        menu_text_y = button_y + (BUTTON_HEIGHT - menu_surface.get_height()) // 2
        screen.blit(menu_surface, (menu_text_x, menu_text_y))

        # Exit Game button
        exit_button_x = menu_button_x + BUTTON_WIDTH + BUTTON_SPACING
        exit_button_rect = pygame.Rect(exit_button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["exit"] = exit_button_rect

        exit_bg_color = COLOR_BUTTON_HOVER if self.hovered_button == "exit" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, exit_bg_color, exit_button_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, exit_button_rect, 2)

        exit_text = "Exit Game (Q)"
        exit_surface = self.font.render(exit_text, True, COLOR_TEXT)
        exit_text_x = exit_button_x + (BUTTON_WIDTH - exit_surface.get_width()) // 2
        exit_text_y = button_y + (BUTTON_HEIGHT - exit_surface.get_height()) // 2
        screen.blit(exit_surface, (exit_text_x, exit_text_y))
