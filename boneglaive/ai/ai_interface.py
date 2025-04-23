#!/usr/bin/env python3
"""
AI interface for the game.
Provides an interface between the game engine and AI players.
"""

from typing import Optional, Dict, Any, List, Tuple
from boneglaive.networking.network_interface import NetworkInterface
from boneglaive.utils.debug import logger

class AIInterface(NetworkInterface):
    """
    Interface that allows an AI to act as a network player.
    This adapts the AI system to the existing multiplayer framework.
    """
    
    def __init__(self, difficulty: str = "medium"):
        """
        Initialize the AI interface.
        
        Args:
            difficulty: The difficulty level ("easy", "medium", "hard")
        """
        self.difficulty = difficulty
        self.ai_player = None  # Will be initialized later
        self.ai_player_number = 2  # AI is always player 2 for now
        self.human_player_number = 1
        self.initialized = False
        self.game = None  # Will be set by the game engine
        
    def initialize(self) -> bool:
        """Initialize the AI interface."""
        # We'll initialize the AI player once we have a reference to the game
        self.initialized = True
        logger.info(f"AI interface initialized with difficulty: {self.difficulty}")
        return True
        
    def cleanup(self) -> None:
        """Clean up resources."""
        self.ai_player = None
        self.game = None
        self.initialized = False
        
    def is_multiplayer(self) -> bool:
        """
        Check if this interface supports multiplayer.
        This always returns True for AI to ensure proper turn handling.
        """
        return True
        
    def is_local_multiplayer(self) -> bool:
        """Check if this is local multiplayer."""
        # AI counts as local multiplayer for the turn system
        return True
        
    def is_network_multiplayer(self) -> bool:
        """Check if this is network multiplayer."""
        return False
        
    def get_player_number(self) -> int:
        """Get the current player number (1 or 2)."""
        return self.human_player_number
        
    def send_game_state(self, state: Dict[str, Any]) -> bool:
        """
        Send game state to the AI player.
        This is called by the game engine when the state changes.
        
        Args:
            state: The current game state
        
        Returns:
            True if successful, False otherwise
        """
        # We don't need to send state updates since the AI has direct access
        # to the game object. This method is kept for compatibility.
        return True
        
    def receive_game_state(self) -> Optional[Dict[str, Any]]:
        """
        Receive game state from the AI player.
        This is not needed since the AI has direct access to the game state.
        
        Returns:
            None as we don't use this mechanism for AI
        """
        return None
        
    def send_chat_message(self, message: str) -> bool:
        """
        Send a chat message to the AI player.
        AI doesn't currently respond to chat, but we could add this later.
        
        Args:
            message: The chat message
            
        Returns:
            True if successful, False otherwise
        """
        # AI doesn't currently do anything with chat messages
        return True
        
    def receive_chat_message(self) -> Optional[str]:
        """
        Receive a chat message from the AI player.
        AI doesn't currently send chat messages.
        
        Returns:
            None as AI doesn't send messages
        """
        return None
        
    def switch_player(self) -> None:
        """
        Switch the current player.
        This toggles between the human player and AI player.
        """
        if self.human_player_number == 1:
            self.human_player_number = 2
            self.ai_player_number = 1
        else:
            self.human_player_number = 1
            self.ai_player_number = 2
            
        logger.debug(f"AI interface switched player to: human={self.human_player_number}, AI={self.ai_player_number}")
        
        # If it's the AI's turn, trigger AI actions
        if self.game and self.game.current_player == self.ai_player_number:
            self._process_ai_turn()
            
    def _process_ai_turn(self) -> None:
        """Process the AI's turn when it's their turn to play."""
        if not self.ai_player:
            # Lazy initialization of AI player now that we have game reference
            from boneglaive.ai.ai_player import AIPlayer
            self.ai_player = AIPlayer(self.game, self.ai_player_number, self.difficulty)
            
        # Let the AI player take its turn
        if self.ai_player:
            logger.info(f"AI player {self.ai_player_number} is taking its turn")
            self.ai_player.take_turn()
            
    def set_game(self, game) -> None:
        """
        Set the game instance that this AI interface will interact with.
        
        Args:
            game: The Game instance
        """
        self.game = game
        logger.debug("Game instance set in AI interface")