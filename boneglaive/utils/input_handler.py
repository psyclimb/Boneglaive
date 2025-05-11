#!/usr/bin/env python3
"""
Abstract input handling to support multiple input sources.
Maps raw input to logical game actions.
"""

import curses
from enum import Enum, auto
from typing import Callable, Dict, Optional, Set, List

class GameAction(Enum):
    """Logical game actions that can be triggered by input."""
    # Cardinal movement
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    
    # Diagonal movement
    MOVE_UP_LEFT = auto()
    MOVE_UP_RIGHT = auto()
    MOVE_DOWN_LEFT = auto()
    MOVE_DOWN_RIGHT = auto()
    
    # Basic actions
    SELECT = auto()
    CANCEL = auto()
    
    # Unit action modes
    MOVE_MODE = auto()
    ATTACK_MODE = auto()
    SKILL_MODE = auto()  # New skill mode
    TELEPORT_MODE = auto()  # Teleportation mode
    
    # Game control
    END_TURN = auto()
    TEST_MODE = auto()
    
    # Debug actions
    DEBUG_INFO = auto()
    DEBUG_TOGGLE = auto()
    DEBUG_OVERLAY = auto()
    DEBUG_PERFORMANCE = auto()
    DEBUG_SAVE = auto()
    
    # UI actions
    HELP = auto()  # Help screen
    CHAT_MODE = auto()  # Chat mode
    CYCLE_UNITS = auto()  # Cycle through player's units (forward)
    CYCLE_UNITS_REVERSE = auto()  # Cycle through player's units (backward)
    LOG_HISTORY = auto()  # Full log history screen
    CONFIRM = auto()  # Confirm setup/action
    QUIT = auto()

