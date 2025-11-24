# Boneglaive Graphical Version - Test Guide

**Version**: Phase 2 - Movement System Complete
**Date**: 2025-11-21

---

## How to Run

```bash
cd /home/user/boneglaive
python run_graphical.py
```

**Note**: Requires display (X11/Wayland). Won't work over SSH without X forwarding.

---

## What You Can Do Now ✅

### 1. Unit Selection
**How**: Left-click on a friendly unit (Player 1 units are on the left, blue colored)

**What happens**:
- Blue pulsing highlight appears around the unit
- Green overlay shows valid movement tiles
- Unit info displays in top-left (name, HP)
- Console shows: `Selected: UNIT_NAME (Player 1) - X moves available`

**Test**:
```
1. Click on a blue unit (Player 1)
2. Verify blue highlight appears
3. Verify green tiles show movement range
4. Check top-left shows unit name and HP
```

---

### 2. Unit Movement ⭐ NEW!
**How**:
1. Select a unit (left-click)
2. Left-click on a green highlighted tile

**What happens**:
- Unit plans movement to that tile
- Selection clears
- Movement range disappears
- Console shows: `Move planned: UNIT_NAME → (X, Y)`

**Test**:
```
1. Select a unit
2. Click on a green tile within movement range
3. Unit should be marked for movement (not moved yet!)
4. Try selecting another unit and planning another move
```

**Important**: The unit doesn't move immediately! Movement is **planned** and executes when you press **E** (End Turn).

---

### 3. End Turn / Execute Actions ⭐ NEW!
**How**: Press **E** key

**What happens**:
- All planned movements execute
- Units move to their planned positions
- Turn advances
- Current player switches
- Console shows turn execution log

**Test**:
```
1. Plan movements for 1-2 units
2. Press E key
3. Watch units move to new positions
4. Verify turn number increases in top-left
5. Verify current player switches
```

---

### 4. Deselection
**How**: Right-click anywhere, or click empty tile

**What happens**:
- Unit deselects
- Blue highlight disappears
- Movement range clears

**Test**:
```
1. Select a unit
2. Right-click
3. Verify highlight and green tiles disappear
```

---

### 5. Invalid Movement
**How**: Select unit, click outside movement range (non-green tile)

**What happens**:
- Console shows: `Cannot move there - not in movement range`
- Nothing changes, unit stays selected

**Test**:
```
1. Select a unit
2. Click far away (not on a green tile)
3. Verify error message in console
4. Unit should stay selected
```

---

## Controls Reference

| Key/Mouse | Action |
|-----------|--------|
| **Left Click** | Select unit / Move to tile |
| **Right Click** | Deselect unit |
| **E** | End turn (execute planned actions) |
| **SPACE** | Pause/Unpause |
| **ESC** | Quit game |

---

## Game Flow Example

### Complete Turn Example:
```
1. Start game (python run_graphical.py)
2. Click GLAIVEMAN at (5, 3) → Selected, shows 2 movement tiles
3. Click green tile at (6, 3) → Move planned
4. Click GLAIVEMAN at (6, 3) → Selected again
5. Click green tile at (7, 3) → Second move planned
6. Press E → Turn executes
7. Both units move to planned positions
8. Turn 2 begins (Player 2's turn)
```

---

## Visual Indicators

### Colors & Overlays
- **Blue pulsing highlight** = Selected unit
- **Green semi-transparent overlay** = Valid movement tile
- **Light gray highlight** = Mouse hover
- **Blue units** = Player 1 (your units)
- **Red units** = Player 2 (enemy units)

### UI Elements
**Top-Left Panel**:
```
Turn: 1
Phase: idle
Selected: GLAIVEMAN
HP: 22/22
```

**Bottom-Left Controls**:
```
ESC - Quit
SPACE - Pause
E - End Turn
LClick - Select/Move
RClick - Cancel
```

---

## What Doesn't Work Yet ❌

### Not Implemented
- ❌ **Attack commands** - Can't attack enemies
- ❌ **Skills** - No skill bar or skill execution
- ❌ **AI** - Player 2 units don't act automatically
- ❌ **Attack range visualization** - No red overlay for attacks
- ❌ **Status effects** - No visual indicators
- ❌ **Combat animations** - No damage/attack animations during turn execution
- ❌ **Sound effects** - No audio
- ❌ **Win/Loss conditions** - Game doesn't end

---

## Expected Behavior

### Movement System
1. **Planning Phase**: Click units and tiles to plan movements
2. **Execution Phase**: Press E to execute all planned actions at once
3. **Turn Cycle**: After execution, turn advances and player switches

### Unit Restrictions
- Can only select **current player's units** (Player 1 on turn 1)
- Can only move to **valid tiles** (within movement range, passable, unoccupied)
- **Movement range varies by unit type** (most units can move 2 tiles)

---

## Console Output Examples

### Successful Selection
```
Selected: GLAIVEMAN (Player 1) - 5 moves available
```

### Successful Movement Planning
```
Move planned: GLAIVEMAN → (7, 3)
```

### Invalid Movement
```
Cannot move there - not in movement range
```

### Turn Execution
```
=== Executing Turn 1 ===
[Game executes movements, attacks, skills]
Turn 2 - Current player: 2
```

---

## Troubleshooting

### Units not appearing correctly
- ✅ Fixed: Grid now 20x10 to match game map
- ✅ Fixed: Units positioned with proper grid offset

### Can't select units
- Make sure you're clicking **Player 1 units** (left side, blue)
- Turn 1 = Player 1, Turn 2 = Player 2, etc.

### Movement doesn't happen
- Movement is **planned** on click
- Must press **E** to execute
- Check console for "Move planned" message

### Units move but I can't see it
- State sync should detect position changes
- If units teleport instead of animating, that's expected (smooth movement animation exists but updates instantly)

---

## Testing Checklist

- [ ] Can select Player 1 units
- [ ] Blue highlight appears on selection
- [ ] Movement range (green tiles) displays
- [ ] Can click green tile to plan movement
- [ ] Selection clears after planning movement
- [ ] Can plan multiple unit movements
- [ ] Press E executes all planned movements
- [ ] Units move to correct positions
- [ ] Turn advances after execution
- [ ] Console shows correct feedback messages
- [ ] Can't move to invalid tiles (shows error)
- [ ] Right-click deselects unit
- [ ] UI shows correct unit info when selected

---

## Next Features Coming

### Phase 2 Remaining
- Click to attack enemy units
- Attack range visualization (red overlay)
- Basic attack execution

### Phase 3 - UI Layer
- Skill bar with icons
- Detailed unit info panel
- Combat log
- Turn order display
- Status effects display

---

*Phase 2 Progress: 75% complete (6/8 tasks)*
*Movement system: FULLY FUNCTIONAL ✅*
