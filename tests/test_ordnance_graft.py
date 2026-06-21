#!/usr/bin/env python3
"""Integration tests for ORDNANCE GRAFT — the bomb mechanics and the drone.

Drives the engine directly (ui=None) and asserts behaviour, not just absence of
crashes: bomb plant/cap/fuse timing, detonation %max-HP math, the Skyhook
cooldown refund, partial vs. full cleanse, and drone spawn/leash/regen.

Run with: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_ordnance_graft.py
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
logging.disable(logging.CRITICAL)

from boneglaive.game.engine import Game
from boneglaive.utils.constants import (
    UnitType, HEIGHT, WIDTH, BOMB_MAX_STACKS, BOMB_LIFESPAN,
    ORDNANCE_DRONE_REGEN, ORDNANCE_DRONE_LEASH,
)
from boneglaive.game.skills.ordnance_graft import (
    plant_bomb, fused_count, arm_bombs, tick_bombs, detonate_fused,
    remove_one_bomb, clear_bombs, bomb_pct,
    BOMB_PCT_FLOOR, BOMB_PCT_REF_HP, BOMB_PCT_PER_HP, STRIKE_DAMAGE,
)

results = []


def check(name, cond, note=""):
    results.append((name, bool(cond), note))


def fresh_game(map_name="lime_foyer"):
    g = Game(skip_setup=True, map_name=map_name)
    g.units = []
    g.unit_grid = {}
    return g


def free_tiles(g, n):
    out = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if g.map.can_place_unit(y, x) and g.get_unit_at(y, x) is None:
                out.append((y, x))
                if len(out) >= n:
                    return out
    return out


def place(g, utype, player, y, x):
    g.add_unit(utype, player, y, x)
    return g.get_unit_at(y, x)


def expected_detonation(target, stacks):
    """Mirror the production formula independently (HP-scaling %, round, floor-1, x stacks)."""
    pct = BOMB_PCT_FLOOR + max(0, target.max_hp - BOMB_PCT_REF_HP) * BOMB_PCT_PER_HP
    per = max(1, round(target.max_hp * pct))
    return per * stacks


# ---------------------------------------------------------------------------
# Bomb plant / cap / fuse
# ---------------------------------------------------------------------------

def test_plant_and_cap():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])

    added = plant_bomb(tgt, 1)
    check("plant_adds_one", added == 1 and len(tgt.bombs) == 1, f"added={added} n={len(tgt.bombs)}")
    check("plant_starts_unfused", fused_count(tgt) == 0, f"fused={fused_count(tgt)}")

    # Over-plant past the cap is clamped.
    plant_bomb(tgt, 10)
    check("cap_clamps", len(tgt.bombs) == BOMB_MAX_STACKS, f"n={len(tgt.bombs)} cap={BOMB_MAX_STACKS}")
    added_when_full = plant_bomb(tgt, 1)
    check("no_add_when_full", added_when_full == 0 and len(tgt.bombs) == BOMB_MAX_STACKS,
          f"added={added_when_full}")


def test_fuse_timing():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bomb(tgt, 2)
    check("unfused_on_plant", fused_count(tgt) == 0, f"fused={fused_count(tgt)}")
    arm_bombs(tgt)
    check("fused_after_arm", fused_count(tgt) == 2, f"fused={fused_count(tgt)}")


def test_bomb_expires_after_lifespan():
    """A bomb lingers BOMB_LIFESPAN turns then falls off. Each turn = one arm+tick of the
    bomb-owner's upkeep (modeled directly here)."""
    g = fresh_game()
    tgt = place(g, UnitType.INTERFERER, 2, *free_tiles(g, 1)[0])
    plant_bomb(tgt, 1)
    check("ttl_on_plant", tgt.bombs[0]['ttl'] == BOMB_LIFESPAN,
          f"ttl={tgt.bombs[0]['ttl']} (expect {BOMB_LIFESPAN})")
    # tick lifespan-1 times — still present
    for _ in range(BOMB_LIFESPAN - 1):
        arm_bombs(tgt); tick_bombs(tgt)
    check("alive_before_lifespan", len(tgt.bombs) == 1,
          f"count={len(tgt.bombs)} after {BOMB_LIFESPAN - 1} turns (should still be 1)")
    # the lifespan'th tick drops it
    arm_bombs(tgt); expired = tick_bombs(tgt)
    check("falls_off_at_lifespan", len(tgt.bombs) == 0 and expired == 1,
          f"count={len(tgt.bombs)} expired={expired} (should fall off on turn {BOMB_LIFESPAN})")


def test_grafting_refreshes_bomb_timers():
    """Grafting a fresh bomb tops up the WHOLE cluster's timer (keep striking, nothing
    decays)."""
    g = fresh_game()
    tgt = place(g, UnitType.INTERFERER, 2, *free_tiles(g, 1)[0])
    plant_bomb(tgt, 1)
    for _ in range(2):  # age the first bomb by 2
        arm_bombs(tgt); tick_bombs(tgt)
    check("aged_two", tgt.bombs[0]['ttl'] == BOMB_LIFESPAN - 2,
          f"ttl={tgt.bombs[0]['ttl']} (expect {BOMB_LIFESPAN - 2})")
    plant_bomb(tgt, 1)  # graft another -> refresh all
    check("all_refreshed", all(b['ttl'] == BOMB_LIFESPAN for b in tgt.bombs),
          f"ttls={[b['ttl'] for b in tgt.bombs]} (all should be {BOMB_LIFESPAN})")


