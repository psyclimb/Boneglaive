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
        import time
        import curses
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        message_log.add_message(
            f"{user.get_display_name()} begins infusing potpourri",
            MessageType.ABILITY,
            player=user.player
        )

        # Show potpourri creation animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get infuse animation sequence
            infuse_animation = ui.asset_manager.get_skill_animation_sequence('infuse')
            if not infuse_animation:
                infuse_animation = [',', ':', '*', 'o', 'O', '@', 'O', 'o', '*', ':', ',', '~']  # Fallback

            # Animate the potpourri creation
            for frame in infuse_animation:
                ui.renderer.draw_tile(user.y, user.x, frame, 5, curses.A_BOLD)  # Magenta/purple for potpourri
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)

            # Flash to show completion
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [5, 3 if user.player == 1 else 4] * 2  # Alternate magenta with player color
                durations = [0.1] * 4

                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)

            # Redraw board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

        # Set potpourri held flag
        user.potpourri_held = True

        message_log.add_message(
            f"{user.get_display_name()} creates a potpourri blend!",
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
        import time
        import curses
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

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

        # Show sweeping animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the sweep order for animation
            sweep_tiles = self._get_sweep_order(user.y, user.x, target_pos[0], target_pos[1])

            # Get demilune sweep animation sequence
            sweep_animation = ui.asset_manager.get_skill_animation_sequence('demilune_sweep')
            if not sweep_animation:
                sweep_animation = ['/', '|', '\\', '-', '*']  # Fallback

            # Animate the sweep across tiles
            for i, (tile_y, tile_x) in enumerate(sweep_tiles):
                # Use different frames for different positions in the sweep
                frame_index = min(i, len(sweep_animation) - 1)
                frame = sweep_animation[frame_index]

                # Draw the sweep effect
                color = 7 if enhanced else 1  # Yellow if enhanced, red otherwise
                ui.renderer.draw_tile(tile_y, tile_x, frame, color, curses.A_BOLD)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)

            # Show impact effect on all tiles simultaneously
            impact_frame = '*'
            for tile_y, tile_x in arc_tiles:
                ui.renderer.draw_tile(tile_y, tile_x, impact_frame, 1, curses.A_BOLD)  # Red for impact
            ui.renderer.refresh()
            sleep_with_animation_speed(0.15)

            # Clear the animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

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

                # Apply Demilune debuff if not immune
                if not target.is_immune_to_effects():
                    target.demilune_debuffed = True
                    target.demilune_debuffed_by = user
                    target.demilune_debuff_duration = 2
                    target.demilune_defense_halved = enhanced

                    # Show moon phase animation if UI is available
                    if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                        # Get lunacy moon phase animation
                        moon_animation = ui.asset_manager.get_skill_animation_sequence('lunacy_moon')
                        if not moon_animation:
                            moon_animation = ['(', ' ', '(', ' ', '(', ' ', '(', ' ', '(']  # Fallback

                        # Animate the moon waning over the target
                        for frame in moon_animation:
                            ui.renderer.draw_tile(target.y, target.x, frame, 7)  # Yellow for moon
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.08)

                        # Redraw board after animation
                        if hasattr(ui, 'draw_board'):
                            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

                    message_log.add_message(
                        f"{target.get_display_name()} is afflicted with Lunacy",
                        MessageType.ABILITY,
                        player=target.player
                    )
                else:
                    message_log.add_message(
                        f"{target.get_display_name()} is immune to Lunacy due to Stasiality",
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
            f"{user.get_display_name()} prepares to bring down the granite gavel on {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Granite Geas skill during the combat phase."""
        import time
        import curses
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

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

        # Show Granite Geas strike animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Part 1: Show POTPOURRIST raising and slamming the pedestal at attacker position
            windup_animation = ui.asset_manager.get_skill_animation_sequence('granite_geas_windup')
            if not windup_animation:
                windup_animation = ['.', ':', '|', 'I', '^', '^', '^', '|', 'I', '!', ':', '.']  # Raising high, pausing, then SLAMMING

            for frame in windup_animation:
                ui.renderer.draw_tile(user.y, user.x, frame, 7, curses.A_BOLD)  # Yellow at attacker position
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)

            # Part 2: Show impact on target
            impact_animation = ui.asset_manager.get_skill_animation_sequence('granite_geas_impact')
            if not impact_animation:
                impact_animation = ['*', '#', '@', '#', '*', '.']  # Impact effect

            for frame in impact_animation:
                ui.renderer.draw_tile(target.y, target.x, frame, 7, curses.A_BOLD)  # Yellow at target position
                ui.renderer.refresh()
                sleep_with_animation_speed(0.06)

            # Flash the target to show hit
            if hasattr(ui.renderer, 'flash_tile'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [6 if target.player == 1 else 10, 3 if target.player == 1 else 4] * 2
                durations = [0.1] * 4
                ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)

            # Redraw board after animation
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

        # Deal damage
        damage = 4
        game.current_attacker = user
        old_hp = target.hp
        target.hp = max(0, target.hp - damage)
        actual_damage = old_hp - target.hp
        game.current_attacker = None

        message_log.add_message(
            f"{target.get_display_name()} takes #DAMAGE_{actual_damage}# damage from Granite Geas",
            MessageType.COMBAT,
            player=target.player
        )

        # Apply taunt if not immune
        if not target.is_immune_to_effects():
            target.taunted_by = user
            target.taunt_duration = taunt_duration
            target.taunt_responded_this_turn = False

            # Show geas binding animation - oils dripping and sealing
            if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                geas_binding = ui.asset_manager.get_skill_animation_sequence('geas_binding')
                if not geas_binding:
                    geas_binding = [',', '.', ':', '|', 'I', '#', '#', '0', '0']  # Oils dripping and sealing

                for frame in geas_binding:
                    ui.renderer.draw_tile(target.y, target.x, frame, 7, curses.A_BOLD)  # Yellow for geas magic
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.08)

                # Redraw board after geas animation
                if hasattr(ui, 'draw_board'):
                    ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

            message_log.add_message(
                f"{target.get_display_name()} is marked by potpourri oils!",
                MessageType.ABILITY,
                player=target.player
            )
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to Taunt due to Stasiality",
                MessageType.ABILITY,
                player=target.player
            )

        return True
