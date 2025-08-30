#!/usr/bin/env python3
"""
Skills specific to the MANDIBLE_FOREMAN unit type.
This module contains all passive and active abilities for MANDIBLE_FOREMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


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
        """Check if Expedite can be used to the target position."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check if position is valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Check if target position is passable
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False
            
        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            
        # Calculate vector components to ensure this is a straight line
        # Expedite only works in cardinal directions (horizontal, vertical, or diagonal)
        delta_y = target_pos[0] - from_y
        delta_x = target_pos[1] - from_x
        
        # Zero delta means targeting same position - disallow this
        if delta_y == 0 and delta_x == 0:
            return False
            
        # Check if movement is along a straight line (cardinal or diagonal direction)
        # This is true if one component is zero or if both have the same absolute value
        is_straight_line = (delta_y == 0 or delta_x == 0 or abs(delta_y) == abs(delta_x))
        if not is_straight_line:
            return False
            
        # Calculate path from user's position (or planned move position) to target
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(from_y, from_x), Position(target_pos[0], target_pos[1]))
        
        # Check if path is within range
        if len(path) > self.range + 1:  # +1 because path includes starting position
            return False
            
        # Check line of sight - cannot rush through impassable terrain
        # Skip first position (user's position or planned move position)
        for pos in path[1:]:
            # If we've reached the target, we're done checking
            if (pos.y, pos.x) == target_pos:
                break
                
            # Check if this position is impassable
            if not game.map.is_passable(pos.y, pos.x):
                return False
                
            # Check if there's a unit blocking the path (we can only target tiles beyond enemies)
            # But this is valid - we'll stop at the enemy in the execute method
            blocking_unit = game.get_unit_at(pos.y, pos.x)
            if blocking_unit:
                # If we hit an enemy, this is actually the first valid target
                # We'll stop here in the execute method
                if blocking_unit.player != user.player:
                    # Target position should be updated to this position
                    # But we don't modify it here, just allow the skill
                    break
                # If we hit an ally, this is invalid - can't rush through allies
                else:
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
        
        # Create a property on the unit to track the expedite path for UI
        # We'll store all the positions in the path for visualization
        from boneglaive.utils.coordinates import get_line, Position
        
        # Use planned move position if available, otherwise use current position
        from_y = user.y
        from_x = user.x
        if user.move_target:
            from_y, from_x = user.move_target
            
        path = get_line(Position(from_y, from_x), Position(target_pos[0], target_pos[1]))
        
        # Store path positions (excluding starting position) with UI indicator
        # Only include passable positions for the indicator to avoid highlighting impassable terrain
        path_positions = []
        for pos in path[1:]:
            # Check if position is passable
            if game.map.is_passable(pos.y, pos.x):
                path_positions.append((pos.y, pos.x))
            # Stop at first impassable position
            else:
                break
                
        user.expedite_path_indicator = path_positions
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} expedites his M.O. to position ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Expedite skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        import curses
        
        # Clear the expedite path indicator
        user.expedite_path_indicator = None
        
        # Store original position
        original_pos = (user.y, user.x)
        
        # Check for enemies in the path
        enemy_hit = None
        enemy_pos = None
        path_positions = []
        
        # Calculate path from start to end
        # Note: By this time, any planned move has already been executed,
        # so we no longer need to check move_target - just use current position
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(user.y, user.x), Position(target_pos[0], target_pos[1]))
        
        # Find the first enemy in the path
        for pos in path[1:]:  # Skip the starting position
            y, x = pos.y, pos.x
            
            # Check if position is valid
            if not game.is_valid_position(y, x):
                continue
                
            # Check if position is passable
            if not game.map.is_passable(y, x):
                # Stop at first impassable terrain
                break
                
            # Add to path positions for movement
            path_positions.append((y, x))
                
            # Check if there's an enemy unit at this position
            unit = game.get_unit_at(y, x)
            if unit and unit.player != user.player:
                enemy_hit = unit
                enemy_pos = (y, x)
                # Stop at the first enemy hit
                break
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} steams forward",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get animation sequence for rush animation
            rush_animation = ui.asset_manager.get_skill_animation_sequence('expedite_rush')
            
            if not rush_animation:
                rush_animation = ['Ξ', '<', '[', '{']  # Fallback
            
            # Instead of animating every position, simulate FOREMAN flying through with jaws open
            # First, determine start and end point for animation
            start_pos = (user.y, user.x)
            end_pos = enemy_pos if enemy_hit else path_positions[-1]
            
            # Get all positions between start and end for drawing FOREMAN
            animation_positions = []
            for pos in path_positions:
                animation_positions.append(pos)
                if pos == end_pos:
                    break
            
            # For very short paths, skip complex animation but still handle movement and collisions
            if len(animation_positions) <= 1:
                # If we hit an enemy, still apply trap and damage
                if enemy_hit:
                    # Apply damage to the enemy
                    damage = self.trap_damage - enemy_hit.defense
                    damage = max(1, damage)  # Minimum damage of 1
                    previous_hp = enemy_hit.hp
                    enemy_hit.hp = max(0, enemy_hit.hp - damage)
                    
                    # Log the damage
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=enemy_hit.get_display_name(),
                        damage=damage,
                        ability="Expedite",
                        attacker_player=user.player,
                        target_player=enemy_hit.player
                    )
                    
                    # Show hit animation and damage numbers even for short paths
                    if ui and hasattr(ui, 'renderer'):
                        # Show impact animation at enemy position
                        impact_animation = ui.asset_manager.get_skill_animation_sequence('expedite_impact')
                        if not impact_animation:
                            impact_animation = ['!', '!', '#', 'X', '*', '.']  # Fallback
                        
                        ui.renderer.animate_attack_sequence(
                            enemy_pos[0], enemy_pos[1],
                            impact_animation,
                            5,  # reddish color for impact
                            0.1  # duration
                        )
                        
                        # Flash the enemy to show it was hit
                        if hasattr(ui, 'asset_manager'):
                            tile_ids = [ui.asset_manager.get_unit_tile(enemy_hit.type)] * 4
                            color_ids = [5, 3 if enemy_hit.player == 1 else 4] * 2  # Alternate red with player color
                            durations = [0.1] * 4
                            
                            ui.renderer.flash_tile(enemy_pos[0], enemy_pos[1], tile_ids, color_ids, durations)
                        
                        # Show damage number
                        damage_text = f"-{damage}"
                        
                        for i in range(3):
                            ui.renderer.draw_damage_text(enemy_pos[0]-1, enemy_pos[1]*2, " " * len(damage_text), 7)
                            attrs = curses.A_BOLD if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(enemy_pos[0]-1, enemy_pos[1]*2, damage_text, 7, attrs)
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)
                    
                    # Check if enemy was defeated and handle death properly
                    if enemy_hit.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(enemy_hit, user, cause="clamp", ui=ui)
                    else:
                        # Check for critical health (retching) using centralized logic
                        game.check_critical_health(enemy_hit, user, previous_hp, ui)
                        
                        # If not immune, trap the enemy
                        if enemy_hit.hp > 0 and not enemy_hit.is_immune_to_trap():
                            # Set trapped_by to indicate this unit is trapped
                            enemy_hit.trapped_by = user
                            enemy_hit.trap_duration = 0  # Initialize trap duration for incremental damage
                            
                            message_log.add_message(
                                f"{enemy_hit.get_display_name()} is trapped in {user.get_display_name()}'s mechanical jaws",
                                MessageType.ABILITY,
                                player=user.player,
                                target=enemy_hit.player,
                                target_name=enemy_hit.get_display_name()
                            )
                            
                            # Show trapping animation
                            if ui and hasattr(ui, 'asset_manager'):
                                trap_animation = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
                                if trap_animation:
                                    ui.renderer.animate_attack_sequence(
                                        enemy_pos[0], enemy_pos[1],
                                        trap_animation,
                                        7,  # white color, matching MANDIBLE_FOREMAN's animation
                                        0.1  # duration
                                    )
                        elif enemy_hit.hp > 0:
                            message_log.add_message(
                                f"{enemy_hit.get_display_name()} is immune to Viseroy due to Stasiality",
                                MessageType.ABILITY,
                                player=enemy_hit.player,  # Use target's player color
                                target_name=enemy_hit.get_display_name()
                            )
                else:
                    # No enemy hit - move to target position directly if valid
                    if game.is_valid_position(target_pos[0], target_pos[1]) and game.map.is_passable(target_pos[0], target_pos[1]):
                        user.y, user.x = target_pos
                
                # Redraw the board after movement
                if hasattr(ui, 'draw_board'):
                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                
                return True
                
            # Initialize the board with FOREMAN removed from original position
            if hasattr(ui, 'draw_board'):
                # Temporarily "remove" FOREMAN from the board
                orig_y, orig_x = user.y, user.x
                user.y, user.x = -1, -1  # Move off-board for redraw
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                user.y, user.x = orig_y, orig_x  # Restore position (but not drawn yet)
            
            # For each frame of the animation
            # We'll move FOREMAN along the path with his jaws open
            for anim_frame in range(len(animation_positions)):
                # Calculate current position (how far along the path)
                position_idx = min(anim_frame, len(animation_positions) - 1)
                current_y, current_x = animation_positions[position_idx]
                
                # Choose jaw animation frame based on how far along we are
                # The closer to the target, the more open the jaws
                jaw_frame_idx = min(position_idx % len(rush_animation), len(rush_animation) - 1)
                jaw_frame = rush_animation[jaw_frame_idx]
                
                # Draw FOREMAN as the jaw symbol at the current position
                ui.renderer.draw_tile(current_y, current_x, jaw_frame, 7)  # white color
                ui.renderer.refresh()
                
                # If not at the last position, restore terrain at current position before moving
                if anim_frame < len(animation_positions) - 1:
                    sleep_with_animation_speed(0.05)  # Control animation speed
                    
                    # Restore the proper terrain tile instead of showing a blank space
                    terrain_type = game.map.get_terrain_at(current_y, current_x)
                    # Convert the enum to string name for asset lookup
                    terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                    terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                    
                    # Use appropriate terrain color based on terrain type
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
                    
                    # Check if there's a unit at this position that isn't the FOREMAN
                    other_unit = game.get_unit_at(current_y, current_x)
                    if other_unit and other_unit != user:
                        # Draw the unit instead of terrain
                        unit_tile = ui.asset_manager.get_unit_tile(other_unit.type)
                        unit_color = 3 if other_unit.player == 1 else 4  # Player colors
                        ui.renderer.draw_tile(current_y, current_x, unit_tile, unit_color)
                    else:
                        # Draw appropriate terrain
                        ui.renderer.draw_tile(current_y, current_x, terrain_tile, terrain_color)
                    
                    ui.renderer.refresh()
            
            # If we hit an enemy, play impact animation
            if enemy_hit:
                impact_animation = ui.asset_manager.get_skill_animation_sequence('expedite_impact')
                
                if not impact_animation:
                    impact_animation = ['!', '!', '#', 'X', '*', '.']  # Fallback
                
                # Show impact animation at enemy position
                ui.renderer.animate_attack_sequence(
                    enemy_pos[0], enemy_pos[1],
                    impact_animation,
                    5,  # reddish color for impact
                    0.1  # duration
                )
                
                # Flash the enemy to show it was hit
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(enemy_hit.type)] * 4
                    color_ids = [5, 3 if enemy_hit.player == 1 else 4] * 2  # Alternate red with player color
                    durations = [0.1] * 4
                    
                    ui.renderer.flash_tile(enemy_pos[0], enemy_pos[1], tile_ids, color_ids, durations)
                
                # Apply damage to the enemy
                damage = self.trap_damage - enemy_hit.defense
                damage = max(1, damage)  # Minimum damage of 1
                previous_hp = enemy_hit.hp
                enemy_hit.hp = max(0, enemy_hit.hp - damage)
                
                # Log the damage
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=enemy_hit.get_display_name(),
                    damage=damage,
                    ability="Expedite",
                    attacker_player=user.player,
                    target_player=enemy_hit.player
                )
                
                # Show damage number
                if hasattr(ui, 'renderer'):
                    damage_text = f"-{damage}"
                    
                    for i in range(3):
                        ui.renderer.draw_damage_text(enemy_pos[0]-1, enemy_pos[1]*2, " " * len(damage_text), 7)
                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                        ui.renderer.draw_damage_text(enemy_pos[0]-1, enemy_pos[1]*2, damage_text, 7, attrs)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                
                # Check if enemy was defeated and handle death properly
                if enemy_hit.hp <= 0:
                    # Use centralized death handling to ensure all systems (like DOMINION) are notified
                    game.handle_unit_death(enemy_hit, user, cause="viseroy", ui=ui)
                # Otherwise check critical health
                else:
                    # Check for critical health (retching) using centralized logic
                    game.check_critical_health(enemy_hit, user, previous_hp, ui)
                
                # Move FOREMAN to final position BEFORE applying trap effect to prevent auto-release
                # Stop before the enemy position
                new_foreman_pos = None
                if len(path_positions) > 1:
                    # Find position just before enemy
                    index = path_positions.index(enemy_pos)
                    if index > 0:
                        stop_pos = path_positions[index - 1]
                        new_foreman_pos = stop_pos
                        user.y, user.x = stop_pos
                    else:
                        # If there's no position before, keep original
                        new_foreman_pos = original_pos
                        user.y, user.x = original_pos
                else:
                    # No valid positions, keep original
                    new_foreman_pos = original_pos
                    user.y, user.x = original_pos
                
                # NOW apply trap AFTER the FOREMAN has moved to final position
                # This prevents the trap from being auto-released due to position change
                if enemy_hit.hp > 0:  # Only trap if target is still alive
                    # If not immune, trap the enemy
                    if not enemy_hit.is_immune_to_trap():  # Changed to is_immune_to_trap
                        # Set trapped_by to indicate this unit is trapped
                        enemy_hit.trapped_by = user
                        enemy_hit.trap_duration = 0  # Initialize trap duration for incremental damage
                        
                        message_log.add_message(
                            f"{enemy_hit.get_display_name()} is trapped in {user.get_display_name()}'s mechanical jaws",
                            MessageType.ABILITY,
                            player=user.player,
                            target=enemy_hit.player,
                            target_name=enemy_hit.get_display_name()
                        )
                        
                        # Show trapping animation
                        trap_animation = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
                        if trap_animation:
                            ui.renderer.animate_attack_sequence(
                                enemy_pos[0], enemy_pos[1],
                                trap_animation,
                                7,  # white color, matching MANDIBLE_FOREMAN's attack animation
                                0.1  # duration
                            )
                    else:
                        message_log.add_message(
                            f"{enemy_hit.get_display_name()} is immune to Viseroy due to Stasiality",
                            MessageType.ABILITY,
                            player=enemy_hit.player,  # Use target's player color
                            target_name=enemy_hit.get_display_name()
                        )
            else:
                # No enemy hit, check if target position is valid and passable
                if game.is_valid_position(target_pos[0], target_pos[1]) and game.map.is_passable(target_pos[0], target_pos[1]):
                    # Move to target position if it's valid and passable
                    user.y, user.x = target_pos
                elif path_positions:
                    # If target isn't valid but we have valid path positions, move to last valid position
                    user.y, user.x = path_positions[-1]
                # If no valid positions at all, don't move (stay at original position)
            
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        else:
            # No UI, just set position without animations
            if enemy_hit:
                # Find position just before enemy
                index = path_positions.index(enemy_pos)
                if index > 0:
                    user.y, user.x = path_positions[index - 1]
                else:
                    user.y, user.x = original_pos
            else:
                # Check if target position is valid and passable
                if game.is_valid_position(target_pos[0], target_pos[1]) and game.map.is_passable(target_pos[0], target_pos[1]):
                    # Move to target position if it's valid and passable
                    user.y, user.x = target_pos
                elif path_positions:
                    # If target isn't valid but we have valid path positions, move to last valid position
                    user.y, user.x = path_positions[-1]
                # If no valid positions at all, don't move (stay at original position)
        
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
            description="Survey a 3x3 area for tactical analysis. No terrain: +1 attack & movement. 1 terrain: +1 attack only. 2+ terrain: no effect.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3,
            area=1
        )
        self.effect_duration = 3  # Duration of the status effect in turns
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Target position must be valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x
        
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
            
        # Check if within range from the starting position (or planned move position)
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
        
        # Set site inspection target indicator for UI
        user.site_inspection_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} prepares to inspect the site around ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Site Inspection skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        
        # Clear the site inspection indicator after execution
        user.site_inspection_indicator = None
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} begins inspecting the site around ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Calculate the area (3x3 around target position)
        y, x = target_pos
        
        # Count impassable terrain in the inspection area
        impassable_count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                check_y = y + dy
                check_x = x + dx
                
                # Skip out of bounds positions
                if not game.is_valid_position(check_y, check_x):
                    continue
                
                # Check if this position has impassable terrain
                if not game.map.is_passable(check_y, check_x):
                    impassable_count += 1
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            inspection_animation = ui.asset_manager.get_skill_animation_sequence('site_inspection')
            if not inspection_animation:
                inspection_animation = ['Θ', 'Φ', 'Θ', 'Φ', 'Θ']  # Fallback with eye-like Greek letters
            
            # Show scanning effect over the area
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    check_y = y + dy
                    check_x = x + dx
                    
                    # Skip out of bounds positions
                    if not game.is_valid_position(check_y, check_x):
                        continue
                        
                    # Show inspection animation at each position
                    ui.renderer.animate_attack_sequence(
                        check_y, check_x,
                        inspection_animation,
                        3 if user.player == 1 else 4,  # Player color
                        0.05  # fast animation
                    )
            
            # Draw an outline around the inspection area
            for i in range(2):  # Repeat the outline effect
                # Top row
                for dx in [-1, 0, 1]:
                    if game.is_valid_position(y - 1, x + dx):
                        ui.renderer.draw_tile(y - 1, x + dx, '─', 3 if user.player == 1 else 4)
                        
                # Bottom row
                for dx in [-1, 0, 1]:
                    if game.is_valid_position(y + 1, x + dx):
                        ui.renderer.draw_tile(y + 1, x + dx, '─', 3 if user.player == 1 else 4)
                        
                # Left column
                for dy in [-1, 0, 1]:
                    if game.is_valid_position(y + dy, x - 1):
                        ui.renderer.draw_tile(y + dy, x - 1, '│', 3 if user.player == 1 else 4)
                        
                # Right column
                for dy in [-1, 0, 1]:
                    if game.is_valid_position(y + dy, x + 1):
                        ui.renderer.draw_tile(y + dy, x + 1, '│', 3 if user.player == 1 else 4)
                        
                # Corners
                if game.is_valid_position(y - 1, x - 1):
                    ui.renderer.draw_tile(y - 1, x - 1, '┌', 3 if user.player == 1 else 4)
                if game.is_valid_position(y - 1, x + 1):
                    ui.renderer.draw_tile(y - 1, x + 1, '┐', 3 if user.player == 1 else 4)
                if game.is_valid_position(y + 1, x - 1):
                    ui.renderer.draw_tile(y + 1, x - 1, '└', 3 if user.player == 1 else 4)
                if game.is_valid_position(y + 1, x + 1):
                    ui.renderer.draw_tile(y + 1, x + 1, '┘', 3 if user.player == 1 else 4)
                    
                ui.renderer.refresh()
                sleep_with_animation_speed(0.2)
                
                # Clear outline (replace with spaces)
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue  # Skip center
                        if game.is_valid_position(y + dy, x + dx):
                            ui.renderer.draw_tile(y + dy, x + dx, ' ', 3 if user.player == 1 else 4)
                            
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
            
            # Apply scaled buffs based on terrain count
            if impassable_count <= 1:
                # Find allies in the area and apply the buff
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        check_y = y + dy
                        check_x = x + dx
                        
                        # Skip out of bounds positions
                        if not game.is_valid_position(check_y, check_x):
                            continue
                            
                        # Check if there's an ally unit at this position
                        ally = game.get_unit_at(check_y, check_x)
                        if ally and ally.player == user.player:
                            # Check if ally is immune to status effects (GRAYMAN with Stasiality)
                            if ally.is_immune_to_effects():
                                message_log.add_message(
                                    f"{ally.get_display_name()} is immune to Site Inspection due to Stasiality",
                                    MessageType.ABILITY,
                                    player=ally.player,  # Use ally's player for correct color coding
                                    target_name=ally.get_display_name()
                                )
                                continue
                                
                            # Determine effect type based on terrain count
                            if impassable_count == 0:
                                # Full effect: +1 attack and +1 movement
                                effect_type = "full"
                                attack_bonus = 1
                                move_bonus = 1
                                effect_message = f"{ally.get_display_name()} gains +1 attack and movement from clear Site Inspection"
                                effect_symbol = "++"
                            else:  # impassable_count == 1
                                # Partial effect: +1 attack only
                                effect_type = "partial"
                                attack_bonus = 1
                                move_bonus = 0
                                effect_message = f"{ally.get_display_name()} gains +1 attack from partially obstructed Site Inspection"
                                effect_symbol = "+1"
                            
                            # Check if ally already has any site inspection status effect
                            has_full_effect = hasattr(ally, 'status_site_inspection') and ally.status_site_inspection
                            has_partial_effect = hasattr(ally, 'status_site_inspection_partial') and ally.status_site_inspection_partial
                            
                            # Apply status effect to ally
                            if not has_full_effect and not has_partial_effect:
                                # No existing effect - apply new one
                                if effect_type == "full":
                                    ally.status_site_inspection = True
                                    ally.status_site_inspection_duration = self.effect_duration
                                else:  # partial
                                    ally.status_site_inspection_partial = True
                                    ally.status_site_inspection_partial_duration = self.effect_duration
                                
                                # Apply stat bonuses
                                ally.attack_bonus = getattr(ally, 'attack_bonus', 0) + attack_bonus
                                ally.move_range_bonus = getattr(ally, 'move_range_bonus', 0) + move_bonus
                                
                                # Log the status effect application
                                message_log.add_message(effect_message, MessageType.ABILITY, player=user.player)
                                
                            elif has_full_effect and effect_type == "full":
                                # Refresh existing full effect
                                ally.status_site_inspection_duration = self.effect_duration
                                message_log.add_message(
                                    f"{ally.get_display_name()}'s full Site Inspection effect refreshed",
                                    MessageType.ABILITY,
                                    player=user.player
                                )
                            elif has_partial_effect and effect_type == "partial":
                                # Refresh existing partial effect
                                ally.status_site_inspection_partial_duration = self.effect_duration
                                message_log.add_message(
                                    f"{ally.get_display_name()}'s partial Site Inspection effect refreshed",
                                    MessageType.ABILITY,
                                    player=user.player
                                )
                            elif has_partial_effect and effect_type == "full":
                                # Upgrade partial to full effect
                                # Remove partial effect
                                ally.status_site_inspection_partial = False
                                ally.status_site_inspection_partial_duration = 0
                                # Apply full effect
                                ally.status_site_inspection = True
                                ally.status_site_inspection_duration = self.effect_duration
                                # Add movement bonus (attack bonus already applied)
                                ally.move_range_bonus = getattr(ally, 'move_range_bonus', 0) + 1
                                message_log.add_message(
                                    f"{ally.get_display_name()}'s Site Inspection upgraded to full effect",
                                    MessageType.ABILITY,
                                    player=user.player
                                )
                            elif has_full_effect and effect_type == "partial":
                                # Keep existing full effect (don't downgrade)
                                message_log.add_message(
                                    f"{ally.get_display_name()} retains full Site Inspection effect",
                                    MessageType.ABILITY,
                                    player=user.player
                                )
                            
                            # Visual feedback for new status effect application (not refreshes)
                            if (not has_full_effect and not has_partial_effect) or (has_partial_effect and effect_type == "full"):
                                if hasattr(ui, 'asset_manager'):
                                    tile_ids = [ui.asset_manager.get_unit_tile(ally.type)] * 4
                                    color_ids = [2, 3 if ally.player == 1 else 4] * 2  # Green to indicate positive effect
                                    durations = [0.1] * 4
                                    
                                    ui.renderer.flash_tile(ally.y, ally.x, tile_ids, color_ids, durations)
                                    
                                    # Display effect symbol above ally
                                    ui.renderer.draw_damage_text(ally.y-1, ally.x*2, effect_symbol, 2)  # Green text
                                    ui.renderer.refresh()
                                    sleep_with_animation_speed(0.3)
                                    
                                    # Clear effect symbol
                                    ui.renderer.draw_damage_text(ally.y-1, ally.x*2, "  ", 7)
                                    ui.renderer.refresh()
            else:
                # 2+ impassable terrain found - skill doesn't apply any buffs
                message_log.add_message(
                    f"Multiple obstructions prevent effective site analysis ({impassable_count} terrain features detected)",
                    MessageType.ABILITY,
                    player=user.player
                )
            
            # Check for INTERFERER scalar nodes in the inspection area
            if hasattr(game, 'scalar_nodes') and game.scalar_nodes:
                revealed_nodes = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        check_y = y + dy
                        check_x = x + dx
                        
                        # Skip out of bounds positions
                        if not game.is_valid_position(check_y, check_x):
                            continue
                            
                        node_pos = (check_y, check_x)
                        if node_pos in game.scalar_nodes:
                            node_info = game.scalar_nodes[node_pos]
                            owner = node_info['owner']
                            
                            # Only reveal enemy scalar nodes
                            if owner.player != user.player:
                                revealed_nodes.append(node_pos)
                
                if revealed_nodes:
                    message_log.add_message(
                        f"Site Inspection reveals {len(revealed_nodes)} standing wave pattern{'s' if len(revealed_nodes) > 1 else ''}",
                        MessageType.ABILITY,
                        player=user.player
                    )
                    
                    # Show visual indicators for revealed nodes
                    if ui and hasattr(ui, 'renderer'):
                        for node_pos in revealed_nodes:
                            node_y, node_x = node_pos
                            # Flash the revealed node position
                            for flash in range(3):
                                ui.renderer.draw_tile(node_y, node_x, '~', 6)  # Wave pattern
                                ui.renderer.refresh()
                                sleep_with_animation_speed(0.2)
                                
                                # Restore terrain
                                terrain_type = game.map.get_terrain_at(node_y, node_x)
                                terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                                terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                                ui.renderer.draw_tile(node_y, node_x, terrain_tile, 1)
                                ui.renderer.refresh()
                                sleep_with_animation_speed(0.1)
            
            # Redraw the board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
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
            description="Deploy network of mechanical jaws in 3x3 area around yourself. Deals 4 damage and completely immobilizes enemies for 2 turns.",
            target_type=TargetType.SELF,
            cooldown=3,
            range_=0,
            area=1
        )
        self.damage = 4
        self.effect_duration = 2
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # For self-targeted skills, we need the final position after any moves
        if user.move_target:
            # Use planned move position if unit has a pending move
            target_pos = user.move_target
        else:
            # Otherwise use current position
            target_pos = (user.y, user.x)
            
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set jawline indicator for UI - using the target position
        user.jawline_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} prepares to deploy a JAWLINE network",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Jawline skill to deploy a network of mechanical jaws."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        import curses
        
        # Update target position if unit has moved (due to move being executed before skill)
        # This ensures we deploy Jawline at the unit's final position after movement
        target_pos = (user.y, user.x)
        
        # Clear the jawline indicator after execution
        user.jawline_indicator = None
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} deploys JAWLINE network",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Calculate the 3x3 area around the user
        area_positions = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                # Skip the center (user's position)
                if dy == 0 and dx == 0:
                    continue
                    
                y = user.y + dy
                x = user.x + dx
                
                # Check if position is valid
                if game.is_valid_position(y, x):
                    area_positions.append((y, x))
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # First, show activation animation at the center
            # Get jaw activation animation
            trap_animation = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
            if not trap_animation:
                trap_animation = ['[', '<', '>', 'X', 'v', '|', ']']  # Fallback - ASCII only, single characters
                
            # Show activation at user's position
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                trap_animation,
                7,  # white color, matching MANDIBLE_FOREMAN's attack animation
                0.15  # duration
            )
            
            # Then expand outward to the 8 surrounding positions
            # Draw expanding ripple effect
            for ripple_size in range(1, 4):  # 3 expanding ripples
                for position in area_positions:
                    y, x = position
                    
                    # Skip positions based on ripple size to create expansion effect
                    # For ripple 1, only show cardinal directions
                    # For ripple 2, show diagonal directions
                    # For ripple 3, show all directions
                    distance = max(abs(y - user.y), abs(x - user.x))
                    if ripple_size == 1 and distance > 1:
                        continue
                    if ripple_size == 2 and distance <= 1:
                        continue
                        
                    # Draw the ripple tile and refresh
                    ripple_char = ['░', '▒', '█'][ripple_size - 1]  # Different density for each ripple
                    ui.renderer.draw_tile(y, x, ripple_char, 7)  # White color, matching MANDIBLE_FOREMAN's attack animation
                    
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
            
            # Now activate each surrounding position with a trap animation
            affected_enemies = []
            
            for position in area_positions:
                y, x = position
                
                # Show trap animation at each position
                ui.renderer.animate_attack_sequence(
                    y, x,
                    trap_animation[-4:],  # Use last few frames of trap animation
                    7,  # white color, matching MANDIBLE_FOREMAN's attack animation
                    0.1  # faster for multiple positions
                )
                
                # Check if there's an enemy at this position
                target = game.get_unit_at(y, x)
                if target and target.player != user.player:
                    # Enemy found - apply damage and effect
                    # Calculate damage (accounting for defense)
                    damage = max(1, self.damage - target.defense)
                    
                    # Track for animation
                    affected_enemies.append((target, damage))
                    
                    # Apply damage
                    previous_hp = target.hp
                    target.hp = max(0, target.hp - damage)
                    
                    # Log damage
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=target.get_display_name(),
                        damage=damage,
                        ability="Jawline",
                        attacker_player=user.player,
                        target_player=target.player
                    )
                    
                    # Check if target was defeated and handle death properly
                    if target.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(target, user, cause="discharge", ui=ui)
                    # If not defeated, check for critical health and apply Jawline effect if not immune
                    else:
                        # Check for critical health (retching) using centralized logic
                        game.check_critical_health(target, user, previous_hp, ui)
                        
                        # Check if target is immune to status effects (GRAYMAN with Stasiality)
                        if target.is_immune_to_effects():
                            message_log.add_message(
                                f"{target.get_display_name()} is immune to Jawline's immobilization due to Stasiality",
                                MessageType.ABILITY,
                                player=target.player,  # Use target's player color for immunity message
                                target_name=target.get_display_name()
                            )
                        else:
                            # Apply Jawline effect if not immune
                            target.jawline_affected = True
                            target.jawline_duration = self.effect_duration
                            # Store original move range to restore later
                            target.jawline_original_move = target.move_range
                            # Set a large negative bonus to reduce movement to 0
                            # This ensures movement is 0 regardless of other bonuses
                            target.move_range_bonus = -target.move_range
                            
                            message_log.add_message(
                                f"{target.get_display_name()} is immobilized by the Jawline tether",
                                MessageType.ABILITY,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
            
            # Show damage numbers for all affected enemies
            for target, damage in affected_enemies:
                # Flash the target
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                    color_ids = [5, 3 if target.player == 1 else 4] * 2  # Alternate red with player color
                    durations = [0.1] * 4
                    
                    ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
                
                # Show damage number
                damage_text = f"-{damage}"
                
                # Make damage text visible
                for i in range(3):
                    ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
            
            # Redraw board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        else:
            # No UI - just apply the effects
            for position in area_positions:
                y, x = position
                
                # Check if there's an enemy at this position
                target = game.get_unit_at(y, x)
                if target and target.player != user.player:
                    # Enemy found - apply damage and effect
                    # Calculate damage (accounting for defense)
                    damage = max(1, self.damage - target.defense)
                    
                    # Apply damage
                    previous_hp = target.hp
                    target.hp = max(0, target.hp - damage)
                    
                    # Log damage
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=target.get_display_name(),
                        damage=damage,
                        ability="Jawline",
                        attacker_player=user.player,
                        target_player=target.player
                    )
                    
                    # Check if target was defeated and handle death properly
                    if target.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(target, user, cause="discharge", ui=ui)
                    # If not defeated, check for critical health and apply Jawline effect if not immune
                    else:
                        # Check for critical health (retching) using centralized logic
                        game.check_critical_health(target, user, previous_hp, ui)
                        
                        # Check if target is immune to status effects (GRAYMAN with Stasiality)
                        if target.is_immune_to_effects():
                            message_log.add_message(
                                f"{target.get_display_name()} is immune to Jawline's immobilization due to Stasiality",
                                MessageType.ABILITY,
                                player=target.player,  # Use target's player color for immunity message
                                target_name=target.get_display_name()
                            )
                        else:
                            # Apply Jawline effect if not immune
                            target.jawline_affected = True
                            target.jawline_duration = self.effect_duration
                            # Store original move range to restore later
                            target.jawline_original_move = target.move_range
                            # Set a large negative bonus to reduce movement to 0
                            # This ensures movement is 0 regardless of other bonuses
                            target.move_range_bonus = -target.move_range
                            
                            message_log.add_message(
                                f"{target.get_display_name()} is immobilized by the Jawline tether",
                                MessageType.ABILITY,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
        
        return True