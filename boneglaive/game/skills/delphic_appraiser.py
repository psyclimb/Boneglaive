#!/usr/bin/env python3
"""
Skills specific to the DELPHIC_APPRAISER unit type.
This module contains all passive and active abilities for DELPHIC_APPRAISER units.
"""

try:
    import curses
except ImportError:
    curses = None
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
    Perceives the 'astral value' of furniture terrain and grants team-wide bonuses.
    With upgrade: Enemy units are assigned astral values and treated as furniture.
    """

    def __init__(self):
        super().__init__(
            name="Valuation Oracle",
            key="V",
            description="Perceives the 'astral value' of furniture terrain (1-9, can inflate to 14). Allies adjacent to furniture with astral value 9 or greater gain +1 to defense and attack range. With upgrade: Enemy units are assigned astral values (1-9) and treated as furniture."
        )

    def _get_enemy_astral_value(self, game: 'Game', appraiser_player: int, enemy_unit: 'Unit') -> Optional[int]:
        """Get or assign astral value for an enemy unit."""
        if not hasattr(game, 'enemy_astral_values'):
            game.enemy_astral_values = {}

        key = (appraiser_player, id(enemy_unit))
        if key not in game.enemy_astral_values:
            # Assign new random value (1-9)
            game.enemy_astral_values[key] = random.randint(1, 9)

        return game.enemy_astral_values[key]

    def _set_enemy_astral_value(self, game: 'Game', appraiser_player: int, enemy_unit: 'Unit', value: int):
        """Set astral value for an enemy unit."""
        if not hasattr(game, 'enemy_astral_values'):
            game.enemy_astral_values = {}

        key = (appraiser_player, id(enemy_unit))
        game.enemy_astral_values[key] = value

    def _is_furniture_or_appraised_enemy(self, game: 'Game', y: int, x: int, appraiser_player: int, valuation_upgraded: bool) -> bool:
        """Check if position has furniture or an appraised enemy (with upgrade)."""
        # Check for actual furniture
        if game.map.is_furniture(y, x):
            return True

        # With upgrade, check for enemy units
        if valuation_upgraded:
            unit = game.get_unit_at(y, x)
            if unit and unit.is_alive() and unit.player != appraiser_player:
                return True

        return False

    def _get_astral_value_at_position(self, game: 'Game', y: int, x: int, appraiser_player: int, valuation_upgraded: bool) -> Optional[int]:
        """Get astral value at position (furniture or appraised enemy)."""
        # Check for furniture first
        if game.map.is_furniture(y, x):
            return game.map.get_cosmic_value(y, x, player=appraiser_player, game=game)

        # With upgrade, check for enemy units
        if valuation_upgraded:
            unit = game.get_unit_at(y, x)
            if unit and unit.is_alive() and unit.player != appraiser_player:
                return self._get_enemy_astral_value(game, appraiser_player, unit)

        return None
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """
        Apply the Valuation Oracle passive effect.
        Grants bonuses to ALL allies adjacent to furniture with astral value >= 9.
        With Market Futures upgrade: Imbued furniture also provides bonuses to adjacent allies.
        With Valuation Oracle upgrade: Enemy units are assigned astral values and treated as furniture.
        """
        if not game:
            return

        # Check if we're in setup phase - if so, delay astral value perception until game starts
        if hasattr(game, 'setup_phase') and game.setup_phase:
            # During setup, don't perceive astral values yet to prevent revealing DELPHIC_APPRAISER presence
            # Cosmic values will be perceived when the game starts (see engine.py setup completion)
            return

        # Check if upgrades are active
        from boneglaive.game.upgrades import UpgradeManager
        market_futures_upgraded = UpgradeManager.is_skill_upgraded(user, "Market Futures")
        valuation_oracle_upgraded = UpgradeManager.is_skill_upgraded(user, "Valuation Oracle")

        # Process ALL ally units (including the DELPHIC_APPRAISER)
        for ally in game.units:
            if not ally.is_alive() or ally.player != user.player:
                continue

            # Check if this ally is adjacent to any high-value furniture (>= 9), imbued furniture, or appraised enemy
            adjacent_to_high_value = False

            # Check all eight adjacent positions
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue  # Skip the unit's own position

                    y, x = ally.y + dy, ally.x + dx

                    # Skip if out of bounds
                    if not game.is_valid_position(y, x):
                        continue

                    # Check if the tile is furniture or appraised enemy
                    if game.map.is_furniture(y, x):
                        # Get astral value with the appraiser's player
                        cosmic_value = game.map.get_cosmic_value(y, x, player=user.player, game=game)

                        # Check if astral value is 9 or greater
                        if cosmic_value is not None and cosmic_value >= 9:
                            adjacent_to_high_value = True
                            break

                    # With Valuation Oracle upgrade: Check for appraised enemies
                    if valuation_oracle_upgraded:
                        enemy_unit = game.get_unit_at(y, x)
                        if enemy_unit and enemy_unit.is_alive() and enemy_unit.player != user.player:
                            # Get or assign enemy astral value
                            enemy_value = self._get_enemy_astral_value(game, user.player, enemy_unit)
                            if enemy_value is not None and enemy_value >= 9:
                                adjacent_to_high_value = True
                                break

                if adjacent_to_high_value:
                    break

            # Apply or remove bonuses based on adjacency to high-value furniture/enemies
            if adjacent_to_high_value:
                # If this is the first time applying the bonus to this ally, log a message
                if not hasattr(ally, 'valuation_oracle_buff') or not ally.valuation_oracle_buff:
                    message_log.add_message(
                        f"{ally.get_display_name()} is empowered by the DELPHIC APPRAISER's valuation",
                        MessageType.ABILITY,
                        player=ally.player
                    )
                    # Mark for initial application animation
                    ally.valuation_oracle_initial_application = True

                # Set status effect flag and duration (lasts indefinitely while adjacent)
                ally.valuation_oracle_buff = True
                ally.valuation_oracle_duration = 999  # High value, will be refreshed each turn while adjacent

                # Apply bonuses to defense and attack range using *_bonus attributes
                ally.defense_bonus = 1
                ally.attack_range_bonus = 1
            else:
                # Before removing, check if unit is adjacent to imbued furniture/enemy (Market Futures upgrade)
                # These buffs are managed by update_anchor_status_effects(), so don't remove them here
                adjacent_to_imbued = False
                if market_futures_upgraded:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue

                            check_y, check_x = ally.y + dy, ally.x + dx
                            if not game.is_valid_position(check_y, check_x):
                                continue

                            # Check for imbued furniture anchor
                            if hasattr(game, 'teleport_anchors') and (check_y, check_x) in game.teleport_anchors:
                                anchor = game.teleport_anchors[(check_y, check_x)]
                                if anchor.get('imbued', False) and anchor['creator'].player == user.player:
                                    adjacent_to_imbued = True
                                    break

                            # Check for imbued enemy
                            enemy_unit = game.get_unit_at(check_y, check_x)
                            if (enemy_unit and enemy_unit.is_alive() and
                                enemy_unit.player != user.player and
                                hasattr(enemy_unit, 'status_imbued') and
                                enemy_unit.status_imbued and
                                enemy_unit.status_imbued_player == user.player):
                                adjacent_to_imbued = True
                                break

                        if adjacent_to_imbued:
                            break

                # Only remove the buff if not adjacent to any imbued furniture/enemy
                if not adjacent_to_imbued:
                    if hasattr(ally, 'valuation_oracle_buff') and ally.valuation_oracle_buff:
                        ally.valuation_oracle_buff = False
                        ally.valuation_oracle_duration = 0
                        # Remove bonuses
                        ally.defense_bonus = 0
                        ally.attack_range_bonus = 0


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
            cooldown=5,
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

        # Target must be a furniture piece OR (with upgrade) an enemy unit
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        is_furniture = terrain in [TerrainType.LECTERN, TerrainType.COAT_RACK,
                         TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF,
                         TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE,
                         TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                         TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                         TerrainType.COT, TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN,
                         TerrainType.POTPOURRI_BOWL]

        # If not furniture, check if it's an enemy (with Valuation Oracle upgrade)
        is_valid_enemy = False
        if not is_furniture:
            from boneglaive.game.upgrades import UpgradeManager
            if UpgradeManager.is_skill_upgraded(user, "Valuation Oracle"):
                enemy_unit = game.get_unit_at(target_pos[0], target_pos[1])
                if enemy_unit and enemy_unit.is_alive() and enemy_unit.player != user.player:
                    is_valid_enemy = True

        # Must be either furniture or valid enemy
        if not is_furniture and not is_valid_enemy:
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

        # Get the target name for the message (enemy unit or furniture)
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if target_unit and target_unit.is_alive() and target_unit.player != user.player:
            # Targeting an enemy unit
            target_name = target_unit.get_display_name()
        else:
            # Targeting furniture
            target_terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
            target_name = self._get_furniture_name(target_terrain)

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} prepares to infuse the {target_name} with Market Futures",
            MessageType.ABILITY,
            player=user.player
        )

        # Set cooldown
        self.current_cooldown = self.cooldown

        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Market Futures skill on a furniture piece or enemy unit."""

        # Clear the market futures indicator when skill is executed
        user.market_futures_indicator = None

        # Check if target is an enemy unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        is_enemy_target = target_unit and target_unit.is_alive() and target_unit.player != user.player

        if is_enemy_target:
            # Check if target is immune to status effects (GRAYMAN with Stasiality)
            if target_unit.is_immune_to_effects():
                # Log immunity message
                message_log.add_message(
                    f"{target_unit.get_display_name()} is immune to Market Futures due to Stasiality",
                    MessageType.ABILITY,
                    player=user.player
                )
            else:
                # Apply Imbued status effect to enemy
                # Get or assign enemy astral value
                if hasattr(user, 'passive_skill') and user.passive_skill:
                    cosmic_value = user.passive_skill._get_enemy_astral_value(game, user.player, target_unit)
                else:
                    cosmic_value = random.randint(1, 9)

                # Apply imbued status effect
                target_unit.status_imbued = True
                target_unit.status_imbued_duration = 7
                target_unit.status_imbued_player = user.player
                target_unit.status_imbued_cosmic_value = cosmic_value

                # Log the skill activation (WARNING type for yellow debuff color)
                message_log.add_message(
                    f"{user.get_display_name()} imbues {target_unit.get_display_name()} with Market Futures",
                    MessageType.WARNING,
                    player=target_unit.player
                )
        else:
            # Target is furniture - create normal anchor
            # Get the astral value (will be generated if it doesn't exist)
            cosmic_value = game.map.get_cosmic_value(target_pos[0], target_pos[1], player=user.player, game=game)
            if cosmic_value is None:
                cosmic_value = random.randint(1, 9)  # Fallback

            # Get the furniture name for messages
            target_terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
            furniture_name = self._get_furniture_name(target_terrain)

            # Create teleportation anchor
            if not hasattr(game, 'teleport_anchors'):
                game.teleport_anchors = {}

            game.teleport_anchors[target_pos] = {
                'creator': user,
                'cosmic_value': cosmic_value,
                'active': True,
                'imbued': True,  # Mark as imbued for special rendering
                'duration': 3  # Market Futures anchor lasts 3 turns
            }

            # Log the skill activation
            message_log.add_message(
                f"{user.get_display_name()} infuses the {furniture_name} with Market Futures",
                MessageType.ABILITY,
                player=user.player
            )

        # Update anchor status effects for all units
        game.update_anchor_status_effects()
        
        # Play Market Futures animation sequence
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the pre-defined market futures animation sequence
            market_futures_animation = ui.asset_manager.get_skill_animation_sequence('market_futures')
            if not market_futures_animation:
                # Fallback animation showing the complete progression
                market_futures_animation = ['A', '|', '-', '#', '\\', '|', '/', '-', '#', '&', '%', '@', '$', '.', '*', '+', '*', '.', '~', '-', '=', 'T', '@']

            # Play the complete Market Futures animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                market_futures_animation,
                6,  # Cyan/blue color for market analysis
                0.1  # Duration per frame
            )

        # If Market Futures upgrade is active, immediately apply Valuation Oracle to adjacent allies
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Market Futures"):
            # Apply Valuation Oracle passive to update bonuses for adjacent allies
            if hasattr(user, 'passive_skill') and user.passive_skill:
                user.passive_skill.apply_passive(user, game, ui)

        return True
        
    def activate_teleport(self, ally: 'Unit', anchor_pos: tuple, destination: tuple, game: 'Game', ui=None) -> bool:
        """Activate the teleportation anchor for an ally (furniture or imbued enemy)."""

        # Check if anchor_pos is a furniture anchor
        anchor = None
        cosmic_value = None
        imbued_unit = None

        if hasattr(game, 'teleport_anchors') and anchor_pos in game.teleport_anchors:
            anchor = game.teleport_anchors[anchor_pos]
            if not anchor['active']:
                return False

            # Check if the ally is on the same team as the anchor creator
            if ally.player != anchor['creator'].player:
                return False

            cosmic_value = anchor['cosmic_value']
        else:
            # Check if anchor_pos has an imbued enemy unit
            imbued_unit = game.get_unit_at(anchor_pos[0], anchor_pos[1])
            if not (imbued_unit and
                    imbued_unit.is_alive() and
                    hasattr(imbued_unit, 'status_imbued') and
                    imbued_unit.status_imbued and
                    imbued_unit.status_imbued_player == ally.player):
                return False

            cosmic_value = imbued_unit.status_imbued_cosmic_value

        # Validate destination
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

        # Check destination range based on cosmic value
        distance = game.chess_distance(anchor_pos[0], anchor_pos[1], destination[0], destination[1])
        if distance > cosmic_value:
            return False
            
        # Execute teleport
        old_pos = (ally.y, ally.x)
        # Teleport atomically: remove from old position, update coordinates, add to new position
        # This avoids intermediate position checks that would block the teleport
        final_unit = game.get_unit_at(destination[0], destination[1])
        if final_unit is not None and final_unit != ally:
            # Target occupied (should have been caught by validation, but check anyway)
            from boneglaive.utils.debug import logger
            logger.error(f"MARKET FUTURES BLOCKED: {ally.get_display_name()}'s teleport to {destination} blocked - position occupied by {final_unit.get_display_name()}")
            message_log.add_message(
                f"{ally.get_display_name()}'s Market Futures teleport blocked - position occupied!",
                MessageType.WARNING,
                player=ally.player
            )
            return False

        # Teleport atomically: remove from old position, update coordinates, add to new position
        old_y, old_x = ally.y, ally.x
        if (old_y, old_x) in game.unit_grid:
            del game.unit_grid[(old_y, old_x)]

        # Set private attributes directly (bypass property setters)
        ally._y = destination[0]
        ally._x = destination[1]

        # Add to new position in grid
        game.unit_grid[(destination[0], destination[1])] = ally

        # Trigger trap checks if unit was trapped or is a foreman
        from boneglaive.utils.constants import UnitType
        if hasattr(ally, 'trapped_by') and ally.trapped_by is not None:
            game._check_position_change_trap_release(ally, old_y, old_x)
        if ally.type == UnitType.MANDIBLE_FOREMAN:
            game._check_position_change_trap_release(ally, old_y, old_x)

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
            # Always apply the investment effect regardless of astral value
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
                teleport_animation = ['$', '^', '>', 'v', 'v', '*', 'A']
                
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
        if hasattr(game, 'teleport_anchors') and anchor_pos in game.teleport_anchors:
            # Furniture anchor - deactivate it
            game.teleport_anchors[anchor_pos]['active'] = False
            game.teleport_anchors[anchor_pos]['imbued'] = False  # Remove imbued status for rendering
        # Note: Imbued enemies don't need deactivation - they remain imbued until duration expires

        # Update anchor status effects for all units after use
        game.update_anchor_status_effects()
        
        return True
    
    def _get_furniture_name(self, terrain_type) -> str:
        """Convert TerrainType enum to readable furniture name."""
        terrain_names = {
            TerrainType.LECTERN: "Lectern",
            TerrainType.COAT_RACK: "Coat Rack", 
            TerrainType.OTTOMAN: "Ottoman",
            TerrainType.CONSOLE: "Console",
            TerrainType.CURIOSITY_SHELF: "Curiosity Shelf",
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
            TerrainType.CONVEYOR: "Conveyor Belt",
            TerrainType.MINI_PUMPKIN: "Mini Pumpkin",
            TerrainType.POTPOURRI_BOWL: "Potpourri Bowl"
        }
        return terrain_names.get(terrain_type, "Radio Console")


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
                        "damage equal to total astral value of furniture within 2 tiles. "
                        "Each damage tick inflates astral values of nearby furniture by +1 "
                        "and prevents all healing for the cursed unit."),
            target_type=TargetType.ENEMY,
            cooldown=3,
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

        # Check if Valuation Oracle upgrade is active
        from boneglaive.game.upgrades import UpgradeManager
        valuation_oracle_upgraded = UpgradeManager.is_skill_upgraded(user, "Valuation Oracle")

        # Find nearby furniture and their astral values
        # With upgrade, also include appraised enemies
        nearby_furniture = []
        nearby_appraised_enemies = []
        for y in range(max(0, target_pos[0] - 2), min(game.map.height, target_pos[0] + 3)):
            for x in range(max(0, target_pos[1] - 2), min(game.map.width, target_pos[1] + 3)):
                terrain = game.map.get_terrain_at(y, x)
                if terrain in [TerrainType.LECTERN, TerrainType.COAT_RACK,
                             TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF,
                             TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE,
                             TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                             TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                             TerrainType.COT, TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN,
                         TerrainType.POTPOURRI_BOWL]:
                    nearby_furniture.append((y, x))

                    # Get astral value (will be generated if it doesn't exist yet)
                    game.map.get_cosmic_value(y, x, player=user.player, game=game)

                # With Valuation Oracle upgrade: Check for appraised enemies (exclude the target)
                if valuation_oracle_upgraded and (y, x) != target_pos:
                    enemy_unit = game.get_unit_at(y, x)
                    if enemy_unit and enemy_unit.is_alive() and enemy_unit.player != user.player:
                        nearby_appraised_enemies.append(enemy_unit)

        # Calculate average astral value of nearby furniture AND appraised enemies
        average_value = 0
        cosmic_values = []

        # Add furniture values
        for pos in nearby_furniture:
            value = game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)
            if value is not None:
                cosmic_values.append(value)

        # Add appraised enemy values
        if hasattr(user, 'passive_skill') and user.passive_skill:
            for enemy_unit in nearby_appraised_enemies:
                enemy_value = user.passive_skill._get_enemy_astral_value(game, user.player, enemy_unit)
                if enemy_value is not None:
                    cosmic_values.append(enemy_value)

        if cosmic_values:
            # Calculate the average, rounded up
            import math
            average_value = math.ceil(sum(cosmic_values) / len(cosmic_values))

            # Ensure average value is within valid range
            average_value = max(1, min(14, average_value))

        # Apply DOT effect to the target enemy, if they're not immune
        dot_duration = average_value  # Duration equals the average value

        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} opens a twisted auction for {target_unit.get_display_name()}",
            MessageType.ABILITY,
            player=user.player
        )

        # Special message for maximum duration (14 turns)
        if dot_duration == 14:
            message_log.add_message(
                f"{user.get_display_name()} rolls deftly!",
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

                # Store initial HP, duration, caster, and furniture positions for upgrade check
                target_unit.auction_curse_initial_hp = target_unit.hp
                target_unit.auction_curse_applied_duration = dot_duration
                target_unit.auction_curse_caster = user
                target_unit.auction_curse_furniture_positions = nearby_furniture.copy() if nearby_furniture else []

                # Log the DOT application
                message_log.add_message(
                    f"{target_unit.get_display_name()} has his vitality stunted",
                    MessageType.WARNING,
                    player=target_unit.player
                )

        # Play Auction Curse animation - astral auctioneers appear at furniture AND appraised enemy locations
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Combine furniture and appraised enemy positions for animation
            auctioneer_positions = nearby_furniture.copy() if nearby_furniture else []

            # With Valuation Oracle upgrade: Add appraised enemy positions
            if valuation_oracle_upgraded and nearby_appraised_enemies:
                for enemy_unit in nearby_appraised_enemies:
                    auctioneer_positions.append((enemy_unit.y, enemy_unit.x))

            # Step 1: Podiums and astral auctioneers ascend at all auctioneer locations
            if auctioneer_positions:
                podium_ascension = ['.', '_', '=', 'i', 'I']  # Ground → podium → auctioneer rises
                for pos in auctioneer_positions:
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        podium_ascension,
                        7,  # White/light color for astral beings
                        0.18  # Duration per frame
                    )
                    sleep_with_animation_speed(0.03)  # Slight stagger between locations

                sleep_with_animation_speed(0.15)  # Pause between major phases

                # Step 2: Astral auctioneers raise bidding paddles
                paddle_raising = ['I', 'Y', 'T']  # Auctioneer → raising paddle → paddle fully raised
                for pos in auctioneer_positions:
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        paddle_raising,
                        7,  # Yellow for astral energy
                        0.15  # Duration per frame
                    )
                    sleep_with_animation_speed(0.03)  # Slight stagger

                sleep_with_animation_speed(0.2)  # Dramatic pause before curse

                # Step 3: Twisted curse descends from all auctioneers to converge on victim
                curse_descent = ['~', '*', 'v', 'V']  # Curse energy → swirling → descending → impact

                # First show curse energy forming at each auctioneer
                for pos in auctioneer_positions:
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        ['~', '*'],  # Just the initial curse energy
                        19,  # Red text for malevolent energy
                        0.12
                    )

                # Then show curse converging on the target
                ui.renderer.animate_attack_sequence(
                    target_pos[0], target_pos[1],
                    ['v', 'V', '@', '&'],  # Curse descends → impacts → victim cursed → ongoing effect
                    19,  # Red text for curse affliction
                    0.2  # Duration per frame
                )

            else:
                # Fallback if no furniture/enemies nearby - simple curse effect
                simple_curse = ['~', '*', 'v', '@']
                ui.renderer.animate_attack_sequence(
                    target_pos[0], target_pos[1],
                    simple_curse,
                    19,  # Red text color
                    0.2
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
            description="Dramatically reappraises a furniture piece as cosmically worthless, creating a 7×7 reality distortion. Sets target furniture to value 1, deals damage that bypasses defense and pulls enemies toward the center based on move values. All other furniture has astral values rerolled.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=3,
            area=3  # 7×7 area (radius 3)
        )
    
    def _get_furniture_name(self, terrain_type) -> str:
        """Convert TerrainType enum to readable furniture name."""
        terrain_names = {
            TerrainType.LECTERN: "Lectern",
            TerrainType.COAT_RACK: "Coat Rack", 
            TerrainType.OTTOMAN: "Ottoman",
            TerrainType.CONSOLE: "Console",
            TerrainType.CURIOSITY_SHELF: "Curiosity Shelf",
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
            TerrainType.CONVEYOR: "Conveyor Belt",
            TerrainType.MINI_PUMPKIN: "Mini Pumpkin",
            TerrainType.POTPOURRI_BOWL: "Potpourri Bowl"
        }
        return terrain_names.get(terrain_type, "Radio Console")

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

        # Target must be a furniture piece OR (with upgrade) an enemy unit
        terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        is_furniture = terrain in [TerrainType.LECTERN, TerrainType.COAT_RACK,
                         TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF,
                         TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE,
                         TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                         TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                         TerrainType.COT, TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN,
                         TerrainType.POTPOURRI_BOWL]

        # If not furniture, check if it's an enemy (with Valuation Oracle upgrade)
        is_valid_enemy = False
        if not is_furniture:
            from boneglaive.game.upgrades import UpgradeManager
            if UpgradeManager.is_skill_upgraded(user, "Valuation Oracle"):
                enemy_unit = game.get_unit_at(target_pos[0], target_pos[1])
                if enemy_unit and enemy_unit.is_alive() and enemy_unit.player != user.player:
                    is_valid_enemy = True

        # Must be either furniture or valid enemy
        if not is_furniture and not is_valid_enemy:
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
        """Execute the Divine Depreciation skill on a furniture piece or enemy."""
        # Clear the divine depreciation indicator when skill is executed
        user.divine_depreciation_indicator = None

        # Check if target is furniture or enemy
        target_terrain = game.map.get_terrain_at(target_pos[0], target_pos[1])
        is_furniture = game.map.is_furniture(target_pos[0], target_pos[1])
        target_enemy = game.get_unit_at(target_pos[0], target_pos[1]) if not is_furniture else None

        # Get the astral value of the target
        if is_furniture:
            original_cosmic_value = game.map.get_cosmic_value(target_pos[0], target_pos[1], player=user.player, game=game)
            if original_cosmic_value is None:
                original_cosmic_value = random.randint(1, 9)  # Fallback
            furniture_name = self._get_furniture_name(target_terrain)
            target_name = furniture_name
        else:
            # Target is an enemy - get their astral value
            if target_enemy is None:
                return False  # Target moved or died before execution
            if hasattr(user, 'passive_skill') and user.passive_skill:
                original_cosmic_value = user.passive_skill._get_enemy_astral_value(game, user.player, target_enemy)
            else:
                original_cosmic_value = random.randint(1, 9)  # Fallback
            target_name = target_enemy.get_display_name()
            furniture_name = target_name  # Use for messages

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

        # Check if Valuation Oracle upgrade is active
        from boneglaive.game.upgrades import UpgradeManager
        valuation_oracle_upgraded = UpgradeManager.is_skill_upgraded(user, "Valuation Oracle")

        # Collect furniture in the area (excluding the target)
        # With upgrade, also collect appraised enemies
        other_furniture = []
        appraised_enemies = []  # Track enemies separately for rerolling
        for pos in affected_area:
            if pos != target_pos:  # Skip the target furniture
                terrain = game.map.get_terrain_at(pos[0], pos[1])
                if terrain in [TerrainType.LECTERN, TerrainType.COAT_RACK,
                             TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF,
                             TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE,
                             TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                             TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                             TerrainType.COT, TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN,
                         TerrainType.POTPOURRI_BOWL]:
                    other_furniture.append(pos)
                    # Ensure astral value exists for all furniture
                    game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)

                # With Valuation Oracle upgrade: Check for appraised enemies
                if valuation_oracle_upgraded:
                    enemy_unit = game.get_unit_at(pos[0], pos[1])
                    if enemy_unit and enemy_unit.is_alive() and enemy_unit.player != user.player:
                        appraised_enemies.append((pos, enemy_unit))

        # Calculate average astral value of other furniture AND appraised enemies (rounded up)
        avg_cosmic_value = 1  # Default if no other furniture
        total_value = 0
        count = 0

        # Add furniture values
        for pos in other_furniture:
            value = game.map.get_cosmic_value(pos[0], pos[1], player=user.player, game=game)
            if value is not None:
                total_value += value
                count += 1

        # Add appraised enemy values
        if hasattr(user, 'passive_skill') and user.passive_skill:
            for pos, enemy_unit in appraised_enemies:
                enemy_value = user.passive_skill._get_enemy_astral_value(game, user.player, enemy_unit)
                if enemy_value is not None:
                    total_value += enemy_value
                    count += 1

        if count > 0:
            import math
            avg_cosmic_value = math.ceil(total_value / count)

        # Store the original astral value BEFORE setting it to 1
        original_target_cosmic_value = original_cosmic_value

        # Set target's astral value to 1 (furniture or enemy)
        if is_furniture:
            game.map.set_cosmic_value(target_pos[0], target_pos[1], 1, user.player)
        else:
            # Set enemy's astral value to 1
            if hasattr(user, 'passive_skill') and user.passive_skill:
                user.passive_skill._set_enemy_astral_value(game, user.player, target_enemy, 1)

        # Calculate effect value based on the difference between average value and target value (now 1)
        effect_value = max(1, avg_cosmic_value - 1)  # Ensure at least 1 damage/healing

        # Special message for maximum damage (8 damage)
        if effect_value == 8:
            message_log.add_message(
                f"{user.get_display_name()} rolls deftly!",
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
            'original_cosmic_value': original_target_cosmic_value,  # Store original for reference
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

        # Store damage and pull calculations for later application (after animation)
        # Calculate pull distance PER UNIT based on original astral value
        effects_to_apply = []
        for unit in enemies_in_area:
            # Calculate pull effect (move toward center)
            start_pos = (unit.y, unit.x)
            target_center = target_pos

            # Calculate direction vector from unit to center
            dir_y = target_center[0] - unit.y
            dir_x = target_center[1] - unit.x

            # Normalize the direction
            distance = max(1, abs(dir_y) + abs(dir_x))  # Manhattan distance

            # Calculate pull distance per unit: (original_cosmic_value - 1) - unit_move_value
            # Bigger astral values = greater pull distance
            # Units with higher move can resist pull better
            unit_move_value = unit.get_effective_stats()['move_range']
            pull_distance = max(1, (original_target_cosmic_value - 1) - unit_move_value)
            
            # Calculate how far to pull the unit (not exceeding distance to center)
            actual_pull = min(pull_distance, distance)

            # Store all effect data for this unit
            effects_to_apply.append({
                'unit': unit,
                'damage': effect_value,
                'pull_distance': actual_pull,
                'dir_y': dir_y,
                'dir_x': dir_x,
                'distance': distance
            })

        # Store rerolled values for graphical animation
        rerolled_values = {}  # {(y, x): new_value}

        # Reroll astral values for all other furniture in the AOE
        for pos in other_furniture:
            # Show flashing random numbers animation on this furniture before setting final value
            if ui and hasattr(ui, 'renderer'):
                # Create animation with random numbers cycling
                reroll_animation = [str(random.randint(1, 9)) for _ in range(12)]  # 12 frames of random numbers
                ui.renderer.animate_attack_sequence(
                    pos[0], pos[1],
                    reroll_animation,
                    7,  # Yellow/white flashing
                    0.1  # Fast flashing
                )

            # Generate a new random astral value (1-9) for this player
            new_value = random.randint(1, 9)
            game.map.set_cosmic_value(pos[0], pos[1], new_value, user.player)
            rerolled_values[pos] = new_value

        # With Valuation Oracle upgrade: Reroll astral values for appraised enemies
        if hasattr(user, 'passive_skill') and user.passive_skill and appraised_enemies:
            for pos, enemy_unit in appraised_enemies:
                # Show flashing random numbers animation on enemy
                if ui and hasattr(ui, 'renderer'):
                    reroll_animation = [str(random.randint(1, 9)) for _ in range(12)]
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        reroll_animation,
                        7,  # Yellow/white flashing
                        0.1  # Fast flashing
                    )

                # Generate a new random astral value (1-9) for this enemy
                new_value = random.randint(1, 9)
                user.passive_skill._set_enemy_astral_value(game, user.player, enemy_unit, new_value)
                rerolled_values[pos] = new_value

                # If enemy is imbued, also update their imbued cosmic value
                if (hasattr(enemy_unit, 'status_imbued') and
                    enemy_unit.status_imbued and
                    enemy_unit.status_imbued_player == user.player):
                    enemy_unit.status_imbued_cosmic_value = new_value

        # Store rerolled values on user for animation to access
        user.divine_depreciation_rerolled_values = rerolled_values

        # Log the skill activation with details about the astral values
        message_log.add_message(
            f"{user.get_display_name()} casts Divine Depreciation on the {furniture_name}",
            MessageType.ABILITY,
            player=user.player
        )

        if other_furniture:
            message_log.add_message(
                f"The {furniture_name}'s value plummets, creating a cascading sinkhole",
                MessageType.ABILITY,
                player=user.player
            )

        # Play fast sinkhole animation sequence
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Step 1: Value Collapse - Show furniture's astral value plummeting
            value_collapse_animation = []
            current_value = original_cosmic_value
            while current_value > 1 and len(value_collapse_animation) < 3:  # Limit to 3 frames max
                value_collapse_animation.append(str(current_value))
                current_value = max(1, current_value - 3)  # Drop faster for shorter animation
            value_collapse_animation.append('1')  # Always end at 1
            
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                value_collapse_animation,
                7,  # White->Yellow showing instability  
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

        # Now apply damage and pull effects after animation completes
        for effect_data in effects_to_apply:
            unit = effect_data['unit']
            damage_value = effect_data['damage']
            actual_pull = effect_data['pull_distance']
            dir_y = effect_data['dir_y']
            dir_x = effect_data['dir_x']
            distance = effect_data['distance']
            
            # Deal damage based on astral value difference, bypassing defense
            old_hp = unit.hp
            
            # Use deal_damage to apply damage directly (bypassing defense)
            actual_damage = unit.deal_damage(damage_value)

            message_log.add_combat_message(
                attacker_name=user.get_display_name(),
                target_name=unit.get_display_name(),
                damage=actual_damage,
                ability="Divine Depreciation",
                attacker_player=user.player,
                target_player=unit.player
            )

            # Show damage number if UI is available (ASCII mode only)
            if ui and hasattr(ui, 'renderer') and hasattr(ui.renderer, 'draw_damage_text') and actual_damage > 0:
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

            # Apply pull effects
            if actual_pull > 0 and distance > 0:
                # Check if unit is immune to displacement effects (GRAYMAN with Stasiality)
                if unit.is_immune_to_effects():
                    message_log.add_message(
                        f"{unit.get_display_name()} is immune to Divine Depreciation's pull effect due to Stasiality",
                        MessageType.ABILITY,
                        player=unit.player  # Use unit's player color for correct display
                    )
                else:
                    # Store original position before movement
                    original_y, original_x = unit.y, unit.x
                    
                    # Use comprehensive pull algorithm for reliable movement toward center
                    final_position = self._find_best_pull_path(unit, target_pos, actual_pull, game)
                    
                    if final_position and (final_position[0] != unit.y or final_position[1] != unit.x):
                        # Calculate how far the unit actually moved
                        steps_taken = abs(final_position[0] - unit.y) + abs(final_position[1] - unit.x)
                        new_y, new_x = final_position
                    else:
                        # No valid path found
                        steps_taken = 0
                        new_y, new_x = unit.y, unit.x

                    # Update unit position if it moved
                    if steps_taken > 0:
                        # Use atomic positioning to prevent collisions
                        if not unit.set_position_atomic(new_y, new_x):
                            from boneglaive.utils.debug import logger
                            logger.error(f"PARALLAX PULL BLOCKED: {unit.get_display_name()}'s pull to ({new_y}, {new_x}) blocked by collision")
                            message_log.add_message(
                                f"{unit.get_display_name()}'s Parallax pull blocked - position occupied!",
                                MessageType.WARNING,
                                player=user.player
                            )
                        else:
                            message_log.add_message(
                                f"{unit.get_display_name()} is pulled {steps_taken} spaces from ({original_y}, {original_x}) to ({new_y}, {new_x}) by the {furniture_name.lower()}'s reality distortion",
                                MessageType.ABILITY,
                                player=user.player
                            )

            # Handle unit death properly through centralized system
            if unit.hp <= 0:
                # Use centralized death handling to ensure all systems (like DOMINION) are notified
                game.handle_unit_death(unit, user, cause="divine_depreciation", ui=ui)

        # Check for Divine Depreciation upgrade - transform into Deft(?) Reroll
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Divine Depreciation"):
            # Replace Divine Depreciation with Deft(?) Reroll in skill list
            for i, skill in enumerate(user.active_skills):
                if skill.name == "Divine Depreciation":
                    user.active_skills[i] = DeftRerollSkill()
                    user.deft_reroll_available = True
                    user.deft_reroll_turn_expires = game.turn + 2  # Available for 1 full turn
                    user.deft_reroll_distortion_id = distortion_id

                    message_log.add_message(
                        f"{user.get_display_name()}'s Divine Depreciation transforms into Deft(?) Reroll",
                        MessageType.ABILITY,
                        player=user.player
                    )
                    break

        return True

    def _find_best_pull_path(self, unit, center_pos, pull_distance, game):
        """
        Find the best path to pull a unit toward the center using comprehensive search.
        
        Args:
            unit: The unit to be pulled
            center_pos: (y, x) tuple of the pull center
            pull_distance: Maximum distance to pull the unit
            game: Game instance for checking positions
            
        Returns:
            (y, x) tuple of final position, or None if no movement possible
        """
        current_y, current_x = unit.y, unit.x
        center_y, center_x = center_pos
        
        # Try to move step by step toward center, using best available position each step
        for step in range(pull_distance):
            best_position = self._find_best_adjacent_position_toward_center(
                current_y, current_x, center_y, center_x, game
            )
            
            if best_position:
                current_y, current_x = best_position
            else:
                # No more valid moves possible
                break
        
        return (current_y, current_x)
    
    def _find_best_adjacent_position_toward_center(self, unit_y, unit_x, center_y, center_x, game):
        """
        Find the best adjacent position that moves the unit closer to center.
        
        Args:
            unit_y, unit_x: Current unit position
            center_y, center_x: Target center position
            game: Game instance for validation
            
        Returns:
            (y, x) tuple of best adjacent position, or None if no valid moves
        """
        # All 8 possible adjacent directions
        directions = [
            (-1, -1), (-1, 0), (-1, 1),  # up-left, up, up-right
            ( 0, -1),          ( 0, 1),  # left, right
            ( 1, -1), ( 1, 0), ( 1, 1)   # down-left, down, down-right
        ]
        
        current_distance = abs(unit_y - center_y) + abs(unit_x - center_x)
        candidates = []
        
        # Check each adjacent position
        for dy, dx in directions:
            new_y = unit_y + dy
            new_x = unit_x + dx
            
            # Check if position is valid
            if (new_y < 0 or new_y >= game.map.height or 
                new_x < 0 or new_x >= game.map.width):
                continue  # Out of bounds
                
            # Check if terrain is passable
            if not game.map.is_passable(new_y, new_x):
                continue  # Impassable terrain
                
            # Check if position is already occupied by another unit
            if game.get_unit_at(new_y, new_x):
                continue  # Occupied
            
            # Calculate distance to center from this position
            distance_to_center = abs(new_y - center_y) + abs(new_x - center_x)
            
            # Only consider positions that get us closer to center
            if distance_to_center < current_distance:
                candidates.append(((new_y, new_x), distance_to_center))
        
        if not candidates:
            return None  # No valid positions that move closer to center
            
        # Sort by distance to center (closer is better, so smaller distance first)
        candidates.sort(key=lambda x: x[1])
        
        # Return the position closest to center
        return candidates[0][0]


