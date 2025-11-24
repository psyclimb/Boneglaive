# Start Here: Phase 3 - UI Layer

**Current Status**: Phase 2 COMPLETE ✅
**Next Phase**: Phase 3 - UI Layer
**Date**: 2025-11-21

---

## Phase 2 Recap: What's Working ✅

### Complete Input System
- Click to select friendly units
- Green overlays show movement range
- Red overlays show attackable enemies
- Click to move or attack
- Press E to execute turn
- Turns advance and switch players

**The game is playable!** All core combat mechanics work.

---

## Phase 3 Goal: Build Comprehensive UI

Add professional UI elements to display game information and enhance gameplay.

### Priority Tasks

#### 1. Skill Bar (Highest Priority)
Display skills for the selected unit with hotkeys.

**What to Build**:
- Horizontal bar at bottom of screen
- Shows 4-5 skill slots per unit
- Hotkeys: 1-9 for skills, Q/W/E/R for special skills
- Shows skill name, AP cost, cooldown
- Gray out unavailable skills
- Highlight selected skill

**Files to Create/Modify**:
- `boneglaive/graphical/ui/skill_bar.py` (new)
- `boneglaive/graphical/renderer.py` (integrate skill bar)

**Skills to Display**:
Each unit type has unique skills. Query from `unit.get_skills()` or similar.

#### 2. Enhanced Unit Info Panel
Expand the current minimal info display.

**What to Add**:
- Unit portrait/sprite
- Current HP/Max HP bar (visual bar)
- Stats (ATK, DEF, Move Range, Attack Range)
- Status effects with icons
- Player indicator
- Unit type name

**Location**: Top-left corner (currently shows minimal text)

#### 3. Combat Log
Scrolling text log of all actions.

**What to Display**:
- Unit actions (X moved, Y attacked Z)
- Damage dealt/taken
- Skills used
- Status effects applied
- Turn changes
- Deaths

**Implementation**:
- Use `boneglaive.utils.message_log` for game messages
- Display last 5-10 messages
- Auto-scroll to bottom
- Semi-transparent background

**Location**: Bottom-left or right side panel

#### 4. Status Effects Display
Visual indicators for buffs/debuffs.

**What to Show**:
- Small icons above unit heads
- Tooltips on hover
- Duration counters (e.g., "3 turns")
- Color coding (buff=green, debuff=red)

**Common Status Effects**:
- Trapped, Pried, Jawline, Estranged, Mired
- Check `boneglaive/game/units.py` for full list

#### 5. Turn Order Display (Optional)
Show upcoming turn order.

**What to Show**:
- Mini unit portraits in sequence
- Current player highlighted
- Action timestamps
- Next 3-5 units to act

---

## Getting Started

### Step 1: Study Existing Skills System

```bash
# Find unit skills
grep -r "def.*skill" boneglaive/game/skills/

# Check unit types and their skills
cat boneglaive/game/skills/registry.py
```

Each unit has 4-5 skills defined in `boneglaive/game/skills/<unit_name>.py`.

### Step 2: Create UI Components Package

```bash
mkdir -p boneglaive/graphical/ui
touch boneglaive/graphical/ui/__init__.py
touch boneglaive/graphical/ui/skill_bar.py
```

### Step 3: Build Skill Bar First

**Why first?** Skills are the most important missing feature. Players need to use skills to make combat interesting.

**Architecture Pattern**:
```python
class SkillBar:
    def __init__(self, font):
        self.selected_unit = None
        self.skills = []
        self.hovered_skill = None

    def update(self, selected_unit):
        # Query skills from unit
        if selected_unit:
            self.skills = get_unit_skills(selected_unit)

    def draw(self, surface, y_position):
        # Draw skill slots at bottom of screen
        pass

    def handle_click(self, mouse_pos):
        # Return skill if clicked
        pass

    def handle_hotkey(self, key):
        # Return skill if hotkey pressed
        pass
```

### Step 4: Integrate with Renderer

In `renderer.py`:
```python
from boneglaive.graphical.ui.skill_bar import SkillBar

class GraphicalRenderer:
    def __init__(self):
        # ...
        self.skill_bar = SkillBar(self.font)

    def draw(self):
        # ...
        self.skill_bar.draw(main_surface, SCREEN_HEIGHT - 100)

    def handle_events(self):
        # Check for hotkeys
        if event.key in [pygame.K_1, pygame.K_2, ...]:
            skill = self.skill_bar.handle_hotkey(event.key)
            if skill:
                self.use_skill(skill)
```

