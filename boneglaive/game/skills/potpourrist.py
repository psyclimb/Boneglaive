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
from boneglaive.utils.constants import UnitType

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

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """Apply passive healing at start of turn."""
        if not user.is_alive():
            return

        # Determine heal amount based on potpourri state
        heal_amount = 2 if user.potpourri_held else 1

        # Bypass all healing prevention by directly modifying HP
        old_hp = user._hp
        user._hp = min(user.max_hp, user._hp + heal_amount)
        actual_heal = user._hp - old_hp

        if actual_heal > 0:
            # Show potpourri flourish animation if UI is available
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                import time
                import curses
                from boneglaive.utils.animation_helpers import sleep_with_animation_speed

                # Get the appropriate potpourri flourish animation (enhanced if holding potpourri)
                animation_key = 'melange_eminence_enhanced' if user.potpourri_held else 'melange_eminence'
                flourish_animation = ui.asset_manager.get_skill_animation_sequence(animation_key)
                if flourish_animation:
                    # Animate the potpourri petals and aromatic fumes wafting around
                    for frame in flourish_animation:
                        ui.renderer.draw_tile(user.y, user.x, frame, 3)  # Green color for healing
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.07)  # Gentle, flowing animation speed

                # Show healing number with flashing effect
                healing_text = f"+{actual_heal}"

                # Flash 3 times
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
                f"{user.get_display_name()} regenerates {actual_heal} HP",
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
            description="Creates potpourri that enhances next skill and increases Melange Eminence to 2 HP/turn.",
            target_type=TargetType.SELF,
            cooldown=0,
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
            f"{user.get_display_name()} prepares a potpourri blend",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Infuse skill during the combat phase."""
        # Set potpourri held flag
        user.potpourri_held = True

        message_log.add_message(
            f"{user.get_display_name()} creates a potpourri blend",
            MessageType.ABILITY,
            player=user.player
        )

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
            description="Swings granite pedestal in forward arc. Enemies deal half damage to POTPOURRIST for 2 turns. Enhanced: +1 damage and halves enemy defense.",
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

        # Target must be adjacent (range 1)
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
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
            f"{user.get_display_name()} readies to swing the granite pedestal in an arc",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Demilune skill during the combat phase."""
        # Check if enhanced by potpourri
        enhanced = user.potpourri_held
        damage = 4 if enhanced else 3

        # Consume potpourri if held
        if user.potpourri_held:
            user.potpourri_held = False

        # Get arc tiles
        arc_tiles = self._get_arc_tiles(user.y, user.x, target_pos[0], target_pos[1])

        message_log.add_message(
            f"{user.get_display_name()} swings the granite pedestal in an arc!",
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

                message_log.add_message(
                    f"{target.get_display_name()} takes #DAMAGE_{actual_damage}# damage from Demilune",
                    MessageType.COMBAT,
                    player=target.player
                )

                # Apply Demilune debuff
                target.demilune_debuffed = True
                target.demilune_debuffed_by = user
                target.demilune_debuff_duration = 2
                target.demilune_defense_halved = enhanced

                message_log.add_message(
                    f"{target.get_display_name()} is afflicted with Lunacy",
                    MessageType.ABILITY,
                    player=target.player
                )

                hit_count += 1

        if hit_count == 0:
            message_log.add_message(
                "The swing hits no enemies!",
                MessageType.WARNING,
                player=user.player
            )

        return True


class GraniteGavelSkill(ActiveSkill):
    """
    Active skill: GRANITE GAVEL
    Single target attack that taunts enemy. POTPOURRIST heals if taunt is ignored.
    """

    def __init__(self):
        super().__init__(
            name="Granite Gavel",
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

        # Check range
        distance = game.chess_distance(user.y, user.x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(user.y, user.x, target_pos[0], target_pos[1]):
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
        """Queue up the Granite Gavel skill for execution at the end of the turn."""
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
            f"{user.get_display_name()} prepares to bring down the granite gavel on {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Granite Gavel skill during the combat phase."""
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

        message_log.add_message(
            f"{user.get_display_name()} brings down the granite gavel!",
            MessageType.ABILITY,
            player=user.player
        )

        # Deal damage
        damage = 4
        game.current_attacker = user
        old_hp = target.hp
        target.hp = max(0, target.hp - damage)
        actual_damage = old_hp - target.hp
        game.current_attacker = None

        message_log.add_message(
            f"{target.get_display_name()} takes #DAMAGE_{actual_damage}# damage from Granite Gavel",
            MessageType.COMBAT,
            player=target.player
        )

        # Apply taunt
        target.taunted_by = user
        target.taunt_duration = taunt_duration
        target.taunt_responded_this_turn = False

        message_log.add_message(
            f"{target.get_display_name()} is marked by potpourri fragments!",
            MessageType.ABILITY,
            player=target.player
        )

        return True
