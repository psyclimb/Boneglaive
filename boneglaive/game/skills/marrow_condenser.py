#!/usr/bin/env python3
"""
Skills specific to the MARROW_CONDENSER unit type.
This module contains all passive and active abilities for MARROW_CONDENSER units.
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
    Passive skill for MARROW_CONDENSER.
    When a unit dies inside the MARROW_CONDENSER's Marrow Dike, he gains permanent
    upgrades to his skills.
    """
    
    def __init__(self):
        super().__init__(
            name="Dominion",
            key="D",
            description="When a unit dies inside of the MARROW_CONDENSER'S Marrow Dike, he gains permanent upgrades to his skills."
        )
        self.ossify_upgraded = False
        self.marrow_dike_upgraded = False
        self.slough_upgraded = False
        self.available_upgrades = ["ossify", "marrow_dike", "slough"]
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        # Logic handled in game engine when units die
        pass
    
    def can_upgrade(self) -> bool:
        """Check if any skills are still available for upgrade."""
        return len(self.available_upgrades) > 0
    
    def get_next_upgrade(self) -> str:
        """Get the next skill to upgrade (for testing, always choose Marrow Dike first)."""
        if not self.available_upgrades:
            return None
        
        # For testing purposes, always upgrade Marrow Dike first if available
        if "marrow_dike" in self.available_upgrades:
            upgrade = "marrow_dike"
        else:
            # Fall back to random selection for other skills
            upgrade = random.choice(self.available_upgrades)
            
        self.available_upgrades.remove(upgrade)
        
        if upgrade == "ossify":
            self.ossify_upgraded = True
        elif upgrade == "marrow_dike":
            self.marrow_dike_upgraded = True
        elif upgrade == "slough":
            self.slough_upgraded = True
            
        return upgrade