---

## Key Files to Reference

### Game Logic
- `boneglaive/game/skills/core.py` - Skill base classes
- `boneglaive/game/skills/registry.py` - Unit → Skills mapping
- `boneglaive/game/skills/*.py` - Individual unit skills
- `boneglaive/game/units.py` - Unit class with status effects

### Visual Reference
- `boneglaive/ui/ui_components.py` - ASCII UI components (for inspiration)
- `demo_animations/` - Visual style reference

### Current Graphical Code
- `boneglaive/graphical/renderer.py` - Main renderer
- `boneglaive/graphical/game_state.py` - Game adapter

---

## Design Guidelines

### Visual Style
- Dark background (matching current theme)
- Semi-transparent panels
- Color coding:
  - Green = movement/positive
  - Red = attack/damage/negative
  - Blue = selection/friendly
  - Yellow = skill/special
  - Purple = status effects

### Font Sizes
- Large (36px): Titles, important info
- Medium (24px): Unit names, skill names
- Small (18px): Stats, details, logs

### Layout
```
┌──────────────────────────────────────────────┐
│ [Unit Info]                    [Turn: 5]     │
│ GLAIVEMAN                      Player 1      │
│ HP: 22/22                                     │
│ ATK: 12  DEF: 8                              │
├──────────────────────────────────────────────┤
│                                              │
│          [GAME GRID WITH UNITS]             │
│                                              │
│                                              │
├──────────────────────────────────────────────┤
│ [Combat Log]         [Skill Bar]            │
│ > P1 GLAIVEMAN      [1]JUDGEMENT  [2]PRY   │
│   moved to (5,3)    [3]AUTOCLAVE  [4]VAULT │
│ > P1 GLAIVEMAN      Cost: 3 AP    Cost: 2  │
│   attacked P2 INTERFERER                    │
└──────────────────────────────────────────────┘
```

---

## Implementation Order

1. **Skill Bar** (highest value, enables skill usage)
2. **Enhanced Unit Info** (improves player understanding)
3. **Combat Log** (helps track what happened)
4. **Status Effects Display** (important for tactics)
5. **Turn Order Display** (nice to have)

Estimate: 2-3 weeks for all Phase 3 tasks

---

## Testing Strategy

### Test Each Component
```bash
# Test skill bar rendering
python -c "from boneglaive.graphical.ui.skill_bar import SkillBar; print('Import OK')"

# Test full integration
python run_graphical.py
# 1. Select unit
# 2. Verify skill bar appears
# 3. Press 1-9 to use skills
# 4. Verify skills execute
```

### Create Test Files
```bash
# Create UI component tests
touch test_skill_bar.py
touch test_combat_log.py
```

---

## Common Pitfalls to Avoid

1. **Don't reinvent the wheel** - Check ASCII UI components for logic
2. **Query game state, don't cache** - Skills/stats can change each frame
3. **Handle unit deselection** - Hide skill bar when no unit selected
4. **Validate skill usage** - Check AP, cooldowns, valid targets
5. **Coordinate systems** - Remember game uses (y,x), renderer uses (x,y)

---

## Resources

### ASCII Game References
```bash
# How skills work in ASCII version
python boneglaive/main.py --single-player
# Press 's' for skill mode, select skill, select target
```

### Skill System
```bash
# List all skills
ls boneglaive/game/skills/*.py

# Check skill implementation
cat boneglaive/game/skills/glaiveman.py
```

---

## Success Criteria

### Phase 3 Complete When:
- [x] Can see and use skills with hotkeys
- [x] Unit info shows all relevant stats
- [x] Combat log displays actions
- [x] Status effects visible on units
- [x] UI feels professional and polished

---

## Estimated Timeline

**Phase 3 Duration**: 2-3 weeks (part-time)

**Breakdown**:
- Skill bar: 1-2 days
- Enhanced unit info: 1 day
- Combat log: 2-3 days
- Status effects: 2-3 days
- Polish and testing: 2-3 days

After Phase 3, the game will have a complete, professional UI!

---

*Ready to start Phase 3!*
*Last updated: 2025-11-21*
