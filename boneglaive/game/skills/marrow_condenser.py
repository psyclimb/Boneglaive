#!/usr/bin/env python3
"""
Skills specific to the MARROW_CONDENSER unit type.
This module contains all passive and active abilities for MARROW_CONDENSER units.
"""

from typing import Optional, TYPE_CHECKING
import random

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
        """Get the next skill to upgrade (randomly selected)."""
        if not self.available_upgrades:
            return None
        
        # Randomly select a skill to upgrade
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
        self.defense_bonus = 2
        self.duration = 1  # Duration in turns
    
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
            description="Creates a wall of condensed bone marrow that blocks movement and attacks.",
            target_type=TargetType.SELF,
            cooldown=4,
            range_=0,
            area=2  # 5x5 area (center + 2 in each direction)
        )
        self.upgraded = False
        self.duration = 3  # Duration in turns
        self.healing_amount = 2  # Amount healed per turn when upgraded
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
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
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Marrow Dike skill during turn resolution."""
        from boneglaive.game.map import TerrainType
        import time
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'marrow_dike_upgraded'):
            self.upgraded = user.passive_skill.marrow_dike_upgraded
        
        # Generate the dike area (5x5 centered on user)
        dike_tiles = []
        center_y, center_x = user.y, user.x
        
        for dy in range(-2, 3):  # -2, -1, 0, 1, 2
            for dx in range(-2, 3):  # -2, -1, 0, 1, 2
                # Skip the center tile (user's position)
                if dy == 0 and dx == 0:
                    continue
                    
                tile_y, tile_x = center_y + dy, center_x + dx
                
                # Check if position is valid
                if game.is_valid_position(tile_y, tile_x):
                    dike_tiles.append((tile_y, tile_x))
        
        # Add the marrow dike to the game state
        if not hasattr(game, 'marrow_dike_tiles'):
            game.marrow_dike_tiles = {}
            
        # Associate these tiles with this user's dike, with expiration timer
        for tile in dike_tiles:
            game.marrow_dike_tiles[tile] = {
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
            # Create wall effect animation
            wall_animation = ['░', '▒', '▓', '█']
            
            # Draw animation for each tile in sequence
            for i, (tile_y, tile_x) in enumerate(dike_tiles):
                # Check if there's a unit here
                unit_at_tile = game.get_unit_at(tile_y, tile_x)
                
                if not unit_at_tile:
                    # Animate the wall creation (no unit at this position)
                    ui.renderer.animate_attack_sequence(
                        tile_y, tile_x,
                        wall_animation,
                        3 if user.player == 1 else 4,  # Player color
                        0.05  # Quick animation
                    )
                    
                    # If upgraded, add a plasma effect
                    if self.upgraded:
                        plasma_animation = ['~', '≈', '≋', '≈', '~']
                        ui.renderer.animate_attack_sequence(
                            tile_y, tile_x,
                            plasma_animation,
                            6,  # Yellowish color for plasma
                            0.05  # Quick animation
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
    Transfers any stat bonuses to an allied unit.
    When upgraded, transfers the stat bonuses without losing them.
    """
    
    def __init__(self):
        super().__init__(
            name="Slough",
            key="S",
            description="Transfers any stat bonuses to an allied unit.",
            target_type=TargetType.ALLY,
            cooldown=0,
            range_=2
        )
        self.upgraded = False
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        
        # Need game and target position
        if not game or not target_pos:
            return False
            
        # Check if target is a valid ally
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player != user.player or target is user:
            return False
            
        # Check if user has any stat bonuses to transfer
        has_bonuses = (
            user.attack_bonus > 0 or 
            user.defense_bonus > 0 or 
            user.move_range_bonus > 0 or
            user.attack_range_bonus > 0
        )
        
        if not has_bonuses:
            return False
            
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue the Slough skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Get target unit for message
        target = game.get_unit_at(target_pos[0], target_pos[1])
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to transfer bonuses to {target.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Slough skill during turn resolution."""
        import time
        
        # Determine if this is upgraded version
        if hasattr(user, 'passive_skill') and hasattr(user.passive_skill, 'slough_upgraded'):
            self.upgraded = user.passive_skill.slough_upgraded
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player != user.player:
            # Target is no longer valid
            message_log.add_message(
                "Slough failed: target no longer valid.",
                MessageType.ABILITY,
                player=user.player
            )
            return False
            
        # Track bonuses being transferred
        bonuses = {
            'attack': user.attack_bonus,
            'defense': user.defense_bonus,
            'move': user.move_range_bonus,
            'range': user.attack_range_bonus
        }
        
        # Apply bonuses to target
        target.attack_bonus += bonuses['attack']
        target.defense_bonus += bonuses['defense']
        target.move_range_bonus += bonuses['move']
        target.attack_range_bonus += bonuses['range']
        
        # Remove bonuses from user if not upgraded
        if not self.upgraded:
            user.attack_bonus = 0
            user.defense_bonus = 0
            user.move_range_bonus = 0
            user.attack_range_bonus = 0
            
            message_log.add_message(
                f"{user.get_display_name()} transfers their stat bonuses to {target.get_display_name()}!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} shares their stat bonuses with {target.get_display_name()} without losing them!",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get transfer animation
            transfer_animation = ui.asset_manager.get_skill_animation_sequence('slough')
            if not transfer_animation:
                transfer_animation = ['↑', '↗', '→', '↘', '↓']  # Fallback
                
            # Get the path from user to target
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(user.y, user.x), Position(target.y, target.x))
            
            # First flash the user to show bonuses being gathered
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [6, 3 if user.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
            
            # Animate along the path
            for pos in path[1:]:  # Skip the first position (user)
                ui.renderer.draw_tile(pos.y, pos.x, transfer_animation[min(path.index(pos), len(transfer_animation)-1)], 6)
                ui.renderer.refresh()
                time.sleep(0.05)
                
            # Wait a moment before showing effect on target
            time.sleep(0.1)
            
            # Flash the target to show bonuses being received
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [6, 3 if target.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
            
            # If upgraded, also flash the user again to show they kept bonuses
            if self.upgraded:
                time.sleep(0.1)
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [6, 3 if user.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
            
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True