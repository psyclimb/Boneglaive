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
            if not hasattr(user, 'valuation_oracle_buff') or not user.valuation_oracle_buff:
                message_log.add_message(
                    f"{user.get_display_name()}'s Valuation Oracle senses the cosmic value of nearby furniture",
                    MessageType.ABILITY,
                    player=user.player
                )

            # Set status effect flag and duration (lasts indefinitely while adjacent)
            user.valuation_oracle_buff = True
            user.valuation_oracle_duration = 999  # High value, will be refreshed each turn while adjacent
            
            # Apply bonuses to defense and attack range using *_bonus attributes
            user.defense_bonus = 1
            user.attack_range_bonus = 1
        else:
            # If no longer adjacent, remove the status effect immediately
            if hasattr(user, 'valuation_oracle_buff') and user.valuation_oracle_buff:
                user.valuation_oracle_buff = False
                user.valuation_oracle_duration = 0
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
            description="Infuses a furniture piece with temporal investment energy. Creates a teleportation anchor that allies can activate. Grants maturing investment: +1 ATK (turn 1), +2 ATK (turn 2), +3 ATK (turn 3) with +1 Range for all 3 turns. Maturation occurs right before attacking.",
            target_type=TargetType.AREA,
            cooldown=6,  # Increased cooldown to 6 turns
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
                         TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE, 
                         TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE, 
                         TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                         TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                         TerrainType.COT, TerrainType.CONVEYOR]:
            return False

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target is within range of current or planned position
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight to target
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Market Futures skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Set the market futures indicator to show the target
        user.market_futures_indicator = target_pos

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to infuse furniture with Market Futures",
            MessageType.ABILITY,
            player=user.player
        )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Market Futures skill on a furniture piece."""

        # Clear the market futures indicator when skill is executed
        user.market_futures_indicator = None

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
            f"{user.get_display_name()} infuses furniture with Market Futures. Cosmic value: {cosmic_value}",
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
            f"{ally.get_display_name()} activates Market Futures teleport",
            MessageType.ABILITY,
            player=ally.player
        )
        
        # Apply investment effect if not immune to status effects
        if ally.is_immune_to_effects():
            # Log immunity message
            message_log.add_message(
                f"{ally.get_display_name()} is immune to investment effects due to Stasiality",
                MessageType.ABILITY,
                player=ally.player
            )
        else:
            # Always apply the investment effect regardless of cosmic value
            message_log.add_message(
                f"Market Futures grants {ally.get_display_name()} a maturing investment effect",
                MessageType.ABILITY,
                player=ally.player
            )
            
            # Apply initial investment bonuses
            ally.attack_bonus += 1      # Will mature over time
            ally.attack_range_bonus += 1  # Flat bonus, doesn't mature
            
            # Set up investment maturation tracking
            ally.market_futures_bonus_applied = True
            ally.market_futures_duration = 3  # 3 turns duration
            ally.market_futures_maturity = 1  # Starts at maturity level 1
            
            # Add currency status icon indicator
            ally.has_investment_effect = True
            
            # Investment message removed from log
            
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
    Forces enemy into unwilling appraisal that inflates surrounding furniture values while draining their life.
    """

    def __init__(self):
        super().__init__(
            name="Auction Curse",
            key="A", 
            description=("Curse target enemy with a twisted auction. Each turn, they take "
                        "damage equal to total cosmic value of furniture within 2 tiles. "
                        "Each damage tick inflates cosmic values of nearby furniture by +1, "
                        "prevents all healing for the cursed unit, and heals allied units "
                        "within 2 tiles by 1 HP with twisted energy."),
            target_type=TargetType.ENEMY,
            cooldown=4,
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

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target is within range of current or planned position
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight to target
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Use the Auction Curse skill directly on target enemy."""
        if not self.can_use(user, target_pos, game):
            return False

        # Set the skill target directly
        user.skill_target = target_pos
        user.selected_skill = self

        # Track action order
        user.action_timestamp = game.action_counter
        game.action_counter += 1

        # Set cooldown
        self.current_cooldown = self.cooldown

        # Log that the skill is ready to execute
        message_log.add_message(
            f"{user.get_display_name()} prepares to cast Auction Curse",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Auction Curse skill on target enemy."""
        # Get the target unit (enemy)
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False

        # Find nearby furniture and their cosmic values
        nearby_furniture = []
        for y in range(max(0, target_pos[0] - 2), min(game.map.height, target_pos[0] + 3)):
            for x in range(max(0, target_pos[1] - 2), min(game.map.width, target_pos[1] + 3)):
                terrain = game.map.get_terrain_at(y, x)
                if terrain in [TerrainType.FURNITURE, TerrainType.COAT_RACK,
                             TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE, 
                             TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE, 
                             TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                             TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                             TerrainType.COT, TerrainType.CONVEYOR]:
                    nearby_furniture.append((y, x))

                    # Get cosmic value (will be generated if it doesn't exist yet)
                    game.map.get_cosmic_value(y, x, player=user.player, game=game)

        # Calculate average cosmic value of nearby furniture
        average_value = 0
        if nearby_furniture:
            # Get cosmic values for all nearby furniture
            cosmic_values = []
            for pos in nearby_furniture:
                value = game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)
                if value is not None:
                    cosmic_values.append(value)

            if cosmic_values:
                # Calculate the average, rounded up
                import math
                average_value = math.ceil(sum(cosmic_values) / len(cosmic_values))

                # Ensure average value is within valid range
                average_value = max(1, min(9, average_value))

        # Apply DOT effect to the target enemy, if they're not immune
        dot_duration = average_value  # Duration equals the average value

        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} casts Auction Curse on {target_unit.get_display_name()}",
            MessageType.ABILITY,
            player=user.player
        )

        # Special message for maximum duration (9 turns)
        if dot_duration == 9:
            message_log.add_message(
                f"DELPHIC APPRAISER {user.get_display_name()} rolls deftly",
                MessageType.ABILITY,
                player=user.player
            )

        # Check if the target is immune to status effects (GRAYMAN with Stasiality)
        if target_unit.is_immune_to_effects():
            # Skip applying effects but add a message about immunity
            message_log.add_message(
                f"{target_unit.get_display_name()} is immune to Auction Curse due to Stasiality",
                MessageType.ABILITY,
                player=target_unit.player  # Use target's player color for correct display
            )
        else:
            # Apply the DOT effect if the target is not immune
            if average_value > 0:
                # Set up the DOT effect
                target_unit.auction_curse_dot = True
                target_unit.auction_curse_dot_duration = dot_duration
                target_unit.auction_curse_no_heal = True  # Prevent all healing
                
                # Log the DOT application
                message_log.add_message(
                    f"Auction Curse applied. {target_unit.get_display_name()} will take 1 damage per turn for {dot_duration} turns",
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

            # Step 2: Show average cosmic value prominently displayed on the podium
            # Create the value display animation at the target position
            value_display = []
            if average_value > 0:
                value_display = ['=', str(average_value), '=']
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

            # Step 4: Show target being afflicted with the DOT effect
            if average_value > 0:
                # Animate curse application
                curse_symbols = ['$', '¢', '%', '-', '.']
                ui.renderer.animate_attack_sequence(
                    target_pos[0], target_pos[1],
                    curse_symbols,
                    10,  # Red color for the target
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

                # Final curse completion animation at the appraiser
                curse_completion = ['*', '!', '*']
                ui.renderer.animate_attack_sequence(
                    user.y, user.x,
                    curse_completion,
                    10,  # Red color for curse completion
                    0.15  # Duration
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
            description="Dramatically reappraises a furniture piece as cosmically worthless, creating a 7×7 reality distortion. Sets target furniture to value 1, deals damage that bypasses defense and pulls enemies toward the center based on move values. All other furniture has cosmic values rerolled.",
            target_type=TargetType.AREA,
            cooldown=6,  # Cooldown of 6 turns
            range_=3,
            area=3  # 7×7 area (radius 3)
        )
    
    def _get_furniture_name(self, terrain_type) -> str:
        """Convert TerrainType enum to readable furniture name."""
        terrain_names = {
            TerrainType.FURNITURE: "Furniture",
            TerrainType.COAT_RACK: "Coat Rack", 
            TerrainType.OTTOMAN: "Ottoman",
            TerrainType.CONSOLE: "Console",
            TerrainType.DEC_TABLE: "Decorative Table",
            TerrainType.TIFFANY_LAMP: "Tiffany Lamp",
            TerrainType.EASEL: "Easel",
            TerrainType.SCULPTURE: "Sculpture", 
            TerrainType.BENCH: "Bench",
            TerrainType.PODIUM: "Podium",
            TerrainType.VASE: "Vase",
            TerrainType.WORKBENCH: "Workbench",
            TerrainType.COUCH: "Couch",
            TerrainType.TOOLBOX: "Toolbox",
            TerrainType.COT: "Cot",
            TerrainType.CONVEYOR: "Conveyor Belt"
        }
        return terrain_names.get(terrain_type, "Furniture")

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
                         TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE, 
                         TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE, 
                         TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                         TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                         TerrainType.COT, TerrainType.CONVEYOR]:
            return False

        # If the unit has a move_target, use that position for range calculation
        if user.move_target:
            source_y, source_x = user.move_target
        else:
            source_y, source_x = user.y, user.x

        # Check if target is within range of current or planned position
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight to target
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Divine Depreciation skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        # Set the divine depreciation indicator to show the target
        user.divine_depreciation_indicator = target_pos

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to cast Divine Depreciation",
            MessageType.ABILITY,
            player=user.player
        )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Divine Depreciation skill on a furniture piece."""
        # Clear the divine depreciation indicator when skill is executed
        user.divine_depreciation_indicator = None

        # Get the cosmic value of the target (will be generated if it doesn't exist)
        original_cosmic_value = game.map.get_cosmic_value(target_pos[0], target_pos[1], player=user.player, game=game)
        if original_cosmic_value is None:
            original_cosmic_value = random.randint(1, 9)  # Fallback
            
        # Get the furniture name for messages
        target_terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        furniture_name = self._get_furniture_name(target_terrain)

        # Create reality distortion zone
        if not hasattr(game, 'reality_distortions'):
            game.reality_distortions = {}

        # Define the affected area (7×7)
        affected_area = []
        center_y, center_x = target_pos
        for dy in range(-3, 4):  # -3, -2, -1, 0, 1, 2, 3
            for dx in range(-3, 4):  # -3, -2, -1, 0, 1, 2, 3
                y, x = center_y + dy, center_x + dx
                if game.is_valid_position(y, x):
                    affected_area.append((y, x))

        # Collect furniture in the area (excluding the target)
        other_furniture = []
        for pos in affected_area:
            if pos != target_pos:  # Skip the target furniture
                terrain = game.map.get_terrain_at(pos[0], pos[1])
                if terrain in [TerrainType.FURNITURE, TerrainType.COAT_RACK,
                             TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
                    other_furniture.append(pos)
                    # Ensure cosmic value exists for all furniture
                    game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)

        # Calculate average cosmic value of other furniture (rounded up)
        avg_cosmic_value = 1  # Default if no other furniture
        if other_furniture:
            total_value = 0
            count = 0
            for pos in other_furniture:
                value = game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)
                if value is not None:
                    total_value += value
                    count += 1

            if count > 0:
                import math
                avg_cosmic_value = math.ceil(total_value / count)

        # Set target furniture's cosmic value to 1
        game.map.set_cosmic_value(target_pos[0], target_pos[1], 1)

        # Calculate effect value based on the difference between average value and target value (now 1)
        effect_value = max(1, avg_cosmic_value - 1)  # Ensure at least 1 damage/healing

        # Special message for maximum damage (8 damage)
        if effect_value == 8:
            message_log.add_message(
                f"DELPHIC APPRAISER {user.get_display_name()} rolls deftly",
                MessageType.ABILITY,
                player=user.player
            )

        # Create the distortion
        distortion_id = f"divine_depreciation_{len(game.reality_distortions) + 1}"
        game.reality_distortions[distortion_id] = {
            'area': affected_area,
            'center': target_pos,
            'creator': user,
            'cosmic_value': 1,  # Now fixed at 1
            'avg_cosmic_value': avg_cosmic_value,  # Store for reference
            'duration': 2  # Effects last 2 turns
        }

        # Collect all enemies in the area for implosion calculation
        enemies_in_area = []
        for pos in affected_area:
            unit = game.get_unit_at(pos[0], pos[1])
            if not unit:
                continue

            if unit.player != user.player:  # Enemy
                enemies_in_area.append(unit)

        # Calculate average move value of enemies (if any)
        avg_move_value = 0
        if enemies_in_area:
            total_move = sum(enemy.get_effective_stats()['move_range'] for enemy in enemies_in_area)
            import math
            avg_move_value = math.ceil(total_move / len(enemies_in_area))

        # Calculate pull distance based on difference between average move value and cosmic value (1)
        pull_distance = max(1, avg_move_value - 1)  # Ensure at least 1 space pull

        # Apply damage and pull effects to enemies
        for unit in enemies_in_area:
            # Deal damage based on cosmic value difference, bypassing defense
            old_hp = unit.hp
            
            # Use take_damage to apply damage directly (bypassing defense)
            actual_damage = unit.take_damage(effect_value, user, "Divine Depreciation")

            message_log.add_combat_message(
                attacker_name=user.get_display_name(),
                target_name=unit.get_display_name(),
                damage=actual_damage,
                ability="Divine Depreciation",
                attacker_player=user.player,
                target_player=unit.player
            )

            # Show damage number if UI is available
            if ui and hasattr(ui, 'renderer') and actual_damage > 0:
                damage_text = f"-{actual_damage}"
                
                # Make damage text more prominent with flashing effect (like FOWL_CONTRIVANCE)
                for i in range(3):
                    # First clear the area
                    ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                    # Draw with alternating bold/normal for a flashing effect
                    attrs = curses.A_BOLD if i % 2 == 0 else 0
                    ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)  # White color
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.1)
                
                # Final damage display (stays on screen slightly longer)
                ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, curses.A_BOLD)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.3)  # Match the 0.3s delay used in FOWL_CONTRIVANCE

            # Calculate pull effect (move toward center)
            start_pos = (unit.y, unit.x)
            target_center = target_pos

            # Calculate direction vector from unit to center
            dir_y = target_center[0] - unit.y
            dir_x = target_center[1] - unit.x

            # Normalize the direction
            distance = max(1, abs(dir_y) + abs(dir_x))  # Manhattan distance

            # Calculate how far to pull the unit (not exceeding distance to center)
            actual_pull = min(pull_distance, distance)

            if actual_pull > 0 and distance > 0:
                # Check if unit is immune to displacement effects (GRAYMAN with Stasiality)
                if unit.is_immune_to_effects():
                    message_log.add_message(
                        f"{unit.get_display_name()} is immune to Divine Depreciation's pull effect due to Stasiality",
                        MessageType.ABILITY,
                        player=unit.player  # Use unit's player color for correct display
                    )
                else:
                    # Calculate pull vector (respecting terrain and other units)
                    pull_y = int(dir_y * actual_pull / distance) if dir_y != 0 else 0
                    pull_x = int(dir_x * actual_pull / distance) if dir_x != 0 else 0

                    # Try to move the unit as close as possible to the target direction
                    new_y, new_x = unit.y, unit.x
                    steps_taken = 0

                    # Try to move the unit step by step
                    for step in range(actual_pull):
                        # Calculate step direction (prioritize largest component)
                        if abs(dir_y) > abs(dir_x):
                            step_y = 1 if dir_y > 0 else -1 if dir_y < 0 else 0
                            step_x = 0
                        else:
                            step_y = 0
                            step_x = 1 if dir_x > 0 else -1 if dir_x < 0 else 0

                        # Check if the next position is valid and empty
                        next_y, next_x = new_y + step_y, new_x + step_x
                        if (game.is_valid_position(next_y, next_x) and
                            game.map.is_passable(next_y, next_x) and
                            game.get_unit_at(next_y, next_x) is None):
                            # Move to the next position
                            new_y, new_x = next_y, next_x
                            steps_taken += 1
                        else:
                            # Try the other direction component
                            if step_y != 0:  # Was trying vertical, try horizontal
                                step_y = 0
                                step_x = 1 if dir_x > 0 else -1 if dir_x < 0 else 0
                            else:  # Was trying horizontal, try vertical
                                step_y = 1 if dir_y > 0 else -1 if dir_y < 0 else 0
                                step_x = 0

                            next_y, next_x = new_y + step_y, new_x + step_x
                            if (game.is_valid_position(next_y, next_x) and
                                game.map.is_passable(next_y, next_x) and
                                game.get_unit_at(next_y, next_x) is None):
                                # Move to the alternative position
                                new_y, new_x = next_y, next_x
                                steps_taken += 1
                            else:
                                # Can't move further in either direction
                                break

                    # Update unit position if it moved
                    if steps_taken > 0:
                        unit.y, unit.x = new_y, new_x
                        message_log.add_message(
                            f"{unit.get_display_name()} is pulled {steps_taken} spaces by the {furniture_name.lower()}'s reality distortion",
                            MessageType.ABILITY,
                            player=user.player
                        )

            # Handle unit death
            if unit.hp <= 0:
                message_log.add_message(
                    f"{unit.get_display_name()} perishes",
                    MessageType.COMBAT,
                    player=user.player
                )
                # Units are not removed from the game, just marked as dead by setting hp to 0
                unit.hp = 0

        # Reroll cosmic values for all other furniture in the AOE
        for pos in other_furniture:
            # Generate a new random cosmic value (1-9)
            new_value = random.randint(1, 9)
            game.map.set_cosmic_value(pos[0], pos[1], new_value)

        # Log the skill activation with details about the cosmic values
        message_log.add_message(
            f"{user.get_display_name()} casts Divine Depreciation on the furniture",
            MessageType.ABILITY,
            player=user.player
        )

        if other_furniture:
            message_log.add_message(
                f"The furniture's value drops to 1, creating a reality distortion",
                MessageType.ABILITY,
                player=user.player
            )

        # Play fast sinkhole animation sequence
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Step 1: Value Collapse - Show furniture's cosmic value plummeting
            value_collapse_animation = []
            current_value = original_cosmic_value
            while current_value > 1 and len(value_collapse_animation) < 3:  # Limit to 3 frames max
                value_collapse_animation.append(str(current_value))
                current_value = max(1, current_value - 3)  # Drop faster for shorter animation
            value_collapse_animation.append('1')  # Always end at 1
            
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                value_collapse_animation,
                7,  # White→Yellow showing instability  
                0.08  # Quick duration
            )

            # Step 2: Sinkhole Formation - Floor collapses inward creating gravitational pull
            sinkhole_animation = ['o', 'O', '@']
            # Show sinkhole forming at center and expanding outward
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                sinkhole_animation,
                0,  # Black/dark showing the void
                0.06  # Quick formation
            )
            
            # Show sinkhole effect radiating outward in concentric rings
            for distance in range(1, 4):  # 1, 2, 3 distance from center
                for y in range(target_pos[0] - distance, target_pos[0] + distance + 1):
                    for x in range(target_pos[1] - distance, target_pos[1] + distance + 1):
                        # Only animate positions at exactly the current distance (ring edge)
                        if (abs(y - target_pos[0]) == distance or abs(x - target_pos[1]) == distance) and \
                           game.is_valid_position(y, x) and (y, x) in affected_area:
                            ui.renderer.animate_attack_sequence(
                                y, x,
                                ['o'],  # Single frame showing ground instability
                                0,  # Dark color
                                0.02  # Very quick
                            )

            # Step 3: Everything Falls In - Units tumble toward center, simultaneous effects
            fall_animation = ['\\', '|', '/']
            
            # Apply effects to all units simultaneously
            for unit in enemies_in_area:
                # Show tumbling/falling effect
                ui.renderer.animate_attack_sequence(
                    unit.y, unit.x,
                    fall_animation,
                    10,  # Red color showing damage/distress
                    0.10  # Duration
                )
            
            # Show furniture revaluation effect simultaneously
            if other_furniture:
                for pos in other_furniture:
                    # Furniture gets jostled and revalued as everything shifts
                    revalue_animation = ['?', '$', '*']
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        revalue_animation,
                        3,  # Yellow/green for revaluation
                        0.10  # Same duration as falling
                    )

        return True