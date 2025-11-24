# Turn Flow Analysis: ASCII vs Graphical

## ASCII Turn Flow (engine.py execute_turn())

### Phase 1: Pre-Action Processing (Lines 2273-2298)
1. **process_buff_durations(ui)** - Status effects for current player
2. **_process_neural_shunt_actions()** - Neural Shunt random actions
3. **Echo unit duration processing** - Decrement/expire Grae Exchange echoes

### Phase 2: Action Collection (Lines 2300-2338)
1. Collect all units with actions (move/attack/skill)
2. Include special actions (Viseroy traps, Auction Curse DOT)
3. **Sort by action_timestamp** - Lower timestamp = earlier action
4. **_pre_establish_marrow_dike_tracking()** - Pre-processing for skills

### Phase 3: Action Execution (Lines 2347-3540)
Execute actions in timestamp order:
1. **Movement** (if unit.move_target)
2. **Attacks** (if unit.attack_target)
3. **Skills** (if unit.skill_target and unit.selected_skill)
4. **Special Actions** (Viseroy trap damage, DOT effects)

Each action:
- Executes with animations (if ui present)
- Logs messages
- Handles death
- Updates game state

### Phase 4: Post-Action Processing (Lines 3540-3599)
Process status effect durations:
1. **Lunacy (Demilune) duration** - Decrement/expire
2. **Karrier Rave duration** - Decrement/expire
3. **Neural Shunt duration** - Decrement/expire

### Phase 5: Turn End (Lines 3604-3611)
1. **Toggle current_player** (3 - current_player)
2. **Increment turn** (if player becomes 1)
3. **initialize_next_player_turn()** - New player setup

### Phase 6: Next Player Turn Initialization (Lines 3703-3745)
1. **Apply passive skills** for new current player
2. **Reset flags:**
   - took_no_actions = True
   - DERELICTIONIST movement/skill flags
   - Dissociation PRT reset
   - Severance status reset

---

## Critical Turn Flow Rules

### Action Ordering
- **Timestamp-based**: Lower timestamp executes first
- **Random tiebreaker**: Equal timestamps randomized
- **ALL players' queued actions** execute in timestamp order

### Player Switching
- Happens AFTER all actions execute
- current_player toggles: 1 → 2 → 1 → 2
- Turn counter increments when player 1's turn starts

### Status Effect Timing
1. **Start of turn** (before actions): process_buff_durations()
2. **End of turn** (after actions): Duration decrements
3. **Next turn start**: Expired effects removed

### Animation Timing (ASCII with curses UI)
- Movement: Animated path
- Attacks: Flash/damage display
- Skills: Custom animations per skill
- Death: Flash/removal sequence

---

## Graphical Version Check

### Current Implementation
Graphical version calls: `game.execute_turn(ui=None)`

This means it uses the SAME engine.py execute_turn() method.

### Issues to Verify

1. **UI Parameter**: Graphical version passes `ui=None`
   - ✗ No animations will trigger
   - ✗ No visual feedback during action execution
   - Need to create graphical UI adapter

2. **Turn State Updates**: Does renderer update after turn?
   - Check: Unit positions sync?
   - Check: HP values sync?
   - Check: Status effects sync?
   - Check: Current player indicator?

3. **Action Queuing**: Are timestamps set correctly?
   - Movement: action_timestamp assigned?
   - Attacks: action_timestamp assigned?
   - Skills: action_timestamp assigned?

4. **Player Switching**: Does UI show turn change?
   - Check: Turn indicator updates?
   - Check: Units refresh for new player?
   - Check: Input locked for opponent's units?

### Necessary Graphical Enhancements

#### 1. UI Adapter for Animations
Create GraphicalUIAdapter to replace curses UI:
- show_attack_animation()
- show_skill_animation()
- show_movement_animation()
- show_death_animation()

#### 2. Turn Flow Visual Feedback
- "Executing Turn..." indicator
- Action-by-action animation
- Turn end transition
- Player switch announcement

#### 3. State Synchronization Points
After execute_turn():
- Sync unit positions
- Sync unit HP
- Sync unit status effects
- Update turn counter display
- Update current player indicator
- Clear action queues

#### 4. Animation Blocking/Flow
ASCII version: Blocks during animations
Graphical version should:
- Show animations sequentially
- Block input during execution
- Return control after animations complete

---

## Action Items for Graphical Version

### High Priority
1. ✅ Actions queue correctly with timestamps
2. ✅ execute_turn() runs
3. ✅ State syncs after turn
4. ⚠️ No animations during turn execution
5. ⚠️ No visual feedback for actions
6. ⚠️ Player switching might not be visible

### To Implement
1. GraphicalUIAdapter class
2. Turn execution visual flow
3. Animation system integration
4. Turn transition screen
5. Action replay/visualization

### To Test
1. Multi-action turn (move + attack)
2. Timestamp ordering (multiple units)
3. Player switching
4. Status effect application/removal
5. Death handling
6. Passive skill triggers
