#!/usr/bin/env python3
"""Skills for ORDNANCE GRAFT — the gunner-samurai who grafts %HP bombs and touches them off."""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import ActiveSkill, PassiveSkill, TargetType
from boneglaive.utils.constants import BOLA_MAX_STACKS
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


# Bola detonation: % of the target's max HP per fused stack, with a bonus against
# healthy targets (the anti-tank sharpener — he punishes full-HP big bodies hardest).
BOLA_PCT_BASE = 0.12
BOLA_PCT_HEALTHY_BONUS = 0.06
BOLA_HEALTHY_THRESHOLD = 0.75
# MERIDIAN CUT cooldown refunded per stack detonated.
CUT_REFUND_PER_STACK = 2
CUT_SKILL_NAME = "Meridian Cut"


def plant_bola(target: 'Unit', amount: int = 1) -> int:
    """Graft `amount` bola stacks onto target (capped). Newly planted stacks are
    unfused (cannot detonate until they fuse next turn). Returns stacks added."""
    before = target.bola_stacks
    target.bola_stacks = min(BOLA_MAX_STACKS, target.bola_stacks + amount)
    added = target.bola_stacks - before
    target.bola_unfused += added
    return added


def bola_pct(target: 'Unit') -> float:
    """Per-stack max-HP fraction for a detonation against this target."""
    pct = BOLA_PCT_BASE
    if target.hp > target.max_hp * BOLA_HEALTHY_THRESHOLD:
        pct += BOLA_PCT_HEALTHY_BONUS
    return pct


def detonate_bola(target: 'Unit', game: 'Game', stacks: int) -> int:
    """Detonate `stacks` fused bolas on target for %max-HP damage (ignores DEF;
    PRT still applies via deal_damage). Returns damage dealt."""
    if stacks <= 0:
        return 0
    per_stack = int(round(target.max_hp * bola_pct(target)))
    total = max(1, per_stack) * stacks
    dealt = target.deal_damage(total)
    logger.debug(f"Bola detonation: {stacks} stacks on {target.get_display_name()} for {dealt}")
    return dealt


def _reduce_cut_cooldown(user: 'Unit', stacks_detonated: int) -> None:
    """Refund MERIDIAN CUT's cooldown by the stacks just detonated (the flow engine)."""
    if stacks_detonated <= 0:
        return
    refund = stacks_detonated * CUT_REFUND_PER_STACK
    for skill in user.active_skills:
        if skill.name == CUT_SKILL_NAME:
            if skill.current_cooldown > 0:
                skill.current_cooldown = max(0, skill.current_cooldown - refund)
            break


class RotorGraft(PassiveSkill):
    """Keeps one leashed quadcopter drone in the field; it plants bolas and can scuttle."""

    def __init__(self):
        super().__init__(
            name="Rotor Graft",
            key="R",
            description="Fields a leashed quadcopter drone whose attacks graft a bola. The drone regenerates a few turns after it is destroyed."
        )

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        # Drone spawn/regeneration/leash are reconciled by the engine each turn
        # (it needs to add units to the board, which a passive can't cleanly do).
        pass


