# Marrow Dike Wall Despawn Animation - Implementation Complete

## Summary
Created a crumbling wall animation for when Marrow Dike walls naturally expire after 3 turns. The animation shows bone walls developing stress fractures, breaking apart into falling fragments with realistic gravity physics, and dissipating into dust. This provides visual feedback when walls expire instead of just disappearing with a text message.

## Files Modified

### 1. boneglaive/graphical/animations/marrow_condenser.py (Lines 1492-1871)
**Added:** 4 new animation classes totaling ~380 lines
- Lines 1496-1574: `WallCrack` class - Stress fracture lines with pulsing blood glow
- Lines 1576-1669: `FallingFragment` class - Bone chunks with gravity, rotation, irregular shapes
- Lines 1671-1724: `DustParticle` class - Fine dust rising upward (negative gravity)
- Lines 1726-1871: `MarrowDikeWallDespawnAnimation` class - Main 3-phase controller

### 2. boneglaive/graphical/animations/animation_factory.py
**Changes:**
- Line 47: Added import for `MarrowDikeWallDespawnAnimation`
- Line 94: Registered "MARROW_DIKE_WALL_DESPAWN" skill with `MarrowDikeWallDespawnAnimation` class
- Lines 534-553: Added handler in `create_animation()` method for wall despawn

### 3. boneglaive/graphical/animations/__init__.py
**Changes:**
- Line 71: Added import for `MarrowDikeWallDespawnAnimation`
- Line 128: Added `MarrowDikeWallDespawnAnimation` to `__all__` exports list

## Animation Details

### Color Scheme (MARROW CONDENSER Palette)
- **Primary Bone (Bright)**: RGB(240, 232, 216) - #f0e8d8 - (reserved)
- **Secondary Bone (Pale)**: RGB(224, 213, 197) - #e0d5c5 - Large fragments, dust
- **Tertiary Bone (Dark)**: RGB(208, 197, 181) - #d0c5b5 - Small debris
- **Muscle Red (Deep)**: RGB(200, 80, 80) - #c85050 - Crack inner glow
- **Blood Red (Dark)**: RGB(139, 0, 0) - #8b0000 - Main crack color, fragment outlines

### Animation Phases (Total: ~1.5 seconds)

#### Phase 1: Cracking (0.4s)
**Visual Elements:**
- 5-7 stress fracture lines emanate from random points on wall surface
- Each crack spreads outward from origin to max length (15-25 pixels)
- Cracks have branching sub-cracks at 60° angles
- Main crack color: Dark blood red (139, 0, 0)
- Inner glow: Muscle red (200, 80, 80)
- Cracks pulse at 8 Hz (sine wave modulation)
- Staggered appearance: Each crack delayed by 0.05s

**Screen Effects:**
- Light shake (intensity 2, duration 0.3s) - wall stress

**Technical:**
- Crack angle: Random 0-2π radians
- Crack length: Random 15-25 pixels
- Pulse phase: Randomized per crack
- Extension: Linear with progress
- Alpha: 180 * progress * pulse (0.6-1.0 range)

#### Phase 2: Crumbling (0.6s)
**Visual Elements:**
- **Large fragments** (8-12 per wall):
  - Size: 6-12 pixels
  - Color: Pale bone (224, 213, 197)
  - Irregular 5-point polygon shape
  - Outlined with blood red (139, 0, 0)

- **Small debris** (15-20 per wall):
  - Size: 3-6 pixels
  - Color: Dark bone (208, 197, 181)
  - Outlined with blood red

- **Fragment physics**:
  - Initial velocity: (-40 to 40, -80 to -20) px/s (horizontal spread, upward kick)
  - Gravity: 350 px/s² downward
  - Rotation: -4 to 4 radians/second
  - Spawn origin: Random within tile bounds

- **Rising dust** (15-20 particles):
  - Size: 1-3 pixels
  - Color: Pale cream (224, 213, 197)
  - Rise velocity: -70 to -50 px/s (negative = upward)
  - Horizontal drift: -15 to 15 px/s
  - Fast fade (0.4-0.8s lifespan)

