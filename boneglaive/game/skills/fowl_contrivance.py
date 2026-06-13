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

try:
    import curses
except ImportError:
    curses = None

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
    
    def apply_passive(self, user: 'Unit', game=None, ui=None) -> None:
        """
        Generate rail network when first FOWL_CONTRIVANCE enters the map.
        Rails are hidden during setup phase to prevent strategic information leakage.
        """
        if game and not game.map.has_rails():
            # Check if we're in setup phase - if so, delay rail creation until game starts
            if hasattr(game, 'setup_phase') and game.setup_phase:
                # During setup, don't create rails yet to prevent revealing FOWL_CONTRIVANCE presence
                # Rails will be created when the game starts (see engine.py setup completion)
                return
            
            # First FOWL_CONTRIVANCE generates the rail network (only when game is active)
            game.map.generate_rail_network()
            
            message_log.add_message(
                f"{user.get_display_name()} establishes a rail network across the battlefield",
                MessageType.ABILITY,
                player=user.player
            )
    
    def handle_unit_death(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """
        Handle death explosion when FOWL_CONTRIVANCE dies.
        Deals 6 damage to enemy units standing on rail tiles.
        Applies Shrapnel to enemy units adjacent to rails.
        """
        if not game or not game.map.has_rails():
            return

        rail_positions = game.map.get_rail_positions()
        units_hit = 0
        total_damage = 0

        # Check each rail position for enemy units
        for rail_y, rail_x in rail_positions:
            unit = game.get_unit_at(rail_y, rail_x)

            # Only damage enemy units (not allies, not FOWL_CONTRIVANCE)
            if unit and unit.is_alive() and unit.player != user.player and not (
                hasattr(unit, 'type') and unit.type == UnitType.FOWL_CONTRIVANCE
            ):
                damage = 6  # Fixed death explosion damage (buffed from 4)
                
                # Store previous HP for critical health check
                previous_hp = unit.hp
                
                # Apply damage
                unit.hp = max(0, unit.hp - damage)
                units_hit += 1
                total_damage += damage
                
                # Show impact animation and damage number (immediate for death explosion)
                if ui and hasattr(ui, 'renderer'):
                    # Play impact animation first
                    if hasattr(ui, 'asset_manager'):
                        impact_animation = ui.asset_manager.get_skill_animation_sequence('rail_explosion_impact')
                        if not impact_animation:
                            impact_animation = ['!', '@', '#', '*', '+', '.']  # Fallback
                        
                        # Animate impact at unit position
                        ui.renderer.animate_attack_sequence(
                            unit.y, unit.x,
                            impact_animation,
                            4,  # Blue color for rail explosion
                            0.1  # Quick explosion effect
                        )
                    
                    # Then show damage numbers
                    damage_text = f"-{damage}"
                    
                    # Make damage text more prominent with flashing effect
                    for i in range(3):
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                        attrs = (curses.A_BOLD if curses else 0) if i % 2 == 0 else 0
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                    
                    # Final damage display (stays visible a bit longer)
                    ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, (curses.A_BOLD if curses else 0))
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.2)
                
                # Log the damage
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability="Rail Genesis Death Explosion (on-rail)",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)

        # Check if this was the last FOWL CONTRIVANCE - if so, remove rails
        remaining_fowl = sum(1 for u in game.units
                            if u.is_alive() and
                            hasattr(u, 'type') and
                            u.type == UnitType.FOWL_CONTRIVANCE)

        if remaining_fowl == 0:
            # Last FOWL CONTRIVANCE destroyed - remove rail network
            game.map.remove_rail_network()
            message_log.add_message(
                "The rail network collapses and vanishes from the battlefield",
                MessageType.ABILITY,
                player=user.player
            )

        # Note: Individual unit damage messages are already shown above, no summary needed


class GaussianDuskSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Fires a devastating rail gun shot that pierces everything in its path.
    Can only fire in cardinal directions (N, S, E, W).
    """

    def __init__(self):
        super().__init__(
            name="Gaussian Dusk",
            key="G",
            description="Fires a devastating rail gun shot in a cardinal direction.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=999,  # Entire map range
            area=0
        )
        self.damage = 9
        self.recharge_duration = 0  # No recharge period
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Cannot use while recharging
        if hasattr(user, 'gaussian_dusk_recharge') and user.gaussian_dusk_recharge > 0:
            return False

        # Normal cooldown validation
        if not super().can_use(user, target_pos, game):
            return False

        # Need a target position to determine direction
        if not target_pos:
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Gaussian Dusk skill for execution."""

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

        # Snap to nearest cardinal direction only (N, S, E, W)
        # No diagonals allowed
        if abs(dx) > abs(dy):
            # Horizontal direction dominates
            direction = (0, 1 if dx > 0 else -1)  # East or West
        else:
            # Vertical direction dominates
            direction = (1 if dy > 0 else -1, 0)  # South or North

        # Store the direction for execution
        user.skill_target = direction
        user.selected_skill = self

        # Set cooldown immediately
        self.current_cooldown = self.cooldown

        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Gaussian Dusk skill during turn resolution."""

        # Get firing direction (target_pos is the direction vector from use())
        direction = target_pos
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
            f"{user.get_display_name()}'s rail cannon unleashes devastating energy across the battlefield",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Track units hit and damage dealt
        units_hit = 0
        total_damage = 0
        damaged_units = []  # Store units and damage for display after animation

        # Apply damage to all positions in the line
        for pos_y, pos_x in positions_in_line:
            # Check for units to damage
            unit = game.get_unit_at(pos_y, pos_x)

            # Damage all enemy units in path with Gaussian curve based on HP%
            if unit and unit.is_alive() and unit.player != user.player:
                from boneglaive.game.upgrades import UpgradeManager
                is_upgraded = UpgradeManager.is_skill_upgraded(user, "Gaussian Dusk")

                # Calculate damage based on HP percentage (Gaussian curve peaking at 50%)
                hp_percent = unit.hp / unit.max_hp

                # Gaussian damage curve: peaks at 50% HP
                if hp_percent >= 0.875:  # 87.5-100%
                    damage = 5
                elif hp_percent >= 0.625:  # 62.5-87.5%
                    damage = 7
                elif hp_percent >= 0.375:  # 37.5-62.5%
                    damage = 9  # Peak damage at ~50% HP
                elif hp_percent >= 0.25:  # 25-37.5%
                    damage = 7
                else:  # 0-25%
                    damage = 5

                # UPGRADE: Execute at low HP, defense shred at high HP
                if is_upgraded:
                    if hp_percent <= 0.25:  # Execute threshold
                        # Instant kill
                        damage = unit.hp
                        message_log.add_message(
                            f"{unit.get_display_name()} is erased by the rail cannon's lethal precision!",
                            MessageType.ABILITY,
                            player=user.player
                        )
                    elif hp_percent >= 0.875:  # Defense shred threshold
                        # Apply shredded status (2 turns) - defense will be forced to 0 via get_effective_stats()
                        unit.shredded = True
                        unit.shredded_duration = 2

                        message_log.add_message(
                            f"{unit.get_display_name()}'s defenses are completely shredded",
                            MessageType.WARNING,
                            player=user.player
                        )
                
                # Store previous HP for critical health check
                previous_hp = unit.hp

                # Apply damage
                unit.hp = max(0, unit.hp - damage)
                units_hit += 1
                total_damage += damage

                # Store unit and damage for later display
                damaged_units.append((unit, damage))

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
        if units_hit == 0:
            message_log.add_message(
                "The rail cannon's beam finds no targets",
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
        
        # Show impact animations and damage numbers after main animation
        if ui and hasattr(ui, 'renderer') and damaged_units:
            for unit, damage in damaged_units:
                if unit.is_alive():  # Only show for living units
                    # Play impact animation first
                    if hasattr(ui, 'asset_manager'):
                        impact_animation = ui.asset_manager.get_skill_animation_sequence('gaussian_dusk_impact')
                        if not impact_animation:
                            impact_animation = ['>', '!', '*', '#', '%', '~', '.']  # Fallback

                        # Animate impact at unit position
                        ui.renderer.animate_attack_sequence(
                            unit.y, unit.x,
                            impact_animation,
                            10,  # Red color for high-energy impact
                            0.08  # Quick, intense impact
                        )

                    # Then show damage numbers
                    damage_text = f"-{damage}"

                    # Make damage text more prominent with flashing effect
                    for i in range(3):
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                        attrs = (curses.A_BOLD if curses else 0) if i % 2 == 0 else 0
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)

                    # Final damage display (stays visible a bit longer)
                    ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, (curses.A_BOLD if curses else 0))
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.2)

        # Apply recharge state - unit cannot take any actions for 1 turn
        user.gaussian_dusk_recharge = self.recharge_duration

        return True


class BigArcSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Launches explosive mortar shells in a 3x3 area. Indirect fire ignores line of sight.
    """
    
    def __init__(self):
        super().__init__(
            name="Parabol",
            key="P",
            description="Launches explosive mortar shells in a 3x3 area. Indirect fire ignores line of sight.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=6,
            area=1  # 3x3 area (center + 1 in each direction)
        )
        self.primary_damage = 8
        self.secondary_damage = 5

    def update_range_for_junction(self, user: 'Unit', game: Optional['Game'] = None):
        """Update self.range based on whether user is on a junction."""
        base_range = 6
        self.range = base_range  # Reset to base

        if not game:
            return

        from boneglaive.game.upgrades import UpgradeManager
        rail_genesis_upgraded = UpgradeManager.is_skill_upgraded(user, "Rail Genesis")
        if not rail_genesis_upgraded:
            return

        # Fixed junction coordinates (4x4 grid)
        junction_coords = [
            (2, 4), (2, 8), (2, 12), (2, 16),
            (4, 4), (4, 8), (4, 12), (4, 16),
            (6, 4), (6, 8), (6, 12), (6, 16),
            (8, 4), (8, 8), (8, 12), (8, 16)
        ]

        current_y, current_x = user.y, user.x
        if (current_y, current_x) in junction_coords:
            self.range = base_range + 1

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Update range based on junction bonus
        self.update_range_for_junction(user, game)
        # Cannot use while recharging from Gaussian Dusk
        if hasattr(user, 'gaussian_dusk_recharge') and user.gaussian_dusk_recharge > 0:
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

        # Use the updated range (already updated by update_range_for_junction above)
        max_range = self.range

        # Check if target position is within range
        y_dist = abs(target_pos[0] - source_y)
        x_dist = abs(target_pos[1] - source_x)

        if max(y_dist, x_dist) > max_range:
            return False

        # Cannot target within radius 3 of self (self-damage protection)
        if max(abs(target_pos[0] - source_y), abs(target_pos[1] - source_x)) <= 3:
            return False

        # Indirect fire - no line of sight required
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Parabol skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Set the parabol indicator to show the area of effect
        user.parabol_indicator = target_pos

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} chambers a big one",
            MessageType.ABILITY,
            player=user.player
        )

        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Parabol skill during turn resolution."""
        from boneglaive.game.upgrades import UpgradeManager

        # Validate target position
        target_y, target_x = target_pos
        if not game.is_valid_position(target_y, target_x):
            return False

        # Clear the parabol indicator when skill is executed
        user.parabol_indicator = None

        # Check if skill is upgraded
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Parabol")

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
            f"{user.get_display_name()}'s payload arrives",
            MessageType.ABILITY,
            player=user.player
        )

        # Track units hit and damage dealt
        units_hit = 0
        total_damage = 0
        damaged_units = []  # Store units and damage for display after animation

        # UPGRADE: Track enemy unit positions from first explosion (will be imprinted as destruction at second site)
        first_explosion_enemy_offsets = []  # Relative positions of enemies

        if is_upgraded:
            # Scan first explosion area for enemy units
            for pos_y, pos_x, is_primary in affected_positions:
                unit = game.get_unit_at(pos_y, pos_x)
                if unit and unit.is_alive() and unit.player != user.player:
                    # Store relative offset from first explosion center
                    offset_y = pos_y - target_y
                    offset_x = pos_x - target_x
                    first_explosion_enemy_offsets.append((offset_y, offset_x))

        # Apply damage to all units in the area
        for pos_y, pos_x, is_primary in affected_positions:
            unit = game.get_unit_at(pos_y, pos_x)

            # Damage enemy units in area (no friendly fire)
            if unit and unit.is_alive() and unit.player != user.player:
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

                # Store unit and damage for later display
                damaged_units.append((unit, damage))

                # Log the damage
                damage_type = "primary" if is_primary else "secondary"
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit.get_display_name(),
                    damage=damage,
                    ability=f"Parabol ({damage_type})",
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
                "The mortar barrage strikes empty ground",
                MessageType.ABILITY,
                player=user.player
            )
        # Note: Individual unit damage messages are already shown above, no summary needed

        # UPGRADE: Execute second explosion with mirrored parabola
        second_explosion_damaged = []
        if is_upgraded:
            # Calculate direction vector from user to first explosion
            dist_y = target_y - user.y
            dist_x = target_x - user.x

            # Second explosion continues from first explosion point, same distance as original shot
            second_center_y = (target_y + dist_y) % game.map.height
            second_center_x = (target_x + dist_x) % game.map.width

            # Generate second explosion area (3x3 centered on second_center)
            second_affected_positions = []
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    pos_y = (second_center_y + dy) % game.map.height
                    pos_x = (second_center_x + dx) % game.map.width
                    is_primary = (dy == 0 and dx == 0)
                    second_affected_positions.append((pos_y, pos_x, is_primary))

            # Log second explosion
            message_log.add_message(
                f"The shell continues underground through a mirrored parabola, erupting at ({second_center_y},{second_center_x})",
                MessageType.ABILITY,
                player=user.player
            )

            # Apply damage to second explosion area
            for pos_y, pos_x, is_primary in second_affected_positions:
                unit = game.get_unit_at(pos_y, pos_x)

                # Damage enemy units in area (no friendly fire)
                if unit and unit.is_alive() and unit.player != user.player:
                    base_damage = self.primary_damage if is_primary else self.secondary_damage
                    effective_defense = unit.get_effective_stats()['defense']
                    damage = max(1, base_damage - effective_defense)

                    previous_hp = unit.hp
                    unit.hp = max(0, unit.hp - damage)

                    second_explosion_damaged.append((unit, damage))

                    damage_type = "primary" if is_primary else "secondary"
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=unit.get_display_name(),
                        damage=damage,
                        ability=f"Parabol Underground ({damage_type})",
                        attacker_player=user.player,
                        target_player=unit.player
                    )

                    if unit.hp <= 0:
                        game.handle_unit_death(unit, user, cause="ability", ui=ui)
                    else:
                        game.check_critical_health(unit, user, previous_hp, ui)

            # Apply the "imprint" effect at second explosion site
            if first_explosion_enemy_offsets:
                import random

                destructible_terrain = [
                    TerrainType.LIMESTONE, TerrainType.PILLAR, TerrainType.MARROW_WALL,
                    TerrainType.LECTERN, TerrainType.COAT_RACK, TerrainType.OTTOMAN,
                    TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF, TerrainType.TIFFANY_LAMP,
                    TerrainType.STAINED_STONE, TerrainType.EASEL, TerrainType.SCULPTURE,
                    TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                    TerrainType.HYDRAULIC_PRESS, TerrainType.WORKBENCH, TerrainType.COUCH,
                    TerrainType.TOOLBOX, TerrainType.COT, TerrainType.CONVEYOR,
                    TerrainType.MINI_PUMPKIN, TerrainType.POTPOURRI_BOWL,
                    TerrainType.SLAG_WALL, TerrainType.TOPIARY,
                    TerrainType.DERELICT_BUILDING,
                    TerrainType.PYLON, TerrainType.SUNDIAL, TerrainType.FIRE_PIT,
                    TerrainType.GRANITE_SPHERE, TerrainType.TERRACOTTA,
                    TerrainType.LITHOPHONE, TerrainType.RATTAN_CHAIR
                ]
                displaceable_terrain = destructible_terrain

                def _revert_topiary_at(pos_y, pos_x):
                    """Revert a topiary-unit at the given position, restoring its PRT."""
                    if not hasattr(game, 'topiary_units') or (pos_y, pos_x) not in game.topiary_units:
                        return
                    topiary_data = game.topiary_units[(pos_y, pos_x)]
                    unit = topiary_data['unit']
                    unit.is_topiary = False
                    unit.topiary_duration = 0
                    if hasattr(unit, 'topiary_original_prt'):
                        unit.prt = unit.topiary_original_prt
                        delattr(unit, 'topiary_original_prt')
                    del game.topiary_units[(pos_y, pos_x)]
                    message_log.add_message(
                        f"{unit.get_display_name()} is freed from topiary by the explosion!",
                        MessageType.ABILITY,
                        player=user.player
                    )

                def _cleanup_terrain_tracking(pos_y, pos_x):
                    """Clean up all dynamic terrain tracking at a position."""
                    if hasattr(game, 'slag_wall_tiles') and (pos_y, pos_x) in game.slag_wall_tiles:
                        del game.slag_wall_tiles[(pos_y, pos_x)]
                    if hasattr(game, 'topiary_terrain') and (pos_y, pos_x) in game.topiary_terrain:
                        del game.topiary_terrain[(pos_y, pos_x)]
                    if hasattr(game, 'marrow_dike_tiles') and (pos_y, pos_x) in game.marrow_dike_tiles:
                        del game.marrow_dike_tiles[(pos_y, pos_x)]
                    if hasattr(game, 'derelict_building_tiles') and (pos_y, pos_x) in game.derelict_building_tiles:
                        del game.derelict_building_tiles[(pos_y, pos_x)]

                # Step 1: Destroy terrain/furniture at primary (center) impact
                terrain = game.map.get_terrain_at(second_center_y, second_center_x)
                if terrain in destructible_terrain:
                    _revert_topiary_at(second_center_y, second_center_x)
                    _cleanup_terrain_tracking(second_center_y, second_center_x)
                    terrain_name = terrain.name.lower().replace('_', ' ')
                    message_log.add_message(
                        f"The underground explosion obliterates the {terrain_name} at ({second_center_y},{second_center_x})",
                        MessageType.ABILITY,
                        player=user.player
                    )
                    game.map.set_terrain_at(second_center_y, second_center_x, TerrainType.EMPTY)

                # Step 2: Collect all displaceable terrain at second explosion site (excluding destroyed center)
                second_site_terrain = []
                for pos_y, pos_x, is_primary in second_affected_positions:
                    if is_primary:
                        continue  # Skip center, already destroyed
                    terrain = game.map.get_terrain_at(pos_y, pos_x)
                    if terrain in displaceable_terrain and terrain != TerrainType.EMPTY:
                        # Skip topiary-units — they get freed, not relocated as terrain
                        if hasattr(game, 'topiary_units') and (pos_y, pos_x) in game.topiary_units:
                            _revert_topiary_at(pos_y, pos_x)
                            game.map.set_terrain_at(pos_y, pos_x, TerrainType.EMPTY)
                            continue
                        second_site_terrain.append((pos_y, pos_x, terrain))

                # Step 3: Move terrain/furniture to match enemy image from first explosion
                # Save dynamic terrain tracking data before clearing source positions
                saved_tracking = {}
                for terrain_y, terrain_x, terrain_type in second_site_terrain:
                    key = (terrain_y, terrain_x)
                    tracking = {}
                    if hasattr(game, 'topiary_terrain') and key in game.topiary_terrain:
                        tracking['topiary_terrain'] = game.topiary_terrain[key]
                    if hasattr(game, 'slag_wall_tiles') and key in game.slag_wall_tiles:
                        tracking['slag_wall'] = game.slag_wall_tiles[key]
                    if hasattr(game, 'marrow_dike_tiles') and key in game.marrow_dike_tiles:
                        tracking['marrow_dike'] = game.marrow_dike_tiles[key]
                    if hasattr(game, 'derelict_building_tiles') and key in game.derelict_building_tiles:
                        tracking['derelict_building'] = game.derelict_building_tiles[key]
                    if tracking:
                        saved_tracking[key] = tracking
                    _cleanup_terrain_tracking(terrain_y, terrain_x)
                    # Clear terrain from its current position
                    game.map.set_terrain_at(terrain_y, terrain_x, TerrainType.EMPTY)

                # Now place terrain/furniture at image positions
                for i, (offset_y, offset_x) in enumerate(first_explosion_enemy_offsets):
                    if i >= len(second_site_terrain):
                        break  # More enemy positions than terrain available

                    terrain_y, terrain_x, terrain_type = second_site_terrain[i]

                    # Calculate target position based on enemy image
                    target_y = (second_center_y + offset_y) % game.map.height
                    target_x = (second_center_x + offset_x) % game.map.width

                    # Check if unit is standing at target position
                    unit_at_target = game.get_unit_at(target_y, target_x)
                    if unit_at_target and unit_at_target.is_alive():
                        # Displace the unit first
                        displacement_attempts = []
                        for dy in range(-2, 3):
                            for dx in range(-2, 3):
                                if dy == 0 and dx == 0:
                                    continue
                                check_y = (target_y + dy) % game.map.height
                                check_x = (target_x + dx) % game.map.width
                                if (game.is_valid_position(check_y, check_x) and
                                    game.map.is_passable(check_y, check_x) and
                                    not game.get_unit_at(check_y, check_x)):
                                    displacement_attempts.append((check_y, check_x))

                        if displacement_attempts:
                            new_y, new_x = random.choice(displacement_attempts)
                            orig_y, orig_x = unit_at_target.y, unit_at_target.x
                            unit_at_target.y = new_y
                            unit_at_target.x = new_x

                            message_log.add_message(
                                f"{unit_at_target.get_display_name()} is violently displaced from ({orig_y},{orig_x}) to ({new_y},{new_x})",
                                MessageType.ABILITY,
                                player=user.player
                            )

                    # Place terrain/furniture at target position
                    game.map.set_terrain_at(target_y, target_x, terrain_type)

                    # Migrate dynamic terrain tracking to new position
                    source_key = (terrain_y, terrain_x)
                    if source_key in saved_tracking:
                        tracking = saved_tracking[source_key]
                        if 'topiary_terrain' in tracking:
                            game.topiary_terrain[(target_y, target_x)] = tracking['topiary_terrain']
                        if 'slag_wall' in tracking:
                            game.slag_wall_tiles[(target_y, target_x)] = tracking['slag_wall']
                        if 'marrow_dike' in tracking:
                            game.marrow_dike_tiles[(target_y, target_x)] = tracking['marrow_dike']
                        if 'derelict_building' in tracking:
                            game.derelict_building_tiles[(target_y, target_x)] = tracking['derelict_building']

                    terrain_name = terrain_type.name.lower().replace('_', ' ')
                    message_log.add_message(
                        f"A {terrain_name} shifts to ({target_y},{target_x}), matching the enemy formation imprint",
                        MessageType.ABILITY,
                        player=user.player
                    )

        # Play mortar barrage animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get launch animation
            launch_animation = ui.asset_manager.get_skill_animation_sequence('parabol_launch')
            if not launch_animation:
                launch_animation = ['o', 'O', '0', '*']
            
            # Get impact animation
            impact_animation = ui.asset_manager.get_skill_animation_sequence('parabol_impact')
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
        
        # Show impact animations and damage numbers after main animation
        if ui and hasattr(ui, 'renderer') and damaged_units:
            for unit, damage in damaged_units:
                if unit.is_alive():  # Only show for living units
                    # Play impact animation first
                    if hasattr(ui, 'asset_manager'):
                        impact_animation = ui.asset_manager.get_skill_animation_sequence('parabol_unit_impact')
                        if not impact_animation:
                            impact_animation = ['*', '@', '#', '%', '&', '+', '.']  # Fallback
                        
                        # Animate impact at unit position
                        ui.renderer.animate_attack_sequence(
                            unit.y, unit.x,
                            impact_animation,
                            3,  # Yellow color for explosive impact
                            0.1  # Moderate duration for mortar explosion
                        )
                    
                    # Then show damage numbers
                    damage_text = f"-{damage}"
                    
                    # Make damage text more prominent with flashing effect
                    for i in range(3):
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                        attrs = (curses.A_BOLD if curses else 0) if i % 2 == 0 else 0
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)

                    # Final damage display (stays visible a bit longer)
                    ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, (curses.A_BOLD if curses else 0))
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.2)

        # UPGRADE: Show second explosion animations
        if is_upgraded and ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager') and second_affected_positions:
            # Show underground travel effect (optional brief pause)
            sleep_with_animation_speed(0.2)

            # Get impact animation
            impact_animation = ui.asset_manager.get_skill_animation_sequence('parabol_impact')
            if not impact_animation:
                impact_animation = ['*', '#', '@', '%', '~', '.']

            # Show impact animation on all second explosion positions
            for frame in impact_animation:
                for pos_y, pos_x, is_primary in second_affected_positions:
                    color = 5 if is_primary else 6  # Magenta/cyan for underground explosion
                    ui.renderer.draw_tile(pos_y, pos_x, frame, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)

            # Redraw the board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

            # Show damage numbers for second explosion
            if second_explosion_damaged:
                for unit, damage in second_explosion_damaged:
                    if unit.is_alive():
                        # Play impact animation
                        if hasattr(ui, 'asset_manager'):
                            impact_animation = ui.asset_manager.get_skill_animation_sequence('parabol_unit_impact')
                            if not impact_animation:
                                impact_animation = ['*', '@', '#', '%', '&', '+', '.']

                            ui.renderer.animate_attack_sequence(
                                unit.y, unit.x,
                                impact_animation,
                                5,  # Magenta color for underground explosion
                                0.1
                            )

                        # Show damage numbers
                        damage_text = f"-{damage}"

                        for i in range(3):
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                            attrs = (curses.A_BOLD if curses else 0) if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)

                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, (curses.A_BOLD if curses else 0))
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.2)

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

        # Upgrade values
        self.upgraded_target_type = TargetType.SELF
        self.upgraded_range = 0
        self.upgraded_area = 2  # 5x5 (center + 2 in each direction)
        self.upgraded_damage = 4  # Uniform damage for AOE
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Cannot use while recharging from Gaussian Dusk
        if hasattr(user, 'gaussian_dusk_recharge') and user.gaussian_dusk_recharge > 0:
            return False

        # Check if upgraded and update target type dynamically
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Fragcrest")

        # Dynamically change targeting based on upgrade status
        # Upgraded: allows BOTH ground and enemy targeting
        if is_upgraded:
            self.target_type = TargetType.AREA  # Allows both ground and unit targeting
            self.range = 4
        else:
            self.target_type = TargetType.ENEMY  # Only enemy units
            self.range = 4

        # Basic validation
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

        # Check what's at the target position
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])

        # Upgraded version: allows both trap placement AND direct fire
        if is_upgraded:
            # If targeting an enemy unit, use base skill logic
            if target_unit and target_unit.is_alive() and target_unit != user:
                # Check if enemy
                if target_unit.player != user.player:
                    # Requires line of sight for direct fire
                    if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
                        return False
                    return True
                else:
                    return False  # Cannot target allies

            # Otherwise, targeting ground for trap placement
            # Must target empty, passable terrain
            if not game.map.is_passable(target_pos[0], target_pos[1]):
                return False
            if target_unit is not None:  # Already checked for enemy above
                return False
            return True

        # Base version (not upgraded): directional cone targeting enemy only
        if not target_unit or not target_unit.is_alive():
            return False

        # Cannot target self
        if target_unit == user:
            return False

        # Must be enemy
        if target_unit.player == user.player:
            return False

        # Requires line of sight to primary target
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Fragcrest skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        # Check if upgraded
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Fragcrest")

        user.skill_target = target_pos
        user.selected_skill = self

        # Set visual indicator for the cone or trap
        user.fragcrest_indicator = target_pos

        # Log that the skill has been queued
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        is_targeting_enemy = (target_unit is not None and
                             target_unit.is_alive() and
                             target_unit.player != user.player)

        # Silent for trap placement, message for direct fire
        if is_upgraded and not is_targeting_enemy:
            # Silent trap deployment - no message log entry (like Scalar Node)
            pass
        else:
            # Direct fire at enemy (base skill or upgraded direct fire)
            message_log.add_message(
                f"{user.get_display_name()} unfolds its tail and aims a fragmentation burst at {target_unit.get_display_name()}",
                MessageType.ABILITY,
                player=user.player
            )

        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Fragcrest skill during turn resolution."""
        # Clear indicator
        user.fragcrest_indicator = None

        # Check if upgraded
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Fragcrest")

        # Check if targeting an enemy unit (direct fire)
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        is_targeting_enemy = (target_unit is not None and
                             target_unit.is_alive() and
                             target_unit.player != user.player)

        # Upgraded version: check if trap placement or direct fire
        if is_upgraded and not is_targeting_enemy:
            # Calculate trap direction based on FOWL CONTRIVANCE position relative to trap
            trap_y, trap_x = target_pos
            user_y, user_x = user.y, user.x

            # Determine direction vector
            dy = trap_y - user_y
            dx = trap_x - user_x

            # Normalize to get direction (for cone calculations later)
            # Store the direction as a unit vector
            import math
            distance = math.sqrt(dy * dy + dx * dx)
            if distance > 0:
                direction_y = dy / distance
                direction_x = dx / distance
            else:
                direction_y = 1  # Default forward
                direction_x = 0

            # Create fragcrest trap tracking in game
            if not hasattr(game, 'fragcrest_traps'):
                game.fragcrest_traps = {}

            # Place the trap with direction information
            game.fragcrest_traps[target_pos] = {
                'owner': user,
                'direction_y': direction_y,
                'direction_x': direction_x,
                'active': False,  # Not active yet, needs to arm
                'armed': False,  # Becomes armed after 1 turn
                'arm_turns_remaining': 1,  # Arms after 1 turn
                'duration': 6,  # Lasts 6 turns after arming
                'caster_pos': (user_y, user_x)  # Store for cone calculation
            }

            # Silent deployment - no message log or animation
            return True

        # Base version: immediate directional cone attack
        else:
            # Get primary target for base version
            primary_target = game.get_unit_at(target_pos[0], target_pos[1])
            if not primary_target or not primary_target.is_alive():
                return False

            # Calculate cone direction and affected positions
            target_y, target_x = target_pos
            affected_positions = self._calculate_cone_positions(user.y, user.x, target_y, target_x, game)

        # Log the skill activation
        if is_upgraded:
            message_log.add_message(
                f"{user.get_display_name()}'s fragmentation burst explodes in all directions",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()}'s fragmentation burst explodes in a deadly cone",
                MessageType.ABILITY,
                player=user.player
            )

        # Track affected units
        affected_units = []
        units_hit = 0
        total_damage = 0
        damaged_units = []  # Store units and damage for display after animation

        # Apply damage and effects to all units in affected area
        for pos_y, pos_x, is_primary in affected_positions:
            unit = game.get_unit_at(pos_y, pos_x)
            
            # Only affect enemy units
            if unit and unit.is_alive() and unit.player != user.player:
                # Calculate damage based on upgrade status
                if is_upgraded:
                    # Upgraded: uniform damage across AOE
                    base_damage = self.upgraded_damage
                else:
                    # Base: primary vs secondary damage in cone
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

                # Store unit and damage for later display
                damaged_units.append((unit, damage))

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
                
                # Apply shrapnel effect (ongoing damage) if not immune
                if unit.is_immune_to_effects():
                    # Log immunity message
                    message_log.add_message(
                        f"{unit.get_display_name()} is immune to shrapnel due to Stasiality",
                        MessageType.ABILITY,
                        player=unit.player
                    )
                else:
                    if not hasattr(unit, 'shrapnel_duration'):
                        unit.shrapnel_duration = 0
                    previous_shrapnel = unit.shrapnel_duration
                    unit.shrapnel_duration = max(unit.shrapnel_duration, self.shrapnel_duration)

                    # Log shrapnel embedding if it's a new effect or extended
                    if unit.shrapnel_duration > previous_shrapnel:
                        message_log.add_message(
                            f"Shrapnel embeds deeply in {unit.get_display_name()}",
                            MessageType.ABILITY,
                            player=unit.player
                        )
                
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
                "The fragmentation burst finds no targets",
                MessageType.ABILITY,
                player=user.player
            )

        # Play fragmentation animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get fragmentation animation
            frag_animation = ui.asset_manager.get_skill_animation_sequence('fragcrest_burst')
            if not frag_animation:
                frag_animation = ['.', ':', '*', '+', '#', 'x']

            # Show tail unfold at user position
            if is_upgraded:
                ui.renderer.draw_tile(user.y, user.x, '@', 6)  # @ for omnidirectional burst
            else:
                ui.renderer.draw_tile(user.y, user.x, 'V', 6)  # V for directional cone
            ui.renderer.refresh()
            sleep_with_animation_speed(0.1)

            # Show fragmentation burst spreading
            for frame in frag_animation:
                for pos_y, pos_x, is_primary in affected_positions:
                    if is_upgraded:
                        # Upgraded: uniform color for AOE
                        color = 1  # Red for all
                    else:
                        # Base: primary vs secondary coloring
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
        
        # Show impact animations and damage numbers after main animation
        if ui and hasattr(ui, 'renderer') and damaged_units:
            for unit, damage in damaged_units:
                if unit.is_alive():  # Only show for living units
                    # Play impact animation first
                    if hasattr(ui, 'asset_manager'):
                        impact_animation = ui.asset_manager.get_skill_animation_sequence('fragcrest_unit_impact')
                        if not impact_animation:
                            impact_animation = ['x', '+', '*', '#', '.']  # Fallback
                        
                        # Animate impact at unit position
                        ui.renderer.animate_attack_sequence(
                            unit.y, unit.x,
                            impact_animation,
                            6,  # Cyan color for fragmentation impact
                            0.12  # Slightly longer for shrapnel effect
                        )
                    
                    # Then show damage numbers
                    damage_text = f"-{damage}"
                    
                    # Make damage text more prominent with flashing effect
                    for i in range(3):
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                        attrs = (curses.A_BOLD if curses else 0) if i % 2 == 0 else 0
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                    
                    # Final damage display (stays visible a bit longer)
                    ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, (curses.A_BOLD if curses else 0))
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.2)
        
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

    def _calculate_aoe_positions(self, center_y: int, center_x: int, game: 'Game') -> List[Tuple[int, int, bool]]:
        """Calculate all positions in a 5x5 AOE centered on the user."""
        positions = []

        # Generate 5x5 area (center + 2 in each direction)
        for dy in range(-2, 3):  # -2, -1, 0, 1, 2
            for dx in range(-2, 3):  # -2, -1, 0, 1, 2
                # Skip the center tile (user's position)
                if dy == 0 and dx == 0:
                    continue

                pos_y = center_y + dy
                pos_x = center_x + dx

                if game.is_valid_position(pos_y, pos_x):
                    # All positions are treated as "primary" for uniform damage
                    positions.append((pos_y, pos_x, True))

        return positions

    def _apply_knockback(self, user: 'Unit', target: 'Unit', game: 'Game') -> None:
        """Apply knockback effect to target unit with collision detection."""
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

        # Store original position for message
        orig_y, orig_x = target.y, target.x

        # Apply knockback step by step to detect collisions
        final_y, final_x = target.y, target.x
        distance_moved = 0

        for step in range(1, self.knockback_distance + 1):
            check_y = target.y + knock_dir[0] * step
            check_x = target.x + knock_dir[1] * step

            # Check if this position is valid and passable
            if (game.is_valid_position(check_y, check_x) and
                game.map.is_passable(check_y, check_x) and
                not game.get_unit_at(check_y, check_x)):

                # Position is clear, unit can move here
                final_y, final_x = check_y, check_x
                distance_moved = step
            else:
                # Hit an obstacle, stop here
                if distance_moved == 0:
                    # Couldn't move at all
                    message_log.add_message(
                        f"{target.get_display_name()} collides with an obstacle and cannot be displaced",
                        MessageType.ABILITY,
                        player=target.player
                    )
                else:
                    # Moved some distance before hitting obstacle
                    message_log.add_message(
                        f"{target.get_display_name()} is displaced from ({orig_y},{orig_x}) to ({final_y},{final_x}) before colliding with an obstacle",
                        MessageType.ABILITY,
                        player=target.player
                    )
                break
        else:
            # Completed full knockback without hitting anything
            if distance_moved > 0:
                message_log.add_message(
                    f"{target.get_display_name()} is blasted backward from ({orig_y},{orig_x}) to ({final_y},{final_x})",
                    MessageType.ABILITY,
                    player=target.player
                )

        # Update unit position if it moved
        if distance_moved > 0:
            target.y = final_y
            target.x = final_x