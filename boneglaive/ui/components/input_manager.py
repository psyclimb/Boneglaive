#!/usr/bin/env python3

from boneglaive.utils.input_handler import GameAction
from boneglaive.utils.event_system import EventType, EventData
from boneglaive.ui.components.base import UIComponent

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