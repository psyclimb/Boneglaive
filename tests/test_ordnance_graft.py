#!/usr/bin/env python3
"""Integration tests for ORDNANCE GRAFT — the bola mechanics and the drone.

Drives the engine directly (ui=None) and asserts behaviour, not just absence of
crashes: bola plant/cap/fuse timing, detonation %max-HP math, the Skyhook
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
    UnitType, HEIGHT, WIDTH, BOLA_MAX_STACKS,
    ORDNANCE_DRONE_REGEN, ORDNANCE_DRONE_LEASH,
)
from boneglaive.game.skills.ordnance_graft import (
    plant_bola, fused_count, arm_bolas, detonate_fused,
    remove_one_bola, clear_bolas, bola_pct,
    BOLA_PCT_FLOOR, BOLA_PCT_REF_HP, BOLA_PCT_PER_HP, STRIKE_DAMAGE,
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
    pct = BOLA_PCT_FLOOR + max(0, target.max_hp - BOLA_PCT_REF_HP) * BOLA_PCT_PER_HP
    per = max(1, round(target.max_hp * pct))
    return per * stacks


# ---------------------------------------------------------------------------
# Bola plant / cap / fuse
# ---------------------------------------------------------------------------

def test_plant_and_cap():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])

    added = plant_bola(tgt, 1)
    check("plant_adds_one", added == 1 and len(tgt.bolas) == 1, f"added={added} n={len(tgt.bolas)}")
    check("plant_starts_unfused", fused_count(tgt) == 0, f"fused={fused_count(tgt)}")

    # Over-plant past the cap is clamped.
    plant_bola(tgt, 10)
    check("cap_clamps", len(tgt.bolas) == BOLA_MAX_STACKS, f"n={len(tgt.bolas)} cap={BOLA_MAX_STACKS}")
    added_when_full = plant_bola(tgt, 1)
    check("no_add_when_full", added_when_full == 0 and len(tgt.bolas) == BOLA_MAX_STACKS,
          f"added={added_when_full}")


def test_fuse_timing():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bola(tgt, 2)
    check("unfused_on_plant", fused_count(tgt) == 0, f"fused={fused_count(tgt)}")
    arm_bolas(tgt)
    check("fused_after_arm", fused_count(tgt) == 2, f"fused={fused_count(tgt)}")


def test_stasiality_immune_to_bola():
    """A unit with stasiality (or effective stasiality) cannot be grafted with bolas.
    GRAYMAN's Stasiality passive blocks the status; the strike damage still lands."""
    g = fresh_game()
    ts = free_tiles(g, 1)
    gray = place(g, UnitType.GRAYMAN, 2, *ts[0])
    check("grayman_is_immune", gray.is_immune_to_effects(), "GRAYMAN should be immune")
    added = plant_bola(gray, 3)
    check("plant_blocked_by_stasiality", added == 0 and len(gray.bolas) == 0,
          f"added={added} bolas={len(gray.bolas)} (should be 0)")

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
    check("inoculant_plants_nothing_on_immune", len(gray2.bolas) == 0,
          f"bolas={len(gray2.bolas)} (graft AND drone echo blocked by stasiality)")


# ---------------------------------------------------------------------------
# Detonation math
# ---------------------------------------------------------------------------

def test_detonation_tank_math():
    """Full 4-stack on a 24-HP tank matches the HP-scaling formula and is lethal-tier."""
    g = fresh_game()
    ts = free_tiles(g, 1)
    tank = place(g, UnitType.POTPOURRIST, 2, *ts[0])  # 24 HP, the roster tank
    plant_bola(tank, 4)
    arm_bolas(tank)
    raw = expected_detonation(tank, 4)            # raw formula damage (may overkill)
    hp0 = tank.hp
    dealt = detonate_fused(tank, g)
    # deal_damage returns ACTUAL damage, capped at the target's HP (no overkill).
    exp = min(raw, hp0)
    check("tank_math", dealt == exp and (hp0 - tank.hp) == exp,
          f"dealt={dealt} expected={exp} (raw={raw} capped at {hp0} HP; 24-HP tank, 4 stacks)")
    check("tank_burst_is_lethal_tier", raw >= tank.max_hp,
          f"4-stack raw {raw} vs {tank.max_hp} HP (should ~one-shot)")
    check("detonation_consumes_fused", len(tank.bolas) == 0, f"remaining={len(tank.bolas)}")


