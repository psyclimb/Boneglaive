#!/usr/bin/env python3
"""
Test script to verify unit positions are correct.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.renderer import GRID_WIDTH, GRID_HEIGHT


def test_unit_positions():
    """Verify units are positioned within the visible grid."""
    print("=" * 60)
    print("Testing Unit Positions")
    print("=" * 60)

    # Initialize game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)

    print(f"\nGame map: {adapter.game.map.height} rows x {adapter.game.map.width} cols")
    print(f"Renderer grid: {GRID_HEIGHT} rows x {GRID_WIDTH} cols")
    print()

    # Check if grid matches map
    if GRID_WIDTH != adapter.game.map.width:
        print(f"⚠ WARNING: Grid width ({GRID_WIDTH}) != Map width ({adapter.game.map.width})")
    if GRID_HEIGHT != adapter.game.map.height:
        print(f"⚠ WARNING: Grid height ({GRID_HEIGHT}) != Map height ({adapter.game.map.height})")

    if GRID_WIDTH == adapter.game.map.width and GRID_HEIGHT == adapter.game.map.height:
        print("✓ Grid dimensions match map dimensions!")

    print(f"\nUnits: {len(adapter.game.units)}")
    print()

    all_valid = True
    for i, unit in enumerate(adapter.game.units, 1):
        x, y = unit.x, unit.y
        in_bounds = (0 <= x < GRID_WIDTH) and (0 <= y < GRID_HEIGHT)
        status = "✓" if in_bounds else "✗ OUT OF BOUNDS"

        print(f"{i}. {unit.type.name}")
        print(f"   Position: (x={x}, y={y}) = (col {x}, row {y})")
        print(f"   Player: {unit.player}")
        print(f"   Status: {status}")

        if not in_bounds:
            all_valid = False
            if x < 0 or x >= GRID_WIDTH:
                print(f"   ⚠ X coordinate {x} is outside grid width [0, {GRID_WIDTH-1}]")
            if y < 0 or y >= GRID_HEIGHT:
                print(f"   ⚠ Y coordinate {y} is outside grid height [0, {GRID_HEIGHT-1}]")
        print()

    print("=" * 60)
    if all_valid:
        print("✓ ALL UNITS ARE WITHIN GRID BOUNDS")
        print("=" * 60)
        return True
    else:
        print("✗ SOME UNITS ARE OUT OF BOUNDS")
        print("=" * 60)
        return False


if __name__ == "__main__":
    try:
        success = test_unit_positions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
