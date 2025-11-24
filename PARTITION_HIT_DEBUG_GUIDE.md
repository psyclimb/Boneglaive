# Partition Hit Animation - Debug Output Guide

## Overview
Comprehensive debug output has been added to help diagnose why the PartitionHitAnimation is not triggering.

## How to Test

1. Run the graphical game: `python run_graphical.py`
2. Cast Partition (P) on an ally
3. Have that ally take damage from an enemy attack
4. **Watch the terminal output** - you'll see a debug block

## What to Look For

When Partition absorbs damage, you'll see output like this:

```
============================================================
[PARTITION HIT DEBUG] Unit: [Unit Name]
[PARTITION HIT DEBUG] PRT absorbed: [X] damage
[PARTITION HIT DEBUG] Has _game: True/False
[PARTITION HIT DEBUG] Has ui: True/False
[PARTITION HIT DEBUG] Got renderer: [ClassName]
[PARTITION HIT DEBUG] Has camera: True/False
[PARTITION HIT DEBUG] Has active_animations: True/False
[PARTITION HIT DEBUG] Camera value: [Camera object or N/A]
```

## Debug Output Interpretation

### Step 1: Basic Checks
```
[PARTITION HIT DEBUG] Unit: UNIT_NAME
[PARTITION HIT DEBUG] PRT absorbed: 1 damage
[PARTITION HIT DEBUG] Has _game: True
[PARTITION HIT DEBUG] Has ui: True
```

**What this means:**
- ✅ Partition is absorbing damage
- ✅ Game and UI objects exist
- ❌ If any are False, the damage system isn't set up correctly

### Step 2: Renderer Checks
```
[PARTITION HIT DEBUG] Got renderer: GraphicalRenderer
[PARTITION HIT DEBUG] Has camera: True
[PARTITION HIT DEBUG] Has active_animations: True
[PARTITION HIT DEBUG] Camera value: <boneglaive.graphical.camera.Camera object at 0x...>
```

**What this means:**
- ✅ Graphical renderer is active
- ✅ Camera exists
- ✅ active_animations list exists

**If you see:**
```
[PARTITION HIT DEBUG] ASCII MODE - using old animation
```
- ❌ Means graphical mode not detected (missing camera or active_animations)
- ❌ Will fall back to ASCII bracket animation

### Step 3: Graphical Mode
```
[PARTITION HIT DEBUG] ✓ GRAPHICAL MODE DETECTED
[PARTITION HIT DEBUG] ✓ Imported PartitionHitAnimation
```

**What this means:**
- ✅ Graphical renderer confirmed
- ✅ Animation class imported successfully

**If you see:**
```
[PARTITION HIT DEBUG] ✗ Import error: [error message]
```
- ❌ Python import failed (file path issue or syntax error)

### Step 4: AnimatedUnit Lookup
```
[PARTITION HIT DEBUG] AnimatedUnit found: True
[PARTITION HIT DEBUG]   - AnimatedUnit: UNIT_NAME at (X, Y)
```

**What this means:**
- ✅ Found the graphical representation of the unit

**If you see:**
```
[PARTITION HIT DEBUG] AnimatedUnit found: False
[PARTITION HIT DEBUG] ✗ AnimatedUnit not found for UNIT_NAME
```
- ❌ The unit doesn't have a graphical AnimatedUnit
- ❌ Could mean unit was created after renderer initialization

### Step 5: Animation Creation
```
[PARTITION HIT DEBUG] Creating PartitionHitAnimation...
[PARTITION HIT DEBUG] ✓ Animation created: <boneglaive.graphical.animations.derelictionist.PartitionHitAnimation object at 0x...>
```

**What this means:**
- ✅ Animation object constructed successfully

**If you see:**
```
[PARTITION HIT DEBUG] ✗ Exception: [error type]: [error message]
[Full traceback...]
```
- ❌ Animation constructor failed
- Check the traceback for details (coordinate conversion error, etc.)

