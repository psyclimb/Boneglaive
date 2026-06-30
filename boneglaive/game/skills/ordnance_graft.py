#!/usr/bin/env python3
"""Skills for ORDNANCE GRAFT — the sapper who grafts %HP bombs and touches them off."""

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
# JOUNCE is the drone-less fallback for Skyhook: when the quadcopter dies, Skyhook is
# swapped out of his kit for Jounce (a grappling-hook line-pull) and swapped back when the
# drone regenerates (see the engine drone death/spawn hooks). It shares Skyhook's arrival
# payload (the slam) and the Crash Landing upgrade, so several places must treat the two
# names as the same kit slot. JOUNCE_RANGE < Skyhook's range_ (4): a weaker reach.
JOUNCE_SKILL_NAME = "Jounce"
JOUNCE_RANGE = 3
# Both names occupy the one "leap" slot; helpers that find it by name accept either.
LEAP_SLOT_NAMES = (SKYHOOK_SKILL_NAME, JOUNCE_SKILL_NAME)
# Flat base damage for his strikes (Inoculant / Skyhook arrival). NOT ATK-scaled — his
# damage identity is the bombs, not the strike. DEF/PRT still reduce it via deal_damage.
STRIKE_DAMAGE = 2

# --- Upgrade tunables (the four skill upgrades; see upgrades.py / SKILL_UPGRADES) ---
# Booster Charge (Inoculant): bombs grafted per strike on an already-bombed target.
INOCULANT_BOOSTED_PLANT = 2
# Crash Landing (Skyhook): the arrival slam can refund its own cooldown via its
# detonations, but never below this floor — it can't perpetually re-launch itself.
SKYHOOK_SELF_REFUND_FLOOR = 1
# Chain Reaction (Harvest): a detonation kill re-grafts and immediately detonates one
# fused bomb onto the nearest enemy within this Chebyshev radius (one chain per kill).
CHAIN_REACTION_RANGE = 2


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


def _resolve_detonation_death(target: 'Unit', game: 'Game', killer: Optional['Unit'],
                              ui, cause: str) -> None:
    """If a detonation just killed `target`, run the engine's centralized death handling.

    `deal_damage` reaches 0 HP through the Unit.hp setter, which fires the unit-side
    `_handle_death` (GP award + DeadUnit/respawn) and removes the unit from `game.units`.
    But that path does NOT run the per-unit DEATH EFFECTS that live in
    `Game.handle_unit_death` (Rail Genesis explosion + rail cleanup, Dominion kill credit,
    Bone Tithe, Derelict/Valuation-Oracle cleanup, doppelganger chains, ...). The engine's
    post-skill death sweep can't pick these up either, because the victim is already gone
    from `game.units` by the time it runs. So we dispatch handle_unit_death here, on the
    direct reference, mirroring the basic-attack kill path. The `_engine_death_handled`
    guard keeps any later sweep from double-processing the same death."""
    if target.hp <= 0 and not getattr(target, '_engine_death_handled', False):
        game.handle_unit_death(target, killer_unit=killer, cause=cause, ui=ui)


def detonate_fused(target: 'Unit', game: 'Game', killer: Optional['Unit'] = None, ui=None,
                   cause: str = "detonation") -> int:
    """Detonate and remove all FUSED bombs on target for %max-HP damage (ignores DEF;
    PRT still applies via deal_damage). Unfused bombs remain. Returns damage dealt.

    A lethal detonation routes the kill through Game.handle_unit_death so on-death
    effects fire; pass `killer` (the ORDNANCE_GRAFT) for kill attribution."""
    stacks = fused_count(target)
    if stacks <= 0:
        return 0
    per_stack = int(round(target.max_hp * bomb_pct(target)))
    total = max(1, per_stack) * stacks
    dealt = target.deal_damage(total)
    target.bombs = [b for b in target.bombs if not b['fused']]
    logger.debug(f"Bomb detonation: {stacks} stacks on {target.get_display_name()} for {dealt}")
    _resolve_detonation_death(target, game, killer, ui, cause)
    return dealt


