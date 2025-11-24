#!/usr/bin/env python3
"""
Test live graphical game with persistent status effects.
This simulates what happens in the actual game.
"""
import sys
import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).parent))

import pygame
pygame.init()

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.renderer import GraphicalRenderer

print("=" * 70)
print("TEST: Live Status Effects Display in Graphical Game")
print("=" * 70)

# Initialize game and renderer
adapter = GameStateAdapter()
adapter.initialize_game(skip_setup=True)
renderer = GraphicalRenderer(adapter)
renderer.sync_units_from_game()

game = adapter.game

print(f"\n1. Game initialized with {len(game.units)} units")
print(f"   Renderer has {len(renderer.units)} visual units")

# Find DERELICTIONIST to use Partition skill (creates shield buff)
derelictionist = None
for unit in game.units:
    if unit.type.name == 'DERELICTIONIST' and unit.hp > 0:
        derelictionist = unit
        break

if not derelictionist:
    print("\n✗ No DERELICTIONIST found")
    sys.exit(1)

print(f"\n2. Found {derelictionist.type.name} at ({derelictionist.y}, {derelictionist.x})")
print(f"   Skills: {[s.name for s in derelictionist.active_skills]}")

# Find an ally to buff
ally = None
for unit in game.units:
    if unit.hp > 0 and unit.player == derelictionist.player and unit != derelictionist:
        ally = unit
        break

if not ally:
    print("\n✗ No ally found")
    sys.exit(1)

print(f"\n3. Found ally {ally.type.name} at ({ally.y}, {ally.x})")

# Move ally adjacent if needed
ally.y = derelictionist.y
ally.x = derelictionist.x + 1
print(f"   Moved ally to ({ally.y}, {ally.x}) - adjacent")

# Get Partition skill (3rd skill)
partition_skill = None
for skill in derelictionist.active_skills:
    if skill.name == "Partition":
        partition_skill = skill
        break

if not partition_skill:
    print("\n✗ Partition skill not found")
    sys.exit(1)

print(f"\n4. Using {partition_skill.name} skill on ally")

# Use skill
target_pos = (ally.y, ally.x)
can_use = partition_skill.can_use(derelictionist, target_pos, game)
print(f"   Can use Partition? {can_use}")

if not can_use:
    print("\n✗ Cannot use Partition skill")
    sys.exit(1)

success = partition_skill.use(derelictionist, target_pos, game)
print(f"   Skill queued: {success}")

print(f"\n5. Ally status BEFORE execute_turn:")
print(f"   partition_shield_active: {ally.partition_shield_active}")
print(f"   partition_shield_duration: {ally.partition_shield_duration}")
print(f"   partition_shield_strength: {ally.partition_shield_strength}")

# Execute turn
print(f"\n6. Executing turn...")
game.execute_turn(ui=None)

print(f"\n7. Ally status AFTER execute_turn:")
print(f"   partition_shield_active: {ally.partition_shield_active}")
print(f"   partition_shield_duration: {ally.partition_shield_duration}")
print(f"   partition_shield_strength: {ally.partition_shield_strength}")

# Now check unit info panel
print(f"\n8. Update renderer's unit info panel with ally:")

# Find ally's animated unit
ally_animated = None
ally_id = adapter._get_unit_id(ally)
for aunit in renderer.units:
    if hasattr(aunit, 'unit_id') and aunit.unit_id == ally_id:
        ally_animated = aunit
        break

if ally_animated:
    print(f"   Found animated unit: {ally_animated.name}")
    renderer.unit_info_panel.update(ally_animated, ally)
    print(f"   ✓ Updated unit info panel")
else:
    # Just update with game unit directly
    print(f"   Using game unit directly")
    from demo_animations.core import AnimatedUnit, COLOR_PLAYER1
    ally_animated = AnimatedUnit(
        ally.type.name,
        player=ally.player - 1,
        grid_x=ally.x,
        grid_y=ally.y,
        color=COLOR_PLAYER1
    )
    ally_animated.hp = ally.hp
    ally_animated.max_hp = ally.max_hp
    renderer.unit_info_panel.update(ally_animated, ally)
    print(f"   ✓ Updated unit info panel")

# Check what status effects the panel sees
print(f"\n9. Check status effects detection:")
from boneglaive.graphical.ui.status_effects import STATUS_EFFECTS

active_count = 0
for effect_key, effect_data in STATUS_EFFECTS.items():
    try:
        if effect_data["check"](ally):
            print(f"   ✓ {effect_data['name']}")
            active_count += 1
    except AttributeError:
        pass

print(f"\n   Total effects detected: {active_count}")

if active_count == 0:
    print("\n✗ NO STATUS EFFECTS DETECTED!")
    print("   This means the Partition buff was NOT applied or was cleared.")
else:
    print("\n✓ Status effects ARE being detected!")
    print("   They should appear in the unit info panel when you select this unit.")

print("\n" + "=" * 70)
pygame.quit()
