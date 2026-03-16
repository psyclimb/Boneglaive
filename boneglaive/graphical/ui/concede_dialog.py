#!/usr/bin/env python3
"""
Concede Dialog UI Component
Modal confirmation dialog shown when player attempts to concede.
"""
import pygame
from typing import Optional

# Colors - matching game over window bone/industrial theme
COLOR_OVERLAY = (0, 0, 0, 200)  # Dark semi-transparent overlay
COLOR_WINDOW_BG_TOP = (42, 42, 47)  # Panel top
COLOR_WINDOW_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_WINDOW_BORDER = (90, 84, 79)  # Metal border
COLOR_TITLE_BG_TOP = (50, 50, 55)  # Title bar gradient top
COLOR_TITLE_BG_BOTTOM = (38, 38, 43)  # Title bar gradient bottom
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_BUTTON_TOP = (74, 74, 79)  # Button gradient top
COLOR_BUTTON_BOTTOM = (50, 50, 55)  # Button gradient bottom
COLOR_BUTTON_HOVER_TOP = (90, 74, 79)  # Button hover gradient top
COLOR_BUTTON_HOVER_BOTTOM = (64, 48, 53)  # Button hover gradient bottom
COLOR_BORDER_HOVER = (184, 168, 149)  # Bone border on hover
COLOR_BORDER_GLOW = (255, 170, 119)  # Orange glow
COLOR_DANGER_TOP = (180, 60, 60)  # Red gradient top for concede button
COLOR_DANGER_BOTTOM = (130, 40, 40)  # Red gradient bottom
COLOR_DANGER_HOVER_TOP = (200, 80, 80)  # Red hover gradient top
COLOR_DANGER_HOVER_BOTTOM = (150, 60, 60)  # Red hover gradient bottom

WINDOW_WIDTH = 600  # Increased from 500 to fit text
WINDOW_HEIGHT = 280
BUTTON_WIDTH = 175  # Increased to match game over window
BUTTON_HEIGHT = 60  # Increased to match game over window
BUTTON_SPACING = 10  # Reduced to match game over window


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

        # Import gradient helpers
        from .menu_components import draw_gradient_rect, draw_glow_rect

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

        # Draw shadow for window
        shadow_rect = window_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 120), shadow_surf.get_rect(), border_radius=8)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Draw window background with gradient
        draw_gradient_rect(screen, window_rect, COLOR_WINDOW_BG_TOP, COLOR_WINDOW_BG_BOTTOM)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, window_rect, 3, border_radius=8)

        # Draw title bar with gradient
        title_bar_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 60)
        draw_gradient_rect(screen, title_bar_rect, COLOR_TITLE_BG_TOP, COLOR_TITLE_BG_BOTTOM)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, title_bar_rect, 3)

        # Draw title text
        title_text = self.font.render("Concession", True, COLOR_TEXT)
        title_x = window_x + (WINDOW_WIDTH - title_text.get_width()) // 2
        title_y = window_y + (60 - title_text.get_height()) // 2
        screen.blit(title_text, (title_x, title_y))

        # Draw message text (now centered properly in wider window)
        message_text = self.font.render("Forfeit and grant your opponent victory?", True, COLOR_TEXT)
        message_x = window_x + (WINDOW_WIDTH - message_text.get_width()) // 2
        message_y = window_y + 110
        screen.blit(message_text, (message_x, message_y))

        # Draw buttons
        button_y = window_y + WINDOW_HEIGHT - BUTTON_HEIGHT - 20

        # Calculate button layout for 2 buttons
        total_button_width = BUTTON_WIDTH * 2 + BUTTON_SPACING
        button_x_start = window_x + (WINDOW_WIDTH - total_button_width) // 2

        # Cancel button (left)
        cancel_x = button_x_start
        cancel_rect = pygame.Rect(cancel_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["cancel"] = cancel_rect

        # Shadow
        shadow_rect = cancel_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Gradient
        if self.hovered_button == "cancel":
            draw_gradient_rect(screen, cancel_rect, COLOR_BUTTON_HOVER_TOP, COLOR_BUTTON_HOVER_BOTTOM)
            draw_glow_rect(screen, cancel_rect, COLOR_BORDER_GLOW, intensity=0.5, width=1)
            border_color = COLOR_BORDER_HOVER
        else:
            draw_gradient_rect(screen, cancel_rect, COLOR_BUTTON_TOP, COLOR_BUTTON_BOTTOM)
            border_color = COLOR_WINDOW_BORDER
        pygame.draw.rect(screen, border_color, cancel_rect, 2, border_radius=5)

        cancel_text = self.font.render("Cancel", True, COLOR_TEXT)
        cancel_text_x = cancel_x + (BUTTON_WIDTH - cancel_text.get_width()) // 2
        cancel_text_y = button_y + (BUTTON_HEIGHT - cancel_text.get_height()) // 2
        screen.blit(cancel_text, (cancel_text_x, cancel_text_y))

        # Concede button (right) - red/danger gradient
        concede_x = cancel_x + BUTTON_WIDTH + BUTTON_SPACING
        concede_rect = pygame.Rect(concede_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.buttons["concede"] = concede_rect

        # Shadow
        shadow_rect = concede_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Red gradient for danger button
        if self.hovered_button == "concede":
            draw_gradient_rect(screen, concede_rect, COLOR_DANGER_HOVER_TOP, COLOR_DANGER_HOVER_BOTTOM)
            draw_glow_rect(screen, concede_rect, COLOR_BORDER_GLOW, intensity=0.5, width=1)
            border_color = COLOR_BORDER_HOVER
        else:
            draw_gradient_rect(screen, concede_rect, COLOR_DANGER_TOP, COLOR_DANGER_BOTTOM)
            border_color = COLOR_WINDOW_BORDER
        pygame.draw.rect(screen, border_color, concede_rect, 2, border_radius=5)

        concede_text = self.font.render("Concede", True, COLOR_TEXT)
        concede_text_x = concede_x + (BUTTON_WIDTH - concede_text.get_width()) // 2
        concede_text_y = button_y + (BUTTON_HEIGHT - concede_text.get_height()) // 2
        screen.blit(concede_text, (concede_text_x, concede_text_y))
