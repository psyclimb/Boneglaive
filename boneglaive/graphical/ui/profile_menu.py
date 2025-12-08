#!/usr/bin/env python3
"""
Profile Menu Screens
Screens for profile management: selection, creation, and viewing stats.
"""
import pygame
from typing import Optional
from .menu_components import MenuScreen, Button, TextInputDialog, COLOR_TEXT, COLOR_BG
from boneglaive.game.player_profile import profile_manager
from boneglaive.utils.config import ConfigManager


class ProfileSubmenu(MenuScreen):
    """Submenu for profile management."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Profile", font, large_font)
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
                "Select Profile",
                font,
                lambda: self._set_action("select_profile")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing),
                button_width, button_height,
                "Create Profile",
                font,
                lambda: self._set_action("create_profile")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 2,
                button_width, button_height,
                "View Stats",
                font,
                lambda: self._set_action("view_stats")
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


class ProfileListScreen(MenuScreen):
    """Screen for selecting from existing profiles."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Select Profile", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()

        # Get available profiles
        self.profiles = profile_manager.list_profiles()

        # Button dimensions
        button_width = 300
        button_height = 50
        button_spacing = 15

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 180

        # Create buttons for each profile
        self.buttons = []

        if not self.profiles:
            # Show message if no profiles
            self.no_profiles_message = True
        else:
            self.no_profiles_message = False
            for i, profile_name in enumerate(self.profiles):
                y_pos = start_y + i * (button_height + button_spacing)
                self.buttons.append(
                    Button(
                        start_x, y_pos,
                        button_width, button_height,
                        profile_name,
                        font,
                        lambda pn=profile_name: self._select_profile(pn)
                    )
                )

        # Add Back button
        back_y = start_y + len(self.profiles) * (button_height + button_spacing) + 30 if self.profiles else start_y
        self.buttons.append(
            Button(
                start_x, back_y,
                button_width, button_height,
                "Back",
                font,
                lambda: self._set_action("back")
            )
        )

        self._action_result = None
        self._message = None

    def _select_profile(self, profile_name: str):
        """Load a profile."""
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
        """Draw the profile list screen."""
        super().draw(surface)

        # Draw no profiles message if needed
        if self.no_profiles_message:
            message = "No profiles found. Create one first!"
            message_surface = self.font.render(message, True, COLOR_TEXT)
            message_rect = message_surface.get_rect(centerx=self.screen_width // 2, top=200)
            surface.blit(message_surface, message_rect)

        # Draw message if any
        if self._message:
            msg_surface = self.font.render(self._message, True, (100, 255, 100))
            msg_rect = msg_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 60)
            surface.blit(msg_surface, msg_rect)


class ProfileStatsScreen(MenuScreen):
    """Screen for viewing profile statistics."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        super().__init__("Profile Stats", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.profile = profile_manager.get_current_profile()

        # No buttons, just display stats
        self.buttons = []

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events - any key/click returns to menu."""
        if event.type == pygame.KEYUP and event.key != pygame.K_ESCAPE:
            # Any key except ESC (prevents immediate exit from ESC press on previous screen)
            return "back"
        elif event.type == pygame.MOUSEBUTTONUP:
            return "back"
        return None

    def draw(self, surface: pygame.Surface):
        """Draw the profile stats screen."""
        surface.fill(COLOR_BG)

        if not self.profile:
            # No profile selected
            message = "No profile selected."
            message_surface = self.large_font.render(message, True, COLOR_TEXT)
            message_rect = message_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            surface.blit(message_surface, message_rect)

            hint = "Press any key to return..."
            hint_surface = self.font.render(hint, True, (150, 150, 150))
            hint_rect = hint_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 40)
            surface.blit(hint_surface, hint_rect)
            return

        # Draw profile name as title
        title_text = f"PROFILE: {self.profile.name}"
        title_surface = self.large_font.render(title_text, True, COLOR_TEXT)
        title_rect = title_surface.get_rect(centerx=self.screen_width // 2, top=60)
        surface.blit(title_surface, title_rect)

        # Calculate stats
        win_rate = self.profile.get_win_rate()
        most_picked = self.profile.get_most_picked_unit() or "None"

        # Draw stats
        lines = [
            "",
            "=== GAME STATS ===",
            f"Games Played: {self.profile.games_played}",
            f"Wins: {self.profile.wins}",
            f"Losses: {self.profile.losses}",
            f"Win Rate: {win_rate:.1f}%",
            "",
            "=== UNIT STATS ===",
            f"Most Picked Unit: {most_picked}",
            "",
            "Unit Pick Counts:",
        ]

        # Add unit picks (only show units with picks > 0)
        for unit_name, picks in sorted(self.profile.unit_picks.items(), key=lambda x: x[1], reverse=True):
            if picks > 0:
                lines.append(f"  {unit_name}: {picks}")

        # Draw all lines
        y_pos = 150
        line_height = 30

        for line in lines:
            if line:  # Non-empty line
                if "===" in line:
                    # Section headers
                    text_surface = self.font.render(line, True, (100, 200, 255))
                elif "Win Rate:" in line or "Most Picked" in line:
                    # Highlight key stats
                    text_surface = self.font.render(line, True, (100, 255, 100))
                else:
                    # Regular text
                    text_surface = self.font.render(line, True, COLOR_TEXT)

                text_rect = text_surface.get_rect(centerx=self.screen_width // 2, top=y_pos)
                surface.blit(text_surface, text_rect)

            y_pos += line_height

        # Draw hint
        hint = "Press any key to return..."
        hint_surface = self.font.render(hint, True, (150, 150, 150))
        hint_rect = hint_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 40)
        surface.blit(hint_surface, hint_rect)
