#!/usr/bin/env python3
import curses
import time
import os
import json
from typing import Optional, List, Tuple, Dict, Callable

from boneglaive.utils.constants import HEIGHT, WIDTH, UnitType
from boneglaive.utils.coordinates import Position
from boneglaive.utils.debug import debug_config, measure_perf, logger
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.input_handler import GameAction

# Base class for UI components
class UIComponent:
    """Base class for UI components."""
    
    def __init__(self, renderer, game_ui):
        """Initialize the component."""
        self.renderer = renderer
        self.game_ui = game_ui
        
    def draw(self):
        """Draw the component."""
        pass
        
    def handle_input(self, key: int) -> bool:
        """Handle input for this component.
        Returns True if the input was handled, False otherwise.
        """
        return False

# Message log component
class MessageLogComponent(UIComponent):
    """Component for displaying and managing the message log."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.show_log = True  # Whether to show the message log
        self.log_height = 5   # Number of log lines to display
        self.show_log_history = False  # Whether to show the full log history screen
        self.log_history_scroll = 0    # Scroll position in log history
    
    def toggle_message_log(self):
        """Toggle the message log display."""
        self.show_log = not self.show_log
        self.game_ui.message = f"Message log {'shown' if self.show_log else 'hidden'}"
        message_log.add_system_message(f"Message log {'shown' if self.show_log else 'hidden'}")
        
    def toggle_log_history(self):
        """Toggle the full log history screen."""
        # Don't show log history while in help or chat mode
        if self.game_ui.help_component.show_help or self.game_ui.chat_component.chat_mode:
            return
            
        # Toggle log history screen
        self.show_log_history = not self.show_log_history
        
        # Reset scroll position when opening
        if self.show_log_history:
            self.log_history_scroll = 0
        
        # Immediately redraw the board
        self.game_ui.draw_board()
        
    def draw_message_log(self):
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
    
    def draw_log_history_screen(self):
        """Draw the full log history screen with scrolling."""
        try:
            # Calculate available height for messages (terminal height minus headers/footers)
            term_height, term_width = self.renderer.get_terminal_size()
            available_height = term_height - 6  # Space for title, instructions and bottom margin
            
            # Get all messages from the log (we'll format and scroll them)
            # Avoid filtering when viewing full history - get all messages
            all_messages = message_log.get_formatted_messages(count=message_log.MAX_MESSAGES, filter_types=None)
            
            # Calculate max scroll position
            max_scroll = max(0, len(all_messages) - available_height)
            # Clamp scroll position
            self.log_history_scroll = max(0, min(self.log_history_scroll, max_scroll))
            
            # Draw title
            self.renderer.draw_text(1, 2, "=== BONEGLAIVE LOG HISTORY ===", 1, curses.A_BOLD)
            
            # Draw navigation instructions
            nav_text = "UP/DOWN: Scroll | ESC: Close | L: Toggle regular log"
            self.renderer.draw_text(3, 2, nav_text, 1)
            
            # Draw scroll indicator
            if len(all_messages) > available_height:
                scroll_pct = int((self.log_history_scroll / max_scroll) * 100)
                scroll_text = f"Showing {self.log_history_scroll+1}-{min(self.log_history_scroll+available_height, len(all_messages))} " \
                             f"of {len(all_messages)} messages ({scroll_pct}%)"
                self.renderer.draw_text(term_height-2, 2, scroll_text, 1)
            else:
                self.renderer.draw_text(term_height-2, 2, f"Showing all {len(all_messages)} messages", 1)
            
            # Slice messages based on scroll position
            visible_messages = all_messages[self.log_history_scroll:self.log_history_scroll+available_height]
            
            # Draw messages (in chronological order, oldest first)
            for i, (text, color_id) in enumerate(visible_messages):
                y_pos = i + 5  # Start after title and instructions
                
                # Add bold attribute for player messages
                attributes = 0
                if "[Player " in text:  # It's a chat message
                    attributes = curses.A_BOLD
                
                # Truncate messages that are too long for the screen
                max_text_width = term_width - 4  # Leave margin
                if len(text) > max_text_width:
                    text = text[:max_text_width-3] + "..."
                
                self.renderer.draw_text(y_pos, 2, text, color_id, attributes)
                
        except Exception as e:
            # Never let log history crash the game
            logger.error(f"Error displaying log history: {str(e)}")
    
    def handle_input(self, key: int) -> bool:
        """Handle input for log history screen."""
        if self.show_log_history:
            if key == curses.KEY_UP:
                # Scroll up
                self.log_history_scroll = max(0, self.log_history_scroll - 1)
                self.game_ui.draw_board()
                return True
            elif key == curses.KEY_DOWN:
                # Scroll down (max scroll is enforced in draw method)
                self.log_history_scroll += 1
                self.game_ui.draw_board()
                return True
            elif key == ord('l'):
                # Toggle regular log view while in history
                self.toggle_message_log()
                self.game_ui.draw_board()
                return True
                
        return False

# Help screen component
class HelpComponent(UIComponent):
    """Component for displaying the help screen."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.show_help = False  # Whether to show help screen
    
    def toggle_help_screen(self):
        """Toggle the help screen display."""
        # Can't use help screen while in chat mode
        if self.game_ui.chat_component.chat_mode:
            return
            
        self.show_help = not self.show_help
        self.game_ui.draw_board()  # Redraw the board immediately to show/hide help
        message_log.add_system_message(f"Help screen {'shown' if self.show_help else 'hidden'}")
    
    def draw_help_screen(self):
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
                "Tab: Cycle forward through your units",
                "Shift+Tab: Cycle backward through your units",
                "m: Move selected unit",
                "a: Attack with selected unit",
                "e: End turn",
                "Esc: Cancel current action/selection",
                "c: Clear selection (same as Esc)",
                "l: Toggle message log",
                "Shift+L: View full game log history (scrollable)",
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

