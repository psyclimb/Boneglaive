# Bone Tithe Animation - Implementation Complete

## Summary
Created a visceral life-draining animation for the MARROW CONDENSER's **Bone Tithe** skill, depicting the violent extraction of bone marrow from all adjacent enemies in a 3x3 area. The animation shows marrow particles streaming from enemies to the caster, culminating in an empowerment burst that displays permanent HP gains.

## Files Modified

### 1. boneglaive/graphical/animations/marrow_condenser.py (Lines 427-950)
**Added:** 4 new animation classes totaling ~525 lines
- Lines 431-523: `ExtractionTendrils` class - 8 jagged bone tendrils with pulsing red veins
- Lines 526-606: `MarrowParticle` class - Individual marrow particles following curved bezier paths
- Lines 609-742: `AbsorptionBurst` class - Implosion effect with empowerment aura and HP display
- Lines 745-949: `BoneTitheAnimation` class - Main 3-phase controller with enemy detection

### 2. boneglaive/graphical/animations/animation_factory.py
**Changes:**
- Line 45: Added import for `BoneTitheAnimation`
- Line 91: Registered "BONE_TITHE" skill with `BoneTitheAnimation` class
- Lines 496-512: Added handler in `create_animation()` method for AOE animation

### 3. boneglaive/graphical/animations/__init__.py
**Changes:**
- Line 69: Added import for `BoneTitheAnimation`
- Line 124: Added `BoneTitheAnimation` to `__all__` exports list

## Animation Details

### Color Scheme (MARROW CONDENSER Palette)
- **Primary Bone (Bright)**: RGB(240, 232, 216) - #f0e8d8 - Empowerment aura
- **Secondary Bone (Pale)**: RGB(224, 213, 197) - #e0d5c5 - Tendrils, bone fragments
- **Tertiary Bone (Darkened)**: RGB(208, 197, 181) - #d0c5b5 - Tendril jagged edges
- **Muscle Red (Deep)**: RGB(200, 80, 80) - #c85050 - (not used, reserved for future)
- **Blood Red (Dark)**: RGB(139, 0, 0) - #8b0000 - Marrow particles (primary)
- **Glowing Energy**: RGB(255, 0, 0) - #ff0000 - Pulsing veins, extraction beams, absorption flash
- **HP Gain Text**: RGB(100, 255, 100) - Green - Floating HP gain numbers

### Animation Phases (Total: ~2.2 seconds)

#### Phase 1: Extraction (0.4s)
**Visual Elements:**
- 8 bone tendrils shoot outward in all directions (cardinal + diagonal)
- Tendrils are pale cream (224, 213, 197) with pulsing red veins (255, 0, 0)
- Jagged edges perpendicular to main tendril (3 jags per tendril)
- Tendrils extend with ease-out motion to 1 tile distance (TILE_SIZE)
- 20 dark red pulse particles burst from caster position
- Tendrils fade out gradually as they reach full extension

**Screen Effects:**
- Light shake (intensity 3, duration 0.3s) - extraction force

**Technical:**
- Vein pulse frequency: 10 Hz (sin wave)
- Tendril alpha: 220 base, fades to 110 at end of phase
- Extension easing: progress² (quadratic ease-out)

#### Phase 2: Draining (0.9s)
**Visual Elements:**
- Automatically detects all adjacent enemies in 3x3 grid
- For each enemy detected:
  - 15-20 marrow particles spawn at enemy position
  - 75% blood particles (dark red 139, 0, 0), 25% bone fragments (pale 224, 213, 197)
  - Particles follow curved bezier paths with acceleration toward caster
  - Particles stagger start time (0-0.3s delay per particle)
- Thin red extraction beams (255, 0, 0) pulse between enemies and caster
- Beam intensity oscillates (0.6-1.0 at 8 Hz)
- Enemy flash indicators at 0.2s (damage timing)

**Screen Effects:**
- No shake during drain (smooth, steady extraction)

