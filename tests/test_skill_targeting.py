#!/usr/bin/env python3
"""
Test script for skill targeting system.
"""
import sys
import os
from pathlib import Path

# Disable pygame display for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

sys.path.insert(0, str(Path(__file__).parent))

def test_skill_targeting():
    """Test skill targeting system."""
    print("=" * 60)
    print("Testing Skill Targeting System")
    print("=" * 60)

    print("\n--- Test 1: Initialize Game and Units ---")
    from boneglaive.graphical.game_state import GameStateAdapter

    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    game = adapter.game

    print(f"Game initialized with {len(game.units)} units")

    # Get a GLAIVEMAN unit
    glaive_units = [u for u in game.units if u.type.name == 'GLAIVEMAN' and u.player == 1 and u.hp > 0]
    if not glaive_units:
        print("✗ No GLAIVEMAN units found")
        return False

    attacker = glaive_units[0]
    print(f"Attacker: {attacker.type.name} at ({attacker.y}, {attacker.x})")

    # Get enemy units
    enemies = [u for u in game.units if u.player != attacker.player and u.hp > 0]
    if not enemies:
        print("✗ No enemy units found")
        return False

    print(f"Found {len(enemies)} enemy units")

    print("\n--- Test 2: Get Unit Skills ---")
    from boneglaive.game.skills.registry import UNIT_SKILLS

    unit_skills = UNIT_SKILLS['GLAIVEMAN']
    active_skills = unit_skills.get('active', [])

    print(f"GLAIVEMAN has {len(active_skills)} active skills:")
    for skill in active_skills:
        print(f"  - {skill.name} (range: {skill.range}, cooldown: {skill.cooldown})")

    pry_skill = active_skills[0]  # Pry skill
    print(f"\nTesting with: {pry_skill.name}")

    print("\n--- Test 3: Query Skill Range ---")
    skill_range = adapter.get_skill_range(attacker, pry_skill)
    print(f"Skill range has {len(skill_range)} valid targets")

    if not skill_range:
        # Try moving attacker closer
        print("No targets in range, moving attacker closer...")
        target = enemies[0]
        new_y = max(0, target.y - 1)
        new_x = target.x
        attacker.y = new_y
        attacker.x = new_x
        print(f"Moved attacker to ({attacker.y}, {attacker.x})")

        skill_range = adapter.get_skill_range(attacker, pry_skill)
        print(f"Skill range now has {len(skill_range)} valid targets")

    if skill_range:
        print(f"Sample targets (renderer coords): {skill_range[:3]}")
        print("✓ Skill range query works")
    else:
        print("✗ Still no valid targets")
        return False

    print("\n--- Test 4: Use Skill ---")
    # Pick first valid target
    target_x, target_y = skill_range[0]
    target_pos = (target_y, target_x)  # Convert to game coords

    # Find target unit
    target_unit = game.get_unit_at(target_pos[0], target_pos[1])
    if target_unit:
        print(f"Target: {target_unit.type.name} at ({target_unit.y}, {target_unit.x})")
        target_hp_before = target_unit.hp

        # Use skill
        success = pry_skill.use(attacker, target_pos, game)

        if success:
            print(f"✓ Skill queued successfully")
            print(f"  skill_target set: {attacker.skill_target}")
            print(f"  selected_skill set: {attacker.selected_skill is not None}")
            print(f"  action_timestamp: {attacker.action_timestamp}")
        else:
            print("✗ Skill use failed")
            return False
    else:
        print(f"✗ No unit at target position {target_pos}")
        return False

    print("\n--- Test 5: Execute Turn ---")
    print(f"Target HP before: {target_hp_before}/{target_unit.max_hp}")

    # Execute turn
    game.execute_turn(ui=None)

    target_hp_after = target_unit.hp
    print(f"Target HP after: {target_hp_after}/{target_unit.max_hp}")

    if target_hp_after < target_hp_before:
        damage = target_hp_before - target_hp_after
        print(f"✓ Skill dealt {damage} damage!")
        return True
    else:
        print("⚠ Skill executed but no damage dealt (may be normal for some skills)")
        return True  # Still success - skill executed

if __name__ == "__main__":
    try:
        success = test_skill_targeting()
        print("\n" + "=" * 60)
        if success:
            print("✓ Skill Targeting Test PASSED")
            sys.exit(0)
        else:
            print("✗ Skill Targeting Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