def test_bomb_survives_harvest_cooldown():
    """A bomb outlives a full Harvest cooldown (3), so you can bank it between detonations."""
    g = fresh_game()
    tgt = place(g, UnitType.INTERFERER, 2, *free_tiles(g, 1)[0])
    plant_bomb(tgt, 1)
    for _ in range(3):  # a full Harvest cooldown's worth of turns
        arm_bombs(tgt); tick_bombs(tgt)
    check("survives_harvest_cd", len(tgt.bombs) == 1,
          f"count={len(tgt.bombs)} after 3 turns (a bomb must outlive the Harvest cd)")


def test_stasiality_immune_to_bomb():
    """A unit with stasiality (or effective stasiality) cannot be grafted with bombs.
    GRAYMAN's Stasiality passive blocks the status; the strike damage still lands."""
    g = fresh_game()
    ts = free_tiles(g, 1)
    gray = place(g, UnitType.GRAYMAN, 2, *ts[0])
    check("grayman_is_immune", gray.is_immune_to_effects(), "GRAYMAN should be immune")
    added = plant_bomb(gray, 3)
    check("plant_blocked_by_stasiality", added == 0 and len(gray.bombs) == 0,
          f"added={added} bombs={len(gray.bombs)} (should be 0)")

    # End-to-end: Inoculant (with drone) damages but plants nothing on the immune unit.
    g2 = fresh_game()
    ts2 = free_tiles(g2, 40)
    gy, gx = ts2[0]
    ey, ex = next((y, x) for (y, x) in ts2 if abs(y - gy) <= 1 and abs(x - gx) <= 1 and (y, x) != (gy, gx))
    graft = place(g2, UnitType.ORDNANCE_GRAFT, 1, gy, gx)
    gray2 = place(g2, UnitType.GRAYMAN, 2, ey, ex)
    g2.current_player = 1
    g2._process_ordnance_graft_upkeep()  # drone (its echo must also be blocked)
    inoc = next(s for s in graft.active_skills if s.name == "Inoculant")
    hp0 = gray2.hp
    inoc.execute(graft, (gray2.y, gray2.x), g2)
    check("inoculant_damages_immune", (hp0 - gray2.hp) > 0, f"damage={hp0 - gray2.hp} (strike still lands)")
    check("inoculant_plants_nothing_on_immune", len(gray2.bombs) == 0,
          f"bombs={len(gray2.bombs)} (graft AND drone echo blocked by stasiality)")


# ---------------------------------------------------------------------------
# Detonation math
# ---------------------------------------------------------------------------

def test_detonation_tank_math():
    """Full 4-stack on a 24-HP tank matches the HP-scaling formula and is lethal-tier."""
    g = fresh_game()
    ts = free_tiles(g, 1)
    tank = place(g, UnitType.POTPOURRIST, 2, *ts[0])  # 24 HP, the roster tank
    plant_bomb(tank, 4)
    arm_bombs(tank)
    raw = expected_detonation(tank, 4)            # raw formula damage (may overkill)
    hp0 = tank.hp
    dealt = detonate_fused(tank, g)
    # deal_damage returns ACTUAL damage, capped at the target's HP (no overkill).
    exp = min(raw, hp0)
    check("tank_math", dealt == exp and (hp0 - tank.hp) == exp,
          f"dealt={dealt} expected={exp} (raw={raw} capped at {hp0} HP; 24-HP tank, 4 stacks)")
    check("tank_burst_is_lethal_tier", raw >= tank.max_hp,
          f"4-stack raw {raw} vs {tank.max_hp} HP (should ~one-shot)")
    check("detonation_consumes_fused", len(tank.bombs) == 0, f"remaining={len(tank.bombs)}")


def test_detonation_curve_favours_big_bodies():
    """The anti-tank curve: a tank takes a strictly HIGHER % of its bar than a squishy
    from the same stack count, and the squishy is only lightly dented."""
    g = fresh_game()
    ts = free_tiles(g, 2)
    tank = place(g, UnitType.POTPOURRIST, 2, *ts[0])      # 24 HP
    squishy = place(g, UnitType.GRAYMAN, 2, *ts[1])       # 18 HP
    for u in (tank, squishy):
        plant_bomb(u, 4)
        arm_bombs(u)
    tank_max, squ_max = tank.max_hp, squishy.max_hp
    tank_dmg = detonate_fused(tank, g)
    squ_dmg = detonate_fused(squishy, g)
    tank_pct = tank_dmg / tank_max
    squ_pct = squ_dmg / squ_max
    check("tank_pct_exceeds_squishy_pct", tank_pct > squ_pct,
          f"tank {tank_dmg}/{tank_max}={tank_pct:.0%} vs squishy {squ_dmg}/{squ_max}={squ_pct:.0%}")
    # The squishy should survive a full 4-stack (anti-tank, weak into squishies).
    check("squishy_survives_full_stack", squ_dmg < squ_max,
          f"squishy 4-stack dealt {squ_dmg} of {squ_max} HP")


def test_detonation_ignores_def_respects_prt():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    base = tgt.defense
    tgt.defense = base + 5  # raise DEF; %HP must ignore it
    plant_bomb(tgt, 2)
    arm_bombs(tgt)
    exp = expected_detonation(tgt, 2)
    hp0 = tgt.hp
    dealt = detonate_fused(tgt, g)
    check("ignores_def", dealt == exp, f"dealt={dealt} expected={exp} (DEF raised, should not matter)")

    # PRT reduces it (deal_damage applies PRT).
    g2 = fresh_game()
    ts2 = free_tiles(g2, 1)
    p = place(g2, UnitType.POTPOURRIST, 2, *ts2[0])
    plant_bomb(p, 2)
    arm_bombs(p)
    raw = expected_detonation(p, 2)
    p.prt = 2
    hp0b = p.hp
    detonate_fused(p, g2)
    actual = hp0b - p.hp
    check("respects_prt", actual < raw, f"with PRT2 dealt {actual}, raw would be {raw}")


