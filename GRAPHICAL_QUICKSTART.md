# Boneglaive Graphical Version - Quick Start Guide

## What Was Created

A complete skeleton for the graphical version of Boneglaive, with architecture designed to integrate the existing ASCII game logic with a modern pygame renderer.

### Package Structure Created

```
boneglaive/
├── graphical/                    # NEW - Main graphical package
│   ├── __init__.py              # Package exports
│   ├── renderer.py              # Main pygame renderer (500+ lines)
│   ├── game_state.py            # Game logic adapter (350+ lines)
│   ├── README.md                # Architecture documentation
│   ├── ROADMAP.md               # Development roadmap
│   ├── ui/                      # UI components (empty, ready for development)
│   │   └── __init__.py
│   ├── animations/              # Animation classes (empty, will copy from demo)
│   │   └── __init__.py
│   └── assets/                  # Game assets (sprites, sounds)
│       └── __init__.py
└── run_graphical.py             # Launch script
```

## Key Files

### 1. `game_state.py` - GameStateAdapter
**Purpose**: Bridge between ASCII game logic and graphical renderer

**Key Features**:
- State synchronization system
- Animation event generation
- Input translation (mouse clicks → game commands)
- Visual unit management

**Main Classes**:
- `GameStateAdapter` - Main adapter
- `AnimationEvent` - Represents animations to play
- `VisualUnit` - Links game units to visual representations

### 2. `renderer.py` - GraphicalRenderer
**Purpose**: Main pygame rendering engine

**Key Features**:
- Grid-based rendering
- Mouse interaction (click, hover)
- Animation playback system
- UI rendering framework
- Screen effects (shake, flash)

**Main Methods**:
- `handle_events()` - Input processing
- `update()` - Game state updates
- `draw()` - Frame rendering
- `screen_to_grid()` / `grid_to_screen()` - Coordinate conversion

### 3. `README.md`
Complete architecture documentation including:
- Design philosophy
- Component responsibilities
- Development guidelines
- Animation system overview
- Next steps

### 4. `ROADMAP.md`
8-phase development plan with:
- Task breakdowns
- Time estimates
- Milestones
- Current status tracking

## How to Test Current Status

### Run the Demo Scene
```bash
cd /home/user/boneglaive
python run_graphical.py
```

**What you'll see**:
- Pygame window opens (1280x800)
- Checkerboard grid
- Two demo units (GLAIVEMAN and ENEMY)
- Mouse hover highlights grid tiles
- Click to select units (shows in UI)
- ESC to quit, SPACE to pause

**What works now** (Phase 1 COMPLETE):
- ✅ Real game units from ASCII game logic
- ✅ Live state synchronization (HP, position, death)
- ✅ Floating damage/heal text
- ✅ Visual effects (shake, particles)
- ✅ Smooth unit movement

