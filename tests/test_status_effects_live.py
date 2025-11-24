#!/usr/bin/env python3
"""
Debug test for status effects panel - checks if effects are detected.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_live_status_effects():
    """Test status effects detection in live game scenario."""
    print("=" * 60)
    print("Debug: Status Effects Detection")
    print("=" * 60)

    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    import pygame
    pygame.init()

    from boneglaive.graphical.game_state import GameStateAdapter
    from boneglaive.graphical.ui.status_effects import StatusEffectsPanel, STATUS_EFFECTS

    print("\n--- Step 1: Initialize Game ---")
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    game = adapter.game

    print(f"Game has {len(game.units)} units")

    print("\n--- Step 2: Find GLAIVEMAN ---")
    glaiveman = None
    for unit in game.units:
        if unit.type.name == 'GLAIVEMAN' and unit.hp > 0 and unit.player == 1:
            glaiveman = unit
            break

    if not glaiveman:
        print("✗ No GLAIVEMAN found")
        return False

    print(f"✓ Found GLAIVEMAN at ({glaiveman.y}, {glaiveman.x})")
    print(f"  Skills: {[s.name for s in glaiveman.active_skills]}")

    print("\n--- Step 3: Find Enemy Target ---")
    enemy = None
    for unit in game.units:
        if unit.hp > 0 and unit.player != glaiveman.player:
            enemy = unit
            break

    if not enemy:
        print("✗ No enemy found")
        return False

    print(f"✓ Found enemy: {enemy.type.name} at ({enemy.y}, {enemy.x})")

    print("\n--- Step 4: Use Pry Skill ---")
    pry_skill = glaiveman.active_skills[0]
    print(f"Using skill: {pry_skill.name}")

    # Check current status
    print(f"Enemy 'was_pried' BEFORE: {enemy.was_pried}")

    # Use skill
    target_pos = (enemy.y, enemy.x)
    success = pry_skill.use(glaiveman, target_pos, game)
    print(f"Skill use returned: {success}")

    print("\n--- Step 5: Execute Turn ---")
    game.execute_turn(ui=None)

    print(f"Enemy 'was_pried' AFTER: {enemy.was_pried}")

    print("\n--- Step 6: Check Status Effects Panel ---")
    font = pygame.font.Font(None, 18)
    small_font = pygame.font.Font(None, 14)
    panel = StatusEffectsPanel(font, small_font)

    # Update panel with enemy
    panel.update(enemy)

    print(f"Panel has {len(panel.effects)} effects")
    if len(panel.effects) > 0:
        print("Effects detected:")
        for effect in panel.effects:
            print(f"  - {effect.name} ({effect.type})")
    else:
        print("⚠ NO EFFECTS DETECTED!")
        print("\nDebugging - checking enemy properties:")
        print(f"  was_pried: {getattr(enemy, 'was_pried', 'NOT FOUND')}")
        print(f"  estranged: {getattr(enemy, 'estranged', 'NOT FOUND')}")
        print(f"  mired: {getattr(enemy, 'mired', 'NOT FOUND')}")

        print("\nChecking STATUS_EFFECTS definitions:")
        if 'was_pried' in STATUS_EFFECTS:
            effect_def = STATUS_EFFECTS['was_pried']
            print(f"  was_pried definition exists")
            try:
                check_result = effect_def['check'](enemy)
                print(f"  Check function result: {check_result}")
            except Exception as e:
                print(f"  Check function error: {e}")

    print("\n--- Step 7: Test Drawing ---")
    surface = pygame.Surface((400, 600))
    height = panel.draw(surface, 10, 100)
    print(f"Panel draw height: {height}px")

    if height > 0:
        print("✓ Panel would be visible!")
    else:
        print("✗ Panel height is 0 (invisible)")

    pygame.quit()
    return len(panel.effects) > 0


if __name__ == "__main__":
    try:
        success = test_live_status_effects()
        print("\n" + "=" * 60)
        if success:
            print("✓ Status Effects ARE Working")
        else:
            print("✗ Status Effects NOT Detected")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
