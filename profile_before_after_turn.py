#!/usr/bin/env python3
"""
Before/After Turn Comparison Profiler

Captures detailed frame timing before, during, and after turn execution
to show exactly how turn changes impact frame rate.

Captures:
- 60 frames BEFORE execute button press (baseline)
- All frames DURING turn execution
- 60 frames AFTER turn completes (recovery)

Generates comparison report showing:
- Average frame time in each phase
- Frame time distribution (min/max/p95)
- Visual timeline of frame drops

Usage:
    python profile_before_after_turn.py

Press E to execute a turn. The profiler will capture timing data
and print a detailed before/after comparison.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from collections import deque
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.ui_adapter import GraphicalUIAdapter

class BeforeAfterProfiler:
    """Captures frame timing before, during, and after turn execution."""

    def __init__(self):
        self.before_frames = deque(maxlen=60)  # 60 frames before turn
        self.during_frames = []  # All frames during turn
        self.after_frames = deque(maxlen=60)  # 60 frames after turn

        self.phase = 'before'  # 'before', 'during', 'after'
        self.turn_count = 0
        self.profiles = []  # List of completed profiles

    def record_frame(self, frame_time_ms):
        """Record a frame time."""
        if self.phase == 'before':
            self.before_frames.append(frame_time_ms)
        elif self.phase == 'during':
            self.during_frames.append(frame_time_ms)
        elif self.phase == 'after':
            self.after_frames.append(frame_time_ms)

            # Check if we've captured enough after frames
            if len(self.after_frames) >= 60:
                self.finalize_profile()

    def start_turn_execution(self):
        """Transition to 'during' phase."""
        self.phase = 'during'
        self.during_frames = []
        self.turn_count += 1

    def end_turn_execution(self):
        """Transition to 'after' phase."""
        self.phase = 'after'
        self.after_frames.clear()

    def finalize_profile(self):
        """Save the completed profile and reset."""
        profile = {
            'turn': self.turn_count,
            'before': list(self.before_frames),
            'during': list(self.during_frames),
            'after': list(self.after_frames)
        }
        self.profiles.append(profile)

        # Print report immediately
        print(self.get_report(profile))

        # Reset to before phase for next turn
        self.phase = 'before'
        self.before_frames.clear()

    def get_stats(self, frames):
        """Calculate statistics for a list of frame times."""
        if not frames:
            return None

        frames_sorted = sorted(frames)
        count = len(frames)

        return {
            'count': count,
            'avg': sum(frames) / count,
            'min': frames_sorted[0],
            'max': frames_sorted[-1],
            'p50': frames_sorted[count // 2],
            'p95': frames_sorted[int(count * 0.95)] if count > 20 else frames_sorted[-1],
            'p99': frames_sorted[int(count * 0.99)] if count > 100 else frames_sorted[-1],
        }

    def get_report(self, profile):
        """Generate a detailed comparison report."""
        lines = []

        lines.append("\n" + "="*70)
        lines.append(f"BEFORE/DURING/AFTER TURN COMPARISON - Turn #{profile['turn']}")
        lines.append("="*70)

        # Calculate stats for each phase
        before_stats = self.get_stats(profile['before'])
        during_stats = self.get_stats(profile['during'])
        after_stats = self.get_stats(profile['after'])

        # Print phase statistics
        lines.append("\nPHASE STATISTICS (frame times in milliseconds):")
        lines.append("-" * 70)

        phases = [
            ('BEFORE (baseline)', before_stats),
            ('DURING (turn execution)', during_stats),
            ('AFTER (recovery)', after_stats)
        ]

        for phase_name, stats in phases:
            if stats:
                lines.append(f"\n{phase_name}:")
                lines.append(f"  Frames: {stats['count']}")
                lines.append(f"  Average: {stats['avg']:.2f} ms ({1000/stats['avg']:.1f} FPS)")
                lines.append(f"  Min: {stats['min']:.2f} ms")
                lines.append(f"  Max: {stats['max']:.2f} ms")
                lines.append(f"  P50 (median): {stats['p50']:.2f} ms")
                lines.append(f"  P95: {stats['p95']:.2f} ms")

                # Flag issues
                if stats['avg'] > 16.67:
                    frames_dropped = ((stats['avg'] / 16.67) - 1) * 100
                    lines.append(f"  STATUS: *** BELOW 60 FPS *** (avg {frames_dropped:.1f}% over budget)")
                elif stats['p95'] > 16.67:
                    lines.append(f"  STATUS: *** FRAME SPIKES *** (P95 above 60 FPS target)")
                else:
                    lines.append(f"  STATUS: OK (consistent 60 FPS)")

        # Impact analysis
        lines.append("\n" + "-" * 70)
        lines.append("IMPACT ANALYSIS:")

        if before_stats and during_stats:
            during_slowdown = during_stats['avg'] / before_stats['avg']
            during_fps_drop = (1000 / before_stats['avg']) - (1000 / during_stats['avg'])

            lines.append(f"\nTurn Execution Impact:")
            lines.append(f"  Frame time increased by: {during_slowdown:.2f}x")
            lines.append(f"  FPS drop: {during_fps_drop:.1f} FPS")

            if during_slowdown > 2.0:
                lines.append(f"  SEVERITY: *** CRITICAL *** (>2x slowdown)")
            elif during_slowdown > 1.5:
                lines.append(f"  SEVERITY: *** HIGH *** (>1.5x slowdown)")
            elif during_slowdown > 1.2:
                lines.append(f"  SEVERITY: MODERATE (>1.2x slowdown)")
            else:
                lines.append(f"  SEVERITY: LOW (minimal impact)")

        if during_stats and after_stats:
            recovery_ratio = after_stats['avg'] / during_stats['avg']

            lines.append(f"\nRecovery:")
            lines.append(f"  Post-turn frame time: {after_stats['avg']:.2f} ms")
            lines.append(f"  Recovery ratio: {recovery_ratio:.2f}x faster than during")

            if after_stats['avg'] > before_stats['avg'] * 1.1:
                lines.append(f"  STATUS: *** INCOMPLETE RECOVERY *** (still slower than baseline)")
            else:
                lines.append(f"  STATUS: Full recovery to baseline")

        # Visual timeline
        lines.append("\n" + "-" * 70)
        lines.append("FRAME TIME TIMELINE (each bar = 10 frames):")
        lines.append("Target: 16.67ms (60 FPS)")
        lines.append("")

        # Show before phase
        if before_stats:
            before_bar = self._create_timeline_bar(profile['before'], "BEFORE", (0, 255, 0))
            lines.append(before_bar)

        # Show during phase
        if during_stats:
            during_bar = self._create_timeline_bar(profile['during'], "DURING", (255, 100, 100))
            lines.append(during_bar)

        # Show after phase
        if after_stats:
            after_bar = self._create_timeline_bar(profile['after'], "AFTER", (100, 200, 255))
            lines.append(after_bar)

        lines.append("\n" + "="*70)

        return "\n".join(lines)

    def _create_timeline_bar(self, frames, label, color):
        """Create a text-based timeline bar."""
        if not frames:
            return ""

        # Group frames into buckets of 10
        buckets = []
        for i in range(0, len(frames), 10):
            bucket = frames[i:i+10]
            avg = sum(bucket) / len(bucket)
            buckets.append(avg)

        # Create bar
        bar_chars = []
        for avg in buckets:
            if avg < 16.67:
                bar_chars.append('.')  # Good
            elif avg < 20:
                bar_chars.append('o')  # Slight drop
            elif avg < 25:
                bar_chars.append('O')  # Noticeable drop
            elif avg < 33:
                bar_chars.append('X')  # Bad (30 FPS)
            else:
                bar_chars.append('#')  # Very bad (<30 FPS)

        bar = ''.join(bar_chars)
        avg_fps = 1000 / (sum(frames) / len(frames))
        return f"  {label:8s} [{bar}] {avg_fps:.1f} FPS avg"

profiler = BeforeAfterProfiler()

# Instrument execute_turn
original_execute_turn = GraphicalRenderer.execute_turn

def profiled_execute_turn(self):
    """Execute turn with profiling."""
    profiler.start_turn_execution()

    # Call original
    original_execute_turn(self)

    profiler.end_turn_execution()

GraphicalRenderer.execute_turn = profiled_execute_turn

# Instrument main loop
original_run = GraphicalRenderer.run

def profiled_run(self):
    """Main loop with frame timing capture."""
    while self.running:
        frame_start = time.perf_counter()

        delta_time = self.clock.tick(60) / 1000.0

        # Update FPS counter
        if self.show_fps:
            current_fps = self.clock.get_fps()
            self.fps_values.append(current_fps)
            if len(self.fps_values) > 30:
                self.fps_values.pop(0)
            if len(self.fps_values) > 0:
                self.fps_display = sum(self.fps_values) / len(self.fps_values)

        self.handle_events()
        self.update(delta_time)
        self.draw()

        # Record frame time
        frame_time = (time.perf_counter() - frame_start) * 1000
        profiler.record_frame(frame_time)

    pygame.quit()

GraphicalRenderer.run = profiled_run

def main():
    """Run game with before/after profiling."""
    print("="*70)
    print("BEFORE/AFTER TURN COMPARISON PROFILER")
    print("="*70)
    print("\nThis profiler captures frame timing around turn execution:")
    print("  - 60 frames BEFORE pressing E (baseline)")
    print("  - All frames DURING turn execution")
    print("  - 60 frames AFTER turn completes (recovery)")
    print("\nPress E to execute a turn and see the comparison.")
    print("="*70 + "\n")

    # Disable blocking sleep calls in graphical mode
    from boneglaive.utils.animation_helpers import set_graphical_mode
    set_graphical_mode(True)

    # Initialize DLC system
    from boneglaive.game.dlc_manager import initialize_dlc_system
    dlc_count = initialize_dlc_system()
    print(f"DLC system initialized: {dlc_count} DLC units loaded\n")

    # Setup game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=False, map_name='lime_foyer')

    renderer = GraphicalRenderer(adapter)
    renderer.show_fps = True

    # Set up UI adapter
    ui_adapter = GraphicalUIAdapter(renderer)
    adapter.game.set_ui_reference(ui_adapter)

    # Sync units
    renderer.sync_units_from_game()

    # Add welcome messages
    renderer.combat_log.add_message("Before/After Profiler Active", "system")
    renderer.combat_log.add_message("Execute turns to see timing comparison", "system")

    print("Game started. Press E to execute turns.\n")

    # Main game loop
    try:
        renderer.run()
    except KeyboardInterrupt:
        print("\n\nProfiling stopped by user.")

    # Final summary
    if profiler.profiles:
        print(f"\n\nCaptured {len(profiler.profiles)} turn execution(s).")
    else:
        print("\n\nNo turn executions captured.")

if __name__ == "__main__":
    main()