def detonate_n_stacks(target: 'Unit', n: int, game: 'Game', killer: Optional['Unit'] = None,
                      ui=None, cause: str = "detonation") -> int:
    """Detonate up to `n` FUSED bombs on target (same %max-HP-per-stack math as
    detonate_fused, but a bounded count) and remove exactly those. Used by Chain Reaction
    so a chained blast consumes only its own seed, leaving any pre-existing fused bombs.
    Returns damage dealt. A lethal detonation routes the kill through
    Game.handle_unit_death (see detonate_fused)."""
    available = fused_count(target)
    stacks = min(max(0, n), available)
    if stacks <= 0:
        return 0
    per_stack = max(1, int(round(target.max_hp * bomb_pct(target))))
    dealt = target.deal_damage(per_stack * stacks)
    # Remove exactly `stacks` fused bombs (leave the rest fused).
    removed = 0
    kept = []
    for b in target.bombs:
        if b['fused'] and removed < stacks:
            removed += 1
            continue
        kept.append(b)
    target.bombs = kept
    _resolve_detonation_death(target, game, killer, ui, cause)
    return dealt


def _reduce_skyhook_cooldown(user: 'Unit', stacks_detonated: int) -> None:
    """Refund the leap skill's cooldown by the stacks just detonated (the flow engine).
    Works whether the "S" slot currently holds Skyhook or its drone-less Jounce fallback —
    both share the same detonation-refund identity."""
    if stacks_detonated <= 0:
        return
    refund = stacks_detonated * SKYHOOK_REFUND_PER_STACK
    for skill in user.active_skills:
        if skill.name in LEAP_SLOT_NAMES:
            if skill.current_cooldown > 0:
                skill.current_cooldown = max(0, skill.current_cooldown - refund)
            break


def _arrival_slam(user: 'Unit', game: 'Game', skill: 'ActiveSkill', ui=None) -> None:
    """The shared arrival payload for the leap slot (Skyhook AND Jounce): once `user` is
    standing on the landing tile, strike + graft one bomb onto EVERY enemy in the 8 adjacent
    tiles. With the Crash Landing upgrade (learned under the Skyhook key — it covers whichever
    skill occupies the slot) the slam also detonates each struck enemy's already-fused bombs,
    refunding `skill`'s cooldown per stack (floored so it can't perpetually re-launch). Records
    the planted tiles into user.last_skyhook_data for the graphical graft-in (harmless headless).

    Caller is responsible for getting `user` onto the tile (teleport for Skyhook, line-pull for
    Jounce) and for the drone before calling this."""
    from boneglaive.game.upgrades import UpgradeManager
    # Crash Landing is stored under the Skyhook key (the slot's canonical upgrade); honor it
    # for whichever skill currently fills the slot.
    crash_landing = UpgradeManager.is_skill_upgraded(user, SKYHOOK_SKILL_NAME)
    crash_stacks = 0

    plant_tiles = []
    for enemy in list(game.units):
        if (enemy.is_alive() and enemy.player != user.player
                and game.chess_distance(user.y, user.x, enemy.y, enemy.x) <= 1
                and game.can_target_unit(user, enemy)):
            immune = enemy.is_immune_to_effects()
            target_def = enemy.get_effective_stats()['defense']
            damage = max(1, STRIKE_DAMAGE - target_def)
            dealt = enemy.deal_damage(damage)
            if plant_bomb(enemy, 1) > 0:
                plant_tiles.append((enemy.y, enemy.x))
            if immune:
                message_log.add_message(
                    f"{user.get_display_name()} comes down hard on {enemy.get_display_name()} for #DAMAGE_{dealt}# damage",
                    MessageType.ABILITY,
                    player=user.player
                )
                message_log.add_message(
                    f"{enemy.get_display_name()} is immune to bomb due to Stasiality",
                    MessageType.ABILITY,
                    player=enemy.player
                )
            else:
                message_log.add_message(
                    f"{user.get_display_name()}'s landing grafts a spiked cluster onto {enemy.get_display_name()} for #DAMAGE_{dealt}# damage ({len(enemy.bombs)})",
                    MessageType.ABILITY,
                    player=user.player
                )
            # The just-planted bomb is unfused, so this only blows bombs already fused from
            # prior turns — the fresh seed survives. A lethal detonation is routed through
            # handle_unit_death inside detonate_fused (on-death effects fire).
            if crash_landing:
                fused_here = fused_count(enemy)
                if fused_here > 0:
                    blown = detonate_fused(enemy, game, killer=user, ui=ui)
                    crash_stacks += fused_here
                    message_log.add_message(
                        f"{enemy.get_display_name()}'s clusters detonate on landing for #DAMAGE_{blown}# damage",
                        MessageType.ABILITY,
                        player=user.player
                    )

    # Hand the planted tiles to the graphical layer (the leap animation plays a graft-in on
    # each after the slam). Always overwrite so a recast can't reuse stale.
    user.last_skyhook_data = {'plants': plant_tiles}

    # Refund the cooldown for the detonations this slam set off — but never below the
    # self-refund floor, so Crash Landing can't perpetually re-launch the slot.
    if crash_stacks > 0:
        _reduce_skyhook_cooldown(user, crash_stacks)
        skill.current_cooldown = max(SKYHOOK_SELF_REFUND_FLOOR, skill.current_cooldown)