class InoculantSkill(ActiveSkill):
    """Melee strike that deals ATK damage and grafts a bola onto the target."""

    def __init__(self):
        super().__init__(
            name="Inoculant",
            key="I",
            description="Strike an adjacent enemy for normal damage and graft a bola bomb onto them (up to 3).",
            target_type=TargetType.ENEMY,
            cooldown=1,
            range_=1
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if target is None or target.player == user.player:
            return False
        if not game.can_target_unit(user, target):
            return False
        from_y, from_x = user.move_target if user.move_target else (user.y, user.x)
        if game.chess_distance(from_y, from_x, target_pos[0], target_pos[1]) > self.range:
            return False
        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        message_log.add_message(
            f"{user.get_display_name()} prepares to inoculate",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if target is None or target.player == user.player:
            return False

        attacker_atk = user.get_effective_stats()['attack']
        target_def = target.get_effective_stats()['defense']
        damage = max(1, attacker_atk - target_def)
        dealt = target.deal_damage(damage)
        added = plant_bola(target, 1)

        message_log.add_message(
            f"{user.get_display_name()} strikes {target.get_display_name()} for {dealt} and grafts a bola ({target.bola_stacks})",
            MessageType.ABILITY,
            player=user.player
        )
        if added == 0:
            message_log.add_message(
                f"{target.get_display_name()} is already saturated with bolas",
                MessageType.ABILITY,
                player=user.player
            )
        return True


class MeridianCutSkill(ActiveSkill):
    """Dash along a line to an empty tile; cut and graft a bola onto an enemy on arrival."""

    def __init__(self):
        super().__init__(
            name="Meridian Cut",
            key="M",
            description="Dash to any empty position within range, ignoring pathing. Strike and graft a bola onto an adjacent enemy on arrival. Cooldown is refunded when bolas detonate.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=3
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        ty, tx = target_pos
        if not game.is_valid_position(ty, tx):
            return False
        if not game.map.is_passable(ty, tx):
            return False
        if game.get_unit_at(ty, tx) is not None:
            return False
        from_y, from_x = user.move_target if user.move_target else (user.y, user.x)
        if game.chess_distance(from_y, from_x, ty, tx) > self.range:
            return False
        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        # The cut IS the movement — don't walk first.
        user.move_target = None
        user.vault_target_indicator = target_pos  # reuse the leap indicator
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        message_log.add_message(
            f"{user.get_display_name()} prepares to cut to ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        ty, tx = target_pos
        user.vault_target_indicator = None

        # Land the dash (bypass the grid setter like Vault — it's a teleport).
        if game.get_unit_at(ty, tx) is not None:
            message_log.add_message(
                f"{user.get_display_name()}'s cut fizzles - no room to land!",
                MessageType.WARNING,
                player=user.player
            )
            return False
        game._remove_from_unit_grid(user)
        user.y, user.x = ty, tx
        game._update_unit_grid(user)
        game._move_leashed_drones(user, ty, tx, ui)

        message_log.add_message(
            f"{user.get_display_name()} flickers across the field",
            MessageType.ABILITY,
            player=user.player
        )

        # Strike + graft an adjacent enemy on arrival (one).
        for enemy in game.units:
            if (enemy.is_alive() and enemy.player != user.player
                    and game.chess_distance(user.y, user.x, enemy.y, enemy.x) <= 1
                    and game.can_target_unit(user, enemy)):
                attacker_atk = user.get_effective_stats()['attack']
                target_def = enemy.get_effective_stats()['defense']
                damage = max(1, attacker_atk - target_def)
                dealt = enemy.deal_damage(damage)
                plant_bola(enemy, 1)
                message_log.add_message(
                    f"{user.get_display_name()} cuts {enemy.get_display_name()} for {dealt} and grafts a bola ({enemy.bola_stacks})",
                    MessageType.ABILITY,
                    player=user.player
                )
                break
        return True


class HarvestSkill(ActiveSkill):
    """Detonate every fused bola on the field for %max-HP damage; refunds MERIDIAN CUT."""

    def __init__(self):
        super().__init__(
            name="Harvest",
            key="H",
            description="Detonate all fused bolas on the field. Each stack deals a percent of the target's max HP (more against healthy targets). Refunds Meridian Cut's cooldown per stack.",
            target_type=TargetType.SELF,
            cooldown=3,
            range_=0
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        # Usable only if at least one fused bola exists on an enemy.
        return any(
            u.is_alive() and u.player != user.player and (u.bola_stacks - u.bola_unfused) > 0
            for u in game.units
        )

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = (user.y, user.x)
        user.selected_skill = self
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        message_log.add_message(
            f"{user.get_display_name()} prepares to touch off the bolas",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        total_stacks = 0
        for target in list(game.units):
            if not (target.is_alive() and target.player != user.player):
                continue
            fused = target.bola_stacks - target.bola_unfused
            if fused <= 0:
                continue
            dealt = detonate_bola(target, game, fused)
            total_stacks += fused
            # Consume only the fused stacks; any unfused remain on the target.
            target.bola_stacks = target.bola_unfused
            message_log.add_message(
                f"{target.get_display_name()}'s bolas detonate for {dealt}",
                MessageType.ABILITY,
                player=user.player
            )

        if total_stacks == 0:
            return False

        _reduce_cut_cooldown(user, total_stacks)
        message_log.add_message(
            f"{user.get_display_name()} reaps the graft",
            MessageType.ABILITY,
            player=user.player
        )
        return True


class ScuttleSkill(ActiveSkill):
    """Drone self-destructs: detonate bolas in its blast and explode for flat damage."""

    BLAST_RADIUS = 1
    BLAST_DAMAGE = 6

    def __init__(self):
        super().__init__(
            name="Scuttle",
            key="S",
            description="The drone self-destructs: detonates bolas within 1 tile and deals 6 damage to units in the blast. The drone regenerates a few turns later.",
            target_type=TargetType.SELF,
            cooldown=0,
            range_=0
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        return bool(game) and getattr(user, 'is_drone', False)

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = (user.y, user.x)
        user.selected_skill = self
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        message_log.add_message(
            f"{user.get_display_name()} prepares to scuttle",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        cy, cx = user.y, user.x
        owner_player = user.player

        for target in list(game.units):
            if not target.is_alive() or target is user:
                continue
            if game.chess_distance(cy, cx, target.y, target.x) > self.BLAST_RADIUS:
                continue
            if target.player == owner_player:
                continue  # no friendly fire
            # Detonate any fused bolas on this target first.
            fused = target.bola_stacks - target.bola_unfused
            if fused > 0:
                detonate_bola(target, game, fused)
                target.bola_stacks = target.bola_unfused
            # Flat blast (bomb damage: ignores DEF, deal_damage still applies PRT).
            target.deal_damage(self.BLAST_DAMAGE)

        message_log.add_message(
            f"{user.get_display_name()} scuttles in a burst of shrapnel",
            MessageType.ABILITY,
            player=owner_player
        )
        # Consume the drone; the engine's death handling starts the regen timer.
        user.hp = 0
        return True
