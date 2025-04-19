#!/usr/bin/env python3
"""
Abstract input handling to support multiple input sources.
Maps raw input to logical game actions.
"""

import curses
from enum import Enum, auto
from typing import Callable, Dict, Optional, Set

class GameAction(Enum):
    """Logical game actions that can be triggered by input."""
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SELECT = auto()
    CANCEL = auto()
    MOVE_MODE = auto()
    ATTACK_MODE = auto()
    END_TURN = auto()
    TEST_MODE = auto()
    DEBUG_INFO = auto()
    DEBUG_TOGGLE = auto()
    DEBUG_OVERLAY = auto()
    DEBUG_PERFORMANCE = auto()
    DEBUG_SAVE = auto()
    HELP = auto()  # New action for help screen
    QUIT = auto()

class InputHandler:
    """
    Handler for input processing.
    Maps raw inputs to game actions and provides callback registration.
    """
    
    def __init__(self, backend_type: str = "curses"):
        self.backend_type = backend_type
        self.action_map: Dict[int, GameAction] = {}
        self.action_callbacks: Dict[GameAction, Callable] = {}
        self._setup_default_mappings()
    
    def _setup_default_mappings(self) -> None:
        """Set up default input mappings for the current backend."""
        if self.backend_type == "curses":
            # Arrow keys
            self.action_map[curses.KEY_UP] = GameAction.MOVE_UP
            self.action_map[curses.KEY_DOWN] = GameAction.MOVE_DOWN
            self.action_map[curses.KEY_LEFT] = GameAction.MOVE_LEFT
            self.action_map[curses.KEY_RIGHT] = GameAction.MOVE_RIGHT
            
            # Action keys
            self.action_map[10] = GameAction.SELECT  # Enter key
            self.action_map[13] = GameAction.SELECT  # Also Enter key
            self.action_map[curses.KEY_ENTER] = GameAction.SELECT  # Also also Enter key
            self.action_map[ord('c')] = GameAction.CANCEL
            self.action_map[ord('m')] = GameAction.MOVE_MODE
            self.action_map[ord('a')] = GameAction.ATTACK_MODE
            self.action_map[ord('e')] = GameAction.END_TURN
            self.action_map[ord('t')] = GameAction.TEST_MODE
            self.action_map[ord('q')] = GameAction.QUIT
            
            # Debug keys
            self.action_map[ord('d')] = GameAction.DEBUG_INFO
            self.action_map[ord('D')] = GameAction.DEBUG_TOGGLE
            self.action_map[ord('O')] = GameAction.DEBUG_OVERLAY
            self.action_map[ord('P')] = GameAction.DEBUG_PERFORMANCE
            self.action_map[ord('S')] = GameAction.DEBUG_SAVE
            
            # Help key
            self.action_map[ord('?')] = GameAction.HELP
    
    def register_action_callback(self, action: GameAction, callback: Callable) -> None:
        """Register a callback function for a game action."""
        self.action_callbacks[action] = callback
    
    def register_action_callbacks(self, callbacks: Dict[GameAction, Callable]) -> None:
        """Register multiple callback functions for game actions."""
        self.action_callbacks.update(callbacks)
    
    def process_input(self, raw_input: int) -> bool:
        """
        Process raw input and trigger appropriate action callbacks.
        Returns True to continue processing, False to quit.
        """
        # Map input to action
        action = self.action_map.get(raw_input)
        
        # If we have a mapping and a callback for this action, execute it
        if action and action in self.action_callbacks:
            # Special case for QUIT action
            if action == GameAction.QUIT:
                return False
            
            # Execute the callback
            self.action_callbacks[action]()
        
        return True
    
    def add_mapping(self, raw_input: int, action: GameAction) -> None:
        """Add or modify an input mapping."""
        self.action_map[raw_input] = action
    
    def remove_mapping(self, raw_input: int) -> None:
        """Remove an input mapping."""
        if raw_input in self.action_map:
            del self.action_map[raw_input]