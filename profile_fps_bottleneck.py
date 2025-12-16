#!/usr/bin/env python3
"""
Profile FPS bottleneck - measure exactly where time is being spent.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.utils.constants import UnitType
from boneglaive.game.units import Unit

def profile_bottleneck():
    """Profile to find the exact bottleneck."""
    print("="*60)
    print("FPS BOTTLENECK PROFILER")
    print("="*60)

    # Create adapter and initialize game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True, map_name='lime_foyer')

    # Create renderer
    renderer = GraphicalRenderer(adapter)
    renderer.show_fps = True

    # Add 6 units
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

    renderer.sync_units_from_game()
    print(f"\nUnits on board: {len(renderer.units)}")

    # Profile 100 frames
    print("\nProfiling 100 frames...")
    profiles = {
        'update': [],
        'draw': [],
        'draw_grid': [],
        'draw_units': [],
        'update_units': [],
        'total': []
    }

    for frame in range(100):
        frame_start = time.perf_counter()
        delta_time = renderer.clock.tick(60) / 1000.0

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False
                break

        if not renderer.running:
            break

        # Profile update
        update_start = time.perf_counter()
        renderer.update(delta_time)
        update_time = (time.perf_counter() - update_start) * 1000

        # Profile draw sections
        draw_start = time.perf_counter()

        # We need to manually time subsections of draw
        # Let's just measure total draw first
        renderer.draw()
        draw_time = (time.perf_counter() - draw_start) * 1000

        frame_time = (time.perf_counter() - frame_start) * 1000

        profiles['update'].append(update_time)
        profiles['draw'].append(draw_time)
        profiles['total'].append(frame_time)

    pygame.quit()

    # Print results
    print("\n" + "="*60)
    print("PROFILING RESULTS (average of 100 frames)")
    print("="*60)

    for key in ['total', 'update', 'draw']:
        avg = sum(profiles[key]) / len(profiles[key])
        print(f"{key:15s}: {avg:6.2f} ms")

    print("\n" + "="*60)
    print("BREAKDOWN")
    print("="*60)

    total_avg = sum(profiles['total']) / len(profiles['total'])
    update_avg = sum(profiles['update']) / len(profiles['update'])
    draw_avg = sum(profiles['draw']) / len(profiles['draw'])

    update_pct = (update_avg / total_avg) * 100
    draw_pct = (draw_avg / total_avg) * 100

    print(f"Update: {update_pct:.1f}%")
    print(f"Draw:   {draw_pct:.1f}%")

    print("\n" + "="*60)
    print("TARGET: <16.67ms per frame for 60 FPS")
    print(f"ACTUAL: {total_avg:.2f}ms per frame ({1000/total_avg:.1f} FPS)")
    print("="*60)

    if total_avg > 16.67:
        slowdown = total_avg - 16.67
        print(f"\nSLOWDOWN: {slowdown:.2f}ms over budget")
        if update_avg > draw_avg:
            print("BOTTLENECK: update() method")
        else:
            print("BOTTLENECK: draw() method")

if __name__ == "__main__":
    profile_bottleneck()
