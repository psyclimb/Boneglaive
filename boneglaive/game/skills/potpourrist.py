#!/usr/bin/env python3
"""
Skills specific to the POTPOURRIST unit type.
This module contains all passive and active abilities for POTPOURRIST units.

The POTPOURRIST is a tank unit with potpourri-based healing and enhancement mechanics.
"""

from typing import Optional, TYPE_CHECKING, List, Tuple

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class MelangeEminence(PassiveSkill):
    """
    Passive skill for POTPOURRIST.
    Heals 1 HP every turn (2 HP while holding potpourri).
    Cannot be prevented by any effect (bypasses Auction Curse).
    """

    def __init__(self):
        super().__init__(
            name="Melange Eminence",
            key="M",
            description="Heals 1 HP every turn (2 HP while holding potpourri). Cannot be prevented by any effect."
        )
        # Track last trigger to prevent duplicate triggers for the same player
        self.last_trigger_player = None

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """Apply passive healing at start of turn."""
        if not user.is_alive():
            return

        # Check for upgrade and apply one-time max HP increase
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Melange Eminence"):
            # Check if max HP hasn't been increased yet
            if user.max_hp < 28:
                old_max_hp = user.max_hp
                user.max_hp = 28
                # Heal 4 HP immediately upon upgrade
                user._hp = min(user.max_hp, user._hp + 4)

                message_log.add_message(
                    f"{user.get_display_name()} sucks up an extra potent fume of the clovey melange",
                    MessageType.ABILITY,
                    player=user.player
                )

        # Prevent duplicate triggers when initialize_next_player_turn() is called multiple times for the same player
        # This happens in VS AI mode where the turn switch is called redundantly
        if game:
            if self.last_trigger_player == game.current_player:
                logger.debug(f"Melange Eminence already triggered for player {game.current_player}, skipping redundant call")
                return

            # Update tracking - trigger once per player switch
            self.last_trigger_player = game.current_player

        # Determine heal amount based on potpourri state
        heal_amount = 2 if user.potpourri_held else 1

        # Bypass all healing prevention by directly modifying HP
        old_hp = user._hp
        user._hp = min(user.max_hp, user._hp + heal_amount)
        actual_heal = user._hp - old_hp

        if actual_heal > 0:

            message_log.add_message(
                f"{user.get_display_name()} inhales the restorative melange and heals for #HEAL_{actual_heal}# HP",
                MessageType.ABILITY,
                player=user.player
            )


