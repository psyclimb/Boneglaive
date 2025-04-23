#!/usr/bin/env python3
"""
Skills and abilities system for Boneglaive units.
This module provides the foundation for implementing unit skills.
"""

import curses
from enum import Enum, auto
from typing import Optional, Dict, List, Any, Tuple, TYPE_CHECKING
from boneglaive.utils.constants import UnitType, UNIT_STATS

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class SkillType(Enum):
    """Types of skills available to units."""
    PASSIVE = auto()    # Always active
    ACTIVE = auto()     # Activated by the player


class TargetType(Enum):
    """Types of targets for skills."""
    SELF = auto()       # Targets the unit itself
    ALLY = auto()       # Targets a single ally
    ENEMY = auto()      # Targets a single enemy
    AREA = auto()       # Targets an area
    NONE = auto()       # No target needed


class Skill:
    """Base class for all skills."""
    
    def __init__(self, 
                 name: str, 
                 key: str,  # Single key used to activate the skill
                 description: str,
                 skill_type: SkillType,
                 target_type: TargetType,
                 cooldown: int = 0,
                 range_: int = 0,
                 area: int = 0):
        self.name = name
        self.key = key
        self.description = description
        self.skill_type = skill_type
        self.target_type = target_type
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.range = range_  # How far the skill can be used
        self.area = area     # Area of effect (0 for single target)
        
        # Special cooldown debug string
        import random
        self.id = f"{name}-{random.randint(1000, 9999)}"
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        # Check cooldown
        if self.current_cooldown > 0:
            return False
        
        # Echo units cannot use skills (they can only do basic attacks)
        if hasattr(user, 'is_echo') and user.is_echo:
            from boneglaive.utils.debug import logger
            logger.debug(f"Skill cannot be used by echo unit: {user.get_display_name()}")
            return False
            
        # Additional checks can be implemented in subclasses
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Use the skill. Return True if successful."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        # Skill effect implemented in subclasses
        return True
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """Apply passive effect. Override in passive skill subclasses."""
        pass
        
    def tick_cooldown(self) -> None:
        """Reduce cooldown by 1."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class PassiveSkill(Skill):
    """Base class for passive skills that are always active."""
    
    def __init__(self, name: str, key: str, description: str):
        super().__init__(
            name=name,
            key=key,
            description=description,
            skill_type=SkillType.PASSIVE,
            target_type=TargetType.NONE,
            cooldown=0,
            range_=0,
            area=0
        )


class ActiveSkill(Skill):
    """Base class for active skills that the player can use."""
    
    def __init__(self, name: str, key: str, description: str, target_type: TargetType, 
                 cooldown: int, range_: int, area: int = 0):
        super().__init__(
            name=name,
            key=key,
            description=description,
            skill_type=SkillType.ACTIVE,
            target_type=target_type,
            cooldown=cooldown,
            range_=range_,
            area=area
        )


# Placeholder skill classes for GLAIVEMAN
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
            description="When wretched or damaged while at critical health, unleashes a cross-shaped attack in four directions (range 3) and heals for half the damage dealt. One-time use. Requires enemy in range."
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
        
        logger.debug(f"EXECUTING AUTOCLAVE for {user.get_display_name()}")
        
        message_log.add_message(
            f"{user.get_display_name()}'s Autoclave activates!",
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
            time.sleep(0.2)  # Small pause before the cross-attack
        
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
                    
                    # Check if target was defeated
                    if target.hp <= 0:
                        message_log.add_message(
                            f"{target.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=user.player,
                            target=target.player,
                            target_name=target.get_display_name()
                        )
            
            # Store targets for animation
            if targets_in_direction:
                targets_by_direction[direction_idx] = targets_in_direction
                
        # Animate the cross-shaped attack in each direction if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Simplified animation sequence for each directional beam
            beam_animation = ['+', 'X', '#'] 
            
            # Animate each direction sequentially
            for direction_idx, targets in targets_by_direction.items():
                for y, x in targets:
                    ui.renderer.animate_attack_sequence(
                        y, x,
                        beam_animation,
                        7,  # color ID (white)
                        0.1  # quick but visible
                    )
                time.sleep(0.1)  # Small pause between directions
                
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Calculate healing (half of total damage dealt)
        healing = total_damage // 2
        if healing > 0:
            # Apply healing (don't exceed max HP)
            user.hp = min(user.max_hp, user.hp + healing)
            
            # Log the healing
            message_log.add_message(
                f"{user.get_display_name()} absorbs life essence, healing for {healing} HP!",
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
                        ui.renderer.draw_text(user.y-1, user.x*2, " " * len(healing_text), 2)
                        # Draw healing text
                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                        ui.renderer.draw_text(user.y-1, user.x*2, healing_text, 2, attrs)
                        ui.renderer.refresh()
                        time.sleep(0.1)


class PrySkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Pry launches an enemy unit straight up into the air where they slam into 
    the ceiling or skybox, breaking loose debris that crashes down with them.
    The primary target takes damage and has their movement reduced, while
    adjacent enemy units also take splash damage from falling debris.
    """
    
    def __init__(self):
        super().__init__(
            name="Pry",
            key="P",
            description="Launches enemy up to range 2, damaging them and adjacent enemies with falling debris. Reduces target's movement by 1.",
            target_type=TargetType.ENEMY,
            cooldown=2,
            range_=2
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
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} readies to launch {target.get_display_name()} skyward!",
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
                f"{user.get_display_name()} pries {target.get_display_name()} upward with their glaive!",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} launches {target.get_display_name()} skyward with their glaive!",
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
                    extended_animation = ['/', '―', '\\', '|', '─', '─', '═', '→', '↗']  # Fallback if animation not found
                
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
                        time.sleep(0.1)
                
                # Finally show the impact at target position with the last part of the animation
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    extended_animation[6:],  # Last frames at target position
                    7,  # color ID (white)
                    0.2  # duration
                )
            
            time.sleep(0.1)  # Small pause before launch
            
            # Now animate the target being launched upward - ONLY on the target's position
            launch_sequence = ui.asset_manager.get_skill_animation_sequence('pry_launch')
            if not launch_sequence:
                launch_sequence = ['↑', '↟', '⇑', ' ']  # Fallback (single character symbols)
            
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
            time.sleep(0.3)  # Pause while target is "in the ceiling"
            
            # Return target to original position for the impact
            target.y, target.x = temp_y, temp_x
            
            # Show impact animation - unit falling straight down on SAME tile
            impact_animation = ui.asset_manager.get_skill_animation_sequence('pry_impact')
            if not impact_animation:
                impact_animation = ['↓', 'V', '@', '*', '.']  # Fallback
            
            ui.renderer.animate_attack_sequence(
                target.y, target.x,
                impact_animation,
                5,  # reddish color for impact
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
                color_ids = [5, 3 if target.player == 1 else 4] * 2  # Alternate red with player color
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
                    
                    # Check if the adjacent unit was defeated
                    if adjacent_unit.hp <= 0:
                        message_log.add_message(
                            f"{adjacent_unit.get_display_name()} perishes from falling debris!",
                            MessageType.COMBAT,
                            player=user.player,
                            target=adjacent_unit.player,
                            target_name=adjacent_unit.get_display_name()
                        )
        
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
                    ui.renderer.draw_text(adjacent_unit.y-1, adjacent_unit.x*2, " " * len(damage_text), 7)
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_text(adjacent_unit.y-1, adjacent_unit.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    time.sleep(0.1)
                
                # Flash the adjacent unit to show it was hit with debris
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(adjacent_unit.type)] * 2
                    color_ids = [5, 3 if adjacent_unit.player == 1 else 4]  # Brief flash
                    durations = [0.1] * 2
                    
                    ui.renderer.flash_tile(adjacent_unit.y, adjacent_unit.x, tile_ids, color_ids, durations)
        
        # Show primary damage number if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Show damage number for primary target
            damage_text = f"-{defense_reduced_damage}"
            
            # Make damage text more prominent
            for i in range(3):
                ui.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
                ui.renderer.refresh()
                time.sleep(0.1)
            
            # Final damage display (stays on screen slightly longer)
            ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
            ui.renderer.refresh()
            time.sleep(0.2)
        
        # Check if primary target is immune to the movement penalty effect
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Pry's movement penalty due to Stasiality!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
        else:
            # Apply movement reduction effect to primary target
            target.move_range_bonus = -1
            target.was_pried = True  # Mark the unit as affected by Pry
            
            # Log the movement reduction
            message_log.add_message(
                f"{target.get_display_name()}'s movement reduced by 1 for next turn!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
            
        # Check if primary target was defeated
        if target.hp <= 0:
            message_log.add_message(
                f"{target.get_display_name()} perishes!",
                MessageType.COMBAT,
                player=user.player,
                target=target.player,
                target_name=target.get_display_name()
            )
        
        return True

# Additional GLAIVEMAN Skills
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
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        original_pos = (user.y, user.x)
        user.y, user.x = target_pos
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} vaults to position ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        return True

class JudgementThrowSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Throws a sacred spinning glaive at an enemy unit, dealing piercing damage.
    """
    
    def __init__(self):
        super().__init__(
            name="Judgement Throw",
            key="J",
            description="Throw a sacred glaive at an enemy (range 3). Deals pierce damage that ignores defense.",
            target_type=TargetType.ENEMY,
            cooldown=2,
            range_=3
        )
        self.damage = 4
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        from boneglaive.utils.message_log import message_log, MessageType
        # Apply damage
        target.hp = max(0, target.hp - self.damage)
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=self.damage,
            ability="Judgement Throw",
            attacker_player=user.player,
            target_player=target.player
        )
        return True

class SiteInspectionSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Surveys an area, granting bonuses to allies near terrain.
    """
    
    def __init__(self):
        super().__init__(
            name="Site Inspection",
            key="S",
            description="Survey a 3x3 area. Grants movement and attack bonuses to allies.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3,
            area=1
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} inspects the site around ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        return True

class DeltaConfigSkill(ActiveSkill):
    """Active skill for GRAYMAN. Teleports to any unoccupied tile on the map."""
    
    def __init__(self):
        super().__init__(
            name="Delta Config",
            key="D",
            description="Teleport to any unoccupied tile on the map.",
            target_type=TargetType.AREA,
            cooldown=12,
            range_=99
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        original_pos = (user.y, user.x)
        user.y, user.x = target_pos
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} teleports to position ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        return True

class EstrangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Phases a target out of normal spacetime."""
    
    def __init__(self):
        super().__init__(
            name="Estrange",
            key="E",
            description="Fire a beam that phases target out of normal spacetime. Target receives -1 to all actions.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )
        self.damage = 2
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        from boneglaive.utils.message_log import message_log, MessageType
        # Apply damage
        target.hp = max(0, target.hp - self.damage)
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=self.damage,
            ability="Estrange",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Apply estranged effect if not immune
        if not target.is_immune_to_effects():
            target.estranged = True
            message_log.add_message(
                f"{target.get_display_name()} is phased out of normal spacetime!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to Estrange due to Stasiality!",
                MessageType.ABILITY,
                player=user.player
            )
        return True

class GraeExchangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Creates an echo that can attack but not move."""
    
    def __init__(self):
        super().__init__(
            name="Græ Exchange",
            key="G",
            description="Create an echo at current position and teleport away. Echo can attack but not move.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        original_pos = (user.y, user.x)
        user.y, user.x = target_pos
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} creates an echo and teleports to ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        return True

class Stasiality(PassiveSkill):
    """Passive skill for GRAYMAN. Immune to status effects and displacement."""
    
    def __init__(self):
        super().__init__(
            name="Stasiality",
            key="S",
            description="Cannot have stats changed or be displaced. Immune to buffs, debuffs, forced movement, and terrain effects."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        # Implementation handled in Unit.is_immune_to_effects()
        pass

class Viseroy(PassiveSkill):
    """Passive skill for MANDIBLE_FOREMAN. Traps enemies in mechanical jaws."""
    
    def __init__(self):
        super().__init__(
            name="Viseroy",
            key="V",
            description="When attacking, traps the enemy unit in mechanical jaws. Trapped units cannot move and take damage each turn."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        # Implementation handled in Game engine
        pass

class DischargeSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Renamed to Expedite in the code. Rushes forward in a straight line.
    """
    
    def __init__(self):
        super().__init__(
            name="Expedite",  # Renamed from Discharge to Expedite
            key="E",
            description="Rush up to 4 tiles in a line. Automatically trap and damage the first enemy encountered.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=4
        )
        self.trap_damage = 6
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} expedites forward!",
            MessageType.ABILITY,
            player=user.player
        )
        user.y, user.x = target_pos
        return True

class JawlineSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Deploys a network of smaller mechanical jaws in a 3×3 area.
    """
    
    def __init__(self):
        super().__init__(
            name="Jawline",
            key="J",
            description="Deploy network of mechanical jaws in 3x3 area around yourself. Deals 4 damage and reduces enemy movement by 1 for 3 turns.",
            target_type=TargetType.SELF,
            cooldown=5,
            range_=0,
            area=1
        )
        self.damage = 4
        self.effect_duration = 3
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # For self-targeted skills, use the unit's position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} deploys JAWLINE network!",
            MessageType.ABILITY,
            player=user.player
        )
        return True

# Define the skills available for each unit type
UNIT_SKILLS = {
    "GLAIVEMAN": {
        "passive": Autoclave(),
        "active": [PrySkill(), VaultSkill(), JudgementThrowSkill()]
    },
    "MANDIBLE_FOREMAN": {
        "passive": Viseroy(),
        "active": [DischargeSkill(), SiteInspectionSkill(), JawlineSkill()]
    },
    "GRAYMAN": {
        "passive": Stasiality(),
        "active": [DeltaConfigSkill(), EstrangeSkill(), GraeExchangeSkill()]
    }
}
