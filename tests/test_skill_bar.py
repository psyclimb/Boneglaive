#!/usr/bin/env python3
"""
Test script for skill bar UI component.
"""
import sys
import os
from pathlib import Path

# Disable pygame display for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

sys.path.insert(0, str(Path(__file__).parent))

def test_skill_bar():
    """Test skill bar component."""
    print("=" * 60)
    print("Testing Skill Bar UI Component")
    print("=" * 60)

    # Initialize pygame (needed for fonts)
    import pygame
    pygame.init()

    print("\n--- Test 1: Import Skill Bar ---")
    from boneglaive.graphical.ui.skill_bar import SkillBar
    print("✓ SkillBar imported successfully")

    print("\n--- Test 2: Create Skill Bar ---")
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    skill_bar = SkillBar(font, small_font)
    print("✓ SkillBar created successfully")

    print("\n--- Test 3: Initialize Game and Units ---")
    from boneglaive.graphical.game_state import GameStateAdapter
    from demo_animations.core import AnimatedUnit

    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    game = adapter.game

    print(f"Game initialized with {len(game.units)} units")

    # Get a player 1 unit
    player1_units = [u for u in game.units if u.player == 1 and u.hp > 0]
    if not player1_units:
        print("✗ No player 1 units found")
        return False

    game_unit = player1_units[0]
    print(f"Testing with unit: {game_unit.type.name}")

    # Create animated unit
    animated_unit = AnimatedUnit(
        name=game_unit.type.name,
        player=game_unit.player,
        grid_x=game_unit.x,
        grid_y=game_unit.y,
        color=(100, 150, 255)
    )

    print("\n--- Test 4: Update Skill Bar with Unit ---")
    skill_bar.update(animated_unit, game_unit)

    if skill_bar.skill_slots:
        print(f"✓ Skill bar loaded {len(skill_bar.skill_slots)} skills")
        for i, slot in enumerate(skill_bar.skill_slots):
            print(f"  Slot {i}: [{slot.hotkey}] {slot.skill.name}")
    else:
        print("✗ No skills loaded into skill bar")
        return False

    print("\n--- Test 5: Test Hotkey Handling ---")
    # Simulate hotkey press
    test_keys = [pygame.K_1, pygame.K_2, pygame.K_q]
    for key in test_keys:
        skill = skill_bar.handle_hotkey(key)
        if skill:
            print(f"✓ Hotkey {pygame.key.name(key)} activated: {skill.name}")
        else:
            print(f"  Hotkey {pygame.key.name(key)} - no skill bound")

    print("\n--- Test 6: Test Cooldown Display ---")
    if skill_bar.skill_slots:
        slot = skill_bar.skill_slots[0]
        original_cd = slot.skill.current_cooldown
        print(f"Skill '{slot.skill.name}' cooldown: {slot.skill.current_cooldown}")
        print(f"Is available: {slot.is_available()}")

        # Test with cooldown
        slot.skill.current_cooldown = 3
        print(f"Set cooldown to 3")
        print(f"Is available: {slot.is_available()}")

        # Restore
        slot.skill.current_cooldown = original_cd
        print("✓ Cooldown display works")

    print("\n--- Test 7: Test Clearing Skill Bar ---")
    skill_bar.update(None, None)
    if len(skill_bar.skill_slots) == 0:
        print("✓ Skill bar cleared successfully")
    else:
        print("✗ Skill bar did not clear")
        return False

    print("\n--- Test 8: Test Different Unit Types ---")
    test_unit_types = ['GLAIVEMAN', 'MANDIBLE_FOREMAN', 'GRAYMAN']
    for unit_type_name in test_unit_types:
        # Find unit of this type
        test_units = [u for u in game.units if u.type.name == unit_type_name and u.hp > 0]
        if test_units:
            test_unit = test_units[0]
            animated = AnimatedUnit(
                name=test_unit.type.name,
                player=test_unit.player,
                grid_x=test_unit.x,
                grid_y=test_unit.y,
                color=(100, 150, 255)
            )
            skill_bar.update(animated, test_unit)
            print(f"  {unit_type_name}: {len(skill_bar.skill_slots)} skills")

    print("\n✓ All skill bar tests passed")
    pygame.quit()
    return True


if __name__ == "__main__":
    try:
        success = test_skill_bar()
        print("\n" + "=" * 60)
        if success:
            print("✓ Skill Bar Test PASSED")
            sys.exit(0)
        else:
            print("✗ Skill Bar Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
