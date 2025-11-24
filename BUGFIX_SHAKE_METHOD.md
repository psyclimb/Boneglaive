# Bug Fix: AttributeError on shake() method

**Date**: 2025-11-21
**Status**: ✅ FIXED

---

## Issue

```
AttributeError: 'AnimatedUnit' object has no attribute 'shake'. Did you mean: 'shake_x'?
```

**Location**: `boneglaive/graphical/renderer.py:437`

---

## Root Cause

The `AnimatedUnit` class from `demo_animations/core.py` does not have a `shake()` method. Instead, it has a `shake_intensity` property that should be set directly.

### Correct Pattern

```python
# ✗ WRONG - calls non-existent method
animated_unit.shake(intensity=10)

# ✓ CORRECT - sets property directly
animated_unit.shake_intensity = 10
```

---

## How AnimatedUnit Handles Shake

From `demo_animations/core.py`:

```python
class AnimatedUnit:
    def __init__(self, ...):
        # Visual effects
        self.shake_x = 0
        self.shake_y = 0
        self.shake_intensity = 0  # <-- Set this property

    def take_damage(self, amount):
        """Apply damage and trigger shake effect."""
        self.hp = max(0, self.hp - amount)
        self.shake_intensity = 10  # <-- Example of correct usage

    def update(self, delta_time):
        # Shake decay
        if self.shake_intensity > 0:
            self.shake_intensity -= delta_time * 40
            if self.shake_intensity < 0:
                self.shake_intensity = 0

            import random
            self.shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
        else:
            self.shake_x = 0
            self.shake_y = 0
```

The shake effect:
1. Set `shake_intensity` to desired value (e.g., 10)
2. `update()` automatically decays intensity over time
3. `update()` sets `shake_x` and `shake_y` based on intensity
4. Drawing uses `shake_x` and `shake_y` for offset

---

## Fix Applied

**File**: `boneglaive/graphical/renderer.py` line 437

**Before**:
```python
# Add damage shake effect
animated_unit.shake(intensity=10)
```

**After**:
```python
# Add damage shake effect
animated_unit.shake_intensity = 10
```

---

## Testing

### Automated Tests
```bash
python test_attack_system.py
# ✓ PASSED

python test_renderer_imports.py
# ✓ PASSED
```

### Manual Testing
The graphical version should now run without AttributeError when damage is dealt.

---

## Related Code

### Other Shake Usages
Verified no other instances of `.shake()` method call in codebase:
```bash
grep -r "\.shake(" boneglaive/graphical/
# No matches found
```

### Similar Pattern in Core
The `take_damage()` method in `AnimatedUnit` already uses the correct pattern:
```python
def take_damage(self, amount):
    self.hp = max(0, self.hp - amount)
    self.shake_intensity = 10  # Correct usage
```

---

## Prevention

When working with `AnimatedUnit`:
- Always set properties directly: `shake_intensity`, `shake_x`, `shake_y`
- Do not call `.shake()` - it doesn't exist
- Reference `demo_animations/core.py` for correct API usage
- Use `take_damage()` method for automatic shake effect

---

## Impact

**Severity**: Medium (runtime error on damage events)
**Affected**: Attack system animation feedback
**User Impact**: Game would crash when attacks dealt damage
**Fixed In**: Phase 2 completion session

---

*Bug fixed: 2025-11-21*
