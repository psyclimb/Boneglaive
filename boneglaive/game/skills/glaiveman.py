#!/usr/bin/env python3
"""
Skills specific to the GLAIVEMAN unit type.
This module contains all passive and active abilities for GLAIVEMAN units.
"""

import curses
import time
from boneglaive.utils.animation_helpers import sleep_with_animation_speed

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Autoclave(PassiveSkill):
    """
    Passive skill for GLAIVEMAN.
    When the GLAIVEMAN wretches (is brought to critical health but not killed)
    or takes damage while already at critical health,
    he retaliates with a four-directional, range 3, cross-shaped attack that
    heals him for half of the damage he dealt.
    Can only occur once per game per GLAIVEMAN.
    Only triggers if there is at least one enemy unit in the attack path.
    """
    
    def __init__(self):
        super().__init__(
            name="Autoclave",
            key="A",
            description="When retched or damaged while at critical health, unleashes a cross-shaped attack in four directions (range 3) and heals for half the damage dealt. One-time use. Requires an enemy in range."
        )
        self.activated = False  # Track if this skill has been used
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """
        Apply the Autoclave passive effect.
        This method is kept for backward compatibility and as a fallback check.
        """
        from boneglaive.utils.debug import logger
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        
        # If already activated or no game, skip
        if self.activated or not game:
            return
            
        # Check if the unit is in critical health - one more chance to trigger if missed
        critical_threshold = int(user.max_hp * CRITICAL_HEALTH_PERCENT)
        
        if user.hp <= critical_threshold:
            logger.debug(f"Fallback check for Autoclave in apply_passive for {user.get_display_name()}")
            
            # Try to trigger now via the new system if there are targets
            if hasattr(game, 'try_trigger_autoclave'):
                game.try_trigger_autoclave(user)
            # If game doesn't have the new method (fallback for compatibility), use old logic
            elif self._has_eligible_targets(user, game) and not self.activated:
                logger.debug("Using legacy fallback method to trigger Autoclave")
                self._trigger_autoclave(user, game)
                self.activated = True
        
    def mark_ready_to_trigger(self) -> None:
        """
        Legacy method kept for backward compatibility.
        The new system uses direct triggering instead of this two-step process.
        """
        # Only log that this deprecated method was called
        from boneglaive.utils.debug import logger
        logger.debug("Deprecated mark_ready_to_trigger called for Autoclave. This method is now a no-op.")
            
    def _has_eligible_targets(self, user: 'Unit', game: 'Game') -> bool:
        """Check if there are any eligible targets for Autoclave."""
        from boneglaive.utils.debug import logger
        
        # Define the four directions (up, right, down, left)
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # Check each direction up to range 3
        for direction_idx, (dy, dx) in enumerate(directions):
            direction_name = ["upward", "rightward", "downward", "leftward"][direction_idx]
            logger.debug(f"Checking {direction_name} direction for Autoclave targets")
            
            for distance in range(1, 4):  # Range 1-3
                target_y = user.y + (dy * distance)
                target_x = user.x + (dx * distance)
                
                # Check if position is valid
                if not game.is_valid_position(target_y, target_x):
                    logger.debug(f"Position ({target_y},{target_x}) is out of bounds, skipping")
                    continue
                
                # Check if terrain is passable - stop checking this direction if we hit terrain
                if not game.map.is_passable(target_y, target_x):
                    logger.debug(f"Terrain at ({target_y},{target_x}) blocks Autoclave path, stopping this direction")
                    break
                    
                # Check if there's an enemy unit at this position
                target = game.get_unit_at(target_y, target_x)
                if target and target.player != user.player:
                    logger.debug(f"Found eligible Autoclave target: {target.get_display_name()} at ({target_y},{target_x})")
                    return True  # Found at least one eligible target
                
                logger.debug(f"No target at ({target_y},{target_x}), continuing search")
                    
        logger.debug("No eligible targets found for Autoclave in any direction")
        return False  # No eligible targets found
            
    def _trigger_autoclave(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """Execute the Autoclave retaliation effect."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        import time
        import curses
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
        
        logger.debug(f"EXECUTING AUTOCLAVE for {user.get_display_name()}")
        
        message_log.add_message(
            f"{user.get_display_name()}'s Autoclave activates",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Use passed UI parameter if provided, otherwise check the game for one
        if ui is None:
            # Get animation component from the game UI if available
            # We need to check if the game has a ui attribute since some tests may not have it
            ui = getattr(game, 'ui', None)
        
        # Define the four directions (up, right, down, left)
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # Track total damage dealt for healing
        total_damage = 0
        affected_units = []
        
        # Play the initial activation animation at the user's position
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence from asset manager
            animation_sequence = ui.asset_manager.get_skill_animation_sequence('autoclave')
            
            # Use renderer to animate at the center (user position)
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                animation_sequence,
                7,  # color ID
                0.5  # longer duration for dramatic effect
            )
            sleep_with_animation_speed(0.2)  # Small pause before the cross-attack
        
        # Check each direction up to range 3 and store valid target info
        targets_by_direction = {}
        for direction_idx, (dy, dx) in enumerate(directions):
            targets_in_direction = []
            
            for distance in range(1, 4):  # Range 1-3
                target_y = user.y + (dy * distance)
                target_x = user.x + (dx * distance)
                
                # Check if position is valid
                if not game.is_valid_position(target_y, target_x):
                    continue
                
                # Check if terrain is passable - stop the beam if it hits impassable terrain
                if not game.map.is_passable(target_y, target_x):
                    # Add position for animation but don't continue past this point
                    targets_in_direction.append((target_y, target_x))
                    break
                    
                # Mark this position for animation
                targets_in_direction.append((target_y, target_x))
                
                # Check if there's a unit at this position
                target = game.get_unit_at(target_y, target_x)
                if target and target.player != user.player:
                    # Calculate damage, accounting for defense
                    damage = max(1, 8 - target.defense)
                    
                    # Apply damage to target
                    previous_hp = target.hp
                    target.hp = max(0, target.hp - damage)
                    
                    # Track total damage for healing
                    total_damage += damage
                    affected_units.append(target)
                    
                    # Log the attack
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=target.get_display_name(),
                        damage=damage,  # Already using the calculated damage value
                        ability="Autoclave",
                        attacker_player=user.player,
                        target_player=target.player
                    )
                    
                    # Show damage number if UI is available
                    if ui and hasattr(ui, 'renderer'):
                        damage_text = f"-{damage}"
                        
                        # Make damage text more prominent with flashing effect
                        for i in range(3):
                            ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                            attrs = curses.A_BOLD if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, attrs)
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)
                        
                        # Final damage display (stays visible a bit longer)
                        ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.2)
                    
                    # Check if target was defeated and handle death properly
                    if target.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(target, user, cause="autoclave", ui=ui)
            
            # Store targets for animation
            if targets_in_direction:
                targets_by_direction[direction_idx] = targets_in_direction
                
        # Animate the cross-shaped attack in each direction if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the autoclave animation sequence
            beam_animation = ui.asset_manager.get_skill_animation_sequence('autoclave')
            if not beam_animation:
                beam_animation = ['+', 'X', '#']  # Fallback 
            
            # Animate each direction sequentially, cycling animation frames spatially
            for direction_idx, targets in targets_by_direction.items():
                # Cycle through animation frames along the beam path
                for i, (y, x) in enumerate(targets):
                    # Use modulo to cycle through animation frames spatially
                    frame_index = i % len(beam_animation)
                    single_frame = [beam_animation[frame_index]]  # Single frame animation

                    ui.renderer.animate_attack_sequence(
                        y, x,
                        single_frame,
                        7,  # color ID (white)
                        0.1  # quick but visible
                    )
                sleep_with_animation_speed(0.1)  # Small pause between directions
                
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Calculate healing (half of total damage dealt)
        healing = total_damage // 2
        if healing > 0:
            # Apply healing (don't exceed max HP)
            user.hp = min(user.max_hp, user.hp + healing)
            
            # Show healing number if UI is available
            if ui and hasattr(ui, 'renderer') and healing > 0:
                healing_text = f"+{healing}"
                
                # Make healing text prominent with flashing effect (green color)
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_damage_text(user.y-1, user.x*2, " " * len(healing_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_damage_text(user.y-1, user.x*2, healing_text, 3, attrs)  # Green color
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
                
                # Final healing display (stays on screen slightly longer)
                ui.renderer.draw_damage_text(user.y-1, user.x*2, healing_text, 3, curses.A_BOLD)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.3)
            
            # Log the healing
            message_log.add_message(
                f"{user.get_display_name()} absorbs life essence, healing for {healing} HP",
                MessageType.ABILITY,
                player=user.player
            )
            
            # Show healing animation if UI is available
            if ui and hasattr(ui, 'renderer'):
                # Flash the unit with green to indicate healing
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                    color_ids = [2, 3 if user.player == 1 else 4] * 2  # Alternate green with player color
                    durations = [0.1] * 4
                    
                    # Flash the unit
                    ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
                    
                # Show healing number above unit
                healing_text = f"+{healing}"
                if hasattr(ui.renderer, 'draw_text'):
                    import curses
                    # Make healing text more prominent
                    for i in range(3):
                        # Clear area first
                        ui.renderer.draw_damage_text(user.y-1, user.x*2, " " * len(healing_text), 2)
                        # Draw healing text
                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                        ui.renderer.draw_damage_text(user.y-1, user.x*2, healing_text, 2, attrs)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)


class PrySkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Pry forces an enemy unit straight up into the air where they slam into 
    the ceiling or skybox, breaking loose debris that crashes down with them.
    The primary target takes damage and has their movement reduced, while
    adjacent enemy units also take splash damage from falling debris.
    """
    
    def __init__(self):
        super().__init__(
            name="Pry",
            key="P",
            description="Pries an enemy up to range 1, damaging them and adjacent enemies with falling debris. Reduces target's movement by 1.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=1
        )
        self.primary_damage = 6  # Primary target damage
        self.splash_damage = 3   # Splash damage to adjacent units
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Pry can be used on the target."""
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            return False
            
        # Check if there's an enemy unit at target position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player:
            return False
        
        # Check if target is within range from the correct position
        # (either current position or planned move position)
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Remove the displacement position check - allow using Pry even if unit can't be moved
        # The execute method will handle the case where there are no valid displacement positions
        # by applying damage and movement penalty without displacement
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """
        Queue up the Pry skill for execution at the end of the turn.
        This now works similarly to move and attack actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order (assumes the Game instance is passed)
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown - done immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued (this was already correctly implemented)
        message_log.add_message(
            f"{user.get_display_name()} readies to pry {target.get_display_name()} skyward",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Pry skill during the turn resolution phase.
        This is called by the game engine when processing actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        import curses
        
        # Get target unit (might have moved)
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player:
            # Target is no longer valid
            message_log.add_message(
                "Pry failed: target no longer valid.",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Log the skill activation
        if game.chess_distance(user.y, user.x, target.y, target.x) == 1:
            message_log.add_message(
                f"{user.get_display_name()} pries {target.get_display_name()} skyward with their glaive",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} pries {target.get_display_name()} skyward with their glaive",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
            
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Calculate distance between user and target
            distance = game.chess_distance(user.y, user.x, target.y, target.x)
            
            # Get appropriate animation based on range
            if distance == 1:
                # Close range prying animation (using glaive as lever)
                lever_animation = ui.asset_manager.get_skill_animation_sequence('pry_range1')
                if not lever_animation:
                    lever_animation = ['┘', '┐', '┌', '└', '/']  # Fallback if animation not found
                
                # Show lever animation at user's position
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    lever_animation,
                    7,  # color ID (white)
                    0.2  # duration
                )
            else:
                # Extended range prying animation (extending glaive as lever)
                extended_animation = ui.asset_manager.get_skill_animation_sequence('pry_range2')
                if not extended_animation:
                    extended_animation = ['/', '-', '\\', '|', '-', '-', '=', '>', '*']  # Fallback if animation not found - ASCII only
                
                # Show initial animation at user's position (first part of the sequence)
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    extended_animation[:3],  # First few frames at attacker position
                    7,  # color ID (white)
                    0.2  # duration
                )
                
                # Get the path from the user to target
                from boneglaive.utils.coordinates import get_line, Position
                path = get_line(Position(user.y, user.x), Position(target.y, target.x))
                
                # If we have at least 3 points in the path (including start and end)
                if len(path) >= 3:
                    # Get the middle position for extending the glaive
                    mid_position = path[1]  # Second point in the path
                    mid_y, mid_x = mid_position.y, mid_position.x
                    
                    # Show the glaive extending through the middle position
                    # Use the middle portion of the animation sequence
                    extension_chars = extended_animation[3:6]  # Middle frames show extension
                    for char in extension_chars:
                        ui.renderer.draw_tile(mid_y, mid_x, char, 7)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                
                # Finally show the impact at target position with the last part of the animation
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    extended_animation[6:],  # Last frames at target position
                    7,  # color ID (white)
                    0.2  # duration
                )
            
            sleep_with_animation_speed(0.1)  # Small pause before launch
            
            # Now animate the target being launched upward - ONLY on the target's position
            launch_sequence = ui.asset_manager.get_skill_animation_sequence('pry_launch')
            if not launch_sequence:
                launch_sequence = ['^', '*', '|', ' ']  # Fallback - ASCII only
            
            # Store original position to ensure proper placement later
            temp_y, temp_x = target.y, target.x
            
            # Animate the unit going straight up
            ui.renderer.animate_attack_sequence(
                target.y, target.x,
                launch_sequence,
                7,  # color ID
                0.2  # quicker animation
            )
            
            # Temporarily hide the target by moving it off-screen for the animation
            target.y, target.x = -999, -999  # Move off-screen
            
            # Redraw to show target has "disappeared"
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            sleep_with_animation_speed(0.3)  # Pause while target is "in the ceiling"
            
            # Return target to original position for the impact
            target.y, target.x = temp_y, temp_x
            
            # Show impact animation - unit falling straight down on SAME tile
            impact_animation = ui.asset_manager.get_skill_animation_sequence('pry_impact')
            if not impact_animation:
                impact_animation = ['v', 'V', '@', '*', '.']  # Fallback - ASCII only
            
            ui.renderer.animate_attack_sequence(
                target.y, target.x,
                impact_animation,
                10,  # red background for impact (white text on red background)
                0.2  # duration
            )
            
            # Show debris falling animation - ONLY on the same tile (straight down)
            debris_animation = ui.asset_manager.get_skill_animation_sequence('pry_debris')
            if not debris_animation:
                debris_animation = ['@', '#', '*', '+', '.']  # Fallback
            
            ui.renderer.animate_attack_sequence(
                target.y, target.x,
                debris_animation,
                7,  # white color for debris
                0.2  # duration
            )
            
            # Redraw to show unit back in place
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            
            # Flash the target to show it was hit
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [10, 3 if target.player == 1 else 4] * 2  # Alternate red background with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
            
        # Apply damage to primary target (ignoring defense for part of the damage)
        # This represents the direct impact of hitting the ceiling and ground
        defense_reduced_damage = max(3, self.primary_damage - target.defense)  # 3 damage minimum
        previous_hp = target.hp
        target.hp = max(0, target.hp - defense_reduced_damage)
        
        # Log the primary damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=defense_reduced_damage,
            ability="Pry",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Check for critical health (retching) using centralized logic if target still alive
        if target.is_alive():
            game.check_critical_health(target, user, previous_hp, ui)
            
        # Apply splash damage to adjacent enemy units (secondary debris damage)
        affected_adjacents = []
        
        # Get all units in adjacent squares
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                # Skip the center (primary target)
                if dy == 0 and dx == 0:
                    continue
                
                # Check adjacent position
                adj_y = target.y + dy
                adj_x = target.x + dx
                
                # Validate position
                if not game.is_valid_position(adj_y, adj_x):
                    continue
                
                # Check if there's a unit at this position
                adjacent_unit = game.get_unit_at(adj_y, adj_x)
                if adjacent_unit and adjacent_unit.is_alive() and adjacent_unit.player != user.player:
                    # Apply splash damage (reduced by defense)
                    splash_damage = max(1, self.splash_damage - adjacent_unit.defense)
                    adjacent_unit.hp = max(0, adjacent_unit.hp - splash_damage)
                    
                    # Log splash damage
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=adjacent_unit.get_display_name(),
                        damage=splash_damage,
                        ability="Pry Debris",
                        attacker_player=user.player,
                        target_player=adjacent_unit.player
                    )
                    
                    # Add to affected units list for animation
                    affected_adjacents.append((adjacent_unit, splash_damage))
                    
                    # Check if the adjacent unit was defeated and handle death properly
                    if adjacent_unit.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(adjacent_unit, user, cause="pry_splash", ui=ui)
        
        # Show splash damage numbers for adjacent units if UI is available
        if ui and hasattr(ui, 'renderer') and affected_adjacents:
            # Get the debris animation for adjacents
            debris_animation = ui.asset_manager.get_skill_animation_sequence('pry_debris')
            if not debris_animation:
                debris_animation = ['@', '#', '*', '+', '.']  # Fallback
                
            # Animate debris and damage for each affected unit
            for adjacent_unit, splash_damage in affected_adjacents:
                # First show individual debris animation at the adjacent unit's position
                ui.renderer.animate_attack_sequence(
                    adjacent_unit.y, adjacent_unit.x,
                    debris_animation[-3:],  # Use last few frames (smaller debris chunks)
                    7,  # color ID (white)
                    0.15  # shorter duration for secondary effects
                )
                
                # Show damage number
                damage_text = f"-{splash_damage}"
                
                # Make damage text visible
                for i in range(2):  # Fewer flashes for secondary targets
                    ui.renderer.draw_damage_text(adjacent_unit.y-1, adjacent_unit.x*2, " " * len(damage_text), 7)
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_damage_text(adjacent_unit.y-1, adjacent_unit.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
                
                # Flash the adjacent unit to show it was hit with debris
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(adjacent_unit.type)] * 2
                    color_ids = [10, 3 if adjacent_unit.player == 1 else 4]  # Brief flash with red background
                    durations = [0.1] * 2
                    
                    ui.renderer.flash_tile(adjacent_unit.y, adjacent_unit.x, tile_ids, color_ids, durations)
        
        # Show primary damage number if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Show damage number for primary target
            damage_text = f"-{defense_reduced_damage}"
            
            # Make damage text more prominent
            for i in range(3):
                ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, attrs)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
            
            # Final damage display (stays on screen slightly longer)
            ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
            ui.renderer.refresh()
            sleep_with_animation_speed(0.2)
        
        # Check if primary target is immune to the movement penalty effect
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Pry's movement penalty due to Stasiality",
                MessageType.ABILITY,
                player=target.player,  # Use the target's player for correct color coding
                target_name=target.get_display_name()
            )
        else:
            # Apply movement reduction effect to primary target
            target.move_range_bonus = -1
            target.was_pried = True  # Mark the unit as affected by Pry

            # Add a duration property for UI status display - use 2 for clearer visibility
            # This will count down once at end of turn and still remain visible next turn
            target.pry_duration = 2  # Will last until the end of next turn

            # Add a debug message
            logger.info(f"Applied Pry effect to {target.get_display_name()} with duration {target.pry_duration}")

            # Ensure the unit has a boolean flag that's easier to check in the UI
            target.pry_active = True

            # CASE 1: Check if the target is trapped by a Viceroy trap and free them
            if hasattr(target, 'trapped_by') and target.trapped_by is not None:
                # Clear the trap - messaging is handled elsewhere
                target.trapped_by = None

            # CASE 2: Check if the target has trapped other units with Viceroy trap and release them
            for unit in game.units:
                if hasattr(unit, 'trapped_by') and unit.trapped_by == target:
                    # Clear the trap - messaging is handled elsewhere
                    unit.trapped_by = None

            # Log the movement reduction
            message_log.add_message(
                f"{target.get_display_name()}'s movement reduced by 1 for next turn",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
            
        # Check if primary target was defeated and handle death properly
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="vault", ui=ui)
        
        return True


class VaultSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Vault allows the GLAIVEMAN to leap over obstacles and enemies,
    landing in an empty space within range.
    """
    
    def __init__(self):
        super().__init__(
            name="Vault",
            key="V",
            description="Leap over obstacles to any empty position within range, ignoring pathing restrictions.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=2
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Vault can be used on the target position."""
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

        # Check if any other unit is already planning to teleport to this position
        # (via Vault, Delta Config, Grae Exchange, or any other teleport skill)
        for other_unit in game.units:
            if (other_unit.is_alive() and other_unit != user):
                # Check for vault targets
                if (hasattr(other_unit, 'vault_target_indicator') and
                    other_unit.vault_target_indicator == target_pos):
                    # Position is already targeted by another unit's vault
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    # Position is already targeted by another unit's teleport
                    return False

        # Check if target is within range from the correct position
        # (either current position or planned move position)
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
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
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set vault target indicator for UI
        user.vault_target_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} prepares to vault to position ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Vault skill to leap over obstacles to a target position."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        
        # Clear the vault target indicator after execution
        user.vault_target_indicator = None
        
        # Store original position for animations
        original_pos = (user.y, user.x)
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get vault animation sequence
            vault_animation = ui.asset_manager.get_skill_animation_sequence('vault')
            if not vault_animation:
                vault_animation = ['^', 'A', '|', '*', '|']  # Fallback - ASCII only
                
            # Get landing animation sequence
            landing_animation = ui.asset_manager.get_skill_animation_sequence('vault_impact')
            if not landing_animation:
                landing_animation = ['v', 'V', '@', '*', '.']  # Fallback - ASCII only
                
            # Show preparation animation at original position
            ui.renderer.animate_attack_sequence(
                original_pos[0], original_pos[1],
                vault_animation,
                7,  # white color
                0.12  # duration
            )
            
            # Calculate path for visual effect (simplified - just a line)
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(original_pos[0], original_pos[1]), Position(target_pos[0], target_pos[1]))
            
            # If path has intermediate points, show arc animation
            if len(path) > 2:  # More than just start and end
                # Get middle positions of path to show arc
                mid_positions = path[1:-1]  # Skip first (start) and last (end) positions
                
                # Create arc visuals with ascending/descending characters
                arc_chars = []
                
                # First half ascending
                for i in range(len(mid_positions) // 2):
                    arc_chars.append('^')
                
                # Apex
                if len(mid_positions) % 2 == 1:  # If odd number of midpoints
                    arc_chars.append('*')
                    
                # Second half descending
                for i in range((len(mid_positions) + 1) // 2, len(mid_positions)):
                    arc_chars.append('v')
                
                # Store original terrain information for restoration
                terrain_info = []
                for pos in mid_positions:
                    terrain_type = game.map.get_terrain_at(pos.y, pos.x)
                    terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                    terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                    
                    # Determine appropriate terrain color based on terrain type
                    if terrain_name == 'empty':
                        terrain_color = 1  # Default (white on black)
                    elif terrain_name == 'dust':
                        terrain_color = 11  # Dust color
                    elif terrain_name == 'limestone':
                        terrain_color = 12  # Limestone color
                    elif terrain_name == 'pillar':
                        terrain_color = 13  # Pillar color
                    elif terrain_name == 'furniture' or terrain_name.startswith('coat_rack') or terrain_name.startswith('ottoman'):
                        terrain_color = 14  # Furniture color
                    elif terrain_name == 'marrow_wall':
                        terrain_color = 20  # Marrow Wall color
                    else:
                        terrain_color = 1  # Default for unknown types
                    
                    # Store unit if present for restoration
                    other_unit = game.get_unit_at(pos.y, pos.x)
                    
                    terrain_info.append({
                        'position': (pos.y, pos.x),
                        'terrain_tile': terrain_tile,
                        'terrain_color': terrain_color,
                        'unit': other_unit
                    })
                
                # Show arc animation along path midpoints
                for i, pos in enumerate(mid_positions):
                    char = arc_chars[i] if i < len(arc_chars) else '⋅'
                    ui.renderer.draw_tile(pos.y, pos.x, char, 7)  # White color
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.08)
                    
                    # Restore proper terrain after animation frame
                    if i < len(terrain_info):
                        info = terrain_info[i]
                        # Check if there's a unit at this position
                        if info['unit'] and info['unit'] != user:
                            # Draw the unit instead of terrain
                            unit_tile = ui.asset_manager.get_unit_tile(info['unit'].type)
                            unit_color = 3 if info['unit'].player == 1 else 4  # Player colors
                            ui.renderer.draw_tile(info['position'][0], info['position'][1], unit_tile, unit_color)
                        else:
                            # Draw appropriate terrain with correct color
                            ui.renderer.draw_tile(info['position'][0], info['position'][1], 
                                                info['terrain_tile'], info['terrain_color'])
            
            # Temporarily hide the unit
            temp_y, temp_x = user.y, user.x
            user.y, user.x = -999, -999  # Move off-screen
            
            # Redraw to show unit is gone from original position
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                
            # Get landing terrain information for restoration after animation
            landing_terrain_type = game.map.get_terrain_at(target_pos[0], target_pos[1])
            landing_terrain_name = landing_terrain_type.name.lower() if hasattr(landing_terrain_type, 'name') else 'empty'
            landing_terrain_tile = ui.asset_manager.get_terrain_tile(landing_terrain_name)
            
            # Determine appropriate terrain color for landing position
            if landing_terrain_name == 'empty':
                landing_terrain_color = 1  # Default (white on black)
            elif landing_terrain_name == 'dust':
                landing_terrain_color = 11  # Dust color
            elif landing_terrain_name == 'limestone':
                landing_terrain_color = 12  # Limestone color
            elif landing_terrain_name == 'pillar':
                landing_terrain_color = 13  # Pillar color
            elif landing_terrain_name == 'furniture' or landing_terrain_name.startswith('coat_rack') or landing_terrain_name.startswith('ottoman'):
                landing_terrain_color = 14  # Furniture color
            elif landing_terrain_name == 'marrow_wall':
                landing_terrain_color = 20  # Marrow Wall color
            else:
                landing_terrain_color = 1  # Default for unknown types
                
            # Show landing animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                landing_animation,
                7,  # white color
                0.12  # duration
            )
            
            # Restore proper terrain at landing position before placing unit
            ui.renderer.draw_tile(target_pos[0], target_pos[1], 
                                landing_terrain_tile, landing_terrain_color)
            
            # Move user to target position
            user.y, user.x = target_pos
            
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                
            # Flash the unit to emphasize landing
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [7, 3 if user.player == 1 else 4] * 2  # Alternate white with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        else:
            # No UI, just set position without animations
            user.y, user.x = target_pos
        
        # Log the completion of vault
        message_log.add_message(
            f"{user.get_display_name()} vaults from ({original_pos[0]}, {original_pos[1]}) to ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True


class JudgementSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Delivers divine judgement via a sacred spinning glaive, dealing piercing damage.
    """
    
    def __init__(self):
        super().__init__(
            name="Judgement",
            key="J",
            description="Throw a sacred glaive at an enemy (range 4). Deals pierce damage that ignores defense.",
            target_type=TargetType.ENEMY,
            cooldown=4,
            range_=4
        )
        self.damage = 4
    
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
            
        # Check if target is within range from the correct position
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check if there's line of sight to the target
        if not game.has_line_of_sight(from_y, from_x, target_pos[0], target_pos[1]):
            return False
            
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])  
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} readies a sacred glaive to throw at {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Judgement skill to deliver divine judgment via a sacred spinning glaive."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        import curses
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} hurls a sacred glaive",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            throw_animation = ui.asset_manager.get_skill_animation_sequence('judgement')
            if not throw_animation:
                throw_animation = ['*', '+', 'x', 'o', 'O', '@']  # Fallback - ASCII characters only

            # Get critical animation
            critical_animation = ui.asset_manager.get_skill_animation_sequence('judgement_critical')
            if not critical_animation:
                critical_animation = ['!', '*', '+', '%', '@']  # Fallback - ASCII characters only
                
            # Get the path from user to target
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(user.y, user.x), Position(target.y, target.x))
            
            # Show wind-up and throw motion at user position using proper animation method
            windup_frames = throw_animation[:3] if len(throw_animation) >= 3 else throw_animation
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                windup_frames,
                7,  # White color
                0.25  # Total duration for wind-up
            )
            
            # Animate the glaive moving along the path with single-tile precision
            if len(path) > 1:
                # Get spinning glaive frames for projectile animation
                spinning_frames = throw_animation[3:5] if len(throw_animation) >= 5 else ['*', '+']
                
                # Store original terrain for each position to restore later
                terrain_backup = []
                for pos in path[1:-1]:  # Skip start and end positions
                    terrain_type = game.map.get_terrain_at(pos.y, pos.x)
                    terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                    terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                    
                    # Determine terrain color
                    if terrain_name == 'empty':
                        terrain_color = 1
                    elif terrain_name == 'dust':
                        terrain_color = 11
                    elif terrain_name == 'limestone':
                        terrain_color = 12
                    elif terrain_name == 'pillar':
                        terrain_color = 13
                    elif terrain_name == 'furniture' or terrain_name.startswith('coat_rack') or terrain_name.startswith('ottoman'):
                        terrain_color = 14
                    elif terrain_name == 'marrow_wall':
                        terrain_color = 20
                    else:
                        terrain_color = 1
                    
                    terrain_backup.append((pos, terrain_tile, terrain_color))
                
                # Animate projectile moving along path
                for i, (pos, original_tile, original_color) in enumerate(terrain_backup):
                    # Show projectile at current position
                    projectile_char = spinning_frames[i % len(spinning_frames)]
                    ui.renderer.draw_tile(pos.y, pos.x, projectile_char, 7)  # White color
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.05)  # Quick movement
                    
                    # Restore original terrain immediately after showing projectile
                    ui.renderer.draw_tile(pos.y, pos.x, original_tile, original_color)
                
                # Final refresh to ensure everything is restored
                ui.renderer.refresh()
            
            # Show impact at target position - single tile only
            if len(throw_animation) >= 6:
                impact_char = throw_animation[5]  # Last frame for impact
                # Store original unit tile for restoration
                original_unit_tile = ui.asset_manager.get_unit_tile(target.type)
                original_color = 3 if target.player == 1 else 4
                
                # Show impact effect on target tile only
                for i in range(4):  # Quick impact flash
                    ui.renderer.draw_tile(target.y, target.x, impact_char, 7, curses.A_BOLD)  # White color with bold (same as STAINED_STONE)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.05)
                    
                    # Restore unit tile
                    ui.renderer.draw_tile(target.y, target.x, original_unit_tile, original_color)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.05)
                
            # Always show base effect message
            message_log.add_message(
                f"The sacred glaive bypasses {target.get_display_name()}'s defenses",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
            
            # Check if the target is at critical health for enhanced animation
            from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
            critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
            is_critical_target = target.hp <= critical_threshold
            
            # Use flash_tile method instead of draw_tile to ensure proper containment to unit tile only
            if hasattr(ui, 'asset_manager'):
                # Create critical effect using flash_tile (which is properly constrained)
                original_unit_tile = ui.asset_manager.get_unit_tile(target.type)
                
                if is_critical_target:
                    # Enhanced critical effect for critical targets
                    for iteration in range(3):
                        # Flash with critical animation frames
                        tile_ids = [original_unit_tile, '!', original_unit_tile, '*', original_unit_tile, '+']
                        color_ids = [3 if target.player == 1 else 4, 6, 3 if target.player == 1 else 4, 6, 3 if target.player == 1 else 4, 6]
                        durations = [0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
                        
                        ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
                        sleep_with_animation_speed(0.05)
                else:
                    # Regular critical effect
                    tile_ids = [original_unit_tile, '!', original_unit_tile, '*', original_unit_tile]
                    color_ids = [3 if target.player == 1 else 4, 6, 3 if target.player == 1 else 4, 6, 3 if target.player == 1 else 4]
                    durations = [0.03, 0.03, 0.03, 0.03, 0.03]
                    
                    ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
            
            # Flash the target to show impact
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [10, 3 if target.player == 1 else 4] * 2  # Alternate red background with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Check if target is at critical health for double damage
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
        is_critical_hit = target.hp <= critical_threshold
        
        # Apply damage with critical bonus if applicable
        base_damage = self.damage  # Base damage
        
        # Double damage if target is at critical health
        if is_critical_hit:
            damage = base_damage * 2  # Critical hit doubles damage
            # Log critical effect
            message_log.add_message(
                f"The sacred glaive strikes with divine judgement",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
        else:
            damage = base_damage
        
        # Store previous HP for animation
        previous_hp = target.hp
        
        # Apply damage (piercing - ignores defense)
        target.hp = max(0, target.hp - damage)
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Judgement",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Show damage number after animations complete
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{damage}"
            
            for i in range(3):
                ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, attrs)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
        
        # Check if target was defeated and handle death properly
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="judgement", ui=ui)
            
        # Redraw the board after animations
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            
        return True