# Chat component
class ChatComponent(UIComponent):
    """Component for handling chat input and display."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.chat_mode = False  # Whether in chat input mode
        self.chat_input = ""  # Current chat input text
        self.player_colors = {1: 3, 2: 4}  # Player colors (matching message_log)
    
    def toggle_chat_mode(self):
        """Toggle chat input mode."""
        # Can't use chat while help screen is shown
        if self.game_ui.help_component.show_help:
            return
            
        # Toggle chat mode
        self.chat_mode = not self.chat_mode
        
        # Clear any existing input when entering chat mode
        if self.chat_mode:
            self.chat_input = ""
            self.game_ui.message = "Chat mode: Type message and press Enter to send, Escape to cancel"
            # Ensure log is visible when entering chat mode
            if not self.game_ui.message_log_component.show_log:
                self.game_ui.message_log_component.toggle_message_log()
        else:
            self.game_ui.message = "Chat mode exited"
            
        # Redraw the board
        self.game_ui.draw_board()
    
    def draw_chat_input(self):
        """Draw the chat input field at the bottom of the message log."""
        try:
            # Calculate position for the chat input (below the message log)
            input_y = HEIGHT + 5 + self.game_ui.message_log_component.log_height + 1
            
            # Calculate the current player
            current_player = self.game_ui.multiplayer.get_current_player()
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
    
    def handle_chat_input(self, key: int) -> bool:
        """Handle input while in chat mode.
        Returns True to continue running, False to quit.
        """
        # Check for special keys
        if key == 27:  # Escape key - exit chat mode (handled separately from CANCEL action)
            self.chat_mode = False
            self.game_ui.message = "Chat cancelled"
            self.game_ui.draw_board()
            return True
            
        elif key == 10 or key == 13:  # Enter key - send message
            if self.chat_input.strip():  # Only send non-empty messages
                # Get current player
                current_player = self.game_ui.multiplayer.get_current_player()
                
                # Add message to log with player information
                message_log.add_player_message(current_player, self.chat_input)
                
                # Clear input and exit chat mode
                self.chat_input = ""
                self.chat_mode = False
                self.game_ui.message = "Message sent"
            else:
                # Empty message, just exit chat mode
                self.chat_mode = False
                self.game_ui.message = "Chat cancelled"
                
            self.game_ui.draw_board()
            return True
            
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
            # Remove last character
            if self.chat_input:
                self.chat_input = self.chat_input[:-1]
                self.game_ui.draw_board()
            return True
            
        elif 32 <= key <= 126:  # Printable ASCII characters
            # Add character to input (limit to reasonable length)
            if len(self.chat_input) < 60:  # Limit message length
                self.chat_input += chr(key)
                self.game_ui.draw_board()
            return True
            
        # Ignore other keys in chat mode
        return True

# Cursor manager component
class CursorManager(UIComponent):
    """Component for managing cursor movement and selection."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)
        self.selected_unit = None
        self.highlighted_positions = []
    
    def move_cursor(self, dy: int, dx: int):
        """Move the cursor by the given delta."""
        new_y = max(0, min(HEIGHT-1, self.cursor_pos.y + dy))
        new_x = max(0, min(WIDTH-1, self.cursor_pos.x + dx))
        self.cursor_pos = Position(new_y, new_x)
    
    def cycle_units_internal(self, reverse=False):
        """Cycle through the player's units.
        
        Args:
            reverse: If True, cycle backward through the units
        """
        # Skip if in help or chat mode
        if self.game_ui.help_component.show_help or self.game_ui.chat_component.chat_mode:
            return
            
        # Get the current player
        current_player = self.game_ui.multiplayer.get_current_player()
        
        # Get a list of units belonging to the current player
        player_units = [unit for unit in self.game_ui.game.units 
                      if unit.is_alive() and 
                         (unit.player == current_player or 
                          (self.game_ui.game.test_mode and unit.player in [1, 2]))]
        
        if not player_units:
            self.game_ui.message = "No units available to cycle through"
            return
            
        # If no unit is selected, select the first or last one depending on direction
        if not self.selected_unit:
            # In reverse mode, start from the last unit
            next_unit = player_units[-1 if reverse else 0]
            self.cursor_pos = Position(next_unit.y, next_unit.x)
            self.selected_unit = next_unit
            self.game_ui.message = ""  # Clear message to avoid redundancy with unit info display
            self.game_ui.draw_board()
            return
            
        # Find the index of the currently selected unit
        try:
            current_index = player_units.index(self.selected_unit)
            
            # Calculate the next index based on direction
            if reverse:
                # Select the previous unit (loop back to last if at the beginning)
                next_index = (current_index - 1) % len(player_units)
            else:
                # Select the next unit (loop back to first if at the end)
                next_index = (current_index + 1) % len(player_units)
                
            next_unit = player_units[next_index]
            
            # If the unit has a move target, cycle to the ghost instead
            if next_unit.move_target:
                self.cursor_pos = Position(next_unit.move_target[0], next_unit.move_target[1])
            else:
                self.cursor_pos = Position(next_unit.y, next_unit.x)
                
            # Clear message to avoid redundancy with unit info display
            self.game_ui.message = ""
                
            self.selected_unit = next_unit
            
        except ValueError:
            # If the selected unit isn't in the player's units (could happen in test mode)
            # In reverse mode, start from the last unit
            next_unit = player_units[-1 if reverse else 0]
            self.cursor_pos = Position(next_unit.y, next_unit.x)
            self.selected_unit = next_unit
            self.game_ui.message = ""  # Clear message to avoid redundancy with unit info display
        
        # Redraw the board to show the new selection
        self.game_ui.draw_board()
    
    def cycle_units(self):
        """Cycle forward through player's units (Tab key)."""
        self.cycle_units_internal(reverse=False)
    
    def cycle_units_reverse(self):
        """Cycle backward through player's units (Shift+Tab key)."""
        self.cycle_units_internal(reverse=True)
        
    def find_unit_by_ghost(self, y, x):
        """Find a unit that has a move target at the given position.
        
        Args:
            y, x: The position to check for a ghost unit
            
        Returns:
            The unit that has a move target at (y, x), or None if no such unit exists
        """
        for unit in self.game_ui.game.units:
            if unit.is_alive() and unit.move_target == (y, x):
                return unit
        return None

