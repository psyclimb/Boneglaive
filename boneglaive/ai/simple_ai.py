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
        try:
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
            units_processed = 0
            for unit in ai_units:
                logger.info(f"AI processing unit: {unit.get_display_name()}")
                self._process_unit(unit)
                units_processed += 1
                
                # Update the UI after each unit action
                if self.ui:
                    self.ui.draw_board()
                    
            logger.info(f"AI processed {units_processed} units")
                    
            # End the turn
            logger.info("AI ending turn")
            return True
        except Exception as e:
            import traceback
            logger.error(f"Error in AI processing turn: {e}")
            logger.error(traceback.format_exc())
            # Even if there's an error, we should let the turn complete
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
            health_factor = 100 - target.hp
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
        
        # Log the top target choices
        if target_scores:
            # Debug log top three if available
            for i, (target, score) in enumerate(target_scores[:min(3, len(target_scores))]):
                logger.debug(f"Coordinated target option {i+1} for {unit.get_display_name()}: {target.get_display_name()} (score: {score})")
        
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
            score += unit.hp / 10
            
            scored_units.append((unit, score))
            
        # Sort by score in descending order
        sorted_units = [u for u, s in sorted(scored_units, key=lambda x: x[1], reverse=True)]
        
        # Log sorted order for debugging
        logger.debug("AI unit processing order:")
        for i, unit in enumerate(sorted_units):
            logger.debug(f"{i+1}. {unit.get_display_name()}")
        
        return sorted_units
    
    def _process_unit(self, unit: 'Unit') -> None:
        """
        Process actions for a single unit.
        
        Args:
            unit: The unit to process
        """
        # Process units based on their type
        if unit.type == UnitType.GLAIVEMAN:
            self._process_glaiveman(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.MANDIBLE_FOREMAN:
            self._process_mandible_foreman(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        else:
            # Default behavior for other unit types
            logger.info(f"No specific AI logic for {unit.type.name}, using default behavior")
            self._process_default_unit(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
    
    def _process_glaiveman(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a Glaiveman unit.
        Implements intelligent skill usage and aggressive movement/attack behavior.
        
        Args:
            unit: The Glaiveman unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Always reset move and attack targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        unit.skill_target = None
        unit.selected_skill = None
        
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
        
        # Get available skills 
        available_skills = []
        try:
            available_skills = unit.get_available_skills()
            logger.info(f"Glaiveman has {len(available_skills)} skills available: {[skill.name for skill in available_skills]}")
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            
        # Flag to track if we used a skill
        used_skill = None
        
        # Skip skill usage on EASY difficulty most of the time
        if self.difficulty == AIDifficulty.EASY and random.random() < 0.7:
            logger.info("EASY difficulty: Skipping skill usage")
        else:
            # On MEDIUM or HARD, intelligently use skills
            try:
                used_skill = self._use_glaiveman_skills(unit, target, available_skills)
                if used_skill:
                    logger.info(f"Glaiveman used {used_skill.name} skill")
                    # Don't return - we'll let the method complete even if a skill was used
                    # This ensures that units always take some action
            except Exception as e:
                logger.error(f"Error using Glaiveman skills: {e}")
                used_skill = None
        
        # Only proceed with move/attack if no skill was used
        if not used_skill:
            # If we didn't use a skill, proceed with normal attack or movement
            
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
    
    def _use_glaiveman_skills(self, unit: 'Unit', target: 'Unit', available_skills: list) -> Optional['ActiveSkill']:
        """
        Intelligently use Glaiveman skills based on current situation.
        
        Args:
            unit: The Glaiveman unit
            target: The enemy target
            available_skills: List of available active skills
            
        Returns:
            The skill that was used, or None if no skill was used
        """
        try:
            if not available_skills:
                logger.info("No skills available for this Glaiveman")
                return None
                
            # Debug available skills
            logger.info(f"Evaluating skills: {[skill.name for skill in available_skills]}")
            
            # Evaluate each skill's potential value
            skill_scores = []
            
            for skill in available_skills:
                # Use different evaluation based on skill type
                try:
                    if skill.name == "Judgement":
                        score = self._evaluate_judgement_skill(unit, target, skill)
                        if score > 0:
                            skill_scores.append((skill, score, target))
                        
                    elif skill.name == "Pry":
                        # For Pry, check if we can use it directly on the target
                        if skill.can_use(unit, (target.y, target.x), self.game):
                            score = self._evaluate_pry_skill(unit, target, skill)
                            if score > 0:
                                skill_scores.append((skill, score, target))
                        # If not, check nearby enemies for Pry
                        else:
                            for nearby_enemy in self.game.units:
                                if (nearby_enemy.player != unit.player and nearby_enemy.is_alive() and 
                                    nearby_enemy != target and 
                                    skill.can_use(unit, (nearby_enemy.y, nearby_enemy.x), self.game)):
                                    score = self._evaluate_pry_skill(unit, nearby_enemy, skill)
                                    if score > 0:
                                        skill_scores.append((skill, score, nearby_enemy))
                                    
                    elif skill.name == "Vault":
                        # For Vault, find the best destination position
                        best_pos, score = self._evaluate_vault_skill(unit, target, skill)
                        if best_pos and score > 0:
                            skill_scores.append((skill, score, best_pos))
                except Exception as e:
                    logger.error(f"Error evaluating skill {skill.name}: {e}")
                    continue
            
            # Debug skill scores
            logger.info(f"Skill scores: {[(s[0].name, s[1]) for s in skill_scores]}")
            
            # Sort by score (highest first)
            skill_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Use the highest scoring skill if score is above threshold
            if skill_scores:  # Only use skill if there are scored skills
                skill, score, target_or_pos = skill_scores[0]
                
                logger.info(f"Using skill {skill.name} with score {score}")
                
                # Use the skill based on its type
                success = False
                if skill.name == "Judgement" or skill.name == "Pry":
                    # These skills target enemy units
                    target_unit = target_or_pos
                    success = skill.use(unit, (target_unit.y, target_unit.x), self.game)
                    logger.info(f"Skill use result: {success}")
                    
                elif skill.name == "Vault":
                    # Vault targets a position
                    vault_pos = target_or_pos
                    success = skill.use(unit, vault_pos, self.game)
                    logger.info(f"Skill use result: {success}")
                
                if success:
                    return skill
                    
            logger.info("No suitable skill used")
            return None
        except Exception as e:
            import traceback
            logger.error(f"Error in _use_glaiveman_skills: {e}")
            logger.error(traceback.format_exc())
            return None
        
    def _evaluate_judgement_skill(self, unit: 'Unit', target: 'Unit', skill) -> float:
        """
        Evaluate the value of using Judgement skill on the target.
        
        Args:
            unit: The Glaiveman unit
            target: The enemy target
            skill: The Judgement skill
            
        Returns:
            A score indicating the value of using this skill (higher is better)
        """
        # Check if we can use the skill
        if not skill.can_use(unit, (target.y, target.x), self.game):
            return -1  # Can't use
            
        score = 0
        
        # Base score for being able to use the skill
        score += 20
        
        # Judgement deals defensive-ignoring damage, which is useful against high-defense targets
        # Also deals double damage to targets at critical health
        is_target_critical = target.is_at_critical_health()
        
        # Calculate expected damage (double for critical, ignores defense)
        expected_damage = skill.damage
        if is_target_critical:
            expected_damage *= 2
            
        # Can we kill the target?
        if target.hp <= expected_damage:
            score += 40  # High priority to kill
        
        # More valuable against high-defense targets
        if target.defense >= 2:
            score += 15
            
        # More valuable against critical targets (due to double damage)
        if is_target_critical:
            score += 25
            
        # Distance consideration - more valuable for targets outside normal attack range
        distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
        attack_range = unit.get_effective_stats()['attack_range']
        
        if distance > attack_range:  # Can't reach with normal attack
            score += 10
            
            if distance <= skill.range:  # Within Judgement range
                score += 10
            
        return score
    
    def _evaluate_pry_skill(self, unit: 'Unit', target: 'Unit', skill) -> float:
        """
        Evaluate the value of using Pry skill on the target.
        
        Args:
            unit: The Glaiveman unit
            target: The enemy target
            skill: The Pry skill
            
        Returns:
            A score indicating the value of using this skill (higher is better)
        """
        # Check if we can use the skill
        if not skill.can_use(unit, (target.y, target.x), self.game):
            return -1  # Can't use
            
        score = 0
        
        # Base score for being able to use the skill
        score += 15
        
        # Calculate expected primary damage
        defense_reduced_damage = max(3, skill.primary_damage - target.defense)  # 3 damage minimum
        
        # Can we kill the target?
        if target.hp <= defense_reduced_damage:
            score += 30  # Priority to kill
            
        # How many adjacent enemies would be affected by splash damage?
        splash_targets = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                # Skip the center (primary target)
                if dy == 0 and dx == 0:
                    continue
                
                # Check adjacent position
                adj_y = target.y + dy
                adj_x = target.x + dx
                
                # Validate position
                if not self.game.is_valid_position(adj_y, adj_x):
                    continue
                
                # Check if there's an enemy unit at this position
                adjacent_unit = self.game.get_unit_at(adj_y, adj_x)
                if adjacent_unit and adjacent_unit.is_alive() and adjacent_unit.player != unit.player:
                    splash_targets += 1
        
        # Bonus for splash targets
        if splash_targets > 0:
            score += splash_targets * 10  # 10 points per splash target
            
        # More valuable for slowing high-movement enemies
        target_move = target.get_effective_stats()['move_range']
        if target_move >= 3:
            score += 10
            
        # More valuable if target is trapped by a MANDIBLE_FOREMAN (since Pry will free them)
        if hasattr(target, 'trapped_by') and target.trapped_by is not None:
            score += 5
            
        # More valuable if target has trapped other units (since Pry will free those units)
        for other_unit in self.game.units:
            if (hasattr(other_unit, 'trapped_by') and other_unit.trapped_by == target and 
                other_unit.player == unit.player):  # Only care about freeing our own units
                score += 15  # High priority to free our trapped allies
                break
                
        return score
        
    def _evaluate_vault_skill(self, unit: 'Unit', target: 'Unit', skill) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Evaluate the value of using Vault skill to a position.
        Finds the best position to vault to and returns its score.
        
        Args:
            unit: The Glaiveman unit
            target: The enemy target
            skill: The Vault skill
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or None
        """
        # Get effective stats including attack range
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        
        # Check all potential vault positions within skill range
        best_position = None
        best_score = -1
        
        # Check positions in a square area around the unit
        for y in range(max(0, unit.y - skill.range), min(self.game.map.height, unit.y + skill.range + 1)):
            for x in range(max(0, unit.x - skill.range), min(self.game.map.width, unit.x + skill.range + 1)):
                # Check if position is valid for vault
                if not skill.can_use(unit, (y, x), self.game):
                    continue
                    
                # Calculate distance to target from this position
                target_distance = self.game.chess_distance(y, x, target.y, target.x)
                
                # Calculate score based on tactical value of position
                score = 0
                
                # Base score for a valid position
                score += 5
                
                # Bonus if we can attack target after vaulting
                if target_distance <= attack_range:
                    score += 20
                    
                    # Additional bonus if this is the only way to attack the target
                    current_distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
                    if current_distance > stats['move_range'] + attack_range:  # Can't reach normally
                        score += 15
                        
                    # Position right next to target is often not ideal unless we need it to attack
                    if target_distance == 1:
                        score -= 5  # Small penalty for being adjacent (vulnerable)
                    
                    # Extra bonus for optimal attack distance
                    if target_distance == attack_range:
                        score += 5  # Optimal attack position
                        
                # Vault to escape when at low health
                if unit.hp < unit.max_hp * 0.4:  # Below 40% health
                    # Score inversely proportional to number of nearby enemies
                    enemies_nearby = 0
                    for enemy in self.game.units:
                        if enemy.player != unit.player and enemy.is_alive():
                            enemy_distance = self.game.chess_distance(y, x, enemy.y, enemy.x)
                            if enemy_distance <= enemy.get_effective_stats()['attack_range'] + 1:
                                enemies_nearby += 1
                    
                    # Bonus for positions with fewer nearby enemies
                    if enemies_nearby == 0:
                        score += 25  # Great escape position with no enemies nearby
                    else:
                        score -= enemies_nearby * 5  # Penalty for each nearby enemy
                
                # Vault to reach key strategic positions
                
                # 1. Vault over obstacles that block normal movement
                blocked_path = False
                # Check if normal movement path is blocked
                from boneglaive.utils.coordinates import Position, get_line
                path = get_line(Position(unit.y, unit.x), Position(target.y, target.x))
                for i, pos in enumerate(path[1:-1]):  # Skip start and end positions
                    # Check for blocking units or terrain
                    if (not self.game.is_valid_position(pos.y, pos.x) or
                        not self.game.map.is_passable(pos.y, pos.x) or
                        self.game.get_unit_at(pos.y, pos.x) is not None):
                        blocked_path = True
                        break
                
                if blocked_path:
                    score += 10  # Bonus for bypassing obstacles
                    
                # 2. Vault to flank target (get on opposite side from our other units)
                for ally in self.game.units:
                    if ally.is_alive() and ally.player == unit.player and ally.id != unit.id:
                        # Check if this position puts us on opposite side of target from ally
                        from math import atan2
                        # Calculate vectors from target to ally and from target to vault position
                        ally_angle = atan2(ally.y - target.y, ally.x - target.x)
                        vault_angle = atan2(y - target.y, x - target.x)
                        # Calculate angle difference (in radians)
                        angle_diff = abs(ally_angle - vault_angle)
                        if angle_diff > 2.5:  # Approximately 140+ degrees
                            score += 10  # Good flanking position
                            break
                
                # Update best position if this is better
                if score > best_score:
                    best_score = score
                    best_position = (y, x)
        
        return best_position, best_score
    
    def _process_mandible_foreman(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a Mandible Foreman unit.
        Focuses on trapping enemies with attacks and managing its trap-related skills.
        
        Args:
            unit: The Mandible Foreman unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Always reset move and attack targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        unit.skill_target = None
        unit.selected_skill = None
        
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
                target = self._find_best_target_for_foreman(unit)
            
        if not target:
            logger.info("No enemies found for Mandible Foreman to target")
            return
            
        logger.info(f"Mandible Foreman targeting enemy: {target.get_display_name()} at position ({target.y}, {target.x})")
        
        # Get available skills 
        available_skills = []
        try:
            available_skills = unit.get_available_skills()
            logger.info(f"Mandible Foreman has {len(available_skills)} skills available: {[skill.name for skill in available_skills]}")
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            
        # Flag to track if we used a skill
        used_skill = None
        
        # Skip skill usage on EASY difficulty most of the time
        if self.difficulty == AIDifficulty.EASY and random.random() < 0.7:
            logger.info("EASY difficulty: Skipping skill usage")
        else:
            # On MEDIUM or HARD, intelligently use skills
            try:
                used_skill = self._use_mandible_foreman_skills(unit, target, available_skills)
                if used_skill:
                    logger.info(f"Mandible Foreman used {used_skill.name} skill")
                    # Don't return - we'll let the method complete even if a skill was used
                    # This ensures that units always take some action
            except Exception as e:
                logger.error(f"Error using Mandible Foreman skills: {e}")
                import traceback
                logger.error(traceback.format_exc())
                used_skill = None
        
        # Only proceed with move/attack if no skill was used
        if not used_skill:
            # If we didn't use a skill, proceed with normal attack or movement
            
            # Check if we can attack the enemy from our current position
            can_attack = self._can_attack(unit, target)
            
            # If we can attack, do it
            if can_attack:
                logger.info(f"Mandible Foreman attacking enemy at ({target.y}, {target.x})")
                unit.attack_target = (target.y, target.x)
            # If we can't attack, try to move closer
            else:
                # EASY difficulty has a chance to skip movement
                if self.difficulty == AIDifficulty.EASY and random.random() < 0.3:
                    logger.info("EASY difficulty: Mandible Foreman decided not to move this turn")
                    return
                    
                logger.info(f"Mandible Foreman moving towards enemy at ({target.y}, {target.x})")
                
                # If using coordination, consider planned positions
                if use_coordination:
                    self._move_with_coordination(unit, target)
                else:
                    self._move_towards_enemy(unit, target)
                
                # Check if we can attack after moving
                can_attack_after_move = self._can_attack_after_move(unit, target)
                if can_attack_after_move:
                    logger.info(f"Mandible Foreman attacking enemy after movement")
                    # The attack_target is set in _can_attack_after_move
    
    def _use_mandible_foreman_skills(self, unit: 'Unit', target: 'Unit', available_skills: list) -> Optional['ActiveSkill']:
        """
        Intelligently use Mandible Foreman skills based on the current situation.
        
        Args:
            unit: The Mandible Foreman unit
            target: The enemy target
            available_skills: List of available active skills
            
        Returns:
            The skill that was used, or None if no skill was used
        """
        try:
            if not available_skills:
                logger.info("No skills available for this Mandible Foreman")
                return None
                
            # Debug available skills
            logger.info(f"Evaluating skills: {[skill.name for skill in available_skills]}")
            
            # Evaluate each skill's potential value
            skill_scores = []
            
            for skill in available_skills:
                # Use different evaluation based on skill type
                try:
                    if skill.name == "Expedite":
                        best_pos, score = self._evaluate_expedite_skill(unit, target, skill)
                        if best_pos and score > 0:
                            skill_scores.append((skill, score, best_pos))
                    elif skill.name == "Jawline":
                        score = self._evaluate_jawline_skill(unit, target, skill)
                        if score > 0:
                            skill_scores.append((skill, score, (unit.y, unit.x)))  # Jawline targets self-position
                    elif skill.name == "Site Inspection":
                        best_pos, score = self._evaluate_site_inspection_skill(unit, target, skill)
                        if best_pos and score > 0:
                            skill_scores.append((skill, score, best_pos))
                except Exception as e:
                    logger.error(f"Error evaluating skill {skill.name}: {e}")
                    continue
            
            # Debug skill scores
            logger.info(f"Skill scores: {[(s[0].name, s[1]) for s in skill_scores]}")
            
            # Sort by score (highest first)
            skill_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Use the highest scoring skill if score is above threshold
            if skill_scores and skill_scores[0][1] >= 30:  # Set threshold for skill usage
                skill, score, target_pos = skill_scores[0]
                
                logger.info(f"Using skill {skill.name} with score {score}")
                
                # Use the skill
                success = skill.use(unit, target_pos, self.game)
                logger.info(f"Skill use result: {success}")
                
                if success:
                    return skill
                    
            logger.info("No suitable skill used")
            return None
        except Exception as e:
            import traceback
            logger.error(f"Error in _use_mandible_foreman_skills: {e}")
            logger.error(traceback.format_exc())
            return None
            
    def _evaluate_expedite_skill(self, unit: 'Unit', target: 'Unit', skill) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Evaluate the value of using Expedite skill to rush towards a position.
        Finds the best position to rush to and returns its score.
        
        Args:
            unit: The Mandible Foreman unit
            target: The enemy target
            skill: The Expedite skill
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or (None, -1) if no valid position
        """
        # If skill is not ready yet, return no valid position
        if not skill.can_use(unit, None, self.game):
            return None, -1
            
        # Get effective stats including attack range
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']  # Usually 1 for Mandible Foreman
        
        # Find positions in direction of target
        best_position = None
        best_score = 0
        
        # Get the vector from unit to target
        dy = target.y - unit.y
        dx = target.x - unit.x
        
        # Normalize the direction for cardinal/diagonal movement
        # Expedite can only move in straight lines (cardinal or diagonal)
        if dy != 0:
            dy = dy // abs(dy)
        if dx != 0:
            dx = dx // abs(dx)
            
        # Calculate maximum distance for skill range
        max_distance = min(skill.range, self.game.chess_distance(unit.y, unit.x, target.y, target.x))
        
        # Check positions along the line toward target
        for distance in range(1, max_distance + 1):
            check_y = unit.y + dy * distance
            check_x = unit.x + dx * distance
            
            # Skip invalid positions
            if not self.game.is_valid_position(check_y, check_x):
                continue
                
            # Check if the position is valid for Expedite
            if skill.can_use(unit, (check_y, check_x), self.game):
                # Calculate score for this position
                pos_score = self._score_expedite_position(unit, (check_y, check_x), target, skill)
                
                # Update best position if this is better
                if pos_score > best_score:
                    best_score = pos_score
                    best_position = (check_y, check_x)
                    
                # Check for enemy units along the path
                # If we hit an enemy, we should consider the enemy position
                check_unit = self.game.get_unit_at(check_y, check_x)
                if check_unit and check_unit.player != unit.player:
                    # Enemy unit found - this is a higher-priority target for Expedite
                    enemy_score = self._score_expedite_enemy_hit(unit, check_unit, skill)
                    
                    # If this enemy gives a higher score than our current best, use it
                    if enemy_score > best_score:
                        best_score = enemy_score
                        # For enemy hits, use their position as the target (Expedite will stop before it)
                        best_position = (check_y, check_x)
                    
                    # We need to stop the path check here because Expedite stops at the first enemy hit
                    break
        
        return best_position, best_score
        
    def _score_expedite_position(self, unit: 'Unit', position: Tuple[int, int], original_target: 'Unit', skill) -> float:
        """
        Score a potential Expedite position based on tactical considerations.
        
        Args:
            unit: The Mandible Foreman unit
            position: The position to evaluate
            original_target: The original enemy target
            skill: The Expedite skill
            
        Returns:
            Score value for this position
        """
        score = 0
        target_y, target_x = position
        
        # Base score for a valid position
        score += 20
        
        # Check if this position gets us closer to the original target
        current_distance = self.game.chess_distance(unit.y, unit.x, original_target.y, original_target.x)
        new_distance = self.game.chess_distance(target_y, target_x, original_target.y, original_target.x)
        
        if new_distance < current_distance:
            # Bonus for getting closer to target - proportional to distance reduction
            score += (current_distance - new_distance) * 5
        else:
            # Penalty for moving away from target
            score -= 10
        
        # Check if we can attack the original target after moving
        attack_range = unit.get_effective_stats()['attack_range']
        if new_distance <= attack_range:
            # Bonus for being able to attack after Expedite
            score += 25
            
        # Check for potential trap victims after Expedite
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                # Skip positions outside attack range
                if abs(dy) + abs(dx) > attack_range:
                    continue
                    
                # Skip the center position itself
                if dy == 0 and dx == 0:
                    continue
                    
                check_y = target_y + dy
                check_x = target_x + dx
                
                # Check if position is valid
                if not self.game.is_valid_position(check_y, check_x):
                    continue
                    
                # Check if there's a trappable enemy at this position
                check_unit = self.game.get_unit_at(check_y, check_x)
                if check_unit and check_unit.player != unit.player:
                    # Check if the enemy is already trapped
                    is_trapped = hasattr(check_unit, 'trapped_by') and check_unit.trapped_by is not None
                    
                    if not is_trapped:
                        # Bonus for finding an untrapped enemy nearby
                        score += 15
        
        return score
        
    def _score_expedite_enemy_hit(self, unit: 'Unit', enemy: 'Unit', skill) -> float:
        """
        Score hitting an enemy directly with Expedite.
        
        Args:
            unit: The Mandible Foreman unit
            enemy: The enemy unit that would be hit
            skill: The Expedite skill
            
        Returns:
            Score value for hitting this enemy
        """
        score = 0
        
        # Base score for a direct hit
        score += 50
        
        # Calculate expected damage
        expected_damage = max(1, skill.trap_damage - enemy.defense)
        
        # Check if the enemy is already trapped
        is_trapped = hasattr(enemy, 'trapped_by') and enemy.trapped_by is not None
        
        if not is_trapped:
            # Big bonus for trapping an untrapped enemy
            score += 30
        else:
            # Penalty for hitting an already trapped enemy
            score -= 20
            
        # Check if we can kill the enemy
        if enemy.hp <= expected_damage:
            # Huge bonus for securing a kill
            score += 50
            
        # Bonus for higher-HP targets (more value from trap damage over time)
        if enemy.hp > expected_damage:
            score += min(20, enemy.hp - expected_damage)
            
        # Check enemy's attack to prioritize dangerous enemies
        enemy_attack = enemy.get_effective_stats()['attack']
        score += enemy_attack * 3
        
        return score
    
    def _evaluate_jawline_skill(self, unit: 'Unit', target: 'Unit', skill) -> float:
        """
        Evaluate the value of using Jawline skill around the Mandible Foreman.
        This skill deploys mechanical jaws in a 3x3 area around the unit,
        dealing damage and immobilizing enemies.
        
        Args:
            unit: The Mandible Foreman unit
            target: The primary enemy target (for context, not necessarily affected)
            skill: The Jawline skill
            
        Returns:
            A score indicating the value of using this skill (higher is better)
        """
        # Check if the skill can be used
        if not skill.can_use(unit, None, self.game):
            return -1  # Can't use
            
        # Start with a base score
        score = 0
            
        # Count potentially affected enemies in the 3x3 area
        affected_enemies = 0
        # track whether the main target would be hit
        target_affected = False
        
        # Get base damage from skill
        jawline_damage = skill.damage  # 4 damage by default
            
        # Check all 8 surrounding positions (3x3 area around unit)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                # Skip the center position (unit's position)
                if dy == 0 and dx == 0:
                    continue
                    
                # Calculate position
                check_y = unit.y + dy
                check_x = unit.x + dx
                
                # Skip if position is invalid
                if not self.game.is_valid_position(check_y, check_x):
                    continue
                
                # Check for enemy at this position
                enemy = self.game.get_unit_at(check_y, check_x)
                if enemy and enemy.player != unit.player and enemy.is_alive():
                    affected_enemies += 1
                    
                    # Check if this is our main target
                    if enemy == target:
                        target_affected = True
                    
                    # Calculate damage to this enemy (factoring defense)
                    expected_damage = max(1, jawline_damage - enemy.defense)
                    
                    # Bonus if we can kill an enemy with Jawline
                    if enemy.hp <= expected_damage:
                        score += 30  # High value for securing a kill
                    
                    # Check if enemy is already immobilized (from Jawline or trapped)
                    already_immobilized = (hasattr(enemy, 'jawline_affected') and enemy.jawline_affected) or \
                                         (hasattr(enemy, 'trapped_by') and enemy.trapped_by is not None)
                    
                    if already_immobilized:
                        # Less valuable to re-immobilize, but still worth damage
                        score += 5
                    else:
                        # High value for immobilizing a new enemy
                        score += 20
                        
                        # Extra bonus for immobilizing high-movement enemies
                        enemy_move = enemy.get_effective_stats()['move_range']
                        if enemy_move >= 3:
                            score += 15  # More valuable to immobilize fast enemies
                            
                    # Prioritize dangerous enemies
                    enemy_attack = enemy.get_effective_stats()['attack']
                    score += enemy_attack * 2
        
        # Base score based on the number of affected enemies
        if affected_enemies == 0:
            return 0  # Not worth using if no enemies affected
        elif affected_enemies == 1:
            score += 15  # Base value for hitting one enemy
        elif affected_enemies == 2:
            score += 35  # Higher value for hitting two enemies
        else:  # 3 or more enemies
            score += 60 + (affected_enemies - 3) * 15  # Excellent value for 3+ enemies
            
        # Bonus if our primary target would be affected
        if target_affected:
            score += 15
            
        # Consider unit's health - more valuable when surrounded and in danger
        health_ratio = unit.hp / unit.max_hp
        if health_ratio <= 0.5 and affected_enemies >= 2:
            # When surrounded and at low health, Jawline is a good defensive move
            score += 20
            
        # Check if unit is already surrounded by enemies (higher priority to use Jawline)
        adjacent_enemy_count = sum(1 for dy in [-1, 0, 1] for dx in [-1, 0, 1] 
                                 if dy != 0 or dx != 0  # Skip center
                                 if self.game.is_valid_position(unit.y + dy, unit.x + dx)
                                 if self.game.get_unit_at(unit.y + dy, unit.x + dx) is not None
                                 and self.game.get_unit_at(unit.y + dy, unit.x + dx).player != unit.player)
        
        if adjacent_enemy_count >= 3:
            # Higher priority when already surrounded
            score += 30
            
        logger.info(f"Jawline would affect {affected_enemies} enemies with score {score}")
        return score
        
    def _evaluate_site_inspection_skill(self, unit: 'Unit', target: 'Unit', skill) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Evaluate the value of using Site Inspection skill to buff allies.
        This skill surveys a 3x3 area without obstacles, granting
        movement and attack bonuses to allies when no impassable terrain is found.
        
        Args:
            unit: The Mandible Foreman unit
            target: The primary enemy target (for context, not directly used)
            skill: The Site Inspection skill
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or (None, -1) if no valid position
        """
        # If skill is not ready yet, return no valid position
        if not skill.can_use(unit, None, self.game):
            return None, -1
            
        # Check positions in a square area around the unit (within skill range)
        best_position = None
        best_score = 0
        
        # Get ally units for targeting
        ally_units = [ally for ally in self.game.units 
                    if ally.player == unit.player and ally.is_alive() and ally != unit]
                    
        if not ally_units:
            logger.info("No ally units found for Site Inspection")
            return None, 0  # No allies to buff, not worth using
            
        # Check positions within the skill range (default range is 3)
        move_range = unit.get_effective_stats()['move_range']
        max_search_range = min(skill.range + move_range, 8)  # Limit search to reasonable area
        
        # Track best target position
        for y in range(max(0, unit.y - max_search_range), min(self.game.map.height, unit.y + max_search_range + 1)):
            for x in range(max(0, unit.x - max_search_range), min(self.game.map.width, unit.x + max_search_range + 1)):
                # Skip invalid positions
                if not self.game.is_valid_position(y, x):
                    continue
                    
                # Check if this is a position we can use Site Inspection from
                # First verify if we can move here (either we're already here or can move here)
                can_move_here = (y == unit.y and x == unit.x) or \
                               (self.game.is_valid_position(y, x) and 
                                self.game.map.is_passable(y, x) and 
                                not self.game.get_unit_at(y, x) and
                                self.game.chess_distance(unit.y, unit.x, y, x) <= move_range)
                
                if not can_move_here:
                    continue
                
                # Now check if we can use the skill from this position to a valid target
                # Site Inspection has an area of 3x3 to scan
                # We'll calculate a score for each potential target position
                
                # Search all positions within skill range from this position
                for target_y in range(max(0, y - skill.range), min(self.game.map.height, y + skill.range + 1)):
                    for target_x in range(max(0, x - skill.range), min(self.game.map.width, x + skill.range + 1)):
                        # Skip if not in range
                        if self.game.chess_distance(y, x, target_y, target_x) > skill.range:
                            continue
                            
                        # Check if skill can be used at this target position
                        if not skill.can_use(unit, (target_y, target_x), self.game):
                            continue
                            
                        # Check the 3x3 area around the target position
                        # Site Inspection only applies buffs if there's no impassable terrain
                        has_impassable = False
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                check_y, check_x = target_y + dy, target_x + dx
                                
                                # Skip out of bounds positions
                                if not self.game.is_valid_position(check_y, check_x):
                                    continue
                                
                                # Check if this position has impassable terrain
                                if not self.game.map.is_passable(check_y, check_x):
                                    has_impassable = True
                                    break
                            if has_impassable:
                                break
                                
                        # Skip positions with impassable terrain - the skill has no effect
                        if has_impassable:
                            continue
                            
                        # Calculate score for this potential inspection area
                        score = self._score_site_inspection_position(unit, (target_y, target_x), ally_units)
                        
                        # If this position is better than our current best, update
                        if score > best_score:
                            best_score = score
                            # If this is our current position, target directly
                            if y == unit.y and x == unit.x:
                                best_position = (target_y, target_x)
                            else:
                                # We'll need to move first, so remember the move position
                                # For simplicity, we'll do the move separately and target after
                                # The skill will be reconsidered after the move
                                best_position = (y, x)  # The position to move to
        
        logger.info(f"Site Inspection best position: {best_position} with score {best_score}")
        return best_position, best_score
    
    def _score_site_inspection_position(self, unit: 'Unit', position: Tuple[int, int], ally_units: List['Unit']) -> float:
        """
        Score a potential Site Inspection position based on tactical considerations.
        
        Args:
            unit: The Mandible Foreman unit
            position: The position to evaluate for Site Inspection
            ally_units: List of ally units that could potentially be buffed
            
        Returns:
            Score value for this position
        """
        score = 0
        inspect_y, inspect_x = position
        
        # Base score for a valid position
        score += 10
        
        # Count buffable allies in the 3x3 area
        buffable_allies = 0
        
        # Check the 3x3 area around the inspection position
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                check_y, check_x = inspect_y + dy, inspect_x + dx
                
                # Skip invalid positions
                if not self.game.is_valid_position(check_y, check_x):
                    continue
                
                # Check for an ally at this position
                ally = self.game.get_unit_at(check_y, check_x)
                if ally and ally.player == unit.player and ally.is_alive():
                    # Check if ally already has the buff (avoid redundancy)
                    already_buffed = hasattr(ally, 'status_site_inspection') and ally.status_site_inspection
                    
                    # Skip allies that are immune to status effects (like Grayman with Stasiality)
                    if hasattr(ally, 'is_immune_to_effects') and ally.is_immune_to_effects():
                        continue
                        
                    if not already_buffed:
                        buffable_allies += 1
                        
                        # Extra value for specific unit types
                        if ally.type == UnitType.GLAIVEMAN:
                            # Glaivemen benefit greatly from both attack and movement
                            score += 15
                        elif hasattr(ally, 'get_effective_stats'):
                            # Check ally's base stats to see who benefits most
                            ally_stats = ally.get_effective_stats()
                            # Units with high base attack benefit more from attack boost
                            if ally_stats['attack'] >= 4:
                                score += 10
                            # Units with high base movement benefit more from movement boost
                            if ally_stats['move_range'] >= 3:
                                score += 10
                    else:
                        # Small bonus for refreshing duration on already buffed allies
                        score += 5
        
        # Base score based on number of buffable allies
        if buffable_allies == 0:
            return 0  # Not worth using if no allies to buff
        elif buffable_allies == 1:
            score += 10  # Base value for buffing one ally
        elif buffable_allies == 2:
            score += 25  # Higher value for buffing two allies
        else:  # 3 or more allies
            score += 45 + (buffable_allies - 3) * 15  # Excellent value for 3+ allies
            
        # Strategic considerations - is there a nearby enemy to attack?
        enemies_nearby = False
        
        # Check for enemies within attack range of the buffed area
        search_range = 5  # Reasonable attack distance 
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                # Check if enemy is close to the inspection area
                distance = self.game.chess_distance(inspect_y, inspect_x, enemy.y, enemy.x)
                if distance <= search_range:
                    enemies_nearby = True
                    # Bonus for having enemies nearby (buffs are more useful)
                    score += 15
                    break
                    
        # If no enemies nearby, reduce the value slightly
        if not enemies_nearby:
            score -= 10
            
        return score
    
    def _find_best_target_for_foreman(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find the best target for a Mandible Foreman.
        Prioritizes enemies that are not trapped and are near other enemies.
        
        Args:
            unit: The Mandible Foreman unit
            
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
            
            # Immediate attack opportunities get high priority
            if can_attack_now:
                score += 40
            # Targets that can be reached this turn get medium priority
            elif can_reach_for_attack:
                score += 30
                
            # Check if the enemy is already trapped by this unit
            is_trapped_by_us = False
            if hasattr(enemy, 'trapped_by') and enemy.trapped_by == unit:
                is_trapped_by_us = True
                
            # Prioritize untrapped enemies
            if not is_trapped_by_us:
                score += 50
            else:
                # Lower priority for enemies we've already trapped
                score -= 20
                
            # Give priority to enemies with adjacent allies (better for Jawline skill later)
            adjacent_allies_count = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue  # Skip center
                        
                    adj_y, adj_x = enemy.y + dy, enemy.x + dx
                    if self.game.is_valid_position(adj_y, adj_x):
                        adj_unit = self.game.get_unit_at(adj_y, adj_x)
                        if adj_unit and adj_unit.player == enemy.player and adj_unit != enemy:
                            adjacent_allies_count += 1
            
            # Bonus for each adjacent ally
            score += adjacent_allies_count * 10
                
            # Prioritize lower health enemies (but not if they're too far)
            if can_reach_for_attack or distance < 10:
                # Invert HP to give higher scores to lower-HP enemies
                hp_factor = 100 - enemy.hp
                score += hp_factor * 0.3
                
            # Prioritize dangerous enemies (high attack power)
            enemy_stats = enemy.get_effective_stats()
            enemy_attack = enemy_stats['attack']
            score += enemy_attack * 0.3
            
            # Distance penalty (further targets get lower scores)
            score -= distance * 1.5
            
            scored_enemies.append((enemy, score))
        
        # Get the enemy with the highest score
        if scored_enemies:
            # Log the top three targets for debugging
            scored_enemies.sort(key=lambda x: x[1], reverse=True)
            for i, (enemy, score) in enumerate(scored_enemies[:3]):
                if i == 0:
                    logger.debug(f"Best target for {unit.get_display_name()}: {enemy.get_display_name()} (score: {score})")
                else:
                    logger.debug(f"Alternative target #{i+1}: {enemy.get_display_name()} (score: {score})")
            
            return scored_enemies[0][0]
            
        # Fallback to nearest enemy if scoring fails
        return self._find_nearest_enemy(unit)
    
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
                hp_factor = 100 - enemy.hp
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
            # Log the top three targets for debugging
            scored_enemies.sort(key=lambda x: x[1], reverse=True)
            for i, (enemy, score) in enumerate(scored_enemies[:3]):
                if i == 0:
                    logger.debug(f"Best target for {unit.get_display_name()}: {enemy.get_display_name()} (score: {score})")
                else:
                    logger.debug(f"Alternative target #{i+1}: {enemy.get_display_name()} (score: {score})")
            
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
            
        # Find the best position to move to
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