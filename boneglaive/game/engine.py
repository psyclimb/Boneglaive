#!/usr/bin/env python3
import logging
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH, CRITICAL_HEALTH_PERCENT
from boneglaive.game.units import Unit
from boneglaive.utils.debug import debug_config, measure_perf, game_assert
from boneglaive.utils.message_log import message_log, MessageType

# Set up module logger
logger = debug_config.setup_logging('game.engine')

class Game:
    def __init__(self, skip_setup=False):
        self.units = []
        self.current_player = 1
        self.turn = 1
        self.winner = None
        self.test_mode = False  # For debugging
        self.local_multiplayer = False
        
        # Game state
        self.setup_phase = not skip_setup  # Whether we're in setup phase
        self.setup_player = 1    # Which player is placing units
        self.setup_confirmed = {1: False, 2: False}  # Whether players have confirmed setup
        self.setup_units_remaining = {1: 3, 2: 3}    # How many units each player can still place (3 glaivemen)
        
        # If skipping setup, add default units
        if skip_setup:
            self.setup_initial_units()
    
    def setup_initial_units(self):
        """
        Add predefined units (used for testing only).
        In normal play, units are placed by players during the setup phase.
        """
        # Clear any existing units
        self.units = []
        
        # Player 1 units (left side)
        self.add_unit(UnitType.GLAIVEMAN, 1, 4, 8)
        self.add_unit(UnitType.GLAIVEMAN, 1, 5, 7)
        self.add_unit(UnitType.GLAIVEMAN, 1, 6, 8)
        
        # Player 2 units (right side)
        self.add_unit(UnitType.GLAIVEMAN, 2, 4, 12)
        self.add_unit(UnitType.GLAIVEMAN, 2, 5, 13)
        self.add_unit(UnitType.GLAIVEMAN, 2, 6, 12)
        
        # Skip setup phase when using test setup
        self.setup_phase = False
        self.setup_player = 1
        self.setup_confirmed = {1: True, 2: True}
        self.setup_units_remaining = {1: 0, 2: 0}
        
    def place_setup_unit(self, y, x):
        """
        Place a unit during the setup phase.
        
        Args:
            y, x: The position to place the unit
            
        Returns:
            True if unit was placed, False if invalid or no units remaining
        """
        # Check if position is valid
        if not self.is_valid_position(y, x):
            return False
            
        # Check if this player has units remaining to place
        if self.setup_units_remaining[self.setup_player] <= 0:
            return False
        
        # Place the unit (always a Glaiveman for now)
        # Allow placement even if position is occupied - we'll resolve conflicts later
        self.add_unit(UnitType.GLAIVEMAN, self.setup_player, y, x)
        
        # Decrement remaining units
        self.setup_units_remaining[self.setup_player] -= 1
        
        return True
            
        
    def confirm_setup(self):
        """
        Confirm the current player's setup and proceed.
        
        Returns:
            True if game should now start, False otherwise
        """
        # Make sure all units have been placed
        if self.setup_units_remaining[self.setup_player] > 0:
            return False
            
        # Mark this player's setup as confirmed
        self.setup_confirmed[self.setup_player] = True
        
        # If player 1 is done, switch to player 2
        if self.setup_player == 1:
            self.setup_player = 2
            # Here, game still in setup phase
            return False
            
        # If player 2 is done, start the game
        if self.setup_player == 2:
            # Resolve any unit placement conflicts before the game starts
            self._resolve_unit_placement_conflicts()
            
            self.setup_phase = False
            
            # Add welcome messages now that game is starting
            message_log.add_system_message("Welcome to Boneglaive!")
            message_log.add_system_message("Game begins!")
            
            # Game should start
            return True
            
        return False
        
    def _resolve_unit_placement_conflicts(self):
        """
        Resolve conflicts in unit placement by displacing units on the same position.
        This is called when player 2 confirms setup before starting the game.
        """
        import random
        
        # Simple approach: create a set of occupied positions and move units that conflict
        occupied_positions = set()
        units_to_check = sorted(self.units, key=lambda u: u.player)  # Sort by player to prioritize player 1
        
        for unit in units_to_check:
            if not unit.is_alive():
                continue
                
            pos = (unit.y, unit.x)
            if pos in occupied_positions:
                # This unit is at a position that's already taken - find a new spot
                placed = False
                
                # Try adjacent positions first
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue  # Skip current position
                            
                        new_y = unit.y + dy
                        new_x = unit.x + dx
                        
                        # Check if position is valid and unoccupied
                        if (self.is_valid_position(new_y, new_x) and
                            (new_y, new_x) not in occupied_positions):
                            # Found a valid spot!
                            unit.y = new_y
                            unit.x = new_x
                            occupied_positions.add((new_y, new_x))
                            placed = True
                            break
                    if placed:
                        break
                        
                # If adjacent positions didn't work, try random positions
                if not placed:
                    for _ in range(20):  # Try up to 20 random positions
                        new_y = random.randint(0, HEIGHT-1)
                        new_x = random.randint(0, WIDTH-1)
                        
                        if (new_y, new_x) not in occupied_positions:
                            unit.y = new_y
                            unit.x = new_x
                            occupied_positions.add((new_y, new_x))
                            placed = True
                            break
                            
                # Last resort - iterate through entire board to find an open spot
                if not placed:
                    for y in range(HEIGHT):
                        for x in range(WIDTH):
                            if (y, x) not in occupied_positions:
                                unit.y = y
                                unit.x = x
                                occupied_positions.add((y, x))
                                placed = True
                                break
                        if placed:
                            break
                            
                # If we still haven't placed, just put it somewhere and accept the overlap
                if not placed:
                    unit.y = random.randint(0, HEIGHT-1)
                    unit.x = random.randint(0, WIDTH-1)
                    occupied_positions.add((unit.y, unit.x))
            else:
                # Position is free, mark it as occupied
                occupied_positions.add(pos)
        
    
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
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)  # Hide UI elements during animation
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
                    
                    # Redraw to show unit in new position without UI elements during animation
                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                    
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
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)  # Hide UI elements during animation transition
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
                    
                    # Calculate damage
                    damage = max(1, unit.attack - target.defense)
                    
                    # Store previous HP to check for status changes
                    previous_hp = target.hp
                    critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
                    
                    # Apply damage
                    target.hp = max(0, target.hp - damage)
                    
                    # Log combat message
                    message_log.add_combat_message(
                        attacker_name=f"{unit.type.name}",
                        target_name=f"{target.type.name}",
                        damage=damage,
                        attacker_player=unit.player,
                        target_player=target.player
                    )
                    
                    # Format unit name with player info
                    target_info = f"Player {target.player}'s {target.type.name}" if target.player else f"{target.type.name}"
                    
                    # Check if target was defeated
                    if target.hp <= 0:
                        message_log.add_message(
                            f"{target_info} perishes!",
                            MessageType.COMBAT,
                            player=unit.player,
                            target=target.player
                        )
                    # Check if target just entered critical health
                    elif previous_hp > critical_threshold and target.hp <= critical_threshold:
                        message_log.add_message(
                            f"{target_info} wretches!",
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
        
        # If UI is provided, redraw with cursor, selection, and attack targets before finishing
        if ui:
            # Slight delay before showing final state
            time.sleep(0.5)
            ui.draw_board(show_cursor=True, show_selection=True, show_attack_targets=True)  # Restore all UI elements
        
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