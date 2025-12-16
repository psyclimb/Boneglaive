#!/usr/bin/env python3
"""
Profile each UI component in draw_ui().
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from boneglaive.graphical.renderer import GraphicalRenderer, SCREEN_WIDTH, SCREEN_HEIGHT, TOP_BAR_HEIGHT, BOTTOM_BAR_HEIGHT, LEFT_PANEL_WIDTH, RIGHT_PANEL_WIDTH
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.utils.constants import UnitType
from boneglaive.game.units import Unit

# Store timings
timings = {
    'top_bar_update': [],
    'unit_status_bar_update': [],
    'action_menu_update': [],
    'top_bar_draw': [],
    'left_panel_fill': [],
    'unit_status_bar_draw': [],
    'combat_log_draw': [],
    'right_panel_fill': [],
    'unit_info_panel_draw': [],
    'motor_animation_draw': [],
    'status_effects_panel_draw': [],
    'action_menu_draw': [],
}

# Monkey-patch draw_ui
original_draw_ui = GraphicalRenderer.draw_ui

def profiled_draw_ui(self, surface):
    """Draw UI with detailed timing."""
    game = self.game_adapter.game
    if game:
        # Get selected game unit
        selected_game_unit = None
        if self.selected_unit:
            for unit in game.units:
                if unit.is_alive() and unit.x == self.selected_unit.grid_x and unit.y == self.selected_unit.grid_y:
                    selected_game_unit = unit
                    break

        # TIME: top_bar.update
        t = time.perf_counter()
        self.top_bar.update(game, self.current_action_mode)
        timings['top_bar_update'].append((time.perf_counter() - t) * 1000)

        # TIME: unit_status_bar.update
        t = time.perf_counter()
        self.unit_status_bar.update(game, selected_game_unit)
        timings['unit_status_bar_update'].append((time.perf_counter() - t) * 1000)

        # TIME: action_menu.update
        t = time.perf_counter()
        has_actions = any(u.move_target or u.attack_target or u.skill_target for u in game.units if u.is_alive())
        self.action_menu.update(game, selected_game_unit, self.current_action_mode, has_actions)
        timings['action_menu_update'].append((time.perf_counter() - t) * 1000)

    # TIME: top_bar.draw
    t = time.perf_counter()
    self.top_bar.draw(surface, SCREEN_WIDTH)
    timings['top_bar_draw'].append((time.perf_counter() - t) * 1000)

    panel_height = SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
    left_panel_x = 0
    left_panel_y = TOP_BAR_HEIGHT

    # TIME: left_panel fill
    t = time.perf_counter()
    self._left_panel_surface.fill((30, 34, 42))
    surface.blit(self._left_panel_surface, (left_panel_x, left_panel_y))
    pygame.draw.line(surface, (60, 64, 72),
                    (LEFT_PANEL_WIDTH - 1, TOP_BAR_HEIGHT),
                    (LEFT_PANEL_WIDTH - 1, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT), 2)
    timings['left_panel_fill'].append((time.perf_counter() - t) * 1000)

    # TIME: unit_status_bar.draw
    t = time.perf_counter()
    unit_bar_height = self.unit_status_bar.get_height()
    self.unit_status_bar.draw(surface, left_panel_x + 5, left_panel_y + 5)
    timings['unit_status_bar_draw'].append((time.perf_counter() - t) * 1000)

    # TIME: combat_log.draw
    t = time.perf_counter()
    log_y = left_panel_y + unit_bar_height + 10
    log_height = panel_height - unit_bar_height - 20
    self.combat_log.draw(surface, left_panel_x + 10, log_y, height=log_height)
    timings['combat_log_draw'].append((time.perf_counter() - t) * 1000)

    right_panel_x = SCREEN_WIDTH - RIGHT_PANEL_WIDTH
    right_panel_y = TOP_BAR_HEIGHT

    # TIME: right_panel fill
    t = time.perf_counter()
    self._right_panel_surface.fill((30, 34, 42))
    surface.blit(self._right_panel_surface, (right_panel_x, right_panel_y))
    pygame.draw.line(surface, (60, 64, 72),
                    (right_panel_x, TOP_BAR_HEIGHT),
                    (right_panel_x, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT), 2)
    timings['right_panel_fill'].append((time.perf_counter() - t) * 1000)

    # TIME: unit_info_panel.draw
    t = time.perf_counter()
    self.unit_info_panel.draw(surface, right_panel_x + 10, right_panel_y + 5)
    timings['unit_info_panel_draw'].append((time.perf_counter() - t) * 1000)

    # TIME: motor_animation.draw
    t = time.perf_counter()
    motor_y = right_panel_y + 245
    self.motor_animation.draw(surface, right_panel_x + 15, motor_y)
    timings['motor_animation_draw'].append((time.perf_counter() - t) * 1000)

    # TIME: status_effects_panel.draw
    t = time.perf_counter()
    status_effects_y = motor_y + 150
    if game and self.selected_unit:
        for unit in game.units:
            if unit.is_alive() and unit.x == self.selected_unit.grid_x and unit.y == self.selected_unit.grid_y:
                self.status_effects_panel.update(unit)
                self.status_effects_panel.draw(surface, right_panel_x + 10, status_effects_y)
                break
    timings['status_effects_panel_draw'].append((time.perf_counter() - t) * 1000)

    # TIME: action_menu.draw
    t = time.perf_counter()
    action_menu_y = status_effects_y + 60
    self.action_menu.draw(surface, right_panel_x + 5, action_menu_y)
    timings['action_menu_draw'].append((time.perf_counter() - t) * 1000)

GraphicalRenderer.draw_ui = profiled_draw_ui

def main():
    print("="*60)
    print("UI COMPONENTS PROFILER")
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
    print("UI COMPONENT TIMINGS (avg of 100 frames)")
    print("="*60)

    total = 0
    for key in ['top_bar_update', 'unit_status_bar_update', 'action_menu_update',
                'top_bar_draw', 'left_panel_fill', 'unit_status_bar_draw',
                'combat_log_draw', 'right_panel_fill', 'unit_info_panel_draw',
                'motor_animation_draw', 'status_effects_panel_draw', 'action_menu_draw']:
        if timings[key]:
            avg = sum(timings[key]) / len(timings[key])
            total += avg
            pct = (avg / 16.67) * 100
            print(f"{key:30s}: {avg:7.2f} ms ({pct:5.1f}% of budget)")

    print("-" * 60)
    print(f"{'TOTAL draw_ui()':30s}: {total:7.2f} ms")
    print("="*60)

if __name__ == "__main__":
    main()
