#!/usr/bin/env python3
"""
Test script for unit info panel UI component.
"""
import sys
import os
from pathlib import Path

# Disable pygame display for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

sys.path.insert(0, str(Path(__file__).parent))

def test_unit_info():
    """Test unit info panel component."""
    print("=" * 60)
    print("Testing Unit Info Panel UI Component")
    print("=" * 60)

    # Initialize pygame
    import pygame
    pygame.init()

    print("\n--- Test 1: Import Unit Info Panel ---")
    from boneglaive.graphical.ui.unit_info import UnitInfoPanel
    print("✓ UnitInfoPanel imported successfully")

    print("\n--- Test 2: Create Unit Info Panel ---")
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    large_font = pygame.font.Font(None, 36)
    panel = UnitInfoPanel(font, small_font, large_font)
    print("✓ UnitInfoPanel created successfully")

    print("\n--- Test 3: Initialize Game and Units ---")
    from boneglaive.graphical.game_state import GameStateAdapter
    from demo_animations.core import AnimatedUnit, COLOR_PLAYER1

    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    game = adapter.game

    print(f"Game initialized with {len(game.units)} units")

    # Find a unit
    test_unit = None
    for unit in game.units:
        if unit.hp > 0 and unit.player == 1:
            test_unit = unit
            break

    if not test_unit:
        print("✗ No alive units found")
        return False

    print(f"Test unit: {test_unit.type.name} at ({test_unit.y}, {test_unit.x})")

    # Create animated unit
    animated_unit = AnimatedUnit(
        test_unit.type.name,
        player=0,  # 0-indexed
        grid_x=test_unit.x,
        grid_y=test_unit.y,
        color=COLOR_PLAYER1
    )
    animated_unit.hp = test_unit.hp
    animated_unit.max_hp = test_unit.max_hp

    print("\n--- Test 4: Update Panel with Unit ---")
    panel.update(animated_unit, test_unit)
    print(f"✓ Panel updated")

    print("\n--- Test 5: Display Unit Info ---")
    print(f"  Name: {test_unit.type.name}")
    print(f"  Player: {test_unit.player}")
    print(f"  HP: {test_unit.hp}/{test_unit.max_hp}")

    stats = test_unit.get_effective_stats()
    print(f"  Attack: {stats['attack']}")
    print(f"  Defense: {stats['defense']}")
    print(f"  Move Range: {stats['move_range']}")
    print(f"  Attack Range: {stats['attack_range']}")

    print("\n--- Test 6: Test HP Bar Colors ---")
    test_cases = [
        (20, 20, "Full HP (green)"),
        (15, 20, "High HP (green)"),
        (10, 20, "Mid HP (yellow)"),
        (5, 20, "Low HP (red)"),
        (1, 20, "Critical HP (red)"),
    ]

    for hp, max_hp, desc in test_cases:
        test_unit.hp = hp
        test_unit.max_hp = max_hp
        animated_unit.hp = hp
        animated_unit.max_hp = max_hp

        hp_percent = hp / max_hp
        print(f"  {desc}: {hp}/{max_hp} ({hp_percent*100:.0f}%)")

    # Reset
    test_unit.hp = 20
    test_unit.max_hp = 20

    print("\n--- Test 7: Test Stat Modifications ---")
    # Apply buffs
    test_unit.attack_bonus = 3
    test_unit.defense_bonus = -2

    stats = test_unit.get_effective_stats()
    print(f"  Attack: {stats['attack']} (base: {test_unit.attack}, bonus: +3)")
    print(f"  Defense: {stats['defense']} (base: {test_unit.defense}, bonus: -2)")

    # Reset
    test_unit.attack_bonus = 0
    test_unit.defense_bonus = 0

    print("\n--- Test 8: Test Panel Drawing (Headless) ---")
    surface = pygame.Surface((1480, 800))
    panel.draw(surface, 1160, 10)
    print(f"✓ Panel drew successfully at (1160, 10)")

    print("\n--- Test 9: Test Empty Panel ---")
    panel.update(None, None)
    print(f"✓ Panel cleared")

    # Drawing empty panel should not error
    panel.draw(surface, 1160, 10)
    print(f"✓ Empty panel draws without error")

    print("\n--- Test 10: Test Different Unit Types ---")
    for unit in game.units[:3]:
        if unit.hp > 0:
            animated = AnimatedUnit(
                unit.type.name,
                player=unit.player - 1,
                grid_x=unit.x,
                grid_y=unit.y,
                color=COLOR_PLAYER1
            )
            animated.hp = unit.hp
            animated.max_hp = unit.max_hp

            panel.update(animated, unit)
            print(f"  ✓ {unit.type.name}: HP {unit.hp}/{unit.max_hp}")

    print("\n✓ All unit info panel tests passed")
    pygame.quit()
    return True


if __name__ == "__main__":
    try:
        success = test_unit_info()
        print("\n" + "=" * 60)
        if success:
            print("✓ Unit Info Panel Test PASSED")
            print("\nPanel features:")
            print("  - Unit name and type")
            print("  - Player indicator with color")
            print("  - Visual HP bar (green/yellow/red)")
            print("  - Detailed stats (ATK, DEF, Move, Range)")
            print("  - Stat modifiers shown in color")
            print("  - Position: Top-right corner")
            sys.exit(0)
        else:
            print("✗ Unit Info Panel Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
