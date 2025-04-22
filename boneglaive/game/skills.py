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
        self.ready_to_trigger = False  # Flag for when conditions are met to trigger
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """
        Apply the Autoclave passive effect.
        Triggers when a unit is brought to critical health but not killed.
        """
        if self.activated or not game:
            return
            
        # Check if the unit is in critical health
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        critical_threshold = int(user.max_hp * CRITICAL_HEALTH_PERCENT)
        
        if user.hp <= critical_threshold and self.ready_to_trigger:
            # Check if there are any eligible targets before triggering
            if self._has_eligible_targets(user, game):
                # This means the unit just entered critical health this turn and has targets
                self._trigger_autoclave(user, game)
                # Mark as activated so it can't be used again
                self.activated = True
            else:
                # No eligible targets, don't trigger the skill but keep it ready
                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"GLAIVEMAN's Autoclave fails to activate - no targets in range!",
                    MessageType.ABILITY,
                    player=user.player
                )
                
            # Reset ready flag regardless
            self.ready_to_trigger = False
            
    def mark_ready_to_trigger(self) -> None:
        """Mark the skill as ready to trigger on the next apply_passive call."""
        if not self.activated:
            self.ready_to_trigger = True
            
    def _has_eligible_targets(self, user: 'Unit', game: 'Game') -> bool:
        """Check if there are any eligible targets for Autoclave."""
        # Define the four directions (up, right, down, left)
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # Check each direction up to range 3
        for dy, dx in directions:
            for distance in range(1, 4):  # Range 1-3
                target_y = user.y + (dy * distance)
                target_x = user.x + (dx * distance)
                
                # Check if position is valid
                if not game.is_valid_position(target_y, target_x):
                    continue
                
                # Check if terrain is passable - stop checking this direction if we hit terrain
                if not game.map.is_passable(target_y, target_x):
                    break
                    
                # Check if there's an enemy unit at this position
                target = game.get_unit_at(target_y, target_x)
                if target and target.player != user.player:
                    return True  # Found at least one eligible target
                    
        return False  # No eligible targets found
            
    def _trigger_autoclave(self, user: 'Unit', game: 'Game') -> None:
        """Execute the Autoclave retaliation effect."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        
        message_log.add_message(
            f"{user.get_display_name()}'s Autoclave activates!",
            MessageType.ABILITY,
            player=user.player
        )
        
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
    Pry displaces the targeted unit to 3 tiles away from the GLAIVEMAN,
    reduces that unit's move value by 1 on their next turn, and deals damage.
    Visually, the GLAIVEMAN shoves his glaive polearm into the ground under 
    the enemy's feet and pries them into a new position like it's a lever.
    """
    
    def __init__(self):
        super().__init__(
            name="Pry",
            key="P",
            description="Displaces target enemy 3 tiles away, reduces movement by 1 next turn, and deals damage.",
            target_type=TargetType.ENEMY,
            cooldown=1,
            range_=1
        )
        self.damage = 5  # Fixed damage amount
        
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
            f"{user.get_display_name()} readies Pry against {target.get_display_name()}!",
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
            
        # Calculate usable displacement positions
        displacement_positions = self._get_displacement_positions(user, target, game)
        
        if not displacement_positions:
            # No valid positions, but still apply damage and movement penalty
            message_log.add_message(
                f"{user.get_display_name()} uses Pry on {target.get_display_name()}!",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
            
            # Play animation if UI is available
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Get animation sequence for Pry
                animation_sequence = ui.asset_manager.get_skill_animation_sequence('pry')
                if animation_sequence:
                    # Show animation at user's position
                    ui.renderer.animate_attack_sequence(
                        user.y, user.x,
                        animation_sequence,
                        7,  # color ID
                        0.3  # duration
                    )
                    time.sleep(0.2)
                    
                    # Show lever effect animation between user and target
                    lever_positions = self._get_lever_positions(user, target)
                    for y, x in lever_positions:
                        ui.renderer.animate_attack_sequence(
                            y, x,
                            ['/', '|', '\\'],
                            7,  # color ID
                            0.1  # quick animation
                        )
            
            # Apply damage to target, accounting for defense
            damage = max(1, self.damage - target.defense)
            previous_hp = target.hp
            target.hp = max(0, target.hp - damage)
            
            # Log the damage
            message_log.add_combat_message(
                attacker_name=f"{user.type.name}",
                target_name=f"{target.type.name}",
                damage=damage,  # Use the calculated damage value
                ability="Pry",
                attacker_player=user.player,
                target_player=target.player
            )
            
            # Check if target is immune to the effect
            if target.is_immune_to_effects():
                message_log.add_message(
                    f"{target.get_display_name()} is immune to Pry due to Stasiality!",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=target.get_display_name()
                )
                return True  # Continue with damage, just don't apply movement effects
                
            # Apply movement reduction effect and mark unit as pried
            target.move_range_bonus = -1
            target.was_pried = True  # Mark the unit as affected by Pry
            
            # Log the movement reduction
            message_log.add_message(
                f"{target.get_display_name()}'s movement reduced by 1 for next turn!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
            
            # Note: The engine will handle releasing trapped units automatically
            
            # No need for a message about being braced against terrain - it's implied
            
            # Show collision animation at the target's current position
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Get collision animation
                impact_animation = ui.asset_manager.get_skill_animation_sequence('pry_collision')
                
                # Show impact animation at target's current position (no displacement)
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    impact_animation,
                    5,  # color ID for collision
                    0.25  # duration
                )
                
                # Flash the target to show it was hit
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                    color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 2
                    durations = [0.1] * 4
                    
                    # Use renderer's flash tile method
                    ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
                
                # Show damage number - use calculated damage after defense reduction
                damage_text = f"-{damage}"
                
                # Make damage text more prominent
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    time.sleep(0.1)
                
                # Final damage display (stays on screen slightly longer)
                ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
                ui.renderer.refresh()
                time.sleep(0.2)
                
            # No actual displacement, but the skill still did damage
            return True
            
        # Choose the best displacement position
        best_pos = self._select_best_displacement(displacement_positions, game)
        
        # Handle case where no valid positions were found (shouldn't happen with our validation, but just in case)
        if best_pos is None:
            message_log.add_message(
                f"Pry failed: no valid displacement positions.",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} uses Pry on {target.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get animation sequence for Pry
            animation_sequence = ui.asset_manager.get_skill_animation_sequence('pry')
            if animation_sequence:
                # Show animation at user's position
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    animation_sequence,
                    7,  # color ID
                    0.3  # duration
                )
                time.sleep(0.2)
                
                # Show lever effect animation between user and target
                lever_positions = self._get_lever_positions(user, target)
                for y, x in lever_positions:
                    ui.renderer.animate_attack_sequence(
                        y, x,
                        ['/', '|', '\\'],
                        7,  # color ID
                        0.1  # quick animation
                    )
            
        # Apply damage to target, accounting for defense
        damage = max(1, self.damage - target.defense)
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,  # Use the calculated damage value
            ability="Pry",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Check if target is immune to the effect
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Pry due to Stasiality!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
            return False
            
        # Apply movement reduction effect and mark unit as pried
        target.move_range_bonus = -1
        target.was_pried = True  # Mark the unit as affected by Pry
        
        # Log the movement reduction
        message_log.add_message(
            f"{target.get_display_name()}'s movement reduced by 1 for next turn!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        # Store original position for animation
        original_y, original_x = target.y, target.x
        
        # Displace the target to the selected position
        target.y, target.x = best_pos
        
        # Calculate displacement distance
        displacement_distance = game.chess_distance(original_y, original_x, best_pos[0], best_pos[1])
        
        # Explicitly check for trap release due to position change
        game._check_position_change_trap_release(target, original_y, original_x)
        
        # Log the displacement with additional details if needed
        if displacement_distance < 3:
            # If displaced less than the full 3 tiles, the unit probably hit an obstacle
            message_log.add_message(
                f"{target.get_display_name()} collides with obstacle after being displaced from ({original_y},{original_x}) to ({best_pos[0]},{best_pos[1]})!",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
        else:
            # Normal displacement message
            message_log.add_message(
                f"{target.get_display_name()} displaced from ({original_y},{original_x}) to ({best_pos[0]},{best_pos[1]})!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
        
        # Animate the displacement if UI is available
        if ui and hasattr(ui, 'draw_board'):
            # Calculate all positions along the path from original to final position
            from boneglaive.utils.coordinates import Position, get_line
            
            # Get all positions along the path for animation
            start_pos = Position(original_y, original_x)
            end_pos = Position(target.y, target.x)
            path = get_line(start_pos, end_pos)
            
            # Show the initial position first
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            time.sleep(0.2)  # Short pause before displacement animation
            
            # Temporarily set target back to original position
            temp_y, temp_x = target.y, target.x
            
            # Animate movement along the path
            for i, pos in enumerate(path[1:], 1):  # Skip the starting position
                # Update unit position for animation
                target.y, target.x = pos.y, pos.x
                
                # Redraw to show unit in intermediate position
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                
                # No trail animation, just show the unit moving along the path
                
                # Shorter delay for intermediate positions
                time.sleep(0.05)
            
            # Restore the final position
            target.y, target.x = temp_y, temp_x
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            
            # Get impact animation sequence from asset manager
            if hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Choose animation based on whether there was a collision
                if displacement_distance < 3:
                    # Use collision animation for impacts with terrain
                    impact_animation = ui.asset_manager.get_skill_animation_sequence('pry_collision')
                    color_id = 5  # Different color for collision (reddish)
                else:
                    # Use normal landing animation
                    impact_animation = ui.asset_manager.get_skill_animation_sequence('pry_impact')
                    color_id = 6  # Normal impact color
                
                # Show impact animation at the landing position
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    impact_animation,
                    color_id,  # Color based on collision type
                    0.25  # duration
                )
                
                # Flash the target to show it was hit
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                    color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 2
                    durations = [0.1] * 4
                    
                    # Use renderer's flash tile method
                    ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
                
                # Show damage number above target with improved visualization
                damage_text = f"-{damage}"  # Use calculated damage after defense reduction
                
                # Make damage text more prominent
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    time.sleep(0.1)
                    
                # Final damage display (stays on screen slightly longer)
                ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
                ui.renderer.refresh()
                time.sleep(0.2)
        
        # Check if target was defeated
        if target.hp <= 0:
            message_log.add_message(
                f"{target.get_display_name()} perishes!",
                MessageType.COMBAT,
                player=user.player,
                target=target.player,
                target_name=target.get_display_name()
            )
            
        return True
        
    def _get_displacement_positions(self, user: 'Unit', target: 'Unit', game: 'Game') -> List[Tuple[int, int]]:
        """Calculate valid positions where the target can be displaced to."""
        # Calculate direction FROM USER TO TARGET (important for direction calculation)
        dy = target.y - user.y
        dx = target.x - user.x
        
        # Normalize direction vector to get the displacement direction
        # This ensures displacement follows a straight line away from the user
        if dy != 0:
            direction_y = dy // abs(dy)  # Will be -1 or 1
        else:
            direction_y = 0
            
        if dx != 0:
            direction_x = dx // abs(dx)  # Will be -1 or 1
        else:
            direction_x = 0
            
        # Calculate exact direction for more precise straight-line displacement
        # This will maintain the same angle of displacement as the original attack
        # First, project the path beyond the target in a straight line
        max_displacement_distance = 3  # Maximum distance to displace unit
        
        # Check each step along the path for the first valid position
        positions_along_path = []
        for distance in range(1, max_displacement_distance + 1):
            # IMPORTANT: The displacement is FROM TARGET in direction AWAY FROM USER
            # We use target position as starting point, and direction vector points away from user
            y = target.y + (direction_y * distance)
            x = target.x + (direction_x * distance)
            
            # Check if this position is within map bounds
            if not game.is_valid_position(y, x):
                # Hit map boundary, stop checking further positions
                break
                
            # Check for impassable terrain - unit stops here
            if not game.map.is_passable(y, x):
                # Hit obstacle, use last valid position
                break
                
            # Check for other units - unit stops here
            if game.get_unit_at(y, x):
                # Hit another unit, use last valid position
                break
                
            # Position is valid, add it to list
            positions_along_path.append((y, x))
        
        # If we found valid positions along the path, use the furthest one
        if positions_along_path:
            # The displacement positions should only be those DIRECTLY IN LINE with the force direction
            # No additional adjacent positions are needed, as we want strict straight-line movement
            positions = positions_along_path
        else:
            # No valid positions found along the original path
            # As a fallback, try just one step in the displacement direction
            fallback_y = target.y + direction_y
            fallback_x = target.x + direction_x
            
            positions = []
            # Only add the fallback position if it's valid
            if (game.is_valid_position(fallback_y, fallback_x) and 
                game.map.is_passable(fallback_y, fallback_x) and
                not game.get_unit_at(fallback_y, fallback_x)):
                positions.append((fallback_y, fallback_x))
        
        # Filter for valid positions (completely passable and unoccupied)
        valid_positions = []
        for pos_y, pos_x in positions:
            # We already filtered for map boundaries above, but check again to be safe
            if not game.is_valid_position(pos_y, pos_x):
                continue
                
            # Check if position is passable terrain
            if not game.map.is_passable(pos_y, pos_x):
                continue
                
            # Check if position is already occupied by another unit
            if game.get_unit_at(pos_y, pos_x):
                continue
                
            # This position is valid
            valid_positions.append((pos_y, pos_x))
            
        return valid_positions
    
    def _select_best_displacement(self, positions: List[Tuple[int, int]], game: 'Game') -> Tuple[int, int]:
        """
        Select the best displacement position.
        With our straight-line implementation, we prioritize the position furthest from the original position.
        """
        # If no positions, return None (handled by caller)
        if not positions:
            return None
            
        # If only one position, return it
        if len(positions) == 1:
            return positions[0]
            
        # Now we want the position furthest from the original position of the target
        # Since our positions are in order of distance (furthest last), we want the last one
        # This maintains the "maximum force" effect where units are pushed as far as possible
        return positions[-1]
        
    def _get_lever_positions(self, user: 'Unit', target: 'Unit') -> List[Tuple[int, int]]:
        """Get positions for lever animation between user and target."""
        # Find midpoint for lever effect
        mid_y = (user.y + target.y) // 2
        mid_x = (user.x + target.x) // 2
        
        # Return list of positions for lever animation
        return [(mid_y, mid_x)]


class VaultSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Vault allows the GLAIVEMAN to leap over obstacles and enemies,
    landing in an empty space within range. The GLAIVEMAN can vault over
    otherwise impassable terrain and units, making it a powerful mobility skill.
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
        """Check if Vault can be used to the target position."""
        from boneglaive.utils.debug import logger
        
        # Debug information
        logger.debug(f"Checking if Vault can be used from ({user.y},{user.x}) to {target_pos}")
        
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            logger.debug("Vault failed: cooldown not ready")
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            logger.debug("Vault failed: missing game or target position")
            return False
            
        # Check if target position is within map bounds
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            logger.debug(f"Vault failed: position {target_pos} out of bounds")
            return False
            
        # Cannot vault to the same position
        if (user.y, user.x) == target_pos:
            logger.debug("Vault failed: cannot vault to same position")
            return False
            
        # Check if the target position is occupied by another unit
        unit_at_target = game.get_unit_at(target_pos[0], target_pos[1])
        if unit_at_target:
            logger.debug(f"Vault failed: position occupied by {unit_at_target.type.name}")
            return False
        
        # Check if the target position is valid for Vault
        # Vault can only land on completely empty or dusty terrain
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        from boneglaive.game.map import TerrainType
        
        # Cannot vault onto:
        # - Limestone (solid piles)
        # - Pillars (they extend to the ceiling)
        # - Furniture (can vault over them but not land on them)
        if terrain not in [TerrainType.EMPTY, TerrainType.DUST]:
            logger.debug(f"Vault failed: cannot vault onto terrain {terrain}")
            return False
            
        # Get the user's position (actual or planned move)
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            logger.debug(f"Using planned move position ({from_y},{from_x}) as origin")
            
        # Calculate effective range based on unit's current movement
        # The vault range changes by the same amount as the unit's movement bonus/penalty
        base_move = UNIT_STATS[user.type][3]  # Get the base move value from unit stats
        effective_stats = user.get_effective_stats()  # This includes all bonuses
        actual_move = effective_stats['move_range']   # Get final move range with all bonuses applied
        move_difference = actual_move - base_move  # Difference can be positive or negative
        
        # Apply the movement difference to vault range
        effective_range = self.range + move_difference
        
        # Check if target is within effective skill range
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > effective_range:
            logger.debug(f"Vault failed: position out of range ({distance} > {effective_range})")
            if move_difference != 0:
                modifier = "increased" if move_difference > 0 else "reduced"
                logger.debug(f"(Note: Vault range {modifier} from {self.range} to {effective_range} based on movement changes)")
            return False
            
        # Check for pillars in the path - cannot vault over pillars
        # Calculate positions along the path
        from boneglaive.utils.coordinates import Position, get_line
        start_pos = Position(from_y, from_x)
        end_pos = Position(target_pos[0], target_pos[1])
        path = get_line(start_pos, end_pos)
        
        # Check all positions along the path (excluding start and end)
        for pos in path[1:-1]:  # Skip start and end positions
            # Check if there's a pillar at this position
            terrain_in_path = game.map.get_terrain_at(pos.y, pos.x)
            if terrain_in_path == TerrainType.PILLAR:
                logger.debug(f"Vault failed: cannot vault over pillars at ({pos.y},{pos.x})")
                return False
            
        logger.debug("Vault check passed - skill can be used")
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """
        Queue up the Vault skill for execution at the end of the turn.
        Sets the skill target and records the skill for execution.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.event_system import get_event_manager, EventType, UIRedrawEventData
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order (assumes the Game instance is passed)
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Create a visual indicator on the target position
        if hasattr(game, 'ui') and game.ui:
            # Store the vault target position in the unit for the UI to render
            user.vault_target_indicator = target_pos
            
            # Request a redraw to show the indicator immediately
            event_manager = get_event_manager()
            event_manager.publish(
                EventType.UI_REDRAW_REQUESTED,
                UIRedrawEventData()
            )
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} readies Vault to position ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Vault skill during the turn resolution phase.
        This moves the unit to the target position, showing an animation of the leap.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.debug import logger
        
        # Debug information to help identify issues
        logger.debug(f"Executing Vault skill from ({user.y},{user.x}) to ({target_pos[0]},{target_pos[1]})")
        
        # IMPORTANT: Don't do validation again at execute time to avoid issues
        # We already verified the target was valid when the skill was queued, and game state
        # may have changed since then (unit may have moved due to previous turn actions)
        
        # Clear vault target indicator to prevent it from showing after execution
        user.vault_target_indicator = None
        
        # Just check basic validity
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            message_log.add_message(
                "Vault failed: target position is out of bounds.",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Check if target position is now occupied by a unit
        if game.get_unit_at(target_pos[0], target_pos[1]):
            message_log.add_message(
                "Vault failed: target position is now occupied.",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} uses Vault!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        # Store original position for animation
        original_y, original_x = user.y, user.x
        
        # Calculate visible path for animation
        from boneglaive.utils.coordinates import Position, get_line
        start_pos = Position(original_y, original_x)
        end_pos = Position(target_pos[0], target_pos[1])
        path = get_line(start_pos, end_pos)
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get animation sequence for Vault (if we had one defined)
            animation_sequence = ui.asset_manager.get_skill_animation_sequence('vault')
            
            # If no specific vault animation is defined, create a simple one
            if not animation_sequence:
                animation_sequence = ['^', 'Λ', '↑', '!']
            
            # Show animation at user's position
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                animation_sequence,
                7,  # color ID
                0.3  # duration
            )
            time.sleep(0.2)
            
            # Show arc animation along the path
            for i, pos in enumerate(path[1:-1], 1):  # Skip start and end positions
                # Create a simple arc character based on position in the path
                progress = i / len(path)
                
                # Arc animation - rises then falls
                if progress < 0.5:
                    arc_char = ['⋰', '↗', '↑', '⇑'][min(3, int(progress * 8))]
                else:
                    arc_char = ['⇓', '↓', '↘', '⋱'][min(3, int((progress - 0.5) * 8))]
                
                # Show the arc character at this path position
                ui.renderer.draw_tile(pos.y, pos.x, arc_char, 7)
                ui.renderer.refresh()
                time.sleep(0.05)  # Quick animation
        
        # Set user's position to the target
        user.y, user.x = target_pos
        
        # Check for trap release due to position change
        game._check_position_change_trap_release(user, original_y, original_x)
        
        # Log the movement
        message_log.add_message(
            f"{user.get_display_name()} vaults from ({original_y},{original_x}) to ({target_pos[0]},{target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        # Animate the landing if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Redraw to show unit in new position
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            
            # Get or create landing animation
            impact_animation = ui.asset_manager.get_skill_animation_sequence('vault_impact')
            if not impact_animation:
                impact_animation = ['v', 'V', '*', '.']  # Simple landing animation
                
            # Show landing animation at the target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                impact_animation,
                7,  # color ID
                0.25  # duration
            )
            
            # Flash the unit to show successful vault
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                player_color = 3 if user.player == 1 else 4
                color_ids = [7, player_color] * 2  # Alternate white with player color
                durations = [0.1] * 4
                
                # Use renderer's flash tile method
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        
        return True


class JudgementThrowSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    The GLAIVEMAN throws a sacred spinning glaive up to a range of 3 at an enemy unit.
    This deals double damage if the enemy is at or below their wretch threshold.
    When it deals double damage, there is a lightning strike effect on the target.
    """
    
    def __init__(self):
        super().__init__(
            name="Judgement Throw",
            key="J",
            description="Throw a sacred glaive at an enemy (range 3). Deals double damage if enemy is wretched.",
            target_type=TargetType.ENEMY,
            cooldown=2,
            range_=3
        )
        self.base_damage = 4  # Base damage amount
        self.critical_damage = 8  # Fixed damage amount when critical
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Judgement Throw can be used on the target."""
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
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """
        Queue up the Judgement Throw skill for execution at the end of the turn.
        This works similarly to move and attack actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        
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
        
        # Set cooldown explicitly - done immediately when queuing up the action
        self.current_cooldown = self.cooldown
        logger.debug(f"Setting {self.name} cooldown to {self.current_cooldown}")
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} readies Judgement Throw against {target.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Judgement Throw skill during the turn resolution phase.
        This is called by the game engine when processing actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        from boneglaive.utils.debug import logger
        import time
        import curses
        
        # Log current cooldown for debugging
        logger.debug(f"Executing {self.name} with cooldown: {self.current_cooldown}")
        
        # Get target at the original position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        
        # Validate whether the ability should resolve - it should resolve as long as:
        # 1. There's a valid enemy at the original position, OR
        # 2. There's a valid enemy within range of the user
        if not target or target.player == user.player:
            # Look for any valid enemy unit within range
            valid_targets = []
            for potential_target in game.units:
                if (potential_target.is_alive() and 
                    potential_target.player != user.player):
                    # Check if this unit is within range
                    distance = game.chess_distance(user.y, user.x, potential_target.y, potential_target.x)
                    if distance <= self.range:
                        valid_targets.append((potential_target, distance))
            
            # If we found valid targets, take the closest one
            if valid_targets:
                # Sort by distance (closest first)
                valid_targets.sort(key=lambda x: x[1])
                target = valid_targets[0][0]
                # Update target position for animation
                target_pos = (target.y, target.x)
            else:
                # No valid targets at all
                message_log.add_message(
                    "Judgement Throw failed: no targets in range.",
                    MessageType.ABILITY,
                    player=user.player,
                    attacker_name=user.get_display_name()
                )
                return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} throws sacred glaive at {target.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        # Calculate path for animation
        from boneglaive.utils.coordinates import Position, get_line
        start_pos = Position(user.y, user.x)
        end_pos = Position(target_pos[0], target_pos[1])
        path = get_line(start_pos, end_pos)
        
        # Check if target is at wretch threshold for double damage
        critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
        is_critical = target.hp <= critical_threshold
        
        # Calculate damage
        if is_critical:
            # Critical damage bypasses defense
            damage = self.critical_damage
        else:
            # Regular damage is affected by defense
            damage = max(1, self.base_damage - target.defense)
            
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get animation sequence for Judgement Throw
            animation_sequence = ui.asset_manager.get_skill_animation_sequence('judgement_throw')
            if not animation_sequence:
                # If not defined yet, use a temporary animation
                animation_sequence = ['*', '#', 'O', '⚡', '↺', '↻']
            
            # Show animation at user's position
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                animation_sequence[:2],
                7,  # color ID
                0.2  # duration
            )
            time.sleep(0.1)
            
            # Animate the glaive flying along the path
            spinning_chars = ['↺', '↻', '↻', '↺']
            for i, pos in enumerate(path[1:-1]):  # Skip start and end positions
                # Create a spinning animation
                spin_char = spinning_chars[i % len(spinning_chars)]
                
                # Show animation at this path position
                ui.renderer.draw_tile(pos.y, pos.x, spin_char, 7)
                ui.renderer.refresh()
                time.sleep(0.075)  # Quick animation
                
                # Clear previous position if not at start
                if i > 0:
                    prev_pos = path[i]
                    ui.renderer.draw_tile(prev_pos.y, prev_pos.x, ' ', 0)
                    
            # Show impact animation at target position
            impact_animation = ['X', '#', '*', '⚡'] if is_critical else ['X', '#', '*']
            impact_color = 5 if is_critical else 6  # Yellow for critical, Red for normal
            
            # If critical hit, add a more dramatic lightning from sky effect
            if is_critical:
                # Import WIDTH from constants
                from boneglaive.utils.constants import WIDTH
                
                # Create a vertical path from above the target (from "sky")
                sky_height = max(0, target_pos[0] - 5)  # Start 5 spaces above target or at top of screen
                
                # Draw lightning bolt coming from the sky
                lightning_path = []
                for y in range(sky_height, target_pos[0] + 1):
                    # Add some randomness to the x position for zigzag effect
                    offset = 0
                    if y > sky_height and y < target_pos[0]:
                        offset = (y % 3) - 1  # Values: -1, 0, 1 for zigzag
                    x_pos = target_pos[1] + offset
                    
                    # Make sure we're still on screen
                    if x_pos >= 0 and x_pos < WIDTH:
                        lightning_path.append((y, x_pos))
                
                # Lightning bolt characters based on position in path
                lightning_chars = ['⋰', '│', '⚡', '↯', '⚡', '↯']
                
                # First flash - draw the entire path
                for i, (y, x) in enumerate(lightning_path):
                    char_index = min(i % len(lightning_chars), len(lightning_chars) - 1)
                    ui.renderer.draw_tile(y, x, lightning_chars[char_index], 5)  # Yellow for lightning
                ui.renderer.refresh()
                time.sleep(0.15)
                
                # Clear the path
                for y, x in lightning_path:
                    ui.renderer.draw_tile(y, x, ' ', 0)
                ui.renderer.refresh()
                time.sleep(0.05)
                
                # Second flash - more intense
                for i, (y, x) in enumerate(lightning_path):
                    char_index = min(i % len(lightning_chars), len(lightning_chars) - 1)
                    ui.renderer.draw_tile(y, x, lightning_chars[char_index], 3)  # Brighter color
                ui.renderer.refresh()
                time.sleep(0.2)
                
                # Final strike - most intense at target position
                ui.renderer.draw_tile(target_pos[0], target_pos[1], '※', 7)  # White for maximum flash
                ui.renderer.refresh()
                time.sleep(0.15)
            
            # Show impact animation
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                impact_animation,
                impact_color,
                0.15
            )
            
            # Flash the target unit
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [impact_color, 3 if target.player == 1 else 4] * 2
                durations = [0.1] * 4
                
                # Use renderer's flash tile method
                ui.renderer.flash_tile(target_pos[0], target_pos[1], tile_ids, color_ids, durations)
        
        # Apply damage to target
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        # Log the damage - use the same message format for both critical and normal hits
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Judgement Throw",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Add the special message only for critical hits
        if is_critical:
            message_log.add_message(
                f"Sacred glaive strikes with divine justice!",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
        
        # If UI is available, show damage number
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{damage}"
            
            # Match regular attack damage display exactly - using color 7 (white/yellow)
            damage_color = 7  # Same color used by regular attacks
            
            # Make damage text more prominent
            for i in range(3):
                ui.renderer.draw_text(target_pos[0]-1, target_pos[1]*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_text(target_pos[0]-1, target_pos[1]*2, damage_text, damage_color, attrs)
                ui.renderer.refresh()
                time.sleep(0.1)
            
            # Final damage display
            ui.renderer.draw_text(target_pos[0]-1, target_pos[1]*2, damage_text, damage_color, curses.A_BOLD)
            ui.renderer.refresh()
            time.sleep(0.3)  # Matching 0.3s delay used by regular attacks
        
        # Check if target was defeated
        if target.hp <= 0:
            message_log.add_message(
                f"{target.get_display_name()} perishes!",
                MessageType.COMBAT,
                player=user.player,
                target=target.player,
                target_name=target.get_display_name()
            )
            
        return True

# MANDIBLE_FOREMAN skills
class Viseroy(PassiveSkill):
    """
    Passive skill for MANDIBLE_FOREMAN.
    When the MANDIBLE FOREMAN attacks a unit, they are trapped in his mechanical jaws.
    The trapped unit cannot move and takes damage each turn.
    The trap is released when the MANDIBLE FOREMAN takes any action or is defeated.
    """
    
    def __init__(self):
        super().__init__(
            name="Viseroy",
            key="V",
            description="When attacking, traps the enemy unit in mechanical jaws. Trapped units cannot move and take damage each turn. Effect ends if the FOREMAN takes an action or is defeated."
        )
    
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """
        Apply the Viseroy passive effect.
        The actual trap mechanics are handled by the Game engine.
        """
        # No passive work needed here - trapping happens on attack in Game.process_turn
        # and releasing happens in Game.process_turn_end
        pass


class DischargeSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    The FOREMAN releases a trapped unit, throwing them 2-3 tiles in a chosen direction.
    Deals moderate damage on impact with walls/obstacles.
    """
    
    def __init__(self):
        super().__init__(
            name="Discharge",
            key="D",
            description="Release a trapped unit, throwing them 2-3 tiles away. Deals damage on impact with obstacles.",
            target_type=TargetType.AREA,  # Target an area to throw the unit towards
            cooldown=2,
            range_=3  # Maximum throw distance
        )
        self.impact_damage = 6  # Base damage on impact
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Discharge can be used - requires a trapped unit."""
        from boneglaive.utils.debug import logger
        
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            logger.debug("Discharge failed: cooldown not ready")
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            logger.debug("Discharge failed: missing game or target position")
            return False
            
        # Check if the unit is a MANDIBLE_FOREMAN
        if user.type != UnitType.MANDIBLE_FOREMAN:
            logger.debug("Discharge failed: only MANDIBLE_FOREMAN can use this skill")
            return False
            
        # Check if there are any trapped units (the FOREMAN must have trapped a unit)
        trapped_units = [u for u in game.units if u.is_alive() and u.trapped_by == user]
        if not trapped_units:
            logger.debug("Discharge failed: no trapped units to discharge")
            return False
            
        # Check if target position is within map bounds
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            logger.debug(f"Discharge failed: position {target_pos} out of bounds")
            return False
            
        # Get the user's position (actual or planned move)
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            
        # Check if target is within skill range
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            logger.debug(f"Discharge failed: position out of range ({distance} > {self.range})")
            return False
            
        # All checks passed - the skill can be used
        logger.debug("Discharge check passed - skill can be used")
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """
        Queue up the Discharge skill for execution at the end of the turn.
        Sets the skill target and records the skill for execution.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Get the trapped unit (we validated there is at least one in can_use)
        trapped_units = [u for u in game.units if u.is_alive() and u.trapped_by == user]
        trapped_unit = trapped_units[0]  # Take the first one if multiple (unlikely)
        
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order (assumes the Game instance is passed)
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} readies to discharge {trapped_unit.get_display_name()} towards ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=trapped_unit.get_display_name()
        )
        
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Discharge skill during the turn resolution phase.
        This releases a trapped unit and throws them towards the target position,
        potentially causing damage on impact with walls or obstacles.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        
        # Get the trapped unit - we'll throw the first one if multiple (unlikely)
        trapped_units = [u for u in game.units if u.is_alive() and u.trapped_by == user]
        
        # Validate if there's still a unit to throw
        if not trapped_units:
            message_log.add_message(
                f"Discharge failed: no trapped units to throw!",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Get the trapped unit to throw
        trapped_unit = trapped_units[0]
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} discharges {trapped_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=trapped_unit.get_display_name()
        )
        
        # Store original position for animation and distance calculation
        original_y, original_x = trapped_unit.y, trapped_unit.x
        
        # Calculate direction vector towards target
        dy = target_pos[0] - user.y
        dx = target_pos[1] - user.x
        
        # Normalize direction to get a unit vector
        distance = max(1, abs(dy) + abs(dx))  # Manhattan distance
        direction_y = int(dy / distance) if distance > 0 else 0
        direction_x = int(dx / distance) if distance > 0 else 0
        
        # Calculate all possible positions along the throw path
        max_throw_distance = 3  # Maximum distance to throw the unit
        throw_positions = []
        
        # Trace the path in the direction of the target
        for throw_distance in range(1, max_throw_distance + 1):
            # Calculate the position at this distance
            y = trapped_unit.y + (direction_y * throw_distance)
            x = trapped_unit.x + (direction_x * throw_distance)
            
            # Check if position is valid
            if not game.is_valid_position(y, x):
                # Hit map boundary, stop calculating additional positions
                break
                
            # Check if there's a unit at this position (can't throw through units)
            unit_at_pos = game.get_unit_at(y, x)
            if unit_at_pos and unit_at_pos != trapped_unit:
                # Hit another unit, can't throw past this point
                break
                
            # Check if position is passable terrain
            if not game.map.is_passable(y, x):
                # Hit impassable terrain - DON'T add this as a valid position
                # Instead, use the last valid position before this one
                break
                
            # Position is valid for the throw path
            throw_positions.append((y, x))
        
        # Default landing position if no valid positions were found
        landing_pos = (trapped_unit.y, trapped_unit.x)
        
        # Determine the actual landing position (last valid position)
        if throw_positions:
            landing_pos = throw_positions[-1]
        
        # Calculate actual throw distance
        throw_distance = game.chess_distance(original_y, original_x, landing_pos[0], landing_pos[1])
        
        # First, release the trapped unit
        trapped_unit.trapped_by = None
        
        # Determine if we hit an obstacle
        # We hit an obstacle if:
        # 1. We didn't move the full max throw distance AND there are positions beyond our landing point 
        # 2. OR the next position after our landing point would be impassable/invalid
        hit_obstacle = False
        
        # Check if we hit an obstacle by seeing if we could have gone further
        if throw_distance > 0 and throw_distance < max_throw_distance:
            # Check if the next position would be invalid
            next_y = landing_pos[0] + direction_y
            next_x = landing_pos[1] + direction_x
            
            # If the next position is invalid or impassable, we hit an obstacle
            if (not game.is_valid_position(next_y, next_x) or 
                not game.map.is_passable(next_y, next_x) or
                game.get_unit_at(next_y, next_x)):
                hit_obstacle = True
        
        if throw_distance > 0:
            # Animation logic if UI is available
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # First show the release animation at the trapped unit's position
                release_animation = ui.asset_manager.get_skill_animation_sequence('discharge_release')
                if not release_animation:
                    # Default animation if not defined in asset manager
                    release_animation = ['{⚡}', '[ ]', '   ']
                
                ui.renderer.animate_attack_sequence(
                    trapped_unit.y, trapped_unit.x,
                    release_animation,
                    7,  # color ID
                    0.2  # duration
                )
                time.sleep(0.2)  # Small pause
                
                # Now animate the throw path
                # Calculate all positions along the path for animation
                from boneglaive.utils.coordinates import Position, get_line
                start_pos = Position(trapped_unit.y, trapped_unit.x)
                end_pos = Position(landing_pos[0], landing_pos[1])
                path = get_line(start_pos, end_pos)
                
                # Show the initial position
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                time.sleep(0.2)  # Short pause before throw animation
                
                # Temporarily update unit position for animation
                orig_y, orig_x = trapped_unit.y, trapped_unit.x
                
                # Animate movement along the path
                for i, pos in enumerate(path[1:], 1):  # Skip the starting position
                    # Update unit position for animation
                    trapped_unit.y, trapped_unit.x = pos.y, pos.x
                    
                    # Redraw to show unit in intermediate position
                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                    
                    # Short delay for smooth animation
                    time.sleep(0.05)
            
            # Now update the unit position to the landing position
            trapped_unit.y, trapped_unit.x = landing_pos
            
            # Log the throw result
            if hit_obstacle:
                message_log.add_message(
                    f"{trapped_unit.get_display_name()} is thrown and collides with obstacle at ({landing_pos[0]},{landing_pos[1]})!",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=trapped_unit.get_display_name()
                )
            else:
                message_log.add_message(
                    f"{trapped_unit.get_display_name()} is thrown to ({landing_pos[0]},{landing_pos[1]})!",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=trapped_unit.get_display_name()
                )
        else:
            # No actual movement but still released
            message_log.add_message(
                f"{trapped_unit.get_display_name()} is released from mechanical jaws!",
                MessageType.ABILITY,
                player=user.player,
                target_name=trapped_unit.get_display_name()
            )
        
        # Apply impact damage if the unit hit an obstacle
        if hit_obstacle:
            # Calculate damage (reduced by defense)
            damage = max(1, self.impact_damage - trapped_unit.get_effective_stats()['defense'])
            
            # Apply damage
            previous_hp = trapped_unit.hp
            trapped_unit.hp = max(0, trapped_unit.hp - damage)
            
            # Log the damage with combat message
            message_log.add_combat_message(
                attacker_name=user.get_display_name(),
                target_name=trapped_unit.get_display_name(),
                damage=damage,
                ability="Discharge Impact",
                attacker_player=user.player,
                target_player=trapped_unit.player
            )
            
            # Show damage effect if UI is available
            if ui and hasattr(ui, 'renderer'):
                # Animate the impact
                impact_animation = ui.asset_manager.get_skill_animation_sequence('discharge_impact')
                if not impact_animation:
                    # Default animation if not defined
                    impact_animation = ['!', '*', '#', 'X']
                
                ui.renderer.animate_attack_sequence(
                    landing_pos[0], landing_pos[1],
                    impact_animation,
                    5,  # color ID for impact (reddish)
                    0.2  # duration
                )
                
                # Flash the unit to show it took damage
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(trapped_unit.type)] * 4
                    color_ids = [5, 3 if trapped_unit.player == 1 else 4] * 2  # Alternate red with player color
                    durations = [0.1] * 4
                    
                    # Use renderer's flash tile method
                    ui.renderer.flash_tile(landing_pos[0], landing_pos[1], tile_ids, color_ids, durations)
                
                # Show damage number above unit with improved visualization
                damage_text = f"-{damage}"
                
                # Make damage text more prominent
                import curses
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_text(landing_pos[0]-1, landing_pos[1]*2, " " * len(damage_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_text(landing_pos[0]-1, landing_pos[1]*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    time.sleep(0.1)
                
                # Final damage display
                ui.renderer.draw_text(landing_pos[0]-1, landing_pos[1]*2, damage_text, 7, curses.A_BOLD)
                ui.renderer.refresh()
                time.sleep(0.3)
            
            # Check if target was defeated
            if trapped_unit.hp <= 0:
                message_log.add_message(
                    f"{trapped_unit.get_display_name()} perishes from the impact!",
                    MessageType.COMBAT,
                    player=user.player,
                    target=trapped_unit.player,
                    target_name=trapped_unit.get_display_name()
                )
        
        # Final board redraw
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True
        
class JawlineSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Deploys a network of smaller mechanical jaws connected by cables in a 3×3 area
    around the FOREMAN. All enemy units in the area have their movement reduced
    and cannot use movement-based skills for a limited time.
    """
    
    def __init__(self):
        super().__init__(
            name="Jawline",
            key="J",
            description="Deploy network of mechanical jaws in 3x3 area around yourself. Reduces enemy movement by 1 and prevents movement skills for 3 turns.",
            target_type=TargetType.SELF,  # Self-centered AoE
            cooldown=5,
            range_=0,  # No range as it's centered on self
            area=1  # 3x3 area (center + 1 in each direction)
        )
        self.effect_duration = 3  # Duration in turns
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Jawline can be used."""
        from boneglaive.utils.debug import logger
        
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            return False
        
        # Since this is a self-centered AoE, no additional position validation needed
        # Just make sure we have a game reference
        if not game:
            return False
            
        # Check that there are actually enemies in the area that can be affected
        # Get the area around the user's position
        area_positions = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                y = user.y + dy
                x = user.x + dx
                if game.is_valid_position(y, x):
                    area_positions.append((y, x))
        
        # Check if there are any enemy units in the area
        has_enemies = False
        for y, x in area_positions:
            unit = game.get_unit_at(y, x)
            if unit and unit.is_alive() and unit.player != user.player:
                has_enemies = True
                break
        
        # Don't allow using the skill if there are no enemies to affect
        if not has_enemies:
            logger.debug(f"Jawline failed: no enemy units in area around {user.get_display_name()}")
            return False
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Jawline skill for execution at the end of the turn."""
        from boneglaive.utils.message_log import message_log, MessageType
        
        # For self-targeted skills, the target_pos should be the user's position
        target_pos = (user.y, user.x)
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Set the skill target to user's position
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued - this will be color-coded by the message log system
        # Include both the unit name and skill name to be more informative
        message_log.add_message(
            f"{user.get_display_name()} prepares to deploy JAWLINE network!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Jawline skill.
        Deploys a network of mechanical jaws in 3x3 area around the FOREMAN,
        restricting enemy movement and abilities.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        import curses
        
        # Clear the jawline_message_shown flag so it can be shown again next time
        if hasattr(user, 'jawline_message_shown'):
            user.jawline_message_shown = False
        
        # Get the actual center (user's position)
        center_pos = (user.y, user.x)
        
        # Log the skill activation with player-specific coloring
        message_log.add_message(
            f"{user.get_display_name()} deploys JAWLINE network!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        # Get the 3x3 area around the user's position
        area_positions = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                y = center_pos[0] + dy
                x = center_pos[1] + dx
                if game.is_valid_position(y, x):
                    area_positions.append((y, x))
        
        # Find all enemy units in the area
        affected_units = []
        for y, x in area_positions:
            unit = game.get_unit_at(y, x)
            if unit and unit.is_alive() and unit.player != user.player:
                affected_units.append(unit)
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Animation sequence for the jawline deployment
            for phase in range(3):
                # First phase: Show radiating lines from the center
                if phase == 0:
                    # Draw lines emanating from the foreman
                    for y, x in area_positions:
                        if (y, x) != center_pos:  # Skip the center
                            ui.renderer.draw_tile(y, x, '·', 6)  # Yellow dots
                    ui.renderer.refresh()
                    time.sleep(0.3)
                    
                # Second phase: Replace with cable visuals
                elif phase == 1:
                    for y, x in area_positions:
                        if (y, x) != center_pos:  # Skip the center
                            # Draw cable characters based on relative position
                            dy = y - center_pos[0]
                            dx = x - center_pos[1]
                            
                            if dy == 0:  # Horizontal
                                ui.renderer.draw_tile(y, x, '─', 7)
                            elif dx == 0:  # Vertical
                                ui.renderer.draw_tile(y, x, '│', 7)
                            elif dy * dx > 0:  # Diagonal (top-left to bottom-right)
                                ui.renderer.draw_tile(y, x, '\\', 7)
                            else:  # Diagonal (top-right to bottom-left)
                                ui.renderer.draw_tile(y, x, '/', 7)
                    ui.renderer.refresh()
                    time.sleep(0.3)
                    
                # Third phase: Show mini-jaws at each position
                else:
                    for y, x in area_positions:
                        if (y, x) != center_pos:  # Skip the center
                            # Show mini-jaw snap animation
                            jaw_animation = ['{.}', '{>}', '{]}']
                            
                            for jaw in jaw_animation:
                                ui.renderer.draw_tile(y, x, jaw, 7)
                                ui.renderer.refresh()
                                time.sleep(0.05)
                    time.sleep(0.2)
            
            # Final effect: Flash affected enemies
            if affected_units:
                for unit in affected_units:
                    # Flash the unit to show it's been affected
                    if hasattr(ui, 'asset_manager'):
                        tile_ids = [ui.asset_manager.get_unit_tile(unit.type)] * 4
                        color_ids = [7, 5] * 2  # Alternate white with red
                        durations = [0.1] * 4
                        
                        # Use renderer's flash tile method
                        ui.renderer.flash_tile(unit.y, unit.x, tile_ids, color_ids, durations)
            
            # Show connection cables between the FOREMAN and affected units
            for unit in affected_units:
                # Get line positions
                from boneglaive.utils.coordinates import Position, get_line
                start_pos = Position(user.y, user.x)
                end_pos = Position(unit.y, unit.x)
                path = get_line(start_pos, end_pos)
                
                # Create cable visuals
                for i, pos in enumerate(path[1:-1]):  # Skip start and end
                    # Skip if there's a unit at this position
                    if not game.get_unit_at(pos.y, pos.x):
                        # Use different symbols for the cable segments
                        cable_chars = ['═', '║', '╬', '╣', '╩', '╠']
                        char_idx = i % len(cable_chars)
                        ui.renderer.draw_tile(pos.y, pos.x, cable_chars[char_idx], 6)
                ui.renderer.refresh()
                time.sleep(0.1)
                
            # Redraw the board
            time.sleep(0.3)
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Apply effects to all affected units
        for unit in affected_units:
            # Check if unit is immune to effects
            if unit.is_immune_to_effects():
                message_log.add_message(
                    f"{unit.get_display_name()} is immune to Jawline due to Stasiality!",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=unit.get_display_name()
                )
                continue  # Skip this unit and process others
                
            # Apply movement reduction
            unit.move_range_bonus -= 1
            
            # Flag unit as affected by Jawline
            # We'll need to add this attribute to the Unit class
            unit.jawline_affected = True
            # Store the duration to be decremented each turn
            unit.jawline_duration = self.effect_duration
            
            # Log the effect application
            message_log.add_message(
                f"{unit.get_display_name()} is tethered by mechanical jaws! Movement -1 for {self.effect_duration} turns.",
                MessageType.ABILITY,
                player=user.player,
                target_name=unit.get_display_name()
            )
        
        # Remove the final summary message completely - we don't need it
        # Individual unit effect messages are sufficient
        
        return True
        
class SiteInspectionSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    FOREMAN surveys a 3x3 area, studying structure and terrain.
    Grants a flat +1 movement bonus to all allied units in the area.
    Additionally grants +1 attack for each unique terrain type present in the area.
    These bonuses are permanent.
    """
    
    def __init__(self):
        super().__init__(
            name="Site Inspection",
            key="S",
            description="Survey a 3x3 area. Grants +1 movement and +1 attack per unique terrain type to all allied units in area.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=3,
            area=1  # 3x3 area (center + 1 in each direction)
        )
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Site Inspection can be used on the target position."""
        from boneglaive.utils.debug import logger
        
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            return False
            
        # Check if target position is within map bounds
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            logger.debug(f"Site Inspection failed: target position {target_pos} is out of bounds")
            return False
            
        # Get the user's position (actual or planned move)
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            
        # Check if target is within effective skill range
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            logger.debug(f"Site Inspection failed: target position out of range ({distance} > {self.range})")
            return False
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Site Inspection skill for execution at the end of the turn."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.event_system import get_event_manager, EventType, UIRedrawEventData
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Add a visual indicator for the Site Inspection area
        # This will be a property on the unit that the renderer can use to show the area effect
        user.site_inspection_indicator = target_pos
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Request a redraw to show the indicator immediately
        if hasattr(game, 'ui') and game.ui:
            event_manager = get_event_manager()
            event_manager.publish(
                EventType.UI_REDRAW_REQUESTED,
                UIRedrawEventData()
            )
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares Site Inspection at coordinates ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Site Inspection skill.
        Surveys a 3x3 area, applying bonuses to all allied units in the area.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.game.map import TerrainType
        import time
        import curses
        
        # Clear the site inspection indicator when we start executing the skill
        user.site_inspection_indicator = None
        
        # Check if target position is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            message_log.add_message(
                f"Site Inspection failed: target position is invalid!",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} performs Site Inspection at ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        # Get the 3x3 area around the target position
        area_positions = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                y = target_pos[0] + dy
                x = target_pos[1] + dx
                if game.is_valid_position(y, x):
                    area_positions.append((y, x))
        
        # Find unique terrain types in the area
        unique_terrain_types = set()
        for y, x in area_positions:
            terrain = game.map.get_terrain_at(y, x)
            unique_terrain_types.add(terrain)
        
        # Calculate attack bonus based on number of unique terrain types
        attack_bonus = len(unique_terrain_types)
        move_bonus = 1  # Flat +1 move bonus
        
        # Find all allied units in the area
        affected_units = []
        for unit in game.units:
            if not unit.is_alive() or unit.player != user.player:
                continue
                
            if (unit.y, unit.x) in area_positions:
                affected_units.append(unit)
        
        # Log the terrain analysis
        terrain_names = ", ".join([t.name for t in unique_terrain_types])
        message_log.add_message(
            f"Site Inspection identifies {len(unique_terrain_types)} terrain types: {terrain_names}",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Show scanning animation across the area
            for y, x in area_positions:
                # Skip positions with units for cleaner display
                if game.get_unit_at(y, x) is None:
                    # Create a measurement animation sequence
                    scan_chars = ['·', '+', '×', '◎']
                    
                    # Show at each position
                    for char in scan_chars:
                        ui.renderer.draw_tile(y, x, char, 3)  # Green for measurement
                        ui.renderer.refresh()
                        time.sleep(0.05)
            
            # Highlight terrain types found
            for terrain_type in unique_terrain_types:
                # Find all positions with this terrain type
                for y, x in area_positions:
                    if game.map.get_terrain_at(y, x) == terrain_type:
                        # Flash these positions
                        for i in range(2):
                            ui.renderer.draw_tile(y, x, '□', 5 if i % 2 == 0 else 6)  # Alternate colors
                            ui.renderer.refresh()
                            time.sleep(0.1)
            
            # Show connection lines between foreman and affected units
            if affected_units:
                # Draw lines from foreman to each affected ally
                for unit in affected_units:
                    if unit != user:  # Skip drawing a line to self
                        # Get line positions
                        from boneglaive.utils.coordinates import Position, get_line
                        start_pos = Position(user.y, user.x)
                        end_pos = Position(unit.y, unit.x)
                        path = get_line(start_pos, end_pos)
                        
                        # Draw dotted line
                        for i, pos in enumerate(path[1:-1]):  # Skip start and end
                            if i % 2 == 0:  # Every other position for dotted line
                                ui.renderer.draw_tile(pos.y, pos.x, '·', 3)
                        ui.renderer.refresh()
                time.sleep(0.3)
                
                # Clear the lines
                for unit in affected_units:
                    if unit != user:
                        start_pos = Position(user.y, user.x)
                        end_pos = Position(unit.y, unit.x)
                        path = get_line(start_pos, end_pos)
                        for pos in path[1:-1]:
                            # Only clear if no unit is present
                            if game.get_unit_at(pos.y, pos.x) is None:
                                ui.renderer.draw_tile(pos.y, pos.x, ' ', 0)
            
            # Redraw board
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Apply bonuses to all affected units
        for unit in affected_units:
            # Check if unit is immune to statistical changes
            if unit.is_immune_to_effects():
                message_log.add_message(
                    f"{unit.get_display_name()} is immune to Site Inspection bonuses due to Stasiality!",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=unit.get_display_name()
                )
                continue
                
            # Apply standard bonuses
            unit.attack_bonus += attack_bonus
            unit.move_range_bonus += move_bonus
            
            # Special handling: find any GLAIVEMAN units and directly boost their vault range
            if unit.type == UnitType.GLAIVEMAN:
                # Find the Vault skill and directly increment its range
                for skill in unit.active_skills:
                    if skill.__class__.__name__ == "VaultSkill":
                        # Directly increase the skill's range attribute
                        skill.range += 1
                        
                        # Log special effect on vault range
                        message_log.add_message(
                            f"{unit.get_display_name()}'s Vault range increases by 1!",
                            MessageType.ABILITY,
                            player=user.player,
                            target_name=unit.get_display_name()
                        )
                        break
            
            # Log the standard bonus application
            message_log.add_message(
                f"{unit.get_display_name()} gains +{attack_bonus} attack and +{move_bonus} movement from Site Inspection!",
                MessageType.ABILITY,
                player=user.player,
                target_name=unit.get_display_name()
            )
            
        # Redraw the board to ensure everything is updated properly
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Final message about permanent bonuses
        message_log.add_message(
            f"Site Inspection bonuses are permanent: +{attack_bonus} attack and +{move_bonus} movement!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True

# GRAYMAN skills
class Stasiality(PassiveSkill):
    """
    Passive skill for GRAYMAN.
    GRAYMAN exists outside normal laws of reality and cannot have his stats changed
    or be displaced by other effects.
    """
    
    def __init__(self):
        super().__init__(
            name="Stasiality",
            key="S",
            description="Cannot have stats changed or be displaced. Immune to buffs, debuffs, forced movement, and terrain effects."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        """
        Apply the Stasiality passive effect.
        
        This is mostly a marker skill - the actual immunity checks are performed
        when status effects are applied to verify if the unit is immune.
        
        Specifically prevents ALL stat changes, both positive and negative:
        - Estrange effect (stat reduction)
        - Trapped by Viseroy (movement prevention)
        - Jawline effect (movement reduction)
        - Pry effect (movement reduction and displacement)
        - Site Inspection effect (stat increases from terrain analysis)
        - Any other buff or debuff that would modify stats
        
        The unit exists in a fixed state, immune to both helpful and harmful effects.
        """
        # Most of the immunity is implemented at the effect application points
        pass
        
class DeltaConfigSkill(ActiveSkill):
    """
    Active skill for GRAYMAN.
    Allows teleportation to any unoccupied tile on the map that isn't a pillar or furniture.
    """
    
    def __init__(self):
        super().__init__(
            name="Delta Config",
            key="D",
            description="Teleport to any unoccupied tile on the map that isn't a pillar or furniture.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=99  # Unlimited range effectively
        )
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Delta Config teleportation can be used to the target position."""
        from boneglaive.utils.debug import logger
        
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            logger.debug("Delta Config failed: cooldown not ready")
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            logger.debug("Delta Config failed: missing game or target position")
            return False
            
        # Check if target position is within map bounds
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            logger.debug(f"Delta Config failed: position {target_pos} out of bounds")
            return False
            
        # Cannot teleport to the same position
        if (user.y, user.x) == target_pos:
            logger.debug("Delta Config failed: cannot teleport to same position")
            return False
            
        # Check if the target position is occupied by another unit
        unit_at_target = game.get_unit_at(target_pos[0], target_pos[1])
        if unit_at_target:
            logger.debug(f"Delta Config failed: position occupied by {unit_at_target.type.name}")
            return False
        
        # Check if the target terrain is valid for teleportation
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        from boneglaive.game.map import TerrainType
        
        # Cannot teleport onto pillars or any furniture
        if terrain in [TerrainType.PILLAR, TerrainType.FURNITURE, TerrainType.COAT_RACK, 
                       TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
            logger.debug(f"Delta Config failed: cannot teleport onto terrain {terrain}")
            return False
            
        logger.debug("Delta Config check passed - skill can be used")
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """
        Queue up the Delta Config teleportation for execution at the end of the turn.
        Sets the skill target and records the skill for execution.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.event_system import get_event_manager, EventType, UIRedrawEventData
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Create a visual indicator on the target position
        if hasattr(game, 'ui') and game.ui:
            # Store the teleport target position for the UI to render
            user.teleport_target_indicator = target_pos
            
            # Request a redraw to show the indicator immediately
            event_manager = get_event_manager()
            event_manager.publish(
                EventType.UI_REDRAW_REQUESTED,
                UIRedrawEventData()
            )
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} assumes the Delta Configuration!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Delta Config teleportation during the turn resolution phase.
        This is called by the game engine when processing actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.debug import logger
        from boneglaive.game.map import TerrainType
        
        # Log debug info
        logger.debug(f"Executing Delta Config from ({user.y},{user.x}) to {target_pos}")
        
        # Ensure the target position is still valid
        # First check if target position is within map bounds
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            message_log.add_message(
                "Delta Config failed: target position is out of bounds.",
                MessageType.ABILITY,
                player=user.player
            )
            logger.debug(f"Delta Config execute failed: position {target_pos} out of bounds")
            return False
            
        # Check if the target position is occupied by another unit
        unit_at_target = game.get_unit_at(target_pos[0], target_pos[1])
        if unit_at_target:
            message_log.add_message(
                f"Delta Config failed: target position is occupied.",
                MessageType.ABILITY,
                player=user.player
            )
            logger.debug(f"Delta Config execute failed: position occupied by {unit_at_target.type.name}")
            return False
        
        # Check if the target terrain is valid for teleportation
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        
        # Cannot teleport onto pillars or any furniture
        if terrain in [TerrainType.PILLAR, TerrainType.FURNITURE, TerrainType.COAT_RACK, 
                       TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
            message_log.add_message(
                f"Delta Config failed: cannot teleport onto that terrain.",
                MessageType.ABILITY,
                player=user.player
            )
            logger.debug(f"Delta Config execute failed: cannot teleport onto terrain {terrain}")
            return False
        
        # Log the teleportation
        message_log.add_message(
            f"{user.get_display_name()} shifts through spacetime to ({target_pos[0]},{target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play teleport animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence for teleportation
            teleport_out_sequence = ui.asset_manager.get_skill_animation_sequence('teleport_out')
            teleport_in_sequence = ui.asset_manager.get_skill_animation_sequence('teleport_in')
            
            # Animate teleportation out at the original position
            if teleport_out_sequence:
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    teleport_out_sequence,
                    7,  # color ID
                    0.3  # duration
                )
            
            # Perform the actual teleportation
            old_y, old_x = user.y, user.x
            user.y, user.x = target_pos
            
            # Clear any teleport indicator
            if hasattr(user, 'teleport_target_indicator'):
                user.teleport_target_indicator = None
            
            # Animate teleportation in at the new position
            if teleport_in_sequence:
                ui.renderer.animate_attack_sequence(
                    user.y, user.x, 
                    teleport_in_sequence,
                    7,  # color ID
                    0.3  # duration
                )
            
        else:
            # If no UI is available, just perform the teleportation
            user.y, user.x = target_pos
            
            # Clear any teleport indicator
            if hasattr(user, 'teleport_target_indicator'):
                user.teleport_target_indicator = None
        
        logger.debug(f"Delta Config completed: teleported to {target_pos}")
        return True
        
class EstrangeSkill(ActiveSkill):
    """
    Active skill for GRAYMAN.
    Fires a beam that partially phases the target out of normal spacetime,
    making them permanently less effective at all actions.
    """
    
    def __init__(self):
        super().__init__(
            name="Estrange",
            key="E",
            description="Fire a beam that phases the target out of normal spacetime. Target receives -1 to all actions permanently.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Estrange can be used on target."""
        from boneglaive.utils.debug import logger
        
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            logger.debug("Estrange failed: cooldown not ready")
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            logger.debug("Estrange failed: missing game or target position")
            return False
            
        # Check if target position is within map bounds
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            logger.debug(f"Estrange failed: position {target_pos} out of bounds")
            return False
        
        # Get target unit at position
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        
        # Check if there's actually a unit at target position
        if not target_unit:
            logger.debug("Estrange failed: no unit at target position")
            return False
            
        # Check if target is an enemy
        if target_unit.player == user.player:
            logger.debug("Estrange failed: cannot target friendly units")
            return False
        
        # Check if target is already estranged
        if target_unit.estranged:
            logger.debug("Estrange failed: unit is already under Estrange effect")
            return False
        
        # Check if the target is in range
        from_y, from_x = user.y, user.x
        to_y, to_x = target_pos
        
        # Use chess distance (max of x distance and y distance)
        distance = game.chess_distance(from_y, from_x, to_y, to_x)
        if distance > self.range:
            logger.debug(f"Estrange failed: target out of range ({distance} > {self.range})")
            return False
        
        # Check line of sight
        if not game.has_line_of_sight(from_y, from_x, to_y, to_x):
            logger.debug("Estrange failed: no line of sight to target")
            return False
            
        logger.debug("Estrange check passed - skill can be used")
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up Estrange for execution."""
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
            
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            
        # Set cooldown immediately
        self.current_cooldown = self.cooldown
        
        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to estrange {target_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Estrange on the target."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.debug import logger
        
        # Get target unit at position
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        
        # Check if there's still a unit at target position
        if not target_unit:
            message_log.add_message(
                "Estrange failed: no unit at target position",
                MessageType.ABILITY,
                player=user.player
            )
            return False
            
        # Check if target is an enemy
        if target_unit.player == user.player:
            message_log.add_message(
                "Estrange failed: cannot target friendly units",
                MessageType.ABILITY,
                player=user.player
            )
            return False
        
        # Check if target is immune to the effect
        if target_unit.is_immune_to_effects():
            message_log.add_message(
                f"{target_unit.get_display_name()} is immune to Estrange due to Stasiality!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target_unit.get_display_name()
            )
            return False
            
        # Apply the Estrange effect
        target_unit.estranged = True
        
        # Log the effect
        message_log.add_message(
            f"{target_unit.get_display_name()} is phased out of normal spacetime!",
            MessageType.ABILITY,
            player=user.player,
            target_name=target_unit.get_display_name()
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Show beam animation from user to target
            beam_animation = ui.asset_manager.get_skill_animation_sequence('estrange')
            
            if beam_animation:
                # Draw a line of animation frames between user and target
                from boneglaive.utils.coordinates import get_line, Position
                
                start_pos = Position(user.y, user.x)
                end_pos = Position(target_pos[0], target_pos[1])
                
                # Get line of positions between user and target
                path = get_line(start_pos, end_pos)
                
                # Animate along the path
                for pos in path[1:]:  # Skip the starting position (user)
                    ui.renderer.animate_attack_sequence(
                        pos.y, pos.x,
                        beam_animation,
                        7,  # color ID
                        0.1  # quick animation for beam
                    )
            
            # Flash the target to show it was affected
            ui.renderer.flash_tile(
                target_unit.y, target_unit.x,
                [ui.asset_manager.get_unit_tile(target_unit.type)] * 4,
                [8, 7, 8, 7],  # Alternate colors for flashing effect
                [0.1, 0.1, 0.1, 0.1]  # Duration for each frame
            )
            
        logger.debug(f"Estrange completed: {target_unit.get_display_name()} is now estranged")
        return True
        
class GraeExchangeSkill(ActiveSkill):
    """
    Active skill for GRAYMAN.
    Creates a faint echo of GRAYMAN at his position, allowing him to teleport away.
    The echo remains for 2 turns and can perform basic attacks but cannot move.
    If destroyed, the echo deals 3 damage to all adjacent units.
    """
    
    def __init__(self):
        super().__init__(
            name="Græ Exchange",
            key="G",
            description="Teleport to target location, leaving an echo at starting position. Echo lasts 2 turns.",
            target_type=TargetType.AREA,  # Using AREA for targeting a position on the map
            cooldown=5,
            range_=6  # Limited teleport range
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Græ Exchange can be used."""
        from boneglaive.utils.debug import logger
        
        # Check cooldown and basic conditions
        if not super().can_use(user, target_pos, game):
            return False
        
        # Cannot use if user is an echo
        if user.is_echo:
            logger.debug("Græ Exchange failed: echo units cannot use skills")
            return False
            
        # Check if user already has an active echo
        if game:
            for unit in game.units:
                if unit.is_alive() and unit.is_echo and unit.original_unit == user:
                    logger.debug("Græ Exchange failed: another echo of this unit already exists")
                    return False
                    
        # Now need target position and game since we're teleporting
        if not target_pos or not game:
            return False
        
        # Check if position is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Check if the position is within range of the user
        from_y, from_x = user.y, user.x
        to_y, to_x = target_pos
        distance = game.chess_distance(from_y, from_x, to_y, to_x)
        if distance > self.range:
            logger.debug(f"Græ Exchange failed: target out of range ({distance} > {self.range})")
            return False
            
        # Check if target position is empty - can't teleport onto another unit
        if game.get_unit_at(target_pos[0], target_pos[1]):
            logger.debug("Græ Exchange failed: target position is occupied")
            return False
            
        # Check if target position is on passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            logger.debug("Græ Exchange failed: cannot teleport to impassable terrain")
            return False
        
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up Græ Exchange for execution."""
        from boneglaive.utils.message_log import message_log, MessageType
        
        if not self.can_use(user, target_pos, game):
            return False
            
        # Target-position skill
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            
        # Log the skill use
        message_log.add_message(
            f"{user.get_display_name()} taps his cane, preparing to leave an afterimage!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Græ Exchange to create an echo and teleport to target position."""
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.constants import UnitType
        from boneglaive.game.units import Unit
        
        # Store original position to create echo there
        original_y, original_x = user.y, user.x
        
        # First play the echo creation animation at current position
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Show creation animation with slow cane tap
            animation_sequence = ui.asset_manager.get_skill_animation_sequence('grae_exchange')
            if animation_sequence:
                # First show the cane tap frames very slowly
                for i in range(3):  # First 3 frames are the cane tap
                    ui.renderer.draw_tile(
                        original_y, original_x,
                        animation_sequence[i],
                        3 if user.player == 1 else 4  # Player color
                    )
                    ui.renderer.refresh()
                    time.sleep(0.3)  # Slow down for the cane tap
                
                # Then show the remaining frames at normal speed
                for i in range(3, len(animation_sequence)):
                    ui.renderer.draw_tile(
                        original_y, original_x,
                        animation_sequence[i],
                        3 if user.player == 1 else 4  # Player color
                    )
                    ui.renderer.refresh()
                    time.sleep(0.15)  # Slightly faster for the rest
            
        # Create an echo unit at original position
        echo_unit = Unit(UnitType.GRAYMAN, user.player, original_y, original_x)
        
        # Set echo properties
        echo_unit.is_echo = True
        echo_unit.echo_duration = 2  # Lasts for 2 of the owner's turns (decremented only on owner's turn)
        echo_unit.original_unit = user
        echo_unit.hp = 5  # Fixed 5 HP as specified
        
        # Copy Greek ID but add a prime symbol to distinguish
        if user.greek_id:
            echo_unit.greek_id = f"{user.greek_id}′"  # Using prime symbol (′) to indicate echo
            
        # Initialize skills (but they won't be usable due to is_echo flag)
        echo_unit.initialize_skills()
        
        # Add the echo to the game
        game.units.append(echo_unit)
        
        # Now show teleport animation and teleport the unit
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Teleport animation: first show "out" at current position
            teleport_out = ui.asset_manager.get_skill_animation_sequence('teleport_out')
            if teleport_out:
                ui.renderer.animate_attack_sequence(
                    original_y, original_x,
                    teleport_out,
                    3 if user.player == 1 else 4,  # Player color
                    0.1  # Duration
                )
            
            # Move the unit to target position
            user.y, user.x = target_pos
            
            # Then show "in" at target position
            teleport_in = ui.asset_manager.get_skill_animation_sequence('teleport_in')
            if teleport_in:
                ui.renderer.animate_attack_sequence(
                    target_pos[0], target_pos[1],
                    teleport_in,
                    3 if user.player == 1 else 4,  # Player color
                    0.1  # Duration
                )
                
            # Redraw board to show the new positions
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                time.sleep(0.3)  # Short pause to observe the teleport effect
        else:
            # If no UI, just update position directly
            user.y, user.x = target_pos
        
        # Log the effect
        message_log.add_message(
            f"{user.get_display_name()} taps his cane, teleports away and leaves behind an afterimage!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True

# Skill Registry - maps unit types to their skills
UNIT_SKILLS = {
    'GLAIVEMAN': {
        'passive': Autoclave(),
        'active': [PrySkill(), VaultSkill(), JudgementThrowSkill()]
    },
    'MANDIBLE_FOREMAN': {
        'passive': Viseroy(),
        'active': [DischargeSkill(), SiteInspectionSkill(), JawlineSkill()]
    },
    'GRAYMAN': {
        'passive': Stasiality(),
        'active': [DeltaConfigSkill(), EstrangeSkill(), GraeExchangeSkill()]
    }
    # Other unit types will be added here
}