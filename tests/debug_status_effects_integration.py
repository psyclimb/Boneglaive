#!/usr/bin/env python3
"""
Debug status effects display in unit info panel.
"""
import sys
import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).parent))

import pygame
pygame.init()

print("=" * 70)
print("DEBUG: Status Effects in Unit Info Panel")
print("=" * 70)

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.ui.unit_info import UnitInfoPanel
from boneglaive.graphical.ui.status_effects import STATUS_EFFECTS
from demo_animations.core import AnimatedUnit, COLOR_PLAYER1

# Initialize
adapter = GameStateAdapter()
adapter.initialize_game(skip_setup=True)
game = adapter.game

# Find test unit
test_unit = None
for unit in game.units:
    if unit.hp > 0 and unit.player == 1:
        test_unit = unit
        break

print(f"\n1. Testing with {test_unit.type.name} at ({test_unit.y}, {test_unit.x})")

print("\n2. Manually apply status effects:")
test_unit.was_pried = True
test_unit.pumped_up_active = True
test_unit.pumped_up_duration = 3
test_unit.estranged = True
print("   Set was_pried = True")
print("   Set pumped_up_active = True")
print("   Set pumped_up_duration = 3")
print("   Set estranged = True")

print("\n3. Verify status effects on unit:")
print(f"   test_unit.was_pried: {test_unit.was_pried}")
print(f"   test_unit.pumped_up_active: {test_unit.pumped_up_active}")
print(f"   test_unit.pumped_up_duration: {test_unit.pumped_up_duration}")
print(f"   test_unit.estranged: {test_unit.estranged}")

print("\n4. Check STATUS_EFFECTS definitions:")
for key in ['was_pried', 'pumped_up_active', 'estranged']:
    if key in STATUS_EFFECTS:
        effect = STATUS_EFFECTS[key]
        print(f"   {key}:")
        print(f"     Name: {effect['name']}")
        print(f"     Check function exists: {effect['check'] is not None}")
        try:
            result = effect['check'](test_unit)
            print(f"     Check result: {result}")
        except Exception as e:
            print(f"     Check ERROR: {e}")

print("\n5. Manually collect active effects (simulating _draw_status_effects):")
active_effects = []
for effect_key, effect_data in STATUS_EFFECTS.items():
    try:
        if effect_data["check"](test_unit):
            active_effects.append(effect_data["name"])
            print(f"   ✓ Found: {effect_data['name']} (key: {effect_key})")
    except AttributeError as e:
        pass  # Unit doesn't have this property

print(f"\n6. Total active effects found: {len(active_effects)}")
if active_effects:
    print("   Effects list:")
    for name in active_effects:
        print(f"     • {name}")
else:
    print("   ✗ NO EFFECTS FOUND!")

print("\n7. Test UnitInfoPanel._draw_status_effects:")
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)
large_font = pygame.font.Font(None, 36)
panel = UnitInfoPanel(font, small_font, large_font)

animated_unit = AnimatedUnit(
    test_unit.type.name,
    player=0,
    grid_x=test_unit.x,
    grid_y=test_unit.y,
    color=COLOR_PLAYER1
)
animated_unit.hp = test_unit.hp
animated_unit.max_hp = test_unit.max_hp

panel.update(animated_unit, test_unit)

# Check what panel thinks game_unit is
print(f"   panel.game_unit is not None: {panel.game_unit is not None}")
print(f"   panel.game_unit is test_unit: {panel.game_unit is test_unit}")

# Try drawing
surface = pygame.Surface((1480, 800))
try:
    panel.draw(surface, 1160, 10)
    print("   ✓ Panel.draw() completed without error")
except Exception as e:
    print(f"   ✗ Panel.draw() ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n8. Directly call _draw_status_effects:")
try:
    # Simulate calling the method
    y_after = panel._draw_status_effects(surface, 1175, 200)
    print(f"   ✓ _draw_status_effects() returned y={y_after}")
except Exception as e:
    print(f"   ✗ _draw_status_effects() ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
pygame.quit()
