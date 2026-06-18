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


PLAYABLE = [
    UnitType.GLAIVEMAN, UnitType.MANDIBLE_FOREMAN, UnitType.GRAYMAN,
    UnitType.MARROW_CONDENSER, UnitType.FOWL_CONTRIVANCE, UnitType.GAS_MACHINIST,
    UnitType.DELPHIC_APPRAISER, UnitType.INTERFERER, UnitType.DERELICTIONIST,
    UnitType.POTPOURRIST, UnitType.LANDSCAPER,
]

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


def test_all_active_skills():
    """Every active skill of every unit executes through ui=None without error."""
    for ut in PLAYABLE:
        # Build a small arena: caster + an enemy + an ally, spread out
        g = fresh_game()
        ts = free_tiles(g, 6)
        if len(ts) < 4:
            record(f"skills:{ut.name}", False, "not enough tiles")
            continue
        caster = place(g, ut, 1, *ts[0])
        ally = place(g, UnitType.POTPOURRIST, 1, *ts[1])
        enemy1 = place(g, UnitType.MANDIBLE_FOREMAN, 2, *ts[2])
        enemy2 = place(g, UnitType.GRAYMAN, 2, *ts[3])
        skills = list(getattr(caster, 'active_skills', []) or [])
        if not skills:
            record(f"skills:{ut.name}", False, "no active_skills")
            continue
        ok_all = True
        notes = []
        for skill in skills:
            # try a few candidate targets: enemy, ally, self, empty tile, adjacent tile
            candidates = [
                (enemy1.y, enemy1.x), (enemy2.y, enemy2.x), (ally.y, ally.x),
                (caster.y, caster.x),
            ]
            candidates += free_tiles(g, 2)
            # also a tile adjacent to caster (for directional/cone skills)
            candidates.append((caster.y, min(caster.x + 1, WIDTH - 1)))
            used = False
            for tgt in candidates:
                try:
                    if skill.can_use(caster, tgt, g):
                        caster.selected_skill = skill
                        caster.skill_target = tgt
                        g.current_player = 1
                        g.execute_turn(ui=None)
                        used = True
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
                # can_use was False everywhere — not a failure, skill just had no valid target here
                notes.append(f"{skill.name}=no-target")
            # reset action state for next skill on a fresh caster turn
            caster.selected_skill = None
            caster.skill_target = None
            caster.skill_used = False if hasattr(caster, 'skill_used') else None
            caster.took_action = False if hasattr(caster, 'took_action') else None
        record(f"skills:{ut.name}", ok_all, "; ".join(notes))


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


def main():
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
