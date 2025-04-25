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
            
        # Check if position is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Calculate vector components to ensure this is a straight line
        # Expedite only works in cardinal directions (horizontal, vertical, or diagonal)
        delta_y = target_pos[0] - user.y
        delta_x = target_pos[1] - user.x
        
        # Zero delta means targeting same position - disallow this
        if delta_y == 0 and delta_x == 0:
            return False
            
        # Check if movement is along a straight line (cardinal or diagonal direction)
        # This is true if one component is zero or if both have the same absolute value
        is_straight_line = (delta_y == 0 or delta_x == 0 or abs(delta_y) == abs(delta_x))
        if not is_straight_line:
            return False
            
        # Calculate path from user to target
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(user.y, user.x), Position(target_pos[0], target_pos[1]))
        
        # Check if path is within range
        if len(path) > self.range + 1:  # +1 because path includes starting position
            return False
            
        # Check line of sight - cannot rush through impassable terrain
        # Skip first position (user's current position)
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
        path = get_line(Position(user.y, user.x), Position(target_pos[0], target_pos[1]))
        
        # Store path positions (excluding current position) with UI indicator
        path_positions = [(pos.y, pos.x) for pos in path[1:]]
        user.expedite_path_indicator = path_positions
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} expedites his M.O. to position ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Expedite skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
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
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(user.y, user.x), Position(target_pos[0], target_pos[1]))
        
        # Find the first enemy in the path
        for pos in path[1:]:  # Skip the starting position
            y, x = pos.y, pos.x
            path_positions.append((y, x))
            
            # Check if position is valid
            if not game.is_valid_position(y, x):
                continue
                
            # Check if there's an enemy unit at this position
            unit = game.get_unit_at(y, x)
            if unit and unit.player != user.player:
                enemy_hit = unit
                enemy_pos = (y, x)
                # Stop at the first enemy hit
                break
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} expedites forward!",
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
            
            # Skip animation if path is too short
            if len(animation_positions) <= 1:
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
                    time.sleep(0.05)  # Control animation speed
                    
                    # Restore the proper terrain tile instead of showing a blank space
                    terrain_type = game.map.get_terrain_at(current_y, current_x)
                    # Convert the enum to string name for asset lookup
                    terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
                    terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
                    terrain_color = 7  # Default white color for terrain
                    
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
                        ui.renderer.draw_text(enemy_pos[0]-1, enemy_pos[1]*2, " " * len(damage_text), 7)
                        attrs = curses.A_BOLD if i % 2 == 0 else 0
                        ui.renderer.draw_text(enemy_pos[0]-1, enemy_pos[1]*2, damage_text, 7, attrs)
                        ui.renderer.refresh()
                        time.sleep(0.1)
                
                # Check if enemy was defeated
                if enemy_hit.hp <= 0:
                    message_log.add_message(
                        f"{enemy_hit.get_display_name()} perishes!",
                        MessageType.COMBAT,
                        player=user.player,
                        target=enemy_hit.player,
                        target_name=enemy_hit.get_display_name()
                    )
                # Otherwise check critical health and apply trap
                else:
                    # Check for critical health (wretching) using centralized logic
                    game.check_critical_health(enemy_hit, user, previous_hp, ui)
                    
                    # If not immune, trap the enemy
                    if not enemy_hit.is_immune_to_trap():  # Changed to is_immune_to_trap
                        # Set trapped_by to indicate this unit is trapped
                        enemy_hit.trapped_by = user
                        enemy_hit.trap_duration = 0  # Initialize trap duration for incremental damage
                        
                        message_log.add_message(
                            f"{enemy_hit.get_display_name()} is trapped in {user.get_display_name()}'s mechanical jaws!",
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
                            f"{enemy_hit.get_display_name()} is immune to being trapped!",
                            MessageType.ABILITY,
                            player=user.player,
                            target=enemy_hit.player,
                            target_name=enemy_hit.get_display_name()
                        )
                
                # Stop before the enemy position
                if len(path_positions) > 1:
                    # Find position just before enemy
                    index = path_positions.index(enemy_pos)
                    if index > 0:
                        stop_pos = path_positions[index - 1]
                        user.y, user.x = stop_pos
                    else:
                        # If there's no position before, keep original
                        user.y, user.x = original_pos
                else:
                    # No valid positions, keep original
                    user.y, user.x = original_pos
            else:
                # No enemy hit, move to target position
                user.y, user.x = target_pos
            
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
                user.y, user.x = target_pos
        
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
            
        # Target position must be valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Check if within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
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
            f"{user.get_display_name()} prepares to inspect the site around ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Site Inspection skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        
        # Clear the site inspection indicator after execution
        user.site_inspection_indicator = None
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} begins inspecting the site around ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            inspection_animation = ui.asset_manager.get_skill_animation_sequence('site_inspection')
            if not inspection_animation:
                inspection_animation = ['□', '■', '□', '■', '□']  # Fallback
            
            # Calculate the area (3x3 around target position)
            y, x = target_pos
            
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
                time.sleep(0.2)
                
                # Clear outline (replace with spaces)
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue  # Skip center
                        if game.is_valid_position(y + dy, x + dx):
                            ui.renderer.draw_tile(y + dy, x + dx, ' ', 3 if user.player == 1 else 4)
                            
                ui.renderer.refresh()
                time.sleep(0.1)
            
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
                        # Apply buff to ally
                        # For now, just flash the ally with a buff color
                        if hasattr(ui, 'asset_manager'):
                            tile_ids = [ui.asset_manager.get_unit_tile(ally.type)] * 4
                            color_ids = [2, 3 if ally.player == 1 else 4] * 2  # Green to indicate buff
                            durations = [0.1] * 4
                            
                            ui.renderer.flash_tile(ally.y, ally.x, tile_ids, color_ids, durations)
                            
                            # Display buff symbol above ally
                            ui.renderer.draw_text(ally.y-1, ally.x*2, "+1", 2)  # Green text
                            ui.renderer.refresh()
                            time.sleep(0.3)
                            
                            # Clear buff symbol
                            ui.renderer.draw_text(ally.y-1, ally.x*2, "  ", 7)
                            ui.renderer.refresh()
            
            # Redraw the board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Log completion of inspection
        message_log.add_message(
            f"{user.get_display_name()} completes site inspection. All allies in the area gain +1 to attack and movement!",
            MessageType.ABILITY,
            player=user.player
        )
        
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
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set jawline indicator for UI
        user.jawline_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} prepares to deploy a JAWLINE network!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Jawline skill to deploy a network of mechanical jaws."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        import curses
        
        # Clear the jawline indicator after execution
        user.jawline_indicator = None
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} deploys JAWLINE network!",
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
                trap_animation = ['[]', '><', '}{', 'Ξ', '}{', '><', '[]']  # Fallback
                
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
                time.sleep(0.1)
            
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
                    
                    # Check if target was defeated
                    if target.hp <= 0:
                        message_log.add_message(
                            f"{target.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=user.player,
                            target=target.player,
                            target_name=target.get_display_name()
                        )
                    # If not defeated, check for critical health and apply Jawline effect if not immune
                    else:
                        # Check for critical health (wretching) using centralized logic
                        game.check_critical_health(target, user, previous_hp, ui)
                        
                        # If not immune, apply Jawline effect
                        if not target.is_immune_to_effects():
                            target.jawline_affected = True
                            target.jawline_duration = self.effect_duration
                            target.move_range_bonus -= 1
                            
                            message_log.add_message(
                                f"{target.get_display_name()}'s movement is reduced by the Jawline tether!",
                                MessageType.ABILITY,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
                        else:
                            message_log.add_message(
                                f"{target.get_display_name()} is immune to Jawline's movement penalty due to Stasiality!",
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
                    ui.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
                    ui.renderer.refresh()
                    time.sleep(0.1)
            
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
                    
                    # Check if target was defeated
                    if target.hp <= 0:
                        message_log.add_message(
                            f"{target.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=user.player,
                            target=target.player,
                            target_name=target.get_display_name()
                        )
                    # If not defeated, check for critical health and apply Jawline effect if not immune
                    else:
                        # Check for critical health (wretching) using centralized logic
                        game.check_critical_health(target, user, previous_hp, ui)
                        
                        # If not immune, apply Jawline effect
                        if not target.is_immune_to_effects():
                            target.jawline_affected = True
                            target.jawline_duration = self.effect_duration
                            target.move_range_bonus -= 1
                            
                            message_log.add_message(
                                f"{target.get_display_name()}'s movement is reduced by the Jawline tether!",
                                MessageType.ABILITY,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
                        else:
                            message_log.add_message(
                                f"{target.get_display_name()} is immune to Jawline's movement penalty due to Stasiality!",
                                MessageType.ABILITY,
                                player=user.player,
                                target=target.player,
                                target_name=target.get_display_name()
                            )
        
        return True