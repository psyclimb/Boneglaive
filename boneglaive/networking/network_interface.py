#!/usr/bin/env python3
"""
Abstract network interface for multiplayer game modes.
Supports both local and remote multiplayer connections.
"""

import abc
import json
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from boneglaive.utils.debug import debug_config, logger

class GameMode(Enum):
    """Game play modes."""
    SINGLE_PLAYER = "single"  # Player vs AI
    LOCAL_MULTIPLAYER = "local"  # Two players on same computer
    NETWORK_MULTIPLAYER = "network"  # Players connected over network

class MessageType(Enum):
    """Types of network messages."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    GAME_STATE = "game_state"
    PLAYER_ACTION = "player_action"
    CHAT = "chat"
    ERROR = "error"
    PING = "ping"
    SETUP_ACTION = "setup_action"
    SETUP_PHASE_TRANSITION = "setup_phase_transition"
    SETUP_COMPLETE = "setup_complete"
    TURN_TRANSITION = "turn_transition"
    TURN_COMPLETE = "turn_complete"
    MESSAGE_LOG_BATCH = "message_log_batch"
    PARITY_CHECK = "parity_check"

class NetworkInterface(abc.ABC):
    """Abstract base class for network implementations."""
    
    def __init__(self, game_mode: GameMode = GameMode.SINGLE_PLAYER):
        self.game_mode = game_mode
        self.player_id = str(uuid.uuid4())[:8]
        self.opponent_id = None
        self.message_handlers = {}
        self.connected = False
    
    @abc.abstractmethod
    def initialize(self) -> bool:
        """Initialize the network connection."""
        pass
    
    @abc.abstractmethod
    def cleanup(self) -> None:
        """Clean up network resources."""
        pass
    
    @abc.abstractmethod
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """Send a message to the other player."""
        pass
    
    @abc.abstractmethod
    def receive_messages(self) -> None:
        """
        Check for and process incoming messages.
        This should be non-blocking.
        """
        pass
    
    @abc.abstractmethod
    def is_host(self) -> bool:
        """Check if this client is the host/server."""
        pass
    
    @abc.abstractmethod
    def get_player_number(self) -> int:
        """Get the player number (1 or 2)."""
        pass
    
    def register_message_handler(self, message_type: MessageType, 
                               handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    def _handle_message(self, message_type: MessageType, data: Dict[str, Any]) -> None:
        """Handle an incoming message by dispatching to the appropriate handler."""
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type](data)
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")
        else:
            logger.warning(f"No handler registered for message type: {message_type.value}")
    
    def is_local_multiplayer(self) -> bool:
        """Check if the game is in local multiplayer mode."""
        return self.game_mode == GameMode.LOCAL_MULTIPLAYER
    
    def is_network_multiplayer(self) -> bool:
        """Check if the game is in network multiplayer mode."""
        return self.game_mode == GameMode.NETWORK_MULTIPLAYER
    
    def is_multiplayer(self) -> bool:
        """Check if the game is in any multiplayer mode."""
        return self.is_local_multiplayer() or self.is_network_multiplayer()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection."""
        return {
            "game_mode": self.game_mode.value,
            "player_id": self.player_id,
            "opponent_id": self.opponent_id,
            "connected": self.connected,
            "is_host": self.is_host(),
            "player_number": self.get_player_number()
        }