class OssifySkill(ActiveSkill):
    """
    Active skill for MARROW_CONDENSER.
    Temporarily compresses bone structure to become nearly impenetrable at the cost of mobility.
    When upgraded, the effect becomes permanent and movement is no longer reduced.
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
        self.defense_bonus = 4  # Increased defense bonus to 4
        self.duration = 2  # Duration in turns
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # If upgraded and permanently applied, can't use again
        if self.upgraded and user.defense_bonus >= self.defense_bonus:
            return False
        
        return super().can_use(user, target_pos, game)
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Ossify skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # For self-targeting skills, set target to current position
        user.skill_target = (user.y, user.x)
        user.selected_skill = self
        
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
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'ossify_upgraded'):
            self.upgraded = user.passive_skill.ossify_upgraded
        
        # Apply defense bonus
        user.defense_bonus += self.defense_bonus
        
        # Apply movement penalty if not upgraded
        if not self.upgraded:
            user.move_range_bonus = -1
            user.ossify_duration = self.duration  # Track duration
            
            message_log.add_message(
                f"{user.get_display_name()}'s bones harden, increasing defense by {self.defense_bonus} but reducing mobility!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            # If upgraded, the effect is permanent with no drawbacks
            message_log.add_message(
                f"{user.get_display_name()}'s bones permanently harden, increasing defense by {self.defense_bonus}!",
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
                time.sleep(0.3)
                
                # Redraw board to reset colors
                if hasattr(ui, 'draw_board'):
                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class MarrowDikeSkill(ActiveSkill):
    """
    Active skill for MARROW_CONDENSER.
    Creates a wall of condensed bone marrow that blocks movement and attacks.
    When upgraded, the Marrow Dike is filled with blood plasma that heals allies.
    """
    
    def __init__(self):
        super().__init__(
            name="Marrow Dike",
            key="M",
            description="Creates a wall of condensed bone marrow that blocks movement and attacks for 4 turns. Cooldown is shared with all allied MARROW_CONDENSER units.",
            target_type=TargetType.SELF,
            cooldown=4,
            range_=0,
            area=2  # 5x5 area (center + 2 in each direction)
        )
        self.upgraded = False
        self.duration = 4  # Increased duration to 4 turns
        self.healing_amount = 3  # Increased healing amount per turn when upgraded
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
            
        # Check if any allied MARROW_CONDENSER has this skill on cooldown
        from boneglaive.utils.message_log import message_log, MessageType
        
        for unit in game.units:
            # Only check allied MARROW_CONDENSER units that are alive and not this user
            if unit.is_alive() and unit != user and unit.player == user.player and unit.type == user.type:
                # Check if this unit has Marrow Dike skill on cooldown
                for skill in unit.active_skills:
                    if skill.name == "Marrow Dike" and skill.current_cooldown > 0:
                        # An allied MARROW_CONDENSER has Marrow Dike on cooldown
                        message_log.add_message(
                            f"Cannot use Marrow Dike - an allied {unit.get_display_name()} has this skill on cooldown!",
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
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to create a Marrow Dike!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown on this unit
        self.current_cooldown = self.cooldown
        
        # Also set cooldown on all allied MARROW_CONDENSER units
        for unit in game.units:
            # Only affect allied MARROW_CONDENSER units that are alive and not this user
            if unit.is_alive() and unit != user and unit.player == user.player and unit.type == user.type:
                # Find their Marrow Dike skill and set the cooldown
                for skill in unit.active_skills:
                    if skill.name == "Marrow Dike":
                        skill.current_cooldown = self.cooldown
                        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Marrow Dike skill during turn resolution."""
        from boneglaive.game.map import TerrainType
        import time
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'marrow_dike_upgraded'):
            self.upgraded = user.passive_skill.marrow_dike_upgraded
        
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
                        player=user.player,
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
                'original_terrain': original_terrain
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
                f"{user.get_display_name()} creates a Marrow Dike filled with healing blood plasma!",
                MessageType.ABILITY,
                player=user.player
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
                    time.sleep(0.2)
                    
                    # Show unit at new position
                    unit_symbol = ui.asset_manager.get_unit_tile(unit.type)
                    ui.renderer.draw_tile(
                        new_y, new_x,
                        unit_symbol,
                        3 if unit.player == 1 else 4  # Player color
                    )
                    ui.renderer.refresh()
                    time.sleep(0.2)
            
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
                    
                    # If upgraded, add a plasma effect
                    if self.upgraded:
                        plasma_animation = ['~', '≈', '≋', '≈', '~']
                        # Draw upgraded walls with yellow blood plasma flowing through them
                        ui.renderer.animate_attack_sequence(
                            tile_y, tile_x,
                            plasma_animation,
                            6,  # Yellowish color for plasma
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
                    time.sleep(0.1)
                    
                    # Redraw to show progress
                    if hasattr(ui, 'draw_board'):
                        ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                        
            # Draw final state
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class SloughSkill(ActiveSkill):
    """
    Active skill for MARROW_CONDENSER.
    Sloughs off positive stat bonuses to all allies in a 5x5 area.
    If no positive bonuses available, heals allies for a small amount.
    
    When upgraded:
    - Maintains positive bonuses when sharing
    - Transfers negative effects to enemies
    - Deals damage if no negative effects to transfer
    """
    
    def __init__(self):
        super().__init__(
            name="Slough",
            key="S",
            description="Sloughs off positive stat bonuses to allies in a 3x3 area. If no bonuses are available, heals allies instead.",
            target_type=TargetType.SELF,  # Changed to self-targeted (area effect)
            cooldown=3,  # Added cooldown
            range_=0,
            area=1  # 3x3 area (center + 1 in each direction)
        )
        self.upgraded = False
        self.heal_amount = 2  # Small healing fallback amount
        self.damage_amount = 3  # Damage for upgraded version with no debuffs
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation (cooldown, etc.)
        if not super().can_use(user, target_pos, game):
            return False
        
        # Skill can always be used - either transferring effects or healing/damaging
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Slough skill for execution."""
        # For self-targeting skills, set target to current position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to slough off bone matter!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Slough skill during turn resolution."""
        import time
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'slough_upgraded'):
            self.upgraded = user.passive_skill.slough_upgraded
        
        # Check if user has any positive stat bonuses to share
        positive_bonuses = {
            'attack': user.attack_bonus if user.attack_bonus > 0 else 0,
            'defense': user.defense_bonus if user.defense_bonus > 0 else 0,
            'move': user.move_range_bonus if user.move_range_bonus > 0 else 0,
            'range': user.attack_range_bonus if user.attack_range_bonus > 0 else 0
        }
        
        has_positive_bonuses = any(value > 0 for value in positive_bonuses.values())
        
        # Check if user has any negative stat changes (for upgraded version)
        negative_effects = {
            'attack': abs(user.attack_bonus) if user.attack_bonus < 0 else 0,
            'defense': abs(user.defense_bonus) if user.defense_bonus < 0 else 0,
            'move': abs(user.move_range_bonus) if user.move_range_bonus < 0 else 0,
            'range': abs(user.attack_range_bonus) if user.attack_range_bonus < 0 else 0
        }
        
        has_negative_effects = any(value > 0 for value in negative_effects.values())
        
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
        
        # Process effects
        allies_affected = []
        enemies_affected = []
        
        # Check for targets in the area
        for tile_y, tile_x in effect_area:
            target = game.get_unit_at(tile_y, tile_x)
            
            if not target or not target.is_alive():
                continue
                
            # Group by ally or enemy
            if target.player == user.player:
                allies_affected.append(target)
            elif self.upgraded:  # Only track enemies if upgraded
                enemies_affected.append(target)
        
        # Apply effects
        allies_buffed = 0
        allies_healed = 0
        enemies_debuffed = 0
        enemies_damaged = 0
        
        # Process allies first
        if allies_affected:
            if has_positive_bonuses:
                # Apply positive bonuses to all allies
                for ally in allies_affected:
                    # Apply each bonus
                    ally.attack_bonus += positive_bonuses['attack']
                    ally.defense_bonus += positive_bonuses['defense']
                    ally.move_range_bonus += positive_bonuses['move']
                    ally.attack_range_bonus += positive_bonuses['range']
                    allies_buffed += 1
                
                # If not upgraded, remove bonuses from user
                if not self.upgraded:
                    # Remove positive bonuses from user
                    if positive_bonuses['attack'] > 0:
                        user.attack_bonus = 0
                    if positive_bonuses['defense'] > 0:
                        user.defense_bonus = 0
                    if positive_bonuses['move'] > 0:
                        user.move_range_bonus = 0
                    if positive_bonuses['range'] > 0:
                        user.attack_range_bonus = 0
            
            else:
                # No bonuses to share, apply healing instead
                for ally in allies_affected:
                    # Only heal if not at full health
                    if ally.hp < ally.max_hp:
                        previous_hp = ally.hp
                        ally.hp = min(ally.max_hp, ally.hp + self.heal_amount)
                        if ally.hp > previous_hp:
                            allies_healed += 1
        
        # Process enemies if upgraded
        if self.upgraded and enemies_affected:
            if has_negative_effects:
                # Apply negative effects to enemies
                for enemy in enemies_affected:
                    enemy.attack_bonus -= negative_effects['attack']
                    enemy.defense_bonus -= negative_effects['defense']
                    enemy.move_range_bonus -= negative_effects['move']
                    enemy.attack_range_bonus -= negative_effects['range']
                    enemies_debuffed += 1
                
                # Clear negative effects from user
                if negative_effects['attack'] > 0:
                    user.attack_bonus = max(0, user.attack_bonus)
                if negative_effects['defense'] > 0:
                    user.defense_bonus = max(0, user.defense_bonus)
                if negative_effects['move'] > 0:
                    user.move_range_bonus = max(0, user.move_range_bonus)
                if negative_effects['range'] > 0:
                    user.attack_range_bonus = max(0, user.attack_range_bonus)
            
            else:
                # No negative effects to share, apply damage instead
                for enemy in enemies_affected:
                    # Apply damage
                    damage_dealt = game.calculate_direct_damage(self.damage_amount, user, enemy)
                    game.damage_unit(enemy, damage_dealt, user, "ability")
                    enemies_damaged += 1
        
        # Log what happened
        if self.upgraded:
            message_log.add_message(
                f"{user.get_display_name()} releases bone matter in all directions!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} sloughs off bone matter!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Additional messages based on effects
        if allies_buffed > 0:
            message_log.add_message(
                f"Beneficial bone growth reinforces {allies_buffed} allies!",
                MessageType.ABILITY,
                player=user.player
            )
        
        if allies_healed > 0:
            message_log.add_message(
                f"Marrow nutrients heal {allies_healed} allies for {self.heal_amount} HP!",
                MessageType.ABILITY,
                player=user.player
            )
        
        if enemies_debuffed > 0:
            message_log.add_message(
                f"Calcified fragments weigh down {enemies_debuffed} enemies!",
                MessageType.ABILITY,
                player=user.player
            )
        
        if enemies_damaged > 0:
            message_log.add_message(
                f"Bone shards tear into {enemies_damaged} enemies for {self.damage_amount} damage!",
                MessageType.ABILITY,
                player=user.player
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get slough animation from asset manager
            slough_animation = ui.asset_manager.get_skill_animation_sequence('slough')
            if not slough_animation:
                # TTY-friendly animation showing bone chunks sloughing off
                slough_animation = ['#', '&', '$', '@', '*', '.']
            
            # First flash the user to show bonuses being gathered/sloughed
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [6, 3 if user.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
            
            # Create animation paths from user to each affected unit
            # Track which positions we've already animated to avoid duplication
            animated_positions = set()
            
            # Define direction vectors for the 8 cardinal/ordinal directions
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
            
            # Show bone/marrow matter in a 3x3 area
            # Find positions around user (3x3 area)
            positions_in_area = []
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    # Skip the center (user's position)
                    if dy == 0 and dx == 0:
                        continue
                    
                    tile_y, tile_x = user.y + dy, user.x + dx
                    if game.is_valid_position(tile_y, tile_x):
                        positions_in_area.append((tile_y, tile_x))
            
            # Animate all positions in the area simultaneously
            for pos_y, pos_x in positions_in_area:
                # Check if any unit is at this position
                target = game.get_unit_at(pos_y, pos_x)
                
                # Use bone and marrow colors (white and red)
                # For empty tiles, alternate white and red to represent bone and marrow
                if not target:
                    # Use white (7) for bone or red (20) for marrow depending on position
                    # Use a pattern that creates an alternating effect
                    is_even_position = (pos_y + pos_x) % 2 == 0
                    color_id = 7 if is_even_position else 20  # White bone or red marrow
                else:
                    # For tiles with units, use different colors based on ally/enemy
                    if target.player == user.player:
                        color_id = 7  # White/bone for allies 
                    else:
                        color_id = 20  # Red/marrow for enemies
                
                # Animate the bone matter spreading
                for frame in slough_animation:
                    ui.renderer.draw_tile(pos_y, pos_x, frame, color_id)
                    ui.renderer.refresh()
                    time.sleep(0.03)  # Quick animation
            
            # Pause briefly after animation
            time.sleep(0.1)
            
            # Apply final effects to targets (flashing allies/enemies)
            
            # Flash allies who were buffed or healed with bone reinforcement
            for ally in allies_affected:
                if has_positive_bonuses or (not has_positive_bonuses and ally.hp < ally.max_hp):
                    # Flash allies with white (bone) color to show reinforcement
                    tile_ids = [ui.asset_manager.get_unit_tile(ally.type)] * 4
                    # Alternating white and normal colors for bone reinforcement effect
                    color_ids = [7, 3 if ally.player == 1 else 4, 7, 3 if ally.player == 1 else 4]
                    durations = [0.08] * 4
                    
                    ui.renderer.flash_tile(ally.y, ally.x, tile_ids, color_ids, durations)
            
            # Flash enemies who were debuffed or damaged with red marrow (if upgraded)
            if self.upgraded:
                for enemy in enemies_affected:
                    # Flash enemies with red for marrow corruption
                    tile_ids = [ui.asset_manager.get_unit_tile(enemy.type)] * 4
                    # Intensifying red effect that shows marrow fragments
                    color_ids = [20, 5, 20, 5]  # Red and darker red alternating
                    durations = [0.08] * 4
                    
                    ui.renderer.flash_tile(enemy.y, enemy.x, tile_ids, color_ids, durations)
            
            # Redraw the board after all animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True