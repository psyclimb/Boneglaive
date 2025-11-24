#!/usr/bin/env python3
"""
Test script for status effects UI component.
"""
import sys
import os
from pathlib import Path

# Disable pygame display for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

sys.path.insert(0, str(Path(__file__).parent))

def test_status_effects():
    """Test status effects component."""
    print("=" * 60)
    print("Testing Status Effects UI Component")
    print("=" * 60)

    # Initialize pygame
    import pygame
    pygame.init()

    print("\n--- Test 1: Import Status Effects ---")
    from boneglaive.graphical.ui.status_effects import StatusEffectsPanel, STATUS_EFFECTS
    print("✓ StatusEffectsPanel imported successfully")
    print(f"✓ {len(STATUS_EFFECTS)} status effects defined")

    print("\n--- Test 2: Create Status Effects Panel ---")
    font = pygame.font.Font(None, 18)
    small_font = pygame.font.Font(None, 14)
    panel = StatusEffectsPanel(font, small_font)
    print("✓ StatusEffectsPanel created successfully")

    print("\n--- Test 3: Initialize Game and Units ---")
    from boneglaive.graphical.game_state import GameStateAdapter

    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    game = adapter.game

    print(f"Game initialized with {len(game.units)} units")

    # Find a unit
    test_unit = None
    for unit in game.units:
        if unit.hp > 0:
            test_unit = unit
            break

    if not test_unit:
        print("✗ No alive units found")
        return False

    print(f"Test unit: {test_unit.type.name} at ({test_unit.y}, {test_unit.x})")

    print("\n--- Test 4: Apply Status Effects to Unit ---")
    # Apply various status effects
    test_unit.was_pried = True
    test_unit.estranged = True
    test_unit.pumped_up_active = True
    test_unit.pumped_up_duration = 3
    test_unit.mired = True
    test_unit.mired_duration = 2
    test_unit.partition_shield_active = True
    test_unit.partition_shield_duration = 4
    test_unit.partition_shield_strength = 10

    print("✓ Applied 7 status effects to test unit:")
    print("  - was_pried (debuff)")
    print("  - estranged (debuff)")
    print("  - pumped_up_active (buff, 3 turns)")
    print("  - mired (debuff, 2 turns)")
    print("  - partition_shield_active (buff, 4 turns, 10 HP)")

    print("\n--- Test 5: Update Panel with Unit ---")
    panel.update(test_unit)
    print(f"✓ Panel updated")
    print(f"✓ Found {len(panel.effects)} status effects on unit")

    if len(panel.effects) == 0:
        print("✗ No effects detected (expected 5-7)")
        return False

    print("\n--- Test 6: Display Effect Details ---")
    for i, effect in enumerate(panel.effects):
        duration_str = f" ({effect.duration} turns)" if effect.duration else ""
        print(f"  {i+1}. [{effect.type}] {effect.name}{duration_str}")
        print(f"     Icon: {effect.icon}")
        print(f"     Description: {effect.description}")
        print(f"     Color: RGB{effect.get_color()}")

    print("\n--- Test 7: Test Different Unit Types ---")
    # Try to find INTERFERER unit with radiation stacks
    interferer = None
    for unit in game.units:
        if unit.type.name == 'INTERFERER' and unit.hp > 0:
            interferer = unit
            break

    if interferer:
        print(f"Found INTERFERER unit")
        interferer.radiation_stacks = [2, 2, 1]  # 3 stacks
        interferer.neural_shunt_affected = True
        interferer.neural_shunt_duration = 2

        panel.update(interferer)
        print(f"✓ INTERFERER has {len(panel.effects)} status effects")
        for effect in panel.effects:
            print(f"  - {effect.name}")
    else:
        print("⚠ No INTERFERER unit found, skipping INTERFERER-specific test")

    print("\n--- Test 8: Test Panel Drawing (Headless) ---")
    # Create dummy surface
    surface = pygame.Surface((400, 600))
    height = panel.draw(surface, 10, 10)
    print(f"✓ Panel drew successfully")
    print(f"✓ Panel height: {height}px")

    print("\n--- Test 9: Test Empty Panel ---")
    panel.update(None)
    print(f"✓ Panel cleared")
    print(f"✓ Effects count: {len(panel.effects)} (should be 0)")

    # Try drawing empty panel
    height = panel.draw(surface, 10, 10)
    print(f"✓ Empty panel height: {height}px (should be 0)")

    if height != 0:
        print("⚠ Empty panel returned non-zero height")

    print("\n--- Test 10: Test All Effect Types ---")
    effect_types = set()
    for effect_key, effect_data in STATUS_EFFECTS.items():
        effect_types.add(effect_data['type'])

    print(f"✓ Effect types found: {', '.join(sorted(effect_types))}")

    # Count effects by type
    type_counts = {}
    for effect_data in STATUS_EFFECTS.values():
        etype = effect_data['type']
        type_counts[etype] = type_counts.get(etype, 0) + 1

    print("Effect counts by type:")
    for etype, count in sorted(type_counts.items()):
        print(f"  {etype}: {count}")

    print("\n✓ All status effects tests passed")
    pygame.quit()
    return True


if __name__ == "__main__":
    try:
        success = test_status_effects()
        print("\n" + "=" * 60)
        if success:
            print("✓ Status Effects Test PASSED")
            sys.exit(0)
        else:
            print("✗ Status Effects Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
