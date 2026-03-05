#!/usr/bin/env python3
"""
Settings Menu Screens
Screens for game settings configuration.
"""
import pygame
from typing import Optional, Tuple
from .menu_components import MenuScreen, Button, Slider, Checkbox, COLOR_TEXT
from boneglaive.utils.config import ConfigManager
from boneglaive.graphical.sound_manager import get_sound_manager
from boneglaive.utils.resolution import ResolutionPresets, Resolution


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

        # Get supported resolutions based on available screen modes
        self.supported_resolutions = self._get_supported_resolutions()

        # Get current resolution
        current_width = self.config.get('window_width', screen_width)
        current_height = self.config.get('window_height', screen_height)
        self.current_resolution = ResolutionPresets.find_preset(current_width, current_height)

        # Find current index in supported resolutions
        self.resolution_index = 0
        for i, res in enumerate(self.supported_resolutions):
            if res.width == current_width and res.height == current_height:
                self.resolution_index = i
                break

        # Track pending resolution changes
        self.pending_resolution = None

        # Get current animation speed
        current_speed = self.config.get('animation_speed', 1.0)
        speed_label = self._get_animation_speed_label(current_speed)

        # Button dimensions
        button_width = 450
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 180

        # Create resolution button
        self.resolution_button = Button(
            start_x, start_y,
            button_width, button_height,
            f"Resolution: {self.supported_resolutions[self.resolution_index]}",
            font,
            lambda: self._cycle_resolution()
        )

        # Create fullscreen toggle button
        self.fullscreen_button = Button(
            start_x, start_y + (button_height + button_spacing),
            button_width, button_height,
            f"Fullscreen: {'ON' if self.config.get('fullscreen', False) else 'OFF'}",
            font,
            lambda: self._toggle_fullscreen()
        )

        # Create animation speed button
        self.anim_speed_button = Button(
            start_x, start_y + (button_height + button_spacing) * 2,
            button_width, button_height,
            f"Animation Speed: {speed_label}",
            font,
            lambda: self._cycle_animation_speed()
        )

        # Create apply button (only visible when there are pending changes)
        self.apply_button = Button(
            start_x, start_y + (button_height + button_spacing) * 3,
            button_width, button_height,
            "Apply Resolution Changes",
            font,
            lambda: self._apply_resolution_changes()
        )
        self.apply_button.visible = False  # Hidden by default

        # Create back button
        self.back_button = Button(
            start_x, start_y + (button_height + button_spacing) * 4,
            button_width, button_height,
            "Back",
            font,
            lambda: self._set_action("back")
        )

        self.buttons = [self.resolution_button, self.fullscreen_button,
                       self.anim_speed_button, self.apply_button, self.back_button]
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

    def _get_supported_resolutions(self) -> list[Resolution]:
        """Get list of supported resolutions, filtering out those too large for display."""
        # Get all preset resolutions
        all_presets = ResolutionPresets.get_all_presets()

        # Filter to common gaming resolutions (exclude 4K for stability)
        gaming_resolutions = [
            ResolutionPresets.RES_1280x720,    # 720p HD
            ResolutionPresets.RES_1280x800,    # 16:10
            ResolutionPresets.RES_1440x900,    # 16:10
            ResolutionPresets.RES_1480x800,    # Default
            ResolutionPresets.RES_1600x900,    # HD+
            ResolutionPresets.RES_1680x1050,   # 16:10
            ResolutionPresets.RES_1920x1080,   # Full HD
            ResolutionPresets.RES_2560x1440,   # 2K
        ]

        # Get available display modes from pygame
        try:
            display_modes = pygame.display.list_modes()
            if display_modes:
                max_width = max(mode[0] for mode in display_modes)
                max_height = max(mode[1] for mode in display_modes)

                # Filter resolutions to those that fit on the display
                supported = []
                for res in gaming_resolutions:
                    if res.width <= max_width and res.height <= max_height:
                        supported.append(res)

                return supported if supported else gaming_resolutions[:3]  # Fallback to first 3
        except:
            pass

        # Default to a safe subset if we can't detect display modes
        return gaming_resolutions[:5]

    def _cycle_resolution(self):
        """Cycle through available resolutions."""
        # Move to next resolution
        self.resolution_index = (self.resolution_index + 1) % len(self.supported_resolutions)
        new_resolution = self.supported_resolutions[self.resolution_index]

        # Update button text
        self.resolution_button.text = f"Resolution: {new_resolution}"

        # Mark as pending change (don't apply immediately)
        self.pending_resolution = new_resolution

        # Show apply button
        self.apply_button.visible = True
        self.apply_button.text = f"Apply {new_resolution.width}x{new_resolution.height}"

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        current_fullscreen = self.config.get('fullscreen', False)
        new_fullscreen = not current_fullscreen

        # Update button text
        self.fullscreen_button.text = f"Fullscreen: {'ON' if new_fullscreen else 'OFF'}"

        # Save to config (fullscreen applies immediately)
        self.config.set('fullscreen', new_fullscreen)
        self.config.save_config()

        # Set action to trigger fullscreen toggle
        self._action_result = "toggle_fullscreen"

    def _apply_resolution_changes(self):
        """Apply pending resolution changes."""
        if self.pending_resolution:
            # Save new resolution to config
            self.config.set('window_width', self.pending_resolution.width)
            self.config.set('window_height', self.pending_resolution.height)
            self.config.save_config()

            # Clear pending resolution
            self.pending_resolution = None

            # Hide apply button
            self.apply_button.visible = False

            # Trigger resolution change
            self._action_result = "change_resolution"

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
