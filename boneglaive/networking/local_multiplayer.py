#!/usr/bin/env python3
"""
Implementation of local multiplayer mode (two players on the same computer).
"""

from typing import Any, Dict, Optional

from boneglaive.networking.network_interface import GameMode, MessageType, NetworkInterface
from boneglaive.utils.debug import logger

class LocalMultiplayerInterface(NetworkInterface):
    """Implementation for local multiplayer (same computer)."""
    
    def __init__(self):
        super().__init__(GameMode.LOCAL_MULTIPLAYER)
        self.current_player = 1  # Player 1 starts
    
    def initialize(self) -> bool:
        """Initialize local multiplayer mode."""
        self.connected = True
        self.opponent_id = "local-opponent"
        logger.info("Local multiplayer mode initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.connected = False
        logger.info("Local multiplayer mode cleaned up")
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        In local multiplayer, messages don't need to be sent over a network.
        They are processed immediately.
        """
        # Process the message immediately as if it came from the other player
        self._handle_message(message_type, data)
        return True
    
    def receive_messages(self) -> None:
        """
        Check for incoming messages.
        In local multiplayer, this doesn't do anything as messages
        are processed immediately in send_message().
        """
        pass
    
    def is_host(self) -> bool:
        """In local multiplayer, the game is always the host."""
        return True
    
    def get_player_number(self) -> int:
        """Get the current player's number."""
        return self.current_player
    
    def switch_player(self) -> None:
        """Switch the active player."""
        self.current_player = 3 - self.current_player  # Toggle between 1 and 2