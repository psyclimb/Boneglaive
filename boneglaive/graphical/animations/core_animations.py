#!/usr/bin/env python3
"""
Core Animation Classes
General-purpose animations used across multiple units or game events.
"""
import random
import math
from .core import Particle
from boneglaive.graphical.sound_helper import play_sound


class RespawnAnimation:
    """
    Respawn animation for units returning to the battlefield.
    Unit rises from beneath the ground with bone particles erupting.

    Phases:
    1. Ground Crack (0.2s) - Cracks appear, bone shards start emerging
    2. Emergence (0.6s) - Unit rises from below ground with rotation
    3. Settling (0.2s) - Unit lands at normal height, final particle burst

    Total duration: 1.0s
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize respawn animation.

        Args:
            caster_unit: Unit being respawned (same as target_unit)
            target_pos: Respawn position (grid_y, grid_x)
            particle_emitter: Particle system for bone effects
            screen_shake_callback: Screen shake function
            camera: Camera for coordinate conversion
        """
        self.caster = caster_unit
        self.target_pos = target_pos
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback or (lambda intensity, duration: None)
        self.camera = camera
        self.game = game

        self.phase = "ground_crack"
        self.timer = 0
        self.active = True

        # Phase durations
        self.crack_duration = 0.2
        self.emergence_duration = 0.6
        self.settling_duration = 0.2

        # Animation properties
        self.emergence_offset = 40  # How far below ground unit starts
        self.rotation_amount = 15  # Degrees of rotation during emergence

        # Store starting position
        if self.caster:
            play_sound("unit_respawn", category="general")
            self.start_y = self.caster.y
            self.caster.respawn_phase = "ground_crack"
            self.caster.respawn_timer = 0
            self.caster.respawn_y_offset = self.emergence_offset
            self.caster.respawn_rotation = 0

            # Initial ground crack particles
            self._emit_ground_crack()

    def _emit_ground_crack(self):
        """Emit initial ground crack particles."""
        if not self.caster or not self.particle_emitter:
            return

        # Ground crack lines (small particles radiating outward)
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            speed = random.uniform(30, 60)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Gray/brown crack particles
            color = random.choice([
                (100, 90, 80),
                (120, 110, 100),
                (90, 80, 70)
            ])

            particle = Particle(
                self.caster.x,
                self.caster.y + 20,  # Ground level
                vx, vy,
                color,
                random.uniform(2, 4),
                random.uniform(0.3, 0.5)
            )
            particle.gravity = 0  # Slide along ground
            self.particle_emitter.particles.append(particle)

    def _emit_bone_particles(self, intensity=1.0):
        """Emit bone shard particles erupting from ground."""
        if not self.caster or not self.particle_emitter:
            return

        count = int(8 * intensity)
        for _ in range(count):
            # Random angle (favor upward)
            angle = random.uniform(-math.pi * 0.3, -math.pi * 0.7)  # Upward cone
            speed = random.uniform(80, 150) * intensity
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Bone colors - white/cream/gray shards
            color = random.choice([
                (240, 240, 230),  # Off-white
                (230, 230, 220),  # Cream
                (200, 200, 190),  # Light gray
                (220, 215, 210),  # Bone white
            ])

            particle = Particle(
                self.caster.x + random.uniform(-15, 15),
                self.caster.y + 20,  # Ground level
                vx, vy,
                color,
                random.uniform(3, 7),
                random.uniform(0.5, 0.8)
            )
            particle.gravity = 200  # Fall back down
            self.particle_emitter.particles.append(particle)

    def _emit_settling_burst(self):
        """Emit final particle burst when unit settles."""
        if not self.caster or not self.particle_emitter:
            return

        # Dust cloud
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 20  # Slight upward bias

            particle = Particle(
                self.caster.x,
                self.caster.y + 20,
                vx, vy,
                (180, 180, 170),
                random.uniform(4, 8),
                random.uniform(0.4, 0.7)
            )
            particle.gravity = 100
            self.particle_emitter.particles.append(particle)

        # Final bone shards
        self._emit_bone_particles(0.5)

    def update(self, delta_time):
        """Update respawn animation - returns True if still active."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "ground_crack":
            # Ground cracks appear, initial bone particles emerge
            progress = min(1.0, self.timer / self.crack_duration)

            # Emit particles throughout crack phase
            if random.random() < 0.3:  # 30% chance per frame
                self._emit_bone_particles(0.3)

            if self.timer >= self.crack_duration:
                self.phase = "emergence"
                self.timer = 0
                if self.caster:
                    self.caster.respawn_phase = "emergence"
                    self.caster.respawn_timer = 0

                # Emergence shake
                self.screen_shake(4, 0.3)

        elif self.phase == "emergence":
            # Unit rises from below ground with rotation
            progress = min(1.0, self.timer / self.emergence_duration)

            if self.caster:
                # Smooth easing (ease-out)
                eased_progress = 1 - (1 - progress) ** 2

                # Y offset decreases from emergence_offset to 0
                self.caster.respawn_y_offset = self.emergence_offset * (1 - eased_progress)

                # Rotation (rotates as it rises, then straightens)
                if progress < 0.5:
                    # First half: increase rotation
                    self.caster.respawn_rotation = (progress / 0.5) * self.rotation_amount
                else:
                    # Second half: decrease rotation back to 0
                    self.caster.respawn_rotation = self.rotation_amount * (1 - (progress - 0.5) / 0.5)

                self.caster.respawn_timer += delta_time

            # Continuous bone particle emission during emergence
            if random.random() < 0.5:  # 50% chance per frame
                self._emit_bone_particles(0.6)

            if self.timer >= self.emergence_duration:
                self.phase = "settling"
                self.timer = 0
                if self.caster:
                    self.caster.respawn_phase = "settling"
                    self.caster.respawn_timer = 0
                    self.caster.respawn_y_offset = 0
                    self.caster.respawn_rotation = 0

                # Landing effects
                self._emit_settling_burst()
                self.screen_shake(3, 0.2)

        elif self.phase == "settling":
            # Brief landing recovery
            progress = min(1.0, self.timer / self.settling_duration)

            if self.caster:
                self.caster.respawn_timer += delta_time

            if self.timer >= self.settling_duration:
                self.active = False
                if self.caster:
                    self.caster.respawn_phase = None
                    self.caster.respawn_y_offset = 0
                    self.caster.respawn_rotation = 0

        return self.active

    def draw(self, surface):
        """No additional drawing needed - unit renders itself with offset/rotation."""
        pass