### Step 6: Adding to Active Animations
```
[PARTITION HIT DEBUG] ✓ Added to active_animations
[PARTITION HIT DEBUG]   - Before count: 0
[PARTITION HIT DEBUG]   - After count: 1
[PARTITION HIT DEBUG] ✓✓✓ SUCCESS - Animation should be visible! ✓✓✓
```

**What this means:**
- ✅ Animation successfully added to renderer's animation list
- ✅ Count increased by 1
- ✅ **Animation SHOULD be visible on screen!**

## Common Failure Scenarios

### Scenario A: No Debug Output at All
```
(No output in terminal when unit takes damage)
```
**Diagnosis:**
- Partition is not actually absorbing damage
- Check if unit has `prt > 0` (Partition status active)
- Check if damage is being dealt (try without Partition first)

### Scenario B: ASCII Mode Detected
```
[PARTITION HIT DEBUG] ASCII MODE - using old animation
```
**Diagnosis:**
- `renderer.camera` is None or doesn't exist
- `renderer.active_animations` doesn't exist
- Running in ASCII mode accidentally

### Scenario C: AnimatedUnit Not Found
```
[PARTITION HIT DEBUG] AnimatedUnit found: False
```
**Diagnosis:**
- `renderer._find_animated_unit_by_game_unit()` returning None
- Unit's ID mismatch between game unit and animated unit
- Unit created after renderer initialized

### Scenario D: Success But No Visual
```
[PARTITION HIT DEBUG] ✓✓✓ SUCCESS - Animation should be visible! ✓✓✓
(But you don't see it on screen)
```
**Diagnosis:**
- Animation is being added but not rendering
- Check if animations are being updated/drawn in render loop
- Check if animation.update() returning False immediately
- Check if animation.draw() is being called

## What to Report Back

Please provide the **complete debug output** from the terminal when Partition takes damage, especially:

1. All lines between the `========` markers
2. Any error messages or tracebacks
3. Whether you see "SUCCESS" message
4. Whether you see any visual effect (even if wrong)

## Example Good Output

```
============================================================
[PARTITION HIT DEBUG] Unit: DERELICTIONIST
[PARTITION HIT DEBUG] PRT absorbed: 2 damage
[PARTITION HIT DEBUG] Has _game: True
[PARTITION HIT DEBUG] Has ui: True
[PARTITION HIT DEBUG] Got renderer: GraphicalRenderer
[PARTITION HIT DEBUG] Has camera: True
[PARTITION HIT DEBUG] Has active_animations: True
[PARTITION HIT DEBUG] Camera value: <boneglaive.graphical.camera.Camera object at 0x7f8a4c2b3e50>
[PARTITION HIT DEBUG] ✓ GRAPHICAL MODE DETECTED
[PARTITION HIT DEBUG] ✓ Imported PartitionHitAnimation
[PARTITION HIT DEBUG] AnimatedUnit found: True
[PARTITION HIT DEBUG]   - AnimatedUnit: DERELICTIONIST at (5, 8)
[PARTITION HIT DEBUG] Creating PartitionHitAnimation...
[PARTITION HIT DEBUG] ✓ Animation created: <boneglaive.graphical.animations.derelictionist.PartitionHitAnimation object at 0x7f8a4c2b3f80>
[PARTITION HIT DEBUG] ✓ Added to active_animations
[PARTITION HIT DEBUG]   - Before count: 0
[PARTITION HIT DEBUG]   - After count: 1
[PARTITION HIT DEBUG] ✓✓✓ SUCCESS - Animation should be visible! ✓✓✓
============================================================
```

This would indicate everything worked - if you still don't see animation, the problem is in the render loop.

## Next Steps

Based on the debug output you provide, I can:
1. Identify exactly where the process is failing
2. Check if the issue is in animation creation or rendering
3. Add more specific debugging if needed
4. Fix the actual problem once identified

---

**Status:** Debug output added to units.py lines 709-775
**Test:** Cast Partition on ally, have ally take damage, check terminal
**Report:** Send complete debug output between ======== markers
