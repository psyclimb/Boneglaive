#!/usr/bin/env python3
"""
Skills specific to the DELPHIC_APPRAISER unit type.
This module contains all passive and active abilities for DELPHIC_APPRAISER units.
"""

import curses
import time
import random
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.animation_helpers import sleep_with_animation_speed
from boneglaive.utils.constants import UnitType
from boneglaive.game.map import TerrainType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class ValuationOracle(PassiveSkill):
    """
    Passive skill for DELPHIC_APPRAISER.
    Perceives the 'cosmic value' of furniture terrain and gains bonuses when adjacent.
    """
    
    def __init__(self):
        super().__init__(
            name="Valuation Oracle",
            key="V",
            description="Perceives the 'cosmic value' (1-9) of furniture terrain. When adjacent to appraised furniture, gains +1 to defense and attack range."
        )
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """
        Apply the Valuation Oracle passive effect.
        Checks if the user is adjacent to any furniture and applies bonuses if so.
        """
        if not game:
            return

        # Check if adjacent to any furniture
        adjacent_to_furniture = False
        furniture_positions = []

        # Check all eight adjacent positions
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue  # Skip the unit's own position

                y, x = user.y + dy, user.x + dx

                # Skip if out of bounds
                if not game.is_valid_position(y, x):
                    continue

                # Check if the tile is furniture
                if game.map.is_furniture(y, x):
                    adjacent_to_furniture = True
                    furniture_positions.append((y, x))

                    # Get cosmic value with the appraiser's player
                    cosmic_value = game.map.get_cosmic_value(y, x, player=user.player, game=game)
                    # Value will be generated if it doesn't exist yet

        # Apply bonuses if adjacent to furniture
        if adjacent_to_furniture:
            # If this is the first time applying the bonus this turn, log a message
            if not hasattr(user, 'valuation_bonus_applied') or not user.valuation_bonus_applied:
                message_log.add_message(
                    f"{user.get_display_name()}'s Valuation Oracle senses the cosmic value of nearby furniture!",
                    MessageType.ABILITY,
                    player=user.player
                )
                user.valuation_bonus_applied = True

            # Apply bonuses to defense and attack range using *_bonus attributes
            user.defense_bonus = 1
            user.attack_range_bonus = 1
        else:
            # Reset the bonus flag if no longer adjacent
            if hasattr(user, 'valuation_bonus_applied') and user.valuation_bonus_applied:
                user.valuation_bonus_applied = False
                # Remove bonuses
                user.defense_bonus = 0
                user.attack_range_bonus = 0


