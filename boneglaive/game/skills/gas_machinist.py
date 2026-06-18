#!/usr/bin/env python3
"""
Skills specific to the GAS_MACHINIST unit type.
This module contains all passive and active abilities for GAS_MACHINIST units.
"""

import random
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class EffluviumLathe(PassiveSkill):
    """
    Passive skill for GAS_MACHINIST.
    Automatically generates 1 Effluvium charge at the start of each turn (max 3).
    Summoning a HEINOUS VAPOR consumes charges to extend its duration.
    """

    def __init__(self):
        super().__init__(
            name="Effluvium Lathe",
            key="L",
            description="Generates 1 Effluvium charge per turn (max 4). Charges extend HEINOUS VAPOR duration by 1 turn each. Does not generate charges while diverged."
        )
        # Initialize with 1 charge instead of 0
        self.charges = 1
        self.max_charges = 4  # Increased from 3 to 4
        # Track which turn and player we last generated a charge for to prevent multiple charges per turn
        # Initialize values to prevent charge generation during game initialization
        self.last_charge_turn = 1
        self.last_charge_player = None  # Track the player for whom we last generated a charge

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """
        Apply the Effluvium Lathe passive - generate 1 charge at the start of each turn.
        This method is called at the start of the player's turn.
        """
        # If this is a new turn for the unit's player, generate a charge
        if game and game.current_player == user.player:
            # Check if we've already generated a charge for this turn and player combination
            # This prevents multiple charges if apply_passive is called multiple times per turn
            # Special case: if last_charge_player is None (initialization), don't generate on turn 1
            if (self.last_charge_turn >= game.turn and
                (self.last_charge_player == user.player or
                 (self.last_charge_player is None and game.turn == 1))):
                return

            # Check if the user is in the diverged state (not on the board)
            # Gas Machinist is considered diverged when removed from the board (y, x set to -999, -999)
            is_diverged = hasattr(user, 'diverge_return_position') and getattr(user, 'diverge_return_position', False)

            # Don't generate charges if the user is diverged
            if is_diverged:
                return

            old_charges = self.charges

            # Generate a new charge if not at max
            if self.charges < self.max_charges:
                self.charges += 1
                # Mark that we've generated a charge for this turn and player
                self.last_charge_turn = game.turn
                self.last_charge_player = user.player

                # Log the charge generation
                if old_charges != self.charges:  # Only log if charges actually changed
                    message_log.add_message(
                        f"{user.get_display_name()}'s Effluvium Lathe generates a charge of gas ({self.charges}/{self.max_charges})",
                        MessageType.ABILITY,
                        player=user.player
                    )

    def consume_charges(self, amount: int) -> int:
        """
        Consume charges for a skill.
        Returns the actual number of charges consumed.
        """
        consumed = min(amount, self.charges)
        self.charges -= consumed
        return consumed


