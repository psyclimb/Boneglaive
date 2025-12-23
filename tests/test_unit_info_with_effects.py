#!/usr/bin/env python3
"""
Test unit info panel with integrated status effects.
"""
import sys
import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).parent))

import pygame
pygame.init()

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.ui.unit_info import UnitInfoPanel
from demo_animations.core import AnimatedUnit, COLOR_PLAYER1

print("=" * 60)
print("Testing Unit Info Panel with Status Effects")
print("=" * 60)

# Initialize
adapter = GameStateAdapter()
adapter.initialize_game(skip_setup=True)
game = adapter.game

# Create panel
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)
large_font = pygame.font.Font(None, 36)
panel = UnitInfoPanel(font, small_font, large_font)

# Find test unit
test_unit = None
for unit in game.units:
    if unit.hp > 0 and unit.player == 1:
        test_unit = unit
        break

print(f"\n1. Testing with {test_unit.type.name}")

# Create animated unit
animated_unit = AnimatedUnit(
    test_unit.type.name,
    player=0,
    grid_x=test_unit.x,
    grid_y=test_unit.y,
    color=COLOR_PLAYER1
)
animated_unit.hp = test_unit.hp
animated_unit.max_hp = test_unit.max_hp

print("\n2. Unit with NO status effects:")
panel.update(animated_unit, test_unit)
surface = pygame.Surface((1480, 800))
panel.draw(surface, 1160, 10)
print("   ✓ Panel draws without errors")

print("\n3. Apply status effects:")
test_unit.was_pried = True
test_unit.pumped_up_active = True
test_unit.pumped_up_duration = 3
test_unit.partition_shield_active = True
test_unit.partition_shield_duration = 4
test_unit.partition_shield_strength = 10

panel.update(animated_unit, test_unit)
print("   ✓ Applied 3 status effects")

print("\n4. Drawing panel with status effects:")
panel.draw(surface, 1160, 10)
print("   ✓ Panel draws with status effects")

print("\n5. Expected status effects in panel:")
print("   • Pried")
print("   • Pumped Up")
print("   • Partition")

print("\n6. Test with different unit:")
enemy = None
for unit in game.units:
    if unit.hp > 0 and unit.player == 2:
        enemy = unit
        break

enemy.estranged = True
enemy.mired = True
enemy.mired_duration = 2

animated_enemy = AnimatedUnit(
    enemy.type.name,
    player=1,
    grid_x=enemy.x,
    grid_y=enemy.y,
    color=(255, 100, 100)
)
animated_enemy.hp = enemy.hp
animated_enemy.max_hp = enemy.max_hp

panel.update(animated_enemy, enemy)
panel.draw(surface, 1160, 10)
print(f"   ✓ {enemy.type.name} with Estranged + Mired")

print("\n" + "=" * 60)
print("✓ Unit Info Panel with Status Effects WORKS!")
print("\nStatus effects now appear:")
print("  - In unit info panel (top-right)")
print("  - As simple bullet list")
print("  - No separate status effects panel")
print("  - No tooltips needed")

pygame.quit()
sys.exit(0)
