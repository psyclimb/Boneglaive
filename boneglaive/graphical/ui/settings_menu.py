#!/usr/bin/env python3
"""
Settings Menu Screens
Screens for game settings configuration.
"""
import pygame
from typing import Optional
from .menu_components import (
    MenuScreen, MenuPanel, Button, Slider, Checkbox, COLOR_TEXT,
    menu_button_width, menu_button_height, menu_button_spacing, menu_start_y
)
from boneglaive.utils.config import ConfigManager
from boneglaive.graphical.sound_manager import get_sound_manager


class SettingsSubmenu(MenuScreen):
    """Submenu for settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background

        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        start_x = (screen_width - button_w) // 2
        start_y = menu_start_y(screen_height)

        self.buttons = [
            Button(start_x, start_y, button_w, button_h, "Display Settings", font,
                   lambda: self._set_action("display_settings")),
            Button(start_x, start_y + (button_h + spacing), button_w, button_h, "Sound Settings", font,
                   lambda: self._set_action("sound_settings")),
            Button(start_x, start_y + (button_h + spacing) * 2, button_w, button_h, "Interface Settings", font,
                   lambda: self._set_action("interface_settings")),
            Button(start_x, start_y + (button_h + spacing) * 3, button_w, button_h, "Back", font,
                   lambda: self._set_action("back"), glaive_direction="left"),
        ]
        self._action_result = None

    def _set_action(self, action: str):
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        super().handle_event(event)
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None


class DisplaySettingsScreen(MenuScreen):
    """Screen for display-related settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Display Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.config = ConfigManager()

        self.resolutions = [
            (1280, 720), (1366, 768), (1480, 800),
            (1600, 900), (1920, 1080), (2560, 1440),
        ]

        current_width = self.config.get('window_width', 1280)
        current_height = self.config.get('window_height', 720)
        self.current_resolution_index = 0
        for i, (w, h) in enumerate(self.resolutions):
            if w == current_width and h == current_height:
                self.current_resolution_index = i
                break

        self.original_resolution = (current_width, current_height)
        self.fullscreen = self.config.get('fullscreen', False)
        self.original_fullscreen = self.fullscreen

        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        start_x = (screen_width - button_w) // 2
        start_y = menu_start_y(screen_height)

        current_res = self.resolutions[self.current_resolution_index]
        self.resolution_button = Button(
            start_x, start_y, button_w, button_h,
            f"Resolution: {current_res[0]}x{current_res[1]}", font,
            lambda: self._cycle_resolution()
        )
        self.fullscreen_button = Button(
            start_x, start_y + (button_h + spacing), button_w, button_h,
            f"Fullscreen: {'On' if self.fullscreen else 'Off'}", font,
            lambda: self._toggle_fullscreen()
        )
        self.apply_button = Button(
            start_x, start_y + (button_h + spacing) * 2, button_w, button_h,
            "Apply Changes", font, lambda: self._apply_settings()
        )
        self.back_button = Button(
            start_x, start_y + (button_h + spacing) * 3, button_w, button_h,
            "Back", font, lambda: self._set_action("back"), glaive_direction="left"
        )

        self.buttons = [self.resolution_button, self.fullscreen_button, self.apply_button, self.back_button]
        self._action_result = None

    def _cycle_resolution(self):
        self.current_resolution_index = (self.current_resolution_index + 1) % len(self.resolutions)
        current_res = self.resolutions[self.current_resolution_index]
        self.resolution_button.text = f"Resolution: {current_res[0]}x{current_res[1]}"

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.fullscreen_button.text = f"Fullscreen: {'On' if self.fullscreen else 'Off'}"

    def _apply_settings(self):
        current_res = self.resolutions[self.current_resolution_index]
        self.config.set('window_width', current_res[0])
        self.config.set('window_height', current_res[1])
        self.config.set('fullscreen', self.fullscreen)
        self.config.save_config()
        self.original_resolution = current_res
        self.original_fullscreen = self.fullscreen
        self._set_action("apply_display")

    def _set_action(self, action: str):
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        super().handle_event(event)
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None


