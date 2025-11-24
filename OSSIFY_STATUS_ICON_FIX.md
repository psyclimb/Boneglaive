# Ossify Status Icon - Fixed

## Problem
The Ossify status icon was not displaying on the MARROW CONDENSER's tile when the skill was applied, even though the icon file existed.

## Root Cause
According to CLAUDE.org documentation (lines 276-308), THREE places must be updated for status effect icons to work:

1. ✅ **Icon file** - `graphics/status_icons/ossify.svg` existed
2. ❌ **game_state.py** - Was checking for wrong attribute name (`ossified` instead of `ossify_active`)
3. ❌ **status_effects.py** - Missing STATUS_EFFECTS dictionary entry entirely

## Files Fixed

### 1. boneglaive/graphical/game_state.py (Line 129)
**Changed:**
```python
# BEFORE (incorrect attribute name)
if hasattr(game_unit, 'ossified') and game_unit.ossified:
    effects['ossify'] = True

# AFTER (correct attribute name)
if hasattr(game_unit, 'ossify_active') and game_unit.ossify_active:
    effects['ossify'] = True
```

**Why:** The OssifySkill sets `user.ossify_active = True` (marrow_condenser.py:150), but game_state.py was checking for the wrong attribute name.

### 2. boneglaive/graphical/ui/status_effects.py (Lines 181-188)
**Added:**
```python
"ossify_active": {
    "name": "Ossify",
    "type": "buff",
    "icon": "O",
    "description": "Compressed bone structure: +2 defense (+3 when upgraded), -1 movement",
    "duration_key": "ossify_duration",
    "check": lambda u: hasattr(u, 'ossify_active') and u.ossify_active
},
```

**Why:** The STATUS_EFFECTS dictionary needs an entry to display the status in the UI panel and provide tooltip information.

## How It Works (3-Part System)

### Part 1: Status Icon Flash Animation (game_state.py)
When `_get_status_effects()` detects `ossify_active` is True, it adds `'ossify': True` to the effects dict. This triggers the StatusIconFlash animation in the renderer, which:
- Loads `graphics/status_icons/ossify.svg`
- Displays it on the unit's tile
- Fades in (0.2s) → holds (0.4s) → fades out (0.3s)

### Part 2: Status Effects Panel (status_effects.py)
When a unit with Ossify is selected, the STATUS_EFFECTS dict entry provides:
- **Name:** "Ossify" (displayed in panel)
- **Type:** "buff" (green color)
- **Icon:** "O" (text fallback if SVG fails)
- **Description:** Full effect description for tooltip
- **Duration:** Displays "2 turns" from `ossify_duration` attribute

### Part 3: Icon SVG File
The icon file at `graphics/status_icons/ossify.svg` provides the visual representation.

## Verification

✅ **Syntax Check:**
- status_effects.py: OK
- game_state.py: OK

✅ **Attribute Matching:**
- Skill sets: `user.ossify_active = True` (marrow_condenser.py:150)
- game_state.py checks: `game_unit.ossify_active` ✓
- status_effects.py checks: `u.ossify_active` ✓

✅ **Duration Tracking:**
- Skill sets: `user.ossify_duration = 2` (marrow_condenser.py:151)
- status_effects.py reads: `"duration_key": "ossify_duration"` ✓

✅ **Icon File:**
- Path: graphics/status_icons/ossify.svg (2.5KB, exists)

## Expected Behavior

When Ossify is cast on a MARROW CONDENSER:

1. **Icon Flash (Immediate):**
   - Ossify icon SVG appears on unit's tile
   - Fades in over 0.2s
   - Holds for 0.4s
   - Fades out over 0.3s
   - Total flash duration: 0.9s

2. **Status Panel (When Selected):**
   - "Ossify" appears in status effects list (green, as it's a buff)
   - Shows duration: "2 turns"
   - Hover tooltip: "Compressed bone structure: +2 defense (+3 when upgraded), -1 movement"

3. **Duration Countdown:**
   - Duration decrements each turn
   - Icon flashes again each turn while active (if status system refreshes)
   - Effect automatically removed when `ossify_duration` reaches 0

## Integration Complete

All three parts of the status icon system are now properly connected:
- ✅ game_state.py: Detects status and triggers icon flash
- ✅ status_effects.py: Displays in UI panel with tooltip
- ✅ ossify.svg: Icon file exists and loads

The Ossify status icon will now display correctly when the skill is used.
