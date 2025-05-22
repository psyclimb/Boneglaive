#!/usr/bin/env python3
import logging
import curses
import time
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH, CRITICAL_HEALTH_PERCENT
from boneglaive.game.units import Unit
from boneglaive.game.map import GameMap, MapFactory, TerrainType
from boneglaive.utils.debug import debug_config, measure_perf, game_assert, logger
from boneglaive.utils.message_log import message_log, MessageType

# Set up module logger if not already set up
if 'logger' not in locals():
    logger = debug_config.setup_logging('game.engine')

class Game:
    def __init__(self, skip_setup=False, map_name="lime_foyer_arena"):
        self.units = []
        self.current_player = 1
        self.turn = 1
        self.winner = None
        self.test_mode = False  # For debugging
        self.local_multiplayer = False

        # Track whether this is player 2's first turn
        self.is_player2_first_turn = True

        # Action ordering
        self.action_counter = 0  # Track order of unit actions
        
        # Create the game map
        self.map = MapFactory.create_map(map_name)
        self.map_name = map_name  # Store current map name
        
        # Game state
        self.setup_phase = not skip_setup  # Whether we're in setup phase
        self.setup_player = 1    # Which player is placing units
        self.setup_confirmed = {1: False, 2: False}  # Whether players have confirmed setup
        self.setup_units_remaining = {1: 3, 2: 3}    # How many units each player can still place (3 total)
        # During setup, players are limited to a maximum of 2 units of the same type
        
        # If skipping setup, add default units
        if skip_setup:
            self.setup_initial_units()
            
        # Subscribe to events
        from boneglaive.utils.event_system import get_event_manager, EventType
        self.event_manager = get_event_manager()
        self.event_manager.subscribe(EventType.EFFECT_EXPIRED, self._handle_effect_expired)
        
        # Apply passive skills for current player's units
        for unit in self.units:
            if unit.is_alive() and unit.player == self.current_player:
                unit.apply_passive_skills(self)
            
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
    
    def _place_default_units_for_player(self, player):
        """
        Place default units for the specified player.
        Used in single player mode to automatically place opponent units.
        
        Args:
            player: The player number (typically 2 for single player mode)
        """
        from boneglaive.utils.debug import logger
        logger.info(f"Setting up default units for player {player}")
        
        # Find valid positions for units that aren't on limestone
        valid_positions = []
        
        # For player 2, place units on the right side of the map with randomness
        if player == 2:
            import random
            
            # Define a larger area to place units
            min_y, max_y = 2, 8  # Expanded Y range for more variety
            min_x, max_x = 10, 16  # Expanded X range for more variety
            
            # Generate a list of all valid positions in this area
            all_possible_positions = []
            for y in range(min_y, max_y):
                for x in range(min_x, max_x):
                    if self.map.can_place_unit(y, x):
                        all_possible_positions.append((y, x))
            
            # If we found enough potential positions
            if len(all_possible_positions) >= 3:
                # Shuffle to add randomness
                random.shuffle(all_possible_positions)
                
                # Start with first random position
                first_pos = all_possible_positions[0]
                valid_positions.append(first_pos)
                first_y, first_x = first_pos
                
                # Remove first position from available positions
                remaining = all_possible_positions[1:]
                
                # Sort by distance to first point (closest first)
                remaining.sort(key=lambda pos: self.chess_distance(first_y, first_x, pos[0], pos[1]))
                
                # Take a random position from the closest 5 (or fewer if not available)
                selection_pool = remaining[:min(5, len(remaining))]
                if selection_pool:
                    second_pos = random.choice(selection_pool)
                    valid_positions.append(second_pos)
                    second_y, second_x = second_pos
                    
                    # Remove second position
                    remaining.remove(second_pos)
                    
                    # For third unit, prefer positions that maintain group cohesion
                    remaining.sort(key=lambda pos: 
                        self.chess_distance(first_y, first_x, pos[0], pos[1]) + 
                        self.chess_distance(second_y, second_x, pos[0], pos[1]))
                    
                    # Again add randomness - select from closest 5 positions
                    selection_pool = remaining[:min(5, len(remaining))]
                    if selection_pool:
                        third_pos = random.choice(selection_pool)
                        valid_positions.append(third_pos)
                
                # Log the positions for debugging
                logger.info(f"Randomized positions for Player {player}: {valid_positions}")
                for i, pos in enumerate(valid_positions):
                    y, x = pos
                    logger.info(f"AI Unit {i+1} will spawn at position ({y}, {x})")
            
            # If we couldn't find enough valid positions with randomization, fall back to the old method
            if len(valid_positions) < 3:
                logger.warning("Failed to find enough randomized positions, falling back to fixed positions")
                valid_positions = []
                for y in range(3, 7):
                    for x in range(11, 15):
                        if self.map.can_place_unit(y, x):
                            valid_positions.append((y, x))
                            if len(valid_positions) >= 3:
                                break
                    if len(valid_positions) >= 3:
                        break
        
        # Check if we're in VS_AI mode
        from boneglaive.utils.config import ConfigManager, NetworkMode
        config = ConfigManager()
        is_vs_ai_mode = config.get('network_mode') == NetworkMode.VS_AI.value
        
        if is_vs_ai_mode and player == 2:
            # In VS_AI mode, use exactly one of each unit type for player 2
            logger.info("VS_AI mode detected - using exactly one of each unit type for player 2")
            
            # Make sure we have the expected number of positions
            if len(valid_positions) >= 3:
                # Fixed unit types for VS_AI player 2
                vs_ai_types = [
                    UnitType.GLAIVEMAN,
                    UnitType.MANDIBLE_FOREMAN,
                    UnitType.MARROW_CONDENSER
                ]
                
                # Add each unit at a valid position
                for i, (y, x) in enumerate(valid_positions[:3]):
                    unit_type = vs_ai_types[i]
                    self.add_unit(unit_type, player, y, x)
                    logger.info(f"Added VS_AI mode {unit_type.name} for player {player} at ({y}, {x})")
                
                # Return early since we've added all units
                return
        
        # Standard unit placement for non-VS_AI modes
        # Track unit counts to enforce 2-unit type limit
        unit_counts = {}
        
        # Set up a variety of unit types to use
        unit_types = [
            UnitType.GLAIVEMAN,
            UnitType.MANDIBLE_FOREMAN,
            UnitType.MARROW_CONDENSER
        ]
        
        for y, x in valid_positions:
            # Choose a valid unit type (respecting the 2-unit limit)
            valid_types = [t for t in unit_types
                        if unit_counts.get(t, 0) < 2]
            
            # Default to GLAIVEMAN if no valid types (shouldn't happen)
            if not valid_types:
                logger.warning(f"No valid unit types available for player {player}. Using GLAIVEMAN.")
                unit_type = UnitType.GLAIVEMAN
            else:
                # Rotate through valid types to ensure variety
                unit_type = valid_types[0]
            
            # Add the unit with the selected type
            self.add_unit(unit_type, player, y, x)
            
            # Update unit count for this type
            unit_counts[unit_type] = unit_counts.get(unit_type, 0) + 1
            
            logger.info(f"Added {unit_type.name} for player {player} at ({y}, {x})")
        
        # If we couldn't find enough valid positions, add some emergency units
        if len(valid_positions) < 3:
            missing = 3 - len(valid_positions)
            logger.warning(f"Not enough valid positions found. Adding {missing} emergency units for player {player}.")
            
            # Emergency positions depend on player
            emergency_positions = [
                (8, 16), (8, 17), (8, 18)  # Player 2 emergency positions
            ]
            
            # Place units at emergency positions
            for i in range(missing):
                y, x = emergency_positions[i]
                
                # Choose a valid unit type (respecting the 2-unit limit)
                valid_types = [t for t in unit_types
                            if unit_counts.get(t, 0) < 2]
                
                # Default to GLAIVEMAN if no valid types
                if not valid_types:
                    unit_type = UnitType.GLAIVEMAN
                else:
                    unit_type = valid_types[0]
                
                # Add the unit with the selected type
                self.add_unit(unit_type, player, y, x)
                
                # Update unit count for this type
                unit_counts[unit_type] = unit_counts.get(unit_type, 0) + 1
                
                logger.info(f"Added emergency {unit_type.name} for player {player} at ({y}, {x})")
    
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
        
        # Check if we're in VS_AI mode - we need to handle this specifically
        from boneglaive.utils.config import ConfigManager, NetworkMode
        config = ConfigManager()
        is_vs_ai_mode = config.get('network_mode') == NetworkMode.VS_AI.value
        
        # Print debug info
        logger.info(f"Game Mode: {config.get('network_mode')}, VS_AI Mode: {is_vs_ai_mode}")
        
        # Define specific unit types to use for Player 2 in VS_AI mode
        vs_ai_p2_unit_types = [
            UnitType.GLAIVEMAN,
            UnitType.MANDIBLE_FOREMAN,
            UnitType.MARROW_CONDENSER
        ]
        
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
                
        # Check right side for player 2 - with randomness
        import random
        logger.info("Finding positions for player 2 units with randomness")
        p2_positions = []
        
        # Define a larger area to place units
        min_y, max_y = 2, 8  # Expanded Y range for more variety
        min_x, max_x = 10, 16  # Expanded X range for more variety
        
        # Generate a list of all valid positions in this area
        all_valid_positions = []
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                if self.map.can_place_unit(y, x):
                    all_valid_positions.append((2, y, x))
        
        # Shuffle the positions to add randomness
        random.shuffle(all_valid_positions)
        
        # Pick positions that maintain group cohesion by ensuring they're not too far apart
        if len(all_valid_positions) >= 3:
            # Start with a random valid position
            first_pos = all_valid_positions[0]
            p2_positions.append(first_pos)
            
            # For remaining units, prefer positions closer to the first unit
            remaining_positions = all_valid_positions[1:]
            
            # Sort remaining positions by distance to first unit (closest first)
            player, first_y, first_x = first_pos
            remaining_positions.sort(key=lambda pos: self.chess_distance(first_y, first_x, pos[1], pos[2]))
            
            # Add some randomness to the selection - don't just pick the closest
            # Take the closest 5 positions and randomly select from them
            selection_pool = remaining_positions[:min(5, len(remaining_positions))]
            if selection_pool:
                second_pos = random.choice(selection_pool)
                p2_positions.append(second_pos)
                
                # Remove the selected position from remaining positions
                remaining_positions.remove(second_pos)
                
                # For the third unit, prefer positions closer to both existing units
                if remaining_positions:
                    player, second_y, second_x = second_pos
                    # Calculate combined distance score to both existing units
                    remaining_positions.sort(key=lambda pos: 
                        self.chess_distance(first_y, first_x, pos[1], pos[2]) + 
                        self.chess_distance(second_y, second_x, pos[1], pos[2]))
                    
                    # Again add randomness - select from closest 5 positions
                    selection_pool = remaining_positions[:min(5, len(remaining_positions))]
                    if selection_pool:
                        third_pos = random.choice(selection_pool)
                        p2_positions.append(third_pos)
        
        # If we couldn't find enough valid positions, fall back to conventional method
        if len(p2_positions) < 3:
            logger.warning("Failed to find randomized positions, falling back to fixed positions")
            p2_positions = []
            for y in range(3, 7):
                for x in range(11, 15):
                    if self.map.can_place_unit(y, x):
                        p2_positions.append((2, y, x))
                        if len(p2_positions) >= 3:
                            break
                if len(p2_positions) >= 3:
                    break
        
        logger.info(f"Selected {len(p2_positions)} randomized positions for player 2")
                
        valid_positions.extend(p2_positions)
        logger.info(f"Found {len(valid_positions)} valid positions for units")
        
        # Unit type setup
        player1_unit_types = [
            UnitType.GLAIVEMAN,
            UnitType.MANDIBLE_FOREMAN,
            UnitType.MARROW_CONDENSER
        ]
        
        # Track unit counts for each player and type
        player_unit_counts = {
            1: {},  # Player 1 unit counts by type
            2: {}   # Player 2 unit counts by type
        }
        
        # SPECIAL HANDLING FOR VS_AI MODE
        if is_vs_ai_mode:
            logger.info("VS_AI mode detected, using exactly one of each unit type for player 2")
            
            # First create units for player 2 (AI) to ensure we get exactly one of each type
            if len(p2_positions) >= 3:
                # Add exactly one of each unit type for player 2
                types_to_add = [UnitType.GLAIVEMAN, UnitType.MANDIBLE_FOREMAN, UnitType.MARROW_CONDENSER]
                
                for i, (player, y, x) in enumerate(p2_positions[:3]):
                    unit_type = types_to_add[i]
                    self.add_unit(unit_type, player, y, x)
                    
                    # Update unit count
                    player_unit_counts.setdefault(player, {})
                    player_unit_counts[player][unit_type] = player_unit_counts[player].get(unit_type, 0) + 1
                    
                    logger.info(f"Added Player 2 (AI) unit {unit_type.name} at ({y}, {x})")
                    
                # Now add player 1 units with variety
                for player, y, x in valid_positions:
                    if player == 1:
                        # Get valid unit types that don't exceed the 2-unit limit
                        valid_types = [t for t in player1_unit_types 
                                    if player_unit_counts.get(player, {}).get(t, 0) < 2]
                        
                        # Default to GLAIVEMAN if no valid types
                        if not valid_types:
                            unit_type = UnitType.GLAIVEMAN
                        else:
                            unit_type = valid_types[0]
                        
                        # Add the unit
                        self.add_unit(unit_type, player, y, x)
                        
                        # Update unit count
                        player_unit_counts.setdefault(player, {})
                        player_unit_counts[player][unit_type] = player_unit_counts[player].get(unit_type, 0) + 1
                        
                        logger.info(f"Added Player 1 unit {unit_type.name} at ({y}, {x})")
            else:
                logger.error(f"Not enough positions for Player 2 in VS_AI mode")
        else:
            # STANDARD UNIT PLACEMENT FOR NON-VS_AI MODES
            logger.info("Using standard unit placement for non-VS_AI mode")
            
            # Add units at valid positions with appropriate types
            for player, y, x in valid_positions:
                if player == 1:
                    # For player 1, respect the 2-unit type limit
                    valid_types = [t for t in player1_unit_types 
                                if player_unit_counts.get(player, {}).get(t, 0) < 2]
                    
                    # Default to GLAIVEMAN if no valid types
                    if not valid_types:
                        unit_type = UnitType.GLAIVEMAN
                    else:
                        unit_type = valid_types[0]
                else:  # player 2
                    # For player 2, use rotation of types
                    # Default rotation of unit types with variety
                    player2_unit_types = [
                        UnitType.GLAIVEMAN,
                        UnitType.MANDIBLE_FOREMAN,
                        UnitType.MARROW_CONDENSER
                    ]
                    
                    # For player 2, respect the 2-unit type limit
                    valid_types = [t for t in player2_unit_types 
                                if player_unit_counts.get(player, {}).get(t, 0) < 2]
                    
                    # Default to GLAIVEMAN if no valid types
                    if not valid_types:
                        unit_type = UnitType.GLAIVEMAN
                    else:
                        unit_type = valid_types[0]
                
                # Add the unit and update unit count
                self.add_unit(unit_type, player, y, x)
                
                # Update unit count for this player and type
                player_unit_counts.setdefault(player, {})
                player_unit_counts[player][unit_type] = player_unit_counts[player].get(unit_type, 0) + 1
                
                logger.info(f"Added {unit_type.name} for player {player} at ({y}, {x})")

        # If we couldn't find enough valid positions, add some emergency units
        # at fixed positions (shouldn't happen with our current map)
        if len(self.units) < 6:
            missing = 6 - len(self.units)
            logger.warning(f"Not enough valid positions found. Adding {missing} emergency units.")
            
            # Determine how many units we're missing for each player
            p1_units = sum(1 for unit in self.units if unit.player == 1)
            p2_units = sum(1 for unit in self.units if unit.player == 2)
            
            p1_missing = max(0, 3 - p1_units)
            p2_missing = max(0, 3 - p2_units)
            
            emergency_p1_positions = [(1, 1, 1), (1, 1, 2), (1, 1, 3)]
            emergency_p2_positions = [(2, 8, 16), (2, 8, 17), (2, 8, 18)]
            
            # Check if we're in VS_AI mode
            from boneglaive.utils.config import ConfigManager, NetworkMode
            config = ConfigManager()
            is_vs_ai_mode = config.get('network_mode') == NetworkMode.VS_AI.value
            
            # For VS_AI mode, ensure we create exactly one of each unit type for player 2
            if is_vs_ai_mode and p2_missing > 0:
                logger.warning("Adding emergency units for VS_AI mode, ensuring one of each unit type")
                
                # Make a list of available unit types
                vs_ai_types = [UnitType.GLAIVEMAN, UnitType.MANDIBLE_FOREMAN, UnitType.MARROW_CONDENSER]
                
                # See which types we already have
                for unit in self.units:
                    if unit.player == 2 and unit.type in vs_ai_types:
                        vs_ai_types.remove(unit.type)
                
                # Add the missing types
                for i in range(min(p2_missing, len(vs_ai_types))):
                    player, y, x = emergency_p2_positions[i]
                    unit_type = vs_ai_types[i]
                    
                    # Add the unit
                    self.add_unit(unit_type, player, y, x)
                    logger.warning(f"Added emergency VS_AI {unit_type.name} for player 2 at ({y}, {x})")
                    
                    # Update unit counts
                    player_unit_counts.setdefault(player, {})
                    player_unit_counts[player][unit_type] = player_unit_counts[player].get(unit_type, 0) + 1
            else:
                # Standard emergency unit placement for non-VS_AI mode
                # First handle missing player 2 units with rotating types
                for i in range(p2_missing):
                    player, y, x = emergency_p2_positions[i]
                    
                    # Determine which unit type to use next
                    valid_types = [UnitType.GLAIVEMAN, UnitType.MANDIBLE_FOREMAN, UnitType.MARROW_CONDENSER]
                    
                    # Filter by existing types if needed
                    if player_unit_counts.get(player, {}):
                        valid_types = [t for t in valid_types 
                                      if player_unit_counts.get(player, {}).get(t, 0) < 2]
                    
                    # Default to GLAIVEMAN if no valid types
                    if not valid_types:
                        unit_type = UnitType.GLAIVEMAN
                    else:
                        unit_type = valid_types[0]
                    
                    # Add the unit
                    self.add_unit(unit_type, player, y, x)
                    logger.warning(f"Added emergency {unit_type.name} for player 2 at ({y}, {x})")
                    
                    # Update unit counts
                    player_unit_counts.setdefault(player, {})
                    player_unit_counts[player][unit_type] = player_unit_counts[player].get(unit_type, 0) + 1
            
            # Now handle missing player 1 units with variety
            for i in range(p1_missing):
                player, y, x = emergency_p1_positions[i]
                
                # For player 1, respect the 2-unit type limit
                valid_types = [t for t in player1_unit_types
                            if player_unit_counts.get(player, {}).get(t, 0) < 2]
                
                # Default to GLAIVEMAN if no valid types
                if not valid_types:
                    unit_type = UnitType.GLAIVEMAN
                else:
                    unit_type = valid_types[0]
                
                # Add the unit
                self.add_unit(unit_type, player, y, x)
                logger.warning(f"Added emergency {unit_type.name} for player 1 at ({y}, {x})")
                
                # Update unit counts
                player_unit_counts.setdefault(player, {})
                player_unit_counts[player][unit_type] = player_unit_counts[player].get(unit_type, 0) + 1
        
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
        
    def count_player_units_by_type(self, player, unit_type):
        """
        Count how many units of a specific type a player has.

        Args:
            player: The player ID (1 or 2)
            unit_type: The UnitType to count

        Returns:
            int: Number of units of that type belonging to the player
        """
        count = 0
        for unit in self.units:
            if unit.player == player and unit.type == unit_type:
                count += 1
        return count

    def place_setup_unit(self, y, x, unit_type=UnitType.GLAIVEMAN):
        """
        Place a unit during the setup phase.

        Args:
            y, x: The position to place the unit
            unit_type: The type of unit to place (defaults to GLAIVEMAN)

        Returns:
            True if unit was placed, False if invalid or no units remaining
            Returns a string error message if limit exceeded
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

        # Check if player already has 2 units of this type
        unit_count = self.count_player_units_by_type(self.setup_player, unit_type)
        if unit_count >= 2:
            # Return a specific error message for unit type limit
            return "max_unit_type_limit"

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
        
        # Check if we're in single player mode
        is_single_player = not self.local_multiplayer
        
        # If player 1 is done, handle based on mode
        if self.setup_player == 1:
            if is_single_player:
                # In single player, auto-confirm player 2 and start the game
                self.setup_confirmed[2] = True
                # Skip player 2 setup
                self.setup_units_remaining[2] = 0
                # Place default units for player 2
                self._place_default_units_for_player(2)
                # End setup phase
                self.setup_phase = False
                # Assign Greek identification letters to units
                self._assign_greek_identifiers()
                # Add welcome message now that game is starting
                message_log.add_system_message(f"Entering {self.map.name}")
                # Skip to game start
                return True
            else:
                # In multiplayer, switch to player 2 for manual setup
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
        Line of sight is blocked by:
        - Solid terrain like pillars and limestone
        - Units in the line of sight
        
        Note: Saft-E-Gas no longer blocks line of sight but instead prevents targeting
        units inside its cloud (handled in can_attack)
        
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
    
    def is_protected_from(self, target_unit, attacker_unit):
        """
        Check if a target unit is protected from an attacker by Saft-E-Gas.
        
        Args:
            target_unit: The unit being targeted
            attacker_unit: The unit trying to target
            
        Returns:
            bool: True if target is protected, False if not
        """
        
        # Check if target is protected by any Saft-E-Gas cloud
        if hasattr(target_unit, 'protected_by_safety_gas') and target_unit.protected_by_safety_gas:
            # Target is protected by at least one Saft-E-Gas cloud
            # Check if attacker is inside ANY of the protecting clouds
            attacker_in_protecting_cloud = False
            
            # Clean up any dead vapors from the protection list
            active_vapors = []
            for vapor in target_unit.protected_by_safety_gas[:]:  # Create a copy of the list to avoid modification issues
                # First verify vapor exists and is actually in the game's units list
                if vapor not in self.units:
                    logger.debug(f"Vapor not found in game units - removing from protection list")
                    continue
                    
                if vapor.is_alive():  # Only keep active vapors
                    # Double check that the vapor is still a SAFETY type (in case it was changed)
                    if hasattr(vapor, 'vapor_type') and vapor.vapor_type == "SAFETY":
                        active_vapors.append(vapor)
                    else:
                        logger.debug(f"Vapor type has changed - removing from protection list")
                else:
                    logger.debug(f"Dead vapor - removing from protection list")
            
            # Update the protection list with only live vapors
            target_unit.protected_by_safety_gas = active_vapors
            
            # If all protecting vapors are gone, remove the protection
            if not active_vapors:
                logger.debug(f"{target_unit.get_display_name()} is no longer protected (all protecting vapors are gone)")
                delattr(target_unit, 'protected_by_safety_gas')
                return False
            
            # Now check if any of the active vapors actually protect against this attacker
            # For each protecting cloud, check if attacker is also in it
            for vapor in active_vapors:
                # Calculate distance from attacker to this vapor
                attacker_distance = self.chess_distance(vapor.y, vapor.x, attacker_unit.y, attacker_unit.x)
                if attacker_distance <= 1:  # Attacker is inside this protecting cloud
                    attacker_in_protecting_cloud = True
                    logger.debug(f"Attacker {attacker_unit.get_display_name()} is inside a protecting cloud")
                    break
            
            # If attacker isn't in any of the protecting clouds, target is protected
            is_protected = not attacker_in_protecting_cloud
            if is_protected:
                logger.debug(f"{target_unit.get_display_name()} is protected from {attacker_unit.get_display_name()}")
            return is_protected
            
        # Target is not protected by any cloud
        return False
    
    def can_attack(self, unit, y, x):
        # First check for unit targets
        target = self.get_unit_at(y, x)
        
        # Calculate attack distance regardless of target type
        distance = self.chess_distance(unit.y, unit.x, y, x)
        effective_stats = unit.get_effective_stats()
        effective_attack_range = effective_stats['attack_range']
        
        # Basic range check for all target types
        if distance > effective_attack_range:
            return False
            
        # Line of sight check for all units
        # Check if there is a clear line of sight to the target
        los_check = self.has_line_of_sight(unit.y, unit.x, y, x)
        if not los_check:
            from boneglaive.utils.debug import logger
            logger.debug(f"{unit.get_display_name()} cannot attack target at ({y}, {x}) due to blocked line of sight")
            return False
                
        # Protection Zone Mechanic: Units inside Saft-E-Gas clouds cannot be targeted by enemy units outside
        # This protection is ALWAYS active, not tied to any "tick" effect
        if target and target.player != unit.player:  # Only applies for enemy targets
            # Use the is_protected_from method to check protection
            if self.is_protected_from(target, unit):
                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"Cannot target {target.get_display_name()} - protected by safety gas!",
                    MessageType.ABILITY
                )
                return False
                
        # Check if it's a valid unit target
        if target and target.player != unit.player:
            return True
            
        # If no valid unit target, check for Marrow Dike wall tiles
        if hasattr(self, 'marrow_dike_tiles') and (y, x) in self.marrow_dike_tiles:
            # Verify this is a wall tile that belongs to the enemy player
            wall_info = self.marrow_dike_tiles[(y, x)]
            if wall_info['owner'].player != unit.player:
                return True
                
        # No valid target (unit or wall)
        return False
    
    def get_possible_moves(self, unit):
        """
        Get all valid moves for a unit, checking for blocked paths.
        
        Returns:
            List of (y, x) tuples representing valid move positions.
        """
        # If unit is immobilized by Jawline effect, return empty list
        if hasattr(unit, 'jawline_affected') and unit.jawline_affected:
            return []
            
        # If unit is trapped, return empty list
        if unit.trapped_by is not None:
            return []
            
        # If unit is an echo, return empty list (echoes can't move)
        if unit.is_echo:
            return []
        
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
                # Calculate chess distance (allows diagonals) from the attack position
                distance = self.chess_distance(y_pos, x_pos, y, x)
                if distance > effective_attack_range:
                    continue  # Skip if out of range
                    
                # Check line of sight for GRAYMAN units
                los_check = True
                if unit.type == UnitType.GRAYMAN:
                    los_check = self.has_line_of_sight(y_pos, x_pos, y, x)
                    if not los_check:
                        continue  # Skip if no line of sight
                
                # Check if there's an enemy unit at this position
                target = self.get_unit_at(y, x)
                if target and target.player != unit.player:
                    # Check if target is protected by any Saft-E-Gas
                    if hasattr(target, 'protected_by_safety_gas') and target.protected_by_safety_gas:
                        # Target is under protection - check if attacker would be in the same cloud
                        attacker_in_protecting_cloud = False
                        
                        # Check each protecting vapor
                        for vapor in target.protected_by_safety_gas:
                            if vapor.is_alive():  # Only check active vapors
                                # Calculate distance from the attack position to this vapor
                                attacker_distance = self.chess_distance(vapor.y, vapor.x, y_pos, x_pos)
                                if attacker_distance <= 1:  # Attacker would be in this cloud
                                    attacker_in_protecting_cloud = True
                                    break
                        
                        # Only add as valid target if attacker would be in a protecting cloud
                        if attacker_in_protecting_cloud:
                            attacks.append((y, x))
                    else:
                        # Target is not protected - add as valid target
                        attacks.append((y, x))
                    
                    continue  # Skip wall check
                
                # Check for Marrow Dike wall tiles that can be attacked
                if hasattr(self, 'marrow_dike_tiles') and (y, x) in self.marrow_dike_tiles:
                    # Verify this is a wall tile that belongs to the enemy player
                    wall_info = self.marrow_dike_tiles[(y, x)]
                    if wall_info['owner'].player != unit.player:
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
        This is a centralized method to handle the "retching" state for all units.
        
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
            # Unit just crossed into critical health - display the retch message
            message_log.add_message(
                f"{unit.get_display_name()} retches!",
                MessageType.COMBAT,
                player=attacker.player if attacker else None,
                target=unit.player,
                target_name=unit.get_display_name()
            )
            
            # Add visual retch animation if UI is available
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Get retch animation from asset manager
                retch_animation = ui.asset_manager.get_skill_animation_sequence('wretch')
                if not retch_animation:
                    # Fallback animation if not defined
                    retch_animation = ['!', '?', '#', '@', '&', '%', '$']
                
                # Flash unit with yellow/red to indicate critical status
                ui.renderer.animate_attack_sequence(
                    unit.y, unit.x,
                    retch_animation,
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
        
        # Process MARROW CONDENSER kill counter ONLY
        # This is just for tracking the kill count used in Bone Tithe damage calculation
        # No stat bonuses are granted for kills outside the Marrow Dike
        if killer_unit and killer_unit.type == UnitType.MARROW_CONDENSER and hasattr(killer_unit, 'passive_skill'):
            passive = killer_unit.passive_skill
            
            # Check if it's Dominion passive
            if passive.name == "Dominion":
                # Increment kill counter (used for bone tithe damage calculation)
                # But do NOT grant any bonuses for kills outside the Marrow Dike
                passive.kills += 1
        
        # Process skill upgrades and stat bonuses if died in a Marrow Dike
        # This is the only place where skill upgrades are granted
        if in_marrow_dike and dike_owner:
            # Verify the owner is a MARROW_CONDENSER
            if dike_owner.type == UnitType.MARROW_CONDENSER and hasattr(dike_owner, 'passive_skill'):
                passive = dike_owner.passive_skill
                
                # Apply the stat bonus based on upgrade tier
                # Instead of granting all bonuses at once, apply them progressively based on upgrade level
                if not passive.marrow_dike_upgraded and not passive.ossify_upgraded and not passive.bone_tithe_upgraded:
                    # First upgrade: +1 defense
                    dike_owner.defense_bonus += 1
                elif passive.marrow_dike_upgraded and not passive.ossify_upgraded and not passive.bone_tithe_upgraded:
                    # Second upgrade: +1 attack
                    dike_owner.attack_bonus += 1
                elif passive.marrow_dike_upgraded and passive.ossify_upgraded and not passive.bone_tithe_upgraded:
                    # Third upgrade: +1 movement
                    dike_owner.move_range_bonus += 1
                
                # Check if it's Dominion and can upgrade skills
                if passive.name == "Dominion" and passive.can_upgrade():
                    upgraded_skill = passive.get_next_upgrade()
                    
                    if upgraded_skill:
                        # Create a more distinctive message for the upgrade
                        upgrade_message = f"DOMINION: {dike_owner.get_display_name()} absorbs power from the fallen!"
                        
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
            logger.info(f"MANDIBLE_FOREMAN {dying_unit.get_display_name()} has perished, checking for trapped units to release")
            # Critical: Make a list of trapped units first before modifying them
            # Check by unit ID rather than direct object comparison which can fail when objects are replaced
            dying_unit_id = id(dying_unit)
            trapped_units = []
            for unit in self.units:
                if unit.is_alive() and hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
                    # Check if this unit is trapped by the dying foreman
                    # Use object identity (id) for more reliable reference checking
                    if id(unit.trapped_by) == dying_unit_id:
                        trapped_units.append(unit)
                    
            for unit in trapped_units:
                logger.info(f"MANDIBLE_FOREMAN perished, releasing {unit.get_display_name()}")
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
    
    def process_buff_durations(self):
        """
        Backward compatibility method - redirects to process_status_effects.
        """
        return self.process_status_effects()
        
    def process_status_effects(self):
        """
        Process status effect durations for all units of the current player.
        Decrements durations and removes expired status effects.
        Also applies movement penalties for units inside reinforced Marrow Dikes.
        Also handles Market Futures investment maturation.
        Also regenerates 1 HP for units that took no actions during their turn.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Process ALL units for effects that apply to any unit inside a reinforced Marrow Dike
        # This affects both current player's units and enemy units
        for unit in self.units:
            if not unit.is_alive():
                continue
                
            # Check if unit is inside an upgraded Marrow Dike
            if hasattr(self, 'marrow_dike_interior'):
                unit_pos = (unit.y, unit.x)
                if unit_pos in self.marrow_dike_interior:
                    dike_info = self.marrow_dike_interior[unit_pos]
                    dike_owner = dike_info.get('owner')
                    
                    # Only apply movement penalty if:
                    # 1. The dike is upgraded
                    # 2. The unit is an enemy of the dike owner
                    # 3. The dike owner is MARROW CONDENSER
                    # 4. The unit is not immune to effects (due to Stasiality)
                    if (dike_info.get('upgraded', False) and 
                        dike_owner and dike_owner.is_alive() and 
                        dike_owner.type == UnitType.MARROW_CONDENSER and 
                        dike_owner.player != unit.player and
                        not unit.is_immune_to_effects()):  # GRAYMAN with Stasiality is immune
                        
                        # Apply movement penalty if not already applied
                        if not hasattr(unit, 'prison_move_penalty') or not unit.prison_move_penalty:
                            unit.move_range_bonus -= 1
                            unit.prison_move_penalty = True
                            
                            # Shorter log message
                            message_log.add_message(
                                f"{unit.get_display_name()} slogs through the Marrow Dike!",
                                MessageType.ABILITY,
                                player=dike_owner.player,
                                attacker_name=dike_owner.get_display_name(),
                                target_name=unit.get_display_name()
                            )
                    # If unit is immune to effects, show a message about immunity 
                    elif (dike_info.get('upgraded', False) and 
                          dike_owner and dike_owner.is_alive() and 
                          dike_owner.type == UnitType.MARROW_CONDENSER and 
                          dike_owner.player != unit.player and
                          unit.is_immune_to_effects()):
                        # Only show the message once when first entering the dike
                        if not hasattr(unit, 'marrow_dike_immunity_message_shown'):
                            message_log.add_message(
                                f"{unit.get_display_name()} ignores the Marrow Dike's effect due to Stasiality!",
                                MessageType.ABILITY,
                                player=unit.player,
                                target_name=unit.get_display_name()
                            )
                            unit.marrow_dike_immunity_message_shown = True
                # If unit is not in a dike but had the penalty, remove it
                elif hasattr(unit, 'prison_move_penalty') and unit.prison_move_penalty:
                    unit.move_range_bonus += 1
                    unit.prison_move_penalty = False
        
        # Now process turn-based effects for current player's units only
        for unit in self.units:
            if not unit.is_alive() or unit.player != self.current_player:
                continue
                
            # Skip Marrow Dike movement penalty check (already handled above)
            # Process other status effects
                
            # Process Pry movement penalty effect
            if hasattr(unit, 'pry_duration') and unit.pry_duration > 0:
                logger.debug(f"Processing Pry effect for {unit.get_display_name()}, duration: {unit.pry_duration}")
                
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
            
            # Process Ossify status effect for MARROW CONDENSER
            if hasattr(unit, 'ossify_active') and unit.ossify_active:
                # Only process if not upgraded (upgraded version is permanent)
                if hasattr(unit, 'ossify_duration'):
                    # Decrement the duration
                    unit.ossify_duration -= 1
                    logger.debug(f"{unit.get_display_name()}'s Ossify duration: {unit.ossify_duration}")
                    
                    # Check if the status effect has expired
                    if unit.ossify_duration <= 0:
                        # Remove the status effect
                        unit.ossify_active = False
                        # Remove the defense bonus and movement penalty
                        if unit.type == UnitType.MARROW_CONDENSER:
                            # Get the defense bonus value from the skill
                            for skill in unit.active_skills:
                                if skill.name == "Ossify":
                                    unit.defense_bonus -= skill.defense_bonus
                                    break
                            
                            # Reset movement penalty
                            unit.move_range_bonus = 0
                        
                        # Log the expiration
                        message_log.add_message(
                            f"{unit.get_display_name()}'s bones return to normal state.",
                            MessageType.ABILITY,
                            player=unit.player
                        )
            
            # Bone Tithe no longer applies defensive buffs to allies
            
            # Auction Curse DOT effect now processed at the end of turn
            
            # Auction Curse no longer applies stat bonuses to allies via bid tokens
                    
            # Process Market Futures investment maturation
            if hasattr(unit, 'market_futures_bonus_applied') and unit.market_futures_bonus_applied:
                if hasattr(unit, 'market_futures_duration') and unit.market_futures_duration > 0:
                    # Market Futures works uniquely:
                    # - Turn 1: +1 ATK, +1 Range (applied immediately)
                    # - Turn 2: +2 ATK, +1 Range (matures right before attack)
                    # - Turn 3: +3 ATK, +1 Range (matures right before attack, then expires)
                    
                    # We need to handle both expiration and maturation here carefully
                    
                    # First, handle maturation flag setup
                    # We'll check this flag during attack execution
                    if hasattr(unit, 'market_futures_maturity'):
                        # For turn 3 (duration = 1), we want it to mature BEFORE expiring
                        # For turn 2 (duration = 2), we want normal maturation
                        if unit.market_futures_duration == 2 or unit.market_futures_duration == 1:
                            # Mark that maturation should happen this turn but hasn't yet
                            unit.market_futures_needs_maturation = True
                            
                            # For the final turn, mark that it's the last maturation before expiry
                            if unit.market_futures_duration == 1:
                                unit.market_futures_final_maturation = True
                    
                    # Always ensure range bonus is maintained throughout effect duration
                    if unit.market_futures_duration >= 1:
                        # Only add range bonus if it hasn't been added already
                        if not hasattr(unit, 'market_futures_range_bonus_active'):
                            unit.market_futures_range_bonus_active = True
                        
                        # Ensure attack range bonus is at least 1
                        if unit.attack_range_bonus < 1:
                            unit.attack_range_bonus = 1
                    
                    # Decrement the duration AFTER handling setup
                    unit.market_futures_duration -= 1
                    logger.debug(f"{unit.get_display_name()}'s Market Futures duration decremented to: {unit.market_futures_duration}")
                    
                    # For expiration, we skip it if it's the final maturation turn
                    # Instead, we'll handle expiration during attack processing
                    if unit.market_futures_duration == 0 and not hasattr(unit, 'market_futures_final_maturation'):
                        # Remove the attack bonus based on current maturity level
                        if hasattr(unit, 'market_futures_maturity'):
                            unit.attack_bonus -= unit.market_futures_maturity
                        
                        # Remove range bonus at expiration
                        unit.attack_range_bonus -= 1
                        
                        # Reset all flags
                        unit.market_futures_bonus_applied = False
                        if hasattr(unit, 'has_investment_effect'):
                            unit.has_investment_effect = False
                        if hasattr(unit, 'market_futures_range_bonus_active'):
                            unit.market_futures_range_bonus_active = False
                        
                        # Log the expiration
                        message_log.add_message(
                            f"{unit.get_display_name()}'s investment effect expires after 3 turns.",
                            MessageType.ABILITY,
                            player=unit.player
                        )

            # Process Jawline status effect
            if hasattr(unit, 'jawline_affected') and unit.jawline_affected:
                # Decrement the duration
                unit.jawline_duration -= 1
                logger.debug(f"{unit.get_display_name()}'s Jawline tether duration: {unit.jawline_duration}")
                
                # Check if the status effect has expired
                if unit.jawline_duration <= 0:
                    # Remove the status effect
                    unit.jawline_affected = False
                    
                    # Reset movement to original value
                    if hasattr(unit, 'jawline_original_move'):
                        # Restore movement by removing the negative bonus that was applied
                        # Reset the bonus without manually setting move_range since we stored the original
                        unit.move_range_bonus = 0
                        
                        # Clean up the stored value
                        delattr(unit, 'jawline_original_move')
                    
                    # Log the expiration
                    message_log.add_message(
                        f"{unit.get_display_name()} breaks free and can move again!",
                        MessageType.ABILITY,
                        player=unit.player
                    )
            
            # Process health regeneration for units that took no actions
            if (hasattr(unit, 'took_no_actions') and unit.took_no_actions and 
                unit.hp < unit.max_hp):
                
                # Check if any enemy units are adjacent to this unit
                has_adjacent_enemy = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        # Skip the center position (the unit itself)
                        if dy == 0 and dx == 0:
                            continue
                            
                        # Check adjacent position
                        adjacent_y, adjacent_x = unit.y + dy, unit.x + dx
                        if self.is_valid_position(adjacent_y, adjacent_x):
                            adjacent_unit = self.get_unit_at(adjacent_y, adjacent_x)
                            if adjacent_unit and adjacent_unit.is_alive() and adjacent_unit.player != unit.player:
                                has_adjacent_enemy = True
                                break
                    if has_adjacent_enemy:
                        break
                
                # Only regenerate if no adjacent enemies
                if not has_adjacent_enemy:
                    # Regenerate 1 HP
                    unit.hp += 1
                    logger.debug(f"{unit.get_display_name()} regenerated 1 HP from resting")
                    
                    # Log the regeneration using proper format for healing messages
                    # "healing for X HP" format ensures the number appears in white
                    message_log.add_message(
                        f"{unit.get_display_name()} healing for 1 HP from resting.",
                        MessageType.ABILITY,  # Using ABILITY type for player coloring
                        player=unit.player
                    )
                else:
                    # Log that unit couldn't rest due to enemies nearby
                    logger.debug(f"{unit.get_display_name()} couldn't rest due to nearby enemies")
                
                # Reset the flag for the next turn
                unit.took_no_actions = False
    
    @measure_perf
    def execute_turn(self, ui=None):
        """Execute all unit actions for the current turn with animated sequence."""
        import time
        import curses
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Store UI reference for animations if provided
        if ui:
            self.ui = ui
            
        # Initialize marrow_dike_tiles attribute if not present
        if not hasattr(self, 'marrow_dike_tiles'):
            self.marrow_dike_tiles = {}
            
        logger.info(f"Executing turn {self.turn} for player {self.current_player}")
        
        # Process status effects for the current player's units
        self.process_buff_durations()
        
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
            
            # Add units with Auction Curse DOT effect (these are processed during attack resolution)
            # Important: DOT should only tick on the opponent's turn (when the caster's turn is active)
            elif (hasattr(unit, 'auction_curse_dot') and unit.auction_curse_dot and 
                  unit.auction_curse_dot_duration > 0 and unit.player != self.current_player):
                # Set a special flag to identify this as a DOT action
                unit.auction_curse_dot_action = True
                units_with_actions.append(unit)
        
        # Sort units by action timestamp (lower numbers = earlier actions)
        # If timestamps are equal, sort by random order to avoid MARROW_CONDENSER always going first
        import random
        units_with_actions.sort(key=lambda unit: (unit.action_timestamp, random.random()))
        
        logger.info(f"Executing {len(units_with_actions)} actions in timestamp order")
        
        # Display actions visually with UI but don't add to message log
        if (units_with_actions or any(unit.trapped_by is not None for unit in self.units)) and ui:
            # Start the spinner animation
            ui.start_spinner()
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            time.sleep(0.3)  # Short delay before actions start
        
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
                    # Mark that this unit took an action (won't regenerate HP)
                    unit.took_no_actions = False
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
                
                # Mark that this unit took an action (won't regenerate HP)
                unit.took_no_actions = False
                
                # Calculate attacking position (either unit's current position or move target)
                attacking_pos = (unit.y, unit.x)  # Unit's position is already updated if it moved
                
                # Verify attack is within range from the attacking position
                attack_distance = self.chess_distance(attacking_pos[0], attacking_pos[1], y, x)
                
                # Get the unit's effective attack range from their stats
                effective_stats = unit.get_effective_stats()
                effective_attack_range = effective_stats['attack_range']
                
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
                
                # Revalidate protection status - might have changed since attack was queued
                if target and target.player != unit.player and self.is_protected_from(target, unit):
                    logger.debug(f"Attack cancelled: {target.get_display_name()} is protected by Saft-E-Gas")
                    message_log.add_message(
                        f"{unit.get_display_name()}'s attack fails - target is protected by safety gas!",
                        MessageType.COMBAT,
                        player=unit.player
                    )
                    continue  # Skip this attack and go to next unit
                
                # Check for Marrow Dike wall tiles that can be targeted
                wall_target = None
                if not target and (y, x) in self.marrow_dike_tiles:
                    # Verify this is a wall tile that belongs to the enemy player
                    wall_info = self.marrow_dike_tiles[(y, x)]
                    if wall_info['owner'].player != unit.player and attack_distance <= effective_attack_range and los_check:
                        wall_target = (y, x)  # Mark this as a valid wall target

                # Check if attack is valid (checks all conditions including protection)
                valid_attack = (target and 
                               target.player != unit.player and 
                               attack_distance <= effective_attack_range and 
                               los_check and 
                               not self.is_protected_from(target, unit))
                               
                if valid_attack or wall_target:  # Valid attack on unit or wall
                    # Handle damage calculation first
                    if wall_target:
                        # Get the wall information
                        wall_y, wall_x = wall_target
                        wall_info = self.marrow_dike_tiles[wall_target]
                        
                        # Walls always take exactly 1 damage from any attack
                        damage = 1
                        
                        # Apply damage to the wall
                        wall_info['hp'] = max(0, wall_info['hp'] - damage)
                        
                        # Log the attack on the wall
                        message_log.add_message(
                            f"{unit.get_display_name()} attacks a Marrow Dike wall!",
                            MessageType.COMBAT,
                            player=unit.player
                        )
                        
                        # Show attack animation with damage after calculation
                        if ui:
                            self._show_wall_attack_animation(ui, unit, wall_target, damage)
                        
                        # Handle wall destruction
                        if wall_info['hp'] <= 0:
                            # Restore original terrain
                            original_terrain = wall_info.get('original_terrain', TerrainType.EMPTY)
                            self.map.set_terrain_at(wall_y, wall_x, original_terrain)
                            
                            # Remove from tracking
                            owner = wall_info['owner']
                            del self.marrow_dike_tiles[wall_target]
                            
                            # Log the destruction
                            message_log.add_message(
                                f"{unit.get_display_name()} breaks through a section of {owner.get_display_name()}'s Marrow Dike!",
                                MessageType.COMBAT,
                                player=unit.player
                            )
                    else:
                        # Normal unit-vs-unit combat
                        
                        # Check for Market Futures maturation - do this RIGHT before the attack
                        # This ensures the maturation message appears before the attack message
                        if hasattr(unit, 'market_futures_needs_maturation') and unit.market_futures_needs_maturation:
                            # Apply Market Futures maturation right before attack
                            old_maturity = unit.market_futures_maturity
                            unit.market_futures_maturity += 1
                            
                            # Update the attack bonus (remove old bonus and add new one)
                            unit.attack_bonus = unit.attack_bonus - old_maturity + unit.market_futures_maturity
                            
                            # Log the investment maturation before attack
                            message_log.add_message(
                                f"{unit.get_display_name()}'s investment matures to +{unit.market_futures_maturity} ATK!",
                                MessageType.ABILITY,
                                player=unit.player
                            )
                            
                            # Clear the flag
                            unit.market_futures_needs_maturation = False
                            
                            # Check if this is the final maturation before expiry
                            if hasattr(unit, 'market_futures_final_maturation'):
                                # Show expiration message AFTER maturation
                                message_log.add_message(
                                    f"{unit.get_display_name()}'s investment effect expires after 3 turns.",
                                    MessageType.ABILITY,
                                    player=unit.player
                                )
                                
                                # Remove the attack bonus after this attack
                                unit.market_futures_will_expire_after_attack = True
                                
                                # Clear the flag
                                delattr(unit, 'market_futures_final_maturation')
                            
                        # Show attack animation
                        if ui:
                            ui.show_attack_animation(unit, target)
                        
                        # Calculate damage using effective stats (including bonuses)
                        # Defense acts as flat damage reduction
                        effective_stats = unit.get_effective_stats()
                        effective_attack = effective_stats['attack']
                        effective_defense = target.get_effective_stats()['defense']
                        
                        # GRAYMAN's attacks bypass defense (both original and echo)
                        if unit.type == UnitType.GRAYMAN or (hasattr(unit, 'is_echo') and unit.is_echo and unit.type == UnitType.GRAYMAN):
                            damage = effective_attack  # Bypass defense completely
                            
                            from boneglaive.utils.message_log import message_log, MessageType
                            # Different messages for original GRAYMAN vs echo
                            if hasattr(unit, 'is_echo') and unit.is_echo:
                                message_log.add_message(
                                    f"The echo's psychic attack bypasses {target.get_display_name()}'s defenses!",
                                    MessageType.ABILITY,
                                    player=unit.player,
                                    target_name=target.get_display_name()
                                )
                            else:
                                message_log.add_message(
                                    f"{unit.get_display_name()}'s psychic attack bypasses {target.get_display_name()}'s defenses!",
                                    MessageType.ABILITY,
                                    player=unit.player,
                                    target_name=target.get_display_name()
                                )
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
                                f"{target.get_display_name()} is immune to Viseroy due to Stasiality!",
                                MessageType.ABILITY,
                                player=target.player,  # Use target's player color
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
                    
                    # Additional XP for killing the target (only applicable when target is a unit, not a wall)
                    if target and target.hp <= 0:
                        xp_gained += XP_KILL_REWARD
                    
                    # Add XP and check if unit leveled up
                    if unit.add_xp(xp_gained):
                        # Unit leveled up - add a message
                        message_log.add_message(
                            f"{unit.get_display_name()} gained experience and reached level {unit.level}!",
                            MessageType.SYSTEM,
                            player=unit.player
                        )
                    
                    # Only log combat messages and handle unit death for unit targets (not walls)
                    if target:
                        # Log combat message
                        message_log.add_combat_message(
                            attacker_name=unit.get_display_name(),
                            target_name=target.get_display_name(),
                            damage=damage,
                            attacker_player=unit.player,
                            target_player=target.player
                        )
                        
                        # Handle removal of Market Futures effect after attack if it's expiring
                        if hasattr(unit, 'market_futures_will_expire_after_attack') and unit.market_futures_will_expire_after_attack:
                            # Remove the attack bonus based on current maturity level
                            if hasattr(unit, 'market_futures_maturity'):
                                unit.attack_bonus -= unit.market_futures_maturity
                            
                            # Remove range bonus
                            unit.attack_range_bonus -= 1
                            
                            # Reset all flags
                            unit.market_futures_bonus_applied = False
                            unit.market_futures_will_expire_after_attack = False
                            if hasattr(unit, 'has_investment_effect'):
                                unit.has_investment_effect = False
                            if hasattr(unit, 'market_futures_range_bonus_active'):
                                unit.market_futures_range_bonus_active = False
                        
                        # No need to format with player info anymore - just use the unit's display name
                        # Check if target was defeated
                        if target.hp <= 0:
                            # Use centralized death handling
                            self.handle_unit_death(target, unit, cause="combat", ui=ui)
                        else:
                            # Check for critical health (retching) using centralized logic
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
                
                # Add a slight pause between actions for a unit and update spinner
                if ui:
                    ui.advance_spinner()
                    time.sleep(0.15)
            
            # EXECUTE SKILL if unit has a skill target
            if unit.skill_target and unit.selected_skill:
                # Mark that this unit took an action (won't regenerate HP)
                unit.took_no_actions = False
                
                # Execute the skill
                skill = unit.selected_skill
                target_pos = unit.skill_target
                
                # Revalidate skill target for protection - might have changed since skill was queued
                from boneglaive.game.skills import TargetType
                if hasattr(skill, 'target_type') and skill.target_type == TargetType.ENEMY:
                    target_unit = self.get_unit_at(target_pos[0], target_pos[1])
                    if target_unit and target_unit.player != unit.player and self.is_protected_from(target_unit, unit):
                        logger.debug(f"Skill cancelled: {target_unit.get_display_name()} is protected by Saft-E-Gas")
                        message_log.add_message(
                            f"{unit.get_display_name()}'s skill fails - target is protected by safety gas!",
                            MessageType.ABILITY,
                            player=unit.player
                        )
                        continue  # Skip this skill and go to next unit
                
                # Execute the skill if it has an execute method
                if hasattr(skill, 'execute'):
                    skill.execute(unit, target_pos, self, ui)
                else:
                    logger.warning(f"Skill {skill.name} has no execute method")
                
                # Add a slight pause after the skill and update spinner
                if ui:
                    ui.advance_spinner()
                    time.sleep(0.15)
            
            # EXECUTE VISEROY TRAP DAMAGE if this is a MANDIBLE_FOREMAN with trapped units
            elif hasattr(unit, 'auction_curse_dot_action') and unit.auction_curse_dot_action:
                # This is a special action but still counts as an action for health regeneration
                unit.took_no_actions = False
                # Process Auction Curse DOT effect
                from boneglaive.utils.message_log import message_log, MessageType
                
                # Show DOT animation if UI is available
                if ui and hasattr(ui, 'renderer'):
                    # Create curse damage animation
                    curse_animation = ['¢', '$', '%', '*', '!']
                    
                    # Show animation at the affected unit's position
                    ui.renderer.animate_attack_sequence(
                        unit.y, unit.x,
                        curse_animation,
                        6,  # Red color for damage
                        0.15  # Duration
                    )
                
                # Apply the damage
                damage = 1
                unit.hp = max(0, unit.hp - damage)
                
                # Get the opposing player (caster of the Auction Curse)
                caster_player = 3 - unit.player  # If unit.player is 1, this gives 2; if 2, gives 1
                
                # Find a DELPHIC_APPRAISER unit from the caster's player to attribute the damage to
                appraiser_unit = None
                for u in self.units:
                    if u.is_alive() and u.player == caster_player and u.type == UnitType.DELPHIC_APPRAISER:
                        appraiser_unit = u
                        break
                
                # Use the found DELPHIC_APPRAISER or a generic name if none found
                attacker_name = appraiser_unit.get_display_name() if appraiser_unit else f"DELPHIC APPRAISER Player {caster_player}"
                
                # Log the damage using standard combat message format - this ensures proper color formatting
                message_log.add_combat_message(
                    attacker_name=attacker_name,
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability="Auction Curse",
                    attacker_player=caster_player,
                    target_player=unit.player
                )
                
                # Decrement the duration
                unit.auction_curse_dot_duration -= 1
                logger.debug(f"{unit.get_display_name()}'s Auction Curse DOT duration: {unit.auction_curse_dot_duration}")
                
                # Check if unit died from the DOT
                if unit.hp <= 0:
                    # Use consistent format for death messages
                    message_log.add_message(
                        f"{unit.get_display_name()} perishes!",
                        MessageType.COMBAT,
                        player=unit.player
                    )
                
                # Check if the DOT effect has expired
                if unit.auction_curse_dot_duration <= 0:
                    # Remove the DOT effect
                    unit.auction_curse_dot = False
                    
                    # Log the expiration - use attacker_name for consistent display
                    message_log.add_message(
                        f"Auction Curse fades from {unit.get_display_name()}.",
                        MessageType.ABILITY,
                        player=caster_player,
                        attacker_name=attacker_name,
                        target_name=unit.get_display_name()
                    )
                
                # Clear the DOT action flag
                unit.auction_curse_dot_action = False
                
            elif hasattr(unit, 'viseroy_trap_action') and unit.viseroy_trap_action:
                # This is a special action but still counts as an action for health regeneration
                unit.took_no_actions = False
                
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
            
            # Add a slight pause between units' actions and update spinner
            if ui:
                ui.advance_spinner()
                time.sleep(0.2)
        
        # Apply trap damage for all trapped units
        self._apply_trap_damage()
        
        # Process HEINOUS_VAPOR effects for current player's vapors only
        vapor_units = [unit for unit in self.units if unit.is_alive() and 
                      unit.type == UnitType.HEINOUS_VAPOR and 
                      hasattr(unit, 'vapor_type') and unit.vapor_type and
                      unit.player == self.current_player]  # Only include current player's vapors
        
        # Process each vapor's area effects
        for vapor_unit in vapor_units:
            # Apply the vapor's area effects only on owner's turn
            vapor_unit.apply_vapor_effects(self, ui)
            
            # Decrement vapor duration for current player's vapors
            if hasattr(vapor_unit, 'vapor_duration'):
                vapor_unit.vapor_duration -= 1
                logger.debug(f"Vapor {vapor_unit.get_display_name()} duration decremented to {vapor_unit.vapor_duration}")
                
                # If duration reached zero, the vapor expires
                if vapor_unit.vapor_duration <= 0:
                    logger.debug(f"Vapor {vapor_unit.get_display_name()} expires")
                    
                    # Clear protection from units if this is a SAFETY type vapor
                    if hasattr(vapor_unit, 'vapor_type') and vapor_unit.vapor_type == "SAFETY":
                        # Find all units that were being protected by this vapor
                        for protected_unit in self.units:
                            if (hasattr(protected_unit, 'protected_by_safety_gas') and 
                                protected_unit.protected_by_safety_gas):  # Check if it's a non-empty list
                                # Make a copy of the list to avoid modification issues
                                protection_list = protected_unit.protected_by_safety_gas.copy()
                                
                                # Clean up dead or removed vapors
                                for vapor in protection_list:
                                    if vapor not in self.units or not vapor.is_alive() or vapor == vapor_unit:
                                        if vapor in protected_unit.protected_by_safety_gas:
                                            protected_unit.protected_by_safety_gas.remove(vapor)
                                            logger.debug(f"{protected_unit.get_display_name()} is no longer protected by expired or removed vapor")
                                
                                # If there are no more protecting vapors, clean up the attribute
                                if not protected_unit.protected_by_safety_gas:
                                    logger.debug(f"{protected_unit.get_display_name()} is no longer protected by any safety gas")
                                    delattr(protected_unit, 'protected_by_safety_gas')
                    
                    # Log the expiration
                    message_log.add_message(
                        f"{vapor_unit.get_display_name()} dissipates...",
                        MessageType.ABILITY,
                        player=vapor_unit.player
                    )
                    
                    # Check if this vapor was from a diverged user
                    if hasattr(vapor_unit, 'diverged_user') and vapor_unit.diverged_user:
                        # Check if this is the last vapor to expire
                        other_vapors = [u for u in self.units if u != vapor_unit and 
                                      u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and 
                                      hasattr(u, 'diverged_user') and u.diverged_user == vapor_unit.diverged_user]
                        
                        # If no other vapors from this user, the user reforms
                        if not other_vapors:
                            gas_machinist = vapor_unit.diverged_user
                            
                            # Return the Gas Machinist to the vapor's position
                            gas_machinist.y = vapor_unit.y
                            gas_machinist.x = vapor_unit.x
                            
                            # Reset the diverge flags
                            gas_machinist.diverge_return_position = False
                            
                            # Log the return
                            message_log.add_message(
                                f"{gas_machinist.get_display_name()} reforms at ({vapor_unit.y}, {vapor_unit.x})!",
                                MessageType.ABILITY,
                                player=gas_machinist.player
                            )
                            
                            # Play reformation animation if UI is available
                            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                                reform_animation = ui.asset_manager.get_skill_animation_sequence('reform')
                                if not reform_animation:
                                    reform_animation = [' ', '.', ':', 'o', 'O', 'M']
                                
                                ui.renderer.animate_attack_sequence(
                                    vapor_unit.y, vapor_unit.x,
                                    reform_animation,
                                    7,  # White color
                                    0.15  # Duration
                                )
                                
                                # Redraw to show final state
                                if hasattr(ui, 'draw_board'):
                                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                                    ui.renderer.refresh()
                    
                    # Kill the vapor using expire() to bypass invulnerability
                    vapor_unit.expire()
            
        # Clear all actions and update skill cooldowns
        for unit in self.units:
            if unit.is_alive():
                # Reset action targets
                unit.reset_action_targets()
                
                # Reduce cooldowns for skills ONLY for units belonging to current player
                if unit.player == self.current_player:
                    unit.tick_cooldowns()
                    
                    # NOTE: Jawline duration is already decremented in process_status_effects
                    # We don't decrement it here to avoid double-counting and making the effect expire too quickly
                    # However, we still need to check if it expired during this turn's execution
                    if unit.jawline_affected and unit.jawline_duration <= 0:
                        unit.jawline_affected = False
                        
                        # Reset movement to original value if we have the stored original
                        if hasattr(unit, 'jawline_original_move'):
                            # Reset the bonus to 0 to restore original movement
                            unit.move_range_bonus = 0
                            
                            # Clean up the stored value
                            delattr(unit, 'jawline_original_move')
                        
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
                
                # Passive skills are now applied at the start of each player's turn
                # instead of at the end of the previous player's turn
        
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
            
            # Removed healing effect for upgraded Marrow Dikes
        
        # Check if game is over
        self.check_game_over()
        
        # If UI is provided, redraw with cursor, selection, and attack targets before finishing
        if ui:
            # Stop the spinner
            ui.stop_spinner()
            
            # Slight delay before showing final state
            time.sleep(0.3)
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
                
            # Apply passive skills for the next player's units at the start of their turn
            # Also initialize the took_no_actions flag for health regeneration
            for unit in self.units:
                if unit.is_alive() and unit.player == self.current_player:
                    unit.apply_passive_skills(self)
                    # Initialize the flag for health regeneration
                    unit.took_no_actions = True
    
    
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
                        f"{unit.get_display_name()} retches!",
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
                    # Use centralized death handling
                    self.handle_unit_death(unit, foreman, cause="trap", ui=ui)
    
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
                
            # Skip friendly units - no friendly fire
            if unit.player == echo_unit.player:
                continue
                
            # Calculate distance to echo
            distance = self.chess_distance(echo_unit.y, echo_unit.x, unit.y, unit.x)
            if distance <= 1 and unit != echo_unit:  # Adjacent including diagonals, excluding the echo itself
                # Verify GRAYMAN units are immune to explosion effect
                if unit.type == UnitType.GRAYMAN and unit.is_immune_to_effects():
                    # Skip GRAYMAN units with Stasiality
                    continue
                    
                affected_units.append(unit)
        
        if not affected_units:
            # No units affected
            return
            
        # Log the explosion with a more dramatic message for the GRAYMAN echo
        message_log.add_message(
            f"{echo_unit.get_display_name()} collapses into a psychic void, tearing through spacetime!",
            MessageType.ABILITY,  # Use ABILITY type to ensure player color is used
            player=echo_unit.player
        )
        
        # Follow up with the affected units information
        if affected_units:
            message_log.add_message(
                f"The reality disruption affects {len(affected_units)} nearby unit(s)!",
                MessageType.ABILITY,
                player=echo_unit.player
            )
        
        # Animation for echo explosion
        if ui and hasattr(ui, 'renderer'):
            import time

            # Center explosion animation at echo position
            center_animation = ['Ψ', '*', 'O', '0', '~', 'Φ', '#', 'θ', '.']
            ui.renderer.animate_attack_sequence(
                echo_unit.y, echo_unit.x,
                center_animation,
                6,  # Yellow/explosion color
                0.08  # Duration (slightly faster for more dramatic effect)
            )
            
            # Get the 8 adjacent positions (cardinal and diagonal)
            adjacent_positions = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:  # Skip the center (already animated)
                        continue
                    
                    new_y, new_x = echo_unit.y + dy, echo_unit.x + dx
                    # Only include positions that are valid (on the board)
                    if self.is_valid_position(new_y, new_x):
                        adjacent_positions.append((new_y, new_x))
            
            # Secondary explosion animation for surrounding tiles
            # Shorter animation sequence for surrounding tiles
            ripple_animation = ['·', ':', '°']
            
            # Animate all adjacent tiles
            for pos in adjacent_positions:
                ui.renderer.animate_attack_sequence(
                    pos[0], pos[1],
                    ripple_animation,
                    6,  # Same yellow/explosion color
                    0.04  # Faster animation for ripple effect
                )
            
            # Redraw board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                if hasattr(time, 'sleep'):
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
            
            # Log the damage using combat message format to ensure player color
            message_log.add_combat_message(
                attacker_name=echo_unit.get_display_name(),
                target_name=unit.get_display_name(),
                damage=damage,
                ability="explosion",
                attacker_player=echo_unit.player,
                target_player=unit.player
            )
            
            # Show impact effects and damage number for explosion if UI is available
            if ui and hasattr(ui, 'renderer'):
                import curses
                
                # First, show an impact effect on the unit before showing damage
                if hasattr(ui, 'asset_manager'):
                    # Get the unit tile
                    unit_tile = ui.asset_manager.get_unit_tile(unit.type)
                    
                    # Flash the unit with alternating colors to show impact
                    for i in range(2):
                        # Use alternating colors (yellow and white) to show impact
                        color = 6 if i % 2 == 0 else 7  # 6:yellow, 7:white
                        ui.renderer.draw_tile(unit.y, unit.x, unit_tile, color, curses.A_BOLD)
                        ui.renderer.refresh()
                        if hasattr(time, 'sleep'):
                            time.sleep(0.1)
                
                # Show the damage text with flashing effect
                damage_text = f"-{damage}"
                
                # Make damage text more prominent with flashing effect
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    if hasattr(time, 'sleep'):
                        time.sleep(0.1)
                
                # Final damage display (stays on screen slightly longer)
                ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 7, curses.A_BOLD)
                ui.renderer.refresh()
                if hasattr(time, 'sleep'):
                    time.sleep(0.2)
            
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
    
    def _show_wall_attack_animation(self, ui, unit, wall_position, damage):
        """
        Show animation for a wall attack when a unit attacks a Marrow Dike wall.
        
        Args:
            ui: The UI reference for animations
            unit: The attacking unit
            wall_position: Tuple of (y, x) for the wall being attacked
            damage: The amount of damage being dealt to the wall
        """
        import time
        import curses
        from boneglaive.utils.coordinates import Position, get_line
        from boneglaive.utils.debug import logger
        
        # Skip animation if UI isn't available or doesn't have required methods
        if not ui or not hasattr(ui, 'renderer') or not hasattr(ui, 'asset_manager'):
            return
            
        # Unpack wall position
        wall_y, wall_x = wall_position
        
        # Get attack animation sequence
        # Use a special cracking/breaking sequence for wall attacks
        wall_attack_animation = ui.asset_manager.get_skill_animation_sequence('wall_attack')
        if not wall_attack_animation:
            # Fallback animation if not defined
            wall_attack_animation = ['*', '#', 'X', '=', '/', '\\', '|']
        
        # Get the unit's actual attack animation from the asset manager
        from boneglaive.utils.constants import UnitType
        
        # Create start and end positions
        start_pos = Position(unit.y, unit.x)
        end_pos = Position(wall_y, wall_x)
        
        # Get attack animation for this unit type
        effect_tile = ui.asset_manager.get_attack_effect(unit.type)
        animation_sequence = ui.asset_manager.get_attack_animation_sequence(unit.type)
        
        # For ranged attacks (archer and mage), show animation at origin then projectile path
        if unit.type in [UnitType.ARCHER, UnitType.MAGE]:
            # First show attack preparation at attacker's position
            prep_sequence = animation_sequence[:2]  # First few frames of animation sequence
            ui.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x,
                prep_sequence,
                7,  # color ID
                0.2  # quick preparation animation
            )
            
            # Then animate projectile from attacker to target
            ui.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                effect_tile,
                7,  # color ID
                0.3  # duration
            )
        # For MANDIBLE_FOREMAN, show a special animation sequence for mandible jaws
        elif unit.type == UnitType.MANDIBLE_FOREMAN:
            # Show the jaws animation at the attacker's position
            ui.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence[:3],  # First three frames - jaws opening
                7,  # color ID
                0.3  # slightly faster animation
            )
            
            # Show a short connecting animation between attacker and target
            ui.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                'Ξ',  # Mandible symbol
                7,    # color ID
                0.2   # quick connection
            )
        # For GLAIVEMAN attacks, check range and choose the right animation
        elif unit.type == UnitType.GLAIVEMAN:
            # Calculate distance to target
            distance = self.chess_distance(start_pos.y, start_pos.x, end_pos.y, end_pos.x)
            
            # For range 2 attacks, use extended animation
            if distance == 2:
                # Get the extended animation sequence
                extended_sequence = ui.asset_manager.animation_sequences.get('glaiveman_extended_attack', [])
                if extended_sequence:
                    # First show windup animation at attacker's position
                    ui.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        extended_sequence[:4],  # First few frames at attacker position
                        7,  # color ID
                        0.3  # duration
                    )
                    
                    # Calculate path from attacker to target
                    path = get_line(start_pos, end_pos)
                    
                    # Show glaive extending if path has at least 3 points
                    if len(path) >= 3:
                        mid_pos = path[1]  # Second point in the path
                        
                        # Show glaive extending through middle position
                        extension_chars = extended_sequence[4:8]  # Middle frames show extension
                        for i, char in enumerate(extension_chars):
                            ui.renderer.draw_tile(mid_pos.y, mid_pos.x, char, 7)
                            ui.renderer.refresh()
                            time.sleep(0.1)
                else:
                    # Fallback to standard animation
                    ui.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        animation_sequence,
                        7,  # color ID
                        0.5  # duration
                    )
            else:
                # For range 1 attacks, use standard animation
                ui.renderer.animate_attack_sequence(
                    start_pos.y, start_pos.x, 
                    animation_sequence,
                    7,  # color ID
                    0.5  # duration
                )
        # Special case for FOWL_CONTRIVANCE - bird swarm animation
        elif unit.type == UnitType.FOWL_CONTRIVANCE:
            # Get animation sequence for bird attacks
            fowl_sequence = ui.asset_manager.animation_sequences.get('fowl_contrivance_attack', [])
            if not fowl_sequence:
                fowl_sequence = ['^', 'v', '>', '<', '^', 'v', 'Λ', 'V']  # Fallback bird animation
            
            # Use alternating colors for a more dynamic bird flock appearance
            color_sequence = [1, 4, 1, 4, 6, 7, 6, 7]  # Red, blue, yellow, white alternating
            
            # Show initial gathering animation at attacker's position
            for i in range(3):
                frame = fowl_sequence[i % len(fowl_sequence)]
                color = color_sequence[i % len(color_sequence)]
                ui.renderer.draw_tile(start_pos.y, start_pos.x, frame, color)
                ui.renderer.refresh()
                time.sleep(0.08)
            
            # Create path points between attacker and target
            path = get_line(start_pos, end_pos)
            
            # Animate along the path with varied bird symbols
            path_points = []
            for i in range(1, len(path) - 1):  # Skip first (attacker) and last (target)
                path_points.append(path[i])
                
            for i, pos in enumerate(path_points):
                frame_idx = (i + 3) % len(fowl_sequence)  # Continue from where gathering left off
                color_idx = (i + 3) % len(color_sequence)
                ui.renderer.draw_tile(pos.y, pos.x, fowl_sequence[frame_idx], color_sequence[color_idx])
                ui.renderer.refresh()
                time.sleep(0.05)
                
                # Clear previous position (except the first one)
                if i > 0 and i < len(path_points) - 1:
                    prev_pos = path_points[i-1]
                    ui.renderer.draw_tile(prev_pos.y, prev_pos.x, ' ', 0)
                    ui.renderer.refresh()
        # For all other melee attacks, show standard animation
        else:
            # Show the attack animation at the attacker's position
            ui.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence,
                7,  # color ID
                0.5  # duration
            )
        
        # Show wall impact animation based on unit type
        if unit.type == UnitType.MAGE:
            impact_animation = ['!', '*', '!']  # Magic impact
        elif unit.type == UnitType.MANDIBLE_FOREMAN:
            impact_animation = ['>', '<', '}', '{', '≡']  # Mandible crushing impact
        elif unit.type == UnitType.FOWL_CONTRIVANCE:
            impact_animation = ['^', 'v', '^', 'V', 'Λ']  # Bird dive impact
        else:
            # Use the wall cracking animation for other units
            impact_animation = wall_attack_animation
            
        # Show impact animation at the wall position
        ui.renderer.animate_attack_sequence(
            wall_y, wall_x,
            impact_animation,
            6,  # Color code (red/orange)
            0.1  # Duration per frame
        )
        
        # Show damage number above the wall
        damage_text = f"-{damage}"
        
        # Make damage text more prominent with flashing effect
        for i in range(3):
            # First clear the area
            ui.renderer.draw_text(wall_y-1, wall_x*2, " " * len(damage_text), 7)
            # Draw with alternating bold/normal for a flashing effect
            attrs = curses.A_BOLD if i % 2 == 0 else 0
            ui.renderer.draw_text(wall_y-1, wall_x*2, damage_text, 1, attrs)  # Red color for wall damage
            ui.renderer.refresh()
            time.sleep(0.1)
        
        # Final damage display (stays on screen slightly longer)
        ui.renderer.draw_text(wall_y-1, wall_x*2, damage_text, 1, curses.A_BOLD)
        ui.renderer.refresh()
        time.sleep(0.3)
        
        # Clear the damage text
        ui.renderer.draw_text(wall_y-1, wall_x*2, " " * len(damage_text), 0)
        
        # Draw a cracking effect on the wall to show damage
        ui.renderer.draw_tile(wall_y, wall_x, '#', 20)  # Use red color for damaged wall
        ui.renderer.refresh()
        time.sleep(0.2)
        
        logger.debug(f"Wall attack animation shown at ({wall_y}, {wall_x})")
    
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
