#!/usr/bin/env python3
"""
Profile Menu Screens
Screens for profile management: selection, creation, and viewing stats.
"""
import pygame
from typing import Optional
from .menu_components import (
    MenuScreen, MenuPanel, Button, TextInputDialog, COLOR_TEXT, COLOR_BG, COLOR_TITLE,
    menu_button_width, menu_button_height, menu_button_spacing, menu_start_y
)
from boneglaive.game.player_profile import profile_manager
from boneglaive.utils.config import ConfigManager


class ProfileSubmenu(MenuScreen):
    """Submenu for profile management."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Profile", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background

        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        start_x = (screen_width - button_w) // 2
        start_y = menu_start_y(screen_height)

        self.buttons = [
            Button(start_x, start_y, button_w, button_h, "Select Profile", font,
                   lambda: self._set_action("select_profile")),
            Button(start_x, start_y + (button_h + spacing), button_w, button_h, "Create Profile", font,
                   lambda: self._set_action("create_profile")),
            Button(start_x, start_y + (button_h + spacing) * 2, button_w, button_h, "Delete Profile", font,
                   lambda: self._set_action("delete_profile")),
            Button(start_x, start_y + (button_h + spacing) * 3, button_w, button_h, "View Stats", font,
                   lambda: self._set_action("view_stats")),
            Button(start_x, start_y + (button_h + spacing) * 4, button_w, button_h, "Back", font,
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


class ProfileListScreen(MenuScreen):
    """Screen for selecting from existing profiles."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Select Profile", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.config = ConfigManager()

        self.profiles = profile_manager.list_profiles()

        button_w = menu_button_width(screen_width)
        button_h = menu_button_height(screen_height)
        spacing = menu_button_spacing(screen_height)
        start_x = (screen_width - button_w) // 2
        start_y = menu_start_y(screen_height)

        self.buttons = []
        if not self.profiles:
            self.no_profiles_message = True
        else:
            self.no_profiles_message = False
            for i, profile_name in enumerate(self.profiles):
                y_pos = start_y + i * (button_h + spacing)
                self.buttons.append(
                    Button(start_x, y_pos, button_w, button_h, profile_name, font,
                           lambda pn=profile_name: self._select_profile(pn))
                )

        back_y = start_y + len(self.profiles) * (button_h + spacing) + spacing * 2 if self.profiles else start_y
        self.buttons.append(
            Button(start_x, back_y, button_w, button_h, "Back", font,
                   lambda: self._set_action("back"), glaive_direction="left")
        )

        self._action_result = None
        self._message = None

    def _select_profile(self, profile_name: str):
        profile = profile_manager.load_profile(profile_name)
        if profile:
            profile_manager.set_current_profile(profile)
            self.config.set('current_profile', profile_name)
            self.config.save_config()
            self._message = f"Profile '{profile_name}' loaded!"
            self._action_result = "back"
        else:
            self._message = f"Error loading profile '{profile_name}'"

    def _set_action(self, action: str):
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        super().handle_event(event)
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None

    def draw(self, surface: pygame.Surface):
        super().draw(surface)

        if self.no_profiles_message:
            message = "No profiles found. Create one first!"
            message_surface = self.font.render(message, True, COLOR_TEXT)
            message_rect = message_surface.get_rect(centerx=self.screen_width // 2, top=int(self.screen_height * 0.28))
            surface.blit(message_surface, message_rect)

        if self._message:
            msg_surface = self.font.render(self._message, True, (100, 255, 100))
            msg_rect = msg_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - int(self.screen_height * 0.08))
            surface.blit(msg_surface, msg_rect)


