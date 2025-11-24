# Boneglaive Animation Demo (Modular)

This is the modular version of the Boneglaive animation demo, refactored from a single 5000+ line file into a clean package structure.

## Structure

```
demo_animations/
├── __init__.py          # Package exports
├── core.py              # Shared classes (Particle, AnimatedUnit, etc.)
├── glaiveman.py         # GLAIVEMAN skill animations
├── mandible_foreman.py  # MANDIBLE FOREMAN skill animations
├── potpourrist.py       # POTPOURRIST skill animations
├── main.py              # Main demo coordinator
└── README.md            # This file
```

## Module Breakdown

### core.py (~458 lines)
**Shared animation framework:**
- `Particle` - Basic particle with velocity, color, size, lifetime
- `ParticleEmitter` - Manages burst, trail, float, beam particles
- `AnimatedUnit` - Unit with smooth movement, shake, hop, aura effects
- `FloatingText` - Damage/heal numbers with float animation
- `DebrisParticle` - Falling rock chunks with rotation physics

### glaiveman.py (~492 lines)
**GLAIVEMAN skill animations:**
- `LightningBolt` - Jagged lightning strike from above
- `CrossBeam` - Expanding cross-shaped steam jets with spinning glaives
- `SpinningGlaiveProjectile` - Six-bladed spinning projectile with trail

### mandible_foreman.py (~1425 lines)
**MANDIBLE FOREMAN skill animations:**
- `JawClamp` - Four-directional mechanical jaws + insect mandibles
- `ViseroyTrap` - Steaming bear trap deployment
- `ViseroyRelease` - Explosive trap spring with projectile
- `SiteInspectionBuff` - Golden scanning animation with stat overlay
- `SiteInspectionScan` - Expanding scan wave
- `ExpediteRush` - High-speed charging attack with steam trail
- `JawlineNetwork` - 3x3 grid of networked bear traps with cables

### potpourrist.py (~633 lines)
**POTPOURRIST skill animations:**
- `PedestalStrike` - Heavy pedestal impact with shockwave and debris
- `InfuseEffect` - Swirling potpourri petals with fragrance waves
- `DemiluneSwing` - Arc swing with stone debris (regular + infused variants)
  - Regular: Gray arc, brown debris, 3 damage
  - Infused: Gold arc, colorful potpourri trail with fumes, 4 damage

### main.py (~2240 lines)
**Demo coordinator:**
- `ModernRendererDemo` - Main pygame loop, unit management, skill sequencing
- Handles TAB to cycle between unit modes
- SPACE to trigger next skill in sequence
- Sprite loading, grid rendering, camera shake, effects management

## Running the Demo

```bash
# From boneglaive directory:
python3 -m demo_animations.main

# Or with the monolithic version (deprecated):
python3 demo_modern_renderer_pygame.py
```

## Controls

- **SPACE** - Trigger next skill in sequence
- **TAB** - Cycle between GLAIVEMAN, MANDIBLE_FOREMAN, POTPOURRIST
- **ESC** - Exit demo

## Benefits of Modular Structure

1. **Maintainability** - Each unit's animations in separate file
2. **Readability** - ~500-1400 lines per module vs 5000+ monolithic
3. **Reusability** - Import only what you need
4. **Collaboration** - Multiple developers can work on different units
5. **Testing** - Easier to test individual animation classes
6. **Organization** - Clear separation of concerns

## Adding New Units

To add a new unit's animations:

1. Create `demo_animations/new_unit.py`
2. Import core classes: `from .core import TILE_SIZE, Particle, etc`
3. Define animation classes
4. Add exports to `__init__.py`
5. Import in `main.py` and add skill handlers
6. Add to unit mode cycle in `handle_events()`

## Original Monolithic File

The original `demo_modern_renderer_pygame.py` (5085 lines) is preserved for backwards compatibility but should be considered deprecated. All new development should use the modular structure.
