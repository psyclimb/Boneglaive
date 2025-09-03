#!/usr/bin/env python3
"""
Skills specific to the DERELIST unit type.
This module contains all passive and active abilities for DERELIST units.

The DERELIST is a support/healer unit focused on psychological abandonment therapy,
trauma processing, and distance-based healing mechanics.
"""

import curses
import time
import random
import math
from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


def calculate_distance(unit1: 'Unit', unit2: 'Unit') -> int:
    """Calculate Manhattan distance between two units."""
    return abs(unit1.y - unit2.y) + abs(unit1.x - unit2.x)


def calculate_distance_coords(y1: int, x1: int, y2: int, x2: int) -> int:
    """Calculate Manhattan distance between two coordinates."""
    return abs(y1 - y2) + abs(x1 - x2)


class Severance(PassiveSkill):
    """
    Passive skill for DERELIST.
    Allows skill-then-move capability with enhanced range after using skills.
    """
    
    def __init__(self):
        super().__init__(
            name="Severance",
            key="S",
            description="After using a skill, can move with +1 range (4 instead of 3). Cannot move twice in one turn."
        )
    
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """Apply effects of the passive skill."""
        # This skill is handled by the game engine during turn processing
        # It allows post-skill movement with enhanced range
        pass


class VagalRunSkill(ActiveSkill):
    """
    Active skill: VAGAL RUN
    Immediate cleansing trauma therapy with delayed abreaction.
    """
    
    def __init__(self):
        super().__init__(
            name="Vagal Run",
            key="V", 
            description="Immediately deals piercing damage (3 at range 1, reduced by distance) and clears all status effects. After 3 turns, abreaction deals same damage and clears status effects again.",
            target_type=TargetType.ALLY,
            cooldown=4,
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False
            
        if not target_pos or not game:
            return False
            
        # Check range first
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Find target unit at position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Can only target allies
        if target.player != user.player:
            return False
            
        # Cannot target self
        if target == user:
            return False
            
        # Check if target already has vagal run effect
        if hasattr(target, 'vagal_run_active') and target.vagal_run_active:
            return False
            
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Vagal Run skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # Queue the skill for execution during combat phase
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set action timestamp for turn order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            
        # Set cooldown immediately when queuing
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued
        target = game.get_unit_at(target_pos[0], target_pos[1])
        target_name = target.get_display_name() if target else "ally"
        
        message_log.add_message(
            f"{user.get_display_name()} prepares to enhance {target_name} with Vagal Run",
            MessageType.ABILITY,
            player=user.player
        )
        
        logger.info(f"VAGAL RUN QUEUED: {user.get_display_name()} targeting {target_name}")
        
        # Severance passive: Apply SEVERANCE status effect for enhanced movement
        if user.type == UnitType.DERELIST:
            user.can_move_post_skill = True
            user.used_skill_this_turn = True
            # Apply SEVERANCE status effect (+1 movement until move is issued)
            user.severance_active = True
            user.severance_duration = 1  # Lasts until movement
            logger.info(f"SEVERANCE: {user.get_display_name()} gains enhanced movement (SEVERANCE status active)")
        
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Vagal Run during combat phase."""
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return
            
        # Calculate distance-based piercing damage
        distance = calculate_distance(user, target)
        piercing_damage = min(3, max(0, 4 - distance))  # Max 3 at distance 1, reduced by distance
        
        # Store the damage amount for abreaction
        target.vagal_run_active = True
        target.vagal_run_caster = user  # Reference to DERELIST who cast this
        target.vagal_run_abreaction_damage = piercing_damage  # Store original damage for abreaction
        target.vagal_run_duration = 3  # Effect lasts 3 turns
        
        # Apply immediate piercing damage (ignores defense, can't kill)
        if piercing_damage > 0:
            actual_damage = target.apply_damage_with_protection(piercing_damage, can_kill=False, damage_source="Vagal Run trauma processing")
            
            message_log.add_message(
                f"{target.get_display_name()} takes {actual_damage} trauma processing damage",
                MessageType.COMBAT
            )
        
        # Clear ALL status effects immediately
        cleared_effects = self._clear_all_status_effects(target)
        
        # Show execution animation if UI available
        if ui and hasattr(ui, 'renderer'):
            # Vagal run animation - cleansing waves
            vagal_animation = ['~', '≈', '∿', '≈', '~']
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                vagal_animation,
                6,  # Yellow color for vagal run
                0.1
            )
        
        # Generate message about cleared effects
        if cleared_effects:
            effects_text = ", ".join(cleared_effects)
            message_log.add_message(
                f"{target.get_display_name()}'s Vagal Run sloughs off {effects_text}",
                MessageType.ABILITY
            )
        else:
            message_log.add_message(
                f"{target.get_display_name()} undergoes trauma processing",
                MessageType.ABILITY
            )
        
        logger.info(f"VAGAL RUN EXECUTED: {user.get_display_name()} applies trauma processing to {target.get_display_name()} (damage: {piercing_damage}, distance: {distance})")
        
        # Note: Severance passive bonus already applied during planning phase
    
    def _clear_all_status_effects(self, target: 'Unit') -> list:
        """Clear all status effects from a unit and return list of cleared effects."""
        cleared_effects = []
        
        # DON'T clear vagal_run_active - that would remove itself!
        
        # Clear negative status effects (based on UI renderer attribute names)
        if hasattr(target, 'derelicted') and target.derelicted:
            target.derelicted = False
            if hasattr(target, 'derelicted_duration'):
                target.derelicted_duration = 0
            cleared_effects.append("Derelicted")
            
        if hasattr(target, 'trapped_by') and target.trapped_by:
            target.trapped_by = None
            if hasattr(target, 'trap_duration'):
                target.trap_duration = 0
            cleared_effects.append("Trapped")
            
        if hasattr(target, 'mired') and target.mired:
            target.mired = False
            if hasattr(target, 'mired_duration'):
                target.mired_duration = 0
            cleared_effects.append("Mired")
            
        if hasattr(target, 'was_pried') and target.was_pried:
            target.was_pried = False
            target.move_range_bonus = max(0, target.move_range_bonus)
            cleared_effects.append("Pried")
            
        if hasattr(target, 'jawline_affected') and target.jawline_affected:
            target.jawline_affected = False
            if hasattr(target, 'jawline_duration'):
                target.jawline_duration = 0
            cleared_effects.append("Jawline")
            
        if hasattr(target, 'neural_shunt_affected') and target.neural_shunt_affected:
            target.neural_shunt_affected = False
            if hasattr(target, 'neural_shunt_duration'):
                target.neural_shunt_duration = 0
            cleared_effects.append("Neural Shunt")
            
        if hasattr(target, 'auction_curse_dot') and target.auction_curse_dot:
            target.auction_curse_dot = False
            cleared_effects.append("Auction Curse")
            
        if hasattr(target, 'radiation_stacks') and target.radiation_stacks:
            if isinstance(target.radiation_stacks, list):
                if len(target.radiation_stacks) > 0:
                    target.radiation_stacks = []
                    cleared_effects.append("Radiation Sickness")
            else:
                if target.radiation_stacks > 0:
                    target.radiation_stacks = 0
                    cleared_effects.append("Radiation Sickness")
        
        # Clear positive status effects (but not permanent abilities or vagal run)
        if hasattr(target, 'carrier_rave_active') and target.carrier_rave_active:
            target.carrier_rave_active = False
            if hasattr(target, 'carrier_rave_duration'):
                target.carrier_rave_duration = 0
            cleared_effects.append("Karrier Rave")
            
        if hasattr(target, 'ossify_active') and target.ossify_active:
            target.ossify_active = False
            if hasattr(target, 'ossify_duration'):
                target.ossify_duration = 0
            cleared_effects.append("Ossify")
            
        if hasattr(target, 'status_site_inspection') and target.status_site_inspection:
            target.status_site_inspection = False
            if hasattr(target, 'status_site_inspection_duration'):
                target.status_site_inspection_duration = 0
            cleared_effects.append("Site Inspection")
            
        if hasattr(target, 'status_site_inspection_partial') and target.status_site_inspection_partial:
            target.status_site_inspection_partial = False
            if hasattr(target, 'status_site_inspection_partial_duration'):
                target.status_site_inspection_partial_duration = 0
            cleared_effects.append("Site Inspection (Partial)")
            
        if hasattr(target, 'valuation_oracle_buff') and target.valuation_oracle_buff:
            target.valuation_oracle_buff = False
            if hasattr(target, 'valuation_oracle_duration'):
                target.valuation_oracle_duration = 0
            target.defense_bonus = 0
            target.attack_range_bonus = 0
            cleared_effects.append("Valuation Oracle")
            
        if hasattr(target, 'slough_def_duration') and target.slough_def_duration > 0:
            target.slough_def_duration = 0
            cleared_effects.append("Slough Defense")
            
        if hasattr(target, 'has_investment_effect') and target.has_investment_effect:
            target.has_investment_effect = False
            if hasattr(target, 'market_futures_duration'):
                target.market_futures_duration = 0
            if hasattr(target, 'market_futures_maturity'):
                target.attack_bonus = max(0, target.attack_bonus - target.market_futures_maturity)
                target.market_futures_maturity = 0
            cleared_effects.append("Investment")
            
        if hasattr(target, 'partition_shield_active') and target.partition_shield_active:
            target.partition_shield_active = False
            if hasattr(target, 'partition_shield_duration'):
                target.partition_shield_duration = 0
            if hasattr(target, 'partition_shield_damage_reduction'):
                target.partition_shield_damage_reduction = 0
            if hasattr(target, 'partition_shield_emergency_active'):
                target.partition_shield_emergency_active = False
            if hasattr(target, 'partition_shield_blocked_fatal'):
                target.partition_shield_blocked_fatal = False
            if hasattr(target, 'partition_shield_caster'):
                target.partition_shield_caster = None
            cleared_effects.append("Partition Shield")
            
        if hasattr(target, 'charging_status') and target.charging_status:
            target.charging_status = False
            cleared_effects.append("Charging")
            
        if hasattr(target, 'first_turn_move_bonus') and target.first_turn_move_bonus:
            target.first_turn_move_bonus = False
            cleared_effects.append("First Turn Bonus")
            
        # Don't clear severance_active as it's related to DERELIST's own passive
        
        # Reset stat bonuses carefully (don't interfere with vagal run's own tracking)
        if not (hasattr(target, 'vagal_run_active') and target.vagal_run_active):
            target.attack_bonus = 0
            target.defense_bonus = 0
            target.move_range_bonus = 0
            target.attack_range_bonus = 0
        
        logger.info(f"Cleared {len(cleared_effects)} status effects from {target.get_display_name()}: {cleared_effects}")
        return cleared_effects
    


class DerelictSkill(ActiveSkill):
    """
    Active skill: DERELICT  
    Push ally away and heal based on distance, apply immobilization.
    """
    
    def __init__(self):
        super().__init__(
            name="Derelict",
            key="D",
            description="Push ally 4 tiles away in straight line. Ally heals for 3 HP + distance from DERELIST and becomes immobilized for 1 turn.",
            target_type=TargetType.ALLY,
            cooldown=4,
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False
            
        if not target_pos or not game:
            return False
            
        # Check range first
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Find target unit at position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Can only target allies
        if target.player != user.player:
            return False
            
        # Cannot target self
        if target == user:
            return False
            
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Derelict skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # Calculate and store push direction NOW (during planning) to avoid position change issues
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if target:
            # Calculate push direction from current DERELIST position
            dy = target.y - user.y
            dx = target.x - user.x
            
            # Normalize direction
            if dy != 0:
                dy = 1 if dy > 0 else -1
            if dx != 0:
                dx = 1 if dx > 0 else -1
            
            # Store push direction on the target unit for execution phase
            target.derelict_push_direction = (dy, dx)
            target.derelict_caster_position = (user.y, user.x)  # Store original DERELIST position
            
        # Queue the skill for execution during combat phase
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set action timestamp for turn order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            
        # Set cooldown immediately when queuing
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued
        target_name = target.get_display_name() if target else "ally"
        
        message_log.add_message(
            f"{user.get_display_name()} prepares to convey {target_name} away",
            MessageType.ABILITY,
            player=user.player
        )
        
        logger.info(f"DERELICT QUEUED: {user.get_display_name()} targeting {target_name} with direction ({dy},{dx})")
        
        # Severance passive: Apply SEVERANCE status effect for enhanced movement
        if user.type == UnitType.DERELIST:
            user.can_move_post_skill = True
            user.used_skill_this_turn = True
            # Apply SEVERANCE status effect (+1 movement until move is issued)
            user.severance_active = True
            user.severance_duration = 1  # Lasts until movement
            logger.info(f"SEVERANCE: {user.get_display_name()} gains enhanced movement (SEVERANCE status active)")
        
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Derelict during combat phase."""
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return
            
        # Use stored push direction (calculated during planning phase)
        if hasattr(target, 'derelict_push_direction'):
            dy, dx = target.derelict_push_direction
            logger.info(f"Using stored push direction: ({dy},{dx})")
        else:
            # Fallback: calculate from current positions (shouldn't happen)
            dy = target.y - user.y
            dx = target.x - user.x
            
            # Normalize direction
            if dy != 0:
                dy = 1 if dy > 0 else -1
            if dx != 0:
                dx = 1 if dx > 0 else -1
            
            logger.warning(f"No stored push direction, using fallback: ({dy},{dx})")
        
        # Show abandonment animation if UI available
        if ui and hasattr(ui, 'renderer'):
            # Abandonment animation - pushing effect
            abandon_animation = ['>', '>>', '>>>', '>>', '>']
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                abandon_animation,
                3,  # Red color for abandonment
                0.15
            )
        
        # Try to push 4 tiles in that direction
        push_distance = 0
        final_y, final_x = target.y, target.x
        
        for distance in range(1, 5):  # Try 1-4 tiles
            new_y = target.y + (dy * distance)
            new_x = target.x + (dx * distance)
            
            # Check if position is valid and not occupied
            if (game.is_valid_position(new_y, new_x) and 
                game.map.is_passable(new_y, new_x) and
                game.get_unit_at(new_y, new_x) is None):
                final_y, final_x = new_y, new_x
                push_distance = distance
            else:
                break
        
        # Move target to final position
        if push_distance > 0:
            target.y = final_y
            target.x = final_x
        
        # Calculate healing based on final distance from DERELIST's ORIGINAL position
        # (Use stored position from planning phase to maintain consistent healing)
        if hasattr(target, 'derelict_caster_position'):
            orig_derelist_y, orig_derelist_x = target.derelict_caster_position
            distance_to_derelist = calculate_distance_coords(final_y, final_x, orig_derelist_y, orig_derelist_x)
        else:
            # Fallback to current position
            distance_to_derelist = calculate_distance_coords(final_y, final_x, user.y, user.x)
            
        heal_amount = 3 + distance_to_derelist
        
        # Apply healing
        if target.hp < target.max_hp:
            old_hp = target.hp
            target.hp = min(target.max_hp, target.hp + heal_amount)
            actual_heal = target.hp - old_hp
            
            message_log.add_message(
                f"{target.get_display_name()} pushed {push_distance} tiles and healed for {actual_heal} HP!",
                MessageType.ABILITY
            )
            
            # Show healing effect on map if UI is available
            if ui and hasattr(ui, 'renderer') and actual_heal > 0:
                import curses
                import time
                from boneglaive.utils.animation_helpers import sleep_with_animation_speed
                
                healing_text = f"+{actual_heal}"
                
                # Make healing text prominent with flashing effect (green color)
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(healing_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_damage_text(target.y-1, target.x*2, healing_text, 3, attrs)  # Green color
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
                
                # Final healing display (stays on screen slightly longer)
                ui.renderer.draw_damage_text(target.y-1, target.x*2, healing_text, 3, curses.A_BOLD)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.3)  # Match the 0.3s delay used in other healing
        else:
            message_log.add_message(
                f"{target.get_display_name()} pushed {push_distance} tiles (already at full health)!",
                MessageType.ABILITY
            )
        
        # Apply Derelicted status (immobilization for 1 turn)
        target.derelicted = True
        target.derelicted_duration = 1
        
        # Clean up stored direction data
        if hasattr(target, 'derelict_push_direction'):
            delattr(target, 'derelict_push_direction')
        if hasattr(target, 'derelict_caster_position'):
            delattr(target, 'derelict_caster_position')
        
        logger.info(f"DERELICT EXECUTED: {user.get_display_name()} pushed {target.get_display_name()} {push_distance} tiles, healed {heal_amount}, applied immobilization")
        
        # Note: Severance passive bonus already applied during planning phase


