#!/usr/bin/env python3
"""
Test FPS with units on the board to verify performance improvements.
This test places units on the board and measures FPS.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.utils.constants import UnitType

def test_fps_with_units():
    """Test FPS with multiple units placed on the board."""
    print("="*60)
    print("FPS Performance Test - Units on Board")
    print("="*60)
    print("\nThis test will:")
    print("1. Start with empty board (5 seconds)")
    print("2. Place 6 units on board (10 seconds)")
    print("3. Display FPS comparison")
    print("\nWatch the FPS counter in the top-right corner!")
    print("="*60 + "\n")

    # Create adapter and initialize game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True, map_name='lime_foyer')

    # Create renderer
    renderer = GraphicalRenderer(adapter)

    # Ensure FPS counter is visible
    renderer.show_fps = True

    # Phase 1: Empty board
    print("Phase 1: Measuring FPS with empty board (5 seconds)...")
    start_time = time.time()
    empty_board_fps = []

    while time.time() - start_time < 5.0 and renderer.running:
        delta_time = renderer.clock.tick(60) / 1000.0

        # Update FPS counter
        if renderer.show_fps:
            current_fps = renderer.clock.get_fps()
            renderer.fps_values.append(current_fps)
            if len(renderer.fps_values) > 30:
                renderer.fps_values.pop(0)
            if len(renderer.fps_values) > 0:
                renderer.fps_display = sum(renderer.fps_values) / len(renderer.fps_values)
                empty_board_fps.append(renderer.fps_display)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False

        renderer.update(delta_time)
        renderer.draw()

    avg_empty_fps = sum(empty_board_fps) / len(empty_board_fps) if empty_board_fps else 0
    print(f"Empty board average FPS: {avg_empty_fps:.1f}")

    # Phase 2: Add units
    print("\nPhase 2: Placing 6 units on board...")

    # Add 3 units per player
    from boneglaive.game.units import Unit
    units_to_add = [
        (UnitType.GLAIVEMAN, 1, 2, 2),
        (UnitType.POTPOURRIST, 1, 3, 3),
        (UnitType.MANDIBLE_FOREMAN, 1, 4, 2),
        (UnitType.GLAIVEMAN, 2, 17, 7),
        (UnitType.POTPOURRIST, 2, 16, 6),
        (UnitType.MANDIBLE_FOREMAN, 2, 15, 7),
    ]

    for unit_type, player, y, x in units_to_add:
        unit = Unit(unit_type, player, y, x)
        adapter.game.units.append(unit)

    # Sync units to renderer
    renderer.sync_units_from_game()
    print(f"Added {len(renderer.units)} units to the board")

    # Measure FPS with units
    print("Measuring FPS with units on board (10 seconds)...")
    start_time = time.time()
    with_units_fps = []

    while time.time() - start_time < 10.0 and renderer.running:
        delta_time = renderer.clock.tick(60) / 1000.0

        # Update FPS counter
        if renderer.show_fps:
            current_fps = renderer.clock.get_fps()
            renderer.fps_values.append(current_fps)
            if len(renderer.fps_values) > 30:
                renderer.fps_values.pop(0)
            if len(renderer.fps_values) > 0:
                renderer.fps_display = sum(renderer.fps_values) / len(renderer.fps_values)
                with_units_fps.append(renderer.fps_display)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False

        renderer.update(delta_time)
        renderer.draw()

    pygame.quit()

    avg_with_units_fps = sum(with_units_fps) / len(with_units_fps) if with_units_fps else 0
    print(f"With units average FPS: {avg_with_units_fps:.1f}")

    # Results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Empty board FPS:  {avg_empty_fps:.1f}")
    print(f"With units FPS:   {avg_with_units_fps:.1f}")

    if avg_empty_fps > 0:
        drop = avg_empty_fps - avg_with_units_fps
        drop_pct = (drop / avg_empty_fps) * 100
        print(f"FPS drop:         {drop:.1f} ({drop_pct:.1f}%)")

    print("="*60)

    if avg_with_units_fps >= 55:
        print("\nSUCCESS: Performance is good (>=55 FPS with units)")
    elif avg_with_units_fps >= 45:
        print("\nACCEPTABLE: Performance is acceptable (>=45 FPS with units)")
    else:
        print("\nWARNING: Performance needs improvement (<45 FPS with units)")

if __name__ == "__main__":
    test_fps_with_units()