class MarketFuturesSkill(ActiveSkill):
    """
    Active skill for DELPHIC_APPRAISER.
    Infuses furniture with temporal investment energy for teleportation.
    """
    
    def __init__(self):
        super().__init__(
            name="Market Futures",
            key="M",
            description="Infuses a furniture piece with temporal investment energy. Creates a teleportation anchor that allies can activate when near the furniture.",
            target_type=TargetType.AREA,
            cooldown=3,  # Cooldown of 3 turns as specified
            range_=4
        )
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Market Futures can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check if the target position is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Target must be a furniture piece
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        if terrain not in [TerrainType.FURNITURE, TerrainType.COAT_RACK, 
                         TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
            return False
            
        # Check if target is within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Market Futures skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to infuse furniture with Market Futures!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Market Futures skill on a furniture piece."""

        # Get the cosmic value (will be generated if it doesn't exist)
        cosmic_value = game.map.get_cosmic_value(target_pos[0], target_pos[1], player=user.player, game=game)
        if cosmic_value is None:
            cosmic_value = random.randint(1, 9)  # Fallback
        
        # Create teleportation anchor
        if not hasattr(game, 'teleport_anchors'):
            game.teleport_anchors = {}
            
        game.teleport_anchors[target_pos] = {
            'creator': user,
            'cosmic_value': cosmic_value,
            'active': True
        }
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} infuses furniture with Market Futures! Cosmic value: {cosmic_value}",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get Market Futures animation - elaborate temporal investment energy
            market_animation = ui.asset_manager.get_skill_animation_sequence('market_futures')
            if not market_animation:
                market_animation = ['A', '¤', 'T', '¤', '$', '¤', '£', '¤', '€', '¤', '¥', '¤', 'Φ', '¤', 'Ψ', '¤', 'Ω', '¤']
                
            # Show animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                market_animation,
                6,  # Cyan/blue color
                0.15  # Duration
            )
            
        return True
        
    def activate_teleport(self, ally: 'Unit', anchor_pos: tuple, destination: tuple, game: 'Game', ui=None) -> bool:
        """Activate the teleportation anchor for an ally."""
        # Verify the anchor exists and is active
        if not hasattr(game, 'teleport_anchors') or anchor_pos not in game.teleport_anchors:
            return False
            
        anchor = game.teleport_anchors[anchor_pos]
        if not anchor['active']:
            return False
            
        # Check if the destination is valid and empty
        if not game.is_valid_position(destination[0], destination[1]):
            return False
            
        if not game.map.is_passable(destination[0], destination[1]):
            return False
            
        if game.get_unit_at(destination[0], destination[1]) is not None:
            return False
            
        # Get cosmic value and check destination range
        cosmic_value = anchor['cosmic_value']
        distance = game.chess_distance(anchor_pos[0], anchor_pos[1], destination[0], destination[1])
        if distance > cosmic_value:
            return False
            
        # Execute teleport
        old_pos = (ally.y, ally.x)
        ally.y, ally.x = destination
        
        # Log the teleportation
        message_log.add_message(
            f"{ally.get_display_name()} activates Market Futures teleport!",
            MessageType.ABILITY,
            player=ally.player
        )
        
        # Apply stat bonuses for high cosmic values (7-9)
        if cosmic_value >= 7:
            message_log.add_message(
                f"High-value teleport grants {ally.get_display_name()} +1 to all stats for 1 turn!",
                MessageType.ABILITY,
                player=ally.player
            )
            
            # Apply temporary stat bonuses
            ally.hp_bonus += 1
            ally.attack_bonus += 1
            ally.defense_bonus += 1
            ally.move_range_bonus += 1
            ally.attack_range_bonus += 1

            # Set a flag to track that these bonuses need to be removed
            ally.market_futures_bonus_applied = True

            # Set duration of the bonus (we'll handle this in the game update loop)
            ally.market_futures_duration = 1
            
        # Play teleport animation
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get teleport animation - ally transforms into golden market arrows
            teleport_animation = ui.asset_manager.get_skill_animation_sequence('market_teleport')
            if not teleport_animation:
                teleport_animation = ['$', '¤', '↗', '¤', '→', '¤', '↘', '¤', '↓', '¤', '*', '¤', 'A']
                
            # Show animation from old position to new position
            ui.renderer.animate_path(
                old_pos[0], old_pos[1], 
                destination[0], destination[1],
                teleport_animation,
                3,  # Yellow/gold color
                0.1  # Duration
            )
            
        # Deactivate the anchor after use
        game.teleport_anchors[anchor_pos]['active'] = False
        
        return True


