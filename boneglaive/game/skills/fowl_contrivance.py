#!/usr/bin/env python3
"""
Skills specific to the FOWL_CONTRIVANCE unit type.
This module contains all passive and active abilities for FOWL_CONTRIVANCE units.
Reworked as a mechanical peacock rail artillery platform.
"""

from typing import Optional, TYPE_CHECKING, List, Dict, Tuple, Set
import random
import time
from boneglaive.utils.animation_helpers import sleep_with_animation_speed

import curses

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.game.map import TerrainType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.constants import UnitType, CRITICAL_HEALTH_PERCENT

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class RailGenesis(PassiveSkill):
    """
    Passive skill for FOWL_CONTRIVANCE.
    The first FOWL_CONTRIVANCE to deploy establishes a permanent rail network
    accessible only to mechanical rail units.
    """
    
    def __init__(self):
        super().__init__(
            name="Rail Genesis",
            key="R",
            description="The first FOWL_CONTRIVANCE to deploy establishes a permanent rail network accessible only to mechanical rail units."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        """
        Generate rail network when first FOWL_CONTRIVANCE enters the map.
        """
        if game and not game.map.has_rails():
            # First FOWL_CONTRIVANCE generates the rail network
            game.map.generate_rail_network()
            
            message_log.add_message(
                f"{user.get_display_name()} establishes a rail network across the battlefield!",
                MessageType.ABILITY,
                player=user.player
            )
    
    def handle_unit_death(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """
        Handle death explosion when FOWL_CONTRIVANCE dies.
        Deals 4 damage to enemy units standing on rail tiles.
        """
        if not game or not game.map.has_rails():
            return
        
        rail_positions = game.map.get_rail_positions()
        units_hit = 0
        total_damage = 0
        
        # Check each rail position for enemy units
        for rail_y, rail_x in rail_positions:
            unit = game.get_unit_at(rail_y, rail_x)
            
            # Only damage enemy units (not allies)
            if unit and unit.is_alive() and unit.player != user.player:
                damage = 4  # Fixed death explosion damage
                
                # Store previous HP for critical health check
                previous_hp = unit.hp
                
                # Apply damage
                unit.hp = max(0, unit.hp - damage)
                units_hit += 1
                total_damage += damage
                
                # Log the damage
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability="Rail Genesis Death Explosion",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)
        
        if units_hit > 0:
            message_log.add_message(
                f"{user.get_display_name()}'s death explosion strikes {units_hit} {'unit' if units_hit == 1 else 'units'} on rails for {total_damage} damage!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()}'s rail network remains intact despite its destruction!",
                MessageType.ABILITY,
                player=user.player
            )


class GaussianDuskSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Charges a devastating rail gun shot that pierces everything in its path.
    Two-phase skill: charging turn, then firing turn.
    """
    
    def __init__(self):
        super().__init__(
            name="Gaussian Dusk",
            key="G",
            description="Charges a devastating rail gun shot that pierces everything in its path. Must charge for 1 turn before firing.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=999,  # Entire map range
            area=0
        )
        self.damage = 12
        self.charging = False
        self.charge_direction = None
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # If already charging, can always use this skill to fire (no cooldown check needed)
        if hasattr(user, 'charging_status') and user.charging_status:
            return True

        # Otherwise, normal cooldown validation for charging
        if not super().can_use(user, target_pos, game):
            return False

        # For initial charging, need a direction
        if not target_pos:
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Gaussian Dusk skill for execution."""
        
        # Check if already charging - if so, this is the firing turn
        if hasattr(user, 'charging_status') and user.charging_status:
            # Fire automatically - use stored direction
            user.skill_target = user.gaussian_charge_direction
            user.selected_skill = self
            return True
        
        # Otherwise, this is the charging turn
        if not self.can_use(user, target_pos, game):
            return False

        # Calculate direction from user position to target
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x
            
        target_y, target_x = target_pos
        
        # Calculate direction vector
        dy = target_y - source_y
        dx = target_x - source_x
        
        # Normalize to one of 8 directions
        if abs(dx) > abs(dy):
            direction = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            direction = (1 if dy > 0 else -1, 0)
        else:
            direction = (1 if dy > 0 else -1, 1 if dx > 0 else -1)

        # Store the direction for execution
        user.skill_target = direction
        user.selected_skill = self
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Gaussian Dusk skill during turn resolution."""
        
        # Check if this is the charging turn or firing turn
        if not hasattr(user, 'charging_status') or not user.charging_status:
            # This is the charging turn - set up charging
            direction = target_pos  # target_pos is the direction vector
            
            # Set charging status effect
            user.charging_status = True
            user.gaussian_charge_direction = direction
            
            # Set visual indicator
            user.gaussian_dusk_indicator = direction

            # Play charging animation
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Get the charging animation sequence
                charge_animation = ui.asset_manager.get_skill_animation_sequence('gaussian_charge')
                if not charge_animation:
                    charge_animation = ['=', '=', '=', '=', '=', '=', '=']  # Fallback
                
                # Show charging animation at user's position
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    charge_animation,
                    6,  # Yellow color for charging
                    0.3  # Longer duration for dramatic charging effect
                )

            # Log that charging has started
            message_log.add_message(
                f"{user.get_display_name()} charges its rail cannon with electromagnetic energy!",
                MessageType.ABILITY,
                player=user.player
            )
            
            # DO NOT set cooldown yet - only after firing
            return True
        
        # This is the firing turn - clear charging state and fire
        user.charging_status = False
        user.gaussian_dusk_indicator = None
        
        # NOW set the cooldown after firing
        self.current_cooldown = self.cooldown
        
        # Log that firing has started
        message_log.add_message(
            f"{user.get_display_name()}'s rail cannon fires a hypersonic projectile!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Get firing direction
        direction = target_pos  # target_pos is actually the direction vector
        dy, dx = direction
        
        # Calculate all positions in the firing line
        positions_in_line = []
        y, x = user.y, user.x
        
        # Trace the line across the entire map
        while 0 <= y + dy < game.map.height and 0 <= x + dx < game.map.width:
            y += dy
            x += dx
            positions_in_line.append((y, x))
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()}'s rail cannon unleashes devastating energy across the battlefield!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Track units hit and damage dealt
        units_hit = 0
        total_damage = 0
        terrain_destroyed = 0
        
        # Apply effects to all positions in the line
        for pos_y, pos_x in positions_in_line:
            # Check for destructible terrain - hypersonic projectile destroys everything in its path
            terrain = game.map.get_terrain_at(pos_y, pos_x)
            destructible_terrain = [
                TerrainType.LIMESTONE,     # Limestone formations
                TerrainType.PILLAR,        # Limestone pillars
                TerrainType.MARROW_WALL,   # Marrow Dike walls
                TerrainType.FURNITURE,     # Generic furniture
                TerrainType.COAT_RACK,     # Coat racks
                TerrainType.OTTOMAN,       # Ottoman seating
                TerrainType.CONSOLE,       # Console tables
                TerrainType.DEC_TABLE      # Decorative tables
            ]
            
            if terrain in destructible_terrain:
                game.map.set_terrain_at(pos_y, pos_x, TerrainType.EMPTY)
                terrain_destroyed += 1
            
            # Check for units to damage
            unit = game.get_unit_at(pos_y, pos_x)
            
            # Damage all enemy units in path (ignores defense completely)
            if unit and unit.is_alive() and unit.player != user.player:
                damage = self.damage  # Fixed 12 damage, ignores defense
                
                # Store previous HP for critical health check
                previous_hp = unit.hp
                
                # Apply damage
                unit.hp = max(0, unit.hp - damage)
                units_hit += 1
                total_damage += damage
                
                # Log the damage
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability="Gaussian Dusk",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)
        
        # Log results
        if units_hit > 0:
            message_log.add_message(
                f"The projectile pierces {units_hit} {'target' if units_hit == 1 else 'targets'} for {total_damage} damage!",
                MessageType.ABILITY,
                player=user.player
            )
            
        if terrain_destroyed > 0:
            message_log.add_message(
                f"The projectile destroys {terrain_destroyed} terrain {'feature' if terrain_destroyed == 1 else 'features'}!",
                MessageType.ABILITY,
                player=user.player
            )
        
        if units_hit == 0 and terrain_destroyed == 0:
            message_log.add_message(
                "The rail cannon's beam finds no targets!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play rail cannon firing animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get charging animation
            charging_animation = ui.asset_manager.get_skill_animation_sequence('gaussian_dusk_charging')
            if not charging_animation:
                charging_animation = ['~', '=', '*', '+']
            
            # Show charging effect at user position briefly
            for frame in charging_animation[:4]:  # Short charging flash
                ui.renderer.draw_tile(user.y, user.x, frame, 4)  # Blue color
                ui.renderer.refresh()
                sleep_with_animation_speed(0.03)
            
            # Get firing animation
            firing_animation = ui.asset_manager.get_skill_animation_sequence('gaussian_dusk_firing')
            if not firing_animation:
                firing_animation = ['*', '#', '@', '~', '.']
            
            # Animate the beam along the entire path
            for i, (pos_y, pos_x) in enumerate(positions_in_line):
                frame_idx = min(i, len(firing_animation) - 1)
                symbol = firing_animation[frame_idx]
                color = 1 if i % 2 == 0 else 6  # Alternating red/yellow
                
                ui.renderer.draw_tile(pos_y, pos_x, symbol, color)
                if i % 3 == 0:  # Refresh every few tiles for smooth animation
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.01)
            
            ui.renderer.refresh()
            sleep_with_animation_speed(0.1)
            
            # Redraw the board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class BigArcSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Launches explosive mortar shells in a 3x3 area. Indirect fire ignores line of sight.
    """
    
    def __init__(self):
        super().__init__(
            name="Big Arc",
            key="B",
            description="Launches explosive mortar shells in a 3x3 area. Indirect fire ignores line of sight.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=6,
            area=1  # 3x3 area (center + 1 in each direction)
        )
        self.primary_damage = 8
        self.secondary_damage = 5
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Cannot use while Gaussian Dusk is charging
        if hasattr(user, 'charging_status') and user.charging_status:
            return False

        # Basic validation for cooldown
        if not super().can_use(user, target_pos, game):
            return False

        # Make sure there's a valid position to target
        if not target_pos or not game or not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target position is within range
        y_dist = abs(target_pos[0] - source_y)
        x_dist = abs(target_pos[1] - source_x)

        if max(y_dist, x_dist) > self.range:
            return False

        # Cannot target own tile or adjacent tiles (self-damage protection)
        if max(abs(target_pos[0] - source_y), abs(target_pos[1] - source_x)) <= 1:
            return False

        # Indirect fire - no line of sight required
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Big Arc skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Set the big arc indicator to show the area of effect
        user.big_arc_indicator = target_pos

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} loads mortar shells for artillery barrage!",
            MessageType.ABILITY,
            player=user.player
        )

        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Big Arc skill during turn resolution."""
        # Validate target position
        target_y, target_x = target_pos
        if not game.is_valid_position(target_y, target_x):
            return False

        # Clear the big arc indicator when skill is executed
        user.big_arc_indicator = None
            
        # Generate the area of effect (3x3 area centered on target_pos)
        affected_positions = []
        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                pos_y, pos_x = target_y + dy, target_x + dx
                
                # Check if position is valid
                if game.is_valid_position(pos_y, pos_x):
                    # Determine if this is primary target (center) or secondary
                    is_primary = (dy == 0 and dx == 0)
                    affected_positions.append((pos_y, pos_x, is_primary))
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()}'s mortar barrage rains down!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Track units hit and damage dealt
        units_hit = 0
        total_damage = 0
        
        # Apply damage to all units in the area
        for pos_y, pos_x, is_primary in affected_positions:
            unit = game.get_unit_at(pos_y, pos_x)
            
            # Damage all units in area
            if unit and unit.is_alive():
                # Calculate damage based on position and unit's defense
                base_damage = self.primary_damage if is_primary else self.secondary_damage
                effective_defense = unit.get_effective_stats()['defense']
                damage = max(1, base_damage - effective_defense)
                
                # Store previous HP for critical health check
                previous_hp = unit.hp
                
                # Apply damage
                unit.hp = max(0, unit.hp - damage)
                units_hit += 1
                total_damage += damage
                
                # Log the damage
                damage_type = "primary" if is_primary else "secondary"
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability=f"Big Arc ({damage_type})",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)
        
        # Log results
        if units_hit == 0:
            message_log.add_message(
                "The mortar barrage strikes empty ground!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"Mortar shells strike {units_hit} {'unit' if units_hit == 1 else 'units'} for {total_damage} damage!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play mortar barrage animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get launch animation
            launch_animation = ui.asset_manager.get_skill_animation_sequence('big_arc_launch')
            if not launch_animation:
                launch_animation = ['o', 'O', '0', '*']
            
            # Get impact animation
            impact_animation = ui.asset_manager.get_skill_animation_sequence('big_arc_impact')
            if not impact_animation:
                impact_animation = ['*', '#', '@', '%', '~', '.']
            
            # Show launch from user position
            for frame in launch_animation:
                ui.renderer.draw_tile(user.y, user.x, frame, 6)  # Yellow color
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Show shells arcing overhead (optional visual effect)
            ui.renderer.draw_tile(user.y, user.x, ' ', 1)  # Clear launch position
            
            # Show impact animation on all affected positions
            for frame in impact_animation:
                for pos_y, pos_x, is_primary in affected_positions:
                    color = 1 if is_primary else 3  # Red for primary, yellow for secondary
                    ui.renderer.draw_tile(pos_y, pos_x, frame, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Redraw the board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class FragcrestSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Deploys a directional fragmentation burst that fans out in a cone, 
    firing explosive shrapnel that blasts enemies backward and embeds fragments for ongoing damage.
    """
    
    def __init__(self):
        super().__init__(
            name="Fragcrest",
            key="F",
            description="Deploys a directional fragmentation burst that fans out in a cone, firing explosive shrapnel that blasts enemies backward and embeds fragments for ongoing damage.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=4,
            area=0
        )
        self.primary_damage = 4
        self.secondary_damage = 2
        self.shrapnel_damage = 1
        self.shrapnel_duration = 3
        self.knockback_distance = 2
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Cannot use while Gaussian Dusk is charging
        if hasattr(user, 'charging_status') and user.charging_status:
            return False

        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        
        # Make sure there's a valid target position
        if not target_pos or not game or not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
        
        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x
        
        # Check if target position is within range
        y_dist = abs(target_pos[0] - source_y)
        x_dist = abs(target_pos[1] - source_x)
        
        if max(y_dist, x_dist) > self.range:
            return False
        
        # Check if there's a unit at the target position
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or not target_unit.is_alive():
            return False
        
        # Cannot target self
        if target_unit == user:
            return False
        
        # Requires line of sight to primary target
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False
        
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Fragcrest skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set visual indicator for the cone
        user.fragcrest_indicator = target_pos
        
        # Log that the skill has been queued
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        message_log.add_message(
            f"{user.get_display_name()} unfolds its tail and aims fragmentation burst at {target_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Fragcrest skill during turn resolution."""
        # Clear indicator
        user.fragcrest_indicator = None
        
        # Get primary target
        primary_target = game.get_unit_at(target_pos[0], target_pos[1])
        if not primary_target or not primary_target.is_alive():
            return False
        
        # Calculate cone direction and affected positions
        target_y, target_x = target_pos
        cone_positions = self._calculate_cone_positions(user.y, user.x, target_y, target_x, game)
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()}'s fragmentation burst explodes in a deadly cone!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Track affected units
        affected_units = []
        units_hit = 0
        total_damage = 0
        
        # Apply damage and effects to all units in cone
        for pos_y, pos_x, is_primary in cone_positions:
            unit = game.get_unit_at(pos_y, pos_x)
            
            # Only affect enemy units
            if unit and unit.is_alive() and unit.player != user.player:
                # Calculate damage
                base_damage = self.primary_damage if is_primary else self.secondary_damage
                effective_defense = unit.get_effective_stats()['defense']
                damage = max(1, base_damage - effective_defense)
                
                # Store previous HP for critical health check
                previous_hp = unit.hp
                
                # Apply damage
                unit.hp = max(0, unit.hp - damage)
                units_hit += 1
                total_damage += damage
                affected_units.append(unit)
                
                # Log the damage
                damage_type = "primary" if is_primary else "cone"
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability=f"Fragcrest ({damage_type})",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Apply shrapnel effect (ongoing damage)
                if not hasattr(unit, 'shrapnel_duration'):
                    unit.shrapnel_duration = 0
                unit.shrapnel_duration = max(unit.shrapnel_duration, self.shrapnel_duration)
                
                # Calculate knockback
                self._apply_knockback(user, unit, game)
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)
        
        # Log results
        if units_hit == 0:
            message_log.add_message(
                "The fragmentation burst finds no targets!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"Fragmentation hits {units_hit} {'unit' if units_hit == 1 else 'units'} for {total_damage} damage and embeds shrapnel!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play fragmentation cone animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get fragmentation animation
            frag_animation = ui.asset_manager.get_skill_animation_sequence('fragcrest_burst')
            if not frag_animation:
                frag_animation = ['.', ':', '*', '+', '#', 'x']
            
            # Show tail unfold at user position
            ui.renderer.draw_tile(user.y, user.x, 'V', 6)  # Yellow peacock tail spread
            ui.renderer.refresh()
            sleep_with_animation_speed(0.1)
            
            # Show fragmentation burst spreading through cone
            for frame in frag_animation:
                for pos_y, pos_x, is_primary in cone_positions:
                    color = 1 if is_primary else 3  # Red for primary, yellow for others
                    ui.renderer.draw_tile(pos_y, pos_x, frame, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Show knockback effects for pushed units
            for unit in affected_units:
                if hasattr(unit, 'old_position'):  # If we tracked old positions
                    # Show knockback trail
                    ui.renderer.draw_tile(unit.y, unit.x, '>', 6)  # Direction indicator
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
            
            # Redraw the board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True

    def _calculate_cone_positions(self, user_y: int, user_x: int, target_y: int, target_x: int, game: 'Game') -> List[Tuple[int, int, bool]]:
        """Calculate all positions in the 90-degree cone."""
        positions = []
        
        # Calculate direction vector
        dy = target_y - user_y
        dx = target_x - user_x
        
        # Normalize direction for cone calculation
        if abs(dx) > abs(dy):
            main_dir = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            main_dir = (1 if dy > 0 else -1, 0)
        else:
            main_dir = (1 if dy > 0 else -1, 1 if dx > 0 else -1)
        
        # Generate cone positions
        for range_step in range(1, self.range + 1):
            # Calculate width at this range (cone gets wider with distance)
            width = min(3, 1 + range_step // 2)
            
            # Calculate center position at this range
            center_y = user_y + main_dir[0] * range_step
            center_x = user_x + main_dir[1] * range_step
            
            # Add positions around the center based on width
            for offset in range(-(width//2), (width//2) + 1):
                if main_dir[0] == 0:  # Horizontal cone
                    pos_y = center_y + offset
                    pos_x = center_x
                else:  # Vertical cone
                    pos_y = center_y
                    pos_x = center_x + offset
                
                if game.is_valid_position(pos_y, pos_x):
                    is_primary = (pos_y == target_y and pos_x == target_x)
                    positions.append((pos_y, pos_x, is_primary))
        
        return positions

    def _apply_knockback(self, user: 'Unit', target: 'Unit', game: 'Game') -> None:
        """Apply knockback effect to target unit."""
        # Calculate knockback direction (away from user)
        dy = target.y - user.y
        dx = target.x - user.x
        
        # Normalize direction
        if abs(dx) > abs(dy):
            knock_dir = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            knock_dir = (1 if dy > 0 else -1, 0)
        else:
            knock_dir = (1 if dy > 0 else -1, 1 if dx > 0 else -1)
        
        # Apply knockback
        new_y = target.y + knock_dir[0] * self.knockback_distance
        new_x = target.x + knock_dir[1] * self.knockback_distance
        
        # Check if knockback destination is valid
        if (game.is_valid_position(new_y, new_x) and 
            game.map.is_passable(new_y, new_x) and
            not game.get_unit_at(new_y, new_x)):
            
            target.y = new_y
            target.x = new_x
            
            message_log.add_message(
                f"{target.get_display_name()} is blasted backward by the explosion!",
                MessageType.ABILITY,
                player=target.player
            )