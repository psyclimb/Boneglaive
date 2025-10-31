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
        self.game_instance = None  # Reference to current game for PRT lookups
    
    def set_game_reference(self, game):
        """Set reference to game instance for PRT damage calculations."""
        self.game_instance = game
        
    def _find_unit_by_name(self, unit_name: str):
        """Find a unit in the game by its display name."""
        if not self.game_instance:
            return None
        for unit in self.game_instance.units:
            if unit.get_display_name() == unit_name:
                return unit
        return None
        
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
                          target_player: Optional[int] = None,
                          **kwargs) -> None:
        """
        Add a combat-specific message with a consistent format.
        Automatically adjusts damage display based on target's PRT value.
        
        Args:
            attacker_name: Name of the attacking unit (should include Greek identifier)
            target_name: Name of the target unit (should include Greek identifier)
            damage: Amount of damage attempted (will be adjusted for PRT automatically)
            ability: Name of ability used (optional)
            attacker_player: Player number of attacker (optional)
            target_player: Player number of target (optional)
        """
        # Engine now passes actual damage dealt (after PRT reduction), so no adjustment needed
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
                # Get player name from game instance if available
                if self.game_instance:
                    player_name = self.game_instance.get_player_name(player_num)
                else:
                    player_name = f"Player {player_num}"
                text = f"[{player_name}] {msg['text']}"
                # Chat messages use player color for the entire message
                formatted.append((text, player_color))
                continue
            
            # Standard message handling with basic player coloring
            text = msg['text']

            # Check for critical event messages FIRST (highest priority)
            if " perishes!" in text or "perishes from falling debris!" in text:
                color = 20  # Dark red for death messages (correct color pair)
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
                 ("trapped in" in text and "due to Stasiality" not in text) or
                 "slogs through" in text):
                color = 7  # Yellow for debuffs/negative effects and displacements
            # Otherwise, use player color for messages with attacker/target info or ability messages
            elif ('attacker_name' in msg and msg['player'] is not None) or (msg['type'] == MessageType.ABILITY and msg['player'] is not None):
                player_num = msg['player']
                color = self.player_colors.get(player_num, 8)  # Use player color (green/blue) instead of gray
            else:
                # Default: keep the initial color (8 - gray) for messages that don't match any special criteria
                pass  # color remains as initialized (8)
                
            # Special handling for damage numbers - highlight them in magenta
            # Look for combat or ability messages containing damage info (typical format: "X hits Y for Z damage")
            if (msg['type'] == MessageType.COMBAT or msg['type'] == MessageType.ABILITY) and 'damage' in text:
                # Find the damage number in the text
                import re
                # Pattern to match "for X damage" or "suffers X [type] damage" where X is a number
                damage_match = re.search(r'for (\d+) damage', text)
                if not damage_match:
                    damage_match = re.search(r'suffers (\d+) (?:\w+ )?damage', text)
                if damage_match:
                    original_damage = int(damage_match.group(1))
                    adjusted_damage = original_damage
                    
                    # Check if this is a damage message to a unit with recent PRT absorption
                    # Try various patterns to find the target unit name
                    target_match = None
                    target_name = None
                    
                    # Pattern 1: "X hits Y for Z damage"
                    target_match = re.search(r'hits ([^f]+) for \d+ damage', text)
                    if target_match:
                        target_name = target_match.group(1).strip()
                    
                    # Pattern 2: "X attacks Y for Z damage with ABILITY"
                    if not target_match:
                        target_match = re.search(r'attacks ([^f]+) for \d+ damage', text)
                        if target_match:
                            target_name = target_match.group(1).strip()
                    
                    # Pattern 3: "X's jaws tighten on Y for Z damage"
                    if not target_match:
                        target_match = re.search(r"tighten on ([^f]+) for \d+ damage", text)
                        if target_match:
                            target_name = target_match.group(1).strip()
                    
                    # Pattern 4: "X deals Y for Z damage" (skill messages)
                    if not target_match:
                        target_match = re.search(r'deals ([^f]+) for \d+ damage', text)
                        if target_match:
                            target_name = target_match.group(1).strip()
                    
                    # Pattern 5: "Y takes Z damage" (damage notification messages)
                    if not target_match:
                        target_match = re.search(r'(.+) takes \d+ damage', text)
                        if target_match:
                            target_name = target_match.group(1).strip()
                    
                    # Pattern 6: "Y suffers Z damage" (abreaction and other effects)
                    if not target_match:
                        target_match = re.search(r'(.+) suffers (\d+) (?:\w+ )?damage', text)
                        if target_match:
                            target_name = target_match.group(1).strip()
                    
                    if target_name:
                        # Find the target unit and check for recent PRT absorption
                        target_unit = self._find_unit_by_name(target_name)
                        if target_unit and hasattr(target_unit, 'last_prt_absorbed') and target_unit.last_prt_absorbed > 0:
                            # Adjust damage by subtracting PRT absorbed
                            adjusted_damage = max(0, original_damage - target_unit.last_prt_absorbed)
                            from boneglaive.utils.debug import logger
                            logger.debug(f"PRT MESSAGE ADJUST: {target_name} damage {original_damage} -> {adjusted_damage} (PRT absorbed {target_unit.last_prt_absorbed})")
                    
                    # Replace with the adjusted damage number
                    if f"for {original_damage} damage" in text:
                        text = text.replace(f"for {original_damage} damage", f"for #DAMAGE_{adjusted_damage}# damage")
                    elif f"suffers {original_damage}" in text:
                        # Handle "suffers X radiation damage" pattern
                        import re
                        text = re.sub(f"suffers {original_damage} (\\w+ )?damage", f"suffers #DAMAGE_{adjusted_damage}# \\1damage", text)
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

# Create a global message log instance
message_log = MessageLog()