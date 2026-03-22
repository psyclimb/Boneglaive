#!/usr/bin/env python3
"""
Menu Manager
Manages menu navigation, screen stack, and event routing.
"""
import pygame
from typing import Optional, List
from .menu_components import TextInputDialog
from .main_menu import MainMenuScreen
from .play_menu import PlaySubmenu, MapSelectionMenu
from .profile_menu import ProfileSubmenu, ProfileListScreen, ProfileStatsScreen, ProfileDeleteScreen
from .settings_menu import SettingsSubmenu, DisplaySettingsScreen, SoundSettingsScreen, InterfaceSettingsScreen
from .about_screen import AboutScreen
from .how_to_play_screen import HowToPlayScreen
from boneglaive.game.player_profile import profile_manager
from boneglaive.utils.config import ConfigManager


class MenuManager:
    """
    Manages the menu system with stack-based navigation.
    """

    def __init__(self, screen_width: int = None, screen_height: int = None):
        self.config = ConfigManager()

        # Load resolution from config if not provided
        if screen_width is None or screen_height is None:
            screen_width = self.config.get('window_width', 1280)
            screen_height = self.config.get('window_height', 720)

        self.screen_width = screen_width
        self.screen_height = screen_height

        # Initialize pygame and create display surface
        pygame.init()

        # Check if fullscreen mode is enabled
        fullscreen_enabled = self.config.get('fullscreen', False)
        if fullscreen_enabled:
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Boneglaive")
        self.clock = pygame.time.Clock()

        # Fonts - scale with resolution
        font_scale = screen_height / 800.0
        font_size = max(16, int(32 * font_scale))
        large_font_size = max(32, int(64 * font_scale))

        self.font = pygame.font.Font(None, font_size)
        self.large_font = pygame.font.Font(None, large_font_size)

        # Shared kaleidoscope background for all menus (create once)
        from .kaleidoscope_background import KaleidoscopeBackground
        self.shared_background = KaleidoscopeBackground(screen_width, screen_height)

        # Screen stack for navigation
        self.screen_stack: List = []

        # Text input dialog (if active)
        self.text_input_dialog: Optional[TextInputDialog] = None

        # Result to return when exiting menu
        self.result = None

        # Auto-load profile if one exists
        self._auto_load_profile()

        # Start with main menu
        self._push_screen(self._create_main_menu())

        self.running = True

    def _auto_load_profile(self):
        """Auto-load the last selected profile if one exists."""
        saved_profile_name = self.config.get('current_profile', '')
        if saved_profile_name:
            profile = profile_manager.load_profile(saved_profile_name)
            if profile:
                profile_manager.set_current_profile(profile)
            else:
                # Clear invalid profile from config
                self.config.set('current_profile', '')
                self.config.save_config()

    def _create_main_menu(self):
        """Create the main menu screen."""
        return MainMenuScreen(self.font, self.large_font, self.screen_width, self.screen_height)

    def _push_screen(self, screen):
        """Push a new screen onto the stack."""
        if self.screen_stack:
            self.screen_stack[-1].on_exit()
        self.screen_stack.append(screen)
        screen.on_enter()

    def _pop_screen(self):
        """Pop the current screen and return to previous."""
        if len(self.screen_stack) > 1:
            old_screen = self.screen_stack.pop()
            old_screen.on_exit()
            self.screen_stack[-1].on_enter()
            return True
        return False

    def _get_current_screen(self):
        """Get the current active screen."""
        return self.screen_stack[-1] if self.screen_stack else None

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            # Handle text input dialog if active
            if self.text_input_dialog:
                if self.text_input_dialog.handle_event(event):
                    # Dialog closed
                    self.text_input_dialog = None
                continue

            # Handle quit event
            if event.type == pygame.QUIT:
                self.running = False
                self.result = ("quit", None)
                return

            # Route event to current screen
            current_screen = self._get_current_screen()
            if current_screen:
                action = current_screen.handle_event(event)
                if action:
                    self._handle_action(action)

    def _handle_action(self, action: str):
        """Handle action from screen."""
        # Navigation actions
        if action == "back":
            self._pop_screen()

        elif action == "play":
            play_submenu = PlaySubmenu(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(play_submenu)

        elif action == "vs_ai" or action == "local_mp":
            # Game mode was set in the screen, now show map selection
            map_menu = MapSelectionMenu(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(map_menu)

        elif action == "start_game":
            # Start the game
            self.running = False
            self.result = ("start_game", None)

        elif action == "profile":
            profile_submenu = ProfileSubmenu(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(profile_submenu)

        elif action == "select_profile":
            profile_list = ProfileListScreen(self.font, self.large_font, self.screen_width, self.screen_height)
            self._push_screen(profile_list)

        elif action == "create_profile":
            # Show text input dialog
            self.text_input_dialog = TextInputDialog(
                "Enter profile name (max 8 characters):",
                self.font,
                max_length=8,
                on_confirm=self._on_profile_created,
                on_cancel=lambda: None
            )

        elif action == "delete_profile":
            # Show delete profile screen
            delete_screen = ProfileDeleteScreen(self.font, self.large_font, self.screen_width, self.screen_height)
            self._push_screen(delete_screen)

        elif action == "view_stats":
            # Check if profile is selected
            profile = profile_manager.get_current_profile()
            if not profile:
                # Could show a message, for now just do nothing
                pass
            else:
                stats_screen = ProfileStatsScreen(self.font, self.large_font, self.screen_width, self.screen_height)
                self._push_screen(stats_screen)

        elif action == "settings":
            settings_submenu = SettingsSubmenu(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(settings_submenu)

        elif action == "display_settings":
            display_settings = DisplaySettingsScreen(self.font, self.large_font, self.screen_width, self.screen_height)
            self._push_screen(display_settings)

        elif action == "sound_settings":
            sound_settings = SoundSettingsScreen(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(sound_settings)

        elif action == "interface_settings":
            interface_settings = InterfaceSettingsScreen(self.font, self.large_font, self.screen_width, self.screen_height)
            self._push_screen(interface_settings)

        elif action == "how_to_play":
            how_to_play_screen = HowToPlayScreen(self.font, self.large_font, self.screen_width, self.screen_height)
            self._push_screen(how_to_play_screen)

        elif action == "about":
            about_screen = AboutScreen(self.font, self.large_font, self.screen_width, self.screen_height)
            self._push_screen(about_screen)

        elif action == "quit":
            self.running = False
            self.result = ("quit", None)

    def _on_profile_created(self, name: str):
        """Handle profile creation."""
        try:
            profile = profile_manager.create_profile(name)
            profile_manager.set_current_profile(profile)
            self.config.set('current_profile', name)
            self.config.save_config()
        except ValueError:
            # Profile already exists - could show error message
            pass

    def update(self, delta_time: float):
        """Update current screen."""
        # Get mouse state
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Left button

        # Update text input dialog if active
        if self.text_input_dialog:
            self.text_input_dialog.update(delta_time)
            return

        # Update current screen
        current_screen = self._get_current_screen()
        if current_screen:
            current_screen.update(delta_time, mouse_pos, mouse_pressed)

    def draw(self):
        """Draw current screen."""
        # Draw current screen
        current_screen = self._get_current_screen()
        if current_screen:
            current_screen.draw(self.screen)

        # Draw text input dialog on top if active
        if self.text_input_dialog:
            self.text_input_dialog.draw(self.screen)

        # Update display
        pygame.display.flip()

    def run(self):
        """Run the menu loop."""
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0  # 60 FPS, convert to seconds

            self.handle_events()
            self.update(delta_time)
            self.draw()

        return self.result

    def cleanup(self):
        """Clean up pygame resources."""
        pygame.quit()
