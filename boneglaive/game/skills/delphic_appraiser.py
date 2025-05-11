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
            'active': True,
            'imbued': True  # Mark as imbued for special rendering
        }
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} infuses furniture with Market Futures! Cosmic value: {cosmic_value}",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play elaborate Market Futures animation sequence as described in document
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Step 1: The APPRAISER touches the furniture
            # Show appraiser reaching toward furniture
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(user.y, user.x), Position(target_pos[0], target_pos[1]))

            # Show reaching animation
            if len(path) > 1:
                # Get the point between appraiser and furniture
                mid_point = path[len(path) // 2]

                # Draw reaching gesture
                ui.renderer.animate_attack_sequence(
                    mid_point.y, mid_point.x,
                    ['A', 'T', '|'],
                    7,  # White color
                    0.15  # Duration
                )

            # Step 2: Temporal market projections spiral around the furniture
            spiral_animation = ['$', '£', '€', '¥', '§']
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                spiral_animation,
                6,  # Cyan/blue color
                0.15  # Duration
            )
            sleep_with_animation_speed(0.1)  # Pause between animation phases

            # Step 3: The furniture transforms into a more valuable future version
            transform_animation = ['#', 'Φ', 'Ψ', 'Ω', '¥']
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                transform_animation,
                3,  # Green color for value enhancement
                0.15  # Duration
            )

            # Step 4: Furniture glows with investment potential
            # Add glowing effect radiating from the furniture to adjacent positions
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue  # Skip the center itself

                    y, x = target_pos[0] + dy, target_pos[1] + dx

                    if game.is_valid_position(y, x):
                        # Small glow animation in adjacent cells
                        ui.renderer.animate_attack_sequence(
                            y, x,
                            ['*', '.'],
                            6,  # Cyan/blue color
                            0.05  # Quick duration
                        )

            # Final anchor marker on furniture
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                ['¤', 'T', '*'],
                3,  # Green color for established anchor
                0.2  # Duration for final state
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

        # Check if the ally is adjacent to the anchor
        distance_to_anchor = game.chess_distance(ally.y, ally.x, anchor_pos[0], anchor_pos[1])
        if distance_to_anchor > 1:  # Not adjacent
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
                teleport_animation = ['$', '↗', '→', '↘', '↓', '*', 'A']
                
            # Show animation from old position to new position
            if hasattr(ui.renderer, 'animate_path'):
                ui.renderer.animate_path(
                    old_pos[0], old_pos[1],
                    destination[0], destination[1],
                    teleport_animation,
                    3,  # Yellow/gold color
                    0.1  # Duration
                )
            else:
                # Fallback to basic animation if animate_path not available
                ui.renderer.animate_attack_sequence(
                    destination[0], destination[1],
                    teleport_animation,
                    3,  # Yellow/gold color
                    0.2  # Duration
                )
            
        # Deactivate the anchor after use
        game.teleport_anchors[anchor_pos]['active'] = False
        game.teleport_anchors[anchor_pos]['imbued'] = False  # Remove imbued status for rendering
        
        return True