# Game mode manager component
class GameModeManager(UIComponent):
    """Component for managing game modes and turn handling."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.mode = "select"  # select, move, attack, setup
        self.show_setup_instructions = False  # Don't show setup instructions by default
    
    def handle_cancel(self):
        """Handle cancel action (Escape key or 'c' key).
        Cancels the current action based on the current state.
        """
        # First check if log history screen is showing - cancel it
        if self.game_ui.message_log_component.show_log_history:
            self.game_ui.message_log_component.show_log_history = False
            self.game_ui.message_log_component.log_history_scroll = 0  # Reset scroll position
            self.game_ui.message = "Log history closed"
            self.game_ui.draw_board()
            return
            
        # Next check if help screen is showing - cancel it
        if self.game_ui.help_component.show_help:
            self.game_ui.help_component.show_help = False
            self.game_ui.message = "Help screen closed"
            self.game_ui.draw_board()
            return
            
        # If in chat mode, cancel chat
        if self.game_ui.chat_component.chat_mode:
            self.game_ui.chat_component.chat_mode = False
            self.game_ui.message = "Chat cancelled"
            self.game_ui.draw_board()
            return
            
        # If in attack or move mode, cancel the mode but keep unit selected
        if self.mode in ["attack", "move"] and self.game_ui.cursor_manager.selected_unit:
            self.game_ui.cursor_manager.highlighted_positions = []
            self.mode = "select"
            self.game_ui.message = f"{self.mode.capitalize()} mode cancelled, unit still selected"
            self.game_ui.draw_board()
            return
            
        # If unit is selected with a planned move, cancel the move
        if self.game_ui.cursor_manager.selected_unit and self.game_ui.cursor_manager.selected_unit.move_target:
            self.game_ui.cursor_manager.selected_unit.move_target = None
            self.game_ui.message = "Move order cancelled"
            self.game_ui.draw_board()
            return
            
        # If unit is selected with a planned attack, cancel the attack
        if self.game_ui.cursor_manager.selected_unit and self.game_ui.cursor_manager.selected_unit.attack_target:
            self.game_ui.cursor_manager.selected_unit.attack_target = None
            self.game_ui.message = "Attack order cancelled"
            self.game_ui.draw_board()
            return
            
        # Otherwise, clear the selection entirely
        self.game_ui.cursor_manager.selected_unit = None
        self.game_ui.cursor_manager.highlighted_positions = []
        self.mode = "select"
        self.game_ui.message = "Selection cleared"
        
        # Redraw the board to immediately update selection visuals
        self.game_ui.draw_board()
    
    def handle_move_mode(self):
        """Enter move mode."""
        # In network multiplayer, only allow actions on current player's turn
        if self.game_ui.multiplayer.is_network_multiplayer() and not self.game_ui.multiplayer.is_current_player_turn():
            if not self.game_ui.game.test_mode:  # Test mode overrides turn restrictions
                self.game_ui.message = "Not your turn!"
                return
                
        if self.game_ui.cursor_manager.selected_unit:
            current_player = self.game_ui.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            # Also allow control in local multiplayer for the active player
            if (self.game_ui.cursor_manager.selected_unit.player == current_player or
                self.game_ui.game.test_mode or
                (self.game_ui.multiplayer.is_local_multiplayer() and 
                 self.game_ui.cursor_manager.selected_unit.player == self.game_ui.game.current_player)):
                self.mode = "move"
                
                # Convert positions to Position objects
                self.game_ui.cursor_manager.highlighted_positions = [
                    Position(y, x) for y, x in self.game_ui.game.get_possible_moves(self.game_ui.cursor_manager.selected_unit)
                ]
                
                if not self.game_ui.cursor_manager.highlighted_positions:
                    self.game_ui.message = "No valid moves available"
            else:
                self.game_ui.message = "You can only move your own units!"
        else:
            self.game_ui.message = "No unit selected"
    
    def handle_attack_mode(self):
        """Enter attack mode."""
        # In network multiplayer, only allow actions on current player's turn
        if self.game_ui.multiplayer.is_network_multiplayer() and not self.game_ui.multiplayer.is_current_player_turn():
            if not self.game_ui.game.test_mode:  # Test mode overrides turn restrictions
                self.game_ui.message = "Not your turn!"
                return
                
        if self.game_ui.cursor_manager.selected_unit:
            current_player = self.game_ui.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            # Also allow control in local multiplayer for the active player
            if (self.game_ui.cursor_manager.selected_unit.player == current_player or 
                self.game_ui.game.test_mode or
                (self.game_ui.multiplayer.is_local_multiplayer() and 
                 self.game_ui.cursor_manager.selected_unit.player == self.game_ui.game.current_player)):
                self.mode = "attack"
                
                # If we selected a unit directly, use its position
                # If we selected a ghost, always use the ghost position
                from_pos = None
                if self.game_ui.cursor_manager.selected_unit.move_target:
                    from_pos = self.game_ui.cursor_manager.selected_unit.move_target
                    self.game_ui.message = "Select attack from planned move position"
                else:
                    self.game_ui.message = "Select attack target"
                
                # Convert positions to Position objects, using move destination if set
                self.game_ui.cursor_manager.highlighted_positions = [
                    Position(y, x) for y, x in self.game_ui.game.get_possible_attacks(
                        self.game_ui.cursor_manager.selected_unit, from_pos)
                ]
                
                if not self.game_ui.cursor_manager.highlighted_positions:
                    if self.game_ui.cursor_manager.selected_unit.move_target:
                        self.game_ui.message = "No valid targets in range from move destination"
                    else:
                        self.game_ui.message = "No valid targets in range"
            else:
                self.game_ui.message = "You can only attack with your own units!"
        else:
            self.game_ui.message = "No unit selected"
    
    def handle_end_turn(self):
        """End the current turn."""
        # Pass UI to execute_turn for animations
        self.game_ui.game.execute_turn(self.game_ui)
        self.game_ui.cursor_manager.selected_unit = None
        self.game_ui.cursor_manager.highlighted_positions = []
        self.mode = "select"
        
        # Handle multiplayer turn switching
        if not self.game_ui.game.winner:
            # End turn in multiplayer manager
            self.game_ui.multiplayer.end_turn()
            self.game_ui.update_player_message()
            
        # Redraw the board to update visuals
        self.game_ui.draw_board()
    
    def handle_test_mode(self):
        """Toggle test mode."""
        self.game_ui.game.toggle_test_mode()
        if self.game_ui.game.test_mode:
            # If in setup phase, skip it and use test units
            if self.game_ui.game.setup_phase:
                self.game_ui.game.setup_phase = False
                self.game_ui.game.setup_initial_units()
                self.game_ui.message = "Test mode ON - setup phase skipped, using test units"
                
                # Add welcome messages when skipping setup phase
                message_log.add_system_message(f"Entering {self.game_ui.game.map.name}")
                message_log.add_system_message("Test mode enabled, using predefined units")
            else:
                self.game_ui.message = "Test mode ON - both players can control all units"
                message_log.add_system_message("Test mode enabled")
        else:
            self.game_ui.message = "Test mode OFF"
            message_log.add_system_message("Test mode disabled")
    
    def handle_setup_select(self):
        """Handle unit placement during setup phase."""
        # Get the current setup player
        setup_player = self.game_ui.game.setup_player
        
        # Check if cursor position is in bounds
        if not self.game_ui.game.is_valid_position(
                self.game_ui.cursor_manager.cursor_pos.y, 
                self.game_ui.cursor_manager.cursor_pos.x):
            self.game_ui.message = f"Cannot place unit here: out of bounds"
            return
            
        # Check if cursor position has blocking terrain
        if not self.game_ui.game.map.can_place_unit(
                self.game_ui.cursor_manager.cursor_pos.y, 
                self.game_ui.cursor_manager.cursor_pos.x):
            self.game_ui.message = f"Cannot place unit here: blocked by limestone"
            return
            
        # Check if there are units remaining to place
        if self.game_ui.game.setup_units_remaining[setup_player] <= 0:
            self.game_ui.message = f"All units placed. Press 'y' to confirm."
            return
            
        # Try to place the unit (no displacement yet)
        success = self.game_ui.game.place_setup_unit(
            self.game_ui.cursor_manager.cursor_pos.y, 
            self.game_ui.cursor_manager.cursor_pos.x)
        
        if success:
            # Unit was placed at the original position
            self.game_ui.message = f"Unit placed. {self.game_ui.game.setup_units_remaining[setup_player]} remaining."
        else:
            self.game_ui.message = "Failed to place unit: unknown error"
            
        # Redraw the board
        self.game_ui.draw_board()
    
    def handle_confirm(self):
        """Handle confirmation action (mainly for setup phase)."""
        if not self.game_ui.game.setup_phase:
            return  # Ignore outside of setup
            
        # Check if all units have been placed
        setup_player = self.game_ui.game.setup_player
        if self.game_ui.game.setup_units_remaining[setup_player] > 0:
            self.game_ui.message = f"Place all units before confirming ({self.game_ui.game.setup_units_remaining[setup_player]} remaining)"
            return
            
        # Confirm the current player's setup
        game_start = self.game_ui.game.confirm_setup()
        
        # Add appropriate status message (not in log)
        if setup_player == 1:
            self.game_ui.message = "Setup confirmed. Player 2's turn to place units."
            # Start player 2 with cursor in center
            self.game_ui.cursor_manager.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)
        elif game_start:
            self.game_ui.message = "Game begins!"
            
        # Redraw the board
        self.game_ui.draw_board()
            
    def is_valid_setup_position(self, y, x):
        """Check if a position is valid for unit placement during setup."""
        # Check if position is in bounds
        if not self.game_ui.game.is_valid_position(y, x):
            return False
            
        # Check if position has blocking terrain (like limestone)
        if not self.game_ui.game.map.can_place_unit(y, x):
            return False
            
        return True
    
    def draw_setup_instructions(self):
        """Draw the setup phase instructions screen."""
        try:
            # Get terminal size
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Draw title
            self.renderer.draw_text(2, 2, "=== BONEGLAIVE SETUP PHASE ===", 1, curses.A_BOLD)
            
            # Draw instructions
            setup_player = self.game_ui.game.setup_player
            player_color = self.game_ui.chat_component.player_colors.get(setup_player, 1)
            
            instructions = [
                f"Player {setup_player}, place your units on the battlefield.",
                "",
                "Each player must place 3 Glaivemen (melee) units.",
                "",
                "Controls:",
                "- Arrow keys: Move cursor",
                "- Enter: Place unit at cursor position",
                "- y: Confirm unit placement (when all units are placed)",
                "",
                "Special rules:",
                "- Player 1's units will be hidden during Player 2's placement",
                "- After both players finish placement, any units overlapping",
                "  will be automatically displaced to nearby positions",
                "- First-placed units will remain in their positions"
            ]
            
            # Draw instructions
            for i, line in enumerate(instructions):
                y_pos = 5 + i
                if "Player 1" in line and setup_player == 1:
                    self.renderer.draw_text(y_pos, 4, line, 3)  # Player 1 color
                elif "Player 2" in line and setup_player == 2:
                    self.renderer.draw_text(y_pos, 4, line, 4)  # Player 2 color
                else:
                    self.renderer.draw_text(y_pos, 4, line)
            
            # Draw current player indicator
            player_text = f"Player {setup_player}'s turn to place units"
            self.renderer.draw_text(5 + len(instructions) + 2, 4, player_text, player_color, curses.A_BOLD)
            
            # Draw footer
            self.renderer.draw_text(term_height - 3, 2, "Press any key to continue...", 1, curses.A_BOLD)
            
        except Exception as e:
            logger.error(f"Error displaying setup instructions: {str(e)}")

# Debug component
class DebugComponent(UIComponent):
    """Component for handling debug functions."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
    
    def handle_debug_info(self):
        """Toggle message log or show debug info."""
        # Toggle message log when 'l' is pressed
        if self.game_ui.input_handler.action_map.get(ord('l')) == GameAction.DEBUG_INFO:
            self.game_ui.message_log_component.toggle_message_log()
            return
            
        # Otherwise show unit positions
        debug_info = []
        for unit in self.game_ui.game.units:
            if unit.is_alive():
                debug_info.append(f"({unit.y},{unit.x})")
        self.game_ui.message = f"Unit positions: {' '.join(debug_info)}"
        logger.debug(f"Unit positions: {debug_info}")
    
    def handle_debug_toggle(self):
        """Toggle debug mode."""
        debug_enabled = debug_config.toggle()
        self.game_ui.message = f"Debug mode {'ON' if debug_enabled else 'OFF'}"
        
        message_text = f"Debug mode {'enabled' if debug_enabled else 'disabled'}"
        logger.info(message_text)
        message_log.add_message(message_text, MessageType.DEBUG)
    
    def handle_debug_overlay(self):
        """Toggle debug overlay."""
        overlay_enabled = debug_config.toggle_overlay()
        self.game_ui.message = f"Debug overlay {'ON' if overlay_enabled else 'OFF'}"
    
    def handle_debug_performance(self):
        """Toggle performance tracking."""
        perf_enabled = debug_config.toggle_perf_tracking()
        self.game_ui.message = f"Performance tracking {'ON' if perf_enabled else 'OFF'}"
    
    def handle_debug_save(self):
        """Save game state to file."""
        if not debug_config.enabled:
            return
            
        try:
            game_state = self.game_ui.game.get_game_state()
            os.makedirs('debug', exist_ok=True)
            filename = f"debug/game_state_turn{self.game_ui.game.turn}.json"
            with open(filename, 'w') as f:
                json.dump(game_state, f, indent=2)
            self.game_ui.message = f"Game state saved to {filename}"
            logger.info(f"Game state saved to {filename}")
        except Exception as e:
            self.game_ui.message = f"Error saving game state: {str(e)}"
            logger.error(f"Error saving game state: {str(e)}")

