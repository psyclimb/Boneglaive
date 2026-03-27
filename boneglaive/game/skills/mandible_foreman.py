#!/usr/bin/env python3
"""
Skills specific to the MANDIBLE_FOREMAN unit type.
This module contains all passive and active abilities for MANDIBLE_FOREMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger

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
    
    def apply_passive(self, user: 'Unit', game=None, ui=None) -> None:
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
            description="Rush toward an enemy in a straight line. Traps and damages the target.",
            target_type=TargetType.ENEMY,
            cooldown=5,
            range_=4  # Base range, upgraded to 5
        )
        self.trap_damage = 5
        self.base_cooldown = 5  # Store base cooldown for upgrade

    def get_range(self, user: 'Unit') -> int:
        """Get the effective range for this skill."""
        return self.range
    
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

        # Check distance - must be at least 2 tiles away (not adjacent)
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance < 2:
            return False
            
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

        # ENEMY targeting: Must have an enemy unit at target position
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or target_unit.player == user.player:
            return False

        # Calculate path from user's position (or planned move position) to target
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(from_y, from_x), Position(target_pos[0], target_pos[1]))

        # Check if path is within range (use get_range to account for upgrades)
        effective_range = self.get_range(user)
        if len(path) > effective_range + 1:  # +1 because path includes starting position
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
            # Store the planned position for the animation to use
            user.expedite_planned_start = user.move_target
            # Clear the move target - Expedite IS the movement, don't walk first
            user.move_target = None
            
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

        # Set cooldown (check for upgrade: -2 cooldown)
        from boneglaive.game.upgrades import UpgradeManager
        cooldown_value = self.base_cooldown
        if UpgradeManager.is_skill_upgraded(user, "Expedite"):
            cooldown_value -= 2
        self.current_cooldown = cooldown_value
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Expedite skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        try:
            import curses
        except ImportError:
            curses = None

        # Detect if running in graphical mode to avoid blocking sleeps
        is_graphical = ui and hasattr(ui, '__class__') and ui.__class__.__name__ == 'GraphicalUIAdapter'

        # Clear the expedite path indicator
        user.expedite_path_indicator = None
        
        # Store original position
        original_pos = (user.y, user.x)
        
        # Check for enemies in the path
        enemy_hit = None
        enemy_pos = None
        path_positions = []
        
        # Calculate path from start to end
        # Check if we stored a planned start position during use() phase
        # This handles the case where the unit had a move_target that was cleared
        if hasattr(user, 'expedite_planned_start') and user.expedite_planned_start:
            start_pos = user.expedite_planned_start
            # Clear the stored position
            user.expedite_planned_start = None
        else:
            # No planned start - use current position
            start_pos = (user.y, user.x)

        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(start_pos[0], start_pos[1]), Position(target_pos[0], target_pos[1]))
        
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

            # Check if there's an enemy unit at this position BEFORE adding to path
            unit = game.get_unit_at(y, x)
            if unit and unit.player != user.player:
                enemy_hit = unit
                enemy_pos = (y, x)
                # Don't add enemy's position to path - we stop before it
                # Stop at the first enemy hit
                break

            # Add to path positions for movement (only if no enemy here)
            path_positions.append((y, x))
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} steams forward",
            MessageType.ABILITY,
            player=user.player
        )

        # Set flag to prevent trap release during Expedite position change
        user.expediting = True

        # UPDATE FOREMAN POSITION FIRST (before applying trap, so movement doesn't break the trap!)
        # With ENEMY targeting, we always target an enemy unit, so we always stop before it
        if enemy_hit:
            # Move to last position in path (which is the tile just before the enemy)
            # If path_positions is empty, enemy was adjacent, so don't move
            if path_positions:
                target_y, target_x = path_positions[-1]
                # Teleport atomically: remove from old position, update coordinates, add to new position
                # This avoids intermediate position checks that would block the rush
                final_unit = game.get_unit_at(target_y, target_x)
                if final_unit is not None and final_unit != user:
                    # Target occupied (should have been caught by can_use, but check anyway)
                    logger.error(f"EXPEDITE BLOCKED: {user.get_display_name()}'s Expedite to {(target_y, target_x)} blocked - position occupied by {final_unit.get_display_name()}")
                    message_log.add_message(
                        f"{user.get_display_name()}'s Expedite blocked - position occupied!",
                        MessageType.WARNING,
                        player=user.player
                    )
                    # Clear expediting flag
                    user.expediting = False
                    return False

                # Teleport atomically: remove from old position, update coordinates, add to new position
                old_y, old_x = user.y, user.x
                if (old_y, old_x) in game.unit_grid:
                    del game.unit_grid[(old_y, old_x)]

                # Set private attributes directly (bypass property setters)
                user._y = target_y
                user._x = target_x

                # Add to new position in grid
                game.unit_grid[(target_y, target_x)] = user

                # Note: We DON'T call trap checks here because user.expediting = True
                # This prevents trap release during Expedite movement
            # else: No valid path positions means enemy is adjacent - stay at starting position
        # Note: With ENEMY targeting, there should always be an enemy_hit since we require targeting an enemy

        # NOW apply damage and trapping AFTER foreman has moved to final position
        # This prevents movement from breaking the trap
        if enemy_hit:
            # Store enemy hit info for graphical version to trigger JawClamp animation
            user.expedite_enemy_hit = enemy_hit
            user.expedite_enemy_pos = enemy_pos

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
                        MessageType.WARNING,
                        player=user.player,
                        target=enemy_hit.player,
                        target_name=enemy_hit.get_display_name()
                    )

                    # Check for Viseroy upgrade - apply disarm if available
                    from boneglaive.game.upgrades import UpgradeManager
                    if UpgradeManager.is_skill_upgraded(user, "Viseroy") and user.viseroy_disarm_cooldown == 0:
                        # Apply disarm effect as a proper status effect
                        enemy_hit.status_disarmed = True
                        enemy_hit.status_disarmed_duration = 1
                        user.viseroy_disarm_cooldown = 3  # 3 turn cooldown

                        message_log.add_message(
                            f"{enemy_hit.get_display_name()} is disarmed by enhanced mechanical jaws",
                            MessageType.WARNING,
                            player=user.player,
                            target=enemy_hit.player,
                            target_name=enemy_hit.get_display_name()
                        )

                        # Show disarm animation (ASCII mode only)
                        if ui and hasattr(ui, 'renderer') and not is_graphical:
                            enemy_pos = (enemy_hit.y, enemy_hit.x)

                            # Phase 1: Crushing jaw animation with disarm symbols (ASCII only)
                            disarm_sequence = ['X', 'x', '*', 'X', '*', 'x', 'X']
                            ui.renderer.animate_attack_sequence(
                                enemy_pos[0], enemy_pos[1],
                                disarm_sequence,
                                10,  # Red background to show danger
                                0.08
                            )

                            # Phase 2: Flash the enemy in red multiple times
                            if hasattr(ui, 'asset_manager'):
                                tile_ids = [ui.asset_manager.get_unit_tile(enemy_hit.type)] * 6
                                color_ids = [10, 1, 10, 1, 10, 1]  # Alternate red and white
                                durations = [0.1] * 6

                                ui.renderer.flash_tile(enemy_pos[0], enemy_pos[1], tile_ids, color_ids, durations)
                elif enemy_hit.hp > 0:
                    message_log.add_message(
                        f"{enemy_hit.get_display_name()} is immune to Viseroy due to Stasiality",
                        MessageType.ABILITY,
                        player=enemy_hit.player,  # Use target's player color
                        target_name=enemy_hit.get_display_name()
                    )

        # Play animation if UI is available (ASCII mode only)
        if not is_graphical and ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get animation sequence for rush animation
            rush_animation = ui.asset_manager.get_skill_animation_sequence('expedite_rush')
            
            if not rush_animation:
                rush_animation = ['{', '<', '[', '{']  # Fallback
            
            # Instead of animating every position, simulate FOREMAN flying through with jaws open
            # First, determine start and end point for animation
            start_pos = (user.y, user.x)
            end_pos = enemy_pos if enemy_hit else (path_positions[-1] if path_positions else start_pos)
            
            # Get all positions between start and end for drawing FOREMAN
            animation_positions = []
            for pos in path_positions:
                animation_positions.append(pos)
                if pos == end_pos:
                    break
            
            # For very short paths, skip complex animation but still show impact animations
            if len(animation_positions) <= 1:
                # If we hit an enemy, show impact animations (damage already applied above)
                if enemy_hit:
                    # Show hit animation and damage numbers even for short paths
                    if ui and hasattr(ui, 'renderer'):
                        # Show impact animation at enemy position
                        impact_animation = ui.asset_manager.get_skill_animation_sequence('expedite_impact')
                        if not impact_animation:
                            impact_animation = ['!', '!', '#', 'X', '*', '.']  # Fallback
                        
                        ui.renderer.animate_attack_sequence(
                            enemy_pos[0], enemy_pos[1],
                            impact_animation,
                            10,  # red background for impact
                            0.1  # duration
                        )
                        
                        # Flash the enemy to show it was hit
                        if hasattr(ui, 'asset_manager'):
                            tile_ids = [ui.asset_manager.get_unit_tile(enemy_hit.type)] * 4
                            color_ids = [10, 3 if enemy_hit.player == 1 else 4] * 2  # Alternate red background with player color
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

                        # Show trapping animation (if trapped - logic already ran above)
                        if enemy_hit.hp > 0 and enemy_hit.trapped_by == user:
                            trap_animation = ui.asset_manager.get_skill_animation_sequence('viseroy_trap')
                            if trap_animation:
                                ui.renderer.animate_attack_sequence(
                                    enemy_pos[0], enemy_pos[1],
                                    trap_animation,
                                    7,  # white color, matching MANDIBLE_FOREMAN's animation
                                    0.1  # duration
                                )
                # Note: Position updates now happen before UI block (line 276+)
                
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
                    10,  # red background for impact
                    0.1  # duration
                )
                
                # Flash the enemy to show it was hit
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(enemy_hit.type)] * 4
                    color_ids = [10, 3 if enemy_hit.player == 1 else 4] * 2  # Alternate red background with player color
                    durations = [0.1] * 4
                    
                    ui.renderer.flash_tile(enemy_pos[0], enemy_pos[1], tile_ids, color_ids, durations)

                # Note: Damage, trap, and position logic now handled before UI block (lines 228-299)
            
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        # Note: Position updates now happen before UI block (lines 275-299), so no else block needed

        # Clear expediting flag now that trap has been applied
        user.expediting = False

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
            description="Survey a 3x3 area for tactical analysis. No terrain: +1 attack & movement. 1 terrain: +1 movement only. 2+ terrain: no effect.",
            target_type=TargetType.AREA,
            cooldown=4,
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

        # Detect if running in graphical mode to avoid blocking sleeps
        is_graphical = ui and hasattr(ui, '__class__') and ui.__class__.__name__ == 'GraphicalUIAdapter'

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

        # Check if Site Inspection is upgraded for enhanced animation
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Site Inspection")

        # Play animation if UI is available (ASCII mode only)
        if not is_graphical and ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            inspection_animation = ui.asset_manager.get_skill_animation_sequence('site_inspection')
            if not inspection_animation:
                inspection_animation = ['#', 'O', '#', 'O', '#']  # Fallback with eye-like symbols

            if is_upgraded:
                # Enhanced animation for upgraded Site Inspection
                # Phase 1: Faster, more intense scanning with double pass
                for pass_num in range(2):  # Two scanning passes
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            check_y = y + dy
                            check_x = x + dx

                            # Skip out of bounds positions
                            if not game.is_valid_position(check_y, check_x):
                                continue

                            # Show inspection animation at each position (faster)
                            ui.renderer.animate_attack_sequence(
                                check_y, check_x,
                                inspection_animation,
                                3 if user.player == 1 else 4,  # Player color
                                0.03  # faster animation for upgraded
                            )

                # Phase 2: Radial pulse effect from center
                for radius in range(3):
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if abs(dy) + abs(dx) == radius or (radius == 2 and abs(dy) == 1 and abs(dx) == 1):
                                check_y = y + dy
                                check_x = x + dx
                                if game.is_valid_position(check_y, check_x):
                                    ui.renderer.draw_tile(check_y, check_x, '●', 2)  # Green pulse
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.08)

                # Phase 3: Enhanced outline with double-line effect
                for i in range(3):  # More repetitions
                    # Draw double-line effect (thicker border)
                    # Top row
                    for dx in [-1, 0, 1]:
                        if game.is_valid_position(y - 1, x + dx):
                            ui.renderer.draw_tile(y - 1, x + dx, '═', 3 if user.player == 1 else 4)

                    # Bottom row
                    for dx in [-1, 0, 1]:
                        if game.is_valid_position(y + 1, x + dx):
                            ui.renderer.draw_tile(y + 1, x + dx, '═', 3 if user.player == 1 else 4)

                    # Left column
                    for dy in [-1, 0, 1]:
                        if game.is_valid_position(y + dy, x - 1):
                            ui.renderer.draw_tile(y + dy, x - 1, '║', 3 if user.player == 1 else 4)

                    # Right column
                    for dy in [-1, 0, 1]:
                        if game.is_valid_position(y + dy, x + 1):
                            ui.renderer.draw_tile(y + dy, x + 1, '║', 3 if user.player == 1 else 4)

                    # Enhanced corners
                    if game.is_valid_position(y - 1, x - 1):
                        ui.renderer.draw_tile(y - 1, x - 1, '╔', 3 if user.player == 1 else 4)
                    if game.is_valid_position(y - 1, x + 1):
                        ui.renderer.draw_tile(y - 1, x + 1, '╗', 3 if user.player == 1 else 4)
                    if game.is_valid_position(y + 1, x - 1):
                        ui.renderer.draw_tile(y + 1, x - 1, '╚', 3 if user.player == 1 else 4)
                    if game.is_valid_position(y + 1, x + 1):
                        ui.renderer.draw_tile(y + 1, x + 1, '╝', 3 if user.player == 1 else 4)

                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.15)

                    # Clear outline
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue  # Skip center
                            if game.is_valid_position(y + dy, x + dx):
                                ui.renderer.draw_tile(y + dy, x + dx, ' ', 3 if user.player == 1 else 4)

                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.08)
            else:
                # Base animation (unchanged)
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

        # Apply scaled buffs based on terrain count (works in both ASCII and graphical modes)
        # Upgrade adds +1 defense to all effects and makes 2+ terrain grant +1 defense
        if impassable_count <= 1 or (impassable_count >= 2 and is_upgraded):
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

                        # Determine effect type based on terrain count and upgrade status
                        if impassable_count == 0:
                            # Clear: +1 attack, +1 movement (+1 defense if upgraded)
                            effect_type = "full"
                            attack_bonus = 1
                            move_bonus = 1
                            defense_bonus = 1 if is_upgraded else 0
                            if is_upgraded:
                                effect_message = f"{ally.get_display_name()} gains +1 attack, +1 movement, +1 defense from clear Site Inspection"
                                effect_symbol = "+++"
                            else:
                                effect_message = f"{ally.get_display_name()} gains +1 attack and movement from clear Site Inspection"
                                effect_symbol = "++"
                        elif impassable_count == 1:
                            # Partially obstructed: +1 movement (+1 defense if upgraded)
                            effect_type = "partial"
                            attack_bonus = 0
                            move_bonus = 1
                            defense_bonus = 1 if is_upgraded else 0
                            if is_upgraded:
                                effect_message = f"{ally.get_display_name()} gains +1 movement, +1 defense from partially obstructed Site Inspection"
                                effect_symbol = "++"
                            else:
                                effect_message = f"{ally.get_display_name()} gains +1 movement from partially obstructed Site Inspection"
                                effect_symbol = "+1"
                        else:  # impassable_count >= 2 (only possible if upgraded)
                            # Heavily obstructed: +1 defense only (upgrade-only effect)
                            effect_type = "obstructed"
                            attack_bonus = 0
                            move_bonus = 0
                            defense_bonus = 1
                            effect_message = f"{ally.get_display_name()} gains +1 defense from obstructed Site Inspection"
                            effect_symbol = "+D"
                        
                        # Check if ally already has any site inspection status effect
                        has_full_effect = hasattr(ally, 'status_site_inspection') and ally.status_site_inspection
                        has_partial_effect = hasattr(ally, 'status_site_inspection_partial') and ally.status_site_inspection_partial
                        
                        # Apply status effect to ally
                        if not has_full_effect and not has_partial_effect:
                            # No existing effect - apply new one
                            if effect_type == "full":
                                ally.status_site_inspection = True
                                ally.status_site_inspection_duration = self.effect_duration
                            elif effect_type == "partial":
                                ally.status_site_inspection_partial = True
                                ally.status_site_inspection_partial_duration = self.effect_duration
                            else:  # obstructed (upgrade only)
                                ally.status_site_inspection_obstructed = True
                                ally.status_site_inspection_obstructed_duration = self.effect_duration

                            # Apply stat bonuses
                            ally.attack_bonus = getattr(ally, 'attack_bonus', 0) + attack_bonus
                            ally.move_range_bonus = getattr(ally, 'move_range_bonus', 0) + move_bonus
                            ally.defense_bonus = getattr(ally, 'defense_bonus', 0) + defense_bonus

                            # Track if defense was applied for cleanup
                            if defense_bonus > 0:
                                if effect_type == "full":
                                    ally.status_site_inspection_had_defense = True
                                elif effect_type == "partial":
                                    ally.status_site_inspection_partial_had_defense = True
                                elif effect_type == "obstructed":
                                    ally.status_site_inspection_obstructed_had_defense = True

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
                        
                        # Visual feedback for new status effect application (not refreshes) - ASCII UI only
                        if (not has_full_effect and not has_partial_effect) or (has_partial_effect and effect_type == "full"):
                            if ui and hasattr(ui, 'asset_manager'):
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
            # 2+ impassable terrain found - skill doesn't apply any buffs (unless upgraded)
            # This else block should not be reached when upgraded since the condition changed
            if not is_upgraded:
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

        # Check for FOWL CONTRIVANCE Fragcrest traps in the inspection area
        if hasattr(game, 'fragcrest_traps') and game.fragcrest_traps:
            revealed_traps = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    check_y = y + dy
                    check_x = x + dx

                    # Skip out of bounds positions
                    if not game.is_valid_position(check_y, check_x):
                        continue

                    trap_pos = (check_y, check_x)
                    if trap_pos in game.fragcrest_traps:
                        trap_info = game.fragcrest_traps[trap_pos]
                        owner = trap_info['owner']

                        # Only reveal enemy Fragcrest traps
                        if owner.player != user.player:
                            revealed_traps.append(trap_pos)
                            # Mark trap as revealed
                            trap_info['revealed'] = True

            if revealed_traps:
                message_log.add_message(
                    f"Site Inspection reveals {len(revealed_traps)} Fragcrest trap{'s' if len(revealed_traps) > 1 else ''}",
                    MessageType.ABILITY,
                    player=user.player
                )

                # Show visual indicators for revealed traps
                if ui and hasattr(ui, 'renderer'):
                    for trap_pos in revealed_traps:
                        trap_y, trap_x = trap_pos
                        # Flash the revealed trap position
                        for flash in range(3):
                            ui.renderer.draw_tile(trap_y, trap_x, 'X', 1)  # X for explosive trap
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.2)
                            
                            # Restore terrain
                            terrain_type = game.map.get_terrain_at(trap_y, trap_x)
                            terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                            terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                            ui.renderer.draw_tile(trap_y, trap_x, terrain_tile, 1)
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

    def get_target_type(self, user: 'Unit') -> TargetType:
        """Get the target type for this skill, accounting for upgrades."""
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Jawline"):
            return TargetType.AREA  # Upgraded: directional area targeting
        return TargetType.SELF  # Base: self-targeted

    def get_range(self, user: 'Unit') -> int:
        """Get the effective range for this skill, accounting for upgrades."""
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Jawline"):
            return 9  # Upgraded: 9 tile range
        return 0  # Base: self-targeted (no range)

    def get_description(self, user: 'Unit') -> str:
        """Get the description for this skill, accounting for upgrades."""
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Jawline"):
            return "Deploy directional 3x9 line of mechanical jaws. Deals 4 damage and completely immobilizes enemies for 2 turns. Blocked by terrain."
        return self.description

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Check if Jawline is upgraded
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Jawline")

        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False

        # If upgraded, require directional targeting (like Expedite)
        if is_upgraded and target_pos:
            # Use correct position (current or planned move)
            from_y = user.y
            from_x = user.x
            if user.move_target:
                from_y, from_x = user.move_target

            # Calculate vector to target
            delta_y = target_pos[0] - from_y
            delta_x = target_pos[1] - from_x

            # Must target at least 1 tile away
            if delta_y == 0 and delta_x == 0:
                return False

            # Must be in a straight line (cardinal or diagonal)
            is_straight_line = (delta_y == 0 or delta_x == 0 or abs(delta_y) == abs(delta_x))
            if not is_straight_line:
                return False

            # Must be within range (9 tiles)
            distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
            if distance > 9:
                return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Check if Jawline is upgraded
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Jawline")

        # For upgraded version, target_pos is the direction endpoint
        # For base version, use self-targeting
        if not is_upgraded:
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
        try:
            import curses
        except ImportError:
            curses = None

        # Detect if running in graphical mode to avoid blocking sleeps
        is_graphical = ui and hasattr(ui, '__class__') and ui.__class__.__name__ == 'GraphicalUIAdapter'

        # Check if Jawline is upgraded
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Jawline")

        # Clear the jawline indicator after execution
        user.jawline_indicator = None

        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} deploys JAWLINE network",
            MessageType.ABILITY,
            player=user.player
        )

        # Calculate affected positions
        area_positions = []

        if is_upgraded:
            # Upgraded: 8 adjacent tiles + 3x9 directional line
            # First, add all 8 adjacent tiles (like base effect)
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

            # Then, add the 3x9 directional line extending from the user
            # Calculate direction vector from user to target
            delta_y = target_pos[0] - user.y
            delta_x = target_pos[1] - user.x

            # Normalize to unit direction
            if delta_y != 0:
                dir_y = delta_y // abs(delta_y)
            else:
                dir_y = 0

            if delta_x != 0:
                dir_x = delta_x // abs(delta_x)
            else:
                dir_x = 0

            # Calculate perpendicular direction for the 3-wide part
            if dir_y == 0:  # Horizontal line
                perp_y, perp_x = 1, 0
            elif dir_x == 0:  # Vertical line
                perp_y, perp_x = 0, 1
            else:  # Diagonal line
                # For diagonals, perpendicular is the other diagonal
                perp_y, perp_x = -dir_x, dir_y

            # Build the 3x9 line, blocked by terrain, furniture, and enemy units
            # First add the 8 surrounding tiles (like base version)
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

            # Then build the directional line extending forward
            # Track which offsets have been blocked at each distance
            blocked_offsets = set()

            for distance in range(1, 10):  # 9 tiles forward
                for offset in [-1, 0, 1]:  # 3 tiles wide
                    # Skip this offset if it was blocked at a previous distance
                    if offset in blocked_offsets:
                        continue

                    y = user.y + (dir_y * distance) + (perp_y * offset)
                    x = user.x + (dir_x * distance) + (perp_x * offset)

                    # Check if position is valid
                    if not game.is_valid_position(y, x):
                        blocked_offsets.add(offset)
                        continue

                    # Check if blocked by impassable terrain
                    if not game.map.is_passable(y, x):
                        blocked_offsets.add(offset)
                        continue

                    # Check if blocked by furniture along this specific lane
                    # Check from the previous position in this lane, not from user
                    if distance > 1:
                        prev_y = user.y + (dir_y * (distance - 1)) + (perp_y * offset)
                        prev_x = user.x + (dir_x * (distance - 1)) + (perp_x * offset)
                        if not game.has_line_of_sight(prev_y, prev_x, y, x):
                            blocked_offsets.add(offset)
                            continue
                    else:
                        # For first tile, check from user
                        if not game.has_line_of_sight(user.y, user.x, y, x):
                            blocked_offsets.add(offset)
                            continue

                    # Position is valid and not blocked - add it if not already in area_positions
                    if (y, x) not in area_positions:
                        area_positions.append((y, x))

                # If all 3 offsets are blocked, stop extending entirely
                if len(blocked_offsets) >= 3:
                    break
        else:
            # Base version: 3x3 area around user
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

        # Play animation if UI is available (ASCII mode only)
        if not is_graphical and ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
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
                    ripple_char = ['.', ':', '#'][ripple_size - 1]  # Different density for each ripple
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
                                MessageType.WARNING,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
            
            # Show damage numbers for all affected enemies
            for target, damage in affected_enemies:
                # Flash the target
                if hasattr(ui, 'asset_manager'):
                    tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                    color_ids = [10, 3 if target.player == 1 else 4] * 2  # Alternate red background with player color
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
                                MessageType.WARNING,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
        
        return True