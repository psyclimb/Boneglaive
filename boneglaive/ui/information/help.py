#!/usr/bin/env python3
import curses

from boneglaive.utils.constants import HEIGHT
from boneglaive.utils.message_log import message_log
from boneglaive.utils.debug import logger
from boneglaive.utils.event_system import (
    EventType, EventData, UIRedrawEventData
)
from boneglaive.ui.components.base import UIComponent

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