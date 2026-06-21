#!/usr/bin/env python3
"""Skills for ORDNANCE GRAFT — the gunner-samurai who grafts %HP bombs and touches them off."""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import ActiveSkill, PassiveSkill, TargetType
from boneglaive.utils.constants import BOMB_MAX_STACKS, BOMB_LIFESPAN
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


# Bomb detonation: % of the target's MAX HP per fused stack, scaling UP with the
# target's max HP — the anti-tank curve. A small body takes a small slice; a big
# body takes a much larger PERCENTAGE, so he prefers the tank and is weak into
# squishies. pct = floor + max(0, max_hp - ref) * per_hp.
#   ref 18 HP -> 8%/stack (squishy floor); 24 HP -> 30%/stack (tank).
# At cap 4 that is ~22% of a squishy's bar vs a tank one-shot. These three are the
# primary balance levers.
BOMB_PCT_FLOOR = 0.08        # per-stack % at (and below) the reference HP
BOMB_PCT_REF_HP = 18         # reference max HP the floor applies to (roster's squishy)
BOMB_PCT_PER_HP = 0.22 / 6   # extra per-stack % for each max-HP point above the reference
# SKYHOOK cooldown refunded per stack detonated (the flow engine).
SKYHOOK_REFUND_PER_STACK = 2
SKYHOOK_SKILL_NAME = "Skyhook"
# Flat base damage for his strikes (Inoculant / Skyhook arrival). NOT ATK-scaled — his
# damage identity is the bombs, not the strike. DEF/PRT still reduce it via deal_damage.
STRIKE_DAMAGE = 2


def plant_bomb(target: 'Unit', amount: int = 1) -> int:
    """Graft `amount` bombs onto target (capped at BOMB_MAX_STACKS). Each is a
    distinct, individually-cleansable instance, planted unfused (cannot detonate until
    it fuses next turn). Returns the number of bombs actually added.

    Each bomb carries a 'ttl' (turns-to-live); it falls off when the ttl runs out (see
    _process_ordnance_graft_upkeep). Grafting a fresh bomb REFRESHES the whole cluster's
    ttl back to full — keep striking the target and nothing decays; stop and it expires.

    Stasiality (or effective stasiality — GRAYMAN, HEINOUS_VAPOR, Topiary form) makes
    a unit immune to new status effects, so bombs can't be grafted onto it at all."""
    if target.is_immune_to_effects():
        return 0
    room = BOMB_MAX_STACKS - len(target.bombs)
    added = max(0, min(amount, room))
    for _ in range(added):
        target.bombs.append({'fused': False, 'ttl': BOMB_LIFESPAN})
    # Refresh every bomb's timer on a successful graft (the cluster is "topped up").
    if added > 0:
        for bomb in target.bombs:
            bomb['ttl'] = BOMB_LIFESPAN
    return added


def fused_count(target: 'Unit') -> int:
    """Number of fused (detonatable) bombs on target."""
    return sum(1 for b in target.bombs if b['fused'])


def arm_bombs(target: 'Unit') -> None:
    """Fuse every unfused bomb on target (it becomes detonatable). Called at the
    owner's turn-start, one fuse-step after a bomb is planted."""
    for bomb in target.bombs:
        bomb['fused'] = True


def tick_bombs(target: 'Unit') -> int:
    """Age every bomb on target by one turn and drop any whose timer has run out (they
    fall off). Called at the owner's turn-start, right after arming. Returns the number
    of bombs that expired this tick."""
    if not target.bombs:
        return 0
    for bomb in target.bombs:
        bomb['ttl'] = bomb.get('ttl', BOMB_LIFESPAN) - 1
    before = len(target.bombs)
    target.bombs[:] = [b for b in target.bombs if b.get('ttl', BOMB_LIFESPAN) > 0]
    return before - len(target.bombs)


def remove_one_bomb(target: 'Unit') -> bool:
    """Defuse a single bomb (drip-cleanse, e.g. Broaching Gas). Prefers removing an
    UNFUSED bomb first so a partial cleanse delays the burst rather than eating an
    already-armed stack. Returns True if a bomb was removed."""
    if not target.bombs:
        return False
    for i, bomb in enumerate(target.bombs):
        if not bomb['fused']:
            del target.bombs[i]
            return True
    target.bombs.pop()
    return True


def clear_bombs(target: 'Unit') -> int:
    """Remove every bomb from target (full cleanse, e.g. Vagal Run). Returns count removed."""
    n = len(target.bombs)
    target.bombs.clear()
    return n


