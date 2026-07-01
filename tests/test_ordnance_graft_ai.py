#!/usr/bin/env python3
"""AI-decision tests for ORDNANCE GRAFT — does the bot play its kit correctly?

The FIRST test in the suite that drives the AI's TacticalEvaluator directly (the
others drive the engine/skills). It builds a battlefield, runs the real AI inputs
(BattlefieldAnalyzer -> StrategicPlanner) as player 2, and asserts on the scored
actions the evaluator returns: that Harvest fires on a lethal cluster, that
planting favours the big (anti-tank) body, that Skyhook needs a living drone, and
that the QUADCOPTER drone coordinates onto the graft's focus.

Run with: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_ordnance_graft_ai.py
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
from boneglaive.utils.constants import UnitType, HEIGHT, WIDTH
from boneglaive.game.skills.ordnance_graft import plant_bomb, arm_bombs, fused_count
from boneglaive.ai.battlefield_analyzer import BattlefieldAnalyzer
from boneglaive.ai.strategic_planner import StrategicPlanner
from boneglaive.ai.tactical_evaluator import TacticalEvaluator

AI_PLAYER = 2  # SmartAI.player_number is hardcoded to 2

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


def build_ai(g, ai_player=AI_PLAYER):
    """Construct the real AI inputs the evaluator consumes."""
    analysis = BattlefieldAnalyzer(g, ai_player).analyze()
    plan = StrategicPlanner(g, ai_player).plan(analysis)
    ev = TacticalEvaluator(g, ai_player)
    return analysis, plan, ev


def graft_skill(unit, name):
    for s in unit.active_skills:
        if s.name == name:
            return s
    return None


def skill_actions(actions, name):
    """Filter a returned action list to skill actions of a given skill name."""
    out = []
    for a in actions:
        if a.type == "skill" and a.target and a.target[0].name == name:
            out.append(a)
    return out


# ---------------------------------------------------------------------------
# (a) Harvest is chosen when a lethal fused stack exists on a tank.
# ---------------------------------------------------------------------------
def test_harvest_fires_when_lethal():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    # Put the tank adjacent so the graft also *could* basic-attack/Inoculant it —
    # Harvest must still win because a full fused cluster one-shots it.
    ey, ex = next((y, x) for (y, x) in ts
                  if max(abs(y - gy), abs(x - gx)) == 1 and (y, x) != (gy, gx))
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    tank = place(g, UnitType.POTPOURRIST, 1, ey, ex)  # 24 HP
    # Spawn the drone so Skyhook is also an option (Harvest must still beat it).
    g.current_player = AI_PLAYER
    g._process_ordnance_graft_upkeep()

    plant_bomb(tank, 4)
    arm_bombs(tank)  # 4 fused stacks on a 24-HP body -> one-shot

    analysis, plan, ev = build_ai(g)
    actions = ev.evaluate_unit_actions(graft, analysis, plan)
    top = actions[0] if actions else None
    top_name = top.target[0].name if (top and top.type == "skill") else (top.type if top else "none")
    ok = bool(actions) and top.type == "skill" and top.target[0].name == "Harvest"
    check("harvest_fires_when_lethal", ok,
          f"top={top_name} pri={round(top.priority,1) if top else 0}")


# ---------------------------------------------------------------------------
# (b) Inoculant prefers the higher-max-HP (anti-tank) enemy over a squishy.
# ---------------------------------------------------------------------------
def test_inoculant_prefers_tank():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    # Two enemies both within range 2 of the graft, NEITHER effect-immune.
    near = [(y, x) for (y, x) in ts
            if 1 <= max(abs(y - gy), abs(x - gx)) <= 2 and (y, x) != (gy, gx)
                  and g.has_line_of_sight(gy, gx, y, x)]
    (ty, tx), (sy, sx) = near[0], near[1]
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    tank = place(g, UnitType.POTPOURRIST, 1, ty, tx)      # 24 HP
    squishy = place(g, UnitType.INTERFERER, 1, sy, sx)    # 18 HP, not immune

    analysis, plan, ev = build_ai(g)
    inocs = skill_actions(ev._evaluate_ordnance_graft_skills(graft, analysis, plan), "Inoculant")
    best = max(inocs, key=lambda a: a.priority) if inocs else None
    chosen = best.target[1] if best else None
    ok = chosen is tank
    check("inoculant_prefers_tank", ok,
          f"n={len(inocs)} chose_max_hp={getattr(chosen,'max_hp',None)}")


# ---------------------------------------------------------------------------
# (b2) The anti-tank value term itself orders tank > squishy, and an immune body low.
# ---------------------------------------------------------------------------
def test_target_value_ordering():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    tank = place(g, UnitType.POTPOURRIST, 1, *ts[5])     # 24 HP
    squishy = place(g, UnitType.INTERFERER, 1, *ts[10])  # 18 HP
    immune = place(g, UnitType.GRAYMAN, 1, *ts[15])      # 18 HP but effect-immune

    analysis, plan, ev = build_ai(g)
    tv_tank = ev._ordnance_target_value(tank, analysis, plan)
    tv_squishy = ev._ordnance_target_value(squishy, analysis, plan)
    tv_immune = ev._ordnance_target_value(immune, analysis, plan)
    ok = tv_tank > tv_squishy > tv_immune
    check("target_value_ordering", ok,
          f"tank={round(tv_tank,1)} squishy={round(tv_squishy,1)} immune={round(tv_immune,1)}")


# ---------------------------------------------------------------------------
# (c) Skyhook is not offered without a living drone, and IS once the drone exists.
# ---------------------------------------------------------------------------
def test_skyhook_requires_drone():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts
                  if 1 <= max(abs(y - gy), abs(x - gx)) <= 2 and (y, x) != (gy, gx)
                  and g.has_line_of_sight(gy, gx, y, x))
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    enemy = place(g, UnitType.POTPOURRIST, 1, ey, ex)
    graft.drone = None  # explicitly no drone

    analysis, plan, ev = build_ai(g)
    no_drone = skill_actions(ev._evaluate_ordnance_graft_skills(graft, analysis, plan), "Skyhook")
    check("skyhook_blocked_without_drone", len(no_drone) == 0, f"offered={len(no_drone)}")

    # Now spawn the drone and re-evaluate: a Skyhook landing should be available.
    g.current_player = AI_PLAYER
    g._process_ordnance_graft_upkeep()
    analysis, plan, ev = build_ai(g)
    with_drone = skill_actions(ev._evaluate_ordnance_graft_skills(graft, analysis, plan), "Skyhook")
    check("skyhook_offered_with_drone", len(with_drone) >= 1,
          f"drone={'live' if (graft.drone and graft.drone.is_alive()) else 'none'} offered={len(with_drone)}")


# ---------------------------------------------------------------------------
# (d) The drone plants on the SAME enemy the graft is fusing this turn.
# ---------------------------------------------------------------------------
def test_drone_follows_graft_focus():
    g = fresh_game()
    ts = free_tiles(g, 60)
    gy, gx = ts[0]
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    g.current_player = AI_PLAYER
    g._process_ordnance_graft_upkeep()  # spawn the drone adjacent to the graft
    drone = graft.drone
    assert drone is not None, "drone failed to spawn"

    # Two enemies both reachable by the DRONE (Chebyshev <= 2 of the drone tile),
    # both non-immune. Tank is the LOWER-value-by-position pick to prove focus wins:
    # make the squishy the global best-by-nothing and force focus onto the tank.
    near = [(y, x) for (y, x) in ts
            if 1 <= max(abs(y - drone.y), abs(x - drone.x)) <= 2
            and g.get_unit_at(y, x) is None
            and g.has_line_of_sight(drone.y, drone.x, y, x)]
    (ty, tx), (sy, sx) = near[0], near[1]
    tank = place(g, UnitType.POTPOURRIST, 1, ty, tx)    # 24 HP
    squishy = place(g, UnitType.INTERFERER, 1, sy, sx)  # 18 HP

    # Simulate the graft having queued Inoculant on the SQUISHY this turn (so focus
    # must override the drone's natural anti-tank preference for the tank).
    graft.selected_skill = graft_skill(graft, "Inoculant")
    graft.skill_target = (squishy.y, squishy.x)

    analysis, plan, ev = build_ai(g)
    drone_inocs = skill_actions(ev._evaluate_ordnance_drone_skills(drone, analysis, plan), "Inoculant")
    best = max(drone_inocs, key=lambda a: a.priority) if drone_inocs else None
    chosen = best.target[1] if best else None
    ok = chosen is squishy  # followed the graft's focus, NOT the higher-value tank
    check("drone_follows_graft_focus", ok,
          f"n={len(drone_inocs)} chose_max_hp={getattr(chosen,'max_hp',None)} (focus=squishy18)")


# ---------------------------------------------------------------------------
# (d2) With no graft focus queued, the drone falls back to the best anti-tank target.
# ---------------------------------------------------------------------------
def test_drone_fallback_prefers_tank():
    g = fresh_game()
    ts = free_tiles(g, 60)
    gy, gx = ts[0]
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    g.current_player = AI_PLAYER
    g._process_ordnance_graft_upkeep()
    drone = graft.drone
    assert drone is not None

    near = [(y, x) for (y, x) in ts
            if 1 <= max(abs(y - drone.y), abs(x - drone.x)) <= 2
            and g.get_unit_at(y, x) is None
            and g.has_line_of_sight(drone.y, drone.x, y, x)]
    (ty, tx), (sy, sx) = near[0], near[1]
    tank = place(g, UnitType.POTPOURRIST, 1, ty, tx)
    squishy = place(g, UnitType.INTERFERER, 1, sy, sx)

    # No queued focus this turn.
    graft.selected_skill = None
    graft.skill_target = None
    graft.attack_target = None

    analysis, plan, ev = build_ai(g)
    drone_inocs = skill_actions(ev._evaluate_ordnance_drone_skills(drone, analysis, plan), "Inoculant")
    best = max(drone_inocs, key=lambda a: a.priority) if drone_inocs else None
    chosen = best.target[1] if best else None
    ok = chosen is tank
    check("drone_fallback_prefers_tank", ok,
          f"n={len(drone_inocs)} chose_max_hp={getattr(chosen,'max_hp',None)}")


# ---------------------------------------------------------------------------
# (e) Harvest is WITHHELD on a lone trivial 1-stack squishy (build instead).
# ---------------------------------------------------------------------------
def test_harvest_withheld_on_lone_weak_stack():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts
                  if 1 <= max(abs(y - gy), abs(x - gx)) <= 2 and (y, x) != (gy, gx)
                  and g.has_line_of_sight(gy, gx, y, x))
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    squishy = place(g, UnitType.INTERFERER, 1, ey, ex)  # 18 HP -> 1 dmg/stack
    plant_bomb(squishy, 1)
    arm_bombs(squishy)  # a single fused 1-dmg bomb: not worth detonating

    analysis, plan, ev = build_ai(g)
    harv = graft_skill(graft, "Harvest")
    harvest_actions = ev._evaluate_ordnance_harvest(graft, harv, analysis, plan)
    check("harvest_withheld_on_lone_weak_stack", len(harvest_actions) == 0,
          f"offered={len(harvest_actions)} fused={fused_count(squishy)}")


# ---------------------------------------------------------------------------
# (e2) But Harvest fires on a lone squishy when the stack actually KILLS it.
# ---------------------------------------------------------------------------
def test_harvest_fires_on_lethal_squishy():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts
                  if 1 <= max(abs(y - gy), abs(x - gx)) <= 2 and (y, x) != (gy, gx)
                  and g.has_line_of_sight(gy, gx, y, x))
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    squishy = place(g, UnitType.INTERFERER, 1, ey, ex)  # 18 HP, 1 dmg/stack
    squishy.hp = 3  # already wounded -> a 4-stack (4 dmg) kills it
    plant_bomb(squishy, 4)
    arm_bombs(squishy)

    analysis, plan, ev = build_ai(g)
    harv = graft_skill(graft, "Harvest")
    harvest_actions = ev._evaluate_ordnance_harvest(graft, harv, analysis, plan)
    check("harvest_fires_on_lethal_squishy", len(harvest_actions) == 1,
          f"offered={len(harvest_actions)} hp={squishy.hp} fused={fused_count(squishy)}")


# ---------------------------------------------------------------------------
# (f) Sanity: a brand-new graft with a target produces a real skill action (no crash,
#     and the evaluator beats doing nothing).
# ---------------------------------------------------------------------------
def test_graft_produces_actions():
    g = fresh_game()
    ts = free_tiles(g, 40)
    gy, gx = ts[0]
    ey, ex = next((y, x) for (y, x) in ts
                  if 1 <= max(abs(y - gy), abs(x - gx)) <= 2 and (y, x) != (gy, gx)
                  and g.has_line_of_sight(gy, gx, y, x))
    graft = place(g, UnitType.ORDNANCE_GRAFT, AI_PLAYER, gy, gx)
    enemy = place(g, UnitType.POTPOURRIST, 1, ey, ex)

    analysis, plan, ev = build_ai(g)
    acts = ev._evaluate_ordnance_graft_skills(graft, analysis, plan)
    # Should at least offer Inoculant on the in-range tank.
    inocs = skill_actions(acts, "Inoculant")
    check("graft_produces_actions", len(inocs) >= 1, f"skill_actions={len(acts)} inoc={len(inocs)}")


def main():
    test_harvest_fires_when_lethal()
    test_inoculant_prefers_tank()
    test_target_value_ordering()
    test_skyhook_requires_drone()
    test_drone_follows_graft_focus()
    test_drone_fallback_prefers_tank()
    test_harvest_withheld_on_lone_weak_stack()
    test_harvest_fires_on_lethal_squishy()
    test_graft_produces_actions()

    print("\n==== ORDNANCE GRAFT AI ====")
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
