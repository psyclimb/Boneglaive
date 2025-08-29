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
        self.filters: List[MessageType] = [MessageType.DEBUG]  # Always filter out DEBUG messages
        self.player_colors: Dict[int, int] = {1: 3, 2: 4}  # Player number to color mapping
        
        # Simple turn-based message batching for network sync
        self.turn_messages: List[Dict[str, Any]] = []  # All messages from current turn
        self.network_mode = False  # Whether we're in network multiplayer mode
        
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
        
        # In network mode, also collect for turn batch
        if self.network_mode:
            self.turn_messages.append(message.copy())
            logger.debug(f"MESSAGE_FLOW_DEBUG: Added message to both visible log ({len(self.messages)}) and turn batch ({len(self.turn_messages)}): {text[:50]}...")
        
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
                          target_player: Optional[int] = None,
                          **kwargs) -> None:
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
        if ability == "Viseroy Trap":
            # Check if this is the first application of trap damage
            trap_duration = kwargs.get('trap_duration', 0)
            if trap_duration == 0:  # First turn trapped
                message = f"{attacker_name}'s jaws tighten on {target_name} for {damage} damage"
            else:
                message = f"{attacker_name}'s jaws tighten on {target_name} for {damage} damage"
        elif ability:
            message = f"{attacker_name} hits {target_name} for {damage} damage with {ability}"
        else:
            message = f"{attacker_name} hits {target_name} for {damage} damage"
            
        # Check for invulnerable target by name (does not change damage sources)
        # Only HEINOUS VAPOR units can have invulnerability
        if "HEINOUS VAPOR" in target_name or "BROACHING GAS" in target_name or "SAFT-E-GAS" in target_name or \
           "COOLANT GAS" in target_name or "CUTTING GAS" in target_name:
            # We need to check if the unit is invulnerable
            # Since message_log doesn't have direct access to the unit objects,
            # we'll rely on the fact that invulnerable units always have damage=0
            if damage == 0:
                # Unit is invulnerable - show 0 damage
                pass  # Keep damage as 0
            else:
                # If damage > 0 but this is an invulnerable unit,
                # force the message to show 0 damage instead
                from boneglaive.utils.debug import logger
                
                # Update the message to show 0 damage
                if ability == "Viseroy Trap":
                    message = f"{attacker_name}'s jaws tighten on {target_name} for 0 damage"
                elif ability:
                    message = f"{attacker_name} hits {target_name} for 0 damage with {ability}"
                else:
                    message = f"{attacker_name} hits {target_name} for 0 damage"
                    
                # Log that we intercepted the damage
                logger.debug(f"Intercepted damage to {target_name}: changed {damage} to 0 (invulnerable)")
                
                # Override the damage value to 0
                damage = 0
            
        # Add the message
        self.add_message(
            text=message,
            msg_type=MessageType.COMBAT,
            player=attacker_player,
            target=target_player,
            damage=damage,  # This will now be 0 for invulnerable units
            ability=ability,
            # Store unit names explicitly to help with coloring
            attacker_name=attacker_name,
            target_name=target_name,
            **kwargs  # Pass along any additional kwargs
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
            
            # Standard message handling with basic player coloring
            text = msg['text']
            
            # Check for critical event messages
            if " perishes!" in text:
                color = 18  # Dark red for death messages
            elif " retches!" in text:
                color = 17  # Bright red for retching messages
            # Dominion upgrade messages should be very visible
            elif "DOMINION:" in text or "absorbs power from the fallen" in text:
                color = 19  # Special color for Dominion upgrades (bright magenta)
            # Check for debuff messages and forced displacement messages
            # Skip Stasiality immunity messages - they should use player color instead of yellow
            elif ("movement reduced" in text or "debuff" in text.lower() or 
                 ("penalty" in text.lower() and "due to Stasiality" not in text) or 
                 "displaced from" in text or "collides with" in text or
                 ("immobilized" in text and "immune to" not in text) or
                 ("trapped in" in text and "due to Stasiality" not in text)):
                color = 7  # Yellow for debuffs/negative effects and displacements
            # Otherwise, use player color for messages with attacker/target info or ability messages
            elif ('attacker_name' in msg and msg['player'] is not None) or (msg['type'] == MessageType.ABILITY and msg['player'] is not None):
                player_num = msg['player']
                color = self.player_colors.get(player_num, 8)  # Use player color (green/blue) instead of gray
                
            # Special handling for damage numbers - highlight them in magenta
            # Look for combat messages containing damage info (typical format: "X hits Y for Z damage")
            if msg['type'] == MessageType.COMBAT and 'damage' in msg:
                # Find the damage number in the text
                import re
                # Pattern to match "for X damage" where X is a number
                damage_match = re.search(r'for (\d+) damage', text)
                if damage_match:
                    damage_num = damage_match.group(1)
                    # Replace the damage number with a placeholder
                    text = text.replace(f"for {damage_num} damage", f"for #DAMAGE_{damage_num}# damage")
                    # We'll process this special placeholder in the UI component

            # Special handling for healing numbers - highlight them in white
            # Look for healing messages (typical format: "X heals Y for Z HP" or "healing for Z HP")
            import re
            heal_match = re.search(r'heals .+ for (\d+) HP', text)
            if heal_match:
                heal_num = heal_match.group(1)
                # Replace the healing number with a placeholder
                text = text.replace(f"for {heal_num} HP", f"for #HEAL_{heal_num}# HP")
            else:
                # Also check for "healing for Z HP" format used by skills like Autoclave
                heal_match = re.search(r'healing for (\d+) HP', text)
                if heal_match:
                    heal_num = heal_match.group(1)
                    # Replace the healing number with a placeholder
                    text = text.replace(f"for {heal_num} HP", f"for #HEAL_{heal_num}# HP")
                # We'll process this special placeholder in the UI component
            
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
    
    def enable_network_mode(self) -> None:
        """Enable network mode - start collecting turn messages."""
        self.network_mode = True
        self.turn_messages = []
        logger.debug("Enabled network message collection")
    
    def start_new_turn(self) -> None:
        """Start a new turn - clear previous turn's message collection for network sync."""
        if self.network_mode:
            # Only clear the turn_messages collection used for network batching
            # DO NOT clear self.messages as those should remain visible on the player's screen
            messages_before = len(self.messages)
            turn_messages_before = len(self.turn_messages)
            self.turn_messages = []
            logger.info(f"MESSAGE_FLOW_DEBUG: Started new turn - preserving {messages_before} visible messages, cleared {turn_messages_before} turn messages for next collection")
    
    def get_turn_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from the current turn."""
        return self.turn_messages.copy()
    
    def clear_turn_messages(self) -> None:
        """Clear current turn messages (after sending)."""
        if self.network_mode:
            self.turn_messages = []
    
    def add_network_messages(self, messages: List[Dict[str, Any]]) -> None:
        """Add messages received from network player (bypass turn collection)."""
        network_was_active = self.network_mode
        self.network_mode = False  # Temporarily disable to avoid re-batching
        
        for message in messages:
            
            # Reconstruct message type from stored value
            msg_type = message['type']
            if isinstance(msg_type, str):
                msg_type = MessageType(msg_type)
            elif hasattr(msg_type, 'value'):
                msg_type = MessageType(msg_type.value)
            
            # Add the message using normal add_message (will appear in local log)
            self.add_message(
                text=message['text'],
                msg_type=msg_type,
                player=message.get('player'),
                target=message.get('target'),
                **{k: v for k, v in message.items() if k not in ['text', 'type', 'player', 'target', 'timestamp']}
            )
        
        self.network_mode = network_was_active  # Restore network mode
        logger.info(f"MESSAGE_FLOW_DEBUG: Added {len(messages)} messages from network player. Total visible messages: {len(self.messages)}")
    
    def get_message_log_checksum(self) -> str:
        """
        Generate a checksum of the current message log for parity checking.
        Uses message text and type to create a reproducible hash.
        """
        import hashlib
        
        # Create a deterministic representation of all messages
        message_data = []
        for msg in self.messages:
            # Use only the essential fields for checksum (text, type, player)
            # Skip timestamp as it may vary slightly between players
            checksum_data = {
                'text': msg['text'],
                'type': msg['type'].value if hasattr(msg['type'], 'value') else str(msg['type']),
                'player': msg.get('player', None)
            }
            message_data.append(checksum_data)
        
        # Create JSON string and hash it
        import json
        json_str = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
        checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
        
        logger.debug(f"Generated message log checksum: {checksum} for {len(self.messages)} messages")
        return checksum
    
    def verify_parity(self, other_checksum: str, other_player: int) -> bool:
        """
        Verify message log parity with another player.
        
        Args:
            other_checksum: The other player's message log checksum
            other_player: The other player's number (for logging)
            
        Returns:
            True if message logs are in parity, False otherwise
        """
        my_checksum = self.get_message_log_checksum()
        parity_match = my_checksum == other_checksum
        
        if parity_match:
            logger.info(f"MESSAGE PARITY: ✓ Match with Player {other_player} (checksum: {my_checksum})")
        else:
            logger.warning(f"MESSAGE PARITY: ✗ Mismatch with Player {other_player}")
            logger.warning(f"My checksum: {my_checksum}")
            logger.warning(f"Their checksum: {other_checksum}")
            logger.warning(f"Total messages: {len(self.messages)}")
            
            # Add a warning message to the log
            self.add_message(
                f"Warning: Message log out of sync with Player {other_player}",
                MessageType.WARNING
            )
        
        return parity_match
    
    def get_full_message_log(self) -> List[Dict[str, Any]]:
        """
        Get the complete message log for syncing purposes.
        Returns serialized messages without timestamps.
        """
        serialized_messages = []
        for msg in self.messages:
            serialized_msg = {
                'text': msg['text'],
                'type': msg['type'].value if hasattr(msg['type'], 'value') else str(msg['type']),
                'player': msg.get('player'),
                'target': msg.get('target'),
            }
            # Add other fields except timestamp
            for key, value in msg.items():
                if key not in ['text', 'type', 'player', 'target', 'timestamp']:
                    serialized_msg[key] = value
            serialized_messages.append(serialized_msg)
        
        logger.info(f"Generated full message log for sync: {len(serialized_messages)} messages")
        return serialized_messages
    
    def replace_message_log(self, new_messages: List[Dict[str, Any]]) -> None:
        """
        Merge new messages with existing ones instead of replacing.
        Used for sync recovery when parity is lost.
        """
        logger.warning(f"SYNC RECOVERY: Merging {len(new_messages)} messages with existing {len(self.messages)} messages")
        
        # CRITICAL FIX: Don't clear existing messages - merge them instead
        old_count = len(self.messages)
        existing_texts = {msg['text'] for msg in self.messages}
        
        # Temporarily disable network mode to avoid re-batching during sync
        network_was_active = self.network_mode
        self.network_mode = False
        
        # Add only new messages that don't already exist
        added_count = 0
        for message in new_messages:
            # Skip messages that already exist (prevent duplicates)
            if message['text'] in existing_texts:
                continue
            # Reconstruct message type
            msg_type = message['type']
            if isinstance(msg_type, str):
                msg_type = MessageType(msg_type)
            elif hasattr(msg_type, 'value'):
                msg_type = MessageType(msg_type.value)
            
            # Add message directly to messages list (bypass turn collection)
            msg_entry = {
                'text': message['text'],
                'type': msg_type,
                'timestamp': time.time(),  # Use current time since we're syncing
                'player': message.get('player'),
                'target': message.get('target'),
            }
            
            # Add other fields
            for key, value in message.items():
                if key not in ['text', 'type', 'player', 'target']:
                    msg_entry[key] = value
                    
            self.messages.append(msg_entry)
            if len(self.messages) > self.MAX_MESSAGES:
                self.messages.pop(0)
            added_count += 1
        
        # Restore network mode
        self.network_mode = network_was_active
        
        new_count = len(self.messages)
        logger.warning(f"SYNC RECOVERY: Added {added_count} new messages. Message log updated from {old_count} to {new_count} total messages")
        
        
        # Add a system message about the sync recovery
        self.add_message(
            "Message log synchronized with other player",
            MessageType.SYSTEM
        )

# Create a global message log instance
message_log = MessageLog()