def _swap_leap_skill(graft: 'Unit', from_name: str, make_to) -> None:
    """In-place swap of the graft's "S" leap slot from the skill named `from_name` to a
    fresh skill built by `make_to()`, carrying the current cooldown across (so losing the
    drone mid-cooldown doesn't hand a free leap, and vice-versa). No-op if the from-skill
    isn't present (already swapped, or the slot holds something else). Mirrors the
    DELPHIC Divine Depreciation<->Deft Reroll runtime swap; active_skills is a per-unit
    list of fresh instances, so this never touches other units."""
    for i, skill in enumerate(graft.active_skills):
        if skill.name == from_name:
            replacement = make_to()
            replacement.current_cooldown = skill.current_cooldown
            graft.active_skills[i] = replacement
            return


def swap_to_jounce(graft: 'Unit') -> None:
    """Drone died: replace Skyhook with its drone-less Jounce fallback."""
    _swap_leap_skill(graft, SKYHOOK_SKILL_NAME, JounceSkill)


def swap_to_skyhook(graft: 'Unit') -> None:
    """Drone returned: restore Skyhook in place of the Jounce fallback."""
    _swap_leap_skill(graft, JOUNCE_SKILL_NAME, SkyhookSkill)


class Quadcopter(PassiveSkill):
    """Keeps one leashed quadcopter drone in the field — a second body the player pilots."""

    def __init__(self):
        super().__init__(
            name="Quadcopter",
            key="R",
            description="Fields a leashed quadcopter drone you pilot as a second body; it carries its own Inoculant to graft bombs. The drone regenerates a few turns after it is destroyed."
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
            f"{user.get_display_name()} readies a spiked cluster",
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
        # Booster Charge upgrade: a strike on a target that ALREADY carries a bomb seats
        # an extra one (rewards committing to a single body — reaches a one-shot stack
        # faster). 'already carries a bomb' is read before planting.
        from boneglaive.game.upgrades import UpgradeManager
        boosted = UpgradeManager.is_skill_upgraded(user, "Inoculant") and len(target.bombs) > 0
        amount = INOCULANT_BOOSTED_PLANT if boosted else 1
        added = plant_bomb(target, amount)
        # Tell the graphical layer how many bombs actually seated, so the Inoculant
        # animation can show a graft-in PER bomb (Booster Charge seats two). Harmless in
        # headless mode (nothing reads it). Stored on the user, like last_harvest_data.
        user.last_inoculant_data = {'planted': added}

        if immune:
            message_log.add_message(
                f"{user.get_display_name()} grafts a spiked cluster onto {target.get_display_name()} for #DAMAGE_{dealt}# damage",
                MessageType.ABILITY,
                player=user.player
            )
            message_log.add_message(
                f"{target.get_display_name()} is immune to bomb due to Stasiality",
                MessageType.ABILITY,
                player=target.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} grafts a spiked cluster onto {target.get_display_name()} for #DAMAGE_{dealt}# damage; it bites home ({len(target.bombs)})",
                MessageType.ABILITY,
                player=user.player
            )
            if added == 0:
                message_log.add_message(
                    f"{target.get_display_name()} is already studded with bombs",
                    MessageType.ABILITY,
                    player=user.player
                )
        return True


