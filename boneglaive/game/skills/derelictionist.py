#!/usr/bin/env python3
"""
Skills specific to the DERELICTIONIST unit type.
This module contains all passive and active abilities for DERELICTIONIST units.

The DERELICTIONIST is a support/healer unit focused on psychological abandonment therapy,
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


# NOTE: These functions are deprecated in favor of game.chess_distance()
# Left for potential legacy compatibility, but should not be used in new code


class Severance(PassiveSkill):
    """
    Passive skill for DERELICTIONIST.
    Allows skill-then-move capability with enhanced range after using skills.
    """
    
    def __init__(self):
        super().__init__(
            name="Severance",
            key="S",
            description="After using a skill, can move with +1 range. Cannot move twice in one turn."
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
            description="Immediately deals piercing damage and clears all status effects. After 3 turns, abreaction deals same damage and clears status effects again.",
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
            
        # Check range first (use move_target if DERELICTIONIST moved first due to Severance)
        source_y, source_x = (user.move_target[0], user.move_target[1]) if user.move_target else (user.y, user.x)
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
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
            f"{user.get_display_name()} prepares to cleanse {target_name}",
            MessageType.ABILITY,
            player=user.player
        )
        
        logger.info(f"VAGAL RUN QUEUED: {user.get_display_name()} targeting {target_name}")
        
        # Severance passive: Apply SEVERANCE status effect for enhanced movement
        if user.type == UnitType.DERELICTIONIST:
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
            
        # Calculate distance-based piercing damage from DERELICTIONIST's effective position
        # (Use move_target if the DERELICTIONIST moved first due to Severance)
        source_y, source_x = (user.move_target[0], user.move_target[1]) if user.move_target else (user.y, user.x)
        distance = game.chess_distance(source_y, source_x, target.y, target.x)
        piercing_damage = min(3, max(0, 6 - distance))  # Max 3 at distance 3, reduced by distance, 0 at distance 7+
        
        # Store the damage/healing amount for abreaction (only if not immune to status effects)
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Vagal Run's abreaction effect due to Stasiality",
                MessageType.ABILITY,
                player=target.player
            )
            # Don't apply the vagal run status effect, but continue with immediate effects
        else:
            target.vagal_run_active = True
            target.vagal_run_caster = user  # Reference to DERELICTIONIST who cast this
            target.vagal_run_duration = 3  # Effect lasts 3 turns
        
        # Apply immediate effect and store abreaction amount (if not immune)
        if distance >= 7:
            # At distance 7+: Heal now and store healing amount for future abreaction heal
            heal_amount = distance - 6
            if not target.is_immune_to_effects():
                target.vagal_run_abreaction_damage = -heal_amount  # Negative value indicates healing for abreaction
            
            if target.hp < target.max_hp:
                # Apply healing using universal heal method
                actual_heal = target.heal(heal_amount, "Vagal Run healing")

                if actual_heal > 0:
                    message_log.add_message(
                        f"{target.get_display_name()} heals for #HEAL_{actual_heal}# HP",
                        MessageType.ABILITY,
                        player=target.player
                    )
                    
                    # Show healing effect on map if UI is available
                    if ui and hasattr(ui, 'renderer'):
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
            
        elif piercing_damage > 0:
            # At close range: Damage now and store damage amount for future abreaction damage
            if not target.is_immune_to_effects():
                target.vagal_run_abreaction_damage = piercing_damage  # Positive value indicates damage for abreaction
            
            actual_damage = target.deal_damage(piercing_damage, can_kill=False)
            
            message_log.add_message(
                f"{user.get_display_name()} rocks {target.get_display_name()}'s vagus nerve for #DAMAGE_{actual_damage}# damage",
                MessageType.ABILITY,
                player=target.player
            )
        else:
            # Medium range (distance 6): No immediate effect, no abreaction
            if not target.is_immune_to_effects():
                target.vagal_run_abreaction_damage = 0
        
        # Clear ALL status effects immediately (even for immune units - this is therapeutic)
        cleared_effects = self._clear_all_status_effects(target)
        
        # Apply derelicted status AFTER clearing effects (only at distance 7+ and not immune)
        if distance >= 7 and not target.is_immune_to_effects():
            target.derelicted = True
            target.derelicted_duration = 1
            
            message_log.add_message(
                f"{target.get_display_name()} becomes anchored by distant abandonment",
                MessageType.WARNING,
                player=target.player
            )
            
            # Show dereliction animation - becoming anchored/bolted down
            if ui and hasattr(ui, 'renderer'):
                derelict_animation = ['|', 'T', '+', '#', '#', '+', '*', 'H', 'X', '&']  # Structure forming, then anchored abandonment
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    derelict_animation,
                    1,  # Red color for abandonment trauma
                    0.6  # Slower for heavy, deliberate immobilization
                )
        
        # Show execution animation if UI available
        if ui and hasattr(ui, 'renderer'):
            # Vagal run animation - trauma cracking through the nerve pathway
            vagal_animation = ['|', '|', '|', '|', '|', '/', '\\', '~', '~', '~']  # Nerve pathway fracturing
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                vagal_animation,
                6,  # Yellow color for trauma processing
                0.4  # Much slower for visibility
            )
        
        # Generate message about cleared effects
        if cleared_effects:
            effects_text = ", ".join(cleared_effects)
            message_log.add_message(
                f"{target.get_display_name()}'s Vagal Run sloughs off {effects_text}",
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
            cleared_effects.append("Site Inspection Partial")
            
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
            
        # Don't clear severance_active as it's related to DERELICTIONIST's own passive
        
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
            description="Push ally 4 tiles away in straight line. Ally heals for distance from DERELICTIONIST and becomes immobilized for 1 turn",
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
            
        # Check range first (use move_target if DERELICTIONIST moved first due to Severance)
        source_y, source_x = (user.move_target[0], user.move_target[1]) if user.move_target else (user.y, user.x)
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
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
            # Calculate push direction from current DERELICTIONIST position
            dy = target.y - user.y
            dx = target.x - user.x
            
            # Normalize direction
            if dy != 0:
                dy = 1 if dy > 0 else -1
            if dx != 0:
                dx = 1 if dx > 0 else -1
            
            # Store push direction on the target unit for execution phase
            target.derelict_push_direction = (dy, dx)
            
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
            f"{user.get_display_name()} prepares to derelict {target_name}",
            MessageType.ABILITY,
            player=user.player
        )
        
        logger.info(f"DERELICT QUEUED: {user.get_display_name()} targeting {target_name} with direction ({dy},{dx})")
        
        # Severance passive: Apply SEVERANCE status effect for enhanced movement
        if user.type == UnitType.DERELICTIONIST:
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
        
        # Show conveyance animation if UI available
        if ui and hasattr(ui, 'renderer'):
            # Conveyance animation - abstract transportation/displacement
            conveyance_animation = ['o', 'o', 'O', '~', '~', '~', '*', '+', '=', '0']  # Being conveyed away
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                conveyance_animation,
                3,  # Red color for therapeutic displacement
                0.4  # Same timing as other animations
            )
        
        # Try to push 4 tiles in that direction
        push_distance = 0
        original_y, original_x = target.y, target.x  # Store original position
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
        
        # Check if target is immune to displacement effects (GRAYMAN with Stasiality)
        if target.is_immune_to_effects():
            # Immune to push, so stay at original position
            final_y, final_x = target.y, target.x
            push_distance = 0
            message_log.add_message(
                f"{target.get_display_name()} is immune to Derelict's displacement due to Stasiality",
                MessageType.ABILITY,
                player=target.player
            )
        else:
            # Move target to final position
            if push_distance > 0:
                target.y = final_y
                target.x = final_x
            
            # Show push result message with coordinates
            if push_distance > 0:
                message_log.add_message(
                    f"{target.get_display_name()} was pushed {push_distance} tiles from ({original_y}, {original_x}) to ({final_y}, {final_x})",
                    MessageType.ABILITY,
                    player=target.player
                )
        
        # Calculate healing based on final distance from DERELICTIONIST's effective position
        # (Use move_target if the DERELICTIONIST moved first due to Severance)
        source_y, source_x = (user.move_target[0], user.move_target[1]) if user.move_target else (user.y, user.x)
        distance_to_derelictionist = game.chess_distance(final_y, final_x, source_y, source_x)
            
        heal_amount = distance_to_derelictionist
        
        # Apply healing if needed
        if target.hp < target.max_hp:
            # Apply healing using universal heal method (it handles curse prevention)
            actual_heal = target.heal(heal_amount, "Derelict distance healing")

            if actual_heal > 0:
                    message_log.add_message(
                        f"{target.get_display_name()} heals for #HEAL_{actual_heal}# HP",
                        MessageType.ABILITY,
                        player=target.player
                    )

                    # Show healing effect on map if UI is available
                    if ui and hasattr(ui, 'renderer'):
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
        
        # Apply Derelicted status (immobilization for 1 turn) - only if not immune
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Derelict's dereliction due to Stasiality",
                MessageType.ABILITY,
                player=target.player
            )
        else:
            target.derelicted = True
            target.derelicted_duration = 1
            
            message_log.add_message(
                f"{target.get_display_name()} becomes anchored by abandonment",
                MessageType.WARNING,
                player=target.player
            )
            
            # Show dereliction animation - becoming anchored/bolted down
            if ui and hasattr(ui, 'renderer'):
                derelict_animation = ['|', 'T', '+', '#', '#', '+', '*', 'H', 'X', '&']  # Structure forming, then anchored abandonment
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    derelict_animation,
                    1,  # Red color for abandonment trauma
                    0.6  # Slower for heavy, deliberate immobilization
                )
        
        # Clean up stored direction data
        if hasattr(target, 'derelict_push_direction'):
            delattr(target, 'derelict_push_direction')
        
        logger.info(f"DERELICT EXECUTED: {user.get_display_name()} pushed {target.get_display_name()} {push_distance} tiles, healed {heal_amount} (distance: {distance_to_derelictionist}), applied immobilization")
        
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
            description="Grant ally shield that blocks 1 damage from all sources for 3 turns. If unit would take fatal damage, completely blocks all damage that turn, then ends effect, teleports DERELICTIONIST 4 tiles away, and applies Derelicted",
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
            
        # Check range first (use move_target if DERELICTIONIST moved first due to Severance)
        source_y, source_x = (user.move_target[0], user.move_target[1]) if user.move_target else (user.y, user.x)
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
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
            f"{user.get_display_name()} prepares to partition {target_name}",
            MessageType.ABILITY,
            player=user.player
        )
        
        logger.info(f"PARTITION QUEUED: {user.get_display_name()} targeting {target_name}")
        
        # Severance passive: Apply SEVERANCE status effect for enhanced movement
        if user.type == UnitType.DERELICTIONIST:
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
        
        # Check if target is immune to effects (GRAYMAN with Stasiality)
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Partition due to Stasiality",
                MessageType.ABILITY,
                player=target.player
            )
            return
            
        # Show partition animation if UI available
        if ui and hasattr(ui, 'renderer'):
            # Partition animation - mental barriers forming around the mind
            partition_animation = ['(', '[', '{', '|', '||', '#', 'W', ',', ')', ']']  # Mental barriers solidifying
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                partition_animation,
                4,  # Blue color for protection
                0.4  # Slow, deliberate barrier formation
            )
        
        # Apply new partition shield system
        target.partition_shield_active = True
        target.partition_shield_caster = user  # Reference to DERELICTIONIST who cast this
        target.partition_shield_duration = 3
        target.partition_shield_emergency_active = False  # Not in emergency mode yet
        target.partition_shield_blocked_fatal = False  # Haven't blocked fatal damage yet
        target.prt = 1  # Set partition stat to 1 for universal damage reduction
        
        message_log.add_message(
            f"{target.get_display_name()} is partitioned from battle",
            MessageType.ABILITY,
            player=target.player
        )
        
        logger.info(f"PARTITION EXECUTED: {user.get_display_name()} applies partition shield to {target.get_display_name()}")
        
        # Note: Severance passive bonus already applied during planning phase