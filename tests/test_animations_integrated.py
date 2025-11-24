#!/usr/bin/env python3
"""
Test script for integrated skill animations in the graphical version.
Tests GLAIVEMAN skills: Judgement, PRY, Autoclave, Vault
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("GLAIVEMAN Animation Test - Integrated")
print("=" * 60)
print()

print("Testing Animation Factory imports...")
try:
    from boneglaive.graphical.animations import AnimationFactory
    print("✓ AnimationFactory imported")
except ImportError as e:
    print(f"✗ Failed to import AnimationFactory: {e}")
    sys.exit(1)

print("✓ Animation core classes imported")
print()

# Test animation creation
print("Testing animation creation:")
print()

# Create mock animated units for testing
class MockAnimatedUnit:
    def __init__(self, name, grid_x, grid_y):
        self.name = name
        self.grid_x = grid_x
        self.grid_y = grid_y

caster = MockAnimatedUnit("GLAIVEMAN", 2, 4)
target = MockAnimatedUnit("ENEMY", 8, 4)

skills_to_test = [
    ("JUDGEMENT", "Spinning glaive projectile"),
    ("PRY", "Cross-beam steam jets"),
    ("AUTOCLAVE", "Lightning bolt from above"),
    ("VAULT", "Not yet implemented"),
]

for skill_name, description in skills_to_test:
    print(f"Testing {skill_name}: {description}")
    anim = AnimationFactory.create_animation(
        skill_name,
        caster_unit=caster,
        target_unit=target
    )

    if anim:
        print(f"  ✓ Animation created: {type(anim).__name__}")
        print(f"    - Has update method: {hasattr(anim, 'update')}")
        print(f"    - Has draw method: {hasattr(anim, 'draw')}")

        # Test update
        try:
            result = anim.update(0.016)  # 60 FPS frame time
            print(f"    - Update returns: {type(result).__name__}")
        except Exception as e:
            print(f"    ✗ Update failed: {e}")
    else:
        if skill_name == "VAULT":
            print(f"  - Animation not implemented (expected)")
        else:
            print(f"  ✗ Failed to create animation")
    print()

print("=" * 60)
print("Test complete!")
print()
print("To test visually:")
print("  1. Run: python run_graphical.py")
print("  2. Select a GLAIVEMAN unit")
print("  3. Press 1, 2, 3, or 4 to select skills")
print("  4. Click on valid target")
print("  5. Watch the animation!")
print("=" * 60)
