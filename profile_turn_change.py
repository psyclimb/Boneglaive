#!/usr/bin/env python3
"""
Turn Change Profiler - Detailed timing breakdown of execute_turn()

This profiler instruments the execute_turn() method to measure exactly
where time is being spent during turn transitions.

Measures:
- sync_state() calls (pre and post execution)
- Game logic execute_turn()
- initialize_next_player_turn()
- sync_units_from_game()
- Individual subsections within sync_state()

Usage:
    python profile_turn_change.py

Then play the game and press E to execute a turn. The profiler will
print a detailed breakdown showing which operations are slow.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
import time
from collections import defaultdict
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.ui_adapter import GraphicalUIAdapter

# Performance data collection
class TurnChangeProfiler:
    def __init__(self):
        self.turn_times = []
        self.current_turn_data = None

    def start_turn(self):
        """Start timing a turn execution."""
        self.current_turn_data = {
            'start_time': time.perf_counter(),
            'sections': {},
            'sync_state_calls': [],
            'total_time': 0
        }

    def record_section(self, section_name, duration_ms):
        """Record timing for a section."""
        if self.current_turn_data:
            self.current_turn_data['sections'][section_name] = duration_ms

    def record_sync_state(self, phase, duration_ms, subsections):
        """Record a sync_state call with subsection breakdown."""
        if self.current_turn_data:
            self.current_turn_data['sync_state_calls'].append({
                'phase': phase,
                'duration_ms': duration_ms,
                'subsections': subsections
            })

    def end_turn(self):
        """Finish timing the turn and store results."""
        if self.current_turn_data:
            self.current_turn_data['total_time'] = (
                time.perf_counter() - self.current_turn_data['start_time']
            ) * 1000
            self.turn_times.append(self.current_turn_data)
            self.current_turn_data = None

    def get_report(self):
        """Generate a detailed report of the last turn execution."""
        if not self.turn_times:
            return "No turn executions recorded yet."

        data = self.turn_times[-1]
        lines = []

        lines.append("\n" + "="*70)
        lines.append("TURN EXECUTION PERFORMANCE BREAKDOWN")
        lines.append("="*70)
        lines.append(f"Total Turn Time: {data['total_time']:.2f} ms")
        lines.append(f"Target: 16.67 ms (60 FPS)")
        lines.append(f"Overhead: {data['total_time'] - 16.67:.2f} ms ({(data['total_time'] / 16.67 * 100):.1f}% of budget)")
        lines.append("="*70)

        # Main sections
        lines.append("\nMAIN SECTIONS:")
        for section, duration in sorted(data['sections'].items(), key=lambda x: x[1], reverse=True):
            pct = (duration / 16.67) * 100
            flag = " *** BOTTLENECK ***" if pct > 20 else ""
            lines.append(f"  {section:40s}: {duration:7.2f} ms ({pct:5.1f}%){flag}")

        # sync_state breakdown
        lines.append("\nSYNC_STATE CALLS:")
        for i, sync_data in enumerate(data['sync_state_calls']):
            phase = sync_data['phase']
            duration = sync_data['duration_ms']
            pct = (duration / 16.67) * 100
            flag = " *** SLOW ***" if pct > 20 else ""

            lines.append(f"\n  Call {i+1} ({phase}):")
            lines.append(f"    Total: {duration:.2f} ms ({pct:.1f}%){flag}")

            if sync_data['subsections']:
                lines.append(f"    Breakdown:")
                for subsection, sub_duration in sorted(
                    sync_data['subsections'].items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    sub_pct = (sub_duration / duration) * 100
                    lines.append(f"      {subsection:30s}: {sub_duration:6.2f} ms ({sub_pct:4.1f}%)")

        lines.append("\n" + "="*70)

        # Summary and recommendations
        lines.append("\nBOTTLENECKS:")
        bottlenecks = []
        for section, duration in data['sections'].items():
            pct = (duration / 16.67) * 100
            if pct > 20:
                bottlenecks.append((section, duration, pct))

        if bottlenecks:
            for section, duration, pct in sorted(bottlenecks, key=lambda x: x[1], reverse=True):
                lines.append(f"  - {section}: {duration:.2f}ms ({pct:.1f}% of frame budget)")
        else:
            lines.append("  No major bottlenecks detected.")

        lines.append("\n" + "="*70)

        return "\n".join(lines)

profiler = TurnChangeProfiler()

# Instrument execute_turn
original_execute_turn = GraphicalRenderer.execute_turn

def profiled_execute_turn(self):
    """Instrumented execute_turn with detailed timing."""
    profiler.start_turn()

    # Motor start
    self.motor_animation.start()
    self.combat_log.add_message(
        f"Turn {self.game_adapter.game.turn} - Player {self.game_adapter.game.current_player}",
        msg_type="system"
    )

    # Clear UI state
    self.selected_unit = None
    self.selected_skill = None
    self.show_movement_range = False
    self.show_target_range = False
    self.show_skill_range = False
    self.show_astral_values = False
    self.valid_positions = []
    self.attack_positions = []
    self.skill_positions = []
    self.skill_bar.update(None, None)

    self.game_adapter.executing_turn = True

    # TIME: Pre-execution sync_state
    t_start = time.perf_counter()
    pre_events = profile_sync_state(self.game_adapter, "pre-execution")
    profiler.record_section('sync_state_pre_execution', (time.perf_counter() - t_start) * 1000)

    for event in pre_events:
        self.handle_animation_event(event)

    # TIME: Check for blocking animations
    t_start = time.perf_counter()
    from boneglaive.graphical.renderer import PRE_EXECUTION_BLOCKING_SKILLS
    has_blocking_animations = any(
        event.event_type == "skill" and
        event.kwargs.get("skill_name") in PRE_EXECUTION_BLOCKING_SKILLS
        for event in pre_events
    )
    profiler.record_section('check_blocking_animations', (time.perf_counter() - t_start) * 1000)

    if has_blocking_animations:
        # TIME: Wait for blocking animations
        t_start = time.perf_counter()
        self.flush_pending_events()

        while self.has_active_animations():
            delta_time = self.clock.tick(60) / 1000.0
            self._update_animations_only(delta_time)
            self.draw()
            pygame.display.flip()
        profiler.record_section('wait_blocking_animations', (time.perf_counter() - t_start) * 1000)

    # TIME: Snapshot status effects
    t_start = time.perf_counter()
    self.game_adapter.snapshot_status_effects()
    profiler.record_section('snapshot_status_effects', (time.perf_counter() - t_start) * 1000)

    # TIME: Game logic execute_turn
    t_start = time.perf_counter()
    self.game_adapter.game.execute_turn(ui=self.ui_adapter)
    profiler.record_section('game_execute_turn', (time.perf_counter() - t_start) * 1000)

    # TIME: Post-execution sync_state
    t_start = time.perf_counter()
    post_events = profile_sync_state(self.game_adapter, "post-execution")
    profiler.record_section('sync_state_post_execution', (time.perf_counter() - t_start) * 1000)

    for event in post_events:
        self.handle_animation_event(event)

    self.game_adapter.executing_turn = False

    # TIME: Fetch messages
    t_start = time.perf_counter()
    from boneglaive.utils.message_log import message_log
    self.combat_log.add_messages_from_game_log(message_log, count=20)
    profiler.record_section('fetch_messages', (time.perf_counter() - t_start) * 1000)

    # TIME: Local multiplayer player switch
    if self.game_adapter.game.local_multiplayer:
        t_start = time.perf_counter()
        old_player = self.game_adapter.game.current_player
        self.game_adapter.game.current_player = 3 - self.game_adapter.game.current_player

        if self.game_adapter.game.current_player == 1:
            self.game_adapter.game.turn += 1

        # TIME: Initialize next player turn (likely culprit!)
        t_init_start = time.perf_counter()
        self.game_adapter.game.initialize_next_player_turn()
        profiler.record_section('initialize_next_player_turn', (time.perf_counter() - t_init_start) * 1000)

        self.combat_log.add_message(f"Player {self.game_adapter.game.current_player}'s turn", "system")

        profiler.record_section('local_multiplayer_switch', (time.perf_counter() - t_start) * 1000)

    print(f"Turn {self.game_adapter.game.turn} - Current player: {self.game_adapter.game.current_player}\n")

    profiler.end_turn()
    print(profiler.get_report())

def profile_sync_state(adapter, phase):
    """Profile sync_state with subsection breakdown."""
    t_start = time.perf_counter()
    subsections = {}

    if not adapter.game:
        return []

    events = []

    # TIME: Unit loop
    t_loop_start = time.perf_counter()
    for unit_id, visual_unit in adapter.visual_units.items():
        game_unit = visual_unit.game_unit

        # Sample a few key checks
        if hasattr(game_unit, 'partition_shield_blocked_fatal'):
            pass  # Just checking attribute access time

    subsections['unit_loop_overhead'] = (time.perf_counter() - t_loop_start) * 1000

    # Call actual sync_state
    t_sync_start = time.perf_counter()
    events = adapter.sync_state()
    subsections['actual_sync_state'] = (time.perf_counter() - t_sync_start) * 1000

    total_duration = (time.perf_counter() - t_start) * 1000
    profiler.record_sync_state(phase, total_duration, subsections)

    return events

# Apply instrumentation
GraphicalRenderer.execute_turn = profiled_execute_turn

def main():
    """Run game with turn change profiling."""
    print("="*70)
    print("TURN CHANGE PROFILER")
    print("="*70)
    print("\nThis profiler measures turn execution performance in detail.")
    print("Play the game normally and press E to execute turns.")
    print("Each turn execution will print a detailed breakdown.\n")
    print("Look for *** BOTTLENECK *** markers (>20% of frame budget)")
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
    renderer.combat_log.add_message("Turn Change Profiler Active", "system")
    renderer.combat_log.add_message("Execute turns to see timing breakdown", "system")

    print("Game started. Press E to execute turns and see profiling data.\n")

    # Main game loop
    renderer.run()

if __name__ == "__main__":
    main()
