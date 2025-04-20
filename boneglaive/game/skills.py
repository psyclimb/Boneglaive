#!/usr/bin/env python3
"""
Skills and abilities system for Boneglaive units.
This module provides the foundation for implementing unit skills.
"""

from enum import Enum, auto
from typing import Optional, Dict, List, Any, TYPE_CHECKING

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
    When the GLAIVEMAN wretches (is brought to critical health but not killed),
    he retaliates with a four-directional, range 3, cross-shaped attack that
    heals him for half of the damage he dealt.
    Can only occur once per game per GLAIVEMAN.
    Only triggers if there is at least one enemy unit in the attack path.
    """
    
    def __init__(self):
        super().__init__(
            name="Autoclave",
            key="A",
            description="When wretched but not killed, unleashes a cross-shaped attack in four directions (range 3) and heals for half the damage dealt. One-time use. Requires enemy in range."
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
            f"GLAIVEMAN's Autoclave activates!",
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
                    
                # Mark this position for animation
                targets_in_direction.append((target_y, target_x))
                
                # Check if there's a unit at this position
                target = game.get_unit_at(target_y, target_x)
                if target and target.player != user.player:
                    # Calculate damage (fixed at 8 regardless of defense)
                    damage = 8
                    
                    # Apply damage to target
                    previous_hp = target.hp
                    target.hp = max(0, target.hp - damage)
                    
                    # Track total damage for healing
                    total_damage += damage
                    affected_units.append(target)
                    
                    # Log the attack
                    message_log.add_combat_message(
                        attacker_name=f"{user.type.name}",
                        target_name=f"{target.type.name}",
                        damage=damage,
                        ability="Autoclave",
                        attacker_player=user.player,
                        target_player=target.player
                    )
                    
                    # Check if target was defeated
                    if target.hp <= 0:
                        message_log.add_message(
                            f"Player {target.player}'s {target.type.name} perishes!",
                            MessageType.COMBAT,
                            player=user.player,
                            target=target.player
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
                f"GLAIVEMAN absorbs life essence, healing for {healing} HP!",
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
            cooldown=2,
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
            
        # Check if target is within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check if there's at least one valid displacement position
        if not self._get_displacement_positions(user, target, game):
            return False
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Use the Pry skill to displace target, reduce movement, and deal damage."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
            
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        
        # Get UI reference for animations if available
        ui = getattr(game, 'ui', None)
        
        # Calculate usable displacement positions
        displacement_positions = self._get_displacement_positions(user, target, game)
        
        if not displacement_positions:
            # This should not happen as we checked in can_use, but just in case
            message_log.add_message(
                "Pry failed: no valid displacement positions.",
                MessageType.ABILITY,
                player=user.player
            )
            return False
            
        # Choose the best displacement position (farthest from other units)
        best_pos = self._select_best_displacement(displacement_positions, game)
        
        # Log the skill activation
        message_log.add_message(
            f"GLAIVEMAN uses Pry on {target.type.name}!",
            MessageType.ABILITY,
            player=user.player
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
            
        # Apply damage to target
        previous_hp = target.hp
        target.hp = max(0, target.hp - self.damage)
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=f"{user.type.name}",
            target_name=f"{target.type.name}",
            damage=self.damage,
            ability="Pry",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Apply movement reduction effect
        target.move_range_bonus = -1
        
        # Log the movement reduction
        message_log.add_message(
            f"{target.type.name}'s movement reduced by 1 for next turn!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Store original position for animation
        original_y, original_x = target.y, target.x
        
        # Displace the target to the selected position
        target.y, target.x = best_pos
        
        # Log the displacement
        message_log.add_message(
            f"{target.type.name} displaced from ({original_y},{original_x}) to ({best_pos[0]},{best_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Animate the displacement if UI is available
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
            time.sleep(0.3)  # Short pause to show displacement
        
        # Check if target was defeated
        if target.hp <= 0:
            message_log.add_message(
                f"Player {target.player}'s {target.type.name} perishes!",
                MessageType.COMBAT,
                player=user.player,
                target=target.player
            )
            
        return True
        
    def _get_displacement_positions(self, user: 'Unit', target: 'Unit', game: 'Game') -> List[Tuple[int, int]]:
        """Calculate valid positions where the target can be displaced to."""
        # Calculate direction from user to target
        dy = target.y - user.y
        dx = target.x - user.x
        
        # Normalize direction vector
        length = max(1, game.chess_distance(0, 0, dy, dx))
        
        if dy != 0:
            direction_y = dy // abs(dy)  # Will be -1 or 1
        else:
            direction_y = 0
            
        if dx != 0:
            direction_x = dx // abs(dx)  # Will be -1 or 1
        else:
            direction_x = 0
        
        # Calculate possible displacement positions (3 tiles away in the same direction)
        displacement_distance = 3
        y = target.y + (direction_y * displacement_distance)
        x = target.x + (direction_x * displacement_distance)
        
        # Get alternative positions around the ideal position
        positions = [
            (y, x),  # Ideal position
            (y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1),  # Adjacent positions
            (y + 1, x + 1), (y + 1, x - 1), (y - 1, x + 1), (y - 1, x - 1)  # Diagonal positions
        ]
        
        # Filter for valid positions
        valid_positions = []
        for pos_y, pos_x in positions:
            # Check if position is in bounds
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
        """Select the best displacement position, prioritizing positions away from other units."""
        # If only one position, return it
        if len(positions) == 1:
            return positions[0]
            
        # Calculate scores for each position based on distance to other units
        # Higher score is better (farther from other units)
        position_scores = []
        
        for pos_y, pos_x in positions:
            score = 0
            for unit in game.units:
                if not unit.is_alive():
                    continue
                    
                # Calculate distance to other unit
                distance = game.chess_distance(pos_y, pos_x, unit.y, unit.x)
                score += distance  # Higher distance is better
                
            position_scores.append((score, (pos_y, pos_x)))
            
        # Sort by score in descending order (highest score first)
        position_scores.sort(reverse=True)
        
        # Return the position with the highest score
        return position_scores[0][1]
        
    def _get_lever_positions(self, user: 'Unit', target: 'Unit') -> List[Tuple[int, int]]:
        """Get positions for lever animation between user and target."""
        # Find midpoint for lever effect
        mid_y = (user.y + target.y) // 2
        mid_x = (user.x + target.x) // 2
        
        # Return list of positions for lever animation
        return [(mid_y, mid_x)]


class VaultSkill(ActiveSkill):
    """Active skill for GLAIVEMAN."""
    
    def __init__(self):
        super().__init__(
            name="Vault",
            key="V",
            description="Movement skill - implementation details to be defined.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3
        )


# Skill Registry - maps unit types to their skills
UNIT_SKILLS = {
    'GLAIVEMAN': {
        'passive': Autoclave(),
        'active': [PrySkill(), VaultSkill()]
    }
    # Other unit types will be added here
}