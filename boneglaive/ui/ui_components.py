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
from boneglaive.game.skills.core import TargetType
from boneglaive.utils.event_system import (
    get_event_manager, EventType, EventData,
    UnitSelectedEventData, UnitDeselectedEventData,
    CursorMovedEventData, ModeChangedEventData,
    MoveEventData, AttackEventData, TurnEventData,
    MessageDisplayEventData, UIRedrawEventData,
    GameOverEventData
)

# Base class for UI components
class UIComponent:
    """Base class for UI components."""
    
    def __init__(self, renderer, game_ui):
        """Initialize the component."""
        self.renderer = renderer
        self.game_ui = game_ui
        self.event_manager = get_event_manager()
        self._event_subscriptions = []
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """
        Set up event handlers for this component.
        Override this in subclasses to subscribe to events.
        """
        pass
    
    def subscribe_to_event(self, event_type, handler):
        """
        Subscribe to an event and track the subscription.
        
        Args:
            event_type: The event type to subscribe to
            handler: The event handler function
        """
        self.event_manager.subscribe(event_type, handler)
        self._event_subscriptions.append((event_type, handler))
    
    def publish_event(self, event_type, event_data=None):
        """
        Publish an event.
        
        Args:
            event_type: The event type to publish
            event_data: The event data to pass to handlers
        """
        self.event_manager.publish(event_type, event_data)
    
    def unsubscribe_all(self):
        """Unsubscribe from all events this component is subscribed to."""
        for event_type, handler in self._event_subscriptions:
            self.event_manager.unsubscribe(event_type, handler)
        self._event_subscriptions = []
    
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
    
    def _setup_event_handlers(self):
        """Set up event handlers for the message log component."""
        # Subscribe to help and chat toggle events to handle conflicts
        self.subscribe_to_event(EventType.HELP_TOGGLED, self._on_help_toggled)
        self.subscribe_to_event(EventType.CHAT_TOGGLED, self._on_chat_toggled)
    
    def _on_help_toggled(self, event_type, event_data):
        """Handle help screen toggle events."""
        # If help screen is shown and log history is open, close log history
        show_help = event_data.show_help if hasattr(event_data, 'show_help') else False
        if show_help and self.show_log_history:
            self.show_log_history = False
            self.log_history_scroll = 0
            
    def _on_chat_toggled(self, event_type, event_data):
        """Handle chat mode toggle events."""
        # If chat mode is enabled and log is hidden, show it
        chat_enabled = event_data.chat_enabled if hasattr(event_data, 'chat_enabled') else False
        if chat_enabled and not self.show_log:
            self.show_log = True
            self.publish_event(
                EventType.LOG_TOGGLED, 
                EventData(show_log=self.show_log)
            )
        
    def toggle_message_log(self):
        """Toggle the message log display."""
        self.show_log = not self.show_log
        
        # Publish event that log was toggled
        self.publish_event(
            EventType.LOG_TOGGLED, 
            EventData(show_log=self.show_log)
        )
        
        # Display message through event system
        self.publish_event(
            EventType.MESSAGE_DISPLAY_REQUESTED,
            MessageDisplayEventData(
                message=f"Message log {'shown' if self.show_log else 'hidden'}",
                message_type=MessageType.SYSTEM
            )
        )
        
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
        
        # Request UI redraw through event system
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
    # Removed colored text handling methods as they're no longer needed
    
    def draw_message_log(self):
        """Draw the message log in the game UI."""
        try:
            # Get formatted messages (with colors)
            messages = message_log.get_formatted_messages(self.log_height)
            
            # Calculate position for the log (closer to the game info)
            start_y = HEIGHT + 6
            
            # Get terminal width for drawing borders
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Draw message log border and header
            # Top border with title
            border_top = "┌─── MESSAGE LOG " + "─" * (term_width - 19) + "┐"
            self.renderer.draw_text(start_y, 0, border_top, 1, curses.A_BOLD)
            
            # Draw side borders and clear message area
            for i in range(1, self.log_height + 1):
                # Left border
                self.renderer.draw_text(start_y + i, 0, "│", 1)
                # Clear line
                self.renderer.draw_text(start_y + i, 1, " " * (term_width - 2), 1)
                # Right border
                self.renderer.draw_text(start_y + i, term_width - 1, "│", 1)
            
            # Bottom border
            border_bottom = "└" + "─" * (term_width - 2) + "┘"
            self.renderer.draw_text(start_y + self.log_height + 1, 0, border_bottom, 1)
            
            # Draw messages in reverse order (newest at the bottom)
            for i, (text, color_id) in enumerate(reversed(messages)):
                y_pos = start_y + self.log_height - i
                
                # Add bold attribute for player messages to make them stand out more
                attributes = 0
                if "[Player " in text:  # It's a chat message
                    attributes = curses.A_BOLD
                
                # Format the message with timestamp prefix if not already formatted
                if not text.startswith("[") and not text.startswith("»"):
                    text = "» " + text
                    
                # Truncate message if too long for display
                max_text_width = term_width - 4  # Allow for borders
                if len(text) > max_text_width:
                    text = text[:max_text_width-3] + "..."
                
                # Set appropriate attributes based on color
                if color_id == 8:  # Gray message log text
                    attributes |= curses.A_DIM  # Add dim attribute to make it gray
                elif color_id in [3, 4]:  # Player colors (green or blue)
                    attributes |= curses.A_BOLD  # Make player text bold
                elif color_id == 7:  # Yellow debuff text
                    attributes |= curses.A_BOLD  # Make debuff text bold for emphasis
                elif color_id == 17:  # Wretch messages (red)
                    attributes |= curses.A_BOLD  # Make wretch messages bold red
                elif color_id == 18:  # Death messages (dark red)
                    attributes |= curses.A_DIM  # Make death messages dim red
                self.renderer.draw_text(y_pos, 2, text, color_id, attributes)
                
        except Exception as e:
            # Never let message log crash the game
            logger.error(f"Error displaying message log: {str(e)}")
    
    def draw_log_history_screen(self):
        """Draw the full log history screen with scrolling."""
        try:
            # Calculate available height for messages (terminal height minus headers/footers)
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Clear the screen first
            for y in range(term_height):
                self.renderer.draw_text(y, 0, " " * term_width, 1)
            
            # Draw border around the entire screen
            # Top border with title
            border_top = "┌─── BONEGLAIVE MESSAGE HISTORY " + "─" * (term_width - 32) + "┐"
            self.renderer.draw_text(0, 0, border_top, 1, curses.A_BOLD)
            
            # Side borders
            for y in range(1, term_height - 1):
                self.renderer.draw_text(y, 0, "│", 1)
                self.renderer.draw_text(y, term_width - 1, "│", 1)
            
            # Bottom border
            border_bottom = "└" + "─" * (term_width - 2) + "┘"
            self.renderer.draw_text(term_height - 1, 0, border_bottom, 1)
            
            # Define content area dimensions
            content_start_y = 3  # After the navigation bar
            content_end_y = term_height - 3  # Before the status bar
            available_height = content_end_y - content_start_y
            
            # Draw navigation instructions in a bar
            nav_bar = "│ " + "─" * (term_width - 4) + " │"
            self.renderer.draw_text(1, 0, nav_bar, 1)
            nav_text = "↑/↓: Scroll | ESC: Close | L: Toggle regular log"
            self.renderer.draw_text(1, 2, nav_text, 1, curses.A_BOLD)
            
            # Draw a separator below the navigation
            separator = "├" + "─" * (term_width - 2) + "┤"
            self.renderer.draw_text(2, 0, separator, 1)
            
            # Get all messages from the log (we'll format and scroll them)
            # Avoid filtering when viewing full history - get all messages
            all_messages = message_log.get_formatted_messages(count=message_log.MAX_MESSAGES, filter_types=None)
            
            # Calculate max scroll position
            max_scroll = max(0, len(all_messages) - available_height)
            # Clamp scroll position
            self.log_history_scroll = max(0, min(self.log_history_scroll, max_scroll))
            
            # Draw a separator above the status bar
            separator_bottom = "├" + "─" * (term_width - 2) + "┤"
            self.renderer.draw_text(term_height - 2, 0, separator_bottom, 1)
            
            # Draw scroll indicator in status bar
            if len(all_messages) > available_height:
                scroll_pct = int((self.log_history_scroll / max_scroll) * 100)
                scroll_text = f"Showing {self.log_history_scroll+1}-{min(self.log_history_scroll+available_height, len(all_messages))} " \
                             f"of {len(all_messages)} messages ({scroll_pct}%)"
                self.renderer.draw_text(term_height - 2, 2, scroll_text, 1, curses.A_BOLD)
            else:
                self.renderer.draw_text(term_height - 2, 2, f"Showing all {len(all_messages)} messages", 1, curses.A_BOLD)
            
            # Slice messages based on scroll position
            visible_messages = all_messages[self.log_history_scroll:self.log_history_scroll+available_height]
            
            # Draw messages (in chronological order, oldest first)
            for i, (text, color_id) in enumerate(visible_messages):
                y_pos = content_start_y + i
                
                # Add bold attribute for player messages
                attributes = 0
                if "[Player " in text:  # It's a chat message
                    attributes = curses.A_BOLD
                
                # Format the message with timestamp prefix if not already formatted
                if not text.startswith("[") and not text.startswith("»"):
                    text = "» " + text
                
                # Truncate messages that are too long for the screen
                max_text_width = term_width - 4  # Leave margin for borders
                if len(text) > max_text_width:
                    text = text[:max_text_width-3] + "..."
                
                # Set appropriate attributes based on color
                if color_id == 8:  # Gray message log text
                    attributes |= curses.A_DIM  # Add dim attribute to make it gray
                elif color_id in [3, 4]:  # Player colors (green or blue)
                    attributes |= curses.A_BOLD  # Make player text bold
                elif color_id == 7:  # Yellow debuff text
                    attributes |= curses.A_BOLD  # Make debuff text bold for emphasis
                elif color_id == 17:  # Wretch messages (red)
                    attributes |= curses.A_BOLD  # Make wretch messages bold red
                elif color_id == 18:  # Death messages (dark red)
                    attributes |= curses.A_DIM  # Make death messages dim red
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
    
    def _setup_event_handlers(self):
        """Set up event handlers for the help component."""
        # Subscribe to chat toggle events to handle conflicts
        self.subscribe_to_event(EventType.CHAT_TOGGLED, self._on_chat_toggled)
        
    def _on_chat_toggled(self, event_type, event_data):
        """Handle chat mode toggle events."""
        # If chat is enabled and help is showing, hide help
        chat_enabled = event_data.chat_enabled if hasattr(event_data, 'chat_enabled') else False
        if chat_enabled and self.show_help:
            self.show_help = False
            self.publish_event(
                EventType.HELP_TOGGLED,
                EventData(show_help=False)
            )
            
    def toggle_help_screen(self):
        """Toggle the help screen display."""
        # Can't use help screen while in chat mode
        if self.game_ui.chat_component.chat_mode:
            return
            
        self.show_help = not self.show_help
        
        # Publish help toggled event
        self.publish_event(
            EventType.HELP_TOGGLED,
            EventData(show_help=self.show_help)
        )
        
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
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
    
    def _setup_event_handlers(self):
        """Set up event handlers for the chat component."""
        # Subscribe to help toggle events to handle conflicts
        self.subscribe_to_event(EventType.HELP_TOGGLED, self._on_help_toggled)
        
    def _on_help_toggled(self, event_type, event_data):
        """Handle help screen toggle events."""
        # If help is enabled and chat is active, exit chat mode
        show_help = event_data.show_help if hasattr(event_data, 'show_help') else False
        if show_help and self.chat_mode:
            self.chat_mode = False
            self.publish_event(
                EventType.CHAT_TOGGLED,
                EventData(chat_enabled=False)
            )
            
    def toggle_chat_mode(self):
        """Toggle chat input mode."""
        # Can't use chat while help screen is shown
        if self.game_ui.help_component.show_help:
            return
            
        # Toggle chat mode
        self.chat_mode = not self.chat_mode
        
        # Publish chat toggled event
        self.publish_event(
            EventType.CHAT_TOGGLED,
            EventData(chat_enabled=self.chat_mode)
        )
        
        # Clear any existing input when entering chat mode
        if self.chat_mode:
            self.chat_input = ""
            # Display message through event system
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Chat mode: Type message and press Enter to send, Escape to cancel"
                )
            )
        else:
            # Display message through event system
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(message="Chat mode exited")
            )
            
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
    
    def draw_chat_input(self):
        """Draw the chat input field at the bottom of the message log."""
        try:
            # Calculate position for the chat input (below the message log)
            input_y = HEIGHT + 6 + self.game_ui.message_log_component.log_height + 1
            
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
    
    def _setup_event_handlers(self):
        """Set up event handlers for cursor manager."""
        # No event handlers needed initially - CursorManager is primarily an event publisher
        pass
    
    def move_cursor(self, dy: int, dx: int):
        """Move the cursor by the given delta."""
        previous_pos = self.cursor_pos
        new_y = max(0, min(HEIGHT-1, self.cursor_pos.y + dy))
        new_x = max(0, min(WIDTH-1, self.cursor_pos.x + dx))
        new_pos = Position(new_y, new_x)
        
        # Only publish event if position actually changed
        if new_pos != self.cursor_pos:
            self.cursor_pos = new_pos
            # Publish cursor moved event
            self.publish_event(
                EventType.CURSOR_MOVED, 
                CursorMovedEventData(position=self.cursor_pos, previous_position=previous_pos)
            )
            
    def move_cursor_diagonal(self, direction: str):
        """Move the cursor diagonally.
        
        Args:
            direction: One of "up-left", "up-right", "down-left", "down-right"
        """
        dy, dx = 0, 0
        
        if direction == "up-left":
            dy, dx = -1, -1
        elif direction == "up-right":
            dy, dx = -1, 1
        elif direction == "down-left":
            dy, dx = 1, -1
        elif direction == "down-right":
            dy, dx = 1, 1
            
        # Use the existing move_cursor method
        self.move_cursor(dy, dx)
    
    def can_act_this_turn(self):
        """Check if the player can act on the current turn."""
        # Always allow in test mode
        if self.game_ui.game.test_mode:
            return True
        
        # In multiplayer, check if it's the player's turn
        if self.game_ui.multiplayer.is_multiplayer():
            # In local multiplayer, can control active player's units
            if self.game_ui.multiplayer.is_local_multiplayer():
                return True
            # In network multiplayer, can only act on own turn
            return self.game_ui.multiplayer.is_current_player_turn()
        
        # Single player can always act
        return True
    
    def get_unit_at_cursor(self):
        """Get the unit at the current cursor position."""
        # First check for a real unit
        unit = self.game_ui.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
        
        # If no real unit, check for a ghost unit
        if not unit:
            unit = self.find_unit_by_ghost(self.cursor_pos.y, self.cursor_pos.x)
            
        return unit
    
    def can_select_unit(self, unit):
        """Check if the unit can be selected by the current player."""
        if not unit:
            return False
            
        current_player = self.game_ui.multiplayer.get_current_player()
        
        # Test mode can select any unit
        if self.game_ui.game.test_mode:
            return True
            
        # Local multiplayer can select current player's units
        if self.game_ui.multiplayer.is_local_multiplayer():
            return unit.player == self.game_ui.game.current_player
            
        # Otherwise, can only select own units
        return unit.player == current_player
    
    def select_unit_at_cursor(self):
        """Select the unit at the current cursor position.
        Returns True if a unit was selected, False otherwise.
        """
        # If there's already a selected unit, deselect it first
        if self.selected_unit:
            self._deselect_unit()
            
        unit = self.get_unit_at_cursor()
        
        if not unit or not self.can_select_unit(unit):
            if unit:
                # Show information about enemy unit instead of selection error
                # Use the unit's display name (includes Greek identifier) instead of "Player X's UNITTYPE"
                unit_info = f"{unit.get_display_name()} - HP: {unit.hp}/{unit.max_hp}"
                
                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=unit_info,
                        message_type=MessageType.SYSTEM,
                        log_message=False  # Don't add to message log
                    )
                )
            else:
                # Get information about what's at this position
                y, x = self.cursor_pos.y, self.cursor_pos.x
                
                # Check terrain type - we don't need to check for units again since that's handled in the 'if unit:' case above
                terrain = self.game_ui.game.map.get_terrain_at(y, x)
                terrain_name = terrain.name.lower().replace('_', ' ')
                
                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Tile: {terrain_name}",
                        message_type=MessageType.SYSTEM,
                        log_message=False  # Don't add to message log
                    )
                )
                
                # No message in log - this is just UI feedback
            return False
        
        # Select the unit
        self.selected_unit = unit
        
        # Check if we're selecting a ghost (unit with a move_target at current position)
        is_ghost = (unit.move_target == (self.cursor_pos.y, self.cursor_pos.x))
        
        # Clear the message by sending empty message event
        self.publish_event(
            EventType.MESSAGE_DISPLAY_REQUESTED,
            MessageDisplayEventData(message="")
        )
        
        # Publish unit selected event
        self.publish_event(
            EventType.UNIT_SELECTED,
            UnitSelectedEventData(unit=unit, position=self.cursor_pos)
        )
        
        # Request UI redraw to immediately show the selection
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        return True
    
    def _deselect_unit(self):
        """Deselect the currently selected unit."""
        if self.selected_unit:
            unit = self.selected_unit
            self.selected_unit = None
            self.highlighted_positions = []
            
            # Publish unit deselected event
            self.publish_event(
                EventType.UNIT_DESELECTED,
                UnitDeselectedEventData(unit=unit)
            )
    
    def select_move_target(self):
        """Select the current cursor position as a move target for the selected unit.
        Returns True if a move target was set, False otherwise.
        """
        # Import Position to use get_line
        from boneglaive.utils.coordinates import Position, get_line
        
        cursor_position = Position(self.cursor_pos.y, self.cursor_pos.x)
        
        # Check if the position is a valid move target
        if cursor_position in self.highlighted_positions:
            # Store the original position before changing it
            from_position = Position(self.selected_unit.y, self.selected_unit.x)
            to_position = cursor_position
            
            # Set the move target
            self.selected_unit.move_target = (to_position.y, to_position.x)
            
            # Track action order
            self.selected_unit.action_timestamp = self.game_ui.game.action_counter
            self.game_ui.game.action_counter += 1
            
            # Publish move planned event
            self.publish_event(
                EventType.MOVE_PLANNED,
                MoveEventData(
                    unit=self.selected_unit,
                    from_position=from_position,
                    to_position=to_position
                )
            )
            
            self.game_ui.message = f"Move set to ({to_position.y}, {to_position.x})"
            # No message added to log for planned movements
            self.highlighted_positions = []
            return True
        else:
            # Check why the position isn't valid
            y, x = self.cursor_pos.y, self.cursor_pos.x
            
            # Check if the position is in range
            distance = self.game_ui.game.chess_distance(self.selected_unit.y, self.selected_unit.x, y, x)
            if distance > self.selected_unit.move_range:
                self.game_ui.message = "Position is out of movement range"
            # Check if there's a unit blocking the path
            elif distance > 1:
                # Check the path for blocking units
                start_pos = Position(self.selected_unit.y, self.selected_unit.x)
                end_pos = Position(y, x)
                path = get_line(start_pos, end_pos)
                
                for pos in path[1:-1]:  # Skip start and end positions
                    blocking_unit = self.game_ui.game.get_unit_at(pos.y, pos.x)
                    if blocking_unit:
                        # Determine if it's an ally or enemy for the message
                        if blocking_unit.player == self.selected_unit.player:
                            self.game_ui.message = "Path blocked by allied unit"
                            message_log.add_message("You cannot move through other units", MessageType.WARNING)
                        else:
                            self.game_ui.message = "Path blocked by enemy unit"
                            message_log.add_message("You cannot move through other units", MessageType.WARNING)
                        return False
            # Check if there's a unit at the destination
            elif self.game_ui.game.get_unit_at(y, x):
                self.game_ui.message = "Position is occupied by another unit"
            # Check if the terrain is blocking
            elif not self.game_ui.game.map.is_passable(y, x):
                self.game_ui.message = "Terrain is impassable"
            else:
                self.game_ui.message = "Invalid move target"
            return False
    
    def select_attack_target(self):
        """Select the current cursor position as an attack target for the selected unit.
        Returns True if an attack target was set, False otherwise.
        """
        # Import Position for position checking
        from boneglaive.utils.coordinates import Position
        
        cursor_position = Position(self.cursor_pos.y, self.cursor_pos.x)
        
        if cursor_position in self.highlighted_positions:
            # Set the attack target
            target_position = (self.cursor_pos.y, self.cursor_pos.x)
            self.selected_unit.attack_target = target_position
            
            # Track action order
            self.selected_unit.action_timestamp = self.game_ui.game.action_counter
            self.game_ui.game.action_counter += 1
            
            # Check if the target is a unit or a wall
            from boneglaive.utils.message_log import message_log, MessageType
            target_unit = self.game_ui.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            is_wall_target = False
            wall_owner = None
            
            # Check if it's a wall tile
            if hasattr(self.game_ui.game, 'marrow_dike_tiles') and target_position in self.game_ui.game.marrow_dike_tiles:
                is_wall_target = True
                wall_info = self.game_ui.game.marrow_dike_tiles[target_position]
                wall_owner = wall_info['owner']
            
            # Publish attack planned event
            self.publish_event(
                EventType.ATTACK_PLANNED,
                AttackEventData(
                    attacker=self.selected_unit,
                    target=target_unit  # May be None for wall targets
                )
            )
            
            # Set appropriate message based on target type
            if is_wall_target:
                self.game_ui.message = f"Attack set against Marrow Dike wall"
                # Add message to log for planned wall attacks
                message_log.add_message(
                    f"{self.selected_unit.get_display_name()} readies attack against {wall_owner.get_display_name()}'s Marrow Dike wall!",
                    MessageType.COMBAT,
                    player=self.selected_unit.player,
                    attacker_name=self.selected_unit.get_display_name()
                )
            elif target_unit:
                self.game_ui.message = f"Attack set against {target_unit.get_display_name()}"
                # Add message to log for planned unit attacks
                message_log.add_message(
                    f"{self.selected_unit.get_display_name()} readies attack against {target_unit.get_display_name()}!",
                    MessageType.COMBAT,
                    player=self.selected_unit.player,
                    attacker_name=self.selected_unit.get_display_name(),
                    target_name=target_unit.get_display_name()
                )
            else:
                # This shouldn't happen, but handle it just in case
                self.game_ui.message = "Attack target set"
                message_log.add_message(
                    f"{self.selected_unit.get_display_name()} readies an attack!",
                    MessageType.COMBAT,
                    player=self.selected_unit.player,
                    attacker_name=self.selected_unit.get_display_name()
                )
            
            self.highlighted_positions = []
            return True
        else:
            self.game_ui.message = "Invalid attack target"
            return False
    
    def clear_selection(self):
        """Clear the current unit selection and highlighted positions."""
        # Deselect unit (which will publish the appropriate event)
        if self.selected_unit:
            self._deselect_unit()
        else:
            # If no unit was selected, just clear the highlighted positions
            self.highlighted_positions = []
    
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
        
        # Store reference to currently selected unit before deselecting
        previously_selected_unit = self.selected_unit
        
        # If no unit was selected, select the first or last one depending on direction
        if not previously_selected_unit:
            # In reverse mode, start from the last unit
            next_unit = player_units[-1 if reverse else 0]
        else:
            # Find the index of the currently selected unit
            try:
                current_index = player_units.index(previously_selected_unit)
                
                # Calculate the next index based on direction
                if reverse:
                    # Select the previous unit (loop back to last if at the beginning)
                    next_index = (current_index - 1) % len(player_units)
                else:
                    # Select the next unit (loop back to first if at the end)
                    next_index = (current_index + 1) % len(player_units)
                    
                next_unit = player_units[next_index]
            except ValueError:
                # If the selected unit isn't in the player's units (could happen in test mode)
                # In reverse mode, start from the last unit
                next_unit = player_units[-1 if reverse else 0]
        
        # Only deselect the current unit after finding the next one
        if previously_selected_unit:
            self._deselect_unit()
            
        # Move cursor to the next unit's position
        previous_pos = self.cursor_pos
        
        # Set position based on whether unit has a move target
        if next_unit.move_target:
            self.cursor_pos = Position(next_unit.move_target[0], next_unit.move_target[1])
        else:
            self.cursor_pos = Position(next_unit.y, next_unit.x)
            
        # Publish cursor moved event if position changed
        if self.cursor_pos != previous_pos:
            self.publish_event(
                EventType.CURSOR_MOVED, 
                CursorMovedEventData(position=self.cursor_pos, previous_position=previous_pos)
            )
        
        # Select the unit
        self.selected_unit = next_unit
        
        # Publish unit selected event
        self.publish_event(
            EventType.UNIT_SELECTED,
            UnitSelectedEventData(unit=next_unit, position=self.cursor_pos)
        )
        
        # Clear message to avoid redundancy with unit info display
        self.game_ui.message = ""
        
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
        self.setup_unit_type = UnitType.GLAIVEMAN  # Default unit type for setup phase
    
    def _setup_event_handlers(self):
        """Set up event handlers for game mode manager."""
        # Subscribe to unit selection events to update UI as needed
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
    
    def _on_unit_selected(self, event_type, event_data):
        """Handle unit selection events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_unit_deselected(self, event_type, event_data):
        """Handle unit deselection events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def set_mode(self, new_mode):
        """Set the game mode with event notification."""
        if new_mode != self.mode:
            old_mode = self.mode
            self.mode = new_mode
            
            # Publish mode changed event
            self.publish_event(
                EventType.MODE_CHANGED,
                ModeChangedEventData(new_mode=new_mode, previous_mode=old_mode)
            )
    
    def handle_cancel(self):
        """Handle cancel action (Escape key or 'c' key).
        Cancels the current action based on the current state.
        """
        cursor_manager = self.game_ui.cursor_manager
        
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
            
        # If in attack, move or skill mode, cancel the mode but keep unit selected
        if self.mode in ["attack", "move", "skill"] and cursor_manager.selected_unit:
            cursor_manager.highlighted_positions = []
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            self.game_ui.message = f"{self.mode.capitalize()} mode cancelled, unit still selected"
            self.game_ui.draw_board()
            return
            
        # If in skill_select mode, return to normal menu
        if self.mode == "skill_select" and cursor_manager.selected_unit:
            # Return to standard menu
            self.set_mode("select")
            # Reset action menu to standard mode
            self.game_ui.action_menu_component.populate_actions(cursor_manager.selected_unit)
            self.game_ui.message = "Skill selection cancelled"
            self.game_ui.draw_board()
            return
            
        # If unit is selected with a planned move, cancel the move
        if cursor_manager.selected_unit and cursor_manager.selected_unit.move_target:
            # Store position info for event before canceling move
            from_position = Position(cursor_manager.selected_unit.y, cursor_manager.selected_unit.x)
            to_position = Position(
                cursor_manager.selected_unit.move_target[0],
                cursor_manager.selected_unit.move_target[1]
            )
            unit = cursor_manager.selected_unit
            
            # Cancel the move
            cursor_manager.selected_unit.move_target = None
            
            # Publish move canceled event - could be useful for UI components
            self.publish_event(
                EventType.MOVE_CANCELLED,
                MoveEventData(
                    unit=unit,
                    from_position=from_position,
                    to_position=to_position
                )
            )
            
            self.game_ui.message = "Move order cancelled"
            self.game_ui.draw_board()
            return
            
        # If unit is selected with a planned attack, cancel the attack
        if cursor_manager.selected_unit and cursor_manager.selected_unit.attack_target:
            # Get target unit for event data
            target_position = cursor_manager.selected_unit.attack_target
            target = self.game_ui.game.get_unit_at(target_position[0], target_position[1])
            attacker = cursor_manager.selected_unit
            
            # Cancel the attack
            cursor_manager.selected_unit.attack_target = None
            
            # Publish attack canceled event - could be useful for UI components
            if target:
                self.publish_event(
                    EventType.ATTACK_CANCELLED,
                    AttackEventData(
                        attacker=attacker,
                        target=target
                    )
                )
            
            self.game_ui.message = "Attack order cancelled"
            self.game_ui.draw_board()
            return
            
        # Otherwise, clear the selection entirely
        cursor_manager.clear_selection()
        # Ensure we're in select mode
        self.set_mode("select")
        self.game_ui.message = "Selection cleared"
        
        # Redraw the board to immediately update selection visuals
        self.game_ui.draw_board()
    
    def _setup_event_handlers(self):
        """Set up event handlers for game mode manager."""
        # Subscribe to unit selection events to update UI as needed
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
        
        # Subscribe to mode request events
        self.subscribe_to_event(EventType.MOVE_MODE_REQUESTED, self._on_move_mode_requested)
        self.subscribe_to_event(EventType.ATTACK_MODE_REQUESTED, self._on_attack_mode_requested)
        self.subscribe_to_event(EventType.SKILL_MODE_REQUESTED, self._on_skill_mode_requested)
        self.subscribe_to_event(EventType.SELECT_MODE_REQUESTED, self._on_select_mode_requested)
        self.subscribe_to_event(EventType.CANCEL_REQUESTED, self._on_cancel_requested)
        
    def _on_move_mode_requested(self, event_type, event_data):
        """Handle move mode request events."""
        # Delegate to handle_move_mode which already has the logic
        self.handle_move_mode()
        
    def _on_attack_mode_requested(self, event_type, event_data):
        """Handle attack mode request events."""
        # Delegate to handle_attack_mode which already has the logic
        self.handle_attack_mode()
        
    def _on_skill_mode_requested(self, event_type, event_data):
        """Handle skill mode request events."""
        # Delegate to handle_skill_mode which we'll implement
        self.handle_skill_mode()
        
    def _on_select_mode_requested(self, event_type, event_data):
        """Handle select mode request events."""
        # Simply change to select mode
        self.set_mode("select")
        
    def _on_cancel_requested(self, event_type, event_data):
        """Handle cancel request events."""
        # Delegate to handle_cancel which already has the logic
        self.handle_cancel()
        
    def handle_move_mode(self):
        """Enter move mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn!",
                    message_type=MessageType.WARNING
                )
            )
            return
                
        if cursor_manager.selected_unit:
            current_player = self.game_ui.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            # Also allow control in local multiplayer for the active player
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if unit has already planned an attack or skill use
                if cursor_manager.selected_unit.attack_target:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned an attack and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit has already planned a skill use
                if cursor_manager.selected_unit.skill_target and cursor_manager.selected_unit.selected_skill:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned a skill use and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is trapped
                if cursor_manager.selected_unit.trapped_by is not None:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is trapped and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is affected by Jawline
                if hasattr(cursor_manager.selected_unit, 'jawline_affected') and cursor_manager.selected_unit.jawline_affected:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is immobilized by Jawline and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is an echo (cannot move)
                if cursor_manager.selected_unit.is_echo:
                    # Don't show a message, just silently return
                    return
                    
                # Change mode (will publish mode changed event)
                self.set_mode("move")
                
                # Convert positions to Position objects
                cursor_manager.highlighted_positions = [
                    Position(y, x) for y, x in self.game_ui.game.get_possible_moves(cursor_manager.selected_unit)
                ]
                
                if not cursor_manager.highlighted_positions:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No valid moves available",
                            message_type=MessageType.WARNING
                        )
                    )
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only move your own units!",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No unit selected",
                    message_type=MessageType.WARNING
                )
            )
    
    def handle_skill_mode(self):
        """Enter skill mode to select from available skills."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn!",
                    message_type=MessageType.WARNING
                )
            )
            return
                
        if cursor_manager.selected_unit:
            # Check if unit belongs to current player or test mode is on
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if unit has already planned an attack
                if cursor_manager.selected_unit.attack_target:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned an attack and cannot use a skill",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is trapped
                if cursor_manager.selected_unit.trapped_by is not None:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is trapped and cannot use skills",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is an echo (cannot use skills)
                if cursor_manager.selected_unit.is_echo:
                    # Don't show a message, just silently return
                    return
                    
                # Previously there was a restriction that prevented using skills after moving
                # This has been removed to allow move+skill combinations
                
                # Get available skills (not on cooldown)
                available_skills = cursor_manager.selected_unit.get_available_skills()
                
                if not available_skills:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No available skills to use",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Change mode to skill selection
                self.set_mode("skill_select")
                
                # Update the action menu to show skills
                self.game_ui.action_menu_component.show_skill_menu(cursor_manager.selected_unit)
                
                # Use event system for message
                # If the unit has a planned move, indicate that the skill will be used from the move position
                if cursor_manager.selected_unit.move_target:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select a skill to use from planned move position"
                        )
                    )
                else:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select a skill to use"
                        )
                    )
                
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only use skills with your own units!",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No unit selected",
                    message_type=MessageType.WARNING
                )
            )
            
    def handle_attack_mode(self):
        """Enter attack mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn!",
                    message_type=MessageType.WARNING
                )
            )
            return
                
        if cursor_manager.selected_unit:
            # Check if unit belongs to current player or test mode is on
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if the unit has already queued a skill
                if cursor_manager.selected_unit.skill_target and cursor_manager.selected_unit.selected_skill:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned a skill use and cannot attack",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Change mode (will publish mode changed event)
                self.set_mode("attack")
                
                # If we selected a unit directly, use its position
                # If we selected a ghost, always use the ghost position
                from_pos = None
                if cursor_manager.selected_unit.move_target:
                    from_pos = cursor_manager.selected_unit.move_target
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select attack from planned move position"
                        )
                    )
                else:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select attack target"
                        )
                    )
                
                # Convert positions to Position objects, using move destination if set
                cursor_manager.highlighted_positions = [
                    Position(y, x) for y, x in self.game_ui.game.get_possible_attacks(
                        cursor_manager.selected_unit, from_pos)
                ]
                
                if not cursor_manager.highlighted_positions:
                    # No message when there are no valid targets
                    pass
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only attack with your own units!",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No unit selected",
                    message_type=MessageType.WARNING
                )
            )
    
    def handle_select_in_select_mode(self):
        """Handle selection when in select mode."""
        return self.game_ui.cursor_manager.select_unit_at_cursor()
    
    def handle_select_in_move_mode(self):
        """Handle selection when in move mode."""
        result = self.game_ui.cursor_manager.select_move_target()
        if result:
            # Return to select mode after successful move (publishes mode changed event)
            self.set_mode("select")
        return result
    
    def handle_select_in_attack_mode(self):
        """Handle selection when in attack mode."""
        result = self.game_ui.cursor_manager.select_attack_target()
        if result:
            # Return to select mode after successful attack (publishes mode changed event)
            self.set_mode("select")
        return result
        
    def handle_select_in_skill_mode(self):
        """Handle selection when in skill mode."""
        result = self.select_skill_target()
        if result:
            # Return to select mode after successful skill use (publishes mode changed event)
            self.set_mode("select")
        return result
        
    def select_skill_target(self):
        """Select a target for the currently selected skill."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Get the selected unit and skill
        unit = cursor_manager.selected_unit
        if not unit or not unit.selected_skill:
            return False
            
        skill = unit.selected_skill
        
        # Special handling for Marrow Dike and Slough
        # These are self-targeted area skills that were pre-confirmed in _select_skill
        if skill.name in ["Marrow Dike", "Slough"] and unit.skill_target:
            # Use the skill with the pre-set target
            if skill.use(unit, unit.skill_target, self.game_ui.game):
                # Clear selection
                cursor_manager.highlighted_positions = []
                
                # Skill used successfully
                return True
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Failed to use {skill.name}",
                        message_type=MessageType.WARNING
                    )
                )
                return False
                
        # For normal skills, get the target position from cursor
        target_pos = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
        
        # Check if the target position is valid for this skill
        if cursor_manager.cursor_pos not in cursor_manager.highlighted_positions:
            # Simply return false without showing a message
            return False
            
        # Use the skill
        if skill.use(unit, target_pos, self.game_ui.game):
            # Clear selection
            cursor_manager.highlighted_positions = []
            
            # Skill used successfully
            return True
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Failed to use skill",
                    message_type=MessageType.WARNING
                )
            )
            return False
    
    def handle_end_turn(self):
        """End the current turn."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Publish turn ended event
        self.publish_event(
            EventType.TURN_ENDED,
            TurnEventData(
                player=self.game_ui.multiplayer.get_current_player(),
                turn_number=self.game_ui.game.turn
            )
        )
        
        # Pass UI to execute_turn for animations
        self.game_ui.game.execute_turn(self.game_ui)
        
        # Clear selection after executing turn
        cursor_manager.clear_selection()
        # Return to select mode
        self.set_mode("select")
        
        # Handle multiplayer turn switching
        if not self.game_ui.game.winner:
            # End turn in multiplayer manager
            self.game_ui.multiplayer.end_turn()
            self.game_ui.update_player_message()
            
            # Publish turn started event for the new player
            self.publish_event(
                EventType.TURN_STARTED,
                TurnEventData(
                    player=self.game_ui.multiplayer.get_current_player(),
                    turn_number=self.game_ui.game.turn
                )
            )
        else:
            # Publish game over event
            self.publish_event(
                EventType.GAME_OVER,
                GameOverEventData(winner=self.game_ui.game.winner)
            )
            
        # Redraw the board to update visuals
        self.game_ui.draw_board()
    
    def handle_test_mode(self):
        """
        Toggle test mode or toggle unit type during setup phase.
        The 't' key serves dual purpose - in setup phase it toggles unit type,
        during gameplay it toggles test mode.
        """
        # In setup phase, use the 't' key to toggle unit type instead of test mode
        # but only if we haven't enabled the actual test mode yet
        if self.game_ui.game.setup_phase and not self.game_ui.game.test_mode:
            self.toggle_setup_unit_type()
            return
            
        # Continue with normal test mode functionality
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
    
    def toggle_setup_unit_type(self):
        """
        Toggle between unit types during the setup phase.
        Cycles between GLAIVEMAN, MANDIBLE FOREMAN, GRAYMAN, MARROW_CONDENSER, FOWL_CONTRIVANCE, and GAS_MACHINIST.
        """
        if self.setup_unit_type == UnitType.GLAIVEMAN:
            self.setup_unit_type = UnitType.MANDIBLE_FOREMAN
            self.game_ui.message = "Setup unit type: MANDIBLE FOREMAN"
        elif self.setup_unit_type == UnitType.MANDIBLE_FOREMAN:
            self.setup_unit_type = UnitType.GRAYMAN
            self.game_ui.message = "Setup unit type: GRAYMAN"
        elif self.setup_unit_type == UnitType.GRAYMAN:
            self.setup_unit_type = UnitType.MARROW_CONDENSER
            self.game_ui.message = "Setup unit type: MARROW CONDENSER"
        elif self.setup_unit_type == UnitType.MARROW_CONDENSER:
            self.setup_unit_type = UnitType.FOWL_CONTRIVANCE
            self.game_ui.message = "Setup unit type: FOWL CONTRIVANCE"
        elif self.setup_unit_type == UnitType.FOWL_CONTRIVANCE:
            self.setup_unit_type = UnitType.GAS_MACHINIST
            self.game_ui.message = "Setup unit type: GAS MACHINIST"
        else:
            self.setup_unit_type = UnitType.GLAIVEMAN
            self.game_ui.message = "Setup unit type: GLAIVEMAN"
        
        # Redraw the board to show the message
        self.game_ui.draw_board()
        
    def handle_setup_select(self):
        """Handle unit placement during setup phase."""
        # Get the current setup player
        setup_player = self.game_ui.game.setup_player
        cursor_pos = self.game_ui.cursor_manager.cursor_pos
        
        # Check if cursor position is in bounds
        if not self.game_ui.game.is_valid_position(cursor_pos.y, cursor_pos.x):
            self.game_ui.message = f"Cannot place unit here: out of bounds"
            return
            
        # Check if cursor position has blocking terrain
        if not self.game_ui.game.map.can_place_unit(cursor_pos.y, cursor_pos.x):
            self.game_ui.message = f"Cannot place unit here: blocked by limestone"
            return
            
        # Check if there are units remaining to place
        if self.game_ui.game.setup_units_remaining[setup_player] <= 0:
            self.game_ui.message = f"All units placed. Press 'y' to confirm."
            return
            
        # Try to place the unit with the current unit type
        success = self.game_ui.game.place_setup_unit(cursor_pos.y, cursor_pos.x, self.setup_unit_type)
        
        if success:
            # Unit was placed at the original position
            unit_type_name = {
                UnitType.GLAIVEMAN: "GLAIVEMAN",
                UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
                UnitType.GRAYMAN: "GRAYMAN",
                UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
                UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
                UnitType.GAS_MACHINIST: "GAS MACHINIST"
            }.get(self.setup_unit_type, "UNKNOWN")
            
            self.game_ui.message = f"{unit_type_name} placed. {self.game_ui.game.setup_units_remaining[setup_player]} remaining."
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
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message=f"Place all units before confirming ({self.game_ui.game.setup_units_remaining[setup_player]} remaining)",
                    message_type=MessageType.WARNING
                )
            )
            return
            
        # Confirm the current player's setup
        game_start = self.game_ui.game.confirm_setup()
        
        # No special handling for VS_AI mode yet - it's not implemented
        is_vs_ai_mode = False
        
        # Add appropriate status message through event system
        if setup_player == 1:
            # No special setup for AI mode yet (would be implemented here)
            
            # Show game start message if game is started
            if game_start:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Game begins! Player 1's turn",
                        message_type=MessageType.SYSTEM
                        )
                    )
            else:
                # Normal local multiplayer mode
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Setup confirmed. Player 2's turn to place units.",
                        message_type=MessageType.SYSTEM
                    )
                )
                # Start player 2 with cursor in center
                self.game_ui.cursor_manager.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)
                # Publish cursor moved event
                self.publish_event(
                    EventType.CURSOR_MOVED, 
                    CursorMovedEventData(position=self.game_ui.cursor_manager.cursor_pos)
                )
        elif game_start:
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Game begins!",
                    message_type=MessageType.SYSTEM
                )
            )
            
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
    # This function would be implemented later for AI mode
    def _placeholder_for_ai_setup(self):
        """Placeholder for future AI unit auto-setup functionality."""
        from boneglaive.utils.debug import logger
        logger.info("AI setup functionality not implemented yet")
        
    def check_confirmation_needed(self):
        """Check if confirmation is needed in setup phase."""
        if not self.game_ui.game.setup_phase:
            return False
        
        # Check if all units have been placed
        setup_player = self.game_ui.game.setup_player
        return self.game_ui.game.setup_units_remaining[setup_player] == 0
            
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
            
            # Map UnitType to display name
            unit_type_display = {
                UnitType.GLAIVEMAN: "GLAIVEMAN",
                UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
                UnitType.GRAYMAN: "GRAYMAN",
                UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
                UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
                UnitType.GAS_MACHINIST: "GAS MACHINIST"
            }
            current_unit_type = unit_type_display.get(self.setup_unit_type, "UNKNOWN")
            
            instructions = [
                f"Player {setup_player}, place your units on the battlefield.",
                "",
                f"Each player must place 3 units (Current unit type: {current_unit_type}).",
                "",
                "Controls:",
                "- Arrow keys or HJKL: Move cursor",
                "- YUBN: Move cursor diagonally",
                "- Enter/Space: Place unit at cursor position",
                "- [Backspace]: Switch between unit types",
                "- [Y]es: Confirm unit placement (when all units are placed)",
                "",
                "Special rules:",
                "- Player 1's units will be hidden during Player 2's placement",
                "- After both players finish placement, any units overlapping",
                "  will be automatically displaced to nearby positions",
                "- First-placed units will remain in their positions",
                "",
                "Note: The 'y' key works as diagonal movement until all units are placed,",
                "      then it becomes [Y]es confirmation key."
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
        # Import required modules
        from boneglaive.utils.constants import UnitType
        import time
        import curses
        
        # Get attack effect from asset manager
        effect_tile = self.game_ui.asset_manager.get_attack_effect(attacker.type)
        
        # Get animation sequence
        animation_sequence = self.game_ui.asset_manager.get_attack_animation_sequence(attacker.type)
        
        # Create start and end positions
        start_pos = Position(attacker.y, attacker.x)
        end_pos = Position(target.y, target.x)
        
        # For ranged attacks (archer and mage), show animation at origin then projectile path
        if attacker.type in [UnitType.ARCHER, UnitType.MAGE]:
            # First show attack preparation at attacker's position
            prep_sequence = animation_sequence[:2]  # First few frames of animation sequence
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x,
                prep_sequence,
                7,  # color ID
                0.2  # quick preparation animation
            )
            
            # Then animate projectile from attacker to target
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                effect_tile,
                7,  # color ID
                0.3  # duration
            )
        # For MANDIBLE_FOREMAN, show a special animation sequence for mandible jaws
        elif attacker.type == UnitType.MANDIBLE_FOREMAN:
            # Show the jaws animation at the attacker's position
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence[:3],  # First three frames - jaws opening
                7,  # color ID
                0.3  # slightly faster animation
            )
            
            # Show a short connecting animation between attacker and target
            # to visualize the mandibles reaching out
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                'Ξ',  # Mandible symbol
                7,    # color ID
                0.2   # quick connection
            )
            
            # Show the final part of the animation at the target position
            self.renderer.animate_attack_sequence(
                end_pos.y, end_pos.x, 
                animation_sequence[3:],  # Last frames - jaws clamping and retracting
                7,  # color ID
                0.4  # duration
            )
        # For GLAIVEMAN attacks, check range and choose the right animation
        elif attacker.type == UnitType.GLAIVEMAN:
            # Calculate distance to target
            distance = self.game_ui.game.chess_distance(start_pos.y, start_pos.x, end_pos.y, end_pos.x)
            
            # For range 2 attacks, use extended animation
            if distance == 2:
                # Get the extended animation sequence
                extended_sequence = self.game_ui.asset_manager.animation_sequences.get('glaiveman_extended_attack', [])
                if extended_sequence:
                    # First show windup animation at attacker's position
                    self.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        extended_sequence[:4],  # First few frames at attacker position
                        7,  # color ID
                        0.3  # duration
                    )
                    
                    # Then animate the glaive extending from attacker to target
                    # Calculate direction from attacker to target
                    from boneglaive.utils.coordinates import get_line
                    path = get_line(start_pos, end_pos)
                    
                    # Get the middle position for the extending animation (if path has at least 3 points)
                    if len(path) >= 3:
                        mid_pos = path[1]  # Second point in the path
                        
                        # Show glaive extending through middle position
                        extension_chars = extended_sequence[4:8]  # Middle frames show extension
                        for i, char in enumerate(extension_chars):
                            self.renderer.draw_tile(mid_pos.y, mid_pos.x, char, 7)
                            self.renderer.refresh()
                            time.sleep(0.1)
                    
                    # Finally show the impact at target position
                    self.renderer.animate_attack_sequence(
                        end_pos.y, end_pos.x, 
                        extended_sequence[8:],  # Last frames at target position
                        7,  # color ID
                        0.3  # duration
                    )
                else:
                    # Fallback to standard animation if extended sequence isn't available
                    self.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        animation_sequence,
                        7,  # color ID
                        0.5  # duration
                    )
            else:
                # For range 1 attacks, use standard animation
                self.renderer.animate_attack_sequence(
                    start_pos.y, start_pos.x, 
                    animation_sequence,
                    7,  # color ID
                    0.5  # duration
                )
        # Special case for FOWL_CONTRIVANCE - more elaborate bird swarm animation
        elif attacker.type == UnitType.FOWL_CONTRIVANCE:
            # Get a more elaborate animation sequence for bird attacks
            fowl_sequence = self.game_ui.asset_manager.animation_sequences.get('fowl_contrivance_attack', [])
            if not fowl_sequence:
                fowl_sequence = ['^', 'v', '>', '<', '^', 'v', 'Λ', 'V']  # Fallback bird animation
            
            # Use alternating colors for a more dynamic bird flock appearance
            color_sequence = [1, 4, 1, 4, 6, 7, 6, 7]  # Red, blue, yellow, white alternating
            
            # Show initial gathering animation at attacker's position
            for i in range(3):
                frame = fowl_sequence[i % len(fowl_sequence)]
                color = color_sequence[i % len(color_sequence)]
                self.renderer.draw_tile(start_pos.y, start_pos.x, frame, color)
                self.renderer.refresh()
                time.sleep(0.08)
            
            # Create path points between attacker and target
            from boneglaive.game.animations import get_line
            path = get_line(start_pos.y, start_pos.x, end_pos.y, end_pos.x)
            
            # Animate along the path with varied bird symbols
            for i, (y, x) in enumerate(path[1:-1]):  # Skip first (attacker) and last (target)
                frame_idx = (i + 3) % len(fowl_sequence)  # Continue from where gathering left off
                color_idx = (i + 3) % len(color_sequence)
                self.renderer.draw_tile(y, x, fowl_sequence[frame_idx], color_sequence[color_idx])
                self.renderer.refresh()
                time.sleep(0.05)
            
            # Final impact animation directly at target
            final_frames = ['^', 'V', 'Λ', 'v', '♦']
            for i, frame in enumerate(final_frames):
                color = 1 if i % 2 == 0 else 7  # Alternate between red and white
                self.renderer.draw_tile(end_pos.y, end_pos.x, frame, color)
                self.renderer.refresh()
                time.sleep(0.1)
        
        # For all other melee attacks, show standard animation
        else:
            # Show the attack animation at the attacker's position
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence,
                7,  # color ID
                0.5  # duration
            )
        
        # Show impact animation at target position with appropriate ASCII characters based on unit type
        if attacker.type == UnitType.MAGE:
            impact_animation = ['!', '*', '!']  # Magic impact
        elif attacker.type == UnitType.MANDIBLE_FOREMAN:
            impact_animation = ['>', '<', '}', '{', '≡']  # Mandible crushing impact
        elif attacker.type == UnitType.FOWL_CONTRIVANCE:
            impact_animation = ['^', 'v', '^', 'V', 'Λ']  # Bird dive impact
        else:
            impact_animation = ['+', 'x', '+']  # Standard melee/arrow impact
            
        impact_colors = [7] * len(impact_animation)
        impact_durations = [0.05] * len(impact_animation)
        
        # Use renderer's animate_attack_sequence for impact
        self.renderer.animate_attack_sequence(
            target.y, target.x,
            impact_animation,
            7,  # color ID 
            0.25  # duration
        )
        
        # Flash the target to show it was hit
        tile_ids = [self.game_ui.asset_manager.get_unit_tile(target.type)] * 4
        color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 2
        durations = [0.1] * 4
        
        # Use renderer's flash tile method
        self.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Show damage number above target with improved visualization
        # Use effective stats for correct damage display
        effective_attack = attacker.get_effective_stats()['attack']
        effective_defense = target.get_effective_stats()['defense']
        
        # Account for GRAYMAN units that bypass defense
        from boneglaive.utils.constants import UnitType
        if attacker.type == UnitType.GRAYMAN or (hasattr(attacker, 'is_echo') and attacker.is_echo and attacker.type == UnitType.GRAYMAN):
            # GRAYMAN units bypass defense completely
            damage = effective_attack
        else:
            # Normal damage calculation
            damage = max(1, effective_attack - effective_defense)
            
        damage_text = f"-{damage}"
        
        # Make damage text more prominent
        for i in range(3):
            # First clear the area
            self.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
            # Draw with alternating bold/normal for a flashing effect
            attrs = curses.A_BOLD if i % 2 == 0 else 0
            self.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
            self.renderer.refresh()
            time.sleep(0.1)
            
        # Final damage display (stays on screen slightly longer)
        self.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
        self.renderer.refresh()
        time.sleep(0.3)
        
        # Redraw board to clear effects (without cursor, selection, or attack target highlighting)
        self.game_ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

# Action menu component
class ActionMenuComponent(UIComponent):
    """Component for displaying and handling the unit action menu."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.visible = False
        self.actions = []
        self.selected_index = 0
        self.menu_mode = "standard"  # Can be "standard" or "skills"
        self.jawline_shown_units = set()  # Track units that have shown Jawline messages
        
        # Need to import UnitType for unit-specific skill checks
        from boneglaive.utils.constants import UnitType
        self.UnitType = UnitType
        
    def _setup_event_handlers(self):
        """Set up event handlers for action menu."""
        # Subscribe to unit selection/deselection events
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
        
    def _on_unit_selected(self, event_type, event_data):
        """Handle unit selection events."""
        unit = event_data.unit
        # Show menu and populate actions
        self.visible = True
        self.populate_actions(unit)
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
    def _on_unit_deselected(self, event_type, event_data):
        """Handle unit deselection events."""
        # Hide menu
        self.visible = False
        # Reset action list and selection
        self.actions = []
        self.selected_index = 0
        
    def populate_actions(self, unit):
        """
        Populate available actions for the selected unit.
        
        Note: Action labels should follow the [K]ey format convention:
        - The key is shown in brackets and capitalized
        - The rest of the label is lowercase and without spaces
        - Example: [M]ove, [A]ttack, [S]kills
        This convention is used throughout the game UI.
        """
        self.actions = []
        self.menu_mode = "standard"
        
        # Add standard actions with consistent labeling
        # Disable move for trapped units, Jawline-affected units, or echoes (echoes can't move)
        unit_can_move = (unit is not None and
                        unit.trapped_by is None and
                        not unit.is_echo and
                        not (hasattr(unit, 'jawline_affected') and unit.jawline_affected))
        self.actions.append({
            'key': 'm',
            'label': 'ove',  # Will be displayed as [M]ove without space
            'action': GameAction.MOVE_MODE,
            'enabled': unit_can_move  # Enabled only if unit can move
        })
        
        self.actions.append({
            'key': 'a',
            'label': 'ttack',  # Will be displayed as [A]ttack without space
            'action': GameAction.ATTACK_MODE,
            'enabled': True
        })
        
        # Add skill action
        unit_has_skills = unit is not None and hasattr(unit, 'active_skills') and len(unit.get_available_skills()) > 0
        unit_can_use_skills = unit_has_skills and unit.trapped_by is None and not unit.is_echo
        self.actions.append({
            'key': 's',
            'label': 'kills',  # Will be displayed as [S]kills without space
            'action': GameAction.SKILL_MODE,
            'enabled': unit_can_use_skills  # Enabled if unit has available skills, is not trapped, and not an echo
        })
        
        # Reset selected index
        self.selected_index = 0
        
    def show_skill_menu(self, unit):
        """
        Show a menu of available skills for the selected unit.
        Only shows skills specific to that unit type.
        
        Args:
            unit: The unit whose skills to display
        """
        self.actions = []
        self.menu_mode = "skills"
        
        # Get available skills
        available_skills = []
        if unit and hasattr(unit, 'active_skills'):
            available_skills = unit.get_available_skills()
        
        # GLAIVEMAN skills
        if unit.type == self.UnitType.GLAIVEMAN:
            # Add Pry skill
            pry_skill = next((skill for skill in available_skills if skill.name == "Pry"), None)
            self.actions.append({
                'key': 'p',
                'label': 'ry',  # Will be displayed as [P]ry
                'action': 'pry_skill',
                'enabled': pry_skill is not None,
                'skill': pry_skill
            })
            
            # Add Vault skill
            vault_skill = next((skill for skill in available_skills if skill.name == "Vault"), None)
            self.actions.append({
                'key': 'v',
                'label': 'ault',  # Will be displayed as [V]ault
                'action': 'vault_skill',
                'enabled': vault_skill is not None,
                'skill': vault_skill
            })
            
            # Add Judgement skill
            judgement_skill = next((skill for skill in available_skills if skill.name == "Judgement"), None)
            self.actions.append({
                'key': 'j',
                'label': 'udgement',  # Will be displayed as [J]udgement
                'action': 'judgement_skill',
                'enabled': judgement_skill is not None,
                'skill': judgement_skill
            })
        
        # MANDIBLE_FOREMAN skills
        elif unit.type == self.UnitType.MANDIBLE_FOREMAN:
            
            # Add Expedite skill (previously Discharge)
            expedite_skill = next((skill for skill in available_skills if skill.name == "Expedite"), None)
            self.actions.append({
                'key': 'e',
                'label': 'xpedite',  # Will be displayed as [E]xpedite
                'action': 'expedite_skill',
                'enabled': expedite_skill is not None,
                'skill': expedite_skill
            })
            
            # Add Site Inspection skill
            site_inspection_skill = next((skill for skill in available_skills if skill.name == "Site Inspection"), None)
            self.actions.append({
                'key': 's',
                'label': 'ite Inspection',  # Will be displayed as [S]ite Inspection
                'action': 'site_inspection_skill',
                'enabled': site_inspection_skill is not None,
                'skill': site_inspection_skill
            })
            
            # Add Jawline skill
            jawline_skill = next((skill for skill in available_skills if skill.name == "Jawline"), None)
            self.actions.append({
                'key': 'j',
                'label': 'awline',  # Will be displayed as [J]awline
                'action': 'jawline_skill',
                'enabled': jawline_skill is not None,
                'skill': jawline_skill
            })
        
        # GRAYMAN skills
        elif unit.type == self.UnitType.GRAYMAN:
            
            # Add Delta Config skill
            delta_config_skill = next((skill for skill in available_skills if skill.name == "Delta Config"), None)
            self.actions.append({
                'key': 'd',
                'label': 'elta Config',  # Will be displayed as [D]elta Config
                'action': 'delta_config_skill',
                'enabled': delta_config_skill is not None,
                'skill': delta_config_skill
            })
            
            # Add Estrange skill
            estrange_skill = next((skill for skill in available_skills if skill.name == "Estrange"), None)
            self.actions.append({
                'key': 'e',
                'label': 'strange',  # Will be displayed as [E]strange
                'action': 'estrange_skill',
                'enabled': estrange_skill is not None,
                'skill': estrange_skill
            })
            
            # Add Græ Exchange skill
            grae_exchange_skill = next((skill for skill in available_skills if skill.name == "Græ Exchange"), None)
            self.actions.append({
                'key': 'g',
                'label': 'ræ Exchange',  # Will be displayed as [G]ræ Exchange
                'action': 'grae_exchange_skill',
                'enabled': grae_exchange_skill is not None,
                'skill': grae_exchange_skill
            })
            
        # MARROW_CONDENSER skills
        elif unit.type == self.UnitType.MARROW_CONDENSER:
            
            # Add Ossify skill
            ossify_skill = next((skill for skill in available_skills if skill.name == "Ossify"), None)
            self.actions.append({
                'key': 'o',
                'label': 'ssify',  # Will be displayed as [O]ssify
                'action': 'ossify_skill',
                'enabled': ossify_skill is not None,
                'skill': ossify_skill
            })
            
            # Add Marrow Dike skill
            marrow_dike_skill = next((skill for skill in available_skills if skill.name == "Marrow Dike"), None)
            self.actions.append({
                'key': 'm',
                'label': 'arrow Dike',  # Will be displayed as [M]arrow Dike
                'action': 'marrow_dike_skill',
                'enabled': marrow_dike_skill is not None,
                'skill': marrow_dike_skill
            })
            
            # Add Bone Tithe skill
            bone_tithe_skill = next((skill for skill in available_skills if skill.name == "Bone Tithe"), None)
            self.actions.append({
                'key': 'b',
                'label': 'one Tithe',  # Will be displayed as [B]one Tithe
                'action': 'bone_tithe_skill',
                'enabled': bone_tithe_skill is not None,
                'skill': bone_tithe_skill
            })
            
        # FOWL_CONTRIVANCE skills
        elif unit.type == self.UnitType.FOWL_CONTRIVANCE:
            
            # Add Murmuration Dusk skill
            murmuration_skill = next((skill for skill in available_skills if skill.name == "Murmuration Dusk"), None)
            self.actions.append({
                'key': 'm',
                'label': 'urmuration Dusk',  # Will be displayed as [M]urmuration Dusk
                'action': 'murmuration_skill',
                'enabled': murmuration_skill is not None,
                'skill': murmuration_skill
            })
            
            # Add Flap skill
            flap_skill = next((skill for skill in available_skills if skill.name == "Flap"), None)
            self.actions.append({
                'key': 'f',
                'label': 'lap',  # Will be displayed as [F]lap
                'action': 'flap_skill',
                'enabled': flap_skill is not None,
                'skill': flap_skill
            })
            
            # Add Emetic Flange skill
            emetic_flange_skill = next((skill for skill in available_skills if skill.name == "Emetic Flange"), None)
            self.actions.append({
                'key': 'e',
                'label': 'metic Flange',  # Will be displayed as [E]metic Flange
                'action': 'emetic_flange_skill',
                'enabled': emetic_flange_skill is not None,
                'skill': emetic_flange_skill
            })
        
        # Reset selected index
        self.selected_index = 0
        
    def draw(self):
        """Draw the action menu."""
        if not self.visible or not self.actions:
            return
            
        # Get unit info for header
        unit = self.game_ui.cursor_manager.selected_unit
        if not unit:
            return
            
        # Calculate menu position
        menu_x = WIDTH * 2 + 2  # Position to the right of the map
        menu_y = 2              # Start higher up to avoid collision with bottom UI elements
        
        # Calculate menu dimensions
        menu_width = 25  # Width that comfortably fits content
        menu_height = len(self.actions) + 4  # Add extra space to ensure all items fit within borders
        
        # Draw menu border
        # Top border
        self.renderer.draw_text(menu_y, menu_x, "┌" + "─" * (menu_width - 2) + "┐", 1)
        
        # Side borders
        for i in range(1, menu_height - 1):
            self.renderer.draw_text(menu_y + i, menu_x, "│", 1)
            self.renderer.draw_text(menu_y + i, menu_x + menu_width - 1, "│", 1)
        
        # Bottom border
        self.renderer.draw_text(menu_y + menu_height - 1, menu_x, "└" + "─" * (menu_width - 2) + "┘", 1)
        
        # Draw menu header with unit player color
        player_color = 3 if unit.player == 1 else 4
        
        # Set header text based on menu mode, using shortened name for menus
        if self.menu_mode == "standard":
            header = f" {unit.get_display_name(shortened=True)} Actions "
        else:
            header = f" {unit.get_display_name(shortened=True)} Skills "
        
        # Center the header
        header_x = menu_x + (menu_width - len(header)) // 2
        self.renderer.draw_text(menu_y + 1, header_x, header, player_color, curses.A_BOLD)
        
        # Draw a separator line
        self.renderer.draw_text(menu_y + 2, menu_x + 1, "─" * (menu_width - 2), 1)
        
        # Draw menu items
        for i, action in enumerate(self.actions):
            y_pos = menu_y + i + 3  # Position after header and separator
            
            # Format action label with capitalized key directly followed by lowercase label: [K]ey
            # Combined into a single string for consistent spacing
            if 'key_display' in action:
                # Use key_display for special keys like ESC
                key_display = action['key_display']
            else:
                # For regular keys, capitalize
                key_display = action['key'].upper()
                
            action_text = f"[{key_display}]{action['label']}"
            
            # Calculate x position with consistent left margin
            action_x = menu_x + 3  # Left margin for all actions
            
            # Choose color based on whether action is enabled
            key_color = player_color if action['enabled'] else 8  # Player color or gray
            
            # Special handling for placeholder skills (marked as not implemented)
            if 'placeholder' in action and action['placeholder']:
                label_color = 7  # Yellow for placeholders
            else:
                label_color = 1 if action['enabled'] else 8  # Normal color or gray
            
            # Set attributes based on enabled status
            attr = curses.A_BOLD if action['enabled'] else curses.A_DIM
            
            # Draw the action text
            key_length = 3  # Length of "[X]" part
            
            # Draw the key part with key color
            self.renderer.draw_text(y_pos, action_x, action_text[:key_length], key_color, attr)
            
            # Draw the label part with label color
            self.renderer.draw_text(y_pos, action_x + key_length, action_text[key_length:], label_color, attr)
            
        # No ESC cancel text per user request
        
    def handle_input(self, key: int) -> bool:
        """Handle input specific to the action menu."""
        if not self.visible:
            return False
            
        # Exit if no actions
        if not self.actions:
            return False
        
        # Handle escape key for the skills menu (return to standard menu)
        if self.menu_mode == "skills" and key == 27:  # Escape key
            # Return to standard menu
            self.publish_event(EventType.CANCEL_REQUESTED, EventData())
            return True
            
        # Handle direct key selection based on menu mode
        for action in self.actions:
            # Check if key matches - handle both char and int keys
            key_match = False
            if isinstance(action['key'], str) and len(action['key']) == 1:
                key_match = (key == ord(action['key']))
            elif isinstance(action['key'], str) and len(action['key']) > 1:
                # Special escape sequence
                if action['key'] == '\x1b' and key == 27:  # ESC key
                    key_match = True
            else:
                key_match = (key == action['key'])
            
            # For standard menu, key must match and action must be enabled    
            if key_match and action['enabled']:
                # Standard menu actions
                if self.menu_mode == "standard":
                    if action['action'] == GameAction.MOVE_MODE:
                        self.publish_event(EventType.MOVE_MODE_REQUESTED, EventData())
                    elif action['action'] == GameAction.ATTACK_MODE:
                        self.publish_event(EventType.ATTACK_MODE_REQUESTED, EventData())
                    elif action['action'] == GameAction.SKILL_MODE:
                        self.publish_event(EventType.SKILL_MODE_REQUESTED, EventData())
                    return True
                
                # Skills menu actions
                elif self.menu_mode == "skills":
                    # For placeholder skills, show message but don't select
                    if 'placeholder' in action and action['placeholder']:
                        self.publish_event(
                            EventType.MESSAGE_DISPLAY_REQUESTED,
                            MessageDisplayEventData(
                                message=f"{action['key'].upper()}{action['label']} not yet implemented",
                                message_type=MessageType.WARNING
                            )
                        )
                        return True
                    
                    # Handle specific skill selection - simplified to handle any action['action']
                    skill = action.get('skill')
                    if skill:
                        self._select_skill(skill)
                        return True
                
        # All other keys pass through - this allows movement keys to still work
        return False
        
    def _select_skill(self, skill):
        """
        Select a skill to use and enter targeting mode.
        
        Args:
            skill: The skill to use
        """
        cursor_manager = self.game_ui.cursor_manager
        mode_manager = self.game_ui.mode_manager
        
        # Set the selected skill
        if cursor_manager.selected_unit:
            cursor_manager.selected_unit.selected_skill = skill
            
            # Change to skill targeting mode
            mode_manager.set_mode("skill")
            
            # Highlight valid targets for the skill based on target type
            game = self.game_ui.game
            targets = []
            from boneglaive.utils.constants import HEIGHT, WIDTH
            
            # Get the unit's current or planned position
            from_y = cursor_manager.selected_unit.y
            from_x = cursor_manager.selected_unit.x
            
            # If unit has a planned move, use that position instead
            if cursor_manager.selected_unit.move_target:
                from_y, from_x = cursor_manager.selected_unit.move_target
            
            # Special visualization for MARROW_CONDENSER area skills
            if skill.name in ["Marrow Dike", "Bone Tithe"]:
                # Special visual indicators for MARROW_CONDENSER's area skills
                area_targets = []
                
                # Get area size from the skill
                area_size = getattr(skill, 'area', 1)  # Default to 1 if not specified
                
                # For Marrow Dike, we want to show the perimeter of the area (the walls)
                if skill.name == "Marrow Dike":
                    # Marrow Dike creates walls in a 5x5 perimeter (area=2)
                    for dy in range(-area_size, area_size+1):
                        for dx in range(-area_size, area_size+1):
                            # Only include perimeter tiles (not the interior)
                            if abs(dy) == area_size or abs(dx) == area_size:
                                tile_y, tile_x = from_y + dy, from_x + dx
                                if game.is_valid_position(tile_y, tile_x):
                                    area_targets.append(Position(tile_y, tile_x))
                    
                    # Also display a special message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message=f"Marrow Dike will create walls around the perimeter.",
                            message_type=MessageType.ABILITY
                        )
                    )
                # For Bone Tithe, we want to show all adjacent tiles
                elif skill.name == "Bone Tithe":
                    # Bone Tithe affects all tiles in a 3x3 area (area=1)
                    for dy in range(-area_size, area_size+1):
                        for dx in range(-area_size, area_size+1):
                            # Skip the center (MARROW_CONDENSER's position)
                            if dy == 0 and dx == 0:
                                continue
                            
                            tile_y, tile_x = from_y + dy, from_x + dx
                            if game.is_valid_position(tile_y, tile_x):
                                area_targets.append(Position(tile_y, tile_x))
                
                # Set highlighted positions for visualization
                cursor_manager.highlighted_positions = area_targets
                
                # Set skill target to self (it's a self-targeted skill)
                cursor_manager.selected_unit.skill_target = (from_y, from_x)
                
                # IMPORTANT: Use the skill now to properly set the cooldown
                # This is a self-targeted skill, similar to Jawline
                
                # For Marrow Dike, just use normal can_use/use flow
                if skill.name == "Marrow Dike":
                    if skill.can_use(cursor_manager.selected_unit, (from_y, from_x), game):
                        skill.use(cursor_manager.selected_unit, (from_y, from_x), game)
                # For Bone Tithe, we need to directly set the cooldown since its can_use check
                # may fail if there are no valid targets, but we still want to set cooldown
                elif skill.name == "Bone Tithe":
                    # Set skill target
                    cursor_manager.selected_unit.skill_target = (from_y, from_x)
                    cursor_manager.selected_unit.selected_skill = skill
                    
                    # Force set the cooldown directly
                    skill.current_cooldown = skill.cooldown
                    
                    # Log the message (similar to what's in skill.use())
                    message_log.add_message(
                        f"{cursor_manager.selected_unit.get_display_name()} prepares to collect the Bone Tithe!",
                        MessageType.ABILITY,
                        player=cursor_manager.selected_unit.player
                    )
                
                # Draw the board to show the highlighted area
                self.game_ui.draw_board()
                
                # Wait for user confirmation (handled by handle_select method)
                # The input handler will call handle_select when Space is pressed,
                # which will execute the skill
                
                # Return without requiring additional targeting
                return
            
            # Different targeting logic based on skill target type
            if skill.target_type == TargetType.SELF:
                # For self-targeted skills like Recalibrate or Jawline, use immediately without targeting
                if skill.can_use(cursor_manager.selected_unit, (from_y, from_x), game):
                    # Set the skill target to self
                    cursor_manager.selected_unit.skill_target = (from_y, from_x)
                    # Actually use the skill now
                    skill.use(cursor_manager.selected_unit, (from_y, from_x), game)
                    # Show message
                    unit = cursor_manager.selected_unit
                    
                    # Special message for Jawline skill
                    if skill.name == "Jawline":
                        # We no longer need to show a message here - it's shown in the skill's use() method
                        # Mark that we've shown this message to prevent any legacy code from showing it again
                        unit.jawline_message_shown = True
                    else:
                        message = f"{skill.name} will be used at end of turn"
                        
                        # Add the message directly to the message log with player information
                        # This ensures it will be colored according to the player
                        message_log.add_message(
                            text=message,
                            msg_type=MessageType.ABILITY,
                            player=unit.player,
                            attacker_name=unit.get_display_name()
                        )
                    
                    # Request a UI redraw to show the message immediately
                    self.publish_event(
                        EventType.UI_REDRAW_REQUESTED,
                        UIRedrawEventData()
                    )
                    # Return to select mode
                    mode_manager.set_mode("select")
                    return
                else:
                    # If can't use, don't show an error message
                    # Reset selected skill
                    cursor_manager.selected_unit.selected_skill = None
                    # Return to select mode
                    mode_manager.set_mode("select")
                    return
            elif skill.target_type == TargetType.ENEMY:
                # For enemy-targeted skills, highlight enemy units in range
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        # Check if there's an enemy unit at this position
                        target = game.get_unit_at(y, x)
                        if target and target.player != cursor_manager.selected_unit.player:
                            # Check if target is within skill range
                            distance = game.chess_distance(from_y, from_x, y, x)
                            
                            if distance <= skill.range:
                                # Check if skill can be used on this target
                                if skill.can_use(cursor_manager.selected_unit, (y, x), game):
                                    targets.append((y, x))
            
            elif skill.target_type == TargetType.AREA:
                # For area-targeted skills like Vault, highlight all valid positions
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        # Skip current position
                        if y == from_y and x == from_x:
                            continue
                            
                        # Check if position is within skill range
                        distance = game.chess_distance(from_y, from_x, y, x)
                        if distance <= skill.range:
                            # Check if skill can be used on this position (will check for obstacles, etc.)
                            if skill.can_use(cursor_manager.selected_unit, (y, x), game):
                                targets.append((y, x))
            
            # Convert targets to Position objects
            cursor_manager.highlighted_positions = [Position(y, x) for y, x in targets]
            
            if not cursor_manager.highlighted_positions:
                # No message when there are no valid targets
                
                # Reset selected skill
                cursor_manager.selected_unit.selected_skill = None
                # Return to select mode
                mode_manager.set_mode("select")

