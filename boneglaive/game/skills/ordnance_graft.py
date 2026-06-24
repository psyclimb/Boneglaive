#!/usr/bin/env python3
"""Skills for ORDNANCE GRAFT — the gunner who grafts %HP bombs and touches them off."""

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
    """Refund SKYHOOK's cooldown by the stacks just detonated (the flow engine)."""
    if stacks_detonated <= 0:
        return
    refund = stacks_detonated * SKYHOOK_REFUND_PER_STACK
    for skill in user.active_skills:
        if skill.name == SKYHOOK_SKILL_NAME:
            if skill.current_cooldown > 0:
                skill.current_cooldown = max(0, skill.current_cooldown - refund)
            break


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
        if game.get_unit_at(ty, tx) is not None:
            message_log.add_message(
                f"{user.get_display_name()}'s skyhook aborts - no room to land!",
                MessageType.WARNING,
                player=user.player
            )
            self.current_cooldown = 0  # refund — the skill did nothing
            return False
        game._remove_from_unit_grid(user)
        user.y, user.x = ty, tx
        game._update_unit_grid(user)
        # The drone carried him here, so it lands ADJACENT to him at the new position.
        game._snap_drone_adjacent(user, ui)

        message_log.add_message(
            f"{user.get_display_name()} is hauled across the field on the drone's line",
            MessageType.ABILITY,
            player=user.player
        )

        # Crash Landing upgrade: the arrival slam also DETONATES the fused bombs already
        # on each enemy it strikes (read once up front). A high-risk burst: hook into
        # melee, blow the existing stack, leave a fresh seed for next time.
        from boneglaive.game.upgrades import UpgradeManager
        crash_landing = UpgradeManager.is_skill_upgraded(user, SKYHOOK_SKILL_NAME)
        crash_stacks = 0

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
                # The just-planted bomb is unfused, so this only blows bombs already fused
                # from prior turns — the fresh seed survives. A lethal detonation is routed
                # through handle_unit_death inside detonate_fused (on-death effects fire).
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

        # Refund the cooldown for the detonations this slam set off — but never below the
        # self-refund floor, so Crash Landing can't perpetually re-launch itself.
        if crash_stacks > 0:
            _reduce_skyhook_cooldown(user, crash_stacks)
            self.current_cooldown = max(SKYHOOK_SELF_REFUND_FLOOR, self.current_cooldown)
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
                    arm_bombs(victim)  # arm the seed so it can detonate now
                    chain_dmg = detonate_n_stacks(victim, 1, game, killer=user, ui=ui)
                    total_stacks += 1
                    detonations.append((victim.y, victim.x, 1))
                    message_log.add_message(
                        f"the blast leaps to {victim.get_display_name()} for #DAMAGE_{chain_dmg}# damage",
                        MessageType.ABILITY,
                        player=user.player
                    )
        user.last_harvest_data = {'detonations': detonations}

        if total_stacks == 0:
            return False

        _reduce_skyhook_cooldown(user, total_stacks)
        message_log.add_message(
            f"{user.get_display_name()} brings in the harvest",
            MessageType.ABILITY,
            player=user.player
        )
        return True
