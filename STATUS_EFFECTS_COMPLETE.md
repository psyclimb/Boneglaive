# Status Effects Panel - Implementation Complete

**Date**: 2025-11-21
**Component**: boneglaive/graphical/ui/status_effects.py
**Status**: ✅ COMPLETE

## Overview

Implemented comprehensive status effects display panel for the graphical version. Unlike the ASCII version (which shows icons next to units on the battlefield), the graphical version displays status effects in a dedicated UI panel when a unit is selected.

## Features Implemented

### 1. Status Effects Panel Component
- **File**: `boneglaive/graphical/ui/status_effects.py` (380 lines)
- Displays status effects for selected unit
- Color-coded by type:
  - **Buffs**: Green (100, 200, 100)
  - **Debuffs**: Red (255, 100, 100)
  - **Special**: Yellow (255, 200, 100)
  - **Neutral**: Gray (150, 150, 200)
- Shows icon, name, and duration for each effect
- Hover tooltips with detailed descriptions
- Auto-sizing based on number of effects

### 2. Comprehensive Effect Coverage
Supports **19 different status effects** across 4 categories:

#### Debuffs (11 effects):
- Pried (defense reduced)
- Trapped (by MANDIBLE_FOREMAN)
- Jawline (network effect)
- Estranged (all stats -1)
- Mired (stuck in Marrow Dike)
- Neural Shunt (disrupted)
- Derelicted (immobilized)
- Demilune (attack reduced, defense halved)
- Taunted (forced to attack POTPOURRIST)
- Radiation (periodic damage)
- Shrapnel (damage over time)

#### Buffs (5 effects):
- Partition Shield (damage absorption)
- Severance (+1 movement)
- Pumped Up (+1 all stats)
- Karrier Rave (phased, triple strike)
- Trauma Processing (damage storage)

#### Special (1 effect):
- Charging (FOWL_CONTRIVANCE)

#### Neutral (2 effects):
- Echo (Grae Exchange temporary copy)
- Potpourri (held by POTPOURRIST)

### 3. Integration with Renderer
- Panel appears on left side when unit selected
- Position: (10, SCREEN_HEIGHT - 530) - above combat log
- Updates automatically on:
  - Unit selection (left click friendly unit)
  - Deselection (right click)
  - Unit death
- Mouse hover for tooltips

### 4. Visual Design
- **Panel**: 350x(variable) px, semi-transparent background
- **Effect Icons**: 36x36px colored squares with text icons
- **Layout**: Icon + name + duration in rows
- **Spacing**: 8px between elements, 10px padding
- **Tooltips**: Appear below panel on hover, word-wrapped

## Technical Details

### Status Effect Detection
Each effect has:
```python
{
    "name": "Display Name",
    "type": "buff|debuff|special|neutral",
    "icon": "2-char icon",
    "description": "Tooltip text",
    "duration_key": "unit_property_name",  # optional
    "check": lambda u: u.property_name  # check function
}
```

### Special Cases Handled
1. **Radiation Stacks**: Shows count of stacks
2. **Partition Shield**: Shows shield strength in HP
3. **Trauma Processing**: Shows stored damage amount
4. **Demilune**: Shows both attack reduction and defense halving

## Files Modified

### Created
- `boneglaive/graphical/ui/status_effects.py` (380 lines)
- `test_status_effects.py` (160 lines) - unit tests
- `test_status_effects_visual.py` (180 lines) - workflow tests

### Modified
- `boneglaive/graphical/renderer.py`:
  - Import StatusEffectsPanel
  - Create panel instance
  - Update on unit selection/deselection
  - Draw panel every frame
  - Handle mouse motion for hover

## Testing

### Test Results: ✅ ALL PASS

#### test_status_effects.py
- Import and creation
- Message adding and retrieval
- Unit type switching
- Drawing (headless)
- Empty panel handling
- Effect type coverage
- **Result**: 10/10 tests passed

#### test_status_effects_visual.py
- Workflow simulation (select/deselect)
- Multiple effect display
- Different unit types
- Tooltip data validation
- **Result**: All tests passed

### Sample Output
```
[P  ] Pried              RED
     Defense reduced by Pry skill
[J  ] Jawline            RED       (3 turns)
     Affected by Jawline skill network
[+  ] Partition          GREEN     (4 turns)
     Protected by Partition shield (15 HP)
[UP ] Pumped Up          GREEN     (2 turns)
     +1 to all stats
```

## Usage

### In-Game Controls
1. **Select Unit**: Left click friendly unit
   - Status effects panel appears on left
   - Shows all active effects
2. **Hover Effect**: Mouse over effect
   - Tooltip appears with full description
3. **Deselect**: Right click anywhere
   - Panel disappears

### For Developers
```python
# Update panel when unit selected
game_unit = get_game_unit(selected_unit)
status_effects_panel.update(game_unit)

# Draw panel
height = status_effects_panel.draw(surface, x, y)

# Handle hover for tooltips
status_effects_panel.handle_mouse_motion(mouse_pos)
```

## Phase 3 Progress Update

**Before**: Phase 3 at 60% (skill bar, targeting, combat log)
**After**: Phase 3 at 80% (+ status effects panel)

**Remaining Phase 3 Tasks**:
- Enhanced unit info panel (20%)
- Turn order display (optional)

## Design Notes

### Why Panel Instead of Battlefield Icons?

The ASCII version shows status effect icons to the right of each tile on the battlefield. For the graphical version, we chose a panel-based approach because:

1. **Screen Real Estate**: Graphical tiles are 64x64px - adding icons would clutter the battlefield
2. **Readability**: Panel allows full effect names and descriptions
3. **Interactivity**: Hover tooltips provide detailed information
4. **Scalability**: Panel can show unlimited effects without crowding

### Color Psychology
- Green (buffs): Positive, beneficial
- Red (debuffs): Negative, harmful
- Yellow (special): Attention, unique mechanics
- Gray (neutral): Informational, non-combat

### Performance
- Effects only calculated when unit selected
- Drawing skipped when panel empty (0 effects)
- Hover detection uses simple rectangle collision
- No per-frame recalculations

## Next Steps

With status effects complete, Phase 3 focus shifts to:
1. **Enhanced Unit Info Panel**: Detailed stats, visual HP bar, portrait
2. **Turn Order Display** (optional): Show upcoming turn sequence

Status effects panel provides critical combat information and completes the core UI layer for Phase 3.
