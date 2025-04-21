#!/usr/bin/env python3
"""
Message log system for tracking and displaying game events and player messages.
"""

import time
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any

from boneglaive.utils.debug import logger

class MessageType(Enum):
    """Types of messages that can appear in the log."""
    SYSTEM = "system"       # System messages (turn changes, game events)
    COMBAT = "combat"       # Combat-related messages (attacks, damage)
    MOVEMENT = "movement"   # Movement-related messages
    PLAYER = "player"       # Player-to-player chat messages
    ABILITY = "ability"     # Special ability usage
    ERROR = "error"         # Error messages
    WARNING = "warning"     # Warning messages
    DEBUG = "debug"         # Debug messages (only shown in debug mode)

class MessageLog:
    """
    Manages a log of game messages and events.
    Allows for filtering, formatting, and retrieval of messages.
    """
    
    MAX_MESSAGES = 500  # Maximum number of messages to store
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.filters: List[MessageType] = []  # Message types to filter out
        self.player_colors: Dict[int, int] = {1: 3, 2: 4}  # Player number to color mapping
        
    def add_message(self, text: str, msg_type: MessageType, 
                   player: Optional[int] = None, target: Optional[int] = None,
                   **kwargs) -> None:
        """
        Add a message to the log.
        
        Args:
            text: The message text
            msg_type: Type of message (from MessageType enum)
            player: Player number associated with the message (optional)
            target: Target player number for the message (optional)
            **kwargs: Additional data to store with the message
        """
        # Create message entry
        message = {
            'text': text,
            'type': msg_type,
            'timestamp': time.time(),
            'player': player,
            'target': target,
        }
        
        # Add any additional data
        message.update(kwargs)
        
        # Add to message list, keeping only the most recent MAX_MESSAGES
        self.messages.append(message)
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages.pop(0)
        
        # Log to debug system if relevant
        if msg_type == MessageType.ERROR:
            logger.error(text)
        elif msg_type == MessageType.WARNING:
            logger.warning(text)
        elif msg_type == MessageType.DEBUG:
            logger.debug(text)
        else:
            logger.info(text)
    
    def add_combat_message(self, attacker_name: str, target_name: str, 
                          damage: int, ability: Optional[str] = None,
                          attacker_player: Optional[int] = None,
                          target_player: Optional[int] = None) -> None:
        """
        Add a combat-specific message with a consistent format.
        
        Args:
            attacker_name: Name of the attacking unit (should include Greek identifier)
            target_name: Name of the target unit (should include Greek identifier)
            damage: Amount of damage dealt
            ability: Name of ability used (optional)
            attacker_player: Player number of attacker (optional)
            target_player: Player number of target (optional)
        """
        # Simple message format without player prefixes
        # The get_formatted_messages method will color the unit names appropriately
        if ability:
            message = f"{attacker_name} hits {target_name} for {damage} damage with {ability}!"
        else:
            message = f"{attacker_name} hits {target_name} for {damage} damage!"
            
        # Add the message
        self.add_message(
            text=message,
            msg_type=MessageType.COMBAT,
            player=attacker_player,
            target=target_player,
            damage=damage,
            ability=ability,
            # Store unit names explicitly to help with coloring
            attacker_name=attacker_name,
            target_name=target_name
        )
    
    def add_player_message(self, player: int, message: str) -> None:
        """
        Add a chat message from a player.
        
        Args:
            player: Player number (1 or 2)
            message: The chat message text
        """
        # Format message to show player identifier
        self.add_message(
            text=message,
            msg_type=MessageType.PLAYER,
            player=player
        )
    
    def add_system_message(self, message: str) -> None:
        """
        Add a system message.
        
        Args:
            message: The system message text
        """
        self.add_message(
            text=message,
            msg_type=MessageType.SYSTEM
        )
    
    def get_recent_messages(self, count: int = 10, 
                           filter_types: Optional[List[MessageType]] = None) -> List[Dict]:
        """
        Get the most recent messages, optionally filtered by type.
        
        Args:
            count: Number of messages to retrieve
            filter_types: List of message types to exclude (optional)
        
        Returns:
            List of message dictionaries
        """
        # If no filter provided, use the instance filter
        if filter_types is None:
            filter_types = self.filters
        
        # Filter messages
        if filter_types:
            filtered_messages = [
                msg for msg in self.messages 
                if msg['type'] not in filter_types
            ]
        else:
            filtered_messages = self.messages
        
        # Return the most recent messages up to the count
        return filtered_messages[-count:]
    
    def get_formatted_messages(self, count: int = 10, 
                              filter_types: Optional[List[MessageType]] = None) -> List[Tuple[str, int]]:
        """
        Get formatted messages with color information for display.
        
        Args:
            count: Number of messages to retrieve
            filter_types: List of message types to exclude (optional)
        
        Returns:
            List of (message_text, color_id) tuples without special colored unit formatting
        """
        messages = self.get_recent_messages(count, filter_types)
        formatted = []
        
        for msg in messages:
            # Default color is gray (8) for most messages
            color = 8  # Grey for standard text
            
            # Error and warning messages are exceptions and use special colors
            if msg['type'] == MessageType.ERROR:
                color = 6  # Red bg
            elif msg['type'] == MessageType.WARNING:
                color = 7  # Yellow
            
            # Format text with prefix based on type
            if msg['type'] == MessageType.PLAYER and msg['player'] is not None:
                # Format player chat messages with clear player indicator
                player_num = msg['player']
                player_color = self.player_colors.get(player_num, 1)
                text = f"[Player {player_num}] {msg['text']}"
                # Chat messages use player color for the entire message
                formatted.append((text, player_color))
                continue
            
            # Standard message handling - no special coloring for unit names
            text = msg['text']
            
            # Add the formatted message
            formatted.append((text, color))
        
        return formatted
    
    def set_filter(self, message_types: List[MessageType]) -> None:
        """
        Set message types to filter out.
        
        Args:
            message_types: List of MessageType to filter out
        """
        self.filters = message_types
    
    def clear_filter(self) -> None:
        """Clear all message filters."""
        self.filters = []
    
    def clear_log(self) -> None:
        """Clear all messages from the log."""
        self.messages = []

# Create a global message log instance
message_log = MessageLog()