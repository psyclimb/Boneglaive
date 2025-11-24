# Animation Implementation Guide for Boneglaive
## Complete Workflow for Adding New Skill Animations

This guide documents the exact process for implementing a new skill animation in the Boneglaive graphical version, based on the successful Market Futures implementation (2025-11-23).

---

## Phase 1: Research & Analysis

### Step 1.1: Read Core Documentation
```bash
# Always start by reading these files to get context
Read: /home/user/boneglaive/CLAUDE.org
Read: /home/user/boneglaive/boneglaive/graphical/animations/core.py (if needed)
```

**Key points from CLAUDE.org:**
- Animation Architecture section (lines 73-156)
- Two animation patterns: Object-based vs Attribute-based
- Critical: ALL animations MUST return True/False from update()
- Coordinate system: Camera-based with grid_to_screen()
- NO animation logic in renderer.py - all in animation classes

### Step 1.2: Identify the Unit and Read Existing Animations
```bash
# For a unit like DELPHIC_APPRAISER:
Read: /home/user/boneglaive/boneglaive/graphical/animations/delphic_appraiser.py
# Or for other units:
Read: /home/user/boneglaive/boneglaive/graphical/animations/[unit_name].py
```

**What to look for:**
- Color scheme used by existing animations
- Coordinate handling patterns
- Screen shake/flash usage
- Animation phase structure
- Common helper classes

### Step 1.3: Read the Skill Implementation
```bash
Read: /home/user/boneglaive/boneglaive/game/skills/[unit_name].py
# Find the specific skill class (e.g., MarketFuturesSkill)
```

**Extract this information:**
- Skill name and key binding
- Full description (includes mechanics and flavor)
- Target type (AREA, ENEMY, ALLY, SELF)
- Range and cooldown
- What the skill does mechanically
- Special effects or status applications

### Step 1.4: Analyze Color Scheme
```bash
# Extract color values from existing animations
grep -n "color = " /home/user/boneglaive/boneglaive/graphical/animations/[unit_name].py | head -30
```

**Document the palette:**
- Primary colors (RGB values)
- Secondary/accent colors
- Special effect colors (glow, curse, energy, etc.)
- Theme (gold/prosperity vs dark/curse vs elemental, etc.)

### Step 1.5: Study Coordinate Handling Pattern
```bash
# Check how existing animations handle coordinates
grep -B 5 -A 5 "camera.grid_to_screen" /home/user/boneglaive/boneglaive/graphical/animations/[unit_name].py
```

**Critical pattern to match:**
```python
# target_pos arrives as (grid_y, grid_x) - note the order!
grid_y, grid_x = target_pos
self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
# Note: grid_x comes first in grid_to_screen(), even though grid_y came first in target_pos!
```

---

## Phase 2: Design the Animation

### Step 2.1: Define Animation Concept
Based on skill description and existing unit theme, design:

**Animation name:** [Skill Name]Animation

**Total duration:** ~2-3 seconds (typical range)

**Number of phases:** 3-5 phases (typical range)

**Phase breakdown:**
1. **Phase 1 Name** (duration) - Description
   - Visual elements
   - Screen shake intensity (0-15, typical: 2-6)
   - Screen flash if needed

2. **Phase 2 Name** (duration) - Description
   - Visual elements
   - Escalating or de-escalating effects

3. **[Additional phases...]**

### Step 2.2: Identify Required Helper Classes
List sub-effect classes needed (examples):
- Beam/projectile classes (linear movement)
- Particle effect classes (spiral, orbit, explosion)
- Symbol/icon classes (anchors, runes, numbers)
- Area effect classes (circles, rings, waves)
- Transformation classes (color shifts, fades, pulses)

### Step 2.3: Design Color Progression
Map colors to phases:
```
Phase 1: [Color values] - [Emotional/thematic purpose]
Phase 2: [Color values] - [Transition or intensification]
Phase 3: [Color values] - [Resolution or aftermath]
```

**Ensure consistency with unit theme:**
- DELPHIC APPRAISER: Gold (255,215,0), Goldenrod (218,165,32), Brown (139,69,19)
- Match existing animations' emotional/thematic palette

---

## Phase 3: Implementation

### Step 3.1: Create Animation Classes in Unit File

**File:** `/home/user/boneglaive/boneglaive/graphical/animations/[unit_name].py`

**Structure:**

