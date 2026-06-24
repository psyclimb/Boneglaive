#!/usr/bin/env python3
"""
Main Menu Screen
The primary menu screen for Boneglaive graphical version.
"""
import pygame
from typing import Optional
from boneglaive import __version__
from .menu_components import MenuScreen, Button, COLOR_TEXT
from .kaleidoscope_background import KaleidoscopeBackground
from boneglaive.utils.paths import asset_path


class MainMenuScreen(MenuScreen):
    """Main menu with title and primary navigation buttons."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Boneglaive", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.use_panel = False  # Main menu uses full kaleidoscope background

        self.background = KaleidoscopeBackground(screen_width, screen_height)

        # Load Creepster horror font for title, scaled to screen height
        creepster_path = asset_path('boneglaive/graphical/assets/Creepster-Regular.ttf')
        title_size = max(48, int(screen_height * 0.12))
        try:
            self.title_font = pygame.font.Font(creepster_path, title_size)
        except Exception:
            self.title_font = large_font

        # Derive layout positions from title height so nothing overlaps
        self._title_top = int(screen_height * 0.06)
        title_h = self.title_font.render("BONEGLAIVE", True, (0, 0, 0)).get_height()
        self._version_top = self._title_top + title_h + int(screen_height * 0.01)
        buttons_top = self._version_top + font.get_height() + int(screen_height * 0.03)

        # Button dimensions, scaled to screen
        button_width = max(200, int(screen_width * 0.23))
        button_height = max(40, int(screen_height * 0.07))
        button_spacing = max(10, int(screen_height * 0.015))

        start_x = (screen_width - button_width) // 2

        # Create buttons
        self.buttons = [
            Button(
                start_x, buttons_top,
                button_width, button_height,
                "Play",
                font,
                lambda: self._set_action("play")
            ),
            Button(
                start_x, buttons_top + (button_height + button_spacing) * 1,
                button_width, button_height,
                "How to Play",
                font,
                lambda: self._set_action("how_to_play")
            ),
            Button(
                start_x, buttons_top + (button_height + button_spacing) * 2,
                button_width, button_height,
                "Settings",
                font,
                lambda: self._set_action("settings")
            ),
            Button(
                start_x, buttons_top + (button_height + button_spacing) * 3,
                button_width, button_height,
                "About",
                font,
                lambda: self._set_action("about")
            ),
            Button(
                start_x, buttons_top + (button_height + button_spacing) * 4,
                button_width, button_height,
                "Quit",
                font,
                lambda: self._set_action("quit")
            )
        ]

        self._action_result = None

    def _set_action(self, action: str):
        """Set the action result."""
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events and return action if triggered."""
        super().handle_event(event)

        # Check if action was set by button
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action

        return None

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update animated elements and buttons."""
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.background.update(delta_time)

    def draw(self, surface: pygame.Surface):
        """Draw the main menu."""
        # Draw animated background
        self.background.draw(surface)

        # Draw the title art
        self._draw_title_art(surface)

        # Draw version subtitle
        version_text = f"v{__version__}"
        version_surface = self.font.render(version_text, True, COLOR_TEXT)
        version_rect = version_surface.get_rect(centerx=self.screen_width // 2, top=self._version_top)
        surface.blit(version_surface, version_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

    def _draw_title_art(self, surface: pygame.Surface):
        """Draw the Boneglaive title using the Creepster horror font."""
        # Dark shadow for depth
        shadow_surface = self.title_font.render("BONEGLAIVE", True, (40, 0, 0))
        shadow_rect = shadow_surface.get_rect(centerx=self.screen_width // 2 + 3, top=self._title_top + 3)
        surface.blit(shadow_surface, shadow_rect)

        # Main title in blood red
        title_surface = self.title_font.render("BONEGLAIVE", True, (180, 20, 20))
        title_rect = title_surface.get_rect(centerx=self.screen_width // 2, top=self._title_top)
        surface.blit(title_surface, title_rect)
