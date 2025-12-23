#!/usr/bin/env python3
"""
Debug Pry workflow - trace exactly what happens.
"""
import sys
import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).parent))

import pygame
pygame.init()

from boneglaive.graphical.game_state import GameStateAdapter

print("=" * 70)
print("DEBUG: Tracing Pry Skill Workflow")
print("=" * 70)

# Initialize
adapter = GameStateAdapter()
adapter.initialize_game(skip_setup=True)
game = adapter.game

print(f"\n1. Game initialized with {len(game.units)} units")

# Find units
glaiveman = None
enemy = None

for unit in game.units:
    if unit.hp > 0:
        if unit.type.name == 'GLAIVEMAN' and unit.player == 1:
            glaiveman = unit
        elif unit.player == 2 and enemy is None:
            enemy = unit

if not glaiveman or not enemy:
    print("ERROR: Could not find required units")
    sys.exit(1)

print(f"2. Found GLAIVEMAN at ({glaiveman.y}, {glaiveman.x})")
print(f"   Found enemy {enemy.type.name} at ({enemy.y}, {enemy.x})")

# Move them adjacent
enemy.y = glaiveman.y
enemy.x = glaiveman.x + 1
print(f"3. Moved enemy adjacent to GLAIVEMAN: ({enemy.y}, {enemy.x})")

# Get Pry skill
pry_skill = glaiveman.active_skills[0]
print(f"\n4. Using skill: {pry_skill.name}")
print(f"   Range: {pry_skill.range}")
print(f"   Cooldown: {pry_skill.cooldown}")

# Check if can use
target_pos = (enemy.y, enemy.x)
can_use = pry_skill.can_use(glaiveman, target_pos, game)
print(f"\n5. Can use Pry on target? {can_use}")

if not can_use:
    print("   ERROR: Cannot use skill!")
    sys.exit(1)

# Check enemy status BEFORE
print(f"\n6. Enemy status BEFORE using Pry:")
print(f"   was_pried: {enemy.was_pried}")
print(f"   HP: {enemy.hp}/{enemy.max_hp}")

# Use skill (queues it)
print(f"\n7. Calling pry_skill.use()...")
success = pry_skill.use(glaiveman, target_pos, game)
print(f"   Returned: {success}")
print(f"   glaiveman.skill_target: {glaiveman.skill_target}")
print(f"   glaiveman.selected_skill: {glaiveman.selected_skill}")

print(f"\n8. Enemy status AFTER .use() but BEFORE execute_turn:")
print(f"   was_pried: {enemy.was_pried}")
print(f"   HP: {enemy.hp}/{enemy.max_hp}")

# Execute turn (this is when skills actually execute)
print(f"\n9. Executing turn...")
game.execute_turn(ui=None)

print(f"\n10. Enemy status AFTER execute_turn:")
print(f"    was_pried: {enemy.was_pried}")
print(f"    HP: {enemy.hp}/{enemy.max_hp}")

# Try status effects panel
from boneglaive.graphical.ui.status_effects import StatusEffectsPanel

font = pygame.font.Font(None, 18)
small_font = pygame.font.Font(None, 14)
panel = StatusEffectsPanel(font, small_font)

print(f"\n11. Updating status effects panel...")
panel.update(enemy)
print(f"    Panel has {len(panel.effects)} effects")

if len(panel.effects) > 0:
    print("    ✓ EFFECTS DETECTED:")
    for effect in panel.effects:
        duration_str = f" ({effect.duration} turns)" if effect.duration else ""
        print(f"      [{effect.icon}] {effect.name}{duration_str}")

    surface = pygame.Surface((400, 600))
    height = panel.draw(surface, 10, 100)
    print(f"    ✓ Panel height: {height}px (would be visible!)")
else:
    print("    ✗ NO EFFECTS DETECTED!")
    print(f"\n    Debug info:")
    print(f"      enemy.was_pried = {enemy.was_pried}")
    print(f"      hasattr 'was_pried'? {hasattr(enemy, 'was_pried')}")

print("\n" + "=" * 70)
pygame.quit()
