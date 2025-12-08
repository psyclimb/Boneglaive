#!/usr/bin/env python3
"""
Settings Menu Screens
Screens for game settings configuration.
"""
import pygame
from typing import Optional
from .menu_components import MenuScreen, Button, COLOR_TEXT
from boneglaive.utils.config import ConfigManager


class SettingsSubmenu(MenuScreen):
    """Submenu for settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Button dimensions
        button_width = 300
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 200

        # Create buttons
        self.buttons = [
            Button(
                start_x, start_y,
                button_width, button_height,
                "Display Settings",
                font,
                lambda: self._set_action("display_settings")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing),
                button_width, button_height,
                "Back",
                font,
                lambda: self._set_action("back")
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


class DisplaySettingsScreen(MenuScreen):
    """Screen for display-related settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Display Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()

        # Get current animation speed
        current_speed = self.config.get('animation_speed', 1.0)
        speed_label = self._get_animation_speed_label(current_speed)

        # Button dimensions
        button_width = 400
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 200

        # Create buttons
        self.anim_speed_button = Button(
            start_x, start_y,
            button_width, button_height,
            f"Animation Speed: {speed_label}",
            font,
            lambda: self._cycle_animation_speed()
        )

        self.back_button = Button(
            start_x, start_y + (button_height + button_spacing),
            button_width, button_height,
            "Back",
            font,
            lambda: self._set_action("back")
        )

        self.buttons = [self.anim_speed_button, self.back_button]
        self._action_result = None

    def _get_animation_speed_label(self, speed: float) -> str:
        """Get display label for animation speed."""
        if speed <= 0.5:
            return "Very Slow"
        elif speed <= 0.8:
            return "Slow"
        elif speed <= 1.2:
            return "Normal"
        elif speed <= 1.6:
            return "Fast"
        else:
            return "Very Fast"

    def _cycle_animation_speed(self):
        """Cycle through animation speed options."""
        # Define speed options: Very Slow, Slow, Normal, Fast, Very Fast
        speed_options = [0.5, 0.7, 1.0, 1.4, 2.0]
        current_speed = self.config.get('animation_speed', 1.0)

        # Find current index and move to next
        try:
            current_index = speed_options.index(current_speed)
            next_index = (current_index + 1) % len(speed_options)
        except ValueError:
            # If current speed isn't in our options, default to Normal (index 2)
            next_index = 2

        new_speed = speed_options[next_index]
        self.config.set('animation_speed', new_speed)
        self.config.save_config()

        # Update button text
        speed_label = self._get_animation_speed_label(new_speed)
        self.anim_speed_button.text = f"Animation Speed: {speed_label}"

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