**Technical:**
- Particle paths: Quadratic bezier with random control points
- Particle speed: Variable (0.6-0.9s duration) with quadratic acceleration
- Particle fade: Fade in (0-0.2), bright (0.2-0.8), fade out (0.8-1.0)
- Blood particles have red glow (size + 2px)

#### Phase 3: Absorption (0.9s)
**Visual Elements:**
- **Sub-phase: Implosion (0.2s)**
  - 30 particles collapse inward from 20-40px distance
  - Mix of bone white, pale cream, and red particles
  - Particles converge to center point

- **Sub-phase: Flash (0.15s)**
  - Bright flash at center transitions white → red
  - Flash size: 50px radius
  - Alpha peaks at 200, then fades

- **Sub-phase: Aura (0.55s)**
  - Expanding empowerment aura (25-40px radius)
  - Outer layer: Bone white (240, 232, 216)
  - Inner layer: Red energy core (255, 0, 0)
  - Aura pulses at 10 Hz
  - HP gain number floats upward above caster
  - Green "+X" text (100, 255, 100) where X = number of enemies hit
  - Text rises 20px and fades out over duration

**Screen Effects:**
- Medium-heavy shake (intensity 6, duration 0.4s) - absorption impact
- Red screen flash (255, 0, 0) for 0.15s at absorption start

**Technical:**
- Implosion: Linear collapse (distance * (1.0 - progress))
- Flash: Triangle wave (rise 0-0.5, fall 0.5-1.0)
- Aura: Expands linearly, fades with pulse modulation
- HP text: Font size 32, rises with alpha fade

## Technical Implementation

### Enemy Detection System
The animation automatically detects adjacent enemies:
```python
# Scans 3x3 grid centered on caster (8 surrounding tiles)
for dy in range(-1, 2):
    for dx in range(-1, 2):
        if dy == 0 and dx == 0:
            continue  # Skip caster position

        grid_y = caster_unit.grid_y + dy
        grid_x = caster_unit.grid_x + dx

        # Find enemy at this grid position from units_list
        # Store screen coordinates via camera.grid_to_screen()
```

### Curved Particle Paths (Bezier)
Marrow particles follow quadratic bezier curves with acceleration:
```python
# Control point creates arc
control_x = (start_x + end_x) / 2 + random.uniform(-30, 30)
control_y = (start_y + end_y) / 2 + random.uniform(-30, 30)

# Quadratic bezier with acceleration
raw_progress = timer / duration
progress = raw_progress * raw_progress  # Quadratic acceleration
t = progress
x = (1-t)² * start_x + 2(1-t)t * control_x + t² * end_x
y = (1-t)² * start_y + 2(1-t)t * control_y + t² * end_y
```

### HP Gain Display
The animation displays the number of enemies hit as permanent HP gain:
```python
# HP gained = number of adjacent enemies detected
hp_gained = len(self.adjacent_enemies)

# Note: Actual HP gain happens in skill logic (marrow_condenser.py:893-894)
# This is purely visual display synchronized with animation
```

### Coordinate Handling
✅ Uses standard camera.grid_to_screen() pattern:
```python
# Caster position
self.center_x, self.center_y = camera.grid_to_screen(
    caster_unit.grid_x, caster_unit.grid_y, centered=True
)

# Enemy positions (detected in 3x3 grid)
for each adjacent enemy:
    screen_x, screen_y = camera.grid_to_screen(
        enemy_grid_x, enemy_grid_y, centered=True
    )
```

## Verification Results

✅ **Syntax Check:**
- marrow_condenser.py: OK (950 lines total)
- animation_factory.py: OK
- __init__.py: OK

✅ **Import Verification:**
- `from boneglaive.graphical.animations import BoneTitheAnimation` - SUCCESS
- Class name confirmed: BoneTitheAnimation

✅ **Registration Verification:**
- `AnimationFactory.has_animation('BONE_TITHE')` - True
- Registered class: BoneTitheAnimation
- Factory creates animation correctly

