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
            GameAction.DEBUG_SAVE: self._handle_debug_save
        })
        
        # Add custom key for toggling message log
        self.input_handler.add_mapping(ord('l'), GameAction.DEBUG_INFO)  # Reuse DEBUG_INFO for log toggle
        
    def _toggle_message_log(self):
        """Toggle the message log display."""
        self.show_log = not self.show_log
        self.message = f"Message log {'shown' if self.show_log else 'hidden'}"
        message_log.add_system_message(f"Message log {'shown' if self.show_log else 'hidden'}")
    
    def _move_cursor(self, dy: int, dx: int):
        """Move the cursor by the given delta."""
        new_y = max(0, min(HEIGHT-1, self.cursor_pos.y + dy))
        new_x = max(0, min(WIDTH-1, self.cursor_pos.x + dx))
        self.cursor_pos = Position(new_y, new_x)
    
    def _handle_select(self):
        """Handle selection action."""
        # In multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                message_log.add_message("Not your turn!", MessageType.WARNING)
                return
        
        if self.mode == "select":
            unit = self.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            if unit and (unit.player == current_player or self.game.test_mode):
                self.selected_unit = unit
                self.message = f"Selected {unit.type.name}"
                message_log.add_message(
                    f"Selected {unit.type.name} at ({unit.y},{unit.x})", 
                    MessageType.SYSTEM,
                    player=current_player
                )
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
        """Handle cancel action."""
        self.selected_unit = None
        self.highlighted_positions = []
        self.mode = "select"
        self.message = "Selection cleared"
    
    def _handle_move_mode(self):
        """Enter move mode."""
        # In multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                return
                
        if self.selected_unit:
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            if self.selected_unit.player == current_player or self.game.test_mode:
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
        # In multiplayer, only allow actions on current player's turn
        if self.multiplayer.is_multiplayer() and not self.multiplayer.is_current_player_turn():
            if not self.game.test_mode:  # Test mode overrides turn restrictions
                self.message = "Not your turn!"
                return
                
        if self.selected_unit:
            current_player = self.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            if self.selected_unit.player == current_player or self.game.test_mode:
                self.mode = "attack"
                
                # Convert positions to Position objects
                self.highlighted_positions = [
                    Position(y, x) for y, x in self.game.get_possible_attacks(self.selected_unit)
                ]
                
                if not self.highlighted_positions:
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
    
    def _update_player_message(self):
        """Update the message showing the current player."""
        current_player = self.multiplayer.get_current_player()
        
        if self.multiplayer.is_multiplayer():
            if self.multiplayer.is_current_player_turn():
                message = f"Turn {self.game.turn}, Player {current_player}'s turn (YOU)"
                message_log.add_system_message(f"Player {current_player}'s turn")
            else:
                message = f"Turn {self.game.turn}, Player {current_player}'s turn (WAITING)"
                message_log.add_system_message(f"Waiting for Player {current_player}'s turn")
        else:
            message = f"Turn {self.game.turn}, Player {self.game.current_player}'s turn"
            message_log.add_system_message(f"Turn {self.game.turn}, Player {self.game.current_player}'s turn")
        
        self.message = message
    
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
        # For melee attacks (warrior), just flash the effect on target
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
        
        # Redraw board to clear effects
        self.draw_board()
    
    @measure_perf
    def draw_board(self):
        """Draw the game board and UI."""
        self.renderer.clear_screen()
        
        # Draw header
        current_player = self.multiplayer.get_current_player()
        game_mode = "Single" if not self.multiplayer.is_multiplayer() else "Local" if self.multiplayer.is_local_multiplayer() else "LAN"
        
        header = f"Turn: {self.game.turn} | Player: {current_player} | Mode: {self.mode} | Game: {game_mode}"
        if self.multiplayer.is_multiplayer():
            header += f" | {'YOUR TURN' if self.multiplayer.is_current_player_turn() else 'WAITING'}"
            
        if debug_config.enabled:
            header += " | DEBUG ON"
            
        self.renderer.draw_text(0, 0, header)
        
        # Draw the battlefield
        for y in range(HEIGHT):
            for x in range(WIDTH):
                pos = Position(y, x)
                
                # Default content is empty ground
                tile = self.asset_manager.get_terrain_tile("empty")
                color_id = 1  # Default color
                
                # Check if there's a unit at this position
                unit = self.game.get_unit_at(y, x)
                if unit:
                    tile = self.asset_manager.get_unit_tile(unit.type)
                    color_id = 3 if unit.player == 1 else 4
                    
                    # If this is the selected unit, make it bold
                    if self.selected_unit and unit == self.selected_unit:
                        self.renderer.draw_tile(y, x, tile, color_id)
                        continue
                
                # Check if position is highlighted for movement or attack
                if pos in self.highlighted_positions:
                    if self.mode == "move":
                        color_id = 5
                    elif self.mode == "attack":
                        color_id = 6
                
                # Check if cursor is here
                if pos == self.cursor_pos:
                    color_id = 2
                
                # Draw the cell
                self.renderer.draw_tile(y, x, tile, color_id)
                
        # Draw message log if enabled
        if self.show_log:
            self._draw_message_log()
        
        # Draw unit info
        if self.selected_unit:
            unit = self.selected_unit
            unit_info = f"Selected: {unit.type.name} | HP: {unit.hp}/{unit.max_hp} | " \
                        f"ATK: {unit.attack} | DEF: {unit.defense} | " \
                        f"Move: {unit.move_range} | Range: {unit.attack_range}"
            self.renderer.draw_text(HEIGHT+3, 0, unit_info)
        
        # Draw message
        self.renderer.draw_text(HEIGHT+5, 0, self.message)
        
        # Draw controls
        controls = "[↑↓←→] Move cursor | [ENTER] Select | [m] Move | [a] Attack | [e] End turn"
        controls += " | [t] Test mode | [l] Log | [q] Quit"
        self.renderer.draw_text(HEIGHT+7, 0, controls)
        
        # Draw winner info if game is over
        if self.game.winner:
            self.renderer.draw_text(HEIGHT+9, 0, f"Player {self.game.winner} wins!", curses.A_BOLD)
        
        # Draw debug overlay if enabled
        if debug_config.show_debug_overlay:
            try:
                # Get debug information
                overlay_lines = debug_config.get_debug_overlay()
                
                # Add game state info
                game_state = self.game.get_game_state()
                overlay_lines.append(f"Game State: Turn {game_state['turn']}, Player {game_state['current_player']}")
                overlay_lines.append(f"Units: {len(game_state['units'])}")
                
                # Display overlay at the bottom of the screen
                line_offset = HEIGHT + 11
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
            
            # Calculate position for the log (top of screen)
            start_y = HEIGHT + 11
            
            # Draw message log header
            self.renderer.draw_text(start_y, 0, "=== MESSAGE LOG ===", 1, curses.A_BOLD)
            
            # Draw messages in reverse order (newest at the bottom)
            for i, (text, color_id) in enumerate(reversed(messages)):
                y_pos = start_y + self.log_height - i
                self.renderer.draw_text(y_pos, 2, text, color_id)
        except Exception as e:
            # Never let message log crash the game
            logger.error(f"Error displaying message log: {str(e)}")
    
    def handle_input(self, key: int) -> bool:
        """
        Handle user input.
        Returns True to continue running, False to quit.
        """
        # Quick exit for 'q' key
        if key == ord('q'):
            return False
        
        # Process through input handler
        return self.input_handler.process_input(key)