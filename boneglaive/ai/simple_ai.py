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
                try:
                    # On HARD difficulty, temporarily use the medium difficulty targeting
                    # This bypasses group coordination that may be causing issues
                    logger.info("Using simplified targeting for HARD mode (temporary fix)")
                    self._ensure_all_units_have_targets(ai_units)
                except Exception as e:
                    logger.error(f"Error in targeting: {e}")
                    # If there's an error in targeting, just continue without coordination
            
            # On HARD difficulty, sort units to process the most tactical ones first
            if self.difficulty == AIDifficulty.HARD:
                try:
                    # Sort units by their tactical advantage (units with attack opportunities go first)
                    logger.info("Sorting AI units by tactical priority")
                    ai_units = self._sort_units_by_tactical_priority(ai_units)
                except Exception as e:
                    logger.error(f"Error sorting units: {e}")
                    # Continue with unsorted units if there's an error
                
            # Process units one at a time
            units_processed = 0
            for unit in ai_units:
                try:
                    logger.info(f"AI processing unit: {unit.get_display_name()}")
                    self._process_unit(unit)
                    units_processed += 1
                    
                    # Update the UI after each unit action
                    if self.ui:
                        self.ui.draw_board()
                except Exception as e:
                    import traceback
                    logger.error(f"Error processing unit {unit.get_display_name()}: {e}")
                    logger.error(traceback.format_exc())
                    # Continue with next unit if there's an error
                    
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
            # Check if position is in bounds and not blocked
            if (0 <= y < self.game.map.height and 
                0 <= x < self.game.map.width and 
                self.game.map.can_place_unit(y, x) and
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
        elif unit.type == UnitType.GRAYMAN:
            self._process_grayman(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.MARROW_CONDENSER:
            self._process_marrow_condenser(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.FOWL_CONTRIVANCE:
            self._process_fowl_contrivance(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.GAS_MACHINIST:
            self._process_gas_machinist(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.HEINOUS_VAPOR:
            self._process_heinous_vapor(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.DELPHIC_APPRAISER:
            self._process_delphic_appraiser(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
        elif unit.type == UnitType.DERELICTIONIST:
            self._process_derelictionist(unit, use_coordination=self.difficulty == AIDifficulty.HARD)
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
        
        # Clear skill indicators
        if hasattr(unit, 'marrow_dike_indicator'):
            unit.marrow_dike_indicator = None
        
        # Check if unit is trapped - trapped units can only attack, not move or use skills
        is_trapped = hasattr(unit, 'trapped_by') and unit.trapped_by is not None
        
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
            # Check if unit is trapped - trapped units cannot use skills, only attacks
            if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
                logger.info(f"{unit.get_display_name()} cannot use skills because it is trapped")
                return None
                
            if not available_skills:
                logger.info("No skills available for this Glaiveman")
                return None
                
            # Debug available skills with cooldown information
            logger_msg = "Evaluating skills: "
            for skill in available_skills:
                logger_msg += f"{skill.name} (CD: {skill.current_cooldown}/{skill.cooldown}), "
            logger.info(logger_msg.rstrip(", "))
            
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
            # Check if unit is trapped - trapped units cannot use skills, only attacks
            if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
                logger.info(f"{unit.get_display_name()} cannot use skills because it is trapped")
                return None
                
            if not available_skills:
                logger.info("No skills available for this Mandible Foreman")
                return None
                
            # Debug available skills with cooldown information
            logger_msg = "Evaluating skills: "
            for skill in available_skills:
                logger_msg += f"{skill.name} (CD: {skill.current_cooldown}/{skill.cooldown}), "
            logger.info(logger_msg.rstrip(", "))
            
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
    
    def _process_marrow_condenser(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a Marrow Condenser unit.
        Implements tactical skill usage focusing on area denial, defense, and HP sustain.
        
        Args:
            unit: The Marrow Condenser unit to process
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
                target = self._find_best_target_for_marrow_condenser(unit)
            
        if not target:
            logger.info("No enemies found for Marrow Condenser to target")
            return
            
        logger.info(f"Marrow Condenser targeting enemy: {target.get_display_name()} at position ({target.y}, {target.x})")
        
        # Get available skills 
        available_skills = []
        try:
            available_skills = unit.get_available_skills()
            logger.info(f"Marrow Condenser has {len(available_skills)} skills available: {[skill.name for skill in available_skills]}")
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            
        # Flag to track if we used a skill
        used_skill = None
        
        # Check if Marrow Condenser is at low health for defensive priority
        health_percent = unit.hp / unit.max_hp
        is_low_health = health_percent <= 0.4  # 40% health threshold
        
        # Check for enemies in melee range (immediate threat)
        enemies_in_melee = self._count_enemies_in_range(unit, 1)
        
        # Check if unit is trapped - trapped units can only attack, not use skills
        is_trapped = hasattr(unit, 'trapped_by') and unit.trapped_by is not None
        
        if is_trapped:
            logger.info(f"MARROW_CONDENSER {unit.get_display_name()} is trapped - can only attack")
            used_skill = None
        # Skip skill usage on EASY difficulty less often (reduced probability)
        elif self.difficulty == AIDifficulty.EASY and random.random() < 0.3:  # 30% chance to skip
            logger.info("EASY difficulty: Skipping skill usage")
            used_skill = None
        else:
            # On MEDIUM or HARD, always use skills if possible
            try:
                used_skill = self._use_marrow_condenser_skills(unit, target, available_skills, is_low_health, enemies_in_melee)
                if used_skill:
                    logger.info(f"Marrow Condenser used {used_skill.name} skill")
                    # Don't return - we'll let the method complete even if a skill was used
                    # This ensures that units always take some action
            except Exception as e:
                logger.error(f"Error using Marrow Condenser skills: {e}")
                import traceback
                logger.error(traceback.format_exc())
                used_skill = None
        
        # Only proceed with move/attack if no skill was used
        if not used_skill:
            # Check if we can attack the enemy from our current position
            can_attack = self._can_attack(unit, target)
            
            if can_attack:
                # We can attack from current position
                unit.attack_target = (target.y, target.x)
                logger.info(f"Marrow Condenser attacking enemy from current position")
            else:
                # Move towards enemy or strategic position
                logger.info(f"Marrow Condenser moving towards enemy")
                
                # If using coordination, consider planned positions
                if use_coordination:
                    self._move_with_coordination(unit, target)
                else:
                    self._move_towards_enemy(unit, target)
                
                # Check if we can attack after moving
                can_attack_after_move = self._can_attack_after_move(unit, target)
                if can_attack_after_move:
                    logger.info(f"Marrow Condenser attacking enemy after movement")
                    # The attack_target is set in _can_attack_after_move
    
    def _process_fowl_contrivance(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a FOWL_CONTRIVANCE unit.
        Implements intelligent rail artillery tactics with emphasis on Gaussian Dusk
        targeting of immobilized or predictable enemies.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # If fowl contrivance has charging status, use gaussian dusk skill again
        if hasattr(unit, 'charging_status') and unit.charging_status:
            logger.info(f"{unit.get_display_name()} has charging status - using Gaussian Dusk skill")
            
            # Find Gaussian Dusk skill
            gaussian_dusk_skill = None
            for skill in unit.skills:
                if hasattr(skill, 'name') and skill.name == "Gaussian Dusk":
                    gaussian_dusk_skill = skill
                    break
            
            if gaussian_dusk_skill:
                # Use the Gaussian Dusk skill again
                result = gaussian_dusk_skill.use(unit, None, self.game)
                logger.info(f"FOWL_CONTRIVANCE gaussian_dusk_skill.use() returned: {result}")
                logger.info(f"FOWL_CONTRIVANCE targets after use(): skill_target={unit.skill_target}, selected_skill={unit.selected_skill.name if unit.selected_skill else None}")
                if result:
                    logger.info(f"FOWL_CONTRIVANCE successfully set up firing - RETURNING EARLY")
                    return
                else:
                    logger.error(f"FOWL_CONTRIVANCE gaussian_dusk_skill.use() returned False while charging!")
            
            logger.error("Could not use Gaussian Dusk skill while charging")
            return
        
        # Reset move and attack targets only when NOT charging (charging units need to preserve targets)
        # SAFETY CHECK: Never clear targets if unit is charging
        if not (hasattr(unit, 'charging_status') and unit.charging_status):
            unit.move_target = None
            unit.attack_target = None
            unit.skill_target = None
            unit.selected_skill = None
        
        # Get a target based on the difficulty level or coordination
        target = None
        
        # If using coordination and this unit has an assigned target, use it
        if use_coordination and unit.id in self.target_assignments:
            target_id = self.target_assignments[unit.id]
            for player_unit in self.game.units:
                if player_unit.id == target_id and player_unit.is_alive():
                    target = player_unit
                    logger.info(f"Using coordinated target for {unit.get_display_name()}: {target.get_display_name()}")
                    break
        
        # If no coordinated target was found, find the best target for Gaussian Dusk
        if not target:
            if self.difficulty == AIDifficulty.EASY:
                target = self._find_random_enemy(unit)
            elif self.difficulty == AIDifficulty.MEDIUM:
                target = self._find_nearest_enemy(unit)
            else:  # HARD difficulty
                target = self._find_best_gaussian_dusk_target(unit)
            
        if not target:
            logger.info("No enemies found for FOWL_CONTRIVANCE to target")
            return
            
        logger.info(f"FOWL_CONTRIVANCE targeting enemy: {target.get_display_name()} at position ({target.y}, {target.x})")
        
        # Get available skills 
        available_skills = []
        try:
            available_skills = unit.get_available_skills()
            logger.info(f"FOWL_CONTRIVANCE has {len(available_skills)} skills available: {[skill.name for skill in available_skills]}")
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            
        # Check if unit is trapped - trapped units can only attack, not use skills
        is_trapped = hasattr(unit, 'trapped_by') and unit.trapped_by is not None
        
        # Try to use Gaussian Dusk if available and we have a good line of sight
        used_skill = None
        if is_trapped:
            logger.info(f"FOWL_CONTRIVANCE {unit.get_display_name()} is trapped - can only attack")
        elif self.difficulty == AIDifficulty.EASY and random.random() < 0.4:  # 40% chance to skip on easy
            logger.info("EASY difficulty: Skipping skill usage")
        else:
            try:
                used_skill = self._use_fowl_contrivance_skills(unit, target, available_skills)
                if used_skill:
                    logger.info(f"FOWL_CONTRIVANCE used {used_skill.name} skill")
                    return  # Don't move if we used a skill
            except Exception as e:
                logger.error(f"Error using FOWL_CONTRIVANCE skills: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # If no skill was used, try to move to a better position for next turn
        # Move to a position with good rail access or line of sight
        best_position = self._find_best_artillery_position(unit, target)
        if best_position:
            unit.move_target = best_position
            logger.info(f"FOWL_CONTRIVANCE moving to artillery position {best_position}")
        else:
            # Fallback to basic attack if in range
            distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
            if distance <= unit.attack_range:
                unit.attack_target = (target.y, target.x)
                logger.info(f"FOWL_CONTRIVANCE attacking with basic attack")

    def _process_grayman(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a Grayman unit.
        Implements intelligent skill usage focusing on teleportation, phasing, and echo creation.
        
        Args:
            unit: The Grayman unit to process
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
                target = self._find_best_target_for_grayman(unit)
            
        if not target:
            logger.info("No enemies found for Grayman to target")
            return
            
        logger.info(f"Grayman targeting enemy: {target.get_display_name()} at position ({target.y}, {target.x})")
        
        # Get available skills 
        available_skills = []
        try:
            available_skills = unit.get_available_skills()
            logger.info(f"Grayman has {len(available_skills)} skills available: {[skill.name for skill in available_skills]}")
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            
        # Flag to track if we used a skill
        used_skill = None
        
        # Check if the Grayman is at critically low health
        health_percent = unit.hp / unit.max_hp
        is_critical_health = health_percent <= 0.25  # 25% health threshold for critical
        
        # Check if Grayman is already in a safe position (no enemies within attack range)
        is_in_safe_position = self._is_grayman_in_safe_position(unit)
        
        # If at critical health AND not already safe, ONLY consider escape skills and avoid combat completely
        if is_critical_health and not is_in_safe_position:
            logger.info(f"CRITICAL HEALTH ({unit.hp}/{unit.max_hp}): Grayman prioritizing escape")
            
            # Debug: Check if teleport skills exist in unit.active_skills
            teleport_skill_names = [s.name for s in unit.active_skills if s.name in ["Delta Config", "Græ Exchange"]]
            logger.info(f"DEBUG: Grayman has teleport skills in unit.active_skills: {teleport_skill_names}")
            
            try:
                # Check for available teleport skills (respecting cooldowns)
                teleport_skills = [s for s in available_skills if s.name in ["Delta Config", "Græ Exchange"]]
                logger.info(f"DEBUG: Available teleport skills: {[s.name for s in teleport_skills]}")
                
                if teleport_skills:
                    # Special emergency escape mode - only evaluate teleport skills
                    used_skill = self._use_grayman_emergency_teleport(unit, target, teleport_skills)
                    
                    if used_skill:
                        logger.info(f"Grayman used EMERGENCY {used_skill.name} teleport at critical health")
                        # Return immediately - do NOT attempt to attack when at critical health
                        return
                    else:
                        logger.warning(f"Failed to find escape option for Grayman at critical health!")
                else:
                    logger.info("DEBUG: No teleport skills available for emergency escape (may be on cooldown)")
                    
            except Exception as e:
                logger.error(f"Error using Grayman emergency teleport: {e}")
                import traceback
                logger.error(traceback.format_exc())
        # If at critical health but already safe, just heal/wait instead of teleporting
        elif is_critical_health and is_in_safe_position:
            logger.info(f"CRITICAL HEALTH but SAFE: Grayman will wait/heal instead of teleporting")
            # Don't use any offensive skills, just let the unit rest
            return
        
        # Normal skill usage for non-critical health
        else:
            # Skip skill usage on EASY difficulty less often (reduced probability)
            if self.difficulty == AIDifficulty.EASY and random.random() < 0.4:  # Reduced from 0.7
                logger.info("EASY difficulty: Skipping skill usage")
            else:
                # On MEDIUM or HARD, always use skills if possible
                try:
                    used_skill = self._use_grayman_skills(unit, target, available_skills)
                    if used_skill:
                        logger.info(f"Grayman used {used_skill.name} skill")
                        # Don't return - we'll let the method complete even if a skill was used
                        # This ensures that units always take some action
                except Exception as e:
                    logger.error(f"Error using Grayman skills: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    used_skill = None
        
        # Only proceed with move/attack if no skill was used AND not at critical health
        if not used_skill:
            # If at critical health and not safe and we couldn't teleport, at least try to move away from enemies
            if is_critical_health and not is_in_safe_position:
                logger.info(f"Critical health: Grayman attempting to retreat")
                retreat_result = self._retreat_from_enemies(unit)
                
                # Even if retreat failed, ensure we don't continue with attacks
                # This prevents the unit from standing still at critical health
                if not retreat_result:
                    logger.warning("Retreat failed, setting dummy move to current position to prevent freezing")
                    # Set a dummy move to current position to ensure the unit doesn't freeze
                    unit.move_target = (unit.y, unit.x)
                    
                # Always return for critical health - NEVER attempt to attack
                return
                
            # If we didn't use a skill and not at critical health, proceed with normal attack or movement
            # Check if we can attack the enemy from our current position
            can_attack = self._can_attack(unit, target)
            
            # If we can attack, do it
            if can_attack:
                logger.info(f"Grayman attacking enemy at ({target.y}, {target.x})")
                unit.attack_target = (target.y, target.x)
            # If we can't attack, try to move closer
            else:
                # EASY difficulty has a small chance to skip movement (reduced probability)
                if self.difficulty == AIDifficulty.EASY and random.random() < 0.1:  # Reduced from 0.3
                    logger.info("EASY difficulty: Grayman decided not to move this turn")
                    return
                    
                logger.info(f"Grayman moving towards enemy at ({target.y}, {target.x})")
                
                # If using coordination, consider planned positions
                if use_coordination:
                    self._move_with_coordination(unit, target)
                else:
                    self._move_towards_enemy(unit, target)
                
                # Check if we can attack after moving
                can_attack_after_move = self._can_attack_after_move(unit, target)
                if can_attack_after_move:
                    logger.info(f"Grayman attacking enemy after movement")
                    # The attack_target is set in _can_attack_after_move
    
    def _is_grayman_in_safe_position(self, unit: 'Unit') -> bool:
        """
        Check if Grayman is in a safe position (no enemies within attack range).
        
        Args:
            unit: The Grayman unit to check
            
        Returns:
            True if Grayman is safe from immediate attacks, False otherwise
        """
        # Count nearby enemies that can attack this position
        enemies_in_range = 0
        
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                # Calculate distance from enemy to unit
                distance = self.game.chess_distance(enemy.y, enemy.x, unit.y, unit.x)
                
                # Get enemy's effective attack range (including movement)
                enemy_stats = enemy.get_effective_stats()
                total_enemy_range = enemy_stats['move_range'] + enemy_stats['attack_range']
                
                # If enemy can reach and attack Grayman, it's not safe
                if distance <= total_enemy_range:
                    enemies_in_range += 1
        
        # Consider safe if no enemies can attack, or at most 1 enemy nearby with good health
        if enemies_in_range == 0:
            logger.info(f"Grayman is SAFE: No enemies in attack range")
            return True
        elif enemies_in_range == 1 and unit.hp > unit.max_hp * 0.4:  # 40% health threshold
            logger.info(f"Grayman is RELATIVELY SAFE: Only 1 enemy in range and health > 40%")
            return True
        else:
            logger.info(f"Grayman is NOT SAFE: {enemies_in_range} enemies in attack range")
            return False
    
    def _use_grayman_emergency_teleport(self, unit: 'Unit', target: 'Unit', teleport_skills: list) -> Optional['ActiveSkill']:
        """
        Special emergency teleport function for Grayman at critical health.
        Focuses ONLY on finding the safest position to teleport to, ignoring offensive considerations.
        
        Args:
            unit: The Grayman unit at critical health
            target: The current enemy target (not used for targeting, just for API compatibility)
            teleport_skills: List of available teleport skills (Delta Config, Grae Exchange)
            
        Returns:
            The skill that was used for emergency teleport, or None if no teleport was possible
        """
        logger.info(f"Evaluating emergency teleport options for Grayman at {unit.hp}/{unit.max_hp} HP")
        
        best_teleport_option = None
        best_teleport_score = -1
        best_teleport_pos = None
        
        # Process each teleport skill
        for skill in teleport_skills:
            if skill.name == "Delta Config":
                # For Delta Config, check EVERY position on the map for safety
                teleport_pos, score = self._evaluate_emergency_delta_config(unit)
                if teleport_pos and score > best_teleport_score:
                    best_teleport_score = score
                    best_teleport_option = skill
                    best_teleport_pos = teleport_pos
                    
            elif skill.name == "Græ Exchange":
                # For Grae Exchange, check positions within range
                teleport_pos, score = self._evaluate_emergency_grae_exchange(unit)
                if teleport_pos and score > best_teleport_score:
                    best_teleport_score = score
                    best_teleport_option = skill
                    best_teleport_pos = teleport_pos
        
        # Report what we found
        logger.info(f"DEBUG: Best teleport option found: {best_teleport_option.name if best_teleport_option else 'None'}")
        logger.info(f"DEBUG: Best teleport score: {best_teleport_score}")
        logger.info(f"DEBUG: Best teleport position: {best_teleport_pos}")
        
        # If we found a good teleport option, use it (lower the required score threshold)
        if best_teleport_option and best_teleport_score > -10 and best_teleport_pos:  # Accept any non-terrible score
            logger.info(f"Using EMERGENCY teleport to {best_teleport_pos} with score {best_teleport_score}")
            
            # Try to use the skill
            try:
                success = best_teleport_option.use(unit, best_teleport_pos, self.game)
                logger.info(f"DEBUG: Emergency teleport use result: {success}")
                
                if success:
                    return best_teleport_option
                else:
                    logger.warning(f"DEBUG: Failed to use {best_teleport_option.name} at position {best_teleport_pos}")
            except Exception as e:
                logger.error(f"ERROR using emergency teleport: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return None
        
    def _evaluate_emergency_delta_config(self, unit: 'Unit') -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Emergency evaluation of Delta Config for escaping when at critical health.
        Finds the safest position on the map to teleport to.
        
        Args:
            unit: The Grayman unit at critical health
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or (None, -1) if no valid position
        """
        # Get the Delta Config skill
        delta_config = None
        for skill in unit.active_skills:
            if skill.name == "Delta Config":
                delta_config = skill
                break
        
        logger.info(f"DEBUG: Emergency Delta Config eval - found skill: {delta_config is not None}")
        
        if not delta_config:
            logger.warning("DEBUG: No Delta Config skill found in unit.active_skills")
            return None, -1
            
        if not delta_config.can_use(unit, None, self.game):
            logger.warning(f"DEBUG: Delta Config not usable, cooldown: {delta_config.current_cooldown}")
            return None, -1
            
        logger.info("DEBUG: Delta Config is available and usable for emergency teleport")
            
        # Find the safest position on the map
        best_position = None
        best_score = 0
        
        # Check all positions on the map (limiting to a reasonable search area)
        search_distance = 15  # Extend search distance for emergency teleport
        
        # Starting position is unit's current position
        start_y, start_x = unit.y, unit.x
        
        # Check positions in expanding rings around the unit
        for distance in range(1, search_distance + 1):
            for y in range(max(0, start_y - distance), min(self.game.map.height, start_y + distance + 1)):
                for x in range(max(0, start_x - distance), min(self.game.map.width, start_x + distance + 1)):
                    # Only check positions at approximately the current distance
                    if abs(y - start_y) != distance and abs(x - start_x) != distance:
                        continue
                        
                    # Skip if not a valid teleport target
                    if not delta_config.can_use(unit, (y, x), self.game):
                        continue
                        
                    # Calculate safety score for this position - ONLY care about safety
                    score = self._calculate_position_safety(unit, y, x)
                    
                    logger.debug(f"DEBUG: Evaluating position ({y}, {x}) for Delta Config - safety score: {score}")
                    
                    # If this is safer than our current best, update
                    if score > best_score:
                        best_score = score
                        best_position = (y, x)
                        logger.info(f"DEBUG: New best Delta Config position: ({y}, {x}) with score {score}")
                        
                        # If we found a perfectly safe position, return it immediately
                        if score >= 100:
                            logger.info(f"Found perfect safety position at ({y}, {x}) with score {score}")
                            return best_position, best_score
        
        return best_position, best_score
    
    def _evaluate_emergency_grae_exchange(self, unit: 'Unit') -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Emergency evaluation of Grae Exchange for escaping when at critical health.
        Finds the safest position within range to teleport to.
        
        Args:
            unit: The Grayman unit at critical health
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or (None, -1) if no valid position
        """
        # Get the Grae Exchange skill
        grae_exchange = None
        for skill in unit.active_skills:
            if skill.name == "Græ Exchange":
                grae_exchange = skill
                break
                
        if not grae_exchange or not grae_exchange.can_use(unit, None, self.game):
            return None, -1
            
        # Find the safest position within range
        best_position = None
        best_score = 0
        
        # Check potential teleport positions within skill range
        for y in range(max(0, unit.y - grae_exchange.range), min(self.game.map.height, unit.y + grae_exchange.range + 1)):
            for x in range(max(0, unit.x - grae_exchange.range), min(self.game.map.width, unit.x + grae_exchange.range + 1)):
                # Skip if not a valid teleport target
                if not grae_exchange.can_use(unit, (y, x), self.game):
                    continue
                    
                # Skip current position
                if (y, x) == (unit.y, unit.x):
                    continue
                    
                # Calculate safety score for this position - ONLY care about safety
                score = self._calculate_position_safety(unit, y, x)
                
                # Echo value at current position (only small consideration)
                echo_value = 0
                
                # Check if there are enemies in attack range from current position for echo value
                for enemy in self.game.units:
                    if enemy.player != unit.player and enemy.is_alive():
                        distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
                        attack_range = unit.get_effective_stats()['attack_range']
                        if distance <= attack_range:
                            echo_value += 5  # Small bonus, safety is primary concern
                
                # Add echo value to score (with lower weight than safety)
                score += echo_value * 0.2
                
                # If this is safer than our current best, update
                if score > best_score:
                    best_score = score
                    best_position = (y, x)
                    
                    # If we found a perfectly safe position, return it immediately
                    if score >= 100:
                        logger.info(f"Found perfect safety position for Grae Exchange at ({y}, {x}) with score {score}")
                        return best_position, best_score
        
        return best_position, best_score
    
    def _calculate_position_safety(self, unit: 'Unit', y: int, x: int) -> float:
        """
        Calculate how safe a position is for a unit at critical health.
        Higher scores indicate safer positions.
        
        Args:
            unit: The unit to calculate safety for
            y, x: The position to evaluate
            
        Returns:
            Safety score (higher is safer)
        """
        # Start with base safety score
        safety_score = 50
        
        # Track distance to closest enemy
        closest_enemy_distance = float('inf')
        enemies_that_can_reach = 0
        
        # Check safety against all enemy units
        enemy_count = 0
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                enemy_count += 1
                # Calculate distance to this enemy
                distance = self.game.chess_distance(y, x, enemy.y, enemy.x)
                closest_enemy_distance = min(closest_enemy_distance, distance)
                
                # Check if enemy can potentially reach this position next turn
                enemy_stats = enemy.get_effective_stats()
                enemy_reach = enemy_stats['move_range'] + enemy_stats['attack_range']
                
                if distance <= enemy_reach:
                    enemies_that_can_reach += 1
                    # Large penalty for each enemy that can reach
                    safety_score -= 40
        
        # Log enemy assessment
        if enemy_count > 0:
            logger.debug(f"DEBUG: Position ({y},{x}) - closest enemy: {closest_enemy_distance}, enemies that can reach: {enemies_that_can_reach}")
        
        # If no enemies can reach, huge safety bonus
        if enemies_that_can_reach == 0:
            safety_score += 50
            
            # Extra bonus for being far from any enemies
            if closest_enemy_distance < float('inf'):
                distance_bonus = min(closest_enemy_distance * 4, 40)
                safety_score += distance_bonus
                logger.debug(f"DEBUG: Position ({y},{x}) - adding distance bonus: {distance_bonus}")
                
        # If position is completely unsafe, ensure negative score
        if enemies_that_can_reach >= 2:
            safety_score = -10
            
        logger.debug(f"DEBUG: Position ({y},{x}) final safety score: {safety_score}")
        return safety_score
        
    def _retreat_from_enemies(self, unit: 'Unit') -> bool:
        """
        Make a unit retreat from enemies when at critical health.
        Tries to move to the safest position within move range.
        
        Args:
            unit: The unit that needs to retreat
            
        Returns:
            True if a retreat move was set, False otherwise
        """
        logger.info(f"DEBUG: Retreat from enemies for {unit.get_display_name()} at position ({unit.y}, {unit.x})")
        
        # Get unit's effective move range
        stats = unit.get_effective_stats()
        move_range = stats['move_range']
        
        # If unit can't move, can't retreat
        if move_range <= 0:
            logger.warning(f"Unit {unit.get_display_name()} cannot move (move_range = {move_range})")
            return False
            
        # Check if unit is trapped - trapped units cannot move
        if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
            logger.warning(f"{unit.get_display_name()} cannot retreat because it is trapped")
            return False
            
        # Get all enemy positions for distance calculation
        enemy_positions = []
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                enemy_positions.append((enemy.y, enemy.x))
                
        # No enemies, no need to retreat
        if not enemy_positions:
            logger.info("No enemies found, no need to retreat")
            return False
            
        # Find all positions we can move to within move range
        reachable_positions = []
        
        # Check all positions within move range
        for y in range(max(0, unit.y - move_range), min(self.game.map.height, unit.y + move_range + 1)):
            for x in range(max(0, unit.x - move_range), min(self.game.map.width, unit.x + move_range + 1)):
                # Skip current position
                if (y, x) == (unit.y, unit.x):
                    continue
                    
                # Check if position is valid and passable
                if not self.game.is_valid_position(y, x) or not self.game.map.is_passable(y, x):
                    continue
                    
                # Check if position is occupied
                if self.game.get_unit_at(y, x):
                    continue
                    
                # Check if within move range (chess distance)
                distance = self.game.chess_distance(unit.y, unit.x, y, x)
                if distance > move_range:
                    continue
                
                # For non-adjacent moves, validate path to ensure no units or impassable terrain blocks the way
                if distance > 1:
                    # Import necessary path checking utilities
                    from boneglaive.utils.coordinates import Position, get_line
                    
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
                
                # Calculate safety score for this position
                safety_score = self._calculate_position_safety(unit, y, x)
                
                # Calculate minimum distance to any enemy
                min_enemy_distance = float('inf')
                for enemy_y, enemy_x in enemy_positions:
                    enemy_distance = self.game.chess_distance(y, x, enemy_y, enemy_x)
                    min_enemy_distance = min(min_enemy_distance, enemy_distance)
                
                # Add position to reachable positions with its safety score and enemy distance
                reachable_positions.append((y, x, safety_score, min_enemy_distance))
                logger.info(f"DEBUG: Found valid retreat position at ({y}, {x}) with safety {safety_score}, enemy distance {min_enemy_distance}")
        
        # If no reachable positions, can't retreat
        if not reachable_positions:
            logger.warning(f"No valid positions to retreat to for {unit.get_display_name()}")
            return False
        
        # Sort by safety score first (descending), then by enemy distance (descending)
        reachable_positions.sort(key=lambda x: (x[2], x[3]), reverse=True)
        
        # Log the top retreat options
        for i, (y, x, safety, distance) in enumerate(reachable_positions[:3]):
            logger.info(f"Retreat option {i+1}: ({y}, {x}) with safety {safety}, enemy distance {distance}")
        
        # Move to the best position
        best_y, best_x, best_safety, best_distance = reachable_positions[0]
        unit.move_target = (best_y, best_x)
        logger.info(f"Retreating to position ({best_y}, {best_x}) with safety {best_safety}, enemy distance {best_distance}")
        return True
    
    def _use_grayman_skills(self, unit: 'Unit', target: 'Unit', available_skills: list) -> Optional['ActiveSkill']:
        """
        Intelligently use Grayman skills based on the current situation.
        
        Args:
            unit: The Grayman unit
            target: The enemy target
            available_skills: List of available active skills
            
        Returns:
            The skill that was used, or None if no skill was used
        """
        try:
            # Check if unit is trapped - trapped units cannot use skills, only attacks
            if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
                logger.info(f"{unit.get_display_name()} cannot use skills because it is trapped")
                return None
                
            if not available_skills:
                logger.info("No skills available for this Grayman")
                return None
                
            # Debug available skills with cooldown information
            logger_msg = "Evaluating skills: "
            for skill in available_skills:
                logger_msg += f"{skill.name} (CD: {skill.current_cooldown}/{skill.cooldown}), "
            logger.info(logger_msg.rstrip(", "))
            
            # Evaluate each skill's potential value
            skill_scores = []
            
            for skill in available_skills:
                # Use different evaluation based on skill type
                try:
                    if skill.name == "Delta Config":
                        best_pos, score = self._evaluate_delta_config_skill(unit, target, skill)
                        if best_pos and score > 0:
                            skill_scores.append((skill, score, best_pos))
                    elif skill.name == "Estrange":
                        score = self._evaluate_estrange_skill(unit, target, skill)
                        if score > 0 and skill.can_use(unit, (target.y, target.x), self.game):
                            skill_scores.append((skill, score, (target.y, target.x)))
                    elif skill.name == "Græ Exchange":
                        best_pos, score = self._evaluate_grae_exchange_skill(unit, target, skill)
                        if best_pos and score > 0:
                            skill_scores.append((skill, score, best_pos))
                except Exception as e:
                    logger.error(f"Error evaluating skill {skill.name}: {e}")
                    continue
            
            # Debug skill scores
            logger.info(f"Skill scores: {[(s[0].name, s[1]) for s in skill_scores]}")
            
            # Sort by score (highest first)
            skill_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Check if Grayman is at low health for emergency teleport threshold
            emergency_teleport = False
            if unit.type == UnitType.GRAYMAN and unit.hp / unit.max_hp <= 0.4:
                emergency_teleport = True
                logger.info(f"EMERGENCY TELEPORT mode active for Grayman at {unit.hp}/{unit.max_hp} HP")
            
            # Use the highest scoring skill if score is above threshold
            # In emergency situations for Grayman, use an even lower threshold
            threshold = 10 if emergency_teleport else 15  # Use lower threshold for emergency teleport
            if skill_scores and skill_scores[0][1] >= threshold:
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
            logger.error(f"Error in _use_grayman_skills: {e}")
            logger.error(traceback.format_exc())
            return None
            
    def _evaluate_delta_config_skill(self, unit: 'Unit', target: 'Unit', skill) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Evaluate the value of using Delta Config skill to teleport to a strategic position.
        Finds the best position to teleport to and returns its score.
        
        Args:
            unit: The Grayman unit
            target: The enemy target
            skill: The Delta Config skill
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or (None, -1) if no valid position
        """
        # If skill is not ready yet, return no valid position
        if not skill.can_use(unit, None, self.game):
            # Debug why the skill can't be used
            logger.debug(f"Delta Config not usable by {unit.get_display_name()}, cooldown: {skill.current_cooldown}")
            return None, -1
            
        # Get effective stats including attack range
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        
        # Check all positions on the map (since Delta Config can teleport anywhere)
        best_position = None
        best_score = 0
        
        # Get current health percentage
        health_percent = unit.hp / unit.max_hp
        
        # Define search range - limit search area to be more efficient 
        search_distance = 10  # Reasonable distance around target and unit
        
        # Get positions to check around both unit and target
        positions_to_check = set()
        
        # Add positions around the target to check
        for y in range(max(0, target.y - search_distance), min(self.game.map.height, target.y + search_distance + 1)):
            for x in range(max(0, target.x - search_distance), min(self.game.map.width, target.x + search_distance + 1)):
                positions_to_check.add((y, x))
        
        # Add positions around current unit position to check
        for y in range(max(0, unit.y - search_distance), min(self.game.map.height, unit.y + search_distance + 1)):
            for x in range(max(0, unit.x - search_distance), min(self.game.map.width, unit.x + search_distance + 1)):
                positions_to_check.add((y, x))
        
        # Also look at other player units as potential targets
        for other_unit in self.game.units:
            if other_unit.player != unit.player and other_unit.is_alive() and other_unit != target:
                # Add positions around other potential targets
                for y in range(max(0, other_unit.y - 3), min(self.game.map.height, other_unit.y + 4)):
                    for x in range(max(0, other_unit.x - 3), min(self.game.map.width, other_unit.x + 4)):
                        positions_to_check.add((y, x))
        
        # Check all the potential positions for teleportation
        for pos in positions_to_check:
            y, x = pos
            
            # Skip if not a valid teleport target
            if not skill.can_use(unit, (y, x), self.game):
                continue
                
            # Calculate score for this position
            score = 0
            
            # Avoid current position (no benefit to teleporting to where we already are)
            if (y, x) == (unit.y, unit.x):
                continue
                
            # Base score for a valid position - increased to encourage Delta Config usage
            score += 20  # Increased from 10
            
            # Score based on health - STRONGLY prioritize escape at low health (emergency teleport)
            if health_percent <= 0.4:  # Increased threshold from 0.3 to 0.4 (40% health)
                # For low health, prioritize positions far from any enemies
                safe_position = True
                closest_enemy_distance = float('inf')
                enemies_that_can_reach = 0
                
                # Calculate current danger level at existing position
                current_danger_level = 0
                for enemy in self.game.units:
                    if enemy.player != unit.player and enemy.is_alive():
                        # Check enemy reach to current position
                        current_distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
                        enemy_stats = enemy.get_effective_stats()
                        enemy_reach = enemy_stats['move_range'] + enemy_stats['attack_range']
                        if current_distance <= enemy_reach:
                            current_danger_level += 1
                
                # Log current danger level for debugging
                logger.debug(f"Grayman at ({unit.y}, {unit.x}) has current danger level: {current_danger_level}")
                
                # Check safety of potential teleport position
                for enemy in self.game.units:
                    if enemy.player != unit.player and enemy.is_alive():
                        distance = self.game.chess_distance(y, x, enemy.y, enemy.x)
                        closest_enemy_distance = min(closest_enemy_distance, distance)
                        
                        # If we're within enemy attack range, less safe
                        enemy_stats = enemy.get_effective_stats()
                        enemy_reach = enemy_stats['move_range'] + enemy_stats['attack_range']
                        if distance <= enemy_reach:
                            enemies_that_can_reach += 1
                            if enemies_that_can_reach >= 1:  # Consider unsafe if any enemy can reach
                                safe_position = False
                                break
                
                # Only consider true emergency teleport if current position is dangerous
                if current_danger_level > 0:
                    # EXTREME bonus for emergency teleport to safety
                    if safe_position:
                        # Massive bonus for escaping danger
                        score += 100  # Increased from 50
                        
                        # Extra bonus for being far from any enemies
                        score += min(closest_enemy_distance * 5, 50)  # Increased from 30
                        
                        # Log that we're considering an emergency teleport
                        logger.info(f"EMERGENCY TELEPORT: Considering position ({y}, {x}) with score {score}")
                elif safe_position:
                    # If current position isn't dangerous, still prefer safe positions but with less urgency
                    score += 40
                    score += min(closest_enemy_distance * 3, 30)
            else:
                # If not at low health, evaluate strategic positions
                
                # Calculate distance to primary target from this position
                distance_to_target = self.game.chess_distance(y, x, target.y, target.x)
                
                # Check if we can attack the target from this position
                can_attack_target = distance_to_target <= attack_range
                
                if can_attack_target:
                    # Big bonus for positions that let us attack the target immediately - increased to make teleporting to attack more appealing
                    score += 50  # Increased from 40
                    
                    # Optimal attack position is at exactly attack range
                    if distance_to_target == attack_range:
                        score += 15  # Extra bonus for optimal distance (increased from 10)
                else:
                    # For non-attack positions, prefer to be somewhat close to target
                    # but not so close that we're vulnerable
                    ideal_distance = attack_range + 1  # Just outside attack range
                    distance_score = 25 - abs(distance_to_target - ideal_distance) * 3  # Increased from 20
                    score += max(0, distance_score)
                
                # Consider positions that give tactical advantage
                
                # 1. Check if position is near cover (next to impassable terrain)
                cover_nearby = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue  # Skip center
                        
                        check_y, check_x = y + dy, x + dx
                        if (self.game.is_valid_position(check_y, check_x) and 
                            not self.game.map.is_passable(check_y, check_x)):
                            cover_nearby = True
                            break
                
                if cover_nearby:
                    score += 15  # Bonus for being near cover
                
                # 2. Check for multiple targets in attack range
                attackable_targets = 0
                for enemy in self.game.units:
                    if enemy.player != unit.player and enemy.is_alive() and enemy != target:
                        # If this position lets us attack another enemy
                        if self.game.chess_distance(y, x, enemy.y, enemy.x) <= attack_range:
                            attackable_targets += 1
                
                # Bonus for each additional target we can attack
                score += attackable_targets * 20
                
                # 3. Check if this position helps us surround a target
                for enemy in self.game.units:
                    if enemy.player != unit.player and enemy.is_alive():
                        # Get positions adjacent to this enemy
                        from boneglaive.utils.coordinates import get_adjacent_positions
                        adjacent_positions = get_adjacent_positions(enemy.y, enemy.x)
                        
                        # Check if our allies are near the enemy
                        ally_count = 0
                        for ally in self.game.units:
                            if ally.player == unit.player and ally.is_alive() and ally != unit:
                                if (ally.y, ally.x) in adjacent_positions:
                                    ally_count += 1
                        
                        # If we have allies adjacent and this position completes the surround
                        if ally_count > 0 and (y, x) in adjacent_positions:
                            score += 15  # Bonus for surrounding tactics
            
            # Update best position if this scores higher
            if score > best_score:
                best_score = score
                best_position = (y, x)
        
        return best_position, best_score
            
    def _evaluate_estrange_skill(self, unit: 'Unit', target: 'Unit', skill) -> float:
        """
        Evaluate the value of using Estrange skill on the target.
        
        Args:
            unit: The Grayman unit
            target: The enemy target
            skill: The Estrange skill
            
        Returns:
            A score indicating the value of using this skill (higher is better)
        """
        # Check if we can use the skill
        if not skill.can_use(unit, (target.y, target.x), self.game):
            return -1  # Can't use
            
        # Start with a base score
        score = 0
            
        # Base score for being able to use the skill
        score += 20
        
        # Check if target is already estranged
        is_estranged = hasattr(target, 'estranged') and target.estranged
        
        if is_estranged:
            # Lower value if already estranged, but still has damage value
            score -= 15
            
        # Check if target is immune to status effects (GRAYMAN with Stasiality)
        is_immune = hasattr(target, 'is_immune_to_effects') and target.is_immune_to_effects()
        
        if is_immune:
            # Much less valuable if target is immune to the status effect
            score -= 20
            
        # Estrange deals damage ignoring defense - useful against high-defense targets
        # Calculate expected damage
        expected_damage = skill.damage
        
        # Check if we can kill the target with Estrange
        if target.hp <= expected_damage:
            # High bonus for securing a kill
            score += 40
            
        # More valuable against high-defense targets (since Estrange ignores defense)
        if target.defense >= 3:
            score += 15
            
        # More valuable against high-value/dangerous enemies
        target_stats = target.get_effective_stats()
        target_attack = target_stats['attack']
        target_move = target_stats['move_range']
        
        # High attack power enemies are high priority for Estrange
        if target_attack >= 4:
            score += 15
            
        # High movement enemies are also good to Estrange if not immune (reduces their mobility)
        if target_move >= 3 and not is_immune:
            score += 15
            
        # More valuable if target is at critical health (finish them off)
        if target.is_at_critical_health():
            score += 10
            
        # Distance consideration
        distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
        if distance <= skill.range:  # Within Estrange range (typically 5)
            # Higher score for targets that are at distance (harder to reach with normal attacks)
            attack_range = unit.get_effective_stats()['attack_range']
            if distance > attack_range:
                score += 10
        
        return score
            
    def _evaluate_grae_exchange_skill(self, unit: 'Unit', target: 'Unit', skill) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Evaluate the value of using Græ Exchange skill to create an echo and teleport.
        Finds the best position to teleport to and returns its score.
        
        Args:
            unit: The Grayman unit
            target: The enemy target
            skill: The Græ Exchange skill
            
        Returns:
            Tuple of (best_position, score) where position is (y, x) or (None, -1) if no valid position
        """
        # If skill is not ready yet, return no valid position
        if not skill.can_use(unit, None, self.game):
            return None, -1
            
        # Get effective stats
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        
        # Track best teleport position
        best_position = None
        best_score = 0
        
        # Get current health percentage
        health_percent = unit.hp / unit.max_hp
        
        # Current position value - how useful is it to leave an echo here?
        current_pos_value = 0
        
        # Check if there are enemies in attack range from current position
        enemies_in_range = 0
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
                if distance <= attack_range:
                    enemies_in_range += 1
                    
                    # Extra value for specific enemy types that are dangerous - increased values
                    if enemy.type == UnitType.GLAIVEMAN or enemy.type == UnitType.FOWL_CONTRIVANCE:
                        current_pos_value += 15  # Increased from 10
                    else:
                        current_pos_value += 8   # Increased from 5
        
        # If no enemies in range, the echo would be useless
        if enemies_in_range == 0:
            current_pos_value = 0
        
        # Check potential teleport positions within skill range
        for y in range(max(0, unit.y - skill.range), min(self.game.map.height, unit.y + skill.range + 1)):
            for x in range(max(0, unit.x - skill.range), min(self.game.map.width, unit.x + skill.range + 1)):
                # Skip if not a valid teleport target
                if not skill.can_use(unit, (y, x), self.game):
                    continue
                    
                # Skip current position (no benefit to teleporting to where we already are)
                if (y, x) == (unit.y, unit.x):
                    continue
                    
                # Calculate score for this position
                score = 0
                
                # Base score for a valid position - higher base score to encourage usage
                score += 20
                
                # Echo value at current position - boost this value to make Grae Exchange more appealing
                score += current_pos_value * 1.5
                
                # STRONGLY prioritize defensive teleport at low health
                if health_percent <= 0.4:  # Below 40% health
                    # Check if target position is safer than current
                    current_danger = 0
                    new_danger = 0
                    safe_position = True
                    closest_enemy_distance = float('inf')
                    
                    # Calculate danger at current and new positions
                    for enemy in self.game.units:
                        if enemy.player != unit.player and enemy.is_alive():
                            enemy_stats = enemy.get_effective_stats()
                            enemy_reach = enemy_stats['move_range'] + enemy_stats['attack_range']
                            
                            # Danger at current position
                            distance_current = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x) 
                            if distance_current <= enemy_reach:
                                current_danger += 1
                                
                            # Danger at new position
                            distance_new = self.game.chess_distance(y, x, enemy.y, enemy.x)
                            closest_enemy_distance = min(closest_enemy_distance, distance_new)
                            if distance_new <= enemy_reach:
                                new_danger += 1
                                safe_position = False
                    
                    # Log danger assessment
                    logger.debug(f"Grae Exchange from danger {current_danger} to danger {new_danger}")
                    
                    # If in danger, huge bonus for finding safety
                    if current_danger > 0:
                        if new_danger == 0 and safe_position:
                            # MASSIVE bonus for escaping to complete safety
                            score += 90  # Emergency escape score
                            score += min(closest_enemy_distance * 5, 40)  # Bonus for distance
                            logger.info(f"EMERGENCY GRAE EXCHANGE to ({y}, {x}) with score {score}")
                        elif new_danger < current_danger:
                            # Still good to reduce danger even if not completely safe
                            score += 30 + (current_danger - new_danger) * 15
                else:
                    # At good health, prioritize strategic positions
                    
                    # Calculate distance to primary target from this position
                    distance_to_target = self.game.chess_distance(y, x, target.y, target.x)
                    
                    # Check if we can attack the target from this position
                    can_attack_target = distance_to_target <= attack_range
                    
                    if can_attack_target:
                        # Bonus for positions that let us attack the target immediately - increased bonus
                        score += 30  # Increased from 20
                    else:
                        # For non-attack positions, prefer to be somewhat close to target
                        # but not too close
                        ideal_distance = attack_range + 1  # Just outside attack range
                        distance_score = 20 - abs(distance_to_target - ideal_distance) * 2  # Increased from 15
                        score += max(0, distance_score)
                    
                    # Check for multiple targets in attack range at new position
                    attackable_targets = 0
                    for enemy in self.game.units:
                        if enemy.player != unit.player and enemy.is_alive():
                            # If this position lets us attack an enemy
                            if self.game.chess_distance(y, x, enemy.y, enemy.x) <= attack_range:
                                attackable_targets += 1
                    
                    # Bonus for targets we can attack at new position
                    score += attackable_targets * 10
                
                # Bonus if the new position has good strategic value (near cover, etc.)
                cover_nearby = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue  # Skip center
                        
                        check_y, check_x = y + dy, x + dx
                        if (self.game.is_valid_position(check_y, check_x) and 
                            not self.game.map.is_passable(check_y, check_x)):
                            cover_nearby = True
                            break
                
                if cover_nearby:
                    score += 10  # Bonus for being near cover at new position
                
                # Update best position if this scores higher
                if score > best_score:
                    best_score = score
                    best_position = (y, x)
        
        return best_position, best_score
    
    def _find_best_target_for_grayman(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find the best target for a Grayman.
        Prioritizes high-value targets within range of skills, especially Estrange.
        
        Args:
            unit: The Grayman unit
            
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
        
        # Find estrange skill and its range if available
        estrange_range = 0
        for skill in unit.active_skills:
            if skill.name == "Estrange":
                estrange_range = skill.range
                break
        
        for enemy in enemy_units:
            score = 0
            
            # Calculate base distance
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            
            # Calculate if the enemy is reachable (either now or after moving)
            can_attack_now = distance <= attacker_attack
            can_reach_for_attack = distance <= (attacker_move + attacker_attack)
            
            # Within Estrange range gets high priority
            if estrange_range > 0 and distance <= estrange_range:
                score += 30
                
                # Immune targets get a score penalty
                if hasattr(enemy, 'is_immune_to_effects') and enemy.is_immune_to_effects():
                    score -= 15
                
                # Already estranged targets get lower priority
                if hasattr(enemy, 'estranged') and enemy.estranged:
                    score -= 10
            
            # Immediate attack opportunities get priority too
            if can_attack_now:
                score += 25
            # Targets that can be reached this turn get medium priority
            elif can_reach_for_attack:
                score += 15
                
            # Prioritize high value/dangerous targets
            enemy_stats = enemy.get_effective_stats()
            
            # High attack units are priority targets
            if enemy_stats['attack'] >= 4:
                score += 20
                
            # High movement units good to Estrange when possible
            if enemy_stats['move_range'] >= 3:
                score += 15
                
            # High defense units good to target with defense-ignoring Estrange
            if enemy_stats['defense'] >= 3:
                score += 15
                
            # Prioritize low health enemies (but not if they're too far)
            if can_reach_for_attack or distance <= estrange_range:
                # Invert HP to give higher scores to lower-HP enemies
                hp_factor = 100 - enemy.hp
                score += hp_factor * 0.3
                
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
    
    def _find_best_target_for_marrow_condenser(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find the best target for a Marrow Condenser.
        Prioritizes groups of enemies for area effect skills and close targets for melee.
        
        Args:
            unit: The Marrow Condenser unit
            
        Returns:
            The best enemy unit to target, or None if no enemies found
        """
        # Get all enemy units
        enemy_units = [u for u in self.game.units if u.player != unit.player and u.is_alive()]
        
        if not enemy_units:
            return None
        
        scored_enemies = []
        
        for enemy in enemy_units:
            score = 0
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            
            # Base score for being a valid target
            score += 10
            
            # Check if enemy can be reached for melee attack (move + attack range)
            stats = unit.get_effective_stats()
            total_reach = stats['move_range'] + stats['attack_range']
            can_reach_for_attack = distance <= total_reach
            
            if can_reach_for_attack:
                score += 30  # High bonus for reachable targets
            
            # Count nearby enemies around this target (for area effect value)
            nearby_enemies = 0
            for other_enemy in enemy_units:
                if other_enemy != enemy:
                    enemy_distance = self.game.chess_distance(enemy.y, enemy.x, other_enemy.y, other_enemy.x)
                    if enemy_distance <= 2:  # Within range of potential Marrow Dike or movement
                        nearby_enemies += 1
            
            # Bonus for enemies with other enemies nearby (good for area effects)
            score += nearby_enemies * 10
            
            # Prioritize enemies within Bone Tithe range (adjacent when reached)
            if distance <= total_reach + 1:  # Can move and be adjacent for Bone Tithe
                score += 25
            
            # Prioritize lower HP enemies (easier to kill for Dominion upgrades)
            if enemy.hp <= 8:  # Low HP threshold
                score += 20
            elif enemy.hp <= 15:  # Medium HP
                score += 10
            
            # Prioritize high-value targets
            enemy_stats = enemy.get_effective_stats()
            
            # High attack units should be eliminated
            if enemy_stats['attack'] >= 4:
                score += 15
                
            # High mobility units are good to trap with Marrow Dike
            if enemy_stats['move_range'] >= 3:
                score += 15
                
            # Distance penalty (closer targets preferred for melee unit)
            score -= distance * 2
            
            scored_enemies.append((enemy, score))
        
        # Get the enemy with the highest score
        if scored_enemies:
            # Log the top targets for debugging
            scored_enemies.sort(key=lambda x: x[1], reverse=True)
            for i, (enemy, score) in enumerate(scored_enemies[:3]):
                if i == 0:
                    logger.debug(f"Best target for {unit.get_display_name()}: {enemy.get_display_name()} (score: {score})")
                else:
                    logger.debug(f"Alternative target #{i+1}: {enemy.get_display_name()} (score: {score})")
            
            return scored_enemies[0][0]
            
        # Fallback to nearest enemy if scoring fails
        return self._find_nearest_enemy(unit)
    
    def _use_marrow_condenser_skills(self, unit: 'Unit', target: 'Unit', available_skills: list, 
                                   is_low_health: bool, enemies_in_melee: int) -> Optional['ActiveSkill']:
        """
        Intelligently use Marrow Condenser skills based on the current situation.
        
        Args:
            unit: The Marrow Condenser unit
            target: The target enemy unit
            available_skills: List of available skills
            is_low_health: Whether the unit is at low health
            enemies_in_melee: Number of enemies in melee range
            
        Returns:
            The skill that was used, or None if no skill was used
        """
        if not available_skills:
            return None
        
        # Count nearby enemies for area effect considerations
        nearby_enemies = self._count_enemies_in_range(unit, 2)  # Within 2 spaces
        adjacent_enemies = self._count_enemies_in_range(unit, 1)  # Adjacent only
        
        # Evaluate each skill and assign scores
        skill_scores = []
        
        for skill in available_skills:
            try:
                score = 0
                target_pos = None
                
                if skill.name == "Ossify":
                    # Defensive skill - higher priority when threatened
                    score, target_pos = self._evaluate_ossify(unit, is_low_health, enemies_in_melee)
                    
                elif skill.name == "Marrow Dike":
                    # Area denial/trap skill - good when enemies are nearby
                    score, target_pos = self._evaluate_marrow_dike(unit, target, nearby_enemies)
                    
                elif skill.name == "Bone Tithe":
                    # Sustain/damage skill - good when adjacent enemies present
                    score, target_pos = self._evaluate_bone_tithe(unit, adjacent_enemies, is_low_health)
                
                if score > 0 and target_pos:
                    skill_scores.append((skill, score, target_pos))
                    
            except Exception as e:
                logger.error(f"Error evaluating skill {skill.name}: {e}")
                continue
        
        # Debug skill scores
        logger.info(f"Marrow Condenser skill scores: {[(s[0].name, s[1]) for s in skill_scores]}")
        
        # Sort by score (highest first)
        skill_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Use the highest scoring skill if score is above threshold
        threshold = 15
        if skill_scores and skill_scores[0][1] >= threshold:
            skill, score, target_pos = skill_scores[0]
            
            logger.info(f"Using skill {skill.name} with score {score}")
            
            # Use the skill
            success = skill.use(unit, target_pos, self.game)
            logger.info(f"Skill use result: {success}")
            
            if success:
                return skill
                
        return None
    
    def _evaluate_ossify(self, unit: 'Unit', is_low_health: bool, enemies_in_melee: int) -> Tuple[float, Optional[Tuple[int, int]]]:
        """
        Evaluate the value of using Ossify for defense.
        
        Args:
            unit: The Marrow Condenser unit
            is_low_health: Whether unit is at low health
            enemies_in_melee: Number of enemies in melee range
            
        Returns:
            Tuple of (score, target_position)
        """
        score = 0
        
        # Base score for using defensive skill
        score += 10
        
        # High priority when low health and threatened
        if is_low_health:
            score += 30
            if enemies_in_melee > 0:
                score += 20  # Extra bonus when actively threatened
        
        # Moderate priority when enemies are in melee range
        elif enemies_in_melee > 0:
            score += 25
        
        # Bonus based on number of threatening enemies
        score += enemies_in_melee * 10
        
        # Check if already ossified (don't reapply)
        if hasattr(unit, 'ossify_active') and unit.ossify_active:
            score = 0  # Don't use if already active
            
        # Target position is self
        target_pos = (unit.y, unit.x) if score > 0 else None
        
        logger.debug(f"Ossify evaluation: score={score}, low_health={is_low_health}, enemies_in_melee={enemies_in_melee}")
        
        return score, target_pos
    
    def _evaluate_marrow_dike(self, unit: 'Unit', target: 'Unit', nearby_enemies: int) -> Tuple[float, Optional[Tuple[int, int]]]:
        """
        Evaluate the value of using Marrow Dike for area denial with team coordination.
        
        Args:
            unit: The Marrow Condenser unit
            target: The target enemy
            nearby_enemies: Number of enemies within 2 spaces
            
        Returns:
            Tuple of (score, target_position)
        """
        score = 0
        
        # Only consider Marrow Dike if there are enemies that would be trapped
        enemies_in_dike_area = 0
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                enemy_distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
                if enemy_distance <= 2:  # Would be inside the 5x5 dike area
                    enemies_in_dike_area += 1
        
        # Don't use Marrow Dike if no enemies would be trapped
        if enemies_in_dike_area == 0:
            return 0, None
        
        # Base score for area denial
        score += 15
        
        # High value when multiple enemies nearby (can trap them)
        if enemies_in_dike_area >= 2:
            score += 40
            score += (enemies_in_dike_area - 2) * 15  # Bonus for each additional enemy
        elif enemies_in_dike_area == 1:
            score += 20  # Still good for single enemy trap
        
        # Bonus if target is close enough to be affected
        distance_to_target = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
        if distance_to_target <= 3:  # Target would be affected by 5x5 dike
            score += 25
        
        # NEW: Team coordination for staggered dike usage
        coordination_modifier = self._evaluate_dike_coordination(unit)
        score += coordination_modifier
        
        # If coordination completely blocks usage, set score to 0
        if coordination_modifier <= -1000:
            score = 0
        
        # Target position is self (center of dike)
        target_pos = (unit.y, unit.x) if score > 0 else None
        
        logger.debug(f"Marrow Dike evaluation: score={score}, nearby_enemies={nearby_enemies}, distance_to_target={distance_to_target}, coordination_modifier={coordination_modifier}")
        
        return score, target_pos
    
    def _evaluate_dike_coordination(self, unit: 'Unit') -> float:
        """
        Evaluate coordination with teammate Marrow Condensers for staggered dike usage.
        
        Args:
            unit: The Marrow Condenser unit considering using Marrow Dike
            
        Returns:
            Coordination modifier score (+/- to add to base dike score)
            Returns -1000+ to completely block usage if poor timing
        """
        # Find teammate Marrow Condensers
        teammate_condensers = []
        for game_unit in self.game.units:
            if (game_unit.player == unit.player and 
                game_unit.is_alive() and 
                game_unit.type == UnitType.MARROW_CONDENSER and 
                game_unit != unit):
                teammate_condensers.append(game_unit)
        
        # If no teammates, use normal evaluation (no coordination needed)
        if not teammate_condensers:
            logger.debug("No teammate Marrow Condensers found - normal dike evaluation")
            return 0
        
        # Check for active teammate dikes
        active_teammate_dikes = []
        if hasattr(self.game, 'marrow_dike_tiles') and self.game.marrow_dike_tiles:
            for tile_info in self.game.marrow_dike_tiles.values():
                if tile_info.get('owner') and tile_info['owner'].player == unit.player:
                    # This is a dike owned by our team
                    dike_owner = tile_info['owner']
                    if dike_owner != unit:  # It's a teammate's dike
                        remaining_duration = tile_info.get('duration', 0)
                        active_teammate_dikes.append({
                            'owner': dike_owner,
                            'remaining_duration': remaining_duration,
                            'upgraded': tile_info.get('upgraded', False)
                        })
        
        logger.debug(f"Found {len(active_teammate_dikes)} active teammate dikes")
        
        # No active teammate dikes - can use normally
        if not active_teammate_dikes:
            # Bonus for good coordination (first dike in chain)
            logger.debug("No active teammate dikes - can start dike chain")
            return 10
        
        # There is an active teammate dike - evaluate stagger timing
        teammate_dike = active_teammate_dikes[0]  # Should only be one due to auto-expire
        remaining_turns = teammate_dike['remaining_duration']
        
        logger.debug(f"Teammate dike has {remaining_turns} turns remaining")
        
        # Calculate spatial chaining bonus for area coverage
        spatial_bonus = self._evaluate_dike_spatial_chaining(unit, active_teammate_dikes)
        logger.debug(f"Spatial chaining bonus: {spatial_bonus}")
        
        # Staggering logic based on remaining duration
        if remaining_turns >= 3:
            # Teammate's dike just started - wait for better timing
            logger.debug("Teammate dike too fresh - blocking usage for better staggering")
            return -1000  # Block usage
            
        elif remaining_turns == 2:
            # Good timing - use dike so it starts as teammate's expires
            logger.debug("Good stagger timing - teammate dike expires soon")
            return 50 + spatial_bonus  # Strong bonus for good timing + spatial bonus
            
        elif remaining_turns == 1:
            # Excellent timing - perfect stagger
            logger.debug("Excellent stagger timing - teammate dike expires next turn")
            return 75 + spatial_bonus  # Very strong bonus for perfect timing + spatial bonus
            
        else:  # remaining_turns <= 0 (shouldn't happen, but handle gracefully)
            # Teammate's dike expired or expiring - normal usage
            logger.debug("Teammate dike expired - normal usage")
            return 0 + spatial_bonus
    
    def _evaluate_dike_spatial_chaining(self, unit: 'Unit', active_teammate_dikes: list) -> float:
        """
        Evaluate spatial positioning bonus for chaining dikes with teammates.
        
        Args:
            unit: The Marrow Condenser unit considering dike placement
            active_teammate_dikes: List of active teammate dike information
            
        Returns:
            Spatial bonus score for area coverage optimization
        """
        if not active_teammate_dikes:
            return 0
            
        # Get positions of existing teammate dike walls
        teammate_dike_positions = set()
        if hasattr(self.game, 'marrow_dike_tiles') and self.game.marrow_dike_tiles:
            for (tile_y, tile_x), tile_info in self.game.marrow_dike_tiles.items():
                if (tile_info.get('owner') and 
                    tile_info['owner'].player == unit.player and 
                    tile_info['owner'] != unit):
                    teammate_dike_positions.add((tile_y, tile_x))
        
        if not teammate_dike_positions:
            return 0
        
        # Calculate where our dike would place walls (5x5 perimeter around unit)
        our_dike_positions = set()
        center_y, center_x = unit.y, unit.x
        
        # Generate 5x5 perimeter positions (same logic as MarrowDikeSkill)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dy) == 2 or abs(dx) == 2:  # Edge positions only
                    tile_y, tile_x = center_y + dy, center_x + dx
                    if self.game.is_valid_position(tile_y, tile_x):
                        our_dike_positions.add((tile_y, tile_x))
        
        # Calculate spatial relationship benefits
        spatial_bonus = 0
        
        # 1. Proximity bonus - reward positioning near teammate dikes for concentrated area control
        min_distance = float('inf')
        for our_pos in our_dike_positions:
            for teammate_pos in teammate_dike_positions:
                distance = self.game.chess_distance(our_pos[0], our_pos[1], teammate_pos[0], teammate_pos[1])
                min_distance = min(min_distance, distance)
        
        if min_distance <= 3:
            # Very close positioning - excellent for concentrated area denial
            spatial_bonus += 25
            logger.debug(f"Close dike positioning bonus: {25}")
        elif min_distance <= 5:
            # Moderate distance - good for extended area coverage
            spatial_bonus += 15
            logger.debug(f"Moderate dike positioning bonus: {15}")
        elif min_distance <= 8:
            # Extended positioning - some strategic value
            spatial_bonus += 5
            logger.debug(f"Extended dike positioning bonus: {5}")
        
        # 2. Coverage area bonus - reward positioning that covers new strategic areas
        # Count enemy units that would be newly affected by our dike
        newly_covered_enemies = 0
        for enemy_unit in self.game.units:
            if (enemy_unit.player != unit.player and enemy_unit.is_alive()):
                enemy_pos = (enemy_unit.y, enemy_unit.x)
                
                # Check if enemy would be in our dike's interior (trapped)
                distance_to_our_center = self.game.chess_distance(enemy_pos[0], enemy_pos[1], center_y, center_x)
                if distance_to_our_center <= 2:  # Inside our 5x5 dike area
                    # Check if enemy is NOT already covered by teammate dike
                    covered_by_teammate = False
                    for teammate_pos in teammate_dike_positions:
                        # Estimate teammate's dike center (approximate)
                        teammate_distance = self.game.chess_distance(enemy_pos[0], enemy_pos[1], teammate_pos[0], teammate_pos[1])
                        if teammate_distance <= 3:  # Rough estimate of being affected by teammate dike
                            covered_by_teammate = True
                            break
                    
                    if not covered_by_teammate:
                        newly_covered_enemies += 1
        
        # Bonus for covering new enemies
        spatial_bonus += newly_covered_enemies * 10
        logger.debug(f"New enemy coverage bonus: {newly_covered_enemies * 10} (covering {newly_covered_enemies} new enemies)")
        
        # 3. Strategic corridor control - bonus for controlling key map areas
        # This is a simplified version - could be enhanced with map-specific logic
        map_center_y, map_center_x = self.game.map.height // 2, self.game.map.width // 2
        distance_to_map_center = self.game.chess_distance(center_y, center_x, map_center_y, map_center_x)
        
        if distance_to_map_center <= 3:
            spatial_bonus += 10
            logger.debug(f"Map center control bonus: 10")
        
        logger.debug(f"Total spatial bonus: {spatial_bonus}")
        return spatial_bonus
    
    def _evaluate_bone_tithe(self, unit: 'Unit', adjacent_enemies: int, is_low_health: bool) -> Tuple[float, Optional[Tuple[int, int]]]:
        """
        Evaluate the value of using Bone Tithe for sustain/damage.
        
        Args:
            unit: The Marrow Condenser unit
            adjacent_enemies: Number of adjacent enemies
            is_low_health: Whether unit is at low health
            
        Returns:
            Tuple of (score, target_position)
        """
        score = 0
        
        # Base score - very low cooldown makes this spammable
        score += 5
        
        # High value when adjacent enemies present (guaranteed hits)
        if adjacent_enemies >= 2:
            score += 35  # Multiple hits = multiple HP gains
            score += (adjacent_enemies - 2) * 15  # Bonus for each additional enemy
        elif adjacent_enemies == 1:
            score += 20  # Still good for single enemy hit
        else:
            score = 0  # No value without adjacent enemies
        
        # Extra value when low health (HP gain more valuable)
        if is_low_health and adjacent_enemies > 0:
            score += 20
        
        # Check for upgrade status for better scaling
        if hasattr(unit, 'passive_skill') and hasattr(unit.passive_skill, 'bone_tithe_upgraded'):
            if unit.passive_skill.bone_tithe_upgraded:
                score += 10  # Upgraded version gives more HP
        
        # Target position is self (area effect centered on self)
        target_pos = (unit.y, unit.x) if score > 0 else None
        
        logger.debug(f"Bone Tithe evaluation: score={score}, adjacent_enemies={adjacent_enemies}, is_low_health={is_low_health}")
        
        return score, target_pos
    
    def _count_enemies_in_range(self, unit: 'Unit', range_: int) -> int:
        """
        Count the number of enemy units within the specified range.
        
        Args:
            unit: The unit to check from
            range_: The range to check within
            
        Returns:
            Number of enemies within range
        """
        count = 0
        for enemy in self.game.units:
            if enemy.player != unit.player and enemy.is_alive():
                distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
                if distance <= range_:
                    count += 1
        return count
    
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
        # Check if unit is trapped - trapped units cannot move but can still attack from current position
        if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
            # Calculate distance from current position to target
            distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
            attack_range = unit.get_effective_stats()['attack_range']
            
            # If target is within attack range from current position, set attack target
            if distance <= attack_range:
                unit.attack_target = (target.y, target.x)
                return True
            return False
            
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
        # Check if unit is trapped - trapped units cannot move
        if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
            logger.info(f"{unit.get_display_name()} cannot move because it is trapped")
            return
            
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
        # Check if unit is trapped - trapped units cannot move
        if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
            logger.info(f"{unit.get_display_name()} cannot move because it is trapped")
            return
            
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

    def _find_best_gaussian_dusk_target(self, unit: 'Unit') -> Optional['Unit']:
        """
        Find the best target for Gaussian Dusk by prioritizing immobilized or predictable enemies.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            
        Returns:
            The best target for Gaussian Dusk, or None if no good targets found
        """
        enemy_units = [enemy for enemy in self.game.units 
                      if enemy.player != unit.player and enemy.is_alive()]
        
        if not enemy_units:
            return None
            
        scored_enemies = []
        
        for enemy in enemy_units:
            score = 0
            
            # High priority: Immobilized or movement-restricted enemies
            if hasattr(enemy, 'jawline_affected') and enemy.jawline_affected:
                score += 100  # Jawline tether - can't move
                logger.debug(f"{enemy.get_display_name()} is tethered by Jawline (+100 points)")
            
            if hasattr(enemy, 'trapped_by') and enemy.trapped_by:
                score += 90  # Trapped units are easy targets
                logger.debug(f"{enemy.get_display_name()} is trapped (+90 points)")
            
            # Medium priority: Units in corners or against walls (limited movement)
            corner_penalty = self._evaluate_corner_position(enemy)
            score += corner_penalty
            if corner_penalty > 0:
                logger.debug(f"{enemy.get_display_name()} in restricted position (+{corner_penalty} points)")
            
            # Check if we can hit multiple enemies in a line
            line_enemies = self._count_enemies_in_gaussian_line(unit, enemy)
            if line_enemies > 1:
                score += (line_enemies - 1) * 30  # Bonus for hitting multiple
                logger.debug(f"Gaussian line through {enemy.get_display_name()} hits {line_enemies} enemies (+{(line_enemies-1)*30} points)")
            
            # Priority based on enemy health - prefer to finish off wounded
            health_percent = enemy.hp / enemy.max_hp
            if health_percent <= 0.3:  # Low health
                score += 25
                logger.debug(f"{enemy.get_display_name()} at low health (+25 points)")
            elif health_percent <= 0.6:  # Medium health  
                score += 15
                logger.debug(f"{enemy.get_display_name()} at medium health (+15 points)")
            
            # Distance consideration - closer is better for reliability
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            if distance <= 5:
                score += 10
            elif distance <= 8:
                score += 5
                
            # Check if we have clear line of sight
            if self._has_clear_gaussian_line(unit, enemy):
                score += 20
                logger.debug(f"Clear line to {enemy.get_display_name()} (+20 points)")
            
            scored_enemies.append((enemy, score))
            
        if scored_enemies:
            # Sort by score (highest first)
            scored_enemies.sort(key=lambda x: x[1], reverse=True)
            logger.debug(f"Best Gaussian Dusk target: {scored_enemies[0][0].get_display_name()} (score: {scored_enemies[0][1]})")
            return scored_enemies[0][0]
            
        # Fallback to nearest enemy
        return self._find_nearest_enemy(unit)

    def _use_fowl_contrivance_skills(self, unit: 'Unit', target: 'Unit', available_skills: list) -> Optional['ActiveSkill']:
        """
        Use FOWL_CONTRIVANCE skills intelligently.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            available_skills: List of available skills
            
        Returns:
            The skill that was used, or None if no skill was used
        """
        # Look for available skills
        gaussian_dusk = None
        parabol = None
        fragcrest = None
        
        for skill in available_skills:
            if hasattr(skill, 'name'):
                if skill.name == "Gaussian Dusk":
                    gaussian_dusk = skill
                elif skill.name == "Parabol":
                    parabol = skill
                elif skill.name == "Fragcrest":
                    fragcrest = skill
        
        # Prefer Gaussian Dusk if we have a good shot
        if gaussian_dusk:
            direction = self._calculate_gaussian_direction(unit, target)
            if direction and self._is_good_gaussian_shot(unit, target, direction):
                # FORCE charging initiation - bypass skill.use() for reliability
                unit.selected_skill = gaussian_dusk
                unit.skill_target = direction
                logger.info(f"FOWL_CONTRIVANCE FORCING Gaussian Dusk charge in direction {direction}")
                return gaussian_dusk
        
        # Try Fragcrest if it's tactically advantageous
        if fragcrest and self._should_use_fragcrest(unit, target, fragcrest):
            if fragcrest.use(unit, (target.y, target.x), self.game):
                logger.info(f"FOWL_CONTRIVANCE using Fragcrest tactically")
                return fragcrest
            else:
                logger.debug("Fragcrest use() failed - likely on cooldown or invalid target")
        
        # Fallback to Parabol if available and enemies are clustered
        if parabol:
            # Check if there are multiple enemies in range
            enemies_in_range = 0
            for enemy in self.game.units:
                if (enemy.player != unit.player and enemy.is_alive() and
                    self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x) <= 6):  # Parabol range
                    enemies_in_range += 1
            
            if enemies_in_range >= 2:  # Use Parabol if hitting multiple enemies
                if parabol.use(unit, (target.y, target.x), self.game):
                    logger.info(f"FOWL_CONTRIVANCE using Parabol on clustered enemies")
                    return parabol
                else:
                    logger.debug("Parabol use() failed - likely on cooldown or invalid target")
        
        return None

    def _find_best_artillery_position(self, unit: 'Unit', target: 'Unit') -> Optional[Tuple[int, int]]:
        """
        Find the best position for artillery tactics.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            
        Returns:
            The best position to move to, or None if current position is fine
        """
        from boneglaive.utils.constants import HEIGHT, WIDTH
        
        current_pos = (unit.y, unit.x)
        best_pos = None
        best_score = 0
        
        # Check positions within movement range
        move_range = unit.move_range
        
        for dy in range(-move_range, move_range + 1):
            for dx in range(-move_range, move_range + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx
                
                # Skip if out of bounds
                if not (0 <= new_y < HEIGHT and 0 <= new_x < WIDTH):
                    continue
                    
                # Skip if not passable or occupied
                if not self.game.map.is_passable(new_y, new_x) or self.game.get_unit_at(new_y, new_x):
                    continue
                    
                # Skip if can't reach this position
                distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                if distance > move_range:
                    continue
                    
                score = self._evaluate_artillery_position(new_y, new_x, target)
                if score > best_score:
                    best_score = score
                    best_pos = (new_y, new_x)
        
        # Only move if we found a significantly better position
        current_score = self._evaluate_artillery_position(unit.y, unit.x, target)
        if best_score > current_score + 10:  # Require significant improvement
            return best_pos
            
        return None

    def _evaluate_artillery_position(self, y: int, x: int, target: 'Unit') -> float:
        """
        Evaluate how good a position is for artillery tactics.
        
        Args:
            y, x: Position to evaluate
            target: The target enemy
            
        Returns:
            Score for the position (higher is better)
        """
        score = 0
        
        # Prefer positions with clear line of sight to target
        temp_unit_pos = (y, x)
        if self._has_clear_line_of_sight_from_pos(temp_unit_pos, (target.y, target.x)):
            score += 30
        
        # Prefer positions that hit multiple enemies in potential Gaussian lines
        max_enemies_in_line = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                enemies_in_line = self._count_enemies_in_line_from_pos((y, x), (dy, dx))
                max_enemies_in_line = max(max_enemies_in_line, enemies_in_line)
        
        score += max_enemies_in_line * 15
        
        # Prefer rails if available (FOWL_CONTRIVANCE rail bonuses)
        if self.game.map.has_rails() and self.game.map.is_rail_at(y, x):
            score += 20
        
        # Prefer distance from enemies (artillery should stay back)
        min_enemy_distance = float('inf')
        for enemy in self.game.units:
            if enemy.player != 2 and enemy.is_alive():  # Player 1 units
                distance = self.game.chess_distance(y, x, enemy.y, enemy.x)
                min_enemy_distance = min(min_enemy_distance, distance)
        
        if min_enemy_distance > 3:
            score += 10  # Bonus for staying at safe distance
        
        return score

    def _calculate_gaussian_direction(self, unit: 'Unit', target: 'Unit') -> Optional[Tuple[int, int]]:
        """
        Calculate the direction for Gaussian Dusk to hit the target.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            
        Returns:
            Direction tuple (dy, dx) or None if no clear shot
        """
        dy = target.y - unit.y
        dx = target.x - unit.x
        
        # Normalize to one of 8 directions
        if abs(dx) > abs(dy):
            direction = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            direction = (1 if dy > 0 else -1, 0)
        else:
            direction = (1 if dy > 0 else -1, 1 if dx > 0 else -1)
            
        return direction

    def _is_good_gaussian_shot(self, unit: 'Unit', target: 'Unit', direction: Tuple[int, int]) -> bool:
        """
        Determine if a Gaussian Dusk shot in the given direction is worthwhile.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            direction: The firing direction
            
        Returns:
            True if it's a good shot, False otherwise
        """
        # Check if target is actually in the line of fire
        if not self._target_in_gaussian_line(unit, target, direction):
            return False
            
        # Count total enemies that would be hit
        enemies_hit = self._count_enemies_in_gaussian_line_direction(unit, direction)
        
        # Good shot if we hit the intended target and at least one enemy total
        return enemies_hit >= 1

    def _has_clear_gaussian_line(self, unit: 'Unit', target: 'Unit') -> bool:
        """
        Check if there's a clear Gaussian Dusk line to the target.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            
        Returns:
            True if there's a clear line, False otherwise
        """
        direction = self._calculate_gaussian_direction(unit, target)
        if not direction:
            return False
            
        return self._target_in_gaussian_line(unit, target, direction)

    def _target_in_gaussian_line(self, unit: 'Unit', target: 'Unit', direction: Tuple[int, int]) -> bool:
        """
        Check if target is actually in the Gaussian firing line.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            direction: The firing direction (dy, dx)
            
        Returns:
            True if target is in the line, False otherwise
        """
        dy, dx = direction
        y, x = unit.y, unit.x
        
        # Trace the line and check if we hit the target
        while 0 <= y + dy < self.game.map.height and 0 <= x + dx < self.game.map.width:
            y += dy
            x += dx
            if y == target.y and x == target.x:
                return True
                
        return False

    def _count_enemies_in_gaussian_line(self, unit: 'Unit', target: 'Unit') -> int:
        """
        Count enemies that would be hit by Gaussian Dusk aimed at target.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target enemy
            
        Returns:
            Number of enemies that would be hit
        """
        direction = self._calculate_gaussian_direction(unit, target)
        if not direction:
            return 0
            
        return self._count_enemies_in_gaussian_line_direction(unit, direction)

    def _count_enemies_in_gaussian_line_direction(self, unit: 'Unit', direction: Tuple[int, int]) -> int:
        """
        Count enemies in a Gaussian Dusk line in the given direction.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            direction: The firing direction (dy, dx)
            
        Returns:
            Number of enemies in the line
        """
        dy, dx = direction
        y, x = unit.y, unit.x
        enemies_hit = 0
        
        # Trace the line across the entire map
        while 0 <= y + dy < self.game.map.height and 0 <= x + dx < self.game.map.width:
            y += dy
            x += dx
            enemy_unit = self.game.get_unit_at(y, x)
            if enemy_unit and enemy_unit.player != unit.player and enemy_unit.is_alive():
                enemies_hit += 1
                
        return enemies_hit

    def _count_enemies_in_line_from_pos(self, pos: Tuple[int, int], direction: Tuple[int, int]) -> int:
        """
        Count enemies in a line from a given position.
        
        Args:
            pos: Starting position (y, x)
            direction: The direction (dy, dx)
            
        Returns:
            Number of enemies in the line
        """
        y, x = pos
        dy, dx = direction
        enemies_hit = 0
        
        # Trace the line across the entire map
        while 0 <= y + dy < self.game.map.height and 0 <= x + dx < self.game.map.width:
            y += dy
            x += dx
            enemy_unit = self.game.get_unit_at(y, x)
            if enemy_unit and enemy_unit.player != 2 and enemy_unit.is_alive():  # Player 1 units
                enemies_hit += 1
                
        return enemies_hit

    def _has_clear_line_of_sight_from_pos(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """
        Check if there's clear line of sight between two positions.
        
        Args:
            from_pos: Starting position (y, x)
            to_pos: Target position (y, x)
            
        Returns:
            True if clear line of sight, False otherwise
        """
        # For simplicity, just check if positions are in same row, column, or diagonal
        y1, x1 = from_pos
        y2, x2 = to_pos
        
        dy = y2 - y1
        dx = x2 - x1
        
        # Must be in a straight line (8-directional)
        if dy != 0 and dx != 0 and abs(dy) != abs(dx):
            return False
            
        return True

    def _evaluate_corner_position(self, unit: 'Unit') -> int:
        """
        Evaluate if a unit is in a corner or restricted position.
        
        Args:
            unit: The unit to evaluate
            
        Returns:
            Bonus points if unit is in a restricted position
        """
        y, x = unit.y, unit.x
        blocked_directions = 0
        
        # Check all 8 directions around the unit
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                    
                new_y, new_x = y + dy, x + dx
                
                # Count blocked directions (impassable terrain or map edge)
                if (not self.game.is_valid_position(new_y, new_x) or 
                    not self.game.map.is_passable(new_y, new_x)):
                    blocked_directions += 1
        
        # More blocked directions = higher score (easier target)
        if blocked_directions >= 5:  # Very restricted
            return 40
        elif blocked_directions >= 3:  # Somewhat restricted
            return 20
        elif blocked_directions >= 1:  # Slightly restricted
            return 10
            
        return 0

    def _should_use_fragcrest(self, unit: 'Unit', target: 'Unit', fragcrest_skill) -> bool:
        """
        Determine if Fragcrest should be used tactically.
        Real players use Fragcrest for:
        - Hitting multiple enemies in cone
        - Finishing low-health targets with shrapnel DOT
        - Tactical knockback positioning
        - When other skills are on cooldown
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The primary target
            fragcrest_skill: The Fragcrest skill object
            
        Returns:
            True if Fragcrest should be used, False otherwise
        """
        # Must be able to use the skill
        if not fragcrest_skill.can_use(unit, (target.y, target.x), self.game):
            return False
            
        # Must be within range (4 tiles)
        distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
        if distance > 4:
            return False
            
        # Must have line of sight
        if not self.game.has_line_of_sight(unit.y, unit.x, target.y, target.x):
            return False
        
        score = 0
        
        # High priority: Multiple enemies in the cone
        cone_enemies = self._count_enemies_in_fragcrest_cone(unit, target)
        if cone_enemies >= 2:
            score += 50  # Very good - hitting multiple targets
            logger.debug(f"Fragcrest can hit {cone_enemies} enemies (+50 points)")
        elif cone_enemies == 1:
            score += 10  # Still useful for single target
            
        # Medium priority: Target is wounded and shrapnel could finish them
        target_health_percent = target.hp / target.max_hp
        if target_health_percent <= 0.3:  # Low health - shrapnel DOT could finish
            score += 30
            logger.debug(f"Target at {target_health_percent:.0%} health, shrapnel could finish (+30 points)")
        elif target_health_percent <= 0.5:  # Medium health
            score += 15
            logger.debug(f"Target at {target_health_percent:.0%} health (+15 points)")
            
        # Tactical knockback: Can push enemy into bad position
        knockback_value = self._evaluate_knockback_tactical_value(unit, target)
        score += knockback_value
        if knockback_value > 0:
            logger.debug(f"Tactical knockback value (+{knockback_value} points)")
            
        # Priority when other skills unavailable
        other_skills_available = 0
        for skill in unit.get_available_skills():
            if hasattr(skill, 'name') and skill.name in ["Gaussian Dusk", "Parabol"]:
                other_skills_available += 1
                
        if other_skills_available == 0:
            score += 25  # Use Fragcrest when it's the only option
            logger.debug("No other skills available (+25 points)")
        elif other_skills_available == 1:
            score += 10  # Some preference when limited options
            
        # Distance preference - closer is better for cone effect
        if distance <= 2:
            score += 15  # Close range - cone effect more concentrated
        elif distance <= 3:
            score += 10
            
        # Bonus if target doesn't have shrapnel DOT already
        if not hasattr(target, 'shrapnel_duration') or target.shrapnel_duration <= 0:
            score += 15  # Fresh shrapnel application
            logger.debug("Target doesn't have shrapnel DOT (+15 points)")
            
        # Use Fragcrest if score is high enough
        threshold = 30 if self.difficulty == AIDifficulty.HARD else 40
        logger.debug(f"Fragcrest tactical score: {score} (threshold: {threshold})")
        return score >= threshold

    def _count_enemies_in_fragcrest_cone(self, unit: 'Unit', primary_target: 'Unit') -> int:
        """
        Count how many enemies would be hit by Fragcrest cone.
        Uses simplified cone calculation similar to the actual skill.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            primary_target: The primary target
            
        Returns:
            Number of enemies that would be hit
        """
        enemies_hit = 0
        
        # Calculate cone direction
        dy = primary_target.y - unit.y
        dx = primary_target.x - unit.x
        
        # Normalize direction for cone calculation
        if abs(dx) > abs(dy):
            main_dir = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            main_dir = (1 if dy > 0 else -1, 0)
        else:
            main_dir = (1 if dy > 0 else -1, 1 if dx > 0 else -1)
        
        # Generate cone positions (simplified version of skill logic)
        cone_positions = []
        for range_step in range(1, 5):  # Fragcrest range is 4
            # Calculate width at this range (cone gets wider with distance)
            width = min(3, 1 + range_step // 2)
            
            # Calculate center position at this range
            center_y = unit.y + main_dir[0] * range_step
            center_x = unit.x + main_dir[1] * range_step
            
            # Add positions around the center based on width
            for offset in range(-(width//2), (width//2) + 1):
                if main_dir[0] == 0:  # Horizontal cone
                    pos_y = center_y + offset
                    pos_x = center_x
                else:  # Vertical cone
                    pos_y = center_y
                    pos_x = center_x + offset
                
                if self.game.is_valid_position(pos_y, pos_x):
                    cone_positions.append((pos_y, pos_x))
        
        # Count enemies in cone positions
        for enemy in self.game.units:
            if (enemy.player != unit.player and enemy.is_alive() and
                (enemy.y, enemy.x) in cone_positions):
                enemies_hit += 1
                
        return enemies_hit

    def _evaluate_knockback_tactical_value(self, unit: 'Unit', target: 'Unit') -> int:
        """
        Evaluate the tactical value of knocking back the target.
        
        Args:
            unit: The FOWL_CONTRIVANCE unit
            target: The target to be knocked back
            
        Returns:
            Tactical value score (0-30)
        """
        # Calculate knockback direction (away from unit)
        dy = target.y - unit.y
        dx = target.x - unit.x
        
        # Normalize direction
        if abs(dx) > abs(dy):
            knock_dir = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            knock_dir = (1 if dy > 0 else -1, 0)
        else:
            knock_dir = (1 if dy > 0 else -1, 1 if dx > 0 else -1)
        
        # Calculate knockback destination
        knockback_distance = 2  # Fragcrest knockback distance
        new_y = target.y + knock_dir[0] * knockback_distance
        new_x = target.x + knock_dir[1] * knockback_distance
        
        score = 0
        
        # Check if knockback destination is valid
        if not (self.game.is_valid_position(new_y, new_x) and 
                self.game.map.is_passable(new_y, new_x) and
                not self.game.get_unit_at(new_y, new_x)):
            # Can't knock back - no tactical value
            return 0
            
        # Tactical advantages of knockback:
        
        # 1. Push enemy away from our allies
        for ally in self.game.units:
            if (ally.player == unit.player and ally.is_alive() and ally != unit):
                current_dist = self.game.chess_distance(target.y, target.x, ally.y, ally.x)
                new_dist = self.game.chess_distance(new_y, new_x, ally.y, ally.x)
                if new_dist > current_dist:
                    score += 10  # Good - pushing enemy away from ally
                    break
                    
        # 2. Push enemy into corner or restricted position
        # Count blocked directions around knockback destination
        blocked_directions = 0
        for dy_check in [-1, 0, 1]:
            for dx_check in [-1, 0, 1]:
                if dy_check == 0 and dx_check == 0:
                    continue
                check_y, check_x = new_y + dy_check, new_x + dx_check
                if (not self.game.is_valid_position(check_y, check_x) or 
                    not self.game.map.is_passable(check_y, check_x)):
                    blocked_directions += 1
                    
        if blocked_directions >= 4:  # Pushing into very restricted area
            score += 20
        elif blocked_directions >= 2:  # Somewhat restricted
            score += 10
            
        # 3. Push enemy further from objectives (if we could identify them)
        # For now, just prefer pushing enemies toward map edges
        from boneglaive.utils.constants import HEIGHT, WIDTH
        edge_distance_before = min(target.y, target.x, HEIGHT - 1 - target.y, WIDTH - 1 - target.x)
        edge_distance_after = min(new_y, new_x, HEIGHT - 1 - new_y, WIDTH - 1 - new_x)
        if edge_distance_after < edge_distance_before:
            score += 5  # Small bonus for pushing toward edges
            
        return min(score, 30)  # Cap at 30 points

    def _process_gas_machinist(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a GAS_MACHINIST unit.
        Implements intelligent vapor placement and tactical positioning.
        Real players use GAS_MACHINIST for:
        - Supporting allies with healing/protection vapors
        - Controlling key positions with vapor clouds
        - Using Diverge for burst healing/damage when needed
        
        Args:
            unit: The GAS_MACHINIST unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Clear targets
        unit.move_target = None
        unit.attack_target = None
        unit.skill_target = None
        unit.selected_skill = None
        
        # Check if unit is trapped - trapped units can only attack, not move or use skills
        is_trapped = hasattr(unit, 'trapped_by') and unit.trapped_by is not None
        
        if is_trapped:
            logger.info(f"GAS_MACHINIST {unit.get_display_name()} is trapped - can only attack")
            # Try to attack if possible
            nearest_enemy = self._find_nearest_enemy(unit)
            if nearest_enemy:
                distance = self.game.chess_distance(unit.y, unit.x, nearest_enemy.y, nearest_enemy.x)
                if distance <= unit.attack_range:
                    unit.attack_target = (nearest_enemy.y, nearest_enemy.x)
                    logger.info(f"Trapped GAS_MACHINIST attacking {nearest_enemy.get_display_name()}")
            return
        
        # Get available skills and charges
        available_skills = []
        try:
            available_skills = unit.get_available_skills()
            logger.info(f"GAS_MACHINIST has {len(available_skills)} skills available: {[skill.name for skill in available_skills]}")
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            
        # Get Effluvium charges
        effluvium_charges = 0
        if hasattr(unit, 'passive_skill') and unit.passive_skill and hasattr(unit.passive_skill, 'charges'):
            effluvium_charges = unit.passive_skill.charges
            
        logger.info(f"GAS_MACHINIST has {effluvium_charges} Effluvium charges")
        
        # Find allies and enemies
        allies = [u for u in self.game.units if u.player == unit.player and u.is_alive() and u != unit]
        enemies = [u for u in self.game.units if u.player != unit.player and u.is_alive()]
        
        if not enemies:
            logger.info("No enemies found for GAS_MACHINIST")
            return
            
        # NEW PRIORITY SYSTEM: Position first, then act
        
        # Priority 1: Emergency Diverge for critically wounded allies in range
        if self._should_use_emergency_diverge(unit, allies, enemies, available_skills, effluvium_charges):
            return
            
        # Priority 2: Move to optimal support position if current position is poor
        current_position_score = self._evaluate_support_position(unit, unit.y, unit.x, allies, enemies)
        best_position = self._find_best_support_position(unit, allies, enemies)
        
        if best_position:
            best_position_score = self._evaluate_support_position(unit, best_position[0], best_position[1], allies, enemies)
            # Move if the new position is better (at least 15 points better)
            if best_position_score > current_position_score + 15:
                unit.move_target = best_position
                logger.info(f"GAS_MACHINIST moving from score {current_position_score} to {best_position_score} at {best_position}")
                return
        
        # Priority 3: Use Diverge tactically from current/planned position
        if self._should_use_tactical_diverge(unit, allies, enemies, available_skills, effluvium_charges):
            return
            
        # Priority 4: Place tactical vapors from good position
        if self._try_place_tactical_vapor(unit, allies, enemies, available_skills):
            return
            
        # Priority 5: Attack if in good position and have target
        nearest_enemy = self._find_nearest_enemy(unit)
        if nearest_enemy and current_position_score >= 15:  # Attack from reasonable positions
            distance = self.game.chess_distance(unit.y, unit.x, nearest_enemy.y, nearest_enemy.x)
            if distance <= unit.attack_range:
                unit.attack_target = (nearest_enemy.y, nearest_enemy.x)
                logger.info(f"GAS_MACHINIST attacking {nearest_enemy.get_display_name()} from good position")
                return
        
        # Priority 6: Move to any better position if we didn't move yet
        if best_position and best_position_score > current_position_score + 5:
            unit.move_target = best_position
            logger.info(f"GAS_MACHINIST making fallback move to {best_position}")
            return
        
        # Priority 7: Basic fallback - attack nearest enemy or move towards allies
        if nearest_enemy:
            distance = self.game.chess_distance(unit.y, unit.x, nearest_enemy.y, nearest_enemy.x)
            if distance <= unit.attack_range:
                unit.attack_target = (nearest_enemy.y, nearest_enemy.x)
                logger.info(f"GAS_MACHINIST fallback attack on {nearest_enemy.get_display_name()}")
                return
        
        # Last resort: move to any better position at all
        if best_position and best_position_score > current_position_score:
            unit.move_target = best_position
            logger.info(f"GAS_MACHINIST last resort move to {best_position}")
            return
            
        logger.info("GAS_MACHINIST has no valid actions - staying put")

    def _process_heinous_vapor(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a HEINOUS_VAPOR unit.
        Implements intelligent vapor positioning and tactical movement.
        Real players use HEINOUS_VAPOR for:
        - Positioning to maximize area effect coverage
        - Supporting allies or harassing enemies based on vapor type
        - Moving to block chokepoints or control territory
        
        Args:
            unit: The HEINOUS_VAPOR unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Clear targets
        unit.move_target = None
        unit.attack_target = None
        unit.skill_target = None
        unit.selected_skill = None
        
        # Find allies and enemies
        allies = [u for u in self.game.units if u.player == unit.player and u.is_alive() and u != unit]
        enemies = [u for u in self.game.units if u.player != unit.player and u.is_alive()]
        
        # Get vapor type to determine behavior
        vapor_type = getattr(unit, 'vapor_type', None)
        logger.info(f"HEINOUS_VAPOR {vapor_type} processing turn")
        
        if vapor_type in ["BROACHING", "SAFETY", "COOLANT"]:
            # Support vapors - position to help allies
            best_position = self._find_best_support_vapor_position(unit, allies, vapor_type)
        elif vapor_type == "CUTTING":
            # Offensive vapor - position to damage enemies
            best_position = self._find_best_offensive_vapor_position(unit, enemies)
        else:
            # Unknown vapor type - default to support
            best_position = self._find_best_support_vapor_position(unit, allies, "SAFETY")
            
        if best_position:
            unit.move_target = best_position
            logger.info(f"HEINOUS_VAPOR {vapor_type} moving to position {best_position}")
        else:
            logger.info(f"HEINOUS_VAPOR {vapor_type} staying in current position")

    def _should_use_emergency_diverge(self, unit: 'Unit', allies: list, enemies: list, available_skills: list, charges: int) -> bool:
        """
        Use Diverge only in emergency situations with critically wounded allies in effective range.
        This prevents wasteful Diverge usage in isolation.
        """
        # Find Diverge skill
        diverge_skill = None
        for skill in available_skills:
            if hasattr(skill, 'name') and skill.name == "Diverge":
                diverge_skill = skill
                break
                
        if not diverge_skill:
            return False
            
        # Use in emergencies: allies below 60% health within effective range
        critically_wounded = []
        for ally in allies:
            if ally.hp <= ally.max_hp * 0.6:  # Below 60% health
                distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)
                if distance <= 4:  # Within Diverge effective range
                    critically_wounded.append(ally)
        
        # Need at least 2 critically wounded allies to justify emergency Diverge
        if len(critically_wounded) >= 2:
            target_pos = (unit.y, unit.x)  # Always self-diverge in emergencies
            if diverge_skill.use(unit, target_pos, self.game):
                logger.info(f"GAS_MACHINIST using emergency Diverge for {len(critically_wounded)} critical allies")
                return True
                
        return False

    def _should_use_tactical_diverge(self, unit: 'Unit', allies: list, enemies: list, available_skills: list, charges: int) -> bool:
        """
        Use Diverge tactically when positioned well and it provides significant value.
        """
        # Find Diverge skill
        diverge_skill = None
        for skill in available_skills:
            if hasattr(skill, 'name') and skill.name == "Diverge":
                diverge_skill = skill
                break
                
        if not diverge_skill:
            return False
            
        # Check if we have vapors to potentially split
        player_vapors = [u for u in self.game.units 
                        if u.player == unit.player and u.is_alive() and 
                        u.type == UnitType.HEINOUS_VAPOR]
        
        # Evaluate tactical value
        score = 0
        
        # Count allies that would benefit from healing within range
        wounded_in_range = 0
        for ally in allies:
            if ally.hp < ally.max_hp * 0.8:  # Less than 80% health
                distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)
                if distance <= 3:  # Within coolant gas effective range
                    wounded_in_range += 1
                    score += 20
        
        # Count enemies that would be threatened by cutting gas
        enemies_in_range = 0
        for enemy in enemies:
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            if distance <= 3:  # Within cutting gas effective range
                enemies_in_range += 1
                score += 10
        
        # Bonus for having charges to extend duration
        if charges >= 3:
            score += 20
        elif charges >= 2:
            score += 10
        
        # Penalty for splitting well-positioned vapors
        if player_vapors:
            for vapor in player_vapors:
                # Check if vapor is well-positioned (near allies/enemies as appropriate)
                vapor_value = self._evaluate_vapor_position(vapor, allies, enemies)
                if vapor_value > 30:  # Well positioned vapor
                    score -= 15  # Penalty for potentially splitting it
        
        # Only use if we have reasonable tactical value and positioning  
        threshold = 30 if hasattr(self, 'difficulty') and self.difficulty == 'HARD' else 40
        logger.debug(f"Tactical Diverge score: {score} (threshold: {threshold})")
        
        if score >= threshold and (wounded_in_range >= 2 or enemies_in_range >= 2):
            # Choose best target - prefer splitting distant vapors over self
            target_pos = None
            
            if player_vapors and wounded_in_range >= 3:
                # Find vapor farthest from wounded allies to split
                best_vapor = None
                best_distance = 0
                for vapor in player_vapors:
                    min_distance_to_wounded = min([self.game.chess_distance(vapor.y, vapor.x, ally.y, ally.x) 
                                                  for ally in allies if ally.hp < ally.max_hp], default=999)
                    if min_distance_to_wounded > best_distance:
                        best_distance = min_distance_to_wounded
                        best_vapor = vapor
                        
                if best_vapor and best_distance >= 4:  # Only split if vapor is distant
                    target_pos = (best_vapor.y, best_vapor.x)
            
            if not target_pos:  # Self-diverge
                target_pos = (unit.y, unit.x)
                
            if diverge_skill.use(unit, target_pos, self.game):
                logger.info(f"GAS_MACHINIST using tactical Diverge at {target_pos} (score: {score})")
                return True
                
        return False
    
    def _evaluate_support_position(self, unit: 'Unit', pos_y: int, pos_x: int, allies: list, enemies: list) -> int:
        """
        Evaluate how good a position is for GAS_MACHINIST support role.
        Returns a numerical score where higher is better.
        """
        score = 0
        
        # Core principle: Position to maximize vapor effectiveness
        
        # Distance to wounded allies (closer is better, but not too close)
        for ally in allies:
            if ally.hp < ally.max_hp:
                distance = self.game.chess_distance(pos_y, pos_x, ally.y, ally.x)
                if distance <= 2:  # Optimal support range
                    score += 25
                elif distance <= 4:  # Good support range  
                    score += 15
                elif distance <= 6:  # Acceptable range
                    score += 5
        
        # Distance to all allies for general support
        for ally in allies:
            distance = self.game.chess_distance(pos_y, pos_x, ally.y, ally.x)
            if distance <= 3:  # Within vapor placement range
                score += 10
                
        # Distance to enemies - prefer positions that can threaten but aren't too exposed
        enemy_threat = 0
        for enemy in enemies:
            distance = self.game.chess_distance(pos_y, pos_x, enemy.y, enemy.x)
            if distance == 1:  # Too close - very dangerous
                score -= 30
            elif distance == 2:  # Close but manageable
                score -= 10
                enemy_threat += 1
            elif distance <= 4:  # Good tactical distance
                score += 5
                enemy_threat += 1
        
        # Bonus for being able to threaten multiple enemies without being overwhelmed
        if enemy_threat >= 2 and enemy_threat <= 4:
            score += 20
            
        # Terrain considerations
        if not self.game.is_valid_position(pos_y, pos_x) or not self.game.map.is_passable(pos_y, pos_x):
            return -999
            
        # Check for other units at position (excluding the unit being evaluated)
        unit_at_position = self.game.get_unit_at(pos_y, pos_x)
        if unit_at_position and unit_at_position != unit:
            return -999
            
        # Bonus for central positioning
        map_center_y = self.game.map.height // 2
        map_center_x = self.game.map.width // 2
        distance_from_center = self.game.chess_distance(pos_y, pos_x, map_center_y, map_center_x)
        if distance_from_center <= 3:
            score += 15
        elif distance_from_center <= 6:
            score += 5
            
        return score
    
    def _evaluate_vapor_position(self, vapor_unit: 'Unit', allies: list, enemies: list) -> int:
        """
        Evaluate how well-positioned a vapor is for its role.
        """
        score = 0
        vapor_type = getattr(vapor_unit, 'vapor_type', 'UNKNOWN')
        
        if vapor_type == "COOLANT":
            # Healing vapor should be near wounded allies
            for ally in allies:
                if ally.hp < ally.max_hp:
                    distance = self.game.chess_distance(vapor_unit.y, vapor_unit.x, ally.y, ally.x)
                    if distance <= 1:
                        score += 25
                    elif distance <= 2:
                        score += 10
        elif vapor_type == "CUTTING":
            # Damage vapor should be near enemies
            for enemy in enemies:
                distance = self.game.chess_distance(vapor_unit.y, vapor_unit.x, enemy.y, enemy.x)
                if distance <= 1:
                    score += 25
                elif distance <= 2:
                    score += 10
        else:
            # Generic support vapor
            for ally in allies:
                distance = self.game.chess_distance(vapor_unit.y, vapor_unit.x, ally.y, ally.x)
                if distance <= 1:
                    score += 15
                    
        return score

    def _try_place_tactical_vapor(self, unit: 'Unit', allies: list, enemies: list, available_skills: list) -> bool:
        """
        Try to place a tactical vapor.
        Real players choose vapor type based on situation.
        
        Args:
            unit: The GAS_MACHINIST unit
            allies: List of allied units
            enemies: List of enemy units
            available_skills: Available skills
            
        Returns:
            True if a vapor was placed, False otherwise
        """
        # Find available vapor skills
        broaching_skill = None
        safety_skill = None
        
        for skill in available_skills:
            if hasattr(skill, 'name'):
                if skill.name == "Broaching Gas":
                    broaching_skill = skill
                elif skill.name == "Saft-E-Gas":
                    safety_skill = skill
        
        # Improved vapor selection based on comprehensive threat assessment
        wounded_allies = [ally for ally in allies if ally.hp < ally.max_hp]
        critically_wounded = [ally for ally in allies if ally.hp < ally.max_hp * 0.5]
        allies_under_threat = self._count_allies_under_comprehensive_threat(allies, enemies)
        
        # Decision tree for vapor selection
        vapor_choice = None
        target_pos = None
        
        # Priority 1: Safety Gas for allies under significant threat
        if safety_skill and allies_under_threat >= 2:
            safety_pos = self._find_best_safety_gas_position(unit, allies, enemies)
            if safety_pos:
                safety_score = self._evaluate_vapor_placement(unit, safety_pos, allies, enemies, "SAFETY")
                if safety_score >= 30:  # Good position found
                    vapor_choice = (safety_skill, safety_pos, "Saft-E-Gas")
        
        # Priority 2: Broaching Gas if multiple wounded allies or mixed situation
        if broaching_skill and (not vapor_choice or len(wounded_allies) >= 2):
            broaching_pos = self._find_best_broaching_gas_position(unit, allies, enemies)
            if broaching_pos:
                broaching_score = self._evaluate_vapor_placement(unit, broaching_pos, allies, enemies, "BROACHING")
                # Choose broaching if it's significantly better or no safety option
                if not vapor_choice or broaching_score > 35:
                    vapor_choice = (broaching_skill, broaching_pos, "Broaching Gas")
        
        # Execute the chosen vapor placement
        if vapor_choice:
            skill, pos, skill_name = vapor_choice
            if skill.use(unit, pos, self.game):
                logger.info(f"GAS_MACHINIST placing {skill_name} at {pos}")
                return True
                
        return False

    def _count_allies_under_comprehensive_threat(self, allies: list, enemies: list) -> int:
        """Count allies under various types of threats (ranged, melee, abilities)."""
        threatened = 0
        for ally in allies:
            under_threat = False
            for enemy in enemies:
                distance = self.game.chess_distance(ally.y, ally.x, enemy.y, enemy.x)
                
                # Ranged threat
                enemy_range = enemy.attack_range
                if distance <= enemy_range and enemy_range > 1:
                    under_threat = True
                    break
                    
                # Immediate melee threat (next turn)
                if distance <= 2 and enemy.move_range >= 1:
                    under_threat = True
                    break
                    
                # Special ability threats (skills with range)
                if hasattr(enemy, 'active_skills'):
                    for skill in enemy.get_available_skills() if hasattr(enemy, 'get_available_skills') else []:
                        if hasattr(skill, 'range') and distance <= getattr(skill, 'range', 0) + 1:
                            under_threat = True
                            break
                    if under_threat:
                        break
                        
            if under_threat:
                threatened += 1
        return threatened
    
    def _evaluate_vapor_placement(self, unit: 'Unit', pos: Tuple[int, int], allies: list, enemies: list, vapor_type: str) -> int:
        """Evaluate the quality of a vapor placement position."""
        pos_y, pos_x = pos
        score = 0
        
        if vapor_type == "SAFETY":
            # Safety gas should protect threatened allies
            for ally in allies:
                distance = self.game.chess_distance(pos_y, pos_x, ally.y, ally.x)
                if distance <= 1:  # Within protection range
                    # Check if ally is actually threatened
                    ally_threatened = False
                    for enemy in enemies:
                        enemy_distance = self.game.chess_distance(ally.y, ally.x, enemy.y, enemy.x)
                        if enemy_distance <= enemy.attack_range:
                            ally_threatened = True
                            break
                    
                    if ally_threatened:
                        score += 30  # High value for protecting threatened allies
                    else:
                        score += 10  # Some value for general protection
        
        elif vapor_type == "BROACHING":
            # Broaching gas should support allies and clear debuffs
            for ally in allies:
                distance = self.game.chess_distance(pos_y, pos_x, ally.y, ally.x)
                if distance <= 1:  # Within cleansing range
                    if ally.hp < ally.max_hp:
                        score += 20  # Value for wounded allies who benefit from cleansing
                    else:
                        score += 10  # General support value
                        
            # Also consider damage potential to enemies
            for enemy in enemies:
                distance = self.game.chess_distance(pos_y, pos_x, enemy.y, enemy.x)
                if distance <= 1:  # Within damage range
                    score += 15  # Value for damaging enemies
        
        # Penalty for dangerous positions (too close to multiple enemies)
        nearby_enemies = sum(1 for enemy in enemies 
                            if self.game.chess_distance(pos_y, pos_x, enemy.y, enemy.x) <= 2)
        if nearby_enemies >= 3:
            score -= 20  # Penalty for very dangerous positions
        
        # Bonus for central positioning
        ally_center_y = sum(ally.y for ally in allies) // max(len(allies), 1)
        ally_center_x = sum(ally.x for ally in allies) // max(len(allies), 1)
        distance_from_ally_center = self.game.chess_distance(pos_y, pos_x, ally_center_y, ally_center_x)
        if distance_from_ally_center <= 2:
            score += 10
            
        return score

    def _find_best_safety_gas_position(self, unit: 'Unit', allies: list, enemies: list) -> Optional[Tuple[int, int]]:
        """Find the best position for Saft-E-Gas to protect allies."""
        best_pos = None
        best_score = 0
        
        # Check positions within range
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                pos_y = unit.y + dy
                pos_x = unit.x + dx
                
                if not self.game.is_valid_position(pos_y, pos_x):
                    continue
                if not self.game.map.is_passable(pos_y, pos_x):
                    continue
                if self.game.get_unit_at(pos_y, pos_x):
                    continue
                    
                distance = self.game.chess_distance(unit.y, unit.x, pos_y, pos_x)
                if distance > 3:  # Saft-E-Gas range
                    continue
                    
                # Score based on allies protected
                score = 0
                for ally in allies:
                    ally_distance = self.game.chess_distance(pos_y, pos_x, ally.y, ally.x)
                    if ally_distance <= 1:  # Within vapor cloud
                        score += 20
                        if ally.hp < ally.max_hp:
                            score += 10  # Bonus for wounded allies
                            
                if score > best_score:
                    best_score = score
                    best_pos = (pos_y, pos_x)
                    
        return best_pos

    def _find_best_broaching_gas_position(self, unit: 'Unit', allies: list, enemies: list) -> Optional[Tuple[int, int]]:
        """Find the best position for Broaching Gas."""
        best_pos = None
        best_score = 0
        
        # Check positions within range
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                pos_y = unit.y + dy
                pos_x = unit.x + dx
                
                if not self.game.is_valid_position(pos_y, pos_x):
                    continue
                if not self.game.map.is_passable(pos_y, pos_x):
                    continue
                if self.game.get_unit_at(pos_y, pos_x):
                    continue
                    
                distance = self.game.chess_distance(unit.y, unit.x, pos_y, pos_x)
                if distance > 3:  # Broaching Gas range
                    continue
                    
                # Score based on tactical value
                score = 0
                
                # Allies in range
                for ally in allies:
                    ally_distance = self.game.chess_distance(pos_y, pos_x, ally.y, ally.x)
                    if ally_distance <= 1:  # Within vapor cloud
                        score += 15
                        
                # Enemies in range (for damage)
                for enemy in enemies:
                    enemy_distance = self.game.chess_distance(pos_y, pos_x, enemy.y, enemy.x)
                    if enemy_distance <= 1:  # Within vapor cloud
                        score += 10
                        
                if score > best_score:
                    best_score = score
                    best_pos = (pos_y, pos_x)
                    
        return best_pos

    def _find_best_support_position(self, unit: 'Unit', allies: list, enemies: list) -> Optional[Tuple[int, int]]:
        """Find the best position for GAS_MACHINIST to support allies using improved evaluation."""
        best_pos = None
        best_score = -999
        
        move_range = unit.move_range
        
        for dy in range(-move_range, move_range + 1):
            for dx in range(-move_range, move_range + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx
                
                distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                if distance > move_range:
                    continue
                
                # CRITICAL: Pre-validate position before scoring to prevent invalid moves
                if not self._is_position_valid_for_movement(unit, new_y, new_x):
                    continue
                    
                # Use the comprehensive evaluation function
                score = self._evaluate_support_position(unit, new_y, new_x, allies, enemies)
                
                # Only consider positions with positive scores (valid positions)
                if score > best_score and score > 0:
                    best_score = score
                    best_pos = (new_y, new_x)
                    
        return best_pos if best_score > 15 else None  # Reasonable threshold for positioning
    
    def _is_position_valid_for_movement(self, unit: 'Unit', y: int, x: int) -> bool:
        """
        Validate that a position is actually reachable for movement.
        This prevents the infinite loop bug where AI tries to move to invalid positions.
        """
        # Basic bounds check
        if not self.game.is_valid_position(y, x):
            return False
        
        # Terrain passability check
        if not self.game.map.is_passable(y, x):
            return False
            
        # Unit collision check (excluding the moving unit itself)
        unit_at_position = self.game.get_unit_at(y, x)
        if unit_at_position and unit_at_position != unit:
            return False
            
        # Distance check (should already be done, but double-check)
        distance = self.game.chess_distance(unit.y, unit.x, y, x)
        if distance > unit.move_range:
            return False
            
        # Additional check: make sure it's not the same position (no point moving to same spot)
        if y == unit.y and x == unit.x:
            return False
            
        return True

    def _find_best_support_vapor_position(self, unit: 'Unit', allies: list, vapor_type: str) -> Optional[Tuple[int, int]]:
        """Find the best position for a support vapor to help allies."""
        best_pos = None
        best_score = 0
        
        move_range = unit.move_range
        
        # Special pursuit logic for COOLANT gas - actively chase wounded allies
        if vapor_type == "COOLANT":
            # Find the most wounded ally to pursue
            target_ally = None
            worst_health_ratio = 1.0
            
            for ally in allies:
                if ally.hp < ally.max_hp:
                    health_ratio = ally.hp / ally.max_hp
                    if health_ratio < worst_health_ratio:
                        worst_health_ratio = health_ratio
                        target_ally = ally
            
            if target_ally:
                # Move as close as possible to the wounded ally
                for dy in range(-move_range, move_range + 1):
                    for dx in range(-move_range, move_range + 1):
                        new_y = unit.y + dy
                        new_x = unit.x + dx
                        
                        if not self.game.is_valid_position(new_y, new_x):
                            continue
                        if not self.game.map.is_passable(new_y, new_x):
                            continue
                        if self.game.get_unit_at(new_y, new_x):
                            continue
                            
                        distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                        if distance > move_range:
                            continue
                        
                        # Score based on proximity to wounded ally
                        ally_distance = self.game.chess_distance(new_y, new_x, target_ally.y, target_ally.x)
                        score = 100 - ally_distance * 20  # Closer is much better
                        
                        # Huge bonus if we can touch the wounded ally
                        if ally_distance <= 1:
                            score += 200
                            # Extra bonus for critically wounded allies
                            if worst_health_ratio <= 0.3:
                                score += 100
                        
                        # Small bonus for being near other wounded allies too
                        for other_ally in allies:
                            if other_ally != target_ally and other_ally.hp < other_ally.max_hp:
                                other_distance = self.game.chess_distance(new_y, new_x, other_ally.y, other_ally.x)
                                if other_distance <= 1:
                                    score += 30
                        
                        if score > best_score:
                            best_score = score
                            best_pos = (new_y, new_x)
                
                logger.debug(f"COOLANT gas pursuing {target_ally.get_display_name()} (HP: {target_ally.hp}/{target_ally.max_hp})")
                return best_pos if best_score > 50 else None
        
        # Default logic for other support vapors (BROACHING, SAFETY)
        for dy in range(-move_range, move_range + 1):
            for dx in range(-move_range, move_range + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx
                
                if not self.game.is_valid_position(new_y, new_x):
                    continue
                if not self.game.map.is_passable(new_y, new_x):
                    continue
                if self.game.get_unit_at(new_y, new_x):
                    continue
                    
                distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                if distance > move_range:
                    continue
                    
                # Score based on allies that would be affected
                score = 0
                for ally in allies:
                    ally_distance = self.game.chess_distance(new_y, new_x, ally.y, ally.x)
                    if ally_distance <= 1:  # Within vapor effect range
                        score += 20
                        if vapor_type in ["BROACHING"] and ally.hp < ally.max_hp:
                            score += 15  # Bonus for healing vapors near wounded
                            
                if score > best_score:
                    best_score = score
                    best_pos = (new_y, new_x)
                    
        return best_pos if best_score > 15 else None

    def _find_best_offensive_vapor_position(self, unit: 'Unit', enemies: list) -> Optional[Tuple[int, int]]:
        """Find the best position for an offensive vapor to damage enemies."""
        best_pos = None
        best_score = 0
        
        move_range = unit.move_range
        
        # Special pursuit logic for CUTTING gas - actively chase enemies
        vapor_type = getattr(unit, 'vapor_type', None)
        if vapor_type == "CUTTING":
            # Find the best enemy to pursue (prioritize low health or isolated enemies)
            target_enemy = None
            best_target_score = 0
            
            for enemy in enemies:
                enemy_score = 0
                
                # Higher priority for low health enemies
                health_ratio = enemy.hp / enemy.max_hp
                if health_ratio <= 0.3:
                    enemy_score += 100  # Very high priority for low health
                elif health_ratio <= 0.5:
                    enemy_score += 50
                else:
                    enemy_score += 20
                    
                # Bonus for isolated enemies (easier to pursue)
                nearby_allies = sum(1 for ally in enemies 
                                  if ally != enemy and 
                                  self.game.chess_distance(enemy.y, enemy.x, ally.y, ally.x) <= 2)
                if nearby_allies == 0:
                    enemy_score += 30  # Isolated enemy bonus
                    
                if enemy_score > best_target_score:
                    best_target_score = enemy_score
                    target_enemy = enemy
            
            if target_enemy:
                # Move as close as possible to the target enemy
                for dy in range(-move_range, move_range + 1):
                    for dx in range(-move_range, move_range + 1):
                        new_y = unit.y + dy
                        new_x = unit.x + dx
                        
                        if not self.game.is_valid_position(new_y, new_x):
                            continue
                        if not self.game.map.is_passable(new_y, new_x):
                            continue
                        if self.game.get_unit_at(new_y, new_x):
                            continue
                            
                        distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                        if distance > move_range:
                            continue
                        
                        # Score based on proximity to target enemy
                        enemy_distance = self.game.chess_distance(new_y, new_x, target_enemy.y, target_enemy.x)
                        score = 100 - enemy_distance * 25  # Closer is much better
                        
                        # Huge bonus if we can touch the target enemy
                        if enemy_distance <= 1:
                            score += 250
                            # Extra bonus for low health enemies
                            if target_enemy.hp <= 5:
                                score += 150
                        
                        # Small bonus for being near other enemies too
                        for other_enemy in enemies:
                            if other_enemy != target_enemy:
                                other_distance = self.game.chess_distance(new_y, new_x, other_enemy.y, other_enemy.x)
                                if other_distance <= 1:
                                    score += 40
                        
                        if score > best_score:
                            best_score = score
                            best_pos = (new_y, new_x)
                
                logger.debug(f"CUTTING gas pursuing {target_enemy.get_display_name()} (HP: {target_enemy.hp}/{target_enemy.max_hp})")
                return best_pos if best_score > 50 else None
        
        # Default logic for other offensive vapors
        for dy in range(-move_range, move_range + 1):
            for dx in range(-move_range, move_range + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx
                
                if not self.game.is_valid_position(new_y, new_x):
                    continue
                if not self.game.map.is_passable(new_y, new_x):
                    continue
                if self.game.get_unit_at(new_y, new_x):
                    continue
                    
                distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                if distance > move_range:
                    continue
                    
                # Score based on enemies that would be affected
                score = 0
                for enemy in enemies:
                    enemy_distance = self.game.chess_distance(new_y, new_x, enemy.y, enemy.x)
                    if enemy_distance <= 1:  # Within vapor effect range
                        score += 25
                        if enemy.hp <= 5:  # Low health enemy
                            score += 10
                            
                if score > best_score:
                    best_score = score
                    best_pos = (new_y, new_x)
                    
        return best_pos if best_score > 20 else None

    def _process_delphic_appraiser(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a DELPHIC_APPRAISER unit.
        Implements intelligent furniture manipulation, Market Futures portal creation,
        Auction Curse DOT application, and Divine Depreciation area devastation.
        
        Args:
            unit: The DELPHIC_APPRAISER unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Always reset targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        unit.skill_target = None
        unit.selected_skill = None
        
        # Check if unit is trapped - trapped units can only attack, not move or use skills
        is_trapped = hasattr(unit, 'trapped_by') and unit.trapped_by is not None
        
        # Get enemies and allies
        enemies = [u for u in self.game.units 
                  if u.player != unit.player and u.is_alive() and u.type != UnitType.HEINOUS_VAPOR]
        allies = [u for u in self.game.units 
                 if u.player == unit.player and u.is_alive() and u != unit]
        
        # Get available skills
        available_skills = unit.get_available_skills()
        
        # Priority 1: Use Divine Depreciation for massive area damage if good opportunity
        if not is_trapped and self._should_use_divine_depreciation(unit, enemies, available_skills):
            return
            
        # Priority 2: Use Auction Curse on high-value targets
        if not is_trapped and self._should_use_auction_curse(unit, enemies, available_skills):
            return
            
        # Priority 3: Create Market Futures portals for team mobility
        if not is_trapped and self._should_use_market_futures(unit, allies, available_skills):
            return
            
        # Priority 4: Use existing Market Futures portals intelligently
        if not is_trapped and self._should_use_teleport_portal(unit, allies):
            return
            
        # Priority 5: Position for Valuation Oracle bonuses near furniture
        self._position_delphic_appraiser(unit, enemies, allies, is_trapped)

    def _should_use_divine_depreciation(self, unit: 'Unit', enemies: list, available_skills: list) -> bool:
        """
        Determine if Divine Depreciation should be used.
        Use when multiple enemies can be caught in the 7x7 area with good furniture density.
        """
        # Find Divine Depreciation skill
        divine_skill = None
        for skill in available_skills:
            if hasattr(skill, 'name') and skill.name == "Divine Depreciation":
                divine_skill = skill
                break
                
        if not divine_skill:
            return False
            
        # Find furniture pieces within range
        furniture_positions = []
        for y in range(self.game.map.height):
            for x in range(self.game.map.width):
                if self.game.map.is_furniture(y, x):
                    distance = self.game.chess_distance(unit.y, unit.x, y, x)
                    if distance <= divine_skill.range:
                        furniture_positions.append((y, x))
        
        if not furniture_positions:
            return False
            
        # Evaluate each furniture piece as a potential target
        best_score = 0
        best_target = None
        
        for furniture_pos in furniture_positions:
            # Count enemies in the 7x7 area around this furniture
            enemies_in_area = []
            furniture_in_area = []
            
            for dy in range(-3, 4):  # 7x7 area
                for dx in range(-3, 4):
                    check_y = furniture_pos[0] + dy
                    check_x = furniture_pos[1] + dx
                    
                    if not self.game.is_valid_position(check_y, check_x):
                        continue
                        
                    # Check for enemies
                    enemy_unit = self.game.get_unit_at(check_y, check_x)
                    if enemy_unit and enemy_unit.player != unit.player and enemy_unit.is_alive():
                        enemies_in_area.append(enemy_unit)
                        
                    # Check for other furniture (for damage calculation)
                    if (check_y, check_x) != furniture_pos and self.game.map.is_furniture(check_y, check_x):
                        furniture_in_area.append((check_y, check_x))
            
            # Calculate potential damage (simplified)
            estimated_avg_cosmic_value = len(furniture_in_area) * 4.5  # Average of 1-9
            estimated_damage = max(1, int(estimated_avg_cosmic_value / max(1, len(furniture_in_area))) - 1) if furniture_in_area else 1
            
            # Don't use Divine Depreciation if no enemies would be hit
            if len(enemies_in_area) == 0:
                continue
                
            # Score this target
            score = 0
            
            # Base score for number of enemies hit
            score += len(enemies_in_area) * 150
            
            # Bonus for estimated damage potential
            score += estimated_damage * 30
            
            # Bonus for hitting low-health enemies (potential kills)
            for enemy in enemies_in_area:
                if enemy.hp <= estimated_damage + 2:  # Likely kill
                    score += 200
                elif enemy.hp <= enemy.max_hp * 0.4:  # Low health
                    score += 75
                    
            # Bonus for furniture density (more chaotic effects)
            score += len(furniture_in_area) * 20
            
            if score > best_score:
                best_score = score
                best_target = furniture_pos
                
        # Use Divine Depreciation if score is high enough
        if best_score >= 200:  # At least one enemy with decent damage potential
            if divine_skill.use(unit, best_target, self.game):
                logger.info(f"DELPHIC_APPRAISER using Divine Depreciation on furniture at {best_target} (score: {best_score})")
                return True
                
        return False

    def _should_use_auction_curse(self, unit: 'Unit', enemies: list, available_skills: list) -> bool:
        """
        Determine if Auction Curse should be used.
        Target enemies in furniture-rich areas for maximum DOT damage.
        """
        # Find Auction Curse skill
        curse_skill = None
        for skill in available_skills:
            if hasattr(skill, 'name') and skill.name == "Auction Curse":
                curse_skill = skill
                break
                
        if not curse_skill:
            return False
            
        # Evaluate each enemy as a potential target
        best_score = 0
        best_target = None
        
        for enemy in enemies:
            # Check if enemy is in range
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            if distance > curse_skill.range:
                continue
                
            # Check if enemy already has auction curse (don't stack)
            if hasattr(enemy, 'auction_curse_duration') and enemy.auction_curse_duration > 0:
                continue
                
            # Count furniture within 2 tiles of enemy (curse damage area)
            furniture_count = 0
            total_cosmic_value = 0
            
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    check_y = enemy.y + dy
                    check_x = enemy.x + dx
                    
                    if not self.game.is_valid_position(check_y, check_x):
                        continue
                        
                    if self.game.map.is_furniture(check_y, check_x):
                        furniture_count += 1
                        # Estimate astral value (1-9 average = 5)
                        cosmic_value = self.game.map.get_cosmic_value(check_y, check_x, player=unit.player, game=self.game)
                        if cosmic_value:
                            total_cosmic_value += cosmic_value
                        else:
                            total_cosmic_value += 5  # Estimated average
            
            # Calculate score
            score = 0
            
            # Base score for furniture density (more damage per turn)
            score += furniture_count * 40
            score += total_cosmic_value * 10
            
            # Prioritize high-health enemies (they'll take more total damage)
            if enemy.hp >= 15:
                score += 100
            elif enemy.hp >= 10:
                score += 60
                
            # Prioritize dangerous enemy types
            if enemy.type == UnitType.FOWL_CONTRIVANCE:
                score += 120  # High priority - artillery threat
            elif enemy.type == UnitType.GRAYMAN:
                score += 100  # High priority - assassin threat
            elif enemy.type == UnitType.GLAIVEMAN:
                score += 80   # Medium-high priority
            elif enemy.type == UnitType.MANDIBLE_FOREMAN:
                score += 70   # Medium priority - control threat
                
            # Bonus if enemy is isolated from healing
            allies_near_enemy = 0
            for other_enemy in enemies:
                if other_enemy != enemy:
                    if self.game.chess_distance(enemy.y, enemy.x, other_enemy.y, other_enemy.x) <= 2:
                        allies_near_enemy += 1
            if allies_near_enemy == 0:
                score += 80  # Isolated target
                
            if score > best_score:
                best_score = score
                best_target = enemy
                
        # Use Auction Curse if score is high enough
        if best_score >= 80:  # Minimum threshold for usefulness
            if curse_skill.use(unit, (best_target.y, best_target.x), self.game):
                logger.info(f"DELPHIC_APPRAISER using Auction Curse on {best_target.get_display_name()} (score: {best_score})")
                return True
                
        return False

    def _should_use_market_futures(self, unit: 'Unit', allies: list, available_skills: list) -> bool:
        """
        Determine if Market Futures should be used to create teleport portals.
        Create portals in strategic locations for team mobility.
        """
        # Find Market Futures skill
        futures_skill = None
        for skill in available_skills:
            if hasattr(skill, 'name') and skill.name == "Market Futures":
                futures_skill = skill
                break
                
        if not futures_skill:
            return False
            
        # Check if we already have active portals (don't create too many)
        active_portals = 0
        if hasattr(self.game, 'teleport_anchors'):
            for anchor_pos, anchor_data in self.game.teleport_anchors.items():
                if anchor_data['active'] and anchor_data['creator'] == unit:
                    active_portals += 1
                    
        if active_portals >= 2:  # Limit to 2 active portals
            return False
            
        # Find furniture pieces within range
        furniture_positions = []
        for y in range(self.game.map.height):
            for x in range(self.game.map.width):
                if self.game.map.is_furniture(y, x):
                    distance = self.game.chess_distance(unit.y, unit.x, y, x)
                    if distance <= futures_skill.range:
                        furniture_positions.append((y, x))
        
        if not furniture_positions:
            return False
            
        # Evaluate each furniture piece as a potential portal location
        best_score = 0
        best_target = None
        
        for furniture_pos in furniture_positions:
            # Skip if already has a portal
            if hasattr(self.game, 'teleport_anchors') and furniture_pos in self.game.teleport_anchors:
                if self.game.teleport_anchors[furniture_pos]['active']:
                    continue
                    
            score = 0
            
            # Get estimated astral value for range calculation
            cosmic_value = self.game.map.get_cosmic_value(furniture_pos[0], furniture_pos[1], player=unit.player, game=self.game)
            if not cosmic_value:
                cosmic_value = 5  # Estimated average
                
            # Score based on strategic positioning
            
            # 1. Central location bonus (can reach more of the map)
            center_y, center_x = self.game.map.height // 2, self.game.map.width // 2
            distance_to_center = self.game.chess_distance(furniture_pos[0], furniture_pos[1], center_y, center_x)
            score += max(0, 100 - distance_to_center * 10)
            
            # 2. Distance from current team position (expand reach)
            min_ally_distance = float('inf')
            for ally in allies:
                ally_distance = self.game.chess_distance(furniture_pos[0], furniture_pos[1], ally.y, ally.x)
                min_ally_distance = min(min_ally_distance, ally_distance)
            if min_ally_distance != float('inf'):
                if min_ally_distance >= 6:  # Good for expanding reach
                    score += 150
                elif min_ally_distance >= 4:
                    score += 100
                elif min_ally_distance >= 2:
                    score += 50
                    
            # 3. High astral value bonus (longer teleport range)
            score += cosmic_value * 15
            
            # 4. Near other furniture bonus (Valuation Oracle synergy)
            nearby_furniture = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    check_y = furniture_pos[0] + dy
                    check_x = furniture_pos[1] + dx
                    if (dy != 0 or dx != 0) and self.game.is_valid_position(check_y, check_x):
                        if self.game.map.is_furniture(check_y, check_x):
                            nearby_furniture += 1
            score += nearby_furniture * 25
            
            # 5. Safety bonus (not too close to enemies)
            enemies = [u for u in self.game.units 
                      if u.player != unit.player and u.is_alive() and u.type != UnitType.HEINOUS_VAPOR]
            min_enemy_distance = float('inf')
            for enemy in enemies:
                enemy_distance = self.game.chess_distance(furniture_pos[0], furniture_pos[1], enemy.y, enemy.x)
                min_enemy_distance = min(min_enemy_distance, enemy_distance)
            if min_enemy_distance != float('inf') and min_enemy_distance >= 4:
                score += 80  # Safe distance
            elif min_enemy_distance >= 2:
                score += 40  # Somewhat safe
                
            if score > best_score:
                best_score = score
                best_target = furniture_pos
                
        # Create Market Futures portal if score is high enough
        if best_score >= 120:  # Minimum threshold for strategic value
            if futures_skill.use(unit, best_target, self.game):
                logger.info(f"DELPHIC_APPRAISER creating Market Futures portal at {best_target} (score: {best_score})")
                return True
                
        return False

    def _should_use_teleport_portal(self, unit: 'Unit', allies: list) -> bool:
        """
        Check if DELPHIC_APPRAISER should use an existing Market Futures portal.
        Uses portals for repositioning or escaping danger.
        """
        if not hasattr(self.game, 'teleport_anchors'):
            return False
            
        # Find adjacent active portals
        adjacent_portals = []
        for anchor_pos, anchor_data in self.game.teleport_anchors.items():
            if not anchor_data['active']:
                continue
                
            distance = self.game.chess_distance(unit.y, unit.x, anchor_pos[0], anchor_pos[1])
            if distance <= 1:  # Adjacent to portal
                adjacent_portals.append((anchor_pos, anchor_data))
                
        if not adjacent_portals:
            return False
            
        # Evaluate teleport destinations for each portal
        best_score = 0
        best_portal = None
        best_destination = None
        
        enemies = [u for u in self.game.units 
                  if u.player != unit.player and u.is_alive() and u.type != UnitType.HEINOUS_VAPOR]
        
        for anchor_pos, anchor_data in adjacent_portals:
            cosmic_value = anchor_data['cosmic_value']
            
            # Find valid destinations within astral value range
            for dy in range(-cosmic_value, cosmic_value + 1):
                for dx in range(-cosmic_value, cosmic_value + 1):
                    dest_y = anchor_pos[0] + dy
                    dest_x = anchor_pos[1] + dx
                    
                    if not self.game.is_valid_position(dest_y, dest_x):
                        continue
                    if not self.game.map.is_passable(dest_y, dest_x):
                        continue
                    if self.game.get_unit_at(dest_y, dest_x):
                        continue
                        
                    distance = self.game.chess_distance(anchor_pos[0], anchor_pos[1], dest_y, dest_x)
                    if distance > cosmic_value:
                        continue
                        
                    # Score this destination
                    score = 0
                    
                    # 1. Safety from enemies
                    min_enemy_distance = float('inf')
                    for enemy in enemies:
                        enemy_distance = self.game.chess_distance(dest_y, dest_x, enemy.y, enemy.x)
                        min_enemy_distance = min(min_enemy_distance, enemy_distance)
                    
                    if min_enemy_distance != float('inf'):
                        if min_enemy_distance >= 5:
                            score += 150  # Very safe
                        elif min_enemy_distance >= 3:
                            score += 100  # Moderately safe
                        elif min_enemy_distance >= 2:
                            score += 50   # Somewhat safe
                        else:
                            score -= 100  # Too close to enemies
                            
                    # 2. Near furniture for Valuation Oracle
                    nearby_furniture = 0
                    for fdy in range(-1, 2):
                        for fdx in range(-1, 2):
                            check_y = dest_y + fdy
                            check_x = dest_x + fdx
                            if (fdy != 0 or fdx != 0) and self.game.is_valid_position(check_y, check_x):
                                if self.game.map.is_furniture(check_y, check_x):
                                    nearby_furniture += 1
                    score += nearby_furniture * 40
                    
                    # 3. Distance from current position (escape bonus)
                    current_distance = self.game.chess_distance(unit.y, unit.x, dest_y, dest_x)
                    if current_distance >= 4:
                        score += 80  # Good escape distance
                        
                    # 4. Immediate danger check (high priority for escaping)
                    immediate_danger = False
                    for enemy in enemies:
                        if self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x) <= 2:
                            if enemy.hp > unit.hp * 0.8:  # Dangerous enemy nearby
                                immediate_danger = True
                                break
                    if immediate_danger:
                        score += 200  # Escape bonus
                        
                    if score > best_score:
                        best_score = score
                        best_portal = anchor_pos
                        best_destination = (dest_y, dest_x)
                        
        # Use portal if score is high enough
        if best_score >= 100:  # Minimum threshold for teleport value
            # Simulate teleport activation (this would normally be done through UI)
            from boneglaive.game.skills.delphic_appraiser import MarketFuturesSkill
            market_skill = MarketFuturesSkill()
            if market_skill.activate_teleport(unit, best_portal, best_destination, self.game, self.ui):
                logger.info(f"DELPHIC_APPRAISER using Market Futures portal to teleport to {best_destination} (score: {best_score})")
                return True
                
        return False

    def _position_delphic_appraiser(self, unit: 'Unit', enemies: list, allies: list, is_trapped: bool) -> None:
        """
        Position DELPHIC_APPRAISER for optimal furniture adjacency and safety.
        Prioritizes Valuation Oracle bonuses while maintaining tactical positioning.
        """
        if is_trapped:
            # If trapped, can only attack
            target = self._find_closest_enemy(unit, enemies)
            if target:
                distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
                attack_range = unit.get_effective_stats()['attack_range']
                if distance <= attack_range:
                    unit.attack_target = (target.y, target.x)
                    logger.info(f"DELPHIC_APPRAISER (trapped) attacking {target.get_display_name()}")
            return
            
        # Find best position considering furniture adjacency and safety
        best_score = -1
        best_position = None
        best_attack_target = None
        
        move_range = unit.get_effective_stats()['move_range']
        attack_range = unit.get_effective_stats()['attack_range']
        
        # Evaluate all possible movement positions
        for dy in range(-move_range, move_range + 1):
            for dx in range(-move_range, move_range + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx
                
                if not self.game.is_valid_position(new_y, new_x):
                    continue
                if not self.game.map.is_passable(new_y, new_x):
                    continue
                if self.game.get_unit_at(new_y, new_x):
                    continue
                    
                distance = self.game.chess_distance(unit.y, unit.x, new_y, new_x)
                if distance > move_range:
                    continue
                    
                # Score this position
                score = 0
                
                # 1. Furniture adjacency bonus (Valuation Oracle)
                adjacent_furniture = 0
                for fdy in range(-1, 2):
                    for fdx in range(-1, 2):
                        if fdy == 0 and fdx == 0:
                            continue
                        check_y = new_y + fdy
                        check_x = new_x + fdx
                        if self.game.is_valid_position(check_y, check_x):
                            if self.game.map.is_furniture(check_y, check_x):
                                adjacent_furniture += 1
                                
                if adjacent_furniture > 0:
                    score += 200 + adjacent_furniture * 50  # High priority for Valuation Oracle
                    
                # 2. Safety from enemies
                min_enemy_distance = float('inf')
                for enemy in enemies:
                    enemy_distance = self.game.chess_distance(new_y, new_x, enemy.y, enemy.x)
                    min_enemy_distance = min(min_enemy_distance, enemy_distance)
                    
                if min_enemy_distance != float('inf'):
                    if min_enemy_distance >= 4:
                        score += 100  # Safe distance
                    elif min_enemy_distance >= 2:
                        score += 50   # Moderate distance
                    elif min_enemy_distance == 1:
                        score -= 150  # Too close, dangerous
                        
                # 3. Attack opportunity
                attack_target = None
                for enemy in enemies:
                    enemy_distance = self.game.chess_distance(new_y, new_x, enemy.y, enemy.x)
                    if enemy_distance <= attack_range:
                        attack_target = enemy
                        score += 80  # Can attack from this position
                        
                        # Prioritize dangerous targets
                        if enemy.type == UnitType.FOWL_CONTRIVANCE:
                            score += 60
                        elif enemy.type == UnitType.GRAYMAN:
                            score += 50
                        elif enemy.hp <= 8:  # Low health
                            score += 40
                        break
                        
                # 4. Team coordination (stay somewhat close to allies)
                if allies:
                    avg_ally_distance = sum(self.game.chess_distance(new_y, new_x, ally.y, ally.x) 
                                          for ally in allies) / len(allies)
                    if avg_ally_distance <= 5:
                        score += 30  # Good team positioning
                    elif avg_ally_distance >= 8:
                        score -= 20  # Too far from team
                        
                if score > best_score:
                    best_score = score
                    best_position = (new_y, new_x)
                    best_attack_target = attack_target
                    
        # Execute best action
        if best_position and best_position != (unit.y, unit.x):
            unit.move_target = best_position
            logger.info(f"DELPHIC_APPRAISER moving to {best_position} (score: {best_score})")
        
        if best_attack_target:
            unit.attack_target = (best_attack_target.y, best_attack_target.x)
            logger.info(f"DELPHIC_APPRAISER attacking {best_attack_target.get_display_name()}")
        elif not best_position:
            # No good movement, try to attack from current position
            target = self._find_closest_enemy(unit, enemies)
            if target:
                distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
                if distance <= attack_range:
                    unit.attack_target = (target.y, target.x)
                    logger.info(f"DELPHIC_APPRAISER attacking {target.get_display_name()} from current position")

    def _process_derelictionist(self, unit: 'Unit', use_coordination: bool = False) -> None:
        """
        Process actions for a DERELICTIONIST unit with ultra-strategic thinking.

        The DERELICTIONIST is a pure support unit that:
        - NEVER attacks (too weak, focus is pure support)
        - Uses distance-based mechanics optimally
        - Leverages Severance passive for skill-then-move combos
        - Prioritizes ally survival and positioning

        Strategic priorities:
        1. Emergency intervention (save dying allies)
        2. Optimal distance healing/cleansing
        3. Strategic ally repositioning
        4. Preventive protection
        5. Positioning for future turns

        Args:
            unit: The DERELICTIONIST unit to process
            use_coordination: Whether to use group coordination tactics
        """
        # Reset all targets
        unit.move_target = None
        unit.attack_target = None  # NEVER attack - pure support
        unit.skill_target = None
        unit.selected_skill = None

        logger.info(f"DERELICTIONIST {unit.get_display_name()} beginning ultra-strategic analysis")

        # Check constraints
        is_trapped = hasattr(unit, 'trapped_by') and unit.trapped_by is not None

        # Get allies and enemies for analysis
        allies = [u for u in self.game.units
                 if u.player == unit.player and u.is_alive() and u != unit]
        enemies = [u for u in self.game.units
                  if u.player != unit.player and u.is_alive() and u.type != UnitType.HEINOUS_VAPOR]

        if not allies:
            logger.info("DERELICTIONIST has no allies - positioning defensively")
            self._derelictionist_defensive_positioning(unit, enemies, is_trapped)
            return

        # Get available skills
        available_skills = unit.get_available_skills()

        # ULTRA-STRATEGIC DECISION TREE

        # Priority 1: CRITICAL INTERVENTION - Save dying allies with Partition
        if self._derelictionist_emergency_save(unit, allies, enemies, available_skills):
            return

        # Priority 2: OPTIMAL DISTANCE HEALING - Use Vagal Run at distance 7+ for max benefit
        if self._derelictionist_distance_healing(unit, allies, available_skills):
            return

        # Priority 3: STRATEGIC REPOSITIONING - Use Derelict to move allies optimally
        if self._derelictionist_strategic_push(unit, allies, enemies, available_skills):
            return

        # Priority 4: STATUS CLEANSING - Clear negative effects from allies
        if self._derelictionist_status_cleansing(unit, allies, available_skills):
            return

        # Priority 5: PREVENTIVE PROTECTION - Shield vulnerable allies
        if self._derelictionist_preventive_shield(unit, allies, enemies, available_skills):
            return

        # Priority 6: OPTIMAL POSITIONING - Use Severance for tactical positioning
        self._derelictionist_optimal_positioning(unit, allies, enemies, is_trapped)

    def _derelictionist_emergency_save(self, unit: 'Unit', allies: list, enemies: list, available_skills: list) -> bool:
        """Emergency intervention to save critically endangered allies."""
        partition_skill = next((s for s in available_skills if hasattr(s, 'name') and s.name == "Partition"), None)
        if not partition_skill:
            return False

        # Find allies in mortal danger
        critical_allies = []

        for ally in allies:
            # Check if ally is critically low on health
            if ally.hp <= ally.max_hp * 0.3:
                # Calculate imminent threat level
                threat_level = 0
                for enemy in enemies:
                    enemy_distance = self.game.chess_distance(enemy.y, enemy.x, ally.y, ally.x)
                    enemy_stats = enemy.get_effective_stats()
                    can_reach = enemy_distance <= enemy_stats['move_range'] + enemy_stats['attack_range']

                    if can_reach and enemy_stats['attack'] >= ally.hp:
                        threat_level += 10  # Can kill next turn
                    elif can_reach:
                        threat_level += 5   # Can damage next turn

                if threat_level >= 10:  # Mortal danger
                    ally_distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)
                    if (ally_distance <= partition_skill.range and
                        not (hasattr(ally, 'partition_shield_active') and ally.partition_shield_active)):
                        critical_allies.append((ally, threat_level, ally_distance))

        if critical_allies:
            # Save the most threatened ally that's closest
            critical_allies.sort(key=lambda x: (-x[1], x[2]))  # Most threat, then closest
            target_ally = critical_allies[0][0]

            logger.info(f"EMERGENCY: Saving {target_ally.get_display_name()} from mortal danger")
            unit.skill_target = (target_ally.y, target_ally.x)
            unit.selected_skill = partition_skill
            unit.action_timestamp = self.game.action_counter
            self.game.action_counter += 1
            return True

        return False

    def _derelictionist_distance_healing(self, unit: 'Unit', allies: list, available_skills: list) -> bool:
        """Use Vagal Run at optimal distance (7+) for maximum healing benefit."""
        vagal_skill = next((s for s in available_skills if hasattr(s, 'name') and s.name == "Vagal Run"), None)
        if not vagal_skill:
            return False

        # Find damaged allies at optimal healing distance (7+)
        healing_targets = []

        for ally in allies:
            ally_distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)

            # Check if already has vagal run active
            if hasattr(ally, 'vagal_run_active') and ally.vagal_run_active:
                continue

            if ally_distance >= 7 and ally_distance <= vagal_skill.range:
                # Calculate healing benefit
                potential_healing = ally_distance - 6
                needed_healing = max(0, ally.max_hp - ally.hp)
                healing_value = min(potential_healing, needed_healing)

                # Also consider status cleansing value
                status_count = self._count_negative_effects(ally)

                total_value = healing_value + status_count * 2

                if total_value > 0:  # Only if there's actual benefit
                    healing_targets.append((ally, total_value, ally_distance))

        if healing_targets:
            # Prioritize highest value targets
            healing_targets.sort(key=lambda x: x[1], reverse=True)
            target_ally = healing_targets[0][0]

            logger.info(f"DISTANCE HEALING: Vagal Run on {target_ally.get_display_name()} at distance {healing_targets[0][2]} (value: {healing_targets[0][1]})")
            unit.skill_target = (target_ally.y, target_ally.x)
            unit.selected_skill = vagal_skill
            unit.action_timestamp = self.game.action_counter
            self.game.action_counter += 1
            return True

        return False

    def _derelictionist_strategic_push(self, unit: 'Unit', allies: list, enemies: list, available_skills: list) -> bool:
        """Use Derelict to strategically reposition allies for tactical advantage."""
        derelict_skill = next((s for s in available_skills if hasattr(s, 'name') and s.name == "Derelict"), None)
        if not derelict_skill:
            return False

        # Analyze each ally for strategic repositioning potential
        push_candidates = []

        for ally in allies:
            ally_distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)

            if ally_distance <= derelict_skill.range:
                # Calculate push direction
                dy = ally.y - unit.y
                dx = ally.x - unit.x
                if dy != 0:
                    dy = 1 if dy > 0 else -1
                if dx != 0:
                    dx = 1 if dx > 0 else -1

                # Simulate push outcome
                push_benefit = self._calculate_derelict_value(unit, ally, enemies, dy, dx)

                if push_benefit > 3:  # Meaningful benefit threshold
                    push_candidates.append((ally, push_benefit))

        if push_candidates:
            # Use the highest value push
            push_candidates.sort(key=lambda x: x[1], reverse=True)
            target_ally = push_candidates[0][0]

            logger.info(f"STRATEGIC PUSH: Derelict on {target_ally.get_display_name()} (benefit: {push_candidates[0][1]})")
            unit.skill_target = (target_ally.y, target_ally.x)
            unit.selected_skill = derelict_skill
            unit.action_timestamp = self.game.action_counter
            self.game.action_counter += 1
            return True

        return False

    def _derelictionist_status_cleansing(self, unit: 'Unit', allies: list, available_skills: list) -> bool:
        """Use Vagal Run to cleanse status effects from heavily debuffed allies."""
        vagal_skill = next((s for s in available_skills if hasattr(s, 'name') and s.name == "Vagal Run"), None)
        if not vagal_skill:
            return False

        # Find allies with multiple negative effects
        cleansing_targets = []

        for ally in allies:
            ally_distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)

            if (ally_distance <= vagal_skill.range and
                not (hasattr(ally, 'vagal_run_active') and ally.vagal_run_active)):

                status_count = self._count_negative_effects(ally)

                if status_count >= 2:  # Multiple negative effects
                    # Consider damage vs benefit
                    if ally_distance <= 5:
                        # Would deal damage - only worth it if ally is already damaged
                        damage = max(0, 6 - ally_distance)
                        if ally.hp > damage and ally.hp <= ally.max_hp * 0.6:
                            cleansing_value = status_count * 3
                            cleansing_targets.append((ally, cleansing_value))
                    else:
                        # Safe cleansing
                        cleansing_value = status_count * 4
                        cleansing_targets.append((ally, cleansing_value))

        if cleansing_targets:
            # Cleanse the most affected ally
            cleansing_targets.sort(key=lambda x: x[1], reverse=True)
            target_ally = cleansing_targets[0][0]

            logger.info(f"STATUS CLEANSING: Cleansing {target_ally.get_display_name()} (value: {cleansing_targets[0][1]})")
            unit.skill_target = (target_ally.y, target_ally.x)
            unit.selected_skill = vagal_skill
            unit.action_timestamp = self.game.action_counter
            self.game.action_counter += 1
            return True

        return False

    def _derelictionist_preventive_shield(self, unit: 'Unit', allies: list, enemies: list, available_skills: list) -> bool:
        """Use Partition to proactively protect vulnerable allies."""
        partition_skill = next((s for s in available_skills if hasattr(s, 'name') and s.name == "Partition"), None)
        if not partition_skill:
            return False

        # Find vulnerable allies who would benefit from protection
        protection_targets = []

        for ally in allies:
            ally_distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)

            if (ally_distance <= partition_skill.range and
                not (hasattr(ally, 'partition_shield_active') and ally.partition_shield_active)):

                # Calculate vulnerability score
                vulnerability = self._calculate_vulnerability(ally, enemies)

                if vulnerability >= 4:  # Meaningfully vulnerable
                    protection_targets.append((ally, vulnerability))

        if protection_targets:
            # Protect the most vulnerable ally
            protection_targets.sort(key=lambda x: x[1], reverse=True)
            target_ally = protection_targets[0][0]

            logger.info(f"PREVENTIVE SHIELD: Protecting {target_ally.get_display_name()} (vulnerability: {protection_targets[0][1]})")
            unit.skill_target = (target_ally.y, target_ally.x)
            unit.selected_skill = partition_skill
            unit.action_timestamp = self.game.action_counter
            self.game.action_counter += 1
            return True

        return False

    def _derelictionist_optimal_positioning(self, unit: 'Unit', allies: list, enemies: list, is_trapped: bool) -> None:
        """Position optimally, potentially using Severance enhanced movement."""
        if is_trapped:
            return

        # Determine movement range (potentially enhanced by Severance)
        base_move = unit.get_effective_stats()['move_range']
        # Severance gives +1 movement after using a skill
        enhanced_move = base_move + (1 if hasattr(unit, 'used_skill_this_turn') and unit.used_skill_this_turn else 0)

        best_position = None
        best_score = self._evaluate_position(unit.y, unit.x, unit, allies, enemies)

        # Evaluate all possible positions
        for dy in range(-enhanced_move, enhanced_move + 1):
            for dx in range(-enhanced_move, enhanced_move + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx

                if (self.game.is_valid_position(new_y, new_x) and
                    self.game.map.is_passable(new_y, new_x) and
                    not self.game.get_unit_at(new_y, new_x) and
                    self.game.chess_distance(unit.y, unit.x, new_y, new_x) <= enhanced_move):

                    score = self._evaluate_position(new_y, new_x, unit, allies, enemies)
                    if score > best_score:
                        best_score = score
                        best_position = (new_y, new_x)

        if best_position:
            unit.move_target = best_position
            logger.info(f"POSITIONING: Moving to {best_position} for tactical advantage")

    def _calculate_derelict_value(self, unit: 'Unit', ally: 'Unit', enemies: list, dy: int, dx: int) -> float:
        """Calculate the strategic value of using Derelict on an ally."""
        value = 0

        # Simulate push outcome
        final_y, final_x = ally.y, ally.x
        push_distance = 0

        for distance in range(1, 5):
            test_y = ally.y + (dy * distance)
            test_x = ally.x + (dx * distance)

            if (self.game.is_valid_position(test_y, test_x) and
                self.game.map.is_passable(test_y, test_x) and
                not self.game.get_unit_at(test_y, test_x)):
                final_y, final_x = test_y, test_x
                push_distance = distance
            else:
                break

        if push_distance > 0:
            # Calculate healing value
            final_distance = self.game.chess_distance(final_y, final_x, unit.y, unit.x)
            healing_value = final_distance if ally.hp < ally.max_hp else 0

            # Calculate safety improvement
            current_danger = sum(1 for enemy in enemies
                               if self.game.chess_distance(ally.y, ally.x, enemy.y, enemy.x) <= 3)
            new_danger = sum(1 for enemy in enemies
                           if self.game.chess_distance(final_y, final_x, enemy.y, enemy.x) <= 3)
            safety_value = max(0, current_danger - new_danger) * 3

            value = healing_value + safety_value

        return value

    def _count_negative_effects(self, ally: 'Unit') -> int:
        """Count negative status effects on an ally."""
        count = 0
        effects = ['derelicted', 'mired', 'jawline_affected', 'neural_shunt_affected', 'auction_curse_dot']

        for effect in effects:
            if hasattr(ally, effect) and getattr(ally, effect):
                count += 1

        # Special handling for radiation
        if hasattr(ally, 'radiation_stacks'):
            stacks = ally.radiation_stacks
            if (isinstance(stacks, list) and len(stacks) > 0) or (isinstance(stacks, int) and stacks > 0):
                count += 1

        if hasattr(ally, 'trapped_by') and ally.trapped_by:
            count += 1

        return count

    def _calculate_vulnerability(self, ally: 'Unit', enemies: list) -> float:
        """Calculate how vulnerable an ally is to enemy attacks."""
        vulnerability = 0

        # Health factor
        if ally.hp <= ally.max_hp * 0.4:
            vulnerability += 3
        elif ally.hp <= ally.max_hp * 0.7:
            vulnerability += 1

        # Threat proximity
        close_enemies = sum(1 for enemy in enemies
                          if self.game.chess_distance(ally.y, ally.x, enemy.y, enemy.x) <= 4)
        vulnerability += close_enemies

        # Unit type - support units are more valuable to protect
        if ally.type in [UnitType.DELPHIC_APPRAISER, UnitType.GAS_MACHINIST]:
            vulnerability += 2

        return vulnerability

    def _evaluate_position(self, y: int, x: int, unit: 'Unit', allies: list, enemies: list) -> float:
        """Evaluate the strategic value of a position."""
        score = 0

        # Distance to allies (want to be in support range)
        for ally in allies:
            distance = self.game.chess_distance(y, x, ally.y, ally.x)
            if distance <= 3:
                score += 3  # Perfect support range
            elif distance <= 6:
                score += 1  # Decent range
            else:
                score -= 0.5  # Too far

        # Safety from enemies
        for enemy in enemies:
            distance = self.game.chess_distance(y, x, enemy.y, enemy.x)
            if distance <= 2:
                score -= 5  # Too close
            elif distance <= 4:
                score -= 2  # Somewhat dangerous
            else:
                score += 0.5  # Good distance

        return score

    def _derelictionist_defensive_positioning(self, unit: 'Unit', enemies: list, is_trapped: bool) -> None:
        """Position defensively when no allies are present."""
        if is_trapped:
            return

        # Find safest position away from enemies
        best_position = None
        best_safety = 0
        move_range = unit.get_effective_stats()['move_range']

        for dy in range(-move_range, move_range + 1):
            for dx in range(-move_range, move_range + 1):
                new_y = unit.y + dy
                new_x = unit.x + dx

                if (self.game.is_valid_position(new_y, new_x) and
                    self.game.map.is_passable(new_y, new_x) and
                    not self.game.get_unit_at(new_y, new_x) and
                    self.game.chess_distance(unit.y, unit.x, new_y, new_x) <= move_range):

                    # Calculate safety score
                    safety = sum(self.game.chess_distance(new_y, new_x, enemy.y, enemy.x) for enemy in enemies)

                    if safety > best_safety:
                        best_safety = safety
                        best_position = (new_y, new_x)

        if best_position:
            unit.move_target = best_position
            logger.info(f"DEFENSIVE: Moving to safe position {best_position}")