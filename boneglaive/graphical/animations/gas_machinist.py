#!/usr/bin/env python3
"""
GAS MACHINIST Animation Classes
Skill animations for the GAS MACHINIST unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, VaporParticleCloud


class VaporSpawnAnimation:
    """
    Spawn animation for HEINOUS VAPOR entities.
    Shows violent gas eruption from ground that condenses into vapor cloud.

    Phases:
    1. Ground Crack - Glowing fissures appear
    2. Eruption - Gas geyser bursts upward with particles
    3. Expansion - Cloud expands spherically
    4. Condensation - Settles into final vapor form with eyes appearing
    """

    # Use same colors as VaporParticleCloud for consistency
    VAPOR_COLORS = VaporParticleCloud.VAPOR_COLORS

    def __init__(self, target_x, target_y, vapor_type='BROACHING', particle_emitter=None,
                 screen_shake_callback=None):
        """
        Initialize vapor spawn animation.

        Args:
            target_x: Spawn X coordinate (screen space)
            target_y: Spawn Y coordinate (screen space)
            vapor_type: Type of vapor (BROACHING, SAFETY, COOLANT, CUTTING)
            particle_emitter: Optional particle emitter for eruption effects
            screen_shake_callback: Optional callback for screen shake
        """
        self.target_x = target_x
        self.target_y = target_y
        self.vapor_type = vapor_type
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback

        # Get color palette for this vapor type
        self.colors = self.VAPOR_COLORS.get(vapor_type, self.VAPOR_COLORS['BROACHING'])
        self.primary_color = self.colors[0]
        self.secondary_color = self.colors[1]
        self.tertiary_color = self.colors[2]

        # Animation state
        self.phase = "crack"
        self.timer = 0
        self.active = True

        # Phase durations
        self.crack_duration = 0.2
        self.eruption_duration = 0.3
        self.expansion_duration = 0.4
        self.condensation_duration = 0.3

        # Visual elements
        self.crack_lines = []
        self._generate_crack_lines()

        self.eruption_particles = []
        self.expansion_radius = 0
        self.condensation_progress = 0
        self.eyes_alpha = 0

    def _generate_crack_lines(self):
        """Generate radiating crack lines from spawn point."""
        num_cracks = 5
        for i in range(num_cracks):
            angle = (i / num_cracks) * 2 * math.pi + random.uniform(-0.2, 0.2)
            length = random.uniform(20, 40)
            width = random.uniform(1, 3)

            self.crack_lines.append({
                'angle': angle,
                'length': length,
                'width': width,
                'offset': random.uniform(0, 0.5)  # Stagger appearance
            })

    def update(self, delta_time):
        """Update spawn animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "crack":
            # Ground cracks appear with glow
            if self.timer >= self.crack_duration:
                self.phase = "eruption"
                self.timer = 0
                # Trigger screen shake at eruption start
                if self.screen_shake_callback:
                    self.screen_shake_callback(intensity=6, duration=0.2)

        elif self.phase == "eruption":
            # Gas geyser bursts upward
            if self.timer < self.eruption_duration:
                # Spawn eruption particles
                if self.particle_emitter and random.random() < 0.8:
                    # Upward velocity with some spread
                    angle = -math.pi/2 + random.uniform(-0.4, 0.4)
                    speed = random.uniform(150, 300)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed

                    from .core import Particle
                    particle = Particle(
                        x=self.target_x + random.uniform(-10, 10),
                        y=self.target_y,
                        vx=vx,
                        vy=vy,
                        color=random.choice(self.colors),
                        size=random.uniform(3, 7),
                        lifetime=random.uniform(0.4, 0.8)
                    )
                    particle.gravity = 100  # Light gravity for gas
                    self.particle_emitter.particles.append(particle)

                # Create internal eruption particles for drawing
                if len(self.eruption_particles) < 50:
                    angle = -math.pi/2 + random.uniform(-0.5, 0.5)
                    speed = random.uniform(100, 200)
                    self.eruption_particles.append({
                        'x': self.target_x,
                        'y': self.target_y,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'size': random.uniform(2, 5),
                        'color': random.choice(self.colors),
                        'lifetime': random.uniform(0.3, 0.6),
                        'max_lifetime': 0.6
                    })
            else:
                self.phase = "expansion"
                self.timer = 0

        elif self.phase == "expansion":
            # Gas expands outward spherically
            progress = self.timer / self.expansion_duration
            self.expansion_radius = progress * 50  # Max radius 50px

            if self.timer >= self.expansion_duration:
                self.phase = "condensation"
                self.timer = 0

        elif self.phase == "condensation":
            # Cloud contracts and eyes appear
            progress = self.timer / self.condensation_duration
            self.condensation_progress = progress
            self.eyes_alpha = int(255 * min(1.0, progress * 2))

            if self.timer >= self.condensation_duration:
                self.active = False
                return False

        # Update eruption particles
        for particle in self.eruption_particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['vy'] += 80 * delta_time  # Slight gravity
            particle['lifetime'] -= delta_time

            if particle['lifetime'] <= 0:
                self.eruption_particles.remove(particle)

        return True

    def draw(self, surface):
        """Draw the spawn animation."""
        if not self.active:
            return

        if self.phase == "crack":
            self._draw_cracks(surface)

        elif self.phase == "eruption":
            self._draw_cracks(surface)
            self._draw_eruption(surface)

        elif self.phase == "expansion":
            self._draw_expansion(surface)

        elif self.phase == "condensation":
            self._draw_condensation(surface)

    def _draw_cracks(self, surface):
        """Draw glowing ground cracks."""
        progress = min(1.0, self.timer / self.crack_duration)

        for crack in self.crack_lines:
            # Staggered appearance
            crack_progress = max(0.0, min(1.0, (progress - crack['offset']) / (1.0 - crack['offset'])))

            if crack_progress > 0:
                # Calculate crack endpoint
                length = crack['length'] * crack_progress
                end_x = self.target_x + math.cos(crack['angle']) * length
                end_y = self.target_y + math.sin(crack['angle']) * length

                # Glow alpha
                alpha = int(200 * crack_progress)

                # Draw glow behind crack
                glow_surf = pygame.Surface((int(length * 2), int(crack['width'] * 6)), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, (*self.primary_color, alpha // 2),
                               (0, int(crack['width'] * 3)),
                               (int(length), int(crack['width'] * 3)),
                               int(crack['width'] * 4))

                # Rotate and blit glow
                glow_surf = pygame.transform.rotate(glow_surf, -math.degrees(crack['angle']))
                glow_rect = glow_surf.get_rect(center=(self.target_x, self.target_y))
                surface.blit(glow_surf, glow_rect)

                # Draw bright crack line
                pygame.draw.line(surface, (*self.secondary_color, alpha),
                               (int(self.target_x), int(self.target_y)),
                               (int(end_x), int(end_y)),
                               int(crack['width']))

    def _draw_eruption(self, surface):
        """Draw gas geyser eruption."""
        # Draw eruption particles
        for particle in self.eruption_particles:
            if particle['lifetime'] > 0:
                alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
                if alpha > 0:
                    color = (*particle['color'], alpha)
                    size = particle['size']

                    # Draw particle with glow
                    particle_surf = pygame.Surface((int(size * 3), int(size * 3)), pygame.SRCALPHA)

                    # Glow
                    pygame.draw.circle(particle_surf, (*particle['color'], alpha // 3),
                                     (int(size * 1.5), int(size * 1.5)), int(size * 1.5))

                    # Core
                    pygame.draw.circle(particle_surf, color,
                                     (int(size * 1.5), int(size * 1.5)), int(size))

                    surface.blit(particle_surf, (int(particle['x'] - size * 1.5),
                                                int(particle['y'] - size * 1.5)))

        # Draw central geyser column
        progress = self.timer / self.eruption_duration
        column_height = progress * 60
        column_width = 20 * (1.0 - progress * 0.5)  # Narrows as it rises

        alpha = int(180 * (1.0 - progress * 0.5))
        if alpha > 0:
            column_surf = pygame.Surface((int(column_width * 2), int(column_height)), pygame.SRCALPHA)

            # Draw column with gradient
            for i in range(int(column_height)):
                line_alpha = int(alpha * (1.0 - (i / column_height) * 0.5))
                color_idx = int((i / column_height) * (len(self.colors) - 1))
                color = self.colors[min(color_idx, len(self.colors) - 1)]

                pygame.draw.line(column_surf, (*color, line_alpha),
                               (int(column_width * 0.5), int(column_height - i)),
                               (int(column_width * 1.5), int(column_height - i)),
                               int(column_width))

            surface.blit(column_surf, (int(self.target_x - column_width),
                                      int(self.target_y - column_height)))

    def _draw_expansion(self, surface):
        """Draw expanding gas cloud."""
        progress = self.timer / self.expansion_duration

        # Draw expanding rings
        num_rings = 3
        for i in range(num_rings):
            ring_offset = i * 0.2
            ring_progress = min(1.0, max(0.0, (progress - ring_offset) / (1.0 - ring_offset)))

            if ring_progress > 0:
                radius = int(self.expansion_radius * ring_progress)
                alpha = int(150 * (1.0 - ring_progress))

                if alpha > 0:
                    color = self.colors[i % len(self.colors)]

                    # Draw filled circle with gradient
                    ring_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
                    center = radius + 10

                    # Outer glow
                    pygame.draw.circle(ring_surf, (*color, alpha // 3), (center, center), radius + 10)

                    # Main ring
                    pygame.draw.circle(ring_surf, (*color, alpha), (center, center), radius, 5)

                    surface.blit(ring_surf, (int(self.target_x - center), int(self.target_y - center)))

    def _draw_condensation(self, surface):
        """Draw condensing vapor cloud with eyes appearing."""
        progress = self.condensation_progress

        # Cloud contracts
        radius = int(50 * (1.0 - progress * 0.5))  # Shrinks from 50 to 25
        alpha = int(200 * (0.5 + progress * 0.5))  # Increases opacity

        # Draw condensing cloud
        cloud_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        center = radius + 10

        # Multiple layers for depth
        for i in range(3):
            layer_radius = int(radius * (1.0 - i * 0.2))
            layer_alpha = int(alpha * (0.6 + i * 0.2))
            color = self.colors[i % len(self.colors)]

            pygame.draw.circle(cloud_surf, (*color, layer_alpha), (center, center), layer_radius)

        surface.blit(cloud_surf, (int(self.target_x - center), int(self.target_y - center)))

        # Eyes fade in
        if self.eyes_alpha > 0:
            eye_color = (173, 255, 47)
            eye_spacing = 10
            eye_y_offset = -3

            for eye_x_offset in [-eye_spacing, eye_spacing]:
                eye_x = int(self.target_x + eye_x_offset)
                eye_y = int(self.target_y + eye_y_offset)

                # Outer glow
                glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*eye_color, self.eyes_alpha // 3), (8, 8), 8)
                surface.blit(glow_surf, (eye_x - 8, eye_y - 8))

                # Main eye
                pygame.draw.circle(surface, (*eye_color, self.eyes_alpha), (eye_x, eye_y), 4)

                # Highlight
                pygame.draw.circle(surface, (255, 255, 200, self.eyes_alpha), (eye_x - 1, eye_y - 1), 2)


# ============================================================================
# DIVERGE ANIMATION
# ============================================================================

class GasSplitStream:
    """
    Animated gas stream that arcs from source to destination.
    Used for the splitting effect in Diverge.
    """
    def __init__(self, start_x, start_y, end_x, end_y, color_palette, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.colors = color_palette
        self.timer = -delay
        self.duration = 0.6
        self.active = True

        # Particles along the stream
        self.particles = []

    def update(self, delta_time):
        """Update stream animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer < 0:  # Delay period
            return True

        # Spawn particles along arc
        if self.timer < self.duration and random.random() < 0.5:
            progress = self.timer / self.duration

            # Arc trajectory (parabolic)
            mid_x = (self.start_x + self.end_x) / 2
            mid_y = (self.start_y + self.end_y) / 2 - 40  # Arc height

            # Bezier-like curve
            px = self.start_x + (mid_x - self.start_x) * progress * 2
            py = self.start_y + (mid_y - self.start_y) * progress * 2

            if progress > 0.5:
                progress2 = (progress - 0.5) * 2
                px = mid_x + (self.end_x - mid_x) * progress2
                py = mid_y + (self.end_y - mid_y) * progress2

            self.particles.append({
                'x': px,
                'y': py,
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(-20, 20),
                'size': random.uniform(3, 6),
                'color': random.choice(self.colors),
                'lifetime': random.uniform(0.3, 0.6),
                'max_lifetime': 0.6
            })

        # Update particles
        for p in self.particles[:]:
            p['x'] += p['vx'] * delta_time
            p['y'] += p['vy'] * delta_time
            p['lifetime'] -= delta_time

            if p['lifetime'] <= 0:
                self.particles.remove(p)

        if self.timer >= self.duration and len(self.particles) == 0:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw the gas stream."""
        if not self.active or self.timer < 0:
            return

        # Draw particles
        for p in self.particles:
            if p['lifetime'] > 0:
                alpha = int(255 * (p['lifetime'] / p['max_lifetime']))
                if alpha > 0:
                    p_surf = pygame.Surface((int(p['size'] * 3), int(p['size'] * 3)), pygame.SRCALPHA)

                    # Glow
                    pygame.draw.circle(p_surf, (*p['color'], alpha // 3),
                                     (int(p['size'] * 1.5), int(p['size'] * 1.5)),
                                     int(p['size'] * 1.5))

                    # Core
                    pygame.draw.circle(p_surf, (*p['color'], alpha),
                                     (int(p['size'] * 1.5), int(p['size'] * 1.5)),
                                     int(p['size']))

                    surface.blit(p_surf, (int(p['x'] - p['size'] * 1.5),
                                         int(p['y'] - p['size'] * 1.5)))


class DivergeAnimation:
    """
    DIVERGE skill animation for GAS MACHINIST.
    Violently splits target into two specialized vapor entities.

    Phases:
    1. Compression - Target compresses as pressure builds
    2. Split - Explosive rupture into white and red gas streams
    3. Formation - Streams arc to spawn positions and condense
    4. Manifestation - Final vapors materialize with eyes
    """

    # Use vapor colors for consistency
    COOLANT_COLORS = VaporParticleCloud.VAPOR_COLORS['COOLANT']
    CUTTING_COLORS = VaporParticleCloud.VAPOR_COLORS['CUTTING']
    INDUSTRIAL_GREY = (138, 138, 138)

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Diverge animation.

        Args:
            target_unit: The unit/vapor being split
            target_pos: (grid_y, grid_x) - position being targeted
            camera: Camera for coordinate conversion
        """
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert target position to screen coordinates
        # target_pos is (grid_y, grid_x) format from renderer
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "compression"
        self.timer = 0
        self.active = True

        # Phase durations
        self.compression_duration = 0.3
        self.split_duration = 0.4
        self.formation_duration = 0.6
        self.manifestation_duration = 0.7

        # Visual elements
        self.compression_scale = 1.0
        self.glow_intensity = 0
        self.split_streams = []
        self.split_triggered = False

        # Spawn positions (adjacent to target)
        # Assuming coolant spawns left, cutting spawns right
        self.coolant_x = self.target_x - TILE_SIZE
        self.coolant_y = self.target_y
        self.cutting_x = self.target_x + TILE_SIZE
        self.cutting_y = self.target_y

        # Start compression
        self._start_compression()

    def _start_compression(self):
        """Phase 1: Compression."""
        self.phase = "compression"
        self.timer = 0

        # Light screen shake
        self.screen_shake_callback(intensity=4, duration=0.3)

    def _start_split(self):
        """Phase 2: Split."""
        self.phase = "split"
        self.timer = 0

        # Create gas streams
        self.split_streams = [
            # Coolant stream (white) - goes left
            GasSplitStream(self.target_x, self.target_y,
                          self.coolant_x, self.coolant_y,
                          self.COOLANT_COLORS, delay=0),

            # Cutting stream (red) - goes right
            GasSplitStream(self.target_x, self.target_y,
                          self.cutting_x, self.cutting_y,
                          self.CUTTING_COLORS, delay=0.05)
        ]

        # Heavy screen shake at split moment
        self.screen_shake_callback(intensity=8, duration=0.4)

        # Explosion particles at split point
        if self.particle_emitter:
            for _ in range(40):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 250)

                from .core import Particle
                particle = Particle(
                    x=self.target_x,
                    y=self.target_y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    color=random.choice(self.COOLANT_COLORS + self.CUTTING_COLORS),
                    size=random.uniform(2, 5),
                    lifetime=random.uniform(0.3, 0.7)
                )
                particle.gravity = 80
                self.particle_emitter.particles.append(particle)

    def _start_formation(self):
        """Phase 3: Formation."""
        self.phase = "formation"
        self.timer = 0

    def _start_manifestation(self):
        """Phase 4: Manifestation."""
        self.phase = "manifestation"
        self.timer = 0

    def update(self, delta_time):
        """Update animation."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update based on phase
        if self.phase == "compression":
            # Compress target unit
            progress = min(1.0, self.timer / self.compression_duration)
            self.compression_scale = 1.0 - (progress * 0.3)  # Compress to 70%
            self.glow_intensity = progress

            # Manipulate target unit visually
            if self.target_unit:
                # Store original scale if not already stored
                if not hasattr(self.target_unit, 'original_scale_y'):
                    self.target_unit.original_scale_y = getattr(self.target_unit, 'pry_stretch_y', 1.0)

                self.target_unit.pry_stretch_y = self.compression_scale

            if self.timer >= self.compression_duration:
                self._start_split()

        elif self.phase == "split":
            # Update gas streams
            for stream in self.split_streams:
                stream.update(delta_time)

            # Reset target unit scale
            if self.target_unit and hasattr(self.target_unit, 'original_scale_y'):
                self.target_unit.pry_stretch_y = self.target_unit.original_scale_y
                delattr(self.target_unit, 'original_scale_y')

            if self.timer >= self.split_duration:
                self._start_formation()

        elif self.phase == "formation":
            # Keep streams updating
            for stream in self.split_streams:
                stream.update(delta_time)

            if self.timer >= self.formation_duration:
                self._start_manifestation()

        elif self.phase == "manifestation":
            # Final vapor condensation effects at both positions
            progress = self.timer / self.manifestation_duration

            if self.timer >= self.manifestation_duration:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        if self.phase == "compression":
            # Draw pulsing industrial grey glow
            if self.glow_intensity > 0:
                pulse = 1.0 + math.sin(self.timer * 10) * 0.2
                radius = int(30 * self.glow_intensity * pulse)
                alpha = int(150 * self.glow_intensity)

                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.INDUSTRIAL_GREY, alpha),
                                 (radius, radius), radius)

                surface.blit(glow_surf, (int(self.target_x - radius),
                                        int(self.target_y - radius)))

        elif self.phase == "split":
            # Draw gas streams
            for stream in self.split_streams:
                stream.draw(surface)

            # Draw split flash at center
            progress = self.timer / self.split_duration
            if progress < 0.3:
                flash_alpha = int(200 * (1.0 - progress / 0.3))
                flash_radius = int(40 + progress / 0.3 * 20)

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)

                surface.blit(flash_surf, (int(self.target_x - flash_radius),
                                         int(self.target_y - flash_radius)))

        elif self.phase == "formation":
            # Continue drawing streams
            for stream in self.split_streams:
                stream.draw(surface)

            # Draw condensation at endpoints
            progress = self.timer / self.formation_duration
            if progress > 0.4:
                cond_progress = (progress - 0.4) / 0.6

                # Coolant condensation (left)
                self._draw_condensation(surface, self.coolant_x, self.coolant_y,
                                       self.COOLANT_COLORS, cond_progress)

                # Cutting condensation (right)
                self._draw_condensation(surface, self.cutting_x, self.cutting_y,
                                       self.CUTTING_COLORS, cond_progress)

        elif self.phase == "manifestation":
            # Draw final materialization at both positions
            progress = self.timer / self.manifestation_duration

            # Industrial metal "clang" rings
            for pos_x, pos_y, colors in [(self.coolant_x, self.coolant_y, self.COOLANT_COLORS),
                                          (self.cutting_x, self.cutting_y, self.CUTTING_COLORS)]:
                num_rings = 3
                for i in range(num_rings):
                    ring_delay = i * 0.15
                    ring_progress = min(1.0, max(0.0, (progress - ring_delay) / (1.0 - ring_delay)))

                    if ring_progress > 0:
                        radius = int(15 + 25 * ring_progress)
                        alpha = int(180 * (1.0 - ring_progress))

                        if alpha > 0:
                            color = colors[i % len(colors)]
                            pygame.draw.circle(surface, (*color, alpha),
                                             (int(pos_x), int(pos_y)), radius, 3)

    def _draw_condensation(self, surface, x, y, colors, progress):
        """Draw condensation effect at a position."""
        # Swirling particles
        for i in range(12):
            angle = (i / 12) * 2 * math.pi + progress * 3
            radius = 25 * (1.0 - progress * 0.5)
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius

            alpha = int(180 * (1.0 - progress * 0.5))
            size = 4 * (1.0 - progress * 0.3)

            if alpha > 0:
                color = colors[i % len(colors)]
                pygame.draw.circle(surface, (*color, alpha),
                                 (int(px), int(py)), int(size))


# ============================================================================
# VAPOR AOE TICK ANIMATION
# ============================================================================

class VaporFogCloud:
    """
    Expanding semi-transparent fog at tile positions for volumetric gas effect.
    """
    def __init__(self, center_x, center_y, colors, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.colors = colors
        self.timer = -delay
        self.duration = 0.8
        self.active = True

        # Initialize fog particles
        self.particles = []
        particle_count = 20
        for i in range(particle_count):
            angle = (i / particle_count) * 2 * math.pi + random.uniform(-0.2, 0.2)
            self.particles.append({
                'angle': angle,
                'distance': random.uniform(5, 15),
                'speed': random.uniform(30, 50),
                'size': random.uniform(4, 8),
                'color': random.choice(colors),
                'opacity_offset': random.uniform(0, 0.3)
            })

    def update(self, delta_time):
        """Update fog cloud expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        # Update particle positions
        if self.timer >= 0:
            for particle in self.particles:
                particle['distance'] += particle['speed'] * delta_time

        return self.active

    def draw(self, surface):
        """Draw expanding fog cloud."""
        if not self.active or self.timer < 0:
            return

        progress = self.timer / self.duration

        # Overall fade out
        base_alpha = int(100 * (1.0 - progress))

        for particle in self.particles:
            # Calculate particle position
            px = self.center_x + math.cos(particle['angle']) * particle['distance']
            py = self.center_y + math.sin(particle['angle']) * particle['distance']

            # Calculate alpha with individual variation
            particle_alpha = int(base_alpha * (1.0 - particle['opacity_offset']))

            if particle_alpha > 0:
                # Draw soft fog particle
                fog_size = int(particle['size'])
                fog_surf = pygame.Surface((fog_size * 2, fog_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(fog_surf, (*particle['color'], particle_alpha),
                                 (fog_size, fog_size), fog_size)
                surface.blit(fog_surf, (int(px - fog_size), int(py - fog_size)))


class TileGasPocket:
    """
    Small swirling particle cluster at individual tile center.
    Shows gas affecting specific tile position.
    """
    def __init__(self, center_x, center_y, colors, delay=0, vapor_type='BROACHING'):
        self.center_x = center_x
        self.center_y = center_y
        self.colors = colors
        self.vapor_type = vapor_type
        self.timer = -delay
        self.duration = 0.9
        self.active = True
        self.swirl_phase = random.uniform(0, 2 * math.pi)

        # Create swirling particles
        self.particles = []
        particle_count = 10
        for i in range(particle_count):
            angle = (i / particle_count) * 2 * math.pi
            self.particles.append({
                'base_angle': angle,
                'radius': random.uniform(8, 16),
                'orbit_speed': random.uniform(2, 4),
                'size': random.uniform(2, 4),
                'color': random.choice(colors)
            })

    def update(self, delta_time):
        """Update gas pocket swirl."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        # Update swirl phase
        if self.timer >= 0:
            self.swirl_phase += delta_time * 3.0

        return self.active

    def draw(self, surface):
        """Draw swirling gas pocket."""
        if not self.active or self.timer < 0:
            return

        progress = self.timer / self.duration

        # Fade in then out
        if progress < 0.3:
            alpha_mult = progress / 0.3
        else:
            alpha_mult = 1.0 - ((progress - 0.3) / 0.7)

        base_alpha = int(180 * alpha_mult)

        for particle in self.particles:
            # Calculate orbiting position
            angle = particle['base_angle'] + self.swirl_phase * particle['orbit_speed']
            px = self.center_x + math.cos(angle) * particle['radius']
            py = self.center_y + math.sin(angle) * particle['radius']

            # Draw particle with glow
            particle_alpha = int(base_alpha)
            if particle_alpha > 0:
                glow_size = int(particle['size'] * 1.5)
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*particle['color'], particle_alpha // 2),
                                 (glow_size, glow_size), glow_size)
                surface.blit(glow_surf, (int(px - glow_size), int(py - glow_size)))

                pygame.draw.circle(surface, (*particle['color'], particle_alpha),
                                 (int(px), int(py)), int(particle['size']))


class VaporPulseWave:
    """
    Expanding pulse ring for vapor AOE effect.
    Enhanced to cover full 3x3 tile area with variable thickness.
    """
    def __init__(self, center_x, center_y, colors, delay=0, intensity='normal'):
        self.center_x = center_x
        self.center_y = center_y
        self.colors = colors
        self.timer = -delay
        self.duration = 0.8
        self.active = True
        self.intensity = intensity  # 'normal' or 'strong'
        self.thickness_phase = random.uniform(0, 2 * math.pi)

    def update(self, delta_time):
        """Update pulse wave."""
        if not self.active:
            return False

        self.timer += delta_time
        self.thickness_phase += delta_time * 6.0  # Pulsing thickness

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding pulse ring with variable thickness."""
        if not self.active or self.timer < 0:
            return

        progress = self.timer / self.duration

        # Expand from 10 to 96 pixels (covers full 1.5 tiles = 3x3 area)
        max_radius = 96 if self.intensity == 'strong' else 90
        radius = int(10 + (max_radius - 10) * progress)

        # Fade out as expanding
        alpha = int(150 * (1.0 - progress))

        if alpha > 0:
            # Choose color based on progress
            color_idx = int(progress * (len(self.colors) - 1))
            color = self.colors[min(color_idx, len(self.colors) - 1)]

            # Variable thickness that pulses
            base_width = 5 if self.intensity == 'strong' else 4
            thickness_variation = 1 + math.sin(self.thickness_phase) * 0.5
            ring_width = int(base_width * thickness_variation)

            # Draw ring
            pygame.draw.circle(surface, (*color, alpha),
                             (int(self.center_x), int(self.center_y)),
                             radius, ring_width)

            # Inner glow
            if progress < 0.5:
                glow_alpha = int(alpha * 0.4)
                pygame.draw.circle(surface, (*color, glow_alpha),
                                 (int(self.center_x), int(self.center_y)),
                                 radius - ring_width, 0)


class VaporWisp:
    """
    Small particle wisp that drifts outward with vapor effect.
    Enhanced with turbulence and swirling motion for gaseous appearance.
    """
    def __init__(self, center_x, center_y, angle, colors, speed_multiplier=1.0):
        self.x = center_x
        self.y = center_y
        self.start_x = center_x
        self.start_y = center_y
        self.angle = angle
        self.colors = colors
        self.speed = random.uniform(20, 40) * speed_multiplier
        self.size = random.uniform(2, 6)  # Increased from 2-4
        self.lifetime = random.uniform(0.6, 0.9)
        self.max_lifetime = self.lifetime
        self.active = True

        # Turbulence parameters
        self.turbulence_frequency = random.uniform(4, 8)
        self.turbulence_amplitude = random.uniform(10, 20)
        self.swirl_speed = random.uniform(-2, 2)  # Angular velocity
        self.time = 0

    def update(self, delta_time):
        """Update wisp movement with turbulence."""
        if not self.active:
            return False

        self.time += delta_time

        # Base outward drift
        base_x = self.start_x + math.cos(self.angle) * self.speed * self.time
        base_y = self.start_y + math.sin(self.angle) * self.speed * self.time

        # Add sinusoidal turbulence perpendicular to movement direction
        perp_angle = self.angle + math.pi / 2
        turbulence_offset = math.sin(self.time * self.turbulence_frequency) * self.turbulence_amplitude

        self.x = base_x + math.cos(perp_angle) * turbulence_offset
        self.y = base_y + math.sin(perp_angle) * turbulence_offset

        # Add swirl (rotate angle slightly)
        self.angle += self.swirl_speed * delta_time

        self.lifetime -= delta_time

        if self.lifetime <= 0:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw particle wisp."""
        if not self.active or self.lifetime <= 0:
            return

        alpha = int(200 * (self.lifetime / self.max_lifetime))

        if alpha > 0:
            # Choose color
            color = random.choice(self.colors)

            # Draw glow
            glow_size = int(self.size * 2)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, alpha // 3),
                             (glow_size, glow_size), glow_size)
            surface.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))

            # Draw core
            pygame.draw.circle(surface, (*color, alpha),
                             (int(self.x), int(self.y)), int(self.size))


