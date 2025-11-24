#!/usr/bin/env python3
"""
Test script to verify HP synchronization works.
Manually damages a unit and checks if floating text appears.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.renderer import GraphicalRenderer
import pygame
import time


def test_hp_sync():
    """Test HP synchronization between game and visual units."""
    print("Initializing game and renderer...")
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)

    print(f"Game has {len(adapter.game.units)} units")

    # Create renderer
    renderer = GraphicalRenderer(adapter)
    renderer.sync_units_from_game()

    print(f"Renderer has {len(renderer.units)} visual units")
    print(f"Adapter has {len(adapter.visual_units)} visual unit mappings\n")

    # Get first unit from game
    test_unit = adapter.game.units[0]
    print(f"Test unit: {test_unit.type}")
    print(f"Initial HP: {test_unit.hp}/{test_unit.max_hp}")

    # Run a few frames to initialize
    for _ in range(5):
        delta_time = 0.016
        renderer.handle_events()
        renderer.update(delta_time)
        renderer.draw()

    print("\n--- Damaging unit by 5 HP ---")
    test_unit.hp -= 5
    print(f"New HP: {test_unit.hp}/{test_unit.max_hp}")

    # Run update to sync state
    print("\nRunning sync_state()...")
    events = adapter.sync_state()
    print(f"Generated {len(events)} events:")
    for event in events:
        print(f"  - {event.event_type}: {event.kwargs}")

    # Process events in renderer
    print("\nProcessing events in renderer...")
    for event in events:
        renderer.handle_animation_event(event)

    print(f"Renderer now has {len(renderer.floating_texts)} floating texts")

    if renderer.floating_texts:
        text = renderer.floating_texts[0]
        print(f"Floating text: '{text.text}' at ({text.x}, {text.y})")
        print("\n✓ SUCCESS: HP sync working! Floating text created.")
    else:
        print("\n✗ FAILURE: No floating text created")
        return False

    # Test healing
    print("\n--- Healing unit by 3 HP ---")
    test_unit.hp += 3
    print(f"New HP: {test_unit.hp}/{test_unit.max_hp}")

    events = adapter.sync_state()
    print(f"Generated {len(events)} events:")
    for event in events:
        print(f"  - {event.event_type}: {event.kwargs}")
        renderer.handle_animation_event(event)

    print(f"Renderer now has {len(renderer.floating_texts)} floating texts")

    if len(renderer.floating_texts) >= 2:
        text = renderer.floating_texts[-1]
        print(f"Heal text: '{text.text}' at ({text.x}, {text.y})")
        print("\n✓ SUCCESS: Heal sync working!")
    else:
        print("\n✗ FAILURE: Heal text not created")
        return False

    # Run a few frames with animation
    print("\n--- Running 2 seconds of animation ---")
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < 2.0:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break

        # Update
        delta_time = 0.016
        renderer.update(delta_time)
        renderer.draw()

        frame_count += 1
        renderer.clock.tick(60)

    print(f"Rendered {frame_count} frames")
    print(f"Floating texts remaining: {len(renderer.floating_texts)}")

    pygame.quit()
    print("\n✓ All tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_hp_sync()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
