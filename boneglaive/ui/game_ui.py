#!/usr/bin/env python3
import curses
import time
import json
import os
from boneglaive.utils.constants import HEIGHT, WIDTH, UNIT_SYMBOLS, ATTACK_EFFECTS, UnitType
from boneglaive.game.engine import Game
from boneglaive.game.animations import get_line
from boneglaive.utils.debug import debug_config, measure_perf, game_assert

# Set up module logger
logger = debug_config.setup_logging('ui.game_ui')

class GameUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.game = Game()
        self.cursor_y = HEIGHT // 2
        self.cursor_x = WIDTH // 2
        self.selected_unit = None
        self.highlighted_positions = []
        self.mode = "select"  # select, move, attack
        self.message = ""
        self.setup_colors()
    
    def setup_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Cursor
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Player 1
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Player 2
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Highlighted move
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)    # Highlighted attack
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Attack animation
    
    def show_attack_animation(self, attacker, target):
        """Show a visual animation for attacks"""
        effect_char = ATTACK_EFFECTS[attacker.type]
        effect_color = curses.color_pair(7)
        
        # For ranged attacks (archer and mage), show projectile path
        if attacker.type in [UnitType.ARCHER, UnitType.MAGE]:
            # Calculate path from attacker to target (note: y,x order for positions)
            path = get_line(attacker.y, attacker.x, target.y, target.x)
            
            # Animate projectile along path
            for pos_y, pos_x in path:
                # Skip the attacker's position and the target's position
                if (pos_y, pos_x) != (attacker.y, attacker.x) and (pos_y, pos_x) != (target.y, target.x):
                    # Draw effect at the current position (add 2 to y for UI offset)
                    self.stdscr.addstr(pos_y+2, pos_x*2, effect_char, effect_color)
                    self.stdscr.refresh()
                    time.sleep(0.1)  # Animation speed
        
        # For melee attacks (warrior), just flash the effect on target
        else:
            self.stdscr.addstr(target.y+2, target.x*2, effect_char, effect_color)
            self.stdscr.refresh()
            time.sleep(0.2)
        
        # Flash the target to show it was hit
        for _ in range(3):
            # Flash target position with inverse colors
            self.stdscr.addstr(target.y+2, target.x*2, UNIT_SYMBOLS[target.type], 
                              curses.color_pair(6 if target.player == 1 else 5))
            self.stdscr.refresh()
            time.sleep(0.1)
            
            # Restore normal color
            target_color = curses.color_pair(3 if target.player == 1 else 4)
            self.stdscr.addstr(target.y+2, target.x*2, UNIT_SYMBOLS[target.type], target_color)
            self.stdscr.refresh()
            time.sleep(0.1)
        
        # Show damage number above target
        damage = max(1, attacker.attack - target.defense)
        self.stdscr.addstr(target.y+1, target.x*2, f"-{damage}", curses.color_pair(7) | curses.A_BOLD)
        self.stdscr.refresh()
        time.sleep(0.5)
        
        # Redraw board to clear effects
        self.draw_board()
    
    @measure_perf
    def draw_board(self):
        self.stdscr.clear()
        
        # Draw header
        header = f"Turn: {self.game.turn} | Player: {self.game.current_player} | Mode: {self.mode}"
        if debug_config.enabled:
            header += " | DEBUG ON"
        self.stdscr.addstr(0, 0, header)
        
        # Draw the battlefield
        for y in range(HEIGHT):
            for x in range(WIDTH):
                # Default content is empty ground
                char = "."
                color = curses.color_pair(1)
                
                # Check if there's a unit at this position
                unit = self.game.get_unit_at(y, x)
                if unit:
                    char = UNIT_SYMBOLS[unit.type]
                    color = curses.color_pair(3) if unit.player == 1 else curses.color_pair(4)
                    
                    # If this is the selected unit, make it bold
                    if self.selected_unit and unit == self.selected_unit:
                        color |= curses.A_BOLD
                
                # Check if position is highlighted for movement or attack
                if (y, x) in self.highlighted_positions:
                    if self.mode == "move":
                        color = curses.color_pair(5)
                    elif self.mode == "attack":
                        color = curses.color_pair(6)
                
                # Check if cursor is here
                if y == self.cursor_y and x == self.cursor_x:
                    color = curses.color_pair(2)
                
                # Draw the cell
                self.stdscr.addstr(y+2, x*2, char, color)
        
        # Draw unit info
        if self.selected_unit:
            unit = self.selected_unit
            unit_info = f"Selected: {unit.type.name} | HP: {unit.hp}/{unit.max_hp} | " \
                        f"ATK: {unit.attack} | DEF: {unit.defense} | " \
                        f"Move: {unit.move_range} | Range: {unit.attack_range}"
            self.stdscr.addstr(HEIGHT+3, 0, unit_info)
        
        # Draw message
        self.stdscr.addstr(HEIGHT+5, 0, self.message)
        
        # Draw controls
        controls = "[↑↓←→] Move cursor | [ENTER] Select | [m] Move | [a] Attack | [e] End turn"
        controls += " | [t] Toggle test mode | [q] Quit"
        self.stdscr.addstr(HEIGHT+7, 0, controls)
        
        # Draw winner info if game is over
        if self.game.winner:
            self.stdscr.addstr(HEIGHT+9, 0, f"Player {self.game.winner} wins!", curses.A_BOLD)
        
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
                    self.stdscr.addstr(line_offset + i, 0, line, curses.A_DIM)
            except Exception as e:
                # Never let debug features crash the game
                logger.error(f"Error displaying debug overlay: {str(e)}")
        
        self.stdscr.refresh()
    
    def handle_input(self, key):
        if key == ord('q'):
            return False  # Exit game loop
        
        # Skip other inputs if game is over
        if self.game.winner:
            if key == ord('r'):  # Reset game
                self.game = Game()
                self.selected_unit = None
                self.highlighted_positions = []
                self.mode = "select"
                self.message = "Game reset"
            return True
        
        # Handle cursor movement
        if key == curses.KEY_UP:
            self.cursor_y = max(0, self.cursor_y - 1)
        elif key == curses.KEY_DOWN:
            self.cursor_y = min(HEIGHT-1, self.cursor_y + 1)
        elif key == curses.KEY_LEFT:
            self.cursor_x = max(0, self.cursor_x - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor_x = min(WIDTH-1, self.cursor_x + 1)
        
        # Handle selection and actions
        elif key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            if self.mode == "select":
                unit = self.game.get_unit_at(self.cursor_y, self.cursor_x)
                if unit and (unit.player == self.game.current_player or self.game.test_mode):
                    self.selected_unit = unit
                    self.message = f"Selected {unit.type.name}"
                else:
                    self.message = "No valid unit selected"
            
            elif self.mode == "move" and (self.cursor_y, self.cursor_x) in self.highlighted_positions:
                self.selected_unit.move_target = (self.cursor_y, self.cursor_x)
                self.message = f"Move set to ({self.cursor_y}, {self.cursor_x})"
                self.mode = "select"
                self.highlighted_positions = []
            
            elif self.mode == "attack" and (self.cursor_y, self.cursor_x) in self.highlighted_positions:
                self.selected_unit.attack_target = (self.cursor_y, self.cursor_x)
                target = self.game.get_unit_at(self.cursor_y, self.cursor_x)
                self.message = f"Attack set against {target.type.name}"
                self.mode = "select"
                self.highlighted_positions = []
        
        # Enter move mode
        elif key == ord('m'):
            if self.selected_unit:
                self.mode = "move"
                self.highlighted_positions = self.game.get_possible_moves(self.selected_unit)
                if not self.highlighted_positions:
                    self.message = "No valid moves available"
            else:
                self.message = "No unit selected"
        
        # Enter attack mode
        elif key == ord('a'):
            if self.selected_unit:
                self.mode = "attack"
                self.highlighted_positions = self.game.get_possible_attacks(self.selected_unit)
                if not self.highlighted_positions:
                    self.message = "No valid targets in range"
            else:
                self.message = "No unit selected"
        
        # End turn
        elif key == ord('e'):
            # Pass UI to execute_turn for animations
            self.game.execute_turn(self)
            self.selected_unit = None
            self.highlighted_positions = []
            self.mode = "select"
            if not self.game.winner:
                self.message = f"Turn {self.game.turn}, Player {self.game.current_player}'s turn"
        
        # Toggle test mode
        elif key == ord('t'):
            self.game.toggle_test_mode()
            if self.game.test_mode:
                self.message = "Test mode ON - both players can control all units"
            else:
                self.message = "Test mode OFF"
        
        # Deselect unit
        elif key == ord('c'):
            self.selected_unit = None
            self.highlighted_positions = []
            self.mode = "select"
            self.message = "Selection cleared"
        
        # Debug key - show all unit positions
        elif key == ord('d'):
            debug_info = []
            for unit in self.game.units:
                if unit.is_alive():
                    debug_info.append(f"({unit.y},{unit.x})")
            self.message = f"Unit positions: {' '.join(debug_info)}"
            logger.debug(f"Unit positions: {debug_info}")
        
        # Enhanced debug keys
        elif key == ord('D'):  # Shift+D
            # Toggle main debug mode
            debug_enabled = debug_config.toggle()
            self.message = f"Debug mode {'ON' if debug_enabled else 'OFF'}"
            logger.info(f"Debug mode {'enabled' if debug_enabled else 'disabled'}")
        
        elif key == ord('O'):  # Shift+O
            # Toggle debug overlay
            overlay_enabled = debug_config.toggle_overlay()
            self.message = f"Debug overlay {'ON' if overlay_enabled else 'OFF'}"
        
        elif key == ord('P'):  # Shift+P
            # Toggle performance tracking
            perf_enabled = debug_config.toggle_perf_tracking()
            self.message = f"Performance tracking {'ON' if perf_enabled else 'OFF'}"
        
        elif key == ord('S') and debug_config.enabled:  # Shift+S, only in debug mode
            # Save game state to file for debugging
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
        
        return True