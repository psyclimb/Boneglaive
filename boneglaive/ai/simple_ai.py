#!/usr/bin/env python3
"""
Simple AI controller for Boneglaive.
This module contains a basic AI implementation focusing on the Glaiveman unit.
"""

import random
from enum import Enum
from typing import List, Tuple, Dict, Optional, TYPE_CHECKING
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.config import ConfigManager

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.ui.game_ui import GameUI

class AIDifficulty(Enum):
    """Difficulty levels for the AI."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class SimpleAI:
    """
    Simple AI controller for Boneglaive.
    Handles decision making for AI-controlled units.
    """
    
    def __init__(self, game: 'Game', ui: Optional['GameUI'] = None):
        """
        Initialize the AI controller.
        
        Args:
            game: Reference to the Game instance
            ui: Optional reference to the GameUI instance
        """
        self.game = game
        self.ui = ui
        self.player_number = 2  # AI is always player 2
        
        # Get difficulty from config
        self.config = ConfigManager()
        self.difficulty = self._get_difficulty_level()
        logger.info(f"AI initialized with difficulty: {self.difficulty.value}")
        
        # Coordination tracking
        self.target_assignments = {}  # Maps unit_id -> target_id
        self.planned_positions = {}   # Maps (y, x) coordinates -> unit_id
        
        # Messaging
        self.enable_thinking_messages = True
    
    def _get_difficulty_level(self) -> AIDifficulty:
        """Get the difficulty level from config."""
        difficulty_str = self.config.get('ai_difficulty', 'medium')
        try:
            return AIDifficulty(difficulty_str.lower())
        except ValueError:
            logger.warning(f"Invalid AI difficulty '{difficulty_str}', using MEDIUM")
            return AIDifficulty.MEDIUM
    
    def process_turn(self) -> bool:
        """
        Process a full AI turn.
        
        Returns:
            True if the turn was processed successfully, False otherwise
        """
        logger.info(f"AI processing turn with {self.difficulty.value} difficulty")
        
        # "AI is thinking..." message moved to multiplayer_manager.py
        # to avoid duplication
            
        # Get all units belonging to the AI player
        ai_units = [unit for unit in self.game.units 
                   if unit.player == self.player_number and unit.is_alive()]
        
        # Log all AI units for debugging
        logger.info(f"Found {len(ai_units)} AI units:")
        for i, unit in enumerate(ai_units):
            logger.info(f"AI unit {i+1}: {unit.get_display_name()} at ({unit.y}, {unit.x})")
        
        if not ai_units:
            logger.warning("AI has no units to control")
            return False
        
        # Reset coordination tracking for the new turn
        self.target_assignments = {}
        self.planned_positions = {}
        
        # Coordinate units based on difficulty
        if self.difficulty == AIDifficulty.MEDIUM or self.difficulty == AIDifficulty.HARD:
            # On HARD difficulty, perform group coordination
            if self.difficulty == AIDifficulty.HARD:
                self._coordinate_group_tactics(ai_units)
            else:
                # On MEDIUM, just ensure each unit has a target
                self._ensure_all_units_have_targets(ai_units)
        
        # On HARD difficulty, sort units to process the most tactical ones first
        if self.difficulty == AIDifficulty.HARD:
            # Sort units by their tactical advantage (units with attack opportunities go first)
            ai_units = self._sort_units_by_tactical_priority(ai_units)
            
        # Process units one at a time
        for unit in ai_units:
            logger.info(f"AI processing unit: {unit.get_display_name()}")
            self._process_unit(unit)
            
            # Update the UI after each unit action
            if self.ui:
                self.ui.draw_board()
                
        # End the turn
        logger.info("AI ending turn")
        return True
        
    def _coordinate_group_tactics(self, ai_units: List['Unit']) -> None:
        """
        Coordinate AI units for group tactics (HARD difficulty).
        Assigns targets and positions strategically for group advantage.
        
        Args:
            ai_units: List of all AI units
        """
        # Get all player units for targeting
        player_units = [unit for unit in self.game.units 
                      if unit.player == 1 and unit.is_alive()]
                      
        if not player_units:
            return
            
        logger.info("Coordinating AI group tactics")
        
        # 1. GROUP SURROUNDING: Try to surround isolated player units
        isolated_targets = self._find_isolated_player_units(player_units)
        
        if isolated_targets and len(ai_units) >= 2:
            # Pick the most isolated player unit to surround
            target_unit = isolated_targets[0]
            logger.info(f"Group tactic: Surrounding isolated unit {target_unit.get_display_name()}")
            
            # Find AI units that are close enough to participate
            nearby_ai_units = []
            for unit in ai_units:
                distance = self.game.chess_distance(unit.y, unit.x, target_unit.y, target_unit.x)
                # Consider units that are close or have good move range
                move_range = unit.get_effective_stats()['move_range']
                if distance <= move_range + 3:  # Within reach in 1-2 turns
                    nearby_ai_units.append(unit)
            
            # Try to assign positions around the target
            if len(nearby_ai_units) >= 2:
                # Get surrounding positions
                surround_positions = self._get_surrounding_positions(target_unit)
                
                # Assign AI units to surrounding positions
                for i, pos in enumerate(surround_positions):
                    if i < len(nearby_ai_units):
                        unit = nearby_ai_units[i]
                        # Set this as a planned position
                        self.planned_positions[pos] = unit.id
                        # Set the target assignment
                        self.target_assignments[unit.id] = target_unit.id
                        
                        logger.info(f"Assigned {unit.get_display_name()} to surround position {pos} targeting {target_unit.get_display_name()}")
        
        # 2. Assign remaining units to appropriate targets
        assigned_units = set(unit.id for unit in ai_units if unit.id in self.target_assignments)
        unassigned_units = [unit for unit in ai_units if unit.id not in assigned_units]
        
        if unassigned_units:
            self._assign_targets_to_units(unassigned_units, player_units)
    
    def _find_isolated_player_units(self, player_units: List['Unit']) -> List['Unit']:
        """
        Find player units that are isolated from other player units.
        These are good targets for surrounding.
        
        Args:
            player_units: List of player units to check
            
        Returns:
            List of isolated player units, sorted by isolation factor
        """
        if len(player_units) <= 1:
            return player_units
            
        # Calculate isolation score for each player unit
        isolation_scores = []
        
        for unit in player_units:
            # Calculate average distance to other player units
            other_units = [u for u in player_units if u.id != unit.id]
            total_distance = sum(self.game.chess_distance(unit.y, unit.x, u.y, u.x) for u in other_units)
            avg_distance = total_distance / len(other_units) if other_units else 0
            
            # Higher score means more isolated
            isolation_scores.append((unit, avg_distance))
        
        # Sort by isolation score (highest first)
        isolation_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return units that are relatively isolated (more than 3 spaces from others on average)
        return [unit for unit, score in isolation_scores if score > 3]
    
    def _get_surrounding_positions(self, unit: 'Unit') -> List[Tuple[int, int]]:
        """
        Get valid positions surrounding a unit for coordinated attacks.
        
        Args:
            unit: The unit to surround
            
        Returns:
            List of valid (y, x) positions around the unit
        """
        from boneglaive.utils.coordinates import get_adjacent_positions
        
        # Get all adjacent positions
        adjacent_positions = get_adjacent_positions(unit.y, unit.x)
        
        # Filter for valid positions
        valid_positions = []
        for y, x in adjacent_positions:
            # Check if position is valid and passable
            if (self.game.is_valid_position(y, x) and 
                self.game.map.is_passable(y, x) and 
                not self.game.get_unit_at(y, x)):
                valid_positions.append((y, x))
        
        return valid_positions
    
    def _assign_targets_to_units(self, ai_units: List['Unit'], player_units: List['Unit']) -> None:
        """
        Assign appropriate targets to AI units based on tactical priorities.
        
        Args:
            ai_units: AI units that need target assignments
            player_units: Available player units to target
        """
        # Track which player units are being targeted by how many AI units
        target_count = {unit.id: 0 for unit in player_units}
        
        for unit in ai_units:
            # Find best target considering group coordination
            best_target = self._find_coordinated_target(unit, player_units, target_count)
            
            if best_target:
                # Update target assignment
                self.target_assignments[unit.id] = best_target.id
                # Increment target count
                target_count[best_target.id] += 1
                
                logger.info(f"Assigned {unit.get_display_name()} to target {best_target.get_display_name()}")
    
    def _find_coordinated_target(self, unit: 'Unit', player_units: List['Unit'], 
                               target_count: Dict[str, int]) -> Optional['Unit']:
        """
        Find the best target for a unit considering group coordination.
        Ensures we don't have too many units attacking the same target.
        
        Args:
            unit: The AI unit needing a target
            player_units: Available player units to target
            target_count: Dictionary tracking how many AI units are targeting each player unit
            
        Returns:
            The best target unit, or None if no targets available
        """
        # Calculate scores for each potential target
        target_scores = []
        
        for target in player_units:
            score = 0
            
            # Distance factor (closer is better)
            distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
            distance_score = max(20 - distance, 0)  # Higher score for closer targets
            score += distance_score
            
            # Target health factor (lower health is better)
            health_factor = 100 - target.current_hp
            score += health_factor * 0.5
            
            # Coordination factor (prefer targets with fewer units assigned)
            current_attackers = target_count[target.id]
            if current_attackers == 0:
                # Bonus for unassigned targets
                score += 15
            elif current_attackers >= 2:
                # Penalty for overassigned targets
                score -= 20 * (current_attackers - 1)
            
            target_scores.append((target, score))
        
        # Sort by score (highest first)
        target_scores.sort(key=lambda x: x[1], reverse=True)
        
        if target_scores:
            return target_scores[0][0]
        return None
            
    def _ensure_all_units_have_targets(self, ai_units: List['Unit']) -> None:
        """
        Make sure all AI units have an enemy target to pursue.
        Basic version for MEDIUM difficulty.
        
        Args:
            ai_units: List of all AI units
        """
        # Get all player units for targeting
        player_units = [unit for unit in self.game.units 
                      if unit.player == 1 and unit.is_alive()]
                      
        if not player_units:
            return
            
        # Every AI unit must have at least one player unit to target
        for ai_unit in ai_units:
            # The unit will find its own nearest enemy when processed
            logger.info(f"AI ensuring unit {ai_unit.get_display_name()} has a target")
            
    def _sort_units_by_tactical_priority(self, units: List['Unit']) -> List['Unit']:
        """
        Sort units by their tactical priority - implemented on HARD difficulty.
        Units that can attack are prioritized.
        
        Args:
            units: List of units to sort
            
        Returns:
            Sorted list of units by tactical priority
        """
        # Create a list of (unit, priority score) tuples
        scored_units = []
        
        for unit in units:
            score = 0
            
            # Check if unit can attack any player unit from current position
            for target in self.game.units:
                if target.player != self.player_number and target.is_alive():
                    # Units that can attack immediately get highest priority
                    if self._can_attack(unit, target):
                        score += 10
                        
                    # Units close to enemies get medium priority
                    distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
                    if distance <= unit.get_effective_stats()['move_range'] + 1:
                        score += 5
            
            # Add current HP as a small factor (prioritize healthy units slightly)
            score += unit.current_hp / 10
            
            scored_units.append((unit, score))
            
        # Sort by score in descending order
        sorted_units = [u for u, s in sorted(scored_units, key=lambda x: x[1], reverse=True)]
        return sorted_units
    
    def _process_unit(self, unit: 'Unit') -> None:
        """
        Process actions for a single unit.
        
        Args:
            unit: The unit to process
        """
        # For now, we'll only implement Glaiveman logic
        if unit.type == UnitType.GLAIVEMAN:
            self._process_glaiveman(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        else:
            # Default behavior for other unit types
            logger.info(f"No specific AI logic for {unit.type.name}, using default behavior")
            self._process_default_unit(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
    
    def _process_glaiveman(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a Glaiveman unit.
        Implements aggressive movement and attack behavior.
        
        Args:
            unit: The Glaiveman unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Always reset move and attack targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        
        # Get a target based on the difficulty level or coordination
        target = None
        
        # If using coordination and this unit has an assigned target, use it
        if use_coordination and unit.id in self.target_assignments:
            # Get the assigned target from coordination
            target_id = self.target_assignments[unit.id]
            # Find the target unit by ID
            for player_unit in self.game.units:
                if player_unit.id == target_id and player_unit.is_alive():
                    target = player_unit
                    logger.info(f"Using coordinated target for {unit.get_display_name()}: {target.get_display_name()}")
                    break
        
        # If no coordinated target was found, fall back to normal targeting
        if not target:
            if self.difficulty == AIDifficulty.EASY:
                target = self._find_random_enemy(unit)
            elif self.difficulty == AIDifficulty.MEDIUM:
                target = self._find_nearest_enemy(unit)
            else:  # HARD difficulty
                target = self._find_best_target(unit)
            
        if not target:
            logger.info("No enemies found for Glaiveman to target")
            return
            
        logger.info(f"Glaiveman targeting enemy: {target.get_display_name()} at position ({target.y}, {target.x})")
        
        # Check if we can attack the enemy from our current position
        can_attack = self._can_attack(unit, target)
        
        # If we can attack, do it
        if can_attack:
            logger.info(f"Glaiveman attacking enemy at ({target.y}, {target.x})")
            unit.attack_target = (target.y, target.x)
        # If we can't attack, try to move closer
        else:
            # EASY difficulty has a chance to skip movement
            if self.difficulty == AIDifficulty.EASY and random.random() < 0.3:
                logger.info("EASY difficulty: Glaiveman decided not to move this turn")
                return
                
            logger.info(f"Glaiveman moving towards enemy at ({target.y}, {target.x})")
            
            # If using coordination, consider planned positions
            if use_coordination:
                self._move_with_coordination(unit, target)
            else:
                self._move_towards_enemy(unit, target)
            
            # Check if we can attack after moving
            can_attack_after_move = self._can_attack_after_move(unit, target)
            if can_attack_after_move:
                logger.info(f"Glaiveman attacking enemy after movement")
                # The attack_target is set in _can_attack_after_move
    
    def _process_default_unit(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Default processing for units without specific AI logic.
        Aggressively moves towards the nearest enemy and attacks if possible.
        
        Args:
            unit: The unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Always reset move and attack targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        
        # Get a target based on the difficulty level or coordination
        target = None
        
        # If using coordination and this unit has an assigned target, use it
        if use_coordination and unit.id in self.target_assignments:
            # Get the assigned target from coordination
            target_id = self.target_assignments[unit.id]
            # Find the target unit by ID
            for player_unit in self.game.units:
                if player_unit.id == target_id and player_unit.is_alive():
                    target = player_unit
                    logger.info(f"Using coordinated target for {unit.get_display_name()}: {target.get_display_name()}")
                    break
        
        # If no coordinated target was found, fall back to normal targeting
        if not target:
            if self.difficulty == AIDifficulty.EASY:
                target = self._find_random_enemy(unit)
            elif self.difficulty == AIDifficulty.MEDIUM:
                target = self._find_nearest_enemy(unit)
            else:  # HARD difficulty
                target = self._find_best_target(unit)
        
        if not target:
            logger.info("No enemies found for unit to target")
            return
            
        logger.info(f"Unit targeting enemy: {target.get_display_name()} at position ({target.y}, {target.x})")
        
        # Check if we can attack the enemy from our current position
        can_attack = self._can_attack(unit, target)
        
        # If we can attack, do it
        if can_attack:
            logger.info(f"Unit attacking enemy at ({target.y}, {target.x})")
            unit.attack_target = (target.y, target.x)
        # If we can't attack, try to move closer
        else:
            # EASY difficulty has a chance to skip movement
            if self.difficulty == AIDifficulty.EASY and random.random() < 0.3:
                logger.info("EASY difficulty: Unit decided not to move this turn")
                return
                
            logger.info(f"Unit moving towards enemy at ({target.y}, {target.x})")
            
            # If using coordination, consider planned positions
            if use_coordination:
                self._move_with_coordination(unit, target)
            else:
                self._move_towards_enemy(unit, target)
            
            # Check if we can attack after moving
            can_attack_after_move = self._can_attack_after_move(unit, target)
            if can_attack_after_move:
                logger.info(f"Unit attacking enemy after movement")
                # The attack_target is set in _can_attack_after_move
    
    def _find_nearest_enemy(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find the nearest enemy unit.
        
        Args:
            unit: The unit to find an enemy for
            
        Returns:
            The nearest enemy unit, or None if no enemies are found
        """
        enemy_units = [enemy for enemy in self.game.units 
                      if enemy.player != unit.player and enemy.is_alive()]
        
        if not enemy_units:
            return None
            
        # Find the enemy with the shortest distance
        nearest_enemy = None
        shortest_distance = float('inf')
        
        for enemy in enemy_units:
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_enemy = enemy
                
        return nearest_enemy
        
    def _find_random_enemy(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find a random enemy unit - used for EASY difficulty.
        
        Args:
            unit: The unit to find an enemy for
            
        Returns:
            A random enemy unit, or None if no enemies are found
        """
        enemy_units = [enemy for enemy in self.game.units 
                      if enemy.player != unit.player and enemy.is_alive()]
        
        if not enemy_units:
            return None
            
        # Choose a random enemy, but with some bias towards closer units
        enemy_distances = [(enemy, self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)) 
                         for enemy in enemy_units]
        
        # Sort by distance (closest first)
        enemy_distances.sort(key=lambda x: x[1])
        
        # On easy difficulty, we're more likely to pick one of the first few enemies
        # but there's a chance to pick any enemy
        if len(enemy_distances) > 1 and random.random() < 0.7:
            # Pick one of the 3 closest enemies, or all if there are fewer than 3
            max_index = min(3, len(enemy_distances))
            return random.choice(enemy_distances[:max_index])[0]
        else:
            # Completely random choice from all enemies
            return random.choice(enemy_distances)[0]
            
    def _find_best_target(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find the best target unit based on tactical evaluation - used for HARD difficulty.
        Considers the target's health, attack range, and distance.
        
        Args:
            unit: The unit to find a target for
            
        Returns:
            The best target unit, or None if no enemies are found
        """
        enemy_units = [enemy for enemy in self.game.units 
                      if enemy.player != unit.player and enemy.is_alive()]
        
        if not enemy_units:
            return None
            
        # Calculate scores for each enemy
        scored_enemies = []
        
        # Get attacker's effective stats
        attacker_stats = unit.get_effective_stats()
        attacker_move = attacker_stats['move_range']
        attacker_attack = attacker_stats['attack_range']
        
        for enemy in enemy_units:
            score = 0
            
            # Calculate base distance
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            
            # Calculate if the enemy is reachable for attack (either now or after moving)
            can_attack_now = distance <= attacker_attack
            can_reach_for_attack = distance <= (attacker_move + attacker_attack)
            
            # Immediate attack opportunities get highest priority
            if can_attack_now:
                score += 50
            # Targets that can be reached this turn get medium priority
            elif can_reach_for_attack:
                score += 30
                
            # Prioritize lower health enemies (but not if they're too far)
            if can_reach_for_attack or distance < 10:
                # Invert HP to give higher scores to lower-HP enemies
                hp_factor = 100 - enemy.current_hp
                score += hp_factor * 0.5
                
            # Prioritize dangerous enemies (high attack power)
            enemy_stats = enemy.get_effective_stats()
            enemy_attack = enemy_stats['attack']
            score += enemy_attack * 0.3
            
            # Distance penalty (further targets get lower scores)
            score -= distance * 2
            
            scored_enemies.append((enemy, score))
        
        # Get the enemy with the highest score
        if scored_enemies:
            scored_enemies.sort(key=lambda x: x[1], reverse=True)
            return scored_enemies[0][0]
            
        # Fallback to nearest enemy if scoring fails
        return self._find_nearest_enemy(unit)
    
    def _can_attack(self, unit: 'Unit', target: 'Unit') -> bool:
        """
        Check if a unit can attack a target from its current position.
        
        Args:
            unit: The attacking unit
            target: The target unit
            
        Returns:
            True if the attack is possible, False otherwise
        """
        # Get effective stats
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        
        # Calculate distance
        distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
        
        # Check if target is within attack range
        return distance <= attack_range
    
    def _can_attack_after_move(self, unit: 'Unit', target: 'Unit') -> bool:
        """
        Check if a unit can attack after moving to its current move target.
        
        Args:
            unit: The attacking unit
            target: The target unit
            
        Returns:
            True if the attack is possible after moving, False otherwise
        """
        # If no move target set, unit can't attack after moving
        if not unit.move_target:
            return False
            
        # Get effective stats
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        
        # Calculate distance from move target to target unit
        move_y, move_x = unit.move_target
        distance = self.game.chess_distance(move_y, move_x, target.y, target.x)
        
        # Check if target is within attack range after moving
        if distance <= attack_range:
            # Set attack target for end of turn processing
            unit.attack_target = (target.y, target.x)
            return True
            
        return False
    
    def _move_with_coordination(self, unit: 'Unit', target: 'Unit') -> None:
        """
        Move a unit towards an enemy using group coordination information.
        Considers planned positions from group tactics.
        
        Args:
            unit: The unit to move
            target: The enemy to move towards
        """
        # Get effective stats
        stats = unit.get_effective_stats()
        move_range = stats['move_range']
        
        # No movement possible
        if move_range <= 0:
            logger.info(f"Unit {unit.get_display_name()} cannot move (move_range = {move_range})")
            return
        
        # Check if this unit has a planned position from coordination
        planned_position = None
        for pos, unit_id in self.planned_positions.items():
            if unit_id == unit.id:
                planned_position = pos
                break
                
        # If we have a planned position and it's valid, use it
        if planned_position:
            y, x = planned_position
            # Verify the position is still valid
            if (self.game.is_valid_position(y, x) and 
                self.game.map.is_passable(y, x) and 
                not self.game.get_unit_at(y, x)):
                
                # Verify it's within move range or find a path towards it
                distance = self.game.chess_distance(unit.y, unit.x, y, x)
                if distance <= move_range:
                    # Direct move to planned position
                    unit.move_target = (y, x)
                    logger.info(f"Moving to coordinated position at ({y}, {x})")
                    return
                else:
                    # Can't reach planned position yet, move towards it
                    logger.info(f"Moving towards coordinated position at ({y}, {x})")
                    # Create a temporary target at the position
                    from boneglaive.game.units import Unit
                    # Create a minimal fake unit at the position as a target
                    fake_target = Unit(player=1, type=UnitType.GLAIVEMAN, y=y, x=x)
                    fake_target.current_hp = 10  # Arbitrary value
                    # Move towards the position
                    self._move_towards_enemy(unit, fake_target)
                    return
        
        # If no valid planned position, use normal movement
        self._move_towards_enemy(unit, target)
        
    def _move_towards_enemy(self, unit: 'Unit', target: 'Unit') -> None:
        """
        Move a unit towards an enemy - always ensure a move happens if possible.
        
        Args:
            unit: The unit to move
            target: The enemy to move towards
        """
        # Get effective stats
        stats = unit.get_effective_stats()
        move_range = stats['move_range']
        
        # No movement possible
        if move_range <= 0:
            logger.info(f"Unit {unit.get_display_name()} cannot move (move_range = {move_range})")
            return
            
        # Find the best move position
        best_pos = self._find_best_move_position(unit, target, move_range)
        
        if best_pos:
            # Set the move target
            unit.move_target = best_pos
            logger.info(f"Setting move target to ({best_pos[0]}, {best_pos[1]})")
        else:
            logger.warning(f"Could not find valid move for {unit.get_display_name()} towards {target.get_display_name()}")
    
    def _find_best_move_position(self, unit: 'Unit', target: 'Unit', move_range: int) -> Optional[Tuple[int, int]]:
        """
        Find the best position to move towards an enemy.
        
        Args:
            unit: The unit to move
            target: The enemy to move towards
            move_range: The unit's movement range
            
        Returns:
            The best position to move to, or None if no valid move found
        """
        # Get all valid positions the unit can move to
        reachable_positions = []
        
        # Import necessary path checking utilities
        from boneglaive.utils.coordinates import Position, get_line
        
        for y in range(max(0, unit.y - move_range), min(self.game.map.height, unit.y + move_range + 1)):
            for x in range(max(0, unit.x - move_range), min(self.game.map.width, unit.x + move_range + 1)):
                # Check if position is valid and within move range
                if not self.game.is_valid_position(y, x):
                    continue
                    
                if not self.game.map.is_passable(y, x):
                    continue
                    
                # Check if position is occupied
                if self.game.get_unit_at(y, x) is not None:
                    continue
                    
                # Check if within move range (chess distance)
                distance = self.game.chess_distance(unit.y, unit.x, y, x)
                if distance > move_range:
                    continue
                
                # For non-adjacent moves, validate path to ensure no units or impassable terrain blocks the way
                if distance > 1:
                    # Get path positions
                    start_pos = Position(unit.y, unit.x)
                    end_pos = Position(y, x)
                    path = get_line(start_pos, end_pos)
                    
                    # Check if path is clear (excluding start and end positions)
                    path_is_clear = True
                    for pos in path[1:-1]:  # Skip start and end positions
                        # Check for blocking units
                        blocking_unit = self.game.get_unit_at(pos.y, pos.x)
                        if blocking_unit:
                            path_is_clear = False
                            break
                            
                        # Check for impassable terrain
                        if not self.game.map.is_passable(pos.y, pos.x):
                            path_is_clear = False
                            break
                    
                    # Skip this position if path is not clear
                    if not path_is_clear:
                        continue
                    
                # Position is valid, add to reachable positions
                reachable_positions.append((y, x))
                
        if not reachable_positions:
            return None
            
        # Get the position closest to the target
        best_pos = None
        shortest_distance = float('inf')
        
        for y, x in reachable_positions:
            distance = self.game.chess_distance(y, x, target.y, target.x)
            if distance < shortest_distance:
                shortest_distance = distance
                best_pos = (y, x)
                
        return best_pos