class InterfaceSettingsScreen(MenuScreen):
    """Screen for interface-related settings."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Interface Settings", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.config = ConfigManager()

        current_layout = self.config.get('ui_layout', 'default')
        layout_label = self._get_layout_label(current_layout)

        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        start_x = (screen_width - button_w) // 2
        start_y = menu_start_y(screen_height)

        self.layout_button = Button(
            start_x, start_y, button_w, button_h,
            f"UI Layout: {layout_label}", font, lambda: self._toggle_layout()
        )
        self.back_button = Button(
            start_x, start_y + (button_h + spacing), button_w, button_h,
            "Back", font, lambda: self._set_action("back"), glaive_direction="left"
        )

        self.buttons = [self.layout_button, self.back_button]
        self._action_result = None

    def _get_layout_label(self, layout: str) -> str:
        return "Reversed" if layout == "reversed" else "Default"

    def _toggle_layout(self):
        current_layout = self.config.get('ui_layout', 'default')
        new_layout = "reversed" if current_layout == "default" else "default"
        setattr(self.config.config, 'ui_layout', new_layout)
        self.config.save_config()
        self.layout_button.text = f"UI Layout: {self._get_layout_label(new_layout)}"

    def _set_action(self, action: str):
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        super().handle_event(event)
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
        self.background = shared_background
        self.config = ConfigManager()
        self.sound_manager = get_sound_manager()
        self.use_panel = False

        current_volume = self.config.get('sfx_volume', 1.0)
        audio_enabled = self.config.get('audio_enabled', True)

        # Scale component dimensions
        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        slider_width = button_w
        slider_height = max(20, int(screen_height * 0.04))
        checkbox_size = max(20, int(screen_height * 0.04))
        spacing = max(50, int(screen_height * 0.09))

        center_x = screen_width // 2
        panel_start_y = int(screen_height * 0.18)
        content_start_y = panel_start_y + int(screen_height * 0.175)

        self.volume_slider = Slider(
            center_x - slider_width // 2, content_start_y,
            slider_width, slider_height,
            min_value=0.0, max_value=1.0, initial_value=current_volume,
            on_change=self._on_volume_change, label="Master Volume", font=font
        )

        self.mute_checkbox = Checkbox(
            center_x - 100, content_start_y + spacing,
            checkbox_size, "Mute All Sounds", font,
            initial_checked=not audio_enabled, on_change=self._on_mute_change
        )

        self.back_button = Button(
            (screen_width - button_w) // 2, content_start_y + spacing * 2 + int(screen_height * 0.03),
            button_w, button_h, "Back", font,
            lambda: self._set_action("back"), glaive_direction="left"
        )

        self.buttons = [self.back_button]
        self._action_result = None

        # Panel dimensions for manual drawing
        panel_width = max(button_w + 80, int(screen_width * 0.4))
        self.panel_y = panel_start_y
        self.panel_width = panel_width
        self.panel_height = (content_start_y + spacing * 2 + int(screen_height * 0.03) + button_h) - panel_start_y + 40

    def _on_volume_change(self, value: float):
        self.config.set('sfx_volume', value)
        self.config.save_config()
        self.sound_manager.set_volume("master", value)

    def _on_mute_change(self, muted: bool):
        audio_enabled = not muted
        self.config.set('audio_enabled', audio_enabled)
        self.config.save_config()
        if audio_enabled:
            self.sound_manager.enable()
        else:
            self.sound_manager.disable()

    def _set_action(self, action: str):
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mute_checkbox.handle_click(event.pos)
        result = super().handle_event(event)
        if result:
            return result
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None

    def update(self, delta_time: float, mouse_pos: tuple, mouse_pressed: bool):
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.volume_slider.update(mouse_pos, mouse_pressed)
        self.mute_checkbox.update(mouse_pos, mouse_pressed)

    def draw(self, surface: pygame.Surface):
        self._draw_dimmed_background(surface)
        self._draw_background_decorations(surface)

        panel_x = (self.screen_width - self.panel_width) // 2
        panel = MenuPanel(panel_x, self.panel_y, self.panel_width, self.panel_height, self.title)
        panel.draw(surface, self.large_font)

        self.volume_slider.draw(surface)
        self.mute_checkbox.draw(surface)
        self.back_button.draw(surface)
