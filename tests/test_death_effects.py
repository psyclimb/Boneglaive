#!/usr/bin/env python3
"""Regression tests for the death-effect dispatch bug (cross-skill).

A unit reaching 0 HP via `deal_damage` / a direct `hp` write fires the Unit.hp
setter's `_handle_death` (GP + respawn) which REMOVES the unit from `game.units`.
The per-unit DEATH effects (FOWL Rail Genesis explosion+rail cleanup, MARROW
Dominion kill credit, etc.) live ONLY in `Game.handle_unit_death`. Several skills
used to deal lethal damage and rely on the engine's post-skill death sweep to call
handle_unit_death — but that sweep iterates `game.units` and the victim is already
gone, so the effects silently never fired.

Each test below kills a FOWL_CONTRIVANCE (the only one in play) that is standing
near a rail tile, then asserts the rail network was cleaned up — which only happens
if `handle_unit_death` actually ran for that FOWL. This is the cross-cutting,
killer-agnostic observable for "on-death effects fired".

Run with: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_death_effects.py
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
from boneglaive.game.map import TerrainType
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH

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


def add(g, utype, player, y, x):
    g.add_unit(utype, player, y, x)
    return g.get_unit_at(y, x)


def lay_rail(g, avoid):
    """Put a single RAIL tile somewhere empty (mirrors the engine's placement idiom so
    remove_rail_network can restore it). Returns True if a rail is present."""
    for (y, x) in free_tiles(g, 80):
        if (y, x) in avoid:
            continue
        g.map.rail_original_terrain[(y, x)] = g.map.get_terrain_at(y, x)
        g.map.set_terrain_at(y, x, TerrainType.RAIL)
        return g.map.has_rails()
    return False


def spy_on_deaths(g):
    """Wrap g.handle_unit_death to record (dying_unit, cause) it's called with."""
    seen = []
    real = g.handle_unit_death

    def spy(dying_unit, killer_unit=None, cause="combat", ui=None):
        seen.append((dying_unit, cause))
        return real(dying_unit, killer_unit, cause, ui)

    g.handle_unit_death = spy
    return seen


# ---------------------------------------------------------------------------
# POTPOURRIST — Demilune (front arc)  [potpourrist.py]
# ---------------------------------------------------------------------------

def test_demilune_kill_fires_death_effects():
    g = fresh_game()
    pot = add(g, UnitType.POTPOURRIST, 1, 5, 5)
    fowl = add(g, UnitType.FOWL_CONTRIVANCE, 2, 5, 6)  # due-east, in the swept arc
    fowl.hp = 1
    check("demilune_rail_pre", lay_rail(g, {(5, 5), (5, 6)}), "rail present before")
    seen = spy_on_deaths(g)
    g.current_player = 1
    dem = next(s for s in pot.active_skills if s.name == "Demilune")
    dem.execute(pot, (5, 6), g, ui=None)  # sweep toward the east tile
    check("demilune_fowl_dead", not fowl.is_alive(), f"FOWL hp={fowl.hp}")
    check("demilune_hud_called", any(d is fowl for d, _ in seen), "handle_unit_death ran for the FOWL")
    check("demilune_rail_cleaned", not g.map.has_rails(), "rails cleaned up by the FOWL's death")


# ---------------------------------------------------------------------------
# POTPOURRIST — Granite Geas (single target)  [potpourrist.py]
# ---------------------------------------------------------------------------

def test_granite_geas_kill_fires_death_effects():
    g = fresh_game()
    ts = free_tiles(g, 6)
    pot = add(g, UnitType.POTPOURRIST, 1, *ts[0])
    fy, fx = next((y, x) for (y, x) in ts[1:] if abs(y - pot.y) <= 1 and abs(x - pot.x) <= 1)
    fowl = add(g, UnitType.FOWL_CONTRIVANCE, 2, fy, fx)
    fowl.hp = 1
    check("geas_rail_pre", lay_rail(g, {(pot.y, pot.x), (fy, fx)}), "rail present before")
    seen = spy_on_deaths(g)
    g.current_player = 1
    geas = next(s for s in pot.active_skills if s.name == "Granite Geas")
    geas.execute(pot, (fy, fx), g, ui=None)
    check("geas_fowl_dead", not fowl.is_alive(), f"FOWL hp={fowl.hp}")
    check("geas_hud_called", any(d is fowl for d, _ in seen), "handle_unit_death ran for the FOWL")
    check("geas_rail_cleaned", not g.map.has_rails(), "rails cleaned up by the FOWL's death")


