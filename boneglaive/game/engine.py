#!/usr/bin/env python3
import logging
import curses
import time
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
            
        # Subscribe to events
        from boneglaive.utils.event_system import get_event_manager, EventType
        self.event_manager = get_event_manager()
        self.event_manager.subscribe(EventType.EFFECT_EXPIRED, self._handle_effect_expired)
            
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
        Add predefined units for a new game.
        Called when skipping setup phase (testing or AI mode).
        In normal human play, units are placed by players during the setup phase.
        """
        from boneglaive.utils.debug import logger
        logger.info("Setting up initial units (skipping setup phase)")
        
        # Clear any existing units
        self.units = []
        
        # Find valid positions for units that aren't on limestone
        valid_positions = []
        
        # Check left side for player 1
        logger.info("Finding positions for player 1 units")
        for y in range(3, 7):
            for x in range(5, 9):
                if self.map.can_place_unit(y, x):
                    valid_positions.append((1, y, x))
                    if len(valid_positions) >= 3:
                        break
            if len(valid_positions) >= 3:
                break
                
        # Check right side for player 2
        logger.info("Finding positions for player 2 units")
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
        logger.info(f"Found {len(valid_positions)} valid positions for units")
        
        # Place units at valid positions
        for player, y, x in valid_positions:
            # Determine unit type - in VS_AI mode, make player 2 have some variety
            unit_type = UnitType.GLAIVEMAN
            
            # For variety, we could add different unit types for player 2 in the future
            # Currently all units are GLAIVEMAN type
            
            # Add the unit with the selected type
            self.add_unit(unit_type, player, y, x)
            logger.info(f"Added {unit_type.name} for player {player} at ({y}, {x})")
        
        # If we couldn't find enough valid positions, add some emergency units
        # at fixed positions (shouldn't happen with our current map)
        if len(self.units) < 6:
            missing = 6 - len(self.units)
            logger.warning(f"Not enough valid positions found. Adding {missing} emergency units.")
            emergency_positions = [
                (1, 1, 1), (1, 1, 2), (1, 1, 3),
                (2, 8, 16), (2, 8, 17), (2, 8, 18)
            ]
            
            for i in range(missing):
                player, y, x = emergency_positions[i]
                self.add_unit(UnitType.GLAIVEMAN, player, y, x)
        
        # Count units for both players
        p1_units = sum(1 for unit in self.units if unit.player == 1)
        p2_units = sum(1 for unit in self.units if unit.player == 2)
        logger.info(f"Total units setup: Player 1: {p1_units}, Player 2: {p2_units}")
        
        # Assign Greek identifiers
        self._assign_greek_identifiers()
        
        # Skip setup phase when using test setup
        self.setup_phase = False
        self.setup_player = 1
        self.setup_confirmed = {1: True, 2: True}
        self.setup_units_remaining = {1: 0, 2: 0}
        logger.info("Setup phase skipped, game ready to begin")
        
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
        unit.set_game_reference(self)  # Set game reference for trap checks
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
    
    def is_adjacent(self, y1, x1, y2, x2):
        """
        Check if two positions are adjacent (including diagonals).
        Returns True if the chess distance between them is 1.
        """
        return self.chess_distance(y1, x1, y2, x2) == 1
        
    def has_line_of_sight(self, from_y, from_x, to_y, to_x):
        """
        Check if there is a clear line of sight between two positions.
        Line of sight is blocked by solid terrain like pillars and limestone.
        
        Args:
            from_y, from_x: Starting position coordinates
            to_y, to_x: Target position coordinates
            
        Returns:
            bool: True if there is line of sight, False if blocked
        """
        from boneglaive.utils.coordinates import Position, get_line
        from boneglaive.utils.debug import logger
        from boneglaive.game.map import TerrainType
        
        # Get all positions along the line
        start_pos = Position(from_y, from_x)
        end_pos = Position(to_y, to_x)
        path = get_line(start_pos, end_pos)
        
        # Skip the source and target positions - we only care about positions between them
        path_between = path[1:-1] if len(path) > 2 else []
        
        # Check each position along the path
        for pos in path_between:
            # Check if terrain at this position blocks line of sight
            terrain = self.map.get_terrain_at(pos.y, pos.x)
            
            # Check if terrain blocks line of sight (use map's function instead of hardcoding)
            if self.map.blocks_line_of_sight(pos.y, pos.x):
                logger.debug(f"Line of sight blocked by {terrain} at position ({pos.y}, {pos.x})")
                return False
            
            # Check if there's a unit at this position that might block line of sight
            blocking_unit = self.get_unit_at(pos.y, pos.x)
            if blocking_unit:
                logger.debug(f"Line of sight blocked by unit {blocking_unit.get_display_name()} at position ({pos.y}, {pos.x})")
                return False
        
        return True
    
    def can_move_to(self, unit, y, x):
        # Echo units cannot move
        if unit.is_echo:
            from boneglaive.utils.debug import logger
            logger.debug(f"{unit.get_display_name()} cannot move because it is an echo")
            return False
            
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
                    
                # Check if terrain along the path is passable
                if not self.map.is_passable(pos.y, pos.x):
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
        
        # Basic range check
        if distance > effective_attack_range:
            return False
            
        # GRAYMAN's attacks and Estrange are blocked by terrain, so check line of sight
        if unit.type == UnitType.GRAYMAN:
            return self.has_line_of_sight(unit.y, unit.x, y, x)
            
        # All other units can attack without line of sight
        return True
    
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
                        # For GRAYMAN units, check line of sight
                        if unit.type == UnitType.GRAYMAN:
                            if self.has_line_of_sight(y_pos, x_pos, y, x):
                                attacks.append((y, x))
                        else:
                            # All other units don't need line of sight
                            attacks.append((y, x))
        
        return attacks
    
    # Store reference to the UI for animations
    def set_ui_reference(self, ui):
        """Store a reference to the game UI for animations."""
        self.ui = ui
    
    def get_ossify_defense_bonus(self, unit):
        """
        Helper method to get the defense bonus from Ossify skill.
        """
        if unit.type == UnitType.MARROW_CONDENSER:
            for skill in unit.active_skills:
                if skill.name == "Ossify" and hasattr(skill, 'defense_bonus'):
                    return skill.defense_bonus
        return 4  # Default defense bonus if we can't find the skill
    
    @measure_perf
    def check_critical_health(self, unit, attacker=None, previous_hp=None, ui=None):
        """
        Check if a unit has reached critical health and trigger appropriate effects.
        This is a centralized method to handle the "wretching" state for all units.
        
        Args:
            unit: The unit to check for critical health
            attacker: Optional unit that caused the damage
            previous_hp: Optional previous HP for transition detection
            ui: Optional UI reference for animations
            
        Returns:
            bool: True if processing should continue, False if processing should stop
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        
        # Skip if unit is already dead
        if not unit.is_alive():
            return True
            
        # Skip if not in critical health
        if not unit.is_at_critical_health():
            return True
            
        # Get critical threshold for reference
        critical_threshold = unit.get_critical_threshold()
            
        # Check if unit just entered critical health
        if previous_hp is not None and previous_hp > critical_threshold:
            # Unit just crossed into critical health - display the wretch message
            message_log.add_message(
                f"{unit.get_display_name()} wretches!",
                MessageType.COMBAT,
                player=attacker.player if attacker else None,
                target=unit.player,
                target_name=unit.get_display_name()
            )
            
            # Add visual wretch animation if UI is available
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Get wretch animation from asset manager
                wretch_animation = ui.asset_manager.get_skill_animation_sequence('wretch')
                if not wretch_animation:
                    # Fallback animation if not defined
                    wretch_animation = ['!', '?', '#', '@', '&', '%', '$']
                
                # Flash unit with yellow/red to indicate critical status
                ui.renderer.animate_attack_sequence(
                    unit.y, unit.x,
                    wretch_animation,
                    6,  # Yellow color for critical
                    0.08  # Quick animation
                )
            
            # Check for Wretched Decension from FOWL_CONTRIVANCE
            if attacker and attacker.type == UnitType.FOWL_CONTRIVANCE:
                # Try to trigger Wretched Decension - if successful, stop processing
                if self.try_trigger_wretched_decension(attacker, unit, ui):
                    return False  # Stop processing
            
            # Try to trigger Autoclave for the target
            self.try_trigger_autoclave(unit, ui)
        
        # Unit is already in critical health - check for ongoing effects
        elif unit.hp <= critical_threshold:
            # Check for Wretched Decension from FOWL_CONTRIVANCE
            if attacker and attacker.type == UnitType.FOWL_CONTRIVANCE:
                # Try to trigger Wretched Decension - if successful, stop processing
                if self.try_trigger_wretched_decension(attacker, unit, ui):
                    return False  # Stop processing
            
            # Try to trigger Autoclave for the target
            self.try_trigger_autoclave(unit, ui)
            
        # Continue normal processing
        return True
    
    @measure_perf
    def handle_unit_death(self, dying_unit, killer_unit=None, cause="combat", ui=None):
        """
        Centralized handling of unit death for consistent processing.
        Handles messages, special effects, and checks for Marrow Dike interactions.
        
        Args:
            dying_unit: The unit that died
            killer_unit: Optional unit that caused the death
            cause: String describing cause of death ('combat', 'trap', 'explosion', etc.)
            ui: Optional UI reference for visual effects
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        
        # Log the death with appropriate message
        message_log.add_message(
            f"{dying_unit.get_display_name()} perishes!",
            MessageType.COMBAT,
            player=killer_unit.player if killer_unit else None,
            target_name=dying_unit.get_display_name()
        )
        
        # Check if unit died within or on a MARROW_CONDENSER's dike
        in_marrow_dike = False
        dike_owner = None
        
        # Check both wall tiles and interior tiles
        if hasattr(self, 'marrow_dike_tiles'):
            target_pos = (dying_unit.y, dying_unit.x)
            if target_pos in self.marrow_dike_tiles:
                in_marrow_dike = True
                dike_owner = self.marrow_dike_tiles[target_pos]['owner']
        
        # Also check interior tiles if tracked
        if hasattr(self, 'marrow_dike_interior') and not in_marrow_dike:
            target_pos = (dying_unit.y, dying_unit.x)
            if target_pos in self.marrow_dike_interior:
                in_marrow_dike = True
                dike_owner = self.marrow_dike_interior[target_pos]['owner']
        
        # Process Dominion upgrades if died in a Marrow Dike
        if in_marrow_dike and dike_owner:
            # Verify the owner is a MARROW_CONDENSER
            if dike_owner.type == UnitType.MARROW_CONDENSER and hasattr(dike_owner, 'passive_skill'):
                passive = dike_owner.passive_skill
                
                # Check if it's Dominion and can upgrade skills
                if passive.name == "Dominion" and passive.can_upgrade():
                    upgraded_skill = passive.get_next_upgrade()
                    
                    if upgraded_skill:
                        # Create a more distinctive message for the upgrade
                        upgrade_message = f"DOMINION: {dike_owner.get_display_name()} absorbs power from the fallen, upgrading {upgraded_skill.capitalize()}!"
                        
                        # Add to message log with ABILITY type for correct player coloring
                        message_log.add_message(
                            upgrade_message,
                            MessageType.ABILITY,
                            player=dike_owner.player,
                            # Include unit name explicitly to help with coloring
                            attacker_name=dike_owner.get_display_name(),
                            # Add upgrade info to help with filtering/searching
                            upgrade=upgraded_skill,
                            is_upgrade=True
                        )
                        
                        # Also log to the game's logger to ensure it's recorded
                        logger.info(upgrade_message)
        
        # Handle MANDIBLE_FOREMAN death - release trapped units
        if dying_unit.type == UnitType.MANDIBLE_FOREMAN:
            for unit in self.units:
                if unit.is_alive() and unit.trapped_by == dying_unit:
                    logger.debug(f"MANDIBLE_FOREMAN perished, releasing {unit.get_display_name()}")
                    unit.trapped_by = None
                    unit.trap_duration = 0  # Reset trap duration
                    message_log.add_message(
                        f"{unit.get_display_name()} is released from mechanical jaws!",
                        MessageType.ABILITY,
                        target_name=unit.get_display_name()
                    )
        
        # Handle Echo death by triggering chain reactions
        if dying_unit.is_echo:
            self._trigger_echo_death_effect(dying_unit, ui)
    
    def process_status_effects(self):
        """
        Process status effect durations for all units of the current player.
        Decrements durations and removes expired status effects.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Process all units for the current player
        for unit in self.units:
            if not unit.is_alive() or unit.player != self.current_player:
                continue
                
            # Process Site Inspection status effect
            if hasattr(unit, 'status_site_inspection') and unit.status_site_inspection:
                # Decrement the duration
                unit.status_site_inspection_duration -= 1
                logger.debug(f"{unit.get_display_name()}'s Site Inspection duration: {unit.status_site_inspection_duration}")
                
                # Check if the status effect has expired
                if unit.status_site_inspection_duration <= 0:
                    # Remove the status effect
                    unit.status_site_inspection = False
                    # Remove the stat bonuses
                    unit.attack_bonus -= 1
                    unit.move_range_bonus -= 1
                    
                    # Log the expiration
                    message_log.add_message(
                        f"{unit.get_display_name()}'s Site Inspection effect has worn off.",
                        MessageType.ABILITY,
                        player=unit.player
                    )
    
    @measure_perf
    def execute_turn(self, ui=None):
        """Execute all unit actions for the current turn with animated sequence."""
        import time
        import curses
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Store UI reference for animations if provided
        if ui:
            self.ui = ui
            
        logger.info(f"Executing turn {self.turn} for player {self.current_player}")
        
        # Process status effects for the current player's units
        self.process_status_effects()
        
        # Process echo units before executing actions
        # Update duration and handle expired echoes - ONLY for echoes belonging to the current player
        for unit in list(self.units):  # Create a copy of the list to safely modify during iteration
            if unit.is_alive() and unit.is_echo and unit.player == self.current_player:
                # Only decrement duration on the owner's turn
                unit.echo_duration -= 1
                logger.debug(f"Echo {unit.get_display_name()} duration decremented to {unit.echo_duration}")
                
                # If duration reached zero, the echo expires
                if unit.echo_duration <= 0:
                    logger.debug(f"Echo {unit.get_display_name()} expires after owner's turns completed")
                    
                    # Log the expiration
                    message_log.add_message(
                        f"{unit.get_display_name()} fades away...",
                        MessageType.ABILITY,
                        player=unit.player
                    )
                    
                    # Kill the echo (this will trigger death handling later)
                    unit.hp = 0
        
        # Create a single list of units with actions, ordered by timestamp
        units_with_actions = []
        
        # Identify units with actions and FOREMANs with trapped units
        for unit in self.units:
            if not unit.is_alive():
                continue
                
            # Regular actions
            if unit.move_target or unit.attack_target or (unit.skill_target and unit.selected_skill):
                units_with_actions.append(unit)
                
            # Add MANDIBLE_FOREMANs with trapped units (for Viseroy trap damage)
            elif (unit.type == UnitType.MANDIBLE_FOREMAN and 
                  unit.player == self.current_player and 
                  not unit.took_action and
                  any(u.is_alive() and u.trapped_by == unit for u in self.units)):
                # Set a special flag to identify this as a trap damage action
                unit.viseroy_trap_action = True
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
            
            # Flag to track if this is a MANDIBLE_FOREMAN taking an action that should release trapped units
            is_foreman_taking_action = False
            
            # Check if this is a MANDIBLE_FOREMAN
            if unit.type == UnitType.MANDIBLE_FOREMAN:
                # Movement and attacks always release trapped units
                if unit.move_target is not None or unit.attack_target is not None:
                    is_foreman_taking_action = True
                # Some skills release trapped units, but not all
                elif unit.skill_target is not None and unit.selected_skill:
                    # Discharge doesn't automatically release trapped units
                    # as the Discharge skill itself handles the release
                    if unit.selected_skill.name != "Discharge":
                        is_foreman_taking_action = True
            
            # If this is a MANDIBLE_FOREMAN taking an action that should release trapped units
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
                            release_animation = ['<', '[', ' ']
                            
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
                        
                        # Check for trap release due to position change
                        self._check_position_change_trap_release(unit, start_y, start_x)
                        
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
                        # Save original position
                        start_y, start_x = unit.y, unit.x
                        
                        # Without UI, just update position
                        unit.y, unit.x = y, x
                        
                        # Check for trap release due to position change
                        self._check_position_change_trap_release(unit, start_y, start_x)
                else:
                    logger.warning(f"Invalid move target ({y},{x}) for unit at ({unit.y},{unit.x})")
            
            # EXECUTE ATTACK if unit has an attack target
            if unit.attack_target:
                from boneglaive.utils.message_log import message_log, MessageType
                y, x = unit.attack_target
                target = self.get_unit_at(y, x)
                
                # Calculate attacking position (either unit's current position or move target)
                attacking_pos = (unit.y, unit.x)  # Unit's position is already updated if it moved
                
                # Verify attack is within range from the attacking position
                attack_distance = self.chess_distance(attacking_pos[0], attacking_pos[1], y, x)
                
                # Additional line of sight check for GRAYMAN units
                los_check = True
                if unit.type == UnitType.GRAYMAN:
                    los_check = self.has_line_of_sight(attacking_pos[0], attacking_pos[1], y, x)
                    if not los_check:
                        message_log.add_message(
                            f"{unit.get_display_name()}'s attack is blocked by terrain!",
                            MessageType.COMBAT,
                            player=unit.player
                        )
                
                if target and target.player != unit.player and attack_distance <= unit.attack_range and los_check:  # Valid attack
                    # Show attack animation if UI is provided
                    if ui:
                        ui.show_attack_animation(unit, target)
                    
                    # Calculate damage using effective stats (including bonuses)
                    # Defense acts as flat damage reduction
                    effective_stats = unit.get_effective_stats()
                    effective_attack = effective_stats['attack']
                    effective_defense = target.get_effective_stats()['defense']
                    
                    # GRAYMAN's attacks bypass defense
                    if unit.type == UnitType.GRAYMAN:
                        damage = effective_attack  # Bypass defense completely
                    else:
                        damage = max(1, effective_attack - effective_defense)
                    
                    # Store previous HP to check for status changes
                    previous_hp = target.hp
                    critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
                    
                    # Apply damage
                    target.hp = max(0, target.hp - damage)
                    
                    # Check if attacker is a MANDIBLE_FOREMAN with the Viseroy passive
                    # If so, trap the target unit
                    if unit.type == UnitType.MANDIBLE_FOREMAN and unit.passive_skill and \
                       unit.passive_skill.name == "Viseroy" and target.hp > 0:
                        # Check if target is immune to being trapped
                        if target.is_immune_to_trap():  # Changed to is_immune_to_trap
                            message_log.add_message(
                                f"{target.get_display_name()} is immune to Viseroy's trap!",
                                MessageType.ABILITY,
                                player=unit.player,
                                target_name=target.get_display_name()
                            )
                        else:
                            # Only trap if the target is still alive and not immune
                            target.trapped_by = unit
                            target.trap_duration = 0  # Initialize trap duration for incremental damage
                            
                            # Log the trapping (using MessageType.COMBAT for yellow coloring)
                            message_log.add_message(
                                f"{target.get_display_name()} is trapped in mechanical jaws!",
                                MessageType.WARNING,  # WARNING messages are explicitly colored yellow
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
                        # Use centralized death handling
                        self.handle_unit_death(target, unit, cause="combat", ui=ui)
                    else:
                        # Check for critical health (wretching) using centralized logic
                        if not self.check_critical_health(target, unit, previous_hp, ui):
                            continue  # Skip to next unit if processing should stop
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
            
            # EXECUTE VISEROY TRAP DAMAGE if this is a MANDIBLE_FOREMAN with trapped units
            elif hasattr(unit, 'viseroy_trap_action') and unit.viseroy_trap_action:
                # Find all units trapped by this foreman
                trapped_units = [u for u in self.units if u.is_alive() and u.trapped_by == unit]
                
                # Apply trap damage to each trapped unit
                for trapped_unit in trapped_units:
                    # Play trap animation if UI is available
                    if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                        # Get animation sequence for Viseroy trap
                        animation_sequence = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
                        
                        # Show jaw animation at trapped unit's position
                        ui.renderer.animate_attack_sequence(
                            trapped_unit.y, trapped_unit.x,
                            animation_sequence,
                            5,  # color ID (reddish)
                            0.2  # duration
                        )
                        time.sleep(0.2)
                    
                    # Play trap animation if UI is available but don't apply damage here
                    # Actual damage is now handled centrally in _apply_trap_damage method
                    if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                        # Get animation sequence for Viseroy trap
                        animation_sequence = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
                        
                        # Show jaw animation at trapped unit's position (visual only)
                        ui.renderer.animate_attack_sequence(
                            trapped_unit.y, trapped_unit.x,
                            animation_sequence,
                            5,  # color ID (reddish)
                            0.2  # duration
                        )
                        time.sleep(0.2)
                    
                    # No need to show a message here, trap visuals are enough
                
                # Clean up the special flag
                unit.viseroy_trap_action = False
            
            # Add a slight pause between units' actions
            if ui:
                time.sleep(0.5)
        
        # Apply trap damage for all trapped units
        self._apply_trap_damage()
            
        # Clear all actions and update skill cooldowns
        for unit in self.units:
            if unit.is_alive():
                # Reset action targets
                unit.reset_action_targets()
                
                # Reduce cooldowns for skills ONLY for units belonging to current player
                if unit.player == self.current_player:
                    unit.tick_cooldowns()
                    
                    # ONLY decrement durations for effects on the unit owner's turn
                    # This handles Jawline duration specifically
                    if unit.jawline_affected:
                        unit.jawline_duration -= 1
                        
                        # If Jawline duration expires, clear the effect
                        if unit.jawline_duration <= 0:
                            unit.jawline_affected = False
                            # Only restore movement if not affected by other penalties
                            if not unit.was_pried and unit.trapped_by is None:
                                unit.move_range_bonus += 1  # Restore the movement penalty
                            
                            # Log the effect expiration
                            message_log.add_message(
                                f"{unit.get_display_name()} breaks free from Jawline tether!",
                                MessageType.ABILITY,
                                target_name=unit.get_display_name()
                            )
                    
                    # Handle Ossify duration (non-upgraded version only)
                    if hasattr(unit, 'ossify_duration') and unit.ossify_duration > 0:
                        # Check if this is a permanently upgraded MARROW_CONDENSER
                        is_permanent_ossify = False
                        if unit.type == UnitType.MARROW_CONDENSER and hasattr(unit, 'passive_skill'):
                            # Check if Ossify is permanently upgraded through Dominion
                            if hasattr(unit.passive_skill, 'ossify_upgraded') and unit.passive_skill.ossify_upgraded:
                                is_permanent_ossify = True
                        
                        # If not permanent, decrement duration (applies to all unit types)
                        if not is_permanent_ossify:
                            unit.ossify_duration -= 1
                            
                            # If duration expires, restore movement and remove defense bonus
                            if unit.ossify_duration <= 0:
                                # Only restore movement if not affected by other penalties
                                if not hasattr(unit, 'was_pried') or not unit.was_pried:
                                    if not hasattr(unit, 'jawline_affected') or not unit.jawline_affected:
                                        if not hasattr(unit, 'trapped_by') or unit.trapped_by is None:
                                            unit.move_range_bonus += 1  # Restore the movement penalty
                                
                                # Remove defense bonus as well
                                unit.defense_bonus -= self.get_ossify_defense_bonus(unit)
                                
                                # Log the effect expiration
                                message_log.add_message(
                                    f"{unit.get_display_name()}'s ossified bone structure returns to normal!",
                                    MessageType.ABILITY,
                                    player=unit.player,
                                    target_name=unit.get_display_name()
                                )
                
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
        
        # Process MarrowDike wall durations
        if hasattr(self, 'marrow_dike_tiles'):
            tiles_to_remove = []
            interior_to_remove = []
            
            # Process each MarrowDike tile
            for (tile_y, tile_x), dike_info in list(self.marrow_dike_tiles.items()):
                # Only decrement on the owner's turn
                if dike_info['owner'].player == self.current_player:
                    dike_info['duration'] -= 1
                    
                    # If duration reached zero, mark for removal
                    if dike_info['duration'] <= 0:
                        tiles_to_remove.append((tile_y, tile_x))
            
            # Also process interior tiles
            if hasattr(self, 'marrow_dike_interior'):
                for (tile_y, tile_x), dike_info in list(self.marrow_dike_interior.items()):
                    # Only decrement on the owner's turn
                    if dike_info['owner'].player == self.current_player:
                        dike_info['duration'] -= 1
                        
                        # If duration reached zero, mark for removal
                        if dike_info['duration'] <= 0:
                            interior_to_remove.append((tile_y, tile_x))
            
            # This section is no longer needed as healing is now handled through the interior tiles
            # Interior processing now considers all dikes on every turn, not just the current player's dikes
            
            # Process removals and restore original terrain
            for tile_y, tile_x in tiles_to_remove:
                tile = (tile_y, tile_x)
                # Restore original terrain
                if tile in self.marrow_dike_tiles and 'original_terrain' in self.marrow_dike_tiles[tile]:
                    original_terrain = self.marrow_dike_tiles[tile]['original_terrain']
                    self.map.set_terrain_at(tile_y, tile_x, original_terrain)
                
                # Remove from marrow_dike_tiles
                if tile in self.marrow_dike_tiles:
                    dike_info = self.marrow_dike_tiles[tile]
                    owner = dike_info['owner']
                    del self.marrow_dike_tiles[tile]
                    
                    # Log the expiration
                    message_log.add_message(
                        f"A section of {owner.get_display_name()}'s Marrow Dike crumbles away...",
                        MessageType.ABILITY,
                        player=owner.player
                    )
            
            # Also remove expired interior tiles
            if hasattr(self, 'marrow_dike_interior'):
                for tile_y, tile_x in interior_to_remove:
                    tile = (tile_y, tile_x)
                    # Remove from marrow_dike_interior
                    if tile in self.marrow_dike_interior:
                        del self.marrow_dike_interior[tile]
            
            # Process healing for upgraded Marrow Dikes (blood plasma healing effect)
            # Group all upgraded dikes by owner to process healing collectively
            if hasattr(self, 'marrow_dike_interior') and self.marrow_dike_interior:
                # Find all upgraded dike interiors belonging to either player, not just current player
                # This makes healing work on every turn for all players
                upgraded_dikes_by_owner = {}
                
                for tile_pos, dike_info in self.marrow_dike_interior.items():
                    # Check if the dike is upgraded (we're healing from ALL upgraded dikes, not just current player's)
                    if dike_info.get('upgraded', False):
                        # Group by owner unit
                        owner = dike_info['owner']
                        if owner not in upgraded_dikes_by_owner:
                            upgraded_dikes_by_owner[owner] = []
                        upgraded_dikes_by_owner[owner].append(tile_pos)
                
                # Process healing for each owner's upgraded dikes
                for owner, interior_tiles in upgraded_dikes_by_owner.items():
                    # Find all allied units standing in the upgraded dike interior
                    healed_units = []
                    
                    for unit in self.units:
                        # Only consider allied units that are not at full health
                        if unit.is_alive() and unit.player == owner.player and unit.hp < unit.max_hp:
                            unit_pos = (unit.y, unit.x)
                            
                            # Check if unit is inside any of this owner's upgraded dike interior
                            for interior_pos in interior_tiles:
                                if unit_pos == interior_pos:
                                    if unit not in healed_units:
                                        healed_units.append(unit)
                                        # Debug log
                                        logger.debug(f"Adding {unit.get_display_name()} to be healed inside dike at {unit_pos}")
                                    break
                    
                    # Apply healing to all identified units
                    if healed_units:
                        # Get healing amount from the skill definition 
                        healing_amount = 2  # Default
                        
                        # Try to get healing amount from the skill if possible
                        for skill in owner.active_skills:
                            if skill.name == "Marrow Dike" and hasattr(skill, 'healing_amount'):
                                healing_amount = skill.healing_amount
                                break
                        
                        # Heal each unit and log the effect
                        for unit in healed_units:
                            # Store previous HP for comparison
                            previous_hp = unit.hp
                            
                            # Apply healing (capped at max HP)
                            unit.hp = min(unit.max_hp, unit.hp + healing_amount)
                            
                            # Only log if unit actually received healing
                            if unit.hp > previous_hp:
                                actual_healing = unit.hp - previous_hp
                                heal_message = f"{unit.get_display_name()} is healed for {actual_healing} HP by {owner.get_display_name()}'s blood plasma!"
                                message_log.add_message(
                                    heal_message,
                                    MessageType.ABILITY,
                                    player=owner.player
                                )
                                # Add debug log
                                logger.info(heal_message)
                                
                                # Show healing animation and display healing numbers if UI is available
                                if ui and hasattr(ui, 'renderer'):
                                    # Flash the unit with healing colors
                                    if hasattr(ui, 'asset_manager'):
                                        # Flash unit with healing animation
                                        tile_ids = [ui.asset_manager.get_unit_tile(unit.type)] * 4
                                        color_ids = [6, 3 if unit.player == 1 else 4] * 2  # Alternate yellow with player color
                                        durations = [0.1] * 4
                                        
                                        # Use renderer's flash tile method
                                        ui.renderer.flash_tile(unit.y, unit.x, tile_ids, color_ids, durations)
                                    
                                    # Get healing animation sequence
                                    healing_animation = ui.asset_manager.get_skill_animation_sequence('marrow_healing')
                                    if healing_animation:
                                        # Show healing animation
                                        ui.renderer.animate_attack_sequence(
                                            unit.y, unit.x,
                                            healing_animation,
                                            6,  # Yellow color for healing
                                            0.05  # Quick animation
                                        )
                                    
                                    # Show healing number above unit
                                    healing_text = f"+{actual_healing}"
                                    
                                    # Make healing text stand out with green color
                                    for i in range(3):
                                        # First clear the area
                                        ui.renderer.draw_text(unit.y-1, unit.x*2, " " * len(healing_text), 7)
                                        # Draw with alternating bold/normal for a flashing effect
                                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                                        ui.renderer.draw_text(unit.y-1, unit.x*2, healing_text, 3, attrs)  # Green color
                                        ui.renderer.refresh()
                                        time.sleep(0.1)
                                    
                                    # Final healing display (stays on screen slightly longer)
                                    ui.renderer.draw_text(unit.y-1, unit.x*2, healing_text, 3, curses.A_BOLD)
                                    ui.renderer.refresh()
                                    time.sleep(0.3)
        
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
    
    def try_trigger_wretched_decension(self, attacker, target, ui=None):
        """
        Try to trigger Wretched Decension if attacker is a FOWL_CONTRIVANCE
        and target is at critical health.
        
        Args:
            attacker: The attacking unit
            target: The unit that was damaged
            ui: Optional UI reference for animations
        
        Returns:
            bool: True if Wretched Decension triggered, False otherwise
        """
        import random
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.constants import UnitType, CRITICAL_HEALTH_PERCENT
        
        logger.debug(f"Checking Wretched Decension trigger for attacker: {attacker.get_display_name()}, target: {target.get_display_name()}")
        
        # Check if attacker is FOWL_CONTRIVANCE
        if attacker.type != UnitType.FOWL_CONTRIVANCE:
            logger.debug("Not a FOWL_CONTRIVANCE, skipping Wretched Decension check")
            return False
        
        # Check if attacker has the passive skill
        if not hasattr(attacker, 'passive_skill') or not attacker.passive_skill or attacker.passive_skill.name != "Wretched Decension":
            logger.debug("No Wretched Decension passive skill, skipping")
            return False
        
        # Check if target is at critical health
        critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
        if target.hp > critical_threshold:
            logger.debug(f"Target not in critical health ({target.hp} > {critical_threshold}), skipping Wretched Decension")
            return False
            
        # Check if target is already dead
        if not target.is_alive():
            logger.debug("Target already dead, skipping Wretched Decension")
            return False
        
        logger.debug("Calculating Wretched Decension chance...")
        
        # Calculate chance based on number of allied FOWL_CONTRIVANCE units
        try:
            trigger_chance = attacker.passive_skill.check_wretched_decension_chance(self, attacker)
            logger.debug(f"Calculated trigger chance: {trigger_chance}")
        except Exception as e:
            logger.debug(f"Error calculating trigger chance: {str(e)}, using fallback method")
            # Fallback if method not available
            allied_fowl_count = 0
            for unit in self.units:
                if unit.is_alive() and unit.player == attacker.player and unit.type == UnitType.FOWL_CONTRIVANCE:
                    allied_fowl_count += 1
            
            logger.debug(f"Allied FOWL_CONTRIVANCE count: {allied_fowl_count}")
            
            # Calculate trigger chance
            if allied_fowl_count == 1:
                trigger_chance = 1.0  # 100% chance
            elif allied_fowl_count == 2:
                trigger_chance = 0.5  # 50% chance
            elif allied_fowl_count >= 3:
                trigger_chance = 0.25  # 25% chance
            else:
                # Should never happen, but fallback
                trigger_chance = 1.0
                
            logger.debug(f"Fallback trigger chance: {trigger_chance}")
        
        # Roll for trigger
        roll = random.random()
        logger.debug(f"Random roll: {roll}, trigger threshold: {trigger_chance}")
        
        if roll <= trigger_chance:
            # Success! Wretched Decension triggers
            logger.debug("TRIGGERING WRETCHED DECENSION!")
            
            message_log.add_message(
                f"The flocks descends to claim the wretched!",
                MessageType.ABILITY,
                player=attacker.player,
                target_name=target.get_display_name()
            )
            
            # Show animation if UI is available
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                logger.debug("Playing Wretched Decension animation")
                
                # Get animation from asset manager
                wretched_animation = ui.asset_manager.get_skill_animation_sequence('wretched_decension')
                if not wretched_animation:
                    # Fallback animation if not defined - birds descending to claim the wretched
                    wretched_animation = [
                        '.', '..', '...', '^', '^^', '^^^', 'v^v', '>v<', 'vVv',
                        'WVW', '\\V/', '#V#', '@V@', '###', '@@@', '...', '.'
                    ]
                
                # Animate the descending flock using built-in animation renderer
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    wretched_animation,
                    1,  # Red color for death
                    0.1  # Duration
                )
                
                # Add a final flash effect at the end
                if hasattr(ui, 'asset_manager'):
                    # Flash between red and white for dramatic finale
                    tile_ids = ['@', '#', '%', ' ']
                    color_ids = [1, 7, 1, 7]  # Alternate red and white
                    durations = [0.1, 0.1, 0.1, 0.2]  # Last frame lingers
                    
                    # Use renderer's flash tile method for finale
                    ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
            
            # Kill the target (set HP to 0)
            target.hp = 0
            
            # Handle unit death
            self.handle_unit_death(target, attacker, cause="wretched_decension", ui=ui)
            return True
        else:
            # Failed to trigger
            logger.debug("Wretched Decension failed to trigger")
            
            message_log.add_message(
                f"The flocks fail to coordinate their descent.",
                MessageType.ABILITY,
                player=attacker.player,
                target_name=target.get_display_name()
            )
            return False
    
    def try_trigger_autoclave(self, target_unit, ui=None):
        """Try to trigger Autoclave if conditions are met."""
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.constants import UnitType, CRITICAL_HEALTH_PERCENT
        
        logger.debug(f"Checking Autoclave trigger for {target_unit.get_display_name()}")
        
        # Skip if not a GLAIVEMAN or already activated
        if target_unit.type != UnitType.GLAIVEMAN:
            logger.debug("Not a GLAIVEMAN, skipping Autoclave check")
            return False
            
        if not target_unit.passive_skill or target_unit.passive_skill.name != "Autoclave":
            logger.debug("No Autoclave passive skill, skipping")
            return False
            
        if target_unit.passive_skill.activated:
            logger.debug("Autoclave already activated, skipping")
            return False
        
        # Check if unit is in critical health
        critical_threshold = int(target_unit.max_hp * CRITICAL_HEALTH_PERCENT)
        if target_unit.hp > critical_threshold:
            logger.debug(f"Unit not in critical health ({target_unit.hp} > {critical_threshold}), skipping Autoclave")
            return False
        
        logger.debug("Checking for eligible Autoclave targets...")
        # Check for eligible targets
        if not target_unit.passive_skill._has_eligible_targets(target_unit, self):
            logger.debug("No eligible targets for Autoclave, aborting")
            
            # Check if we've already shown the failure message for this unit
            # If not, show it and mark it as shown
            if not hasattr(target_unit, 'autoclave_failure_shown'):
                message_log.add_message(
                    f"{target_unit.get_display_name()}'s Autoclave fails to activate - no targets in range!",
                    MessageType.ABILITY,
                    player=target_unit.player
                )
                target_unit.autoclave_failure_shown = True
                
                # Visual feedback if UI is available
                if ui and hasattr(ui, 'renderer'):
                    # Show failed activation animation
                    failed_animation = ['!', '?', '!']
                    ui.renderer.animate_attack_sequence(
                        target_unit.y, target_unit.x,
                        failed_animation,
                        6,  # yellowish color for warning
                        0.2  # duration
                    )
            
            return False
        
        logger.debug("TRIGGERING AUTOCLAVE!")
        # Trigger the effect immediately
        target_unit.passive_skill._trigger_autoclave(target_unit, self, ui)
        target_unit.passive_skill.activated = True
        return True
    
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
                not foreman.took_action):
                logger.debug(f"Applying Viseroy trap damage to {unit.get_display_name()}")
                
                # Play trap animation if UI is available
                ui = getattr(self, 'ui', None)
                if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                    # Get animation sequence for Viseroy trap
                    animation_sequence = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
                    
                    # Show jaw animation at trapped unit's position
                    ui.renderer.animate_attack_sequence(
                        unit.y, unit.x,
                        animation_sequence,
                        5,  # color ID (reddish)
                        0.2  # duration
                    )
                    time.sleep(0.2)
                
                # Incremental trap damage - starts at 3 and increases by 1 each turn
                # First turn trapped: trap_duration = 0, damage base = 3
                # Second turn trapped: trap_duration = 1, damage base = 4
                # Third turn trapped: trap_duration = 2, damage base = 5, etc.
                base_trap_damage = 3 + unit.trap_duration
                effective_defense = unit.get_effective_stats()['defense']
                damage = max(1, base_trap_damage - effective_defense)
                
                # Increment trap duration for next turn's damage calculation
                unit.trap_duration += 1
                
                # Apply damage to the trapped unit
                previous_hp = unit.hp
                unit.hp = max(0, unit.hp - damage)
                
                # Log the damage
                message_log.add_combat_message(
                    attacker_name=foreman.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability="Viseroy Trap",
                    attacker_player=foreman.player,
                    target_player=unit.player,
                    trap_duration=unit.trap_duration  # Pass trap duration for message formatting
                )
                
                # Check for Autoclave trigger - same logic as regular attacks
                critical_threshold = int(unit.max_hp * CRITICAL_HEALTH_PERCENT)
                # Check if target just entered critical health
                if previous_hp > critical_threshold and unit.hp <= critical_threshold:
                    message_log.add_message(
                        f"{unit.get_display_name()} wretches!",
                        MessageType.COMBAT,
                        player=foreman.player,
                        target=unit.player,
                        target_name=unit.get_display_name()
                    )
                    
                    # Directly try to trigger Autoclave for the trapped unit
                    self.try_trigger_autoclave(unit, ui)
                    
                # Check if target is already in critical health and took more damage
                elif previous_hp <= critical_threshold and unit.hp <= critical_threshold and unit.hp > 0:
                    # Directly try to trigger Autoclave for the trapped unit
                    self.try_trigger_autoclave(unit, ui)
                
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
                    
                    # Show damage number above target with same appearance as attack damage
                    damage_text = f"-{damage}"
                    
                    # Make damage text more prominent
                    for i in range(3):
                        # First clear the area
                        ui.renderer.draw_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                        # Draw with alternating bold/normal for a flashing effect
                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                        ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 7, attrs)  # White color (same as attack damage)
                        ui.renderer.refresh()
                        time.sleep(0.1)
                    
                    # Final damage display (stays on screen slightly longer)
                    ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 7, curses.A_BOLD)
                    ui.renderer.refresh()
                    time.sleep(0.3)  # Match the 0.3s delay used in attack damage
                
                # Check if the trapped unit was defeated
                if unit.hp <= 0:
                    message_log.add_message(
                        f"{unit.get_display_name()} perishes!",
                        MessageType.COMBAT,
                        player=foreman.player,
                        target=unit.player,
                        target_name=unit.get_display_name()
                    )
                    unit.trapped_by = None
    
    def _check_position_change_trap_release(self, unit, old_y, old_x):
        """
        Check if the unit that changed position is either:
        1. A MANDIBLE_FOREMAN that has trapped units
        2. A unit that is trapped by a MANDIBLE_FOREMAN
        
        If either case is true, release the trap since the jaws can't maintain
        their grip when either unit's position changes.
        
        This method is called for any position change, including:
        - Regular movement
        - Forced displacement (like Pry skill)
        - Any other position change mechanism
        
        Args:
            unit: The unit that had its position changed
            old_y, old_x: Previous position of the unit
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        
        # Case 1: The unit is a MANDIBLE_FOREMAN that has trapped units
        if unit.type == UnitType.MANDIBLE_FOREMAN:
            # Find any units trapped by this FOREMAN
            trapped_units = [u for u in self.units if u.is_alive() and u.trapped_by == unit]
            if trapped_units:
                logger.debug(f"MANDIBLE_FOREMAN {unit.get_display_name()} position changed, releasing trapped units")
                
                # Release the trapped units
                for trapped_unit in trapped_units:
                    trapped_unit.trapped_by = None
                    trapped_unit.trap_duration = 0  # Reset trap duration
                    message_log.add_message(
                        f"{trapped_unit.get_display_name()} is released from mechanical jaws!",
                        MessageType.ABILITY,
                        target_name=trapped_unit.get_display_name()
                    )
        
        # Case 2: The unit is trapped by a MANDIBLE_FOREMAN
        if unit.trapped_by is not None:
            logger.debug(f"Trapped unit {unit.get_display_name()} position changed, breaking free from jaws")
            
            # Store reference to the foreman for the message
            foreman = unit.trapped_by
            
            # Release the unit
            unit.trapped_by = None
            unit.trap_duration = 0  # Reset trap duration
            
            # Log the release
            message_log.add_message(
                f"{unit.get_display_name()} breaks free from mechanical jaws!",
                MessageType.ABILITY,
                target_name=unit.get_display_name()
            )
    
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
                        release_animation = ['<', '[', ' ']
                        
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
        
    def _trigger_echo_death_effect(self, echo_unit, ui=None):
        """
        Handle the death effect when an echo unit is destroyed.
        Echoes explode and deal 3 damage to all adjacent units when destroyed.
        
        Args:
            echo_unit: The echo unit that was destroyed
            ui: Optional UI reference for animations
        """
        import time
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        
        logger.debug(f"Echo {echo_unit.get_display_name()} destroyed, triggering death effect")
        
        # Find all units in adjacent tiles (chess distance 1)
        affected_units = []
        for unit in self.units:
            if not unit.is_alive():
                continue
                
            # Calculate distance to echo
            distance = self.chess_distance(echo_unit.y, echo_unit.x, unit.y, unit.x)
            if distance <= 1 and unit != echo_unit:  # Adjacent including diagonals, excluding the echo itself
                affected_units.append(unit)
        
        if not affected_units:
            # No units affected
            return
            
        # Log the explosion
        message_log.add_message(
            f"{echo_unit.get_display_name()} explodes, affecting {len(affected_units)} nearby unit(s)!",
            MessageType.ABILITY,
            player=echo_unit.player
        )
        
        # Animation for explosion
        if ui and hasattr(ui, 'renderer'):
            # Show explosion animation at echo position
            explosion_animation = ['*', 'X', '#', '+', '.']
            ui.renderer.animate_attack_sequence(
                echo_unit.y, echo_unit.x,
                explosion_animation,
                7,  # Yellow/explosion color
                0.1  # Duration
            )
            
            # Redraw board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                time.sleep(0.2)  # Short pause after explosion
            
        # Apply damage to affected units
        for unit in affected_units:
            # Increased from 3 to 4 damage for GRAYMAN echo explosions
            damage = 4
            # Apply defense reduction for explosions
            effective_defense = unit.get_effective_stats()['defense']
            damage = max(1, damage - effective_defense)
            
            # Store previous HP
            previous_hp = unit.hp
            
            # Apply damage
            unit.hp = max(0, unit.hp - damage)
            
            # Log the damage
            message_log.add_message(
                f"{unit.get_display_name()} takes {damage} damage from echo explosion!",
                MessageType.COMBAT,
                player=echo_unit.player,
                target_name=unit.get_display_name()
            )
            
            # Check if unit was killed
            if unit.hp <= 0 and previous_hp > 0:
                # Use centralized death handling
                self.handle_unit_death(unit, echo_unit, cause="explosion", ui=ui)
                
                # Check if this was a MANDIBLE_FOREMAN or another echo
                if unit.type == UnitType.MANDIBLE_FOREMAN:
                    # Release trapped units
                    for trapped_unit in self.units:
                        if trapped_unit.is_alive() and trapped_unit.trapped_by == unit:
                            logger.debug(f"MANDIBLE_FOREMAN perished from explosion, releasing {trapped_unit.get_display_name()}")
                            trapped_unit.trapped_by = None
                            message_log.add_message(
                                f"{trapped_unit.get_display_name()} is released from mechanical jaws!",
                                MessageType.ABILITY,
                                target_name=trapped_unit.get_display_name()
                            )
                elif unit.is_echo:
                    # Chain reaction - trigger this echo's death effect too
                    self._trigger_echo_death_effect(unit, ui)
    
    @measure_perf
    def _handle_effect_expired(self, event_type, event_data):
        """
        Handle effect expiration events from skills.
        Removes bonuses and debuffs when a skill effect expires.
        
        Args:
            event_type: The event type (should be EFFECT_EXPIRED)
            event_data: The event data containing the skill_name
        """
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        
        skill_name = getattr(event_data, 'skill_name', None)
        if not skill_name:
            logger.warning("Received EFFECT_EXPIRED event without skill_name")
            return
        
        logger.debug(f"Handling effect expiration for skill: {skill_name}")
        
        # Handle different skills if needed in the future
        
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