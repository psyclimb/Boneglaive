#!/usr/bin/env python3
"""Walk-in behaviour shared by the movement skills (Vault, Delta Config, Expedite, Jaunt).

When the player queues a move BEFORE one of these skills, the unit should visually walk to
the move tile and then perform the skill FROM there. The skills carry the move destination to
their animations via Unit.skill_walkin_from (set in use() / execute() when a move was queued,
cleared otherwise), and the shared core.WalkIn helper drives the actual walk A->B.

This test asserts the headless contract (the carrier) plus the WalkIn helper's geometry. The
per-skill animation framing (origin at B, walk first) is verified separately via render traces;
here we lock in the data plumbing that feeds it.

Run: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_movement_skill_walkin.py
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
from boneglaive.utils.constants import UnitType

results = []


def check(name, cond, note=""):
    results.append((name, bool(cond), note))


def fresh_game(map_name="lime_foyer"):
    g = Game(skip_setup=True, map_name=map_name)
    g.units = []
    g.unit_grid = {}
    return g


def place(g, utype, player, y, x):
    g.add_unit(utype, player, y, x)
    return g.get_unit_at(y, x)


def skill_named(unit, name):
    for s in unit.active_skills:
        if s.name == name:
            return s
    return None


# ---------------------------------------------------------------------------
# Each movement skill records the queued move destination in skill_walkin_from
# (so its animation can walk there first), and leaves it None with no move.
# ---------------------------------------------------------------------------

def test_vault_records_walkin_from_move():
    """Vault (absolute teleport) hands the queued move tile to the animation; with no queued
    move it leaves the carrier None."""
    g = fresh_game()
    glaive = place(g, UnitType.GLAIVEMAN, 1, 7, 5)
    vault = skill_named(glaive, "Vault")
    # Move to (5,5), then Vault (range 2) to an empty tile (5,7) reachable from the move tile.
    glaive.move_target = (5, 5)
    check("vault_can_use_from_move", vault.can_use(glaive, (5, 7), g) is True, "setup")
    vault.use(glaive, (5, 7), g)
    check("vault_walkin_set", glaive.skill_walkin_from == (5, 5),
          f"skill_walkin_from={glaive.skill_walkin_from} (want (5,5))")
    check("vault_move_cleared", glaive.move_target is None, "Vault clears move_target")

    # No queued move -> no walk-in.
    g2 = fresh_game()
    glaive2 = place(g2, UnitType.GLAIVEMAN, 1, 5, 5)
    v2 = skill_named(glaive2, "Vault")
    v2.use(glaive2, (5, 7), g2)
    check("vault_walkin_none_without_move", glaive2.skill_walkin_from is None,
          f"skill_walkin_from={glaive2.skill_walkin_from} (want None)")


def test_delta_config_records_walkin_from_move():
    """Delta Config keeps move_target (the engine walks him then teleports); it still hands the
    move tile to the animation so the teleport-pull originates there visually."""
    g = fresh_game()
    gray = place(g, UnitType.GRAYMAN, 1, 5, 2)
    delta = skill_named(gray, "Delta Config")
    gray.move_target = (5, 4)
    check("delta_can_use_from_move", delta.can_use(gray, (5, 8), g) is True, "setup")
    delta.use(gray, (5, 8), g)
    check("delta_walkin_set", gray.skill_walkin_from == (5, 4),
          f"skill_walkin_from={gray.skill_walkin_from} (want (5,4))")
    # Delta deliberately KEEPS move_target (engine performs the move, then the teleport).
    check("delta_keeps_move", gray.move_target == (5, 4),
          f"move_target={gray.move_target} (Delta keeps it for the real move)")

    g2 = fresh_game()
    gray2 = place(g2, UnitType.GRAYMAN, 1, 5, 2)
    d2 = skill_named(gray2, "Delta Config")
    d2.use(gray2, (5, 6), g2)
    check("delta_walkin_none_without_move", gray2.skill_walkin_from is None,
          f"skill_walkin_from={gray2.skill_walkin_from} (want None)")


def test_expedite_records_walkin_from_move():
    """Expedite (line dash) already dashes from the move tile; it also hands that tile to the
    walk-in so the sprite walks there before the dash."""
    g = fresh_game()
    foreman = place(g, UnitType.MANDIBLE_FOREMAN, 1, 5, 2)
    enemy = place(g, UnitType.GLAIVEMAN, 2, 5, 8)   # dash anchor in line from the move tile
    expedite = skill_named(foreman, "Expedite")
    foreman.move_target = (5, 4)
    check("expedite_can_use_from_move", expedite.can_use(foreman, (5, 8), g) is True, "setup")
    expedite.use(foreman, (5, 8), g)
    check("expedite_walkin_set", foreman.skill_walkin_from == (5, 4),
          f"skill_walkin_from={foreman.skill_walkin_from} (want (5,4))")
    check("expedite_move_cleared", foreman.move_target is None, "Expedite clears move_target")
    check("expedite_planned_start_set", foreman.expedite_planned_start == (5, 4),
          "the dash still starts from the move tile too")

    g2 = fresh_game()
    foreman2 = place(g2, UnitType.MANDIBLE_FOREMAN, 1, 5, 2)
    place(g2, UnitType.GLAIVEMAN, 2, 5, 6)
    e2 = skill_named(foreman2, "Expedite")
    e2.use(foreman2, (5, 6), g2)
    check("expedite_walkin_none_without_move", foreman2.skill_walkin_from is None,
          f"skill_walkin_from={foreman2.skill_walkin_from} (want None)")


# ---------------------------------------------------------------------------
# The shared WalkIn helper: walks A->B over a distance-scaled duration; inert
# when there's no launch tile (or it equals the current tile).
# ---------------------------------------------------------------------------

def test_walkin_helper_walks_and_is_inert_without_move():
    import pygame
    pygame.init()
    from boneglaive.graphical.animations.core import WalkIn, TILE_SIZE
    from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y

    def scr(y, x):
        return (x * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X,
                y * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y)

    class Sprite:
        def __init__(self, y, x):
            self.x, self.y = scr(y, x)
            self.target_x, self.target_y = self.x, self.y
            self.is_moving = False

    # With a launch tile B != A: walks there.
    s = Sprite(7, 5)                       # A
    w = WalkIn(s, (5, 5))                  # B
    bx, by = scr(5, 5)
    check("walkin_had_walk", w.had_walk is True, "a move was queued")
    check("walkin_dur_positive", w.duration > 0.0, f"duration={w.duration}")
    dt, t = 1 / 60.0, 0.0
    midpoint = None
    while w.update(dt) and t < 2.0:
        t += dt
        if midpoint is None and t > 0.03:
            midpoint = (s.x, s.y)
    # Mid-walk he's strictly between A and B (moving up a column: x constant, y decreasing).
    ay = scr(7, 5)[1]
    check("walkin_midpoint_between", midpoint is not None and by < midpoint[1] < ay,
          f"mid_y={None if midpoint is None else round(midpoint[1])} (want between {by} and {ay})")
    check("walkin_arrives_at_b", (round(s.x), round(s.y)) == (round(bx), round(by)),
          f"end=({round(s.x)},{round(s.y)}) want B=({round(bx)},{round(by)})")

    # No launch tile -> inert: never moves, first update returns False.
    s2 = Sprite(5, 5)
    w2 = WalkIn(s2, None)
    check("walkin_inert_no_move", w2.had_walk is False and w2.update(dt) is False,
          "no queued move -> inert")
    # Launch tile equal to current tile -> also inert.
    s3 = Sprite(4, 4)
    w3 = WalkIn(s3, (4, 4))
    check("walkin_inert_same_tile", w3.had_walk is False, "launch tile == current tile -> inert")


def test_walkin_clears_hop_offset_on_arrival():
    """Regression: a move-then-skill walk-in must not leave the sprite floating above its tile.

    WalkIn borrows AnimatedUnit's walk cycle (it sets is_moving=True each frame so the unit's
    own update plays the stride), which raises hop_offset — a value draw() SUBTRACTS from y.
    WalkIn ends the walk by forcing is_moving=False. When the walk's timer runs out on a frame
    where the eased sprite is still >2px from B, the unit-update arrival branch (distance<2,
    the only OTHER place hop_offset is zeroed) doesn't fire that frame, so a mid-stride hop is
    left frozen and draws the sprite skewed upward for the rest of the game (the Jaunt bug).
    Whether that window is hit depends on framerate — at ~30 FPS the leftover reaches ~14px.

    Drives the REAL AnimatedUnit through the documented per-frame order (unit.update THEN
    walk.update). Uses a low-FPS dt and a multi-tile route chosen so the walk ends inside that
    unclean window (so the test genuinely fails without WalkIn's own hop reset)."""
    import pygame
    pygame.init()
    from boneglaive.graphical.animations.core import AnimatedUnit, WalkIn

    # dt=1/30 (30 FPS) + a 6-tile horizontal route lands WalkIn's arrival frame while the
    # sprite is still mid-hop and >2px short of B — the exact case the fix addresses.
    dt = 1 / 30.0
    unit = AnimatedUnit("graft", 1, grid_x=2, grid_y=5, color=(200, 200, 200))
    w = WalkIn(unit, (5, 8))   # B = (y=5, x=8), six tiles across
    check("hop_walkin_started", w.had_walk is True, "a move was queued")

    t = 0.0
    hop_peaked = False
    walking = True
    while walking and t < 2.0:
        unit.update(dt)                 # unit's own per-frame update runs FIRST (raises hop)
        if unit.hop_offset > 0.5:
            hop_peaked = True
        walking = w.update(dt)          # then the controller advances the walk-in
        t += dt

    # The stride must actually have hopped at some point (else the test proves nothing)...
    check("hop_rose_during_walk", hop_peaked is True,
          f"hop_offset never rose during the walk (peaked={hop_peaked})")
    # ...and must be flat again once he's arrived, so draw() centers him on the tile.
    check("hop_cleared_on_arrival", unit.hop_offset == 0,
          f"hop_offset={unit.hop_offset} after arrival (want 0 — non-zero floats the sprite up)")
    check("walkin_landed_and_stopped", unit.is_moving is False, "walk-in ends stopped")


def main():
    test_vault_records_walkin_from_move()
    test_delta_config_records_walkin_from_move()
    test_expedite_records_walkin_from_move()
    test_walkin_helper_walks_and_is_inert_without_move()
    test_walkin_clears_hop_offset_on_arrival()

    print("==== MOVEMENT-SKILL WALK-IN ====")
    passed = 0
    for name, ok, note in results:
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}  ({note})")
        passed += ok
    print("==== ALL PASS ====" if passed == len(results) else f"==== {len(results) - passed} FAILED ====")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
