#!/usr/bin/env python3
import logging
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH
from boneglaive.game.units import Unit
from boneglaive.utils.debug import debug_config, measure_perf, game_assert
from boneglaive.utils.message_log import message_log, MessageType

# Set up module logger
logger = debug_config.setup_logging('game.engine')

class Game:
    def __init__(self):
        self.units = []
        self.current_player = 1
        self.turn = 1
        self.winner = None
        self.test_mode = False  # For debugging
        self.local_multiplayer = False
        
        # Initialize with some units
        self.setup_initial_units()
    
    def setup_initial_units(self):
        # Player 1 units (left side)
        self.add_unit(UnitType.GLAIVEMAN, 1, 4, 8)
        self.add_unit(UnitType.ARCHER, 1, 5, 7)
        self.add_unit(UnitType.MAGE, 1, 6, 8)
        
        # Player 2 units (right side)
        self.add_unit(UnitType.GLAIVEMAN, 2, 4, 12)
        self.add_unit(UnitType.ARCHER, 2, 5, 13)
        self.add_unit(UnitType.MAGE, 2, 6, 12)
    
    def add_unit(self, unit_type, player, y, x):
        self.units.append(Unit(unit_type, player, y, x))
    
    def get_unit_at(self, y, x):
        for unit in self.units:
            if unit.is_alive() and unit.y == y and unit.x == x:
                return unit
        return None
    
    def is_valid_position(self, y, x):
        return 0 <= y < HEIGHT and 0 <= x < WIDTH
    
    def chess_distance(self, y1, x1, y2, x2):
        """
        Calculate the chess/Chebyshev distance between two points.
        This allows diagonal movement, where the distance is the maximum
        of the horizontal and vertical distances.
        """
        return max(abs(y1 - y2), abs(x1 - x2))
    
    def can_move_to(self, unit, y, x):
        # Check if position is in bounds
        if not self.is_valid_position(y, x):
            return False
        
        # Check if position is occupied
        if self.get_unit_at(y, x):
            return False
        
        # Check if position is within move range (using chess distance for diagonals)
        distance = self.chess_distance(unit.y, unit.x, y, x)
        return distance <= unit.move_range
    
    def can_attack(self, unit, y, x):
        target = self.get_unit_at(y, x)
        if not target or target.player == unit.player:
            return False
        
        # Check if target is within attack range (using chess distance for diagonals)
        distance = self.chess_distance(unit.y, unit.x, y, x)
        return distance <= unit.attack_range
    
    def get_possible_moves(self, unit):
        moves = []
        for y in range(max(0, unit.y - unit.move_range), min(HEIGHT, unit.y + unit.move_range + 1)):
            for x in range(max(0, unit.x - unit.move_range), min(WIDTH, unit.x + unit.move_range + 1)):
                if self.can_move_to(unit, y, x):
                    moves.append((y, x))
        return moves
    
    def get_possible_attacks(self, unit, from_pos=None):
        """
        Get possible attack targets for a unit.
        
        Args:
            unit: The unit to check attacks for
            from_pos: Optional (y, x) position to calculate attacks from (for post-move attacks)
        
        Returns:
            List of (y, x) tuples representing possible attack positions
        """
        attacks = []
        
        # Use provided position or unit's current position
        y_pos, x_pos = from_pos if from_pos else (unit.y, unit.x)
        
        for y in range(max(0, y_pos - unit.attack_range), min(HEIGHT, y_pos + unit.attack_range + 1)):
            for x in range(max(0, x_pos - unit.attack_range), min(WIDTH, x_pos + unit.attack_range + 1)):
                # Check if there's an enemy unit at this position
                target = self.get_unit_at(y, x)
                if target and target.player != unit.player:
                    # Calculate chess distance (allows diagonals) from the attack position
                    distance = self.chess_distance(y_pos, x_pos, y, x)
                    if distance <= unit.attack_range:
                        attacks.append((y, x))
        
        return attacks
    
    @measure_perf
    def execute_turn(self, ui=None):
        """Execute all unit actions for the current turn with animated sequence."""
        import time
        
        logger.info(f"Executing turn {self.turn} for player {self.current_player}")
        
        # Track units that will move and units that will attack
        moving_units = []
        attacking_units = []
        
        # Identify units with actions
        for unit in self.units:
            if not unit.is_alive():
                continue
                
            if unit.move_target:
                moving_units.append(unit)
                
            if unit.attack_target:
                attacking_units.append(unit)
        
        # PHASE 1: Execute and animate all movements
        if moving_units and ui:
            message_log.add_system_message("Units moving...")
            ui.draw_board(show_cursor=False, show_selection=False)  # Show initial state without cursor or selection
            time.sleep(0.5)  # Short delay before movements start
            
        for unit in moving_units:
            y, x = unit.move_target
            if self.can_move_to(unit, y, x):  # Double-check the move is still valid
                logger.debug(f"Moving {unit.type.name} from ({unit.y},{unit.x}) to ({y},{x})")
                
                # Show movement animation if UI is provided
                if ui:
                    # Save original position
                    start_y, start_x = unit.y, unit.x
                    
                    # Update unit position
                    unit.y, unit.x = y, x
                    
                    # Redraw to show unit in new position without cursor or selection
                    ui.draw_board(show_cursor=False, show_selection=False)
                    
                    # Log movement
                    message_log.add_message(
                        f"{unit.type.name} moved from ({start_y},{start_x}) to ({y},{x})",
                        MessageType.MOVEMENT,
                        player=unit.player
                    )
                    time.sleep(0.3)  # Short delay after each unit moves
                else:
                    # Without UI, just update position
                    unit.y, unit.x = y, x
            else:
                logger.warning(f"Invalid move target ({y},{x}) for unit at ({unit.y},{unit.x})")
        
        # After all movements, pause to show the new board state
        if moving_units and attacking_units and ui:
            time.sleep(1.0)  # Longer delay between movement and attack phases
            message_log.add_system_message("Executing attacks...")
            ui.draw_board(show_cursor=False, show_selection=False)  # Show updated state without cursor or selection
            time.sleep(0.5)  # Short delay before attacks start
        
        # PHASE 2: Execute all attacks
        for unit in attacking_units:
            if not unit.is_alive():
                continue
            
            if unit.attack_target:
                y, x = unit.attack_target
                target = self.get_unit_at(y, x)
                if target and target.player != unit.player:  # Valid attack
                    # Show attack animation if UI is provided
                    if ui:
                        ui.show_attack_animation(unit, target)
                    
                    # Calculate and apply damage
                    damage = max(1, unit.attack - target.defense)
                    target.hp = max(0, target.hp - damage)
                    
                    # Log combat message
                    message_log.add_combat_message(
                        attacker_name=f"{unit.type.name}",
                        target_name=f"{target.type.name}",
                        damage=damage,
                        attacker_player=unit.player,
                        target_player=target.player
                    )
                    
                    # Check if target was defeated
                    if target.hp <= 0:
                        target_info = f"Player {target.player}'s {target.type.name}" if target.player else f"{target.type.name}"
                        message_log.add_message(
                            f"{target_info} was defeated!",
                            MessageType.COMBAT,
                            player=unit.player,
                            target=target.player
                        )
        
        # Clear all actions
        for unit in self.units:
            unit.move_target = None
            unit.attack_target = None
        
        # Check if game is over
        self.check_game_over()
        
        # If UI is provided, redraw with cursor and selection before finishing
        if ui:
            # Slight delay before showing final state
            time.sleep(0.5)
            ui.draw_board(show_cursor=True, show_selection=True)  # Restore cursor and selection
        
        # In multiplayer modes, player switching is primarily handled by the multiplayer manager
        # But we still need to update the game's current_player property here
        if not self.winner:
            # Toggle between player 1 and 2
            self.current_player = 3 - self.current_player
            # Increment turn counter when player 1's turn comes around again
            if self.current_player == 1:
                self.turn += 1
    
    def check_game_over(self):
        player1_alive = any(unit.is_alive() and unit.player == 1 for unit in self.units)
        player2_alive = any(unit.is_alive() and unit.player == 2 for unit in self.units)
        
        if not player1_alive:
            self.winner = 2
            message_log.add_system_message(f"Player 2 wins! All Player 1 units have been defeated.")
        elif not player2_alive:
            self.winner = 1
            message_log.add_system_message(f"Player 1 wins! All Player 2 units have been defeated.")
    
    def toggle_test_mode(self):
        self.test_mode = not self.test_mode
        logger.info(f"Test mode {'enabled' if self.test_mode else 'disabled'}")
        return self.test_mode
    
    @measure_perf
    def get_game_state(self):
        """Return a dictionary with the current game state for debugging"""
        state = {
            'turn': self.turn,
            'current_player': self.current_player,
            'winner': self.winner,
            'test_mode': self.test_mode,
            'units': []
        }
        
        for unit in self.units:
            if unit.is_alive():
                unit_info = {
                    'type': unit.type.name,
                    'player': unit.player,
                    'position': (unit.y, unit.x),
                    'hp': f"{unit.hp}/{unit.max_hp}",
                    'stats': {
                        'attack': unit.attack,
                        'defense': unit.defense,
                        'move_range': unit.move_range,
                        'attack_range': unit.attack_range
                    }
                }
                state['units'].append(unit_info)
        
        return state