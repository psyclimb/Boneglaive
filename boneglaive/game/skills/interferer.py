#!/usr/bin/env python3
"""
Skills specific to the INTERFERER unit type.
This module contains all passive and active abilities for INTERFERER units.
"""

import curses
import time
import random
from typing import Optional, TYPE_CHECKING
from boneglaive.utils.animation_helpers import sleep_with_animation_speed

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class NeutronIlluminant(PassiveSkill):
    """
    Passive skill for INTERFERER.
    On successful attack, causes radiation sickness in directional pattern.
    Cardinal attacks radiate diagonally, diagonal attacks radiate cardinally.
    """
    
    def __init__(self):
        super().__init__(
            name="Neutron Illuminant",
            key="N",
            description="On attack, causes radiation sickness around the INTERFERER. Cardinal attacks radiate diagonally, diagonal attacks radiate cardinally. 1 damage/turn for 2 turns per stack."
        )
        self.current_cooldown = 0
        self.cooldown = 0  # No cooldown
        
    def apply_passive(self, user: 'Unit', game=None) -> None:
        """Apply effects of the passive skill."""
        # This is handled by the game engine when attacks are processed
        pass
    
    def tick_cooldown(self) -> None:
        """Reduce cooldown by 1 turn."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
    
    def can_trigger(self) -> bool:
        """Check if the passive can trigger (not on cooldown)."""
        return self.current_cooldown == 0
    
    def trigger_flash_effect(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Trigger the neutron flash animation effect that always plays on INTERFERER attacks."""
        # Always show the flash effect regardless of radiation sickness application
        if ui and hasattr(ui, 'renderer'):
            # Flash animation at the INTERFERER's position
            flash_animation = ['*', '✦', '※', '✦', '*']
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                flash_animation,
                7,  # White/bright color for the flash
                0.04  # Faster flash duration
            )
            
            # Additional radiating flash effect around the INTERFERER
            radiation_positions = self._get_radiation_positions(user, target_pos)
            flash_radiation_animation = ['*', '+', '.']
            for pos in radiation_positions:
                y, x = pos
                if game.is_valid_position(y, x):
                    ui.renderer.animate_attack_sequence(
                        y, x,
                        flash_radiation_animation,
                        6,  # Yellow color for radiation flash
                        0.03  # Faster radiating flash
                    )

    def _get_radiation_positions(self, user: 'Unit', target_pos: tuple) -> list:
        """Get radiation positions based on attack direction."""
        # Calculate attack direction
        dy = target_pos[0] - user.y
        dx = target_pos[1] - user.x
        
        # Normalize direction for pattern determination
        is_cardinal = (dy == 0 or dx == 0)
        
        if is_cardinal:
            # Cardinal attack -> radiate diagonally around INTERFERER
            return [
                (user.y - 1, user.x - 1),  # Up-left of INTERFERER
                (user.y - 1, user.x + 1),  # Up-right of INTERFERER
                (user.y + 1, user.x - 1),  # Down-left of INTERFERER
                (user.y + 1, user.x + 1)   # Down-right of INTERFERER
            ]
        else:
            # Diagonal attack -> radiate cardinally around INTERFERER
            return [
                (user.y - 1, user.x),      # Up from INTERFERER
                (user.y + 1, user.x),      # Down from INTERFERER
                (user.y, user.x - 1),      # Left from INTERFERER
                (user.y, user.x + 1)       # Right from INTERFERER
            ]

    def trigger_radiation(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Trigger radiation sickness in directional pattern around the INTERFERER."""
        if not self.can_trigger():
            return
            
        # Set cooldown (0, so always triggers)
        self.current_cooldown = self.cooldown
        
        # Get radiation positions
        radiation_positions = self._get_radiation_positions(user, target_pos)
        
        # Apply radiation to valid positions
        affected_units = []
        for pos in radiation_positions:
            y, x = pos
            if not game.is_valid_position(y, x):
                continue
                
            target = game.get_unit_at(y, x)
            if target and target.player != user.player and target.is_alive():
                # Apply radiation sickness
                if not hasattr(target, 'radiation_stacks'):
                    target.radiation_stacks = []
                
                # Add new radiation stack (2 turns duration)
                target.radiation_stacks.append(2)
                affected_units.append(target)
        
        # Log radiation effect only if units were affected
        if affected_units:
            message_log.add_message(
                f"Neutron radiation spreads from the impact",
                MessageType.ABILITY,
                player=user.player
            )


class NeuralShuntSkill(ActiveSkill):
    """
    Active skill for INTERFERER.
    Neural disruption causes target to perform random actions.
    """
    
    def __init__(self):
        super().__init__(
            name="Neural Shunt",
            key="N",
            description="Neural disruption attack (range 1). Deals 8 damage and causes target to perform random actions for 2 turns.",
            target_type=TargetType.ENEMY,
            cooldown=4,
            range_=1
        )
        self.damage = 7
        self.effect_duration = 2
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check if target is an enemy unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player:
            return False
            
        # Check range
        from_y = user.y
        from_x = user.x
        if user.move_target:
            from_y, from_x = user.move_target
            
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        target = game.get_unit_at(target_pos[0], target_pos[1])
        message_log.add_message(
            f"{user.get_display_name()} coordinates a neural interference triangulation",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Neural Shunt skill."""
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
        
        
        # Show complex neural shunt animation
        if ui and hasattr(ui, 'renderer'):
            # Stage 1: Three radio wave streams converge on target from different directions
            # Get three positions around the target (avoiding the INTERFERER's position)
            convergence_positions = []
            directions = [(-1, -1), (-1, 1), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]  # All 8 directions except up
            
            # Pick 3 directions that don't have the INTERFERER
            for dy, dx in directions:
                wave_y = target.y + dy * 2  # Position 2 tiles away from target
                wave_x = target.x + dx * 2
                # Skip if this would be the INTERFERER's position or invalid
                if ((wave_y, wave_x) != (user.y, user.x) and 
                    game.is_valid_position(wave_y, wave_x) and 
                    len(convergence_positions) < 3):
                    convergence_positions.append((wave_y, wave_x, dy, dx))
            
            # Stage 1: Show radio waves building at the three positions
            wave_buildup = ['~', '≈', '∼']
            for i, frame in enumerate(wave_buildup):
                for pos_y, pos_x, _, _ in convergence_positions:
                    ui.renderer.draw_tile(pos_y, pos_x, frame, 6)  # Yellow for radio waves
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)
                
                # Clear the wave positions
                for pos_y, pos_x, _, _ in convergence_positions:
                    # Restore original terrain
                    terrain_type = game.map.get_terrain_at(pos_y, pos_x)
                    terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                    if hasattr(ui, 'asset_manager'):
                        terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                        terrain_color = 1 if terrain_name == 'empty' else 11  # Simple color scheme
                        ui.renderer.draw_tile(pos_y, pos_x, terrain_tile, terrain_color)
            
            # Stage 2: Waves converge toward target
            convergence_frames = ['*', '+', '>', '<', '^', 'v']
            for i, frame_char in enumerate(convergence_frames):
                for pos_y, pos_x, dy, dx in convergence_positions:
                    # Calculate intermediate position closer to target
                    progress = (i + 1) / len(convergence_frames)
                    inter_y = int(pos_y + dy * progress)
                    inter_x = int(pos_x + dx * progress)
                    
                    if game.is_valid_position(inter_y, inter_x) and (inter_y, inter_x) != (target.y, target.x):
                        ui.renderer.draw_tile(inter_y, inter_x, frame_char, 6)  # Yellow
                
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
                
                # Clear intermediate positions
                for pos_y, pos_x, dy, dx in convergence_positions:
                    progress = (i + 1) / len(convergence_frames)
                    inter_y = int(pos_y + dy * progress)
                    inter_x = int(pos_x + dx * progress)
                    
                    if game.is_valid_position(inter_y, inter_x) and (inter_y, inter_x) != (target.y, target.x):
                        terrain_type = game.map.get_terrain_at(inter_y, inter_x)
                        terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                        if hasattr(ui, 'asset_manager'):
                            terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                            terrain_color = 1 if terrain_name == 'empty' else 11
                            ui.renderer.draw_tile(inter_y, inter_x, terrain_tile, terrain_color)
            
            # Stage 3: Neural surge flash down nervous system
            if hasattr(ui, 'asset_manager'):
                original_unit_tile = ui.asset_manager.get_unit_tile(target.type)
                
                # Neural surge effect - rapid flashing through the nervous system
                surge_frames = ['|', '\\', '/', '-', '|', '\\', '/', '-']
                surge_colors = [1, 5, 6, 7, 1, 5, 6, 7]  # Red, yellow, white alternating
                
                for i, (frame, color) in enumerate(zip(surge_frames, surge_colors)):
                    ui.renderer.draw_tile(target.y, target.x, frame, color)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.03)  # Very fast neural surge
            
            # Stage 4: Confusion flashing
            confusion_frames = ['?', original_unit_tile, '?', original_unit_tile, '?']
            confusion_colors = [6, 3 if target.player == 1 else 4, 6, 3 if target.player == 1 else 4, 6]
            confusion_durations = [0.1, 0.1, 0.1, 0.1, 0.1]
            
            ui.renderer.flash_tile(target.y, target.x, confusion_frames, confusion_colors, confusion_durations)
            
            # Final restoration
            ui.renderer.draw_tile(target.y, target.x, original_unit_tile, 3 if target.player == 1 else 4)
            ui.renderer.refresh()
        
        # Apply damage
        damage = max(1, self.damage - target.defense)
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Neural Shunt",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Show damage number
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{damage}"
            for i in range(3):
                ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, attrs)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
        
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="neural_shunt", ui=ui)
        else:
            # Check for critical health
            game.check_critical_health(target, user, previous_hp, ui)
            
            # Apply neural shunt effect if target survives and not immune
            if target.is_immune_to_effects():
                message_log.add_message(
                    f"{target.get_display_name()} is immune to Neural Shunt due to Stasiality",
                    MessageType.ABILITY,
                    player=target.player,
                    target_name=target.get_display_name()
                )
            else:
                target.neural_shunt_affected = True
                target.neural_shunt_duration = self.effect_duration
                
                message_log.add_message(
                    f"{target.get_display_name()}'s actions become erratic",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=target.get_display_name()
                )
        
        # Trigger Neutron Illuminant flash and radiation effects
        if user.passive_skill and user.passive_skill.name == "Neutron Illuminant":
            # Always trigger flash effect for Neural Shunt attacks
            user.passive_skill.trigger_flash_effect(user, target_pos, game, ui)
            # Also trigger radiation effect (only applies if enemies are in range)
            user.passive_skill.trigger_radiation(user, target_pos, game, ui)
        
        return True


