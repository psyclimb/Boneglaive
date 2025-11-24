#!/usr/bin/env python3
"""
Headless test script to verify HP synchronization logic.
Tests without creating a pygame display window.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.game_state import GameStateAdapter, VisualUnit
from boneglaive.game.units import Unit


class MockAnimatedUnit:
    """Mock animated unit for testing."""
    def __init__(self, name, hp, max_hp, x=0, y=0):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.x = x * 64 + 32  # Mock screen position
        self.y = y * 64 + 32
        self.grid_x = x
        self.grid_y = y
        self.shake_called = False
        self.move_to_grid_called = False

    def shake(self, intensity=10):
        self.shake_called = True
        print(f"    Unit shake called with intensity={intensity}")

    def move_to_grid(self, grid_x, grid_y):
        self.move_to_grid_called = True
        self.grid_x = grid_x
        self.grid_y = grid_y
        print(f"    Unit moved to grid ({grid_x}, {grid_y})")


def test_hp_sync_logic():
    """Test HP synchronization logic without pygame display."""
    print("=" * 60)
    print("Testing HP Synchronization Logic (Headless)")
    print("=" * 60)

    # Initialize adapter
    print("\n1. Initializing game...")
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    print(f"   Game created with {len(adapter.game.units)} units")

    # Get first unit
    game_unit = adapter.game.units[0]
    print(f"\n2. Setting up test unit: {game_unit.type}")
    print(f"   Initial HP: {game_unit.hp}/{game_unit.max_hp}")
    print(f"   Position: ({game_unit.x}, {game_unit.y})")

    # Create mock visual unit
    mock_animated = MockAnimatedUnit(
        name=str(game_unit.type),
        hp=game_unit.hp,
        max_hp=game_unit.max_hp,
        x=game_unit.x,
        y=game_unit.y
    )

    # Register visual unit
    adapter.create_visual_unit(game_unit, mock_animated)
    print(f"\n3. Visual unit registered")
    print(f"   UUID: {game_unit.uuid}")
    print(f"   Visual units tracked: {len(adapter.visual_units)}")

    # Test damage
    print("\n" + "-" * 60)
    print("TEST 1: Damage Detection")
    print("-" * 60)

    original_hp = game_unit.hp
    damage_amount = 5
    game_unit.hp -= damage_amount

    print(f"   Applied damage: -{damage_amount}")
    print(f"   HP: {original_hp} -> {game_unit.hp}")

    events = adapter.sync_state()
    print(f"\n   Events generated: {len(events)}")

    damage_event_found = False
    for event in events:
        print(f"   - Event type: {event.event_type}")
        if event.event_type == "damage":
            damage_event_found = True
            dmg = event.kwargs.get("damage_amount", 0)
            print(f"     Damage amount: {dmg}")
            assert dmg == damage_amount, f"Expected {damage_amount}, got {dmg}"

    assert damage_event_found, "No damage event generated!"
    print("\n   ✓ Damage event generated correctly")

    # Test healing
    print("\n" + "-" * 60)
    print("TEST 2: Healing Detection")
    print("-" * 60)

    original_hp = game_unit.hp
    heal_amount = 3
    game_unit.hp += heal_amount

    print(f"   Applied healing: +{heal_amount}")
    print(f"   HP: {original_hp} -> {game_unit.hp}")

    events = adapter.sync_state()
    print(f"\n   Events generated: {len(events)}")

    heal_event_found = False
    for event in events:
        print(f"   - Event type: {event.event_type}")
        if event.event_type == "heal":
            heal_event_found = True
            heal = event.kwargs.get("heal_amount", 0)
            print(f"     Heal amount: {heal}")
            assert heal == heal_amount, f"Expected {heal_amount}, got {heal}"

    assert heal_event_found, "No heal event generated!"
    print("\n   ✓ Heal event generated correctly")

    # Test movement
    print("\n" + "-" * 60)
    print("TEST 3: Movement Detection")
    print("-" * 60)

    old_x, old_y = game_unit.x, game_unit.y
    new_x, new_y = old_x + 1, old_y + 1
    game_unit.x = new_x
    game_unit.y = new_y

    print(f"   Moved unit: ({old_x}, {old_y}) -> ({new_x}, {new_y})")

    events = adapter.sync_state()
    print(f"\n   Events generated: {len(events)}")

    movement_event_found = False
    for event in events:
        print(f"   - Event type: {event.event_type}")
        if event.event_type == "movement":
            movement_event_found = True
            old_pos = event.kwargs.get("old_position")
            new_pos = event.kwargs.get("new_position")
            print(f"     Old position: {old_pos}")
            print(f"     New position: {new_pos}")

    assert movement_event_found, "No movement event generated!"
    assert mock_animated.move_to_grid_called, "move_to_grid not called!"
    print("\n   ✓ Movement event generated correctly")
    print(f"   ✓ Visual unit moved to ({mock_animated.grid_x}, {mock_animated.grid_y})")

    # Test death
    print("\n" + "-" * 60)
    print("TEST 4: Death Detection")
    print("-" * 60)

    game_unit.hp = -10
    print(f"   Set HP to: {game_unit.hp}")

    events = adapter.sync_state()
    print(f"\n   Events generated: {len(events)}")

    death_event_found = False
    damage_event_found = False
    for event in events:
        print(f"   - Event type: {event.event_type}")
        if event.event_type == "death":
            death_event_found = True
        if event.event_type == "damage":
            damage_event_found = True

    assert damage_event_found, "No damage event for lethal damage!"
    assert death_event_found, "No death event generated!"
    print("\n   ✓ Death event generated correctly")

    # Test no changes
    print("\n" + "-" * 60)
    print("TEST 5: No Changes (No Events)")
    print("-" * 60)

    events = adapter.sync_state()
    print(f"   Events generated: {len(events)}")

    assert len(events) == 0, "Expected no events when nothing changed!"
    print("\n   ✓ No spurious events generated")

    # Summary
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nHP Synchronization Logic:")
    print("  ✓ Damage detection")
    print("  ✓ Healing detection")
    print("  ✓ Movement detection")
    print("  ✓ Death detection")
    print("  ✓ No spurious events")
    print("\nPhase 1 Task 5: COMPLETE")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_hp_sync_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