class DroneInoculantSkill(InoculantSkill):
    """The QUADCOPTER's own copy of Inoculant. Behaves identically to the graft's for
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

    def _find_landing_position(self, game: 'Game', target_pos: tuple) -> Optional[tuple]:
        """Find where the graft actually comes down. The landing tile was empty when
        Skyhook was queued, but a unit may have moved onto it, or terrain/furniture may
        have spawned there, before this resolves. If the tile is still open he lands on
        it; otherwise he twists down onto the nearest open adjacent tile (he's hauled in
        on a line, so a one-tile sidestep is fine). Returns None only if he's completely
        boxed in. Mirrors Glaiveman Vault's displacement so the two leaps behave alike."""
        from boneglaive.utils.coordinates import get_adjacent_positions

        ty, tx = target_pos

        def is_open(y: int, x: int) -> bool:
            if not game.is_valid_position(y, x):
                return False
            if not game.map.is_passable(y, x):
                return False
            if game.get_unit_at(y, x) is not None:
                return False
            # Don't drop onto a tile another unit is already moving/leaping into this
            # same turn — that would just create a collision the engine has to untangle.
            for other in game.units:
                if not other.is_alive():
                    continue
                if getattr(other, 'move_target', None) == (y, x):
                    return False
                if getattr(other, 'vault_target_indicator', None) == (y, x):
                    return False
                if getattr(other, 'teleport_target_indicator', None) == (y, x):
                    return False
            return True

        # The intended tile is still best if it freed up (or never got taken).
        if is_open(ty, tx):
            return (ty, tx)

        # Otherwise sidestep to the nearest open adjacent tile.
        for adj_y, adj_x in get_adjacent_positions(ty, tx):
            if is_open(adj_y, adj_x):
                return (adj_y, adj_x)

        return None

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

        # The drone is the carrier: if it died after this was queued (e.g. an enemy killed
        # it earlier in this turn's resolution), there's nothing to haul him — abort. The
        # drone-gate in can_use() isn't enough; the state can change before we execute.
        if not self._has_living_drone(user):
            message_log.add_message(
                f"{user.get_display_name()}'s skyhook fails - the drone is gone!",
                MessageType.WARNING,
                player=user.player
            )
            self.current_cooldown = 0  # refund — the skill did nothing
            return False

        # The drone hauls him to the landing tile (teleport — flies over everything).
        # The tile was clear when this was queued, but a unit may have moved onto it or
        # terrain/furniture may have spawned there since. Resolve the real landing tile:
        # the intended one if it's still open, else the nearest open adjacent tile. Only
        # a complete box-in aborts the leap.
        landing = self._find_landing_position(game, target_pos)
        if landing is None:
            message_log.add_message(
                f"{user.get_display_name()}'s skyhook aborts - no room to land!",
                MessageType.WARNING,
                player=user.player
            )
            self.current_cooldown = 0  # refund — the skill did nothing
            return False
        displaced = landing != (ty, tx)
        land_y, land_x = landing
        game._remove_from_unit_grid(user)
        user.y, user.x = land_y, land_x
        game._update_unit_grid(user)
        # Tell the graphical layer the carry arc ends on the displaced tile (the Skyhook
        # animation reads vault_displaced_to, same as Vault) so the sprite doesn't fly to
        # the obstruction. Harmless in headless mode (no animation reads it).
        if displaced:
            user.vault_displaced_to = (land_y, land_x)
        # The drone carried him here, so it lands ADJACENT to him at the new position.
        game._snap_drone_adjacent(user, ui)

        if displaced:
            message_log.add_message(
                f"{user.get_display_name()} is hauled across the field, twisting down beside the obstruction to ({land_y}, {land_x})",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} is hauled across the field on the drone's line",
                MessageType.ABILITY,
                player=user.player
            )

        # Arrival slam: strike + graft a bomb onto every adjacent enemy (and, with Crash
        # Landing, detonate their fused stacks + refund). Shared with Jounce.
        _arrival_slam(user, game, self, ui)
        return True