class AuctionCurseSkill(ActiveSkill):
    """
    Active skill for DELPHIC_APPRAISER.
    Subjects an enemy to a cosmic auction that reduces their stats and awards tokens to an ally.
    """

    def __init__(self):
        super().__init__(
            name="Auction Curse",
            key="A",
            description="Subjects an enemy to a cosmic auction, reducing their stats based on nearby furniture values and immediately awards buffs to a selected ally.",
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

        # Store enemy target position
        user.enemy_target = target_pos

        # Set a flag indicating we need to select an ally next
        user.awaiting_ally_target = True

        # Log that the skill has been queued and needs an ally target
        message_log.add_message(
            f"{user.get_display_name()} prepares to cast Auction Curse! Select an ally to receive tokens.",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def set_ally_target(self, user: 'Unit', ally_pos: tuple, game: 'Game') -> bool:
        """Set the ally target for the auction curse."""
        # Validate ally target
        if not game.is_valid_position(ally_pos[0], ally_pos[1]):
            return False

        # Check if target is a valid ally
        ally = game.get_unit_at(ally_pos[0], ally_pos[1])
        if not ally or ally.player != user.player:
            return False

        # Check if ally is within range 3
        distance = game.chess_distance(user.y, user.x, ally_pos[0], ally_pos[1])
        if distance > 3:
            return False

        # Set the skill target to the enemy target we saved earlier
        user.skill_target = user.enemy_target
        user.selected_skill = self

        # Store the ally target for use during execution
        user.ally_target = ally_pos

        # Reset the awaiting flag
        user.awaiting_ally_target = False

        # Track action order
        user.action_timestamp = game.action_counter
        game.action_counter += 1

        # Set cooldown
        self.current_cooldown = self.cooldown

        # Log that both targets have been selected
        message_log.add_message(
            f"{user.get_display_name()} will curse an enemy and empower {ally.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Auction Curse skill on an enemy and apply tokens to the selected ally."""
        # Get the target unit (enemy)
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False

        # Get the ally unit
        if not hasattr(user, 'ally_target'):
            return False

        ally_pos = user.ally_target
        ally = game.get_unit_at(ally_pos[0], ally_pos[1])
        if not ally or ally.player != user.player:
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

        # Apply stat reductions to the target enemy
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

        # Play first part of auction curse animation
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Step 1: The APPRAISER creates an auction podium with cosmic value displayed
            # Start from the Appraiser's position
            podium_animation = ['A', '=', '|', '=', '|']
            ui.renderer.animate_attack_sequence(
                user.y, user.x,  # First part is at the user's position
                podium_animation,
                7,  # White color for the appraiser
                0.2  # Duration
            )
            sleep_with_animation_speed(0.1)  # Pause between animation phases

            # Step 2: Show cosmic value prominently displayed on the podium
            # Create the value display animation at the target position
            value_display = []
            if highest_value > 0:
                value_display = ['=', str(highest_value), '=']
            else:
                value_display = ['=', '?', '=']

            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                value_display,
                6,  # Yellowish color for the value display
                0.2  # Duration
            )
            sleep_with_animation_speed(0.1)  # Pause between animation phases

            # Step 3: Spectral furniture pieces appear as bidders raising paddles
            # Animate spectral bidders around the target in nearby positions
            if nearby_furniture:
                # Show bidding animation from furniture positions
                for i, pos in enumerate(nearby_furniture[:3]):  # Limit to 3 pieces of furniture for clarity
                    bidder_animations = ['π', 'Γ', '|', '!']
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        bidder_animations,
                        3,  # Green color for the bidders
                        0.1  # Duration
                    )
                    # Slight delay between different bidders
                    sleep_with_animation_speed(0.05)

            # Step 4: With each successful bid, stat attributes visibly transfer from enemy
            # Show attributes being stripped from the target
            if attack_reduction > 0 or range_reduction > 0 or move_reduction > 0:
                # Animate attributes being removed
                stat_transfer = ['$', '¢', '%', '-', '.']
                ui.renderer.animate_attack_sequence(
                    target_pos[0], target_pos[1],
                    stat_transfer,
                    1,  # Red color for the target
                    0.15  # Duration
                )

                # Step 5: Stats transfer to the APPRAISER as glowing tokens
                # Show tokens moving from target to appraiser
                token_path = []

                # Get path from target to user
                from boneglaive.utils.coordinates import get_line, Position
                path = get_line(Position(target_pos[0], target_pos[1]), Position(user.y, user.x))

                # Animate token movement along the path
                token_symbol = '$'
                for point in path:
                    ui.renderer.draw_tile(point.y, point.x, token_symbol, 6)  # Yellow for tokens
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.07)

                    # Clear previous position (except target and user positions)
                    if (point.y != target_pos[0] or point.x != target_pos[1]) and (point.y != user.y or point.x != user.x):
                        # Get the terrain to restore proper display
                        terrain = game.map.get_terrain_at(point.y, point.x)
                        terrain_char = ' '
                        if terrain:
                            terrain_name = terrain.name.lower().replace('_', ' ')
                            if 'empty' in terrain_name:
                                terrain_char = ' '
                            elif 'furniture' in terrain_name:
                                terrain_char = '#'
                            else:
                                terrain_char = '.'
                        ui.renderer.draw_tile(point.y, point.x, terrain_char, 0)

                # Final token collection animation at the appraiser
                token_collection = ['$', '+', '*']
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    token_collection,
                    3,  # Green color for successfully collected tokens
                    0.1  # Duration
                )

        # Apply stat bonuses to the ally based on reductions applied
        if attack_reduction > 0:
            ally.attack_bonus += 1
            ally.bid_attack_duration = 2  # Duration of 2 turns
            message_log.add_message(
                f"{ally.get_display_name()} gains +1 attack for 2 turns!",
                MessageType.ABILITY,
                player=user.player
            )

        if range_reduction > 0:
            ally.attack_range_bonus += 1
            ally.bid_range_duration = 2
            message_log.add_message(
                f"{ally.get_display_name()} gains +1 range for 2 turns!",
                MessageType.ABILITY,
                player=user.player
            )

        if move_reduction > 0:
            ally.move_range_bonus += 1
            ally.bid_move_duration = 2
            message_log.add_message(
                f"{ally.get_display_name()} gains +1 movement for 2 turns!",
                MessageType.ABILITY,
                player=user.player
            )

        # Play token award animation from appraiser to ally
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager') and bid_tokens > 0:
            # Tell the player what's happening
            message_log.add_message(
                f"{user.get_display_name()} awards {bid_tokens} bid tokens to {ally.get_display_name()}!",
                MessageType.ABILITY,
                player=user.player
            )

            # Get token award animation - glowing tokens transferring to ally
            token_animation = ui.asset_manager.get_skill_animation_sequence('bid_token')
            if not token_animation:
                token_animation = ['$', '*', '+', '¢', '£', '€', 'A']

            # Show animation from user to ally
            if hasattr(ui.renderer, 'animate_path'):
                ui.renderer.animate_path(
                    user.y, user.x,
                    ally.y, ally.x,
                    token_animation,
                    2,  # Green color
                    0.1  # Duration
                )
            else:
                # Fallback to basic animation if animate_path not available
                ui.renderer.animate_attack_sequence(
                    ally.y, ally.x,
                    token_animation,
                    2,  # Green color
                    0.2  # Duration
                )

        # Clean up temp attributes
        if hasattr(user, 'enemy_target'):
            delattr(user, 'enemy_target')
        if hasattr(user, 'ally_target'):
            delattr(user, 'ally_target')

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
        
        # Play elaborate animation sequence as described in DELPHIC_APPRAISER.md
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Step 1: The APPRAISER makes a dramatic downward valuation gesture
            gesture_animation = ['A', '↓', '$', '↓']
            ui.renderer.animate_attack_sequence(
                user.y, user.x,  # First part is at the user's position
                gesture_animation,
                7,  # White color for the appraiser
                0.2  # Duration
            )
            sleep_with_animation_speed(0.1)  # Pause between animation phases

            # Step 2: The furniture's cosmic value rapidly drops to zero
            value_drop_animation = []
            # Start with the actual cosmic value
            current_value = cosmic_value
            while current_value >= 0:
                value_drop_animation.append(str(current_value))
                current_value -= 1

            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                value_drop_animation,
                5,  # Magenta color for value display
                0.15  # Duration
            )
            sleep_with_animation_speed(0.1)  # Pause between animation phases

            # Step 3: The furniture piece appears to age centuries in seconds
            aging_animation = ['Ω', '§', '@', '#', '_']
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                aging_animation,
                6,  # Yellowish color for aging
                0.15  # Duration
            )
            sleep_with_animation_speed(0.1)  # Pause between animation phases

            # Step 4: The floor around it warps and sinks
            # First show a ripple effect from the center outward
            for distance in range(1, 3):  # Range 1-2 to cover the 3x3 area
                for y in range(target_pos[0] - distance, target_pos[0] + distance + 1):
                    for x in range(target_pos[1] - distance, target_pos[1] + distance + 1):
                        # Only animate positions at exactly the current distance (edges)
                        if abs(y - target_pos[0]) == distance or abs(x - target_pos[1]) == distance:
                            # Check if position is valid and in affected area
                            if game.is_valid_position(y, x) and (y, x) in affected_area:
                                ui.renderer.animate_attack_sequence(
                                    y, x,
                                    ['~', '_', '.'],
                                    4,  # Purple color
                                    0.05  # Quick duration for ripple
                                )
                sleep_with_animation_speed(0.1)  # Pause between ripples

            # Step 5: Depression filled with failed investment certificates and devalued market assets
            # Display market collapse symbols in all affected positions
            for pos in affected_area:
                depressed_tile_animation = ['$', '0', '_', '.']
                ui.renderer.animate_attack_sequence(
                    pos[0], pos[1],
                    depressed_tile_animation,
                    4,  # Purple color
                    0.1  # Duration
                )
                    
        return True