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


# Bola detonation: % of the target's MAX HP per fused stack, scaling UP with the
# target's max HP — the anti-tank curve. A small body takes a small slice; a big
# body takes a much larger PERCENTAGE, so he prefers the tank and is weak into
# squishies. pct = floor + max(0, max_hp - ref) * per_hp.
#   ref 18 HP -> 8%/stack (squishy floor); 24 HP -> 30%/stack (tank).
# At cap 4 that is ~22% of a squishy's bar vs a tank one-shot. These three are the
# primary balance levers.
BOLA_PCT_FLOOR = 0.08        # per-stack % at (and below) the reference HP
BOLA_PCT_REF_HP = 18         # reference max HP the floor applies to (roster's squishy)
BOLA_PCT_PER_HP = 0.22 / 6   # extra per-stack % for each max-HP point above the reference
# MERIDIAN CUT cooldown refunded per stack detonated.
CUT_REFUND_PER_STACK = 2
CUT_SKILL_NAME = "Meridian Cut"
# Flat base damage for his strikes (Inoculant / Meridian Cut). NOT ATK-scaled — his
# damage identity is the bombs, not the sword. DEF/PRT still reduce it via deal_damage.
STRIKE_DAMAGE = 2


def plant_bola(target: 'Unit', amount: int = 1) -> int:
    """Graft `amount` bola bombs onto target (capped at BOLA_MAX_STACKS). Each is a
    distinct, individually-cleansable instance, planted unfused (cannot detonate until
    it fuses next turn). Returns the number of bombs actually added."""
    room = BOLA_MAX_STACKS - len(target.bolas)
    added = max(0, min(amount, room))
    for _ in range(added):
        target.bolas.append({'fused': False})
    return added


def fused_count(target: 'Unit') -> int:
    """Number of fused (detonatable) bolas on target."""
    return sum(1 for b in target.bolas if b['fused'])


def arm_bolas(target: 'Unit') -> None:
    """Fuse every unfused bomb on target (it becomes detonatable). Called at the
    owner's turn-start, one fuse-step after a bomb is planted."""
    for bomb in target.bolas:
        bomb['fused'] = True


def remove_one_bola(target: 'Unit') -> bool:
    """Defuse a single bomb (drip-cleanse, e.g. Broaching Gas). Prefers removing an
    UNFUSED bomb first so a partial cleanse delays the burst rather than eating an
    already-armed stack. Returns True if a bomb was removed."""
    if not target.bolas:
        return False
    for i, bomb in enumerate(target.bolas):
        if not bomb['fused']:
            del target.bolas[i]
            return True
    target.bolas.pop()
    return True


def clear_bolas(target: 'Unit') -> int:
    """Remove every bomb from target (full cleanse, e.g. Vagal Run). Returns count removed."""
    n = len(target.bolas)
    target.bolas.clear()
    return n


def bola_pct(target: 'Unit') -> float:
    """Per-stack max-HP fraction for a detonation against this target. Scales up with
    the target's max HP (the anti-tank curve): bigger body -> bigger percentage."""
    return BOLA_PCT_FLOOR + max(0, target.max_hp - BOLA_PCT_REF_HP) * BOLA_PCT_PER_HP


def detonate_fused(target: 'Unit', game: 'Game') -> int:
    """Detonate and remove all FUSED bolas on target for %max-HP damage (ignores DEF;
    PRT still applies via deal_damage). Unfused bombs remain. Returns damage dealt."""
    stacks = fused_count(target)
    if stacks <= 0:
        return 0
    per_stack = int(round(target.max_hp * bola_pct(target)))
    total = max(1, per_stack) * stacks
    dealt = target.deal_damage(total)
    target.bolas = [b for b in target.bolas if not b['fused']]
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
    """Keeps one leashed quadcopter drone in the field; it mirrors its owner's plants."""

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
            description="Strike an adjacent enemy for normal damage and graft a bola bomb onto them (up to 4).",
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

        target_def = target.get_effective_stats()['defense']
        damage = max(1, STRIKE_DAMAGE - target_def)
        dealt = target.deal_damage(damage)
        added = plant_bola(target, 1)

        message_log.add_message(
            f"{user.get_display_name()} strikes {target.get_display_name()} for {dealt} and grafts a bola ({len(target.bolas)})",
            MessageType.ABILITY,
            player=user.player
        )
        if added == 0:
            message_log.add_message(
                f"{target.get_display_name()} is already saturated with bolas",
                MessageType.ABILITY,
                player=user.player
            )
        # The autonomous drone mirrors the strike on the same target.
        game._drone_echo_strike(user, target, ui)
        return True


class MeridianCutSkill(ActiveSkill):
    """Dash along a line to an empty tile, cutting and grafting a bola onto EVERY enemy
    the dash passes through (and the drone mirrors the sweep)."""

    def __init__(self):
        super().__init__(
            name="Meridian Cut",
            key="M",
            description="Dash to any empty position within range, ignoring pathing. Cut and graft a bola onto every enemy along the dash line. Cooldown is refunded when bolas detonate.",
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
        from boneglaive.utils.coordinates import get_line, Position

        ty, tx = target_pos
        user.vault_target_indicator = None

        # Capture the dash ORIGIN before we move — the sweep hits enemies on the line
        # from here to the destination.
        oy, ox = user.y, user.x

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

        # Cut + graft every enemy on the dash line (origin->destination). The origin
        # holds the graft and the destination is required-empty, so only the enemies
        # the dash physically passed THROUGH are hit. The drone mirrors each cut.
        for pos in get_line(Position(oy, ox), Position(ty, tx)):
            enemy = game.get_unit_at(pos.y, pos.x)
            if enemy is None or enemy is user:
                continue
            if not (enemy.is_alive() and enemy.player != user.player
                    and game.can_target_unit(user, enemy)):
                continue
            target_def = enemy.get_effective_stats()['defense']
            damage = max(1, STRIKE_DAMAGE - target_def)
            dealt = enemy.deal_damage(damage)
            plant_bola(enemy, 1)
            message_log.add_message(
                f"{user.get_display_name()} cuts {enemy.get_display_name()} for {dealt} and grafts a bola ({len(enemy.bolas)})",
                MessageType.ABILITY,
                player=user.player
            )
            # The autonomous drone mirrors the cut on this enemy.
            game._drone_echo_strike(user, enemy, ui)
        return True


class HarvestSkill(ActiveSkill):
    """Detonate every fused bola on the field for %max-HP damage; refunds MERIDIAN CUT."""

    def __init__(self):
        super().__init__(
            name="Harvest",
            key="H",
            description="Detonate all fused bolas on the field. Each stack deals a percent of the target's max HP that scales up with the size of the body — devastating against tanks, weak against small units. Refunds Meridian Cut's cooldown per stack.",
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
            u.is_alive() and u.player != user.player and fused_count(u) > 0
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
            fused = fused_count(target)
            if fused <= 0:
                continue
            # Detonate consumes the fused bombs; any unfused remain on the target.
            dealt = detonate_fused(target, game)
            total_stacks += fused
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