```python
# Add at the end of the file, after existing animations

# ============================================================================
# [SKILL NAME] ANIMATION
# ============================================================================

class HelperEffectClass1:
    """
    Brief description of what this helper does.
    """
    def __init__(self, center_x, center_y, [other_params]):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0  # Or -delay for delayed start
        self.duration = [float]  # How long this effect lasts
        self.active = True

        # Initialize any other state/particles/geometry

    def update(self, delta_time):
        """CRITICAL: Must return True if active, False when done."""
        self.timer += delta_time

        # Update logic here

        if self.timer >= self.duration:
            self.active = False

        return self.active  # MUST RETURN BOOLEAN!

    def draw(self, surface):
        """Draw this effect to the pygame surface."""
        if not self.active or self.timer < 0:  # Handle delays
            return

        progress = min(1.0, self.timer / self.duration)

        # Drawing logic here using pygame primitives:
        # - pygame.draw.line()
        # - pygame.draw.circle()
        # - pygame.draw.polygon()
        # - pygame.draw.rect()
        # - pygame.font.Font()

        # Always use SRCALPHA surfaces for transparency
        # Always calculate alpha values based on progress


class MainSkillAnimation:
    """
    [Skill name] skill animation for [UNIT NAME].
    [Brief description of what the skill does visually]

    Phases:
    1. [Phase 1 name] - [Description]
    2. [Phase 2 name] - [Description]
    3. [Phase 3 name] - [Description]
    [etc.]
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize [Skill Name] animation.

        Args:
            target_pos: (grid_y, grid_x) - [description of what this targets]
            game: Game instance to access map/furniture/unit data
            Other args standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit  # May be None
        self.target_pos = target_pos  # (grid_y, grid_x) format
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert target grid position to screen coords using Camera
        # CRITICAL: target_pos is (grid_y, grid_x), but grid_to_screen takes (grid_x, grid_y)!
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "phase1_name"  # phase1 -> phase2 -> phase3 -> etc.
        self.timer = 0
        self.active = True

        # Sub-effects (initialize as None or empty lists)
        self.helper_effects = []
        self.other_effect = None

        # Any additional state (glow intensity, etc.)
        self.glow_intensity = 0

        # Start Phase 1
        self._start_phase1()

    def _start_phase1(self):
        """Phase 1: [Description]."""
        self.phase = "phase1_name"
        self.timer = 0

        # Create helper effects
        self.helper_effects.append(HelperEffect(...))

        # Trigger screen effects
        self.screen_shake_callback(intensity, duration)  # intensity: 2-15, duration: 0.5-1.0
        # self.screen_flash_callback((r, g, b), duration)  # If needed

    def _start_phase2(self):
        """Phase 2: [Description]."""
        self.phase = "phase2_name"
        self.timer = 0

        # Create new effects, update state

    # [Additional phase methods...]

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update any progressive state (glow, etc.)
        if self.phase == "phase1_name":
            self.glow_intensity = min(1.0, self.timer / phase1_duration)
        elif self.phase == "phase2_name":
            # Update for phase 2
            pass

        # Phase transitions (check timer thresholds)
        if self.phase == "phase1_name" and self.timer >= phase1_duration:
            self._start_phase2()
        elif self.phase == "phase2_name" and self.timer >= phase2_duration:
            self._start_phase3()
        # [...more transitions...]
        elif self.phase == "final_phase" and self.timer >= final_duration:
            self.active = False  # Animation complete

        # Update all sub-effects
        for effect in self.helper_effects:
            effect.update(delta_time)

        if self.other_effect:
            self.other_effect.update(delta_time)

        return self.active  # CRITICAL: Must return boolean!

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw base effects (glows, overlays, etc.)
        if self.glow_intensity > 0:
            # Create pulsing glow
            radius = int(base_radius + pulse_amount * math.sin(self.timer * frequency))
            alpha = int(self.glow_intensity * max_alpha)

            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, alpha), (radius, radius), radius)
            surface.blit(glow_surf, (int(self.target_x - radius), int(self.target_y - radius)))

        # Draw phase-specific effects
        for effect in self.helper_effects:
            effect.draw(surface)

        if self.other_effect:
            self.other_effect.draw(surface)

        # Draw any phase-specific overlays
        if self.phase == "specific_phase":
            # Phase-specific drawing code
            pass
```

### Step 3.2: Register in Animation Factory

