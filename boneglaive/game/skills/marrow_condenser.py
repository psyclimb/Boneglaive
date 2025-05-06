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
            description="When a unit kills an enemy, gains +1 to attack, defense, and movement. Any unit dying in Marrow Dike upgrades skills."
        )
        self.ossify_upgraded = False
        self.marrow_dike_upgraded = False
        self.bone_tithe_upgraded = False
        self.available_upgrades = ["marrow_dike", "ossify", "bone_tithe"]
        self.kills = 0  # Track the number of kills for flat stat bonuses
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
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
            f"{user.get_display_name()} prepares to ossify their bones!",
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
            f"{user.get_display_name()}'s bones harden!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            ossify_animation = ui.asset_manager.get_skill_animation_sequence('ossify')
            if not ossify_animation:
                ossify_animation = ['|', '#', '█', '▓', '▒']  # Fallback animation
                
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
            description="Creates a wall of condensed bone marrow that blocks movement and attacks for 4 turns.",
            target_type=TargetType.SELF,
            cooldown=2,  # 2-turn cooldown
            range_=0,
            area=2  # 5x5 area (center + 2 in each direction)
        )
        self.upgraded = False
        self.duration = 4  # Duration of 4 turns
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
            
        # Check if player already has an active Marrow Dike (keep this check)
        from boneglaive.utils.message_log import message_log, MessageType
        
        # 1. Check if this player already has an active Marrow Dike (wall tiles)
        if hasattr(game, 'marrow_dike_tiles') and len(game.marrow_dike_tiles) > 0:
            for tile_info in game.marrow_dike_tiles.values():
                if tile_info.get('owner') and tile_info['owner'].player == user.player:
                    message_log.add_message(
                        f"Cannot use Marrow Dike - you already have an active dike!",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False
        
        # 2. Also check interior tiles
        if hasattr(game, 'marrow_dike_interior') and len(game.marrow_dike_interior) > 0:
            for tile_info in game.marrow_dike_interior.values():
                if tile_info.get('owner') and tile_info['owner'].player == user.player:
                    message_log.add_message(
                        f"Cannot use Marrow Dike - you already have an active dike!",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False
        
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Marrow Dike skill for execution."""
        # For self-targeting skills, set target to current position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order exactly like other units
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
            from boneglaive.utils.debug import logger
            logger.debug(f"Setting action timestamp for {user.get_display_name()}'s Marrow Dike skill to {user.action_timestamp}")
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to create a Marrow Dike!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown on this unit
        self.current_cooldown = self.cooldown
                        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Marrow Dike skill during turn resolution."""
        from boneglaive.game.map import TerrainType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        
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
        
        # First, identify and move units on the perimeter
        units_to_move = []
        unit_movements = []  # Store original and new positions for animation
        
        for tile_y, tile_x in dike_tiles:
            unit_at_tile = game.get_unit_at(tile_y, tile_x)
            if unit_at_tile:
                # Check if the unit is immune to effects (GRAYMAN with Stasiality)
                if unit_at_tile.is_immune_to_effects():
                    # Log message about immunity
                    message_log.add_message(
                        f"{unit_at_tile.get_display_name()} is immune to Marrow Dike's pull due to Stasiality!",
                        MessageType.ABILITY,
                        player=unit_at_tile.player,  # Use target unit's player for correct color coding
                        target_name=unit_at_tile.get_display_name()
                    )
                    # Skip this unit - it won't be moved and the wall won't be placed here
                    continue
                
                # Add to list of units to be moved inside
                units_to_move.append(unit_at_tile)
                
                # Calculate direction toward center from unit
                dy = 1 if tile_y < center_y else (-1 if tile_y > center_y else 0)
                dx = 1 if tile_x < center_x else (-1 if tile_x > center_x else 0)
                
                # Calculate new position (just one step inward)
                new_y = tile_y + dy
                new_x = tile_x + dx
                
                # Check if the target position is passable terrain
                if not game.map.is_passable(new_y, new_x):
                    # Cannot pull onto impassable terrain - log warning message
                    message_log.add_message(
                        f"{unit_at_tile.get_display_name()} cannot be pulled onto impassable terrain!",
                        MessageType.WARNING,
                        player=user.player,
                        target_name=unit_at_tile.get_display_name()
                    )
                    # Skip this unit - it won't be moved
                    continue
                
                # Store the movement info for animation
                unit_movements.append({
                    'unit': unit_at_tile,
                    'from': (tile_y, tile_x),
                    'to': (new_y, new_x),
                    'dy': dy,
                    'dx': dx
                })
        
        # Move units to inside the dike (toward center)
        for movement in unit_movements:
            unit = movement['unit']
            new_y, new_x = movement['to']
            
            # Make sure new position is not already occupied
            if not game.get_unit_at(new_y, new_x):
                # Log the movement
                message_log.add_message(
                    f"{unit.get_display_name()} is pulled inside the Marrow Dike!",
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
                
            # Store original terrain to restore later
            original_terrain = game.map.get_terrain_at(tile_y, tile_x)
            game.previous_terrain[tile] = original_terrain
            
            # Set the tile to MARROW_WALL terrain (special terrain for dike)
            game.map.set_terrain_at(tile_y, tile_x, TerrainType.MARROW_WALL)
            
            # Associate this tile with the dike
            game.marrow_dike_tiles[tile] = {
                'owner': user,
                'duration': self.duration,
                'upgraded': self.upgraded,
                'original_terrain': original_terrain,
                'hp': 3 if self.upgraded else 2  # 3 HP when upgraded, 2 HP otherwise
            }
        
        # Track interior tiles for Dominion passive detection
        for tile_y, tile_x in dike_interior:
            tile = (tile_y, tile_x)
            
            # Associate this interior tile with the dike (no terrain change needed)
            game.marrow_dike_interior[tile] = {
                'owner': user,
                'duration': self.duration,
                'upgraded': self.upgraded
            }
        
        # Log the skill activation
        if self.upgraded:
            message_log.add_message(
                f"{user.get_display_name()} shores up a Marrow Dike and fills it with plasma!",
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
                            f"{unit_at_pos.get_display_name()} ignores the Marrow Dike's effect due to Stasiality!",
                            MessageType.ABILITY,
                            player=unit_at_pos.player,
                            target_name=unit_at_pos.get_display_name()
                        )
                        unit_at_pos.marrow_dike_immunity_message_shown = True
                    # For non-immune units, apply the movement penalty immediately
                    elif not hasattr(unit_at_pos, 'prison_move_penalty') or not unit_at_pos.prison_move_penalty:
                        unit_at_pos.move_range_bonus -= 1
                        unit_at_pos.prison_move_penalty = True
                        
                        # Shorter message for each enemy unit trapped inside
                        message_log.add_message(
                            f"{unit_at_pos.get_display_name()} slogs through the Marrow Dike!",
                            MessageType.ABILITY,
                            player=user.player,
                            attacker_name=user.get_display_name(),
                            target_name=unit_at_pos.get_display_name()
                        )
        else:
            message_log.add_message(
                f"{user.get_display_name()} creates a Marrow Dike!",
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
                    pull_animation = ['→', '↓', '←', '↑']  # Direction indicators
                    
                    # Choose the right direction indicator based on direction
                    direction_idx = 0
                    if dx > 0:
                        direction_idx = 0  # →
                    elif dy > 0:
                        direction_idx = 1  # ↓
                    elif dx < 0:
                        direction_idx = 2  # ←
                    elif dy < 0:
                        direction_idx = 3  # ↑
                        
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
                    # Animate the wall creation with RED color (5) for Marrow regardless of player
                    ui.renderer.animate_attack_sequence(
                        tile_y, tile_x,
                        wall_animation,
                        5,  # Red color for Marrow walls
                        0.05  # Quick animation
                    )
                    
                    # If upgraded, add a reinforced wall effect
                    if self.upgraded:
                        prison_animation = ['#', '≡', '■', '≡', '#']
                        # Draw upgraded walls with reinforced elements
                        ui.renderer.animate_attack_sequence(
                            tile_y, tile_x,
                            prison_animation,
                            7,  # White color for bone structures
                            0.05  # Quick animation
                        )
                    
                    # Draw final wall symbol in red to make it stand out
                    ui.renderer.draw_tile(
                        tile_y, tile_x,
                        '#',  # Hash symbol for walls
                        20  # Use specific color defined for marrow walls (red)
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


class BoneTitheSkill(ActiveSkill):
    """
    Active skill for MARROW CONDENSER.
    Extracts a tithe of bone marrow from nearby enemies, damaging them while
    strengthening the MARROW CONDENSER with their essence.
    
    When upgraded:
    - Increases HP gain per enemy hit from +1 to +2
    - Enhanced ability to absorb and condense enemy marrow
    """
    
    def __init__(self):
        super().__init__(
            name="Bone Tithe",
            key="B",
            description="Extracts marrow from adjacent enemies for 1 (+1 per kill) damage and gains +1 HP for each enemy hit.",
            target_type=TargetType.SELF,  # Self-targeted area effect
            cooldown=2,
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
                    f"{user.get_display_name()} needs at least {min_health_needed+1} HP to use Bone Tithe!",
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
            f"{user.get_display_name()} prepares to collect the Bone Tithe!",
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
        
        # Get number of kills for damage scaling
        kill_count = 0
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'kills'):
            kill_count = user.passive_skill.kills
        
        # Calculate damage based on kill count
        damage = self.base_damage + kill_count
        
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
            f"{user.get_display_name()} extracts the Bone Tithe from nearby entities!",
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
            user.max_hp += hp_gained
            user.hp += hp_gained
            
            message_log.add_message(
                f"{user.get_display_name()} compacts bone marrow into himself, gaining {hp_gained} max HP!",
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
                    ui.renderer.draw_text(enemy.y - 1, enemy.x * 2, damage_text, 1, curses.A_BOLD)
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