def test_detonation_curve_favours_big_bodies():
    """The anti-tank curve: a tank takes a strictly HIGHER % of its bar than a squishy
    from the same stack count, and the squishy is only lightly dented."""
    g = fresh_game()
    ts = free_tiles(g, 2)
    tank = place(g, UnitType.POTPOURRIST, 2, *ts[0])      # 24 HP
    squishy = place(g, UnitType.GRAYMAN, 2, *ts[1])       # 18 HP
    for u in (tank, squishy):
        plant_bola(u, 4)
        arm_bolas(u)
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
    plant_bola(tgt, 2)
    arm_bolas(tgt)
    exp = expected_detonation(tgt, 2)
    hp0 = tgt.hp
    dealt = detonate_fused(tgt, g)
    check("ignores_def", dealt == exp, f"dealt={dealt} expected={exp} (DEF raised, should not matter)")

    # PRT reduces it (deal_damage applies PRT).
    g2 = fresh_game()
    ts2 = free_tiles(g2, 1)
    p = place(g2, UnitType.POTPOURRIST, 2, *ts2[0])
    plant_bola(p, 2)
    arm_bolas(p)
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
    plant_bola(tgt, 2)
    arm_bolas(tgt)          # these 2 fuse
    plant_bola(tgt, 1)      # a fresh unfused one (total 3)
    check("mixed_fuse_state", fused_count(tgt) == 2 and len(tgt.bolas) == 3,
          f"fused={fused_count(tgt)} total={len(tgt.bolas)}")
    detonate_fused(tgt, g)
    check("unfused_survives_detonation", len(tgt.bolas) == 1 and fused_count(tgt) == 0,
          f"remaining={len(tgt.bolas)} fused={fused_count(tgt)}")


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

    plant_bola(tank, 3)
    arm_bolas(tank)
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
    plant_bola(tank2, 1)
    arm_bolas(tank2)
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
    """Skyhook lifts the graft to the destination and grafts a bola onto an enemy
    adjacent to the landing; the drone mirrors it (two bolas)."""
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
    check("skyhook_plants_one_bola", len(enemy.bolas) == 1,
          f"arrival enemy bolas={len(enemy.bolas)} (graft slams alone, no mirror)")
    check("skyhook_arrival_damage", (e_hp0 - enemy.hp) == STRIKE_DAMAGE,
          f"dmg={e_hp0 - enemy.hp} (flat strike, DEF 0)")


def test_skyhook_arrival_aoe():
    """Skyhook's arrival slam hits EVERY enemy in the 8 tiles around the landing —
    each is struck once and grafted one bola (the graft slams alone; no drone mirror)."""
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
    both_grafted = len(e1.bolas) == 1 and len(e2.bolas) == 1
    both_hit = (e1_hp0 - e1.hp) == STRIKE_DAMAGE and (e2_hp0 - e2.hp) == STRIKE_DAMAGE
    check("skyhook_aoe_grafts_all_adjacent", both_grafted,
          f"e1 bolas={len(e1.bolas)} e2 bolas={len(e2.bolas)} (both should be 1)")
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


# ---------------------------------------------------------------------------
# Cleanse: partial (Broaching) vs full (Vagal Run)
# ---------------------------------------------------------------------------

def test_partial_cleanse_removes_one():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bola(tgt, 3)
    removed = remove_one_bola(tgt)
    check("partial_removes_one", removed and len(tgt.bolas) == 2,
          f"removed={removed} remaining={len(tgt.bolas)}")


def test_partial_cleanse_prefers_unfused():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bola(tgt, 1)
    arm_bolas(tgt)          # 1 fused
    plant_bola(tgt, 1)      # 1 unfused (total 2)
    remove_one_bola(tgt)
    # Should peel the UNFUSED one, leaving the fused stack intact.
    check("partial_prefers_unfused", len(tgt.bolas) == 1 and fused_count(tgt) == 1,
          f"remaining={len(tgt.bolas)} fused={fused_count(tgt)}")


def test_full_cleanse_removes_all():
    g = fresh_game()
    ts = free_tiles(g, 1)
    tgt = place(g, UnitType.POTPOURRIST, 2, *ts[0])
    plant_bola(tgt, 3)
    arm_bolas(tgt)
    n = clear_bolas(tgt)
    check("full_cleanse_clears_all", n == 3 and len(tgt.bolas) == 0,
          f"removed={n} remaining={len(tgt.bolas)}")


