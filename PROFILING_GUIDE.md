# Performance Profiling Guide for Turn Change Stutter

## Problem
Frame rate drops and stuttering occur when pressing E to execute turns in the graphical version of Boneglaive.

## Tools Created

Three profiling tools have been created to help identify the bottleneck:

### 1. Turn Change Profiler (`profile_turn_change.py`)
**Purpose**: Detailed breakdown of exactly where time is spent during `execute_turn()`

**What it measures**:
- sync_state() calls (pre and post execution)
- Game logic execute_turn()
- initialize_next_player_turn()
- snapshot_status_effects()
- Each subsection with millisecond precision

**When to use**: When you want to know which specific function is causing the slowdown

**Output example**:
```
TURN EXECUTION PERFORMANCE BREAKDOWN
======================================================================
Total Turn Time: 89.45 ms
Target: 16.67 ms (60 FPS)
Overhead: 72.78 ms (536.7% of budget)

MAIN SECTIONS:
  sync_state_pre_execution                : 24.12 ms ( 144.7%) *** BOTTLENECK ***
  game_execute_turn                       : 18.45 ms ( 110.7%) *** BOTTLENECK ***
  initialize_next_player_turn             : 32.88 ms ( 197.2%) *** BOTTLENECK ***
  sync_state_post_execution               : 11.23 ms (  67.4%)
```

**Usage**:
```bash
cd /home/user/boneglaive
python profile_turn_change.py
# Play the game, press E to execute a turn
# Report prints immediately after each turn
```

---

### 2. Real-time Turn Transition Monitor (`monitor_turn_transitions.py`)
**Purpose**: Lightweight background monitoring that alerts only when problems occur

**What it measures**:
- Baseline FPS during normal gameplay
- FPS during turn execution
- Automatic alerts when FPS drops below threshold (default: 45 FPS)

**When to use**: When you want to play naturally and be notified of issues without constant output

**Output example**:
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
*** TURN TRANSITION PERFORMANCE ALERT ***
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Turn #3
Duration: 1.47 seconds
Baseline FPS: 59.8
Turn Avg FPS: 32.4
Turn Min FPS: 18.2
FPS Drop: 27.4 (45.8%)

SEVERITY: CRITICAL - Game is noticeably stuttering
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

**Usage**:
```bash
cd /home/user/boneglaive
python monitor_turn_transitions.py
# Plays silently, prints alerts only when FPS drops
```

---

### 3. Before/After Turn Comparison (`profile_before_after_turn.py`)
**Purpose**: Shows how frame times change before, during, and after turn execution

**What it measures**:
- 60 frames BEFORE pressing E (baseline)
- All frames DURING turn execution
- 60 frames AFTER turn completes (recovery)
- Statistical comparison (min/max/P95/P99)

**When to use**: When you want to see the full picture of how turns impact performance

**Output example**:
```
BEFORE/DURING/AFTER TURN COMPARISON - Turn #1
======================================================================

PHASE STATISTICS (frame times in milliseconds):
----------------------------------------------------------------------

BEFORE (baseline):
  Frames: 60
  Average: 16.45 ms (60.8 FPS)
  P95: 17.23 ms
  STATUS: OK (consistent 60 FPS)

DURING (turn execution):
  Frames: 87
  Average: 38.92 ms (25.7 FPS)
  Max: 112.34 ms
  STATUS: *** BELOW 60 FPS *** (avg 133.4% over budget)

AFTER (recovery):
  Frames: 60
  Average: 16.78 ms (59.6 FPS)
  STATUS: Full recovery to baseline

IMPACT ANALYSIS:
----------------------------------------------------------------------
Turn Execution Impact:
  Frame time increased by: 2.37x
  FPS drop: 35.1 FPS
  SEVERITY: *** CRITICAL *** (>2x slowdown)

FRAME TIME TIMELINE (each bar = 10 frames):
  BEFORE   [......] 60.8 FPS avg
  DURING   [OOXXXXX##] 25.7 FPS avg
  AFTER    [......] 59.6 FPS avg
```

**Usage**:
```bash
cd /home/user/boneglaive
python profile_before_after_turn.py
# Press E to execute turn, report prints immediately
```

---

## How to Use These Tools

### Step 1: Confirm the Problem Exists
```bash
python monitor_turn_transitions.py
```
Play a few turns. If you see alerts, the problem is confirmed.

### Step 2: Identify the Bottleneck
```bash
python profile_turn_change.py
```
Execute one turn and look at the "MAIN SECTIONS" output. Find which functions are marked `*** BOTTLENECK ***` (>20% of 16.67ms budget).

### Step 3: Understand the Impact
```bash
python profile_before_after_turn.py
```
See the full before/during/after comparison to understand severity and recovery time.

---

## Expected Findings

Based on code review, likely culprits are:

1. **sync_state()** - Called twice per turn, 534 lines of unit checking
2. **initialize_next_player_turn()** - Loops through ALL units applying passive skills
3. **sync_units_from_game()** - Rebuilds entire visual unit mapping
4. **Sprite loading** - If DLC units trigger SVG reloads

The profilers will definitively show which one(s) are causing the issue.

---

## Interpreting Results

### Frame Budget
- **60 FPS = 16.67ms per frame**
- Operations taking >20% of budget (>3.33ms) are concerning
- Operations taking >100% of budget (>16.67ms) will drop frames

### Severity Levels
- **CRITICAL**: >2x slowdown, <30 FPS during turns
- **HIGH**: >1.5x slowdown, 30-45 FPS during turns
- **MODERATE**: >1.2x slowdown, 45-55 FPS during turns
- **LOW**: <1.2x slowdown, minimal visible impact

---

## Next Steps After Profiling

Once you identify the bottleneck(s), potential fixes:

1. **If sync_state() is slow**: Skip redundant checks, cache state
2. **If initialize_next_player_turn() is slow**: Only apply passives to active player's units
3. **If sync_units_from_game() is slow**: Do incremental updates instead of full rebuild
4. **If sprite loading is slow**: Pre-load and cache all sprites at startup

The profiling data will guide which optimization to implement first.

---

## Notes

- All tools are non-invasive and use monkey-patching
- Minimal performance overhead (profilers themselves add <1ms)
- Tools can be run on any map with any units
- Output is human-readable with clear severity indicators

---

Generated: 2025-12-16