class InfuseSkill(ActiveSkill):
    """
    Active skill: INFUSE
    Creates potpourri that enhances next skill and boosts Melange Eminence.
    """

    def __init__(self):
        super().__init__(
            name="Infuse",
            key="1",
            description="Creates potpourri that enhances next skill and increases Melange Eminence to 2 HP/turn. Lasts 2 turns.",
            target_type=TargetType.SELF,
            cooldown=1,
            range_=0
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False

        # Can only use when NOT already holding potpourri
        return not user.potpourri_held

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Infuse skill for execution at the end of the turn."""
        if not self.can_use(user, target_pos, game):
            return False

        # Set the skill target (self)
        user.skill_target = (user.y, user.x)
        user.selected_skill = self

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Set cooldown
        self.current_cooldown = self.cooldown

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} begins mixing a potent blend of potpourri",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Infuse skill during the combat phase."""

        message_log.add_message(
            f"{user.get_display_name()} infuses the blend with aromatic power",
            MessageType.ABILITY,
            player=user.player
        )


        # Set potpourri held flag and duration
        user.potpourri_held = True
        user.potpourri_duration = 3  # Lasts 2 turns (decremented at start of each turn)

        return True


class DemiluneSkill(ActiveSkill):
    """
    Active skill: DEMILUNE
    Swings granite pedestal in forward arc, dealing damage and weakening enemies.
    """

    def __init__(self):
        super().__init__(
            name="Demilune",
            key="2",
            description="Swings granite pedestal in forward arc. Enemies deal half damage to POTPOURRIST for 2 turns. Enhanced: +1 damage and extends Lunacy to 3 turns.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=1
        )

    def _get_arc_tiles(self, user_y: int, user_x: int, target_y: int, target_x: int) -> List[Tuple[int, int]]:
        """Get 5 tiles in forward arc based on target direction."""
        # The arc pattern is always: 3 tiles in forward direction + 2 tiles on the sides
        # Example targeting north: NW, N, NE (forward) + W, E (sides)

        tiles = []

        # Determine forward direction from target
        dy = target_y - user_y
        dx = target_x - user_x

        # Add forward 3 tiles and perpendicular side 2 tiles based on direction
        if abs(dy) >= abs(dx):  # Vertical movement dominant
            if dy < 0:  # Target above - forward is north
                # Forward tiles: NW, N, NE
                tiles.append((user_y - 1, user_x - 1))
                tiles.append((user_y - 1, user_x))
                tiles.append((user_y - 1, user_x + 1))
                # Side tiles: W, E
                tiles.append((user_y, user_x - 1))
                tiles.append((user_y, user_x + 1))
            else:  # Target below - forward is south
                # Forward tiles: SW, S, SE
                tiles.append((user_y + 1, user_x - 1))
                tiles.append((user_y + 1, user_x))
                tiles.append((user_y + 1, user_x + 1))
                # Side tiles: W, E
                tiles.append((user_y, user_x - 1))
                tiles.append((user_y, user_x + 1))
        else:  # Horizontal movement dominant
            if dx < 0:  # Target left - forward is west
                # Forward tiles: NW, W, SW
                tiles.append((user_y - 1, user_x - 1))
                tiles.append((user_y, user_x - 1))
                tiles.append((user_y + 1, user_x - 1))
                # Side tiles: N, S
                tiles.append((user_y - 1, user_x))
                tiles.append((user_y + 1, user_x))
            else:  # Target right - forward is east
                # Forward tiles: NE, E, SE
                tiles.append((user_y - 1, user_x + 1))
                tiles.append((user_y, user_x + 1))
                tiles.append((user_y + 1, user_x + 1))
                # Side tiles: N, S
                tiles.append((user_y - 1, user_x))
                tiles.append((user_y + 1, user_x))

        return tiles

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False

        if not target_pos or not game:
            return False

        # Determine position to check range from (move target if moving, otherwise current position)
        check_y, check_x = user.move_target if user.move_target else (user.y, user.x)

        # Target must be adjacent (range 1)
        distance = game.chess_distance(check_y, check_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Target must be in a cardinal direction (north, south, east, west only)
        dy = target_pos[0] - check_y
        dx = target_pos[1] - check_x

        # Cardinal directions: one coordinate must be 0, the other non-zero
        is_cardinal = (dx == 0 and dy != 0) or (dy == 0 and dx != 0)
        if not is_cardinal:
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Demilune skill for execution at the end of the turn."""
        if not self.can_use(user, target_pos, game):
            return False

        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Set cooldown
        self.current_cooldown = self.cooldown

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} readies a mighty swing",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def _get_sweep_order(self, user_y: int, user_x: int, target_y: int, target_x: int) -> List[Tuple[int, int]]:
        """Get tiles in sweeping order for animation (left to right or top to bottom)."""
        tiles = []

        # Determine forward direction
        dy = target_y - user_y
        dx = target_x - user_x

        # Order tiles to show a sweeping motion
        if abs(dy) >= abs(dx):  # Vertical movement dominant
            if dy < 0:  # Target above - sweep left to right
                tiles = [
                    (user_y, user_x - 1),      # W (side)
                    (user_y - 1, user_x - 1),  # NW (forward)
                    (user_y - 1, user_x),      # N (forward)
                    (user_y - 1, user_x + 1),  # NE (forward)
                    (user_y, user_x + 1)       # E (side)
                ]
            else:  # Target below - sweep left to right
                tiles = [
                    (user_y, user_x - 1),      # W (side)
                    (user_y + 1, user_x - 1),  # SW (forward)
                    (user_y + 1, user_x),      # S (forward)
                    (user_y + 1, user_x + 1),  # SE (forward)
                    (user_y, user_x + 1)       # E (side)
                ]
        else:  # Horizontal movement dominant
            if dx < 0:  # Target left - sweep top to bottom
                tiles = [
                    (user_y - 1, user_x),      # N (side)
                    (user_y - 1, user_x - 1),  # NW (forward)
                    (user_y, user_x - 1),      # W (forward)
                    (user_y + 1, user_x - 1),  # SW (forward)
                    (user_y + 1, user_x)       # S (side)
                ]
            else:  # Target right - sweep top to bottom
                tiles = [
                    (user_y - 1, user_x),      # N (side)
                    (user_y - 1, user_x + 1),  # NE (forward)
                    (user_y, user_x + 1),      # E (forward)
                    (user_y + 1, user_x + 1),  # SE (forward)
                    (user_y + 1, user_x)       # S (side)
                ]

        return tiles

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Demilune skill during the combat phase."""

        # Check if enhanced by potpourri
        enhanced = user.potpourri_held

        # Base damage is always 3, +1 if enhanced
        damage = 4 if enhanced else 3

        # Consume potpourri if held
        if user.potpourri_held:
            user.potpourri_held = False
            user.potpourri_duration = 0

            # Trigger Infuse cooldown when consumed
            # Add 1 to account for cooldown decrement at start of next turn
            for skill in user.active_skills:
                if skill.name == "Infuse":
                    skill.current_cooldown = skill.cooldown + 1
                    break

            message_log.add_message(
                f"{user.get_display_name()} infuses Demilune with his fragrant blend",
                MessageType.ABILITY,
                player=user.player
            )

        # Get arc tiles
        arc_tiles = self._get_arc_tiles(user.y, user.x, target_pos[0], target_pos[1])

        # Check for Demilune upgrade (Selenic Backdraft — mirrored arc)
        from boneglaive.game.upgrades import UpgradeManager
        demilune_upgraded = UpgradeManager.is_skill_upgraded(user, "Demilune")

        # If upgraded, calculate back-arc tiles for the Selenic Backdraft swing
        back_arc_tiles = []
        if demilune_upgraded:
            dy = target_pos[0] - user.y
            dx = target_pos[1] - user.x
            opposite_target = (user.y - dy, user.x - dx)
            back_arc_tiles = self._get_arc_tiles(user.y, user.x, opposite_target[0], opposite_target[1])

            message_log.add_message(
                f"{user.get_display_name()} swings the granite pedestal and creates a selenic backdraft",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} swings the granite pedestal in a crescent sweep",
                MessageType.ABILITY,
                player=user.player
            )


        # Apply damage and debuff to all enemy units in arc
        hit_count = 0
        for tile_y, tile_x in arc_tiles:
            target = game.get_unit_at(tile_y, tile_x)
            if target and target.player != user.player and target.is_alive():
                # Deal damage
                game.current_attacker = user
                old_hp = target.hp
                target.hp = max(0, target.hp - damage)
                actual_damage = old_hp - target.hp
                game.current_attacker = None

                # Route lethal hits through centralized death handling so on-death
                # effects fire (the hp setter's _handle_death only awards GP and removes
                # the unit from game.units — the post-skill sweep then can't find it).
                if target.hp <= 0:
                    game.handle_unit_death(target, user, cause="demilune", ui=ui)
                else:
                    game.check_critical_health(target, user, old_hp, ui)

                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=target.get_display_name(),
                    damage=actual_damage,
                    ability="Demilune",
                    attacker_player=user.player,
                    target_player=target.player
                )


                # Apply Demilune debuff if not immune
                if not target.is_immune_to_effects():
                    target.demilune_debuffed = True
                    target.demilune_debuffed_by = user
                    # Enhanced (infused) extends Lunacy to 3 turns instead of 2
                    target.demilune_debuff_duration = 3 if enhanced else 2


                    message_log.add_message(
                        f"{target.get_display_name()}'s power wanes",
                        MessageType.WARNING,
                        player=target.player
                    )
                else:
                    message_log.add_message(
                        f"{target.get_display_name()} is immune to Lunacy due to Stasiality",
                        MessageType.ABILITY,
                        player=target.player
                    )

                hit_count += 1

        # Selenic Backdraft: upgraded back-arc deals same damage + applies Selenic Backdraft status
        if demilune_upgraded and back_arc_tiles:

            for tile_y, tile_x in back_arc_tiles:
                target = game.get_unit_at(tile_y, tile_x)
                if target and target.player != user.player and target.is_alive():
                    # Deal same damage as front arc
                    game.current_attacker = user
                    old_hp = target.hp
                    target.hp = max(0, target.hp - damage)
                    actual_damage = old_hp - target.hp
                    game.current_attacker = None

                    # Route lethal hits through centralized death handling (see Demilune front arc).
                    if target.hp <= 0:
                        game.handle_unit_death(target, user, cause="selenic_backdraft", ui=ui)
                    else:
                        game.check_critical_health(target, user, old_hp, ui)

                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=target.get_display_name(),
                        damage=actual_damage,
                        ability="Selenic Backdraft",
                        attacker_player=user.player,
                        target_player=target.player
                    )


                    # Apply Selenic Backdraft status if not immune
                    if not target.is_immune_to_effects():
                        target.selenic_backdraft = True
                        target.selenic_backdraft_by = user
                        target.selenic_backdraft_duration = 3 if enhanced else 2

                        message_log.add_message(
                            f"{target.get_display_name()} is blinded by the selenic backdraft",
                            MessageType.WARNING,
                            player=target.player
                        )
                    else:
                        message_log.add_message(
                            f"{target.get_display_name()} is immune to Selenic Backdraft due to Stasiality",
                            MessageType.ABILITY,
                            player=target.player
                        )

                    hit_count += 1

        return True


