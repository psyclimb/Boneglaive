#!/usr/bin/env python3
"""
Quick test to verify FPS counter is working.
This test will display the game for 3 seconds to check the FPS counter.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter

def test_fps_counter():
    """Test that FPS counter is visible and updating."""
    print("Testing FPS counter...")
    print("The game will run for 3 seconds to verify FPS counter is visible.")
    print("Look for 'FPS: XX.X' in the top-right corner with green text.")

    # Create adapter and initialize game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True, map_name='lime_foyer')

    # Create renderer
    renderer = GraphicalRenderer(adapter)
    renderer.sync_units_from_game()

    # Verify FPS counter is enabled
    assert renderer.show_fps == True, "FPS counter should be enabled by default"
    print("FPS counter is enabled: ✓")

    # Run for 3 seconds
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < 3.0 and renderer.running:
        delta_time = renderer.clock.tick(60) / 1000.0

        # Update FPS counter (same as in run())
        if renderer.show_fps:
            current_fps = renderer.clock.get_fps()
            renderer.fps_values.append(current_fps)
            if len(renderer.fps_values) > 30:
                renderer.fps_values.pop(0)
            if len(renderer.fps_values) > 0:
                renderer.fps_display = sum(renderer.fps_values) / len(renderer.fps_values)

        # Handle events (to allow closing window)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False

        # Draw frame
        renderer.draw()
        frame_count += 1

    pygame.quit()

    # Verify we got FPS data
    assert len(renderer.fps_values) > 0, "FPS values should be collected"
    assert renderer.fps_display > 0, "FPS display should be calculated"

    print(f"\nTest completed successfully!")
    print(f"Frames rendered: {frame_count}")
    print(f"Average FPS: {renderer.fps_display:.1f}")
    print(f"FPS counter is working correctly: ✓")

if __name__ == "__main__":
    test_fps_counter()