# Input manager component
class InputManager(UIComponent):
    """Component for handling input processing."""
    
    def __init__(self, renderer, game_ui, input_handler):
        super().__init__(renderer, game_ui)
        self.input_handler = input_handler
        self.setup_input_callbacks()
    
    def _setup_event_handlers(self):
        """Set up event handlers for input manager."""
        pass
        
    def setup_input_callbacks(self):
        """Set up callbacks for input handling."""
        cursor_manager = self.game_ui.cursor_manager
        mode_manager = self.game_ui.mode_manager
        event_manager = self.event_manager
        
        # Helper function to publish mode requests
        def publish_move_mode_request():
            event_manager.publish(EventType.MOVE_MODE_REQUESTED, EventData())
            
        def publish_attack_mode_request():
            event_manager.publish(EventType.ATTACK_MODE_REQUESTED, EventData())
            
        def publish_select_mode_request():
            event_manager.publish(EventType.SELECT_MODE_REQUESTED, EventData())
            
        def publish_cancel_request():
            event_manager.publish(EventType.CANCEL_REQUESTED, EventData())
        
        self.input_handler.register_action_callbacks({
            # Cardinal directions
            GameAction.MOVE_UP: lambda: cursor_manager.move_cursor(-1, 0),
            GameAction.MOVE_DOWN: lambda: cursor_manager.move_cursor(1, 0),
            GameAction.MOVE_LEFT: lambda: cursor_manager.move_cursor(0, -1),
            GameAction.MOVE_RIGHT: lambda: cursor_manager.move_cursor(0, 1),
            
            # Diagonal directions
            GameAction.MOVE_UP_LEFT: lambda: cursor_manager.move_cursor_diagonal("up-left"),
            GameAction.MOVE_UP_RIGHT: lambda: cursor_manager.move_cursor_diagonal("up-right"),
            GameAction.MOVE_DOWN_LEFT: lambda: cursor_manager.move_cursor_diagonal("down-left"),
            GameAction.MOVE_DOWN_RIGHT: lambda: cursor_manager.move_cursor_diagonal("down-right"),
            GameAction.SELECT: self.game_ui.handle_select,
            GameAction.CANCEL: publish_cancel_request,
            GameAction.MOVE_MODE: publish_move_mode_request,
            GameAction.ATTACK_MODE: publish_attack_mode_request,
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
        
        # Update input context based on current state
        self._update_input_context()
        
        # Default processing
        return self.input_handler.process_input(key)
        
    def _update_input_context(self):
        """Update the input handler context based on current game state."""
        # Default context includes all available contexts
        contexts = ["default", "movement", "action", "debug", "ui"]
        
        # In chat mode, only basic controls are active
        if self.game_ui.chat_component.chat_mode:
            self.input_handler.set_context("default")
            return
            
        # If help screen is showing, limit controls
        if self.game_ui.help_component.show_help:
            self.input_handler.set_context("help")
            return
            
        # If log history is showing, only allow log navigation
        if self.game_ui.message_log_component.show_log_history:
            self.input_handler.set_context("log")
            return
        
        # Create custom context when unit is affected by Jawline (immobilized)
        cursor_manager = self.game_ui.cursor_manager
        if (cursor_manager.selected_unit and 
            hasattr(cursor_manager.selected_unit, 'jawline_affected') and 
            cursor_manager.selected_unit.jawline_affected):
            
            # Create a custom context without move mode
            self.input_handler.set_context("jawline_immobilized")
            return
            
        # If action menu is visible, we want all normal keys to work (menu handles direct key presses)
        # So we just use the default context which includes everything
        if self.game_ui.action_menu_component.visible:
            self.input_handler.set_context("default")
            return
            
        # If in setup phase, enable the setup context
        if self.game_ui.game.setup_phase:
            # Create a special context that includes setup commands and movement, but not 'y' for diagonal
            self.input_handler.set_context("setup_phase")
            return
            
        # Default - all contexts active
        self.input_handler.set_context("default")