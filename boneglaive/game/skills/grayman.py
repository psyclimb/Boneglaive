#!/usr/bin/env python3
"""
Skills specific to the GRAYMAN unit type.
This module contains all passive and active abilities for GRAYMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Stasiality(PassiveSkill):
    """Passive skill for GRAYMAN. Immune to status effects and displacement."""

    def __init__(self):
        super().__init__(
            name="Stasiality",
            key="S",
            description="Cannot have stats changed or be displaced. Immune to buffs, debuffs, forced movement, and terrain effects."
        )

    def apply_passive(self, user: 'Unit', game=None, ui=None) -> None:
        """
        Apply Stasiality passive effects.
        Base: Immunity to status effects (handled in Unit.is_immune_to_effects())
        Upgraded: Reduce move to 0, reduce Delta Config cooldown by 6, reduce Græ Exchange cooldown by 1, +1 PRT
        """
        from boneglaive.game.upgrades import UpgradeManager

        # Check if Stasiality is upgraded
        if UpgradeManager.is_skill_upgraded(user, "Stasiality"):
            # Reduce movement to 0 (GRAYMAN becomes completely inert)
            user.move_range = 0

            # Grant +1 PRT (Partition - damage reduction)
            user.prt = 1

            # Reduce skill cooldowns
            for skill in user.active_skills:
                if skill.name == "Delta Config":
                    # Reduce from 12 to 6 (reduced by 6)
                    skill.cooldown = 6
                elif skill.name == "Græ Exchange":
                    # Reduce from 5 to 4 (reduced by 1)
                    skill.cooldown = 4


class DeltaConfigSkill(ActiveSkill):
    """Active skill for GRAYMAN. Teleports to any unoccupied tile on the map."""
    
    def __init__(self):
        super().__init__(
            name="Delta Config",
            key="D",
            description="Teleport to any unoccupied tile on the map.",
            target_type=TargetType.AREA,
            cooldown=8,
            range_=99
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Target position must be valid and passable
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
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self

        # Don't clear move_target - allow move+skill combos
        # If user moves first, they can reposition before teleporting

        # Set teleport target indicator for UI
        user.teleport_target_indicator = target_pos

        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} energizes and assumes the Delta Configuration to ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Delta Config teleportation skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
        from boneglaive.game.upgrades import UpgradeManager

        # SAFETY CHECK: Verify target position is still valid and empty
        # (Another unit might have moved there between planning and execution)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            message_log.add_message(
                f"{user.get_display_name()}'s Delta Config failed - target position occupied",
                MessageType.WARNING,
                player=user.player
            )
            # Clear indicators and return failure
            user.teleport_target_indicator = None
            return False

        # Clear the teleport target indicator after execution
        user.teleport_target_indicator = None

        # Store original position for animations
        original_pos = (user.y, user.x)

        # Check if skill is upgraded
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Delta Config")

        # If upgraded, collect adjacent enemies for abduction
        abducted_enemies = []
        if is_upgraded:
            adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dy, dx in adjacent_offsets:
                adj_y = original_pos[0] + dy
                adj_x = original_pos[1] + dx
                if game.is_valid_position(adj_y, adj_x):
                    enemy = game.get_unit_at(adj_y, adj_x)
                    if enemy and enemy.player != user.player and enemy.is_alive():
                        abducted_enemies.append((enemy, dy, dx))

        # Log the skill activation with different message if upgraded
        if is_upgraded and abducted_enemies:
            enemy_names = ", ".join([e[0].get_display_name() for e in abducted_enemies])
            message_log.add_message(
                f"{user.get_display_name()} creates an electromagnetic well, capturing {enemy_names}",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} de-energizes",
                MessageType.ABILITY,
                player=user.player
            )

        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Calculate path between origin and destination
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(original_pos[0], original_pos[1]),
                           Position(target_pos[0], target_pos[1]))

            # PHASE 1: ENERGIZE - GRAYMAN powers up at origin
            if is_upgraded:
                # Intensified energize for upgraded version
                energize_frames = ['Ψ', '@', '#', '*', '@', '#', 'Ψ', '*']
                energize_colors = [7, 6, 7, 6, 7, 6, 7, 6]  # More flashes
            else:
                # Normal energize
                energize_frames = ['Ψ', '*', 'Ψ', '*']
                energize_colors = [7, 6, 7, 6]  # White and yellow alternating

            for frame, color in zip(energize_frames, energize_colors):
                ui.renderer.draw_tile(original_pos[0], original_pos[1], frame, color)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)

            # PHASE 1.5 (UPGRADED ONLY): ELECTROMAGNETIC WELL EXPANSION
            if is_upgraded and abducted_enemies:
                adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                expand_anim = ui.asset_manager.get_skill_animation_sequence('delta_config_well_expand')
                if not expand_anim:
                    expand_anim = ['.', ':', 'o', 'O', '0', '@']

                # Show electromagnetic field expanding around GRAYMAN
                for frame in expand_anim:
                    # Keep GRAYMAN visible during expansion
                    ui.renderer.draw_tile(original_pos[0], original_pos[1], 'Ψ', 7)
                    # Draw bubble on all 8 adjacent tiles
                    for dy, dx in adjacent_offsets:
                        adj_y, adj_x = original_pos[0] + dy, original_pos[1] + dx
                        if game.is_valid_position(adj_y, adj_x):
                            ui.renderer.draw_tile(adj_y, adj_x, frame, 6)  # Yellow
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.08)

                # Pulse captured enemies to show they're trapped
                for pulse_cycle in range(2):
                    for enemy, _, _ in abducted_enemies:
                        enemy_tile = ui.asset_manager.get_unit_tile(enemy.type)
                        pulse_color = 6 if pulse_cycle % 2 == 0 else (3 if enemy.player == 1 else 4)
                        ui.renderer.draw_tile(enemy.y, enemy.x, enemy_tile, pulse_color)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)

            # PHASE 2: PULL DESTINATION TOWARD ORIGIN
            max_pull_length = len(path) - 1  # Full distance visualization

            if is_upgraded and abducted_enemies:
                # UPGRADED: Pull with electromagnetic field effect
                # Same progressive pulling but with well visualization
                for pull_distance in range(1, max_pull_length + 1):
                    # Keep GRAYMAN and well energized during pull
                    ui.renderer.draw_tile(original_pos[0], original_pos[1], '@', 6)  # More intense for upgraded

                    # Keep well visible around GRAYMAN
                    adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for dy, dx in adjacent_offsets:
                        adj_y, adj_x = original_pos[0] + dy, original_pos[1] + dx
                        if game.is_valid_position(adj_y, adj_x):
                            # Pulsing well during pull
                            well_char = 'o' if pull_distance % 2 == 0 else 'O'
                            ui.renderer.draw_tile(adj_y, adj_x, well_char, 6)

                    # Draw the electromagnetic "pull chain" from destination back toward origin
                    # Alternate between ~ and < for electromagnetic effect
                    for i in range(pull_distance):
                        pos_index = len(path) - 1 - i  # Start from destination, work backward
                        if pos_index > 0 and pos_index < len(path):  # Don't overdraw origin
                            # Alternate symbols for electromagnetic wave effect
                            pull_char = '~' if i % 2 == 0 else '<'
                            ui.renderer.draw_tile(path[pos_index].y, path[pos_index].x, pull_char, 6)

                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.06)
            else:
                # NORMAL: Pull destination toward origin - "Reeling in" the distant point
                # Draw pull symbols progressively from destination toward origin
                for pull_distance in range(1, max_pull_length + 1):
                    # Keep GRAYMAN energized during pull
                    ui.renderer.draw_tile(original_pos[0], original_pos[1], '*', 6)

                    # Draw the "pulled" chain from destination back toward origin
                    for i in range(pull_distance):
                        pos_index = len(path) - 1 - i  # Start from destination, work backward
                        if pos_index > 0 and pos_index < len(path):  # Don't overdraw origin
                            ui.renderer.draw_tile(path[pos_index].y, path[pos_index].x, '<', 6)

                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.06)

            # PHASE 3: DE-ENERGIZE & HOLD - Brief pause showing full tension
            ui.renderer.draw_tile(original_pos[0], original_pos[1], 'Ψ', 7)
            ui.renderer.refresh()
            sleep_with_animation_speed(0.1)

            # PHASE 4: ELASTIC SNAPBACK/TELEPORT - Instant release
            if not is_upgraded:
                # NORMAL: Clear the entire pull chain
                max_pull_length = len(path) - 1
                for i in range(max_pull_length):
                    pos_index = len(path) - 1 - i
                    if pos_index > 0 and pos_index < len(path):
                        terrain_type = game.map.get_terrain_at(path[pos_index].y, path[pos_index].x)
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
                        elif terrain_name.startswith('furniture') or terrain_name in ['coat_rack', 'ottoman']:
                            terrain_color = 14
                        else:
                            terrain_color = 1

                        ui.renderer.draw_tile(path[pos_index].y, path[pos_index].x, terrain_tile, terrain_color)

            # Clear origin position (GRAYMAN and well disappear)
            terrain_type = game.map.get_terrain_at(original_pos[0], original_pos[1])
            terrain_name = terrain_type.name.lower() if hasattr(terrain_type, 'name') else 'empty'
            terrain_tile = ui.asset_manager.get_terrain_tile(terrain_name)
            terrain_color = 1  # Default to empty color
            ui.renderer.draw_tile(original_pos[0], original_pos[1], terrain_tile, terrain_color)

            # INSTANT: Move unit and appear at destination with impact
            # Teleport atomically: remove from old position, update coordinates, add to new position
            # This avoids intermediate position checks that would block the teleport
            final_unit = game.get_unit_at(target_pos[0], target_pos[1])
            if final_unit is not None and final_unit != user:
                # Target occupied (should have been caught by can_use, but check anyway)
                logger.error(f"TELEPORT BLOCKED: {user.get_display_name()}'s Delta Config to {target_pos} blocked - position occupied by {final_unit.get_display_name()}")
                message_log.add_message(
                    f"{user.get_display_name()}'s Delta Config blocked - position occupied!",
                    MessageType.WARNING,
                    player=user.player
                )
                return False

            # Teleport atomically: remove from old position, update coordinates, add to new position
            old_y, old_x = user.y, user.x
            if (old_y, old_x) in game.unit_grid:
                del game.unit_grid[(old_y, old_x)]

            # Set private attributes directly (bypass property setters)
            user._y = target_pos[0]
            user._x = target_pos[1]

            # Add to new position in grid
            game.unit_grid[(target_pos[0], target_pos[1])] = user

            # Trigger trap checks if unit was trapped or is a foreman
            if hasattr(user, 'trapped_by') and user.trapped_by is not None:
                game._check_position_change_trap_release(user, old_y, old_x)
            if user.type == UnitType.MANDIBLE_FOREMAN:
                game._check_position_change_trap_release(user, old_y, old_x)

            if is_upgraded:
                # Big electromagnetic burst for upgraded version
                ui.renderer.draw_tile(target_pos[0], target_pos[1], '@', 6)
            else:
                ui.renderer.draw_tile(target_pos[0], target_pos[1], '*', 6)  # Big flash
            ui.renderer.refresh()
            sleep_with_animation_speed(0.08)

            # Show GRAYMAN at destination
            ui.renderer.draw_tile(target_pos[0], target_pos[1], 'Ψ', 7)
            ui.renderer.refresh()
            sleep_with_animation_speed(0.05)

            # PHASE 5 (UPGRADED ONLY): WELL COLLAPSE AND ENEMY PLACEMENT
            if is_upgraded and abducted_enemies:
                adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                collapse_anim = ui.asset_manager.get_skill_animation_sequence('delta_config_well_collapse')
                if not collapse_anim:
                    collapse_anim = ['@', '0', 'O', 'o', ':', '.', ' ']

                # Show well collapsing around destination
                for frame in collapse_anim:
                    # Keep GRAYMAN visible during collapse
                    ui.renderer.draw_tile(target_pos[0], target_pos[1], 'Ψ', 7)
                    # Draw collapse on all 8 adjacent tiles
                    for dy, dx in adjacent_offsets:
                        adj_y, adj_x = target_pos[0] + dy, target_pos[1] + dx
                        if game.is_valid_position(adj_y, adj_x):
                            ui.renderer.draw_tile(adj_y, adj_x, frame, 6)  # Yellow
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.06)

                # Shockwave burst
                shockwave_frames = ['*', '+', '.']
                for frame in shockwave_frames:
                    for dy, dx in adjacent_offsets:
                        adj_y, adj_x = target_pos[0] + dy, target_pos[1] + dx
                        if game.is_valid_position(adj_y, adj_x):
                            ui.renderer.draw_tile(adj_y, adj_x, frame, 7)  # White
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.05)

            # Redraw board to show final state
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

            # Flash the unit to emphasize snapback completed
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [6, 3 if user.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4

                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        else:
            # No UI, just set position without animations
            # Teleport atomically: remove from old position, update coordinates, add to new position
            # This avoids intermediate position checks that would block the teleport
            final_unit = game.get_unit_at(target_pos[0], target_pos[1])
            if final_unit is not None and final_unit != user:
                # Target occupied (should have been caught by can_use, but check anyway)
                logger.error(f"TELEPORT BLOCKED: {user.get_display_name()}'s Delta Config to {target_pos} blocked - position occupied by {final_unit.get_display_name()}")
                message_log.add_message(
                    f"{user.get_display_name()}'s Delta Config blocked - position occupied!",
                    MessageType.WARNING,
                    player=user.player
                )
                return False

            # Teleport atomically: remove from old position, update coordinates, add to new position
            old_y, old_x = user.y, user.x
            if (old_y, old_x) in game.unit_grid:
                del game.unit_grid[(old_y, old_x)]

            # Set private attributes directly (bypass property setters)
            user._y = target_pos[0]
            user._x = target_pos[1]

            # Add to new position in grid
            game.unit_grid[(target_pos[0], target_pos[1])] = user

            # Trigger trap checks if unit was trapped or is a foreman
            if hasattr(user, 'trapped_by') and user.trapped_by is not None:
                game._check_position_change_trap_release(user, old_y, old_x)
            if user.type == UnitType.MANDIBLE_FOREMAN:
                game._check_position_change_trap_release(user, old_y, old_x)

        # MOVE ABDUCTED ENEMIES TO DESTINATION (both with and without UI)
        if is_upgraded and abducted_enemies:
            adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            # Move each abducted enemy to their new position around the destination
            for enemy, rel_dy, rel_dx in abducted_enemies:
                # Try to maintain relative position
                dest_y = target_pos[0] + rel_dy
                dest_x = target_pos[1] + rel_dx

                # Check if target position is valid and empty
                if (game.is_valid_position(dest_y, dest_x) and
                    game.map.is_passable(dest_y, dest_x) and
                    game.get_unit_at(dest_y, dest_x) is None):
                    # Atomically move enemy: remove from old grid position, update coords, add to new grid position
                    old_enemy_y, old_enemy_x = enemy.y, enemy.x
                    if (old_enemy_y, old_enemy_x) in game.unit_grid:
                        del game.unit_grid[(old_enemy_y, old_enemy_x)]

                    # Set private attributes directly (bypass property setters to avoid double grid updates)
                    enemy._y = dest_y
                    enemy._x = dest_x

                    # Add to new position in grid
                    game.unit_grid[(dest_y, dest_x)] = enemy

                    # Mark enemy as abducted for graphical teleport animation
                    enemy.abducted_by_delta_config = True

                    # Trigger trap checks if enemy was trapped or is a foreman
                    if hasattr(enemy, 'trapped_by') and enemy.trapped_by is not None:
                        game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)
                    if enemy.type == UnitType.MANDIBLE_FOREMAN:
                        game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)
                else:
                    # Fallback: find any valid adjacent position around destination
                    placed = False
                    for alt_dy, alt_dx in adjacent_offsets:
                        alt_y = target_pos[0] + alt_dy
                        alt_x = target_pos[1] + alt_dx
                        if (game.is_valid_position(alt_y, alt_x) and
                            game.map.is_passable(alt_y, alt_x) and
                            game.get_unit_at(alt_y, alt_x) is None):
                            # Atomically move enemy to fallback position
                            old_enemy_y, old_enemy_x = enemy.y, enemy.x
                            if (old_enemy_y, old_enemy_x) in game.unit_grid:
                                del game.unit_grid[(old_enemy_y, old_enemy_x)]

                            # Set private attributes directly (bypass property setters)
                            enemy._y = alt_y
                            enemy._x = alt_x

                            # Add to new position in grid
                            game.unit_grid[(alt_y, alt_x)] = enemy

                            # Mark enemy as abducted for graphical teleport animation
                            enemy.abducted_by_delta_config = True

                            # Trigger trap checks if enemy was trapped or is a foreman
                            if hasattr(enemy, 'trapped_by') and enemy.trapped_by is not None:
                                game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)
                            if enemy.type == UnitType.MANDIBLE_FOREMAN:
                                game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)

                            placed = True
                            break

                    # If no position found, enemy stays at original position (well failed to capture fully)
                    # No need to do anything - enemy is already at their original position in the grid

        # Log the completion of teleportation
        if is_upgraded and abducted_enemies:
            message_log.add_message(
                f"The electromagnetic well warps from ({original_pos[0]}, {original_pos[1]}) to ({target_pos[0]}, {target_pos[1]}), releasing its cargo",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} and the distant point at ({original_pos[0]}, {original_pos[1]}) snap to position ({target_pos[0]}, {target_pos[1]})",
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
            description="Fires a beam that phases target out of normal spacetime. Target receives -1 to all actions.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )
        self.damage = 3  # Increased from 2 to 3
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False
            
        # Check if target is an enemy (not same player)
        if target_unit.player == user.player:
            return False
            
        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x
            
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
                
        # Check if target is within range from the correct position
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check line of sight
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(from_y, from_x), Position(target_pos[0], target_pos[1]))
            
        # Check for obstacles along the path (excluding the start and end points)
        for pos in path[1:-1]:
            # Check if the position is blocked by terrain
            if not game.map.is_passable(pos.y, pos.x):
                return False
                
            # Check if position is blocked by another unit
            blocking_unit = game.get_unit_at(pos.y, pos.x)
            if blocking_unit:
                return False
            
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])  
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} charges the estrangement beam targeting {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Estrange skill to phase a target out of normal spacetime."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
        from boneglaive.game.upgrades import UpgradeManager

        import curses

        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False

        # Check if upgrade is active and target is already estranged
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Estrange")
        target_already_estranged = hasattr(target, 'estranged') and target.estranged

        if is_upgraded and target_already_estranged:
            # UPGRADED PATH: Banish the already-estranged target and spawn echo
            # Log the banishment
            message_log.add_message(
                f"{user.get_display_name()} fires an estrangement beam at the already-phased {target.get_display_name()}",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )

            # Play enhanced banishment animation
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                # Get the path from user to target
                from boneglaive.utils.coordinates import get_line, Position
                path = get_line(Position(user.y, user.x), Position(target.y, target.x))

                # Get estrange animation sequence
                estrange_animation = ui.asset_manager.get_skill_animation_sequence('estrange')
                if not estrange_animation:
                    estrange_animation = ['=', '!', '~', '-', '~', '-', '~', '!', '=']

                # Show intensified beam
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    estrange_animation[:3],
                    6,  # yellowish color
                    0.1
                )

                # Animate the beam along the path (faster, more intense)
                beam_tiles = []
                for i, pos in enumerate(path[1:-1]):
                    frame_index = (i + 3) % len(estrange_animation)
                    beam_frame = estrange_animation[frame_index]
                    ui.renderer.draw_tile(pos.y, pos.x, beam_frame, 6)
                    beam_tiles.append((pos.y, pos.x, beam_frame))
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.03)  # Faster

                # Show banishment effect - target implodes
                implosion_animation = ['@', '0', 'o', '.', ' ']
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    implosion_animation,
                    19,  # Gray
                    0.15
                )

            # Store target position for echo spawning
            banished_pos = (target.y, target.x)

            # Log banishment message
            message_log.add_message(
                f"{target.get_display_name()} is torn from reality and banished!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )

            # Remove target from game (banishment - temporary)
            # Mark the unit as banished so they don't award GP
            target.is_banished = True

            # Store the banished unit so we can return them later
            if target in game.units:
                game.units.remove(target)

            # Spawn GRAYMAN echo at the banished target's location
            from boneglaive.game.units import Unit
            from boneglaive.utils.debug import logger

            echo_unit = Unit(user.type, user.player, banished_pos[0], banished_pos[1])
            echo_unit.initialize_skills()
            echo_unit.set_game_reference(game)

            # Set echo properties
            echo_unit.is_echo = True
            echo_unit.echo_duration = 2
            echo_unit.original_unit = user
            echo_unit.hp = 5
            echo_unit.max_hp = 5
            echo_unit.attack = 3

            # Store the banished unit in the echo so we can return them later
            echo_unit.banished_unit = target

            # Visual identifier
            if hasattr(user, 'greek_id') and user.greek_id:
                echo_unit.greek_id = user.greek_id.lower()

            # Add echo to game
            game.units.append(echo_unit)

            # CRITICAL: Add echo to spatial grid so get_unit_at() can find it
            game._update_unit_grid(echo_unit)

            logger.info(f"ECHO SPAWNED from banishment: {echo_unit.type.name} at position ({banished_pos[0]}, {banished_pos[1]})")

            # Log echo spawn
            message_log.add_message(
                f"An echo manifests in {target.get_display_name()}'s place",
                MessageType.ABILITY,
                player=user.player
            )

            # Show echo spawn animation
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                spawn_animation = [' ', '.', ':', 'ψ', 'Ψ', 'ψ']
                ui.renderer.animate_attack_sequence(
                    banished_pos[0], banished_pos[1],
                    spawn_animation,
                    7,  # White
                    0.15
                )

            # Redraw board
            if ui and hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

            return True

        # NORMAL PATH: Standard Estrange behavior
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} fires an estrangement beam at {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the path from user to target
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(user.y, user.x), Position(target.y, target.x))
            
            # Get estrange animation sequence
            estrange_animation = ui.asset_manager.get_skill_animation_sequence('estrange')
            if not estrange_animation:
                estrange_animation = ['=', '!', '~', '-', '~', '-', '~', '!', '=']  # ASCII-only fallback for basic terminals
            
            # Show a building effect at user position first
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                estrange_animation[:3],  # Use first few frames
                6,  # yellowish color
                0.1  # duration
            )
            
            # Animate the beam along the path
            beam_tiles = []
            for i, pos in enumerate(path[1:-1]):  # Skip first (user) and last (target) positions
                frame_index = (i + 3) % len(estrange_animation)  # Start from frame 3 and cycle
                beam_frame = estrange_animation[frame_index]
                ui.renderer.draw_tile(pos.y, pos.x, beam_frame, 6)
                beam_tiles.append((pos.y, pos.x, beam_frame))
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Animate each tile cycling through frames
            for cycle in range(len(estrange_animation)):
                for i, (tile_y, tile_x, _) in enumerate(beam_tiles):
                    frame_index = (i + 3 + cycle) % len(estrange_animation)
                    beam_frame = estrange_animation[frame_index]
                    ui.renderer.draw_tile(tile_y, tile_x, beam_frame, 6)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
            
            # Show impact at target position
            ui.renderer.animate_attack_sequence(
                target.y, target.x,
                estrange_animation[-3:],  # Use last few frames
                6,  # yellowish color
                0.15  # duration
            )
            
            # Flash the target to show impact
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [6, 3 if target.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Apply damage
        damage = self.damage
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        # Add message that estrangement bypasses defenses
        message_log.add_message(
            f"The estrangement beam bypasses {target.get_display_name()}'s defenses",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Estrange",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Show damage number if UI is available
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{damage}"
            
            for i in range(3):
                ui.renderer.draw_damage_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_damage_text(target.y-1, target.x*2, damage_text, 7, attrs)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
        
        # Apply estranged effect if not immune
        if not target.is_immune_to_effects():
            # Apply the estranged effect permanently (no duration)
            target.estranged = True
            
            # Log the effect application - using WARNING type for yellow text
            message_log.add_message(
                f"{target.get_display_name()} is phased out of normal spacetime",
                MessageType.WARNING,
                player=user.player,
                target_name=target.get_display_name()
            )
            
            # Show phasing animation if UI is available
            if ui and hasattr(ui, 'renderer'):
                # Create "phasing" visual effect with tilting characters
                phase_animation = ['|', '/', '—', '\\', '|']
                
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    phase_animation,
                    19,  # Gray color (19 is the estrangement color)
                    0.1  # duration
                )
                
                # Make the target appear "faded" by changing its color temporarily
                if hasattr(ui, 'asset_manager'):
                    # Get the unit tile
                    unit_tile = ui.asset_manager.get_unit_tile(target.type)
                    
                    # Redraw the unit with the status effect - consistent with other status effects
                    ui.renderer.draw_tile(
                        target.y, target.x,
                        f"{unit_tile}~",  # Combine unit symbol with tilde (consistent with UI rendering)
                        19,  # Gray color for estranged units
                        curses.A_DIM  # Dim attribute for negative status effect
                    )
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.3)
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to Estrange due to Stasiality",
                MessageType.ABILITY,
                player=target.player,  # Use target's player for correct color coding
                target_name=target.get_display_name()
            )
            
            # Show immunity animation if UI is available
            if ui and hasattr(ui, 'renderer'):
                # Immunity effect - show a shield ripple
                shield_animation = ['(', '[', '{', '}', ']', ')']
                
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    shield_animation,
                    7,  # white color
                    0.1  # duration
                )
        
        # Check if target was defeated and handle death properly
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="estrange", ui=ui)
        
        # Redraw board after animations
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
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

        # If no target_pos provided, just check if skill is available (for UI menu)
        if not target_pos:
            return True

        if not game:
            return False

        # Target position must be valid and passable
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
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target

        # Check if target is within range from the correct position
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self

        # Don't clear move_target - allow move+skill combos
        # If user moves first, echo will spawn at the moved position

        # Set teleport target indicator for UI
        user.teleport_target_indicator = target_pos

        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} initiates the Græ Exchange ritual targeting position ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )

        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Græ Exchange skill - create an echo at current position and teleport away."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        # CRITICAL: Capture original position FIRST, before any checks or logic
        # This ensures we get the true starting position before animations or other code modifies it
        original_pos = (user.y, user.x)
        logger.info(f"[GRÆ EXCHANGE DEBUG] Captured original_pos: {original_pos} for {user.get_display_name()}")

        # SAFETY CHECK: Verify target position is still valid and empty
        # (Another unit might have moved there between planning and execution)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            message_log.add_message(
                f"{user.get_display_name()}'s Græ Exchange failed - target position occupied",
                MessageType.WARNING,
                player=user.player
            )
            # Clear indicators and return failure
            user.teleport_target_indicator = None
            return False

        # Clear the teleport target indicator after execution
        user.teleport_target_indicator = None

        # Log the skill activation with special message for echoes
        if hasattr(user, 'is_echo') and user.is_echo:
            message_log.add_message(
                f"The echo {user.get_display_name()} performs Græ Exchange!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} begins the Græ Exchange ritual",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            exchange_animation = ui.asset_manager.get_skill_animation_sequence('grae_exchange')
            if not exchange_animation:
                exchange_animation = ['/', '_', '*', 'p', 'P']  # Fallback
            
            # Play initial animation at user's position
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                exchange_animation,
                6,  # yellowish color
                0.15  # duration
            )
            
            # Flash the current position to emphasize the echo creation
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 6
                color_ids = [6, 3 if user.player == 1 else 4] * 3  # Alternate yellow with player color
                durations = [0.1] * 6
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        
        # Create an echo unit at the original position - BEFORE moving the user
        from boneglaive.game.units import Unit
        echo_unit = Unit(user.type, user.player, original_pos[0], original_pos[1])
        echo_unit.initialize_skills()
        echo_unit.set_game_reference(game)
        logger.info(f"[GRÆ EXCHANGE DEBUG] Created echo at position ({echo_unit.y}, {echo_unit.x})")
        
        # Set echo properties
        echo_unit.is_echo = True
        echo_unit.echo_duration = 2  # Echo lasts 2 turns

        # Preserve the original_unit chain
        # If an echo is creating another echo, point to the ORIGINAL GRAYMAN, not the intermediate echo
        if hasattr(user, 'is_echo') and user.is_echo and hasattr(user, 'original_unit'):
            # Echo creating echo - preserve the chain to the original GRAYMAN
            echo_unit.original_unit = user.original_unit
        else:
            # Normal GRAYMAN creating echo
            echo_unit.original_unit = user

        echo_unit.hp = 5  # Echo has 5 HP and cannot be healed
        echo_unit.max_hp = 5  # Echo max HP is also 5

        # Set attack value for echo unit to exactly 3 (regardless of original unit's attack)
        echo_unit.attack = 3  # Increased from 2 to 3

        # Add Greek letter identifier with visual differentiation
        if hasattr(user, 'greek_id') and user.greek_id:
            if hasattr(user, 'is_echo') and user.is_echo:
                # Echo creating echo - use dot symbol to show it's 2nd generation
                echo_unit.greek_id = '·'
            else:
                # Normal unit creating echo - use lowercase
                echo_unit.greek_id = user.greek_id.lower()
        
        # Log explicit debug message about echo creation
        logger.info(f"ECHO UNIT CREATED: {echo_unit.type.name} at position ({original_pos[0]}, {original_pos[1]}) with {echo_unit.hp} HP")
        
        # Now teleport the user to the target position
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get teleport out animation sequence
            teleport_out = ui.asset_manager.get_skill_animation_sequence('teleport_out')
            if not teleport_out:
                teleport_out = ['P', '.', ':', '=', ' ']  # Fallback
            
            # Get teleport in animation sequence
            teleport_in = ui.asset_manager.get_skill_animation_sequence('teleport_in')
            if not teleport_in:
                teleport_in = [' ', '=', ':', '.', 'P']  # Fallback
            
            # Temporarily remove GRAYMAN from grid to make space for echo
            temp_y, temp_x = user.y, user.x
            game._remove_from_unit_grid(user)  # Remove from grid FIRST
            user.y, user.x = -999, -999  # Move off-screen (doesn't update grid since we removed it)

            # Add the echo unit to the game at the position GRAYMAN just left
            game.units.append(echo_unit)

            # CRITICAL: Add echo to spatial grid so get_unit_at() can find it
            game._update_unit_grid(echo_unit)
            logger.info(f"[GRÆ EXCHANGE DEBUG] Echo added to grid at ({echo_unit.y}, {echo_unit.x})")

            # Redraw to show the echo in the original position and the real unit gone
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                ui.renderer.refresh()
            
            # Pause for effect
            sleep_with_animation_speed(0.3)
            
            # Show the teleport to the new position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                teleport_in,
                7,  # white color
                0.15  # duration
            )
            
            # Actually move the unit to the target position
            # Teleport atomically: remove from old position, update coordinates, add to new position
            logger.info(f"[GRÆ EXCHANGE DEBUG] Before teleport - User at ({temp_y}, {temp_x}), Echo at ({echo_unit.y}, {echo_unit.x}), Target: {target_pos}")

            # Check target position is still empty
            final_unit = game.get_unit_at(target_pos[0], target_pos[1])
            if final_unit is not None and final_unit != user:
                # Target occupied (should have been caught by can_use, but check anyway)
                logger.error(f"TELEPORT BLOCKED: {user.get_display_name()}'s Græ Exchange to {target_pos} blocked - position occupied by {final_unit.get_display_name()}")

                # CRITICAL: Teleport failed! Remove echo first, then restore GRAYMAN
                # Remove the echo since the skill failed
                game.units.remove(echo_unit)
                game._remove_from_unit_grid(echo_unit)

                # Now restore GRAYMAN to original position
                user._y, user._x = temp_y, temp_x  # Direct assignment to bypass setters
                game._update_unit_grid(user)  # Add back to grid

                message_log.add_message(
                    f"{user.get_display_name()}'s Græ Exchange blocked - position occupied!",
                    MessageType.WARNING,
                    player=user.player
                )
                return False

            # Teleport atomically (user already removed from grid at line 1109)
            # Set private attributes directly (bypass property setters)
            user._y = target_pos[0]
            user._x = target_pos[1]

            # Add to new position in grid
            game.unit_grid[(target_pos[0], target_pos[1])] = user

            # Trigger trap checks if unit was trapped or is a foreman
            if hasattr(user, 'trapped_by') and user.trapped_by is not None:
                game._check_position_change_trap_release(user, temp_y, temp_x)
            if user.type == UnitType.MANDIBLE_FOREMAN:
                game._check_position_change_trap_release(user, temp_y, temp_x)
            
            # Redraw to show the final state
            logger.info(f"[GRÆ EXCHANGE DEBUG] After teleport - User at ({user.y}, {user.x}), Echo at ({echo_unit.y}, {echo_unit.x})")
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                ui.renderer.refresh()
                
            # Flash the moved unit to emphasize completion
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [7, 3 if user.player == 1 else 4] * 2  # Alternate white with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        else:
            # No UI, just set position without animations
            # Remove GRAYMAN from grid temporarily to make space for echo
            game._remove_from_unit_grid(user)

            # Add the echo unit to the game
            game.units.append(echo_unit)

            # CRITICAL: Add echo to spatial grid so get_unit_at() can find it
            game._update_unit_grid(echo_unit)
            logger.info(f"[GRÆ EXCHANGE DEBUG] (No UI) Echo added to grid at ({echo_unit.y}, {echo_unit.x})")

            # Move the user to the target position
            # Teleport atomically: remove from old position, update coordinates, add to new position
            # Check target position is still empty
            final_unit = game.get_unit_at(target_pos[0], target_pos[1])
            if final_unit is not None and final_unit != user:
                # Target occupied (should have been caught by can_use, but check anyway)
                logger.error(f"TELEPORT BLOCKED: {user.get_display_name()}'s Græ Exchange to {target_pos} blocked - position occupied by {final_unit.get_display_name()}")

                # CRITICAL: Teleport failed! Remove echo first, then restore GRAYMAN
                # Remove the echo since the skill failed
                game.units.remove(echo_unit)
                game._remove_from_unit_grid(echo_unit)

                # Now restore GRAYMAN to original position
                user._y, user._x = original_pos[0], original_pos[1]  # Direct assignment to bypass setters
                game._update_unit_grid(user)  # Add back to grid

                message_log.add_message(
                    f"{user.get_display_name()}'s Græ Exchange blocked - position occupied!",
                    MessageType.WARNING,
                    player=user.player
                )
                return False

            # Teleport atomically (user already removed from grid at line 1191)
            # Set private attributes directly (bypass property setters)
            user._y = target_pos[0]
            user._x = target_pos[1]

            # Add to new position in grid
            game.unit_grid[(target_pos[0], target_pos[1])] = user

            # Trigger trap checks if unit was trapped or is a foreman
            if hasattr(user, 'trapped_by') and user.trapped_by is not None:
                game._check_position_change_trap_release(user, original_pos[0], original_pos[1])
            if user.type == UnitType.MANDIBLE_FOREMAN:
                game._check_position_change_trap_release(user, original_pos[0], original_pos[1])
        
        # Log the completion with special message for echoes
        if hasattr(user, 'is_echo') and user.is_echo:
            message_log.add_message(
                f"The echo {user.get_display_name()} splits into another echo and teleports from ({original_pos[0]}, {original_pos[1]}) to ({target_pos[0]}, {target_pos[1]})",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} creates an echo and teleports from ({original_pos[0]}, {original_pos[1]}) to ({target_pos[0]}, {target_pos[1]})",
                MessageType.ABILITY,
                player=user.player
            )

        return True