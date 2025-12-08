#!/usr/bin/env python3
"""
About Screen
Information about the game, copyright, and license.
"""
import pygame
from typing import Optional
from .menu_components import COLOR_BG, COLOR_TEXT


class AboutScreen:
    """Screen displaying game information and license."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        self.font = font
        self.large_font = large_font
        self.screen_width = screen_width
        self.screen_height = screen_height

    def on_enter(self):
        """Called when screen becomes active."""
        pass

    def on_exit(self):
        """Called when leaving screen."""
        pass

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events - any key/click returns to menu."""
        if event.type == pygame.KEYUP or event.type == pygame.MOUSEBUTTONUP:
            return "back"
        return None

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update screen state."""
        pass

    def draw(self, surface: pygame.Surface):
        """Draw the about screen."""
        surface.fill(COLOR_BG)

        # About screen content
        lines = [
            ("Boneglaive v0.9.0b BETA", self.large_font, COLOR_TEXT, True),
            ("Tactical Turn-Based Combat Game", self.font, COLOR_TEXT, False),
            ("Beta Release", self.font, COLOR_TEXT, False),
            ("", self.font, COLOR_TEXT, False),
            ("Copyright (C) 2025 Psyclimb", self.font, (100, 200, 255), False),
            ("", self.font, COLOR_TEXT, False),
            ("This program is free software licensed under GPL-3.0", self.font, (100, 200, 255), False),
            ("This program comes with ABSOLUTELY NO WARRANTY.", self.font, COLOR_TEXT, False),
            ("", self.font, COLOR_TEXT, False),
            ("You are welcome to redistribute it under certain conditions.", self.font, COLOR_TEXT, False),
            ("See the LICENSE file for full terms.", self.font, COLOR_TEXT, False),
            ("", self.font, COLOR_TEXT, False),
            ("Source code: https://github.com/psyclimb/Boneglaive", self.font, (100, 255, 100), False),
            ("", self.font, COLOR_TEXT, False),
            ("Built with Python and Pygame", self.font, (180, 180, 180), False),
            ("", self.font, COLOR_TEXT, False),
            ("Press any key to return to menu...", self.font, (150, 150, 150), False)
        ]

        # Calculate starting position to center content
        total_height = sum(32 if bold else 24 for _, _, _, bold in lines)
        start_y = max(40, (self.screen_height - total_height) // 2)

        # Draw each line
        y_pos = start_y
        for text, font, color, bold in lines:
            if text:  # Non-empty line
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect(centerx=self.screen_width // 2, top=y_pos)
                surface.blit(text_surface, text_rect)

            # Move to next line
            y_pos += 32 if bold else 24