class ProfileStatsScreen(MenuScreen):
    """Screen for viewing profile statistics."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Profile Stats", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.profile = profile_manager.get_current_profile()
        self.activation_timer = 0.0
        self.use_panel = False
        self.buttons = []

    def on_enter(self):
        super().on_enter()
        self.activation_timer = 0.0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.activation_timer < 0.2:
            return None
        if event.type == pygame.KEYUP and event.key != pygame.K_ESCAPE:
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

        if not self.profile:
            message = "No profile selected."
            message_surface = self.large_font.render(message, True, COLOR_TEXT)
            message_rect = message_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            surface.blit(message_surface, message_rect)

            hint = "Press any key to return..."
            hint_surface = self.font.render(hint, True, (150, 150, 150))
            hint_rect = hint_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - int(self.screen_height * 0.06))
            surface.blit(hint_surface, hint_rect)
            return

        # Draw stats inside a panel
        panel_w = menu_button_width(self.screen_width) + 80
        panel_h = int(self.screen_height * 0.7)
        panel_x = (self.screen_width - panel_w) // 2
        panel_y = int(self.screen_height * 0.18)
        title_text = f"PROFILE: {self.profile.name}"
        panel = MenuPanel(panel_x, panel_y, panel_w, panel_h, title_text)
        panel.draw(surface, self.large_font)

        # Stats content
        win_rate = self.profile.get_win_rate()
        most_picked = self.profile.get_most_picked_unit() or "None"

        lines = [
            ("", None),
            ("=== GAME STATS ===", (100, 200, 255)),
            (f"Games Played: {self.profile.games_played}", COLOR_TEXT),
            (f"Wins: {self.profile.wins}", COLOR_TEXT),
            (f"Losses: {self.profile.losses}", COLOR_TEXT),
            (f"Win Rate: {win_rate:.1f}%", (100, 255, 100)),
            ("", None),
            ("=== UNIT STATS ===", (100, 200, 255)),
            (f"Most Picked Unit: {most_picked}", (100, 255, 100)),
            ("", None),
            ("Unit Pick Counts:", COLOR_TEXT),
        ]

        for unit_name, picks in sorted(self.profile.unit_picks.items(), key=lambda x: x[1], reverse=True):
            if picks > 0:
                lines.append((f"  {unit_name}: {picks}", COLOR_TEXT))

        line_height = max(20, int(self.screen_height * 0.04))
        content_y = panel_y + 90
        for text, color in lines:
            if text and color:
                text_surface = self.font.render(text, True, color)
                text_rect = text_surface.get_rect(centerx=self.screen_width // 2, top=content_y)
                surface.blit(text_surface, text_rect)
            content_y += line_height

        hint = "Press any key to return..."
        hint_surface = self.font.render(hint, True, (150, 150, 150))
        hint_rect = hint_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - int(self.screen_height * 0.06))
        surface.blit(hint_surface, hint_rect)


class ProfileDeleteScreen(MenuScreen):
    """Screen for deleting profiles."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Delete Profile", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.config = ConfigManager()

        self.profiles = profile_manager.list_profiles()
        self._build_buttons()
        self._action_result = None
        self._message = None

    def _build_buttons(self):
        button_w = menu_button_width(self.screen_width)
        button_h = menu_button_height(self.screen_height)
        spacing = menu_button_spacing(self.screen_height)
        start_x = (self.screen_width - button_w) // 2
        start_y = menu_start_y(self.screen_height)

        self.buttons = []
        if not self.profiles:
            self.no_profiles_message = True
        else:
            self.no_profiles_message = False
            for i, profile_name in enumerate(self.profiles):
                y_pos = start_y + i * (button_h + spacing)
                self.buttons.append(
                    Button(start_x, y_pos, button_w, button_h,
                           f"Delete: {profile_name}", self.font,
                           lambda pn=profile_name: self._delete_profile(pn))
                )

        back_y = start_y + len(self.profiles) * (button_h + spacing) + spacing * 2 if self.profiles else start_y
        self.buttons.append(
            Button(start_x, back_y, button_w, button_h, "Back", self.font,
                   lambda: self._set_action("back"), glaive_direction="left")
        )

    def _delete_profile(self, profile_name: str):
        current_profile = profile_manager.get_current_profile()
        is_active = current_profile and current_profile.name == profile_name

        if profile_manager.delete_profile(profile_name):
            if is_active:
                profile_manager.set_current_profile(None)
                self.config.set('current_profile', '')
                self.config.save_config()
                self._message = f"Active profile '{profile_name}' deleted!"
            else:
                self._message = f"Profile '{profile_name}' deleted!"
            self.profiles = profile_manager.list_profiles()
            self._build_buttons()
        else:
            self._message = f"Error deleting profile '{profile_name}'"

    def _set_action(self, action: str):
        self._action_result = action

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        super().handle_event(event)
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action
        return None

    def draw(self, surface: pygame.Surface):
        super().draw(surface)

        if self.no_profiles_message:
            message = "No profiles to delete."
            message_surface = self.font.render(message, True, COLOR_TEXT)
            message_rect = message_surface.get_rect(centerx=self.screen_width // 2, top=int(self.screen_height * 0.28))
            surface.blit(message_surface, message_rect)

        if self._message:
            if "Cannot delete" in self._message or "Error" in self._message:
                color = (255, 100, 100)
            else:
                color = (100, 255, 100)
            msg_surface = self.font.render(self._message, True, color)
            msg_rect = msg_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - int(self.screen_height * 0.08))
            surface.blit(msg_surface, msg_rect)