class PartitionSkill(ActiveSkill):
    """
    Active skill: PARTITION
    Protective barrier with emergency intervention capability.
    """
    
    def __init__(self):
        super().__init__(
            name="Partition",
            key="P",
            description="Grant ally shield that blocks 1 damage from all sources for 3 turns. If unit would take fatal damage, completely blocks all damage that turn, then ends effect, teleports DERELIST 4 tiles away, and applies Derelicted.",
            target_type=TargetType.ALLY,
            cooldown=5,
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False
            
        if not target_pos or not game:
            return False
            
        # Check range first
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Find target unit at position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Can only target allies
        if target.player != user.player:
            return False
        
        # Check if target already has partition shield
        if hasattr(target, 'partition_shield_active') and target.partition_shield_active:
            return False
            
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Partition skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # Queue the skill for execution during combat phase
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set action timestamp for turn order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            
        # Set cooldown immediately when queuing
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued
        target = game.get_unit_at(target_pos[0], target_pos[1])
        target_name = target.get_display_name() if target else "ally"
        
        message_log.add_message(
            f"{user.get_display_name()} prepares to partition {target_name} from harm",
            MessageType.ABILITY,
            player=user.player
        )
        
        logger.info(f"PARTITION QUEUED: {user.get_display_name()} targeting {target_name}")
        
        # Severance passive: Apply SEVERANCE status effect for enhanced movement
        if user.type == UnitType.DERELIST:
            user.can_move_post_skill = True
            user.used_skill_this_turn = True
            # Apply SEVERANCE status effect (+1 movement until move is issued)
            user.severance_active = True
            user.severance_duration = 1  # Lasts until movement
            logger.info(f"SEVERANCE: {user.get_display_name()} gains enhanced movement (SEVERANCE status active)")
        
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Partition during combat phase."""
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return
            
        # Show partition animation if UI available
        if ui and hasattr(ui, 'renderer'):
            # Partition animation - protective barrier forming
            partition_animation = ['[', '[[', '[[[', '[[', '[']
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                partition_animation,
                4,  # Blue color for protection
                0.12
            )
        
        # Apply new partition shield system
        target.partition_shield_active = True
        target.partition_shield_caster = user  # Reference to DERELIST who cast this
        target.partition_shield_duration = 3
        target.partition_shield_emergency_active = False  # Not in emergency mode yet
        target.partition_shield_blocked_fatal = False  # Haven't blocked fatal damage yet
        target.prt = 1  # Set partition stat to 1 for universal damage reduction
        
        message_log.add_message(
            f"{target.get_display_name()} gains partition shield (blocks 1 damage) for 3 turns!",
            MessageType.ABILITY
        )
        
        logger.info(f"PARTITION EXECUTED: {user.get_display_name()} applies partition shield to {target.get_display_name()}")
        
        # Note: Severance passive bonus already applied during planning phase