**File:** `/home/user/boneglaive/boneglaive/graphical/animations/animation_factory.py`

**A. Add import at top:**
```python
# Find the imports for your unit (e.g., delphic_appraiser)
from boneglaive.graphical.animations.[unit_name] import (
    ExistingAnimation1,
    ExistingAnimation2,
    NewSkillAnimation,  # ADD THIS
)
```

**B. Register in SKILL_ANIMATIONS dict:**
```python
# Find the section for your unit's skills
# Add entry in format: "SKILL_NAME": (AnimationClass, {})
"SKILL_NAME": (NewSkillAnimation, {}),
```

**C. Add handler in create_animation() method:**

Find the section with other animations for your unit, add:

```python
elif anim_class.__name__ == "NewSkillAnimation":
    # [Skill Name] - brief description
    # Requires: target_pos ([what it targets]), game instance, callbacks
    if not target_pos:
        print("[AnimationFactory] SKILL_NAME requires a target position")
        return None
    animation = anim_class(
        caster_unit=caster_unit,
        target_unit=target_unit,
        target_pos=target_pos,
        is_crit=is_crit,
        is_infused=is_infused,
        particle_emitter=particle_emitter,
        debris_list=[],  # Usually empty unless using debris
        screen_shake_callback=screen_shake_callback,
        screen_flash_callback=screen_flash_callback,
        units_list=units_list if units_list else [],
        camera=camera,
        game=kwargs.get('game')  # Pass game instance
    )
```

### Step 3.3: Export in __init__.py

**File:** `/home/user/boneglaive/boneglaive/graphical/animations/__init__.py`

**A. Add to imports section:**
```python
from .[unit_name] import (
    ExistingAnimation1,
    ExistingAnimation2,
    NewSkillAnimation,  # ADD THIS
)
```

**B. Add to __all__ list:**
```python
__all__ = [
    # ... existing entries ...
    # [Unit Name]
    'ExistingAnimation1',
    'ExistingAnimation2',
    'NewSkillAnimation',  # ADD THIS
    # ... rest of entries ...
]
```

---

## Phase 4: Verification

### Step 4.1: Syntax Checks
```bash
# Run these commands to verify Python syntax
python3 -m py_compile boneglaive/graphical/animations/[unit_name].py
python3 -m py_compile boneglaive/graphical/animations/animation_factory.py
python3 -m py_compile boneglaive/graphical/animations/__init__.py
```

**Expected output:** No errors, or "✓ [filename] syntax OK"

### Step 4.2: Import Verification
```bash
# Test that the animation can be imported
python3 -c "from boneglaive.graphical.animations import NewSkillAnimation; print('✓ Import successful:', NewSkillAnimation.__name__)"
```

**Expected output:** `✓ Import successful: NewSkillAnimation`

### Step 4.3: Registration Verification
```bash
# Test that AnimationFactory recognizes the skill
python3 -c "from boneglaive.graphical.animations.animation_factory import AnimationFactory; print('✓ Registered:', AnimationFactory.has_animation('SKILL_NAME')); print('✓ Class:', AnimationFactory.SKILL_ANIMATIONS.get('SKILL_NAME')[0].__name__)"
```

**Expected output:**
```
✓ Registered: True
✓ Class: NewSkillAnimation
```

### Step 4.4: Coordinate Verification
```bash
# Verify coordinate handling matches pattern
grep -B 2 -A 2 "grid_y, grid_x = target_pos" boneglaive/graphical/animations/[unit_name].py | grep -A 2 "target_pos is"
```

**Expected:** Should show the pattern with comment explaining format

### Step 4.5: Create Implementation Document
```bash
# Create a summary document for the user
cat > /home/user/boneglaive/[SKILL_NAME]_IMPLEMENTATION.md << 'EOF'
# [Skill Name] Animation - Implementation Complete

## Summary
[Brief description]

## Files Modified
1. boneglaive/graphical/animations/[unit_name].py
   - Added: [List of classes and line numbers]

2. boneglaive/graphical/animations/animation_factory.py
   - Changes: [Import, registration, handler]

3. boneglaive/graphical/animations/__init__.py
   - Changes: [Import and export]

## Animation Details
### Color Scheme
- [List RGB values and purposes]

### Phases
1. [Phase details]
2. [Phase details]
[etc.]

### Coordinate Handling
✓ Uses standard pattern: target_pos (grid_y, grid_x) → camera.grid_to_screen(grid_x, grid_y, centered=True)

## Verification Results
✓ [List all verification checks]

## Testing Notes
[Instructions for manual testing]

## Integration Status
✅ [Checklist of completed tasks]
EOF
```