**Screen Effects:**
- Medium shake (intensity 4, duration 0.4s) - wall collapse

**Technical:**
- Fragment spawn: Random offsets within TILE_SIZE
- Fragment alpha: 255 until 30% progress, then fade
- Dust alpha: Fade in (0-0.2), fade out (0.2-1.0)
- Rotation applied via 2D rotation matrix
- Irregular polygon: 5 asymmetric points per fragment

#### Phase 3: Dissipation (0.5s)
**Visual Elements:**
- Existing fragments continue falling and fading
- Existing dust continues rising and fading
- No new effects spawned
- All particles fade to alpha 0

**Screen Effects:**
- No shake (settling phase)

**Technical:**
- Continues updating fragment/dust positions
- Alpha decay for remaining particles
- Phase completes when timer >= 0.5s

## Technical Implementation

### Irregular Fragment Shape
Fragments are drawn as 5-point irregular polygons for natural appearance:
```python
half_size = self.size / 2
points = [
    (x - half_size * 0.8, y - half_size),      # Top-left
    (x + half_size * 0.6, y - half_size * 0.7), # Top-right
    (x + half_size, y + half_size * 0.5),       # Right
    (x + half_size * 0.3, y + half_size),       # Bottom-right
    (x - half_size * 0.9, y + half_size * 0.6)  # Bottom-left
]
```

### Gravity Physics
Realistic falling motion with acceleration:
```python
# Apply gravity each frame
self.vy += gravity * delta_time  # gravity = 350 px/s²

# Update position
self.x += self.vx * delta_time
self.y += self.vy * delta_time

# Update rotation
self.rotation += self.rotation_speed * delta_time
```

### Crack Branching
Each crack has two sub-branches at 45° angles:
```python
branch_angle1 = self.angle + math.pi / 4  # +45°
branch_angle2 = self.angle - math.pi / 4  # -45°
branch_len = current_length * 0.3          # 30% of main crack
```

### Coordinate Handling
✅ Uses standard camera.grid_to_screen() pattern:
```python
# Input: target_pos = (grid_y, grid_x) - wall position
grid_y, grid_x = target_pos
self.center_x, self.center_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

# All particles spawn relative to this center
```

## Verification Results

✅ **Syntax Check:**
- marrow_condenser.py: OK (1871 lines total)
- animation_factory.py: OK
- __init__.py: OK

✅ **Import Verification:**
- `from boneglaive.graphical.animations import MarrowDikeWallDespawnAnimation` - SUCCESS
- Class name confirmed: MarrowDikeWallDespawnAnimation

✅ **Registration Verification:**
- `AnimationFactory.has_animation('MARROW_DIKE_WALL_DESPAWN')` - True
- Registered class: MarrowDikeWallDespawnAnimation
- Factory creates animation correctly

✅ **Return Values:**
- All `update()` methods return boolean (True if active, False when done)
- WallCrack.update() ✓
- FallingFragment.update() ✓
- DustParticle.update() ✓
- MarrowDikeWallDespawnAnimation.update() ✓

✅ **Coordinate Pattern:**
- Follows standard from ANIMATION_IMPLEMENTATION_GUIDE.md
- Wall position: `camera.grid_to_screen(grid_x, grid_y, centered=True)` ✓
- All particles spawned relative to wall center ✓

## Integration Notes

**Animation Triggering:**
This animation is designed to be triggered when Marrow Dike walls expire in engine.py:3330-3351. Integration will require:

1. **Location:** boneglaive/game/engine.py, lines ~3330-3351
2. **Trigger Point:** When `dike_info['duration'] <= 0` for each wall
3. **Required Info:** Wall position (tile_y, tile_x)

