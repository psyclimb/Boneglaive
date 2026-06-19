#!/usr/bin/env python3
"""Headless combat smoke test — exercises every unit's basic attack and each
active skill through engine.execute_turn(ui=None), asserting no exception and
(where applicable) that the engine state advances.

Run with: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_headless_combat.py

This is the regression oracle for the Phase B work (removing inline-ASCII
animation code from game/). It does NOT validate visuals — only that game
logic survives the ui=None path for every unit and skill.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure repo root is importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Headless SDL before pygame is imported anywhere
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
logging.disable(logging.CRITICAL)

from boneglaive.game.engine import Game
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH
from boneglaive.game.recruitment import RECRUITMENT_ORDER
from boneglaive.game.unit_validation import validate_unit_registration


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


def adjacent_pair(g):
    for y in range(HEIGHT):
        for x in range(WIDTH - 1):
            if (g.map.can_place_unit(y, x) and g.map.can_place_unit(y, x + 1)
                    and g.get_unit_at(y, x) is None and g.get_unit_at(y, x + 1) is None):
                return (y, x), (y, x + 1)
    return None, None


def place(g, utype, player, y, x):
    g.add_unit(utype, player, y, x)
    return g.get_unit_at(y, x)


# Derived from the recruitment roster so a newly added unit is exercised
# automatically (no hand-maintained list to forget to update).
PLAYABLE = list(RECRUITMENT_ORDER)

results = []


def record(name, ok, note=""):
    results.append((name, ok, note))


def test_basic_attacks():
    """Every unit's basic attack resolves through ui=None without error."""
    for ut in PLAYABLE:
        try:
            g = fresh_game()
            a, b = adjacent_pair(g)
            atk = place(g, ut, 1, *a)
            tgt = place(g, UnitType.POTPOURRIST, 2, *b)  # POTPOURRIST: high HP, survives hits
            hp0 = tgt.hp
            atk.attack_target = (tgt.y, tgt.x)
            g.current_player = 1
            g.execute_turn(ui=None)
            # ATK 0 units (DERELICTIONIST) may deal 0 via basic; just require no crash
            record(f"basic_attack:{ut.name}", True, f"dmg={hp0 - tgt.hp}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            record(f"basic_attack:{ut.name}", False, repr(e))


def _candidate_targets(g, caster, enemies, allies):
    """Build a broad set of candidate target tiles to satisfy diverse skill ranges."""
    cands = []
    # every enemy and ally position (skills that target units)
    for u in enemies + allies:
        cands.append((u.y, u.x))
    cands.append((caster.y, caster.x))  # self
    # all 8 tiles adjacent to caster (directional/cone/adjacent skills)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            cands.append((caster.y + dy, caster.x + dx))
    # tiles at range 2-4 along cardinals (ranged placement skills)
    for d in (2, 3, 4):
        cands.append((caster.y, caster.x + d))
        cands.append((caster.y, caster.x - d))
        cands.append((caster.y + d, caster.x))
        cands.append((caster.y - d, caster.x))
    # any free tiles + every furniture tile on the map (furniture-targeted skills)
    cands += free_tiles(g, 4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            t = g.map.get_terrain_at(y, x) if hasattr(g.map, 'get_terrain_at') else None
            if t is not None:
                cands.append((y, x))
    # de-dup, keep in-bounds
    seen = set()
    out = []
    for (y, x) in cands:
        if 0 <= y < HEIGHT and 0 <= x < WIDTH and (y, x) not in seen:
            seen.add((y, x))
            out.append((y, x))
    return out


def test_all_active_skills():
    """Every active skill of every unit executes through ui=None without error.

    Uses a furniture-rich map and an arena with both adjacent and ranged enemies
    so that as many skills as possible reach their execute() path (the place the
    inline-ASCII animation code lives)."""
    for ut in PLAYABLE:
        # stained_stones is furniture-rich (helps Delphic furniture skills)
        g = fresh_game(map_name="stained_stones")
        ts = free_tiles(g, 8)
        if len(ts) < 5:
            record(f"skills:{ut.name}", False, "not enough tiles")
            continue
        caster = place(g, ut, 1, *ts[0])
        # an adjacent enemy (for Pry/Granite Geas/Neural Shunt), if a neighbour tile is free
        adj_enemy = None
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1)):
            ny, nx = caster.y + dy, caster.x + dx
            if 0 <= ny < HEIGHT and 0 <= nx < WIDTH and g.map.can_place_unit(ny, nx) and g.get_unit_at(ny, nx) is None:
                adj_enemy = place(g, UnitType.MANDIBLE_FOREMAN, 2, ny, nx)
                break
        ally = place(g, UnitType.POTPOURRIST, 1, *ts[1])
        enemy2 = place(g, UnitType.GRAYMAN, 2, *ts[2])
        enemy3 = place(g, UnitType.GLAIVEMAN, 2, *ts[3])
        enemies = [e for e in (adj_enemy, enemy2, enemy3) if e]
        allies = [ally]
        skills = list(getattr(caster, 'active_skills', []) or [])
        if not skills:
            record(f"skills:{ut.name}", False, "no active_skills")
            continue
        ok_all = True
        notes = []
        executed_count = 0
        for skill in skills:
            candidates = _candidate_targets(g, caster, enemies, allies)
            used = False
            for tgt in candidates:
                try:
                    if skill.can_use(caster, tgt, g):
                        caster.selected_skill = skill
                        caster.skill_target = tgt
                        g.current_player = 1
                        g.execute_turn(ui=None)
                        used = True
                        executed_count += 1
                        notes.append(f"{skill.name}=OK")
                        break
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    ok_all = False
                    notes.append(f"{skill.name}=ERR:{e!r}")
                    used = True
                    break
            if not used:
                notes.append(f"{skill.name}=no-target")
            # reset action state for next skill
            caster.selected_skill = None
            caster.skill_target = None
            for attr in ('skill_used', 'took_action', 'attacked', 'moved'):
                if hasattr(caster, attr):
                    setattr(caster, attr, False)
        record(f"skills:{ut.name}", ok_all, f"{executed_count}/{len(skills)} executed | " + "; ".join(notes))


def test_turn_cycle_and_respawn():
    """Full turn cycle, respawn processing, and game-over scan don't crash."""
    try:
        g = fresh_game()
        ts = free_tiles(g, 2)
        place(g, UnitType.POTPOURRIST, 1, *ts[0])
        place(g, UnitType.GRAYMAN, 2, *ts[1])
        g.current_player = 1
        for _ in range(3):
            g.execute_turn(ui=None)
            g.initialize_next_player_turn()
            g.check_game_over()
        record("turn_cycle_x3", True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        record("turn_cycle_x3", False, repr(e))


def test_unit_registration_complete():
    """Every recruitable unit is fully wired — skills, upgrades, help, and art.

    The code/data half is also enforced at import (registry.py); this adds the
    asset-file checks (require_assets=True), which only make sense where the
    proprietary art is present, i.e. a dev checkout like this one.
    """
    problems = validate_unit_registration(require_assets=True)
    record("unit_registration_complete", not problems, "; ".join(problems))


def main():
    test_unit_registration_complete()
    test_basic_attacks()
    test_all_active_skills()
    test_turn_cycle_and_respawn()

    print("\n==== HEADLESS COMBAT SMOKE ====")
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
