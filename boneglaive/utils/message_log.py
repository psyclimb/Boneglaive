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
            List of (message_text, color_id) tuples with special colored unit formatting
        """
        messages = self.get_recent_messages(count, filter_types)
        formatted = []
        
        for msg in messages:
            # All regular message text is grey (color 8) except for unit names which will 
            # be colored based on their player ownership
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
            
            # Standard message handling
            text = msg['text']
            
            # For combat, movement, and ability messages, we need to apply colorization to unit names
            if msg['type'] in [MessageType.COMBAT, MessageType.MOVEMENT, MessageType.ABILITY]:
                # Handle full combat messages with attacker and target
                if 'attacker_name' in msg and 'target_name' in msg:
                    attacker_name = msg['attacker_name']
                    target_name = msg['target_name']
                    attacker_player = msg['player']
                    target_player = msg['target']
                    
                    # Replace unit names with colored indicators for the renderer
                    # We'll use special markers to indicate colored text segments
                    # These will be interpreted by the UI renderer
                    attacker_color = self.player_colors.get(attacker_player, 1)
                    target_color = self.player_colors.get(target_player, 1)
                    
                    # Format for colored text: __COLOR{color_id}:{text}__
                    # We need to handle cases where both attacker and target have the same name
                    # by being more careful with replacements
                    
                    if attacker_name == target_name:
                        # When names are identical, use a regex to identify distinct instances
                        import re
                        
                        # Find all instances of the name in the text
                        pattern = re.escape(attacker_name)
                        matches = list(re.finditer(pattern, text))
                        
                        # Replace instances backwards to avoid offset issues
                        # First instance is usually the attacker, second is the target
                        if len(matches) >= 2:
                            # Replace second occurrence (target) first
                            start2, end2 = matches[1].span()
                            colored_target = f"__COLOR{target_color}:{target_name}__"
                            text = text[:start2] + colored_target + text[end2:]
                            
                            # Replace first occurrence (attacker)
                            start1, end1 = matches[0].span()
                            colored_attacker = f"__COLOR{attacker_color}:{attacker_name}__"
                            text = text[:start1] + colored_attacker + text[end1:]
                    else:
                        # Different names - simpler replacement
                        colored_attacker = f"__COLOR{attacker_color}:{attacker_name}__"
                        colored_target = f"__COLOR{target_color}:{target_name}__"
                        
                        # Replace longer name first to avoid partial replacements
                        if len(attacker_name) >= len(target_name):
                            text = text.replace(attacker_name, colored_attacker)
                            text = text.replace(target_name, colored_target)
                        else:
                            text = text.replace(target_name, colored_target)
                            text = text.replace(attacker_name, colored_attacker)
                # Handle simple messages with just one unit name
                elif 'target_name' in msg:
                    target_name = msg['target_name']
                    target_player = msg['target']
                    
                    # Get the color for the target
                    target_color = self.player_colors.get(target_player, 1)
                    
                    # Format the colored version
                    colored_target = f"__COLOR{target_color}:{target_name}__"
                    
                    # Use regex for safer replacement
                    import re
                    pattern = re.escape(target_name)
                    text = re.sub(pattern, colored_target, text)
                # Handle messages with just an attacker name
                elif 'attacker_name' in msg:
                    attacker_name = msg['attacker_name']
                    attacker_player = msg['player']
                    
                    # Get the color for the attacker
                    attacker_color = self.player_colors.get(attacker_player, 1)
                    
                    # Format the colored version
                    colored_attacker = f"__COLOR{attacker_color}:{attacker_name}__"
                    
                    # Use regex for safer replacement
                    import re
                    pattern = re.escape(attacker_name)
                    text = re.sub(pattern, colored_attacker, text)
            
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