class GraniteGeasSkill(ActiveSkill):
    """
    Active skill: GRANITE GEAS
    Single target attack that taunts enemy. POTPOURRIST heals if taunt is ignored.
    """

    def __init__(self):
        super().__init__(
            name="Granite Geas",
            key="3",
            description="Single target attack. If target doesn't attack POTPOURRIST next turn, POTPOURRIST heals 4 HP. Enhanced: Lasts 2 turns.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=1
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False

        if not target_pos or not game:
            return False

        # Determine position to check range from (move target if moving, otherwise current position)
        check_y, check_x = user.move_target if user.move_target else (user.y, user.x)

        # Check range
        distance = game.chess_distance(check_y, check_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(check_y, check_x, target_pos[0], target_pos[1]):
            return False

        # Find target unit at position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False

        # Can only target enemies
        if target.player == user.player:
            return False

        # Check universal targeting restrictions
        if not game.can_target_unit(user, target):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue up the Granite Geas skill for execution at the end of the turn."""
        if not self.can_use(user, target_pos, game):
            return False

        # Get target for the message
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False

        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Set cooldown
        self.current_cooldown = self.cooldown

        # Log that the skill has been queued
        message_log.add_message(
            f"{user.get_display_name()} raises the anointed granite pedestal high into the air over {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Granite Geas skill during the combat phase."""

        # Get target
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False

        # Check if enhanced by potpourri
        enhanced = user.potpourri_held
        taunt_duration = 2 if enhanced else 1

        # Consume potpourri if held
        if user.potpourri_held:
            user.potpourri_held = False
            user.potpourri_duration = 0

            # Trigger Infuse cooldown when consumed
            # Add 1 to account for cooldown decrement at start of next turn
            for skill in user.active_skills:
                if skill.name == "Infuse":
                    skill.current_cooldown = skill.cooldown + 1
                    break

            message_log.add_message(
                f"{user.get_display_name()} infuses Granite Geas with his fragrant blend",
                MessageType.ABILITY,
                player=user.player
            )

        message_log.add_message(
            f"{user.get_display_name()} comes down hard on {target.get_display_name()} with a ton of oiled granite",
            MessageType.ABILITY,
            player=user.player
        )


        # Deal damage (check for Infuse upgrade bonus)
        from boneglaive.game.upgrades import UpgradeManager
        infuse_upgraded = UpgradeManager.is_skill_upgraded(user, "Infuse")

        # Base damage is 5, +1 if enhanced and Infuse is upgraded
        damage = 5
        if enhanced and infuse_upgraded:
            damage = 6

        game.current_attacker = user
        old_hp = target.hp
        target.hp = max(0, target.hp - damage)
        actual_damage = old_hp - target.hp
        game.current_attacker = None

        # Route lethal hits through centralized death handling (see Demilune front arc).
        if target.hp <= 0:
            game.handle_unit_death(target, user, cause="granite_geas", ui=ui)
        else:
            game.check_critical_health(target, user, old_hp, ui)

        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=actual_damage,
            ability="Granite Geas",
            attacker_player=user.player,
            target_player=target.player
        )


        # Apply taunt if not immune
        if not target.is_immune_to_effects():
            target.taunted_by = user
            target.taunt_duration = taunt_duration
            target.taunt_responded_this_turn = False
            target.geas_affected = True  # For status icon display

            # Mark unit for graphical animation (renderer will detect this)
            target.granite_geas_chain_hit = True  # Also mark primary target
            target.granite_geas_infused = enhanced

            # Check for Granite Geas upgrade (attack reduction)
            from boneglaive.game.upgrades import UpgradeManager
            granite_geas_upgraded = UpgradeManager.is_skill_upgraded(user, "Granite Geas")
            target.geas_attack_reduction = granite_geas_upgraded


            message_log.add_message(
                f"{target.get_display_name()} is bound by a redolent geas",
                MessageType.WARNING,
                player=target.player
            )
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to the geas due to stasiality",
                MessageType.ABILITY,
                player=target.player
            )

        # Chain to adjacent enemies if upgrade is active
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Granite Geas"):
            # Track which units have been hit to avoid infinite loops
            hit_units = {target}
            # Queue of units to process
            to_process = [target]

            while to_process:
                current_target = to_process.pop(0)

                # Find all enemies adjacent to current target
                adjacent_positions = [
                    (current_target.y - 1, current_target.x),
                    (current_target.y + 1, current_target.x),
                    (current_target.y, current_target.x - 1),
                    (current_target.y, current_target.x + 1),
                    (current_target.y - 1, current_target.x - 1),
                    (current_target.y - 1, current_target.x + 1),
                    (current_target.y + 1, current_target.x - 1),
                    (current_target.y + 1, current_target.x + 1)
                ]

                for adj_y, adj_x in adjacent_positions:
                    adj_unit = game.get_unit_at(adj_y, adj_x)
                    if (adj_unit and adj_unit.player != user.player and
                        adj_unit.is_alive() and adj_unit not in hit_units):


                        # Deal damage
                        game.current_attacker = user
                        old_hp = adj_unit.hp
                        adj_unit.hp = max(0, adj_unit.hp - damage)
                        actual_chain_damage = old_hp - adj_unit.hp
                        game.current_attacker = None

                        # Route lethal hits through centralized death handling (see Demilune front arc).
                        if adj_unit.hp <= 0:
                            game.handle_unit_death(adj_unit, user, cause="granite_geas", ui=ui)
                        else:
                            game.check_critical_health(adj_unit, user, old_hp, ui)

                        message_log.add_combat_message(
                            attacker_name=user.get_display_name(),
                            target_name=adj_unit.get_display_name(),
                            damage=actual_chain_damage,
                            ability="Granite Geas",
                            attacker_player=user.player,
                            target_player=adj_unit.player
                        )

                        # Apply taunt if not immune
                        if not adj_unit.is_immune_to_effects():
                            adj_unit.taunted_by = user
                            adj_unit.taunt_duration = taunt_duration
                            adj_unit.taunt_responded_this_turn = False
                            adj_unit.geas_affected = True
                            adj_unit.geas_attack_reduction = False

                            # Mark unit for graphical animation (renderer will detect this)
                            adj_unit.granite_geas_chain_hit = True
                            adj_unit.granite_geas_infused = enhanced


                        # Mark as hit and add to queue for further chaining
                        hit_units.add(adj_unit)
                        to_process.append(adj_unit)

        return True
