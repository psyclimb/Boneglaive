#!/usr/bin/env python3
import curses
from typing import Optional, List, Tuple, Dict

from boneglaive.utils.constants import HEIGHT, WIDTH, UnitType
from boneglaive.game.engine import Game
from boneglaive.utils.coordinates import Position
from boneglaive.utils.debug import debug_config, measure_perf, logger
from boneglaive.utils.asset_manager import AssetManager
from boneglaive.utils.config import ConfigManager
from boneglaive.utils.input_handler import InputHandler, GameAction
from boneglaive.renderers.curses_renderer import CursesRenderer
from boneglaive.utils.render_interface import RenderInterface
from boneglaive.utils.message_log import message_log, MessageType

# Import component classes
from boneglaive.ui.ui_components import (
    MessageLogComponent, HelpComponent, ChatComponent, 
    CursorManager, GameModeManager, DebugComponent,
    AnimationComponent, InputManager
)
from boneglaive.ui.ui_renderer import UIRenderer

class GameUI:
    """User interface for the game - refactored to use component architecture."""
    
    def __init__(self, stdscr):
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Set up renderer
        self.renderer = CursesRenderer(stdscr)
        self.renderer.initialize()
        
        # Set up asset manager
        self.asset_manager = AssetManager(self.config_manager)
        
        # Set up input handler
        self.input_handler = InputHandler()
        
        # Game state with setup phase by default
        self.game = Game(skip_setup=False)
        
        # Set up multiplayer manager
        from boneglaive.game.multiplayer_manager import MultiplayerManager
        self.multiplayer = MultiplayerManager(self.game)
        
        # Message buffer for UI feedback
        self.message = ""
        
        # Initialize components (order matters due to dependencies)
        self.cursor_manager = CursorManager(self.renderer, self)
        self.help_component = HelpComponent(self.renderer, self)
        self.message_log_component = MessageLogComponent(self.renderer, self)
        self.chat_component = ChatComponent(self.renderer, self)
        self.mode_manager = GameModeManager(self.renderer, self)
        self.debug_component = DebugComponent(self.renderer, self)
        self.animation_component = AnimationComponent(self.renderer, self)
        self.input_manager = InputManager(self.renderer, self, self.input_handler)
        self.ui_renderer = UIRenderer(self.renderer, self)
        
        # Only show welcome message when not in setup phase
        if not self.game.setup_phase:
            message_log.add_system_message(f"Entering {self.game.map.name}")
        
        # Only show game mode message when not in setup phase
        if not self.game.setup_phase:
            if self.multiplayer.is_local_multiplayer():
                message_log.add_system_message("Local multiplayer mode. Players will take turns on this computer.")
            elif self.multiplayer.is_network_multiplayer():
                message_log.add_system_message("LAN multiplayer mode. Connected to remote player.")
        
        # Update message with current player
        self.update_player_message()
    
    def update_player_message(self):
        """Update the message showing the current player (only in message log)."""
        # Don't show any player messages during setup phase
        if self.game.setup_phase:
            return
            
        current_player = self.multiplayer.get_current_player()
        
        if self.multiplayer.is_multiplayer():
            if self.multiplayer.is_current_player_turn():
                message_log.add_system_message(f"Turn {self.game.turn}, Player {current_player}'s turn (YOU)")
            else:
                message_log.add_system_message(f"Turn {self.game.turn}, Player {current_player}'s turn (WAITING)")
        else:
            message_log.add_system_message(f"Turn {self.game.turn}, Player {self.game.current_player}'s turn")
        
        # Keep the message display area clear
        self.message = ""
    
    def handle_select(self):
        """Route selection to appropriate handler based on mode."""
        # In setup phase, the select action places units
        if self.game.setup_phase:
            return self.mode_manager.handle_setup_select()
        
        # Check if player can act on this turn
        if not self.cursor_manager.can_act_this_turn():
            self.message = "Not your turn!"
            message_log.add_message("Not your turn!", MessageType.WARNING)
            return
        
        # Route to appropriate mode handler
        if self.mode_manager.mode == "select":
            self.mode_manager.handle_select_in_select_mode()
        elif self.mode_manager.mode == "move":
            self.mode_manager.handle_select_in_move_mode()
        elif self.mode_manager.mode == "attack":
            self.mode_manager.handle_select_in_attack_mode()
    
    def draw_board(self, show_cursor=True, show_selection=True, show_attack_targets=True):
        """Delegate board drawing to the UI renderer component."""
        self.ui_renderer.draw_board(show_cursor, show_selection, show_attack_targets)
    
    def show_attack_animation(self, attacker, target):
        """Delegate animation to the animation component."""
        self.animation_component.show_attack_animation(attacker, target)
    
    def handle_input(self, key: int) -> bool:
        """Handle user input using the input manager."""
        # Handle setup instructions screen
        if self.game.setup_phase and self.mode_manager.show_setup_instructions:
            self.mode_manager.show_setup_instructions = False
            self.draw_board()
            return True
        
        # Delegate input handling to the input manager
        return self.input_manager.process_input(key)