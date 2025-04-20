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
        """Handle selection action."""
        # In setup phase, the select action places units
        if self.game.setup_phase:
            return self.mode_manager.handle_setup_select()
            
        # In multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                message_log.add_message("Not your turn!", MessageType.WARNING)
                return
        
        if self.mode_manager.mode == "select":
            # First check if there's a real unit at the cursor position
            unit = self.game.get_unit_at(self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x)
            
            # If not, check if there's a ghost unit (planned move) at this position
            if not unit:
                unit = self.cursor_manager.find_unit_by_ghost(
                    self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x)
                
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            if unit and (unit.player == current_player or self.game.test_mode or 
                     (self.multiplayer.is_local_multiplayer() and unit.player == self.game.current_player)):
                # Clear any previous selection
                self.cursor_manager.selected_unit = unit
                
                # Check if we're selecting a ghost (unit with a move_target at current position)
                is_ghost = (unit.move_target == (self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x))
                
                # Clear the message to avoid redundancy with unit info display
                self.message = ""
                # Redraw the board to immediately show the selection
                self.draw_board()
            else:
                self.message = "No valid unit selected"
                if unit:
                    message_log.add_message(
                        f"Cannot select {unit.type.name} - belongs to Player {unit.player}", 
                        MessageType.WARNING
                    )
                else:
                    message_log.add_message("No unit at that position", MessageType.WARNING)
        
        elif self.mode_manager.mode == "move":
            # Import Position to use get_line
            from boneglaive.utils.coordinates import Position, get_line
            
            # Check if the position is a valid move target
            if Position(self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x) in self.cursor_manager.highlighted_positions:
                self.cursor_manager.selected_unit.move_target = (self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x)
                
                self.message = f"Move set to ({self.cursor_manager.cursor_pos.y}, {self.cursor_manager.cursor_pos.x})"
                # No message added to log for planned movements
                self.mode_manager.mode = "select"
                self.cursor_manager.highlighted_positions = []
            else:
                # Check why the position isn't valid
                y, x = self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x
                
                # Check if the position is in range
                distance = self.game.chess_distance(self.cursor_manager.selected_unit.y, self.cursor_manager.selected_unit.x, y, x)
                if distance > self.cursor_manager.selected_unit.move_range:
                    self.message = "Position is out of movement range"
                # Check if there's an enemy unit blocking the path
                elif distance > 1:
                    # Check the path for enemy units
                    start_pos = Position(self.cursor_manager.selected_unit.y, self.cursor_manager.selected_unit.x)
                    end_pos = Position(y, x)
                    path = get_line(start_pos, end_pos)
                    
                    for pos in path[1:-1]:  # Skip start and end positions
                        blocking_unit = self.game.get_unit_at(pos.y, pos.x)
                        if blocking_unit:
                            # Determine if it's an ally or enemy for the message
                            if blocking_unit.player == self.cursor_manager.selected_unit.player:
                                self.message = "Path blocked by allied unit"
                                message_log.add_message("You cannot move through other units", MessageType.WARNING)
                            else:
                                self.message = "Path blocked by enemy unit"
                                message_log.add_message("You cannot move through other units", MessageType.WARNING)
                            return
                # Check if there's a unit at the destination
                elif self.game.get_unit_at(y, x):
                    self.message = "Position is occupied by another unit"
                # Check if the terrain is blocking
                elif not self.game.map.is_passable(y, x):
                    self.message = "Terrain is impassable"
                else:
                    self.message = "Invalid move target"
        
        elif self.mode_manager.mode == "attack":
            # Import Position for position checking
            from boneglaive.utils.coordinates import Position
            
            if Position(self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x) in self.cursor_manager.highlighted_positions:
                self.cursor_manager.selected_unit.attack_target = (self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x)
                target = self.game.get_unit_at(self.cursor_manager.cursor_pos.y, self.cursor_manager.cursor_pos.x)
                
                self.message = f"Attack set against {target.type.name}"
                # No message added to log for planned attacks
                self.mode_manager.mode = "select"
                self.cursor_manager.highlighted_positions = []
            else:
                self.message = "Invalid attack target"
    
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