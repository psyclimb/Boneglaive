# Partition Hit Animation - FINAL FIX

## Root Cause Discovered

The debug output revealed the actual problem:

```
[PARTITION HIT DEBUG] Has ui: False
[PARTITION HIT DEBUG] ✗ No renderer found
```

**Issue:** `game.ui` was **never set** in the graphical version!

## Architecture Problem

The flow was:
1. ✅ Units have `_game` reference (set via `unit.set_game_reference(game)`)
2. ✅ Game has `set_ui_reference(ui)` method
3. ❌ **But `game.set_ui_reference()` was never called in graphical initialization!**

Result: `self._game.ui` was `None`, so the hook couldn't access the renderer.

## The Fix

### File: run_graphical.py (lines 55-59)

**Added after renderer creation:**
```python
# Create UI adapter and set it on the game for animations
from boneglaive.graphical.ui_adapter import GraphicalUIAdapter
ui_adapter = GraphicalUIAdapter(renderer)
adapter.game.set_ui_reference(ui_adapter)
print("Set UI reference on game for animations")
```

**Why this works:**
1. Creates `GraphicalUIAdapter` with the renderer
2. Calls `game.set_ui_reference(ui_adapter)` - sets `game.ui`
3. Now `unit._game.ui` is not None!
4. Now `unit._game.ui.renderer` exists!
5. Animation hook can access `renderer.camera` and `renderer.active_animations`

## Verification Flow

With the fix, the debug output should now show:
```
[PARTITION HIT DEBUG] Has ui: True
[PARTITION HIT DEBUG] Got renderer: GraphicalRenderer
[PARTITION HIT DEBUG] Has camera: True
[PARTITION HIT DEBUG] Has active_animations: True
[PARTITION HIT DEBUG] ✓ GRAPHICAL MODE DETECTED
[PARTITION HIT DEBUG] ✓✓✓ SUCCESS - Animation should be visible! ✓✓✓
```

## Why This Wasn't Caught Earlier

The graphical version was developed separately from the ASCII version:
- ASCII version: UI is created first, then passed to Game
- Graphical version: Game created standalone, renderer created separately
- The missing link: Never connected them with `set_ui_reference()`

## Files Modified

1. **run_graphical.py** (lines 55-59)
   - Import GraphicalUIAdapter
   - Create ui_adapter instance
   - Call `adapter.game.set_ui_reference(ui_adapter)`

## Impact

This fix enables **all** animation hooks that depend on `unit._game.ui`:
- ✅ Partition hit animation (our current fix)
- ✅ Any future unit-triggered animations
- ✅ Dissociation animation (fatal damage block)
- ✅ Any other PRT-related visual effects

## Testing

Run the graphical game and:
1. Cast Partition on an ally
2. Have that ally take damage
3. **Check terminal** - should now see "SUCCESS" message
4. **Check screen** - should see blue ripple + shimmer animation

Expected terminal output:
```
Set UI reference on game for animations
...
[PARTITION HIT DEBUG] ✓✓✓ SUCCESS - Animation should be visible! ✓✓✓
```

## Clean Up Needed (Optional)

Once confirmed working, the extensive debug output can be removed or reduced to just:
```python
logger.debug(f"PARTITION HIT: Spawned graphical animation for {self.get_display_name()}")
```

---

**Root Cause:** `game.ui` never set in graphical initialization
**Solution:** Call `game.set_ui_reference(ui_adapter)` in `run_graphical.py`
**Status:** ✅ Ready to test - animation should now trigger!