def test_only_fused_detonate():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bomb(tgt, 2)
    arm_bombs(tgt)          # these 2 fuse
    plant_bomb(tgt, 1)      # a fresh unfused one (total 3)
    check("mixed_fuse_state", fused_count(tgt) == 2 and len(tgt.bombs) == 3,
          f"fused={fused_count(tgt)} total={len(tgt.bombs)}")
    detonate_fused(tgt, g)
    check("unfused_survives_detonation", len(tgt.bombs) == 1 and fused_count(tgt) == 0,
          f"remaining={len(tgt.bombs)} fused={fused_count(tgt)}")


# ---------------------------------------------------------------------------
# Skyhook cooldown refund (the flow engine)
# ---------------------------------------------------------------------------

def test_skyhook_refund():
    g = fresh_game()
    ts = free_tiles(g, 2)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    tank = place(g, UnitType.POTPOURRIST, 2, *ts[1])

    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    harvest = next(s for s in graft.active_skills if s.name == "Harvest")
    sky.current_cooldown = sky.cooldown  # 4

    plant_bomb(tank, 3)
    arm_bombs(tank)
    harvest.execute(graft, (graft.y, graft.x), g)
    # 3 stacks detonated -> refund 2*3 = 6, clamped to 0 from a base of 4.
    check("refund_clamps_to_zero", sky.current_cooldown == 0,
          f"cd={sky.current_cooldown} (3 stacks should over-refund a cd-4 skill)")

    # Single-stack refund trims by exactly 2.
    g2 = fresh_game()
    ts2 = free_tiles(g2, 2)
    graft2 = place(g2, UnitType.ORDNANCE_GRAFT, 1, *ts2[0])
    tank2 = place(g2, UnitType.POTPOURRIST, 2, *ts2[1])
    sky2 = next(s for s in graft2.active_skills if s.name == "Skyhook")
    harvest2 = next(s for s in graft2.active_skills if s.name == "Harvest")
    sky2.current_cooldown = 4
    plant_bomb(tank2, 1)
    arm_bombs(tank2)
    harvest2.execute(graft2, (graft2.y, graft2.x), g2)
    check("refund_one_stack", sky2.current_cooldown == 2,
          f"cd={sky2.current_cooldown} (1 stack -> -2 from 4)")


# ---------------------------------------------------------------------------
# Skyhook (drone-lift reposition + arrival plant; gated on the drone)
# ---------------------------------------------------------------------------

def _passable_corridor(g, length):
    """Find a row with `length` consecutive passable, empty columns. Returns (row, c0)."""
    for r in range(HEIGHT):
        cs = [c for c in range(WIDTH)
              if g.map.is_passable(r, c) and g.get_unit_at(r, c) is None]
        for i in range(len(cs) - (length - 1)):
            if all(cs[i + k] == cs[i] + k for k in range(length)):
                return r, cs[i]
    return None, None


def test_skyhook_repositions_and_plants():
    """Skyhook lifts the graft to the destination and grafts a bomb onto an enemy
    adjacent to the landing; the drone mirrors it (two bombs)."""
    g = fresh_game()
    r, c0 = _passable_corridor(g, 4)
    if r is None:
        check("skyhook_reposition", False, "no corridor")
        return
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, r, c0)
    # Enemy sits at c0+4; land adjacent to it at c0+3.
    enemy = place(g, UnitType.POTPOURRIST, 2, r, c0 + 4) if (c0 + 4) < WIDTH and g.map.is_passable(r, c0 + 4) else None
    if enemy is None:
        check("skyhook_reposition", False, "no tile for arrival enemy")
        return
    g.current_player = 1
    g._process_ordnance_graft_upkeep()  # spawn drone
    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    dest = (r, c0 + 3)
    e_hp0 = enemy.hp
    ok = sky.execute(graft, dest, g)
    check("skyhook_moves_graft", (graft.y, graft.x) == dest,
          f"graft@({graft.y},{graft.x}) expected {dest}")
    check("skyhook_plants_one_bomb", len(enemy.bombs) == 1,
          f"arrival enemy bombs={len(enemy.bombs)} (graft slams alone, no mirror)")
    check("skyhook_arrival_damage", (e_hp0 - enemy.hp) == STRIKE_DAMAGE,
          f"dmg={e_hp0 - enemy.hp} (flat strike, DEF 0)")