def test_broaching_gas_peels_one_bomb():
    """End-to-end through the REAL drip-cleanse path: a BROACHING vapor strips ONE
    bomb per tick from an ally, never the whole cluster. This is the interaction the
    multi-instance model exists for. The ally carries only bolas, so the random
    cleanse always lands on bola — and even then only one bomb comes off."""
    g = fresh_game()
    ts = free_tiles(g, 3)
    # The Gas Machinist's own ally got bola'd by an enemy graft; his vapor peels it.
    gas = place(g, UnitType.GAS_MACHINIST, 1, *ts[0])
    vy, vx = ts[1]
    vapor = place(g, UnitType.HEINOUS_VAPOR, 1, vy, vx)
    vapor.vapor_type = "BROACHING"
    vapor.vapor_creator = gas
    # Ally adjacent to the vapor (inside its 3x3), carrying a full bola stack.
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
    plant_bola(ally, 3)
    arm_bolas(ally)
    try:
        vapor.apply_vapor_effects(g, ui=None)
        # Exactly one bomb removed — the cluster degrades, it isn't wiped.
        check("broaching_peels_one_bomb", len(ally.bolas) == 2,
              f"remaining={len(ally.bolas)} (started 3, drip-cleanse should take 1)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("broaching_peels_one_bomb", False, repr(e))


def test_vagal_run_clears_bolas():
    """End-to-end: Derelictionist's Vagal Run defuses the whole cluster."""
    g = fresh_game()
    ts = free_tiles(g, 2)
    derel = place(g, UnitType.DERELICTIONIST, 1, *ts[0])
    tgt = place(g, UnitType.POTPOURRIST, 1, *ts[1])  # ally target (Vagal Run cleanses allies)
    plant_bola(tgt, 3)
    arm_bolas(tgt)
    vagal = next(s for s in derel.active_skills if s.name == "Vagal Run")
    try:
        vagal.execute(derel, (tgt.y, tgt.x), g)
        check("vagal_run_clears_bolas", len(tgt.bolas) == 0, f"remaining={len(tgt.bolas)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("vagal_run_clears_bolas", False, repr(e))


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


def test_inoculant_plants_one_bola():
    """Inoculant is a single strike + 1 bola (the drone no longer auto-mirrors)."""
    g = fresh_game()
    graft, enemy, drone = _graft_with_drone_and_enemy(g)
    inoc = next(s for s in graft.active_skills if s.name == "Inoculant")
    hp0 = enemy.hp
    inoc.execute(graft, (enemy.y, enemy.x), g)
    check("inoculant_one_bola", len(enemy.bolas) == 1, f"bolas={len(enemy.bolas)} (graft alone)")
    check("inoculant_flat_damage", (hp0 - enemy.hp) == STRIKE_DAMAGE,
          f"damage={hp0 - enemy.hp} expected={STRIKE_DAMAGE}")


def test_drone_basic_attack_plants_bola():
    """The PLAYER pilots the drone; its basic attack grafts a bola and deals flat damage.
    Driven through execute_turn (the drone is a player-1 unit with a queued attack).
    Uses an INTERFERER target (DEF 0, no Potpourrist-style damage reduction) so the flat
    STRIKE_DAMAGE shows cleanly."""
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts if abs(y - gy) <= 1 and abs(x - gx) <= 1 and (y, x) != (gy, gx))
    graft = place(g, UnitType.ORDNANCE_GRAFT, 1, gy, gx)
    enemy = place(g, UnitType.INTERFERER, 2, ey, ex)
    g.current_player = 1
    g._process_ordnance_graft_upkeep()
    drone = getattr(graft, 'drone', None)
    if drone is None:
        check("drone_attack_plants", False, "no drone")
        return
    # Put the drone adjacent to the enemy (within leash) and queue its basic attack.
    target_adj = None
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ny, nx = enemy.y + dy, enemy.x + dx
            if ((dy or dx) and g.is_valid_position(ny, nx) and g.map.is_passable(ny, nx)
                    and g.get_unit_at(ny, nx) is None
                    and g.chess_distance(ny, nx, graft.y, graft.x) <= 3):
                target_adj = (ny, nx)
                break
        if target_adj:
            break
    if target_adj is None:
        check("drone_attack_plants", False, "no adjacent-to-enemy tile within leash")
        return
    g._remove_from_unit_grid(drone)
    drone.y, drone.x = target_adj
    g._update_unit_grid(drone)
    hp0 = enemy.hp
    drone.attack_target = (enemy.y, enemy.x)
    g.current_player = 1
    g.execute_turn(ui=None)
    check("drone_attack_plants_bola", len(enemy.bolas) == 1,
          f"bolas={len(enemy.bolas)} (drone basic attack should graft 1)")
    check("drone_attack_flat_damage", (hp0 - enemy.hp) == STRIKE_DAMAGE,
          f"damage={hp0 - enemy.hp} expected={STRIKE_DAMAGE} (drone uses flat STRIKE_DAMAGE, not ATK 3)")


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


def main():
    test_plant_and_cap()
    test_fuse_timing()
    test_stasiality_immune_to_bola()
    test_detonation_tank_math()
    test_detonation_curve_favours_big_bodies()
    test_detonation_ignores_def_respects_prt()
    test_only_fused_detonate()
    test_skyhook_refund()
    test_skyhook_repositions_and_plants()
    test_skyhook_arrival_aoe()
    test_skyhook_requires_living_drone()
    test_skyhook_blocked_after_drone_dies()
    test_partial_cleanse_removes_one()
    test_partial_cleanse_prefers_unfused()
    test_full_cleanse_removes_all()
    test_broaching_gas_peels_one_bomb()
    test_vagal_run_clears_bolas()
    test_inoculant_plants_one_bola()
    test_drone_basic_attack_plants_bola()
    test_drone_leash_bounds_player_moves()
    test_drone_spawns_on_upkeep()
    test_drone_leash_rejects_far_move()
    test_drone_regenerates_after_death()

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