class EnbroachmentGasSkill(ActiveSkill):
    """
    Active skill for GAS_MACHINIST.
    Summons a HEINOUS VAPOR that dissolves status effects from allies
    and deals damage to enemies.
    """

    def __init__(self):
        super().__init__(
            name="Broaching Gas",
            key="B",
            description="Summons a HEINOUS VAPOR that deals 1 damage to enemies and cleanses allies of negative status effects.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=4
        )
        self.vapor_type = "BROACHING"
        self.vapor_symbol = "1"  # 1 symbol for Broaching Gas

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Broaching Gas can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Check if the target position is valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Target position must be passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        # Target position must be empty (no unit)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target is within range of current or planned position
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Broaching Gas skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Set the broaching gas indicator to show the target
        user.broaching_gas_indicator = target_pos

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to spin out a Broaching Gas",
            MessageType.ABILITY,
            player=user.player
        )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Broaching Gas skill to summon a HEINOUS VAPOR."""
        import time

        # Clear the broaching gas indicator when skill is executed
        user.broaching_gas_indicator = None

        # Get the passive skill to consume charges
        passive = None
        if user.passive_skill and user.passive_skill.name == "Effluvium Lathe":
            passive = user.passive_skill

        # Determine duration based on charges
        base_duration = 1
        charges_consumed = 0
        total_duration = base_duration

        if passive:
            # Consume all available charges
            charges_consumed = passive.consume_charges(passive.charges)

            # Special calculation: spending 1 charge gives 1 turn duration
            # Additional charges beyond the first still add 1 turn each
            if charges_consumed == 1:
                total_duration = 1  # 1 charge = 1 turn duration
            else:
                total_duration = base_duration + charges_consumed - 1  # Adjust formula

        # Skill activation message removed - only show expulsion message


        # Create a HEINOUS_VAPOR unit at the target position
        from boneglaive.game.units import Unit
        vapor_unit = Unit(UnitType.HEINOUS_VAPOR, user.player, target_pos[0], target_pos[1])
        vapor_unit.initialize_skills()
        vapor_unit.set_game_reference(game)

        # Set vapor properties
        vapor_unit.vapor_type = self.vapor_type
        vapor_unit.vapor_symbol = self.vapor_symbol
        vapor_unit.vapor_duration = total_duration
        vapor_unit.vapor_creator = user
        vapor_unit.vapor_skill = self
        # HEINOUS VAPOR uses PRT for effective invulnerability
        # Note: HEINOUS_VAPOR units are automatically immune to status effects via is_immune_to_effects() method

        # Add vapor to the game units
        game.units.append(vapor_unit)

        # Assign a letter identifier for this vapor based on its type (global across both players)
        from boneglaive.utils.constants import UNIT_ID_ALPHABET
        existing_vapors_of_type = len([u for u in game.units if u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and hasattr(u, 'vapor_type') and u.vapor_type == self.vapor_type])
        if existing_vapors_of_type <= len(UNIT_ID_ALPHABET):
            vapor_unit.greek_id = UNIT_ID_ALPHABET[existing_vapors_of_type - 1]  # -1 because we just added this vapor

        # Log the successful summoning with proper letter identifier
        message_log.add_message(
            f"{vapor_unit.get_display_name()} is expelled to position ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )

        return True


class SaftEGasSkill(ActiveSkill):
    """
    Active skill for GAS_MACHINIST.
    Summons a HEINOUS VAPOR that disrupts ranged attacks and heals allies.
    """

    def __init__(self):
        super().__init__(
            name="Saft-E-Gas",
            key="S",
            description="Summons a HEINOUS VAPOR that grants +1 defense to allies and heals allies by 1 HP.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=4
        )
        self.vapor_type = "SAFETY"
        self.vapor_symbol = "0"  # 0 symbol for Safety Gas

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Saft-E-Gas can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Check if the target position is valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Target position must be passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        # Target position must be empty (no unit)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target is within range of current or planned position
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Saft-E-Gas skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Set the saft-e-gas indicator to show the target
        user.saft_e_gas_indicator = target_pos

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to spin out a Saft-E-Gas",
            MessageType.ABILITY,
            player=user.player
        )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Saft-E-Gas skill to summon a HEINOUS VAPOR."""
        import time

        # Clear the saft-e-gas indicator when skill is executed
        user.saft_e_gas_indicator = None

        # Get the passive skill to consume charges
        passive = None
        if user.passive_skill and user.passive_skill.name == "Effluvium Lathe":
            passive = user.passive_skill

        # Determine duration based on charges
        base_duration = 1
        charges_consumed = 0
        total_duration = base_duration

        if passive:
            # Consume all available charges
            charges_consumed = passive.consume_charges(passive.charges)

            # Special calculation: spending 1 charge gives 1 turn duration
            # Additional charges beyond the first still add 1 turn each
            if charges_consumed == 1:
                total_duration = 1  # 1 charge = 1 turn duration
            else:
                total_duration = base_duration + charges_consumed - 1  # Adjust formula

        # Skill activation message removed - only show expulsion message


        # Create a HEINOUS_VAPOR unit at the target position
        from boneglaive.game.units import Unit
        vapor_unit = Unit(UnitType.HEINOUS_VAPOR, user.player, target_pos[0], target_pos[1])
        vapor_unit.initialize_skills()
        vapor_unit.set_game_reference(game)

        # Set vapor properties
        vapor_unit.vapor_type = self.vapor_type
        vapor_unit.vapor_symbol = self.vapor_symbol
        vapor_unit.vapor_duration = total_duration
        vapor_unit.vapor_creator = user
        vapor_unit.vapor_skill = self
        # HEINOUS VAPOR uses PRT for effective invulnerability
        # Note: HEINOUS_VAPOR units are automatically immune to status effects via is_immune_to_effects() method

        # Add vapor to the game units
        game.units.append(vapor_unit)

        # Assign a letter identifier for this vapor based on its type (global across both players)
        from boneglaive.utils.constants import UNIT_ID_ALPHABET
        existing_vapors_of_type = len([u for u in game.units if u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and hasattr(u, 'vapor_type') and u.vapor_type == self.vapor_type])
        if existing_vapors_of_type <= len(UNIT_ID_ALPHABET):
            vapor_unit.greek_id = UNIT_ID_ALPHABET[existing_vapors_of_type - 1]  # -1 because we just added this vapor

        # Log the successful summoning with proper letter identifier
        message_log.add_message(
            f"{vapor_unit.get_display_name()} is expelled to position ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )

        return True


class DivergeSkill(ActiveSkill):
    """
    Active skill for GAS_MACHINIST.
    Violently splits an existing HEINOUS VAPOR or self into two specialized entities.
    """

    def __init__(self):
        super().__init__(
            name="Diverge",
            key="D",
            description="Splits an existing HEINOUS VAPOR or self into Coolant Gas (heals allies) and Cutting Gas (damages enemies). Consumes all Effluvium charges to extend duration.",
            target_type=TargetType.SELF,  # Changed to SELF to enable self-targeting
            cooldown=4,
            range_=4
        )
        self.coolant_symbol = "2"  # 2 symbol for Coolant Gas
        self.cutting_symbol = "3"  # 3 symbol for Cutting Gas
        self.calibration_symbol = "4"  # 4 symbol for Calibration Gas

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Diverge can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Get current or planned position for range check and self-targeting
        # If there's a planned move, use that position for range check
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        # Target must be either self or a HEINOUS VAPOR owned by the player
        # If user has a planned move, only that position is valid for self-targeting, not the current position
        if user.move_target:
            # When there's a planned move, only the new position is valid
            is_self_target = (target_pos[0] == user.move_target[0] and target_pos[1] == user.move_target[1])
        else:
            # Otherwise, current position is valid
            is_self_target = (target_pos[0] == user.y and target_pos[1] == user.x)

        if is_self_target:
            return True

        # Otherwise, check if target is a HEINOUS VAPOR owned by the player
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or target_unit.type != UnitType.HEINOUS_VAPOR or target_unit.player != user.player:
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Diverge skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Get the user's current or planned position
        from_y, from_x = user.y, user.x
        if hasattr(user, 'move_target') and user.move_target:
            from_y, from_x = user.move_target

        # Log that the skill has been queued
        # If there's a planned move, only that position is considered "self"
        if user.move_target:
            is_self_target = (target_pos[0] == user.move_target[0] and target_pos[1] == user.move_target[1])
        else:
            is_self_target = (target_pos[0] == user.y and target_pos[1] == user.x)

        if is_self_target:
            message_log.add_message(
                f"{user.get_display_name()} prepares to diverge",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            target_unit = game.get_unit_at(target_pos[0], target_pos[1])
            message_log.add_message(
                f"{user.get_display_name()} prepares to diverge {target_unit.get_display_name()}",
                MessageType.ABILITY,
                player=user.player
            )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Diverge skill to split a HEINOUS VAPOR or self into two vapors."""
        import time
        from boneglaive.utils.coordinates import get_adjacent_positions

        # Get the user's current position - by execution time any planned move will have been executed
        from_y, from_x = user.y, user.x

        # Determine if targeting self or a vapor
        # Check if target matches current position or was a planned move position (which is now the current position)
        is_self_target = (target_pos[0] == user.y and target_pos[1] == user.x)
        target_unit = None if is_self_target else game.get_unit_at(target_pos[0], target_pos[1])

        # Get the passive skill to consume charges
        passive = None
        if user.passive_skill and user.passive_skill.name == "Effluvium Lathe":
            passive = user.passive_skill

        # Determine duration based on charges
        base_duration = 1
        charges_consumed = 0
        total_duration = base_duration

        if passive:
            # Consume all available charges
            charges_consumed = passive.consume_charges(passive.charges)

            # Special calculation: spending 1 charge gives 1 turn duration
            # Additional charges beyond the first still add 1 turn each
            if charges_consumed == 1:
                total_duration = 1  # 1 charge = 1 turn duration
            else:
                total_duration = base_duration + charges_consumed - 1  # Adjust formula

        # Skill activation messages removed - will show splitting message later


        # Check if Diverge is upgraded to determine how many positions we need
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Diverge")
        positions_needed = 3 if is_upgraded else 2

        # If targeting self, we need at least one valid position to place vapors
        # For self-targeting, we'll handle the GAS_MACHINIST differently
        if is_self_target:
            # We need to find at least one valid position - either the GAS_MACHINIST's position or adjacent
            origin_y, origin_x = target_pos

            # First, check if the current position is usable (after the GAS_MACHINIST is removed)
            if game.is_valid_position(origin_y, origin_x) and game.map.is_passable(origin_y, origin_x):
                # Current position is valid for one of the vapors
                valid_positions = [(origin_y, origin_x)]
            else:
                valid_positions = []

            # Then try adjacent positions
            adjacent_positions = get_adjacent_positions(origin_y, origin_x)
            for pos in adjacent_positions:
                y, x = pos
                if (game.is_valid_position(y, x) and
                    game.map.is_passable(y, x) and
                    game.get_unit_at(y, x) is None):
                    valid_positions.append(pos)
                    if len(valid_positions) >= positions_needed:  # Stop when we have enough positions
                        break

            # If we still don't have enough valid positions, try a wider search
            if len(valid_positions) < positions_needed:
                # Try a wider radius around the original position
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        # Skip adjacent ones that we already checked
                        if abs(dy) <= 1 and abs(dx) <= 1:
                            continue

                        y, x = origin_y + dy, origin_x + dx
                        if (game.is_valid_position(y, x) and
                            game.map.is_passable(y, x) and
                            game.get_unit_at(y, x) is None):
                            valid_positions.append((y, x))
                            if len(valid_positions) >= positions_needed:
                                break
                    if len(valid_positions) >= positions_needed:
                        break

            # For self-targeting, we need at least ONE valid position
            if not valid_positions:
                message_log.add_message(
                    "Diverge failed: no valid positions for vapor entities",
                    MessageType.ABILITY,
                    player=user.player
                )
                return False

            # If we have only one position, both vapors will go there
            if len(valid_positions) == 1:
                message_log.add_message(
                    "Limited space - both vapors will be created at the same position",
                    MessageType.ABILITY,
                    player=user.player
                )

        # For vapor targeting, handle positions differently
        else:
            # For targeting an existing vapor
            origin_y, origin_x = target_pos
            adjacent_positions = get_adjacent_positions(origin_y, origin_x)
            valid_positions = []

            # Filter for valid, empty positions
            for pos in adjacent_positions:
                y, x = pos
                if (game.is_valid_position(y, x) and
                    game.map.is_passable(y, x) and
                    game.get_unit_at(y, x) is None):
                    valid_positions.append(pos)

            # If no valid positions, try to place on the target position itself (after the vapor is removed)
            if not valid_positions:
                if game.is_valid_position(origin_y, origin_x) and game.map.is_passable(origin_y, origin_x):
                    valid_positions.append((origin_y, origin_x))

            # If still no valid positions, fail
            if not valid_positions:
                message_log.add_message(
                    "Diverge failed: no valid positions for vapor entities",
                    MessageType.ABILITY,
                    player=user.player
                )
                return False

        # If targeting self, remove user temporarily
        if is_self_target:
            # Store user position for potential return
            user_position = (user.y, user.x)
            # Move user off-screen temporarily
            user.y, user.x = -999, -999

        # If targeting a vapor, remove it
        elif target_unit:
            # Remove the target vapor from both units list and spatial grid
            game.units.remove(target_unit)
            game._remove_from_unit_grid(target_unit)

        # Create the gases
        from boneglaive.game.units import Unit
        import random

        # Randomly shuffle valid positions to avoid predictable placement
        random.shuffle(valid_positions)

        # Create Coolant Gas
        coolant_gas = Unit(UnitType.HEINOUS_VAPOR, user.player, valid_positions[0][0], valid_positions[0][1])
        coolant_gas.initialize_skills()
        coolant_gas.set_game_reference(game)

        # Set Coolant Gas properties
        coolant_gas.vapor_type = "COOLANT"
        coolant_gas.vapor_symbol = self.coolant_symbol
        coolant_gas.vapor_duration = total_duration  # Use duration based on charges
        coolant_gas.vapor_creator = user
        coolant_gas.vapor_skill = self
        coolant_gas.is_invulnerable = True  # Set invulnerability flag
        # Note: HEINOUS_VAPOR units are automatically immune to status effects via is_immune_to_effects() method

        # For case where we only have one valid position, we've already logged a message if needed

        # Create Cutting Gas - use a second position if available, otherwise use the same position
        cutting_pos = valid_positions[1] if len(valid_positions) > 1 else valid_positions[0]
        cutting_gas = Unit(UnitType.HEINOUS_VAPOR, user.player, cutting_pos[0], cutting_pos[1])
        cutting_gas.initialize_skills()
        cutting_gas.set_game_reference(game)

        # Set Cutting Gas properties
        cutting_gas.vapor_type = "CUTTING"
        cutting_gas.vapor_symbol = self.cutting_symbol
        cutting_gas.vapor_duration = total_duration  # Use duration based on charges
        cutting_gas.vapor_creator = user
        cutting_gas.vapor_skill = self
        cutting_gas.is_invulnerable = True  # Set invulnerability flag
        # Note: HEINOUS_VAPOR units are automatically immune to status effects via is_immune_to_effects() method

        # Create Calibration Gas if upgraded
        calibration_gas = None
        if is_upgraded:
            # Use a third position if available, otherwise stack with others
            calibration_pos = valid_positions[2] if len(valid_positions) > 2 else valid_positions[0]
            calibration_gas = Unit(UnitType.HEINOUS_VAPOR, user.player, calibration_pos[0], calibration_pos[1])
            calibration_gas.initialize_skills()
            calibration_gas.set_game_reference(game)

            # Set Calibration Gas properties
            calibration_gas.vapor_type = "CALIBRATION"
            calibration_gas.vapor_symbol = self.calibration_symbol
            calibration_gas.vapor_duration = total_duration
            calibration_gas.vapor_creator = user
            calibration_gas.vapor_skill = self
            calibration_gas.is_invulnerable = True

        # Add gases to the game
        game.units.append(coolant_gas)
        game.units.append(cutting_gas)
        if calibration_gas:
            game.units.append(calibration_gas)

        # Assign Greek identifiers for all vapors based on their types (global across both players)
        from boneglaive.utils.constants import UNIT_ID_ALPHABET

        # Count existing COOLANT gases from both players (including the one we just added)
        existing_coolant_count = len([u for u in game.units if u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and hasattr(u, 'vapor_type') and u.vapor_type == "COOLANT"])
        if existing_coolant_count <= len(UNIT_ID_ALPHABET):
            coolant_gas.greek_id = UNIT_ID_ALPHABET[existing_coolant_count - 1]  # -1 because we just added this vapor

        # Count existing CUTTING gases from both players (including the one we just added)
        existing_cutting_count = len([u for u in game.units if u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and hasattr(u, 'vapor_type') and u.vapor_type == "CUTTING"])
        if existing_cutting_count <= len(UNIT_ID_ALPHABET):
            cutting_gas.greek_id = UNIT_ID_ALPHABET[existing_cutting_count - 1]  # -1 because we just added this vapor

        # Count existing CALIBRATION gases if upgraded
        if calibration_gas:
            existing_calibration_count = len([u for u in game.units if u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and hasattr(u, 'vapor_type') and u.vapor_type == "CALIBRATION"])
            if existing_calibration_count <= len(UNIT_ID_ALPHABET):
                calibration_gas.greek_id = UNIT_ID_ALPHABET[existing_calibration_count - 1]

        # If targeting self, set return position property
        if is_self_target:
            # Set property to indicate user will return at either gas's location when they expire
            user.diverge_return_position = True
            coolant_gas.diverged_user = user
            cutting_gas.diverged_user = user
            if calibration_gas:
                calibration_gas.diverged_user = user

            # Log the user being split with proper Greek letters
            if calibration_gas:
                message_log.add_message(
                    f"{user.get_display_name()} splits into {coolant_gas.get_display_name()}, {cutting_gas.get_display_name()}, and {calibration_gas.get_display_name()}",
                    MessageType.ABILITY,
                    player=user.player
                )
            else:
                message_log.add_message(
                    f"{user.get_display_name()} splits into {coolant_gas.get_display_name()} and {cutting_gas.get_display_name()}",
                    MessageType.ABILITY,
                    player=user.player
                )
        else:
            # Log the vapor being split with proper Greek letters
            if calibration_gas:
                if target_unit:
                    message_log.add_message(
                        f"{user.get_display_name()} splits {target_unit.get_display_name()} into {coolant_gas.get_display_name()}, {cutting_gas.get_display_name()}, and {calibration_gas.get_display_name()}",
                        MessageType.ABILITY,
                        player=user.player
                    )
                else:
                    message_log.add_message(
                        f"{user.get_display_name()} diverges vapor into {coolant_gas.get_display_name()}, {cutting_gas.get_display_name()}, and {calibration_gas.get_display_name()}",
                        MessageType.ABILITY,
                        player=user.player
                    )
            else:
                if target_unit:
                    message_log.add_message(
                        f"{user.get_display_name()} splits {target_unit.get_display_name()} into {coolant_gas.get_display_name()} and {cutting_gas.get_display_name()}",
                        MessageType.ABILITY,
                        player=user.player
                    )
                else:
                    message_log.add_message(
                        f"{user.get_display_name()} diverges vapor into {coolant_gas.get_display_name()} and {cutting_gas.get_display_name()}",
                        MessageType.ABILITY,
                        player=user.player
                    )


        return True


class AerosolizeArmsSkill(ActiveSkill):
    """
    Active skill for GAS_MACHINIST (unlocked when Effluvium Lathe is upgraded).
    Disarms a target unit and creates a LIVING AEROSOL controlled by that unit's player.
    """

    def __init__(self):
        super().__init__(
            name="Aerosolize Arms",
            key="A",
            description="Disarm target unit and create a LIVING AEROSOL controlled by that player. Aerosol matches target's attack.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=4
        )
        self.aerosol_symbol = "5"  # 5 symbol for Living Aerosol

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Aerosolize Arms can be used."""
        # Check if Effluvium Lathe is upgraded
        from boneglaive.game.upgrades import UpgradeManager
        if not UpgradeManager.is_skill_upgraded(user, "Effluvium Lathe"):
            return False

        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Target must be a valid unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or not target_unit.is_alive():
            return False

        # Cannot target self
        if target_unit == user:
            return False

        # Cannot target HEINOUS_VAPOR units
        if target_unit.type == UnitType.HEINOUS_VAPOR:
            return False

        # Cannot target units immune to status effects (GRAYMAN with Stasiality)
        if target_unit.is_immune_to_effects():
            return False

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target is within range
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Aerosolize Arms skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        target_unit = game.get_unit_at(target_pos[0], target_pos[1])

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to aerosolize {target_unit.get_display_name()}'s arms",
            MessageType.ABILITY,
            player=user.player
        )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Aerosolize Arms skill."""
        import time
        from boneglaive.utils.coordinates import get_adjacent_positions

        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or not target_unit.is_alive():
            return False

        # Check if target is immune to disarm (GRAYMAN with Stasiality)
        if target_unit.is_immune_to_effects():
            message_log.add_message(
                f"{target_unit.get_display_name()} is immune to disarm due to Stasiality",
                MessageType.ABILITY,
                player=user.player
            )
            return False

        # Get the passive skill to determine duration
        passive = None
        if user.passive_skill and user.passive_skill.name == "Effluvium Lathe":
            passive = user.passive_skill

        # Determine duration based on charges (same formula as other vapors)
        base_duration = 1
        charges_consumed = 0
        total_duration = base_duration

        if passive:
            # Consume all available charges
            charges_consumed = passive.consume_charges(passive.charges)

            # Special calculation: spending 1 charge gives 1 turn duration
            # Additional charges beyond the first still add 1 turn each
            if charges_consumed == 1:
                total_duration = 1  # 1 charge = 1 turn duration
            else:
                total_duration = base_duration + charges_consumed - 1  # Adjust formula

        # Apply disarm to target (duration matches vapor duration)
        target_unit.status_disarmed = True
        target_unit.status_disarmed_duration = total_duration

        message_log.add_message(
            f"{target_unit.get_display_name()} is disarmed by aerosolized effluvium",
            MessageType.WARNING,
            player=user.player,
            target=target_unit.player,
            target_name=target_unit.get_display_name()
        )


        # Find a valid position for the LIVING AEROSOL (prefer target's location or adjacent)
        valid_positions = []

        # Try adjacent positions first
        adjacent_positions = get_adjacent_positions(target_unit.y, target_unit.x)
        for pos in adjacent_positions:
            y, x = pos
            if (game.is_valid_position(y, x) and
                game.map.is_passable(y, x) and
                game.get_unit_at(y, x) is None):
                valid_positions.append(pos)

        if not valid_positions:
            message_log.add_message(
                "Aerosolize Arms failed: no valid positions for LIVING AEROSOL",
                MessageType.ABILITY,
                player=user.player
            )
            return False

        # Create LIVING_AEROSOL at first valid position
        from boneglaive.game.units import Unit
        aerosol_pos = valid_positions[0]
        aerosol_unit = Unit(UnitType.HEINOUS_VAPOR, target_unit.player, aerosol_pos[0], aerosol_pos[1])
        aerosol_unit.initialize_skills()
        aerosol_unit.set_game_reference(game)

        # Set LIVING AEROSOL properties
        aerosol_unit.vapor_type = "LIVING_AEROSOL"
        aerosol_unit.vapor_symbol = self.aerosol_symbol
        aerosol_unit.vapor_duration = total_duration
        aerosol_unit.vapor_creator = user
        aerosol_unit.vapor_skill = self
        aerosol_unit.source_unit = target_unit  # Track which unit it came from

        # Copy target's attack stat
        aerosol_unit.attack = target_unit.attack

        # Add to game
        game.units.append(aerosol_unit)

        # Assign Greek identifier
        from boneglaive.utils.constants import UNIT_ID_ALPHABET
        existing_aerosols = len([u for u in game.units if u.is_alive() and u.type == UnitType.HEINOUS_VAPOR and hasattr(u, 'vapor_type') and u.vapor_type == "LIVING_AEROSOL"])
        if existing_aerosols <= len(UNIT_ID_ALPHABET):
            aerosol_unit.greek_id = UNIT_ID_ALPHABET[existing_aerosols - 1]

        # Log creation
        message_log.add_message(
            f"{aerosol_unit.get_display_name()} materializes under Player {target_unit.player}'s control",
            MessageType.ABILITY,
            player=user.player
        )


        return True