class ParallaxSkill(ActiveSkill):
    """
    Dynamic skill that appears when a unit is adjacent to a Market Futures anchor.
    Allows allies to activate teleportation through the anchor.
    """

    def __init__(self):
        super().__init__(
            name="Parallax",
            key="P",
            description="Activate Market Futures teleportation. Select a destination within range of the nearby anchor. Gain maturing investment: +1 ATK (turn 1), +2 ATK (turn 2), +3 ATK (turn 3) with +1 Range for all 3 turns.",
            target_type=TargetType.AREA,
            cooldown=0,  # No cooldown, availability controlled by can_use_anchor flag
            range_=1  # Default range, overridden by get_skill_range()
        )

    def get_skill_range(self, user: 'Unit', game: Optional['Game'] = None) -> int:
        """Get dynamic range based on adjacent anchor's cosmic value (1-9)."""
        if not game or not hasattr(user, 'can_use_anchor') or not user.can_use_anchor:
            return 1  # Default if no anchor

        # Find adjacent anchor
        anchor_pos, anchor = self._find_adjacent_anchor(user, game)
        if anchor_pos and anchor:
            return anchor['cosmic_value']  # Range 1-9 based on furniture's astral value

        return 1  # Fallback

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Parallax can be used (unit must be adjacent to an active anchor)."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Must have can_use_anchor flag set (adjacency checked by engine)
        if not hasattr(user, 'can_use_anchor') or not user.can_use_anchor:
            return False

        # Find the anchor we're adjacent to
        anchor_pos, anchor = self._find_adjacent_anchor(user, game)
        if not anchor_pos or not anchor:
            return False

        # Check if target destination is valid
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Check if destination is passable and empty
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # Check if destination is within anchor's cosmic value range
        cosmic_value = anchor['cosmic_value']
        distance = game.chess_distance(anchor_pos[0], anchor_pos[1], target_pos[0], target_pos[1])
        if distance > cosmic_value:
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Execute Parallax teleportation immediately (not queued like other skills)."""
        if not self.can_use(user, target_pos, game):
            return False

        # Set cooldown BEFORE execution (since this executes immediately, not queued)
        self.current_cooldown = self.cooldown

        # Parallax executes immediately, not during turn execution
        # This matches the ASCII game behavior where teleport happens instantly
        success = self.execute(user, target_pos, game, ui=None)

        if success:
            # Clear any skill selection after immediate teleport
            user.skill_target = None
            user.selected_skill = None

        return success

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Parallax teleportation."""
        # Find the anchor we're adjacent to
        anchor_pos, anchor = self._find_adjacent_anchor(user, game)
        if not anchor_pos or not anchor:
            message_log.add_message(
                f"{user.get_display_name()} cannot find a nearby locus",
                MessageType.WARNING,
                player=user.player
            )
            return False

        # Use the Market Futures skill's activate_teleport method
        # Since we're in the same file, just instantiate it directly
        market_futures = MarketFuturesSkill()
        success = market_futures.activate_teleport(
            ally=user,
            anchor_pos=anchor_pos,
            destination=target_pos,
            game=game,
            ui=ui
        )

        return success

    def _find_adjacent_anchor(self, user: 'Unit', game: 'Game') -> Tuple[Optional[tuple], Optional[dict]]:
        """
        Find the active anchor this unit is adjacent to.

        Returns:
            (anchor_pos, anchor_data) tuple, or (None, None) if not found
        """
        if not hasattr(game, 'teleport_anchors'):
            return None, None

        # Check all anchors for adjacency
        for anchor_pos, anchor in game.teleport_anchors.items():
            if not anchor['active']:
                continue

            # Check if user is adjacent to this anchor
            if (anchor['creator'].player == user.player and
                game.chess_distance(user.y, user.x, anchor_pos[0], anchor_pos[1]) <= 1):
                return anchor_pos, anchor

        return None, None


