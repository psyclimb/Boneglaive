# Boneglaive Graphical Version - Development Roadmap

## Overview
Incremental plan to transform the animation demo into a fully playable graphical game.

---

## ✅ Phase 0: Foundation (COMPLETE)
**Goal**: Set up project structure and skeleton code

**Completed**:
- [x] Create `boneglaive/graphical/` package structure
- [x] Implement `GameStateAdapter` skeleton
- [x] Implement `GraphicalRenderer` skeleton
- [x] Create launch script (`run_graphical.py`)
- [x] Write architecture documentation
- [x] Set up demo scene for testing

**Test Command**: `python run_graphical.py`

---

## 🚧 Phase 1: Game Logic Integration (IN PROGRESS)
**Goal**: Connect renderer to actual game logic

**Duration**: 1-2 weeks

### Tasks:

#### 1.1 Study Existing Game Structure
- [ ] Map out `boneglaive/game/` architecture
- [ ] Identify main game loop
- [ ] Document unit class structure
- [ ] Document skill execution flow
- [ ] Find combat resolution logic
- [ ] Identify state change points (HP, position, turn)

**Deliverable**: Architecture diagram of existing game

#### 1.2 Implement Real Game Instance
- [ ] Uncomment game imports in `game_state.py`
- [ ] Implement `initialize_game()` to create real game
- [ ] Map game units → visual units
- [ ] Implement proper `_get_unit_id()`
- [ ] Create initial test battle (1v1)

**Deliverable**: Renderer shows real game units

#### 1.3 State Synchronization
- [ ] Implement HP change detection in `sync_state()`
- [ ] Implement position change detection
- [ ] Implement turn change detection
- [ ] Test with manual game state manipulation
- [ ] Add debug logging for state changes

**Deliverable**: Visual units update when game state changes

#### 1.4 Event System
- [ ] Decide: Polling vs event hooks?
- [ ] If hooks: Add event emission to game logic
- [ ] Implement skill execution detection
- [ ] Queue animations for skill usage
- [ ] Test animation triggering

**Deliverable**: Animations play when skills are used in game

**Milestone**: Can run a scripted battle with visual feedback

---

## ✅ Phase 2: Core Input System (COMPLETE)
**Goal**: Make the game playable with mouse/keyboard

### Tasks:

#### 2.1 Unit Selection ✅
- [x] Implement click-to-select for player units
- [x] Visual selection indicator
- [x] Show selected unit info in UI
- [x] Deselection on right-click or ESC

#### 2.2 Movement System ✅
- [x] Query valid movement positions from game logic
- [x] Implement `get_movement_range()` in adapter
- [x] Visualize movement range on grid
- [x] Implement click-to-move
- [x] Animate unit movement
- [x] Update game logic position

**Deliverable**: Can select and move units with mouse ✅

#### 2.3 Attack System ✅
- [x] Query attack range from game logic
- [x] Implement `get_attack_range()` in adapter
- [x] Visualize attack range (red overlays on enemies)
- [x] Click enemy to plan attack
- [x] Execute attack through game logic
- [x] Apply damage and sync state

**Deliverable**: Can attack enemies with mouse ✅

#### 2.4 Turn Management ✅
- [x] Display current turn/player
- [x] End turn button (E key)
- [x] Execute all planned actions
- [x] Advance turn and switch player
- [ ] Turn transition animation (deferred to Phase 7)
- [ ] AI turn execution (not yet implemented)
- [ ] Turn order display (deferred to Phase 3)

**Deliverable**: Full turn-based gameplay loop works ✅

**Milestone**: Can play a complete battle start-to-finish ✅

**Completion Date**: 2025-11-21

---

## 🎨 Phase 3: UI Layer (2-3 weeks)
**Goal**: Build comprehensive UI for game info and control

### Tasks:

#### 3.1 Unit Info Panel
- [ ] Design panel layout
- [ ] Show HP, AP, status effects
- [ ] Portrait/sprite display
- [ ] Stat display (ATK, DEF, etc.)
- [ ] Update in real-time

#### 3.2 Skill Bar
- [ ] Horizontal skill bar at bottom
- [ ] Skill icons (or text labels)
- [ ] Hotkey indicators (1-9, Q-R)
- [ ] AP cost display
- [ ] Grayed out when unavailable
- [ ] Cooldown indicators

#### 3.3 Combat Log
- [ ] Scrolling text log
- [ ] Action descriptions
- [ ] Damage/heal numbers
- [ ] Color-coded messages
- [ ] Auto-scroll to bottom

#### 3.4 Turn Order Display
- [ ] Show upcoming turn order
- [ ] Unit portraits in sequence
- [ ] Current turn highlighted
- [ ] Update when turn changes

#### 3.5 Status Effects Display
- [ ] Icons above unit heads
- [ ] Tooltip on hover
- [ ] Duration indicators
- [ ] Stacking display

**Milestone**: Game has complete UI for all information

---

## 🎬 Phase 4: Animation Completion (3-4 weeks)
**Goal**: Port all animations from demo, add missing ones

### Tasks:

#### 4.1 Port Existing Animations
- [ ] Copy `demo_animations/` → `graphical/animations/`
- [ ] Refactor to work with real game state
- [ ] Test each animation in-game
- [ ] GLAIVEMAN: Judgement, PRY, Autoclave, Vault
- [ ] POTPOURRIST: All skills
- [ ] MANDIBLE FOREMAN: All skills