def test_skyhook_arrival_aoe():
    """Skyhook's arrival slam hits EVERY enemy in the 8 tiles around the landing —
    each is struck once and grafted one bomb (the graft slams alone; no drone mirror)."""
    g = fresh_game()
    # Find a landing tile (empty, in range) with >=2 free neighbours for enemies.
    graft = None
    landing = None
    nbrs = []
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            if not (g.map.is_passable(y, x) and g.get_unit_at(y, x) is None):
                continue
            free_n = [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                      if (dy or dx) and g.map.is_passable(y + dy, x + dx)
                      and g.get_unit_at(y + dy, x + dx) is None]
            if len(free_n) >= 3:  # 1 for the graft's start, 2 for enemies
                landing = (y, x)
                nbrs = free_n
                break
        if landing:
            break
    if landing is None:
        check("skyhook_aoe", False, "no suitable landing tile")
        return
    # Put the graft on one neighbour (so the landing tile stays empty + in range 1).
    gstart = nbrs[0]
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *gstart)
    e1 = place(g, UnitType.POTPOURRIST, 2, *nbrs[1])  # DEF 0
    e2 = place(g, UnitType.POTPOURRIST, 2, *nbrs[2])  # DEF 0
    g.current_player = 1
    g._process_ordnance_graft_upkeep()  # drone
    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    # Landing must be empty (drone may have taken a tile) and adjacent to both enemies.
    if g.get_unit_at(*landing) is not None:
        check("skyhook_aoe", False, "landing tile got occupied by drone")
        return
    e1_hp0, e2_hp0 = e1.hp, e2.hp
    sky.execute(graft, landing, g)
    both_grafted = len(e1.bombs) == 1 and len(e2.bombs) == 1
    both_hit = (e1_hp0 - e1.hp) == STRIKE_DAMAGE and (e2_hp0 - e2.hp) == STRIKE_DAMAGE
    check("skyhook_aoe_grafts_all_adjacent", both_grafted,
          f"e1 bombs={len(e1.bombs)} e2 bombs={len(e2.bombs)} (both should be 1)")
    check("skyhook_aoe_strikes_all_adjacent", both_hit,
          f"e1 dmg={e1_hp0 - e1.hp} e2 dmg={e2_hp0 - e2.hp} (both flat strike)")


def _empty_dest_in_range(g, graft, rng=4):
    """An empty, passable, in-range tile to skyhook to (chosen AFTER units exist)."""
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if ((y, x) != (graft.y, graft.x) and g.is_valid_position(y, x)
                    and g.map.is_passable(y, x) and g.get_unit_at(y, x) is None
                    and g.chess_distance(graft.y, graft.x, y, x) <= rng):
                return (y, x)
    return None


def test_skyhook_requires_living_drone():
    """The key gate: Skyhook is unusable with no drone, usable once it exists."""
    g = fresh_game()
    ts = free_tiles(g, 40)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    # No drone yet (no upkeep run) -> cannot use (pick dest now, no drone occupying tiles).
    graft.drone = None
    dest = _empty_dest_in_range(g, graft)
    check("skyhook_blocked_no_drone", sky.can_use(graft, dest, g) is False,
          f"can_use with no drone = {sky.can_use(graft, dest, g)} (want False)")
    # Spawn the drone -> now usable (recompute dest so it isn't the drone's tile).
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    dest = _empty_dest_in_range(g, graft)
    check("skyhook_ok_with_drone", sky.can_use(graft, dest, g) is True,
          f"can_use with drone = {sky.can_use(graft, dest, g)} (want True)")


def test_skyhook_blocked_after_drone_dies():
    """Killing the drone grounds Skyhook until it regenerates."""
    g = fresh_game()
    ts = free_tiles(g, 40)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    g.current_player = 1
    g._process_ordnance_graft_upkeep()  # drone exists
    dest = _empty_dest_in_range(g, graft)  # empty tile, not the drone's
    usable_before = sky.can_use(graft, dest, g)
    # Kill the drone through the engine death path.
    drone = graft.drone
    drone.hp = 0
    g.handle_unit_death(drone, None, cause="test", ui=None)
    check("skyhook_grounded_when_drone_killed", usable_before is True and sky.can_use(graft, dest, g) is False,
          f"before={usable_before} after_death={sky.can_use(graft, dest, g)} (want True then False)")


def test_skyhook_aborts_and_refunds_if_drone_dies_after_queue():
    """If the drone dies AFTER Skyhook is queued (use) but before it resolves (execute),
    execute must abort (graft does NOT move) and refund the cooldown."""
    g = fresh_game()
    ts = free_tiles(g, 40)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    g.current_player = 1
    g._process_ordnance_graft_upkeep()  # drone exists
    dest = _empty_dest_in_range(g, graft)
    before = (graft.y, graft.x)
    sky.use(graft, dest, g)  # queue it (drone alive) -> charges cooldown
    # the drone dies before the queued Skyhook resolves
    drone = graft.drone
    drone.hp = 0
    g.handle_unit_death(drone, None, cause="test", ui=None)
    ok = sky.execute(graft, dest, g)
    check("skyhook_dead_drone_aborts", ok is False and (graft.y, graft.x) == before,
          f"returned={ok} moved={(graft.y, graft.x) != before} (want abort, no move)")
    check("skyhook_dead_drone_refunds", sky.current_cooldown == 0,
          f"cd={sky.current_cooldown} (want refunded to 0)")


def test_skyhook_aborts_and_refunds_if_landing_occupied():
    """If the landing tile becomes occupied between queue and resolve, execute aborts and
    refunds the cooldown (the player shouldn't eat a 4-turn cd for a no-op)."""
    g = fresh_game()
    ts = free_tiles(g, 40)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    sky = next(s for s in graft.active_skills if s.name == "Skyhook")
    g.current_player = 1
    g._process_ordnance_graft_upkeep()  # drone exists
    dest = _empty_dest_in_range(g, graft)
    sky.use(graft, dest, g)  # queue it -> charges cooldown
    place(g, UnitType.INTERFERER, 2, dest[0], dest[1])  # something lands on the target tile
    before = (graft.y, graft.x)
    ok = sky.execute(graft, dest, g)
    check("skyhook_occupied_aborts", ok is False and (graft.y, graft.x) == before,
          f"returned={ok} moved={(graft.y, graft.x) != before} (want abort, no move)")
    check("skyhook_occupied_refunds", sky.current_cooldown == 0,
          f"cd={sky.current_cooldown} (want refunded to 0)")


# ---------------------------------------------------------------------------
# Cleanse: partial (Broaching) vs full (Vagal Run)
# ---------------------------------------------------------------------------

