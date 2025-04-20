#!/usr/bin/env python3
import curses
import time
import json
import os
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

class GameUI:
    """User interface for the game."""
    
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
        self._setup_input_callbacks()
        
        # Game state
        self.game = Game()
        
        # Set up multiplayer manager
        from boneglaive.game.multiplayer_manager import MultiplayerManager
        self.multiplayer = MultiplayerManager(self.game)
        
        self.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)
        self.selected_unit = None
        self.highlighted_positions = []
        self.mode = "select"  # select, move, attack
        self.message = ""
        self.show_log = True  # Whether to show the message log
        self.log_height = 5   # Number of log lines to display
        self.show_help = False  # Whether to show help screen
        self.chat_mode = False  # Whether in chat input mode
        self.chat_input = ""  # Current chat input text
        self.player_colors = {1: 3, 2: 4}  # Player colors (matching message_log)
        
        # Welcome message
        message_log.add_system_message("Welcome to Boneglaive!")
        
        # Add game mode message
        if self.multiplayer.is_local_multiplayer():
            message_log.add_system_message("Local multiplayer mode. Players will take turns on this computer.")
        elif self.multiplayer.is_network_multiplayer():
            message_log.add_system_message("LAN multiplayer mode. Connected to remote player.")
        
        # Update message with current player
        self._update_player_message()
    
    def _setup_input_callbacks(self):
        """Set up callbacks for input handling."""
        self.input_handler.register_action_callbacks({
            GameAction.MOVE_UP: lambda: self._move_cursor(-1, 0),
            GameAction.MOVE_DOWN: lambda: self._move_cursor(1, 0),
            GameAction.MOVE_LEFT: lambda: self._move_cursor(0, -1),
            GameAction.MOVE_RIGHT: lambda: self._move_cursor(0, 1),
            GameAction.SELECT: self._handle_select,
            GameAction.CANCEL: self._handle_cancel,
            GameAction.MOVE_MODE: self._handle_move_mode,
            GameAction.ATTACK_MODE: self._handle_attack_mode,
            GameAction.END_TURN: self._handle_end_turn,
            GameAction.TEST_MODE: self._handle_test_mode,
            GameAction.DEBUG_INFO: self._handle_debug_info,
            GameAction.DEBUG_TOGGLE: self._handle_debug_toggle,
            GameAction.DEBUG_OVERLAY: self._handle_debug_overlay,
            GameAction.DEBUG_PERFORMANCE: self._handle_debug_performance,
            GameAction.DEBUG_SAVE: self._handle_debug_save,
            GameAction.HELP: self._toggle_help_screen,
            GameAction.CHAT_MODE: self._toggle_chat_mode
        })
        
        # Add custom key for toggling message log
        self.input_handler.add_mapping(ord('l'), GameAction.DEBUG_INFO)  # Reuse DEBUG_INFO for log toggle
        
    def _toggle_message_log(self):
        """Toggle the message log display."""
        self.show_log = not self.show_log
        self.message = f"Message log {'shown' if self.show_log else 'hidden'}"
        message_log.add_system_message(f"Message log {'shown' if self.show_log else 'hidden'}")
    
    def _toggle_help_screen(self):
        """Toggle the help screen display."""
        # Can't use help screen while in chat mode
        if self.chat_mode:
            return
            
        self.show_help = not self.show_help
        self.draw_board()  # Redraw the board immediately to show/hide help
        message_log.add_system_message(f"Help screen {'shown' if self.show_help else 'hidden'}")
        
    def _toggle_chat_mode(self):
        """Toggle chat input mode."""
        # Can't use chat while help screen is shown
        if self.show_help:
            return
            
        # Toggle chat mode
        self.chat_mode = not self.chat_mode
        
        # Clear any existing input when entering chat mode
        if self.chat_mode:
            self.chat_input = ""
            self.message = "Chat mode: Type message and press Enter to send, Escape to cancel"
            # Ensure log is visible when entering chat mode
            if not self.show_log:
                self._toggle_message_log()
        else:
            self.message = "Chat mode exited"
            
        # Redraw the board
        self.draw_board()
    
    def _move_cursor(self, dy: int, dx: int):
        """Move the cursor by the given delta."""
        new_y = max(0, min(HEIGHT-1, self.cursor_pos.y + dy))
        new_x = max(0, min(WIDTH-1, self.cursor_pos.x + dx))
        self.cursor_pos = Position(new_y, new_x)
    
    def _find_unit_by_ghost(self, y, x):
        """
        Find a unit that has a move target at the given position.
        
        Args:
            y, x: The position to check for a ghost unit
            
        Returns:
            The unit that has a move target at (y, x), or None if no such unit exists
        """
        for unit in self.game.units:
            if unit.is_alive() and unit.move_target == (y, x):
                return unit
        return None
    
    def _handle_select(self):
        """Handle selection action."""
        # In multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                message_log.add_message("Not your turn!", MessageType.WARNING)
                return
        
        if self.mode == "select":
            # First check if there's a real unit at the cursor position
            unit = self.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            
            # If not, check if there's a ghost unit (planned move) at this position
            if not unit:
                unit = self._find_unit_by_ghost(self.cursor_pos.y, self.cursor_pos.x)
                
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            if unit and (unit.player == current_player or self.game.test_mode or 
                         (self.multiplayer.is_local_multiplayer() and unit.player == self.game.current_player)):
                # Clear any previous selection
                self.selected_unit = unit
                
                # Check if we're selecting a ghost (unit with a move_target at current position)
                is_ghost = (unit.move_target == (self.cursor_pos.y, self.cursor_pos.x))
                
                if is_ghost:
                    self.message = f"Selected {unit.type.name} (ghost at planned position)"
                    message_log.add_message(
                        f"Selected {unit.type.name} at planned position ({self.cursor_pos.y},{self.cursor_pos.x})", 
                        MessageType.SYSTEM,
                        player=current_player
                    )
                else:
                    self.message = f"Selected {unit.type.name}"
                    message_log.add_message(
                        f"Selected {unit.type.name} at ({unit.y},{unit.x})", 
                        MessageType.SYSTEM,
                        player=current_player
                    )
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
        
        elif self.mode == "move" and Position(self.cursor_pos.y, self.cursor_pos.x) in self.highlighted_positions:
            self.selected_unit.move_target = (self.cursor_pos.y, self.cursor_pos.x)
            unit_type = self.selected_unit.type.name
            start_pos = (self.selected_unit.y, self.selected_unit.x)
            end_pos = (self.cursor_pos.y, self.cursor_pos.x)
            
            self.message = f"Move set to ({self.cursor_pos.y}, {self.cursor_pos.x})"
            message_log.add_message(
                f"{unit_type} will move from {start_pos} to {end_pos}", 
                MessageType.MOVEMENT,
                player=self.selected_unit.player
            )
            self.mode = "select"
            self.highlighted_positions = []
        
        elif self.mode == "attack" and Position(self.cursor_pos.y, self.cursor_pos.x) in self.highlighted_positions:
            self.selected_unit.attack_target = (self.cursor_pos.y, self.cursor_pos.x)
            target = self.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            
            self.message = f"Attack set against {target.type.name}"
            message_log.add_message(
                f"{self.selected_unit.type.name} will attack {target.type.name}", 
                MessageType.COMBAT,
                player=self.selected_unit.player,
                target=target.player
            )
            self.mode = "select"
            self.highlighted_positions = []
    
    def _handle_cancel(self):
        """
        Handle cancel action (Escape key or 'c' key).
        Cancels the current action based on the current state.
        """
        # First check if help screen is showing - cancel it
        if self.show_help:
            self.show_help = False
            self.message = "Help screen closed"
            self.draw_board()
            return
            
        # If in chat mode, cancel chat (handled in _handle_chat_input for Escape)
        if self.chat_mode:
            self.chat_mode = False
            self.message = "Chat cancelled"
            self.draw_board()
            return
            
        # If in attack or move mode, cancel the mode but keep unit selected
        if self.mode in ["attack", "move"] and self.selected_unit:
            self.highlighted_positions = []
            self.mode = "select"
            self.message = f"{self.mode.capitalize()} mode cancelled, unit still selected"
            self.draw_board()
            return
            
        # If unit is selected with a planned move, cancel the move
        if self.selected_unit and self.selected_unit.move_target:
            self.selected_unit.move_target = None
            self.message = "Move order cancelled"
            self.draw_board()
            return
            
        # If unit is selected with a planned attack, cancel the attack
        if self.selected_unit and self.selected_unit.attack_target:
            self.selected_unit.attack_target = None
            self.message = "Attack order cancelled"
            self.draw_board()
            return
            
        # Otherwise, clear the selection entirely
        self.selected_unit = None
        self.highlighted_positions = []
        self.mode = "select"
        self.message = "Selection cleared"
        
        # Redraw the board to immediately update selection visuals
        self.draw_board()
    
    def _handle_move_mode(self):
        """Enter move mode."""
        # In network multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_network_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                return
                
        if self.selected_unit:
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            # Also allow control in local multiplayer for the active player
            if (self.selected_unit.player == current_player or
                self.game.test_mode or
                (self.multiplayer.is_local_multiplayer() and self.selected_unit.player == self.game.current_player)):
                self.mode = "move"
                
                # Convert positions to Position objects
                self.highlighted_positions = [
                    Position(y, x) for y, x in self.game.get_possible_moves(self.selected_unit)
                ]
                
                if not self.highlighted_positions:
                    self.message = "No valid moves available"
            else:
                self.message = "You can only move your own units!"
        else:
            self.message = "No unit selected"
    
    def _handle_attack_mode(self):
        """Enter attack mode."""
        # In network multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_network_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                return
                
        if self.selected_unit:
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            # Also allow control in local multiplayer for the active player
            if (self.selected_unit.player == current_player or 
                self.game.test_mode or
                (self.multiplayer.is_local_multiplayer() and self.selected_unit.player == self.game.current_player)):
                self.mode = "attack"
                
                # If we selected a unit directly, use its position
                # If we selected a ghost, always use the ghost position
                from_pos = None
                if self.selected_unit.move_target:
                    from_pos = self.selected_unit.move_target
                    self.message = "Select attack from planned move position"
                else:
                    self.message = "Select attack target"
                
                # Convert positions to Position objects, using move destination if set
                self.highlighted_positions = [
                    Position(y, x) for y, x in self.game.get_possible_attacks(self.selected_unit, from_pos)
                ]
                
                if not self.highlighted_positions:
                    if self.selected_unit.move_target:
                        self.message = "No valid targets in range from move destination"
                    else:
                        self.message = "No valid targets in range"
            else:
                self.message = "You can only attack with your own units!"
        else:
            self.message = "No unit selected"
    
    def _handle_end_turn(self):
        """End the current turn."""
        # Pass UI to execute_turn for animations
        self.game.execute_turn(self)
        self.selected_unit = None
        self.highlighted_positions = []
        self.mode = "select"
        
        # Handle multiplayer turn switching
        if not self.game.winner:
            # End turn in multiplayer manager
            self.multiplayer.end_turn()
            self._update_player_message()
            
        # Redraw the board to update visuals
        self.draw_board()
    
    def _update_player_message(self):
        """Update the message showing the current player (only in message log)."""
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
    
    def _handle_test_mode(self):
        """Toggle test mode."""
        self.game.toggle_test_mode()
        if self.game.test_mode:
            self.message = "Test mode ON - both players can control all units"
            message_log.add_system_message("Test mode enabled")
        else:
            self.message = "Test mode OFF"
            message_log.add_system_message("Test mode disabled")
    
    def _handle_debug_info(self):
        """Toggle message log or show debug info."""
        # Toggle message log when 'l' is pressed
        if self.input_handler.action_map.get(ord('l')) == GameAction.DEBUG_INFO:
            self._toggle_message_log()
            return
            
        # Otherwise show unit positions
        debug_info = []
        for unit in self.game.units:
            if unit.is_alive():
                debug_info.append(f"({unit.y},{unit.x})")
        self.message = f"Unit positions: {' '.join(debug_info)}"
        logger.debug(f"Unit positions: {debug_info}")
    
    def _handle_debug_toggle(self):
        """Toggle debug mode."""
        debug_enabled = debug_config.toggle()
        self.message = f"Debug mode {'ON' if debug_enabled else 'OFF'}"
        
        message_text = f"Debug mode {'enabled' if debug_enabled else 'disabled'}"
        logger.info(message_text)
        message_log.add_message(message_text, MessageType.DEBUG)
    
    def _handle_debug_overlay(self):
        """Toggle debug overlay."""
        overlay_enabled = debug_config.toggle_overlay()
        self.message = f"Debug overlay {'ON' if overlay_enabled else 'OFF'}"
    
    def _handle_debug_performance(self):
        """Toggle performance tracking."""
        perf_enabled = debug_config.toggle_perf_tracking()
        self.message = f"Performance tracking {'ON' if perf_enabled else 'OFF'}"
    
    def _handle_debug_save(self):
        """Save game state to file."""
        if not debug_config.enabled:
            return
            
        try:
            game_state = self.game.get_game_state()
            os.makedirs('debug', exist_ok=True)
            filename = f"debug/game_state_turn{self.game.turn}.json"
            with open(filename, 'w') as f:
                json.dump(game_state, f, indent=2)
            self.message = f"Game state saved to {filename}"
            logger.info(f"Game state saved to {filename}")
        except Exception as e:
            self.message = f"Error saving game state: {str(e)}"
            logger.error(f"Error saving game state: {str(e)}")
    
    @measure_perf
    def show_attack_animation(self, attacker, target):
        """Show a visual animation for attacks."""
        # Get attack effect from asset manager
        effect_tile = self.asset_manager.get_attack_effect(attacker.type)
        
        # Create start and end positions
        start_pos = Position(attacker.y, attacker.x)
        end_pos = Position(target.y, target.x)
        
        # For ranged attacks (archer and mage), show projectile path
        if attacker.type in [UnitType.ARCHER, UnitType.MAGE]:
            # Animate projectile using renderer
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                effect_tile,
                7,  # color ID
                0.1  # duration
            )
        # For melee attacks (glaiveman), just flash the effect on target
        else:
            # Draw effect at target position
            self.renderer.draw_tile(target.y, target.x, effect_tile, 7)
            self.renderer.refresh()
            time.sleep(0.2)
        
        # Flash the target to show it was hit
        tile_ids = [self.asset_manager.get_unit_tile(target.type)] * 6
        color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 3
        durations = [0.1] * 6
        
        # Use renderer's flash tile method
        self.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Show damage number above target
        damage = max(1, attacker.attack - target.defense)
        self.renderer.draw_text(target.y+1, target.x*2, f"-{damage}", 7, curses.A_BOLD)
        self.renderer.refresh()
        time.sleep(0.5)
        
        # Redraw board to clear effects (without cursor or selection highlighting)
        self.draw_board(show_cursor=False, show_selection=False)
    
    @measure_perf
    def draw_board(self, show_cursor=True, show_selection=True):
        """
        Draw the game board and UI.
        
        Args:
            show_cursor: Whether to show the cursor (default: True)
            show_selection: Whether to show selected unit highlighting (default: True)
        """
        # Set cursor visibility
        self.renderer.set_cursor(False)  # Always hide the physical cursor
        
        # Clear screen
        self.renderer.clear_screen()
        
        # If help screen is being shown, draw it and return
        if self.show_help:
            self._draw_help_screen()
            self.renderer.refresh()
            return
        
        # Draw header
        current_player = self.multiplayer.get_current_player()
        game_mode = "Single" if not self.multiplayer.is_multiplayer() else "Local" if self.multiplayer.is_local_multiplayer() else "LAN"
        
        # Get player color for the header
        player_color = self.player_colors.get(current_player, 1)
        
        # Create shorter player indicator
        player_indicator = f"Player {current_player}"
        
        # Build the rest of the header
        header = f"{player_indicator} | Mode: {self.mode} | Game: {game_mode}"
        if self.multiplayer.is_network_multiplayer():  # Only show YOUR TURN/WAITING in network multiplayer
            header += f" | {'YOUR TURN' if self.multiplayer.is_current_player_turn() else 'WAITING'}"
            
        if self.chat_mode:
            header += " | CHAT MODE"
            
        if debug_config.enabled:
            header += " | DEBUG ON"
        
        # Draw player indicator with player color and the rest with default color
        self.renderer.draw_text(0, 0, player_indicator, player_color, curses.A_BOLD)
        self.renderer.draw_text(0, len(player_indicator), header[len(player_indicator):], 1)
        
        # Draw the battlefield
        for y in range(HEIGHT):
            for x in range(WIDTH):
                pos = Position(y, x)
                
                # Default content is empty ground
                tile = self.asset_manager.get_terrain_tile("empty")
                color_id = 1  # Default color
                
                # Check if there's a unit at this position
                unit = self.game.get_unit_at(y, x)
                
                # Check if any unit has a move target set to this position
                target_unit = None
                for u in self.game.units:
                    if u.is_alive() and u.move_target == (y, x):
                        target_unit = u
                        break
                        
                # Check if any unit is targeting this position for attack
                attacking_unit = None
                for u in self.game.units:
                    if u.is_alive() and u.attack_target == (y, x):
                        attacking_unit = u
                        break
                
                if unit:
                    # There's a real unit here
                    tile = self.asset_manager.get_unit_tile(unit.type)
                    color_id = 3 if unit.player == 1 else 4
                    
                    # If this unit is being targeted for attack, use red background
                    if attacking_unit:
                        # Check if cursor is here before drawing targeted unit
                        is_cursor_here = (pos == self.cursor_pos and show_cursor)
                        
                        if is_cursor_here:
                            # Draw with cursor color but still bold to show it's selected
                            self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                        else:
                            # Use red background to show this unit is targeted for attack
                            self.renderer.draw_tile(y, x, tile, 10, curses.A_BOLD)
                        continue
                        
                    # If this is the selected unit and we should show selection, use special highlighting
                    if show_selection and self.selected_unit and unit == self.selected_unit:
                        # Check if cursor is also here
                        is_cursor_here = (pos == self.cursor_pos and show_cursor)
                        
                        if is_cursor_here:
                            # Draw with cursor color but bold to show it's selected
                            self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                        else:
                            # Use yellow background to highlight the selected unit
                            self.renderer.draw_tile(y, x, tile, 9, curses.A_BOLD)
                        continue
                
                elif target_unit and not unit:
                    # This is a move target location - draw a "ghost" of the moving unit
                    tile = self.asset_manager.get_unit_tile(target_unit.type)
                    color_id = 8  # Gray preview color
                    
                    # Check if it's selected (user selected the ghost)
                    is_selected = show_selection and self.selected_unit and self.selected_unit == target_unit and self.selected_unit.move_target == (y, x)
                    
                    # Check if cursor is here
                    is_cursor_here = (pos == self.cursor_pos and show_cursor)
                    
                    if is_selected:
                        # Draw as selected ghost (yellow background)
                        self.renderer.draw_tile(y, x, tile, 9, curses.A_DIM)
                        continue
                    elif is_cursor_here:
                        # Draw with cursor color
                        self.renderer.draw_tile(y, x, tile, 2)
                        continue
                    
                    # Otherwise draw normal ghost
                    self.renderer.draw_tile(y, x, tile, color_id, curses.A_DIM)
                
                # Check if position is highlighted for movement or attack
                if pos in self.highlighted_positions:
                    if self.mode == "move":
                        color_id = 5
                    elif self.mode == "attack":
                        color_id = 6
                
                # Cursor takes priority for visibility when it should be shown
                if show_cursor and pos == self.cursor_pos:
                    color_id = 2
                
                # Draw the cell
                self.renderer.draw_tile(y, x, tile, color_id)
                
        # Draw message log if enabled
        if self.show_log:
            self._draw_message_log()
            
        # Draw chat input field if in chat mode
        if self.chat_mode:
            self._draw_chat_input()
        
        # Draw unit info
        if self.selected_unit:
            unit = self.selected_unit
            unit_info = f"Selected: {unit.type.name} | HP: {unit.hp}/{unit.max_hp} | " \
                        f"ATK: {unit.attack} | DEF: {unit.defense} | " \
                        f"Move: {unit.move_range} | Range: {unit.attack_range}"
            self.renderer.draw_text(HEIGHT+1, 0, unit_info)
        
        # Draw message
        self.renderer.draw_text(HEIGHT+2, 0, self.message)
        
        # Draw simplified help reminder
        help_text = "Press ? for help"
        self.renderer.draw_text(HEIGHT+3, 0, help_text)
        
        # Draw winner info if game is over
        if self.game.winner:
            self.renderer.draw_text(HEIGHT+4, 0, f"Player {self.game.winner} wins!", curses.A_BOLD)
        
        # Draw debug overlay if enabled
        if debug_config.show_debug_overlay:
            try:
                # Get debug information
                overlay_lines = debug_config.get_debug_overlay()
                
                # Add game state info
                game_state = self.game.get_game_state()
                overlay_lines.append(f"Game State: Turn {game_state['turn']}, Player {game_state['current_player']}")
                overlay_lines.append(f"Units: {len(game_state['units'])}")
                
                # Display overlay below message log
                line_offset = HEIGHT + 5 + self.log_height + 2
                for i, line in enumerate(overlay_lines):
                    self.renderer.draw_text(line_offset + i, 0, line, 1, curses.A_DIM)
            except Exception as e:
                # Never let debug features crash the game
                logger.error(f"Error displaying debug overlay: {str(e)}")
        
        self.renderer.refresh()
    
    def _draw_message_log(self):
        """Draw the message log in the game UI."""
        try:
            # Get formatted messages (with colors)
            messages = message_log.get_formatted_messages(self.log_height)
            
            # Calculate position for the log (closer to the game info)
            start_y = HEIGHT + 5
            
            # Draw message log header
            self.renderer.draw_text(start_y, 0, "=== MESSAGE LOG ===", 1, curses.A_BOLD)
            
            # Draw messages in reverse order (newest at the bottom)
            for i, (text, color_id) in enumerate(reversed(messages)):
                y_pos = start_y + self.log_height - i
                
                # Add bold attribute for player messages to make them stand out more
                attributes = 0
                if "[Player " in text:  # It's a chat message
                    attributes = curses.A_BOLD
                
                self.renderer.draw_text(y_pos, 2, text, color_id, attributes)
        except Exception as e:
            # Never let message log crash the game
            logger.error(f"Error displaying message log: {str(e)}")
    
    def _draw_chat_input(self):
        """Draw the chat input field at the bottom of the message log."""
        try:
            # Calculate position for the chat input (below the message log)
            input_y = HEIGHT + 5 + self.log_height + 1
            
            # Calculate the current player
            current_player = self.multiplayer.get_current_player()
            player_color = self.player_colors.get(current_player, 1)
            
            # Draw the input prompt with player-specific color
            prompt = f"[Player {current_player}]> "
            self.renderer.draw_text(input_y, 0, prompt, player_color)
            
            # Draw the input text with a cursor at the end
            current_input = self.chat_input + "_"  # Add a simple cursor
            self.renderer.draw_text(input_y, len(prompt), current_input, player_color)
        except Exception as e:
            # Never let chat input crash the game
            logger.error(f"Error displaying chat input: {str(e)}")
    
    def _draw_help_screen(self):
        """Draw the help screen overlay."""
        try:
            # Clear the screen area for help display
            self.renderer.clear_screen()
            
            # Draw help title
            self.renderer.draw_text(2, 2, "=== BONEGLAIVE HELP ===", 1, curses.A_BOLD)
            
            # Draw control information section
            self.renderer.draw_text(4, 2, "BASIC CONTROLS:", 1, curses.A_BOLD)
            controls = [
                "Arrow keys: Move cursor",
                "Enter: Select unit/confirm action",
                "m: Move selected unit",
                "a: Attack with selected unit",
                "e: End turn",
                "Esc: Cancel current action/selection",
                "c: Clear selection (same as Esc)",
                "l: Toggle message log",
                "r: Enter chat/message mode",
                "t: Toggle test mode (allows controlling both players' units)",
                "q: Quit game",
                "?: Toggle this help screen"
            ]
            
            for i, control in enumerate(controls):
                self.renderer.draw_text(6 + i, 4, control)
            
            # Draw debug controls section
            self.renderer.draw_text(17, 2, "DEBUG CONTROLS:", 1, curses.A_BOLD)
            debug_controls = [
                "d: Show unit positions",
                "D (Shift+D): Toggle debug mode",
                "O (Shift+O): Toggle debug overlay",
                "P (Shift+P): Toggle performance tracking",
                "S (Shift+S): Save game state to file (debug mode only)"
            ]
            
            for i, control in enumerate(debug_controls):
                self.renderer.draw_text(19 + i, 4, control)
            
            # Footer
            self.renderer.draw_text(HEIGHT - 2, 2, "Press ? again to return to game", 1, curses.A_BOLD)
            
        except Exception as e:
            logger.error(f"Error displaying help screen: {str(e)}")
    
    def handle_input(self, key: int) -> bool:
        """
        Handle user input.
        Returns True to continue running, False to quit.
        """
        # Quick exit for 'q' key (except in chat mode)
        if key == ord('q') and not self.chat_mode:
            return False
        
        # If in chat mode, handle chat input
        if self.chat_mode:
            return self._handle_chat_input(key)
        
        # Process through input handler
        return self.input_handler.process_input(key)
        
    def _handle_chat_input(self, key: int) -> bool:
        """
        Handle input while in chat mode.
        Returns True to continue running, False to quit.
        """
        # Check for special keys
        if key == 27:  # Escape key - exit chat mode (handled separately from CANCEL action)
            self.chat_mode = False
            self.message = "Chat cancelled"
            self.draw_board()
            return True
            
        elif key == 10 or key == 13:  # Enter key - send message
            if self.chat_input.strip():  # Only send non-empty messages
                # Get current player
                current_player = self.multiplayer.get_current_player()
                
                # Add message to log with player information
                message_log.add_player_message(current_player, self.chat_input)
                
                # Clear input and exit chat mode
                self.chat_input = ""
                self.chat_mode = False
                self.message = "Message sent"
            else:
                # Empty message, just exit chat mode
                self.chat_mode = False
                self.message = "Chat cancelled"
                
            self.draw_board()
            return True
            
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
            # Remove last character
            if self.chat_input:
                self.chat_input = self.chat_input[:-1]
                self.draw_board()
            return True
            
        elif 32 <= key <= 126:  # Printable ASCII characters
            # Add character to input (limit to reasonable length)
            if len(self.chat_input) < 60:  # Limit message length
                self.chat_input += chr(key)
                self.draw_board()
            return True
            
        # Ignore other keys in chat mode
        return True