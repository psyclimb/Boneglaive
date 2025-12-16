#!/usr/bin/env python3
"""
Profile each section of the draw() method.
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

# Store timings
timings = {
    'draw_grid': [],
    'draw_range_indicators': [],
    'draw_selection': [],
    'draw_units': [],
    'draw_animations': [],
    'draw_particles': [],
    'draw_ui': [],
    'draw_skill_bar': [],
    'draw_fps': [],
    'flip': [],
}

# Monkey-patch draw() to measure each section
original_draw = GraphicalRenderer.draw

def profiled_draw(self):
    """Draw with timing for each section."""
    import random
    from boneglaive.graphical.renderer import COLOR_BG

    # Screen shake
    shake_offset_x = 0
    shake_offset_y = 0
    if self.screen_shake_intensity > 0:
        shake_offset_x = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
        shake_offset_y = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
    self.camera.set_shake(shake_offset_x, shake_offset_y)

    main_surface = self._main_surface
    main_surface.fill(COLOR_BG)

    # TIME: draw_grid
    t = time.perf_counter()
    self.draw_grid(main_surface)
    timings['draw_grid'].append((time.perf_counter() - t) * 1000)

    # TIME: draw_range_indicators
    t = time.perf_counter()
    self.draw_range_indicators(main_surface)
    timings['draw_range_indicators'].append((time.perf_counter() - t) * 1000)

    # TIME: draw_selection
    t = time.perf_counter()
    if self.selected_unit:
        self.draw_selection_highlight(main_surface, self.selected_unit)
    timings['draw_selection'].append((time.perf_counter() - t) * 1000)

    # Skip astral values, imbued furniture, skill shadows for brevity

    # TIME: draw_units
    t = time.perf_counter()
    for unit in self.units:
        if hasattr(unit, 'teleport_hidden') and unit.teleport_hidden:
            continue
        if self.setup_mode and self.game_adapter.game and self.game_adapter.game.setup_phase:
            setup_player = self.game_adapter.game.setup_player
            game_unit = self._get_game_unit(unit)
            if game_unit and game_unit.player != setup_player:
                continue
        unit.draw(main_surface, self.small_font)
    timings['draw_units'].append((time.perf_counter() - t) * 1000)

    # TIME: draw_animations
    t = time.perf_counter()
    for animation in self.active_animations:
        animation.draw(main_surface)
    timings['draw_animations'].append((time.perf_counter() - t) * 1000)

    # TIME: draw_particles
    t = time.perf_counter()
    self.particle_emitter.draw(main_surface)
    for text in self.floating_texts:
        text.draw(main_surface, self.font)
    for debris in self.debris_particles:
        debris.draw(main_surface)
    timings['draw_particles'].append((time.perf_counter() - t) * 1000)

    # TIME: draw_ui
    t = time.perf_counter()
    self.draw_ui(main_surface)
    timings['draw_ui'].append((time.perf_counter() - t) * 1000)

    # TIME: draw_skill_bar
    t = time.perf_counter()
    from boneglaive.graphical.renderer import SCREEN_WIDTH, SCREEN_HEIGHT
    self.skill_bar.draw(main_surface, SCREEN_WIDTH, SCREEN_HEIGHT)
    timings['draw_skill_bar'].append((time.perf_counter() - t) * 1000)

    # Blit to screen
    self.screen.fill(COLOR_BG)
    self.screen.blit(main_surface, (int(shake_offset_x), int(shake_offset_y)))

    # Flash overlay (skip timing, very fast)
    if self.flash_alpha > 0:
        self._flash_surface.set_alpha(int(self.flash_alpha))
        self._flash_surface.fill(self.flash_color)
        self.screen.blit(self._flash_surface, (0, 0))

    # Overlays (help, respawn, setup) - skip for brevity

    # TIME: draw_fps
    t = time.perf_counter()
    if self.show_fps:
        fps_text = f"FPS: {self.fps_display:.1f}"
        fps_surface = self.small_font.render(fps_text, True, (100, 255, 100))
        fps_x = SCREEN_WIDTH - fps_surface.get_width() - 10
        fps_y = 5
        bg_rect = pygame.Rect(fps_x - 5, fps_y - 2, fps_surface.get_width() + 10, fps_surface.get_height() + 4)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(180)
        bg_surface.fill((20, 20, 20))
        self.screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
        self.screen.blit(fps_surface, (fps_x, fps_y))
    timings['draw_fps'].append((time.perf_counter() - t) * 1000)

    # TIME: flip
    t = time.perf_counter()
    pygame.display.flip()
    timings['flip'].append((time.perf_counter() - t) * 1000)

GraphicalRenderer.draw = profiled_draw

def main():
    print("="*60)
    print("DRAW() METHOD PROFILER")
    print("="*60)

    # Setup
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True, map_name='lime_foyer')
    renderer = GraphicalRenderer(adapter)

    # Add units
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
    print("DRAW() SECTION TIMINGS (avg of 100 frames)")
    print("="*60)

    total = 0
    for key in ['draw_grid', 'draw_range_indicators', 'draw_selection', 'draw_units',
                'draw_animations', 'draw_particles', 'draw_ui', 'draw_skill_bar',
                'draw_fps', 'flip']:
        if timings[key]:
            avg = sum(timings[key]) / len(timings[key])
            total += avg
            pct = (avg / 16.67) * 100
            print(f"{key:25s}: {avg:7.2f} ms ({pct:5.1f}% of budget)")

    print("-" * 60)
    print(f"{'TOTAL':25s}: {total:7.2f} ms")
    print(f"TARGET: 16.67 ms (60 FPS)")
    print(f"ACTUAL: {1000/total:.1f} FPS")
    print("="*60)

if __name__ == "__main__":
    main()
