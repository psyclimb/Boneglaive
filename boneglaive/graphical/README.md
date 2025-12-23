# Boneglaive Graphical Version

Modern graphical renderer for Boneglaive using pygame.

## Architecture Overview

```
boneglaive/
├── game/              # Existing ASCII game logic (DO NOT MODIFY)
├── graphical/         # NEW - Graphical version
│   ├── renderer.py         # Main pygame renderer
│   ├── game_state.py       # Adapter between game logic and graphics
│   ├── ui/                 # UI components
│   ├── animations/         # Skill/effect animations
│   └── assets/             # Sprites, fonts, sounds
└── demo_animations/   # Reference animations (standalone demo)
```

## Design Philosophy

**Separation of Concerns**: The graphical version is a *visualization layer* on top of the existing game logic. The ASCII game continues to work independently.

**Adapter Pattern**: `GameStateAdapter` bridges the ASCII game logic with the graphical renderer:
- Game logic runs "headless" (no direct pygame interaction)
- Adapter polls game state each frame
- State changes generate animation events
- Renderer displays visual representation

## Key Components

### GameStateAdapter (`game_state.py`)

Responsibilities:
- Maintain connection to game logic instance
- Detect state changes (HP, position, status effects)
- Generate animation events
- Translate player input from renderer to game commands
- Keep visual units synchronized with game units

Key Methods:
- `sync_state()` - Poll game state, detect changes, return animation events
- `handle_player_action()` - Process player input and send to game logic
- `queue_skill_animation()` - Queue a skill animation to play
- `get_game_state()` - Get current game state for UI display

### GraphicalRenderer (`renderer.py`)

Responsibilities:
- Manage pygame window and rendering
- Handle player input (mouse, keyboard)
- Update and draw all visual elements
- Coordinate animations with game state
- Render UI elements

Key Methods:
- `handle_events()` - Process pygame events
- `update(delta_time)` - Update game state and animations
- `draw()` - Render current frame
- `handle_grid_click()` - Process grid tile clicks

## Current Status

### ✅ Completed
- Package structure created
- `GameStateAdapter` skeleton with event system
- `GraphicalRenderer` skeleton with basic rendering
- Grid rendering and mouse interaction
- Demo scene setup (for testing without game logic)

### 🚧 TODO - Critical Path

#### Phase 1: Basic Rendering (CURRENT)
1. Test the skeleton:
   ```bash
   cd /home/user/boneglaive
   python -m boneglaive.graphical.renderer
   ```
2. Verify grid renders and demo units appear
3. Test mouse hover and click on grid

#### Phase 2: Game Logic Integration
1. **Study existing game structure**:
   - Read `boneglaive/game/` to understand architecture
   - Identify main game loop
   - Find unit class structure
   - Locate skill execution code

2. **Hook up GameStateAdapter**:
   - Import actual game classes (currently commented out)
   - Initialize real game instance in `initialize_game()`
   - Implement `_get_unit_id()` based on actual unit structure
   - Map game units to visual units in `create_visual_unit()`

3. **Implement state synchronization**:
   - Complete `sync_state()` to detect real HP/position changes
   - Add event hooks in game logic (if needed) for skill usage
   - Test with simple combat scenario

#### Phase 3: Animation Integration
1. Copy core animations from `demo_animations/` to `graphical/animations/`
2. Create animation factory in renderer
3. Implement `handle_animation_event()` to spawn animations
4. Test one skill end-to-end (JUDGEMENT recommended)

#### Phase 4: Input Handling
1. Implement unit selection
2. Add movement range visualization
3. Implement movement
4. Add skill selection UI
5. Implement skill targeting
6. Add turn management (end turn button)

#### Phase 5: UI Layer
1. Unit info panel (HP, AP, status)
2. Skill bar with hotkeys
3. Turn order display
4. Combat log
5. Win/loss screens

## Running the Graphical Version

### Current (Demo Mode)
```bash
cd /home/user/boneglaive
python -m boneglaive.graphical.renderer
```

This runs with dummy units and no game logic (for testing renderer).

### Future (Game Mode)
```bash
# Once game logic is hooked up:
python -m boneglaive.graphical.main
```

## Development Guidelines

### File Organization
- **One class per file** for UI components
- **Group animations by unit** (e.g., `animations/glaiveman.py`)
- **Keep game logic separate** - never import `boneglaive.game` in renderer, only in adapter

### Code Style
- Follow existing demo_animations patterns for consistency
- Use type hints for clarity
- Document complex algorithms (bezier curves, easing functions, etc.)
- Add TODO comments for missing implementations

### Testing Strategy
1. **Renderer tests**: Run with demo scene, verify visual correctness
2. **Adapter tests**: Run with mock game instance, verify state sync
3. **Integration tests**: Run with real game, verify full loop

### Performance Considerations
- Particle limits (max 500 on screen)
- Animation pooling for frequently used effects
- Sprite caching
- Consider spatial partitioning if many units (not needed yet)

## Animation System

### Animation Event Flow
```
Game Logic → State Change → Adapter Detects → Animation Event → Renderer Creates Animation → Visual Display
```

### Animation Types
- **Blocking**: Skill executions (game waits for animation to finish)
- **Non-blocking**: Passive effects (play alongside other animations)
- **Instant**: State changes (HP bars, position updates)

### Creating New Animations
1. Create animation class in `animations/`
2. Add to animation registry in renderer
3. Hook up in `handle_animation_event()`

## Next Steps for Developer

**Immediate** (this session):
1. Run `python -m boneglaive.graphical.renderer`
2. Verify demo scene works
3. Test mouse interaction

**Short-term** (next session):
1. Study `boneglaive/game/` structure
2. Identify main game class and entry point
3. Map game units to visual units
4. Get one real unit rendering from game logic

**Medium-term** (next few sessions):
1. Implement one complete skill (JUDGEMENT)
2. Get basic combat working
3. Add UI for skill selection

**Long-term**:
1. Port all animations
2. Build full UI
3. Add menus, save/load
4. Polish and optimize

## Questions / Design Decisions Needed

1. **Event hooks**: Do we modify game logic to emit events, or poll for changes?
   - Current: Polling (less invasive)
   - Alternative: Event emission (cleaner but requires game code changes)

2. **Animation blocking**: How to prevent game from advancing during animations?
   - Current: Adapter checks if animations are playing before allowing actions
   - Alternative: Game logic has callbacks for animation completion

3. **Coordinate systems**: Grid coords vs pixel coords?
   - Current: Grid coords in game logic, pixel coords in renderer
   - Adapter handles conversion

4. **Unit identification**: How to uniquely identify units?
   - Current: Using unit.name (may not be unique)
   - Need: Proper unique ID system

## Resources

- pygame docs: https://www.pygame.org/docs/
- demo_animations: Reference implementation for visual effects
- ASCII game: Source of truth for game logic

---

*Last updated: 2025-11-21*
