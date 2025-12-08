#!/usr/bin/env python3
"""
Main Menu Screen
The primary menu screen for Boneglaive graphical version.
"""
import pygame
from typing import Optional
from .menu_components import MenuScreen, Button, COLOR_BG, COLOR_TEXT
from boneglaive.game.player_profile import profile_manager


class MainMenuScreen(MenuScreen):
    """Main menu with title and primary navigation buttons."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Boneglaive", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Button dimensions
        button_width = 300
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 300

        # Create buttons
        self.buttons = [
            Button(
                start_x, start_y,
                button_width, button_height,
                "Play",
                font,
                lambda: self._set_action("play")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 1,
                button_width, button_height,
                "Profile",
                font,
                lambda: self._set_action("profile")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 2,
                button_width, button_height,
                "Settings",
                font,
                lambda: self._set_action("settings")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 3,
                button_width, button_height,
                "About",
                font,
                lambda: self._set_action("about")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 4,
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

    def draw(self, surface: pygame.Surface):
        """Draw the main menu."""
        # Clear background
        surface.fill(COLOR_BG)

        # Draw ASCII art title
        self._draw_title_art(surface)

        # Draw version subtitle
        version_text = "v0.9.0b BETA"
        version_surface = self.font.render(version_text, True, COLOR_TEXT)
        version_rect = version_surface.get_rect(centerx=self.screen_width // 2, top=240)
        surface.blit(version_surface, version_rect)

        # Draw profile indicator (top-right corner)
        profile = profile_manager.get_current_profile()
        if profile:
            profile_text = f"Profile: {profile.name}"
            profile_surface = self.font.render(profile_text, True, (100, 200, 255))
            profile_rect = profile_surface.get_rect(right=self.screen_width - 20, top=20)
            surface.blit(profile_surface, profile_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # Draw controls hint
        hint_text = "Use mouse or keyboard to navigate"
        hint_surface = self.font.render(hint_text, True, (150, 150, 150))
        hint_rect = hint_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 20)
        surface.blit(hint_surface, hint_rect)

    def _draw_title_art(self, surface: pygame.Surface):
        """Draw the Boneglaive title in large text."""
        # For now, use a simple large text title
        # Could be enhanced with actual ASCII art later
        title_font = pygame.font.Font(None, 72)
        title_surface = title_font.render("BONEGLAIVE", True, (100, 200, 255))
        title_rect = title_surface.get_rect(centerx=self.screen_width // 2, top=100)
        surface.blit(title_surface, title_rect)

        # Draw subtitle
        subtitle_font = pygame.font.Font(None, 36)
        subtitle_surface = subtitle_font.render("Tactical Turn-Based Combat", True, (180, 180, 180))
        subtitle_rect = subtitle_surface.get_rect(centerx=self.screen_width // 2, top=180)
        surface.blit(subtitle_surface, subtitle_rect)
