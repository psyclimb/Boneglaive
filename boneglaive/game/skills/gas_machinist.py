#!/usr/bin/env python3
"""
Skills specific to the GAS_MACHINIST unit type.
This module contains all passive and active abilities for GAS_MACHINIST units.
"""

import curses
import time
import random
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.animation_helpers import sleep_with_animation_speed
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
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """
        Apply the Effluvium Lathe passive - generate 1 charge at the start of each turn.
        This method is called at the start of the player's turn.
        """
        # If this is a new turn for the unit's player, generate a charge
        if game and game.current_player == user.player:
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
                
                # Log the charge generation
                if old_charges != self.charges:  # Only log if charges actually changed
                    message_log.add_message(
                        f"{user.get_display_name()}'s Effluvium Lathe generates a charge ({self.charges}/{self.max_charges})!",
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
            description="Summons a HEINOUS VAPOR (Φ) that deals 2 damage to enemies and cleanses allies of negative status effects.",
            target_type=TargetType.AREA,
            cooldown=2,
            range_=3
        )
        self.vapor_type = "BROACHING"
        self.vapor_symbol = "Φ"  # Phi symbol for Broaching Gas
        
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
            
        # Check if target is within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Broaching Gas skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to summon a Broaching Gas vapor!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Broaching Gas skill to summon a HEINOUS VAPOR."""
        import time
        
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
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} summons a Broaching Gas vapor!",
            MessageType.ABILITY,
            player=user.player
        )
        
        if charges_consumed > 0:
            message_log.add_message(
                f"Using {charges_consumed} Effluvium charges to extend duration to {total_duration} turns!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get vapor summoning animation
            vapor_animation = ui.asset_manager.get_skill_animation_sequence('summon_vapor')
            if not vapor_animation:
                vapor_animation = ['~', 'o', 'O', 'Φ']  # Fallback animation
                
            # Show summoning animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                vapor_animation,
                7,  # White color
                0.15  # Duration
            )
        
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
        vapor_unit.is_invulnerable = True  # Set invulnerability flag
        
        # Add vapor to the game units
        game.units.append(vapor_unit)
        
        # Log the successful summoning
        message_log.add_message(
            f"A Broaching Gas vapor ({self.vapor_symbol}) appears at position ({target_pos[0]}, {target_pos[1]})!",
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
            description="Summons a HEINOUS VAPOR (Θ) that blocks enemy ranged attacks and heals allies by 1 HP.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3
        )
        self.vapor_type = "SAFETY"
        self.vapor_symbol = "Θ"  # Theta symbol for Safety Gas
        
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
            
        # Check if target is within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Saft-E-Gas skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to summon a Saft-E-Gas vapor!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Saft-E-Gas skill to summon a HEINOUS VAPOR."""
        import time
        
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
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} summons a Saft-E-Gas vapor!",
            MessageType.ABILITY,
            player=user.player
        )
        
        if charges_consumed > 0:
            message_log.add_message(
                f"Using {charges_consumed} Effluvium charges to extend duration to {total_duration} turns!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get vapor summoning animation
            vapor_animation = ui.asset_manager.get_skill_animation_sequence('summon_vapor')
            if not vapor_animation:
                vapor_animation = ['~', 'o', 'O', 'Θ']  # Fallback animation
                
            # Show summoning animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                vapor_animation,
                7,  # White color
                0.15  # Duration
            )
        
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
        vapor_unit.is_invulnerable = True  # Set invulnerability flag
        
        # Add vapor to the game units
        game.units.append(vapor_unit)
        
        # Log the successful summoning
        message_log.add_message(
            f"A Saft-E-Gas vapor ({self.vapor_symbol}) appears at position ({target_pos[0]}, {target_pos[1]})!",
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
            description="Splits an existing HEINOUS VAPOR or self into Coolant Gas (Σ, heals allies) and Cutting Gas (%, damages enemies). Consumes all Effluvium charges to extend duration.",
            target_type=TargetType.SELF,  # Changed to SELF to enable self-targeting
            cooldown=4,
            range_=5
        )
        self.coolant_symbol = "Σ"  # Sigma symbol for Coolant Gas
        self.cutting_symbol = "%"  # Percent symbol for Cutting Gas
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Diverge can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check range
        # If there's a planned move, use that position for range check
        from_y, from_x = user.y, user.x
        if hasattr(user, 'move_target') and user.move_target:
            from_y, from_x = user.move_target
            
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Target must be either self (current position OR planned position) or a HEINOUS VAPOR owned by the player
        is_self_target = (target_pos[0] == user.y and target_pos[1] == user.x) or \
                         (user.move_target and target_pos[0] == user.move_target[0] and target_pos[1] == user.move_target[1])
        
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
        is_self_target = (target_pos[0] == from_y and target_pos[1] == from_x)
        
        if is_self_target:
            message_log.add_message(
                f"{user.get_display_name()} prepares to diverge!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            target_unit = game.get_unit_at(target_pos[0], target_pos[1])
            message_log.add_message(
                f"{user.get_display_name()} prepares to diverge a vapor at ({target_pos[0]}, {target_pos[1]})!",
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
        
        # Log the skill activation
        if is_self_target:
            message_log.add_message(
                f"{user.get_display_name()} diverges into two vapor entities!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} causes the vapor to diverge into two specialized entities!",
                MessageType.ABILITY,
                player=user.player
            )
            
        if charges_consumed > 0:
            message_log.add_message(
                f"Using {charges_consumed} Effluvium charges to extend duration to {total_duration} turns!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get diverge animation
            diverge_animation = ui.asset_manager.get_skill_animation_sequence('diverge')
            if not diverge_animation:
                diverge_animation = ['*', '+', 'x', '#', '@']  # Fallback animation
                
            # Show diverge animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                diverge_animation,
                7,  # White color
                0.15  # Duration
            )
        
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
                    if len(valid_positions) >= 2:  # We only need at most 2 positions
                        break
                        
            # If we still don't have any valid positions, try a wider search
            if not valid_positions:
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
                            if len(valid_positions) >= 2:
                                break
                    if len(valid_positions) >= 2:
                        break
                        
            # For self-targeting, we need at least ONE valid position
            if not valid_positions:
                message_log.add_message(
                    "Diverge failed: no valid positions for vapor entities!",
                    MessageType.ABILITY,
                    player=user.player
                )
                return False
                
            # If we have only one position, both vapors will go there
            if len(valid_positions) == 1:
                message_log.add_message(
                    "Limited space - both vapors will be created at the same position!",
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
                    "Diverge failed: no valid positions for vapor entities!",
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
            # Remove the target vapor
            game.units.remove(target_unit)
            
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
        
        # Add gases to the game
        game.units.append(coolant_gas)
        game.units.append(cutting_gas)
        
        # If targeting self, set return position property
        if is_self_target:
            # Set property to indicate user will return at either gas's location when they expire
            user.diverge_return_position = True
            coolant_gas.diverged_user = user
            cutting_gas.diverged_user = user
            
            # Log the user being split
            message_log.add_message(
                f"{user.get_display_name()} splits into a Coolant Gas ({self.coolant_symbol}) and a Cutting Gas ({self.cutting_symbol})!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            # Log the vapor being split
            message_log.add_message(
                f"The vapor splits into a Coolant Gas ({self.coolant_symbol}) and a Cutting Gas ({self.cutting_symbol})!",
                MessageType.ABILITY,
                player=user.player
            )
            
        # Play additional animations for the new gases
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Show animation for Coolant Gas
            coolant_animation = ui.asset_manager.get_skill_animation_sequence('coolant_gas')
            if not coolant_animation:
                coolant_animation = ['~', '*', self.coolant_symbol]
            
            ui.renderer.animate_attack_sequence(
                coolant_gas.y, coolant_gas.x,
                coolant_animation,
                6,  # Blue/cyan color
                0.15
            )
            
            # Show animation for Cutting Gas
            cutting_animation = ui.asset_manager.get_skill_animation_sequence('cutting_gas')
            if not cutting_animation:
                cutting_animation = ['~', '*', self.cutting_symbol]
            
            ui.renderer.animate_attack_sequence(
                cutting_gas.y, cutting_gas.x,
                cutting_animation,
                1,  # Red color
                0.15
            )
            
            # Redraw to show final state
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                ui.renderer.refresh()
        
        return True