class DeftRerollSkill(ActiveSkill):
    """
    Temporary skill that replaces Divine Depreciation when upgraded.
    Instantly rerolls all furniture from the last Divine Depreciation.
    """

    def __init__(self):
        super().__init__(
            name="Deft(?) Reroll",
            key="D",
            description="Instantly reroll all furniture values in the last Divine Depreciation area.",
            target_type=TargetType.SELF,
            cooldown=0,
            range_=0
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Deft(?) Reroll can be used."""
        # Always usable when available
        if not hasattr(user, 'deft_reroll_distortion_id'):
            return False
        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Execute the skill immediately without queuing."""
        if not self.can_use(user, target_pos, game):
            return False

        # Execute immediately - get the ui from game if available
        ui = game.ui if game and hasattr(game, 'ui') else None
        self.execute(user, (user.y, user.x), game, ui)

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Reroll all furniture from the last Divine Depreciation."""
        # Get stored distortion
        if not hasattr(user, 'deft_reroll_distortion_id'):
            return False

        distortion_id = user.deft_reroll_distortion_id
        distortion = game.reality_distortions.get(distortion_id)

        if not distortion:
            return False

        # Note: Animation is handled by renderer.py for immediate execution skills

        # Check if Valuation Oracle upgrade is active
        from boneglaive.game.upgrades import UpgradeManager
        valuation_oracle_upgraded = UpgradeManager.is_skill_upgraded(user, "Valuation Oracle")

        # Get furniture list from distortion (excluding center which is fixed at 1)
        furniture_to_reroll = []
        appraised_enemies = []  # Track enemies separately for rerolling
        for pos in distortion['area']:
            if pos != distortion['center']:  # Skip center furniture/enemy
                terrain = game.map.get_terrain_at(pos[0], pos[1])
                if terrain in [TerrainType.LECTERN, TerrainType.COAT_RACK,
                             TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF,
                             TerrainType.TIFFANY_LAMP, TerrainType.EASEL, TerrainType.SCULPTURE,
                             TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
                             TerrainType.WORKBENCH, TerrainType.COUCH, TerrainType.TOOLBOX,
                             TerrainType.COT, TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN,
                             TerrainType.POTPOURRI_BOWL]:
                    furniture_to_reroll.append(pos)

                # With Valuation Oracle upgrade: Check for appraised enemies
                if valuation_oracle_upgraded:
                    enemy_unit = game.get_unit_at(pos[0], pos[1])
                    if enemy_unit and enemy_unit.is_alive() and enemy_unit.player != user.player:
                        appraised_enemies.append((pos, enemy_unit))

        # Store rerolled values for graphical animation
        rerolled_values = {}  # {(y, x): new_value}

        # Reroll animation + values for all furniture
        for pos in furniture_to_reroll:
            # Show flashing reroll animation
            if ui and hasattr(ui, 'renderer'):
                reroll_animation = [str(random.randint(1, 14)) for _ in range(12)]
                ui.renderer.animate_attack_sequence(
                    pos[0], pos[1],
                    reroll_animation,
                    7,  # Yellow/white
                    0.5
                )

            # Generate new cosmic value
            new_value = random.randint(1, 14)
            game.map.set_cosmic_value(pos[0], pos[1], new_value, user.player)
            rerolled_values[pos] = new_value

        # With Valuation Oracle upgrade: Reroll astral values for appraised enemies
        if hasattr(user, 'passive_skill') and user.passive_skill and appraised_enemies:
            for pos, enemy_unit in appraised_enemies:
                # Show flashing reroll animation
                if ui and hasattr(ui, 'renderer'):
                    reroll_animation = [str(random.randint(1, 14)) for _ in range(12)]
                    ui.renderer.animate_attack_sequence(
                        pos[0], pos[1],
                        reroll_animation,
                        7,  # Yellow/white
                        0.5
                    )

                # Generate a new random astral value (1-14) for this enemy
                new_value = random.randint(1, 14)
                user.passive_skill._set_enemy_astral_value(game, user.player, enemy_unit, new_value)
                rerolled_values[pos] = new_value

                # If enemy is imbued, also update their imbued cosmic value
                if (hasattr(enemy_unit, 'status_imbued') and
                    enemy_unit.status_imbued and
                    enemy_unit.status_imbued_player == user.player):
                    enemy_unit.status_imbued_cosmic_value = new_value

        # Store rerolled values on user for animation to access
        user.deft_reroll_values = rerolled_values

        # Redraw board
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

        message_log.add_message(
            f"{user.get_display_name()} rerolls the astral values",
            MessageType.ABILITY,
            player=user.player
        )

        # Restore Divine Depreciation
        self._restore_divine_depreciation(user)
        return True

    def _restore_divine_depreciation(self, user: 'Unit') -> None:
        """Replace Deft(?) Reroll back with Divine Depreciation."""
        for i, skill in enumerate(user.active_skills):
            if skill.name == "Deft(?) Reroll":
                divine_dep = DivineDrepreciationSkill()
                divine_dep.current_cooldown = 5  # Full cooldown + 1 penalty for using Deft(?) Reroll
                user.active_skills[i] = divine_dep

                message_log.add_message(
                    f"{user.get_display_name()}'s Deft(?) Reroll reverts to Divine Depreciation",
                    MessageType.ABILITY,
                    player=user.player
                )
                break

        # Clear tracking attributes
        user.deft_reroll_available = False
        if hasattr(user, 'deft_reroll_distortion_id'):
            delattr(user, 'deft_reroll_distortion_id')
        if hasattr(user, 'deft_reroll_turn_expires'):
            delattr(user, 'deft_reroll_turn_expires')