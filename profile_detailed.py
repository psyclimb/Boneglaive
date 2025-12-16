#!/usr/bin/env python3
"""
Detailed profiler - instruments the renderer to measure each section.
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

# Monkey-patch the renderer to add timing
original_update = GraphicalRenderer.update
original_draw_grid = GraphicalRenderer.draw_grid
original_draw = GraphicalRenderer.draw

timings = {
    'update_total': [],
    'update_units': [],
    'draw_total': [],
    'draw_grid': [],
    'draw_units': [],
}

def timed_update(self, delta_time):
    start = time.perf_counter()

    # Call original update but measure unit updates separately
    if self.paused:
        return

    # Fast parts
    if (self.game_adapter.game and
        self.game_adapter.game.setup_phase and
        not self.setup_mode):
        self.start_setup_mode()

    self.astral_value_pulse_time += delta_time

    # Imbued sparkles
    updated_sparkles = []
    for sparkle in self.imbued_sparkles:
        sparkle['life'] += delta_time
        if sparkle['life'] >= sparkle['max_life']:
            continue
        sparkle['x'] += sparkle['vx'] * delta_time
        sparkle['y'] += sparkle['vy'] * delta_time
        updated_sparkles.append(sparkle)
    self.imbued_sparkles = updated_sparkles

    # Screen shake
    if self.screen_shake_duration > 0:
        self.screen_shake_duration -= delta_time
        if self.screen_shake_duration <= 0:
            self.screen_shake_intensity = 0

    # Flash
    if self.flash_duration > 0:
        self.flash_duration -= delta_time
        self.flash_alpha = int(255 * max(0, self.flash_duration / 0.2))

    # Sync (already optimized)
    should_sync = (
        len(self.active_animations) > 0 or
        hasattr(self, '_force_sync') and self._force_sync
    )
    if should_sync:
        animation_events = self.game_adapter.sync_state()
        for event in animation_events:
            self.handle_animation_event(event)
        if hasattr(self, '_force_sync'):
            self._force_sync = False

    # TIME THIS: Update units
    units_start = time.perf_counter()
    for unit in self.units:
        unit.update(delta_time)
    timings['update_units'].append((time.perf_counter() - units_start) * 1000)

    # Rest of update (particles, etc)
    self.particle_emitter.update(delta_time)
    self.floating_texts = [t for t in self.floating_texts if t.update(delta_time)]

    # Debris, animations, motor - skip for brevity, these are small

    total_time = (time.perf_counter() - start) * 1000
    timings['update_total'].append(total_time)

def timed_draw_grid(self, surface):
    start = time.perf_counter()
    original_draw_grid(self, surface)
    timings['draw_grid'].append((time.perf_counter() - start) * 1000)

def timed_draw(self):
    start = time.perf_counter()

    # Measure draw_units within draw
    draw_units_start = None

    # We'll hook the unit drawing
    original_unit_draw = None
    units_drawn = [0]  # Use list to make it mutable in closure

    # Just call original and measure total
    original_draw(self)

    timings['draw_total'].append((time.perf_counter() - start) * 1000)

# Apply patches
GraphicalRenderer.update = timed_update
GraphicalRenderer.draw_grid = timed_draw_grid
GraphicalRenderer.draw = timed_draw

def profile_detailed():
    """Run detailed profiling."""
    print("="*60)
    print("DETAILED FPS PROFILER")
    print("="*60)

    # Setup
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True, map_name='lime_foyer')
    renderer = GraphicalRenderer(adapter)

    # Add 6 units
    for unit_type, player, y, x in [
        (UnitType.GLAIVEMAN, 1, 2, 2),
        (UnitType.POTPOURRIST, 1, 3, 3),
        (UnitType.MANDIBLE_FOREMAN, 1, 4, 2),
        (UnitType.GLAIVEMAN, 2, 17, 7),
        (UnitType.POTPOURRIST, 2, 16, 6),
        (UnitType.MANDIBLE_FOREMAN, 2, 15, 7),
    ]:
        unit = Unit(unit_type, player, y, x)
        adapter.game.units.append(unit)

    renderer.sync_units_from_game()
    print(f"Units: {len(renderer.units)}\n")

    # Run 100 frames
    print("Profiling 100 frames...\n")
    for frame in range(100):
        delta_time = renderer.clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.running = False
                break

        if not renderer.running:
            break

        renderer.update(delta_time)
        renderer.draw()

    pygame.quit()

    # Results
    print("="*60)
    print("RESULTS (avg of 100 frames)")
    print("="*60)

    for key, times in timings.items():
        if times:
            avg = sum(times) / len(times)
            print(f"{key:20s}: {avg:7.2f} ms")

    print("\n" + "="*60)

    # Calculate total
    update_avg = sum(timings['update_total']) / len(timings['update_total'])
    draw_avg = sum(timings['draw_total']) / len(timings['draw_total'])
    total_avg = update_avg + draw_avg

    print(f"TOTAL per frame: {total_avg:.2f} ms ({1000/total_avg:.1f} FPS)")
    print(f"TARGET: 16.67 ms (60 FPS)")

    if total_avg > 16.67:
        print(f"\nOVER BUDGET BY: {total_avg - 16.67:.2f} ms")

if __name__ == "__main__":
    profile_detailed()
