#!/usr/bin/env python3
"""
Skills specific to the MARROW CONDENSER unit type.
This module contains all passive and active abilities for MARROW CONDENSER units.
"""

from typing import Optional, TYPE_CHECKING
import random
import curses

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Dominion(PassiveSkill):
    """
    Passive skill for MARROW CONDENSER.
    When a unit dies inside the MARROW CONDENSER's Marrow Dike, he gains permanent
    upgrades to his skills.
    """
    
    def __init__(self):
        super().__init__(
            name="Dominion",
            key="D",
            description="When a unit dies inside Marrow Dike: first death adds +1 movement, second adds +1 attack, third adds +1 defense. Deaths also upgrade skills."
        )
        self.ossify_upgraded = False
        self.marrow_dike_upgraded = False
        self.bone_tithe_upgraded = False
        self.available_upgrades = ["marrow_dike", "ossify", "bone_tithe"]
        self.kills = 0  # Track the number of kills for flat stat bonuses
    
    def apply_passive(self, user: 'Unit', game=None, ui=None) -> None:
        # Logic handled in game engine when units die
        pass
    
    def can_upgrade(self) -> bool:
        """Check if any skills are still available for upgrade."""
        return len(self.available_upgrades) > 0
    
    def get_next_upgrade(self) -> str:
        """Get the next skill to upgrade in fixed order: Marrow Dike, Ossify, then Bone Tithe."""
        if not self.available_upgrades:
            return None
        
        # Fixed upgrade order:
        # 1. Marrow Dike
        # 2. Ossify
        # 3. Bone Tithe
        if "marrow_dike" in self.available_upgrades:
            upgrade = "marrow_dike"
        elif "ossify" in self.available_upgrades:
            upgrade = "ossify"
        elif "bone_tithe" in self.available_upgrades:
            upgrade = "bone_tithe"
        else:
            # Fallback (should never happen with current implementation)
            return None
            
        self.available_upgrades.remove(upgrade)
        
        if upgrade == "ossify":
            self.ossify_upgraded = True
        elif upgrade == "marrow_dike":
            self.marrow_dike_upgraded = True
        elif upgrade == "bone_tithe":
            self.bone_tithe_upgraded = True
            
        return upgrade


class OssifySkill(ActiveSkill):
    """
    Active skill for MARROW CONDENSER.
    Temporarily compresses bone structure to become nearly impenetrable at the cost of mobility.
    When upgraded, the defense bonus increases from +2 to +3.
    """
    
    def __init__(self):
        super().__init__(
            name="Ossify",
            key="O",
            description="Temporarily compresses bone structure to become nearly impenetrable at the cost of mobility.",
            target_type=TargetType.SELF,
            cooldown=3,
            range_=0
        )
        self.upgraded = False
        self.defense_bonus = 2  # Defense bonus of 2
        self.duration = 2  # Duration in turns
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Check if unit is trapped - trapped units can only attack, not use skills
        if hasattr(user, 'trapped_by') and user.trapped_by is not None:
            return False
            
        # Basic validation (cooldown, etc.)
        return super().can_use(user, target_pos, game)
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Ossify skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # For self-targeting skills, set target to current position
        user.skill_target = (user.y, user.x)
        user.selected_skill = self
        
        # Track action order exactly like other units
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            from boneglaive.utils.debug import logger
            logger.debug(f"Setting action timestamp for {user.get_display_name()}'s Ossify skill to {user.action_timestamp}")
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to ossify their bones.",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Ossify skill during turn resolution."""
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'ossify_upgraded'):
            self.upgraded = user.passive_skill.ossify_upgraded
        
        # Calculate defense bonus based on upgrade status
        defense_bonus = 3 if self.upgraded else 2
        
        # Apply defense bonus
        user.defense_bonus += defense_bonus
        
        # Apply movement penalty (always)
        user.move_range_bonus = -1
        # Set the ossify status effect flag and duration for UI display
        user.ossify_active = True
        user.ossify_duration = self.duration  # Track duration
        
        # Use shorter message
        message_log.add_message(
            f"{user.get_display_name()}'s bones harden.",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            ossify_animation = ui.asset_manager.get_skill_animation_sequence('ossify')
            if not ossify_animation:
                ossify_animation = ['|', '#', '#', '+', '.']  # Fallback animation
                
            # Show animation at user's position
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                ossify_animation,
                7 if self.upgraded else 3,  # White for upgraded, player color for normal
                0.15  # Duration
            )
            
            # Flash the unit to show effect
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [7, 3 if user.player == 1 else 4] * 2  # Alternate white with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
                
            # If upgraded, show a more permanent effect
            if self.upgraded:
                # Additional visual effect for permanent upgrade
                ui.renderer.draw_tile(
                    user.y, user.x,
                    ui.asset_manager.get_unit_tile(user.type),
                    7  # White to indicate permanent hardening
                )
                ui.renderer.refresh()
                sleep_with_animation_speed(0.3)
                
                # Redraw board to reset colors
                if hasattr(ui, 'draw_board'):
                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class MarrowDikeSkill(ActiveSkill):
    """
    Active skill for MARROW CONDENSER.
    Creates a wall of condensed bone marrow that blocks movement and attacks.
    
    When upgraded:
    - Enemies starting their turn inside take -1 movement penalty
    - The walls are reinforced with additional HP
    """
    
    def __init__(self):
        super().__init__(
            name="Marrow Dike",
            key="M",
            description="Creates a wall of condensed bone marrow that blocks movement and attacks for 3 turns.",
            target_type=TargetType.SELF,
            cooldown=4,  # 4-turn cooldown
            range_=0,
            area=2  # 5x5 area (center + 2 in each direction)
        )
        self.upgraded = False
        self.duration = 3  # Duration of 3 turns
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Check if unit is trapped - trapped units can only attack, not use skills
        if hasattr(user, 'trapped_by') and user.trapped_by is not None:
            return False
            
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
            