✅ **Return Values:**
- All `update()` methods return boolean (True if active, False when done)
- ExtractionTendrils.update() ✓
- MarrowParticle.update() ✓
- AbsorptionBurst.update() ✓
- BoneTitheAnimation.update() ✓

✅ **Coordinate Pattern:**
- Follows standard from ANIMATION_IMPLEMENTATION_GUIDE.md
- Caster: `camera.grid_to_screen(grid_x, grid_y, centered=True)` ✓
- Enemies: Same pattern for each detected adjacent unit ✓

## Testing Instructions

### Setup
1. Run the graphical version: `python run_graphical.py`
2. Ensure MARROW CONDENSER is available in the game
3. Position MARROW CONDENSER adjacent to enemy units

### Test Procedure
1. Select MARROW CONDENSER unit on the battlefield
2. Position near one or more enemy units (ideally surround with multiple enemies)
3. Press **B** key to activate Bone Tithe skill
4. Skill is self-targeting (no manual targeting required)
5. Press **E** to execute turn and watch animation

### Expected Results

**Phase 1 (0.4s) - Extraction:**
- [ ] 8 pale bone tendrils shoot outward in all directions
- [ ] Tendrils have pulsing red veins through center
- [ ] Jagged edges on tendrils (3 perpendicular jags each)
- [ ] Dark red pulse particles burst from caster
- [ ] Light screen shake during extraction
- [ ] Tendrils extend to 1 tile distance, then fade

**Phase 2 (0.9s) - Draining:**
- [ ] Marrow particles stream from each adjacent enemy
- [ ] 15-20 particles per enemy (dark red blood + pale bone fragments)
- [ ] Particles follow curved paths accelerating toward caster
- [ ] Thin red extraction beams pulse between enemies and caster
- [ ] Beams intensity oscillates smoothly
- [ ] No screen shake (smooth draining phase)

**Phase 3 (0.9s) - Absorption:**
- [ ] Particles collapse inward (implosion, 0.2s)
- [ ] Bright white flash transitions to red (0.15s)
- [ ] Red screen flash occurs at absorption start
- [ ] Expanding empowerment aura (bone white with red core)
- [ ] Green "+X" HP gain number floats upward above caster
- [ ] Number shows count of adjacent enemies hit
- [ ] Medium-heavy screen shake during absorption
- [ ] Aura fades with pulsing effect

**Overall:**
- [ ] Animation duration: ~2.2 seconds total
- [ ] Animation centered on MARROW CONDENSER (caster)
- [ ] Particle streams originate from each adjacent enemy position
- [ ] Enemy detection automatic (no manual targeting)
- [ ] Works with 0-8 adjacent enemies (scales dynamically)
- [ ] No coordinate misalignment
- [ ] No graphical glitches or artifacts
- [ ] Colors match MARROW CONDENSER sprite theme
- [ ] HP gain number accurately reflects enemy count
- [ ] Animation completes before game logic continues

### Edge Cases to Test

**No Adjacent Enemies:**
- Animation should still play (tendrils extend, but no particles)
- HP gain should show "+0"
- All 3 phases complete normally

**Single Adjacent Enemy:**
- 1 set of marrow particles (15-20 particles)
- 1 extraction beam
- HP gain shows "+1"

**Surrounded by Enemies (8 adjacent):**
- Maximum particle density (120-160 particles total)
- 8 extraction beams (one per enemy)
- HP gain shows "+8"
- Performance should remain smooth

**Mixed Adjacent Units (Allies + Enemies):**
- Only affects enemy units (ignores allies)
- Particles only stream from enemies
- HP gain reflects only enemy count

### Common Issues to Check

**Animation doesn't appear:**
- Check console for "[AnimationFactory] Created BoneTitheAnimation for BONE_TITHE"
- Verify skill key binding is correct (B key)
- Ensure MARROW CONDENSER unit is properly selected

