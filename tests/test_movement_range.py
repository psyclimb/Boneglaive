#!/usr/bin/env python3
"""Test movement range functionality."""
import sys
sys.path.insert(0, '.')

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.renderer import GraphicalRenderer
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

print("=" * 60)
print("Testing Movement Range")
print("=" * 60)

# Create adapter and game
adapter = GameStateAdapter()
adapter.initialize_game(skip_setup=True)

print(f"\nGame created with {len(adapter.game.units)} units")
print(f"Current player: {adapter.game.current_player}")

# Test first unit
unit = adapter.game.units[0]
print(f"\nTesting unit: {unit.type.name}")
print(f"  Position: ({unit.x}, {unit.y})")
print(f"  Move range: {unit.move_range}")
print(f"  Player: {unit.player}")

# Get possible moves directly from game
possible_moves = adapter.game.get_possible_moves(unit)
print(f"\nDirect game.get_possible_moves():")
print(f"  Returned {len(possible_moves)} moves")
if possible_moves:
    print(f"  First 5: {possible_moves[:5]}")

# Now test through adapter
print(f"\nTesting adapter.get_movement_range():")
movement_range = adapter.get_movement_range(unit)
print(f"  Returned {len(movement_range)} positions")
if movement_range:
    print(f"  First 5: {movement_range[:5]}")

print("\n" + "=" * 60)
if len(movement_range) > 0:
    print("✓ Movement range is working!")
else:
    print("✗ Movement range is EMPTY - BUG FOUND")
print("=" * 60)