# Removed prevention check - existing dikes will auto-expire when creating new ones
        
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Marrow Dike skill for execution."""
        # For self-targeting skills, set target to current position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set up wall formation indicator - use move target position if unit has issued a move command
        if user.move_target:
            center_y, center_x = user.move_target
        else:
            center_y, center_x = user.y, user.x
        user.marrow_dike_indicator = (center_y, center_x)
        
        # Track action order exactly like other units
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            from boneglaive.utils.debug import logger
            logger.debug(f"Setting action timestamp for {user.get_display_name()}'s Marrow Dike skill to {user.action_timestamp}")
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to create a Marrow Dike.",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown on this unit
        self.current_cooldown = self.cooldown
                        
        return True
    
    def _expire_existing_player_dikes(self, user: 'Unit', game: 'Game') -> None:
        """Auto-expire any existing dikes owned by the same player to allow new dike creation."""
        from boneglaive.game.map import TerrainType
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Find all wall tiles owned by this player
        tiles_to_remove = []
        if hasattr(game, 'marrow_dike_tiles'):
            for (tile_y, tile_x), dike_info in list(game.marrow_dike_tiles.items()):
                if dike_info.get('owner') and dike_info['owner'].player == user.player:
                    tiles_to_remove.append((tile_y, tile_x))
        
        # Find all interior tiles owned by this player  
        interior_to_remove = []
        if hasattr(game, 'marrow_dike_interior'):
            for (tile_y, tile_x), dike_info in list(game.marrow_dike_interior.items()):
                if dike_info.get('owner') and dike_info['owner'].player == user.player:
                    interior_to_remove.append((tile_y, tile_x))
        
        # Clean up mired status from units in expiring dike interiors
        for tile_y, tile_x in interior_to_remove:
            unit_at_pos = game.get_unit_at(tile_y, tile_x)
            if unit_at_pos and unit_at_pos.is_alive():
                # Remove mired status if it was applied by this dike
                if hasattr(unit_at_pos, 'mired') and unit_at_pos.mired:
                    unit_at_pos.mired = False
                    unit_at_pos.mired_duration = 0
                    # Restore movement penalty that was applied by mired effect
                    if hasattr(unit_at_pos, 'move_range_bonus'):
                        unit_at_pos.move_range_bonus += 1  # Remove the -1 penalty
        
        # Process wall tile removals and restore terrain
        for tile_y, tile_x in tiles_to_remove:
            tile = (tile_y, tile_x)
            
            # Restore original terrain only if current terrain is still MARROW_WALL
            if tile in game.marrow_dike_tiles and 'original_terrain' in game.marrow_dike_tiles[tile]:
                current_terrain = game.map.get_terrain_at(tile_y, tile_x)
                if current_terrain == TerrainType.MARROW_WALL:
                    original_terrain = game.marrow_dike_tiles[tile]['original_terrain']
                    game.map.set_terrain_at(tile_y, tile_x, original_terrain)
            
            # Remove from tracking and add crumbling message
            if tile in game.marrow_dike_tiles:
                dike_info = game.marrow_dike_tiles[tile]
                owner = dike_info['owner']
                del game.marrow_dike_tiles[tile]
                
                # Add crumbling message (same as natural expiration)
                message_log.add_message(
                    f"A section of {owner.get_display_name()}'s Marrow Dike crumbles away...",
                    MessageType.ABILITY,
                    player=owner.player
                )
        
        # Remove interior tiles from tracking
        for tile_y, tile_x in interior_to_remove:
            tile = (tile_y, tile_x)
            if tile in game.marrow_dike_interior:
                del game.marrow_dike_interior[tile]
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Marrow Dike skill during turn resolution."""
        from boneglaive.game.map import TerrainType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
        
        # Clear the indicator since we're executing
        user.marrow_dike_indicator = None

        # Auto-expire any existing dikes owned by this player
        self._expire_existing_player_dikes(user, game)
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'marrow_dike_upgraded'):
            self.upgraded = user.passive_skill.marrow_dike_upgraded
            
            # Update description for upgraded version
            if self.upgraded:
                self.description = "Creates a reinforced Marrow Dike that immobilizes enemies (-1 move) with stronger walls."
        
        # Generate the dike area (perimeter of a 5x5 area centered on user)
        dike_tiles = []
        dike_interior = []
        center_y, center_x = user.y, user.x
        
        # First pass to identify all tiles in 5x5 area
        for dy in range(-2, 3):  # -2, -1, 0, 1, 2
            for dx in range(-2, 3):  # -2, -1, 0, 1, 2
                # Skip the center tile (user's position)
                if dy == 0 and dx == 0:
                    continue
                    
                tile_y, tile_x = center_y + dy, center_x + dx
                
                # Check if position is valid
                if game.is_valid_position(tile_y, tile_x):
                    # If it's on the perimeter, add to dike_tiles (walls)
                    if abs(dy) == 2 or abs(dx) == 2:  # Edge positions
                        dike_tiles.append((tile_y, tile_x))
                    else:  # Interior positions
                        dike_interior.append((tile_y, tile_x))
        
        # Add the marrow dike to the game state for tracking duration and owner
        if not hasattr(game, 'marrow_dike_tiles'):
            game.marrow_dike_tiles = {}
            
        # Add tracking for interior tiles as well
        if not hasattr(game, 'marrow_dike_interior'):
            game.marrow_dike_interior = {}
            
        # Create a dictionary to track tiles that need to be restored later
        if not hasattr(game, 'previous_terrain'):
            game.previous_terrain = {}
        
        # First, identify and move units on the perimeter with improved pull logic
        units_to_move = []
        unit_movements = []  # Store original and new positions for animation
        reserved_positions = set()  # Track positions that are already claimed
        
        for tile_y, tile_x in dike_tiles:
            unit_at_tile = game.get_unit_at(tile_y, tile_x)
            if unit_at_tile:
                # Check if the unit is immune to effects (GRAYMAN with Stasiality)
                if unit_at_tile.is_immune_to_effects():
                    # Log message about immunity
                    message_log.add_message(
                        f"{unit_at_tile.get_display_name()} is immune to Marrow Dike's pull due to Stasiality.",
                        MessageType.ABILITY,
                        player=unit_at_tile.player,  # Use target unit's player for correct color coding
                        target_name=unit_at_tile.get_display_name()
                    )
                    # Skip this unit - it won't be moved and the wall won't be placed here
                    continue
                
                # Find the best available interior position for this unit
                best_position = self._find_best_interior_position(
                    unit_at_tile, tile_y, tile_x, center_y, center_x, 
                    dike_interior, game, reserved_positions
                )
                
                if best_position:
                    new_y, new_x = best_position
                    # Reserve this position so other units can't claim it
                    reserved_positions.add((new_y, new_x))
                    
                    # Store the movement info for animation
                    unit_movements.append({
                        'unit': unit_at_tile,
                        'from': (tile_y, tile_x),
                        'to': (new_y, new_x),
                        'dy': new_y - tile_y,
                        'dx': new_x - tile_x
                    })
        
        # Move units to inside the dike
        for movement in unit_movements:
            unit = movement['unit']
            from_y, from_x = movement['from']
            new_y, new_x = movement['to']
            
            # Double-check the position is still available (should be due to reservation system)
            if not game.get_unit_at(new_y, new_x):
                # Log the movement
                message_log.add_message(
                    f"{unit.get_display_name()} is pulled from ({from_y}, {from_x}) inside the Marrow Dike to ({new_y}, {new_x}).",
                    MessageType.ABILITY,
                    player=user.player,
                    target_name=unit.get_display_name()
                )
                
                # Move the unit
                unit.y = new_y
                unit.x = new_x
        
        # Now store the previous terrain and place the dike walls as actual terrain
        for tile_y, tile_x in dike_tiles:
            tile = (tile_y, tile_x)
            
            # Check if there's still a unit at this position after moves
            if game.get_unit_at(tile_y, tile_x):
                # This should be rare, but skip if still occupied
                continue
                
            # Check if current terrain is passable - only place walls on passable terrain
            current_terrain = game.map.get_terrain_at(tile_y, tile_x)
            if not game.map.is_passable(tile_y, tile_x):
                # Skip placing wall on impassable terrain (furniture, walls, etc.)
                continue
                
            # Check if this tile already has a marrow dike wall (overlapping dike prevention)
            if current_terrain == TerrainType.MARROW_WALL:
                # Skip placing wall on existing wall to prevent overlap bug
                continue
                
            # Store original terrain to restore later
            original_terrain = current_terrain
            game.previous_terrain[tile] = original_terrain
            
            # Set the tile to MARROW_WALL terrain (special terrain for dike)
            game.map.set_terrain_at(tile_y, tile_x, TerrainType.MARROW_WALL)
            
            # Associate this tile with the dike
            game.marrow_dike_tiles[tile] = {
                'owner': user,
                'duration': self.duration,
                'upgraded': self.upgraded,
                'original_terrain': original_terrain,
                'hp': 2 if self.upgraded else 1  # 2 HP when upgraded, 1 HP otherwise
            }
        
        # Track interior tiles for Dominion passive detection
        for tile_y, tile_x in dike_interior:
            tile = (tile_y, tile_x)
            
            # Check if this tile was pre-established during turn resolution
            if tile in game.marrow_dike_interior and game.marrow_dike_interior[tile].get('pre_established', False):
                # Update the pre-established tracking with final values - DOMINION tracking officially begins now
                game.marrow_dike_interior[tile].update({
                    'duration': self.duration,
                    'upgraded': self.upgraded,
                    'pre_established': False  # Mark as no longer pre-established - now "real" tracking
                })
            else:
                # Associate this interior tile with the dike - DOMINION tracking begins now
                game.marrow_dike_interior[tile] = {
                    'owner': user,
                    'duration': self.duration,
                    'upgraded': self.upgraded
                }
        
        # Log the skill activation
        if self.upgraded:
            message_log.add_message(
                f"{user.get_display_name()} shores up a Marrow Dike and fills it with plasma.",
                MessageType.ABILITY,
                player=user.player
            )
            
            # Immediately apply movement penalties to enemies trapped inside the upgraded Marrow Dike
            for tile_y, tile_x in dike_interior:
                unit_at_pos = game.get_unit_at(tile_y, tile_x)
                if unit_at_pos and unit_at_pos.is_alive() and unit_at_pos.player != user.player:
                    # Check if unit is immune to effects due to Stasiality
                    if unit_at_pos.is_immune_to_effects():
                        # Show message about immunity
                        message_log.add_message(
                            f"{unit_at_pos.get_display_name()} ignores the Marrow Dike's effect due to Stasiality.",
                            MessageType.ABILITY,
                            player=unit_at_pos.player,
                            target_name=unit_at_pos.get_display_name()
                        )
                        unit_at_pos.marrow_dike_immunity_message_shown = True
                    # For non-immune units, apply the mired status effect
                    elif not hasattr(unit_at_pos, 'mired') or not unit_at_pos.mired:
                        unit_at_pos.mired = True
                        unit_at_pos.mired_duration = self.duration
                        unit_at_pos.move_range_bonus -= 1
                        
                        # Shorter message for each enemy unit trapped inside
                        message_log.add_message(
                            f"{unit_at_pos.get_display_name()} slogs through the Marrow Dike.",
                            MessageType.ABILITY,
                            player=user.player,
                            attacker_name=user.get_display_name(),
                            target_name=unit_at_pos.get_display_name()
                        )
        else:
            message_log.add_message(
                f"{user.get_display_name()} creates a Marrow Dike.",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer'):
            # First visualize any unit movement animations
            for movement in unit_movements:
                if hasattr(ui, 'renderer'):
                    unit = movement['unit']
                    orig_y, orig_x = movement['from']
                    new_y, new_x = movement['to']
                    dy, dx = movement['dy'], movement['dx']
                    
                    # Show animation of unit being pulled in
                    pull_animation = ['>', 'v', '<', '^']  # Direction indicators

                    # Choose the right direction indicator based on direction
                    direction_idx = 0
                    if dx > 0:
                        direction_idx = 0  # >
                    elif dy > 0:
                        direction_idx = 1  # v
                    elif dx < 0:
                        direction_idx = 2  # <
                    elif dy < 0:
                        direction_idx = 3  # ^
                        
                    # Draw directional indicator
                    ui.renderer.draw_tile(
                        orig_y, orig_x,
                        pull_animation[direction_idx],
                        6  # Yellow color for movement
                    )
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.2)
                    
                    # Show unit at new position
                    unit_symbol = ui.asset_manager.get_unit_tile(unit.type)
                    ui.renderer.draw_tile(
                        new_y, new_x,
                        unit_symbol,
                        3 if unit.player == 1 else 4  # Player color
                    )
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.2)
            
            # Now show the walls being created
            # Get wall animation from asset manager
            wall_animation = ui.asset_manager.get_skill_animation_sequence('marrow_dike')
            if not wall_animation:
                # Fallback animation if not defined in asset manager
                wall_animation = ['╎', '╏', '┃', '┆', '┇', '┊', '┋', '#']
            
            # Draw animation for each tile in sequence
            for i, (tile_y, tile_x) in enumerate(dike_tiles):
                # Check if there's still a unit at this position after moves
                unit_at_tile = game.get_unit_at(tile_y, tile_x)
                
                if not unit_at_tile:
                    # Animate the wall creation with player's color
                    ui.renderer.animate_attack_sequence(
                        tile_y, tile_x,
                        wall_animation,
                        3 if user.player == 1 else 4,  # Player color (3 for Player 1, 4 for Player 2)
                        0.05  # Quick animation
                    )
                    
                    # If upgraded, add a reinforced wall effect
                    if self.upgraded:
                        prison_animation = ['#', '=', '#', '=', '#']
                        # Draw upgraded walls with reinforced elements
                        ui.renderer.animate_attack_sequence(
                            tile_y, tile_x,
                            prison_animation,
                            7,  # White color for bone structures
                            0.05  # Quick animation
                        )
                    
                    # Draw final wall symbol in player's color
                    ui.renderer.draw_tile(
                        tile_y, tile_x,
                        '#',  # Hash symbol for walls
                        3 if user.player == 1 else 4  # Player color (3 for Player 1, 4 for Player 2)
                    )
                
                # If it's the 10th tile or last tile, pause briefly to avoid overwhelming rendering
                if i % 10 == 9 or i == len(dike_tiles) - 1:
                    sleep_with_animation_speed(0.1)
                    
                    # Redraw to show progress
                    if hasattr(ui, 'draw_board'):
                        ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                        
            # Draw final state
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True

    def _find_best_interior_position(self, unit, perimeter_y, perimeter_x, center_y, center_x, dike_interior, game, reserved_positions):
        """
        Find the best available interior position for a unit on the perimeter.
        
        Args:
            unit: The unit to be moved
            perimeter_y, perimeter_x: Current position of the unit (on perimeter)
            center_y, center_x: Center position of the dike
            dike_interior: Set of (y, x) tuples representing interior positions
            game: Game instance for checking occupancy and terrain
            reserved_positions: Set of positions already claimed by other units in this pull operation
            
        Returns:
            (y, x) tuple of best position, or None if no valid position found
        """
        # All 8 possible adjacent directions
        directions = [
            (-1, -1), (-1, 0), (-1, 1),  # up-left, up, up-right
            ( 0, -1),          ( 0, 1),  # left, right
            ( 1, -1), ( 1, 0), ( 1, 1)   # down-left, down, down-right
        ]
        
        candidates = []
        
        # Check each adjacent position
        for dy, dx in directions:
            new_y = perimeter_y + dy
            new_x = perimeter_x + dx
            candidate_pos = (new_y, new_x)
            
            # Check if position is valid
            if (new_y < 0 or new_y >= game.map.height or 
                new_x < 0 or new_x >= game.map.width):
                continue  # Out of bounds
            
            # Check if position is in the interior area
            if candidate_pos not in dike_interior:
                continue  # Not in interior
                
            # Check if terrain is passable
            if not game.map.is_passable(new_y, new_x):
                continue  # Impassable terrain
                
            # Check if position is already occupied by another unit
            if game.get_unit_at(new_y, new_x):
                continue  # Occupied by existing unit
                
            # Check if position is already reserved by another unit in this pull operation
            if candidate_pos in reserved_positions:
                continue  # Already claimed
            
            # This is a valid candidate - calculate its priority
            # Distance to center (prefer closer to center)
            distance_to_center = abs(new_y - center_y) + abs(new_x - center_x)
            
            candidates.append((candidate_pos, distance_to_center))
        
        if not candidates:
            return None  # No valid positions found
            
        # Sort by distance to center (closer is better, so smaller distance first)
        candidates.sort(key=lambda x: x[1])
        
        # Return the best position (closest to center)
        return candidates[0][0]


