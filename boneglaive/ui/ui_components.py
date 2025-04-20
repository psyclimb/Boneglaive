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
                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Cannot select {unit.type.name} - belongs to Player {unit.player}",
                        message_type=MessageType.WARNING
                    )
                )
                message_log.add_message(
                    f"Cannot select {unit.type.name} - belongs to Player {unit.player}", 
                    MessageType.WARNING
                )
            else:
                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="No unit at that position",
                        message_type=MessageType.WARNING
                    )
                )
                message_log.add_message("No unit at that position", MessageType.WARNING)
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
            self.selected_unit.attack_target = (self.cursor_pos.y, self.cursor_pos.x)
            
            # Get the target unit for the event data
            target = self.game_ui.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            
            # Publish attack planned event
            self.publish_event(
                EventType.ATTACK_PLANNED,
                AttackEventData(
                    attacker=self.selected_unit,
                    target=target
                )
            )
            
            self.game_ui.message = f"Attack set against {target.type.name}"
            # No message added to log for planned attacks
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
        
        # Deselect current unit if there is one
        if self.selected_unit:
            self._deselect_unit()
            
        # If no unit was selected, select the first or last one depending on direction
        if not self.selected_unit:
            # In reverse mode, start from the last unit
            next_unit = player_units[-1 if reverse else 0]
            # Move cursor to unit position (which will publish cursor moved event)
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
            
            # Move cursor to unit position
            previous_pos = self.cursor_pos
            
            # If the unit has a move target, cycle to the ghost instead
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
                
            # Clear message to avoid redundancy with unit info display
            self.game_ui.message = ""
                
            # Select the unit
            self.selected_unit = next_unit
            
            # Publish unit selected event
            self.publish_event(
                EventType.UNIT_SELECTED,
                UnitSelectedEventData(unit=next_unit, position=self.cursor_pos)
            )
            
        except ValueError:
            # If the selected unit isn't in the player's units (could happen in test mode)
            # In reverse mode, start from the last unit
            next_unit = player_units[-1 if reverse else 0]
            
            # Move cursor to unit position
            previous_pos = self.cursor_pos
            
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
            
        # If in attack or move mode, cancel the mode but keep unit selected
        if self.mode in ["attack", "move"] and cursor_manager.selected_unit:
            cursor_manager.highlighted_positions = []
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            self.game_ui.message = f"{self.mode.capitalize()} mode cancelled, unit still selected"
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
                    if cursor_manager.selected_unit.move_target:
                        # Use event system for message
                        self.publish_event(
                            EventType.MESSAGE_DISPLAY_REQUESTED,
                            MessageDisplayEventData(
                                message="No valid targets in range from move destination",
                                message_type=MessageType.WARNING
                            )
                        )
                    else:
                        # Use event system for message
                        self.publish_event(
                            EventType.MESSAGE_DISPLAY_REQUESTED,
                            MessageDisplayEventData(
                                message="No valid targets in range",
                                message_type=MessageType.WARNING
                            )
                        )
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
            
        # Try to place the unit (no displacement yet)
        success = self.game_ui.game.place_setup_unit(cursor_pos.y, cursor_pos.x)
        
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

# Action menu component
class ActionMenuComponent(UIComponent):
    """Component for displaying and handling the unit action menu."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.visible = False
        self.actions = []
        self.selected_index = 0
        
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
        """Populate available actions for the selected unit."""
        self.actions = []
        
        # Add standard actions
        self.actions.append({
            'key': 'm',
            'label': 'Move',
            'action': GameAction.MOVE_MODE,
            'enabled': True
        })
        
        self.actions.append({
            'key': 'a',
            'label': 'Attack',
            'action': GameAction.ATTACK_MODE,
            'enabled': True
        })
        
        # Add skill action (placeholder)
        self.actions.append({
            'key': 's',
            'label': 'Skills',
            'action': GameAction.SKILL_MODE,
            'enabled': False  # Disabled for now
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
        menu_y = 5              # Start a few lines down
        
        # Draw menu header
        header = f"=== {unit.type.name} Actions ==="
        self.renderer.draw_text(menu_y, menu_x, header, 1, curses.A_BOLD)
        
        # Draw menu items
        for i, action in enumerate(self.actions):
            y_pos = menu_y + i + 2  # Skip a line after header
            
            # Format action label with key in brackets
            label = f"[{action['key']}] {action['label']}"
            
            # Choose color based on whether action is enabled
            color = 1 if action['enabled'] else 8  # Normal color or gray
            
            # Add highlight if this is the selected action
            attr = curses.A_BOLD if i == self.selected_index else 0
            
            # If action is disabled, use dim attribute
            if not action['enabled']:
                attr |= curses.A_DIM
                
            self.renderer.draw_text(y_pos, menu_x, label, color, attr)
            
        # Draw footer with instructions
        footer_y = menu_y + len(self.actions) + 3
        self.renderer.draw_text(footer_y, menu_x, "ESC: Cancel", 1)
        
    def handle_input(self, key: int) -> bool:
        """Handle input specific to the action menu."""
        if not self.visible:
            return False
            
        # Exit if no actions
        if not self.actions:
            return False
            
        # Handle up/down navigation
        if key == curses.KEY_UP or key == ord('k'):
            self.selected_index = max(0, self.selected_index - 1)
            self.publish_event(
                EventType.UI_REDRAW_REQUESTED,
                UIRedrawEventData()
            )
            return True
            
        elif key == curses.KEY_DOWN or key == ord('j'):
            self.selected_index = min(len(self.actions) - 1, self.selected_index + 1)
            self.publish_event(
                EventType.UI_REDRAW_REQUESTED,
                UIRedrawEventData()
            )
            return True
            
        # Handle selection
        elif key == 10 or key == 13 or key == ord(' '):  # Enter or space
            selected_action = self.actions[self.selected_index]
            if selected_action['enabled']:
                # Trigger the action based on the action type
                if selected_action['action'] == GameAction.MOVE_MODE:
                    self.publish_event(EventType.MOVE_MODE_REQUESTED, EventData())
                elif selected_action['action'] == GameAction.ATTACK_MODE:
                    self.publish_event(EventType.ATTACK_MODE_REQUESTED, EventData())
                elif selected_action['action'] == GameAction.SKILL_MODE:
                    # For now, just show a message that skills are not implemented
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Skills not implemented yet",
                            message_type=MessageType.INFO
                        )
                    )
                return True
            
        # Handle direct key selection
        else:
            for action in self.actions:
                if key == ord(action['key']) and action['enabled']:
                    # Trigger action
                    if action['action'] == GameAction.MOVE_MODE:
                        self.publish_event(EventType.MOVE_MODE_REQUESTED, EventData())
                    elif action['action'] == GameAction.ATTACK_MODE:
                        self.publish_event(EventType.ATTACK_MODE_REQUESTED, EventData())
                    elif action['action'] == GameAction.SKILL_MODE:
                        # For now, just show a message that skills are not implemented
                        self.publish_event(
                            EventType.MESSAGE_DISPLAY_REQUESTED,
                            MessageDisplayEventData(
                                message="Skills not implemented yet",
                                message_type=MessageType.INFO
                            )
                        )
                    return True
                    
        return False

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
        
        # Default processing
        return self.input_handler.process_input(key)