class JounceSkill(ActiveSkill):
    """Skyhook's drone-less fallback (swapped into the "S" slot while the quadcopter is
    dead). He fires his grappling hook at a unit, furniture, or solid terrain he can SEE,
    and reels himself in a STRAIGHT LINE to stop just short of it — then performs the same
    arrival slam as Skyhook (strike + graft a bomb on every adjacent enemy; shares Crash
    Landing + the detonation cooldown refund). Weaker than Skyhook: shorter range, requires
    line of sight, can't fly over obstacles, and he stops adjacent to the anchor rather than
    on a chosen tile."""

    def __init__(self):
        super().__init__(
            name=JOUNCE_SKILL_NAME,
            key="S",
            description="Grapple a unit, furniture, or solid terrain in your line of sight and reel yourself in a straight line to stop beside it, then slam down to strike and graft a bomb onto every adjacent enemy. Skyhook's fallback while the drone is down. Cooldown is refunded when bombs detonate.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=JOUNCE_RANGE
        )

    def _is_anchor(self, game: 'Game', y: int, x: int) -> bool:
        """A tile is a valid grapple anchor if it holds something to hook onto: a living
        unit, a piece of furniture, or solid (LOS-blocking) terrain. A plain empty/passable
        tile is NOT an anchor — there's nothing to grab."""
        if not game.is_valid_position(y, x):
            return False
        if game.get_unit_at(y, x) is not None:
            return True
        # Solid terrain that blocks sight is grabbable (walls, pillars, pylons, ...).
        if game.map.blocks_line_of_sight(y, x):
            return True
        # Furniture blocks movement but not sight — still a hookable object.
        if not game.map.is_passable(y, x):
            return True
        return False

    def _launch_origin(self, user: 'Unit') -> tuple:
        """Where the grapple reels FROM. A queued move (move_target) is honored while the
        action is being planned; once use() consumes/clears it, the captured destination
        (jounce_launch_from) stands in; otherwise his current tile. Keeps can_use's range/LOS
        checks and execute's landing resolution measuring from the SAME origin."""
        if user.move_target:
            return user.move_target
        if getattr(user, 'jounce_launch_from', None):
            return user.jounce_launch_from
        return (user.y, user.x)

    def _resolve_landing(self, game: 'Game', user: 'Unit', target_pos: tuple) -> Optional[tuple]:
        """Walk the straight line from the user toward the anchor and return the tile he
        reels to: the LAST open (valid + passable + unoccupied) tile before the anchor. He
        stops as soon as the path is blocked — by the anchor itself or anything in front of
        it. Returns the user's own tile if the anchor is already adjacent (nowhere to pull,
        but he can still slam in place), or None if the target isn't a valid anchor / the
        very first step toward it is blocked by a different obstacle with no progress."""
        from boneglaive.utils.coordinates import Position, get_line

        ty, tx = target_pos
        if not self._is_anchor(game, ty, tx):
            return None

        # Reel origin: the unit's intended position. While the action is still being
        # planned/validated (UI + AI), a queued move lives in move_target. By execute()
        # time use() has cleared move_target (the leap replaces the walk), so fall back to
        # the destination it captured in jounce_launch_from — NOT the stale pre-move tile —
        # so the line is walked from where he ends up, not where he started the turn.
        from_y, from_x = self._launch_origin(user)
        # If the reel originates from a queued move destination (not his current tile), that
        # tile must still be free to stand on — the physical move never ran, so nothing else
        # confirmed it's open. If it got blocked since queueing, the whole move+reel fails.
        if (from_y, from_x) != (user.y, user.x):
            if not game.map.is_passable(from_y, from_x):
                return None
            occupant = game.get_unit_at(from_y, from_x)
            if occupant is not None and occupant is not user:
                return None
        path = get_line(Position(from_y, from_x), Position(ty, tx))
        # path[0] is the user's tile; walk outward and keep the last open tile we reach.
        landing = (from_y, from_x)
        for pos in path[1:]:
            py, px = pos.y, pos.x
            if (py, px) == (ty, tx):
                break  # reached the anchor tile — stop just short (don't enter it)
            if not game.is_valid_position(py, px):
                break
            if not game.map.is_passable(py, px):
                break  # an obstacle in front of the anchor halts the reel
            if game.get_unit_at(py, px) is not None:
                break  # someone is in the way
            landing = (py, px)
        return landing

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        ty, tx = target_pos
        if not game.is_valid_position(ty, tx):
            return False
        from_y, from_x = self._launch_origin(user)
        # Range is measured to the anchor (what he hooks), within Jounce's shorter reach.
        if game.chess_distance(from_y, from_x, ty, tx) > self.range:
            return False
        # Must be able to SEE the anchor (the hook needs a clear line). LOS checks the
        # tiles BETWEEN endpoints, so a wall/unit AT the target is still visible to grab.
        if not game.has_line_of_sight(from_y, from_x, ty, tx):
            return False
        # The target must actually be a grabbable anchor with a resolvable landing.
        if self._resolve_landing(game, user, target_pos) is None:
            return False
        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        # The grapple-pull IS the movement — don't walk first. But if a move was queued,
        # remember its destination as the reel origin: he hooks and pulls FROM where he
        # meant to move to, not from his pre-move tile. Captured before move_target is
        # cleared; consumed in execute(). (No queued move -> reel from his current tile.)
        user.jounce_launch_from = user.move_target if user.move_target else (user.y, user.x)
        user.move_target = None
        user.vault_target_indicator = target_pos  # reuse the leap indicator
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        message_log.add_message(
            f"{user.get_display_name()} fires a grappling hook toward ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        user.vault_target_indicator = None

        # Re-resolve the landing at execute time — the board may have changed since this was
        # queued (the anchor moved/died, the lane got blocked). If it's no longer a valid
        # grapple, abort and refund (the skill did nothing). _resolve_landing reels from the
        # destination use() captured (jounce_launch_from); consume it here so it can't carry
        # into a later turn.
        launch_from = getattr(user, 'jounce_launch_from', None)
        pre_move_pos = (user.y, user.x)
        landing = self._resolve_landing(game, user, target_pos)
        user.jounce_launch_from = None
        # Hand the animation the tile he reeled FROM when it differs from where the sprite
        # currently sits (i.e. a move was queued). The Jounce animation walks the sprite to
        # this launch tile first, THEN fires the grapple from it, so the trajectory matches
        # what the player aimed (the move ghost), instead of firing from his pre-move tile.
        # Cleared otherwise so a stale launch tile never leaks into a plain in-place Jounce.
        user.jounce_anim_from = launch_from if (launch_from and launch_from != pre_move_pos) else None
        if landing is None:
            user.jounce_anim_from = None  # nothing happened — don't walk the sprite anywhere
            message_log.add_message(
                f"{user.get_display_name()}'s grapple finds no purchase!",
                MessageType.WARNING,
                player=user.player
            )
            self.current_cooldown = 0  # refund — the skill did nothing
            return False

        land_y, land_x = landing
        moved = (land_y, land_x) != (user.y, user.x)
        if moved:
            game._remove_from_unit_grid(user)
            user.y, user.x = land_y, land_x
            game._update_unit_grid(user)
            # Tell the graphical layer where the pull ends (the animation reads this, like
            # Skyhook's displacement). Harmless headless.
            user.vault_displaced_to = (land_y, land_x)
            message_log.add_message(
                f"{user.get_display_name()} reels in along the line to ({land_y}, {land_x})",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} hauls hard on the line, already at the anchor",
                MessageType.ABILITY,
                player=user.player
            )

        # Same arrival slam as Skyhook (strike + graft on all adjacent enemies; Crash
        # Landing detonates + refunds). Shares the upgrade and the flow engine.
        _arrival_slam(user, game, self, ui)
        return True