def test_partial_cleanse_removes_one():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bomb(tgt, 3)
    removed = remove_one_bomb(tgt)
    check("partial_removes_one", removed and len(tgt.bombs) == 2,
          f"removed={removed} remaining={len(tgt.bombs)}")


def test_partial_cleanse_prefers_unfused():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bomb(tgt, 1)
    arm_bombs(tgt)          # 1 fused
    plant_bomb(tgt, 1)      # 1 unfused (total 2)
    remove_one_bomb(tgt)
    # Should peel the UNFUSED one, leaving the fused stack intact.
    check("partial_prefers_unfused", len(tgt.bombs) == 1 and fused_count(tgt) == 1,
          f"remaining={len(tgt.bombs)} fused={fused_count(tgt)}")


def test_full_cleanse_removes_all():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bomb(tgt, 3)
    arm_bombs(tgt)
    n = clear_bombs(tgt)
    check("full_cleanse_clears_all", n == 3 and len(tgt.bombs) == 0,
          f"removed={n} remaining={len(tgt.bombs)}")


def test_broaching_gas_peels_one_bomb():
    """End-to-end through the REAL drip-cleanse path: a BROACHING vapor strips ONE
    bomb per tick from an ally, never the whole cluster. This is the interaction the
    multi-instance model exists for. The ally carries only bombs, so the random
    cleanse always lands on bomb — and even then only one bomb comes off."""
    g = fresh_game()
    ts = free_tiles(g, 3)
    # The Gas Machinist's own ally got bombed by an enemy graft; his vapor peels it.
    gas = place(g, UnitType.GAS_MACHINIST, 1, *ts[0])
    vy, vx = ts[1]
    vapor = place(g, UnitType.HEINOUS_VAPOR, 1, vy, vx)
    vapor.vapor_type = "BROACHING"
    vapor.vapor_creator = gas
    # Ally adjacent to the vapor (inside its 3x3), carrying a full bomb stack.
    ally_pos = None
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1)):
        ny, nx = vy + dy, vx + dx
        if 0 <= ny < HEIGHT and 0 <= nx < WIDTH and g.map.can_place_unit(ny, nx) and g.get_unit_at(ny, nx) is None:
            ally_pos = (ny, nx)
            break
    if ally_pos is None:
        check("broaching_peels_one_bomb", False, "no adjacent tile for ally")
        return
    ally = place(g, UnitType.POTPOURRIST, 1, *ally_pos)  # same player as vapor
    plant_bomb(ally, 3)
    arm_bombs(ally)
    try:
        vapor.apply_vapor_effects(g, ui=None)
        # Exactly one bomb removed — the cluster degrades, it isn't wiped.
        check("broaching_peels_one_bomb", len(ally.bombs) == 2,
              f"remaining={len(ally.bombs)} (started 3, drip-cleanse should take 1)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("broaching_peels_one_bomb", False, repr(e))


def test_vagal_run_clears_bombs():
    """End-to-end: Derelictionist's Vagal Run defuses the whole cluster."""
    g = fresh_game()
    ts = free_tiles(g, 2)
    derel = place(g, UnitType.DERELICTIONIST, 1, *ts[0])
    tgt = place(g, UnitType.POTPOURRIST, 1, *ts[1])  # ally target (Vagal Run cleanses allies)
    plant_bomb(tgt, 3)
    arm_bombs(tgt)
    vagal = next(s for s in derel.active_skills if s.name == "Vagal Run")
    try:
        vagal.execute(derel, (tgt.y, tgt.x), g)
        check("vagal_run_clears_bombs", len(tgt.bombs) == 0, f"remaining={len(tgt.bombs)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("vagal_run_clears_bombs", False, repr(e))


# ---------------------------------------------------------------------------
# Drone
# ---------------------------------------------------------------------------

def _graft_with_drone_and_enemy(g, map_name="lime_foyer"):
    """Place a graft adjacent to an enemy and give it a live drone. Returns
    (graft, enemy, drone)."""
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts if abs(y - gy) <= 1 and abs(x - gx) <= 1 and (y, x) != (gy, gx))
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, gy, gx)
    enemy = place(g, UnitType.POTPOURRIST, 2, ey, ex)
    g.current_player = 1
    g._process_ordnance_graft_upkeep()  # spawns the drone
    return graft, enemy, getattr(graft, 'drone', None)


def test_inoculant_plants_one_bomb():
    """Inoculant is a single strike + 1 bomb (the drone no longer auto-mirrors)."""
    g = fresh_game()
    graft, enemy, drone = _graft_with_drone_and_enemy(g)
    inoc = next(s for s in graft.active_skills if s.name == "Inoculant")
    hp0 = enemy.hp
    inoc.execute(graft, (enemy.y, enemy.x), g)
    check("inoculant_one_bomb", len(enemy.bombs) == 1, f"bombs={len(enemy.bombs)} (graft alone)")
    check("inoculant_flat_damage", (hp0 - enemy.hp) == STRIKE_DAMAGE,
          f"damage={hp0 - enemy.hp} expected={STRIKE_DAMAGE}")


def _drone_next_to_enemy(g):
    """Set up a graft+drone with an INTERFERER (DEF 0) adjacent to the drone, in leash.
    Returns (graft, drone, enemy) or (None, None, None) if no valid layout."""
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts if abs(y - gy) <= 1 and abs(x - gx) <= 1 and (y, x) != (gy, gx))
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, gy, gx)
    enemy = place(g, UnitType.INTERFERER, 2, ey, ex)
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    drone = getattr(graft, 'drone', None)
    if drone is None:
        return None, None, None
    # park the drone adjacent to the enemy (within leash)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ny, nx = enemy.y + dy, enemy.x + dx
            if ((dy or dx) and g.is_valid_position(ny, nx) and g.map.is_passable(ny, nx)
                    and g.get_unit_at(ny, nx) is None
                    and g.chess_distance(ny, nx, graft.y, graft.x) <= 3):
                g._remove_from_unit_grid(drone)
                drone.y, drone.x = ny, nx
                g._update_unit_grid(drone)
                return graft, drone, enemy
    return None, None, None