class InputHandler:
    """
    Handler for input processing.
    Maps raw inputs to game actions and provides callback registration.
    """
    
    def __init__(self, backend_type: str = "curses"):
        self.backend_type = backend_type
        self.action_map: Dict[int, GameAction] = {}
        self.context_sensitive_maps: Dict[str, Dict[int, GameAction]] = {}
        self.action_callbacks: Dict[GameAction, Callable] = {}
        self.current_context = "default"
        self._setup_default_mappings()
    
    def _setup_default_mappings(self) -> None:
        """Set up default input mappings for the current backend."""
        if self.backend_type == "curses":
            # Default context mappings (arrow keys always work)
            self.action_map[curses.KEY_UP] = GameAction.MOVE_UP
            self.action_map[curses.KEY_DOWN] = GameAction.MOVE_DOWN
            self.action_map[curses.KEY_LEFT] = GameAction.MOVE_LEFT
            self.action_map[curses.KEY_RIGHT] = GameAction.MOVE_RIGHT
            
            # Create an empty movement context (removed Vim-style keys)
            movement_context = {}
            
            # Store context (keeping the structure in place for potential future additions)
            self.context_sensitive_maps["movement"] = movement_context
            
            # Action keys (always available)
            self.action_map[10] = GameAction.SELECT  # Enter key
            self.action_map[13] = GameAction.SELECT  # Also Enter key
            self.action_map[curses.KEY_ENTER] = GameAction.SELECT  # Also also Enter key
            self.action_map[ord(' ')] = GameAction.SELECT  # Space bar for selection
            self.action_map[27] = GameAction.CANCEL  # Escape key for cancel
            self.action_map[ord('c')] = GameAction.CANCEL  # Keep 'c' key for cancel
            self.action_map[ord('q')] = GameAction.QUIT
            
            # Action context (only available when not in movement mode)
            action_context = {}
            action_context[ord('m')] = GameAction.MOVE_MODE
            action_context[ord('a')] = GameAction.ATTACK_MODE
            action_context[ord('s')] = GameAction.SKILL_MODE  # Key for skills
            action_context[ord('p')] = GameAction.TELEPORT_MODE  # Key for teleportation (p for portal)
            action_context[ord('t')] = GameAction.END_TURN
            # Removed test mode key ('e')
            
            # Store action context
            self.context_sensitive_maps["action"] = action_context
            
            # Removed debug context and keys
            
            # UI context for help, chat, etc.
            ui_context = {}
            # Help key
            ui_context[ord('?')] = GameAction.HELP
            # Chat key
            ui_context[ord('r')] = GameAction.CHAT_MODE
            # Log history key (Shift+L)
            ui_context[ord('L')] = GameAction.LOG_HISTORY
            
            # Store UI context
            self.context_sensitive_maps["ui"] = ui_context
            
            # Setup mode context
            setup_context = {}
            setup_context[curses.KEY_BACKSPACE] = GameAction.TEST_MODE  # Reuse TEST_MODE for unit type toggle using backspace
            setup_context[127] = GameAction.TEST_MODE  # ASCII 127 is also backspace on some systems
            
            # Store setup context
            self.context_sensitive_maps["setup"] = setup_context
            
            # Cycle units keys (Tab and Shift+Tab)
            self.action_map[9] = GameAction.CYCLE_UNITS  # ASCII code 9 is Tab
            # Map both common representations of Shift+Tab
            self.action_map[curses.KEY_BTAB] = GameAction.CYCLE_UNITS_REVERSE  # Shift+Tab in most terminals
            self.action_map[353] = GameAction.CYCLE_UNITS_REVERSE  # Alternative code for Shift+Tab
    
    def register_action_callback(self, action: GameAction, callback: Callable) -> None:
        """Register a callback function for a game action."""
        self.action_callbacks[action] = callback
    
    def register_action_callbacks(self, callbacks: Dict[GameAction, Callable]) -> None:
        """Register multiple callback functions for game actions."""
        self.action_callbacks.update(callbacks)
    
    def set_context(self, context: str) -> None:
        """
        Set the current input context.
        
        Args:
            context: The name of the context to set as current
        """
        self.current_context = context
        
    def get_active_contexts(self) -> List[str]:
        """
        Get a list of active contexts based on game state.
        
        Returns:
            List of active context names
        """
        contexts = ["default"]
        
        # If we're in the default context, add all available contexts (removed debug)
        if self.current_context == "default":
            contexts.extend(["movement", "action", "ui"])
        # If we're in menu context, allow movement but not action keys
        elif self.current_context == "menu":
            contexts.extend(["movement", "ui"])
        # If we're in setup phase, include all contexts including movement
        # The 'y' conflict will be handled by checking for a confirmation dialog
        elif self.current_context == "setup_phase":
            contexts.extend(["movement", "ui", "setup"])
            # Keep movement consistent, we'll handle 'y' conflict at a higher level
        # If we're in help/log context, restrict to minimal controls
        elif self.current_context == "help" or self.current_context == "log":
            # No extra contexts
            pass
        # If we're in a specific context, only add that one
        elif self.current_context in self.context_sensitive_maps:
            contexts.append(self.current_context)
            
        return contexts
        
    def process_input(self, raw_input: int) -> bool:
        """
        Process raw input and trigger appropriate action callbacks.
        Returns True to continue processing, False to quit.
        """
        # Get action from default map
        action = self.action_map.get(raw_input)
        
        # If no action found in default map, check context-sensitive maps
        if not action:
            for context in self.get_active_contexts():
                if context in self.context_sensitive_maps:
                    context_map = self.context_sensitive_maps[context]
                    if raw_input in context_map:
                        action = context_map[raw_input]
                        break
        
        # If we have a mapping and a callback for this action, execute it
        if action and action in self.action_callbacks:
            # Special case for QUIT action
            if action == GameAction.QUIT:
                return False
            
            # Execute the callback
            self.action_callbacks[action]()
        
        return True
    
    def add_mapping(self, raw_input: int, action: GameAction, context: str = "default") -> None:
        """
        Add or modify an input mapping.
        
        Args:
            raw_input: The input key code
            action: The action to map to
            context: The context for this mapping (default is the base context)
        """
        if context == "default":
            self.action_map[raw_input] = action
        else:
            if context not in self.context_sensitive_maps:
                self.context_sensitive_maps[context] = {}
            self.context_sensitive_maps[context][raw_input] = action
    
    def remove_mapping(self, raw_input: int, context: str = "default") -> None:
        """
        Remove an input mapping.
        
        Args:
            raw_input: The input key code to remove
            context: The context to remove from (default is the base context)
        """
        if context == "default":
            if raw_input in self.action_map:
                del self.action_map[raw_input]
        else:
            if context in self.context_sensitive_maps:
                context_map = self.context_sensitive_maps[context]
                if raw_input in context_map:
                    del context_map[raw_input]