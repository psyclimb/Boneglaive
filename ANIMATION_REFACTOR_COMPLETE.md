# Animation System Refactor - COMPLETE ✅

**Date:** 2025-11-22
**Status:** Phase 4 (Animations) - Major refactoring complete

## What Was Accomplished

### 1. Architecture Refactor ✅
- **Moved all animation logic from `renderer.py` into dedicated animation classes**
- **One file per unit:** `glaiveman.py`, `potpourrist.py`, `mandible_foreman.py`
- **Deleted `pry_animation.py`** - consolidated into `glaiveman.py`
- **Removed all `demo_animations` dependencies** - game is fully self-contained

### 2. Animation Implementations ✅

**GLAIVEMAN (Complete):**
- ✅ JUDGEMENT - Spinning glaive projectile with critical lightning
- ✅ PRY - Enemy launch to ceiling with debris splash damage
- ✅ VAULT - Acrobatic leap with 360-degree flip (sprite rotation)
- ✅ AUTOCLAVE - Lightning bolt effect

**All animations:**
- Visual only (no damage application)
- Managed by AnimationFactory
- Damage numbers appear AFTER animations complete

### 3. Key Technical Achievements ✅

**Damage Timing Fix:**
- Game logic (`skills.py`) handles all damage/HP changes
- Animations queue damage events during playback
- `pending_animation_events` shown when animations finish
- Works for ALL skills/attacks (present and future)

**Consistent Structure:**
```
animations/
├── core.py              # Base classes
├── animation_factory.py # Skill name → animation class mapping
├── glaiveman.py         # All GLAIVEMAN animations
├── potpourrist.py       # All POTPOURRIST animations
└── mandible_foreman.py  # All MANDIBLE FOREMAN animations
```

**Two Animation Patterns:**
1. **Object-based:** Self-contained (e.g., `SpinningGlaiveProjectile`)
2. **Attribute-based:** Manipulates unit properties (e.g., `PryAnimationController`, `VaultAnimationController`)

### 4. Sprite Rotation Support ✅
- Added rotation support to `AnimatedUnit.draw()` in `core.py`
- Checks for `wind_up_rotation` attribute and applies `pygame.transform.rotate()`
- Used by VAULT for 360-degree flip

## Important Files

**Updated:**
- `boneglaive/graphical/animations/glaiveman.py` - All GLAIVEMAN animations
- `boneglaive/graphical/animations/core.py` - Added sprite rotation support
- `boneglaive/graphical/animations/animation_factory.py` - Maps skills to animations
- `boneglaive/graphical/renderer.py` - Simplified, no animation logic
- `boneglaive/graphical/ui_adapter.py` - Uses local animations, not demo
- `CLAUDE.org` - Added "Animation Architecture" section

**Deleted:**
- `boneglaive/graphical/animations/pry_animation.py` - Consolidated into glaiveman.py

## Next Steps

**Pending:**
- Test POTPOURRIST animations (all skills)
- Test MANDIBLE FOREMAN animations (all skills)

## Critical Patterns to Maintain

**When adding new animations:**
1. Create class in unit file (e.g., `glaiveman.py`)
2. Add to `animation_factory.py` SKILL_ANIMATIONS dict
3. Handle special constructor args in factory's `create_animation()` if needed
4. Export in `animations/__init__.py`

**Anti-patterns (DON'T):**
- ❌ Animation logic in `renderer.py` update loop
- ❌ Separate file per animation
- ❌ Animations applying damage
- ❌ Special-case handling outside factory

## Testing

**Run:** `python run_graphical.py`

**Test GLAIVEMAN:**
- Select GLAIVEMAN
- Press 1 (JUDGEMENT) - should see spinning glaive, critical lightning on low HP enemies
- Press 2 (PRY) - should see enemy launch to ceiling, debris fall on adjacent units
- Press 3 (VAULT) - should see acrobatic leap with 360-degree flip
- Press 4 (AUTOCLAVE) - should see lightning bolt

**Verify:**
- Damage numbers appear AFTER animations complete
- No double damage
- Sprites rotate during VAULT
