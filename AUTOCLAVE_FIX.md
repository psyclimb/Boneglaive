# Autoclave Animation Fix

**Date**: 2025-11-22
**Issue**: Autoclave triggered but animation didn't display

---

## Root Cause Analysis

### The Problem
The original implementation tried to **trigger Autoclave a second time** in `game_state.py`, but Autoclave had already been triggered by the game logic during turn execution.

**Original (Broken) Logic:**
```python
# In game_state.py sync_state()
if hp_delta < 0:  # Damage taken
    if game_unit.type == UnitType.GLAIVEMAN:
        if self.game.try_trigger_autoclave(game_unit):  # ❌ Already activated!
            # Queue animation
```

**Why it failed:**
1. Player executes turn (presses E)
2. Game logic resolves attacks → GLAIVEMAN takes damage
3. **Game logic calls `try_trigger_autoclave()` → Autoclave executes, `activated = True`**
4. Turn completes
5. `sync_state()` runs and detects HP change
6. Tries to call `try_trigger_autoclave()` **again**
7. Returns `False` because `activated == True` (already used)
8. No animation event queued ❌

---

## The Solution

**Detect passive skill activation state changes** instead of trying to trigger it again.

### Implementation

**1. Track Passive Skill State (`VisualUnit`)**
```python
class VisualUnit:
    def __init__(self, game_unit, animated_unit):
        # ... existing fields ...
        self.last_passive_activated = self._get_passive_activation_state(game_unit)

    def _get_passive_activation_state(self, game_unit):
        """Get current activation state of passive skill."""
        if hasattr(game_unit, 'passive_skill') and game_unit.passive_skill:
            if hasattr(game_unit.passive_skill, 'activated'):
                return game_unit.passive_skill.activated
        return False
```

**2. Detect State Change (`sync_state()`)**
```python
# In sync_state(), for each unit:
current_passive_activated = visual_unit._get_passive_activation_state(game_unit)
if current_passive_activated and not visual_unit.last_passive_activated:
    # Passive skill just activated!
    passive_name = game_unit.passive_skill.name
    events.append(AnimationEvent(
        "skill",
        source_unit=game_unit,
        skill_name=passive_name.upper(),  # "AUTOCLAVE"
        skill_target=None
    ))
    visual_unit.last_passive_activated = True
```

### How It Works Now

1. **Turn executes** → Game logic triggers Autoclave → `activated = True`
2. **`sync_state()` runs** → Detects `activated` changed from `False` to `True`
3. **Queues animation event** → `AnimationEvent("skill", skill_name="AUTOCLAVE")`
4. **Renderer processes event** → Calls `AnimationFactory.create_animation("AUTOCLAVE")`
5. **Animation plays** → 4 cross beams expand, steam and glaives ✅

---

## Files Modified

1. **`boneglaive/graphical/game_state.py`**:
   - Added `last_passive_activated` field to `VisualUnit.__init__()`
   - Added `_get_passive_activation_state()` helper method
   - Removed incorrect `try_trigger_autoclave()` call
   - Added passive skill activation detection in `sync_state()`

2. **`boneglaive/graphical/renderer.py`**:
   - Added debug prints to skill event handling (for diagnosis)

---

## Key Insight

**Don't try to trigger game logic events from the renderer layer!**

The graphical renderer should:
- ✅ **Detect** changes in game state
- ✅ **Queue** visual animations for those changes
- ❌ **NOT trigger** game logic actions

The game logic (engine.py) handles all gameplay:
- ✅ Skill activation
- ✅ Damage/healing
- ✅ Passive skill triggers

The graphical layer (game_state.py) observes state:
- ✅ Detects HP changes
- ✅ Detects position changes
- ✅ Detects skill activations (including passives)
- ✅ Queues animations for visual feedback

---

## Testing

**Expected behavior:**
1. Damage GLAIVEMAN to ≤30% HP with enemies in range
2. Console shows:
   ```
   [GameState] Passive skill 'Autoclave' activated for [GLAIVEMAN_NAME]!
   [Renderer] Processing skill event: AUTOCLAVE from [GLAIVEMAN_NAME]
   [Renderer] Found caster visual unit at (X, Y)
   [Renderer] Creating animation for AUTOCLAVE...
   [AnimationFactory] Created AutoclaveAnimation for AUTOCLAVE
   [Animation] Successfully triggered AUTOCLAVE animation
   ```
3. **Animation displays**: Central flash + 4 cross beams

---

## Status

✅ **Fixed** - Autoclave animation now triggers properly by detecting passive skill activation state changes.
