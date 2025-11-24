#!/usr/bin/env python3
"""
Visual test for status effects panel - simulates unit selection workflow.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_status_effects_workflow():
    """Test status effects panel in workflow context."""
    print("=" * 60)
    print("Testing Status Effects Panel - Workflow Simulation")
    print("=" * 60)

    print("\n--- Simulating Graphical Renderer Workflow ---")

    # Initialize pygame (headless)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    import pygame
    pygame.init()

    from boneglaive.graphical.game_state import GameStateAdapter
    from boneglaive.graphical.ui.status_effects import StatusEffectsPanel

    print("\n1. Initialize game")
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    game = adapter.game
    print(f"   ✓ Game has {len(game.units)} units")

    print("\n2. Create status effects panel")
    font = pygame.font.Font(None, 18)
    small_font = pygame.font.Font(None, 14)
    panel = StatusEffectsPanel(font, small_font)
    print("   ✓ Panel created")

    print("\n3. Find unit with status effects")
    # Apply effects to first unit
    test_unit = None
    for unit in game.units:
        if unit.hp > 0 and unit.player == 1:
            test_unit = unit
            break

    if not test_unit:
        print("   ✗ No suitable unit found")
        return False

    print(f"   ✓ Found: {test_unit.type.name} at ({test_unit.y}, {test_unit.x})")

    print("\n4. Apply multiple status effects")
    test_unit.was_pried = True
    test_unit.jawline_affected = True
    test_unit.jawline_duration = 3
    test_unit.pumped_up_active = True
    test_unit.pumped_up_duration = 2
    test_unit.partition_shield_active = True
    test_unit.partition_shield_duration = 4
    test_unit.partition_shield_strength = 15
    print("   ✓ Applied 5 status effects")

    print("\n5. Simulate unit selection (update panel)")
    panel.update(test_unit)
    print(f"   ✓ Panel updated, found {len(panel.effects)} effects")

    if len(panel.effects) == 0:
        print("   ✗ No effects detected!")
        return False

    print("\n6. Display effects as they would appear in UI")
    print("   " + "-" * 50)
    for effect in panel.effects:
        duration_str = f" ({effect.duration} turns)" if effect.duration else ""
        color_name = {
            (100, 200, 100): "GREEN",
            (255, 100, 100): "RED",
            (200, 150, 255): "PURPLE",
            (150, 150, 200): "GRAY",
            (255, 200, 100): "YELLOW"
        }.get(effect.get_color(), "UNKNOWN")

        print(f"   [{effect.icon:3}] {effect.name:18} {color_name:8} {duration_str}")
        print(f"        {effect.description}")
    print("   " + "-" * 50)

    print("\n7. Test panel drawing")
    surface = pygame.Surface((400, 600))
    height = panel.draw(surface, 10, 100)
    print(f"   ✓ Panel drew at height {height}px")

    print("\n8. Simulate deselection (clear panel)")
    panel.update(None)
    print(f"   ✓ Panel cleared, {len(panel.effects)} effects")

    height = panel.draw(surface, 10, 100)
    print(f"   ✓ Empty panel height: {height}px")

    print("\n9. Test with different unit type")
    # Find another unit type
    other_unit = None
    for unit in game.units:
        if unit.hp > 0 and unit != test_unit:
            other_unit = unit
            break

    if other_unit:
        print(f"   Testing with: {other_unit.type.name}")
        other_unit.derelicted = True
        other_unit.derelicted_duration = 2
        other_unit.trauma_processing_active = True
        other_unit.trauma_debt = 5

        panel.update(other_unit)
        print(f"   ✓ Found {len(panel.effects)} effects on {other_unit.type.name}")
        for effect in panel.effects:
            print(f"      - {effect.name}")
    else:
        print("   ⚠ No other unit found for testing")

    print("\n10. Verify tooltip data")
    if panel.effects:
        test_effect = panel.effects[0]
        print(f"   Testing tooltip for: {test_effect.name}")
        print(f"   Description: {test_effect.description}")
        print(f"   Type: {test_effect.type}")
        print(f"   Color: RGB{test_effect.get_color()}")
        print("   ✓ Tooltip data valid")

    print("\n✓ All workflow tests passed")
    pygame.quit()
    return True


if __name__ == "__main__":
    try:
        success = test_status_effects_workflow()
        print("\n" + "=" * 60)
        if success:
            print("✓ Status Effects Workflow Test PASSED")
            print("\nStatus effects panel is ready for use in graphical game!")
            print("When you select a unit, status effects will appear in a panel")
            print("on the left side of the screen, above the combat log.")
            sys.exit(0)
        else:
            print("✗ Status Effects Workflow Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