#### 4.2 Animation Registry
- [ ] Create `AnimationFactory` class
- [ ] Map skill names → animation classes
- [ ] Handle animation variants (normal, infused, critical)
- [ ] Animation queueing system
- [ ] Priority system (blocking vs non-blocking)

#### 4.3 Generic Animations
- [ ] Generic melee attack
- [ ] Generic projectile
- [ ] Generic buff effect
- [ ] Generic debuff effect
- [ ] Death animations
- [ ] Spawn animations

#### 4.4 Remaining Units (TODO: List units)
- [ ] Unit A animations
- [ ] Unit B animations
- [ ] Unit C animations
- [ ] ... (add as needed)

**Milestone**: All skills have visual animations

---

## 🎮 Phase 5: Game Modes & Menus (2-3 weeks)
**Goal**: Add menus, battle selection, progression

### Tasks:

#### 5.1 Main Menu
- [ ] Title screen
- [ ] New Game button
- [ ] Continue button (if save exists)
- [ ] Settings button
- [ ] Quit button
- [ ] Background animation

#### 5.2 Battle Selection
- [ ] Mission/battle list
- [ ] Difficulty selection
- [ ] Team composition screen
- [ ] Enemy preview
- [ ] Start battle transition

#### 5.3 Team Composition
- [ ] Unit roster display
- [ ] Drag-and-drop team builder
- [ ] Unit details on click
- [ ] Formation/position setup
- [ ] Save/load teams

#### 5.4 Settings Menu
- [ ] Volume controls
- [ ] Graphics settings
- [ ] Keybind configuration
- [ ] Accessibility options
- [ ] Reset to defaults

#### 5.5 Victory/Defeat Screens
- [ ] Victory animation
- [ ] Rewards display
- [ ] Statistics summary
- [ ] Continue/retry buttons
- [ ] Defeat animation
- [ ] Return to menu

**Milestone**: Game has complete menu system and flow

---

## 💾 Phase 6: Save/Load System (1-2 weeks)
**Goal**: Persistent game state

### Tasks:

#### 6.1 Save System
- [ ] Serialize game state to JSON
- [ ] Save visual state (for replay)
- [ ] Auto-save after each turn
- [ ] Manual save option
- [ ] Multiple save slots

#### 6.2 Load System
- [ ] Load game state from JSON
- [ ] Reconstruct visual state
- [ ] Validate save file integrity
- [ ] Handle version mismatches
- [ ] Continue from saved battle

#### 6.3 Replay System (Optional)
- [ ] Record all actions
- [ ] Playback recorded battle
- [ ] Speed controls (1x, 2x, 4x)
- [ ] Skip to turn

**Milestone**: Can save and resume games

---

## 🎯 Phase 7: Polish & Optimization (2-3 weeks)
**Goal**: Make game smooth and polished

### Tasks:

#### 7.1 Performance Optimization
- [ ] Profile rendering performance
- [ ] Optimize particle systems
- [ ] Implement sprite batching
- [ ] Reduce draw calls
- [ ] Add graphics quality settings

#### 7.2 Visual Polish
- [ ] Screen transitions
- [ ] Menu animations
- [ ] Improved particle effects
- [ ] Better UI styling
- [ ] Consistent color scheme

#### 7.3 Audio (If desired)
- [ ] Background music
- [ ] Skill sound effects
- [ ] UI sound effects
- [ ] Volume controls
- [ ] Music transitions

#### 7.4 Feedback & Feel
- [ ] Stronger hit reactions
- [ ] Better camera shake
- [ ] Improved flash effects
- [ ] Smoother animations
- [ ] Better timing

#### 7.5 Bug Fixing
- [ ] Test all skills thoroughly
- [ ] Fix animation edge cases
- [ ] Fix UI glitches
- [ ] Fix input issues
- [ ] Test on different resolutions

**Milestone**: Game feels polished and complete

---

## 🚀 Phase 8: Release Preparation (1 week)
**Goal**: Prepare for release

### Tasks:

#### 8.1 Documentation
- [ ] Write user manual
- [ ] Create tutorial/help screen
- [ ] Document controls
- [ ] Write README for players

#### 8.2 Packaging
- [ ] Create executable (PyInstaller)
- [ ] Bundle assets
- [ ] Test on clean system
- [ ] Create installer (if desired)

#### 8.3 Testing
- [ ] Full playthrough test
- [ ] Test all units and skills
- [ ] Test on multiple systems
- [ ] Fix any critical bugs

**Milestone**: Game is ready for release

---

## 🔮 Future Enhancements (Post-Release)

### Potential Features:
- [ ] Multiplayer (local or network)
- [ ] Level editor
- [ ] Custom unit creator
- [ ] Mod support
- [ ] Additional game modes
- [ ] Achievements
- [ ] Leaderboards
- [ ] Mobile port (?)

---

## Current Status

**Phase**: 2 (Input System) COMPLETE → 3 (UI Layer) NEXT

**Completed Phases**:
- ✅ Phase 0: Foundation
- ✅ Phase 1: Game Logic Integration
- ✅ Phase 2: Input System

**Next Phase**:
- 🚧 Phase 3: UI Layer (skill bar, combat log, status effects)

**Progress**: 3/8 phases complete (37.5%)

**Estimated Remaining Time**: 12-17 weeks for Phases 3-7

---

## Dependencies

### Required:
- pygame (already installed)
- Python 3.8+

### Optional:
- pygame-gui (for advanced UI)
- PyInstaller (for packaging)
- cairosvg (for SVG sprites)

---

*Last updated: 2025-11-21*
