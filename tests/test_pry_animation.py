#!/usr/bin/env python3
"""
Test PRY animation integration.
Verifies that PRY animation is properly created and triggered.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from boneglaive.graphical.animations import AnimationFactory, PryAnimation
from boneglaive.graphical.animations.core import AnimatedUnit, ParticleEmitter, DebrisParticle

def test_pry_animation_factory():
    """Test that AnimationFactory creates PRY animation correctly."""
    print("Testing PRY animation factory...")

    # Create mock animated units
    caster = AnimatedUnit(
        name="GLAIVEMAN",
        player=1,
        grid_x=5,
        grid_y=5,
        color=(100, 150, 200),
        sprite_path=None
    )

    target = AnimatedUnit(
        name="ENEMY",
        player=2,
        grid_x=6,
        grid_y=5,
        color=(200, 100, 100),
        sprite_path=None
    )

    # Create required systems
    particle_emitter = ParticleEmitter()
    debris_list = []
    shake_called = []

    def mock_screen_shake(intensity, duration):
        shake_called.append((intensity, duration))
        print(f"  Screen shake called: intensity={intensity}, duration={duration}")

    # Create PRY animation via factory
    animation = AnimationFactory.create_animation(
        "PRY",
        caster_unit=caster,
        target_unit=target,
        particle_emitter=particle_emitter,
        debris_list=debris_list,
        screen_shake_callback=mock_screen_shake
    )

    assert animation is not None, "PRY animation should be created"
    assert isinstance(animation, PryAnimation), "Should be PryAnimation instance"
    print("  ✓ PRY animation created successfully")

    # Test animation phases
    print("\nTesting animation phases:")

    # Initial state
    assert animation.phase == "launching", "Should start in launching phase"
    assert animation.lever_phase == "inserting", "Lever should start in inserting phase"
    assert animation.active == True, "Animation should be active"
    print("  ✓ Initial state correct")

    # Save original positions
    caster_orig_x = caster.x
    target_orig_y = target.y

    # Simulate launching phase (0.4s)
    animation.update(0.2)  # 0.2s into launch
    assert animation.phase == "launching", "Should still be launching"
    assert target.y < target_orig_y, "Target should have moved upward"
    print(f"  ✓ Launching phase: target moved from {target_orig_y} to {target.y}")

    animation.update(0.3)  # Total 0.5s - past 0.4s threshold
    assert animation.phase == "ceiling_impact", "Should transition to ceiling_impact"
    assert len(particle_emitter.particles) > 0, "Should have launch particles"
    assert len(debris_list) > 0, "Should have debris from ceiling impact"
    print(f"  ✓ Ceiling impact: {len(particle_emitter.particles)} particles, {len(debris_list)} debris")

    # Simulate ceiling_impact phase (0.2s)
    animation.update(0.25)  # Past ceiling impact duration
    assert animation.phase == "falling", "Should transition to falling"
    print("  ✓ Falling phase started")

    # Simulate falling phase (0.4s)
    animation.update(0.5)  # Past falling duration
    assert animation.phase == "impact", "Should transition to impact"
    assert len(shake_called) > 0, "Screen shake should have been called"
    print(f"  ✓ Ground impact: screen shake = {shake_called[-1]}")

    # Simulate impact phase (0.15s)
    animation.update(0.2)  # Past impact duration
    assert animation.phase == "done", "Should be done"
    assert animation.active == False, "Animation should be inactive"
    assert target.y == target_orig_y, "Target should return to original position"
    assert caster.x == caster_orig_x, "Caster should return to original position"
    print("  ✓ Animation complete, positions restored")

    print("\n✓ All PRY animation tests passed!")

def test_pry_has_animation():
    """Test that AnimationFactory recognizes PRY as having an animation."""
    assert AnimationFactory.has_animation("PRY") == True
    assert AnimationFactory.has_animation("pry") == True
    assert AnimationFactory.has_animation("VAULT") == False  # Not implemented yet
    print("✓ PRY recognized as having animation")

if __name__ == "__main__":
    test_pry_has_animation()
    print()
    test_pry_animation_factory()
    print("\n" + "="*60)
    print("PRY ANIMATION INTEGRATION TEST COMPLETE")
    print("="*60)