---

## Phase 5: Documentation

### Step 5.1: Create Testing Instructions for User
Include in the implementation document:

```markdown
## Testing Instructions

### Setup
1. Run the graphical version: `python run_graphical.py`
2. Ensure [UNIT_NAME] is available in the game

### Test Procedure
1. Select [UNIT_NAME] unit
2. Press [KEY] to activate [SKILL_NAME]
3. Target [TARGET_TYPE] within range [RANGE]
4. Observe animation sequence:
   - [ ] Phase 1 displays correctly
   - [ ] Phase 2 transitions smoothly
   - [ ] Phase 3 completes
   - [ ] Animation is centered on target tile
   - [ ] Screen shake feels appropriate
   - [ ] Colors match unit theme

### Expected Results
- Animation plays at [TARGET_LOCATION]
- Duration: ~[X] seconds
- No coordinate misalignment
- No graphical glitches
- Animation completes before game logic continues

### Common Issues to Check
- [ ] Animation appears at wrong location → Check coordinate conversion
- [ ] Animation disappears immediately → Check update() return value
- [ ] Animation never ends → Check phase transition logic
- [ ] Colors don't match → Verify RGB values against existing animations
```

---

## Critical Reminders

### Coordinate System
```
INPUT:  target_pos = (grid_y, grid_x)  ← Note: Y comes first!
UNPACK: grid_y, grid_x = target_pos
CONVERT: self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
                                                               ↑      ↑
                                                               X first, then Y!
USE:    Draw at (self.target_x, self.target_y)
```

### Animation Return Values
```python
# CORRECT - Always return boolean
def update(self, delta_time):
    # ... update logic ...
    if finished:
        return False
    return True

# WRONG - Implicit None return causes immediate removal!
def update(self, delta_time):
    # ... update logic ...
    if finished:
        self.active = False
    # Missing return statement → returns None → animation disappears!
```

### Color Consistency
- Always check existing unit animations for color palette
- Use RGB tuples: (R, G, B) or (R, G, B, alpha)
- Document the theme: prosperity/gold, curse/dark, elemental, etc.
- Maintain emotional consistency across all unit animations

### Screen Effects Guidelines
**Screen Shake:**
- Light: 2-3 intensity, 0.5-0.6 duration
- Medium: 4-6 intensity, 0.7-0.9 duration
- Heavy: 8-12 intensity, 0.6-0.8 duration
- Extreme: 12-15 intensity (rare, for ultimate abilities)

**Screen Flash:**
- Use sparingly (major impacts only)
- Duration: 0.2-0.4 seconds typically
- Color should match ability theme

### File Organization
```
boneglaive/graphical/animations/
├── core.py                     # Base classes, don't modify
├── animation_factory.py        # Registration and creation
├── __init__.py                 # Exports
├── glaiveman.py               # All GLAIVEMAN animations
├── potpourrist.py             # All POTPOURRIST animations
├── mandible_foreman.py        # All MANDIBLE FOREMAN animations
├── [unit_name].py             # One file per unit
└── ...
```

**Pattern:** One file per unit, all animations for that unit in that file.

---

## Common Patterns

### Orbital Particles
```python
for i in range(num_particles):
    angle = (i / num_particles) * 2 * math.pi + self.timer * rotation_speed
    radius = base_radius + oscillation * math.sin(self.timer * frequency)
    px = center_x + math.cos(angle) * radius
    py = center_y + math.sin(angle) * radius
    # Draw particle at (px, py)
```

### Pulsing Glow
```python
radius = int(base_radius + pulse_amplitude * math.sin(self.timer * pulse_frequency))
alpha = int(base_alpha + alpha_variation * math.cos(self.timer * alpha_frequency))
```

### Expanding Rings
```python
progress = self.timer / self.duration
radius = int(min_radius + (max_radius - min_radius) * progress)
alpha = int(max_alpha * (1.0 - progress))  # Fade out as expanding
```

### Beam/Projectile
```python
progress = min(1.0, self.timer / self.duration)
current_x = start_x + (end_x - start_x) * progress
current_y = start_y + (end_y - start_y) * progress
pygame.draw.line(surface, color, (int(start_x), int(start_y)), (int(current_x), int(current_y)), width)
```