def bomb_pct(target: 'Unit') -> float:
    """Per-stack max-HP fraction for a detonation against this target. Scales up with
    the target's max HP (the anti-tank curve): bigger body -> bigger percentage."""
    return BOMB_PCT_FLOOR + max(0, target.max_hp - BOMB_PCT_REF_HP) * BOMB_PCT_PER_HP


def detonate_fused(target: 'Unit', game: 'Game') -> int:
    """Detonate and remove all FUSED bombs on target for %max-HP damage (ignores DEF;
    PRT still applies via deal_damage). Unfused bombs remain. Returns damage dealt."""
    stacks = fused_count(target)
    if stacks <= 0:
        return 0
    per_stack = int(round(target.max_hp * bomb_pct(target)))
    total = max(1, per_stack) * stacks
    dealt = target.deal_damage(total)
    target.bombs = [b for b in target.bombs if not b['fused']]
    logger.debug(f"Bomb detonation: {stacks} stacks on {target.get_display_name()} for {dealt}")
    return dealt


def _reduce_skyhook_cooldown(user: 'Unit', stacks_detonated: int) -> None:
    """Refund SKYHOOK's cooldown by the stacks just detonated (the flow engine)."""
    if stacks_detonated <= 0:
        return
    refund = stacks_detonated * SKYHOOK_REFUND_PER_STACK
    for skill in user.active_skills:
        if skill.name == SKYHOOK_SKILL_NAME:
            if skill.current_cooldown > 0:
                skill.current_cooldown = max(0, skill.current_cooldown - refund)
            break


class RotorGraft(PassiveSkill):
    """Keeps one leashed quadcopter drone in the field; it mirrors its owner's plants."""

    def __init__(self):
        super().__init__(
            name="Rotor Graft",
            key="R",
            description="Fields a leashed quadcopter drone whose attacks graft a bomb. The drone regenerates a few turns after it is destroyed."
        )

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        # Drone spawn/regeneration/leash are reconciled by the engine each turn
        # (it needs to add units to the board, which a passive can't cleanly do).
        pass


class InoculantSkill(ActiveSkill):
    """Strike that deals flat damage and grafts a bomb onto a nearby enemy (range 2)."""

    def __init__(self):
        super().__init__(
            name="Inoculant",
            key="I",
            description="Strike an enemy within 2 tiles for normal damage and graft a bomb onto them (up to 4).",
            target_type=TargetType.ENEMY,
            cooldown=1,
            range_=2
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

        immune = target.is_immune_to_effects()
        target_def = target.get_effective_stats()['defense']
        damage = max(1, STRIKE_DAMAGE - target_def)
        dealt = target.deal_damage(damage)
        added = plant_bomb(target, 1)

        if immune:
            message_log.add_message(
                f"{user.get_display_name()} strikes {target.get_display_name()} for {dealt}, but the bomb finds no purchase",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} strikes {target.get_display_name()} for {dealt} and grafts a bomb ({len(target.bombs)})",
                MessageType.ABILITY,
                player=user.player
            )
            if added == 0:
                message_log.add_message(
                    f"{target.get_display_name()} is already saturated with bombs",
                    MessageType.ABILITY,
                    player=user.player
                )
        return True


class DroneInoculantSkill(InoculantSkill):
    """The ORDNANCE DRONE's own copy of Inoculant. Behaves identically to the graft's for
    now, but is a SEPARATE class so its numbers can be balanced independently later. Shown
    as "Inoculant" on the front end, but uses its own drone-fitting skill icon."""

    def __init__(self):
        # Re-run the ActiveSkill constructor with the same parameters as InoculantSkill,
        # but with the drone's own icon. (Bypasses InoculantSkill.__init__, which would
        # hardcode the graft's icon.) Override range/cooldown/etc here in the future to
        # diverge the drone's Inoculant from the graft's.
        ActiveSkill.__init__(
            self,
            name="Inoculant",
            key="I",
            description="Strike an enemy within 2 tiles for normal damage and graft a bomb onto them (up to 4).",
            target_type=TargetType.ENEMY,
            cooldown=1,
            range_=2,
            icon_name="drone_inoculant",
        )