**Example integration pattern:**
```python
# In engine.py when processing expired walls
for tile_y, tile_x in tiles_to_remove:
    # Create despawn animation for this wall
    if renderer and hasattr(renderer, 'create_animation'):
        renderer.create_animation(
            skill_name="MARROW_DIKE_WALL_DESPAWN",
            target_pos=(tile_y, tile_x),
            camera=camera
        )

    # Then restore terrain and delete from tracking
    # ... existing cleanup code ...
```

**Note:** This integration is SEPARATE from the animation implementation and would be handled in a future task.

## Testing Instructions

### Standalone Testing (Without Integration)
Since wall despawn triggering requires game engine integration, the animation can be tested independently:

```python
# In Python console or test script
from boneglaive.graphical.animations import MarrowDikeWallDespawnAnimation
from boneglaive.graphical.camera import Camera
import pygame

# Setup pygame and camera
pygame.init()
screen = pygame.display.set_mode((800, 600))
camera = Camera(...)

# Create animation at a test position
wall_pos = (5, 5)  # Grid position
animation = MarrowDikeWallDespawnAnimation(
    caster_unit=None,
    target_unit=None,
    target_pos=wall_pos,
    is_crit=False,
    is_infused=False,
    particle_emitter=None,
    debris_list=[],
    screen_shake_callback=lambda i, d: None,
    screen_flash_callback=lambda c, d: None,
    units_list=[],
    camera=camera,
    game=None
)

# Update and draw in game loop
while animation.update(delta_time):
    animation.draw(screen)
    pygame.display.flip()
```

### Expected Results

**Phase 1 (0.4s) - Cracking:**
- [ ] 5-7 dark red cracks appear on wall tile
- [ ] Cracks spread outward from random origin points
- [ ] Each crack has 2 branching sub-cracks
- [ ] Cracks pulse with blood red glow
- [ ] Staggered appearance creates cascading effect
- [ ] Light screen shake during cracking

**Phase 2 (0.6s) - Crumbling:**
- [ ] 8-12 large pale bone fragments spawn
- [ ] 15-20 small dark bone debris pieces spawn
- [ ] Fragments have irregular 5-point shapes
- [ ] Fragments rotate as they fall
- [ ] Fragments have initial upward kick, then fall with gravity
- [ ] 15-20 pale dust particles rise upward
- [ ] Dust particles drift horizontally
- [ ] Medium screen shake during collapse

**Phase 3 (0.5s) - Dissipation:**
- [ ] Falling fragments continue moving and fade out
- [ ] Rising dust continues moving and fades out
- [ ] No new effects spawn
- [ ] All particles reach alpha 0 by end
- [ ] No screen shake (quiet settling)

**Overall:**
- [ ] Animation duration: ~1.5 seconds total
- [ ] Animation centered on wall tile position
- [ ] Fragments spawn within tile bounds
- [ ] Dust rises opposite to fragment falling (visual contrast)
- [ ] No coordinate misalignment
- [ ] No graphical glitches or artifacts
- [ ] Colors match MARROW CONDENSER sprite theme
- [ ] Animation completes before returning False

### Common Issues to Check

**Animation doesn't appear:**
- Check console for "[AnimationFactory] Created MarrowDikeWallDespawnAnimation for MARROW_DIKE_WALL_DESPAWN"
- Verify target_pos is provided (required)
- Ensure camera is passed correctly

**Fragments appear at wrong locations:**
- Verify camera tracking is correct
- Check grid_to_screen conversion
- Fragments should spawn within ±TILE_SIZE/2 of wall center

**Fragments don't fall:**
- Check gravity constant (350 px/s²)
- Verify delta_time is being passed correctly
- Check initial_vy is negative (upward kick)

**Cracks don't branch:**
- Verify crack length > 10 pixels
- Check branch angle calculation (±π/4)
- Ensure alpha > 0 for branch drawing

**Animation disappears immediately:**
- Verified: All update() methods return True when active
- Should not occur with current implementation

**Animation never ends:**
- Check phase transition logic (>= not >)
- Verify timer increments properly
- Final phase should set self.active = False at 0.5s

## Integration Status

