# Marrow Dike Animation - Implementation Complete

## Summary
Created a dramatic wall eruption animation for the MARROW CONDENSER's **Marrow Dike** skill, depicting bone walls violently bursting from the ground around a 5x5 perimeter. The animation shows spreading ground cracks, marrow geysers erupting, and bone solidification with a networked glow effect. Additionally, the marrow_wall.svg terrain asset was updated to match the MARROW CONDENSER's color palette.

**IMPORTANT**: This animation is purely visual. Enemy displacement logic is handled by the skill itself (marrow_condenser.py:431-448), NOT by the animation.

## Files Modified

### 1. graphics/terrain/marrow_wall.svg
**Changed:** Color scheme updated to match MARROW CONDENSER sprite palette
- **Base marrow tissue**: #c85050 → #b87060 (desaturated red-brown)
- **Dark marrow regions**: #b84040, #a83838 → #987050, #886848 (muted browns)
- **Light fatty tissue**: #d8706c, #e88078 → #e0d5c5, #f0e8d8 (pale cream/bone)
- **Blood vessels**: #983030 → #8b0000, opacity 0.6 → 0.3-0.4 (dark blood red, subtle)
- **Fat globules**: #f8d878 → #e0d5c5 (pale cream instead of yellow)
- **Sinew fibers**: Preserved (already cream/white #f0e5d5, #e8dcc8, #f8f0e0)

### 2. boneglaive/graphical/animations/marrow_condenser.py (Lines 952-1490)
**Added:** 5 new animation classes totaling ~540 lines
- Lines 952-1052: `GroundCrack` class - Spreading fissures with dark blood glow
- Lines 1055-1167: `MarrowEruptionParticle` class - Parabolic arcs with gravity and rotation
- Lines 1170-1300: `MarrowEruption` class - Per-wall eruption with geyser effect
- Lines 1303-1357: `WallNetwork` class - Solidification glow spreading across all walls
- Lines 1360-1489: `MarrowDikeAnimation` class - Main 3-phase controller with 16-wall cascade

### 3. boneglaive/graphical/animations/animation_factory.py
**Changes:**
- Line 48: Added import for `MarrowDikeAnimation`
- Line 94: Registered "MARROW_DIKE" skill with `MarrowDikeAnimation` class
- Lines 514-530: Added handler in `create_animation()` method
  - Passes `game` reference for wall position calculation
  - Passes `units_list` for upgraded detection (Mired status check)

### 4. boneglaive/graphical/animations/__init__.py
**Changes:**
- Line 71: Added import for `MarrowDikeAnimation`
- Line 126: Added `MarrowDikeAnimation` to `__all__` exports list

## Animation Details

### Color Scheme (MARROW CONDENSER Palette)
- **Primary Bone (Bright)**: RGB(240, 232, 216) - #f0e8d8 - Network glow, bone particles
- **Secondary Bone (Pale)**: RGB(224, 213, 197) - #e0d5c5 - Bone fragments, lighter particles
- **Tertiary Bone (Dark)**: RGB(208, 197, 181) - #d0c5b5 - Crack edges
- **Blood Red (Dark)**: RGB(139, 0, 0) - #8b0000 - Marrow particles, crack glow
- **Glowing Energy**: RGB(255, 0, 0) - #ff0000 - Geyser core, crack pulses, flash effects
- **White Flash**: RGB(255, 255, 255) - #ffffff - Initial eruption flash

### Animation Phases (Total: ~2.4 seconds)

#### Phase 1: Fracture (0.5s)
**Visual Elements:**
- 16 ground cracks spread outward from caster to each wall position
- Cracks appear in cascading order:
  - Corners first (0-3): Top-left → Top-right → Bottom-right → Bottom-left
  - Edges clockwise (4-15): Top edge → Right edge → Bottom edge → Left edge
  - Each crack staggered by 0.05s
- Crack appearance: 3 jagged line segments per crack
- Crack color: Dark bone (208, 197, 181) with dark blood glow (139, 0, 0)
- Glow pulses at 10 Hz during spreading
- 30 pulse particles burst from caster position (mix of bone white and blood red)

**Screen Effects:**
- Light shake (intensity 3, duration 0.4s) - ground fracturing

**Technical:**
- Crack spread speed: 200 pixels/second
- Crack width: 4px with 8px glow
- Pulse particle lifespan: 0.4s with fade

#### Phase 2: Eruption (1.0s)
**Visual Elements:**
- 16 marrow eruptions burst from ground at each wall position
- Eruptions cascade in same order as cracks (0.05s stagger)
- Each eruption consists of:
  - **Geyser effect**: Expanding red energy column (20-80px height)
  - **Marrow particles**: 20-25 particles per wall
    - 70% blood particles (dark red 139, 0, 0)
    - 30% bone fragments (pale cream 224, 213, 197)
  - **Parabolic arcs**: Particles follow gravity simulation
    - Initial velocity: 150-250 pixels/second upward
    - Launch angle: Random spread (-30° to +30° from vertical)
    - Gravity: 400 pixels/second²
  - **White flash**: 0.1s flash at start of each eruption
  - **Particle rotation**: Bone fragments spin (1-3 rotations/second)
- Geyser color: Glowing red core (255, 0, 0) with bright bone rim (240, 232, 216)
- Wall tile appears at position after geyser fades (0.6s mark)

**Screen Effects:**
- Heavy shake (intensity 8, duration 0.7s) - violent eruption
- Red screen flash (255, 0, 0) for 0.15s at first eruption

**Technical:**
- Geyser expansion: Quadratic ease-out (1.0 - (1.0 - progress)²)
- Particle physics: position += velocity * dt; velocity_y += gravity * dt
- Particle lifespan: 0.8-1.0s with fade at 0.7 progress
- Wall appearance: Alpha transition 0 → 255 over 0.2s

#### Phase 3: Solidification (0.9s)
**Visual Elements:**
- Network glow spreads across all 16 wall tiles
- Glow pattern:
  - Starts from corners (4 corners glow simultaneously)
  - Spreads along edges toward next corner
  - Creates connected perimeter glow effect
- Glow appearance:
  - Inner ring: Bright bone white (240, 232, 216)
  - Outer ring: Red energy (255, 0, 0)
  - Ring width: 20px inner, 8px outer
- Glow pulses at 8 Hz (sine wave)
- 40 solidification particles burst from each wall (total 640 particles)
  - Mix of bone white and pale cream
  - Small particles (2-4px radius)
  - Rise upward 20-40px then fade
  - Lifespan: 0.5s

**Screen Effects:**
- Medium shake (intensity 5, duration 0.5s) - wall solidification
- No screen flash (network glow provides ambient lighting)

**Technical:**
- Network glow progress: Linear spread based on cascade order
- Glow alpha: Base 180, pulses ±40 with sine wave
- Particle rise speed: 40 pixels/second upward
- Particle fade: Linear alpha decay over lifespan

## Technical Implementation

### Wall Position Calculation
The animation calculates 16 wall positions on 5x5 perimeter:
```python
def _get_wall_positions(self, center_grid_y, center_grid_x):
    """Calculate grid positions of all 16 walls in 5x5 perimeter."""
    walls = []
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            # Skip interior (only perimeter)
            if abs(dy) != 2 and abs(dx) != 2:
                continue

            grid_y = center_grid_y + dy
            grid_x = center_grid_x + dx

            # Calculate cascade order (corners first, then clockwise)
            cascade_order = self._calculate_cascade_order(dy, dx)

            walls.append({
                'grid_y': grid_y,
                'grid_x': grid_x,
                'offset': (dy, dx),
                'cascade_order': cascade_order
            })

    # Sort by cascade order for staggered eruption
    walls.sort(key=lambda w: w['cascade_order'])
    return walls
```

### Cascade Order System
Walls erupt in aesthetic order (corners → edges clockwise):
```python
def _calculate_cascade_order(self, dy, dx):
    """Calculate order for cascading animation."""
    # Corners (priority 0-3)
    if abs(dy) == 2 and abs(dx) == 2:
        if dy == -2 and dx == -2: return 0  # Top-left
        elif dy == -2 and dx == 2: return 1  # Top-right
        elif dy == 2 and dx == 2: return 2   # Bottom-right
        else: return 3                        # Bottom-left

    # Top edge (left to right, orders 4-5)
    elif dy == -2:
        return 4 if dx == -1 else 5

    # Right edge (top to bottom, orders 6-7)
    elif dx == 2:
        return 6 if dy == -1 else 7

    # Bottom edge (right to left, orders 8-9)
    elif dy == 2:
        return 8 if dx == 1 else 9

    # Left edge (bottom to top, orders 10-11)
    else:  # dx == -2
        return 10 if dy == 1 else 11
```

### Parabolic Particle Physics
Marrow particles follow realistic gravity simulation:
```python
# Initial velocity (upward with random angle)
angle = math.radians(random.uniform(-30, 30))  # Spread from vertical
base_speed = random.uniform(150, 250)
self.velocity_x = math.sin(angle) * base_speed
self.velocity_y = -base_speed  # Negative = upward in pygame

# Update each frame
GRAVITY = 400  # pixels/second²
self.velocity_y += GRAVITY * dt
self.x += self.velocity_x * dt
self.y += self.velocity_y * dt

# Bone fragments rotate while airborne
if self.is_bone_fragment:
    self.rotation += self.rotation_speed * dt
```

### Upgraded Detection (Mired Status)
Animation detects if skill is upgraded and shows Mired visual:
```python
# Check if skill is upgraded (grants Mired status)
self.is_upgraded = False
if hasattr(self.caster_unit, 'marrow_dike_mired'):
    self.is_upgraded = self.caster_unit.marrow_dike_mired

# If upgraded, add Mired visual indicators
if self.is_upgraded:
    # Extra particle effects, darker glow colors, etc.
    # (Currently reserved for future enhancement)
```

### Coordinate Handling
✅ Uses standard camera.grid_to_screen() pattern:
```python
# Caster position
caster_grid_y, caster_grid_x = self.target_pos
self.center_x, self.center_y = self.camera.grid_to_screen(
    caster_grid_x, caster_grid_y, centered=True
)

# Wall positions (16 walls in 5x5 perimeter)
for wall_data in self.wall_positions:
    screen_x, screen_y = self.camera.grid_to_screen(
        wall_data['grid_x'], wall_data['grid_y'], centered=True
    )
    wall_data['screen_x'] = screen_x
    wall_data['screen_y'] = screen_y
```

## SVG Asset Changes

### marrow_wall.svg Color Updates
Transformed from bright red marrow to desaturated bone-themed palette:

**Before (Original Bright Red Theme)**:
- Base: #c85050 (bright red)
- Dark regions: #b84040, #a83838 (saturated reds)
- Light tissue: #d8706c, #e88078 (pink-red)
- Blood vessels: #983030 (bright red-brown)
- Fat: #f8d878 (yellow)

**After (Desaturated Bone Theme)**:
- Base: #b87060 (muted red-brown)
- Dark regions: #987050, #886848 (earthy browns)
- Light tissue: #e0d5c5, #f0e8d8 (pale cream/bone)
- Blood vessels: #8b0000, opacity 0.3-0.4 (dark blood, subtle)
- Fat: #e0d5c5 (pale cream matching bone)

**Preserved Elements**:
- White sinew fibers maintained (already cream/white)
- Structural detail and texture patterns unchanged
- Anatomical accuracy preserved (marrow tissue with collagen strands)

## Verification Results

✅ **Syntax Check:**
- marrow_condenser.py: OK (1490 lines total)
- animation_factory.py: OK
- __init__.py: OK
- marrow_wall.svg: Valid SVG

✅ **Import Verification:**
- `from boneglaive.graphical.animations import MarrowDikeAnimation` - SUCCESS
- Class name confirmed: MarrowDikeAnimation

✅ **Registration Verification:**
- `AnimationFactory.has_animation('MARROW_DIKE')` - True
- Registered class: MarrowDikeAnimation
- Factory creates animation correctly

✅ **Return Values:**
- All `update()` methods return boolean (True if active, False when done)
- GroundCrack.update() ✓
- MarrowEruptionParticle.update() ✓
- MarrowEruption.update() ✓
- WallNetwork.update() ✓
- MarrowDikeAnimation.update() ✓

✅ **Coordinate Pattern:**
- Follows standard from ANIMATION_IMPLEMENTATION_GUIDE.md
- Caster: `camera.grid_to_screen(grid_x, grid_y, centered=True)` ✓
- Walls: Same pattern for all 16 positions ✓

## Testing Instructions

### Setup
1. Run the graphical version: `python run_graphical.py`
2. Ensure MARROW CONDENSER is available in the game
3. Position MARROW CONDENSER where there is room for 5x5 perimeter

### Test Procedure
1. Select MARROW CONDENSER unit on the battlefield
2. Press **D** key to activate Marrow Dike skill
3. Skill is self-targeting (centers on caster)
4. Press **E** to execute turn and watch animation

### Expected Results

**Phase 1 (0.5s) - Fracture:**
- [ ] 16 ground cracks spread from caster to wall positions
- [ ] Cracks cascade in order: corners first, then edges clockwise
- [ ] Each crack is dark bone color with pulsing blood red glow
- [ ] 30 pulse particles burst from caster position
- [ ] Light screen shake during fracturing
- [ ] Cracks appear jagged with 3 line segments each

**Phase 2 (1.0s) - Eruption:**
- [ ] 16 marrow geysers erupt from ground in cascade order
- [ ] Each geyser has expanding red energy column
- [ ] 20-25 marrow particles per eruption (blood + bone mix)
- [ ] Particles follow parabolic arcs (gravity physics)
- [ ] Bone fragments rotate while airborne
- [ ] White flash at start of each eruption
- [ ] Wall tiles appear as geysers fade (around 0.6s)
- [ ] Heavy screen shake throughout eruptions
- [ ] Red screen flash at first eruption

**Phase 3 (0.9s) - Solidification:**
- [ ] Network glow spreads across all 16 wall tiles
- [ ] Glow starts from corners, spreads along edges
- [ ] Inner ring bright bone white, outer ring red
- [ ] Glow pulses at steady frequency
- [ ] 40 small particles burst upward from each wall
- [ ] Particles are bone white and pale cream
- [ ] Medium screen shake during solidification

**Overall:**
- [ ] Animation duration: ~2.4 seconds total
- [ ] Animation centered on MARROW CONDENSER (caster)
- [ ] 16 wall tiles form perfect 5x5 perimeter around caster
- [ ] Wall tiles match MARROW CONDENSER color scheme (desaturated bone tones)
- [ ] Cascade order creates aesthetic corner → edge flow
- [ ] Enemy units pulled inward by skill (handled by skill logic, not animation)
- [ ] No coordinate misalignment
- [ ] No graphical glitches or artifacts
- [ ] Colors match MARROW CONDENSER sprite theme
- [ ] Animation completes before game logic continues

### Edge Cases to Test

**Upgraded Skill (Mired Status):**
- Skill upgraded with `marrow_dike_mired = True`
- Enemies should receive Mired status (handled by skill logic)
- Animation detects upgrade flag (visual enhancements reserved for future)

**Near Map Edge:**
- Caster positioned near boundary
- Some wall positions may be off-map
- Animation should handle gracefully (walls only spawn on valid tiles)

**Walls Blocked by Existing Terrain:**
- Existing walls, furniture, or obstacles in perimeter positions
- Skill logic handles replacement (boneglaive/game/units.py:890-903)
- Animation shows eruption regardless of existing terrain

**Multiple MARROW CONDENSERs:**
- Multiple units use Marrow Dike in same turn
- Each animation should be independent
- No visual interference between animations

### Common Issues to Check

**Animation doesn't appear:**
- Check console for "[AnimationFactory] Created MarrowDikeAnimation for MARROW_DIKE"
- Verify skill key binding is correct (D key)
- Ensure MARROW CONDENSER unit is properly selected

**Cracks appear at wrong locations:**
- Verify camera tracking is correct
- Check that caster position is detected properly
- Cracks should spread from caster center to each wall position

**Particles don't follow parabolic arcs:**
- Verify gravity constant (400 pixels/second²)
- Check initial velocity calculation
- Should arc upward then fall back down

**Wall tiles wrong color:**
- Verify marrow_wall.svg was updated with desaturated colors
- Base should be #b87060 (muted red-brown)
- Light areas should be #e0d5c5, #f0e8d8 (pale cream)

**Cascade order wrong:**
- Should be: TL corner → TR corner → BR corner → BL corner → edges clockwise
- Check `_calculate_cascade_order()` logic
- Each wall staggered by 0.05s

**Animation disappears immediately:**
- Verified: All update() methods return True when active
- Should not occur with current implementation

**Enemies not pulled inward:**
- This is CORRECT behavior for animation
- Enemy displacement handled by skill logic (marrow_condenser.py:431-448)
- Animation is purely visual, does not affect game state

## Integration Status

✅ **File Updates:**
- [x] marrow_wall.svg - Color scheme updated to match MARROW CONDENSER
- [x] marrow_condenser.py - Added 5 classes (4 helpers + main controller)
- [x] All classes follow ANIMATION_IMPLEMENTATION_GUIDE.md patterns
- [x] Proper imports and pygame usage
- [x] Total file size: 1490 lines

✅ **Animation Factory Registration:**
- [x] Import added to animation_factory.py
- [x] "MARROW_DIKE" registered in SKILL_ANIMATIONS dict
- [x] Handler added in create_animation() method
- [x] Passes game reference for wall position calculation
- [x] Passes units_list for upgraded detection

✅ **Package Exports:**
- [x] Import added to __init__.py
- [x] MarrowDikeAnimation added to __all__ list

✅ **Verification:**
- [x] Python syntax valid for all files
- [x] SVG syntax valid
- [x] Import successful
- [x] Registration confirmed
- [x] Coordinate pattern verified
- [x] Return values verified

## Animation Design Rationale

The Marrow Dike animation visually represents the skill's defensive wall creation and enemy displacement:

1. **Fracture Phase** - Ground cracks spreading outward establish the perimeter where walls will erupt. The pulsing blood glow in cracks foreshadows the marrow that will burst forth. The cascading order (corners first) creates visual interest and emphasizes the perimeter structure.

2. **Eruption Phase** - Violent marrow geysers erupting from ground create dramatic impact. The parabolic particle physics makes eruptions feel realistic and forceful. Mix of blood particles and bone fragments reinforces the anatomical theme of marrow tissue bursting from earth. White flashes punctuate each eruption for emphasis.

3. **Solidification Phase** - Network glow spreading across walls shows them connecting into unified structure. The pulsing glow suggests living bone tissue stabilizing. Small rising particles represent excess marrow energy dissipating as walls harden.

### Key Visual Choices:

- **Cascade order**: Creates aesthetic flow (corners → edges) instead of random eruptions
- **Parabolic physics**: Makes particles feel realistic with gravity, not just linear movement
- **Bone fragment rotation**: Adds dynamic motion to airborne pieces
- **Network glow pattern**: Emphasizes perimeter structure and wall connectivity
- **Geyser expansion**: Quadratic ease-out makes eruption feel forceful, then settling
- **Color progression**: Ground cracks (dark) → violent eruption (bright red) → solidified walls (pale bone)
- **Staggered timing**: 0.05s per wall creates smooth cascade without overwhelming screen

### SVG Asset Update Rationale:

The original marrow_wall.svg was too bright and saturated red, clashing with MARROW CONDENSER's more subdued bone/cream palette. The desaturated version:
- Maintains anatomical accuracy (marrow tissue with sinew)
- Matches unit sprite color scheme
- Feels more "calcified" and defensive
- Reduces visual noise on screen (less eye-catching red)
- Better represents hardened bone walls vs raw tissue

## Performance Considerations

**Particle Count:**
- Maximum scenario: 16 walls × 25 eruption particles = 400 eruption particles
- Plus: 16 walls × 40 solidification particles = 640 solidification particles
- Plus: 30 pulse particles + 16 geysers + 16 cracks + network glow
- Total peak: ~1100 visual elements (managed by staggered timing)

**Optimization:**
- Particle staggering: Eruptions cascade over 1.0s (not all at once)
- Solidification particles: Short lifespan (0.5s), removed quickly
- Phase separation: Cracks complete before eruptions start
- Particle culling: Completed particles removed from update list
- Drawing: SRCALPHA surfaces for proper transparency
- Physics: Simple calculations (gravity, linear velocity)

**Memory:**
- Particle objects: Lightweight (position, velocity, color, timer)
- Geyser effects: One per wall, reused during phase
- Network glow: Single object tracking 16 wall states
- No texture loading (all procedural drawing)

## Next Steps

**MARROW CONDENSER Animation Status:**
1. ✅ **Ossify** - Defensive bone compression (COMPLETE)
2. ✅ **Bone Tithe** - Life-draining marrow extraction (COMPLETE)
3. ✅ **Marrow Dike** - Wall eruption and enemy displacement (COMPLETE)

**All Three MARROW CONDENSER Skills Have Animations!**

The marrow_condenser.py file now contains three complete skill animations (Ossify, Bone Tithe, and Marrow Dike) totaling 1490 lines, using the established MARROW CONDENSER color palette and anatomical theme. The marrow_wall.svg terrain asset has also been updated to match the unit's aesthetic.

**Potential Future Enhancements:**
- Enhanced Mired status visual (for upgraded Marrow Dike)
- Wall destruction animation (when walls are attacked)
- Unit-wall collision effects (when enemies hit walls)
- Ambient glow on walls during their duration
- Wall repair animation (if healing/repair mechanic added)
