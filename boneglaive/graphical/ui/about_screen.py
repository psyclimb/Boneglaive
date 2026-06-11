#!/usr/bin/env python3
"""
About Screen
Information about the game, copyright, and license.
"""
import pygame
from typing import Optional
from .menu_components import (
    MenuScreen, MenuPanel, COLOR_TEXT,
    menu_button_width
)


class AboutScreen(MenuScreen):
    """Screen displaying game information and license."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("About", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.use_panel = False
        self.activation_timer = 0.0
        self.buttons = []

    def on_enter(self):
        self.activation_timer = 0.0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.activation_timer < 0.2:
            return None
        if event.type == pygame.KEYUP and event.key != pygame.K_ESCAPE:
            return "back"
        elif event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            return "back"
        elif event.type == pygame.MOUSEBUTTONUP:
            return "back"
        return None

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.activation_timer += delta_time

    def draw(self, surface: pygame.Surface):
        self._draw_dimmed_background(surface)
        self._draw_background_decorations(surface)

        # Draw content panel
        panel_w = max(500, int(self.screen_width * 0.55))
        panel_h = int(self.screen_height * 0.7)
        panel_x = (self.screen_width - panel_w) // 2
        panel_y = int(self.screen_height * 0.18)
        panel = MenuPanel(panel_x, panel_y, panel_w, panel_h, "About")
        panel.draw(surface, self.large_font)

        # Content lines: (text, color)
        lines = [
            ("Boneglaive v1.2", COLOR_TEXT),
            ("Tactical Turn-Based Combat Game", COLOR_TEXT),
            ("", None),
            ("Copyright (C) 2026 Psyclimb", (100, 200, 255)),
            ("Source code: GNU GPL v3.0", (100, 200, 255)),
            ("Game assets copyright (C) 2026 Psyclimb.", (100, 200, 255)),
            ("All rights reserved.", (100, 200, 255)),
            ("", None),
            ("This program comes with ABSOLUTELY NO WARRANTY.", COLOR_TEXT),
            ("You are welcome to redistribute the source", COLOR_TEXT),
            ("under certain conditions. See LICENSE", COLOR_TEXT),
            ("and ASSETS_LICENSE.md for full terms.", COLOR_TEXT),
            ("", None),
            ("https://github.com/psyclimb/Boneglaive", (100, 255, 100)),
            ("", None),
            ("Built with Python and Pygame", (180, 180, 180)),
        ]

        line_height = max(18, int(self.screen_height * 0.035))
        content_y = panel_y + 90

        for text, color in lines:
            if text and color:
                text_surface = self.font.render(text, True, color)
                text_rect = text_surface.get_rect(centerx=self.screen_width // 2, top=content_y)
                surface.blit(text_surface, text_rect)
            content_y += line_height

        # Hint at bottom
        hint = "Press any key to return..."
        hint_surface = self.font.render(hint, True, (150, 150, 150))
        hint_rect = hint_surface.get_rect(
            centerx=self.screen_width // 2,
            bottom=self.screen_height - int(self.screen_height * 0.06)
        )
        surface.blit(hint_surface, hint_rect)
