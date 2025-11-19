#!/usr/bin/env python3
"""
Menu system for the game.
Handles main menu, settings, and multiplayer lobby.
"""

import curses
import sys
import random
from typing import Dict, List, Optional, Tuple, Callable

from boneglaive.utils.config import ConfigManager, NetworkMode, DisplayMode
from boneglaive.utils.debug import debug_config, logger
from boneglaive.renderers.curses_renderer import CursesRenderer
from boneglaive.utils.render_interface import RenderInterface
from boneglaive.game.player_profile import profile_manager

class MenuItem:
    """Represents a menu item."""
    
    def __init__(self, label: str, action: Optional[Callable] = None, 
                submenu: Optional['Menu'] = None):
        self.label = label
        self.action = action
        self.submenu = submenu
    
    def activate(self):
        """Activate this menu item."""
        if self.action:
            return self.action()
        elif self.submenu:
            return ("submenu", self.submenu)
        return None

class Menu:
    """Represents a menu with items."""
    
    def __init__(self, title: str, items: List[MenuItem], parent: Optional['Menu'] = None):
        self.title = title
        self.items = items
        self.parent = parent
        self.selected_index = 0
    
    def move_selection(self, direction: int):
        """Move the selection up or down."""
        self.selected_index = (self.selected_index + direction) % len(self.items)
    
    def activate_selection(self):
        """Activate the selected menu item."""
        return self.items[self.selected_index].activate()
    
    def go_back(self):
        """Go back to the parent menu if there is one."""
        if self.parent:
            return ("submenu", self.parent)
        return None