def test_drone_basic_attack_is_plain_hit():
    """The drone's basic attack is now a PLAIN hit: its real ATK (3), and it plants NO
    bomb (planting moved to the drone's own Inoculant skill)."""
    g = fresh_game()
    graft, drone, enemy = _drone_next_to_enemy(g)
    if drone is None:
        check("drone_plain_attack", False, "no valid drone/enemy layout")
        return
    atk = drone.get_effective_stats()['attack']
    hp0 = enemy.hp
    drone.attack_target = (enemy.y, enemy.x)
    g.current_player = 1
    g.execute_turn(ui=None)
    check("drone_basic_no_bomb", len(enemy.bombs) == 0,
          f"bombs={len(enemy.bombs)} (basic attack should plant NOTHING now)")
    check("drone_basic_uses_atk", (hp0 - enemy.hp) == atk,
          f"damage={hp0 - enemy.hp} expected ATK {atk} (no longer flat {STRIKE_DAMAGE})")


def test_drone_has_inoculant_and_plants():
    """The drone now has its OWN Inoculant skill — using it grafts a bomb (flat 2)."""
    g = fresh_game()
    graft, drone, enemy = _drone_next_to_enemy(g)
    if drone is None:
        check("drone_inoculant", False, "no valid drone/enemy layout")
        return
    inoc = next((s for s in drone.active_skills if s.name == "Inoculant"), None)
    check("drone_has_inoculant", inoc is not None, "drone should have an Inoculant skill")
    if inoc is None:
        return
    inoc.current_cooldown = 0
    hp0 = enemy.hp
    check("drone_inoculant_can_use", inoc.can_use(drone, (enemy.y, enemy.x), g) is True,
          "drone Inoculant should be usable on the adjacent enemy")
    drone.selected_skill = inoc
    drone.skill_target = (enemy.y, enemy.x)
    g.current_player = 1
    g.execute_turn(ui=None)
    check("drone_inoculant_plants", len(enemy.bombs) == 1,
          f"bombs={len(enemy.bombs)} (drone Inoculant should graft 1)")
    check("drone_inoculant_flat_damage", (hp0 - enemy.hp) == STRIKE_DAMAGE,
          f"damage={hp0 - enemy.hp} expected flat {STRIKE_DAMAGE}")


def test_drone_leash_bounds_player_moves():
    """The player can move the drone within the leash radius but not past it.
    A 'near' tile is within both the leash AND the drone's move range; a 'far' tile is
    beyond the leash (so it must be rejected regardless of move range)."""
    g = fresh_game()
    graft, enemy, drone = _graft_with_drone_and_enemy(g)
    if drone is None:
        check("drone_leash_bounds", False, "no drone")
        return
    from boneglaive.utils.constants import ORDNANCE_DRONE_LEASH
    # Park the drone exactly at the leash edge (clear tile), then test single-step
    # (adjacent) moves so path-through-units never interferes: one step that keeps it
    # within leash, and one step outward that would exceed leash.
    edge = None
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if (g.is_valid_position(y, x) and g.map.is_passable(y, x) and g.get_unit_at(y, x) is None
                    and g.chess_distance(y, x, graft.y, graft.x) == ORDNANCE_DRONE_LEASH):
                edge = (y, x)
                break
        if edge:
            break
    if edge is None:
        check("drone_leash_bounds", False, "no leash-edge tile")
        return
    g._remove_from_unit_grid(drone)
    drone.y, drone.x = edge
    g._update_unit_grid(drone)
    # Adjacent steps from the edge: classify by resulting leash distance.
    inward = outward = None
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dy or dx):
                continue
            ny, nx = drone.y + dy, drone.x + dx
            if not (g.is_valid_position(ny, nx) and g.map.is_passable(ny, nx) and g.get_unit_at(ny, nx) is None):
                continue
            d = g.chess_distance(ny, nx, graft.y, graft.x)
            if inward is None and d <= ORDNANCE_DRONE_LEASH:
                inward = (ny, nx)
            if outward is None and d > ORDNANCE_DRONE_LEASH:
                outward = (ny, nx)
    in_ok = g.can_move_to(drone, *inward) if inward else None
    out_ok = g.can_move_to(drone, *outward) if outward else None
    check("drone_move_within_leash", inward is None or in_ok is True,
          f"step within leash allowed={in_ok} (tile {inward})")
    check("drone_move_beyond_leash_blocked", outward is None or out_ok is False,
          f"step past leash allowed={out_ok} (tile {outward}, leash={ORDNANCE_DRONE_LEASH})")


