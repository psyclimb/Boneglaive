#!/usr/bin/env python3
"""
Basic generic strategy for all unit types.
This is a simple strategy that will be used as a fallback.
"""

import random
from typing import List, Optional, Dict, Any, Tuple

from boneglaive.game.engine import Game
from boneglaive.game.units import Unit
from boneglaive.ai.decision import Decision, ActionType
from boneglaive.ai.strategies.strategy import Strategy
from boneglaive.utils.debug import logger

class BasicStrategy(Strategy):
    """
    A basic strategy that makes simple decisions.
    This serves as a fallback when no unit-specific strategy is available.
    """
    
    def get_best_action(self, game: Game, unit: Unit) -> Optional[Decision]:
        """
        Get the best action for a unit based on a simple strategy.
        
        Args:
            game: The current Game instance
            unit: The Unit to get an action for
            
        Returns:
            A Decision object representing the best action, or None if no action is possible
        """
        logger.debug(f"BasicStrategy: Getting best action for {unit.get_display_name()}")
        
        # Check for attacks first - if we can attack, do it
        attack_decision = self._try_get_attack_decision(game, unit)
        if attack_decision:
            return attack_decision
            
        # If no attack is possible, try to use a skill
        skill_decision = self._try_get_skill_decision(game, unit)
        if skill_decision:
            return skill_decision
            
        # If no skill is possible, try to move
        move_decision = self._try_get_move_decision(game, unit)
        if move_decision:
            return move_decision
            
        # If nothing else is possible, just wait
        return Decision(
            action_type=ActionType.WAIT,
            unit_id=id(unit)  # Use object ID as a unique identifier
        )
        
    def _try_get_attack_decision(self, game: Game, unit: Unit) -> Optional[Decision]:
        """Try to get an attack decision for the unit."""
        # Get valid attack targets
        attack_targets = []
        
        # First, get the unit's position (current or planned move)
        from_y, from_x = unit.y, unit.x
        if unit.move_target:
            from_y, from_x = unit.move_target
            
        # Get attack range
        effective_stats = unit.get_effective_stats()
        attack_range = effective_stats['attack_range']
        
        # Check all positions within attack range
        for y in range(max(0, from_y - attack_range), min(game.map.height, from_y + attack_range + 1)):
            for x in range(max(0, from_x - attack_range), min(game.map.width, from_x + attack_range + 1)):
                # Skip current position
                if (y, x) == (from_y, from_x):
                    continue
                    
                # Calculate simplified distance
                distance = abs(y - from_y) + abs(x - from_x)
                
                if distance <= attack_range:
                    # Check if there's an enemy unit at this position
                    target_unit = game.get_unit_at(y, x)
                    if target_unit and target_unit.player != unit.player and target_unit.is_alive():
                        attack_targets.append((y, x))
        
        if attack_targets:
            # For now, just pick a random target
            # This will be improved with better targeting logic in the future
            target_pos = random.choice(attack_targets)
            
            return Decision(
                action_type=ActionType.ATTACK,
                unit_id=id(unit),
                target_pos=target_pos,
                score=0.8  # Attacks are generally good
            )
            
        return None
        
    def _try_get_skill_decision(self, game: Game, unit: Unit) -> Optional[Decision]:
        """Try to get a skill decision for the unit."""
        # Get available skills
        available_skills = unit.get_available_skills()
        
        if not available_skills:
            return None
            
        # For now, just pick a random skill and see if we can use it
        # This will be improved with better skill selection in the future
        random.shuffle(available_skills)  # Shuffle to avoid always using the same skill
        
        for skill in available_skills:
            # Try to find a valid target for the skill
            # Simple implementation that will be improved
            for y in range(game.map.height):
                for x in range(game.map.width):
                    if skill.can_use(unit, (y, x), game):
                        return Decision(
                            action_type=ActionType.SKILL,
                            unit_id=id(unit),
                            target_pos=(y, x),
                            skill_name=skill.name,
                            score=0.9  # Skills are valuable
                        )
        
        return None
        
    def _try_get_move_decision(self, game: Game, unit: Unit) -> Optional[Decision]:
        """Try to get a move decision for the unit."""
        # Get valid move positions
        valid_positions = []
        
        # Get move range
        effective_stats = unit.get_effective_stats()
        move_range = effective_stats['move_range']
        
        # Check all positions within move range
        for y in range(max(0, unit.y - move_range), min(game.map.height, unit.y + move_range + 1)):
            for x in range(max(0, unit.x - move_range), min(game.map.width, unit.x + move_range + 1)):
                # Skip current position
                if (y, x) == (unit.y, unit.x):
                    continue
                    
                # Simplified distance check
                distance = abs(y - unit.y) + abs(x - unit.x)
                
                if distance <= move_range:
                    # Check if position is valid and empty
                    if (game.is_valid_position(y, x) and 
                        game.map.is_passable(y, x) and 
                        game.get_unit_at(y, x) is None):
                        valid_positions.append((y, x))
        
        if valid_positions:
            # For now, just pick a random position
            # This will be improved with better positioning logic in the future
            target_pos = random.choice(valid_positions)
            
            return Decision(
                action_type=ActionType.MOVE,
                unit_id=id(unit),
                target_pos=target_pos,
                score=0.6  # Moving is less valuable than attacking or using skills
            )
            
        return None