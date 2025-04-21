#!/usr/bin/env python3
"""
Skills and abilities system for Boneglaive units.
This module provides the foundation for implementing unit skills.
"""

import curses
from enum import Enum, auto
from typing import Optional, Dict, List, Any, Tuple, TYPE_CHECKING

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
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        # Check cooldown
        if self.current_cooldown > 0:
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
            cooldown=3,
            range_=5
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
            
        # Get unit's effective move range (which includes any Pry debuff)
        effective_stats = user.get_effective_stats()
        effective_range = min(self.range, effective_stats['move_range'])
        
        # Check if target is within effective skill range
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > effective_range:
            logger.debug(f"Vault failed: position out of range ({distance} > {effective_range})")
            logger.debug(f"(Note: Effective range {effective_range} is limited by move range due to Pry)")
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

# Skill Registry - maps unit types to their skills
UNIT_SKILLS = {
    'GLAIVEMAN': {
        'passive': Autoclave(),
        'active': [PrySkill(), VaultSkill(), JudgementThrowSkill()]
    }
    # Other unit types will be added here
}