def test_drone_leash_pull_is_minimal():
    """When the graft moves out of leash range, the drone is pulled the MINIMUM distance
    back within range (closest in-leash tile to where it was) — NOT snapped adjacent."""
    g = fresh_game()
    graft, enemy, drone = _graft_with_drone_and_enemy(g)
    if drone is None:
        check("leash_pull_minimal", False, "no drone")
        return
    from boneglaive.utils.constants import ORDNANCE_DRONE_LEASH
    # Park the drone somewhere, then move the graft far away so the drone is out of leash.
    # Use the full grid: pick a graft destination > leash from the drone's current spot.
    drone_y, drone_x = drone.y, drone.x
    far_graft = None
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (g.is_valid_position(y, x) and g.map.is_passable(y, x) and g.get_unit_at(y, x) is None
                    and g.chess_distance(y, x, drone_y, drone_x) > ORDNANCE_DRONE_LEASH + 1):
                far_graft = (y, x)
                break
        if far_graft:
            break
    if far_graft is None:
        check("leash_pull_minimal", False, "no far graft tile")
        return
    # Teleport the graft there and run the leash follow.
    g._remove_from_unit_grid(graft)
    graft.y, graft.x = far_graft
    g._update_unit_grid(graft)
    g._move_leashed_drones(graft, drone_y, drone_x, ui=None)

    new_d_to_graft = g.chess_distance(drone.y, drone.x, graft.y, graft.x)
    # (1) Back within leash.
    check("leash_pull_within_range", new_d_to_graft <= ORDNANCE_DRONE_LEASH,
          f"drone now {new_d_to_graft} from graft (leash={ORDNANCE_DRONE_LEASH})")
    # (2) Minimal: no other valid in-leash tile is closer to the drone's old position.
    best_possible = None
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (g.chess_distance(y, x, graft.y, graft.x) <= ORDNANCE_DRONE_LEASH
                    and g.is_valid_position(y, x) and g.map.is_passable(y, x)
                    and (g.get_unit_at(y, x) is None or (y, x) == (drone.y, drone.x))):
                d = g.chess_distance(drone_y, drone_x, y, x)
                if best_possible is None or d < best_possible:
                    best_possible = d
    actual_pull = g.chess_distance(drone_y, drone_x, drone.y, drone.x)
    check("leash_pull_is_minimal", actual_pull == best_possible,
          f"pulled {actual_pull}, minimum possible {best_possible}")
    # (3) Not snapped adjacent (when the leash boundary is reachable, it should sit out near the edge).
    check("leash_pull_not_snapped_adjacent", new_d_to_graft > 1 or best_possible is not None,
          f"drone {new_d_to_graft} from graft (should be near the leash edge, not glued to it)")


def test_drone_spawns_on_upkeep():
    g = fresh_game()
    ts = free_tiles(g, 1)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    check("no_drone_before_upkeep", getattr(graft, 'drone', None) is None, "")
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    drone = getattr(graft, 'drone', None)
    ok = (drone is not None and drone.is_alive() and getattr(drone, 'is_drone', False)
          and drone.creator is graft
          and g.chess_distance(graft.y, graft.x, drone.y, drone.x) <= 1)
    check("drone_spawns_adjacent", ok,
          f"drone={'yes' if drone else 'no'}")


def test_drone_leash_rejects_far_move():
    g = fresh_game()
    ts = free_tiles(g, 1)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    drone = graft.drone
    # A move within leash is allowed; a move past it is rejected by can_move_to.
    far_y, far_x = graft.y, graft.x + ORDNANCE_DRONE_LEASH + 2
    near_y, near_x = graft.y, graft.x + 1
    far_ok = True
    near_ok = True
    if 0 <= far_x < WIDTH and g.map.is_passable(far_y, far_x):
        far_ok = g.can_move_to(drone, far_y, far_x)
    if 0 <= near_x < WIDTH and g.map.is_passable(near_y, near_x) and g.get_unit_at(near_y, near_x) is None:
        near_ok = g.can_move_to(drone, near_y, near_x)
    check("leash_rejects_far", far_ok is False, f"far_move_allowed={far_ok} (leash={ORDNANCE_DRONE_LEASH})")
    check("leash_allows_near", near_ok is True, f"near_move_allowed={near_ok}")


def test_drone_regenerates_after_death():
    g = fresh_game()
    ts = free_tiles(g, 1)
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *ts[0])
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    drone = graft.drone
    # Kill the drone through the engine's death path.
    drone.hp = 0
    g.handle_unit_death(drone, None, cause="test", ui=None)
    check("regen_timer_set", graft.drone is None and graft.drone_regen_timer == ORDNANCE_DRONE_REGEN,
          f"drone={graft.drone} timer={graft.drone_regen_timer}")
    # Upkeep decrements the timer, then spawns once it has drained: the timer takes
    # ORDNANCE_DRONE_REGEN cycles to reach 0, and the drone returns on the next
    # (N+1-th) upkeep. Assert the drone is strictly absent until then.
    for i in range(ORDNANCE_DRONE_REGEN):
        g._process_ordnance_graft_upkeep()
        check(f"no_regen_while_draining_t{i}", graft.drone is None, f"timer={graft.drone_regen_timer}")
    g._process_ordnance_graft_upkeep()  # timer now 0 -> spawn
    check("regen_after_timer", graft.drone is not None and graft.drone.is_alive(),
          f"drone={'yes' if graft.drone else 'no'}")


