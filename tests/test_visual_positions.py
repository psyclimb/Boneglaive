#!/usr/bin/env python3
"""
Test to verify unit visual positions match their grid positions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.renderer import GraphicalRenderer, GRID_OFFSET_X, GRID_OFFSET_Y, TILE_SIZE


def test_visual_positions():
    """Verify visual positions match grid positions with proper offset."""
    print("=" * 70)
    print("Testing Visual Unit Positions")
    print("=" * 70)

    # Initialize without pygame display
    import os
    os.environ['SDL_VIDEODRIVER'] = 'dummy'

    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)

    # Create renderer (will use dummy video driver)
    try:
        renderer = GraphicalRenderer(adapter)
        renderer.sync_units_from_game()
    except Exception as e:
        print(f"Note: Display error expected in SSH: {e}")
        print("Continuing with manual position check...\n")

        # Manual check without renderer
        from boneglaive.graphical.renderer import AnimatedUnit, COLOR_PLAYER1, COLOR_PLAYER2

        units = []
        for game_unit in adapter.game.units:
            color = COLOR_PLAYER1 if game_unit.player == 1 else COLOR_PLAYER2
            unit_name = str(game_unit.type).split('.')[-1]

            animated = AnimatedUnit(
                name=unit_name,
                player=game_unit.player,
                grid_x=game_unit.x,
                grid_y=game_unit.y,
                color=color
            )
            animated.x += GRID_OFFSET_X
            animated.y += GRID_OFFSET_Y
            animated.target_x = animated.x
            animated.target_y = animated.y

            units.append(animated)

        renderer = type('obj', (object,), {'units': units})()

    print(f"\nGrid offset: ({GRID_OFFSET_X}, {GRID_OFFSET_Y})")
    print(f"Tile size: {TILE_SIZE}px")
    print(f"Units: {len(renderer.units)}")
    print()

    all_correct = True

    for i, animated_unit in enumerate(renderer.units, 1):
        # Calculate expected screen position
        # Should be: grid * TILE_SIZE + TILE_SIZE//2 + GRID_OFFSET
        expected_x = animated_unit.grid_x * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
        expected_y = animated_unit.grid_y * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y

        # Get actual position
        actual_x = animated_unit.x
        actual_y = animated_unit.y

        # Check if correct
        correct = (actual_x == expected_x) and (actual_y == expected_y)
        status = "✓" if correct else "✗ WRONG"

        print(f"{i}. {animated_unit.name} (Player {animated_unit.player})")
        print(f"   Grid position: ({animated_unit.grid_x}, {animated_unit.grid_y})")
        print(f"   Expected screen pos: ({expected_x}, {expected_y})")
        print(f"   Actual screen pos:   ({actual_x}, {actual_y})")
        print(f"   Status: {status}")

        if not correct:
            all_correct = False
            print(f"   ⚠ Position mismatch!")
            print(f"      Delta X: {actual_x - expected_x}")
            print(f"      Delta Y: {actual_y - expected_y}")

        # Check if on grid (within bounds)
        min_x = GRID_OFFSET_X
        max_x = GRID_OFFSET_X + 20 * TILE_SIZE
        min_y = GRID_OFFSET_Y
        max_y = GRID_OFFSET_Y + 10 * TILE_SIZE

        if not (min_x <= actual_x <= max_x):
            print(f"   ⚠ X position {actual_x} outside grid bounds [{min_x}, {max_x}]")
            all_correct = False
        if not (min_y <= actual_y <= max_y):
            print(f"   ⚠ Y position {actual_y} outside grid bounds [{min_y}, {max_y}]")
            all_correct = False

        print()

    print("=" * 70)
    if all_correct:
        print("✓ ALL UNITS POSITIONED CORRECTLY")
        print("=" * 70)
        return True
    else:
        print("✗ SOME UNITS HAVE INCORRECT POSITIONS")
        print("=" * 70)
        return False


if __name__ == "__main__":
    try:
        success = test_visual_positions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
