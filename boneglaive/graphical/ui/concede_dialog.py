#!/usr/bin/env python3
"""
Concede Dialog UI Component
Modal confirmation dialog shown when player attempts to concede.
"""
import pygame
from typing import Optional

# Colors
COLOR_OVERLAY = (0, 0, 0, 200)  # Dark semi-transparent overlay
COLOR_WINDOW_BG = (30, 34, 42)
COLOR_WINDOW_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_BUTTON_BG = (50, 54, 62)
COLOR_BUTTON_HOVER = (70, 74, 82)
COLOR_BUTTON_BORDER = (120, 120, 120)
COLOR_DANGER = (200, 100, 100)  # Red for concede button
COLOR_DANGER_HOVER = (220, 120, 120)

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 280
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 50
BUTTON_SPACING = 20


class ConcedeDialog:
    """Modal confirmation dialog for conceding the game."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False

        # Button state
        self.hovered_button = None  # "cancel" or "concede"
        self.buttons = {}  # {name: pygame.Rect}

        # Cache overlay surface (performance)
        self._overlay_cache = None

    def show(self):
        """Show the concede confirmation dialog."""
        self.visible = True
        self.hovered_button = None

    def hide(self):
        """Hide the concede dialog."""
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
            Action string ("cancel" or "concede") or None
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
            Action string ("cancel" or "concede") or None
        """
        if not self.visible:
            return None

        # ESC = cancel
        if key == pygame.K_ESCAPE:
            return "cancel"
        # ENTER or C = confirm concede
        elif key == pygame.K_RETURN or key == pygame.K_c:
            return "concede"

        return None

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the concede confirmation dialog."""
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

        # Draw window background
        window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, COLOR_WINDOW_BG, window_rect)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, window_rect, 2)

        # Draw title bar
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 50)
        pygame.draw.rect(screen, COLOR_TITLE_BG, title_rect)
        pygame.draw.line(screen, COLOR_WINDOW_BORDER,
                        (window_x, window_y + 50),
                        (window_x + WINDOW_WIDTH, window_y + 50), 2)

        # Draw title text
        title_text = self.font.render("Concession", True, COLOR_TEXT)
        title_rect = title_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + 25))
        screen.blit(title_text, title_rect)

        # Draw message text
        message_text = self.font.render("Forfeit and grant your opponent victory?", True, COLOR_TEXT)
        message_rect = message_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + 100))
        screen.blit(message_text, message_rect)

        # Draw buttons
        button_y = window_y + WINDOW_HEIGHT - BUTTON_HEIGHT - 20

        # Cancel button (left)
        cancel_x = window_x + (WINDOW_WIDTH // 2) - BUTTON_WIDTH - (BUTTON_SPACING // 2)
        cancel_rect = pygame.Rect(cancel_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["cancel"] = cancel_rect

        cancel_color = COLOR_BUTTON_HOVER if self.hovered_button == "cancel" else COLOR_BUTTON_BG
        pygame.draw.rect(screen, cancel_color, cancel_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, cancel_rect, 2)

        cancel_text = self.font.render("Cancel", True, COLOR_TEXT)
        cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
        screen.blit(cancel_text, cancel_text_rect)

        # Concede button (right) - red/danger color
        concede_x = window_x + (WINDOW_WIDTH // 2) + (BUTTON_SPACING // 2)
        concede_rect = pygame.Rect(concede_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["concede"] = concede_rect

        concede_color = COLOR_DANGER_HOVER if self.hovered_button == "concede" else COLOR_DANGER
        pygame.draw.rect(screen, concede_color, concede_rect)
        pygame.draw.rect(screen, COLOR_BUTTON_BORDER, concede_rect, 2)

        concede_text = self.font.render("Concede", True, COLOR_TEXT)
        concede_text_rect = concede_text.get_rect(center=concede_rect.center)
        screen.blit(concede_text, concede_text_rect)

        # Draw keyboard hints
        hint_text = self.small_font.render("ESC: Cancel  |  ENTER/C: Concede", True, COLOR_TEXT_DIM)
        hint_rect = hint_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + WINDOW_HEIGHT - 10))
        screen.blit(hint_text, hint_rect)
