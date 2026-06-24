#!/usr/bin/env python3
"""
DERELICTIONIST Animation Classes
Skill animations for the DERELICTIONIST unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE
from boneglaive.graphical.sound_helper import play_sound


# ============================================================================
# PARTITION ANIMATION
# ============================================================================

class EnergyWave:
    """
    Single energy wave expanding outward from center.
    Creates the initial forcefield generation effect.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay  # Negative timer for staggered start
        self.duration = 0.5
        self.active = True
        self.max_radius = 45

    def update(self, delta_time):
        """Update wave expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding energy wave."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expand outward with ease-out
        radius = int(self.max_radius * progress)

        # Fade out as it expands
        alpha = int(200 * (1.0 - progress))

        if alpha > 0 and radius > 0:
            wave_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Draw bright blue expanding ring (hollow circle)
            pygame.draw.circle(wave_surf, (154, 202, 248, alpha), (radius, radius), radius, 3)

            # Inner glow
            if alpha > 100:
                pygame.draw.circle(wave_surf, (122, 186, 232, alpha // 2), (radius, radius), radius - 2, 2)

            surface.blit(wave_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class ForcefieldBubble:
    """
    Main forcefield bubble shell.
    Transparent sphere with shimmering surface.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.5
        self.active = True

        # Bubble properties
        self.radius = 38
        self.shimmer_phase = 0
        self.alpha = 0

        # Shimmer points around circumference
        self.shimmer_points = []
        num_points = 16
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            self.shimmer_points.append({
                'angle': angle,
                'offset': random.uniform(0, 2 * math.pi)
            })

    def update(self, delta_time):
        """Update bubble shimmer and alpha."""
        if not self.active:
            return False

        self.timer += delta_time
        self.shimmer_phase += delta_time * 3

        # Fade in, stay visible, then fade out
        if self.timer < 0.3:
            self.alpha = int(150 * (self.timer / 0.3))
        elif self.timer < 1.2:
            self.alpha = 150
        else:
            self.alpha = int(150 * (1.0 - (self.timer - 1.2) / 0.3))

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw forcefield bubble."""
        if not self.active or self.alpha <= 0:
            return

        bubble_size = self.radius * 2
        bubble_surf = pygame.Surface((bubble_size, bubble_size), pygame.SRCALPHA)

        # Main bubble shell (bright blue, semi-transparent)
        pygame.draw.circle(bubble_surf, (90, 138, 168, self.alpha // 2),
                         (self.radius, self.radius), self.radius, 2)

        # Inner shimmer layer
        inner_radius = self.radius - 4
        pygame.draw.circle(bubble_surf, (154, 202, 248, self.alpha // 3),
                         (self.radius, self.radius), inner_radius, 1)

        # Draw shimmer points around circumference
        for point in self.shimmer_points:
            # Shimmer intensity varies over time
            shimmer = 0.5 + 0.5 * math.sin(self.shimmer_phase + point['offset'])
            shimmer_alpha = int(self.alpha * shimmer)

            if shimmer_alpha > 50:
                # Position on bubble circumference
                px = self.radius + math.cos(point['angle']) * self.radius
                py = self.radius + math.sin(point['angle']) * self.radius

                # Draw small bright spot
                shimmer_size = 3
                pygame.draw.circle(bubble_surf, (232, 232, 240, shimmer_alpha),
                                 (int(px), int(py)), shimmer_size)

        surface.blit(bubble_surf, (int(self.center_x - self.radius), int(self.center_y - self.radius)))


class EnergyArcs:
    """
    Electric-like arcs dancing across the forcefield surface.
    Creates dynamic energy effect.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.2
        self.active = True
        self.radius = 38

        # Arc segments
        self.arcs = []

    def spawn_arc(self):
        """Spawn a new arc on the bubble surface."""
        # Random start and end angles
        start_angle = random.uniform(0, 2 * math.pi)
        arc_length = random.uniform(math.pi / 4, math.pi / 2)

        self.arcs.append({
            'start_angle': start_angle,
            'end_angle': start_angle + arc_length,
            'lifetime': 0,
            'duration': random.uniform(0.2, 0.4),
            'active': True
        })

    def update(self, delta_time):
        """Update arcs."""
        if not self.active:
            return False

        self.timer += delta_time

        # Spawn new arcs periodically
        if random.random() < delta_time * 5:  # ~5 arcs per second
            self.spawn_arc()

        # Update existing arcs
        for arc in self.arcs:
            arc['lifetime'] += delta_time
            if arc['lifetime'] >= arc['duration']:
                arc['active'] = False

        # Remove dead arcs
        self.arcs = [a for a in self.arcs if a['active']]

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw energy arcs."""
        if not self.active:
            return

        for arc in self.arcs:
            progress = arc['lifetime'] / arc['duration']

            # Fade in and out
            if progress < 0.3:
                alpha = int(220 * (progress / 0.3))
            elif progress > 0.7:
                alpha = int(220 * (1.0 - (progress - 0.7) / 0.3))
            else:
                alpha = 220

            if alpha > 0:
                # Draw arc segments
                num_segments = 8
                for i in range(num_segments):
                    t = i / num_segments
                    angle = arc['start_angle'] + (arc['end_angle'] - arc['start_angle']) * t

                    # Position on bubble surface
                    x1 = self.center_x + math.cos(angle) * self.radius
                    y1 = self.center_y + math.sin(angle) * self.radius

                    # Next segment
                    if i < num_segments - 1:
                        t2 = (i + 1) / num_segments
                        angle2 = arc['start_angle'] + (arc['end_angle'] - arc['start_angle']) * t2
                        x2 = self.center_x + math.cos(angle2) * self.radius
                        y2 = self.center_y + math.sin(angle2) * self.radius

                        # Draw line segment (bright ice blue)
                        pygame.draw.line(surface, (154, 202, 248, alpha),
                                       (int(x1), int(y1)), (int(x2), int(y2)), 2)


class BubbleParticles:
    """
    Small particles floating around inside the forcefield.
    Creates sense of contained energy.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.2
        self.active = True
        self.radius = 35  # Stay inside bubble

        # Create floating particles
        self.particles = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius * 0.8)
            self.particles.append({
                'angle': angle,
                'distance': distance,
                'float_speed': random.uniform(-0.5, 0.5),
                'orbit_speed': random.uniform(-0.8, 0.8),
                'size': random.uniform(2, 4),
                'phase': random.uniform(0, 2 * math.pi)
            })

    def update(self, delta_time):
        """Update floating particles."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particle positions
        for p in self.particles:
            # Float in/out slightly
            p['phase'] += delta_time * 2
            p['distance'] += math.sin(p['phase']) * p['float_speed'] * delta_time * 10

            # Gentle orbit
            p['angle'] += p['orbit_speed'] * delta_time

            # Keep inside bubble
            p['distance'] = max(0, min(self.radius * 0.8, p['distance']))

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw floating particles."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fade in and out
        if progress < 0.2:
            alpha = int(180 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(180 * (1.0 - (progress - 0.8) / 0.2))
        else:
            alpha = 180

        if alpha > 0:
            for p in self.particles:
                # Calculate position
                px = self.center_x + math.cos(p['angle']) * p['distance']
                py = self.center_y + math.sin(p['angle']) * p['distance']

                # Draw particle (pale blue)
                particle_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (122, 186, 232, alpha),
                                 (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(particle_surf, (int(px - p['size']), int(py - p['size'])))


class PartitionAnimation:
    """
    Partition skill animation for DERELICTIONIST.
    Creates a circular forcefield bubble around an ally that shields them from harm.

    Phases:
    1. Formation (0.5s) - Energy waves expand outward, bubble forms
    2. Active (1.2s) - Forcefield fully formed with shimmering surface and energy arcs
    3. Fadeout (0.5s) - Bubble fades out gracefully
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Partition animation.

        Args:
            caster_unit: The DERELICTIONIST casting Partition
            target_unit: The ally being partitioned
            target_pos: (grid_y, grid_x) - Position of ally
            camera: Camera for coordinate conversion
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Convert target grid position to screen coords
        # CRITICAL: target_pos is (grid_y, grid_x), but grid_to_screen takes (grid_x, grid_y)!
        grid_y, grid_x = target_pos
        self.center_x, self.center_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "formation"  # formation -> active -> fadeout
        self.timer = 0
        self.active = True

        # Sub-effects
        self.waves = []
        self.bubble = None
        self.arcs = None
        self.particles = None

        # Start Phase 1
        self._start_formation()

    def _start_formation(self):
        """Phase 1: Formation - Energy waves create forcefield."""
        self.phase = "formation"
        self.timer = 0
        play_sound("partition_cast")

        # Create expanding energy waves (3 waves with stagger)
        for i in range(3):
            self.waves.append(EnergyWave(self.center_x, self.center_y, delay=i * 0.1))

        # Emit initial particle burst (pale blue)
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.center_x, self.center_y, (122, 186, 232), count=20)

        # Light screen shake for energy surge
        self.screen_shake_callback(2, 0.4)

    def _start_active(self):
        """Phase 2: Active - Forcefield fully formed and shimmering."""
        self.phase = "active"
        self.timer = 0

        # Create main forcefield bubble
        self.bubble = ForcefieldBubble(self.center_x, self.center_y)

        # Create energy arcs
        self.arcs = EnergyArcs(self.center_x, self.center_y)

        # Create floating particles inside bubble
        self.particles = BubbleParticles(self.center_x, self.center_y)

        # Bright flash at full formation (removed — screen flashes reserved for Rail Genesis)

    def _start_fadeout(self):
        """Phase 3: Fadeout - Forcefield fades gracefully."""
        self.phase = "fadeout"
        self.timer = 0

        # Bubble and particles will fade out naturally through their alpha

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "formation" and self.timer >= 0.5:
            self._start_active()
        elif self.phase == "active" and self.timer >= 1.2:
            self._start_fadeout()
        elif self.phase == "fadeout" and self.timer >= 0.5:
            self.active = False  # Animation complete

        # Update sub-effects
        self.waves = [w for w in self.waves if w.update(delta_time)]

        if self.bubble:
            self.bubble.update(delta_time)

        if self.arcs:
            self.arcs.update(delta_time)

        if self.particles:
            self.particles.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw expanding waves (Phase 1)
        for wave in self.waves:
            wave.draw(surface)

        # Draw floating particles (Phase 2-3, draw first so they appear behind bubble)
        if self.particles:
            self.particles.draw(surface)

        # Draw main bubble shell (Phase 2-3)
        if self.bubble:
            self.bubble.draw(surface)

        # Draw energy arcs (Phase 2-3, draw last so they appear on top)
        if self.arcs:
            self.arcs.draw(surface)


# ============================================================================
# PARTITION HIT ANIMATION (Damage Reaction)
# ============================================================================

