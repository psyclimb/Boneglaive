# Boneglaive Game Architecture Analysis

## Overview
Analysis of the existing ASCII game structure for integration with the graphical renderer.

---

## Main Components

### 1. Game Class (`boneglaive/game/engine.py`)

**Location**: Line 17

**Key Properties**:
```python
class Game:
    def __init__(self, skip_setup=False, map_name="lime_foyer_arena", player_names=None):
        self.units = []              # List of all Unit objects
        self.current_player = 1      # Current player (1 or 2)
        self.turn = 1                # Turn number
        self.winner = None           # Winner (1, 2, or None)
        self.map = Map               # Game map object
        self.setup_phase = bool      # Whether in setup phase
```

**Key Methods**:
- `execute_turn(ui=None)` - Main turn execution (line 2255)
- `change_map(map_name)` - Change map
- `get_player_name(player_num)` - Get player display name

**Entry Point**:
- Constructor can skip setup: `Game(skip_setup=True)`
- Creates default units if skip_setup=True

---

### 2. Unit Class (`boneglaive/game/units.py`)

**Location**: Line 13

**Key Properties**:
```python
class Unit:
    def __init__(self, unit_type, player, y, x):
        self.type = unit_type        # UnitType enum
        self.player = player         # 1 or 2
        self.y = y                   # Grid Y position
        self.x = x                   # Grid X position
        self.hp = int                # Current HP
        self.max_hp = int            # Maximum HP
        self.attack = int            # Attack stat
        self.defense = int           # Defense stat
        self.move_range = int        # Movement range
        self.attack_range = int      # Attack range

        # Actions
        self.move_target = (y, x)    # Movement target
        self.attack_target = Unit    # Attack target
        self.skill_target = Unit     # Skill target
        self.selected_skill = str    # Selected skill name

        # Visual indicators
        self.vault_target_indicator = (y, x)
        # ... many more indicators

        # Status effects
        self.trapped_by = Unit       # If trapped
        self.jawline_affected = bool
        self.estranged = bool
        # ... many more status flags
```

**Unique Identification**:
- No built-in unique ID
- Can use: `(unit.player, unit.type, unit.greek_id)` tuple
- Or generate UUID on creation

**Position System**:
- Uses `(y, x)` coordinate system (row, col)
- Origin is top-left
- Properties have setters for validation

---

### 3. Skill System

**Skill Execution Flow**:
1. Player selects unit
2. Player selects skill
3. Player selects target
4. `execute_turn()` called
5. Skills execute in action order
6. Effects applied
7. Turn ends

**Skill Location**:
- Main skills: `boneglaive/game/skills.py`
- Unit-specific: `boneglaive/game/skills/` directory

**Key Pattern**:
```python
# Skills are methods on Unit class
unit.use_skill(game, target)
# Or function calls
execute_glaive_judgement(game, caster, target)
```

---

### 4. Turn Execution (`execute_turn`)

**Location**: `engine.py` line 2255

**Flow**:
1. Process status effects/buffs
2. Process echoes (expired units)
3. Collect units with actions
4. Sort by action timestamp
5. Execute each action in order:
   - Movement
   - Attacks
   - Skills
6. Process effects
7. Check win condition
8. Advance to next turn

**Key Point**: Turn execution is **batch processed** - all actions queued then executed in order.

---

### 5. Map System (`boneglaive/game/map.py`)

**Map Object**:
```python
class Map:
    self.width = int
    self.height = int
    self.tiles = [[Tile]]  # 2D array
    self.furniture = [Furniture]
    self.spawn_zones = {player: [(y, x)]}
```

**Tile Types**: Different terrain types affect movement/vision

---

## Coordinate System

### ASCII Game
- Uses `(y, x)` - **(row, column)**
- Origin: Top-left (0, 0)
- Y increases downward
- X increases rightward

### Graphical Renderer
- Uses `(grid_x, grid_y)` - **(column, row)**
- Origin: Top-left (0, 0)
- grid_x increases rightward (column)
- grid_y increases downward (row)

### **IMPORTANT CONVERSION**:
```python
# ASCII (y, x) → Graphical (grid_x, grid_y)
grid_x = unit.x
grid_y = unit.y

# Graphical (grid_x, grid_y) → ASCII (y, x)
unit.y = grid_y
unit.x = grid_x
```

**The coordinates are swapped in naming convention only!**

---

## State Change Detection Points

### HP Changes
- Direct: `unit.hp = new_value`
- Via damage: `unit.take_damage(amount)` (if exists)
- Via healing: `unit.heal(amount)` (if exists)

**Detection Strategy**: Store `last_hp` per unit, compare each frame

### Position Changes
- Direct: `unit.y = new_y; unit.x = new_x`
- Via movement: During turn execution

**Detection Strategy**: Store `last_position`, compare each frame

### Status Effects
- Various boolean flags on unit
- Duration counters

**Detection Strategy**: Track status flags, emit events on change

### Death
- `unit.hp <= 0`
- Unit may remain in `game.units` list but marked as dead

**Detection Strategy**: Check `unit.is_alive()` method (if exists) or `unit.hp > 0`

---

## Integration Strategy

### Phase 1: Minimal Integration

1. **Create Game Instance**:
```python
from boneglaive.game.engine import Game

game = Game(skip_setup=True, map_name="lime_foyer_arena")
# This creates a game with default units
```

2. **Access Units**:
```python
for unit in game.units:
    if unit.hp > 0:  # Unit is alive
        visual_unit = create_visual_unit(unit)
```