class BoneTitheSkill(ActiveSkill):
    """
    Active skill for MARROW CONDENSER.
    Extracts a tithe of bone marrow from nearby enemies, damaging them while
    strengthening the MARROW CONDENSER with their essence.
    
    When upgraded:
    - Increases HP gain per enemy hit from +1 to +2
    - Damage scales with all kills (1 + kill count), including kills from before the upgrade
    """
    
    def __init__(self):
        super().__init__(
            name="Bone Tithe",
            key="B",
            description="Extracts marrow from adjacent enemies for 1 damage and gains +1 HP for each enemy hit.",
            target_type=TargetType.SELF,  # Self-targeted area effect
            cooldown=1,
            range_=0,
            area=1  # 3x3 area (center + 1 in each direction)
        )
        self.upgraded = False
        self.base_damage = 1  # Base damage (increases with kills)
        self.hp_gain_per_hit = 1  # Base HP gain per enemy hit (increases to 2 when upgraded)
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation (cooldown, etc.)
        if not super().can_use(user, target_pos, game):
            return False
            
        # Always usable as long as basic validation passes
        return True
        
        # If not upgraded, check if user has enough health to heal at least one ally
        if not self.upgraded:
            min_health_needed = self.self_damage
            if potential_allies_to_heal > 0 and user.hp <= min_health_needed:
                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"{user.get_display_name()} needs at least {min_health_needed+1} HP to use Bone Tithe.",
                    MessageType.WARNING,
                    player=user.player
                )
                return False
        
        # Skill can be used if there are any valid targets or we're upgraded (which might share buffs)
        return potential_allies_to_heal > 0 or self.upgraded
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Bone Tithe skill for execution."""
        # For self-targeting skills, set target to current position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
            
        # Always set both skill target and selected_skill
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Clear any previous action timestamp
        user.action_timestamp = 0
        
        # Always set a new action timestamp, matching exactly what other unit types do
        if game:
            # Set action timestamp directly from action counter (no conditions)
            user.action_timestamp = game.action_counter
            # Increment action counter for next action
            game.action_counter += 1
            # Log the timestamp assignment for debugging
            from boneglaive.utils.debug import logger
            logger.debug(f"Setting action timestamp for {user.get_display_name()}'s Bone Tithe skill to {user.action_timestamp}")
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to collect the Bone Tithe.",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown immediately - this matches other skill implementations
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Bone Tithe skill during turn resolution."""
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
        from boneglaive.utils.debug import logger
        
        # Log that we're executing this skill
        logger.debug(f"Executing Bone Tithe for {user.get_display_name()} with timestamp {user.action_timestamp}")
        
        # Reset skill target and selected skill to indicate we're executing it now
        # This matches the pattern used in other successful skills
        user.took_action = True
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'bone_tithe_upgraded'):
            self.upgraded = user.passive_skill.bone_tithe_upgraded

        # Calculate damage based on upgrade status
        if self.upgraded:
            # Upgraded version: Base damage + kill count (retroactive)
            kill_count = 0
            if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'kills'):
                kill_count = user.passive_skill.kills

            # Damage scales with kills when upgraded
            damage = self.base_damage + kill_count
        else:
            # Base version: Flat damage with no kill count bonus
            damage = self.base_damage
        
        # Generate area of effect (3x3 area centered on user)
        effect_area = []
        center_y, center_x = user.y, user.x
        
        # Generate all positions in 3x3 area
        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                # Skip the center position (user's position)
                if dy == 0 and dx == 0:
                    continue
                    
                tile_y, tile_x = center_y + dy, center_x + dx
                
                # Check if position is valid
                if game.is_valid_position(tile_y, tile_x):
                    effect_area.append((tile_y, tile_x))
        
        # Track affected units for effects and animation
        enemies_hit = []
        allies_buffed = []
        hp_gained = 0
        
        # Log the overall effect
        message_log.add_message(
            f"{user.get_display_name()} extracts the Bone Tithe from nearby entities.",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Check for targets in the area
        for tile_y, tile_x in effect_area:
            target = game.get_unit_at(tile_y, tile_x)
            
            if not target or not target.is_alive():
                continue
                
            # Affect enemies with damage
            if target.player != user.player:
                # Record previous HP for death checks
                previous_hp = target.hp
                
                # Apply damage (accounting for defense)
                actual_damage = max(1, damage - target.get_effective_stats()['defense'])
                target.hp = max(0, target.hp - actual_damage)
                
                # Add to list of affected enemies
                enemies_hit.append({
                    'unit': target,
                    'damage': actual_damage,
                    'position': (tile_y, tile_x)
                })
                
                # Log damage
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=target.get_display_name(),
                    damage=actual_damage,
                    ability="Bone Tithe",
                    attacker_player=user.player,
                    target_player=target.player
                )
                
                # Check if unit was killed
                if target.hp <= 0 and previous_hp > 0:
                    # Use centralized death handling
                    game.handle_unit_death(target, user, cause="bone_tithe", ui=ui)
                
                # Gain HP for each enemy hit (doubled when upgraded)
                hp_gain_amount = 2 if self.upgraded else 1
                hp_gained += hp_gain_amount
        
        # Apply HP gain to user based on number of enemies hit
        if hp_gained > 0:
            # Check if user is cursed by Auction Curse (healing prevention)
            if hasattr(user, 'auction_curse_no_heal') and user.auction_curse_no_heal:
                message_log.add_message(
                    f"{user.get_display_name()}'s bone marrow gain is prevented by the curse.",
                    MessageType.WARNING,
                    player=user.player
                )
                hp_gained = 0  # No healing occurred
            else:
                # Increase max HP first, then heal using universal method
                user.max_hp += hp_gained
                actual_heal = user.heal(hp_gained, "bone marrow gain")
                hp_gained = actual_heal  # Update for display purposes
                
                # Show healing number if UI is available
                if ui and hasattr(ui, 'renderer') and hp_gained > 0:
                    healing_text = f"+{hp_gained}"
                    
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
                
                message_log.add_message(
                    f"{user.get_display_name()} compacts bone marrow into himself, gaining {hp_gained} max HP.",
                    MessageType.ABILITY,
                    player=user.player
                )
        
        # No ally buff messaging needed with the new upgrade
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get bone tithe animation from asset manager
            bone_tithe_animation = ui.asset_manager.get_skill_animation_sequence('slough')  # Still using 'slough' key for animation compatibility with existing assets
            if not bone_tithe_animation:
                # ASCII-only animation showing bone shards flying outward
                bone_tithe_animation = ['#', '*', '+', 'X', '*', '.']
            
            # First flash the user to show bone shards being expelled
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [6, 3 if user.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
            
            # Animate bone shards flying outward in all 8 directions
            directions = [
                (-1, 0),   # North
                (-1, 1),   # Northeast
                (0, 1),    # East
                (1, 1),    # Southeast
                (1, 0),    # South
                (1, -1),   # Southwest
                (0, -1),   # West
                (-1, -1)   # Northwest
            ]
            
            # For each direction, create an animation path
            for dy, dx in directions:
                # Start from user position
                y, x = user.y, user.x
                
                # Calculate up to two steps outward
                for step in range(1, 3):
                    next_y = y + dy
                    next_x = x + dx
                    
                    # Skip if position is invalid
                    if not game.is_valid_position(next_y, next_x):
                        break
                        
                    # Animate at this position
                    for frame in bone_tithe_animation:
                        # Determine color based on what's at this position
                        target = game.get_unit_at(next_y, next_x)
                        if target:
                            # Enemy hit (red)
                            if target.player != user.player:
                                color = 1  # Red for damage 
                            # Ally buffed (green if upgraded)
                            elif self.upgraded:
                                color = 2  # Green for buff
                            # Default
                            else:
                                color = 7  # White for neutral
                        else:
                            # No target, use white for bone fragments
                            color = 7
                        
                        # Draw animation frame
                        ui.renderer.draw_tile(next_y, next_x, frame, color)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.03)  # Quick animation
                    
                    # Move to next position for next step
                    y, x = next_y, next_x
            
            # Pause briefly after animation
            sleep_with_animation_speed(0.1)
            
            # Show damage numbers and flash affected enemies
            for enemy_data in enemies_hit:
                enemy = enemy_data['unit']
                damage = enemy_data['damage']
                
                # Show damage number
                if hasattr(ui, 'renderer'):
                    damage_text = f"-{damage}"
                    ui.renderer.draw_damage_text(enemy.y - 1, enemy.x * 2, damage_text, 1, curses.A_BOLD)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
                
                # Flash the enemy to show damage
                tile_ids = [ui.asset_manager.get_unit_tile(enemy.type)] * 3
                color_ids = [1, 7, 1]  # Red, white, red for damage effect
                durations = [0.08] * 3
                ui.renderer.flash_tile(enemy.y, enemy.x, tile_ids, color_ids, durations)
            
            # Show buff effect on allies if upgraded
            if self.upgraded and allies_buffed:
                for ally in allies_buffed:
                    # Flash allies with green to show defense buff
                    tile_ids = [ui.asset_manager.get_unit_tile(ally.type)] * 3
                    color_ids = [2, 7, 2]  # Green, white, green for buff
                    durations = [0.08] * 3
                    ui.renderer.flash_tile(ally.y, ally.x, tile_ids, color_ids, durations)
            
            # Redraw the board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        # Clean up skill state after execution
        user.skill_target = None
        user.selected_skill = None
        
        # Log that execution is complete
        logger.debug(f"Bone Tithe execution complete for {user.get_display_name()}")
        
        return True