class HarvestSkill(ActiveSkill):
    """Detonate every fused bomb on the field for %max-HP damage; refunds Skyhook's cooldown."""

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
            f"{user.get_display_name()} thumbs the firing key",
            MessageType.ABILITY,
            player=user.player
        )
        self.current_cooldown = self.cooldown
        return True

    def _chain_target(self, user: 'Unit', dead: 'Unit', game: 'Game', already: set):
        """Chain Reaction: the nearest living enemy within CHAIN_REACTION_RANGE of a unit
        just killed by a detonation, that hasn't already received a chain this Harvest.
        Returns the unit or None."""
        best = None
        best_d = None
        for u in game.units:
            if not (u.is_alive() and u.player != user.player) or u is dead or id(u) in already:
                continue
            d = game.chess_distance(dead.y, dead.x, u.y, u.x)
            if d > CHAIN_REACTION_RANGE:
                continue
            if best_d is None or d < best_d:
                best_d, best = d, u
        return best

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        from boneglaive.game.upgrades import UpgradeManager
        chain_reaction = UpgradeManager.is_skill_upgraded(user, "Harvest")
        total_stacks = 0
        # Record where the bombs go off BEFORE detonation consumes them, so the
        # graphical layer can fire its explosions on the right tiles (the animation
        # runs after execute(), when the bombs have already been cleared).
        detonations = []  # list of (y, x, stacks)
        chain_plants = []  # tiles where Chain Reaction grafts a fresh seed (for the graft-in VFX)
        # Victims that have already received a chain seed this Harvest (so two separate
        # kills can't pile chains onto the same body).
        chain_hit = set()
        for target in list(game.units):
            if not (target.is_alive() and target.player != user.player):
                continue
            fused = fused_count(target)
            if fused <= 0:
                continue
            detonations.append((target.y, target.x, fused))
            # Detonate consumes the fused bombs; any unfused remain on the target.
            # A lethal blast routes the kill through handle_unit_death (on-death effects).
            dealt = detonate_fused(target, game, killer=user, ui=ui)
            total_stacks += fused
            message_log.add_message(
                f"{target.get_display_name()}'s clusters detonate for #DAMAGE_{dealt}# damage",
                MessageType.ABILITY,
                player=user.player
            )
            # Chain Reaction upgrade: a detonation KILL re-grafts and immediately blows a
            # SINGLE fresh bomb on the nearest enemy in range (once per kill — the chained
            # blast does not itself chain, so the cascade is bounded). It consumes only its
            # own seed (detonate_n_stacks ..., 1), leaving the victim's pre-existing fused
            # bombs for the normal pass. The seed scales off the victim's HP, so it still
            # favours big bodies.
            if chain_reaction and target.hp <= 0:
                victim = self._chain_target(user, target, game, chain_hit)
                if victim is not None and plant_bomb(victim, 1) > 0:
                    chain_hit.add(id(victim))
                    chain_plants.append((victim.y, victim.x))  # graft-in VFX on the seed
                    arm_bombs(victim)  # arm the seed so it can detonate now
                    chain_dmg = detonate_n_stacks(victim, 1, game, killer=user, ui=ui)
                    total_stacks += 1
                    detonations.append((victim.y, victim.x, 1))
                    message_log.add_message(
                        f"the blast leaps to {victim.get_display_name()} for #DAMAGE_{chain_dmg}# damage",
                        MessageType.ABILITY,
                        player=user.player
                    )
        user.last_harvest_data = {'detonations': detonations, 'chain_plants': chain_plants}

        if total_stacks == 0:
            return False

        _reduce_skyhook_cooldown(user, total_stacks)
        message_log.add_message(
            f"{user.get_display_name()} brings in the harvest",
            MessageType.ABILITY,
            player=user.player
        )
        return True
