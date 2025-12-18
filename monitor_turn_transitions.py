#!/usr/bin/env python3
"""
Real-time Turn Transition Monitor

Lightweight monitoring that runs during normal gameplay and alerts
when turn transitions cause frame drops.

Tracks:
- Baseline FPS during normal gameplay
- FPS during turn execution
- Alerts when FPS drops below threshold
- Minimal performance impact

Usage:
    python monitor_turn_transitions.py

The monitor runs in the background and prints alerts only when
performance issues are detected during turn changes.
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

class TurnTransitionMonitor:
    """Monitors FPS during turn transitions."""

    def __init__(self, alert_threshold=40):
        self.alert_threshold = alert_threshold  # Alert if FPS drops below this
        self.baseline_fps = deque(maxlen=120)  # 2 seconds of baseline
        self.turn_fps = deque(maxlen=60)  # 1 second during turn
        self.in_turn_execution = False
        self.turn_start_time = None
        self.turn_count = 0
        self.alerts = []

    def update_baseline(self, fps):
        """Record baseline FPS during normal gameplay."""
        if not self.in_turn_execution:
            self.baseline_fps.append(fps)

    def start_turn_execution(self):
        """Mark the start of turn execution."""
        self.in_turn_execution = True
        self.turn_start_time = time.time()
        self.turn_fps.clear()
        self.turn_count += 1

    def update_turn_fps(self, fps):
        """Record FPS during turn execution."""
        if self.in_turn_execution:
            self.turn_fps.append(fps)

    def end_turn_execution(self):
        """Mark the end of turn execution and check for issues."""
        if not self.in_turn_execution:
            return

        self.in_turn_execution = False
        turn_duration = time.time() - self.turn_start_time

        # Calculate stats
        baseline_avg = sum(self.baseline_fps) / len(self.baseline_fps) if self.baseline_fps else 60
        turn_avg = sum(self.turn_fps) / len(self.turn_fps) if self.turn_fps else 60
        turn_min = min(self.turn_fps) if self.turn_fps else 60

        fps_drop = baseline_avg - turn_avg
        drop_pct = (fps_drop / baseline_avg) * 100 if baseline_avg > 0 else 0

        # Check if turn caused significant FPS drop
        if turn_avg < self.alert_threshold or drop_pct > 25:
            alert = {
                'turn': self.turn_count,
                'duration': turn_duration,
                'baseline_avg': baseline_avg,
                'turn_avg': turn_avg,
                'turn_min': turn_min,
                'fps_drop': fps_drop,
                'drop_pct': drop_pct
            }
            self.alerts.append(alert)
            self.print_alert(alert)

    def print_alert(self, alert):
        """Print an alert about poor turn performance."""
        print("\n" + "!"*70)
        print("*** TURN TRANSITION PERFORMANCE ALERT ***")
        print("!"*70)
        print(f"Turn #{alert['turn']}")
        print(f"Duration: {alert['duration']:.2f} seconds")
        print(f"Baseline FPS: {alert['baseline_avg']:.1f}")
        print(f"Turn Avg FPS: {alert['turn_avg']:.1f}")
        print(f"Turn Min FPS: {alert['turn_min']:.1f}")
        print(f"FPS Drop: {alert['fps_drop']:.1f} ({alert['drop_pct']:.1f}%)")

        if alert['turn_avg'] < 30:
            print("\nSEVERITY: CRITICAL - Game is noticeably stuttering")
        elif alert['turn_avg'] < 45:
            print("\nSEVERITY: HIGH - Noticeable frame drops")
        else:
            print("\nSEVERITY: MODERATE - Minor frame drops")

        print("!"*70 + "\n")

    def get_summary(self):
        """Get summary statistics."""
        if not self.alerts:
            return "No performance issues detected during turn transitions."

        lines = []
        lines.append("\n" + "="*70)
        lines.append("TURN TRANSITION PERFORMANCE SUMMARY")
        lines.append("="*70)
        lines.append(f"Total turns executed: {self.turn_count}")
        lines.append(f"Problematic turns: {len(self.alerts)}")
        lines.append(f"Success rate: {((self.turn_count - len(self.alerts)) / self.turn_count * 100):.1f}%")
        lines.append("\nProblematic Turns:")

        for alert in self.alerts:
            lines.append(f"  Turn #{alert['turn']}: {alert['turn_avg']:.1f} FPS (drop: {alert['drop_pct']:.1f}%)")

        lines.append("="*70)
        return "\n".join(lines)

monitor = TurnTransitionMonitor(alert_threshold=45)

# Instrument execute_turn to track transitions
original_execute_turn = GraphicalRenderer.execute_turn

def monitored_execute_turn(self):
    """Execute turn with monitoring."""
    monitor.start_turn_execution()

    # Call original method
    original_execute_turn(self)

    monitor.end_turn_execution()

GraphicalRenderer.execute_turn = monitored_execute_turn

# Instrument main loop to track FPS
original_run = GraphicalRenderer.run

def monitored_run(self):
    """Main loop with FPS monitoring."""
    while self.running:
        delta_time = self.clock.tick(60) / 1000.0

        # Update FPS counter
        if self.show_fps:
            current_fps = self.clock.get_fps()
            self.fps_values.append(current_fps)
            if len(self.fps_values) > 30:
                self.fps_values.pop(0)
            if len(self.fps_values) > 0:
                self.fps_display = sum(self.fps_values) / len(self.fps_values)

        # Track FPS for monitoring
        current_fps = self.clock.get_fps()
        if current_fps > 0:  # Avoid recording startup frames
            monitor.update_baseline(current_fps)
            monitor.update_turn_fps(current_fps)

        self.handle_events()
        self.update(delta_time)
        self.draw()

    pygame.quit()

GraphicalRenderer.run = monitored_run

def main():
    """Run game with turn transition monitoring."""
    print("="*70)
    print("TURN TRANSITION MONITOR")
    print("="*70)
    print("\nThis monitor tracks FPS during turn transitions.")
    print("It runs silently and alerts only when issues are detected.")
    print(f"Alert threshold: {monitor.alert_threshold} FPS")
    print("\nPlay normally. Alerts will print when turn FPS drops.\n")
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
    renderer.combat_log.add_message("Turn Transition Monitor Active", "system")
    renderer.combat_log.add_message("Monitoring for performance issues...", "system")

    print("Game started. Monitor is active and watching for issues.\n")

    # Main game loop
    try:
        renderer.run()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")

    # Print summary
    print(monitor.get_summary())

if __name__ == "__main__":
    main()
