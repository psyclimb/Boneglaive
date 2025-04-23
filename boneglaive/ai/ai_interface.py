#!/usr/bin/env python3
"""
AI interface for the game.
Provides an interface between the game engine and AI players.
"""

from typing import Optional, Dict, Any, List, Tuple
from boneglaive.networking.network_interface import NetworkInterface, MessageType, GameMode
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
        super().__init__(GameMode.LOCAL_MULTIPLAYER)  # Treat AI as local multiplayer for simplicity
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
        
    def is_host(self) -> bool:
        """Check if this client is the host/server.
        In AI mode, the human player is always the host."""
        return True
        
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        Send a message to the AI player.
        Since the AI is local, we just process the message directly.
        
        Args:
            message_type: The type of message to send
            data: The message data
            
        Returns:
            True if successful, False otherwise
        """
        # Process the message based on type
        if message_type == MessageType.GAME_STATE:
            # Game state updates are handled directly through the game reference
            return True
        elif message_type == MessageType.CHAT:
            # AI doesn't respond to chat messages
            return True
        else:
            # Log unhandled message types
            logger.debug(f"Unhandled message type in AIInterface: {message_type}")
            return False
            
    def receive_messages(self) -> None:
        """
        Check for and process incoming messages from the AI.
        This is a no-op since the AI doesn't send messages; it acts directly on the game state.
        """
        # AI doesn't send messages through this system
        pass
        
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
        # Log before switching
        logger.debug(f"AI interface switching player from: human={self.human_player_number}, AI={self.ai_player_number}")
        
        # Toggle player numbers
        if self.human_player_number == 1:
            self.human_player_number = 2
            self.ai_player_number = 1
        else:
            self.human_player_number = 1
            self.ai_player_number = 2
            
        logger.debug(f"AI interface switched player to: human={self.human_player_number}, AI={self.ai_player_number}")
        
        # Check whose turn it is based on the current game state
        if self.game:
            current_player = self.game.current_player
            logger.info(f"Current game player: {current_player}, AI player: {self.ai_player_number}")
            
            # If it's the AI's turn, trigger AI actions
            if current_player == self.ai_player_number:
                logger.info(f"Triggering AI turn for player {self.ai_player_number}")
                # Add a small delay to make the AI's turn more visible
                import time
                time.sleep(0.5)
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