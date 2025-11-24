# Partition Hit Animation - Fix Applied

## Issue
The PartitionHitAnimation was not triggering when Partition absorbed damage.

## Root Cause Analysis

**Problem:** The hook in `units.py` was checking for attributes on the wrong object.

**Incorrect code was looking for:**
- `self._game.ui.camera` ❌ (doesn't exist on ui_adapter)
- `self._game.ui.units_list` ❌ (doesn't exist on ui_adapter)
- `self._game.ui.active_animations` ❌ (doesn't exist on ui_adapter)

**Correct locations:**
- `self._game.ui.renderer.camera` ✅
- `self._game.ui.renderer.active_animations` ✅
- Use `renderer._find_animated_unit_by_game_unit(self)` ✅ (existing method)

## Architecture Discovery

```
self._game.ui (GraphicalUIAdapter)
    └── .renderer (GraphicalRenderer)
        ├── .camera (Camera)
        ├── .active_animations (list)
        └── ._find_animated_unit_by_game_unit(unit) (method)
```

## Fix Applied

### File: boneglaive/game/units.py (lines 709-739)

**Changed:**
1. Store `renderer = self._game.ui.renderer` first
2. Check for `hasattr(renderer, 'camera')` instead of `hasattr(ui, 'camera')`
3. Use `renderer._find_animated_unit_by_game_unit(self)` instead of manual loop
4. Append to `renderer.active_animations` instead of `ui.active_animations`
5. Pass `renderer.camera` instead of `ui.camera`
6. Added better error logging with exception details

**Before:**
```python
if hasattr(self._game.ui, 'camera') and self._game.ui.camera:
    # Find AnimatedUnit manually
    if hasattr(self._game.ui, 'units_list'):
        for aunit in self._game.ui.units_list:
            if aunit.unit_id == self.id:
                animated_unit = aunit
                break

    if animated_unit:
        hit_anim = PartitionHitAnimation(animated_unit, self._game.ui.camera)
        if hasattr(self._game.ui, 'active_animations'):
            self._game.ui.active_animations.append(hit_anim)
```

**After:**
```python
renderer = self._game.ui.renderer

if hasattr(renderer, 'camera') and hasattr(renderer, 'active_animations') and renderer.camera:
    # Use existing method
    animated_unit = renderer._find_animated_unit_by_game_unit(self)

    if animated_unit:
        hit_anim = PartitionHitAnimation(animated_unit, renderer.camera)
        renderer.active_animations.append(hit_anim)
        logger.debug(f"PARTITION HIT: Spawned graphical animation for {self.get_display_name()}")
    else:
        logger.debug(f"PARTITION HIT: Could not find AnimatedUnit for {self.get_display_name()}")
```

## Benefits of Fix

1. **Uses existing infrastructure:** `_find_animated_unit_by_game_unit()` already exists
2. **Correct object references:** All attributes are on `renderer`, not `ui`
3. **Better error handling:** Separate exceptions for import vs runtime errors
4. **Proper logging:** Debug messages for each failure case
5. **Cleaner code:** No manual loop through units_list

## Verification

✅ **Syntax check:** units.py compiles without errors
✅ **Correct architecture:** Uses renderer.camera and renderer.active_animations
✅ **Existing method:** Uses renderer._find_animated_unit_by_game_unit()
✅ **Error handling:** Catches both ImportError and general Exception

## Testing Checklist

Test the animation now triggers:
- [ ] Cast Partition on an ally
- [ ] Have that ally take damage
- [ ] Verify ripple + shimmer animation appears
- [ ] Check debug log shows "PARTITION HIT: Spawned graphical animation for [unit]"
- [ ] Test multiple hits in same turn
- [ ] Verify no errors in console

## Debug Logging

If animation still doesn't appear, check logs for:
- `PARTITION HIT: Spawned graphical animation for X` → Animation created successfully
- `PARTITION HIT: Could not find AnimatedUnit for X` → Unit lookup failed
- `Could not import PartitionHitAnimation` → Import issue
- `PARTITION HIT: Error spawning animation` → Runtime error

## Files Modified

1. **boneglaive/game/units.py** (lines 709-739)
   - Fixed attribute access paths
   - Used existing renderer methods
   - Improved error handling

## Status

✅ **Fix Applied:** Hook now correctly accesses renderer attributes
✅ **Verified:** Syntax check passes
✅ **Ready for Testing:** Animation should now trigger on PRT damage

---

**Root Issue:** Architectural misunderstanding - UI adapter vs Renderer
**Solution:** Use `renderer.camera`, `renderer.active_animations`, `renderer._find_animated_unit_by_game_unit()`
**Impact:** Animation will now spawn correctly when Partition absorbs damage