class ForcefieldHitFlash:
    """
    Quick forcefield visibility when Partition absorbs damage.
    Based on ForcefieldBubble from Partition application, but shorter and more intense.
    Shows the same sphere as the main animation but as a brief bright flash.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5  # Much shorter than main animation (0.5s vs 1.5s)
        self.active = True

        # Bubble properties (same as ForcefieldBubble)
        self.radius = 38
        self.shimmer_phase = 0
        self.alpha = 0

        # More shimmer points for more intense flash (20 vs 16)
        self.shimmer_points = []
        num_points = 20
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            self.shimmer_points.append({
                'angle': angle,
                'offset': random.uniform(0, 2 * math.pi)
            })

    def update(self, delta_time):
        """Update bubble shimmer and alpha."""
        if not self.active:
            return False

        self.timer += delta_time
        self.shimmer_phase += delta_time * 8  # Faster shimmer (×8 vs ×3)

        # Quick fade in, brief hold, fade out
        if self.timer < 0.1:
            # Quick fade in
            self.alpha = int(200 * (self.timer / 0.1))
        elif self.timer < 0.3:
            # Hold at bright
            self.alpha = 200
        else:
            # Fade out
            self.alpha = int(200 * (1.0 - (self.timer - 0.3) / 0.2))

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw forcefield bubble (same style as ForcefieldBubble)."""
        if not self.active or self.alpha <= 0:
            return

        bubble_size = self.radius * 2
        bubble_surf = pygame.Surface((bubble_size, bubble_size), pygame.SRCALPHA)

        # Main bubble shell (bright blue, semi-transparent)
        pygame.draw.circle(bubble_surf, (90, 138, 168, self.alpha // 2),
                         (self.radius, self.radius), self.radius, 2)

        # Inner shimmer layer
        inner_radius = self.radius - 4
        pygame.draw.circle(bubble_surf, (154, 202, 248, self.alpha // 3),
                         (self.radius, self.radius), inner_radius, 1)

        # Draw shimmer points around circumference
        for point in self.shimmer_points:
            # Shimmer intensity varies over time
            shimmer = 0.5 + 0.5 * math.sin(self.shimmer_phase + point['offset'])
            shimmer_alpha = int(self.alpha * shimmer)

            if shimmer_alpha > 50:
                # Position on bubble circumference
                px = self.radius + math.cos(point['angle']) * self.radius
                py = self.radius + math.sin(point['angle']) * self.radius

                # Draw small bright spot
                shimmer_size = 3
                pygame.draw.circle(bubble_surf, (232, 232, 240, shimmer_alpha),
                                 (int(px), int(py)), shimmer_size)

        surface.blit(bubble_surf, (int(self.center_x - self.radius), int(self.center_y - self.radius)))


class PartitionHitAnimation:
    """
    Partition shield hit animation - plays when protected unit takes damage.
    Shows the same forcefield sphere as the main Partition animation, but as a quick bright flash.

    Uses the same visual design as the Partition application for consistency:
    - Same sphere size (38px radius)
    - Same blue colors
    - Same shimmer points
    - But brighter (alpha 200 vs 150) and faster (0.5s vs 1.5s)

    Triggered automatically when PRT absorbs damage.
    """

    def __init__(self, unit, camera, damage_source_pos=None):
        """
        Initialize Partition hit animation.

        Args:
            unit: AnimatedUnit that has Partition active and took damage
            camera: Camera for coordinate conversion
            damage_source_pos: Optional (grid_y, grid_x) of damage source (unused currently)
        """
        self.unit = unit
        self.camera = camera
        self.active = True
        self.timer = 0
        self.duration = 0.5  # Quick flash

        # Convert unit position to screen coords
        self.center_x, self.center_y = camera.grid_to_screen(unit.grid_x, unit.grid_y, centered=True)

        play_sound("partition_hit")

        # Single effect: forcefield flash
        self.firmament = ForcefieldHitFlash(self.center_x, self.center_y)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update forcefield flash
        self.firmament.update(delta_time)

        # End when duration reached
        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw forcefield flash
        self.firmament.draw(surface)


# ============================================================================
# PARTITION DISSOCIATION ANIMATION (Emergency Trigger)
# ============================================================================

class ConcentricRings:
    """
    Inward-rippling rings on bubble surface when fatal damage is detected.
    Multiple rings ripple inward toward center to show impact absorption.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True
        self.max_radius = 38  # Match forcefield bubble radius

        # Create 3 rings with staggered timing
        self.rings = []
        for i in range(3):
            self.rings.append({
                'delay': i * 0.08,
                'progress': 0
            })

    def update(self, delta_time):
        """Update rings rippling inward."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update each ring
        for ring in self.rings:
            if self.timer >= ring['delay']:
                ring_age = self.timer - ring['delay']
                ring['progress'] = min(1.0, ring_age / self.duration)

        if self.timer >= (self.duration + 0.16):  # Last ring delay + duration
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw inward-rippling rings."""
        if not self.active:
            return

        for ring in self.rings:
            if ring['progress'] > 0:
                # Ripple INWARD (start at max radius, end at 0)
                radius = int(self.max_radius * (1.0 - ring['progress']))

                # Fade out as reaching center
                alpha = int(220 * (1.0 - ring['progress']))

                if alpha > 0 and radius > 0:
                    ring_surf = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
                    # Bright ice-white rings
                    pygame.draw.circle(ring_surf, (232, 232, 240, alpha),
                                     (self.max_radius, self.max_radius), radius, 3)
                    surface.blit(ring_surf,
                               (int(self.center_x - self.max_radius),
                                int(self.center_y - self.max_radius)))


class ImpenetrableForcefield:
    """
    Forcefield bubble that solidifies into impenetrable barrier.
    Becomes opaque, thick-walled, with locked geometric patterns.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.4  # Lock phase + hold
        self.active = True

        # Bubble properties
        self.radius = 38
        self.wall_thickness = 2  # Start thin, will grow to 6
        self.alpha = 0
        self.solidification_progress = 0

        # Shimmer points (same as normal bubble, but will lock solid)
        self.shimmer_points = []
        num_points = 20  # More points for emergency lock
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            self.shimmer_points.append({
                'angle': angle,
                'locked': False,
                'lock_time': random.uniform(0.1, 0.4)  # Stagger locking
            })

    def update(self, delta_time):
        """Update forcefield solidification."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase 1: Lock-in (0-0.6s) - Solidify rapidly
        if self.timer < 0.6:
            self.solidification_progress = self.timer / 0.6
            self.wall_thickness = 2 + int(4 * self.solidification_progress)
            self.alpha = int(200 * self.solidification_progress)

            # Lock shimmer points progressively
            for point in self.shimmer_points:
                if self.timer >= point['lock_time']:
                    point['locked'] = True

        # Phase 2: Hold impenetrable (0.6-1.4s)
        elif self.timer < 1.4:
            self.solidification_progress = 1.0
            self.wall_thickness = 6
            self.alpha = 200

        # End
        else:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw impenetrable forcefield."""
        if not self.active or self.alpha <= 0:
            return

        bubble_size = self.radius * 2
        bubble_surf = pygame.Surface((bubble_size, bubble_size), pygame.SRCALPHA)

        # Main bubble shell (bright ice-blue, increasingly opaque)
        # Use brighter colors as it solidifies
        shell_color_r = 90 + int(142 * self.solidification_progress)  # 90 -> 232
        shell_color_g = 138 + int(94 * self.solidification_progress)  # 138 -> 232
        shell_color_b = 168 + int(72 * self.solidification_progress)  # 168 -> 240

        pygame.draw.circle(bubble_surf,
                         (shell_color_r, shell_color_g, shell_color_b, self.alpha),
                         (self.radius, self.radius), self.radius, self.wall_thickness)

        # Inner glow (brighter as it locks)
        if self.solidification_progress > 0.3:
            inner_alpha = int(self.alpha * 0.4)
            pygame.draw.circle(bubble_surf, (232, 232, 240, inner_alpha),
                             (self.radius, self.radius), self.radius - self.wall_thickness - 2)

        # Draw shimmer points (locked solid or dancing)
        for point in self.shimmer_points:
            if point['locked']:
                # Locked solid bright spot
                shimmer_alpha = self.alpha
            else:
                # Still dancing (not locked yet)
                shimmer_alpha = int(self.alpha * 0.5)

            if shimmer_alpha > 50:
                px = self.radius + math.cos(point['angle']) * self.radius
                py = self.radius + math.sin(point['angle']) * self.radius

                size = 4 if point['locked'] else 3
                pygame.draw.circle(bubble_surf, (255, 255, 255, shimmer_alpha),
                                 (int(px), int(py)), size)

        # Geometric reinforcement patterns (appear during solidification)
        if self.solidification_progress > 0.4:
            pattern_alpha = int(self.alpha * (self.solidification_progress - 0.4) / 0.6)
            if pattern_alpha > 0:
                # Draw hexagonal pattern
                num_hexes = 6
                hex_radius = self.radius * 0.6
                for i in range(num_hexes):
                    angle = (i / num_hexes) * 2 * math.pi
                    hx = self.radius + math.cos(angle) * hex_radius
                    hy = self.radius + math.sin(angle) * hex_radius
                    pygame.draw.circle(bubble_surf, (154, 202, 248, pattern_alpha),
                                     (int(hx), int(hy)), 4, 1)

        surface.blit(bubble_surf, (int(self.center_x - self.radius), int(self.center_y - self.radius)))


class RollingEyesEffect:
    """
    Large white circles spiraling upward from unit position (eyes rolling back into skull).
    Key visual indicator of dissociation.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.8
        self.active = True

        # Two eyes
        self.eyes = [
            {'offset_x': -8, 'phase': 0},
            {'offset_x': 8, 'phase': 0.1}  # Slight delay for second eye
        ]

    def update(self, delta_time):
        """Update eye rolling animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw rolling eyes effect."""
        if not self.active:
            return

        for eye in self.eyes:
            eye_timer = self.timer - eye['phase']
            if eye_timer < 0:
                continue

            progress = min(1.0, eye_timer / (self.duration - eye['phase']))

            # Eyes spiral upward and fade
            spiral_height = progress * 25  # Rise 25 pixels
            spiral_angle = progress * math.pi * 2  # One full rotation

            # Spiral outward slightly as rising
            spiral_radius = progress * 6

            eye_x = self.center_x + eye['offset_x'] + math.cos(spiral_angle) * spiral_radius
            eye_y = self.center_y - spiral_height

            # Fade out as rising
            alpha = int(255 * (1.0 - progress))

            if alpha > 0:
                # Draw large white circle (eyeball)
                eye_size = 6
                eye_surf = pygame.Surface((eye_size * 2, eye_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(eye_surf, (255, 255, 255, alpha), (eye_size, eye_size), eye_size)
                # Dark pupil
                pygame.draw.circle(eye_surf, (40, 40, 60, alpha), (eye_size, eye_size), eye_size // 2)
                surface.blit(eye_surf, (int(eye_x - eye_size), int(eye_y - eye_size)))


class AnchoredEffect:
    """
    Heavy particles settling downward around unit (Derelicted/immobilized effect).
    Creates visual weight and grounded feeling.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.8
        self.active = True

        # Create falling particles
        self.particles = []
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            start_radius = 20
            self.particles.append({
                'start_x': center_x + math.cos(angle) * start_radius,
                'start_y': center_y + math.sin(angle) * start_radius - 15,  # Start above
                'target_y': center_y + 18,  # Settle at feet
                'size': random.uniform(3, 6)
            })

    def update(self, delta_time):
        """Update anchored particles settling."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw anchored settling particles."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        for p in self.particles:
            # Fall with ease-out
            ease_progress = 1 - math.pow(1 - progress, 3)
            current_y = p['start_y'] + (p['target_y'] - p['start_y']) * ease_progress

            # Fade in as settling
            alpha = int(180 * progress)

            if alpha > 0:
                particle_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                # Dark blue, heavy particles
                pygame.draw.circle(particle_surf, (58, 122, 168, alpha),
                                 (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(particle_surf, (int(p['start_x'] - p['size']), int(current_y - p['size'])))


class PartitionDissociationAnimation:
    """
    Partition dissociation animation for DERELICTIONIST emergency trigger.

    Plays when partitioned ally would take fatal damage:
    - Forcefield solidifies into impenetrable barrier (PRT → 999)
    - Eyes roll back (dissociation visual)
    - Severance line connects protected unit to DERELICTIONIST
    - Line snaps (relationship broken)
    - Protected unit becomes anchored (Derelicted status)
    - DERELICTIONIST is teleported away

    Phases:
    1. Fatal Impact (0.3s) - Rings ripple inward, forcefield flashes
    2. Emergency Lock (0.6s) - Forcefield solidifies, becomes impenetrable
    3. Dissociation (0.8s) - Eyes roll back, severance line appears and stretches
    4. Aftermath (0.8s) - Line snaps, particles scatter, anchored effect
    """

    def __init__(self, protected_unit, derelictionist_unit, camera,
                 screen_shake_callback, screen_flash_callback, particle_emitter=None):
        """
        Initialize Partition Dissociation animation.

        Args:
            protected_unit: AnimatedUnit with partition shield that triggered dissociation
            derelictionist_unit: DERELICTIONIST who cast the partition
            camera: Camera for coordinate conversion
            screen_shake_callback: Function to trigger screen shake
            screen_flash_callback: Function to trigger screen flash
            particle_emitter: Optional particle emitter
        """
        # Store references
        self.protected_unit = protected_unit
        self.derelictionist = derelictionist_unit
        self.camera = camera
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.particle_emitter = particle_emitter

        # Convert unit positions to screen coords
        self.protected_x, self.protected_y = camera.grid_to_screen(
            protected_unit.grid_x, protected_unit.grid_y, centered=True)
        self.derelictionist_x, self.derelictionist_y = camera.grid_to_screen(
            derelictionist_unit.grid_x, derelictionist_unit.grid_y, centered=True)

        # Animation state
        self.phase = "impact"  # impact -> lock -> dissociation -> aftermath
        self.timer = 0
        self.active = True

        # Sub-effects
        self.rings = None
        self.forcefield = None
        self.eyes = None
        # severance_line removed
        # snap_particles removed
        self.anchored = None

        # Start Phase 1
        self._start_impact()

    def _start_impact(self):
        """Phase 1: Fatal Impact Detection."""
        self.phase = "impact"
        self.timer = 0
        play_sound("partition_dissociate")

        # Concentric rings ripple inward
        self.rings = ConcentricRings(self.protected_x, self.protected_y)

        # Screen shake (danger detected)
        self.screen_shake_callback(7, 0.3)

        # Bright white-blue flash (removed — screen flashes reserved for Rail Genesis)

    def _start_lock(self):
        """Phase 2: Emergency Lock - Forcefield solidifies."""
        self.phase = "lock"
        self.timer = 0

        # Create impenetrable forcefield
        self.forcefield = ImpenetrableForcefield(self.protected_x, self.protected_y)

        # Medium shake (barrier locking)
        self.screen_shake_callback(5, 0.5)

    def _start_dissociation(self):
        """Phase 3: Dissociation - Eyes roll back."""
        self.phase = "dissociation"
        self.timer = 0
        play_sound("partition_shatter")

        # Eyes rolling back
        self.eyes = RollingEyesEffect(self.protected_x, self.protected_y)

        # No severance line - removed per user request

        # Light shake (mental separation)
        self.screen_shake_callback(3, 0.6)

    def _start_aftermath(self):
        """Phase 4: Aftermath - Anchored effect."""
        self.phase = "aftermath"
        self.timer = 0

        # No line snap particles - line removed

        # Anchored effect on protected unit
        self.anchored = AnchoredEffect(self.protected_x, self.protected_y)

        # Light shake (aftermath)
        self.screen_shake_callback(2, 0.4)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "impact" and self.timer >= 0.3:
            self._start_lock()
        elif self.phase == "lock" and self.timer >= 0.6:
            self._start_dissociation()
        elif self.phase == "dissociation" and self.timer >= 0.8:
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.8:
            self.active = False  # Animation complete

        # Update sub-effects
        if self.rings:
            self.rings.update(delta_time)
        if self.forcefield:
            self.forcefield.update(delta_time)
        if self.eyes:
            self.eyes.update(delta_time)
        # severance_line removed
        # snap_particles removed
        if self.anchored:
            self.anchored.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw in layers (back to front)

        # Phase 1: Rings
        if self.rings:
            self.rings.draw(surface)

        # Phase 2-4: Forcefield (draw early so other effects appear on top)
        if self.forcefield:
            self.forcefield.draw(surface)

        # Phase 4: Anchored particles (behind unit)
        if self.anchored:
            self.anchored.draw(surface)

        # severance_line removed
        # snap_particles removed

        # Phase 3: Eyes (on top, most visible)
        if self.eyes:
            self.eyes.draw(surface)


# ============================================================================
# DERELICTED STATUS EFFECT APPLICATION ANIMATION
# ============================================================================

class SeveranceGlowLine:
    """
    Vertical glowing line extending through unit (psychological connection severed).
    Bright ice-blue glow representing the moment of abandonment.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5
        self.active = True

        self.line_length = 50  # Extends 25px above and below unit

    def update(self, delta_time):
        """Update glow line pulsing."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw vertical severance glow line."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Pulse intensity
        pulse = 0.7 + 0.3 * math.sin(self.timer * 12)

        # Alpha fades out over time
        base_alpha = int(200 * (1.0 - progress) * pulse)

        if base_alpha > 0:
            # Outer glow (widest, dimmest)
            pygame.draw.line(surface, (170, 218, 255, base_alpha // 3),
                           (int(self.center_x), int(self.center_y - self.line_length / 2)),
                           (int(self.center_x), int(self.center_y + self.line_length / 2)),
                           5)

            # Middle glow
            pygame.draw.line(surface, (221, 238, 255, base_alpha // 2),
                           (int(self.center_x), int(self.center_y - self.line_length / 2)),
                           (int(self.center_x), int(self.center_y + self.line_length / 2)),
                           3)

            # Inner core (brightest)
            pygame.draw.line(surface, (255, 255, 255, base_alpha),
                           (int(self.center_x), int(self.center_y - self.line_length / 2)),
                           (int(self.center_x), int(self.center_y + self.line_length / 2)),
                           1)


class FragmentationCracks:
    """
    Dark cracks spreading through unit area with ice-blue fragments scattering.
    Represents self fragmenting from abandonment trauma.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5
        self.active = True

        # Create radial cracks
        self.cracks = []
        num_cracks = 6
        for i in range(num_cracks):
            angle = (i / num_cracks) * 2 * math.pi
            self.cracks.append({
                'angle': angle,
                'length': random.uniform(15, 25)
            })

        # Create scattering fragments
        self.fragments = []
        num_fragments = 12
        for i in range(num_fragments):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 50)
            self.fragments.append({
                'x': center_x,
                'y': center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(2, 4),
                'color_choice': random.choice([(90, 154, 200), (122, 186, 232), (154, 202, 248)])
            })

    def update(self, delta_time):
        """Update crack spreading and fragments scattering."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update fragment positions
        for frag in self.fragments:
            frag['x'] += frag['vx'] * delta_time
            frag['y'] += frag['vy'] * delta_time
            # Slow down
            frag['vx'] *= 0.93
            frag['vy'] *= 0.93

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw cracks and fragments."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Draw cracks (black lines)
        crack_alpha = int(255 * progress)
        if crack_alpha > 0:
            for crack in self.cracks:
                length = crack['length'] * progress
                end_x = self.center_x + math.cos(crack['angle']) * length
                end_y = self.center_y + math.sin(crack['angle']) * length

                pygame.draw.line(surface, (0, 0, 0, crack_alpha),
                               (int(self.center_x), int(self.center_y)),
                               (int(end_x), int(end_y)),
                               2)

        # Draw fragments (ice-blue particles)
        frag_alpha = int(220 * (1.0 - progress))
        if frag_alpha > 0:
            for frag in self.fragments:
                frag_surf = pygame.Surface((int(frag['size'] * 2), int(frag['size'] * 2)), pygame.SRCALPHA)
                color = frag['color_choice'] + (frag_alpha)
                pygame.draw.circle(frag_surf, color,
                                 (int(frag['size']), int(frag['size'])), int(frag['size']))
                surface.blit(frag_surf, (int(frag['x'] - frag['size']), int(frag['y'] - frag['size'])))


class FallingMetalBeam:
    """
    Individual rusted metal beam/girder falling with rotation.
    Heavy abandoned structural element binding the unit.
    """
    def __init__(self, start_x, start_y, target_x, target_y, beam_type='vertical'):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.beam_type = beam_type  # 'vertical', 'horizontal', or 'fragment'

        self.timer = 0
        self.duration = 0.6  # Falling duration
        self.active = True

        # Rotation during fall
        self.rotation = random.uniform(-20, 20)
        self.rotation_speed = random.uniform(-180, 180)  # degrees per second

        # Beam dimensions based on type
        if beam_type == 'vertical':
            self.width = 4
            self.height = 18
        elif beam_type == 'horizontal':
            self.width = 14
            self.height = 3
        else:  # fragment
            self.width = random.randint(4, 8)
            self.height = random.randint(4, 8)

        # Metal color (grey with slight blue tint)
        self.color = (96, 96, 96)  # Base grey
        self.edge_color = (80, 80, 80)  # Darker edge

    def update(self, delta_time):
        """Update falling motion and rotation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False
            # Snap to final position
            self.x = self.target_x
            self.y = self.target_y
        else:
            # Ease-out fall
            progress = self.timer / self.duration
            ease_progress = 1 - math.pow(1 - progress, 3)

            self.x = self.x + (self.target_x - self.x) * ease_progress * delta_time / (self.duration - self.timer + 0.001)
            self.y = self.y + (self.target_y - self.y) * ease_progress * delta_time / (self.duration - self.timer + 0.001)

            # Update rotation
            self.rotation += self.rotation_speed * delta_time

        return self.active

    def draw(self, surface):
        """Draw falling metal beam."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(150 + 105 * progress)  # Fade in as falling

        # Create rotated rect surface
        beam_surf = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)

        # Draw metal beam with edge highlight
        beam_rect = pygame.Rect(2, 2, self.width, self.height)
        pygame.draw.rect(beam_surf, self.color + (alpha), beam_rect)
        pygame.draw.rect(beam_surf, self.edge_color + (alpha), beam_rect, 1)

        # Rotate
        rotated_surf = pygame.transform.rotate(beam_surf, self.rotation)
        rotated_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))

        surface.blit(rotated_surf, rotated_rect)


class MetalStructure:
    """
    Settled metal structure piece that binds the unit.
    Locked in place after falling.
    """
    def __init__(self, x, y, width, height, angle=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle

        self.timer = 0
        self.duration = 0.5  # Lock-in duration
        self.active = True

        self.locked = False

        # Colors
        self.base_color = (64, 64, 64)  # Locked dark grey
        self.glow_color = (90, 154, 200)  # Ice-blue glow

    def update(self, delta_time):
        """Update locking animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False
            self.locked = True

        return self.active

    def draw(self, surface):
        """Draw locked metal structure."""
        if not self.active and not self.locked:
            return

        progress = min(1.0, self.timer / self.duration) if self.active else 1.0

        # Create rotated rect surface
        struct_surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)

        # Draw metal structure
        struct_rect = pygame.Rect(5, 5, self.width, self.height)
        alpha = 255
        pygame.draw.rect(struct_surf, self.base_color + (alpha), struct_rect)
        pygame.draw.rect(struct_surf, (48, 48, 48, alpha), struct_rect, 1)

        # Ice-blue glow during locking
        if self.active:
            glow_alpha = int(180 * (1.0 - progress))
            if glow_alpha > 0:
                pygame.draw.rect(struct_surf, self.glow_color + (glow_alpha), struct_rect, 2)

        # Rotate
        rotated_surf = pygame.transform.rotate(struct_surf, self.angle)
        rotated_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))

        surface.blit(rotated_surf, rotated_rect)


