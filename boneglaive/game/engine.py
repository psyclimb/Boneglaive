#!/usr/bin/env python3
import logging
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH, CRITICAL_HEALTH_PERCENT
from boneglaive.game.units import Unit
from boneglaive.game.map import GameMap, MapFactory, TerrainType
from boneglaive.utils.debug import debug_config, measure_perf, game_assert
from boneglaive.utils.message_log import message_log, MessageType

# Set up module logger
logger = debug_config.setup_logging('game.engine')

class Game:
    def __init__(self, skip_setup=False, map_name="lime_foyer"):
        self.units = []
        self.current_player = 1
        self.turn = 1
        self.winner = None
        self.test_mode = False  # For debugging
        self.local_multiplayer = False
        
        # Action ordering
        self.action_counter = 0  # Track order of unit actions
        
        # Create the game map
        self.map = MapFactory.create_map(map_name)
        self.map_name = map_name  # Store current map name
        
        # Game state
        self.setup_phase = not skip_setup  # Whether we're in setup phase
        self.setup_player = 1    # Which player is placing units
        self.setup_confirmed = {1: False, 2: False}  # Whether players have confirmed setup
        self.setup_units_remaining = {1: 3, 2: 3}    # How many units each player can still place (3 glaivemen)
        
        # If skipping setup, add default units
        if skip_setup:
            self.setup_initial_units()
            
    def change_map(self, new_map_name):
        """
        Change the current map and reset the game.
        Used for switching maps between games.
        
        Args:
            new_map_name: The name of the new map to use
            
        Returns:
            Success flag
        """
        try:
            self.map = MapFactory.create_map(new_map_name)
            self.map_name = new_map_name
            
            # Reset game state for a new game
            self.units = []
            self.current_player = 1
            self.turn = 1
            self.winner = None
            self.action_counter = 0  # Reset action counter
            
            # Start in setup phase
            self.setup_phase = True
            self.setup_player = 1
            self.setup_confirmed = {1: False, 2: False}
            self.setup_units_remaining = {1: 3, 2: 3}
            
            return True
        except Exception as e:
            logger.error(f"Failed to change map: {e}")
            return False
    
    def setup_initial_units(self):
        """
        Add predefined units (used for testing only).
        In normal play, units are placed by players during the setup phase.
        """
        # Clear any existing units
        self.units = []
        
        # Find valid positions for units that aren't on limestone
        valid_positions = []
        
        # Check left side for player 1
        for y in range(3, 7):
            for x in range(5, 9):
                if self.map.can_place_unit(y, x):
                    valid_positions.append((1, y, x))
                    if len(valid_positions) >= 3:
                        break
            if len(valid_positions) >= 3:
                break
                
        # Check right side for player 2
        p2_positions = []
        for y in range(3, 7):
            for x in range(11, 15):
                if self.map.can_place_unit(y, x):
                    p2_positions.append((2, y, x))
                    if len(p2_positions) >= 3:
                        break
            if len(p2_positions) >= 3:
                break
                
        valid_positions.extend(p2_positions)
        
        # Place units at valid positions
        for player, y, x in valid_positions:
            self.add_unit(UnitType.GLAIVEMAN, player, y, x)
        
        # If we couldn't find enough valid positions, add some emergency units
        # at fixed positions (shouldn't happen with our current map)
        if len(self.units) < 6:
            missing = 6 - len(self.units)
            emergency_positions = [
                (1, 1, 1), (1, 1, 2), (1, 1, 3),
                (2, 8, 16), (2, 8, 17), (2, 8, 18)
            ]
            
            for i in range(missing):
                player, y, x = emergency_positions[i]
                self.add_unit(UnitType.GLAIVEMAN, player, y, x)
        
        # Assign Greek identifiers
        self._assign_greek_identifiers()
        
        # Skip setup phase when using test setup
        self.setup_phase = False
        self.setup_player = 1
        self.setup_confirmed = {1: True, 2: True}
        self.setup_units_remaining = {1: 0, 2: 0}
        
    def place_setup_unit(self, y, x, unit_type=UnitType.GLAIVEMAN):
        """
        Place a unit during the setup phase.
        
        Args:
            y, x: The position to place the unit
            unit_type: The type of unit to place (defaults to GLAIVEMAN)
            
        Returns:
            True if unit was placed, False if invalid or no units remaining
        """
        # Check if position is valid
        if not self.is_valid_position(y, x):
            return False
            
        # Check if position has blocking terrain (like limestone)
        if not self.map.can_place_unit(y, x):
            return False
            
        # Check if this player has units remaining to place
        if self.setup_units_remaining[self.setup_player] <= 0:
            return False
        
        # Place the unit with the specified type
        # Allow placement even if position is occupied by another unit - we'll resolve conflicts later
        self.add_unit(unit_type, self.setup_player, y, x)
        
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
            
            # Assign Greek identification letters to units
            self._assign_greek_identifiers()
            
            self.setup_phase = False
            
            # Add welcome message now that game is starting
            message_log.add_system_message(f"Entering {self.map.name}")
            
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
                        
                        # Check if position is valid, passable, and unoccupied
                        if (self.is_valid_position(new_y, new_x) and
                            self.map.is_passable(new_y, new_x) and
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
                        
                        if ((new_y, new_x) not in occupied_positions and 
                            self.map.is_passable(new_y, new_x)):
                            unit.y = new_y
                            unit.x = new_x
                            occupied_positions.add((new_y, new_x))
                            placed = True
                            break
                            
                # Last resort - iterate through entire board to find an open spot
                if not placed:
                    for y in range(HEIGHT):
                        for x in range(WIDTH):
                            if ((y, x) not in occupied_positions and
                                self.map.is_passable(y, x)):
                                unit.y = y
                                unit.x = x
                                occupied_positions.add((y, x))
                                placed = True
                                break
                        if placed:
                            break
                            
                # If we still haven't placed, just put it somewhere passable and accept the overlap if needed
                if not placed:
                    # Try to find any passable position
                    passable_positions = []
                    for y in range(HEIGHT):
                        for x in range(WIDTH):
                            if self.map.is_passable(y, x):
                                passable_positions.append((y, x))
                    
                    if passable_positions:
                        # Choose a random passable position
                        new_y, new_x = random.choice(passable_positions)
                        unit.y = new_y
                        unit.x = new_x
                        occupied_positions.add((unit.y, unit.x))
                    else:
                        # Extremely unlikely case - no passable positions
                        unit.y = random.randint(0, HEIGHT-1)
                        unit.x = random.randint(0, WIDTH-1)
                        occupied_positions.add((unit.y, unit.x))
            else:
                # Position is free, mark it as occupied
                occupied_positions.add(pos)
        
    
    def add_unit(self, unit_type, player, y, x):
        unit = Unit(unit_type, player, y, x)
        unit.initialize_skills()  # Initialize skills for the unit
        self.units.append(unit)
    
    def get_unit_at(self, y, x):
        for unit in self.units:
            if unit.is_alive() and unit.y == y and unit.x == x:
                return unit
        return None
        
    def _assign_greek_identifiers(self):
        """
        Assign Greek letter identifiers to all units based on unit type.
        Greek letters are shared between players and assigned sequentially.
        """
        from boneglaive.utils.constants import GREEK_ALPHABET
        import collections
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Group units by type only (not by player)
        unit_groups = collections.defaultdict(list)
        
        # First, collect all units into groups by type
        for unit in self.units:
            if unit.is_alive():
                # Group key is just unit_type
                key = unit.type
                unit_groups[key].append(unit)
        
        # Now assign Greek letters to each unit within its group
        for unit_type, units in unit_groups.items():
            # Sort units by player first, then position
            units.sort(key=lambda u: (u.player, u.y, u.x))
            
            # Assign Greek letters
            for i, unit in enumerate(units):
                if i < len(GREEK_ALPHABET):
                    unit.greek_id = GREEK_ALPHABET[i]
                    logger.debug(f"Assigned {unit.greek_id} to Player {unit.player}'s {unit.type.name}")
                else:
                    # Fallback if we have more units than Greek letters
                    unit.greek_id = f"{i+1}"
                    logger.debug(f"Used number {unit.greek_id} for Player {unit.player}'s {unit.type.name}")
        
        # No need to log the identifier assignments
        for player in [1, 2]:
            player_units = [u for u in self.units if u.is_alive() and u.player == player]
            if player_units:
                message_log.add_message(
                    f"Player {player} units: " + ", ".join([f"{u.get_display_name()}" for u in player_units]),
                    MessageType.SYSTEM
                )
    
    def is_valid_position(self, y, x):
        """Check if a position is within map bounds."""
        return 0 <= y < HEIGHT and 0 <= x < WIDTH
    
    def chess_distance(self, y1, x1, y2, x2):
        """
        Calculate the chess/Chebyshev distance between two points.
        This allows diagonal movement, where the distance is the maximum
        of the horizontal and vertical distances.
        """
        return max(abs(y1 - y2), abs(x1 - x2))
    
    def can_move_to(self, unit, y, x):
        # If unit is trapped by a MANDIBLE_FOREMAN, it cannot move
        if unit.trapped_by is not None:
            from boneglaive.utils.debug import logger
            logger.debug(f"{unit.get_display_name()} cannot move because it is trapped by {unit.trapped_by.get_display_name()}")
            return False
            
        # Check if position is in bounds
        if not self.is_valid_position(y, x):
            return False
        
        # Check if position is occupied by another unit
        if self.get_unit_at(y, x):
            return False
        
        # Check if terrain is passable (not limestone or other blocking terrain)
        if not self.map.is_passable(y, x):
            return False
        
        # Check if position is within effective move range (using chess distance for diagonals)
        distance = self.chess_distance(unit.y, unit.x, y, x)
        effective_stats = unit.get_effective_stats()
        effective_move_range = effective_stats['move_range']
        if distance > effective_move_range:
            return False
            
        # Check if path passes through any units (both enemy and allied)
        # We only need to check this for moves that aren't adjacent
        if distance > 1:
            from boneglaive.utils.coordinates import Position, get_line
            
            # Get all positions along the path
            start_pos = Position(unit.y, unit.x)
            end_pos = Position(y, x)
            path = get_line(start_pos, end_pos)
            
            # Skip the first position (the unit's current position)
            for pos in path[1:-1]:  # Skip start and end positions
                # Check if there's ANY unit at this position
                blocking_unit = self.get_unit_at(pos.y, pos.x)
                if blocking_unit:
                    return False
        
        return True
    
    def can_attack(self, unit, y, x):
        target = self.get_unit_at(y, x)
        if not target or target.player == unit.player:
            return False
        
        # Check if target is within effective attack range (using chess distance for diagonals)
        distance = self.chess_distance(unit.y, unit.x, y, x)
        effective_stats = unit.get_effective_stats()
        effective_attack_range = effective_stats['attack_range']
        return distance <= effective_attack_range
    
    def get_possible_moves(self, unit):
        """
        Get all valid moves for a unit, checking for blocked paths.
        
        Returns:
            List of (y, x) tuples representing valid move positions.
        """
        moves = []
        # Get effective move range that includes bonuses/penalties
        effective_stats = unit.get_effective_stats()
        effective_move_range = effective_stats['move_range']
        
        # Check all positions within the effective move range
        for y in range(max(0, unit.y - effective_move_range), min(HEIGHT, unit.y + effective_move_range + 1)):
            for x in range(max(0, unit.x - effective_move_range), min(WIDTH, unit.x + effective_move_range + 1)):
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
        
        # Get effective attack range
        effective_stats = unit.get_effective_stats()
        effective_attack_range = effective_stats['attack_range']
        
        for y in range(max(0, y_pos - effective_attack_range), min(HEIGHT, y_pos + effective_attack_range + 1)):
            for x in range(max(0, x_pos - effective_attack_range), min(WIDTH, x_pos + effective_attack_range + 1)):
                # Check if there's an enemy unit at this position
                target = self.get_unit_at(y, x)
                if target and target.player != unit.player:
                    # Calculate chess distance (allows diagonals) from the attack position
                    distance = self.chess_distance(y_pos, x_pos, y, x)
                    if distance <= effective_attack_range:
                        attacks.append((y, x))
        
        return attacks
    
    # Store reference to the UI for animations
    def set_ui_reference(self, ui):
        """Store a reference to the game UI for animations."""
        self.ui = ui
    
    @measure_perf
    def execute_turn(self, ui=None):
        """Execute all unit actions for the current turn with animated sequence."""
        import time
        
        # Store UI reference for animations if provided
        if ui:
            self.ui = ui
            
        logger.info(f"Executing turn {self.turn} for player {self.current_player}")
        
        # Create a single list of units with actions, ordered by timestamp
        units_with_actions = []
        
        # Identify units with actions
        for unit in self.units:
            if not unit.is_alive():
                continue
                
            if unit.move_target or unit.attack_target or (unit.skill_target and unit.selected_skill):
                units_with_actions.append(unit)
        
        # Sort units by action timestamp (lower numbers = earlier actions)
        units_with_actions.sort(key=lambda unit: unit.action_timestamp)
        
        logger.info(f"Executing {len(units_with_actions)} actions in timestamp order")
        
        # Display starting message if we have actions and UI
        if (units_with_actions or any(unit.trapped_by is not None for unit in self.units)) and ui:
            message_log.add_system_message("Executing actions in order...")
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            time.sleep(0.5)  # Short delay before actions start
        
        # Process each unit's actions in timestamp order
        for unit in units_with_actions:
            # Log the unit and its action
            logger.debug(f"Processing unit {unit.get_display_name()} with timestamp {unit.action_timestamp}")
            
            # Flag to track if this is a MANDIBLE_FOREMAN taking an action
            is_foreman_taking_action = (unit.type == UnitType.MANDIBLE_FOREMAN and 
                                       (unit.move_target is not None or 
                                        unit.attack_target is not None or 
                                        unit.skill_target is not None))
            
            # If this is a MANDIBLE_FOREMAN taking action, release any trapped units
            if is_foreman_taking_action:
                # Find all units trapped by this FOREMAN
                trapped_units = [u for u in self.units if u.is_alive() and u.trapped_by == unit]
                if trapped_units:
                    logger.debug(f"MANDIBLE_FOREMAN {unit.get_display_name()} is taking action, releasing trapped units")
                    
                    # Release trapped units before the FOREMAN's action is executed
                    for trapped_unit in trapped_units:
                        # Play release animation if UI is available
                        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                            # Create a series of jaw opening characters for the release
                            release_animation = ['{}', '[]', '  ']
                            
                            # Show animation at the trapped unit's position
                            ui.renderer.animate_attack_sequence(
                                trapped_unit.y, trapped_unit.x,
                                release_animation,
                                6,  # color ID (yellowish)
                                0.2  # duration
                            )
                        
                        # Release the unit
                        trapped_unit.trapped_by = None
                        message_log.add_message(
                            f"{trapped_unit.get_display_name()} is released from mechanical jaws!",
                            MessageType.ABILITY,
                            target_name=trapped_unit.get_display_name()
                        )
                    
                    # Redraw the board to show the updated state
                    if ui:
                        ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                        time.sleep(0.2)  # Short pause after release
            
            # EXECUTE MOVE if unit has a move target
            if unit.move_target:
                y, x = unit.move_target
                if self.can_move_to(unit, y, x):  # Double-check the move is still valid
                    logger.debug(f"Moving {unit.get_display_name()} from ({unit.y},{unit.x}) to ({y},{x})")
                    
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
                            f"{unit.get_display_name()} moved from ({start_y},{start_x}) to ({y},{x})",
                            MessageType.MOVEMENT,
                            player=unit.player,
                            # Include unit name for coloring
                            attacker_name=unit.get_display_name()
                        )
                        time.sleep(0.3)  # Short delay after each unit moves
                    else:
                        # Without UI, just update position
                        unit.y, unit.x = y, x
                else:
                    logger.warning(f"Invalid move target ({y},{x}) for unit at ({unit.y},{unit.x})")
            
            # EXECUTE ATTACK if unit has an attack target
            if unit.attack_target:
                y, x = unit.attack_target
                target = self.get_unit_at(y, x)
                
                # Calculate attacking position (either unit's current position or move target)
                attacking_pos = (unit.y, unit.x)  # Unit's position is already updated if it moved
                
                # Verify attack is within range from the attacking position
                attack_distance = self.chess_distance(attacking_pos[0], attacking_pos[1], y, x)
                if target and target.player != unit.player and attack_distance <= unit.attack_range:  # Valid attack
                    # Show attack animation if UI is provided
                    if ui:
                        ui.show_attack_animation(unit, target)
                    
                    # Calculate damage
                    # Defense acts as flat damage reduction
                    damage = max(1, unit.attack - target.defense)
                    
                    # Store previous HP to check for status changes
                    previous_hp = target.hp
                    critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
                    
                    # Apply damage
                    target.hp = max(0, target.hp - damage)
                    
                    # Check if attacker is a MANDIBLE_FOREMAN with the Viceroy passive
                    # If so, trap the target unit
                    if unit.type == UnitType.MANDIBLE_FOREMAN and unit.passive_skill and \
                       unit.passive_skill.name == "Viceroy" and target.hp > 0:
                        # Only trap if the target is still alive
                        target.trapped_by = unit
                        
                        # Log the trapping
                        message_log.add_message(
                            f"{target.get_display_name()} is trapped in mechanical jaws!",
                            MessageType.ABILITY,
                            player=unit.player,
                            target_name=target.get_display_name()
                        )
                    
                    # Award XP to the attacker based on damage dealt
                    from boneglaive.utils.constants import XP_DAMAGE_FACTOR, XP_KILL_REWARD
                    xp_gained = int(damage * XP_DAMAGE_FACTOR)
                    
                    # Additional XP for killing the target
                    if target.hp <= 0:
                        xp_gained += XP_KILL_REWARD
                    
                    # Add XP and check if unit leveled up
                    if unit.add_xp(xp_gained):
                        # Unit leveled up - add a message
                        message_log.add_message(
                            f"{unit.get_display_name()} gained experience and reached level {unit.level}!",
                            MessageType.SYSTEM,
                            player=unit.player
                        )
                    
                    # Log combat message
                    message_log.add_combat_message(
                        attacker_name=unit.get_display_name(),
                        target_name=target.get_display_name(),
                        damage=damage,
                        attacker_player=unit.player,
                        target_player=target.player
                    )
                    
                    # No need to format with player info anymore - just use the unit's display name
                    # Check if target was defeated
                    if target.hp <= 0:
                        message_log.add_message(
                            f"{target.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=unit.player,
                            target=target.player,
                            # Store unit names explicitly to help with coloring
                            target_name=target.get_display_name()
                        )
                        
                        # If a MANDIBLE_FOREMAN dies, release any trapped unit
                        if target.type == UnitType.MANDIBLE_FOREMAN:
                            # Find any units trapped by this FOREMAN
                            for trapped_unit in self.units:
                                if trapped_unit.is_alive() and trapped_unit.trapped_by == target:
                                    logger.debug(f"MANDIBLE_FOREMAN perished, releasing {trapped_unit.get_display_name()}")
                                    trapped_unit.trapped_by = None
                                    message_log.add_message(
                                        f"{trapped_unit.get_display_name()} is released from mechanical jaws!",
                                        MessageType.ABILITY,
                                        target_name=trapped_unit.get_display_name()
                                    )
                    # Check if target just entered critical health - trigger wretches message and Autoclave
                    elif previous_hp > critical_threshold and target.hp <= critical_threshold:
                        message_log.add_message(
                            f"{target.get_display_name()} wretches!",
                            MessageType.COMBAT,
                            player=unit.player,
                            target=target.player,
                            # Store unit names explicitly to help with coloring
                            target_name=target.get_display_name()
                        )
                        
                        # Check if target is a GLAIVEMAN and has the Autoclave passive
                        if target.type == UnitType.GLAIVEMAN and target.passive_skill and \
                           target.passive_skill.name == "Autoclave":
                            # Mark Autoclave as ready to trigger during the apply_passive_skills phase
                            target.passive_skill.mark_ready_to_trigger()
                    # Check if target is already in critical health and took more damage - also trigger Autoclave
                    elif previous_hp <= critical_threshold and target.hp <= critical_threshold and target.hp > 0:
                        # Check if target is a GLAIVEMAN and has the Autoclave passive
                        if target.type == UnitType.GLAIVEMAN and target.passive_skill and \
                           target.passive_skill.name == "Autoclave":
                            # Mark Autoclave as ready to trigger during the apply_passive_skills phase
                            target.passive_skill.mark_ready_to_trigger()
                else:
                    # Log invalid attack attempts for debugging
                    if not target:
                        logger.warning(f"Attack failed: no target at ({y},{x})")
                    elif target.player == unit.player:
                        logger.warning(f"Attack failed: cannot attack allied unit")
                    elif attack_distance > unit.attack_range:
                        logger.warning(f"Attack failed: target out of range (distance={attack_distance}, range={unit.attack_range})")
                    else:
                        logger.warning(f"Attack failed: unknown reason")
                
                # Add a slight pause between actions for a unit
                if ui:
                    time.sleep(0.3)
            
            # EXECUTE SKILL if unit has a skill target
            if unit.skill_target and unit.selected_skill:
                # Execute the skill
                skill = unit.selected_skill
                target_pos = unit.skill_target
                
                # Execute the skill if it has an execute method
                if hasattr(skill, 'execute'):
                    skill.execute(unit, target_pos, self, ui)
                else:
                    logger.warning(f"Skill {skill.name} has no execute method")
                
                # Add a slight pause after the skill
                if ui:
                    time.sleep(0.3)
            
            # Add a slight pause between units' actions
            if ui:
                time.sleep(0.5)
        
        # Now that all planned actions have been processed, apply trap damage
        # This ensures that FOREMENs that moved/attacked/used skills have released their trapped units
        # before trap damage is applied
        self._apply_trap_damage()
        
        # Redraw the board after trap damage to show updated health
        if ui:
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            time.sleep(0.3)  # Short pause after trap damage
            
        # Clear all actions and update skill cooldowns
        for unit in self.units:
            if unit.is_alive():
                # Reset action targets
                unit.reset_action_targets()
                
                # Reduce cooldowns for skills ONLY for units belonging to current player
                if unit.player == self.current_player:
                    unit.tick_cooldowns()
                
                # Handle units that were affected by Pry during the turn that just ended
                # They need to keep their was_pried status until after THEIR next turn
                if unit.was_pried and unit.player == self.current_player:
                    # This unit was just pried this turn - next turn it will feel the effects
                    # Keep was_pried flag until after their turn is done
                    pass
                elif unit.was_pried and unit.player != self.current_player:
                    # This unit was pried on their previous turn and just finished a turn with the penalty
                    # Time to clear the was_pried flag
                    unit.was_pried = False  # Keep the move_range_bonus until end of turn
                
                # Apply passive skills (can be affected by game state)
                # Pass ui reference for animations if available
                unit.apply_passive_skills(self)
        
        # Check if game is over
        self.check_game_over()
        
        # If UI is provided, redraw with cursor, selection, and attack targets before finishing
        if ui:
            # Slight delay before showing final state
            time.sleep(0.5)
            ui.draw_board(show_cursor=True, show_selection=True, show_attack_targets=True)  # Restore all UI elements
        
        # Before changing players, reset movement penalties for units of the player
        # whose turn is ENDING (not starting). This way penalties last through their entire next turn.
        if not self.winner:
            # Reset penalties for current player's units BEFORE switching players
            for unit in self.units:
                if unit.is_alive() and unit.player == self.current_player:
                    # If this unit was pried during THIS turn, don't reset (penalty should last next turn)
                    if not unit.was_pried:
                        unit.reset_movement_penalty()
                        
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
    
    def _apply_trap_damage(self):
        """Apply damage to units trapped by MANDIBLE_FOREMENs."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        import time
        import curses
        
        # Find all trapped units
        for unit in self.units:
            if not unit.is_alive() or unit.trapped_by is None:
                continue
                
            # Only apply trap damage if:
            # 1. The trapper is alive
            # 2. It's the trapper's turn
            # 3. The trapper has not taken any action this turn that would have released the trapped unit
            foreman = unit.trapped_by
            if (foreman.is_alive() and 
                foreman.player == self.current_player and
                not (foreman.move_target or foreman.attack_target or foreman.skill_target)):
                logger.debug(f"Applying Viceroy trap damage to {unit.get_display_name()}")
                
                # Play trap animation if UI is available
                ui = getattr(self, 'ui', None)
                if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                    # Get animation sequence for Viceroy trap
                    animation_sequence = ui.asset_manager.get_skill_animation_sequence('viceroy_trap')
                    
                    # Show jaw animation at trapped unit's position
                    ui.renderer.animate_attack_sequence(
                        unit.y, unit.x,
                        animation_sequence,
                        5,  # color ID (reddish)
                        0.2  # duration
                    )
                    time.sleep(0.2)
                
                # Calculate damage using the FOREMAN's attack
                damage = max(1, foreman.attack - unit.defense)
                
                # Apply damage to the trapped unit
                previous_hp = unit.hp
                unit.hp = max(0, unit.hp - damage)
                
                # Log the damage
                message_log.add_combat_message(
                    attacker_name=foreman.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability="Viceroy Trap",
                    attacker_player=foreman.player,
                    target_player=unit.player
                )
                
                # Show damage number if UI is available
                if ui and hasattr(ui, 'renderer'):
                    # Flash the unit to show damage
                    if hasattr(ui, 'asset_manager'):
                        # Flash the unit with damage colors
                        tile_ids = [ui.asset_manager.get_unit_tile(unit.type)] * 4
                        color_ids = [5, 3 if unit.player == 1 else 4] * 2  # Alternate red with player color
                        durations = [0.1] * 4
                        
                        # Use renderer's flash tile method
                        ui.renderer.flash_tile(unit.y, unit.x, tile_ids, color_ids, durations)
                    
                    # Show damage number
                    damage_text = f"-{damage}"
                    
                    # Make damage text more prominent
                    for i in range(3):
                        # First clear the area
                        ui.renderer.draw_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                        # Draw with alternating bold/normal for a flashing effect
                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                        ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 5, attrs)  # Red for trap damage
                        ui.renderer.refresh()
                        time.sleep(0.1)
                    
                    # Final damage display
                    ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 5, curses.A_BOLD)
                    ui.renderer.refresh()
                    time.sleep(0.2)
                
                # Check if the trapped unit was defeated
                if unit.hp <= 0:
                    message_log.add_message(
                        f"{unit.get_display_name()} perishes in the jaws!",
                        MessageType.COMBAT,
                        target=unit.player,
                        target_name=unit.get_display_name()
                    )
                    unit.trapped_by = None
    
    def _release_trapped_units(self):
        """
        Release any trapped units for MANDIBLE_FOREMENs that took actions.
        No damage is applied when a unit is released from the jaws.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        import time
        
        # Find all MANDIBLE_FOREMENs that took actions
        for foreman in self.units:
            if not foreman.is_alive() or foreman.type != UnitType.MANDIBLE_FOREMAN or not foreman.took_action:
                continue
                
            # Release any units trapped by this foreman
            for unit in self.units:
                if unit.is_alive() and unit.trapped_by == foreman:
                    logger.debug(f"MANDIBLE_FOREMAN took action, releasing {unit.get_display_name()}")
                    
                    # Play release animation if UI is available
                    ui = getattr(self, 'ui', None)
                    if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                        # Create a series of jaw opening characters for the release
                        release_animation = ['{}', '[]', '  ']
                        
                        # Show animation at the trapped unit's position
                        ui.renderer.animate_attack_sequence(
                            unit.y, unit.x,
                            release_animation,
                            6,  # color ID (yellowish)
                            0.2  # duration
                        )
                        
                        # Draw a line between the FOREMAN and the unit to show the release
                        if foreman.is_alive():
                            # Calculate positions along the path
                            from boneglaive.utils.coordinates import Position, get_line
                            start_pos = Position(foreman.y, foreman.x)
                            end_pos = Position(unit.y, unit.x)
                            path = get_line(start_pos, end_pos)
                            
                            # Show the connection breaking
                            for pos in path[1:-1]:  # Skip start and end positions
                                ui.renderer.draw_tile(pos.y, pos.x, '·', 7)  # Small dots showing connection breaking
                            ui.renderer.refresh()
                            time.sleep(0.1)
                            
                            # Clear the connection
                            for pos in path[1:-1]:
                                ui.renderer.draw_tile(pos.y, pos.x, ' ', 0)
                            ui.renderer.refresh()
                    
                    # Release the unit
                    unit.trapped_by = None
                    message_log.add_message(
                        f"{unit.get_display_name()} is released from mechanical jaws!",
                        MessageType.ABILITY,
                        target_name=unit.get_display_name()
                    )
            
            # Reset the foreman's action tracking
            foreman.took_action = False
    
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