def test_drone_flies_over_terrain_but_cannot_land():
    """The drone flies OVER impassable terrain/furniture in its path, but cannot LAND on it
    (the destination must still be passable). A non-flying unit is blocked by the same path."""
    g = fresh_game()
    # find start(passable,empty) - furniture(impassable) - landing(passable,empty) in a row
    spot = None
    for y in range(HEIGHT):
        for x in range(1, WIDTH - 1):
            if (not g.map.is_passable(y, x)
                    and g.map.is_passable(y, x - 1) and g.get_unit_at(y, x - 1) is None
                    and g.map.is_passable(y, x + 1) and g.get_unit_at(y, x + 1) is None):
                spot = (y, x)
                break
        if spot:
            break
    if spot is None:
        check("drone_flight_setup", False, "no furniture-between-passable spot on this map")
        return
    fy, fx = spot          # furniture
    start, landing = fx - 1, fx + 1
    # place the graft off the flight row but within leash of both tiles
    gpos = next(((gy, gx) for (gy, gx) in [(fy + 1, landing), (fy - 1, landing), (fy + 1, fx), (fy - 1, fx)]
                 if 0 <= gy < HEIGHT and g.map.is_passable(gy, gx) and g.get_unit_at(gy, gx) is None
                 and g.chess_distance(gy, gx, fy, landing) <= ORDNANCE_DRONE_LEASH
                 and g.chess_distance(gy, gx, fy, start) <= ORDNANCE_DRONE_LEASH), None)
    if gpos is None:
        check("drone_flight_setup", False, "no off-row graft position within leash")
        return
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, *gpos)
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    drone = graft.drone
    graft.move_target = None
    g._remove_from_unit_grid(drone)
    drone.y, drone.x = fy, start
    g._update_unit_grid(drone)

    check("drone_flies_over_terrain", g.can_move_to(drone, fy, landing) is True,
          f"can_move_to(landing beyond furniture)={g.can_move_to(drone, fy, landing)} (want True)")
    check("drone_cannot_land_on_terrain", g.can_move_to(drone, fy, fx) is False,
          f"can_move_to(furniture tile)={g.can_move_to(drone, fy, fx)} (want False)")

    # a non-flying unit is blocked by the same furniture in its path
    g2 = fresh_game()
    gray = place(g2, UnitType.GRAYMAN, 1, fy, start)
    check("nonflyer_blocked_by_terrain", g2.can_move_to(gray, fy, landing) is False,
          f"GRAYMAN over furniture={g2.can_move_to(gray, fy, landing)} (want False)")

    # The drone also flies OVER units in its path, but still can't land on an occupied tile.
    g3 = fresh_game()
    row = None
    for yy in range(HEIGHT):
        cs = [x for x in range(WIDTH) if g3.map.is_passable(yy, x) and g3.get_unit_at(yy, x) is None]
        for i in range(len(cs) - 2):
            if cs[i + 1] == cs[i] + 1 and cs[i + 2] == cs[i] + 2:
                row = (yy, cs[i])
                break
        if row:
            break
    if row is None:
        check("drone_unit_flight_setup", False, "no 3-tile passable corridor")
        return
    ry, rc = row
    ustart, umid, uland = rc, rc + 1, rc + 2
    gp = next(((gy, gx) for (gy, gx) in [(ry + 1, uland), (ry - 1, uland), (ry + 1, umid), (ry - 1, umid)]
               if 0 <= gy < HEIGHT and g3.map.is_passable(gy, gx) and g3.get_unit_at(gy, gx) is None
               and g3.chess_distance(gy, gx, ry, uland) <= ORDNANCE_DRONE_LEASH
               and g3.chess_distance(gy, gx, ry, ustart) <= ORDNANCE_DRONE_LEASH), None)
    if gp is None:
        check("drone_unit_flight_setup", False, "no off-row graft position within leash (units)")
        return
    graft3 = place(g3, UnitType.ORDNANCE_GRAFT, 1, *gp)
    g3.current_player = 1
    g3._process_ordnance_graft_upkeep()
    drone3 = graft3.drone
    graft3.move_target = None
    g3._remove_from_unit_grid(drone3)
    drone3.y, drone3.x = ry, ustart
    g3._update_unit_grid(drone3)
    place(g3, UnitType.INTERFERER, 2, ry, umid)  # a unit blocking the flight path
    check("drone_flies_over_unit", g3.can_move_to(drone3, ry, uland) is True,
          f"can_move_to(landing past a unit)={g3.can_move_to(drone3, ry, uland)} (want True)")
    check("drone_cannot_land_on_unit", g3.can_move_to(drone3, ry, umid) is False,
          f"can_move_to(occupied tile)={g3.can_move_to(drone3, ry, umid)} (want False)")


def main():
    test_plant_and_cap()
    test_fuse_timing()
    test_bomb_expires_after_lifespan()
    test_grafting_refreshes_bomb_timers()
    test_bomb_survives_harvest_cooldown()
    test_stasiality_immune_to_bomb()
    test_detonation_tank_math()
    test_detonation_curve_favours_big_bodies()
    test_detonation_ignores_def_respects_prt()
    test_only_fused_detonate()
    test_skyhook_refund()
    test_skyhook_repositions_and_plants()
    test_skyhook_arrival_aoe()
    test_skyhook_requires_living_drone()
    test_skyhook_blocked_after_drone_dies()
    test_skyhook_aborts_and_refunds_if_drone_dies_after_queue()
    test_skyhook_aborts_and_refunds_if_landing_occupied()
    test_partial_cleanse_removes_one()
    test_partial_cleanse_prefers_unfused()
    test_full_cleanse_removes_all()
    test_broaching_gas_peels_one_bomb()
    test_vagal_run_clears_bombs()
    test_inoculant_plants_one_bomb()
    test_drone_basic_attack_is_plain_hit()
    test_drone_has_inoculant_and_plants()
    test_drone_leash_bounds_player_moves()
    test_drone_leash_pull_is_minimal()
    test_drone_spawns_on_upkeep()
    test_drone_leash_rejects_far_move()
    test_drone_regenerates_after_death()
    test_drone_flies_over_terrain_but_cannot_land()

    print("\n==== ORDNANCE GRAFT INTEGRATION ====")
    allok = True
    for name, ok, note in results:
        allok &= ok
        flag = "PASS" if ok else "FAIL"
        line = f"  [{flag}] {name}"
        if note:
            line += f"  ({note})"
        print(line)
    print("==== " + ("ALL PASS" if allok else "SOME FAILED") + " ====")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