class KarrierRaveSkill(ActiveSkill):
    """
    Active skill for INTERFERER.
    Becomes untargetable and next attack strikes 3 times.
    """
    
    def __init__(self):
        super().__init__(
            name="Karrier Rave",
            key="K",
            description="Phase out of reality for 1 turn. Become untargetable, but cannot attack. Next attack after phasing strikes 3 times.",
            target_type=TargetType.SELF,
            cooldown=6,
            range_=0
        )
        self.effect_duration = 2
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
            
        # For self-targeted skills, use current position
        if user.move_target:
            target_pos = user.move_target
        else:
            target_pos = (user.y, user.x)
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        message_log.add_message(
            f"{user.get_display_name()} synchronizes with the karrier wave transmission",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Karrier Rave skill."""
        message_log.add_message(
            f"{user.get_display_name()} rides the karrier wave out of phase",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Show animation
        if ui and hasattr(ui, 'renderer'):
            phase_animation = ['φ', '~', '*', '·', ' ']
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                phase_animation,
                7,  # White color
                0.2
            )
        
        # Apply karrier rave effect
        user.carrier_rave_active = True
        user.carrier_rave_duration = self.effect_duration
        user.carrier_rave_strikes_ready = False  # Will be set to True when effect ends
        
        message_log.add_message(
            f"{user.get_display_name()} becomes untargetable",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True


class ScalarNodeSkill(ActiveSkill):
    """
    Active skill for INTERFERER.
    Places invisible traps that deal damage when triggered.
    """
    
    def __init__(self):
        super().__init__(
            name="Scalar Node",
            key="S",
            description="Place invisible trap on empty terrain (range 3). Triggers when enemy ends turn on tile, dealing 12 damage. Silent deployment and activation.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3
        )
        self.damage = 12
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Must target empty, passable terrain
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False
            
        # Check range
        from_y = user.y
        from_x = user.x
        if user.move_target:
            from_y, from_x = user.move_target
            
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Silent deployment - no message log entry
        
        self.current_cooldown = self.cooldown
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Scalar Node placement."""
        # Silent deployment - no message log entries
        
        # Create scalar node tracking in game
        if not hasattr(game, 'scalar_nodes'):
            game.scalar_nodes = {}
            
        # Place the node
        game.scalar_nodes[target_pos] = {
            'owner': user,
            'damage': self.damage,
            'active': True
        }
        
        # No visual indication - completely invisible
        # No animation or message log entries for psychological warfare
        
        return True