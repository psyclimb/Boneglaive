#!/usr/bin/env python3
"""
Setup Exit Dialog UI Component
Modal confirmation dialog shown when player presses ESC on the unit select screen.
"""
import pygame
from typing import Optional

# Colors - matching the bone/industrial theme
COLOR_OVERLAY = (0, 0, 0, 200)
COLOR_WINDOW_BG_TOP = (42, 42, 47)
COLOR_WINDOW_BG_BOTTOM = (26, 26, 31)
COLOR_WINDOW_BORDER = (90, 84, 79)
COLOR_TITLE_BG_TOP = (50, 50, 55)
COLOR_TITLE_BG_BOTTOM = (38, 38, 43)
COLOR_TEXT = (240, 232, 216)
COLOR_TEXT_DIM = (180, 160, 165)
COLOR_BUTTON_TOP = (74, 74, 79)
COLOR_BUTTON_BOTTOM = (50, 50, 55)
COLOR_BUTTON_HOVER_TOP = (90, 74, 79)
COLOR_BUTTON_HOVER_BOTTOM = (64, 48, 53)
COLOR_BORDER_HOVER = (184, 168, 149)
COLOR_BORDER_GLOW = (255, 170, 119)

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 280
BUTTON_WIDTH = 175
BUTTON_HEIGHT = 60
BUTTON_SPACING = 10


class SetupExitDialog:
    """Modal dialog shown when ESC is pressed during unit selection."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False

        self.hovered_button = None  # "cancel", "main_menu", or "quit"
        self.buttons = {}  # {name: pygame.Rect}

        self._overlay_cache = None

    def show(self):
        """Show the dialog."""
        self.visible = True
        self.hovered_button = None

    def hide(self):
        """Hide the dialog."""
        self.visible = False
        self.hovered_button = None

    def handle_mouse_motion(self, mouse_pos: tuple):
        """Update hovered button."""
        if not self.visible:
            return

        self.hovered_button = None
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                self.hovered_button = button_name
                break

    def handle_mouse_click(self, mouse_pos: tuple) -> Optional[str]:
        """
        Handle mouse click.

        Returns:
            "cancel", "main_menu", "quit", or None
        """
        if not self.visible:
            return None

        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                return button_name

        return None

    def handle_key(self, key: int) -> Optional[str]:
        """
        Handle keyboard input.

        Returns:
            "cancel", "main_menu", "quit", or None
        """
        if not self.visible:
            return None

        if key == pygame.K_ESCAPE:
            return "cancel"

        return None

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the exit dialog."""
        if not self.visible:
            return

        from .menu_components import draw_gradient_rect, draw_glow_rect, draw_bone_corner

        # Draw semi-transparent overlay
        if self._overlay_cache is None or self._overlay_cache.get_size() != (screen_width, screen_height):
            self._overlay_cache = pygame.Surface((screen_width, screen_height))
            self._overlay_cache.set_alpha(200)
            self._overlay_cache.fill((0, 0, 0))
        screen.blit(self._overlay_cache, (0, 0))

        # Window position (centered)
        window_x = (screen_width - WINDOW_WIDTH) // 2
        window_y = (screen_height - WINDOW_HEIGHT) // 2
        window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Shadow
        shadow_rect = window_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 120), shadow_surf.get_rect(), border_radius=8)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Window background
        draw_gradient_rect(screen, window_rect, COLOR_WINDOW_BG_TOP, COLOR_WINDOW_BG_BOTTOM)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, window_rect, 3, border_radius=8)

        # Bone corner decorations
        padding = 8
        corner_radius = 6
        draw_bone_corner(screen, window_x + padding, window_y + padding, corner_radius)
        draw_bone_corner(screen, window_x + WINDOW_WIDTH - padding, window_y + padding, corner_radius)
        draw_bone_corner(screen, window_x + padding, window_y + WINDOW_HEIGHT - padding, corner_radius)
        draw_bone_corner(screen, window_x + WINDOW_WIDTH - padding, window_y + WINDOW_HEIGHT - padding, corner_radius)

        # Title bar
        title_bar_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 60)
        draw_gradient_rect(screen, title_bar_rect, COLOR_TITLE_BG_TOP, COLOR_TITLE_BG_BOTTOM)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, title_bar_rect, 3)

        # Title text
        title_text = self.font.render("Leave Setup", True, COLOR_TEXT)
        title_x = window_x + (WINDOW_WIDTH - title_text.get_width()) // 2
        title_y = window_y + (60 - title_text.get_height()) // 2
        screen.blit(title_text, (title_x, title_y))

        # Message text
        message_text = self.font.render("Return to the main menu or exit the game?", True, COLOR_TEXT_DIM)
        message_x = window_x + (WINDOW_WIDTH - message_text.get_width()) // 2
        message_y = window_y + 100
        screen.blit(message_text, (message_x, message_y))

        # Three buttons: Cancel | Main Menu | Exit Game
        button_y = window_y + WINDOW_HEIGHT - BUTTON_HEIGHT - 20
        total_button_width = BUTTON_WIDTH * 3 + BUTTON_SPACING * 2
        button_x_start = window_x + (WINDOW_WIDTH - total_button_width) // 2

        button_defs = [
            ("cancel", "Cancel", button_x_start),
            ("main_menu", "Main Menu", button_x_start + BUTTON_WIDTH + BUTTON_SPACING),
            ("quit", "Exit Game", button_x_start + (BUTTON_WIDTH + BUTTON_SPACING) * 2),
        ]

        self.buttons = {}
        for button_name, button_label, bx in button_defs:
            button_rect = pygame.Rect(bx, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            self.buttons[button_name] = button_rect

            # Shadow
            shadow_rect = button_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
            screen.blit(shadow_surf, shadow_rect.topleft)

            # Background gradient
            if self.hovered_button == button_name:
                draw_gradient_rect(screen, button_rect, COLOR_BUTTON_HOVER_TOP, COLOR_BUTTON_HOVER_BOTTOM)
                draw_glow_rect(screen, button_rect, COLOR_BORDER_GLOW, intensity=0.5, width=1)
                border_color = COLOR_BORDER_HOVER
            else:
                draw_gradient_rect(screen, button_rect, COLOR_BUTTON_TOP, COLOR_BUTTON_BOTTOM)
                border_color = COLOR_WINDOW_BORDER
            pygame.draw.rect(screen, border_color, button_rect, 2, border_radius=5)

            # Label
            label_surf = self.font.render(button_label, True, COLOR_TEXT)
            label_x = bx + (BUTTON_WIDTH - label_surf.get_width()) // 2
            label_y = button_y + (BUTTON_HEIGHT - label_surf.get_height()) // 2
            screen.blit(label_surf, (label_x, label_y))
