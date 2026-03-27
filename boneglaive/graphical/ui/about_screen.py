#!/usr/bin/env python3
"""
About Screen
Information about the game, copyright, and license.
"""
import pygame
from typing import Optional
from .menu_components import COLOR_BG, COLOR_TEXT, COLOR_BONE, draw_glaive_icon, COLOR_METAL


class AboutScreen:
    """Screen displaying game information and license."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        self.font = font
        self.large_font = large_font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.activation_timer = 0.0

    def on_enter(self):
        """Called when screen becomes active."""
        self.activation_timer = 0.0  # Reset timer when entering screen

    def on_exit(self):
        """Called when leaving screen."""
        pass

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events - any key/click returns to menu."""
        # Only accept input after 200ms to prevent click-through
        if self.activation_timer < 0.2:
            return None

        if event.type == pygame.KEYUP and event.key != pygame.K_ESCAPE:
            # Any key except ESC (ESC is handled by base MenuScreen class)
            return "back"
        elif event.type == pygame.MOUSEBUTTONUP:
            return "back"
        return None

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update screen state."""
        self.activation_timer += delta_time

    def draw(self, surface: pygame.Surface):
        """Draw the about screen."""
        surface.fill(COLOR_BG)

        # Draw decorative corner glaives
        width = surface.get_width()
        height = surface.get_height()
        draw_glaive_icon(surface, 40, 40, COLOR_METAL, length=60, pointing_right=True)
        draw_glaive_icon(surface, width - 100, 40, COLOR_METAL, length=60, pointing_right=False)

        # About screen content with improved spacing
        # Format: (text, font, color, line_height_multiplier)
        lines = [
            ("Boneglaive v1.0", self.large_font, COLOR_TEXT, 2.5),
            ("Tactical Turn-Based Combat Game", self.font, COLOR_TEXT, 1.2),
            ("", self.font, COLOR_TEXT, 1.8),
            ("Copyright (C) 2026 Psyclimb", self.font, (100, 200, 255), 2.0),
            ("This program is free software licensed under GPL-3.0", self.font, (100, 200, 255), 1.2),
            ("This program comes with ABSOLUTELY NO WARRANTY.", self.font, COLOR_TEXT, 2.0),
            ("You are welcome to redistribute it under certain conditions.", self.font, COLOR_TEXT, 1.0),
            ("See the LICENSE file for full terms.", self.font, COLOR_TEXT, 2.0),
            ("Source code: https://github.com/psyclimb/Boneglaive", self.font, (100, 255, 100), 2.0),
            ("Built with Python and Pygame", self.font, (180, 180, 180), 2.5),
            ("Press any key to return to menu...", self.font, (150, 150, 150), 1.0)
        ]

        # Calculate base line height
        base_line_height = self.font.get_height()

        # Calculate starting position - significantly higher than center
        total_height = sum(base_line_height * multiplier for _, _, _, multiplier in lines)
        start_y = max(100, (self.screen_height - total_height) // 2 - 80)

        # Draw each line
        y_pos = start_y
        for text, font, color, line_height_multiplier in lines:
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(centerx=self.screen_width // 2, top=y_pos)
            surface.blit(text_surface, text_rect)

            # Move to next line with spacing
            y_pos += int(base_line_height * line_height_multiplier)
