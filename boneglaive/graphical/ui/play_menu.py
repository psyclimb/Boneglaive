#!/usr/bin/env python3
"""
Play Menu Screens
Screens for game mode selection and map selection.
"""
import pygame
from typing import Optional, List
from .menu_components import (
    MenuScreen, Button, COLOR_TEXT,
    menu_button_width, menu_button_height, menu_button_spacing, menu_start_y,
    map_button_width, map_button_height
)
from boneglaive.utils.config import ConfigManager, GameMode
from boneglaive.game.map import MapFactory
from boneglaive.utils.paths import asset_path, load_svg


class PlaySubmenu(MenuScreen):
    """Submenu for selecting game mode."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Play Game", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()
        self.background = shared_background

        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        start_x = (screen_width - button_w) // 2
        start_y = menu_start_y(screen_height)

        self.buttons = [
            Button(start_x, start_y, button_w, button_h, "VS AI", font,
                   lambda: self._set_action("vs_ai")),
            Button(start_x, start_y + (button_h + spacing), button_w, button_h, "Local Multiplayer", font,
                   lambda: self._set_action("local_mp")),
            Button(start_x, start_y + (button_h + spacing) * 2, button_w, button_h, "Back", font,
                   lambda: self._set_action("back"), glaive_direction="left"),
        ]
        self._action_result = None

    def _set_action(self, action: str):
        if action == "vs_ai":
            self.config.set('game_mode', GameMode.VS_AI.value)
            self.config.save_config()
        elif action == "local_mp":
            self.config.set('game_mode', GameMode.LOCAL_MULTIPLAYER.value)
            self.config.save_config()
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        super().handle_event(event)
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None


class MapSelectionMenu(MenuScreen):
    """Menu for selecting a map to play on."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Select Map", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()
        self.background = shared_background

        self.available_maps = MapFactory.list_available_maps()

        button_w = map_button_width(screen_width)
        button_h = map_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        self.button_width = button_w
        self.button_height = button_h
        self.button_spacing = spacing

        start_x = (screen_width - button_w) // 2

        # Center all buttons vertically: map buttons + extra spacing + back button
        num_maps = len(self.available_maps)
        total_height = num_maps * (button_h + spacing) + spacing * 2 + button_h
        start_y = max(10, (screen_height - total_height) // 2)

        self.buttons = []
        for i, map_name in enumerate(self.available_maps):
            display_name = map_name.replace('_', ' ').title()
            map_icon = self._load_map_icon(map_name)
            y_pos = start_y + i * (button_h + spacing)
            self.buttons.append(
                Button(start_x, y_pos, button_w, button_h, display_name, font,
                       lambda mn=map_name: self._select_map(mn), image=map_icon)
            )

        back_y = start_y + num_maps * (button_h + spacing) + spacing * 2
        self.buttons.append(
            Button(start_x, back_y, button_w, button_h, "Back", font,
                   lambda: self._set_action("back"), glaive_direction="left")
        )

        self._action_result = None
        self.scroll_offset = 0
        self.max_visible_buttons = 8

    def _select_map(self, map_name: str):
        self.config.set('selected_map', map_name)
        self.config.save_config()
        self._action_result = "start_game"

    def _set_action(self, action: str):
        self._action_result = action

    def _load_map_icon(self, map_name: str) -> Optional[pygame.Surface]:
        icon_map = {
            'lime_foyer': 'lime_foyer_icon.svg',
            'hard_pressed': 'hard_pressed_icon.svg',
            'stained_stones': 'stained_stones_icon.svg',
            'verdant_terrace': 'verdant_terrace_icon.svg'
        }
        icon_filename = icon_map.get(map_name)
        if not icon_filename:
            return None
        icon_path = asset_path(f"graphics/map_icons/{icon_filename}")
        return load_svg(icon_path, 128, 128)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEWHEEL:
            if len(self.buttons) > self.max_visible_buttons:
                self.scroll_offset -= event.y * 30
                button_step = self.button_height + self.button_spacing
                self.scroll_offset = max(0, min(self.scroll_offset,
                    (len(self.buttons) - self.max_visible_buttons) * button_step))

        super().handle_event(event)

        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None

    def draw(self, surface: pygame.Surface):
        super().draw(surface)

        if len(self.buttons) > self.max_visible_buttons:
            hint_text = "Scroll to see more maps"
            hint_surface = self.font.render(hint_text, True, (150, 150, 150))
            hint_rect = hint_surface.get_rect(
                centerx=self.screen_width // 2,
                bottom=self.screen_height - int(self.screen_height * 0.03)
            )
            surface.blit(hint_surface, hint_rect)
