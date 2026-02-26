#!/usr/bin/env python3
"""
Settings Menu Screens
Screens for game settings configuration.
"""
import pygame
from typing import Optional
from .menu_components import MenuScreen, Button, Slider, Checkbox, COLOR_TEXT
from boneglaive.utils.config import ConfigManager
from boneglaive.graphical.sound_manager import get_sound_manager


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
                "Sound Settings",
                font,
                lambda: self._set_action("sound_settings")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 2,
                button_width, button_height,
                "Interface Settings",
                font,
                lambda: self._set_action("interface_settings")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 3,
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

class InterfaceSettingsScreen(MenuScreen):
    """Screen for interface-related settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Interface Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()

        # Get current UI layout
        current_layout = self.config.get('ui_layout', 'default')
        layout_label = self._get_layout_label(current_layout)

        # Button dimensions
        button_width = 400
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 200

        # Create buttons
        self.layout_button = Button(
            start_x, start_y,
            button_width, button_height,
            f"UI Layout: {layout_label}",
            font,
            lambda: self._toggle_layout()
        )

        self.back_button = Button(
            start_x, start_y + (button_height + button_spacing),
            button_width, button_height,
            "Back",
            font,
            lambda: self._set_action("back")
        )

        self.buttons = [self.layout_button, self.back_button]
        self._action_result = None

    def _get_layout_label(self, layout: str) -> str:
        """Get display label for UI layout."""
        if layout == "reversed":
            return "Reversed"
        else:
            return "Default"

    def _toggle_layout(self):
        """Toggle between default and reversed UI layout."""
        current_layout = self.config.get('ui_layout', 'default')
        new_layout = "reversed" if current_layout == "default" else "default"

        # Set the new value directly on the config object
        setattr(self.config.config, 'ui_layout', new_layout)
        self.config.save_config()

        # Update button text
        layout_label = self._get_layout_label(new_layout)
        self.layout_button.text = f"UI Layout: {layout_label}"

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


class SoundSettingsScreen(MenuScreen):
    """Screen for sound-related settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Sound Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()
        self.sound_manager = get_sound_manager()

        # Get current sound settings
        current_volume = self.config.get('sfx_volume', 1.0)
        audio_enabled = self.config.get('audio_enabled', True)

        # Component dimensions
        slider_width = 300
        slider_height = 30
        checkbox_size = 30
        spacing = 60

        # Calculate positions
        center_x = screen_width // 2
        start_y = 250

        # Create volume slider
        self.volume_slider = Slider(
            center_x - slider_width // 2,
            start_y,
            slider_width,
            slider_height,
            min_value=0.0,
            max_value=1.0,
            initial_value=current_volume,
            on_change=self._on_volume_change,
            label="Master Volume",
            font=font
        )

        # Create mute checkbox
        self.mute_checkbox = Checkbox(
            center_x - 100,
            start_y + spacing,
            checkbox_size,
            "Mute All Sounds",
            font,
            initial_checked=not audio_enabled,
            on_change=self._on_mute_change
        )

        # Create back button
        button_width = 300
        button_height = 60
        self.back_button = Button(
            (screen_width - button_width) // 2,
            start_y + spacing * 3,
            button_width,
            button_height,
            "Back",
            font,
            lambda: self._set_action("back")
        )

        # Build button list for base class (exclude slider and checkbox as they have custom handling)
        self.buttons = [self.back_button]
        self._action_result = None

    def _on_volume_change(self, value: float):
        """Handle volume slider change."""
        # Update config
        self.config.set('sfx_volume', value)
        self.config.save_config()

        # Update sound manager
        self.sound_manager.set_volume("master", value)

    def _on_mute_change(self, muted: bool):
        """Handle mute checkbox change."""
        audio_enabled = not muted

        # Update config
        self.config.set('audio_enabled', audio_enabled)
        self.config.save_config()

        # Update sound manager
        if audio_enabled:
            self.sound_manager.enable()
        else:
            self.sound_manager.disable()

    def _set_action(self, action: str):
        """Set the action result."""
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events and return action if triggered."""
        # Handle checkbox clicks
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mute_checkbox.handle_click(event.pos)

        # Handle base class events (buttons, ESC)
        result = super().handle_event(event)
        if result:
            return result

        # Check if action was set by button
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action

        return None

    def update(self, delta_time: float, mouse_pos: tuple, mouse_pressed: bool):
        """Update screen state."""
        # Update slider
        self.volume_slider.update(mouse_pos, mouse_pressed)

        # Update checkbox
        self.mute_checkbox.update(mouse_pos, mouse_pressed)

        # Update buttons
        super().update(delta_time, mouse_pos, mouse_pressed)

    def draw(self, surface: pygame.Surface):
        """Draw the screen."""
        # Call parent to draw background and title
        super().draw(surface)

        # Draw slider
        self.volume_slider.draw(surface)

        # Draw checkbox
        self.mute_checkbox.draw(surface)

        # Buttons are drawn by parent class