class SkyhookSkill(ActiveSkill):
    """The drone hauls him to a new position (aerial extraction), slamming down to strike
    and graft a bomb onto every adjacent enemy. Requires a living drone; refunded by detonations."""

    def __init__(self):
        super().__init__(
            name="Skyhook",
            key="S",
            description="The drone lifts you to any empty position within range, ignoring pathing, then slams down to strike and graft a bomb onto every enemy in the surrounding tiles. Requires a living drone. Cooldown is refunded when bombs detonate.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=4
        )

    def _has_living_drone(self, user: 'Unit') -> bool:
        drone = getattr(user, 'drone', None)
        return bool(drone and drone.is_alive())

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        # Gated on the drone: no drone, no extraction (it regenerates in a few turns).
        if not self._has_living_drone(user):
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
        # The skyhook IS the movement — don't walk first.
        user.move_target = None
        user.vault_target_indicator = target_pos  # reuse the leap indicator
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        message_log.add_message(
            f"{user.get_display_name()} signals the drone for a skyhook to ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        ty, tx = target_pos
        user.vault_target_indicator = None

        # The drone hauls him to the landing tile (teleport — flies over everything).
        if game.get_unit_at(ty, tx) is not None:
            message_log.add_message(
                f"{user.get_display_name()}'s skyhook aborts - no room to land!",
                MessageType.WARNING,
                player=user.player
            )
            return False
        game._remove_from_unit_grid(user)
        user.y, user.x = ty, tx
        game._update_unit_grid(user)
        # The drone carried him here, so it lands ADJACENT to him at the new position.
        game._snap_drone_adjacent(user, ui)

        message_log.add_message(
            f"{user.get_display_name()} is lifted across the field by the drone",
            MessageType.ABILITY,
            player=user.player
        )

        # Arrival slam: strike + graft a bomb onto EVERY enemy in the 8 adjacent tiles
        # around the landing point. Snapshot the unit list since the strikes can change
        # board state.
        for enemy in list(game.units):
            if (enemy.is_alive() and enemy.player != user.player
                    and game.chess_distance(user.y, user.x, enemy.y, enemy.x) <= 1
                    and game.can_target_unit(user, enemy)):
                immune = enemy.is_immune_to_effects()
                target_def = enemy.get_effective_stats()['defense']
                damage = max(1, STRIKE_DAMAGE - target_def)
                dealt = enemy.deal_damage(damage)
                plant_bomb(enemy, 1)
                if immune:
                    message_log.add_message(
                        f"{user.get_display_name()} strikes {enemy.get_display_name()} on arrival for {dealt}, but the bomb finds no purchase",
                        MessageType.ABILITY,
                        player=user.player
                    )
                else:
                    message_log.add_message(
                        f"{user.get_display_name()} grafts a bomb onto {enemy.get_display_name()} on arrival for {dealt} ({len(enemy.bombs)})",
                        MessageType.ABILITY,
                        player=user.player
                    )
        return True


class HarvestSkill(ActiveSkill):
    """Detonate every fused bomb on the field for %max-HP damage; refunds MERIDIAN CUT."""

    def __init__(self):
        super().__init__(
            name="Harvest",
            key="H",
            description="Detonate all fused bombs on the field. Each stack deals a percent of the target's max HP that scales up with the size of the body — devastating against tanks, weak against small units. Refunds Skyhook's cooldown per stack.",
            target_type=TargetType.SELF,
            cooldown=3,
            range_=0
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        # Usable only if at least one fused bomb exists on an enemy.
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
            f"{user.get_display_name()} prepares to touch off the bombs",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        total_stacks = 0
        # Record where the bombs go off BEFORE detonation consumes them, so the
        # graphical layer can fire its explosions on the right tiles (the animation
        # runs after execute(), when the bombs have already been cleared).
        detonations = []  # list of (y, x, stacks)
        for target in list(game.units):
            if not (target.is_alive() and target.player != user.player):
                continue
            fused = fused_count(target)
            if fused <= 0:
                continue
            detonations.append((target.y, target.x, fused))
            # Detonate consumes the fused bombs; any unfused remain on the target.
            dealt = detonate_fused(target, game)
            total_stacks += fused
            message_log.add_message(
                f"{target.get_display_name()}'s bombs detonate for {dealt}",
                MessageType.ABILITY,
                player=user.player
            )
        user.last_harvest_data = {'detonations': detonations}

        if total_stacks == 0:
            return False

        _reduce_skyhook_cooldown(user, total_stacks)
        message_log.add_message(
            f"{user.get_display_name()} reaps the graft",
            MessageType.ABILITY,
            player=user.player
        )
        return True