**Particles appear at wrong locations:**
- Verify camera tracking is correct
- Check that enemy positions are detected properly
- Should stream from adjacent tile centers to caster center

**HP gain number incorrect:**
- Should equal number of adjacent enemy units
- Note: Actual HP gain in game may differ if skill is upgraded (+2 per enemy)

**Too many/few particles:**
- Each enemy should spawn 15-20 particles
- Check that enemy detection is working (3x3 grid scan)

**Animation disappears immediately:**
- Verified: All update() methods return True when active
- Should not occur with current implementation

## Integration Status

✅ **File Updates:**
- [x] marrow_condenser.py - Added 4 classes (3 helpers + main controller)
- [x] All classes follow ANIMATION_IMPLEMENTATION_GUIDE.md patterns
- [x] Proper imports and pygame usage
- [x] Total file size: 950 lines

✅ **Animation Factory Registration:**
- [x] Import added to animation_factory.py
- [x] "BONE_TITHE" registered in SKILL_ANIMATIONS dict
- [x] Handler added in create_animation() method
- [x] AOE configuration with units_list for enemy detection

✅ **Package Exports:**
- [x] Import added to __init__.py
- [x] BoneTitheAnimation added to __all__ list

✅ **Verification:**
- [x] Python syntax valid for all files
- [x] Import successful
- [x] Registration confirmed
- [x] Coordinate pattern verified
- [x] Return values verified

## Animation Design Rationale

The Bone Tithe animation visually represents the skill's horrific life-draining mechanics:

1. **Extraction Phase** - Bone tendrils with pulsing red veins reach out like grasping fingers, establishing the vampiric connection to nearby enemies. The jagged edges emphasize the violent, invasive nature of the skill.

2. **Draining Phase** - Marrow particles violently streaming from enemies to the caster creates clear visual feedback of life essence being stolen. The curved bezier paths add organic, fluid motion that feels more disturbing than straight lines. The mix of blood red and bone white particles reinforces the theme of extracting internal marrow tissue.

3. **Absorption Phase** - The implosion → flash → empowerment sequence shows the MARROW CONDENSER metabolizing stolen life force. The expanding aura with bone white exterior and red energy core represents the permanent strengthening effect. The floating green HP gain number provides clear mechanical feedback.

### Key Visual Choices:

- **Curved particle paths**: More organic and disturbing than straight lines, emphasizes liquid marrow being drawn out
- **Particle acceleration**: Creates suction/vacuum effect, reinforces the forceful extraction
- **Jagged tendrils**: Makes the skill feel violent and invasive, not gentle
- **Pulsing effects**: Red veins and beams pulse like a heartbeat, emphasizing life drain theme
- **Color progression**: Dark blood (extraction) → bright red energy (absorption) → bone white (empowerment)
- **Dynamic scaling**: Works with 0-8 enemies, particle density scales appropriately

## Performance Considerations

**Particle Count:**
- Maximum scenario: 8 enemies × 20 particles = 160 marrow particles
- Plus: 30 implosion particles + 20 pulse particles + 8 beams
- Total peak: ~218 visual elements (well within performance bounds)

**Optimization:**
- Particle staggering reduces instantaneous rendering load
- Particle culling removes completed particles from update list
- Bezier calculations cached in particle objects
- Drawing uses SRCALPHA surfaces for proper transparency

## Next Steps

**MARROW CONDENSER Animation Status:**
1. ✅ **Ossify** - Defensive bone compression (COMPLETE)
2. ✅ **Bone Tithe** - Life-draining marrow extraction (COMPLETE)
3. ⏳ **Marrow Dike** - Wall creation animation (TODO)

**For Marrow Dike Animation:**
- 5x5 perimeter wall deployment
- Enemy displacement (pulling inward)
- Wall durability visualization
- Upgraded version: Mired status effect indicator

The marrow_condenser.py file now contains two complete skill animations (Ossify and Bone Tithe) using the established color palette and anatomical theme, ready for the third skill animation (Marrow Dike) to be added in the same file.
