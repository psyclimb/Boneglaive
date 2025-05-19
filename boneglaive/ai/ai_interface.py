#!/usr/bin/env python3
"""
AI interface for Boneglaive.
Provides a clean interface between the game and AI controllers.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from boneglaive.utils.debug import logger
from boneglaive.networking.network_interface import NetworkInterface, MessageType, GameMode

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.ui.game_ui import GameUI

class AIInterface(NetworkInterface):
    """
    Interface for AI controllers.
    Used by the multiplayer manager to handle AI turns.
    """
    
    def __init__(self):
        """Initialize the AI interface."""
        super().__init__(GameMode.SINGLE_PLAYER)  # We use SINGLE_PLAYER mode for AI
        self.game = None
        self.ui = None
        self.initialized = False
        self.ai_controller = None
    
    def initialize(self, game: 'Game', ui: Optional['GameUI'] = None) -> bool:
        """
        Initialize the AI interface with a game instance.
        
        Args:
            game: The Game instance
            ui: Optional UI reference for animations
            
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.game = game
            self.ui = ui
            
            # Import and initialize the AI controller
            from boneglaive.ai.simple_ai import SimpleAI
            self.ai_controller = SimpleAI(game, ui)
            
            logger.info("AI interface initialized successfully")
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AI interface: {e}")
            self.initialized = False
            return False
    
    def process_turn(self) -> bool:
        """
        Process an AI turn.
        
        Returns:
            True if the turn was processed successfully, False otherwise
        """
        if not self.initialized or not self.ai_controller:
            logger.error("AI interface not properly initialized")
            return False
            
        try:
            result = self.ai_controller.process_turn()
            return result
        except Exception as e:
            logger.error(f"Error processing AI turn: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources used by the AI."""
        self.game = None
        self.ui = None
        self.ai_controller = None
        self.initialized = False
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        Send a message to the AI (not used - AI interface doesn't send messages).
        
        Args:
            message_type: Type of message to send
            data: Message data
            
        Returns:
            True if successful, False otherwise
        """
        # This is a dummy implementation for the abstract method
        logger.debug(f"AI interface received message of type {message_type} with data: {data}")
        return True
    
    def receive_messages(self) -> None:
        """Check for and process incoming messages (not used)."""
        # This is a dummy implementation for the abstract method
        pass
    
    def is_host(self) -> bool:
        """
        Check if this client is the host (always True for AI).
        
        Returns:
            True (AI is always considered the host)
        """
        return True
    
    def get_player_number(self) -> int:
        """
        Get the player number (always 2 for AI).
        
        Returns:
            2 (AI is always player 2)
        """
        return 2
    
    def is_multiplayer(self) -> bool:
        """
        Override to return True so the multiplayer manager handles AI mode.
        
        Returns:
            True
        """
        return True