**What doesn't work yet**:
- Input not connected to game (can't issue commands)
- No skill targeting
- No turn management
- Skill animations not hooked up

Phase 1 (game logic integration) is COMPLETE! Phase 2 (input system) is next.

## Architecture Overview

### Adapter Pattern Design

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  ASCII Game     │◄────────│  GameStateAdapter│◄────────│  Graphical  │
│  Logic          │  poll   │                  │  input  │  Renderer   │
│  (headless)     │────────►│  State Sync      │────────►│  (pygame)   │
└─────────────────┘  events └──────────────────┘  visual └─────────────┘
```

**Flow**:
1. Renderer handles player input (mouse click)
2. Adapter translates to game command
3. Game logic executes command
4. Adapter detects state changes
5. Adapter generates animation events
6. Renderer plays animations
7. Renderer updates visual display

## Next Steps

### Immediate (This/Next Session)

1. **Test the skeleton**:
   ```bash
   python run_graphical.py
   ```
   Verify it runs without errors.

2. **Study existing game structure**:
   ```bash
   # Look at game entry points
   cd boneglaive/game
   ls -R

   # Find main game class
   grep -r "class.*Game" boneglaive/game/

   # Find unit classes
   grep -r "class.*Unit" boneglaive/game/
   ```

3. **Map the architecture**:
   - Document main game loop
   - Identify unit class structure
   - Find skill execution points
   - Note state change locations

### Short-term (Next Few Days)

4. **Connect real game logic**:
   - Uncomment imports in `game_state.py`
   - Initialize actual game instance
   - Map one unit from game → renderer
   - Test with real game state

5. **Get one skill working**:
   - Hook up JUDGEMENT skill
   - Copy animation from demo_animations
   - Test end-to-end (click → execute → animate)

### Medium-term (Next Week)

6. **Basic combat loop**:
   - Movement system
   - Attack targeting
   - Turn management
   - Win/loss conditions

7. **UI framework**:
   - Unit info panel
   - Skill bar
   - Combat log

## Design Decisions Made

### 1. Adapter Pattern (vs. Fork)
**Decision**: Keep ASCII game separate, use adapter to bridge.

**Rationale**:
- ASCII game continues to work
- Less code duplication
- Easier maintenance
- Can swap renderers

### 2. Polling (vs. Event Hooks)
**Decision**: Adapter polls game state for changes.

**Rationale**:
- Less invasive to existing code
- Easier to implement initially
- Can add hooks later if needed

### 3. Grid Coordinates
**Decision**: Game logic uses grid coords, renderer uses pixels.

**Rationale**:
- Clean separation
- Adapter handles conversion
- Easy to change tile size

### 4. Animation Blocking
**Decision**: Adapter prevents input during blocking animations.

**Rationale**:
- Simpler than game-level animation callbacks
- Renderer has full control over timing
- Can add async later if needed

## Key TODOs Throughout Code

Search for `TODO` comments in the code for specific integration points:

```bash
grep -r "TODO" boneglaive/graphical/
```

**Major TODOs**:
- Import actual game classes
- Implement unit ID system
- Create animation factory
- Build UI components
- Add event hooks (if needed)

## Reference Materials

### For Animation Implementation
- **demo_animations/**: Reference for all visual effects
- Copy patterns from demo units (GLAIVEMAN, POTPOURRIST, etc.)

### For Game Logic Integration
- **boneglaive/game/**: Source of truth for game rules
- Study combat resolution, skill execution, turn order

### For UI Design
- ASCII version shows what info is needed
- Think about how to display this graphically

## Development Philosophy

**Incremental**: Build one vertical slice first (1v1 combat with one skill), then expand.

**Test-driven**: Test each component as you build it (demo scene helps here).

**Reference-based**: Use demo_animations as visual reference, ASCII game as logic reference.

**Documented**: Keep README and ROADMAP updated as you progress.

## Common Pitfalls to Avoid

1. **Don't rewrite game logic** - Use what exists
2. **Don't optimize prematurely** - Get it working first
3. **Don't try to animate everything at once** - Start with one skill
4. **Don't skip the adapter** - It's the key to clean architecture
5. **Don't forget state sync** - Visual must match game state

## Success Criteria

### Phase 1 Complete When:
- [ ] Real game instance running
- [ ] One unit from game appears in renderer
- [ ] HP changes in game update visual HP
- [ ] One skill executes and animates

### Fully Playable When:
- [ ] Can select units
- [ ] Can move and attack
- [ ] All skills work
- [ ] Turn-based gameplay functions
- [ ] Win/loss conditions work

### Release Ready When:
- [ ] All animations ported
- [ ] Complete UI
- [ ] Menus and navigation
- [ ] Save/load works
- [ ] No major bugs

## Getting Help

**Questions to answer first**:
1. Which phase are you on? (Check ROADMAP.md)
2. What specific task? (Check task list in ROADMAP.md)
3. What error/issue? (Check logs, test in demo mode)

**Debugging tips**:
- Test in demo mode first (no game logic)
- Add print statements in adapter sync_state()
- Use pygame debug overlays
- Check animation event queue

## Estimated Timeline

- **Phase 1** (Game Logic): 1-2 weeks
- **Phase 2** (Input): 2-3 weeks
- **Phase 3** (UI): 2-3 weeks
- **Phase 4** (Animations): 3-4 weeks
- **Phase 5** (Menus): 2-3 weeks
- **Phase 6** (Save/Load): 1-2 weeks
- **Phase 7** (Polish): 2-3 weeks

**Total**: ~15-20 weeks for full implementation

---

**Current Status**: Phase 0 complete, Phase 1 starting

**Next Action**: Run `python run_graphical.py` and verify demo scene works

---

*Created: 2025-11-21*
