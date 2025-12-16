#!/usr/bin/env python3
"""
Performance profiling script for Boneglaive graphical renderer.
Identifies rendering bottlenecks.
"""
import cProfile
import pstats
import io
import sys
from pathlib import Path

# Ensure we can import boneglaive modules
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.renderer import GraphicalRenderer


def profile_renderer():
    """Profile the renderer for a few seconds."""
    # Create game state adapter
    adapter = GameStateAdapter()

    # Initialize game
    print("Initializing game...")
    adapter.initialize_game(skip_setup=True, map_name='edgecase')
    print(f"Game created with {len(adapter.game.units)} units")

    # Create renderer
    print("Initializing renderer...")
    renderer = GraphicalRenderer(adapter)

    # Create UI adapter
    from boneglaive.graphical.ui_adapter import GraphicalUIAdapter
    ui_adapter = GraphicalUIAdapter(renderer)
    adapter.game.set_ui_reference(ui_adapter)

    # Sync units
    renderer.sync_units_from_game()
    print(f"Created {len(renderer.units)} visual units")

    # Profile just the update and draw calls
    print("\nProfiling renderer for ~300 frames (5 seconds at 60 FPS)...")

    profiler = cProfile.Profile()
    profiler.enable()

    frame_count = 0
    target_frames = 300

    while frame_count < target_frames and renderer.running:
        delta_time = 1/60.0  # Simulate 60 FPS

        # Handle minimal events to keep pygame happy
        import pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False
                break

        # Update and draw (the core loop)
        renderer.update(delta_time)
        renderer.draw()

        frame_count += 1

        # Stop early if quit
        if not renderer.running:
            break

    profiler.disable()

    print(f"\nProfiled {frame_count} frames")
    print("\n" + "="*80)
    print("PERFORMANCE PROFILE - Top Time Consumers")
    print("="*80)

    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    print(s.getvalue())

    # Also print by total time
    print("\n" + "="*80)
    print("PERFORMANCE PROFILE - By Total Time")
    print("="*80)
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('tottime')
    ps.print_stats(30)
    print(s.getvalue())

    # Cleanup
    pygame.quit()

    print("\nProfile complete!")


if __name__ == "__main__":
    profile_renderer()
