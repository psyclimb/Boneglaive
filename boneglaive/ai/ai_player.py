#!/usr/bin/env python3
"""
AI player for the game.
Makes decisions for a computer-controlled player.
"""

import random
import time
from typing import List, Dict, Any, Tuple, Optional

from boneglaive.game.engine import Game
from boneglaive.utils.debug import logger
from boneglaive.game.units import Unit
from boneglaive.utils.message_log import message_log, MessageType

class AIPlayer:
    """
    AI player that makes decisions for a computer-controlled opponent.
    Handles unit movement, attacks, and skill usage based on the selected
    difficulty level and strategy.
    """
    
    def __init__(self, game: Game, player_number: int, difficulty: str = "medium"):
        """
        Initialize the AI player.
        
        Args:
            game: The Game instance
            player_number: The player number (1 or 2) that this AI controls
            difficulty: The difficulty level ("easy", "medium", "hard")
        """
        self.game = game
        self.player_number = player_number
        self.difficulty = difficulty
        
        # Strategy objects will be initialized when needed
        self.strategies = {}
        
        logger.info(f"AI player initialized with difficulty {difficulty} for player {player_number}")
        
    def take_turn(self) -> None:
        """
        Take a turn as the AI player.
        This is the main method that orchestrates AI decision-making.
        """
        logger.info(f"AI player {self.player_number} is taking its turn")
        
        # Announce the AI turn
        message_log.add_message(
            f"AI (Player {self.player_number}) is thinking...",
            MessageType.INFO
        )
        
        # Get all units controlled by this player
        units = self._get_my_units()
        
        if not units:
            logger.warning(f"AI player {self.player_number} has no units to control")
            self._end_turn()
            return
            
        # Process each unit's actions
        for unit in units:
            # Add a short delay to make AI actions visible
            time.sleep(0.5)
            
            # Skip units that can't act
            if not self._can_unit_act(unit):
                continue
                
            # Choose and execute an action for this unit
            self._process_unit_action(unit)
            
            # Update the game display after each unit's action
            if hasattr(self.game, 'ui') and self.game.ui:
                self.game.ui.draw_board()
                time.sleep(0.3)  # Brief pause between units
        
        # End the turn
        self._end_turn()
        
    def _get_my_units(self) -> List[Unit]:
        """Get all units controlled by this AI player."""
        return [unit for unit in self.game.units if unit.player == self.player_number and unit.is_alive()]
        
    def _can_unit_act(self, unit: Unit) -> bool:
        """Check if a unit can still take actions this turn."""
        # For now, all living units can act
        return unit.is_alive()
        
    def _process_unit_action(self, unit: Unit) -> None:
        """
        Process actions for a single unit.
        This is a simple placeholder implementation that will be expanded.
        """
        logger.debug(f"AI processing action for {unit.get_display_name()}")
        
        # Temporary basic logic to demonstrate functionality
        # This will be replaced with more sophisticated strategy-based decisions
        
        # Random choice between move, attack, and skill
        action_choice = random.choice(["move", "attack", "skill"])
        
        if action_choice == "move":
            self._try_move_unit(unit)
        elif action_choice == "attack":
            if not self._try_attack_with_unit(unit):
                # If attack fails, try to move instead
                self._try_move_unit(unit)
        elif action_choice == "skill":
            if not self._try_use_skill(unit):
                # If skill fails, try to attack
                if not self._try_attack_with_unit(unit):
                    # If attack fails, try to move
                    self._try_move_unit(unit)
                    
    def _try_move_unit(self, unit: Unit) -> bool:
        """
        Try to move a unit to a valid position.
        
        Args:
            unit: The unit to move
            
        Returns:
            True if the move was successful, False otherwise
        """
        logger.debug(f"AI trying to move {unit.get_display_name()}")
        
        # Get all possible move positions
        move_positions = self._get_valid_move_positions(unit)
        
        if not move_positions:
            logger.debug(f"No valid move positions for {unit.get_display_name()}")
            return False
            
        # For now, just pick a random valid move position
        target_pos = random.choice(move_positions)
        
        # Queue the move for execution at turn end
        unit.move_target = target_pos
        logger.debug(f"AI moved {unit.get_display_name()} to {target_pos}")
        
        # Announce the move
        message_log.add_message(
            f"AI moves {unit.get_display_name()} to position ({target_pos[0]}, {target_pos[1]})",
            MessageType.INFO
        )
        
        return True
        
    def _try_attack_with_unit(self, unit: Unit) -> bool:
        """
        Try to attack with a unit if there are valid targets in range.
        
        Args:
            unit: The unit to attack with
            
        Returns:
            True if the attack was queued, False otherwise
        """
        logger.debug(f"AI trying to attack with {unit.get_display_name()}")
        
        # Get all possible attack targets
        attack_targets = self._get_valid_attack_targets(unit)
        
        if not attack_targets:
            logger.debug(f"No valid attack targets for {unit.get_display_name()}")
            return False
            
        # For now, just pick a random valid target
        target_pos = random.choice(attack_targets)
        
        # Queue the attack for execution at turn end
        unit.attack_target = target_pos
        target_unit = self.game.get_unit_at(target_pos[0], target_pos[1])
        logger.debug(f"AI attacked {target_unit.get_display_name()} with {unit.get_display_name()}")
        
        # Announce the attack
        message_log.add_message(
            f"AI attacks {target_unit.get_display_name()} with {unit.get_display_name()}",
            MessageType.INFO
        )
        
        return True
        
    def _try_use_skill(self, unit: Unit) -> bool:
        """
        Try to use a skill with the unit if available.
        This is a placeholder implementation that will be expanded.
        
        Args:
            unit: The unit to use a skill with
            
        Returns:
            True if a skill was used, False otherwise
        """
        logger.debug(f"AI trying to use skill with {unit.get_display_name()}")
        
        # Get available skills
        available_skills = unit.get_available_skills()
        
        if not available_skills:
            logger.debug(f"No available skills for {unit.get_display_name()}")
            return False
            
        # For now, just pick a random skill
        skill = random.choice(available_skills)
        
        # Try to find a valid target for the skill
        # This is a very basic implementation that will be expanded
        for y in range(self.game.map.height):
            for x in range(self.game.map.width):
                if skill.can_use(unit, (y, x), self.game):
                    # Use the skill
                    result = skill.use(unit, (y, x), self.game)
                    
                    if result:
                        logger.debug(f"AI used skill {skill.name} with {unit.get_display_name()} at ({y}, {x})")
                        
                        # Announce the skill usage
                        message_log.add_message(
                            f"AI uses {skill.name} with {unit.get_display_name()} at position ({y}, {x})",
                            MessageType.INFO
                        )
                        
                        return True
        
        logger.debug(f"No valid skill targets for {unit.get_display_name()}")
        return False
        
    def _get_valid_move_positions(self, unit: Unit) -> List[Tuple[int, int]]:
        """
        Get all valid positions the unit can move to.
        
        Args:
            unit: The unit to get valid moves for
            
        Returns:
            List of (y, x) tuples representing valid move positions
        """
        valid_positions = []
        effective_stats = unit.get_effective_stats()
        move_range = effective_stats['move_range']
        
        # Check all positions within move range
        for y in range(max(0, unit.y - move_range), min(self.game.map.height, unit.y + move_range + 1)):
            for x in range(max(0, unit.x - move_range), min(self.game.map.width, unit.x + move_range + 1)):
                # Skip current position
                if (y, x) == (unit.y, unit.x):
                    continue
                    
                # Calculate Manhattan distance (simplified for now)
                distance = abs(y - unit.y) + abs(x - unit.x)
                
                if distance <= move_range:
                    # Check if position is valid and empty
                    if (self.game.is_valid_position(y, x) and 
                        self.game.map.is_passable(y, x) and 
                        self.game.get_unit_at(y, x) is None):
                        valid_positions.append((y, x))
        
        return valid_positions
        
    def _get_valid_attack_targets(self, unit: Unit) -> List[Tuple[int, int]]:
        """
        Get all valid positions the unit can attack.
        
        Args:
            unit: The unit to get valid attack targets for
            
        Returns:
            List of (y, x) tuples representing valid attack targets
        """
        valid_targets = []
        effective_stats = unit.get_effective_stats()
        attack_range = effective_stats['attack_range']
        
        # First, get the unit's position (current or planned move)
        from_y, from_x = unit.y, unit.x
        if unit.move_target:
            from_y, from_x = unit.move_target
            
        # Check all positions within attack range
        for y in range(max(0, from_y - attack_range), min(self.game.map.height, from_y + attack_range + 1)):
            for x in range(max(0, from_x - attack_range), min(self.game.map.width, from_x + attack_range + 1)):
                # Skip current position
                if (y, x) == (from_y, from_x):
                    continue
                    
                # Calculate Manhattan distance (simplified for now)
                distance = abs(y - from_y) + abs(x - from_x)
                
                if distance <= attack_range:
                    # Check if there's an enemy unit at this position
                    target_unit = self.game.get_unit_at(y, x)
                    if target_unit and target_unit.player != unit.player and target_unit.is_alive():
                        valid_targets.append((y, x))
        
        return valid_targets
        
    def _end_turn(self) -> None:
        """End the AI player's turn."""
        logger.info(f"AI player {self.player_number} is ending its turn")
        
        # Announce end of AI turn
        message_log.add_message(
            f"AI (Player {self.player_number}) ends their turn",
            MessageType.INFO
        )
        
        # Execute the turn to process all queued actions
        self.game.execute_turn()
        
        # The game does the player switching in execute_turn, 
        # so we don't need to do anything else here
        # Just trigger the multiplayer manager to update turns
        if hasattr(self.game, 'ui') and hasattr(self.game.ui, 'multiplayer'):
            self.game.ui.multiplayer.end_turn()
        
        # If no game UI, try a direct approach to toggle the AI interface
        elif hasattr(self.game, 'multiplayer'):
            self.game.multiplayer.end_turn()