class VaporAOETickAnimation:
    """
    AOE tick animation for HEINOUS VAPOR effects.
    Shows pulsing colored waves emanating from vapor across 3x3 area.

    Used for all vapor types:
    - Broaching (green): damage + cleanse
    - Safety (blue): healing + defense
    - Coolant (white): strong healing
    - Cutting (red): strong damage
    """

    def __init__(self, target_x, target_y, vapor_type='BROACHING', particle_emitter=None,
                 screen_shake_callback=None):
        """
        Initialize vapor AOE tick animation.

        Args:
            target_x: Center X coordinate (screen space)
            target_y: Center Y coordinate (screen space)
            vapor_type: Type of vapor (BROACHING, SAFETY, COOLANT, CUTTING)
        """
        self.target_x = target_x
        self.target_y = target_y
        self.vapor_type = vapor_type

        # Get colors for this vapor type
        self.colors = VaporParticleCloud.VAPOR_COLORS.get(vapor_type,
                                                          VaporParticleCloud.VAPOR_COLORS['BROACHING'])

        # Animation state
        self.timer = 0
        self.duration = 1.0
        self.active = True

        # Visual elements (gaseous only - no hard circles/rings)
        self.wisps = []
        self.fog_clouds = []
        self.tile_pockets = []

        # Determine intensity based on vapor type
        # Cutting and Broaching are damage types (more intense)
        # Coolant is strong heal (also intense)
        # Safety is gentle support (normal)
        if vapor_type in ['CUTTING', 'COOLANT']:
            self.intensity = 'strong'
            self.wisp_count = 50  # Increased from 20
            self.wisp_speed = 1.2
        else:
            self.intensity = 'normal'
            self.wisp_count = 40  # Increased from 15
            self.wisp_speed = 1.0

        # Calculate 3x3 tile grid positions (9 tiles)
        # Each tile is TILE_SIZE (64px), so tiles are at -64, 0, +64 from center
        tile_offsets = [
            (-TILE_SIZE, -TILE_SIZE), (0, -TILE_SIZE), (TILE_SIZE, -TILE_SIZE),
            (-TILE_SIZE, 0),          (0, 0),          (TILE_SIZE, 0),
            (-TILE_SIZE, TILE_SIZE),  (0, TILE_SIZE),  (TILE_SIZE, TILE_SIZE)
        ]

        # Create fog clouds at each tile position
        for i, (offset_x, offset_y) in enumerate(tile_offsets):
            tile_x = target_x + offset_x
            tile_y = target_y + offset_y
            # Stagger delays based on distance from center
            distance = math.sqrt(offset_x**2 + offset_y**2)
            delay = distance / 200.0  # Further tiles appear slightly later
            self.fog_clouds.append(
                VaporFogCloud(tile_x, tile_y, self.colors, delay)
            )

        # Create gas pockets at each tile position
        for i, (offset_x, offset_y) in enumerate(tile_offsets):
            tile_x = target_x + offset_x
            tile_y = target_y + offset_y
            distance = math.sqrt(offset_x**2 + offset_y**2)
            delay = distance / 250.0
            self.tile_pockets.append(
                TileGasPocket(tile_x, tile_y, self.colors, delay, vapor_type)
            )

        # Create wisps (more particles for gaseous effect)
        for i in range(self.wisp_count):
            angle = (i / self.wisp_count) * 2 * math.pi + random.uniform(-0.2, 0.2)
            self.wisps.append(
                VaporWisp(target_x, target_y, angle, self.colors, self.wisp_speed)
            )

    def update(self, delta_time):
        """Update animation."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update fog clouds
        for fog_cloud in self.fog_clouds:
            fog_cloud.update(delta_time)

        # Update tile gas pockets
        for pocket in self.tile_pockets:
            pocket.update(delta_time)

        # Update all wisps
        for wisp in self.wisps:
            wisp.update(delta_time)

        # End animation when duration exceeded
        if self.timer >= self.duration:
            self.active = False
            return False

        return True

    def draw(self, surface):
        """Draw the AOE tick animation - gaseous elements only."""
        if not self.active:
            return

        # Layer 1: Background fog clouds (volumetric base)
        for fog_cloud in self.fog_clouds:
            fog_cloud.draw(surface)

        # Layer 2: Tile gas pockets (tile-specific indicators)
        for pocket in self.tile_pockets:
            pocket.draw(surface)

        # Layer 3: Wisps (top layer - turbulent gas particles)
        for wisp in self.wisps:
            wisp.draw(surface)



# ============================================================================
# GAS MACHINIST BASIC ATTACK - PRESSURIZED GAS JET
# ============================================================================

class GasMachinistPressurizedAttack:
    """
    GAS MACHINIST basic attack animation - pressurized gas jet spray.
    Releases a multi-colored gas stream from the industrial cylinders.
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

        # Calculate attack vector
        self.dx = target_unit.x - attacker_unit.x
        self.dy = target_unit.y - attacker_unit.y
        distance = math.sqrt(self.dx * self.dx + self.dy * self.dy)

        if distance > 0:
            self.dx /= distance
            self.dy /= distance

        self.distance = distance

        # Animation state
        self.phase = "pressurize"  # pressurize → release → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.pressurize_duration = 0.12
        self.release_duration = 0.3
        self.impact_duration = 0.15

        # Gas colors from the three cylinders
        self.color_green = (34, 139, 34)    # #228b22 - Broaching Gas
        self.color_red = (220, 20, 60)      # #dc143c - Cutting Gas
        self.color_blue = (30, 144, 255)    # #1e90ff - Saft-E-Gas

    def _trigger_pressurize(self):
        """Phase 1: Pressurization - valves open."""
        # Small puffs at attacker as pressure builds
        for _ in range(8):
            angle = random.uniform(-math.pi/4, math.pi/4)
            vx = self.dx * 50 + math.cos(angle) * 30
            vy = self.dy * 50 + math.sin(angle) * 30

            # Mix of gas colors
            color = random.choice([self.color_green, self.color_red, self.color_blue])

            from .core import Particle
            particle = Particle(self.attacker.x, self.attacker.y, vx, vy, color,
                              size=2, lifetime=0.15)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_release(self):
        """Phase 2: Release pressurized gas jet."""
        # Create streaming gas particles along attack path
        for i in range(25):
            progress = i / 25
            x = self.attacker.x + self.dx * self.distance * progress
            y = self.attacker.y + self.dy * self.distance * progress

            # Spread perpendicular to jet direction
            perp_x = -self.dy
            perp_y = self.dx
            spread = random.uniform(-12, 12)

            vx = self.dx * 180 + perp_x * spread * 1.5
            vy = self.dy * 180 + perp_y * spread * 1.5

            # Stratified layers - different gases
            if i % 3 == 0:
                color = self.color_green
            elif i % 3 == 1:
                color = self.color_red
            else:
                color = self.color_blue

            from .core import Particle
            particle = Particle(x, y, vx, vy, color,
                              size=random.uniform(3, 5), lifetime=random.uniform(0.25, 0.35))
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Gas cloud impact."""
        # Mixed gas cloud explosion at target
        for _ in range(22):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 130)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Equal mix of all three gas colors
            color = random.choice([
                self.color_green,
                self.color_red,
                self.color_blue,
            ])

            from .core import Particle
            particle = Particle(self.target.x, self.target.y, vx, vy, color,
                              size=random.uniform(3, 6), lifetime=random.uniform(0.2, 0.35))
            particle.gravity = 50  # Slow settle
            self.particle_emitter.particles.append(particle)

        # Light impact
        self.target.shake_intensity = 7
        self.screen_shake(3, 0.15)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "pressurize":
            if self.timer == 0 or not hasattr(self, "_pressurize_triggered"):
                self._trigger_pressurize()
                self._pressurize_triggered = True

            if self.timer >= self.pressurize_duration:
                self.phase = "release"
                self.timer = 0
                self._trigger_release()

        elif self.phase == "release":
            if self.timer >= self.release_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw pressurized gas jet."""
        import pygame

        # Draw pressurizing effect (valve glow)
        if self.phase == "pressurize":
            progress = self.timer / self.pressurize_duration
            
            # Three colored glows (one for each cylinder)
            for i, color in enumerate([self.color_green, self.color_red, self.color_blue]):
                offset = (i - 1) * 8  # Spread glows left/right
                glow_x = self.attacker.x + offset
                glow_y = self.attacker.y
                glow_radius = int(10 * progress)

                if glow_radius > 2:
                    glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*color, int(120 * progress)),
                                     (glow_radius, glow_radius), glow_radius)
                    surface.blit(glow_surf, (int(glow_x - glow_radius),
                                            int(glow_y - glow_radius)))

        # Draw gas jet stream during release phase
        if self.phase == "release":
            progress = self.timer / self.release_duration
            
            # Draw streaming gas cone
            jet_length = self.distance * progress
            jet_width = 15

            # Calculate perpendicular vector
            perp_x = -self.dy
            perp_y = self.dx

            # Draw three layered gas streams (RGB)
            for layer_idx, color in enumerate([self.color_green, self.color_red, self.color_blue]):
                # Stagger layers slightly
                layer_offset = (layer_idx - 1) * 5
                
                # Create points for gas stream polygon
                num_segments = 8
                for seg in range(num_segments):
                    seg_progress = seg / num_segments
                    if seg_progress > progress:
                        break

                    pos_x = self.attacker.x + self.dx * jet_length * seg_progress
                    pos_y = self.attacker.y + self.dy * jet_length * seg_progress

                    # Width increases with distance
                    width = jet_width * (0.5 + seg_progress * 0.5)

                    # Draw gas puff at this segment
                    puff_radius = int(width)
                    if puff_radius > 2:
                        alpha = int(100 * (1.0 - seg_progress * 0.5))
                        puff_surf = pygame.Surface((puff_radius * 2, puff_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(puff_surf, (*color, alpha),
                                         (puff_radius, puff_radius), puff_radius)
                        
                        offset_x = perp_x * layer_offset
                        offset_y = perp_y * layer_offset
                        surface.blit(puff_surf, (int(pos_x - puff_radius + offset_x),
                                                int(pos_y - puff_radius + offset_y)))

        # Draw impact cloud flash
        if self.phase == "impact":
            progress = self.timer / self.impact_duration
            if progress < 0.6:
                flash_alpha = int(200 * (1.0 - progress / 0.6))
                flash_radius = int(30 * (1.0 + progress * 0.5))

                # Multi-colored gas cloud flash
                for i, color in enumerate([self.color_green, self.color_red, self.color_blue]):
                    angle_offset = (i / 3) * 2 * math.pi
                    offset_x = math.cos(angle_offset) * 8
                    offset_y = math.sin(angle_offset) * 8

                    flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(flash_surf, (*color, flash_alpha // 2),
                                     (flash_radius, flash_radius), flash_radius)
                    surface.blit(flash_surf, (int(self.target.x - flash_radius + offset_x),
                                             int(self.target.y - flash_radius + offset_y)))