# ---------------------------------------------------------------------------
# GAS_MACHINIST — Broaching Gas vapor tick  [units.py apply_vapor_effects]
# ---------------------------------------------------------------------------

def _vapor_kill_setup(g, vapor_type):
    ts = free_tiles(g, 8)
    gas = add(g, UnitType.GAS_MACHINIST, 1, *ts[0])
    vy, vx = ts[1]
    vapor = add(g, UnitType.HEINOUS_VAPOR, 1, vy, vx)
    vapor.vapor_type = vapor_type
    vapor.vapor_creator = gas
    fy, fx = next((y, x) for (y, x) in ts[2:]
                  if abs(y - vy) <= 1 and abs(x - vx) <= 1 and (y, x) != (vy, vx))
    fowl = add(g, UnitType.FOWL_CONTRIVANCE, 2, fy, fx)
    fowl.hp = 1
    return gas, vapor, fowl


def test_broaching_gas_kill_fires_death_effects():
    g = fresh_game()
    gas, vapor, fowl = _vapor_kill_setup(g, "BROACHING")
    check("broaching_rail_pre", lay_rail(g, {(vapor.y, vapor.x), (fowl.y, fowl.x)}), "rail present before")
    seen = spy_on_deaths(g)
    g.current_player = 1
    vapor.apply_vapor_effects(g, None)
    check("broaching_fowl_dead", not fowl.is_alive(), f"FOWL hp={fowl.hp}")
    check("broaching_hud_called", any(d is fowl for d, _ in seen), "handle_unit_death ran for the FOWL")
    check("broaching_rail_cleaned", not g.map.has_rails(), "rails cleaned up by the FOWL's death")


def test_cutting_gas_kill_fires_death_effects():
    g = fresh_game()
    gas, vapor, fowl = _vapor_kill_setup(g, "CUTTING")
    check("cutting_rail_pre", lay_rail(g, {(vapor.y, vapor.x), (fowl.y, fowl.x)}), "rail present before")
    seen = spy_on_deaths(g)
    g.current_player = 1
    vapor.apply_vapor_effects(g, None)
    check("cutting_fowl_dead", not fowl.is_alive(), f"FOWL hp={fowl.hp}")
    check("cutting_hud_called", any(d is fowl for d, _ in seen), "handle_unit_death ran for the FOWL")
    check("cutting_rail_cleaned", not g.map.has_rails(), "rails cleaned up by the FOWL's death")


# ---------------------------------------------------------------------------
# INTERFERER — radiation / RF burn DoT  [units.py apply_radiation_damage]
# ---------------------------------------------------------------------------

def test_radiation_kill_fires_death_effects():
    g = fresh_game()
    ts = free_tiles(g, 4)
    fowl = add(g, UnitType.FOWL_CONTRIVANCE, 2, *ts[0])
    fowl.hp = 3
    fowl.radiation_stacks = [2, 2, 2, 2, 2]  # 5 stacks = 5 damage = lethal
    check("rf_rail_pre", lay_rail(g, {(fowl.y, fowl.x)}), "rail present before")
    seen = spy_on_deaths(g)
    fowl.apply_radiation_damage(g, None)
    check("rf_fowl_dead", not fowl.is_alive(), f"FOWL hp={fowl.hp}")
    check("rf_hud_called", any(d is fowl for d, _ in seen), "handle_unit_death ran for the FOWL")
    check("rf_rail_cleaned", not g.map.has_rails(), "rails cleaned up by the FOWL's death")


def main():
    test_demilune_kill_fires_death_effects()
    test_granite_geas_kill_fires_death_effects()
    test_broaching_gas_kill_fires_death_effects()
    test_cutting_gas_kill_fires_death_effects()
    test_radiation_kill_fires_death_effects()

    print("\n==== DEATH-EFFECT DISPATCH (cross-skill) ====")
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