class AuctionCurseSkill(ActiveSkill):
    """
    Active skill for DELPHIC_APPRAISER.
    Subjects an enemy to a cosmic auction that reduces their stats.
    """
    
    def __init__(self):
        super().__init__(
            name="Auction Curse",
            key="A",
            description="Subjects an enemy to a cosmic auction, reducing their stats based on nearby furniture values. Generates bid tokens to buff allies.",
            target_type=TargetType.ENEMY,
            cooldown=2,  # Cooldown of 2 turns as specified
            range_=3
        )
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Auction Curse can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check if the target position is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Target must be an enemy unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit or target_unit.player == user.player:
            return False
            
        # Check if target is within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Auction Curse skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to cast Auction Curse!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Auction Curse skill on an enemy."""
        # Get the target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False
            
        # Find nearby furniture and their cosmic values
        nearby_furniture = []
        for y in range(max(0, target_pos[0] - 2), min(game.map.height, target_pos[0] + 3)):
            for x in range(max(0, target_pos[1] - 2), min(game.map.width, target_pos[1] + 3)):
                terrain = game.map.get_terrain_at(y, x)
                if terrain in [TerrainType.FURNITURE, TerrainType.COAT_RACK, 
                             TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
                    nearby_furniture.append((y, x))
                    
                    # Get cosmic value (will be generated if it doesn't exist yet)
                    game.map.get_cosmic_value(y, x, player=user.player, game=game)
                        
        # Determine highest cosmic value of nearby furniture
        highest_value = 0
        if nearby_furniture:
            # Get cosmic values for all nearby furniture
            cosmic_values = []
            for pos in nearby_furniture:
                value = game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)
                if value is not None:
                    cosmic_values.append(value)

            if cosmic_values:
                highest_value = max(cosmic_values)
            
        # Determine stat reductions based on highest value
        attack_reduction = 0
        range_reduction = 0
        move_reduction = 0
        
        bid_tokens = 0
        
        if highest_value >= 1:  # Low values (1-3)
            attack_reduction = 1
            bid_tokens += 1
            
        if highest_value >= 4:  # Medium values (4-6)
            range_reduction = 1
            bid_tokens += 1
            
        if highest_value >= 7:  # High values (7-9)
            move_reduction = 1
            bid_tokens += 1
            
        # Apply stat reductions to the target
        duration = 2  # Effect lasts for 2 turns
        
        if attack_reduction > 0:
            target_unit.attack_bonus -= attack_reduction
            target_unit.auction_curse_attack_duration = duration

        if range_reduction > 0:
            target_unit.attack_range_bonus -= range_reduction
            target_unit.auction_curse_range_duration = duration

        if move_reduction > 0:
            target_unit.move_range_bonus -= move_reduction
            target_unit.auction_curse_move_duration = duration
            
        # Store bid tokens for the user
        if not hasattr(user, 'bid_tokens'):
            user.bid_tokens = {'attack': 0, 'attack_range': 0, 'move_range': 0}
            
        if attack_reduction > 0:
            user.bid_tokens['attack'] += 1
        if range_reduction > 0:
            user.bid_tokens['attack_range'] += 1
        if move_reduction > 0:
            user.bid_tokens['move_range'] += 1
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} casts Auction Curse on {target_unit.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        if highest_value > 0:
            penalty_msg = f"Cosmic value {highest_value} reduces"
            penalties = []
            
            if attack_reduction > 0:
                penalties.append("attack")
            if range_reduction > 0:
                penalties.append("range")
            if move_reduction > 0:
                penalties.append("movement")
                
            penalty_msg += f" {', '.join(penalties)} for {duration} turns!"
            message_log.add_message(
                penalty_msg,
                MessageType.ABILITY,
                player=user.player
            )
            
        message_log.add_message(
            f"{user.get_display_name()} gains {bid_tokens} bid tokens!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get auction animation - creates podium, spectral bidders, transferring stats
            auction_animation = ui.asset_manager.get_skill_animation_sequence('auction_curse')
            if not auction_animation:
                auction_animation = ['A', '¤', '=', '¤', 'π', '¤', 'Γ', '¤', '$', '¤', '¢', '¤', '£', '¤', '|', '¤', '+', '¤']
                
            # Show animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                auction_animation,
                1,  # Red color
                0.15  # Duration
            )
            
        return True
        
    def award_bid_token(self, user: 'Unit', target_pos: tuple, stat: str, game: 'Game', ui=None) -> bool:
        """Award a bid token to an ally, granting them a stat bonus."""
        # Check if the user has bid tokens
        if not hasattr(user, 'bid_tokens'):
            return False
            
        # Check if user has tokens of the requested type
        if user.bid_tokens.get(stat, 0) <= 0:
            return False
            
        # Check if target is a valid ally
        ally = game.get_unit_at(target_pos[0], target_pos[1])
        if not ally or ally.player != user.player:
            return False
            
        # Check if target is within range 3
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > 3:
            return False
            
        # Apply stat bonus to the ally based on the stat type
        if stat == 'attack':
            ally.attack_bonus += 1
            ally.bid_attack_duration = 2  # Duration of 2 turns
        elif stat == 'attack_range':
            ally.attack_range_bonus += 1
            ally.bid_range_duration = 2
        elif stat == 'move_range':
            ally.move_range_bonus += 1
            ally.bid_move_duration = 2
        
        # Consume the token
        user.bid_tokens[stat] -= 1
        
        # Log the token award
        message_log.add_message(
            f"{user.get_display_name()} awards a {stat} bid token to {ally.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get token award animation - glowing tokens transferring to ally
            token_animation = ui.asset_manager.get_skill_animation_sequence('bid_token')
            if not token_animation:
                token_animation = ['$', '¤', '*', '¤', '+', '¤', '¢', '¤', '£', '¤', '€', '¤', 'A']
                
            # Show animation from user to ally
            ui.renderer.animate_path(
                user.y, user.x,
                ally.y, ally.x,
                token_animation,
                2,  # Green color
                0.1  # Duration
            )
            
        return True


class DivineDrepreciationSkill(ActiveSkill):
    """
    Active skill for DELPHIC_APPRAISER.
    Reappraises a furniture piece as cosmically worthless, creating a reality distortion.
    """
    
    def __init__(self):
        super().__init__(
            name="Divine Depreciation",
            key="D",
            description="Dramatically reappraises a furniture piece as cosmically worthless, creating a 3×3 reality distortion. Damages enemies and alters attack/skill ranges.",
            target_type=TargetType.AREA,
            cooldown=4,  # Cooldown of 4 turns as specified
            range_=3,
            area=1  # 3×3 area (radius 1)
        )
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Divine Depreciation can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check if the target position is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
            
        # Target must be a furniture piece
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        if terrain not in [TerrainType.FURNITURE, TerrainType.COAT_RACK, 
                         TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
            return False
            
        # Check if target is within range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Divine Depreciation skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to cast Divine Depreciation!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Divine Depreciation skill on a furniture piece."""
        # Get the cosmic value (will be generated if it doesn't exist)
        cosmic_value = game.map.get_cosmic_value(target_pos[0], target_pos[1], player=user.player, game=game)
        if cosmic_value is None:
            cosmic_value = random.randint(1, 9)  # Fallback
        
        # Create reality distortion zone
        if not hasattr(game, 'reality_distortions'):
            game.reality_distortions = {}
            
        # Define the affected area (3×3)
        affected_area = []
        center_y, center_x = target_pos
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                y, x = center_y + dy, center_x + dx
                if game.is_valid_position(y, x):
                    affected_area.append((y, x))
                    
        # Create the distortion
        distortion_id = f"divine_depreciation_{len(game.reality_distortions) + 1}"
        game.reality_distortions[distortion_id] = {
            'area': affected_area,
            'center': target_pos,
            'creator': user,
            'cosmic_value': cosmic_value,
            'duration': 2  # Effects last 2 turns
        }
        
        # Apply effects to units in the area
        for pos in affected_area:
            unit = game.get_unit_at(pos[0], pos[1])
            if not unit:
                continue
                
            if unit.player != user.player:  # Enemy
                # Deal damage
                damage = 2 + cosmic_value
                old_hp = unit.hp
                unit.hp -= damage
                
                # Apply range penalty
                unit.attack_range_bonus -= 1
                unit.divine_depreciation_duration = 2  # Duration of 2 turns
                
                message_log.add_message(
                    f"{unit.get_display_name()} takes {damage} damage and -1 to attack range from Divine Depreciation!",
                    MessageType.COMBAT,
                    player=user.player
                )
                
                # Handle unit death
                if unit.hp <= 0:
                    message_log.add_message(
                        f"{unit.get_display_name()} is destroyed by Divine Depreciation!",
                        MessageType.COMBAT,
                        player=user.player
                    )
                    game.remove_unit(unit)
            else:  # Ally
                # Apply range bonus
                unit.attack_range_bonus += 1
                unit.divine_depreciation_duration = 2  # Duration of 2 turns
                
                message_log.add_message(
                    f"{unit.get_display_name()} gains +1 to attack range from Divine Depreciation!",
                    MessageType.ABILITY,
                    player=user.player
                )
                
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} casts Divine Depreciation on furniture with cosmic value {cosmic_value}!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get divine depreciation animation - furniture value drops, floor warps and sinks
            depreciation_animation = ui.asset_manager.get_skill_animation_sequence('divine_depreciation')
            if not depreciation_animation:
                depreciation_animation = ['A', '¤', '↓', '¤', '9', '¤', '6', '¤', '3', '¤', '0', '¤', '_', '¤', '.', '¤', ' ', '¤']
                
            # Show animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                depreciation_animation,
                5,  # Magenta color
                0.15  # Duration
            )
            
            # Show area effect
            for pos in affected_area:
                if pos != target_pos:  # Skip center, we already animated it
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        ['↓', '¤', '_', '¤', '.', '¤', ' ', '¤'],  # Downward symbols for depression
                        4,  # Purple color
                        0.1  # Duration
                    )
                    
        return True