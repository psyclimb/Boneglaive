#!/usr/bin/env python3
"""
Skills specific to the FOWL_CONTRIVANCE unit type.
This module contains all passive and active abilities for FOWL_CONTRIVANCE units.
"""

from typing import Optional, TYPE_CHECKING, List, Dict, Tuple, Set
import random
import time
from boneglaive.utils.animation_helpers import sleep_with_animation_speed

import curses

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.constants import UnitType, CRITICAL_HEALTH_PERCENT

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class WretchedDecension(PassiveSkill):
    """
    Passive skill for FOWL_CONTRIVANCE.
    When FOWL_CONTRIVANCE causes a unit to retch (reduced to critical health), 
    that unit may instantly perish instead, with the flock descending to carry away the near-dead.
    The chance depends on how many FOWL_CONTRIVANCE units are on the same team.
    """
    
    def __init__(self):
        super().__init__(
            name="Wretched Decension",
            key="W",
            description="When a unit is reduced to critical health, the flocks may descend to claim the wretched! Chance decreases with more FOWL_CONTRIVANCE units."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        """
        Passive is handled in the game engine's check_critical_health method.
        This passive does not directly modify the unit but triggers when 
        other units reach critical health.
        """
        pass
    
    def check_wretched_decension_chance(self, game: 'Game', user: 'Unit') -> float:
        """Calculate chance of Wretched Decension triggering based on number of allied FOWL_CONTRIVANCE units."""
        # Count allied FOWL_CONTRIVANCE units
        allied_fowl_count = 0
        for unit in game.units:
            if unit.is_alive() and unit.player == user.player and unit.type == UnitType.FOWL_CONTRIVANCE:
                allied_fowl_count += 1
        
        # Calculate chance based on count
        if allied_fowl_count == 1:
            return 1.0  # 100% chance
        elif allied_fowl_count == 2:
            return 0.5  # 50% chance
        elif allied_fowl_count >= 3:
            return 0.25  # 25% chance
        
        return 1.0  # Fallback (should never happen)


class MurmurationDuskSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Medium-range area attack where bird flocks dive-bomb in intricate patterns.
    """
    
    def __init__(self):
        super().__init__(
            name="Murmuration Dusk",
            key="M",
            description="Medium-range area attack where bird flocks dive-bomb enemy units in intricate patterns.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3,  # Note: parameter is range_ but it gets stored as self.range
            area=1  # 3x3 area (center + 1 in each direction)
        )
        self.damage = 6
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
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
        
        # Check if target position is within range (Manhattan distance) from current or planned position
        y_dist = abs(target_pos[0] - source_y)
        x_dist = abs(target_pos[1] - source_x)
        
        if y_dist > self.range or x_dist > self.range:
            return False
        
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Murmuration Dusk skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to summon a murmuration of birds!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Murmuration Dusk skill during turn resolution."""
        # Validate target position
        target_y, target_x = target_pos
        if not game.is_valid_position(target_y, target_x):
            return False
            
        # Generate the area of effect (3x3 area centered on target_pos)
        affected_positions = []
        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                pos_y, pos_x = target_y + dy, target_x + dx
                
                # Check if position is valid
                if game.is_valid_position(pos_y, pos_x):
                    affected_positions.append((pos_y, pos_x))
        
        # Log the skill activation
        message_log.add_message(
            f"Shadows lengthen as {user.get_display_name()} summons the dusk birds!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Track units hit and damage dealt
        units_hit = 0
        total_damage = 0
        
        # Apply damage to all enemy units in the area
        for pos_y, pos_x in affected_positions:
            unit = game.get_unit_at(pos_y, pos_x)
            
            # Only damage enemy units - not self or allies
            if unit and unit.is_alive() and unit.player != user.player:
                # Calculate damage based on unit's defense
                effective_defense = unit.get_effective_stats()['defense']
                damage = max(1, self.damage - effective_defense)
                
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
                    ability="Murmuration Dusk",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health (retching) using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)
        
        if units_hit > 0:
            message_log.add_message(
                f"The murmuration strikes with the finality of sunset, dealing {total_damage} damage!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                "The dusk birds yield no results!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get murmuration animation from asset manager
            murmuration_animation = ui.asset_manager.get_skill_animation_sequence('murmuration_dusk')
            if not murmuration_animation:
                # Fallback animation if not defined in asset manager
                murmuration_animation = ['^', 'v', '~', '*', 'V', 'Λ', '^']
            
            # Create an elaborate bird swarm animation that covers the entire area
            
            # First animate birds gathering above the user
            gathering_animation = ['`', '*', '^', '~', '^', '~']
            for frame in gathering_animation:
                ui.renderer.draw_tile(user.y, user.x, frame, 4)  # Blue color for the gathering flock
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Animate birds flying from user to target center
            points = []
            try:
                from boneglaive.game.animations import get_line
                points = get_line(user.y, user.x, target_y, target_x)
            except ImportError:
                # Fallback if animation module not available
                points = [(user.y, user.x), (target_y, target_x)]
            
            # Flying animation
            flock_symbols = ['^', 'v', '>', '<', '∧', '∨', '<', '>']
            for i, (y, x) in enumerate(points):
                # Skip the first position (user's position)
                if i == 0:
                    continue
                    
                # Choose a flock symbol based on path direction
                symbol_idx = i % len(flock_symbols)
                symbol = flock_symbols[symbol_idx]
                
                # Use alternating blue and red colors for the flying flock
                color = 4 if i % 2 == 0 else 1  # Blue/Red alternating
                
                ui.renderer.draw_tile(y, x, symbol, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.03)

            # Now show the swirling pattern at each affected position
            
            # First pass: create swirling effect at all positions simultaneously
            for frame_idx in range(len(murmuration_animation)):
                for pos_y, pos_x in affected_positions:
                    # Get the correct bird symbol for this frame
                    if frame_idx < len(murmuration_animation):
                        bird_symbol = murmuration_animation[frame_idx]
                    else:
                        bird_symbol = murmuration_animation[-1]
                    
                    # Alternate colors for a more intense, flashing effect
                    # Use different colors based on position to create a wave-like pattern
                    color_idx = (pos_y + pos_x + frame_idx) % 4
                    if color_idx == 0:
                        color = 4  # Blue
                    elif color_idx == 1:
                        color = 1  # Red
                    elif color_idx == 2:
                        color = 6  # Yellow (special color for birds in motion)
                    else:
                        color = 7  # White
                    
                    ui.renderer.draw_tile(pos_y, pos_x, bird_symbol, color)
                
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)  # Quick animation

            # Second pass: show impact animations on enemy units that were hit
            units_damaged = []
            for pos_y, pos_x in affected_positions:
                unit = game.get_unit_at(pos_y, pos_x)
                if unit and unit.is_alive() and unit.player != user.player:
                    units_damaged.append((pos_y, pos_x))
            
            # Impact animation on units
            if units_damaged:
                impact_animation = ['^', '*', '~', '*', '~', '*', '^']
                for impact_frame in impact_animation:
                    for pos_y, pos_x in units_damaged:
                        ui.renderer.draw_tile(pos_y, pos_x, impact_frame, 1)  # Red color for impact
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.05)

            # Final swirling animation before dissipating
            dissipate_animation = ['*', '.', ' ', ' ']
            for frame in dissipate_animation:
                for pos_y, pos_x in affected_positions:
                    ui.renderer.draw_tile(pos_y, pos_x, frame, 7)  # White color for dissipation
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Redraw the board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class FlapSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Focused single-target attack with extreme damage from a concentrated hawk formation.
    """
    
    def __init__(self):
        super().__init__(
            name="Flap",
            key="F",
            description="Focused single-target attack with extreme damage from a concentrated hawk formation.",
            target_type=TargetType.ENEMY,  # Changed from UNIT to ENEMY
            cooldown=2,
            range_=4  # Note: parameter is range_ but it gets stored as self.range
        )
        self.damage = 9
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
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
        
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Flap skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Log that the skill has been queued
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        message_log.add_message(
            f"{user.get_display_name()} prepares and avian artillery strike on {target_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Flap skill during turn resolution."""
        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or not target_unit.is_alive():
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} unleashes a concentrated barrage that strikes {target_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Calculate damage based on target's defense
        effective_defense = target_unit.get_effective_stats()['defense']
        damage = max(1, self.damage - effective_defense)
        
        # Store previous HP for critical health check
        previous_hp = target_unit.hp
        
        # Apply damage
        target_unit.hp = max(0, target_unit.hp - damage)
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target_unit.get_display_name(),
            damage=damage,
            ability="Flap",
            attacker_player=user.player,
            target_player=target_unit.player
        )
        
        # Handle death if unit was killed
        if target_unit.hp <= 0:
            game.handle_unit_death(target_unit, user, cause="ability", ui=ui)
        else:
            # Check for critical health (retching) using centralized logic
            game.check_critical_health(target_unit, user, previous_hp, ui)
        
        message_log.add_message(
            f"The concentrated barrage deals {damage} damage to {target_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get hawk animation from asset manager
            flap_animation = ui.asset_manager.get_skill_animation_sequence('flap')
            if not flap_animation:
                # Fallback animation if not defined in asset manager
                flap_animation = ['^', 'V', '^', 'v', '^', '*']
            
            # Elaborate animation sequence
            
            # First, show the birds gathering above the user (similar to Murmuration Dusk)
            gathering_animation = ['`', '*', '~', '^']
            for frame in gathering_animation:
                ui.renderer.draw_tile(user.y, user.x, frame, 4)  # Blue color for gathering
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)

            # Animation paths - create multiple paths from user to target
            try:
                from boneglaive.game.animations import get_line
                # Create main attack path
                main_path = get_line(user.y, user.x, target_pos[0], target_pos[1])
                
                # Create additional paths that converge on the target
                # These paths will create a more dramatic "multiple birds converging" effect
                alternate_paths = []
                
                # Create path offsets to make birds come from slightly different directions
                offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dy, dx in offsets[:4]:  # Use first 4 offsets (cardinal directions)
                    # Calculate an offset starting position
                    start_y = max(0, min(game.map.height - 1, user.y + dy))
                    start_x = max(0, min(game.map.width - 1, user.x + dx))
                    
                    # Don't start from positions with units on them
                    if not game.get_unit_at(start_y, start_x):
                        path = get_line(start_y, start_x, target_pos[0], target_pos[1])
                        alternate_paths.append(path)
            
            except ImportError:
                # Fallback if animation module not available
                main_path = [(user.y, user.x), (target_pos[0], target_pos[1])]
                alternate_paths = []
            
            # Animation symbols for the hawks
            hawk_symbols = ['Y', 'V', '~', '^', '~', 'V', 'Y']
            
            # Animate the main attack path
            for i, (y, x) in enumerate(main_path):
                # Skip user's position
                if i == 0:
                    continue
                    
                # Choose a symbol based on path position
                symbol_idx = min(i, len(hawk_symbols) - 1)
                symbol = hawk_symbols[symbol_idx]
                
                # Red color for the main attack path
                ui.renderer.draw_tile(y, x, symbol, 1)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.03)
                
                # For non-target positions, clear the path behind
                if i < len(main_path) - 1:
                    ui.renderer.draw_tile(y, x, ' ', 1)

            # Now animate the alternate paths simultaneously
            if alternate_paths:
                max_length = max(len(path) for path in alternate_paths)
                
                for step in range(1, max_length):
                    for path_idx, path in enumerate(alternate_paths):
                        if step < len(path):
                            y, x = path[step]
                            
                            # Skip positions with units on them
                            if game.get_unit_at(y, x) and (y, x) != target_pos:
                                continue
                                
                            # Choose a different bird symbol for each path
                            symbol = hawk_symbols[path_idx % len(hawk_symbols)]
                            
                            # Use different colors for different paths
                            color = 4 if path_idx % 2 == 0 else 6  # Blue or yellow
                            
                            ui.renderer.draw_tile(y, x, symbol, color)
                    
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.02)
                    
                    # Clear symbols from previous step
                    for path_idx, path in enumerate(alternate_paths):
                        if step - 1 > 0 and step - 1 < len(path):
                            prev_y, prev_x = path[step - 1]
                            # Only clear if not at target position
                            if (prev_y, prev_x) != target_pos:
                                ui.renderer.draw_tile(prev_y, prev_x, ' ', 1)

            # Convergence animation at target position
            # Show the multiple birds converging on the target with increasing intensity
            convergence_animation = []
            for i in range(len(flap_animation)):
                # Use more intense symbols as the animation progresses
                convergence_animation.append(flap_animation[i])
            
            # Add impact symbols
            impact_animation = ['*', 'v', '*', '^', '*', 'v']
            convergence_animation.extend(impact_animation)
            
            # Show the convergence animation
            for frame_idx, frame in enumerate(convergence_animation):
                # Color changes throughout animation for dramatic effect
                if frame_idx < len(convergence_animation) // 3:
                    color = 4  # Blue
                elif frame_idx < 2 * len(convergence_animation) // 3:
                    color = 1  # Red
                else:
                    color = 7  # White for impact
                
                ui.renderer.draw_tile(target_pos[0], target_pos[1], frame, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Final impact animation - show damage effect
            if hasattr(ui, 'asset_manager'):
                tile_ids = []
                color_ids = []
                durations = []
                
                # Create a dramatic flashing sequence
                for _ in range(3):
                    # Use the target unit's symbol
                    tile_ids.append(ui.asset_manager.get_unit_tile(target_unit.type))
                    # Flash between red and normal color
                    color_ids.append(1)  # Red
                    color_ids.append(3 if target_unit.player == 1 else 4)  # Player color
                    # Add durations for each
                    durations.extend([0.1, 0.1])
                
                # Flash the target to show impact
                ui.renderer.flash_tile(
                    target_pos[0], target_pos[1],
                    tile_ids, color_ids, durations
                )
            
            # Redraw the board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class EmeticFlangeSkill(ActiveSkill):
    """
    Active skill for FOWL_CONTRIVANCE.
    Close-range explosion of birds bursting outward in all directions.
    Damages and pushes affected units back 1 tile.
    """
    
    def __init__(self):
        super().__init__(
            name="Emetic Flange",
            key="E",
            description="Close-range explosion of birds bursting outward, damaging and pushing enemy units back 1 tile.",
            target_type=TargetType.SELF,
            cooldown=3,  # Reduced from 4 to 3
            range_=0,  # Note: parameter is range_ but it gets stored as self.range
            area=1  # All adjacent tiles (8 surrounding tiles)
        )
        self.damage = 4
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Only cooldown validation needed, as it's self-targeted
        return super().can_use(user, target_pos, game)
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Emetic Flange skill for execution."""
        # For self-targeting skills, set target to current position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to unleash a vomitous bursting flock of birds!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Emetic Flange skill during turn resolution."""
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} explodes into a burst of birds in all directions!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Generate adjacent positions (all 8 surrounding tiles)
        adjacent_positions = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                # Skip the center position (user's position)
                if dy == 0 and dx == 0:
                    continue
                    
                pos_y, pos_x = user.y + dy, user.x + dx
                
                # Check if position is valid
                if game.is_valid_position(pos_y, pos_x):
                    adjacent_positions.append((pos_y, pos_x, dy, dx))  # Store direction vectors for push
        
        # Track units hit and pushed
        units_hit = 0
        units_pushed = 0
        total_damage = 0
        
        # Apply damage and push to adjacent enemy units only
        for pos_y, pos_x, push_dy, push_dx in adjacent_positions:
            unit = game.get_unit_at(pos_y, pos_x)
            
            # Only affect enemy units, not allies
            if unit and unit.is_alive() and unit.player != user.player:
                # Calculate damage based on target's defense
                effective_defense = unit.get_effective_stats()['defense']
                damage = max(1, self.damage - effective_defense)
                
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
                    ability="Emetic Flange",
                    attacker_player=user.player,
                    target_player=unit.player
                )
                
                # Handle death if unit was killed
                if unit.hp <= 0:
                    game.handle_unit_death(unit, user, cause="ability", ui=ui)
                else:
                    # Check for critical health (retching) using centralized logic
                    game.check_critical_health(unit, user, previous_hp, ui)
                
                # Only attempt to push if unit is not immune to effects (e.g., GRAYMAN with Stasiality)
                if not unit.is_immune_to_effects():
                    # Calculate push destination
                    push_dest_y = pos_y + push_dy
                    push_dest_x = pos_x + push_dx
                    
                    # Check if push destination is valid and unoccupied
                    if (game.is_valid_position(push_dest_y, push_dest_x) and 
                        game.map.is_passable(push_dest_y, push_dest_x) and
                        not game.get_unit_at(push_dest_y, push_dest_x)):
                        
                        # Push the unit
                        unit.y = push_dest_y
                        unit.x = push_dest_x
                        units_pushed += 1
                else:
                    # Log that the unit is immune to the push effect
                    message_log.add_message(
                        f"{unit.get_display_name()} is immune to Emetic Flange's push effect due to Stasiality!",
                        MessageType.ABILITY,
                        player=unit.player,  # Use target unit's player for correct color coding
                        target_name=unit.get_display_name()
                    )
        
        # Log results
        if units_hit > 0:
            message_log.add_message(
                f"The bird explosion strikes {units_hit} {'unit' if units_hit == 1 else 'units'} for {total_damage} damage!",
                MessageType.ABILITY,
                player=user.player
            )
            
            if units_pushed > 0:
                message_log.add_message(
                    f"{units_pushed} {'unit was' if units_pushed == 1 else 'units were'} pushed back by the explosive flock!",
                    MessageType.ABILITY,
                    player=user.player
                )
        else:
            message_log.add_message(
                "The birds burst outward, but find no targets!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get animation from asset manager
            emetic_animation = ui.asset_manager.get_skill_animation_sequence('emetic_flange')
            if not emetic_animation:
                # Fallback animation if not defined in asset manager
                emetic_animation = ['*', '#', '@', '&', '%', '>', '>']
            
            # First flash the user to show skill activation
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                # Flash with blue/red/blue/red
                color_ids = [4, 1, 4, 1]  # Blue and red alternating
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
            
            # Initial explosion animation at center
            center_animation = ['*', '#', '@', '&', '*', '#', '@']
            for frame in center_animation[:3]:  # First half of animation at center
                ui.renderer.draw_tile(user.y, user.x, frame, 1)  # Red color for explosion
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Create explosion animation that spreads outward
            # Initialize all positions with empty spaces
            explosion_frames = []
            max_frames = 6  # Number of animation frames
            
            # Create frames showing explosion spreading outward
            for frame_idx in range(max_frames):
                frame = {}
                # For each position, determine what to show based on animation frame
                for pos_y, pos_x, _, _ in adjacent_positions:
                    # Calculate distance from center (Manhattan distance)
                    dist = abs(pos_y - user.y) + abs(pos_x - user.x)
                    
                    # Determine which symbol to show based on frame and distance
                    if frame_idx >= dist - 1 and frame_idx < dist + len(emetic_animation):
                        # Select appropriate animation frame
                        anim_idx = frame_idx - (dist - 1)
                        if anim_idx < len(emetic_animation):
                            symbol = emetic_animation[anim_idx]
                            
                            # Use different colors for different directions
                            # This creates a more colorful explosion effect
                            dy, dx = pos_y - user.y, pos_x - user.x
                            if abs(dy) == abs(dx):  # Diagonal
                                color = 6 if (dy + dx) % 2 == 0 else 3  # Yellow or green
                            elif dy == 0:  # Horizontal
                                color = 1  # Red
                            else:  # Vertical
                                color = 4  # Blue
                                
                            frame[(pos_y, pos_x)] = (symbol, color)
                
                explosion_frames.append(frame)
            
            # Play all the frames
            for frame in explosion_frames:
                for (pos_y, pos_x), (symbol, color) in frame.items():
                    ui.renderer.draw_tile(pos_y, pos_x, symbol, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Create a list of pushed units for animation
            pushed_units_info = []
            
            # For each enemy unit, check if it was hit and was pushed
            for pos_y, pos_x, push_dy, push_dx in adjacent_positions:
                unit = game.get_unit_at(pos_y, pos_x)
                
                # Only check enemy units that were hit but not killed
                if unit and unit.is_alive() and unit.player != user.player:
                    # For units that were pushed (not immune to effects)
                    if not unit.is_immune_to_effects():
                        # Calculate push destination
                        push_dest_y = pos_y + push_dy
                        push_dest_x = pos_x + push_dx
                        
                        # If the unit is at the push destination, it was pushed
                        if unit.y == push_dest_y and unit.x == push_dest_x:
                            # Add to list for animation, tracking original and new positions
                            pushed_units_info.append((unit, pos_y, pos_x, push_dy, push_dx))
            
            # Show push animation for units that were actually pushed
            for unit, orig_y, orig_x, push_dy, push_dx in pushed_units_info:
                # Animation for unit being pushed
                push_animation = ['↖', '↗', '↘', '↙']
                
                # Choose direction indicator based on push direction
                direction_idx = 0
                if push_dy < 0 and push_dx < 0:  # Northwest
                    direction_idx = 0  # ↖
                elif push_dy < 0 and push_dx > 0:  # Northeast
                    direction_idx = 1  # ↗
                elif push_dy > 0 and push_dx > 0:  # Southeast
                    direction_idx = 2  # ↘
                elif push_dy > 0 and push_dx < 0:  # Southwest
                    direction_idx = 3  # ↙
                
                # Draw push direction indicator
                ui.renderer.draw_tile(
                    orig_y, orig_x,
                    push_animation[direction_idx],
                    6  # Yellow for push animation
                )
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
            
            # Cleanup animation - birds flying away
            cleanup_animation = ['*', '.', ' ']
            for frame in cleanup_animation:
                for pos_y, pos_x, _, _ in adjacent_positions:
                    ui.renderer.draw_tile(pos_y, pos_x, frame, 7)  # White for cleanup
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Redraw the board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True