class DustImpact:
    """
    Grey dust cloud when metal structure hits ground.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 0.3
        self.active = True

        # Create dust particles
        self.particles = []
        num_particles = 8
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            speed = random.uniform(10, 25)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 10,  # Slight upward bias
                'size': random.uniform(1.5, 3)
            })

    def update(self, delta_time):
        """Update dust particles."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particle positions
        for p in self.particles:
            p['x'] += p['vx'] * delta_time
            p['y'] += p['vy'] * delta_time
            p['vy'] += 30 * delta_time  # Gravity
            p['vx'] *= 0.92

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw dust particles."""
        if not self.active:
            return

        progress = self.timer / self.duration
        alpha = int(180 * (1.0 - progress))

        if alpha > 0:
            for p in self.particles:
                dust_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(dust_surf, (128, 128, 128, alpha),
                                 (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(dust_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))


class BindingGlow:
    """
    Ice-blue wisps curling around locked metal structures.
    Represents cold abandonment energy binding the unit.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.4
        self.active = True

        # Create wisp particles
        self.wisps = []
        num_wisps = 6
        for i in range(num_wisps):
            angle = (i / num_wisps) * 2 * math.pi
            radius = 20
            self.wisps.append({
                'base_angle': angle,
                'radius': radius,
                'offset': random.uniform(0, 2 * math.pi)
            })

    def update(self, delta_time):
        """Update wisp animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw ice-blue wisps."""
        if not self.active:
            return

        progress = self.timer / self.duration
        alpha = int(150 * (1.0 - progress))

        if alpha > 0:
            for wisp in self.wisps:
                # Spiral outward
                angle = wisp['base_angle'] + self.timer * 4 + wisp['offset']
                radius = wisp['radius'] * (1 + progress * 0.5)

                x = self.center_x + math.cos(angle) * radius
                y = self.center_y + math.sin(angle) * radius

                wisp_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(wisp_surf, (122, 186, 232, alpha), (4, 4), 3)
                pygame.draw.circle(wisp_surf, (170, 218, 255, alpha // 2), (4, 4), 2)
                surface.blit(wisp_surf, (int(x - 4), int(y - 4)))


class DerelictedApplicationAnimation:
    """
    Derelicted status effect application animation.

    When a unit becomes Derelicted (immobilized by abandonment trauma):
    - Psychological connection is severed (bright ice-blue line)
    - Self fragments from trauma (cracks and ice-blue shards)
    - Heavy abandoned metal structures fall and bind the unit
    - Unit becomes trapped in derelict ruins, unable to move

    Phases:
    1. Connection Severance (0.5s) - Vertical glow line, psychological cut
    2. Fragmentation (0.5s) - Cracks spread, ice-blue fragments scatter
    3. Structural Collapse (0.8s) - Metal beams/debris fall and bind
    4. Immobilization Lock (instant) - Structures solidify, unit trapped
    """

    def __init__(self, target_unit, camera, screen_shake_callback,
                 screen_flash_callback, particle_emitter=None):
        """
        Initialize Derelicted application animation.

        Args:
            target_unit: AnimatedUnit receiving Derelicted status
            camera: Camera for coordinate conversion
            screen_shake_callback: Function to trigger screen shake
            screen_flash_callback: Function to trigger screen flash
            particle_emitter: Optional particle emitter
        """
        # Store references
        self.target_unit = target_unit
        self.camera = camera
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.particle_emitter = particle_emitter

        # Convert unit position to screen coords
        self.center_x, self.center_y = camera.grid_to_screen(
            target_unit.grid_x, target_unit.grid_y, centered=True)

        # Animation state
        self.phase = "severance"  # severance -> fragmentation -> collapse -> lock
        self.timer = 0
        self.active = True

        # Sub-effects
        self.severance_line = None
        self.fragmentation = None
        self.falling_beams = []
        self.locked_structures = []
        self.dust_impacts = []
        self.binding_glow = None

        # Start Phase 1
        self._start_severance()

    def _start_severance(self):
        """Phase 1: Connection Severance."""
        self.phase = "severance"
        self.timer = 0
        play_sound("derelicted_apply")

        # Bright vertical glow line
        self.severance_line = SeveranceGlowLine(self.center_x, self.center_y)

        # Screen shake (psychological impact)
        self.screen_shake_callback(3, 0.4)

    def _start_fragmentation(self):
        """Phase 2: Fragmentation."""
        self.phase = "fragmentation"
        self.timer = 0

        # Cracks and scattering fragments
        self.fragmentation = FragmentationCracks(self.center_x, self.center_y)

    def _start_collapse(self):
        """Phase 3: Structural Collapse."""
        self.phase = "collapse"
        self.timer = 0

        # Create falling metal beams in cross-hatch pattern
        # Vertical beams
        self.falling_beams.append(FallingMetalBeam(
            self.center_x - 15, self.center_y - 30,
            self.center_x - 15, self.center_y,
            'vertical'
        ))
        self.falling_beams.append(FallingMetalBeam(
            self.center_x + 15, self.center_y - 30,
            self.center_x + 15, self.center_y,
            'vertical'
        ))

        # Horizontal beams
        self.falling_beams.append(FallingMetalBeam(
            self.center_x, self.center_y - 25,
            self.center_x, self.center_y - 5,
            'horizontal'
        ))

        # Fragments
        for i in range(3):
            angle = random.uniform(0, 2 * math.pi)
            offset = random.uniform(18, 25)
            self.falling_beams.append(FallingMetalBeam(
                self.center_x + math.cos(angle) * 10, self.center_y - 30,
                self.center_x + math.cos(angle) * offset, self.center_y + math.sin(angle) * offset,
                'fragment'
            ))

        # Screen shake (structures falling)
        self.screen_shake_callback(4, 0.6)

    def _start_lock(self):
        """Phase 4: Immobilization Lock."""
        self.phase = "lock"
        self.timer = 0

        # Create locked structures from fallen beams
        self.locked_structures.append(MetalStructure(self.center_x - 15, self.center_y, 4, 18, 0))
        self.locked_structures.append(MetalStructure(self.center_x + 15, self.center_y, 4, 18, 0))
        self.locked_structures.append(MetalStructure(self.center_x, self.center_y - 5, 14, 3, 0))

        # Dust impacts
        for struct in self.locked_structures:
            self.dust_impacts.append(DustImpact(struct.x, struct.y + 10))

        # Binding glow
        self.binding_glow = BindingGlow(self.center_x, self.center_y)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "severance" and self.timer >= 0.5:
            self._start_fragmentation()
        elif self.phase == "fragmentation" and self.timer >= 0.5:
            self._start_collapse()
        elif self.phase == "collapse" and self.timer >= 0.8:
            self._start_lock()
        elif self.phase == "lock" and self.timer >= 0.5:
            self.active = False  # Animation complete

        # Update sub-effects
        if self.severance_line:
            self.severance_line.update(delta_time)
        if self.fragmentation:
            self.fragmentation.update(delta_time)

        for beam in self.falling_beams:
            beam.update(delta_time)

        for struct in self.locked_structures:
            struct.update(delta_time)

        for dust in self.dust_impacts:
            dust.update(delta_time)

        if self.binding_glow:
            self.binding_glow.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw in layers (back to front)

        # Phase 3-4: Dust impacts (behind everything)
        for dust in self.dust_impacts:
            dust.draw(surface)

        # Phase 3: Falling beams
        for beam in self.falling_beams:
            beam.draw(surface)

        # Phase 4: Locked structures
        for struct in self.locked_structures:
            struct.draw(surface)

        # Phase 1: Severance line (bright, on top)
        if self.severance_line:
            self.severance_line.draw(surface)

        # Phase 2: Fragmentation (on top)
        if self.fragmentation:
            self.fragmentation.draw(surface)

        # Phase 4: Binding glow (topmost)
        if self.binding_glow:
            self.binding_glow.draw(surface)


# ============================================================================
# DERELICTIONIST DEFECTION TELEPORT ANIMATION
# ============================================================================

class SeveranceDissolve:
    """
    Vertical severance line with fragmenting effect at origin.
    Right half fragments, left half fades, matching sprite's dissolution theme.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5
        self.active = True

        # Severance line
        self.line_length = 50

        # Create fragments on right side
        self.fragments = []
        num_fragments = 15
        for i in range(num_fragments):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(30, 80)
            size = random.uniform(2, 5)
            # Color from sprite: #7abae8, #9acaf8, #aadaff
            color_choice = random.choice([
                (122, 186, 232),  # #7abae8
                (154, 202, 248),  # #9acaf8
                (170, 218, 255),  # #aadaff
            ])
            self.fragments.append({
                'x': center_x + 10,  # Start on right side
                'y': center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': size,
                'color': color_choice
            })

    def update(self, delta_time):
        """Update severance dissolution."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update fragments
        for frag in self.fragments:
            frag['x'] += frag['vx'] * delta_time
            frag['y'] += frag['vy'] * delta_time
            # Slow down
            frag['vx'] *= 0.94
            frag['vy'] *= 0.94

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw severance line and fragments."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Severance line (bright ice-blue to white, from sprite)
        line_alpha = int(255 * (1.0 - progress))
        if line_alpha > 0:
            # Outer glow
            pygame.draw.line(surface, (170, 218, 255, line_alpha // 3),
                           (int(self.center_x), int(self.center_y - self.line_length / 2)),
                           (int(self.center_x), int(self.center_y + self.line_length / 2)),
                           5)
            # Middle glow
            pygame.draw.line(surface, (221, 242, 255, line_alpha // 2),
                           (int(self.center_x), int(self.center_y - self.line_length / 2)),
                           (int(self.center_x), int(self.center_y + self.line_length / 2)),
                           3)
            # Core
            pygame.draw.line(surface, (255, 255, 255, line_alpha),
                           (int(self.center_x), int(self.center_y - self.line_length / 2)),
                           (int(self.center_x), int(self.center_y + self.line_length / 2)),
                           1)

        # Fragments
        frag_alpha = int(220 * (1.0 - progress))
        if frag_alpha > 0:
            for frag in self.fragments:
                frag_surf = pygame.Surface((int(frag['size'] * 2), int(frag['size'] * 2)), pygame.SRCALPHA)
                color = frag['color'] + (frag_alpha)
                pygame.draw.circle(frag_surf, color, (int(frag['size']), int(frag['size'])), int(frag['size']))
                surface.blit(frag_surf, (int(frag['x'] - frag['size']), int(frag['y'] - frag['size'])))


class IceParticleSwirl:
    """
    Cold ice-blue particles swirling at a location.
    Used for both origin vanishing and destination materialization.
    """
    def __init__(self, center_x, center_y, mode='vanish', delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.mode = mode  # 'vanish' or 'materialize'
        self.timer = -delay
        self.duration = 0.5
        self.active = True

        # Create swirling particles
        self.particles = []
        num_particles = 12
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            self.particles.append({
                'angle': angle,
                'radius': 25 if mode == 'vanish' else 5,
                'orbit_speed': random.uniform(3, 5) * (1 if mode == 'vanish' else -1),
                'size': random.uniform(2, 4),
                'color': random.choice([
                    (90, 154, 200),   # #5a9ac8
                    (122, 186, 232),  # #7abae8
                    (170, 218, 255),  # #aadaff
                ])
            })

    def update(self, delta_time):
        """Update particle swirl."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:  # Only after delay
            for p in self.particles:
                p['angle'] += p['orbit_speed'] * delta_time
                # Spiral inward (vanish) or outward (materialize)
                if self.mode == 'vanish':
                    p['radius'] = max(0, p['radius'] - 50 * delta_time)
                else:
                    p['radius'] = min(25, p['radius'] + 50 * delta_time)

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw swirling particles."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(200 * (1.0 - abs(progress - 0.5) * 2))  # Peak at middle

        if alpha > 0:
            for p in self.particles:
                px = self.center_x + math.cos(p['angle']) * p['radius']
                py = self.center_y + math.sin(p['angle']) * p['radius']

                particle_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                color = p['color'] + (alpha)
                pygame.draw.circle(particle_surf, color, (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(particle_surf, (int(px - p['size']), int(py - p['size'])))


class FragmentReassembly:
    """
    Fragments converging from edges toward destination center.
    Reassembles DERELICTIONIST with right half fragmenting in first.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.7
        self.active = True

        # Create converging fragments
        self.fragments = []
        num_fragments = 20
        for i in range(num_fragments):
            angle = (i / num_fragments) * 2 * math.pi
            distance = random.uniform(50, 100)
            self.fragments.append({
                'start_x': center_x + math.cos(angle) * distance,
                'start_y': center_y + math.sin(angle) * distance,
                'size': random.uniform(2, 6),
                'color': random.choice([
                    (122, 186, 232),  # #7abae8
                    (154, 202, 248),  # #9acaf8
                    (170, 218, 255),  # #aadaff
                    (186, 234, 255),  # #baeaff
                ])
            })

    def update(self, delta_time):
        """Update fragment convergence."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw converging fragments."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        # Ease-in convergence
        ease_progress = 1 - math.pow(1 - progress, 3)

        alpha = int(220 * progress)  # Fade in as converging

        if alpha > 0:
            for frag in self.fragments:
                # Move from start toward center
                current_x = frag['start_x'] + (self.center_x - frag['start_x']) * ease_progress
                current_y = frag['start_y'] + (self.center_y - frag['start_y']) * ease_progress

                frag_surf = pygame.Surface((int(frag['size'] * 2), int(frag['size'] * 2)), pygame.SRCALPHA)
                color = frag['color'] + (alpha)
                pygame.draw.circle(frag_surf, color, (int(frag['size']), int(frag['size'])), int(frag['size']))
                surface.blit(frag_surf, (int(current_x - frag['size']), int(current_y - frag['size'])))


class ColdVaporBurst:
    """
    Cold mist/vapor bursting outward from center.
    Creates atmospheric cold energy effect.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True

        # Create vapor particles
        self.vapors = []
        num_vapors = 8
        for i in range(num_vapors):
            angle = (i / num_vapors) * 2 * math.pi
            speed = random.uniform(20, 40)
            self.vapors.append({
                'x': center_x,
                'y': center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(4, 8)
            })

    def update(self, delta_time):
        """Update vapor burst."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:
            for v in self.vapors:
                v['x'] += v['vx'] * delta_time
                v['y'] += v['vy'] * delta_time
                # Slow down and expand
                v['vx'] *= 0.9
                v['vy'] *= 0.9
                v['size'] += delta_time * 10

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw cold vapor."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(150 * (1.0 - progress))

        if alpha > 0:
            for v in self.vapors:
                vapor_surf = pygame.Surface((int(v['size'] * 2), int(v['size'] * 2)), pygame.SRCALPHA)
                # Pale ice-blue vapor
                pygame.draw.circle(vapor_surf, (200, 230, 255, alpha // 2), (int(v['size']), int(v['size'])), int(v['size']))
                surface.blit(vapor_surf, (int(v['x'] - v['size']), int(v['y'] - v['size'])))


class StabilizationGlow:
    """
    Final settling glow around DERELICTIONIST at destination.
    Pulsing ice-blue glow that fades to normal.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True

    def update(self, delta_time):
        """Update stabilization glow."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw stabilization glow."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Pulse and fade
        pulse = 0.7 + 0.3 * math.sin(self.timer * 15)
        alpha = int(180 * (1.0 - progress) * pulse)

        if alpha > 0:
            radius = 35
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            # Ice-blue glow (#5a9ac8)
            pygame.draw.circle(glow_surf, (90, 154, 200, alpha // 3), (radius, radius), radius)
            pygame.draw.circle(glow_surf, (122, 186, 232, alpha // 2), (radius, radius), radius - 5)
            pygame.draw.circle(glow_surf, (170, 218, 255, alpha), (radius, radius), radius - 10)
            surface.blit(glow_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class DerelictionistDefectTeleportAnimation:
    """
    DERELICTIONIST defection teleport animation for partition dissociation.

    The DERELICTIONIST dramatically teleports away when their partition shield
    triggers emergency dissociation, using cold ice-blue dissolution and
    reassembly effects matching the sprite's theme.

    Phases:
    1. Severance Fade-Out (0.5s) - Dissolves into fragments at origin
    2. Void Transit (0.5s) - Swirling particles at both locations
    3. Reformation (0.7s) - Reassembles from fragments at destination
    4. Stabilization (0.3s) - Final glow and settling
    """

    def __init__(self, derelictionist_unit, origin_pos, destination_pos, camera,
                 screen_shake_callback, particle_emitter=None):
        """
        Initialize DERELICTIONIST defection teleport animation.

        Args:
            derelictionist_unit: AnimatedUnit of DERELICTIONIST
            origin_pos: (grid_y, grid_x) - Starting position
            destination_pos: (grid_y, grid_x) - Ending position
            camera: Camera for coordinate conversion
            screen_shake_callback: Function to trigger screen shake
            particle_emitter: Optional particle emitter
        """
        # Store references
        self.derelictionist = derelictionist_unit
        self.camera = camera
        self.screen_shake_callback = screen_shake_callback
        self.particle_emitter = particle_emitter

        # Convert grid positions to screen coords
        # CRITICAL: origin_pos and destination_pos are (grid_y, grid_x)
        origin_grid_y, origin_grid_x = origin_pos
        dest_grid_y, dest_grid_x = destination_pos

        self.origin_x, self.origin_y = camera.grid_to_screen(origin_grid_x, origin_grid_y, centered=True)
        self.dest_x, self.dest_y = camera.grid_to_screen(dest_grid_x, dest_grid_y, centered=True)

        print(f"  Origin grid: ({origin_grid_x}, {origin_grid_y}) -> screen: ({self.origin_x}, {self.origin_y})")
        print(f"  Dest grid: ({dest_grid_x}, {dest_grid_y}) -> screen: ({self.dest_x}, {self.dest_y})")

        # Animation state
        self.phase = "severance"  # severance -> transit -> reformation -> stabilization
        self.timer = 0
        self.active = True

        # Hide the unit sprite during teleport (will show again during reformation)
        self.unit_hidden = True
        if not hasattr(derelictionist_unit, 'teleport_hidden'):
            derelictionist_unit.teleport_hidden = False
        derelictionist_unit.teleport_hidden = True

        # Sub-effects
        self.severance = None
        self.origin_swirl = None
        self.dest_swirl = None
        self.fragments = None
        self.vapor = None
        self.glow = None

        # Start Phase 1
        self._start_severance()

    def _start_severance(self):
        """Phase 1: Severance Fade-Out."""
        self.phase = "severance"
        self.timer = 0
        play_sound("defect_vanish")

        # Severance dissolution at origin
        self.severance = SeveranceDissolve(self.origin_x, self.origin_y)

        # Light screen shake
        self.screen_shake_callback(3, 0.4)

    def _start_transit(self):
        """Phase 2: Void Transit."""
        self.phase = "transit"
        self.timer = 0

        # Particles swirling at both locations
        self.origin_swirl = IceParticleSwirl(self.origin_x, self.origin_y, mode='vanish')
        self.dest_swirl = IceParticleSwirl(self.dest_x, self.dest_y, mode='materialize', delay=0.2)

    def _start_reformation(self):
        """Phase 3: Reformation."""
        self.phase = "reformation"
        self.timer = 0
        play_sound("defect_arrive")

        # Show the unit sprite again (it's now at destination)
        self.unit_hidden = False
        self.derelictionist.teleport_hidden = False

        # Fragments converge at destination
        self.fragments = FragmentReassembly(self.dest_x, self.dest_y)

        # Cold vapor burst
        self.vapor = ColdVaporBurst(self.dest_x, self.dest_y, delay=0.3)

        # Medium screen shake
        self.screen_shake_callback(4, 0.5)

    def _start_stabilization(self):
        """Phase 4: Stabilization."""
        self.phase = "stabilization"
        self.timer = 0

        # Final glow
        self.glow = StabilizationGlow(self.dest_x, self.dest_y)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "severance" and self.timer >= 0.5:
            self._start_transit()
        elif self.phase == "transit" and self.timer >= 0.5:
            self._start_reformation()
        elif self.phase == "reformation" and self.timer >= 0.7:
            self._start_stabilization()
        elif self.phase == "stabilization" and self.timer >= 0.3:
            self.active = False  # Animation complete
            # Ensure unit is visible when animation ends
            self.unit_hidden = False
            if hasattr(self.derelictionist, 'teleport_hidden'):
                self.derelictionist.teleport_hidden = False

        # Update sub-effects
        if self.severance:
            self.severance.update(delta_time)
        if self.origin_swirl:
            self.origin_swirl.update(delta_time)
        if self.dest_swirl:
            self.dest_swirl.update(delta_time)
        if self.fragments:
            self.fragments.update(delta_time)
        if self.vapor:
            self.vapor.update(delta_time)
        if self.glow:
            self.glow.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Debug: Print when drawing
        if not hasattr(self, '_draw_logged'):
            pass
            print(f"  Effects: severance={self.severance is not None}, origin_swirl={self.origin_swirl is not None}, dest_swirl={self.dest_swirl is not None}")
            print(f"  fragments={self.fragments is not None}, vapor={self.vapor is not None}, glow={self.glow is not None}")
            self._draw_logged = True

        # Draw in layers (back to front)

        # Phase 1: Severance at origin
        if self.severance:
            self.severance.draw(surface)

        # Phase 2: Swirls at both locations
        if self.origin_swirl:
            self.origin_swirl.draw(surface)
        if self.dest_swirl:
            self.dest_swirl.draw(surface)

        # Phase 3: Reformation at destination
        if self.fragments:
            self.fragments.draw(surface)
        if self.vapor:
            self.vapor.draw(surface)

        # Phase 4: Stabilization glow
        if self.glow:
            self.glow.draw(surface)


# ============================================================================
# VAGAL RUN ANIMATION
# ============================================================================

class LightningArc:
    """
    Initial lightning arc connecting DERELICTIONIST to ally's head.
    Jagged bolt with bright white core and ice-blue glow.
    """
    def __init__(self, start_x, start_y, end_x, end_y):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.timer = 0
        self.duration = 0.4
        self.active = True

        # Generate jagged path points
        self.path_points = self._generate_jagged_path()

    def _generate_jagged_path(self):
        """Generate jagged lightning path from start to end."""
        points = [(self.start_x, self.start_y)]

        # Create 4-6 segments with random jitter
        num_segments = random.randint(4, 6)
        for i in range(1, num_segments):
            t = i / num_segments
            # Linear interpolation
            x = self.start_x + (self.end_x - self.start_x) * t
            y = self.start_y + (self.end_y - self.start_y) * t

            # Add perpendicular jitter
            dx = self.end_x - self.start_x
            dy = self.end_y - self.start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                # Perpendicular vector
                perp_x = -dy / length
                perp_y = dx / length
                # Random jitter
                jitter = random.uniform(-8, 8)
                x += perp_x * jitter
                y += perp_y * jitter

            points.append((x, y))

        points.append((self.end_x, self.end_y))
        return points

    def update(self, delta_time):
        """Update lightning arc."""
        if not self.active:
            return False

        self.timer += delta_time

        # Regenerate path occasionally for flickering effect
        if random.random() < 0.3:
            self.path_points = self._generate_jagged_path()

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw jagged lightning arc."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Flicker alpha
        base_alpha = int(220 * (1.0 - progress * 0.5))
        flicker = 0.8 + 0.2 * random.random()
        alpha = int(base_alpha * flicker)

        if alpha > 0 and len(self.path_points) > 1:
            # Draw outer glow (ice-blue)
            for i in range(len(self.path_points) - 1):
                pygame.draw.line(surface, (122, 186, 232, alpha // 3),
                               (int(self.path_points[i][0]), int(self.path_points[i][1])),
                               (int(self.path_points[i+1][0]), int(self.path_points[i+1][1])),
                               4)

            # Draw middle layer (bright ice-blue)
            for i in range(len(self.path_points) - 1):
                pygame.draw.line(surface, (170, 218, 255, alpha // 2),
                               (int(self.path_points[i][0]), int(self.path_points[i][1])),
                               (int(self.path_points[i+1][0]), int(self.path_points[i+1][1])),
                               2)

            # Draw core (white)
            for i in range(len(self.path_points) - 1):
                pygame.draw.line(surface, (255, 255, 255, alpha),
                               (int(self.path_points[i][0]), int(self.path_points[i][1])),
                               (int(self.path_points[i+1][0]), int(self.path_points[i+1][1])),
                               1)


class VagusNervePath:
    """
    Glowing vertical pathway representing the vagus nerve running down the ally's body.
    Starts at head, goes through neck, chest, to abdomen.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.3  # Visible during phases 2-3
        self.active = True

        # Nerve path dimensions
        self.path_top = center_y - 20  # Head
        self.path_bottom = center_y + 20  # Abdomen

        # Current activation position (lightning progress)
        self.activation_y = self.path_top

    def update(self, delta_time):
        """Update nerve pathway glow."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def set_activation_position(self, y_pos):
        """Set where the lightning has reached on the nerve path."""
        self.activation_y = y_pos

    def draw(self, surface):
        """Draw glowing nerve pathway."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Base glow alpha
        base_alpha = int(180 * min(1.0, self.timer / 0.3))  # Fade in
        if progress > 0.7:
            base_alpha = int(180 * (1.0 - (progress - 0.7) / 0.3))  # Fade out

        # Pulse effect
        pulse = 0.6 + 0.4 * math.sin(self.timer * 8)
        alpha = int(base_alpha * pulse)

        if alpha > 0:
            # Draw vertical nerve path (multiple layers for glow)
            # Outer glow
            pygame.draw.line(surface, (90, 154, 200, alpha // 4),
                           (int(self.center_x), int(self.path_top)),
                           (int(self.center_x), int(self.path_bottom)),
                           6)

            # Middle glow
            pygame.draw.line(surface, (122, 186, 232, alpha // 2),
                           (int(self.center_x), int(self.path_top)),
                           (int(self.center_x), int(self.path_bottom)),
                           3)

            # Core line
            pygame.draw.line(surface, (170, 218, 255, alpha),
                           (int(self.center_x), int(self.path_top)),
                           (int(self.center_x), int(self.path_bottom)),
                           1)

            # Bright spot where lightning is currently at
            if self.activation_y >= self.path_top and self.activation_y <= self.path_bottom:
                bright_alpha = int(255 * pulse)
                pygame.draw.circle(surface, (255, 255, 255, bright_alpha),
                                 (int(self.center_x), int(self.activation_y)), 4)
                pygame.draw.circle(surface, (221, 242, 255, bright_alpha // 2),
                                 (int(self.center_x), int(self.activation_y)), 6)


class CascadingLightning:
    """
    Forking lightning bolts cascading downward through the vagus nerve.
    Multiple bolts with branching, traveling from head to abdomen.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.8
        self.active = True

        # Cascade path
        self.path_top = center_y - 20  # Head
        self.path_bottom = center_y + 20  # Abdomen
        self.current_y = self.path_top

        # Lightning segments (jagged vertical path)
        self.segments = []
        self._generate_segments()

    def _generate_segments(self):
        """Generate jagged vertical lightning segments."""
        self.segments = []
        num_segments = 8
        for i in range(num_segments + 1):
            t = i / num_segments
            y = self.path_top + (self.path_bottom - self.path_top) * t
            # Horizontal jitter
            x = self.center_x + random.uniform(-4, 4)
            self.segments.append((x, y))

    def update(self, delta_time):
        """Update cascading lightning."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:
            # Progress downward
            progress = min(1.0, self.timer / self.duration)
            self.current_y = self.path_top + (self.path_bottom - self.path_top) * progress

            # Occasionally regenerate for flicker
            if random.random() < 0.2:
                self._generate_segments()

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw cascading lightning bolt."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Determine visible portion of lightning
        visible_segments = int(len(self.segments) * progress)

        # Flicker alpha
        base_alpha = 220
        flicker = 0.7 + 0.3 * random.random()
        alpha = int(base_alpha * flicker)

        if alpha > 0 and visible_segments > 1:
            # Draw lightning segments
            for i in range(visible_segments - 1):
                # Outer glow
                pygame.draw.line(surface, (122, 186, 232, alpha // 3),
                               (int(self.segments[i][0]), int(self.segments[i][1])),
                               (int(self.segments[i+1][0]), int(self.segments[i+1][1])),
                               3)
                # Core
                pygame.draw.line(surface, (255, 255, 255, alpha),
                               (int(self.segments[i][0]), int(self.segments[i][1])),
                               (int(self.segments[i+1][0]), int(self.segments[i+1][1])),
                               1)


class LightningBranches:
    """
    Small branching lightning arcs spreading horizontally from the main nerve path.
    Creates forking effect as lightning cascades down.
    """
    def __init__(self, center_x, center_y, spawn_time=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.spawn_time = spawn_time
        self.duration = 0.3
        self.active = False  # Becomes active when spawn_time reached

        # Random branch direction and length
        self.angle = random.choice([-1, 1]) * random.uniform(0.3, 0.8) * math.pi
        self.length = random.uniform(10, 20)

        # Branch points
        self.branch_points = []
        self._generate_branch()

    def _generate_branch(self):
        """Generate jagged branch."""
        self.branch_points = [(self.center_x, self.center_y)]
        num_segments = 3
        for i in range(1, num_segments + 1):
            t = i / num_segments
            distance = self.length * t
            x = self.center_x + math.cos(self.angle) * distance
            y = self.center_y + math.sin(self.angle) * distance
            # Jitter
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)
            self.branch_points.append((x, y))

    def update(self, delta_time, global_time):
        """Update branch (activates at spawn_time)."""
        if global_time < self.spawn_time:
            return True  # Not spawned yet

        if not self.active:
            self.active = True

        self.timer += delta_time

        if self.timer >= self.duration:
            return False

        return True

    def draw(self, surface, global_time):
        """Draw lightning branch."""
        if not self.active or global_time < self.spawn_time:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(200 * (1.0 - progress))

        if alpha > 0 and len(self.branch_points) > 1:
            # Draw branch
            for i in range(len(self.branch_points) - 1):
                pygame.draw.line(surface, (170, 218, 255, alpha // 2),
                               (int(self.branch_points[i][0]), int(self.branch_points[i][1])),
                               (int(self.branch_points[i+1][0]), int(self.branch_points[i+1][1])),
                               2)
                pygame.draw.line(surface, (255, 255, 255, alpha),
                               (int(self.branch_points[i][0]), int(self.branch_points[i][1])),
                               (int(self.branch_points[i+1][0]), int(self.branch_points[i+1][1])),
                               1)


class FractureExplosion:
    """
    Explosive burst of ice-blue lightning and particles when lightning reaches bottom.
    Represents status effects shattering and trauma dispersing.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.6
        self.active = True

        # Radial lightning branches
        self.radial_branches = []
        num_branches = 12
        for i in range(num_branches):
            angle = (i / num_branches) * 2 * math.pi
            length = random.uniform(20, 35)
            self.radial_branches.append({
                'angle': angle,
                'length': length,
                'segments': self._generate_radial_segments(angle, length)
            })

        # Shatter particles
        self.particles = []
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            self.particles.append({
                'x': center_x,
                'y': center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(2, 5),
                'color': random.choice([
                    (122, 186, 232),
                    (154, 202, 248),
                    (170, 218, 255),
                ])
            })

    def _generate_radial_segments(self, angle, length):
        """Generate jagged radial lightning branch."""
        segments = [(self.center_x, self.center_y)]
        num_segments = 4
        for i in range(1, num_segments + 1):
            t = i / num_segments
            distance = length * t
            x = self.center_x + math.cos(angle) * distance
            y = self.center_y + math.sin(angle) * distance
            # Jitter perpendicular to angle
            jitter = random.uniform(-3, 3)
            x += math.cos(angle + math.pi / 2) * jitter
            y += math.sin(angle + math.pi / 2) * jitter
            segments.append((x, y))
        return segments

    def update(self, delta_time):
        """Update explosion."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particles
        for p in self.particles:
            p['x'] += p['vx'] * delta_time
            p['y'] += p['vy'] * delta_time
            p['vx'] *= 0.93
            p['vy'] *= 0.93

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw fracture explosion."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Radial lightning branches (fade quickly)
        if progress < 0.4:
            branch_alpha = int(255 * (1.0 - progress / 0.4))
            for branch in self.radial_branches:
                if branch_alpha > 0 and len(branch['segments']) > 1:
                    for i in range(len(branch['segments']) - 1):
                        # Glow
                        pygame.draw.line(surface, (122, 186, 232, branch_alpha // 3),
                                       (int(branch['segments'][i][0]), int(branch['segments'][i][1])),
                                       (int(branch['segments'][i+1][0]), int(branch['segments'][i+1][1])),
                                       3)
                        # Core
                        pygame.draw.line(surface, (255, 255, 255, branch_alpha),
                                       (int(branch['segments'][i][0]), int(branch['segments'][i][1])),
                                       (int(branch['segments'][i+1][0]), int(branch['segments'][i+1][1])),
                                       1)

        # Shatter particles
        particle_alpha = int(220 * (1.0 - progress))
        if particle_alpha > 0:
            for p in self.particles:
                particle_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                color = p['color'] + (particle_alpha)
                pygame.draw.circle(particle_surf, color, (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(particle_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))


class ElectricalAfterimage:
    """
    Flickering residual electrical energy after the main lightning cascade.
    Small arcs and glowing particles settling down.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5
        self.active = True

        # Small flickering arcs
        self.flicker_arcs = []
        for _ in range(5):
            y_offset = random.uniform(-15, 15)
            self.flicker_arcs.append({
                'y': center_y + y_offset,
                'phase': random.uniform(0, 2 * math.pi)
            })

        # Settling particles
        self.particles = []
        for _ in range(8):
            x_offset = random.uniform(-10, 10)
            y_offset = random.uniform(-15, 15)
            self.particles.append({
                'x': center_x + x_offset,
                'y': center_y + y_offset,
                'vy': random.uniform(5, 15),  # Falling slowly
                'size': random.uniform(1.5, 3)
            })

    def update(self, delta_time):
        """Update afterimage."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update settling particles
        for p in self.particles:
            p['y'] += p['vy'] * delta_time
            p['vy'] *= 0.95  # Slow down

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw electrical afterimage."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(180 * (1.0 - progress))

        if alpha > 0:
            # Flickering arcs (horizontal small lines)
            for arc in self.flicker_arcs:
                if random.random() < 0.4:  # Flicker on/off
                    arc_length = 8
                    pygame.draw.line(surface, (170, 218, 255, alpha),
                                   (int(self.center_x - arc_length), int(arc['y'])),
                                   (int(self.center_x + arc_length), int(arc['y'])),
                                   1)

            # Settling particles
            for p in self.particles:
                particle_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (122, 186, 232, alpha),
                                 (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(particle_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))


class VagalRunAnimation:
    """
    Vagal Run skill animation for DERELICTIONIST.
    Ice-blue lightning cascades down the vagus nerve from head to abdomen,
    fracturing trauma and clearing status effects with therapeutic intensity.

    Phases:
    1. Connection Strike (0.4s) - Lightning arc connects caster to ally's head
    2. Vagal Cascade (0.8s) - Lightning runs down vagus nerve (head→chest→abdomen)
    3. Trauma Fracture Burst (0.6s) - Explosive burst, status effects shatter
    4. Nerve Afterglow (0.5s) - Residual electrical energy fades
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Vagal Run animation.

        Args:
            caster_unit: DERELICTIONIST casting Vagal Run
            target_unit: Ally receiving therapy
            target_pos: (grid_y, grid_x) - Position of ally
            camera: Camera for coordinate conversion
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Convert positions to screen coords
        # Caster position (may be None if caster died before abreaction)
        if caster_unit:
            self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x, caster_unit.grid_y, centered=True)
        else:
            # No caster (died before abreaction) - use target position for connection
            self.caster_x, self.caster_y = None, None

        # Target position (CRITICAL: target_pos is (grid_y, grid_x), grid_to_screen takes (grid_x, grid_y))
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "connection"  # connection -> cascade -> burst -> afterglow
        self.timer = 0
        self.active = True

        # Sub-effects
        self.connection_arc = None
        self.nerve_path = None
        self.cascading_bolts = []
        self.branches = []
        self.explosion = None
        self.afterimage = None

        # Start Phase 1
        self._start_connection()

    def _start_connection(self):
        """Phase 1: Connection Strike."""
        self.phase = "connection"
        self.timer = 0
        play_sound("vagal_run_cast")

        # Lightning arc from caster to target's head (skip if no caster)
        if self.caster_x is not None and self.caster_y is not None:
            self.connection_arc = LightningArc(self.caster_x, self.caster_y,
                                              self.target_x, self.target_y - 20)
        else:
            # No caster (abreaction with dead caster) - skip connection phase
            # Go straight to cascade after minimal delay
            self.connection_arc = None

        # Light screen shake
        self.screen_shake_callback(3, 0.4)

    def _start_cascade(self):
        """Phase 2: Vagal Cascade - Lightning runs down nerve."""
        self.phase = "cascade"
        self.timer = 0

        # Create nerve path
        self.nerve_path = VagusNervePath(self.target_x, self.target_y)

        # Create multiple cascading lightning bolts with stagger
        for i in range(3):
            self.cascading_bolts.append(
                CascadingLightning(self.target_x, self.target_y, delay=i * 0.15)
            )

        # Create branching arcs that spawn during cascade
        for i in range(8):
            spawn_time = random.uniform(0.1, 0.7)
            y_pos = self.target_y - 20 + random.uniform(0, 40)
            self.branches.append(
                LightningBranches(self.target_x, y_pos, spawn_time=spawn_time)
            )

        # Medium screen shake
        self.screen_shake_callback(5, 0.8)

    def _start_burst(self):
        """Phase 3: Trauma Fracture Burst."""
        self.phase = "burst"
        self.timer = 0
        play_sound("vagal_run_burst")

        # Explosive fracture at bottom of nerve path
        self.explosion = FractureExplosion(self.target_x, self.target_y + 20)

        # Heavy screen shake
        self.screen_shake_callback(6, 0.6)

    def _start_afterglow(self):
        """Phase 4: Nerve Afterglow."""
        self.phase = "afterglow"
        self.timer = 0

        # Residual electrical energy
        self.afterimage = ElectricalAfterimage(self.target_x, self.target_y)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        # If no caster, skip connection phase faster (0.1s instead of 0.4s)
        connection_duration = 0.1 if self.caster_x is None else 0.4
        if self.phase == "connection" and self.timer >= connection_duration:
            self._start_cascade()
        elif self.phase == "cascade" and self.timer >= 0.8:
            self._start_burst()
        elif self.phase == "burst" and self.timer >= 0.6:
            self._start_afterglow()
        elif self.phase == "afterglow" and self.timer >= 0.5:
            self.active = False  # Animation complete

        # Update sub-effects
        if self.connection_arc:
            self.connection_arc.update(delta_time)

        if self.nerve_path:
            self.nerve_path.update(delta_time)
            # Update nerve activation position based on cascade progress
            if self.phase == "cascade":
                cascade_progress = min(1.0, self.timer / 0.8)
                activation_y = self.target_y - 20 + 40 * cascade_progress
                self.nerve_path.set_activation_position(activation_y)

        # Update cascading bolts
        for bolt in self.cascading_bolts:
            bolt.update(delta_time)

        # Update branches (pass global timer for spawn timing)
        cascade_time = self.timer if self.phase == "cascade" else 0.8
        self.branches = [b for b in self.branches if b.update(delta_time, cascade_time)]

        if self.explosion:
            self.explosion.update(delta_time)

        if self.afterimage:
            self.afterimage.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw in layers (back to front)

        # Phase 1: Connection arc
        if self.connection_arc:
            self.connection_arc.draw(surface)

        # Phase 2: Nerve path (behind lightning)
        if self.nerve_path:
            self.nerve_path.draw(surface)

        # Phase 2: Cascading lightning bolts
        for bolt in self.cascading_bolts:
            bolt.draw(surface)

        # Phase 2: Lightning branches
        cascade_time = self.timer if self.phase == "cascade" else 0.8
        for branch in self.branches:
            branch.draw(surface, cascade_time)

        # Phase 3: Explosion
        if self.explosion:
            self.explosion.draw(surface)

        # Phase 4: Afterimage
        if self.afterimage:
            self.afterimage.draw(surface)


class VagalRunAbreactionAnimation:
    """
    Vagal Run abreaction animation (delayed effect after 3 turns).
    Same as VagalRunAnimation but WITHOUT the initial connection arc from caster.
    Lightning appears directly on the target and cascades down the vagus nerve.

    Used when abreaction triggers, especially when the DERELICTIONIST may be dead.

    Phases:
    1. Vagal Cascade (0.8s) - Lightning runs down vagus nerve (head→chest→abdomen)
    2. Trauma Fracture Burst (0.6s) - Explosive burst, status effects shatter
    3. Nerve Afterglow (0.5s) - Residual electrical energy fades

    Total duration: ~1.9s (vs 2.3s for full animation)
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Vagal Run abreaction animation.

        Args:
            caster_unit: DERELICTIONIST who cast Vagal Run (may be None/dead)
            target_unit: Unit experiencing abreaction
            target_pos: (grid_y, grid_x) - Position of target
            camera: Camera for coordinate conversion
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit  # May be None
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Convert target position to screen coords
        # CRITICAL: target_pos is (grid_y, grid_x), grid_to_screen takes (grid_x, grid_y)
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state (starts directly at cascade - NO connection phase)
        self.phase = "cascade"  # cascade -> burst -> afterglow
        self.timer = 0
        self.active = True

        # Sub-effects
        self.nerve_path = None
        self.cascading_bolts = []
        self.branches = []
        self.explosion = None
        self.afterimage = None

        # Start directly with cascade phase
        self._start_cascade()

    def _start_cascade(self):
        """Phase 1: Vagal Cascade - Lightning runs down nerve."""
        self.phase = "cascade"
        self.timer = 0
        play_sound("vagal_run_cast")

        # Create nerve path
        self.nerve_path = VagusNervePath(self.target_x, self.target_y)

        # Create multiple cascading lightning bolts with stagger
        for i in range(3):
            self.cascading_bolts.append(
                CascadingLightning(self.target_x, self.target_y, delay=i * 0.15)
            )

        # Create branching arcs that spawn during cascade
        for i in range(8):
            spawn_time = random.uniform(0.1, 0.7)
            y_pos = self.target_y - 20 + random.uniform(0, 40)
            self.branches.append(
                LightningBranches(self.target_x, y_pos, spawn_time=spawn_time)
            )

        # Medium screen shake
        self.screen_shake_callback(5, 0.8)

    def _start_burst(self):
        """Phase 2: Trauma Fracture Burst."""
        self.phase = "burst"
        self.timer = 0
        play_sound("vagal_run_burst")

        # Explosive fracture at bottom of nerve path
        self.explosion = FractureExplosion(self.target_x, self.target_y + 20)

        # Heavy screen shake
        self.screen_shake_callback(6, 0.6)

    def _start_afterglow(self):
        """Phase 3: Nerve Afterglow."""
        self.phase = "afterglow"
        self.timer = 0

        # Residual electrical energy
        self.afterimage = ElectricalAfterimage(self.target_x, self.target_y)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions (no connection phase - starts at cascade)
        if self.phase == "cascade" and self.timer >= 0.8:
            self._start_burst()
        elif self.phase == "burst" and self.timer >= 0.6:
            self._start_afterglow()
        elif self.phase == "afterglow" and self.timer >= 0.5:
            self.active = False  # Animation complete

        # Update sub-effects
        if self.nerve_path:
            self.nerve_path.update(delta_time)
            # Update nerve activation position based on cascade progress
            if self.phase == "cascade":
                cascade_progress = min(1.0, self.timer / 0.8)
                activation_y = self.target_y - 20 + 40 * cascade_progress
                self.nerve_path.set_activation_position(activation_y)

        # Update cascading bolts
        for bolt in self.cascading_bolts:
            bolt.update(delta_time)

        # Update branches (pass global timer for spawn timing)
        cascade_time = self.timer if self.phase == "cascade" else 0.8
        self.branches = [b for b in self.branches if b.update(delta_time, cascade_time)]

        if self.explosion:
            self.explosion.update(delta_time)

        if self.afterimage:
            self.afterimage.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw in layers (back to front)

        # Phase 1: Nerve path (behind lightning)
        if self.nerve_path:
            self.nerve_path.draw(surface)

        # Phase 1: Cascading lightning bolts
        for bolt in self.cascading_bolts:
            bolt.draw(surface)

        # Phase 1: Lightning branches
        cascade_time = self.timer if self.phase == "cascade" else 0.8
        for branch in self.branches:
            branch.draw(surface, cascade_time)

        # Phase 2: Explosion
        if self.explosion:
            self.explosion.draw(surface)

        # Phase 3: Afterimage
        if self.afterimage:
            self.afterimage.draw(surface)


# ============================================================================
# DERELICT ANIMATION
# ============================================================================



# ============================================================================
# DERELICTIONIST BASIC ATTACK - VOID GRASP
# ============================================================================

class DerelictionistVoidAttack:
    """
    DERELICTIONIST basic attack animation - void tears open at target.
    A dark void aperture cracks open at the target's location, framed by
    cold blue edge glow, then snaps shut on impact.
    """

    def __init__(self, attacker_unit, target_unit, particle_emitter, screen_shake_callback):
        """
        Args:
            attacker_unit: AnimatedUnit doing the attacking
            target_unit: AnimatedUnit being attacked
            particle_emitter: ParticleEmitter for effects
            screen_shake_callback: Function(intensity, duration)
        """
        self.attacker = attacker_unit
        self.target = target_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback

        # Calculate attack vector (used for attacker lean particles)
        self.dx = target_unit.x - attacker_unit.x
        self.dy = target_unit.y - attacker_unit.y
        distance = math.sqrt(self.dx * self.dx + self.dy * self.dy)
        if distance > 0:
            self.dx /= distance
            self.dy /= distance
        self.distance = distance

        # Animation state
        self.phase = "void_form"  # void_form → reach → dissolve → done
        self.timer = 0
        self.active = True

        # Phase durations (unchanged — tied to sound events)
        self.void_form_duration = 0.15
        self.reach_duration = 0.25
        self.dissolve_duration = 0.2

        self.reach_progress = 0.0

        # Color palette from derelictionist.svg and derelicted.svg
        self.color_void       = (10, 10, 20)        # near-black cold void core
        self.color_edge_dark  = (74, 122, 154)      # #4a7a9a — dark suit blue
        self.color_edge_mid   = (90, 154, 200)      # #5a9ac8 — bright suit blue
        self.color_edge_light = (170, 218, 255)     # #aadaff — severance glow
        self.color_ice        = (221, 242, 255)     # #ddf2ff — near-white cold

        # Void aperture state (drawn at target)
        self.void_radius_x = 0.0   # horizontal half-width (wider — ellipse)
        self.void_radius_y = 0.0   # vertical half-height (narrower)
        self.void_angle = 0.0      # slight tilt per-instance
        self.void_pulse = 0.0      # oscillation offset

        # Random tilt so the void doesn't always look the same
        self.void_angle = random.uniform(-0.3, 0.3)

    def _trigger_void_form(self):
        """Phase 1: Void crack appears at target — attacker surges forward."""
        play_sound("void_attack")
        from .core import Particle
        # Small burst of dark-edge fragments radiating from target as void cracks open
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 90)
            color = random.choice([self.color_edge_dark, self.color_edge_mid, self.color_edge_light])
            p = Particle(self.target.x, self.target.y,
                         math.cos(angle) * speed, math.sin(angle) * speed,
                         color, size=random.uniform(1.5, 3), lifetime=0.18)
            p.gravity = 0
            self.particle_emitter.particles.append(p)

    def _trigger_reach(self):
        """Phase 2: Void fully open — cold light bleeds from the edges."""
        from .core import Particle
        # Slow-drifting cold fragments leaking out of the void edge
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 55)
            color = random.choice([self.color_edge_mid, self.color_edge_light, self.color_ice])
            p = Particle(self.target.x + random.uniform(-8, 8),
                         self.target.y + random.uniform(-8, 8),
                         math.cos(angle) * speed, math.sin(angle) * speed,
                         color, size=random.uniform(1.5, 3.5), lifetime=0.28)
            p.gravity = 0
            self.particle_emitter.particles.append(p)

    def _trigger_dissolve(self):
        """Phase 3: Void snaps shut — cold shockwave fragments."""
        play_sound("void_impact")
        from .core import Particle
        # Outward burst of cold blue as the void collapses
        for _ in range(22):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(70, 160)
            color = random.choice([self.color_edge_dark, self.color_edge_mid,
                                   self.color_edge_light, self.color_ice])
            p = Particle(self.target.x, self.target.y,
                         math.cos(angle) * speed, math.sin(angle) * speed,
                         color, size=random.uniform(2, 5), lifetime=random.uniform(0.18, 0.32))
            p.gravity = 60
            self.particle_emitter.particles.append(p)

        self.target.shake_intensity = 10
        self.screen_shake(5, 0.18)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time
        self.void_pulse += delta_time * 18  # fast shimmer

        if self.phase == "void_form":
            if not hasattr(self, "_void_triggered"):
                self._trigger_void_form()
                self._void_triggered = True

            # Void cracks open — rapidly expand
            progress = self.timer / self.void_form_duration
            self.void_radius_x = progress * 22
            self.void_radius_y = progress * 13

            if self.timer >= self.void_form_duration:
                self.phase = "reach"
                self.timer = 0
                self._trigger_reach()

        elif self.phase == "reach":
            self.reach_progress = min(1.0, self.timer / self.reach_duration)

            # Void held open, slight pulse
            pulse = 1.0 + 0.06 * math.sin(self.void_pulse)
            self.void_radius_x = 22 * pulse
            self.void_radius_y = 13 * pulse

            if self.timer >= self.reach_duration:
                self.phase = "dissolve"
                self.timer = 0
                self._trigger_dissolve()

        elif self.phase == "dissolve":
            # Void snaps shut
            progress = self.timer / self.dissolve_duration
            ease = 1.0 - (progress * progress)  # fast snap
            self.void_radius_x = 22 * ease
            self.void_radius_y = 13 * ease

            if self.timer >= self.dissolve_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw void aperture at target location."""
        if self.phase == "done":
            return

        rx = int(self.void_radius_x)
        ry = int(self.void_radius_y)
        if rx < 2 or ry < 2:
            return

        tx = int(self.target.x)
        ty = int(self.target.y)

        # --- Outer glow layers (largest to smallest, cold blue) ---
        glow_data = [
            (rx + 10, ry + 6, self.color_edge_dark,  55),
            (rx + 6,  ry + 4, self.color_edge_mid,   90),
            (rx + 3,  ry + 2, self.color_edge_light, 140),
        ]
        for grx, gry, color, alpha in glow_data:
            gw = (grx + 2) * 2
            gh = (gry + 2) * 2
            glow_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
            # Pulse alpha slightly during reach phase
            if self.phase == "reach":
                alpha = int(alpha * (1.0 + 0.15 * math.sin(self.void_pulse)))
            pygame.draw.ellipse(glow_surf, (*color, alpha), (2, 2, grx * 2, gry * 2))
            surface.blit(glow_surf, (tx - grx - 2, ty - gry - 2))

        # --- Void core — near-black ellipse ---
        core_w = rx * 2
        core_h = ry * 2
        core_surf = pygame.Surface((core_w + 2, core_h + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(core_surf, (*self.color_void, 245), (1, 1, core_w, core_h))
        surface.blit(core_surf, (tx - rx - 1, ty - ry - 1))

        # --- Sharp cold-white rim right on the edge ---
        rim_alpha = 200
        if self.phase == "dissolve":
            progress = self.timer / self.dissolve_duration
            rim_alpha = int(200 * (1.0 - progress))
        if rim_alpha > 10:
            rim_surf = pygame.Surface((rx * 2 + 4, ry * 2 + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(rim_surf, (*self.color_edge_light, rim_alpha),
                                (2, 2, rx * 2, ry * 2), 2)
            surface.blit(rim_surf, (tx - rx - 2, ty - ry - 2))

        # --- Flash on snap shut ---
        if self.phase == "dissolve":
            progress = self.timer / self.dissolve_duration
            if progress < 0.35:
                flash_alpha = int(180 * (1.0 - progress / 0.35))
                flash_r = int((rx + 8) * (1.0 + progress * 0.4))
                flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_ice, flash_alpha),
                                   (flash_r, flash_r), flash_r)
                surface.blit(flash_surf, (tx - flash_r, ty - flash_r))


# ============================================================================
# DERELICT SKILL ANIMATIONS (Base Derelict)
# ============================================================================

class DerelictPushTrail:
    """
    Push trail animation for base Derelict skill.
    Shows blue particles trailing behind the ally as they get pushed away.
    """

    def __init__(self, start_pos, end_pos, camera):
        """
        Initialize push trail animation.

        Args:
            start_pos: (grid_y, grid_x) starting position
            end_pos: (grid_y, grid_x) ending position
            camera: Camera for coordinate conversion
        """
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.camera = camera

        # Animation state
        self.timer = 0
        self.active = True
        self.duration = 0.5  # Trail fades in 0.5s

        # DERELICTIONIST signature blue glow colors
        self.color_trail_bright = (122, 186, 232)  # #7abae8 - bright blue
        self.color_trail_dim = (90, 154, 200)      # #5a9ac8 - dimmer blue

        play_sound("derelict_push")

        # Generate trail particles along the push path
        self.trail_particles = []

        # Calculate path from start to end
        start_y, start_x = start_pos
        end_y, end_x = end_pos

        # Get screen positions
        start_screen_x, start_screen_y = camera.grid_to_screen(start_x, start_y, centered=True)
        end_screen_x, end_screen_y = camera.grid_to_screen(end_x, end_y, centered=True)

        # Create particles along the line
        num_particles = max(8, int(abs(end_screen_x - start_screen_x) + abs(end_screen_y - start_screen_y)) // 8)

        for i in range(num_particles):
            t = i / max(1, num_particles - 1)  # Progress along path (0 to 1)

            # Interpolate position
            px = start_screen_x + (end_screen_x - start_screen_x) * t
            py = start_screen_y + (end_screen_y - start_screen_y) * t

            # Add some randomness
            px += random.uniform(-3, 3)
            py += random.uniform(-3, 3)

            self.trail_particles.append({
                'x': px,
                'y': py,
                'size': random.uniform(2, 4),
                'color': random.choice([self.color_trail_bright, self.color_trail_dim]),
                'spawn_delay': t * 0.15,  # Stagger particle appearance
                'lifetime': 1.0,
                'max_lifetime': 1.0
            })

    def update(self, delta_time):
        """Update trail particles."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particles
        for particle in self.trail_particles[:]:
            # Check spawn delay
            if self.timer < particle['spawn_delay']:
                continue

            # Fade out
            particle['lifetime'] -= delta_time

            if particle['lifetime'] <= 0:
                self.trail_particles.remove(particle)

        # Animation complete when all particles are gone
        if not self.trail_particles or self.timer > self.duration + 0.5:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw trail particles."""
        if not self.active:
            return

        import pygame

        for particle in self.trail_particles:
            # Skip if not yet spawned
            if self.timer < particle['spawn_delay']:
                continue

            # Calculate fade alpha
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            if alpha > 0:
                size = int(particle['size'])
                if size > 0:
                    # Draw particle with glow
                    trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (*particle['color'], alpha), (size, size), size)
                    surface.blit(trail_surf, (int(particle['x']) - size, int(particle['y']) - size))


# ============================================================================
# DERELICT BUILDING ANIMATIONS (Upgraded Derelict)
# ============================================================================

class DerelictBuildingFormation:
    """
    Dust cloud animation when derelict building walls form.
    Simple particle effect showing dust puffing up from where walls appear.
    """

    def __init__(self, building_tiles, camera, game):
        """
        Initialize dust cloud formation animation.

        Args:
            building_tiles: List of (grid_y, grid_x) tuples for building positions
            camera: Camera for coordinate conversion
            game: Game instance
        """
        self.building_tiles = building_tiles
        self.camera = camera
        self.game = game

        # Animation state
        self.timer = 0
        self.active = True
        self.duration = 0.5  # Dust settles in 0.5s

        # Dust colors - gray/blue dust particles
        self.color_dust_light = (138, 154, 170)     # Light gray-blue dust
        self.color_dust_dark = (106, 122, 138)      # Darker gray-blue dust

        # Convert to screen coordinates
        self.screen_tiles = []
        for grid_y, grid_x in building_tiles:
            screen_x, screen_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
            self.screen_tiles.append((screen_x, screen_y, grid_x, grid_y))

        # Spawn dust particles at each tile location
        self.dust_particles = []
        for sx, sy, gx, gy in self.screen_tiles:
            # Create 8-12 dust particles per tile
            num_particles = random.randint(8, 12)
            for _ in range(num_particles):
                self.dust_particles.append({
                    'x': sx + random.uniform(-20, 20),
                    'y': sy + random.uniform(-15, 15),
                    'vx': random.uniform(-40, 40),
                    'vy': random.uniform(-60, -20),  # Puff upward
                    'size': random.uniform(2, 5),
                    'color': random.choice([self.color_dust_light, self.color_dust_dark]),
                    'lifetime': 1.0,
                    'max_lifetime': 1.0
                })

    def update(self, delta_time):
        """Update dust cloud animation. Returns True if still active."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update dust particles
        for particle in self.dust_particles[:]:
            # Move particle
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time

            # Slow down over time (friction)
            particle['vx'] *= 0.96
            particle['vy'] *= 0.96

            # Gravity (slight downward drift after initial puff)
            particle['vy'] += 30 * delta_time

            # Fade out
            particle['lifetime'] -= delta_time

            if particle['lifetime'] <= 0:
                self.dust_particles.remove(particle)

        # Animation complete when all particles are gone
        if not self.dust_particles:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw dust cloud."""
        if not self.active:
            return

        import pygame

        # Draw dust particles
        for particle in self.dust_particles:
            # Calculate fade alpha based on lifetime
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            if alpha > 0:
                size = int(particle['size'])
                if size > 0:
                    dust_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dust_surf, (*particle['color'], alpha), (size, size), size)
                    surface.blit(dust_surf, (int(particle['x']) - size, int(particle['y']) - size))


class DerelictBuildingTiles:
    """
    Persistent background effect for derelict building tiles.
    Shows subtle weathering, cracks, and age on the building walls.
    """

    def __init__(self, building_tiles, camera, game):
        """
        Initialize persistent building tiles.

        Args:
            building_tiles: List of (grid_y, grid_x) tuples for building positions
            camera: Camera for coordinate conversion
            game: Game instance to check building duration
        """
        self.building_tiles = building_tiles
        self.camera = camera
        self.game = game

        # Animation state
        self.active = True
        self.timer = 0

        # Building colors - matching Derelict skill icon (steel with blue glow)
        self.color_base_wall = (90, 106, 122)       # #5a6a7a - steel gray-blue base
        self.color_dark_decay = (74, 90, 106)       # #4a5a6a - darker steel decay
        self.color_light_patch = (106, 122, 138)    # #6a7a8a - lighter steel patches
        self.color_blue_glow = (122, 186, 232)      # #7abae8 - DERELICTIONIST blue glow
        self.color_blue_dark = (74, 122, 154)       # #4a7a9a - darker blue glow
        self.color_rust_stain = (139, 106, 74)      # #8b6a4a - rust stains
        self.color_exposed_rebar = (58, 74, 90)     # #3a4a5a - dark steel rebar
        self.color_cracks = (42, 58, 74)            # #2a3a4a - dark outline cracks
        self.color_shadow = (26, 42, 58)            # #1a2a3a - deep shadow

        # Convert to screen coordinates
        self.screen_tiles = []
        for grid_y, grid_x in building_tiles:
            screen_x, screen_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
            self.screen_tiles.append((screen_x, screen_y, grid_x, grid_y))

        # Weathering/decay effects per tile (random but consistent for crumbling wall)
        self.tile_weathering = {}
        for gy, gx in building_tiles:
            self.tile_weathering[(gx, gy)] = {
                # Decay patches (x, y, width, height)
                'decay_patches': [(random.randint(0, TILE_SIZE - 20), random.randint(0, TILE_SIZE - 20),
                                  random.randint(10, 20), random.randint(10, 20)) for _ in range(random.randint(2, 4))],
                # Light patches (x, y, width, height)
                'light_patches': [(random.randint(0, TILE_SIZE - 15), random.randint(0, TILE_SIZE - 15),
                                  random.randint(8, 15), random.randint(8, 15)) for _ in range(random.randint(1, 2))],
                # Rust stains (x, y, radius)
                'rust_stains': [(random.randint(5, TILE_SIZE - 5), random.randint(5, TILE_SIZE - 5),
                                random.randint(3, 6)) for _ in range(random.randint(1, 3))],
                # Blue glow patches (x, y, size) - DERELICTIONIST signature glow
                'blue_glow_patches': [(random.randint(5, TILE_SIZE - 5), random.randint(5, TILE_SIZE - 5),
                                      random.randint(3, 6)) for _ in range(random.randint(1, 2))],
                # Vertical cracks (x, start_y, end_y)
                'vertical_cracks': [(random.randint(10, TILE_SIZE - 10), random.randint(0, 10),
                                    TILE_SIZE - random.randint(0, 10)) for _ in range(random.randint(1, 2))],
                # Horizontal cracks (y, start_x, end_x)
                'horizontal_cracks': [(random.randint(10, TILE_SIZE - 10), random.randint(0, 10),
                                      TILE_SIZE - random.randint(0, 10)) for _ in range(random.randint(1, 2))],
                # Erosion holes (x, y, radius)
                'erosion_holes': [(random.randint(8, TILE_SIZE - 8), random.randint(8, TILE_SIZE - 8),
                                  random.randint(1, 3)) for _ in range(random.randint(3, 6))],
                # Exposed rebar sections (x, y, length)
                'exposed_rebar': [(random.randint(5, TILE_SIZE - 15), random.randint(5, TILE_SIZE - 5),
                                  random.randint(5, 12)) for _ in range(random.randint(0, 2))]
            }

    def update(self, delta_time):
        """Update building tiles. Returns True if still active."""
        if not self.active:
            return False

        self.timer += delta_time

        # Check if any building tiles still exist in game
        still_exist = False
        if hasattr(self.game, 'derelict_building_tiles'):
            for grid_y, grid_x in self.building_tiles:
                if (grid_y, grid_x) in self.game.derelict_building_tiles:
                    still_exist = True
                    break

        if not still_exist:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw persistent building tiles as unified crumbling wall structure."""
        if not self.active:
            return

        import pygame

        # First pass: Collect all active tiles
        active_tiles = []
        for screen_x, screen_y, grid_x, grid_y in self.screen_tiles:
            if hasattr(self.game, 'derelict_building_tiles'):
                if (grid_y, grid_x) in self.game.derelict_building_tiles:
                    active_tiles.append((screen_x, screen_y, grid_x, grid_y))

        if not active_tiles:
            return

        # Find grid positions for adjacency checks
        grid_positions = {(gx, gy) for _, _, gx, gy in active_tiles}

        # Draw each tile as solid wall with weathering
        for screen_x, screen_y, grid_x, grid_y in active_tiles:
            wall_rect = pygame.Rect(
                int(screen_x - TILE_SIZE // 2),
                int(screen_y - TILE_SIZE // 2),
                TILE_SIZE,
                TILE_SIZE
            )

            # 1. Base wall fill (solid concrete/brick texture)
            pygame.draw.rect(surface, self.color_base_wall, wall_rect)

            # 2. Weathering patches (darker/lighter areas)
            weathering = self.tile_weathering.get((grid_x, grid_y), {})

            # Dark decay patches
            for px, py, pw, ph in weathering.get('decay_patches', []):
                decay_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
                decay_surf.fill((*self.color_dark_decay, 180))
                surface.blit(decay_surf, (wall_rect.left + px, wall_rect.top + py))

            # Light weathered patches
            for lx, ly, lw, lh in weathering.get('light_patches', []):
                light_surf = pygame.Surface((lw, lh), pygame.SRCALPHA)
                light_surf.fill((*self.color_light_patch, 120))
                surface.blit(light_surf, (wall_rect.left + lx, wall_rect.top + ly))

            # 3. Rust/water stains
            for sx, sy, sr in weathering.get('rust_stains', []):
                stain_surf = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
                pygame.draw.circle(stain_surf, (*self.color_rust_stain, 140), (sr, sr), sr)
                surface.blit(stain_surf, (wall_rect.left + sx - sr, wall_rect.top + sy - sr))

            # 4. Blue glow patches (DERELICTIONIST signature)
            for gx, gy, gs in weathering.get('blue_glow_patches', []):
                glow_surf = pygame.Surface((gs * 2, gs * 2), pygame.SRCALPHA)
                # Create radial glow effect
                pygame.draw.circle(glow_surf, (*self.color_blue_glow, 100), (gs, gs), gs)
                pygame.draw.circle(glow_surf, (*self.color_blue_dark, 60), (gs, gs), gs // 2)
                surface.blit(glow_surf, (wall_rect.left + gx - gs, wall_rect.top + gy - gs))

            # 5. Cracks - vertical and horizontal
            # Vertical cracks
            for crack_x, crack_start_y, crack_end_y in weathering.get('vertical_cracks', []):
                pygame.draw.line(surface, self.color_cracks,
                               (wall_rect.left + crack_x, wall_rect.top + crack_start_y),
                               (wall_rect.left + crack_x, wall_rect.top + crack_end_y), 2)
                # Add shadow/depth
                pygame.draw.line(surface, self.color_shadow,
                               (wall_rect.left + crack_x + 1, wall_rect.top + crack_start_y),
                               (wall_rect.left + crack_x + 1, wall_rect.top + crack_end_y), 1)

            # Horizontal cracks
            for crack_y, crack_start_x, crack_end_x in weathering.get('horizontal_cracks', []):
                pygame.draw.line(surface, self.color_cracks,
                               (wall_rect.left + crack_start_x, wall_rect.top + crack_y),
                               (wall_rect.left + crack_end_x, wall_rect.top + crack_y), 2)
                # Add shadow/depth
                pygame.draw.line(surface, self.color_shadow,
                               (wall_rect.left + crack_start_x, wall_rect.top + crack_y + 1),
                               (wall_rect.left + crack_end_x, wall_rect.top + crack_y + 1), 1)

            # 6. Erosion holes/pockmarks
            for ex, ey, er in weathering.get('erosion_holes', []):
                pygame.draw.circle(surface, self.color_shadow, (wall_rect.left + ex, wall_rect.top + ey), er)
                pygame.draw.circle(surface, self.color_dark_decay, (wall_rect.left + ex, wall_rect.top + ey), er, 1)

            # 7. Exposed rebar (thin steel lines peeking through)
            for rx, ry, rl in weathering.get('exposed_rebar', []):
                pygame.draw.line(surface, self.color_exposed_rebar,
                               (wall_rect.left + rx, wall_rect.top + ry),
                               (wall_rect.left + rx + rl, wall_rect.top + ry), 2)
                # Highlight
                pygame.draw.line(surface, self.color_light_patch,
                               (wall_rect.left + rx, wall_rect.top + ry - 1),
                               (wall_rect.left + rx + rl, wall_rect.top + ry - 1), 1)

            # 8. Edge darkening for depth
            # Top edge shadow
            pygame.draw.line(surface, self.color_shadow,
                           (wall_rect.left, wall_rect.top),
                           (wall_rect.right, wall_rect.top), 2)
            # Left edge shadow
            pygame.draw.line(surface, self.color_shadow,
                           (wall_rect.left, wall_rect.top),
                           (wall_rect.left, wall_rect.bottom), 2)