# Animation component
class AnimationComponent(UIComponent):
    """Component for handling animations."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        
    @measure_perf
    def show_attack_animation(self, attacker, target):
        """Show a visual animation for attacks."""
        # Get attack effect from asset manager
        effect_tile = self.game_ui.asset_manager.get_attack_effect(attacker.type)
        
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
        tile_ids = [self.game_ui.asset_manager.get_unit_tile(target.type)] * 6
        color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 3
        durations = [0.1] * 6
        
        # Use renderer's flash tile method
        self.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Show damage number above target
        damage = max(1, attacker.attack - target.defense)
        self.renderer.draw_text(target.y+1, target.x*2, f"-{damage}", 7, curses.A_BOLD)
        self.renderer.refresh()
        time.sleep(0.5)
        
        # Redraw board to clear effects (without cursor, selection, or attack target highlighting)
        self.game_ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

# Input manager component
class InputManager(UIComponent):
    """Component for handling input processing."""
    
    def __init__(self, renderer, game_ui, input_handler):
        super().__init__(renderer, game_ui)
        self.input_handler = input_handler
        self.setup_input_callbacks()
    
    def setup_input_callbacks(self):
        """Set up callbacks for input handling."""
        cursor_manager = self.game_ui.cursor_manager
        mode_manager = self.game_ui.mode_manager
        
        self.input_handler.register_action_callbacks({
            GameAction.MOVE_UP: lambda: cursor_manager.move_cursor(-1, 0),
            GameAction.MOVE_DOWN: lambda: cursor_manager.move_cursor(1, 0),
            GameAction.MOVE_LEFT: lambda: cursor_manager.move_cursor(0, -1),
            GameAction.MOVE_RIGHT: lambda: cursor_manager.move_cursor(0, 1),
            GameAction.SELECT: self.game_ui.handle_select,
            GameAction.CANCEL: mode_manager.handle_cancel,
            GameAction.MOVE_MODE: mode_manager.handle_move_mode,
            GameAction.ATTACK_MODE: mode_manager.handle_attack_mode,
            GameAction.END_TURN: mode_manager.handle_end_turn,
            GameAction.TEST_MODE: mode_manager.handle_test_mode,
            GameAction.DEBUG_INFO: self.game_ui.debug_component.handle_debug_info,
            GameAction.DEBUG_TOGGLE: self.game_ui.debug_component.handle_debug_toggle,
            GameAction.DEBUG_OVERLAY: self.game_ui.debug_component.handle_debug_overlay,
            GameAction.DEBUG_PERFORMANCE: self.game_ui.debug_component.handle_debug_performance,
            GameAction.DEBUG_SAVE: self.game_ui.debug_component.handle_debug_save,
            GameAction.HELP: self.game_ui.help_component.toggle_help_screen,
            GameAction.CHAT_MODE: self.game_ui.chat_component.toggle_chat_mode,
            GameAction.CYCLE_UNITS: cursor_manager.cycle_units,
            GameAction.CYCLE_UNITS_REVERSE: cursor_manager.cycle_units_reverse,
            GameAction.LOG_HISTORY: self.game_ui.message_log_component.toggle_log_history,
            GameAction.CONFIRM: mode_manager.handle_confirm  # For setup phase confirmation
        })
        
        # Add custom key for toggling message log
        self.input_handler.add_mapping(ord('l'), GameAction.DEBUG_INFO)  # Reuse DEBUG_INFO for log toggle
        
    def process_input(self, key: int) -> bool:
        """Process input and delegate to appropriate component."""
        # Quick exit for 'q' key (except in chat mode)
        if key == ord('q') and not self.game_ui.chat_component.chat_mode and not self.game_ui.message_log_component.show_log_history:
            return False
            
        # First check if any components want to handle this input
        if self.game_ui.message_log_component.handle_input(key):
            return True
            
        # If in chat mode, handle chat input
        if self.game_ui.chat_component.chat_mode:
            return self.game_ui.chat_component.handle_chat_input(key)
        
        # Default processing
        return self.input_handler.process_input(key)