class MenuUI:
    """User interface for the menu system."""
    
    def __init__(self, stdscr=None, renderer=None):
        self.config = ConfigManager()
        # Set up renderer - use provided renderer or create curses renderer
        if renderer is not None:
            self.renderer = renderer
        else:
            self.renderer = CursesRenderer(stdscr)
            self.renderer.initialize()
        self.current_menu = self._create_main_menu()
        self.running = True

        # Auto-load the last selected profile if one exists
        saved_profile_name = self.config.get('current_profile', '')
        if saved_profile_name:
            profile = profile_manager.load_profile(saved_profile_name)
            if profile:
                profile_manager.set_current_profile(profile)
                logger.info(f"Auto-loaded profile: {saved_profile_name}")
            else:
                logger.warning(f"Failed to auto-load profile: {saved_profile_name}")
                # Clear the invalid profile from config
                self.config.set('current_profile', '')
                self.config.save_config()

        # Draw the menu immediately to avoid black screen
        self.draw()
    
    def _create_main_menu(self) -> Menu:
        """Create the main menu."""
        # Create submenus first
        play_menu = Menu("Play Game", [
            MenuItem("VS AI", self._start_vs_ai),
            MenuItem("Local Multiplayer", self._start_local_multiplayer),
            MenuItem("Back", lambda: ("submenu", None))
        ])

        settings_menu = Menu("Settings", [
            MenuItem("Display Settings", lambda: ("submenu", self._create_display_settings_menu())),
            MenuItem("Back", lambda: ("submenu", None))
        ])

        profile_menu = Menu("Profile", [
            MenuItem("Select Profile", self._select_profile),
            MenuItem("Create Profile", self._create_profile),
            MenuItem("View Stats", self._view_profile_stats),
            MenuItem("Back", lambda: ("submenu", None))
        ])

        # Create main menu
        main_menu = Menu("Boneglaive", [
            MenuItem("Play", None, play_menu),
            MenuItem("Profile", None, profile_menu),
            MenuItem("Settings", None, settings_menu),
            MenuItem("About", self._show_about),
            MenuItem("Quit", self._quit_game)
        ])

        # Set parent menus
        play_menu.parent = main_menu
        profile_menu.parent = main_menu
        settings_menu.parent = main_menu

        return main_menu
    
    def _create_display_settings_menu(self) -> Menu:
        """Create the display settings menu."""
        current_speed = self.config.get('animation_speed')
        speed_label = self._get_animation_speed_label(current_speed)
        
        menu = Menu("Display Settings", [
            MenuItem(f"Animation Speed: {speed_label}", self._cycle_animation_speed),
            MenuItem("Back", lambda: ("submenu", None))
        ])
        menu.parent = self._find_menu_by_title("Settings")
        return menu
    
    def _create_network_settings_menu(self) -> Menu:
        """Create the network settings menu."""
        menu = Menu("Network Settings", [
            MenuItem(f"Server IP: {self.config.get('server_ip')}", self._set_server_ip),
            MenuItem(f"Server Port: {self.config.get('server_port')}", self._set_server_port),
            MenuItem("Back", lambda: ("submenu", None))
        ])
        menu.parent = self._find_menu_by_title("Settings")
        return menu
    
    def _find_menu_by_title(self, title: str) -> Optional[Menu]:
        """Find a menu by its title."""
        if self.current_menu.title == title:
            return self.current_menu
        
        # Check if it's the parent
        if self.current_menu.parent and self.current_menu.parent.title == title:
            return self.current_menu.parent
        
        # Check if it's in the main menu chain
        menu = self.current_menu
        while menu.parent:
            menu = menu.parent
            if menu.title == title:
                return menu
        
        return None
    
    
    def _start_local_multiplayer(self):
        """Set local multiplayer mode and go to map selection."""
        self.config.set('network_mode', NetworkMode.LOCAL_MULTIPLAYER.value)
        self.config.save_config()
        logger.info("Selected local multiplayer mode")
        return ("submenu", self._create_map_selection_menu())
    
    def _start_lan_host(self):
        """Set LAN host mode and go to map selection."""
        self.config.set('network_mode', NetworkMode.LAN_HOST.value)
        self.config.save_config()
        logger.info("Selected LAN host mode")
        return ("submenu", self._create_map_selection_menu())
    
    def _start_lan_client(self):
        """Set LAN client mode and go to map selection."""
        self.config.set('network_mode', NetworkMode.LAN_CLIENT.value)
        self.config.save_config()
        logger.info("Selected LAN client mode")
        return ("submenu", self._create_map_selection_menu())
        
    def _start_vs_ai(self):
        """Set VS AI mode and go to map selection."""
        self.config.set('network_mode', NetworkMode.VS_AI.value)
        self.config.save_config()
        logger.info("Selected VS AI mode")
        return ("submenu", self._create_map_selection_menu())
    
    def _create_map_selection_menu(self) -> Menu:
        """Create the map selection menu with all available maps."""
        # Get all available maps (both JSON and hardcoded)
        from boneglaive.game.map import MapFactory
        from boneglaive.utils.seasonal_events import get_active_season, seasonal_manager
        
        available_maps = MapFactory.list_available_maps()
        
        # Check for active seasonal event
        active_season = get_active_season()
        menu_title = "Select Map"
        if active_season:
            seasonal_info = seasonal_manager.get_seasonal_info(active_season)
            menu_title = f"Select Map - {seasonal_info['name']} Active"
        
        # Create menu items for each map
        menu_items = []
        for map_name in available_maps:
            # Create a display name (capitalize and replace underscores)
            display_name = map_name.replace('_', ' ').title()
            
            # Add seasonal indicator if seasonal map exists
            if active_season and seasonal_manager.get_seasonal_map_path(map_name, active_season):
                display_name += " *"  # Seasonal indicator (asterisk)
            
            menu_items.append(MenuItem(display_name, lambda mn=map_name: self._select_map(mn)))
        
        # Add back button
        menu_items.append(MenuItem("Back", lambda: ("submenu", None)))
        
        menu = Menu(menu_title, menu_items)
        menu.parent = self._find_menu_by_title("Play Game")
        return menu
    
    def _select_map(self, map_name: str):
        """Select a map and start the game."""
        self.config.set('selected_map', map_name)
        self.config.save_config()
        logger.info(f"Selected map: {map_name}")
        return ("start_game", None)
    
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
        
        # Refresh the menu to show updated label
        return ("submenu", self._create_display_settings_menu())
    
    def _set_server_ip(self):
        """Set the server IP address."""
        # In a real implementation, this would show a text input dialog
        # For now, we'll just use a placeholder
        self.config.set('server_ip', "192.168.1.100")  # Placeholder
        self.config.save_config()
        return ("submenu", self._create_network_settings_menu())  # Refresh menu
    
    def _set_server_port(self):
        """Set the server port."""
        # In a real implementation, this would show a number input dialog
        # For now, we'll just use a placeholder
        self.config.set('server_port', 7777)  # Placeholder
        self.config.save_config()
        return ("submenu", self._create_network_settings_menu())  # Refresh menu
    
    def _show_about(self):
        """Show the about screen with license information."""
        return ("show_about", None)
    
    def _display_about_screen(self):
        """Display the about screen with copyright and license information."""
        self.renderer.clear_screen()
        
        # About screen content
        lines = [
            "Boneglaive v0.9.0a BETA",
            "Tactical Turn-Based Combat Game",
            "Beta Release",
            "",
            "Copyright (C) 2025 Psyclimb",
            "",
            "This program is free software licensed under GPL-3.0",
            "This program comes with ABSOLUTELY NO WARRANTY.",
            "",
            "You are welcome to redistribute it under certain conditions.",
            "See the LICENSE file for full terms.",
            "",
            "Source code: https://github.com/psyclimb/Boneglaive",
            "",
            "Built with Python and curses",
            "",
            "Press any key to return to menu..."
        ]
        
        # Get renderer dimensions - different properties for different renderers
        if hasattr(self.renderer, 'grid_height'):
            # Pygame renderer uses grid_height/grid_width
            height = self.renderer.grid_height
            width = self.renderer.grid_width
        else:
            # Curses renderer uses height/width
            height = self.renderer.height
            width = self.renderer.width
        
        # Calculate starting position to center the content
        start_row = max(2, (height - len(lines)) // 2)
        
        # Draw each line
        for i, line in enumerate(lines):
            if line:  # Non-empty line
                # Center the text horizontally
                col = max(2, (width - len(line)) // 2)
                if "v0.9.0a BETA" in line:
                    # Title in bold
                    self.renderer.draw_text(start_row + i, col, line, 1, curses.A_BOLD)
                elif "Copyright" in line or "GPL-3.0" in line:
                    # Important legal text in different color
                    self.renderer.draw_text(start_row + i, col, line, 2, 0)
                elif "Source code:" in line:
                    # URL in different color
                    self.renderer.draw_text(start_row + i, col, line, 3, 0)
                else:
                    # Regular text
                    self.renderer.draw_text(start_row + i, col, line, 1, 0)
        
        # Refresh display and wait for input
        self.renderer.refresh()
        self.renderer.get_input()  # Wait for any key press

    def _get_text_input(self, prompt: str, max_length: int = 8) -> Optional[str]:
        """
        Get text input from the user.

        Args:
            prompt: Prompt to display
            max_length: Maximum length of input (default 8 for profile names)

        Returns:
            User input string, or None if cancelled
        """
        self.renderer.clear_screen()

        # Get screen dimensions
        if hasattr(self.renderer, 'grid_height'):
            height = self.renderer.grid_height
            width = self.renderer.grid_width
        else:
            height = self.renderer.height
            width = self.renderer.width

        # Draw prompt
        prompt_row = height // 2 - 2
        prompt_col = max(2, (width - len(prompt)) // 2)
        self.renderer.draw_text(prompt_row, prompt_col, prompt, 1, curses.A_BOLD)

        # Draw input area
        input_row = prompt_row + 2
        input_col = max(2, (width - max_length - 4) // 2)
        self.renderer.draw_text(input_row, input_col, "> ", 1, 0)

        # Draw instructions
        instructions = "(ENTER to confirm, ESC to cancel)"
        instr_row = input_row + 2
        instr_col = max(2, (width - len(instructions)) // 2)
        self.renderer.draw_text(instr_row, instr_col, instructions, 2, 0)

        self.renderer.refresh()

        # Get input character by character
        input_text = ""
        cursor_col = input_col + 2

        # Show cursor but disable automatic echo (we handle drawing manually)
        if hasattr(self.renderer, 'stdscr'):
            curses.noecho()  # Don't auto-echo, we draw manually
            curses.curs_set(1)  # Show cursor

        while True:
            key = self.renderer.get_input()

            if key == 27:  # ESC key
                if hasattr(self.renderer, 'stdscr'):
                    curses.curs_set(0)  # Hide cursor
                return None
            elif key == ord('\n') or key == ord('\r') or key == 10:  # Enter key
                if hasattr(self.renderer, 'stdscr'):
                    curses.curs_set(0)  # Hide cursor
                return input_text.strip().upper() if input_text.strip() else None
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
                if input_text:
                    input_text = input_text[:-1]
                    # Clear the character
                    self.renderer.draw_text(input_row, cursor_col + len(input_text), " ", 1, 0)
                    self.renderer.refresh()
            elif 32 <= key <= 126 and len(input_text) < max_length:  # Printable characters
                char = chr(key).upper()
                input_text += char
                self.renderer.draw_text(input_row, cursor_col + len(input_text) - 1, char, 1, 0)
                self.renderer.refresh()

    def _create_profile(self):
        """Create a new profile."""
        name = self._get_text_input("Enter profile name (max 8 characters):", 8)

        if name:
            try:
                profile = profile_manager.create_profile(name)
                profile_manager.set_current_profile(profile)
                # Save profile to config for auto-load on next startup
                self.config.set('current_profile', name)
                self.config.save_config()
                logger.info(f"Created profile: {name}")
                # Show success message
                return ("show_message", f"Profile '{name}' created!")
            except ValueError as e:
                # Profile already exists
                logger.warning(f"Profile creation failed: {e}")
                return ("show_message", f"Error: {e}")

        return None

    def _select_profile(self):
        """Select an existing profile from a list."""
        profiles = profile_manager.list_profiles()

        if not profiles:
            return ("show_message", "No profiles found. Create one first!")

        # Create a menu with all profiles
        profile_items = []
        for profile_name in profiles:
            # Create a lambda that captures the profile name
            profile_items.append(
                MenuItem(profile_name, lambda p=profile_name: self._load_profile(p))
            )
        profile_items.append(MenuItem("Back", lambda: ("submenu", None)))

        profile_select_menu = Menu("Select Profile", profile_items)
        profile_select_menu.parent = self._find_menu_by_title("Profile")

        return ("submenu", profile_select_menu)

    def _load_profile(self, name: str):
        """Load a specific profile."""
        profile = profile_manager.load_profile(name)
        if profile:
            profile_manager.set_current_profile(profile)
            # Save profile to config for auto-load on next startup
            self.config.set('current_profile', name)
            self.config.save_config()
            logger.info(f"Loaded profile: {name}")
            return ("show_message", f"Profile '{name}' loaded!")
        else:
            return ("show_message", f"Error loading profile '{name}'")

    def _view_profile_stats(self):
        """Display current profile statistics."""
        profile = profile_manager.get_current_profile()

        if not profile:
            return ("show_message", "No profile selected.")

        return ("show_profile_stats", None)

    def _display_profile_stats(self):
        """Display the profile statistics screen."""
        profile = profile_manager.get_current_profile()

        if not profile:
            return

        self.renderer.clear_screen()

        # Get screen dimensions
        if hasattr(self.renderer, 'grid_height'):
            height = self.renderer.grid_height
            width = self.renderer.grid_width
        else:
            height = self.renderer.height
            width = self.renderer.width

        # Profile stats content
        win_rate = profile.get_win_rate()
        most_picked = profile.get_most_picked_unit() or "None"

        lines = [
            f"PROFILE: {profile.name}",
            "",
            "=== GAME STATS ===",
            f"Games Played: {profile.games_played}",
            f"Wins: {profile.wins}",
            f"Losses: {profile.losses}",
            f"Win Rate: {win_rate:.1f}%",
            "",
            "=== UNIT STATS ===",
            f"Most Picked Unit: {most_picked}",
            "",
            "Unit Pick Counts:",
        ]

        # Add unit picks (only show units with picks > 0)
        for unit_name, picks in sorted(profile.unit_picks.items(), key=lambda x: x[1], reverse=True):
            if picks > 0:
                lines.append(f"  {unit_name}: {picks}")

        lines.append("")
        lines.append("Press any key to return to menu...")

        # Calculate starting position to center the content
        start_row = max(2, (height - len(lines)) // 2)

        # Draw each line
        for i, line in enumerate(lines):
            if line:  # Non-empty line
                # Center the text horizontally
                col = max(2, (width - len(line)) // 2)
                if f"PROFILE:" in line:
                    # Title in bold
                    self.renderer.draw_text(start_row + i, col, line, 1, curses.A_BOLD)
                elif "===" in line:
                    # Section headers
                    self.renderer.draw_text(start_row + i, col, line, 3, curses.A_BOLD)
                elif "Win Rate:" in line or "Most Picked" in line:
                    # Highlight key stats
                    self.renderer.draw_text(start_row + i, col, line, 2, 0)
                else:
                    # Regular text
                    self.renderer.draw_text(start_row + i, col, line, 1, 0)

        # Refresh display and wait for input
        self.renderer.refresh()
        self.renderer.get_input()  # Wait for any key press

    def _display_message(self, message: str):
        """Display a simple message screen."""
        self.renderer.clear_screen()

        # Get screen dimensions
        if hasattr(self.renderer, 'grid_height'):
            height = self.renderer.grid_height
            width = self.renderer.grid_width
        else:
            height = self.renderer.height
            width = self.renderer.width

        # Display message
        row = height // 2
        col = max(2, (width - len(message)) // 2)
        self.renderer.draw_text(row, col, message, 1, 0)

        # Instructions
        instructions = "Press any key to continue..."
        instr_row = row + 2
        instr_col = max(2, (width - len(instructions)) // 2)
        self.renderer.draw_text(instr_row, instr_col, instructions, 2, 0)

        self.renderer.refresh()
        self.renderer.get_input()

    def _quit_game(self):
        """Quit the game."""
        self.running = False
        return ("quit", None)
    

    def _draw_title_art(self, start_row: int) -> int:
        """Draw the ASCII art title and return the next available row."""
        if hasattr(self.renderer, 'grid_height'):
            width = self.renderer.grid_width
        else:
            width = self.renderer.width
        
        # ASCII art for BONEGLAIVE
        title_art = [
            "██████╗  ██████╗ ███╗   ██╗███████╗ ██████╗ ██╗      █████╗ ██╗██╗   ██╗███████╗",
            "██╔══██╗██╔═══██╗████╗  ██║██╔════╝██╔════╝ ██║     ██╔══██╗██║██║   ██║██╔════╝",
            "██████╔╝██║   ██║██╔██╗ ██║█████╗  ██║  ███╗██║     ███████║██║██║   ██║█████╗  ",
            "██╔══██╗██║   ██║██║╚██╗██║██╔══╝  ██║   ██║██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝  ",
            "██████╔╝╚██████╔╝██║ ╚████║███████╗╚██████╔╝███████╗██║  ██║██║ ╚████╔╝ ███████╗",
            "╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝"
        ]
        
        # Center and draw each line of the title
        for i, line in enumerate(title_art):
            col = max(0, (width - len(line)) // 2)
            self.renderer.draw_text(start_row + i, col, line, 1, 0)
        
        # Add subtitle
        subtitle = "v0.9.0a BETA"
        subtitle_col = max(0, (width - len(subtitle)) // 2)
        self.renderer.draw_text(start_row + len(title_art) + 1, subtitle_col, subtitle, 1, 0)
        
        return start_row + len(title_art) + 2

    def draw(self):
        """Draw the current menu."""
        menu = self.current_menu
        self.renderer.clear_screen()

        # Get screen dimensions
        if hasattr(self.renderer, 'grid_height'):
            height = self.renderer.grid_height
            width = self.renderer.grid_width
        else:
            height = self.renderer.height
            width = self.renderer.width

        # Draw current profile indicator in top-right corner
        profile = profile_manager.get_current_profile()
        if profile:
            profile_text = f"Profile: {profile.name}"
            profile_col = width - len(profile_text) - 2
            self.renderer.draw_text(1, profile_col, profile_text, 3, 0)

        # Draw title art only for main menu
        if menu.title == "Boneglaive":
            # Draw the ASCII art title
            current_row = self._draw_title_art(2)
            
            # Add some spacing before menu items
            menu_start_row = current_row + 2
        else:
            # For submenus, draw simple title
            title_text = f"=== {menu.title} ==="
            title_col = max(0, (width - len(title_text)) // 2)
            self.renderer.draw_text(2, title_col, title_text, 1, curses.A_BOLD)
            menu_start_row = 4
        
        # Calculate menu block centering - find the widest menu item
        max_item_width = max(len(item.label) for item in menu.items)
        menu_left_col = max(2, (width - max_item_width) // 2)
        
        # Draw menu items left-aligned within the centered block
        for i, item in enumerate(menu.items):
            row = menu_start_row + i
            
            if i == menu.selected_index:
                # Left-align within the centered menu block with bold styling
                self.renderer.draw_text(row, menu_left_col, item.label, 2, curses.A_BOLD)
            else:
                # Left-align within the centered menu block
                self.renderer.draw_text(row, menu_left_col, item.label, 1, 0)
        
        # Draw navigation help at bottom
        help_text = "Up/Down: Navigate | Enter: Select | Esc/c: Back | q: Quit"
        help_col = max(0, (width - len(help_text)) // 2)
        help_row = height - 3
        self.renderer.draw_text(help_row, help_col, help_text, 1, curses.A_DIM)
        
        # Refresh the display
        self.renderer.refresh()
    
    def handle_input(self, key: int):
        """Handle user input."""
        # Navigation
        if key == curses.KEY_UP:
            self.current_menu.move_selection(-1)
        elif key == curses.KEY_DOWN:
            self.current_menu.move_selection(1)
        
        # Selection
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key
            result = self.current_menu.activate_selection()
            menu_result = self._handle_menu_result(result)
            if menu_result:
                return menu_result
        
        # Back/Cancel
        elif key in [27, ord('c')]:  # Esc, c key
            result = self.current_menu.go_back()
            menu_result = self._handle_menu_result(result)
            if menu_result:
                return menu_result
        
        # Quit
        elif key == ord('q'):
            self.running = False
            return ("quit", None)
    
    def _handle_menu_result(self, result):
        """Handle the result of a menu action."""
        if not result:
            return

        action, data = result

        if action == "submenu":
            if data is None and self.current_menu.parent:
                self.current_menu = self.current_menu.parent
            elif data:
                self.current_menu = data

        elif action == "start_game":
            self.running = False
            # This ensures the result is passed up to the caller
            return ("start_game", None)

        elif action == "show_about":
            self._display_about_screen()

        elif action == "show_profile_stats":
            self._display_profile_stats()

        elif action == "show_message":
            self._display_message(data)

        elif action == "quit":
            self.running = False
            return ("quit", None)
    
    def run(self):
        """Run the menu loop."""
        while self.running:
            try:
                self.draw()
                key = self.renderer.get_input()
                result = self.handle_input(key)

                if result:
                    return result
            except KeyboardInterrupt:
                # Graceful shutdown on Ctrl+C
                self.running = False
                return ("quit", None)

        return ("quit", None)