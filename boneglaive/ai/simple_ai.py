#!/usr/bin/env python3
"""
Simple AI controller for Boneglaive.
This module contains a basic AI implementation focusing on the Glaiveman unit.
"""

import random
from typing import List, Tuple, Dict, Optional, TYPE_CHECKING
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType
from boneglaive.utils.message_log import message_log, MessageType

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.ui.game_ui import GameUI

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
        
        # Messaging
        self.enable_thinking_messages = True
    
    def process_turn(self) -> bool:
        """
        Process a full AI turn.
        
        Returns:
            True if the turn was processed successfully, False otherwise
        """
        logger.info("AI processing turn")
        
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
            
        # Ensure each unit has a target
        self._ensure_all_units_have_targets(ai_units)
            
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
        
    def _ensure_all_units_have_targets(self, ai_units: List['Unit']) -> None:
        """
        Make sure all AI units have an enemy target to pursue.
        
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
    
    def _process_unit(self, unit: 'Unit') -> None:
        """
        Process actions for a single unit.
        
        Args:
            unit: The unit to process
        """
        # For now, we'll only implement Glaiveman logic
        if unit.type == UnitType.GLAIVEMAN:
            self._process_glaiveman(unit)
        else:
            # Default behavior for other unit types
            logger.info(f"No specific AI logic for {unit.type.name}, using default behavior")
            self._process_default_unit(unit)
    
    def _process_glaiveman(self, unit: 'Unit') -> None:
        """
        Process actions for a Glaiveman unit.
        Implements aggressive movement and attack behavior.
        
        Args:
            unit: The Glaiveman unit to process
        """
        # Always reset move and attack targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        
        # 1. Find the nearest enemy
        nearest_enemy = self._find_nearest_enemy(unit)
        
        if not nearest_enemy:
            logger.info("No enemies found for Glaiveman to target")
            return
            
        logger.info(f"Glaiveman targeting enemy: {nearest_enemy.get_display_name()} at position ({nearest_enemy.y}, {nearest_enemy.x})")
        
        # 2. Check if we can attack the enemy from our current position
        can_attack = self._can_attack(unit, nearest_enemy)
        
        # 3. If we can attack, do it
        if can_attack:
            logger.info(f"Glaiveman attacking enemy at ({nearest_enemy.y}, {nearest_enemy.x})")
            unit.attack_target = (nearest_enemy.y, nearest_enemy.x)
        # 4. If we can't attack, try to move closer
        else:
            logger.info(f"Glaiveman moving towards enemy at ({nearest_enemy.y}, {nearest_enemy.x})")
            self._move_towards_enemy(unit, nearest_enemy)
            
            # Check if we can attack after moving
            can_attack_after_move = self._can_attack_after_move(unit, nearest_enemy)
            if can_attack_after_move:
                logger.info(f"Glaiveman attacking enemy after movement")
                # The attack_target is set in _can_attack_after_move
    
    def _process_default_unit(self, unit: 'Unit') -> None:
        """
        Default processing for units without specific AI logic.
        Aggressively moves towards the nearest enemy and attacks if possible.
        
        Args:
            unit: The unit to process
        """
        # Always reset move and attack targets at the start of processing
        unit.move_target = None
        unit.attack_target = None
        
        # 1. Find the nearest enemy
        nearest_enemy = self._find_nearest_enemy(unit)
        
        if not nearest_enemy:
            logger.info("No enemies found for unit to target")
            return
            
        logger.info(f"Unit targeting enemy: {nearest_enemy.get_display_name()} at position ({nearest_enemy.y}, {nearest_enemy.x})")
        
        # 2. Check if we can attack the enemy from our current position
        can_attack = self._can_attack(unit, nearest_enemy)
        
        # 3. If we can attack, do it
        if can_attack:
            logger.info(f"Unit attacking enemy at ({nearest_enemy.y}, {nearest_enemy.x})")
            unit.attack_target = (nearest_enemy.y, nearest_enemy.x)
        # 4. If we can't attack, try to move closer
        else:
            logger.info(f"Unit moving towards enemy at ({nearest_enemy.y}, {nearest_enemy.x})")
            self._move_towards_enemy(unit, nearest_enemy)
            
            # Check if we can attack after moving
            can_attack_after_move = self._can_attack_after_move(unit, nearest_enemy)
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