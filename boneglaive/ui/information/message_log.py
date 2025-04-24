#!/usr/bin/env python3
import curses
from typing import Optional, List, Tuple

from boneglaive.utils.constants import HEIGHT
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.event_system import (
    EventType, EventData, MessageDisplayEventData, UIRedrawEventData
)
from boneglaive.ui.components.base import UIComponent

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