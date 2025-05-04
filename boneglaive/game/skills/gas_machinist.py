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
            description="Generates 1 Effluvium charge per turn (max 3). Charges extend HEINOUS VAPOR duration by 1 turn each."
        )
        # Initialize charges to 0
        self.charges = 0
        self.max_charges = 3
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """
        Apply the Effluvium Lathe passive - generate 1 charge at the start of each turn.
        This method is called at the start of the player's turn.
        """
        # If this is a new turn for the unit's player, generate a charge
        if game and game.current_player == user.player:
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
            total_duration = base_duration + charges_consumed
            
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
            total_duration = base_duration + charges_consumed
            
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
            description="Splits an existing HEINOUS VAPOR or self into Coolant Gas (Σ, heals allies) and Cutting Gas (%, damages enemies).",
            target_type=TargetType.AREA,
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
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Target must be either self or a HEINOUS VAPOR owned by the player
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
        
        # Log that the skill has been queued
        is_self_target = (target_pos[0] == user.y and target_pos[1] == user.x)
        
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
        
        # Determine if targeting self or a vapor
        is_self_target = (target_pos[0] == user.y and target_pos[1] == user.x)
        target_unit = None if is_self_target else game.get_unit_at(target_pos[0], target_pos[1])
        
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
        
        # Get available adjacent positions for placing the vapors
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
        
        # If no valid positions, try to place on the target position
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
        
        # Randomly shuffle valid positions to avoid predictable placement
        random.shuffle(valid_positions)
        
        # Create Coolant Gas
        coolant_gas = Unit(UnitType.HEINOUS_VAPOR, user.player, valid_positions[0][0], valid_positions[0][1])
        coolant_gas.initialize_skills()
        coolant_gas.set_game_reference(game)
        
        # Set Coolant Gas properties
        coolant_gas.vapor_type = "COOLANT"
        coolant_gas.vapor_symbol = self.coolant_symbol
        coolant_gas.vapor_duration = 2  # Fixed duration of 2 turns for diverged gases
        coolant_gas.vapor_creator = user
        coolant_gas.vapor_skill = self
        
        # Create Cutting Gas - use a second position if available, otherwise use the same position
        cutting_pos = valid_positions[1] if len(valid_positions) > 1 else valid_positions[0]
        cutting_gas = Unit(UnitType.HEINOUS_VAPOR, user.player, cutting_pos[0], cutting_pos[1])
        cutting_gas.initialize_skills()
        cutting_gas.set_game_reference(game)
        
        # Set Cutting Gas properties
        cutting_gas.vapor_type = "CUTTING"
        cutting_gas.vapor_symbol = self.cutting_symbol
        cutting_gas.vapor_duration = 2  # Fixed duration of 2 turns for diverged gases
        cutting_gas.vapor_creator = user
        cutting_gas.vapor_skill = self
        
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