### Spiral Effect
```python
angle = base_angle + self.timer * rotation_speed
distance = start_distance + distance_change * progress
x = center_x + math.cos(angle) * distance
y = center_y + math.sin(angle) * distance
```

### Staggered Start (Delay)
```python
def __init__(self, x, y, delay=0):
    self.timer = -delay  # Start negative
    # ...

def draw(self, surface):
    if self.timer < 0:  # Don't draw during delay
        return
    # ... drawing code ...
```

---

## Troubleshooting Checklist

### Animation Doesn't Appear
- [ ] Verified SKILL_ANIMATIONS registration (correct skill name)
- [ ] Verified import in animation_factory.py
- [ ] Verified handler in create_animation() method
- [ ] Check console for "[AnimationFactory] Created [AnimationName]" message
- [ ] Check console for error messages

### Animation Disappears Immediately
- [ ] Verified update() returns True when active
- [ ] Verified no implicit None returns
- [ ] Check initial self.active = True
- [ ] Check phase transition logic doesn't skip to end

### Animation in Wrong Location
- [ ] Verified coordinate conversion: grid_to_screen(grid_x, grid_y, centered=True)
- [ ] Verified target_pos unpacking: grid_y, grid_x = target_pos
- [ ] Check drawing uses self.target_x, self.target_y (not grid coords)
- [ ] Verify Camera is passed to animation

### Animation Colors Wrong
- [ ] Check RGB values match existing unit animations
- [ ] Verify alpha channel in SRCALPHA surfaces
- [ ] Check color tuples are (R, G, B) or (R, G, B, alpha)

### Animation Never Ends
- [ ] Verify final phase sets self.active = False
- [ ] Check phase transition conditions (>= not >)
- [ ] Verify timer increments properly
- [ ] Check no infinite loops in phase transitions

---

## Quick Reference: Common pygame Drawing

```python
# Circle (filled)
pygame.draw.circle(surface, color, (center_x, center_y), radius)

# Circle (outline)
pygame.draw.circle(surface, color, (center_x, center_y), radius, width)

# Line
pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

# Rectangle
pygame.draw.rect(surface, color, (x, y, width, height))

# Polygon
points = [(x1, y1), (x2, y2), (x3, y3)]
pygame.draw.polygon(surface, color, points)

# Text
font = pygame.font.Font(None, size)  # None = default font
text_surface = font.render("text", True, color)
text_surface.set_alpha(alpha)
rect = text_surface.get_rect(center=(x, y))
surface.blit(text_surface, rect)

# Alpha surface for transparency
surf = pygame.Surface((width, height), pygame.SRCALPHA)
# Draw on surf with alpha colors: (R, G, B, alpha)
surface.blit(surf, (x, y))
```

---

## Summary Checklist for Complete Implementation

- [ ] Phase 1: Research completed
  - [ ] Read CLAUDE.org
  - [ ] Studied existing unit animations
  - [ ] Read skill implementation
  - [ ] Analyzed color scheme
  - [ ] Verified coordinate pattern

- [ ] Phase 2: Design completed
  - [ ] Animation concept defined
  - [ ] Phases outlined with durations
  - [ ] Helper classes identified
  - [ ] Color progression mapped

- [ ] Phase 3: Implementation completed
  - [ ] Animation classes created in unit file
  - [ ] Registered in animation_factory.py (3 places)
  - [ ] Exported in __init__.py (2 places)

- [ ] Phase 4: Verification completed
  - [ ] Syntax checks pass
  - [ ] Import verification successful
  - [ ] Registration verification successful
  - [ ] Coordinate pattern verified
  - [ ] Implementation document created

- [ ] Phase 5: Documentation completed
  - [ ] Testing instructions provided
  - [ ] Common issues documented
  - [ ] Integration status confirmed

---

## Final Notes

- **Be thorough:** Follow every step, don't skip verification
- **Match patterns exactly:** Coordinate handling must be identical to existing animations
- **Test incrementally:** Verify each phase before moving to the next
- **Document everything:** Create detailed implementation notes for the user
- **Stay consistent:** Colors, timing, and effects should match unit theme

This guide represents the complete, reproducible workflow that produced the successful Market Futures animation implementation on 2025-11-23.