✅ **File Updates:**
- [x] marrow_condenser.py - Added 4 classes (3 helpers + main controller)
- [x] All classes follow ANIMATION_IMPLEMENTATION_GUIDE.md patterns
- [x] Proper imports and pygame usage
- [x] Total file size: 1871 lines

✅ **Animation Factory Registration:**
- [x] Import added to animation_factory.py
- [x] "MARROW_DIKE_WALL_DESPAWN" registered in SKILL_ANIMATIONS dict
- [x] Handler added in create_animation() method
- [x] Requires target_pos (wall position)

✅ **Package Exports:**
- [x] Import added to __init__.py
- [x] MarrowDikeWallDespawnAnimation added to __all__ list

✅ **Verification:**
- [x] Python syntax valid for all files
- [x] Import successful
- [x] Registration confirmed
- [x] Coordinate pattern verified
- [x] Return values verified

⏳ **Game Engine Integration:**
- [ ] Hook into engine.py:3330-3351 (wall expiration)
- [ ] Trigger animation for each expiring wall
- [ ] Animation plays before terrain restoration
- **Note:** This is a separate task requiring engine.py modifications

## Animation Design Rationale

The Marrow Dike Wall Despawn animation visually represents the natural degradation and collapse of temporary bone structures:

1. **Cracking Phase** - Shows structural weakness developing. The pulsing blood glow in cracks suggests the marrow "life force" bleeding out. Multiple crack origins create organic, chaotic failure pattern rather than uniform collapse.

2. **Crumbling Phase** - Violent breakdown into constituent materials. Mix of large chunks and small debris creates realistic demolition. Fragments get initial upward kick (explosive force), then gravity takes over for natural arcing fall. Rising dust opposes falling fragments for visual richness and depth.

3. **Dissipation Phase** - Materials dissolve back into nothing, representing temporary magical construct fading. No new effects keeps focus on existing particles' graceful fadeout.

### Key Visual Choices:

- **Irregular fragments**: 5-point asymmetric polygons feel more natural than circles/squares
- **Rotation during fall**: Adds realism and visual interest to tumbling debris
- **Rising dust vs falling chunks**: Creates visual contrast and depth perception
- **Pulsing cracks**: Suggests life force draining, connects to Bone Tithe's blood theme
- **Staggered cracks**: Cascading failure feels more organic than instant shattering
- **Gravity physics**: Parabolic arcs are visually satisfying and realistic
- **Dark blood outlines**: Ties fragments back to anatomical marrow theme

## Performance Considerations

**Particle Count:**
- Per wall: 5-7 cracks + 8-12 large fragments + 15-20 small fragments + 15-20 dust = ~55-59 visual elements
- Multiple walls expiring: Animation instance per wall (independent)
- Total peak for 16 walls: ~880-944 particles (if all expire simultaneously)

**Optimization:**
- Particle culling: Inactive particles removed from update lists
- Simple physics: Linear velocity + gravity (minimal computation)
- Small surfaces: Fragments use small SRCALPHA surfaces
- Short duration: 1.5s animation completes quickly
- Staggered spawning: Not all particles active at once

**Memory:**
- Lightweight particle objects (position, velocity, rotation, timer)
- No texture loading (all procedural drawing)
- Particles auto-cleanup when finished

## Next Steps

**MARROW CONDENSER Animation Status:**
1. ✅ **Ossify** - Defensive bone compression (COMPLETE)
2. ✅ **Bone Tithe** - Life-draining marrow extraction (COMPLETE)
3. ✅ **Marrow Dike** - Wall eruption perimeter (COMPLETE)
4. ✅ **Marrow Dike Wall Despawn** - Wall crumbling (COMPLETE)

**Future Enhancements:**
- Engine integration: Hook animation into wall expiration logic (engine.py)
- Wall damage animation: When walls take damage but don't break
- Staggered despawns: If multiple walls expire, cascade the animations
- Sound effects: Cracking, crumbling, debris sounds

All four MARROW CONDENSER skill animations are now complete, using the consistent color palette and anatomical bone/marrow theme!
