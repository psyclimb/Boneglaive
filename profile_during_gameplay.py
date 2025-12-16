#!/usr/bin/env python3
"""
Profile FPS during actual gameplay - captures performance during turn execution.
This monitors FPS continuously and logs bottlenecks when FPS drops.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from collections import deque
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.utils.constants import UnitType
from boneglaive.game.units import Unit

# Real-time performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.frame_times = deque(maxlen=60)  # Last 60 frames
        self.section_times = {
            'update': deque(maxlen=60),
            'update_units': deque(maxlen=60),
            'update_animations': deque(maxlen=60),
            'update_particles': deque(maxlen=60),
            'draw': deque(maxlen=60),
            'draw_grid': deque(maxlen=60),
            'draw_units': deque(maxlen=60),
            'draw_ui': deque(maxlen=60),
            'flip': deque(maxlen=60),
        }
        self.last_report_time = time.time()
        self.report_interval = 2.0  # Report every 2 seconds

    def record_frame(self, frame_time):
        self.frame_times.append(frame_time)

    def record_section(self, section_name, duration):
        if section_name in self.section_times:
            self.section_times[section_name].append(duration)

    def get_avg_fps(self):
        if not self.frame_times:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1000 / avg_frame_time if avg_frame_time > 0 else 0

    def should_report(self):
        now = time.time()
        if now - self.last_report_time >= self.report_interval:
            self.last_report_time = now
            return True
        return False

    def get_report(self):
        """Get current performance report."""
        report = []
        avg_fps = self.get_avg_fps()
        report.append(f"\n{'='*60}")
        report.append(f"PERFORMANCE REPORT (avg last 60 frames)")
        report.append(f"FPS: {avg_fps:.1f}")
        report.append(f"{'='*60}")

        # Calculate averages and identify bottlenecks
        bottlenecks = []
        for section, times in self.section_times.items():
            if times:
                avg = sum(times) / len(times)
                pct_of_budget = (avg / 16.67) * 100

                # Flag if over 20% of frame budget
                flag = " *** SLOW ***" if pct_of_budget > 20 else ""
                report.append(f"{section:20s}: {avg:6.2f} ms ({pct_of_budget:5.1f}%){flag}")

                if pct_of_budget > 20:
                    bottlenecks.append((section, avg, pct_of_budget))

        report.append(f"{'='*60}")

        if bottlenecks:
            report.append("\nBOTTLENECKS DETECTED:")
            for section, avg, pct in sorted(bottlenecks, key=lambda x: x[1], reverse=True):
                report.append(f"  {section}: {avg:.2f}ms ({pct:.1f}% of budget)")

        return "\n".join(report)

# Monkey-patch renderer to add instrumentation
monitor = PerformanceMonitor()

original_update = GraphicalRenderer.update
original_draw = GraphicalRenderer.draw

def instrumented_update(self, delta_time):
    """Update with timing instrumentation."""
    t_start = time.perf_counter()

    # Minimal update logic with timing checkpoints
    if self.paused:
        return

    # Setup check (fast)
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

    # TIME: Update units
    t = time.perf_counter()
    for unit in self.units:
        unit.update(delta_time)
    monitor.record_section('update_units', (time.perf_counter() - t) * 1000)

    # TIME: Update particles
    t = time.perf_counter()
    self.particle_emitter.update(delta_time)
    self.floating_texts = [ft for ft in self.floating_texts if ft.update(delta_time)]
    monitor.record_section('update_particles', (time.perf_counter() - t) * 1000)

    # Debris (skip timing, usually empty)
    remaining_debris = []
    for debris in self.debris_particles:
        if debris.update(delta_time):
            if not debris.check_collision(self.units, self.particle_emitter):
                remaining_debris.append(debris)
    self.debris_particles = remaining_debris

    # TIME: Update animations
    t = time.perf_counter()
    updated_animations = []
    for anim in self.active_animations:
        still_active = anim.update(delta_time)

        # Handle animation triggers (impact, etc)
        if hasattr(anim, 'trigger_impact') and anim.trigger_impact:
            # Create particles (simplified for profiling)
            self.particle_emitter.emit_burst(anim.target_x, anim.target_y, (255, 215, 0), count=40)
            anim.trigger_impact = False

        if still_active:
            updated_animations.append(anim)

    self.active_animations = updated_animations
    monitor.record_section('update_animations', (time.perf_counter() - t) * 1000)

    # Motor animation
    self.motor_animation.update(delta_time)

    # Check for pending events
    if self.pending_animation_events and not self.has_active_animations():
        self.flush_pending_events()

    monitor.record_section('update', (time.perf_counter() - t_start) * 1000)

def instrumented_draw(self):
    """Draw with timing instrumentation."""
    import random
    from boneglaive.graphical.renderer import COLOR_BG, SCREEN_WIDTH, SCREEN_HEIGHT

    t_start = time.perf_counter()

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
    monitor.record_section('draw_grid', (time.perf_counter() - t) * 1000)

    # Range indicators (usually fast)
    self.draw_range_indicators(main_surface)

    # Selection
    if self.selected_unit:
        self.draw_selection_highlight(main_surface, self.selected_unit)

    # Astral values, imbued furniture, skill shadows (skip for brevity)
    if self.show_astral_values:
        self.draw_astral_values(main_surface)
    self.draw_imbued_furniture(main_surface)
    self.draw_skill_shadows(main_surface)

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
    monitor.record_section('draw_units', (time.perf_counter() - t) * 1000)

    # Animations
    for animation in self.active_animations:
        animation.draw(main_surface)

    # Particles
    self.particle_emitter.draw(main_surface)
    for text in self.floating_texts:
        text.draw(main_surface, self.font)
    for debris in self.debris_particles:
        debris.draw(main_surface)

    # TIME: draw_ui
    t = time.perf_counter()
    self.draw_ui(main_surface)
    monitor.record_section('draw_ui', (time.perf_counter() - t) * 1000)

    # Skill bar
    self.skill_bar.draw(main_surface, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Blit to screen
    self.screen.fill(COLOR_BG)
    self.screen.blit(main_surface, (int(shake_offset_x), int(shake_offset_y)))

    # Flash overlay
    if self.flash_alpha > 0:
        self._flash_surface.set_alpha(int(self.flash_alpha))
        self._flash_surface.fill(self.flash_color)
        self.screen.blit(self._flash_surface, (0, 0))

    # Overlays (help, respawn, setup)
    self.help_page.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
    if self.respawn_mode and self.respawn_selecting_unit:
        self.respawn_window.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
    if self.setup_mode and self.setup_selecting_unit:
        self.setup_window.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        help_panel_x = 620
        help_panel_y = 50
        help_panel_width = SCREEN_WIDTH - help_panel_x - 20
        help_panel_height = SCREEN_HEIGHT - 100
        self.setup_help_panel_rect = self.setup_unit_help.draw(self.screen, help_panel_x, help_panel_y, help_panel_width, help_panel_height)

    # FPS counter
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

    # TIME: flip
    t = time.perf_counter()
    pygame.display.flip()
    monitor.record_section('flip', (time.perf_counter() - t) * 1000)

    monitor.record_section('draw', (time.perf_counter() - t_start) * 1000)

# Apply instrumentation
GraphicalRenderer.update = instrumented_update
GraphicalRenderer.draw = instrumented_draw

def main():
    """Run game with continuous performance monitoring."""
    print("="*60)
    print("GAMEPLAY PERFORMANCE MONITOR")
    print("="*60)
    print("\nThis profiler runs during actual gameplay.")
    print("Performance reports print every 2 seconds.")
    print("Play the game normally - move units, execute turns, etc.")
    print("Watch for BOTTLENECKS when FPS drops!")
    print("\nPress Ctrl+C to exit")
    print("="*60 + "\n")

    # Setup game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=False, map_name='lime_foyer')

    renderer = GraphicalRenderer(adapter)
    renderer.show_fps = True

    # Set up UI adapter
    from boneglaive.graphical.ui_adapter import GraphicalUIAdapter
    ui_adapter = GraphicalUIAdapter(renderer)
    adapter.game.set_ui_reference(ui_adapter)

    # Add welcome messages
    renderer.combat_log.add_message("Performance Monitor Active", "system")
    renderer.combat_log.add_message("Reports print to console", "system")

    print("Game started. Play normally and watch console for reports.\n")

    # Main game loop
    try:
        while renderer.running:
            frame_start = time.perf_counter()
            delta_time = renderer.clock.tick(60) / 1000.0

            # Update FPS counter
            if renderer.show_fps:
                current_fps = renderer.clock.get_fps()
                renderer.fps_values.append(current_fps)
                if len(renderer.fps_values) > 30:
                    renderer.fps_values.pop(0)
                if len(renderer.fps_values) > 0:
                    renderer.fps_display = sum(renderer.fps_values) / len(renderer.fps_values)

            renderer.handle_events()
            renderer.update(delta_time)
            renderer.draw()

            frame_time = (time.perf_counter() - frame_start) * 1000
            monitor.record_frame(frame_time)

            # Print report periodically
            if monitor.should_report():
                print(monitor.get_report())

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")

    pygame.quit()

    # Final report
    print("\n" + "="*60)
    print("FINAL PERFORMANCE SUMMARY")
    print(monitor.get_report())

if __name__ == "__main__":
    main()