3. **Detect State Changes**:
```python
# In adapter sync_state():
for unit in game.units:
    if unit.hp != visual_unit.last_hp:
        # HP changed!
        emit_animation_event("hp_change", unit, delta)
```

4. **Execute Turn**:
```python
# When player ends turn:
game.execute_turn(ui=None)  # Runs headless
# Then sync state to see what changed
```

### Phase 2: Event Hooks (Optional)

**Option**: Modify game code to emit events:
```python
# In Unit class:
@property
def hp(self):
    return self._hp

@hp.setter
def hp(self, value):
    old_hp = self._hp
    self._hp = value
    if old_hp != value:
        emit_event("hp_changed", unit=self, old=old_hp, new=value)
```

**Trade-off**: More invasive but cleaner event system

---

## Unit ID System

### Problem
Units don't have unique IDs built-in.

### Solution Options

**Option 1**: Generate UUIDs
```python
import uuid
unit.uuid = str(uuid.uuid4())
```

**Option 2**: Use tuple key
```python
unit_id = (unit.player, unit.type, unit.greek_id)
```

**Option 3**: Use object id
```python
unit_id = id(unit)  # Python object ID
```

**Recommendation**: Option 1 (UUID) - most flexible and unique

### Implementation
```python
# Monkey-patch in adapter initialization:
for unit in game.units:
    if not hasattr(unit, 'uuid'):
        unit.uuid = str(uuid.uuid4())
```

---

## Skill Animation Mapping

### Strategy
Map skill names to animation classes:

```python
SKILL_ANIMATIONS = {
    "JUDGEMENT": ("glaive_judgement", SpinningGlaiveProjectile),
    "JUDGEMENT_CRIT": ("glaive_judgement_crit", SpinningGlaiveProjectile),
    "PRY": ("glaive_pry", PryAnimation),
    "DEMILUNE": ("potpourrist_demilune", DemiluneSwing),
    # ... etc
}
```

### Detection
```python
# In execute_turn, detect skill usage:
if unit.selected_skill:
    skill_name = unit.selected_skill
    target = unit.skill_target
    # Queue animation
    adapter.queue_skill_animation(skill_name, unit, target)
```

---

## Turn Management

### Current Player
```python
game.current_player  # 1 or 2
```

### Turn Number
```python
game.turn  # Integer
```

### Advancing Turn
```python
game.execute_turn()  # Executes current player's turn
# current_player switches after turn completes
```

### Turn Order
Units act in timestamp order within a turn (see `action_timestamp`)

---

## Win Conditions

### Check Winner
```python
if game.winner:
    # Game is over
    winning_player = game.winner  # 1 or 2
```

### Detection
Game sets `game.winner` when all units of one player are dead

---

## Message Log System

### Access
```python
from boneglaive.utils.message_log import message_log

# Get recent messages
messages = message_log.get_messages()
```

### Integration
Can display these in graphical combat log

---

## Next Steps for Integration

### Immediate Tasks

1. **Import Game class**:
```python
# In game_state.py:
from boneglaive.game.engine import Game
from boneglaive.game.units import Unit
```

2. **Initialize game instance**:
```python
def initialize_game(self, game_instance=None):
    if game_instance:
        self.game = game_instance
    else:
        self.game = Game(skip_setup=True)

    # Add UUIDs to units
    self._add_unit_ids()
```

3. **Implement unit ID system**:
```python
def _add_unit_ids(self):
    import uuid
    for unit in self.game.units:
        if not hasattr(unit, 'uuid'):
            unit.uuid = str(uuid.uuid4())
```

4. **Map units to visuals**:
```python
def sync_units(self, renderer):
    for game_unit in self.game.units:
        if game_unit.hp > 0:  # Alive
            if game_unit.uuid not in self.visual_units:
                # Create new visual unit
                animated = renderer.create_unit(
                    game_unit.type,
                    game_unit.player,
                    game_unit.x,  # Note: x is column
                    game_unit.y   # Note: y is row
                )
                self.create_visual_unit(game_unit, animated)
```

5. **Implement sync_state**:
```python
def sync_state(self):
    events = []

    for uuid, visual in self.visual_units.items():
        game_unit = visual.game_unit

        # HP change
        if game_unit.hp != visual.last_hp:
            delta = game_unit.hp - visual.last_hp
            if delta < 0:
                events.append(AnimationEvent("damage", game_unit, damage=-delta))
            else:
                events.append(AnimationEvent("heal", game_unit, heal=delta))
            visual.last_hp = game_unit.hp

        # Position change
        if (game_unit.y, game_unit.x) != visual.last_position:
            events.append(AnimationEvent("movement", game_unit,
                                        old=(visual.last_position),
                                        new=(game_unit.y, game_unit.x)))
            visual.last_position = (game_unit.y, game_unit.x)

    return events
```

---

## Summary

### Key Files
- **engine.py**: Game class, turn execution
- **units.py**: Unit class, stats, status
- **skills.py**: Skill implementations
- **map.py**: Map/terrain system

### Coordinate System
- ASCII: (y, x) - row, column
- Graphical: (grid_x, grid_y) - column, row
- **Swap when converting!**

### Integration Path
1. Import Game and Unit classes
2. Create game instance with skip_setup=True
3. Add UUID system to units
4. Map game units → visual units
5. Poll game state each frame
6. Detect changes → emit animation events
7. Render animations → update visuals

### Next File to Edit
**`boneglaive/graphical/game_state.py`** - Uncomment imports and implement initialization

---

*Created: 2025-11-21*
