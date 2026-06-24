#!/usr/bin/env python3
"""
INTERFERER Animation Classes
Skill animations for the INTERFERER unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, Particle
from boneglaive.graphical.sound_helper import play_sound

# Carabiner glow colors from the sprite
COLOR_CARABINER_GLOW = (0, 191, 255)  # #00bfff - deep sky blue
COLOR_RADIO_WAVE = (0, 206, 209)  # #00ced1 - dark turquoise
COLOR_FLASH_CORE = (200, 240, 255)  # Pale blue for core


class _RadioEffulgentWave:
    """
    Base class for Radio Effulgent RF wave animations.
    Radiates concentric arc wavefronts outward from the INTERFERER toward
    affected tiles, with interference patterns on arrival and directional
    EM field-line particles.
    """

    def __init__(self, caster_x, caster_y, caster_unit, particle_emitter,
                 screen_flash_callback=None, tile_offsets=None):
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.caster_unit = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_flash_callback = screen_flash_callback

        self.timer = 0
        self.duration = 0.55
        self.finished = False

        # Build per-direction data: direction vector, target screen pos, angle
        self.directions = []
        for dx_tiles, dy_tiles in (tile_offsets or []):
            tx = caster_x + dx_tiles * TILE_SIZE
            ty = caster_y + dy_tiles * TILE_SIZE
            vec_x = float(dx_tiles)
            vec_y = float(dy_tiles)
            length = math.sqrt(vec_x * vec_x + vec_y * vec_y)
            if length > 0:
                vec_x /= length
                vec_y /= length
            angle = math.atan2(vec_y, vec_x)
            self.directions.append({
                'tx': tx, 'ty': ty,
                'vx': vec_x, 'vy': vec_y,
                'angle': angle,
            })

        # Wavefront config — 4 concentric arcs per direction, staggered launch
        self.num_wavefronts = 4
        self.wave_interval = 0.055        # time between successive wavefronts
        self.wave_travel_time = 0.18      # time for a wavefront to reach tile
        self.interference_duration = 0.22 # lingering rings at target tile
        self.arc_spread = 1.2             # radians (~70°) total arc width

        # Spawn directional EM field-line particles
        self._spawn_particles()

    def _spawn_particles(self):
        """Spawn directional particles along each emission axis."""
        for d in self.directions:
            # Field-line particles from caster toward tile
            for _ in range(8):
                spread = random.uniform(-0.25, 0.25)
                cos_a = math.cos(d['angle'] + spread)
                sin_a = math.sin(d['angle'] + spread)
                speed = random.uniform(140, 280)
                px = self.caster_x + d['vx'] * random.uniform(4, 12)
                py = self.caster_y + d['vy'] * random.uniform(4, 12)
                color = random.choice([COLOR_CARABINER_GLOW, COLOR_RADIO_WAVE, COLOR_FLASH_CORE])
                p = Particle(px, py, cos_a * speed, sin_a * speed, color,
                             size=random.uniform(1.5, 3.0), lifetime=random.uniform(0.18, 0.32))
                p.fade = True
                p.gravity = 0
                self.particle_emitter.particles.append(p)

            # Small static sparks at the target tile
            for _ in range(5):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(15, 50)
                color = random.choice([COLOR_FLASH_CORE, COLOR_CARABINER_GLOW])
                p = Particle(d['tx'] + random.uniform(-6, 6),
                             d['ty'] + random.uniform(-6, 6),
                             math.cos(angle) * speed, math.sin(angle) * speed,
                             color, size=random.uniform(1.5, 2.5),
                             lifetime=random.uniform(0.25, 0.45))
                p.fade = True
                p.gravity = 0
                self.particle_emitter.particles.append(p)

    def update(self, delta_time):
        self.timer += delta_time

        # Continuous directional sparks during wave propagation
        if self.timer < self.wave_travel_time + self.wave_interval * self.num_wavefronts:
            for d in self.directions:
                if random.random() < 0.35:
                    spread = random.uniform(-0.18, 0.18)
                    cos_a = math.cos(d['angle'] + spread)
                    sin_a = math.sin(d['angle'] + spread)
                    speed = random.uniform(100, 200)
                    progress = min(1.0, self.timer / self.wave_travel_time)
                    px = self.caster_x + d['vx'] * TILE_SIZE * progress * random.uniform(0.3, 1.0)
                    py = self.caster_y + d['vy'] * TILE_SIZE * progress * random.uniform(0.3, 1.0)
                    color = random.choice([COLOR_RADIO_WAVE, COLOR_CARABINER_GLOW])
                    p = Particle(px, py, cos_a * speed, sin_a * speed, color,
                                 size=random.uniform(1.0, 2.5), lifetime=0.15)
                    p.fade = True
                    p.gravity = 0
                    self.particle_emitter.particles.append(p)

        if self.timer >= self.duration:
            self.finished = True
        return not self.finished

    def draw(self, surface):
        if self.finished:
            return

        for d in self.directions:
            angle = d['angle']
            tx, ty = d['tx'], d['ty']

            # Draw expanding arc wavefronts radiating from caster toward tile
            for w in range(self.num_wavefronts):
                wave_start = w * self.wave_interval
                wave_age = self.timer - wave_start
                if wave_age < 0 or wave_age > self.wave_travel_time + 0.08:
                    continue

                # Wavefront expands from caster outward
                travel_progress = min(1.0, wave_age / self.wave_travel_time)
                radius = TILE_SIZE * travel_progress * 1.1

                if radius < 2:
                    continue

                # Fade: bright at start, fading as it reaches tile
                fade = 1.0 - travel_progress * 0.7
                # Alternate colors between wavefronts
                if w % 2 == 0:
                    base_color = COLOR_CARABINER_GLOW
                else:
                    base_color = COLOR_RADIO_WAVE

                # Draw arc centered on caster, facing toward the tile
                half_spread = self.arc_spread / 2
                start_angle = angle - half_spread
                end_angle = angle + half_spread

                # Arc surface large enough to contain the full arc
                surf_size = int(radius * 2 + 8)
                if surf_size < 4:
                    continue
                arc_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                center = surf_size // 2

                # Draw multiple concentric sub-arcs for thickness and glow
                for thickness_pass in range(3):
                    if thickness_pass == 0:
                        # Outer glow — wide, dim
                        arc_alpha = int(55 * fade)
                        arc_width = max(3, int(4 * (1.0 - travel_progress * 0.5)))
                        arc_color = (*base_color, arc_alpha)
                    elif thickness_pass == 1:
                        # Core arc — medium, brighter
                        arc_alpha = int(130 * fade)
                        arc_width = max(2, int(2.5 * (1.0 - travel_progress * 0.3)))
                        arc_color = (*base_color, arc_alpha)
                    else:
                        # Leading edge highlight — thin, brightest
                        arc_alpha = int(90 * fade)
                        arc_width = max(1, int(1.5))
                        arc_color = (*COLOR_FLASH_CORE, arc_alpha)

                    r = int(radius)
                    if r < arc_width:
                        continue
                    rect = pygame.Rect(center - r, center - r, r * 2, r * 2)
                    pygame.draw.arc(arc_surf, arc_color, rect,
                                    start_angle, end_angle, arc_width)

                surface.blit(arc_surf,
                             (int(self.caster_x - center), int(self.caster_y - center)),
                             special_flags=pygame.BLEND_ADD)

            # Interference pattern at the target tile (after wavefronts arrive)
            first_arrival = self.wave_travel_time
            interference_age = self.timer - first_arrival
            if 0 < interference_age < self.interference_duration:
                progress = interference_age / self.interference_duration
                fade_alpha = 1.0 - progress

                # Oscillating concentric rings (standing wave), diameter = TILE_SIZE
                half_tile = TILE_SIZE // 2
                num_rings = 3
                for r_idx in range(num_rings):
                    # Each ring oscillates in radius — constructive/destructive pattern
                    phase = interference_age * 18.0 + r_idx * (math.pi * 2 / num_rings)
                    oscillation = math.sin(phase) * 0.3 + 0.7
                    # Scale rings evenly across the tile: innermost ~33%, mid ~66%, outer ~100% of half_tile
                    base_radius = half_tile * (r_idx + 1) / num_rings
                    ring_radius = int(base_radius * oscillation)
                    if ring_radius < 2:
                        continue

                    ring_alpha = int(100 * fade_alpha * oscillation)
                    if ring_alpha < 5:
                        continue

                    ring_surf_size = ring_radius * 2 + 6
                    ring_surf = pygame.Surface((ring_surf_size, ring_surf_size), pygame.SRCALPHA)
                    ring_center = ring_surf_size // 2

                    # Alternate cyan/turquoise for interference bands
                    ring_color = COLOR_CARABINER_GLOW if r_idx % 2 == 0 else COLOR_RADIO_WAVE
                    pygame.draw.circle(ring_surf, (*ring_color, ring_alpha),
                                       (ring_center, ring_center), ring_radius, max(1, 2 - r_idx // 2))

                    surface.blit(ring_surf,
                                 (int(tx - ring_center), int(ty - ring_center)),
                                 special_flags=pygame.BLEND_ADD)

    def is_finished(self):
        return self.finished


class NeutronIlluminantCardinal(_RadioEffulgentWave):
    """
    Radio Effulgent RF wave animation for CARDINAL attacks.
    Cardinal attacks radiate RF waves diagonally around the INTERFERER.
    """

    def __init__(self, caster_x, caster_y, caster_unit, particle_emitter, screen_flash_callback=None):
        # Diagonal tile offsets (NE, SE, SW, NW)
        super().__init__(caster_x, caster_y, caster_unit, particle_emitter,
                         screen_flash_callback,
                         tile_offsets=[(1, -1), (1, 1), (-1, 1), (-1, -1)])


class NeutronIlluminantDiagonal(_RadioEffulgentWave):
    """
    Radio Effulgent RF wave animation for DIAGONAL attacks.
    Diagonal attacks radiate RF waves cardinally around the INTERFERER.
    """

    def __init__(self, caster_x, caster_y, caster_unit, particle_emitter, screen_flash_callback=None):
        # Cardinal tile offsets (N, E, S, W)
        super().__init__(caster_x, caster_y, caster_unit, particle_emitter,
                         screen_flash_callback,
                         tile_offsets=[(0, -1), (1, 0), (0, 1), (-1, 0)])


class NeuralShuntAnimation:
    """
    Neural Shunt animation - INTERFERER strikes with carabiners while three radio towers
    triangulate on target with interference waves.
    """

    def __init__(self, caster_x, caster_y, target_x, target_y, caster_unit, target_unit,
                 particle_emitter, screen_flash_callback=None, screen_shake_callback=None):
        """
        Args:
            caster_x: Screen X position of INTERFERER
            caster_y: Screen Y position of INTERFERER
            target_x: Screen X position of target
            target_y: Screen Y position of target
            caster_unit: AnimatedUnit for INTERFERER
            target_unit: AnimatedUnit for target
            particle_emitter: ParticleEmitter for spawning particles
            screen_flash_callback: Callback to trigger screen flash
            screen_shake_callback: Callback to trigger screen shake
        """
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.target_x = target_x
        self.target_y = target_y
        self.caster_unit = caster_unit
        self.target_unit = target_unit
        self.particle_emitter = particle_emitter
        self.screen_flash_callback = screen_flash_callback
        self.screen_shake_callback = screen_shake_callback

        # Animation timing
        self.phase = "windup"  # windup, strike, converge, shock
        self.timer = 0
        self.windup_duration = 0.2
        self.strike_duration = 0.4  # Increased for dual carabiner swing
        self.converge_duration = 0.35
        self.shock_duration = 0.25
        self.finished = False

        # Blue colors from INTERFERER carabiners
        self.color_outer = (0, 191, 255)  # Deep sky blue
        self.color_inner = (0, 206, 209)  # Dark turquoise
        self.color_bright = (255, 255, 255)
        self.color_static = (150, 200, 255)  # Lighter blue for static
        self.color_cyan_glow = (0, 230, 255)  # Cyan EM glow
        self.color_metal_dark = (100, 100, 120)  # Dark metal
        self.color_metal_light = (200, 200, 220)  # Light metal

        # Calculate 3 radio tower positions (triangulation around target)
        angles = [0, 2.094, 4.189]  # 0°, 120°, 240°
        distance = TILE_SIZE * 2.5
        self.tower_positions = []
        for angle in angles:
            x = target_x + math.cos(angle) * distance
            y = target_y + math.sin(angle) * distance
            self.tower_positions.append((x, y))

        # Radio wave animation state
        self.wave_rings = []  # List of expanding rings from each tower
        self.interference_points = []  # Points where waves intersect

        # Dual carabiner strike state
        self.strike_spawned = False
        self.strike_progress = 0
        self.converge_progress = 0

        # Flash tracking for tile illumination
        self.flash_triggered = False
        self.flash_timer = 0
        self.flash_display_duration = 0.2

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == "windup":
            # INTERFERER winds up, towers start pulsing
            if self.timer >= self.windup_duration:
                self.phase = "strike"
                self.timer = 0

        elif self.phase == "strike":
            # INTERFERER strikes with dual carabiners - visible weapon swing
            self.strike_progress = min(1.0, self.timer / self.strike_duration)

            if not self.strike_spawned and self.strike_progress >= 0.8:
                play_sound("neural_shunt_strike_converge")
                # Impact particles at INTERFERER position on strike completion
                for _ in range(30):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(80, 180)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_cyan_glow, self.color_bright])
                    particle = Particle(self.caster_x, self.caster_y, vx, vy, color, random.uniform(3, 7), 0.5)
                    particle.fade = True
                    self.particle_emitter.particles.append(particle)

                # Screen shake on impact - same as basic attack
                if self.screen_shake_callback:
                    self.screen_shake_callback(6, 0.18)

                # Trigger tile flash at INTERFERER position
                self.flash_triggered = True
                self.flash_timer = 0

                self.strike_spawned = True

            # Update flash timer for tile illumination
            if self.flash_triggered:
                self.flash_timer += delta_time

            if self.timer >= self.strike_duration:
                self.phase = "converge"
                self.timer = 0

        elif self.phase == "converge":
            # Radio waves emanate from three towers and converge on target
            self.converge_progress = min(1.0, self.timer / self.converge_duration)

            # Spawn new radio wave rings periodically - MORE FREQUENT
            if self.timer % 0.05 < delta_time:  # Every ~50ms (was 80ms)
                for tower_x, tower_y in self.tower_positions:
                    self.wave_rings.append({
                        'x': tower_x,
                        'y': tower_y,
                        'radius': 5,
                        'max_radius': TILE_SIZE * 2.5,
                        'alpha': 255  # Brighter (was 200)
                    })

            # Update existing wave rings (expand and fade)
            updated_rings = []
            for ring in self.wave_rings:
                ring['radius'] += 180 * delta_time  # Expand faster (was 150)
                ring['alpha'] = max(0, ring['alpha'] - 250 * delta_time)  # Fade slower (was 300)
                if ring['radius'] < ring['max_radius'] and ring['alpha'] > 0:
                    updated_rings.append(ring)
            self.wave_rings = updated_rings

            # Spawn MORE interference particles moving toward target
            if random.random() < 0.9:  # Much more frequent (was 0.5)
                tower_x, tower_y = random.choice(self.tower_positions)
                # Particle somewhere between tower and target
                t = random.uniform(0.3, 0.9)
                x = tower_x + (self.target_x - tower_x) * t
                y = tower_y + (self.target_y - tower_y) * t

                # Move toward target
                dx = self.target_x - x
                dy = self.target_y - y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    vx = (dx / dist) * 120  # Faster (was 100)
                    vy = (dy / dist) * 120
                else:
                    vx = vy = 0

                color = random.choice([self.color_outer, self.color_static, self.color_bright])
                particle = Particle(x, y, vx, vy, color, random.uniform(4, 7), 0.4)  # Larger, longer-lived
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.converge_duration:
                self.phase = "shock"
                self.timer = 0
                play_sound("neural_shunt_shock")

        elif self.phase == "shock":
            # Neural interference shock at target
            progress = self.timer / self.shock_duration

            # Spawn electric static particles around target
            if progress < 0.6 and random.random() < 0.8:
                offset_x = random.uniform(-TILE_SIZE * 0.6, TILE_SIZE * 0.6)
                offset_y = random.uniform(-TILE_SIZE * 0.6, TILE_SIZE * 0.6)
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(30, 80)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                color = random.choice([self.color_bright, self.color_static, self.color_outer])
                particle = Particle(self.target_x + offset_x, self.target_y + offset_y,
                                  vx, vy, color, random.uniform(2, 5), 0.25)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.shock_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the neural shunt radio wave convergence."""
        if self.phase == "windup":
            # Draw pulsing glow at tower positions
            progress = self.timer / self.windup_duration
            pulse = 0.5 + 0.5 * math.sin(self.timer * 20)
            for tower_x, tower_y in self.tower_positions:
                glow_radius = int(10 * progress * pulse)
                if glow_radius > 2:
                    glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*self.color_outer, int(150 * progress)),
                                     (glow_radius, glow_radius), glow_radius)
                    surface.blit(glow_surf, (int(tower_x - glow_radius),
                                            int(tower_y - glow_radius)))

        elif self.phase == "strike":
            # Draw dual carabiner swing - TWO weapon arcs
            progress = self.strike_progress

            # Calculate direction toward target
            dx = self.target_x - self.caster_x
            dy = self.target_y - self.caster_y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance > 0:
                dx /= distance
                dy /= distance

            # Perpendicular vector for arc
            perp_x = -dy
            perp_y = dx

            # Weapon swing parameters
            carabiner_length = TILE_SIZE * 1.5
            arc_width = TILE_SIZE * 0.4
            num_segments = 15

            # Draw TWO carabiner arcs (left and right)
            for carabiner_idx in range(2):
                # Offset for left/right carabiner
                side_offset = (carabiner_idx - 0.5) * 20

                # Calculate arc points
                points = []
                for i in range(num_segments):
                    seg_progress = i / (num_segments - 1)
                    swing_progress = progress * seg_progress

                    # Base position along swing direction
                    base_x = self.caster_x + dx * carabiner_length * swing_progress
                    base_y = self.caster_y + dy * carabiner_length * swing_progress

                    # Arc offset using sine curve
                    arc_offset = math.sin(swing_progress * math.pi) * arc_width
                    point_x = base_x + perp_x * (arc_offset + side_offset)
                    point_y = base_y + perp_y * (arc_offset + side_offset)

                    points.append((int(point_x), int(point_y)))

                # Draw carabiner weapon trail
                if len(points) >= 2:
                    # Outer cyan EM glow
                    pygame.draw.lines(surface, self.color_cyan_glow, False, points, 8)
                    # Metallic core
                    pygame.draw.lines(surface, self.color_metal_dark, False, points, 5)
                    pygame.draw.lines(surface, self.color_metal_light, False, points, 3)

            # Draw tile flash at INTERFERER position
            if self.flash_triggered and self.flash_timer < self.flash_display_duration:
                flash_progress = self.flash_timer / self.flash_display_duration
                alpha = int(220 * (1 - flash_progress))

                # Draw bright cyan glow at INTERFERER position (like Radio Effulgent)
                for radius_mult in [1.5, 1.0, 0.5]:
                    radius = int(TILE_SIZE * 0.8 * radius_mult)
                    glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

                    # Outer cyan glow
                    layer_alpha = alpha // (int(1.0 / radius_mult) + 1)
                    color = (*self.color_cyan_glow, layer_alpha)
                    pygame.draw.circle(glow_surf, color, (radius, radius), radius)

                    # Bright center
                    if radius_mult <= 0.7:
                        core_alpha = min(255, int(alpha * 1.5))
                        core_color = (255, 255, 255, core_alpha)  # White bright core
                        core_radius = radius // 2
                        pygame.draw.circle(glow_surf, core_color, (radius, radius), core_radius)

                    surface.blit(glow_surf,
                               (int(self.caster_x - radius), int(self.caster_y - radius)),
                               special_flags=pygame.BLEND_ADD)

        elif self.phase == "converge":
            # Draw visible radio tower positions with pulsing glow
            pulse = 0.7 + 0.3 * math.sin(self.timer * 8)
            for tower_x, tower_y in self.tower_positions:
                # Large glowing tower marker
                tower_radius = int(18 * pulse)
                tower_surf = pygame.Surface((tower_radius * 2, tower_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(tower_surf, (*self.color_outer, 200),
                                 (tower_radius, tower_radius), tower_radius)
                # Bright core
                core_radius = int(tower_radius * 0.5)
                pygame.draw.circle(tower_surf, (*self.color_bright, 255),
                                 (tower_radius, tower_radius), core_radius)
                surface.blit(tower_surf, (int(tower_x - tower_radius),
                                         int(tower_y - tower_radius)),
                           special_flags=pygame.BLEND_ADD)

            # Draw radio wave rings expanding from towers - THICKER
            for ring in self.wave_rings:
                radius = int(ring['radius'])
                alpha = int(ring['alpha'])
                if radius > 0 and alpha > 0:
                    # Draw expanding ring with thicker width
                    ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (*self.color_outer, alpha),
                                     (radius, radius), radius, 4)  # Width=4 (was 2)
                    surface.blit(ring_surf, (int(ring['x'] - radius),
                                            int(ring['y'] - radius)))

            # Draw beam lines from towers to target
            for tower_x, tower_y in self.tower_positions:
                beam_alpha = int(120 * self.converge_progress)
                if beam_alpha > 10:
                    # Draw thick beam line
                    pygame.draw.line(surface, (*self.color_static, beam_alpha),
                                   (int(tower_x), int(tower_y)),
                                   (int(self.target_x), int(self.target_y)), 3)
                    # Brighter inner line
                    pygame.draw.line(surface, (*self.color_bright, beam_alpha // 2),
                                   (int(tower_x), int(tower_y)),
                                   (int(self.target_x), int(self.target_y)), 1)

            # Draw MUCH larger interference glow at target (waves converging)
            interference_radius = int(50 * self.converge_progress)  # Bigger (was 30)
            if interference_radius > 5:
                glow_surf = pygame.Surface((interference_radius * 2, interference_radius * 2), pygame.SRCALPHA)
                alpha = int(200 * self.converge_progress)  # Brighter (was 150)
                pygame.draw.circle(glow_surf, (*self.color_static, alpha),
                                 (interference_radius, interference_radius), interference_radius)
                # Add bright core
                core_radius = int(interference_radius * 0.5)
                pygame.draw.circle(glow_surf, (*self.color_bright, int(alpha * 0.7)),
                                 (interference_radius, interference_radius), core_radius)
                surface.blit(glow_surf, (int(self.target_x - interference_radius),
                                        int(self.target_y - interference_radius)),
                           special_flags=pygame.BLEND_ADD)

        elif self.phase == "shock":
            # Draw neural interference shock rings at target
            progress = self.timer / self.shock_duration

            # Multiple expanding shock rings
            for i in range(3):
                ring_radius = int(TILE_SIZE * 0.5 * (1 + progress + i * 0.15))
                alpha = int(160 * (1 - progress) / (i + 1))
                if ring_radius > 0 and alpha > 0:
                    ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (*self.color_outer, alpha),
                                     (ring_radius, ring_radius), ring_radius, 3)
                    surface.blit(ring_surf, (int(self.target_x - ring_radius),
                                            int(self.target_y - ring_radius)))

    def is_finished(self):
        """Check if animation is complete."""
        return self.finished

class ScalarNodeTriggerAnimation:
    """
    Scalar Node trigger animation - hidden standing wave breaks loose in searing
    blue-white electrical fire when enemy steps on the trap.
    """

    def __init__(self, trap_x, trap_y, target_unit, particle_emitter, screen_flash_callback=None):
        """
        Args:
            trap_x: Screen X position of trap
            trap_y: Screen Y position of trap
            target_unit: AnimatedUnit that triggered the trap
            particle_emitter: ParticleEmitter for spawning particles
            screen_flash_callback: Callback to trigger screen flash
        """
        self.trap_x = trap_x
        self.trap_y = trap_y
        self.target_unit = target_unit
        self.particle_emitter = particle_emitter
        self.screen_flash_callback = screen_flash_callback

        # Animation timing
        self.phase = "erupt"  # erupt, flare, burn, fade
        self.timer = 0
        self.erupt_duration = 0.15  # Violent eruption of flames
        self.flare_duration = 0.2   # Peak intensity
        self.burn_duration = 0.2    # Sustained fire
        self.fade_duration = 0.2    # Dying down

        # Colors - blue-white electrical fire
        self.color_white = (255, 255, 255)
        self.color_blue_white = (200, 230, 255)
        self.color_electric_blue = (100, 200, 255)
        self.color_deep_blue = (50, 150, 255)

        # Visual state
        self.flame_height = 0
        self.max_flame_height = TILE_SIZE * 1.5
        self.intensity = 0

        # Eruption spawned flag
        self.eruption_spawned = False

        # Lightning arcs (list of segment lists)
        self.lightning_bolts = []
        self.lightning_timer = 0
        self.lightning_interval = 0.08  # New arc every 80ms

        # Smoke particles
        self.smoke_particles = []

    def _generate_lightning_arc(self, start_x, start_y, target_x, target_y, segments=5):
        """Generate a jagged lightning arc between two points."""
        arc_segments = []
        current_x = start_x
        current_y = start_y

        for i in range(segments):
            progress = (i + 1) / segments
            next_x = start_x + (target_x - start_x) * progress
            next_y = start_y + (target_y - start_y) * progress

            # Add jagged offset (except for last segment)
            if i < segments - 1:
                offset_x = random.uniform(-15, 15)
                offset_y = random.uniform(-10, 10)
                next_x += offset_x
                next_y += offset_y

            arc_segments.append(((current_x, current_y), (next_x, next_y)))
            current_x = next_x
            current_y = next_y

        return {'segments': arc_segments, 'lifetime': 0.15, 'max_lifetime': 0.15}

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time
        self.lightning_timer += delta_time

        # Update lightning bolts
        for bolt in self.lightning_bolts:
            bolt['lifetime'] -= delta_time
        self.lightning_bolts = [b for b in self.lightning_bolts if b['lifetime'] > 0]

        # Update smoke particles
        for smoke in self.smoke_particles:
            smoke['y'] -= 30 * delta_time  # Rise
            smoke['x'] += smoke['vx'] * delta_time
            smoke['size'] += 15 * delta_time  # Expand
            smoke['alpha'] -= 150 * delta_time  # Fade
        self.smoke_particles = [s for s in self.smoke_particles if s['alpha'] > 0]

        if self.phase == "erupt":
            # Violent eruption of blue-white flames from ground
            progress = self.timer / self.erupt_duration
            self.intensity = progress
            self.flame_height = self.max_flame_height * (progress ** 0.5)  # Fast rise

            # Spawn initial eruption burst
            if not self.eruption_spawned:
                play_sound("scalar_node_trigger")
                # Massive upward burst of flame particles
                for _ in range(60):
                    # Strongly biased upward like a geyser
                    angle = math.pi * 1.5 + random.uniform(-0.5, 0.5)  # Mostly up, some spread
                    speed = random.uniform(200, 400)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_white, self.color_white,
                                         self.color_blue_white, self.color_electric_blue])
                    size = random.uniform(5, 12)
                    particle = Particle(self.trap_x, self.trap_y, vx, vy, color, size, 0.5)
                    particle.fade = True
                    particle.gravity = 80  # Slight arc
                    self.particle_emitter.particles.append(particle)

                self.eruption_spawned = True

            # Continue spawning flame particles during eruption
            if random.random() < 0.8:
                angle = math.pi * 1.5 + random.uniform(-0.4, 0.4)
                speed = random.uniform(250, 350)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                color = random.choice([self.color_white, self.color_blue_white])
                size = random.uniform(6, 10)
                particle = Particle(self.trap_x, self.trap_y, vx, vy, color, size, 0.4)
                particle.fade = True
                particle.gravity = 100
                self.particle_emitter.particles.append(particle)

            # Spawn lightning arcs during eruption
            if self.lightning_timer >= self.lightning_interval:
                self.lightning_timer = 0
                # Create 2-3 arcs radiating outward
                for _ in range(random.randint(2, 3)):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(40, 80)
                    target_x = self.trap_x + math.cos(angle) * distance
                    target_y = self.trap_y + math.sin(angle) * distance - random.uniform(0, 40)
                    arc = self._generate_lightning_arc(self.trap_x, self.trap_y, target_x, target_y, segments=4)
                    self.lightning_bolts.append(arc)

            # Spawn smoke particles
            if random.random() < 0.3:
                smoke = {
                    'x': self.trap_x + random.uniform(-10, 10),
                    'y': self.trap_y - random.uniform(0, 20),
                    'vx': random.uniform(-20, 20),
                    'size': random.uniform(12, 20),
                    'alpha': random.uniform(80, 120),
                    'color': random.choice([(100, 100, 120), (80, 80, 100), (120, 120, 140)])
                }
                self.smoke_particles.append(smoke)

            if self.timer >= self.erupt_duration:
                self.phase = "flare"
                self.timer = 0
                self.lightning_timer = 0

        elif self.phase == "flare":
            # Peak intensity - bright searing column of electrical fire
            self.intensity = 1.0
            self.flame_height = self.max_flame_height

            # Dense stream of bright flame particles
            if random.random() < 0.9:
                offset_x = random.uniform(-TILE_SIZE * 0.15, TILE_SIZE * 0.15)
                x = self.trap_x + offset_x
                y = self.trap_y

                angle = math.pi * 1.5 + random.uniform(-0.25, 0.25)
                speed = random.uniform(180, 280)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed

                # Very bright colors at peak
                color = random.choice([self.color_white, self.color_white,
                                     self.color_blue_white, self.color_blue_white,
                                     self.color_electric_blue])
                size = random.uniform(6, 11)
                particle = Particle(x, y, vx, vy, color, size, 0.45)
                particle.fade = True
                particle.gravity = 120
                self.particle_emitter.particles.append(particle)

            # Electric sparks at peak intensity
            if random.random() < 0.6:
                offset_x = random.uniform(-TILE_SIZE * 0.3, TILE_SIZE * 0.3)
                offset_y = random.uniform(-self.flame_height * 0.7, -TILE_SIZE * 0.3)
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(80, 150)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                particle = Particle(self.trap_x + offset_x, self.trap_y + offset_y,
                                  vx, vy, self.color_white, 4, 0.25)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            # Spawn lightning arcs at peak
            if self.lightning_timer >= self.lightning_interval:
                self.lightning_timer = 0
                # More arcs at peak intensity
                for _ in range(random.randint(3, 4)):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(50, 100)
                    target_x = self.trap_x + math.cos(angle) * distance
                    target_y = self.trap_y + math.sin(angle) * distance - random.uniform(10, 50)
                    arc = self._generate_lightning_arc(self.trap_x, self.trap_y, target_x, target_y, segments=5)
                    self.lightning_bolts.append(arc)

            # Heavy smoke at peak
            if random.random() < 0.5:
                smoke = {
                    'x': self.trap_x + random.uniform(-15, 15),
                    'y': self.trap_y - random.uniform(10, 30),
                    'vx': random.uniform(-30, 30),
                    'size': random.uniform(15, 25),
                    'alpha': random.uniform(100, 140),
                    'color': random.choice([(90, 90, 110), (70, 70, 90), (110, 110, 130)])
                }
                self.smoke_particles.append(smoke)

            if self.timer >= self.flare_duration:
                self.phase = "burn"
                self.timer = 0
                self.lightning_timer = 0

        elif self.phase == "burn":
            # Sustained column of electrical fire (less intense than flare)
            self.intensity = 0.85
            self.flame_height = self.max_flame_height

            # Moderate stream of flame particles
            if random.random() < 0.6:
                offset_x = random.uniform(-TILE_SIZE * 0.2, TILE_SIZE * 0.2)
                x = self.trap_x + offset_x
                y = self.trap_y

                angle = math.pi * 1.5 + random.uniform(-0.3, 0.3)
                speed = random.uniform(140, 220)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed

                color = random.choice([self.color_blue_white, self.color_electric_blue,
                                     self.color_deep_blue])
                size = random.uniform(5, 9)
                particle = Particle(x, y, vx, vy, color, size, 0.4)
                particle.fade = True
                particle.gravity = 130
                self.particle_emitter.particles.append(particle)

            # Occasional sparks
            if random.random() < 0.3:
                offset_x = random.uniform(-TILE_SIZE * 0.3, TILE_SIZE * 0.3)
                offset_y = random.uniform(-self.flame_height * 0.6, -TILE_SIZE * 0.2)
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(60, 100)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                particle = Particle(self.trap_x + offset_x, self.trap_y + offset_y,
                                  vx, vy, self.color_blue_white, 3, 0.2)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.burn_duration:
                self.phase = "fade"
                self.timer = 0

        elif self.phase == "fade":
            # Dying down
            progress = self.timer / self.fade_duration
            self.intensity = 1.0 - progress
            self.flame_height = self.max_flame_height * (1.0 - progress)

            # Fewer particles as it fades
            if random.random() < 0.3 * (1.0 - progress):
                offset_x = random.uniform(-TILE_SIZE * 0.2, TILE_SIZE * 0.2)
                x = self.trap_x + offset_x
                y = self.trap_y
                angle = math.pi * 1.5 + random.uniform(-0.4, 0.4)
                speed = random.uniform(60, 120) * (1.0 - progress)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                color = random.choice([self.color_electric_blue, self.color_deep_blue])
                particle = Particle(x, y, vx, vy, color, random.uniform(3, 6), 0.3)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.fade_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the scalar node electrical fire eruption."""
        # Draw smoke first (behind everything)
        for smoke in self.smoke_particles:
            smoke_radius = int(smoke['size'])
            if smoke_radius > 3:
                smoke_surf = pygame.Surface((smoke_radius * 2, smoke_radius * 2), pygame.SRCALPHA)
                alpha = max(0, min(255, int(smoke['alpha'])))
                color = smoke['color']
                pygame.draw.circle(smoke_surf, (color[0], color[1], color[2], alpha),
                                 (smoke_radius, smoke_radius), smoke_radius)
                surface.blit(smoke_surf, (int(smoke['x'] - smoke_radius),
                                         int(smoke['y'] - smoke_radius)))

        # Draw lightning arcs
        for bolt in self.lightning_bolts:
            alpha = int(255 * (bolt['lifetime'] / bolt['max_lifetime']))

            # Draw multiple layers for thickness/glow
            for thickness, brightness in [(4, 0.5), (2, 0.8), (1, 1.0)]:
                for (x1, y1), (x2, y2) in bolt['segments']:
                    # Blue-white lightning color
                    color_alpha = max(0, min(255, int(alpha * brightness)))
                    color = (200 + int(55 * brightness),
                            230 + int(25 * brightness),
                            255,
                            color_alpha)

                    if thickness > 1:
                        # Draw thicker lines with pygame
                        pygame.draw.line(surface, color,
                                       (int(x1), int(y1)), (int(x2), int(y2)), thickness)
                    else:
                        # Bright white core
                        pygame.draw.line(surface, (255, 255, 255, color_alpha),
                                       (int(x1), int(y1)), (int(x2), int(y2)), 1)

        if self.phase in ["erupt", "flare", "burn", "fade"]:
            # Searing electrical torch/pillar
            if self.flame_height > 10:
                # Draw flame as elongated glow shooting upward
                flame_width = int(TILE_SIZE * 0.6 * self.intensity)
                flame_height = int(self.flame_height)

                # Multiple layers for depth
                for layer in range(3):
                    width = flame_width - layer * 8
                    if width < 5:
                        continue

                    # Create elongated flame shape
                    flame_surf = pygame.Surface((width * 2, flame_height), pygame.SRCALPHA)

                    # Color gradient - white at base, blue-white at top
                    for i in range(flame_height):
                        progress_up = i / flame_height
                        if progress_up < 0.3:
                            # Base: white
                            color = self.color_white
                        elif progress_up < 0.6:
                            # Middle: blue-white
                            color = self.color_blue_white
                        else:
                            # Top: electric blue
                            color = self.color_electric_blue

                        alpha = max(0, min(255, int(220 * self.intensity * (1 - progress_up * 0.7) / (layer + 1))))
                        pygame.draw.line(flame_surf, (color[0], color[1], color[2], alpha),
                                       (width - layer * 2, i),
                                       (width + layer * 2, i), 2)

                    surface.blit(flame_surf, (int(self.trap_x - width),
                                             int(self.trap_y - flame_height)),
                               special_flags=pygame.BLEND_ADD)

                # Bright core at base
                core_radius = int(12 * self.intensity)
                if core_radius > 3:
                    core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                    core_alpha = max(0, min(255, int(255 * self.intensity)))
                    pygame.draw.circle(core_surf, (self.color_white[0], self.color_white[1],
                                                  self.color_white[2], core_alpha),
                                     (core_radius, core_radius), core_radius)
                    surface.blit(core_surf, (int(self.trap_x - core_radius),
                                            int(self.trap_y - core_radius)),
                               special_flags=pygame.BLEND_ADD)

    def is_finished(self):
        """Check if animation is complete."""
        return self.phase == "fade" and self.timer >= self.fade_duration


class KarrierRavePhaseOut:
    """
    KARRIER RAVE activation - INTERFERER tunes into carrier wave and phases out of reality.
    """

    def __init__(self, caster_x, caster_y, caster_unit, particle_emitter, screen_flash_callback=None):
        """
        Args:
            caster_x: Screen X position of INTERFERER
            caster_y: Screen Y position of INTERFERER
            caster_unit: AnimatedUnit for the INTERFERER
            particle_emitter: ParticleEmitter for spawning particles
            screen_flash_callback: Callback to trigger screen flash
        """
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.caster_unit = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_flash_callback = screen_flash_callback

        # Animation timing
        self.phase = "tune"  # tune, phase_out, complete
        self.timer = 0
        self.tune_duration = 0.3   # Tuning into carrier wave
        self.phase_duration = 0.4  # Phasing out

        # Colors - electromagnetic/radio wave colors
        self.color_carrier_wave = (150, 200, 255)  # Light blue
        self.color_phase = (200, 150, 255)  # Purple/magenta
        self.color_white = (255, 255, 255)

        # Visual state
        self.intensity = 0
        self.phase_alpha = 255  # Caster's opacity

        # Multi-frequency radio wave rings (3 carrier frequencies) - CONVERGING INWARD
        self.wave_rings = []  # List of {x, y, radius, min_radius, alpha, frequency, phase}
        self.wave_spawn_timer = 0
        self.fast_wave_interval = 0.05   # High frequency
        self.medium_wave_interval = 0.1  # Medium frequency
        self.slow_wave_interval = 0.15   # Low frequency

        # Transmission lines (converging toward center - incoming signals)
        self.transmission_lines = []  # List of {angle, start_distance, distance, alpha}
        self.line_count = 8  # 8 converging lines

        # Static/noise particles for tuning phase
        self.static_particles = []  # List of {x, y, lifetime, alpha}

        # Wave oscillation (for amplitude modulation)
        self.oscillation_timer = 0

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time
        self.wave_spawn_timer += delta_time
        self.oscillation_timer += delta_time

        # Update transmission lines (converging inward)
        for line in self.transmission_lines:
            line['distance'] -= 200 * delta_time  # Move toward center
            if line['distance'] < 10:
                line['alpha'] -= 400 * delta_time
        self.transmission_lines = [l for l in self.transmission_lines if l['alpha'] > 0 and l['distance'] > 0]

        # Update static particles
        for static in self.static_particles:
            static['lifetime'] -= delta_time
            static['alpha'] = int(255 * (static['lifetime'] / 0.15))
        self.static_particles = [s for s in self.static_particles if s['lifetime'] > 0]

        if self.phase == "tune":
            # Tuning into carrier wave - multi-frequency expanding rings
            if self.timer == 0 or not hasattr(self, '_tune_sound_played'):
                play_sound("karrier_rave_phaseout")
                self._tune_sound_played = True
            progress = self.timer / self.tune_duration
            self.intensity = progress

            # Spawn multi-frequency radio wave rings (CONVERGING INWARD)
            # Fast frequency carrier
            if self.wave_spawn_timer >= self.fast_wave_interval:
                self.wave_rings.append({
                    'x': self.caster_x,
                    'y': self.caster_y,
                    'radius': 140,  # Start large
                    'min_radius': 0,  # Shrink to INTERFERER
                    'alpha': 200,
                    'frequency': 'fast',
                    'speed': 180,
                    'phase_offset': random.uniform(0, 2 * math.pi)
                })
                self.wave_spawn_timer = 0

            # Medium frequency (every 2 fast waves)
            if len(self.wave_rings) % 2 == 0 and random.random() < 0.3:
                self.wave_rings.append({
                    'x': self.caster_x,
                    'y': self.caster_y,
                    'radius': 120,  # Start large
                    'min_radius': 0,
                    'alpha': 180,
                    'frequency': 'medium',
                    'speed': 120,
                    'phase_offset': random.uniform(0, 2 * math.pi)
                })

            # Slow frequency (occasional)
            if random.random() < 0.1:
                self.wave_rings.append({
                    'x': self.caster_x,
                    'y': self.caster_y,
                    'radius': 100,  # Start large
                    'min_radius': 0,
                    'alpha': 150,
                    'frequency': 'slow',
                    'speed': 80,
                    'phase_offset': random.uniform(0, 2 * math.pi)
                })

            # Update existing rings - SHRINK INWARD with oscillating amplitude
            for ring in self.wave_rings:
                ring['radius'] -= ring['speed'] * delta_time  # Converge inward
                # Fade out as rings approach center
                if ring['radius'] < 20:
                    ring['alpha'] -= 300 * delta_time
                # Add oscillation for amplitude modulation
                ring['oscillation'] = math.sin(self.oscillation_timer * 10 + ring['phase_offset']) * 0.3 + 0.7
            self.wave_rings = [r for r in self.wave_rings if r['alpha'] > 0 and r['radius'] > ring['min_radius']]

            # Spawn transmission lines (converging from distance toward INTERFERER)
            if random.random() < 0.15:
                for i in range(self.line_count):
                    angle = (2 * math.pi * i / self.line_count) + random.uniform(-0.1, 0.1)
                    self.transmission_lines.append({
                        'angle': angle,
                        'distance': 120,  # Start at distance
                        'start_distance': 120,
                        'alpha': 200
                    })

            # Spawn static/noise particles (finding the frequency)
            if random.random() < 0.8:
                x = self.caster_x + random.uniform(-40, 40)
                y = self.caster_y + random.uniform(-40, 40)
                self.static_particles.append({
                    'x': x,
                    'y': y,
                    'lifetime': 0.15,
                    'alpha': random.randint(100, 200)
                })

            # Spawn wave-riding particles (on wave crests - FLOWING INWARD)
            if len(self.wave_rings) > 0 and random.random() < 0.5:
                # Pick a random ring
                ring = random.choice(self.wave_rings)
                if ring['radius'] > 10:
                    angle = random.uniform(0, 2 * math.pi)
                    x = ring['x'] + math.cos(angle) * ring['radius']
                    y = ring['y'] + math.sin(angle) * ring['radius']
                    # Particle rides the wave INWARD toward INTERFERER
                    vx = -math.cos(angle) * ring['speed'] * 0.5
                    vy = -math.sin(angle) * ring['speed'] * 0.5
                    particle = Particle(x, y, vx, vy, self.color_carrier_wave, 3, 0.4)
                    particle.fade = True
                    self.particle_emitter.particles.append(particle)

            if self.timer >= self.tune_duration:
                self.phase = "phase_out"
                self.timer = 0

        elif self.phase == "phase_out":
            # Phasing out of reality - fade to translucent as carrier wave absorbs him
            progress = self.timer / self.phase_duration
            self.intensity = 1.0 - progress
            self.phase_alpha = int(255 * (1.0 - progress * 0.7))  # Fade to 30% opacity

            # Spawn phase particles - FLOWING INWARD toward INTERFERER
            if random.random() < 0.7:
                # Spawn at distance, flow inward
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(40, 80)
                x = self.caster_x + math.cos(angle) * distance
                y = self.caster_y + math.sin(angle) * distance
                # Flow inward
                vx = -math.cos(angle) * random.uniform(60, 120)
                vy = -math.sin(angle) * random.uniform(60, 120)
                color = random.choice([self.color_phase, self.color_carrier_wave, self.color_white])
                particle = Particle(x, y, vx, vy, color, random.uniform(3, 7), 0.6)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            # Spawn converging radio wave rings during phase-out
            if random.random() < 0.3:
                self.wave_rings.append({
                    'x': self.caster_x,
                    'y': self.caster_y,
                    'radius': random.uniform(80, 120),  # Start large
                    'min_radius': 0,
                    'alpha': 150,
                    'frequency': 'slow',
                    'speed': 100,
                    'phase_offset': random.uniform(0, 2 * math.pi)
                })

            # Update existing rings - CONVERGE INWARD
            for ring in self.wave_rings:
                ring['radius'] -= 100 * delta_time  # Shrink inward
                if ring['radius'] < 15:
                    ring['alpha'] -= 250 * delta_time
                # Add oscillation
                ring['oscillation'] = math.sin(self.oscillation_timer * 10 + ring.get('phase_offset', 0)) * 0.3 + 0.7
            self.wave_rings = [r for r in self.wave_rings if r['alpha'] > 0 and r['radius'] > ring.get('min_radius', 0)]

            if self.timer >= self.phase_duration:
                self.phase = "complete"
                self.timer = 0
                # Set caster to semi-transparent (phased out)
                if self.caster_unit:
                    self.caster_unit.phased_alpha = 80  # Very translucent

        return self.phase != "complete"

    def draw(self, surface):
        """Draw the enhanced radio wave transmission effect."""
        # Draw transmission lines (CONVERGING toward INTERFERER from distance)
        for line in self.transmission_lines:
            if line['distance'] > 5:
                # Start point at distance
                start_x = self.caster_x + math.cos(line['angle']) * line['distance']
                start_y = self.caster_y + math.sin(line['angle']) * line['distance']
                alpha = max(0, min(255, int(line['alpha'])))
                # Draw line from distance toward INTERFERER (converging inward)
                pygame.draw.line(surface, (self.color_carrier_wave[0],
                                          self.color_carrier_wave[1],
                                          self.color_carrier_wave[2], alpha),
                               (int(start_x), int(start_y)),
                               (int(self.caster_x), int(self.caster_y)), 1)

        # Draw static/noise particles (tuning phase)
        for static in self.static_particles:
            alpha = max(0, min(255, static['alpha']))
            size = 2
            static_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(static_surf, (self.color_carrier_wave[0],
                                           self.color_carrier_wave[1],
                                           self.color_carrier_wave[2], alpha),
                             (size, size), size)
            surface.blit(static_surf, (int(static['x'] - size), int(static['y'] - size)))

        # Draw radio wave rings with oscillating amplitude
        for i, ring in enumerate(self.wave_rings):
            radius = int(ring['radius'])
            if radius > ring['min_radius'] + 2:  # Draw if not too close to center
                ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                # Apply oscillation to alpha for amplitude modulation
                base_alpha = ring['alpha']
                oscillation = ring.get('oscillation', 1.0)
                alpha = max(0, min(255, int(base_alpha * oscillation)))

                # Draw thicker ring for wave visualization
                thickness = 3 if ring.get('frequency') == 'fast' else 2
                pygame.draw.circle(ring_surf, (self.color_carrier_wave[0],
                                             self.color_carrier_wave[1],
                                             self.color_carrier_wave[2], alpha),
                                 (radius, radius), radius, thickness)
                surface.blit(ring_surf, (int(ring['x'] - radius),
                                        int(ring['y'] - radius)))

        # Draw wave interference points (where rings overlap)
        if len(self.wave_rings) > 1:
            for i in range(len(self.wave_rings)):
                for j in range(i + 1, len(self.wave_rings)):
                    ring1 = self.wave_rings[i]
                    ring2 = self.wave_rings[j]

                    # Check if rings are close in radius (interference zone)
                    radius_diff = abs(ring1['radius'] - ring2['radius'])
                    if radius_diff < 15:  # Interference threshold
                        # Draw bright spot at interference point
                        # Sample a few points around the circle
                        for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
                            ix = self.caster_x + math.cos(angle) * ring1['radius']
                            iy = self.caster_y + math.sin(angle) * ring1['radius']

                            interference_alpha = int(min(ring1['alpha'], ring2['alpha']) * 0.6)
                            if interference_alpha > 50:
                                spot_radius = 6
                                spot_surf = pygame.Surface((spot_radius * 2, spot_radius * 2), pygame.SRCALPHA)
                                pygame.draw.circle(spot_surf, (self.color_white[0],
                                                             self.color_white[1],
                                                             self.color_white[2], interference_alpha),
                                                 (spot_radius, spot_radius), spot_radius)
                                surface.blit(spot_surf, (int(ix - spot_radius),
                                                        int(iy - spot_radius)),
                                           special_flags=pygame.BLEND_ADD)

        # Draw glow around INTERFERER during tuning
        if self.phase == "tune" and self.intensity > 0:
            glow_radius = int(30 * self.intensity)
            if glow_radius > 5:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                alpha = int(150 * self.intensity)
                pygame.draw.circle(glow_surf, (self.color_carrier_wave[0],
                                             self.color_carrier_wave[1],
                                             self.color_carrier_wave[2], alpha),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(self.caster_x - glow_radius),
                                        int(self.caster_y - glow_radius)),
                           special_flags=pygame.BLEND_ADD)

        # Draw enhanced phase shimmer with ripples during phase-out
        if self.phase == "phase_out":
            # Multiple ripple layers
            for ripple_num in range(3):
                shimmer_radius = int(35 + ripple_num * 15)
                shimmer_surf = pygame.Surface((shimmer_radius * 2, shimmer_radius * 2), pygame.SRCALPHA)
                alpha = int(100 * self.intensity / (ripple_num + 1))
                pygame.draw.circle(shimmer_surf, (self.color_phase[0],
                                                self.color_phase[1],
                                                self.color_phase[2], alpha),
                                 (shimmer_radius, shimmer_radius), shimmer_radius, 2)
                surface.blit(shimmer_surf, (int(self.caster_x - shimmer_radius),
                                           int(self.caster_y - shimmer_radius)),
                           special_flags=pygame.BLEND_ADD)


class KarrierRaveTripleStrike:
    """
    KARRIER RAVE triple strike - INTERFERER goes WILD with glowing carabiners.
    Omnislash-style: rapid dashing attacks from different angles with Radio Effulgent pulses.
    Each strike incorporates directional beam patterns (cardinal/diagonal based on position).
    """

    def __init__(self, caster_x, caster_y, target_x, target_y, caster_unit, target_unit,
                 particle_emitter, screen_flash_callback=None):
        """
        Args:
            caster_x: Screen X position of attacker (original position)
            caster_y: Screen Y position of attacker (original position)
            target_x: Screen X position of target
            target_y: Screen Y position of target
            caster_unit: AnimatedUnit for the attacker
            target_unit: AnimatedUnit for the target
            particle_emitter: ParticleEmitter for spawning particles
            screen_flash_callback: Callback to trigger screen flash
        """
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.original_caster_x = caster_x  # Store original position
        self.original_caster_y = caster_y
        self.target_x = target_x
        self.target_y = target_y
        self.caster_unit = caster_unit
        self.target_unit = target_unit
        self.particle_emitter = particle_emitter
        self.screen_flash_callback = screen_flash_callback

        # Animation timing - fast and furious!
        self.phase = "dash1"  # dash1, strike1, dash2, strike2, dash3, strike3, return, fade
        self.timer = 0
        self.dash_duration = 0.08      # Quick dash to position
        self.strike_duration = 0.1     # Impact and flash
        self.return_duration = 0.12    # Return to original position
        self.fade_duration = 0.15      # Final fade

        # Strike counter
        self.current_strike = 1

        # Track if strike has been spawned
        self.strike_spawned = False

        # Colors
        self.color_carrier = (150, 200, 255)  # Carabiner glow
        self.color_energy = (200, 220, 255)   # Energy aura
        self.color_rave = (180, 220, 255)     # Rave particles
        self.color_white = (255, 255, 255)

        # Radio Effulgent beam state (for timing, but won't be drawn)
        self.beams = []  # List of beam dicts
        self.beam_length = TILE_SIZE * 2

        # INTERFERER position offsets for Omnislash-style positioning
        # He'll dash to different angles around target
        self.current_offset_x = 0
        self.current_offset_y = 0
        self.target_offset_x = 0
        self.target_offset_y = 0

        # Calculate strike positions (different angles around target)
        angle_offset = TILE_SIZE * 0.6
        self.strike_positions = [
            (target_x - angle_offset, target_y),          # Left side (cardinal)
            (target_x + angle_offset * 0.7, target_y - angle_offset * 0.7),  # Upper-right (diagonal)
            (target_x, target_y + angle_offset)           # Below (cardinal)
        ]

        # Motion blur trail for dash effect
        self.blur_trail = []  # List of {x, y, alpha} positions

        # Carabiner glow intensity
        self.carabiner_glow = 0  # 0-1, pulses during animation

    def _add_strike_beams(self, use_diagonal=False):
        """Add Radio Effulgent style beams for a strike (appends to existing beams)."""
        if use_diagonal:
            # Diagonal pattern (X shape)
            directions = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
        else:
            # Cardinal pattern (+ shape)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            # Normalize direction
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx_norm = dx / length
                dy_norm = dy / length
            else:
                dx_norm, dy_norm = 0, 0

            self.beams.append({
                'dx': dx_norm,
                'dy': dy_norm,
                'length': 0,
                'max_length': self.beam_length,
                'alpha': 255
            })

    def update(self, delta_time):
        """Update Omnislash-style dashing attack animation."""
        self.timer += delta_time

        # Update beams (but they won't be drawn)
        for beam in self.beams:
            if beam['length'] < beam['max_length']:
                beam['length'] += 900 * delta_time  # Fast extension
            else:
                beam['alpha'] -= 700 * delta_time  # Quick fade
        self.beams = [b for b in self.beams if b['alpha'] > 0]

        # Update blur trail (fade out)
        for blur in self.blur_trail:
            blur['alpha'] -= 800 * delta_time
        self.blur_trail = [b for b in self.blur_trail if b['alpha'] > 0]

        # Pulse carabiner glow
        self.carabiner_glow = 0.7 + 0.3 * math.sin(self.timer * 30)

        # === DASH PHASES === Omnislash-style positioning
        if self.phase == "dash1":
            progress = min(1.0, self.timer / self.dash_duration)
            # Lerp to first strike position
            target_pos = self.strike_positions[0]
            self.current_offset_x = (target_pos[0] - self.original_caster_x) * progress
            self.current_offset_y = (target_pos[1] - self.original_caster_y) * progress

            # Add blur trail
            if random.random() < 0.5:
                self.blur_trail.append({
                    'x': self.original_caster_x + self.current_offset_x,
                    'y': self.original_caster_y + self.current_offset_y,
                    'alpha': 200
                })

            # Energy particles during dash
            if random.random() < 0.7:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(40, 80)
                particle = Particle(
                    self.original_caster_x + self.current_offset_x,
                    self.original_caster_y + self.current_offset_y,
                    math.cos(angle) * speed, math.sin(angle) * speed,
                    self.color_rave, random.uniform(2, 5), 0.25
                )
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.dash_duration:
                self.phase = "strike1"
                self.timer = 0
                self.strike_spawned = False

        elif self.phase == "strike1":
            if not self.strike_spawned:
                play_sound("karrier_rave_strike_hit")
                # Cardinal cross pattern
                self._add_strike_beams(use_diagonal=False)
                # Impact particles
                for _ in range(25):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(120, 250)
                    particle = Particle(self.target_x, self.target_y,
                                      math.cos(angle) * speed, math.sin(angle) * speed,
                                      self.color_energy, random.uniform(4, 8), 0.3)
                    particle.fade = True
                    self.particle_emitter.particles.append(particle)
                self.strike_spawned = True

            if self.timer >= self.strike_duration:
                self.phase = "dash2"
                self.timer = 0

        elif self.phase == "dash2":
            progress = min(1.0, self.timer / self.dash_duration)
            # Lerp from position 0 to position 1
            start_pos = self.strike_positions[0]
            target_pos = self.strike_positions[1]
            interp_x = start_pos[0] + (target_pos[0] - start_pos[0]) * progress
            interp_y = start_pos[1] + (target_pos[1] - start_pos[1]) * progress
            self.current_offset_x = interp_x - self.original_caster_x
            self.current_offset_y = interp_y - self.original_caster_y

            # Blur trail
            if random.random() < 0.6:
                self.blur_trail.append({
                    'x': interp_x, 'y': interp_y, 'alpha': 220
                })

            # More energy particles
            if random.random() < 0.8:
                angle = random.uniform(0, 2 * math.pi)
                particle = Particle(interp_x, interp_y,
                                  math.cos(angle) * 60, math.sin(angle) * 60,
                                  self.color_carrier, 4, 0.2)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.dash_duration:
                self.phase = "strike2"
                self.timer = 0
                self.strike_spawned = False

        elif self.phase == "strike2":
            if not self.strike_spawned:
                play_sound("karrier_rave_strike_hit")
                # Diagonal X pattern
                self._add_strike_beams(use_diagonal=True)
                # Impact particles
                for _ in range(30):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(140, 270)
                    particle = Particle(self.target_x, self.target_y,
                                      math.cos(angle) * speed, math.sin(angle) * speed,
                                      self.color_white, random.uniform(5, 9), 0.35)
                    particle.fade = True
                    self.particle_emitter.particles.append(particle)
                self.strike_spawned = True

            if self.timer >= self.strike_duration:
                self.phase = "dash3"
                self.timer = 0

        elif self.phase == "dash3":
            progress = min(1.0, self.timer / self.dash_duration)
            # Lerp from position 1 to position 2
            start_pos = self.strike_positions[1]
            target_pos = self.strike_positions[2]
            interp_x = start_pos[0] + (target_pos[0] - start_pos[0]) * progress
            interp_y = start_pos[1] + (target_pos[1] - start_pos[1]) * progress
            self.current_offset_x = interp_x - self.original_caster_x
            self.current_offset_y = interp_y - self.original_caster_y

            # Heavy blur trail for final dash
            if random.random() < 0.8:
                self.blur_trail.append({
                    'x': interp_x, 'y': interp_y, 'alpha': 240
                })

            # Intense particles
            if random.random() < 0.9:
                angle = random.uniform(0, 2 * math.pi)
                particle = Particle(interp_x, interp_y,
                                  math.cos(angle) * 70, math.sin(angle) * 70,
                                  self.color_white, 5, 0.25)
                particle.fade = True
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.dash_duration:
                self.phase = "strike3"
                self.timer = 0
                self.strike_spawned = False

        elif self.phase == "strike3":
            if not self.strike_spawned:
                play_sound("karrier_rave_strike_final")
                # Final blow from below (cardinal) - create beams for both patterns
                self._add_strike_beams(use_diagonal=False)  # Cardinal beams
                self._add_strike_beams(use_diagonal=True)   # Diagonal beams

                for _ in range(50):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(180, 350)
                    color = random.choice([self.color_white, self.color_carrier, self.color_energy])
                    particle = Particle(self.target_x, self.target_y,
                                      math.cos(angle) * speed, math.sin(angle) * speed,
                                      color, random.uniform(6, 12), 0.45)
                    particle.fade = True
                    self.particle_emitter.particles.append(particle)
                self.strike_spawned = True

            if self.timer >= self.strike_duration:
                self.phase = "return"
                self.timer = 0

        elif self.phase == "return":
            # Dash back to original position
            progress = min(1.0, self.timer / self.return_duration)
            start_pos = self.strike_positions[2]
            interp_x = start_pos[0] + (self.original_caster_x - start_pos[0]) * progress
            interp_y = start_pos[1] + (self.original_caster_y - start_pos[1]) * progress
            self.current_offset_x = interp_x - self.original_caster_x
            self.current_offset_y = interp_y - self.original_caster_y

            # Light blur trail on return
            if random.random() < 0.4:
                self.blur_trail.append({
                    'x': interp_x, 'y': interp_y, 'alpha': 150
                })

            # Fade carabiner glow
            self.carabiner_glow *= (1.0 - progress)

            if self.timer >= self.return_duration:
                self.phase = "fade"
                self.timer = 0

        elif self.phase == "fade":
            if self.timer >= self.fade_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw Omnislash-style triple strike with motion blur and glowing carabiners."""
        # Draw motion blur trail
        for blur in self.blur_trail:
            alpha = max(0, min(255, int(blur['alpha'])))
            if alpha > 10:
                blur_size = 12
                blur_surf = pygame.Surface((blur_size * 2, blur_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(blur_surf, (self.color_rave[0], self.color_rave[1],
                                              self.color_rave[2], alpha),
                                 (blur_size, blur_size), blur_size)
                surface.blit(blur_surf, (int(blur['x'] - blur_size),
                                        int(blur['y'] - blur_size)),
                           special_flags=pygame.BLEND_ADD)

        # NOTE: Beams are created and updated but NOT drawn (as requested)
        # The beam system remains in place for timing but is invisible

        # Draw glowing carabiner aura around INTERFERER at current position
        if self.carabiner_glow > 0 and self.phase != "fade":
            interferer_x = self.original_caster_x + self.current_offset_x
            interferer_y = self.original_caster_y + self.current_offset_y

            # Pulsing energy aura
            glow_radius = int(25 * self.carabiner_glow)
            if glow_radius > 5:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                alpha = int(180 * self.carabiner_glow)
                pygame.draw.circle(glow_surf, (self.color_carrier[0],
                                              self.color_carrier[1],
                                              self.color_carrier[2], alpha),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(interferer_x - glow_radius),
                                        int(interferer_y - glow_radius)),
                           special_flags=pygame.BLEND_ADD)

            # Bright core glow (carabiners)
            core_radius = int(12 * self.carabiner_glow)
            if core_radius > 3:
                core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                core_alpha = int(240 * self.carabiner_glow)
                pygame.draw.circle(core_surf, (255, 255, 255, core_alpha),
                                 (core_radius, core_radius), core_radius)
                surface.blit(core_surf, (int(interferer_x - core_radius),
                                        int(interferer_y - core_radius)),
                           special_flags=pygame.BLEND_ADD)

        # Note: INTERFERER sprite stays at original position - the blur trail and glowing
        # aura show his rapid movement. He's moving so fast you only see afterimages!



# ============================================================================
# INTERFERER BASIC ATTACK - DUAL CARABINER SWING
# ============================================================================

class InterfererDualCarabinerAttack:
    """
    INTERFERER basic attack animation - swings both huge carabiners.
    Two metallic arcs with cyan EM glow + Radio Effulgent pulse on impact.
    """

    def __init__(self, attacker_unit, target_unit, particle_emitter, screen_shake_callback, screen_flash_callback=None):
        """
        Args:
            attacker_unit: AnimatedUnit doing the attacking
            target_unit: AnimatedUnit being attacked
            particle_emitter: ParticleEmitter for effects
            screen_shake_callback: Function(intensity, duration)
            screen_flash_callback: Function(color, intensity, duration) for EM flash
        """
        self.attacker = attacker_unit
        self.target = target_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback

        # Calculate attack vector
        self.dx = target_unit.x - attacker_unit.x
        self.dy = target_unit.y - attacker_unit.y
        distance = math.sqrt(self.dx * self.dx + self.dy * self.dy)

        if distance > 0:
            self.dx /= distance
            self.dy /= distance

        self.distance = distance

        # Animation state
        self.phase = "windup"  # windup → swing → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.windup_duration = 0.1
        self.swing_duration = 0.25
        self.impact_duration = 0.15

        # Swing progress for weapon drawing
        self.swing_progress = 0.0

        # Carabiner colors
        self.color_metal_dark = (105, 105, 105)    # #696969
        self.color_metal_light = (211, 211, 211)   # #d3d3d3
        self.color_cyan_glow = (0, 191, 255)       # #00bfff

        # Track flash for tile illumination
        self.flash_triggered = False
        self.flash_timer = 0
        self.flash_display_duration = 0.2

    def _trigger_windup(self):
        """Phase 1: Windup dual carabiner swing."""
        play_sound("interferer_attack_windup_swing")
        # Cyan EM particles as carabiners charge
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 70)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            from .core import Particle
            particle = Particle(self.attacker.x, self.attacker.y, vx, vy, 
                              self.color_cyan_glow,
                              size=random.uniform(2, 3), lifetime=0.12)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_swing(self):
        """Phase 2: Swing dual carabiners (visual only)."""
        # Cyan EM sparks along swing path
        for i in range(12):
            progress = i / 12
            x = self.attacker.x + self.dx * self.distance * progress * 0.7
            y = self.attacker.y + self.dy * self.distance * progress * 0.7

            vx = self.dx * 100
            vy = self.dy * 100

            from .core import Particle
            particle = Particle(x, y, vx, vy, self.color_cyan_glow,
                              size=random.uniform(2, 3), lifetime=0.18)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Dual carabiner impact with Radio Effulgent pulse."""
        play_sound("interferer_attack_impact")
        # Metallic impact with cyan EM burst
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 170)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Mix of metallic and cyan colors
            color = random.choice([
                self.color_metal_light,
                self.color_cyan_glow,
                (255, 255, 255),
            ])

            from .core import Particle
            particle = Particle(self.target.x, self.target.y, vx, vy, color,
                              size=random.uniform(2, 4), lifetime=random.uniform(0.15, 0.25))
            particle.gravity = 120
            self.particle_emitter.particles.append(particle)

        # Mark that flash was triggered for tile illumination
        self.flash_triggered = True
        self.flash_timer = 0

        # Strong metallic impact
        self.target.shake_intensity = 12
        self.screen_shake(6, 0.18)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update flash timer if flash is active
        if self.flash_triggered:
            self.flash_timer += delta_time

        if self.phase == "windup":
            if self.timer == 0 or not hasattr(self, "_windup_triggered"):
                self._trigger_windup()
                self._windup_triggered = True

            if self.timer >= self.windup_duration:
                self.phase = "swing"
                self.timer = 0
                self._trigger_swing()

        elif self.phase == "swing":
            # Update swing progress for weapon drawing
            self.swing_progress = min(1.0, self.timer / self.swing_duration)

            if self.timer >= self.swing_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw dual carabiner swing."""
        import pygame

        # Draw windup cyan glow
        if self.phase == "windup":
            progress = self.timer / self.windup_duration
            glow_radius = int(18 * progress)

            if glow_radius > 2:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_cyan_glow, int(100 * progress)),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(self.attacker.x - glow_radius),
                                        int(self.attacker.y - glow_radius)))

        # Draw dual carabiner swing arcs during swing phase
        if self.phase == "swing":
            # Calculate perpendicular vector for arc sweep
            perp_x = -self.dy
            perp_y = self.dx

            # Draw TWO carabiner arcs (left and right)
            for carabiner_idx in range(2):
                # Offset each carabiner arc slightly (one on each side)
                side_offset = (carabiner_idx - 0.5) * 20  # Left and right spread

                arc_width = 30  # Arc width
                carabiner_length = self.distance + 20

                # Calculate arc points
                points = []
                num_segments = 15

                for i in range(num_segments):
                    progress = (i / (num_segments - 1)) * self.swing_progress

                    # Position along attack vector
                    base_x = self.attacker.x + self.dx * carabiner_length * progress
                    base_y = self.attacker.y + self.dy * carabiner_length * progress

                    # Arc offset (sine curve) + side offset for dual weapons
                    arc_offset = math.sin(progress * math.pi) * arc_width + side_offset

                    # Calculate point position
                    point_x = base_x + perp_x * arc_offset
                    point_y = base_y + perp_y * arc_offset

                    points.append((int(point_x), int(point_y)))

                # Draw carabiner arc
                if len(points) >= 2:
                    # Draw cyan EM glow (outer)
                    pygame.draw.lines(surface, self.color_cyan_glow, False, points, 8)
                    # Draw metallic core
                    pygame.draw.lines(surface, self.color_metal_dark, False, points, 5)
                    pygame.draw.lines(surface, self.color_metal_light, False, points, 3)

        # Draw impact flash
        if self.phase == "impact":
            progress = self.timer / self.impact_duration
            if progress < 0.5:
                flash_alpha = int(255 * (1.0 - progress / 0.5))
                flash_radius = int(32 * (1.0 + progress))

                # Cyan-white flash
                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                # Cyan center
                center_radius = int(flash_radius * 0.6)
                pygame.draw.circle(flash_surf, (*self.color_cyan_glow, flash_alpha),
                                 (flash_radius, flash_radius), center_radius)

                surface.blit(flash_surf, (int(self.target.x - flash_radius),
                                         int(self.target.y - flash_radius)))

        # Draw Radio Effulgent tile pulse at INTERFERER position (not target)
        if self.flash_triggered and self.flash_timer < self.flash_display_duration:
            progress = self.flash_timer / self.flash_display_duration
            alpha = int(220 * (1 - progress))

            # Draw bright cyan glow at INTERFERER position (like Radio Effulgent)
            for radius_mult in [1.5, 1.0, 0.5]:
                from .core import TILE_SIZE
                radius = int(TILE_SIZE * 0.8 * radius_mult)
                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

                # Outer cyan glow
                layer_alpha = alpha // (int(1.0 / radius_mult) + 1)
                color = (*self.color_cyan_glow, layer_alpha)
                pygame.draw.circle(glow_surf, color, (radius, radius), radius)

                # Bright center
                if radius_mult <= 0.7:
                    core_alpha = min(255, int(alpha * 1.5))
                    core_color = (255, 255, 255, core_alpha)  # White bright core
                    core_radius = radius // 2
                    pygame.draw.circle(glow_surf, core_color, (radius, radius), core_radius)

                surface.blit(glow_surf,
                           (int(self.attacker.x - radius), int(self.attacker.y - radius)),
                           special_flags=pygame.BLEND_ADD)

