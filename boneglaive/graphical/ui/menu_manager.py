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
from .settings_menu import SettingsSubmenu, DisplaySettingsScreen, SoundSettingsScreen, InterfaceSettingsScreen
from .about_screen import AboutScreen
from .how_to_play_screen import HowToPlayScreen
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

        # Start with main menu
        self._push_screen(self._create_main_menu())

        self.running = True

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

        elif action == "settings":
            settings_submenu = SettingsSubmenu(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(settings_submenu)

        elif action == "display_settings":
            display_settings = DisplaySettingsScreen(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(display_settings)

        elif action == "apply_display":
            self._apply_display_settings()

        elif action == "sound_settings":
            sound_settings = SoundSettingsScreen(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(sound_settings)

        elif action == "interface_settings":
            interface_settings = InterfaceSettingsScreen(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(interface_settings)

        elif action == "how_to_play":
            how_to_play_screen = HowToPlayScreen(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(how_to_play_screen)

        elif action == "about":
            about_screen = AboutScreen(self.font, self.large_font, self.screen_width, self.screen_height, self.shared_background)
            self._push_screen(about_screen)

        elif action == "quit":
            self.running = False
            self.result = ("quit", None)

    def _apply_display_settings(self):
        """Reinitialise the pygame display with settings just written to config."""
        # Reload config from disk — DisplaySettingsScreen used its own ConfigManager
        # instance to save, so self.config still holds the old values.
        self.config = ConfigManager()
        new_width = self.config.get('window_width', 1280)
        new_height = self.config.get('window_height', 720)
        fullscreen = self.config.get('fullscreen', False)

        # Resize the pygame window immediately
        if fullscreen:
            self.screen = pygame.display.set_mode((new_width, new_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((new_width, new_height))

        self.screen_width = new_width
        self.screen_height = new_height

        # Refresh scale_manager and all module-level constants in UI files
        from .scale_utils import scale_manager, refresh_all_module_constants
        scale_manager.config = self.config
        scale_manager.update_scale()
        refresh_all_module_constants()

        # Rebuild fonts for new resolution
        font_scale = new_height / 800.0
        font_size = max(16, int(32 * font_scale))
        large_font_size = max(32, int(64 * font_scale))
        self.font = pygame.font.Font(None, font_size)
        self.large_font = pygame.font.Font(None, large_font_size)

        # Rebuild shared background at new size
        from .kaleidoscope_background import KaleidoscopeBackground
        self.shared_background = KaleidoscopeBackground(new_width, new_height)

        # Tear down the screen stack and restart from main menu so all
        # screens are recreated at the correct resolution.
        while self.screen_stack:
            self.screen_stack.pop()
        self._push_screen(self._create_main_menu())

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
        pass
