#!/usr/bin/env python3
"""
Menu system for the game.
Handles main menu, settings, and multiplayer lobby.
"""

import curses
import sys
from typing import Dict, List, Optional, Tuple, Callable

from boneglaive.utils.config import ConfigManager, NetworkMode, DisplayMode
from boneglaive.utils.debug import debug_config, logger
from boneglaive.renderers.curses_renderer import CursesRenderer
from boneglaive.utils.render_interface import RenderInterface

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
    
    def __init__(self, stdscr):
        self.config = ConfigManager()
        self.renderer = CursesRenderer(stdscr)
        self.renderer.initialize()
        self.current_menu = self._create_main_menu()
        self.running = True
        
        # Draw the menu immediately to avoid black screen
        self.draw()
    
    def _create_main_menu(self) -> Menu:
        """Create the main menu."""
        # Create submenus first
        play_menu = Menu("Play Game", [
            MenuItem("Single Player", self._start_single_player),
            MenuItem("VS AI", self._start_vs_ai),
            MenuItem("Local Multiplayer", self._start_local_multiplayer),
            MenuItem("Host LAN Game", self._start_lan_host),
            MenuItem("Join LAN Game", self._start_lan_client),
            MenuItem("Back", lambda: ("submenu", None))
        ])
        
        settings_menu = Menu("Settings", [
            MenuItem("Display Settings", lambda: ("submenu", self._create_display_settings_menu())),
            MenuItem("Network Settings", lambda: ("submenu", self._create_network_settings_menu())),
            MenuItem("Back", lambda: ("submenu", None))
        ])
        
        # Create main menu
        main_menu = Menu("Boneglaive", [
            MenuItem("Play", None, play_menu),
            MenuItem("Settings", None, settings_menu),
            MenuItem("Help", self._show_help),
            MenuItem("Quit", self._quit_game)
        ])
        
        # Set parent menus
        play_menu.parent = main_menu
        settings_menu.parent = main_menu
        
        return main_menu
    
    def _create_display_settings_menu(self) -> Menu:
        """Create the display settings menu."""
        menu = Menu("Display Settings", [
            MenuItem("Text Mode", lambda: self._set_display_mode(DisplayMode.TEXT.value)),
            MenuItem("Graphical Mode (Not Implemented)", lambda: self._set_display_mode(DisplayMode.GRAPHICAL.value)),
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
    
    def _start_single_player(self):
        """Start a single player game."""
        self.config.set('network_mode', NetworkMode.SINGLE_PLAYER.value)
        self.config.save_config()
        logger.info("Starting single player game")
        return ("start_game", None)
    
    def _start_local_multiplayer(self):
        """Start a local multiplayer game."""
        self.config.set('network_mode', NetworkMode.LOCAL_MULTIPLAYER.value)
        self.config.save_config()
        logger.info("Starting local multiplayer game")
        return ("start_game", None)
    
    def _start_lan_host(self):
        """Start hosting a LAN game."""
        self.config.set('network_mode', NetworkMode.LAN_HOST.value)
        self.config.save_config()
        logger.info("Starting LAN game host")
        return ("start_game", None)
    
    def _start_lan_client(self):
        """Start joining a LAN game."""
        self.config.set('network_mode', NetworkMode.LAN_CLIENT.value)
        self.config.save_config()
        logger.info("Starting LAN game client")
        return ("start_game", None)
        
    def _start_vs_ai(self):
        """Start a game against the AI."""
        self.config.set('network_mode', NetworkMode.VS_AI.value)
        self.config.save_config()
        logger.info("Starting VS AI game")
        return ("start_game", None)
    
    def _set_display_mode(self, mode: str):
        """Set the display mode."""
        self.config.set('display_mode', mode)
        self.config.save_config()
        return None
    
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
    
    def _show_help(self):
        """Show the help screen."""
        # In a real implementation, this would show a help screen
        return None
    
    def _quit_game(self):
        """Quit the game."""
        self.running = False
        return ("quit", None)
    
    def draw(self):
        """Draw the current menu."""
        menu = self.current_menu
        self.renderer.clear_screen()
        
        # Draw title
        title_text = f"{menu.title}"
        self.renderer.draw_text(1, 2, title_text, 1, curses.A_BOLD)
        
        # Draw menu items
        for i, item in enumerate(menu.items):
            # Create more visually distinct selection indicator
            if i == menu.selected_index:
                # Draw selection indicator for selected item
                self.renderer.draw_text(3 + i, 2, "> ", 2, curses.A_BOLD)
                self.renderer.draw_text(3 + i, 4, item.label, 2, curses.A_BOLD)
            else:
                self.renderer.draw_text(3 + i, 4, item.label, 1, 0)
        
        # Draw navigation help
        self.renderer.draw_text(3 + len(menu.items) + 2, 2, 
                              "↑↓: Navigate | Enter: Select | Esc/Backspace: Back", 1)
        
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
        
        # Back
        elif key in [27, curses.KEY_BACKSPACE, 8, 127]:  # Esc, Backspace
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
        
        elif action == "quit":
            self.running = False
            return ("quit", None)
    
    def run(self):
        """Run the menu loop."""
        while self.running:
            self.draw()
            key = self.renderer.get_input()
            result = self.handle_input(key)
            
            if result:
                return result
        
        return ("quit", None)