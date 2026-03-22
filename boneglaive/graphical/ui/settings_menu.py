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

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Use shared kaleidoscope background
        self.background = shared_background
        self.background_alpha = 0.15  # Very dim

        # Button dimensions
        button_width = 500
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 250

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
                lambda: self._set_action("back"),
                glaive_direction="left"
            )
        ]

        self._action_result = None

    def _set_action(self, action: str):
        """Set the action result."""
        self._action_result = action

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update screen state."""
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.background.update(delta_time)

    def draw(self, surface: pygame.Surface):
        """Draw the menu with dimmed background."""
        # Draw dimmed kaleidoscope
        self.background.draw(surface)

        # Draw dark overlay to dim it
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, int(255 * (1.0 - self.background_alpha))))
        surface.blit(overlay, (0, 0))

        # Draw menu elements
        super().draw(surface)

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

        # Available resolutions (16:9 or similar aspect ratios)
        self.resolutions = [
            (1280, 720),    # 720p - Default
            (1366, 768),    # Common laptop
            (1480, 800),    # Alternative
            (1600, 900),    # HD+
            (1920, 1080),   # 1080p
            (2560, 1440),   # 1440p
        ]

        # Find current resolution index
        current_width = self.config.get('window_width', 1280)
        current_height = self.config.get('window_height', 720)
        self.current_resolution_index = 0  # Default to 1280x720
        for i, (w, h) in enumerate(self.resolutions):
            if w == current_width and h == current_height:
                self.current_resolution_index = i
                break

        self.original_resolution = (current_width, current_height)

        # Get current fullscreen setting
        self.fullscreen = self.config.get('fullscreen', False)
        self.original_fullscreen = self.fullscreen

        # Button dimensions
        button_width = 500
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 200  # Moved up to make room for fullscreen button

        # Create resolution button
        current_res = self.resolutions[self.current_resolution_index]
        self.resolution_button = Button(
            start_x, start_y,
            button_width, button_height,
            f"Resolution: {current_res[0]}x{current_res[1]}",
            font,
            lambda: self._cycle_resolution()
        )

        # Create fullscreen button
        self.fullscreen_button = Button(
            start_x, start_y + (button_height + button_spacing),
            button_width, button_height,
            f"Fullscreen: {'On' if self.fullscreen else 'Off'}",
            font,
            lambda: self._toggle_fullscreen()
        )

        # Create apply button
        self.apply_button = Button(
            start_x, start_y + (button_height + button_spacing) * 2,
            button_width, button_height,
            "Apply Changes",
            font,
            lambda: self._apply_settings()
        )

        # Create back button
        self.back_button = Button(
            start_x, start_y + (button_height + button_spacing) * 3,
            button_width, button_height,
            "Back",
            font,
            lambda: self._set_action("back"),
            glaive_direction="left"
        )

        self.buttons = [self.resolution_button, self.fullscreen_button, self.apply_button, self.back_button]
        self._action_result = None

    def _cycle_resolution(self):
        """Cycle to next resolution."""
        self.current_resolution_index = (self.current_resolution_index + 1) % len(self.resolutions)
        current_res = self.resolutions[self.current_resolution_index]
        self.resolution_button.text = f"Resolution: {current_res[0]}x{current_res[1]}"

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        self.fullscreen_button.text = f"Fullscreen: {'On' if self.fullscreen else 'Off'}"

    def _apply_settings(self):
        """Save display settings and signal the menu manager to apply them live."""
        current_res = self.resolutions[self.current_resolution_index]

        # Persist to config
        self.config.set('window_width', current_res[0])
        self.config.set('window_height', current_res[1])
        self.config.set('fullscreen', self.fullscreen)
        self.config.save_config()

        self.original_resolution = current_res
        self.original_fullscreen = self.fullscreen

        # Signal menu manager to reinitialise the display immediately
        self._set_action("apply_display")

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
        button_width = 500
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 300

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
            lambda: self._set_action("back"),
            glaive_direction="left"
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

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Sound Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()
        self.sound_manager = get_sound_manager()

        # Use shared kaleidoscope background
        self.background = shared_background
        self.background_alpha = 0.15  # Very dim

        # Disable auto-panel, we'll draw manually
        self.use_panel = False

        # Get current sound settings
        current_volume = self.config.get('sfx_volume', 1.0)
        audio_enabled = self.config.get('audio_enabled', True)

        # Component dimensions
        slider_width = 300
        slider_height = 30
        checkbox_size = 30
        spacing = 70

        # Calculate positions (more compact layout)
        center_x = screen_width // 2
        panel_start_y = 200
        content_start_y = panel_start_y + 140  # Space for title

        # Create volume slider
        self.volume_slider = Slider(
            center_x - slider_width // 2,
            content_start_y,
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
            content_start_y + spacing,
            checkbox_size,
            "Mute All Sounds",
            font,
            initial_checked=not audio_enabled,
            on_change=self._on_mute_change
        )

        # Create back button
        button_width = 400
        button_height = 60
        self.back_button = Button(
            (screen_width - button_width) // 2,
            content_start_y + spacing * 2 + 20,
            button_width,
            button_height,
            "Back",
            font,
            lambda: self._set_action("back"),
            glaive_direction="left"
        )

        # Build button list for base class (exclude slider and checkbox as they have custom handling)
        self.buttons = [self.back_button]
        self._action_result = None

        # Store panel dimensions for manual drawing
        self.panel_y = panel_start_y
        self.panel_height = (content_start_y + spacing * 2 + 20 + button_height) - panel_start_y + 40

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
        # Update background animation
        self.background.update(delta_time)

        # Update slider
        self.volume_slider.update(mouse_pos, mouse_pressed)

        # Update checkbox
        self.mute_checkbox.update(mouse_pos, mouse_pressed)

        # Update buttons
        super().update(delta_time, mouse_pos, mouse_pressed)

    def draw(self, surface: pygame.Surface):
        """Draw the screen with manual panel."""
        import pygame
        from .menu_components import MenuPanel, COLOR_BG

        # Draw dimmed kaleidoscope
        self.background.draw(surface)

        # Draw dark overlay to dim it
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, int(255 * (1.0 - self.background_alpha))))
        surface.blit(overlay, (0, 0))

        # Draw decorative background elements
        self._draw_background_decorations(surface)

        # Draw manual panel
        panel_width = 500
        panel_x = (self.screen_width - panel_width) // 2
        panel = MenuPanel(panel_x, self.panel_y, panel_width, self.panel_height, self.title)
        panel.draw(surface, self.large_font)

        # Draw slider
        self.volume_slider.draw(surface)

        # Draw checkbox
        self.mute_checkbox.draw(surface)

        # Draw button
        self.back_button.draw(surface)

        # Draw bottom decorations
        self._draw_bottom_decorations(surface)
