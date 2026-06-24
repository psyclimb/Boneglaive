#!/usr/bin/env python3
"""
MARROW CONDENSER Animation Classes
Skill animations for the MARROW CONDENSER unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE
from boneglaive.graphical.sound_helper import play_sound


# ============================================================================
# OSSIFY ANIMATION
# ============================================================================

class CompressingRings:
    """
    Expanding bone compression rings that pulse outward during Phase 1.
    Creates the visual of bone structure compressing inward.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay  # Negative timer for staggered start
        self.duration = 0.7
        self.active = True

        # Ring properties
        self.max_radius = 40
        self.ring_width = 3

    def update(self, delta_time):
        """Update ring expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding compression rings."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Draw multiple rings at different stages
        num_rings = 5
        for i in range(num_rings):
            # Stagger ring expansion
            ring_delay = i * 0.15
            ring_progress = min(1.0, max(0.0, (progress * 1.5 - ring_delay)))

            if ring_progress > 0:
                # Ring expands outward
                radius = int(10 + self.max_radius * ring_progress)

                # Fade out as ring expands
                alpha = int(180 * (1.0 - ring_progress) * (1.0 - progress * 0.3))

                if alpha > 0:
                    # Bone white color (240, 232, 216)
                    ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                    center = radius + 5

                    # Draw ring with bone white color
                    pygame.draw.circle(ring_surf, (240, 232, 216, alpha), (center, center), radius, self.ring_width)

                    # Inner glow (pale cream)
                    pygame.draw.circle(ring_surf, (224, 213, 197, alpha // 2), (center, center), radius - 2, 1)

                    surface.blit(ring_surf, (int(self.center_x - center), int(self.center_y - center)))


class OssifiedPlates:
    """
    Hexagonal bone armor plates that form around the unit during Phase 2.
    Creates a crystalline defensive structure.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.0
        self.active = True

        # Plate properties
        self.num_plates = 6
        self.plate_distance = 28
        self.rotation = 0

    def update(self, delta_time):
        """Update plate formation and rotation."""
        if not self.active:
            return False

        self.timer += delta_time

        # Slow rotation
        self.rotation += delta_time * 0.5

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw hexagonal bone plates."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fade in plates
        alpha = int(200 * min(1.0, progress * 2))

        if alpha > 0:
            for i in range(self.num_plates):
                angle = (i / self.num_plates) * 2 * math.pi + self.rotation

                # Position plate around unit
                px = self.center_x + math.cos(angle) * self.plate_distance
                py = self.center_y + math.sin(angle) * self.plate_distance

                # Draw hexagonal plate
                plate_size = 12
                points = []
                for j in range(6):
                    hex_angle = (j / 6) * 2 * math.pi + angle
                    hx = px + math.cos(hex_angle) * plate_size
                    hy = py + math.sin(hex_angle) * plate_size
                    points.append((int(hx), int(hy)))

                # Create surface for plate
                plate_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
                offset_points = [(int(x - px + 25), int(y - py + 25)) for x, y in points]

                # Draw bone plate (pale cream with darker outline)
                pygame.draw.polygon(plate_surf, (224, 213, 197, alpha), offset_points)
                pygame.draw.polygon(plate_surf, (139, 0, 0, alpha), offset_points, 2)  # Dark red outline

                # Add glowing red energy veins
                if progress > 0.5:
                    vein_alpha = int(alpha * 0.6 * math.sin(self.timer * 8))
                    if vein_alpha > 0:
                        # Draw cross pattern through hexagon
                        center_pt = (25, 25)
                        pygame.draw.line(plate_surf, (255, 0, 0, abs(vein_alpha)),
                                       offset_points[0], offset_points[3], 2)
                        pygame.draw.line(plate_surf, (255, 0, 0, abs(vein_alpha)),
                                       offset_points[1], offset_points[4], 2)
                        pygame.draw.line(plate_surf, (255, 0, 0, abs(vein_alpha)),
                                       offset_points[2], offset_points[5], 2)

                surface.blit(plate_surf, (int(px - 25), int(py - 25)))


class BoneShards:
    """
    Sharp ossified bone shards that orbit the unit during Phase 2-3.
    Represents the crystalline defensive structure.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.0
        self.active = True

        # Shard properties
        self.shards = []
        num_shards = 8
        for i in range(num_shards):
            angle = (i / num_shards) * 2 * math.pi
            self.shards.append({
                'angle': angle,
                'distance': 32,
                'size': random.randint(8, 14),
                'rotation': random.uniform(0, 2 * math.pi),
                'rotation_speed': random.uniform(-3, 3)
            })

    def update(self, delta_time):
        """Update shard orbits and rotations."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update each shard
        for shard in self.shards:
            shard['angle'] += delta_time * 1.5  # Orbit speed
            shard['rotation'] += delta_time * shard['rotation_speed']

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw orbiting bone shards."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(220 * min(1.0, progress * 2))

        if alpha > 0:
            for shard in self.shards:
                # Calculate shard position
                sx = self.center_x + math.cos(shard['angle']) * shard['distance']
                sy = self.center_y + math.sin(shard['angle']) * shard['distance']

                # Create diamond/shard shape
                half_size = shard['size'] / 2
                points = [
                    (sx, sy - half_size),  # Top
                    (sx + half_size * 0.5, sy),  # Right
                    (sx, sy + half_size),  # Bottom
                    (sx - half_size * 0.5, sy)   # Left
                ]

                # Rotate points
                rotated_points = []
                for px, py in points:
                    dx = px - sx
                    dy = py - sy
                    rx = dx * math.cos(shard['rotation']) - dy * math.sin(shard['rotation'])
                    ry = dx * math.sin(shard['rotation']) + dy * math.cos(shard['rotation'])
                    rotated_points.append((int(sx + rx), int(sy + ry)))

                # Draw shard (bright bone white)
                shard_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                offset_points = [(int(x - sx + 15), int(y - sy + 15)) for x, y in rotated_points]
                pygame.draw.polygon(shard_surf, (240, 232, 216, alpha), offset_points)
                pygame.draw.polygon(shard_surf, (208, 197, 181, alpha), offset_points, 1)

                surface.blit(shard_surf, (int(sx - 15), int(sy - 15)))


class OssifyAnimation:
    """
    Ossify skill animation for MARROW CONDENSER.
    Compresses bone structure into nearly impenetrable defensive state.

    Phases:
    1. Compression (0.7s) - Bone plates compress inward with expanding rings
    2. Ossification (1.0s) - Crystalline bone structure solidifies with hexagonal plates
    3. Hardened (0.8s) - Final defensive shell with pulsing aura
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Ossify animation.

        Args:
            caster_unit: The MARROW CONDENSER casting Ossify
            camera: Camera for coordinate conversion
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Convert caster position to screen coords
        self.center_x, self.center_y = camera.grid_to_screen(caster_unit.grid_x, caster_unit.grid_y, centered=True)

        # Animation state
        self.phase = "compression"  # compression -> ossification -> hardened
        self.timer = 0
        self.active = True

        # Sub-effects
        self.rings = []
        self.plates = None
        self.shards = None

        # Hardened state glow
        self.glow_intensity = 0
        self.pulse_phase = 0

        # Start Phase 1
        self._start_compression()

    def _start_compression(self):
        """Phase 1: Compression - Bone structure visibly compresses."""
        self.phase = "compression"
        self.timer = 0

        # Play compression sound
        play_sound("ossify_compression")

        # Create staggered compression rings
        for i in range(5):
            self.rings.append(CompressingRings(self.center_x, self.center_y, delay=i * 0.1))

        # Emit converging bone particles
        if self.particle_emitter:
            for _ in range(30):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(40, 60)
                px = self.center_x + math.cos(angle) * distance
                py = self.center_y + math.sin(angle) * distance

                # Velocity toward center
                speed = random.uniform(80, 120)
                vx = -math.cos(angle) * speed
                vy = -math.sin(angle) * speed

                self.particle_emitter.emit_trail(px, py, (240, 232, 216), count=1)

        # Medium screen shake for compression
        self.screen_shake_callback(5, 0.6)

    def _start_ossification(self):
        """Phase 2: Ossification - Crystalline bone structure forms."""
        self.phase = "ossification"
        self.timer = 0

        # Play crystallization sound
        play_sound("ossify_crystallize")

        # Create hexagonal plates
        self.plates = OssifiedPlates(self.center_x, self.center_y)

        # Create orbiting shards
        self.shards = BoneShards(self.center_x, self.center_y)

        # Emit burst of bone fragments
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.center_x, self.center_y, (224, 213, 197), count=25)

        # Light screen shake for crystallization
        self.screen_shake_callback(2, 0.8)

    def _start_hardened(self):
        """Phase 3: Hardened - Final defensive shell with intensity glow."""
        self.phase = "hardened"
        self.timer = 0

        # Play hardening sound
        play_sound("ossify_harden")

        # Brief white flash at hardening completion (removed — screen flashes reserved for Rail Genesis)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update pulse for hardened glow
        self.pulse_phase += delta_time * 4

        # Phase transitions
        if self.phase == "compression" and self.timer >= 0.7:
            self._start_ossification()
        elif self.phase == "ossification" and self.timer >= 1.0:
            self._start_hardened()
        elif self.phase == "hardened" and self.timer >= 0.8:
            self.active = False  # Animation complete

        # Update glow intensity
        if self.phase == "hardened":
            # Fade in, then fade out
            if self.timer < 0.4:
                self.glow_intensity = self.timer / 0.4
            else:
                self.glow_intensity = 1.0 - ((self.timer - 0.4) / 0.4)

        # Update sub-effects
        self.rings = [r for r in self.rings if r.update(delta_time)]

        if self.plates:
            self.plates.update(delta_time)

        if self.shards:
            self.shards.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw compression rings (Phase 1)
        for ring in self.rings:
            ring.draw(surface)

        # Draw ossified plates (Phase 2)
        if self.plates:
            self.plates.draw(surface)

        # Draw bone shards (Phase 2-3)
        if self.shards:
            self.shards.draw(surface)

        # Draw hardened state glow (Phase 3)
        if self.phase == "hardened" and self.glow_intensity > 0:
            # Pulsing defensive aura
            base_radius = 35
            pulse = math.sin(self.pulse_phase) * 5
            radius = int(base_radius + pulse)
            alpha = int(self.glow_intensity * 120)

            if alpha > 0:
                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

                # Outer glow (bright bone white)
                pygame.draw.circle(glow_surf, (240, 232, 216, alpha // 2), (radius, radius), radius)

                # Inner glow (pale cream with red energy)
                inner_radius = int(radius * 0.7)
                pygame.draw.circle(glow_surf, (224, 213, 197, alpha), (radius, radius), inner_radius)

                # Red energy core
                core_radius = int(radius * 0.4)
                core_alpha = int(alpha * 0.3)
                pygame.draw.circle(glow_surf, (255, 0, 0, core_alpha), (radius, radius), core_radius)

                surface.blit(glow_surf, (int(self.center_x - radius), int(self.center_y - radius)))


# ============================================================================
# BONE TITHE ANIMATION
# ============================================================================

class ExtractionTendrils:
    """
    Jagged bone tendrils that shoot outward from the caster in 8 directions.
    Represents the extraction force reaching out to drain marrow from adjacent enemies.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.4
        self.active = True

        # 8 directions (cardinal + diagonal)
        self.directions = [
            (0, -1),   # North
            (1, -1),   # Northeast
            (1, 0),    # East
            (1, 1),    # Southeast
            (0, 1),    # South
            (-1, 1),   # Southwest
            (-1, 0),   # West
            (-1, -1)   # Northwest
        ]

        # Tendril properties
        self.max_length = TILE_SIZE  # Reach 1 tile distance
        self.pulse_phase = 0

    def update(self, delta_time):
        """Update tendril extension."""
        if not self.active:
            return False

        self.timer += delta_time
        self.pulse_phase += delta_time * 10  # Red vein pulsing

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw bone tendrils reaching outward."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Ease-out for tendril extension
        extension = progress * progress * self.max_length

        for dx, dy in self.directions:
            # End point of tendril
            end_x = self.center_x + dx * extension
            end_y = self.center_y + dy * extension

            # Fade out tendrils toward end of duration
            alpha = int(220 * (1.0 - progress * 0.5))

            if alpha > 0:
                # Draw jagged bone tendril (pale cream with red vein)
                # Main tendril line (pale bone)
                pygame.draw.line(surface, (224, 213, 197, alpha),
                               (int(self.center_x), int(self.center_y)),
                               (int(end_x), int(end_y)), 4)

                # Pulsing red vein through center
                vein_alpha = int(alpha * 0.6 * (0.5 + 0.5 * math.sin(self.pulse_phase)))
                if vein_alpha > 0:
                    pygame.draw.line(surface, (255, 0, 0, vein_alpha),
                                   (int(self.center_x), int(self.center_y)),
                                   (int(end_x), int(end_y)), 2)

                # Jagged edges (small perpendicular lines)
                if extension > 10:
                    num_jags = 3
                    for i in range(1, num_jags + 1):
                        t = i / (num_jags + 1)
                        jag_x = self.center_x + dx * extension * t
                        jag_y = self.center_y + dy * extension * t

                        # Perpendicular direction
                        perp_dx = -dy
                        perp_dy = dx

                        # Alternating jags
                        jag_size = 4 if i % 2 == 0 else -4
                        jag_end_x = jag_x + perp_dx * jag_size
                        jag_end_y = jag_y + perp_dy * jag_size

                        pygame.draw.line(surface, (208, 197, 181, alpha // 2),
                                       (int(jag_x), int(jag_y)),
                                       (int(jag_end_x), int(jag_end_y)), 2)


class MarrowParticle:
    """
    Individual marrow particle being extracted from an enemy to the caster.
    Follows a curved path with acceleration toward the target.
    """
    def __init__(self, start_x, start_y, end_x, end_y, is_bone_fragment=False):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.timer = 0
        self.duration = random.uniform(0.6, 0.9)  # Variable travel time
        self.active = True

        # Particle properties
        self.is_bone_fragment = is_bone_fragment
        if is_bone_fragment:
            self.color = (224, 213, 197)  # Pale bone
            self.size = random.uniform(2, 4)
        else:
            self.color = (139, 0, 0)  # Dark blood red
            self.size = random.uniform(3, 6)

        # Curved path control point (creates arc)
        mid_x = (start_x + end_x) / 2 + random.uniform(-30, 30)
        mid_y = (start_y + end_y) / 2 + random.uniform(-30, 30)
        self.control_x = mid_x
        self.control_y = mid_y

    def update(self, delta_time):
        """Update particle movement along curved path."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def get_position(self):
        """Calculate current position along bezier curve with acceleration."""
        # Progress with acceleration (ease-in, particles speed up as they approach target)
        raw_progress = min(1.0, self.timer / self.duration)
        progress = raw_progress * raw_progress  # Quadratic acceleration

        # Quadratic bezier curve
        t = progress
        x = (1-t)**2 * self.start_x + 2*(1-t)*t * self.control_x + t**2 * self.end_x
        y = (1-t)**2 * self.start_y + 2*(1-t)*t * self.control_y + t**2 * self.end_y

        return x, y, raw_progress

    def draw(self, surface):
        """Draw marrow particle."""
        if not self.active:
            return

        x, y, progress = self.get_position()

        # Fade in at start, bright in middle, fade at end
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))
        else:
            alpha = 255

        if alpha > 0:
            particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*self.color, alpha),
                             (int(self.size), int(self.size)), int(self.size))

            # Add glow for blood particles
            if not self.is_bone_fragment:
                glow_size = self.size + 2
                pygame.draw.circle(particle_surf, (255, 0, 0, alpha // 3),
                                 (int(self.size), int(self.size)), int(glow_size))

            surface.blit(particle_surf, (int(x - self.size), int(y - self.size)))


class AbsorptionBurst:
    """
    Implosion effect when marrow particles converge at the caster.
    Creates expanding empowerment aura and displays HP gain.
    """
    def __init__(self, center_x, center_y, hp_gained):
        self.center_x = center_x
        self.center_y = center_y
        self.hp_gained = hp_gained
        self.timer = 0
        self.duration = 0.9
        self.active = True

        # Animation phases
        self.phase = "implosion"  # implosion -> flash -> aura

        # Visual properties
        self.implosion_particles = []
        self.aura_radius = 0
        self.flash_alpha = 0

        # Create implosion particles (converging inward, then exploding outward)
        for i in range(30):
            angle = (i / 30) * 2 * math.pi
            distance = random.uniform(20, 40)
            self.implosion_particles.append({
                'angle': angle,
                'start_distance': distance,
                'lifetime': 0,
                'size': random.uniform(2, 5),
                'color': random.choice([(240, 232, 216), (255, 0, 0), (224, 213, 197)])
            })

    def update(self, delta_time):
        """Update absorption burst effects."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particle lifetimes
        for particle in self.implosion_particles:
            particle['lifetime'] += delta_time

        # Phase transitions
        if self.phase == "implosion" and self.timer >= 0.2:
            self.phase = "flash"
            self.timer = 0
        elif self.phase == "flash" and self.timer >= 0.15:
            self.phase = "aura"
            self.timer = 0
        elif self.phase == "aura" and self.timer >= 0.55:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw absorption burst effects."""
        if not self.active:
            return

        if self.phase == "implosion":
            # Particles collapse inward (0.2s)
            progress = min(1.0, self.timer / 0.2)
            for particle in self.implosion_particles:
                # Collapse toward center
                distance = particle['start_distance'] * (1.0 - progress)
                px = self.center_x + math.cos(particle['angle']) * distance
                py = self.center_y + math.sin(particle['angle']) * distance

                alpha = int(255 * (1.0 - progress * 0.3))
                if alpha > 0:
                    size = int(particle['size'])
                    particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, (*particle['color'], alpha),
                                     (size, size), size)
                    surface.blit(particle_surf, (int(px - size), int(py - size)))

        elif self.phase == "flash":
            # Bright flash at center (0.15s)
            progress = self.timer / 0.15
            if progress < 0.5:
                self.flash_alpha = int(200 * (progress / 0.5))
            else:
                self.flash_alpha = int(200 * (1.0 - (progress - 0.5) / 0.5))

            if self.flash_alpha > 0:
                # White flash transitioning to red
                if progress < 0.3:
                    flash_color = (255, 255, 255)  # White
                else:
                    flash_color = (255, 0, 0)  # Red

                flash_size = 50
                flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*flash_color, self.flash_alpha),
                                 (flash_size, flash_size), flash_size)
                surface.blit(flash_surf, (int(self.center_x - flash_size), int(self.center_y - flash_size)))

        elif self.phase == "aura":
            # Expanding empowerment aura (0.55s)
            progress = self.timer / 0.55
            self.aura_radius = int(25 + 15 * progress)

            # Pulsing aura (bone white with red core)
            pulse = 0.8 + 0.2 * math.sin(self.timer * 10)
            alpha = int(150 * (1.0 - progress) * pulse)

            if alpha > 0:
                # Outer bone white glow
                aura_surf = pygame.Surface((self.aura_radius * 2, self.aura_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (240, 232, 216, alpha // 2),
                                 (self.aura_radius, self.aura_radius), self.aura_radius)

                # Inner red energy core
                core_radius = int(self.aura_radius * 0.6)
                pygame.draw.circle(aura_surf, (255, 0, 0, alpha),
                                 (self.aura_radius, self.aura_radius), core_radius)

                surface.blit(aura_surf, (int(self.center_x - self.aura_radius), int(self.center_y - self.aura_radius)))

            # HP gain number (floats upward)
            if self.hp_gained > 0:
                # Float upward over duration
                text_y = self.center_y - 40 - (progress * 20)
                alpha_text = int(255 * (1.0 - progress))

                if alpha_text > 0:
                    font = pygame.font.Font(None, 32)
                    hp_text = f"+{self.hp_gained}"
                    text_surf = font.render(hp_text, True, (100, 255, 100))
                    text_surf.set_alpha(alpha_text)
                    text_rect = text_surf.get_rect(center=(int(self.center_x), int(text_y)))
                    surface.blit(text_surf, text_rect)


class BoneTitheAnimation:
    """
    Bone Tithe skill animation for MARROW CONDENSER.
    Extracts bone marrow from enemies in 5x5 beam pattern, dealing damage
    and permanently increasing the caster's HP.

    Phases:
    1. Extraction (0.4s) - Bone tendrils shoot outward in 8 directions
    2. Draining (0.9s) - Marrow particles stream from enemies to caster
    3. Absorption (0.9s) - Marrow absorbed with empowerment burst
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Bone Tithe animation.

        Args:
            caster_unit: The MARROW CONDENSER casting Bone Tithe
            units_list: All units (to detect adjacent enemies)
            camera: Camera for coordinate conversion
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.units_list = units_list if units_list else []

        # Convert caster position to screen coords
        self.center_x, self.center_y = camera.grid_to_screen(caster_unit.grid_x, caster_unit.grid_y, centered=True)

        # Animation state
        self.phase = "extraction"  # extraction -> draining -> absorption
        self.timer = 0
        self.active = True

        # Detect all enemies in 5x5 beam pattern
        self.adjacent_enemies = []
        for dy in range(-2, 3):  # 5x5 area
            for dx in range(-2, 3):  # 5x5 area
                if dy == 0 and dx == 0:
                    continue  # Skip caster position

                grid_y = caster_unit.grid_y + dy
                grid_x = caster_unit.grid_x + dx

                # Find enemy at this position
                for unit in self.units_list:
                    if (unit.grid_y == grid_y and unit.grid_x == grid_x and
                        hasattr(unit, 'player') and unit.player != caster_unit.player):
                        screen_x, screen_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
                        self.adjacent_enemies.append({
                            'unit': unit,
                            'screen_x': screen_x,
                            'screen_y': screen_y,
                            'angle': math.atan2(dy, dx),
                            'flashed': False
                        })
                        break

        # Calculate HP gained (1 per enemy, or 2 if upgraded)
        # Note: Actual HP gain happens in skill logic, this is just for display
        self.hp_gained = len(self.adjacent_enemies)

        # Sub-effects
        self.tendrils = None
        self.marrow_particles = []
        self.absorption_burst = None
        self.extraction_beams = []  # Thin lines connecting enemies to caster during drain

        # Start Phase 1
        self._start_extraction()

    def _start_extraction(self):
        """Phase 1: Extraction - Bone tendrils shoot outward."""
        self.phase = "extraction"
        self.timer = 0

        # Play extraction sound
        play_sound("bone_tithe_extraction")

        # Create extraction tendrils
        self.tendrils = ExtractionTendrils(self.center_x, self.center_y)

        # Dark red pulse particles (enhanced for 5x5 area)
        if self.particle_emitter:
            for _ in range(30):  # More particles for larger area
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(5, 25)  # Larger spread
                px = self.center_x + math.cos(angle) * distance
                py = self.center_y + math.sin(angle) * distance
                # Use particle emitter for dark red pulse
                self.particle_emitter.emit_burst(px, py, (139, 0, 0), count=4)  # More per burst

        # Light screen shake for extraction force
        self.screen_shake_callback(3, 0.3)

    def _start_draining(self):
        """Phase 2: Draining - Marrow particles stream from enemies."""
        self.phase = "draining"
        self.timer = 0

        # Play draining sound
        play_sound("bone_tithe_drain")

        # Create marrow particles for each enemy
        for enemy_data in self.adjacent_enemies:
            enemy_x = enemy_data['screen_x']
            enemy_y = enemy_data['screen_y']

            # 20-30 particles per enemy (mix of blood and bone) for enhanced 5x5 effect
            num_particles = random.randint(20, 30)
            for i in range(num_particles):
                is_bone = (i % 4 == 0)  # 25% bone fragments, 75% blood
                particle = MarrowParticle(enemy_x, enemy_y, self.center_x, self.center_y, is_bone_fragment=is_bone)
                # Stagger particle creation
                particle.timer = -random.uniform(0, 0.3)
                self.marrow_particles.append(particle)

            # Create extraction beam data
            self.extraction_beams.append({
                'start_x': enemy_x,
                'start_y': enemy_y,
                'intensity': 0
            })

    def _start_absorption(self):
        """Phase 3: Absorption - Marrow absorbed with empowerment."""
        self.phase = "absorption"
        self.timer = 0

        # Play absorption sound
        play_sound("bone_tithe_absorb")

        # Create absorption burst
        self.absorption_burst = AbsorptionBurst(self.center_x, self.center_y, self.hp_gained)

        # Medium-heavy screen shake for absorption
        self.screen_shake_callback(6, 0.4)

        # Red flash during absorption (removed — screen flashes reserved for Rail Genesis)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "extraction" and self.timer >= 0.4:
            self._start_draining()
        elif self.phase == "draining" and self.timer >= 0.9:
            self._start_absorption()
        elif self.phase == "absorption" and self.timer >= 0.9:
            self.active = False  # Animation complete

        # Update sub-effects
        if self.tendrils:
            self.tendrils.update(delta_time)

        self.marrow_particles = [p for p in self.marrow_particles if p.update(delta_time)]

        if self.absorption_burst:
            self.absorption_burst.update(delta_time)

        # Flash enemies during draining phase
        if self.phase == "draining":
            for enemy_data in self.adjacent_enemies:
                if not enemy_data['flashed'] and self.timer > 0.2:
                    # Flash enemy red (damage indicator)
                    enemy_data['flashed'] = True
                    # Note: Enemy flash would be handled by unit shake/flash in actual game

            # Update extraction beam intensity (pulse effect)
            for beam in self.extraction_beams:
                beam['intensity'] = 0.6 + 0.4 * math.sin(self.timer * 8)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw extraction tendrils (Phase 1)
        if self.tendrils:
            self.tendrils.draw(surface)

        # Draw extraction beams (Phase 2)
        if self.phase == "draining" and self.extraction_beams:
            for beam in self.extraction_beams:
                alpha = int(120 * beam['intensity'])
                if alpha > 0:
                    # Thin red beam from enemy to caster
                    beam_surf = pygame.Surface((abs(int(beam['start_x'] - self.center_x)) + 10,
                                               abs(int(beam['start_y'] - self.center_y)) + 10), pygame.SRCALPHA)
                    # Draw on temporary surface, then blit
                    start = (int(beam['start_x']), int(beam['start_y']))
                    end = (int(self.center_x), int(self.center_y))
                    pygame.draw.line(surface, (255, 0, 0, alpha), start, end, 2)

        # Draw marrow particles (Phase 2)
        for particle in self.marrow_particles:
            particle.draw(surface)

        # Draw absorption burst (Phase 3)
        if self.absorption_burst:
            self.absorption_burst.draw(surface)


class BoneTitheDeathHealAnimation:
    """
    Death effect animation for upgraded Bone Tithe.
    When MARROW CONDENSER dies, bone chunks fly to allies to heal them.

    Phases:
    1. Explosion (0.3s) - Body bursts, bone fragments scatter
    2. Distribution (0.8s) - Bone chunks fly to each ally
    3. Absorption (0.5s) - Allies glow with nourishment
    """

    def __init__(self, death_pos, affected_allies, heal_amount,
                 particle_emitter, screen_shake_callback, screen_flash_callback,
                 camera, **kwargs):
        """
        Args:
            death_pos: (grid_y, grid_x) where MC died
            affected_allies: List of dicts with 'unit' and 'heal' amount
            heal_amount: Total HP that was distributed
        """
        self.death_pos = death_pos
        self.affected_allies = affected_allies
        self.heal_amount = heal_amount
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Convert death position to screen coords
        self.death_x, self.death_y = camera.grid_to_screen(death_pos[1], death_pos[0], centered=True)

        # Animation state
        self.phase = "explosion"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.bone_chunks = []
        self.ally_glows = {}

        self._start_explosion()

    def _start_explosion(self):
        """Phase 1: Explosion - GORE ERUPTION - body violently bursts."""
        self.phase = "explosion"
        self.timer = 0

        # Play explosion sound
        play_sound("bone_tithe_death_explosion")

        # SVG-accurate MARROW CONDENSER colors
        MUSCLE_RED = (200, 80, 80)      # #c85050
        DARK_BLOOD = (139, 0, 0)        # #8b0000
        BLOOD_RED = (160, 48, 48)       # #a03030
        BONE_WHITE = (240, 232, 216)    # #f0e8d8
        BONE_ACCENT = (224, 213, 197)   # #e0d5c5
        EYE_GLOW = (255, 0, 0)          # #ff0000

        # Crimson screen flash (removed — screen flashes reserved for Rail Genesis)

        if self.particle_emitter:
            # 1. VISCERAL BLOOD EXPLOSION - massive central burst
            self.particle_emitter.emit_blood_explosion(self.death_x, self.death_y, count=120)

            # 2. CHUNKY MARROW FRAGMENTS - large red muscle chunks with heavy gravity
            for _ in range(60):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(5, 25)
                px = self.death_x + math.cos(angle) * distance
                py = self.death_y + math.sin(angle) * distance
                # Alternate muscle colors for depth
                color = MUSCLE_RED if random.random() > 0.5 else BLOOD_RED
                self.particle_emitter.emit_burst(px, py, color, count=4)

            # 3. BONE SHARDS - sharp white fragments spinning wildly
            for _ in range(40):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(10, 35)
                px = self.death_x + math.cos(angle) * distance
                py = self.death_y + math.sin(angle) * distance
                # Mix bone colors
                color = BONE_WHITE if random.random() > 0.3 else BONE_ACCENT
                self.particle_emitter.emit_burst(px, py, color, count=3)

            # 4. DARK BLOOD MIST - ring of darker blood spray
            for i in range(20):
                angle = (i / 20) * 2 * math.pi
                distance = 30
                px = self.death_x + math.cos(angle) * distance
                py = self.death_y + math.sin(angle) * distance
                self.particle_emitter.emit_burst(px, py, DARK_BLOOD, count=5)

        # INTENSE screen shake
        self.screen_shake_callback(10, 0.5)

    def _start_distribution(self):
        """Phase 2: Distribution - TUMBLING VISCERA - chunks fly to allies."""
        self.phase = "distribution"
        self.timer = 0

        # Play distribution sound
        play_sound("bone_tithe_death_distribute")

        # Create diverse projectiles for each ally
        for ally_data in self.affected_allies:
            ally_unit = ally_data['unit']
            # Handle both game units (x, y) and animated units (grid_x, grid_y)
            if hasattr(ally_unit, 'grid_x'):
                target_x, target_y = self.camera.grid_to_screen(ally_unit.grid_x, ally_unit.grid_y, centered=True)
            else:
                # Game unit uses x, y (note: these are in (x, y) format already)
                target_x, target_y = self.camera.grid_to_screen(ally_unit.x, ally_unit.y, centered=True)

            # 6-10 chunks per ally with varied types
            num_chunks = random.randint(6, 10)
            for i in range(num_chunks):
                delay = i * 0.08  # Slightly faster release

                # Mix of projectile types for variety
                rand = random.random()
                if rand < 0.3:  # 30% marrow globs
                    chunk = MarrowGlobProjectile(
                        self.death_x, self.death_y,
                        target_x, target_y,
                        self.particle_emitter,
                        delay=delay
                    )
                elif rand < 0.5:  # 20% bone splinters
                    chunk = BoneSplinterProjectile(
                        self.death_x, self.death_y,
                        target_x, target_y,
                        self.particle_emitter,
                        delay=delay
                    )
                else:  # 50% enhanced bone chunks
                    chunk_type = random.choice(['rib', 'cartilage', 'vertebra', 'muscle'])
                    chunk = BoneChunkProjectile(
                        self.death_x, self.death_y,
                        target_x, target_y,
                        chunk_type,
                        self.particle_emitter,  # Pass for blood trails
                        delay=delay
                    )
                self.bone_chunks.append(chunk)

    def _start_absorption(self):
        """Phase 3: Absorption - NOURISHING IMPACT - allies absorb marrow energy."""
        self.phase = "absorption"
        self.timer = 0

        # Play absorption sound
        play_sound("bone_tithe_death_heal")

        # Initialize glow and impact effects for each ally
        for ally_data in self.affected_allies:
            ally_unit = ally_data['unit']

            # Handle both game units (x, y) and animated units (grid_x, grid_y)
            if hasattr(ally_unit, 'grid_x'):
                ally_x, ally_y = self.camera.grid_to_screen(ally_unit.grid_x, ally_unit.grid_y, centered=True)
            else:
                ally_x, ally_y = self.camera.grid_to_screen(ally_unit.x, ally_unit.y, centered=True)

            self.ally_glows[id(ally_unit)] = {
                'intensity': 0,
                'heal': ally_data['heal']
            }

            # Impact burst - crimson energy explosion when chunks hit
            self.particle_emitter.emit_burst(
                ally_x, ally_y,
                color=(200, 80, 80),  # MUSCLE_RED
                count=25
            )

            # Secondary dark blood ring
            self.particle_emitter.emit_burst(
                ally_x, ally_y,
                color=(139, 0, 0),  # DARK_BLOOD
                count=15
            )

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions (extended for gore effects)
        if self.phase == "explosion" and self.timer >= 0.6:
            self._start_distribution()
        elif self.phase == "distribution" and self.timer >= 1.2:
            self._start_absorption()
        elif self.phase == "absorption" and self.timer >= 0.8:
            self.active = False

        # Update sub-effects
        self.bone_chunks = [c for c in self.bone_chunks if c.update(delta_time)]

        # Update ally glow intensities
        if self.phase == "absorption":
            progress = self.timer / 0.5
            for glow_data in self.ally_glows.values():
                glow_data['intensity'] = math.sin(progress * math.pi)

        return self.active

    def draw(self, surface):
        """Draw animation effects."""
        if not self.active:
            return

        # Draw explosion burst (phase 1) - GORE VISUAL
        if self.phase == "explosion":
            progress = self.timer / 0.6  # Updated timing

            # Blood/muscle burst wave (expanding red circle)
            burst_radius = int(50 * progress)
            alpha = int(180 * (1.0 - progress))
            if alpha > 0:
                burst_surf = pygame.Surface((burst_radius * 2, burst_radius * 2), pygame.SRCALPHA)
                # Dark blood red burst
                pygame.draw.circle(burst_surf, (139, 0, 0, alpha),
                                 (burst_radius, burst_radius), burst_radius)
                # Lighter red core
                inner_radius = int(burst_radius * 0.6)
                pygame.draw.circle(burst_surf, (200, 80, 80, int(alpha * 0.7)),
                                 (burst_radius, burst_radius), inner_radius)
                surface.blit(burst_surf, (int(self.death_x - burst_radius),
                                         int(self.death_y - burst_radius)))

            # Rib cage silhouette (early in explosion, then fragments)
            if progress < 0.5:
                rib_alpha = int(255 * (1.0 - progress * 2))
                if rib_alpha > 20:
                    rib_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                    center = 30
                    # Draw simplified rib cage
                    for i in range(7):
                        y_offset = 10 + i * 6
                        curve = (3 - abs(i - 3)) * 3
                        pygame.draw.arc(rib_surf, (240, 232, 216, rib_alpha),
                                      (center - 15 - curve, y_offset, 30 + curve * 2, 10),
                                      0, 3.14, 2)
                    # Sternum
                    pygame.draw.line(rib_surf, (240, 232, 216, rib_alpha),
                                   (center, 10), (center, 50), 3)
                    surface.blit(rib_surf, (int(self.death_x - 30), int(self.death_y - 30)))

        # Draw bone chunks (phase 2)
        for chunk in self.bone_chunks:
            chunk.draw(surface)

        # Draw ally glows (phase 3) - CRIMSON ENERGY ABSORPTION
        if self.phase == "absorption":
            for ally_data in self.affected_allies:
                ally_unit = ally_data['unit']
                glow_id = id(ally_unit)
                if glow_id in self.ally_glows:
                    intensity = self.ally_glows[glow_id]['intensity']
                    heal_amount = self.ally_glows[glow_id]['heal']

                    # Handle both game units (x, y) and animated units (grid_x, grid_y)
                    if hasattr(ally_unit, 'grid_x'):
                        ally_x, ally_y = self.camera.grid_to_screen(
                            ally_unit.grid_x, ally_unit.grid_y, centered=True
                        )
                    else:
                        ally_x, ally_y = self.camera.grid_to_screen(
                            ally_unit.x, ally_unit.y, centered=True
                        )

                    # Red marrow energy glow (not green healing - this is absorbed bone matter)
                    alpha = int(180 * intensity)
                    if alpha > 0:
                        # Outer dark blood aura
                        outer_radius = int(35 + math.sin(self.timer * 8) * 5)
                        outer_surf = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(outer_surf, (139, 0, 0, int(alpha * 0.6)),
                                         (outer_radius, outer_radius), outer_radius)
                        surface.blit(outer_surf, (int(ally_x - outer_radius),
                                                int(ally_y - outer_radius)))

                        # Middle muscle red glow
                        mid_radius = int(25 + math.sin(self.timer * 10) * 4)
                        mid_surf = pygame.Surface((mid_radius * 2, mid_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(mid_surf, (200, 80, 80, int(alpha * 0.8)),
                                         (mid_radius, mid_radius), mid_radius)
                        surface.blit(mid_surf, (int(ally_x - mid_radius),
                                              int(ally_y - mid_radius)))

                        # Bright red core pulse
                        core_radius = int(15 + math.sin(self.timer * 12) * 3)
                        core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(core_surf, (255, 100, 100, alpha),
                                         (core_radius, core_radius), core_radius)
                        surface.blit(core_surf, (int(ally_x - core_radius),
                                               int(ally_y - core_radius)))

                    # Healing number with red energy color
                    if intensity > 0.3:
                        font = pygame.font.Font(None, 32)
                        text = f"+{heal_amount}"
                        # Red healing text (bone marrow nourishment, not green heal)
                        text_surf = font.render(text, True, (255, 120, 120))
                        text_surf.set_alpha(int(255 * intensity))
                        # Float upward slightly
                        y_offset = int(-30 - (1.0 - intensity) * 15)
                        text_rect = text_surf.get_rect(center=(int(ally_x), int(ally_y + y_offset)))
                        surface.blit(text_surf, text_rect)


class BoneChunkProjectile:
    """Individual bone chunk flying to an ally - enhanced with blood trails."""
    def __init__(self, start_x, start_y, end_x, end_y, chunk_type, particle_emitter=None, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.chunk_type = chunk_type
        self.particle_emitter = particle_emitter
        self.timer = -delay
        self.duration = 0.6
        self.active = True

        # Curved path control
        mid_x = (start_x + end_x) / 2 + random.uniform(-20, 20)
        mid_y = (start_y + end_y) / 2 - random.uniform(20, 40)  # Arc upward
        self.control_x = mid_x
        self.control_y = mid_y

        # Visual - larger, chunkier
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-600, 600)  # Faster tumbling
        self.size = random.randint(8, 18)  # Larger chunks
        self.wobble = random.uniform(0, math.pi * 2)

        # Colors - SVG-accurate
        self.bone_color = (240, 232, 216)  # #f0e8d8
        self.blood_color = (139, 0, 0)     # #8b0000
        self.muscle_color = (200, 80, 80)  # #c85050

    def update(self, delta_time):
        if not self.active:
            return False

        self.timer += delta_time
        self.rotation += self.rotation_speed * delta_time
        self.wobble += delta_time * 4  # Wobble phase

        # Emit blood trail
        if self.particle_emitter and self.timer > 0:
            x, y, _ = self.get_position()
            # More blood for muscle/cartilage chunks
            trail_count = 2 if self.chunk_type in ['cartilage', 'muscle'] else 1
            if random.random() > 0.3:  # 70% chance
                self.particle_emitter.emit_trail(x, y, self.blood_color, count=trail_count)

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def get_position(self):
        """Calculate position along bezier curve."""
        if self.timer < 0:
            return self.start_x, self.start_y, 0

        raw_progress = min(1.0, self.timer / self.duration)
        progress = raw_progress * raw_progress  # Acceleration

        t = progress
        x = (1-t)**2 * self.start_x + 2*(1-t)*t * self.control_x + t**2 * self.end_x
        y = (1-t)**2 * self.start_y + 2*(1-t)*t * self.control_y + t**2 * self.end_y

        return x, y, raw_progress

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        x, y, progress = self.get_position()

        # Fade in/out
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))
        else:
            alpha = 255

        if alpha > 0:
            # Wobble effect
            wobble_offset = int(math.sin(self.wobble) * 3)
            size_mod = 1.0 + math.sin(self.wobble * 2) * 0.1

            # Draw chunk based on type with blood coating
            chunk_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            center = self.size * 1.5

            if self.chunk_type == 'rib':
                # Elongated bone with blood
                pygame.draw.ellipse(chunk_surf, (*self.blood_color, int(alpha * 0.6)),
                                   (0, center - self.size // 3, self.size * 3, self.size))
                pygame.draw.ellipse(chunk_surf, (*self.bone_color, alpha),
                                   (4, center - self.size // 4, self.size * 2.5, int(self.size * 0.7)))
            elif self.chunk_type == 'cartilage':
                # Squishy tissue blob with blood core
                pygame.draw.circle(chunk_surf, (*self.blood_color, alpha),
                                 (int(center), int(center)), int(self.size * size_mod))
                pygame.draw.circle(chunk_surf, (*self.muscle_color, int(alpha * 0.8)),
                                 (int(center), int(center)), int(self.size * 0.8 * size_mod))
                # Glistening wet highlight
                pygame.draw.circle(chunk_surf, (255, 150, 150, int(alpha * 0.4)),
                                 (int(center - self.size * 0.3), int(center - self.size * 0.3)),
                                 int(self.size * 0.3))
            elif self.chunk_type == 'muscle':
                # Stringy muscle tissue
                for i in range(3):
                    offset = (i - 1) * self.size // 2
                    pygame.draw.ellipse(chunk_surf, (*self.muscle_color, alpha),
                                       (self.size // 2 + offset, self.size // 3,
                                        self.size, self.size * 2))
                # Dark blood between fibers
                pygame.draw.line(chunk_surf, (*self.blood_color, int(alpha * 0.7)),
                               (center, self.size // 2), (center, self.size * 2.5), 2)
            else:  # vertebra
                # Bone disc with marrow center
                pygame.draw.circle(chunk_surf, (*self.blood_color, int(alpha * 0.7)),
                                 (int(center), int(center)), int(self.size * 1.2))
                pygame.draw.circle(chunk_surf, (*self.bone_color, alpha),
                                 (int(center), int(center)), self.size)
                # Dark marrow core
                pygame.draw.circle(chunk_surf, (*self.muscle_color, int(alpha * 0.8)),
                                 (int(center), int(center)), self.size // 2)

            # Rotate with wobble
            wobble_angle = self.rotation + wobble_offset * 10
            rotated = pygame.transform.rotate(chunk_surf, wobble_angle)
            rect = rotated.get_rect(center=(int(x + wobble_offset), int(y)))
            surface.blit(rotated, rect)


class MarrowGlobProjectile:
    """
    Heavy, dripping marrow chunk with gravity physics.
    Visceral red spheres that tumble through the air trailing blood.
    """
    def __init__(self, start_x, start_y, end_x, end_y, particle_emitter, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.particle_emitter = particle_emitter
        self.timer = -delay
        self.duration = 0.7
        self.active = True

        # Physics properties
        self.gravity = 250  # units/s²
        self.velocity_x = (end_x - start_x) / self.duration
        self.velocity_y = (end_y - start_y) / self.duration - 100  # Initial upward boost
        self.current_x = start_x
        self.current_y = start_y

        # Visual properties
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-400, 400)
        self.size = random.randint(8, 14)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(3, 6)

        # Color - dark red marrow
        self.core_color = (139, 0, 0)       # Dark blood
        self.surface_color = (200, 80, 80)  # Muscle red

    def update(self, delta_time):
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer < 0:
            return True

        # Apply gravity physics
        self.velocity_y += self.gravity * delta_time
        self.current_x += self.velocity_x * delta_time
        self.current_y += self.velocity_y * delta_time

        # Update rotation and wobble
        self.rotation += self.rotation_speed * delta_time
        self.wobble_phase += self.wobble_speed * delta_time

        # Emit blood drip trail
        if self.particle_emitter and self.timer > 0.1:
            self.particle_emitter.emit_trail(
                self.current_x, self.current_y,
                (139, 0, 0), count=2
            )

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def get_position(self):
        """Get current position and progress."""
        if self.timer < 0:
            return self.start_x, self.start_y, 0

        progress = min(1.0, self.timer / self.duration)
        return self.current_x, self.current_y, progress

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        x, y, progress = self.get_position()

        # Fade in/out
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))
        else:
            alpha = 255

        if alpha > 0:
            # Size pulsing (breathing effect)
            pulse = math.sin(self.wobble_phase) * 0.15 + 1.0
            actual_size = int(self.size * pulse)

            # Create layered marrow glob
            glob_surf = pygame.Surface((actual_size * 3, actual_size * 3), pygame.SRCALPHA)
            center = actual_size * 1.5

            # Dark core (blood center)
            pygame.draw.circle(glob_surf, (*self.core_color, alpha),
                             (int(center), int(center)), actual_size)

            # Lighter outer layer (muscle tissue)
            pygame.draw.circle(glob_surf, (*self.surface_color, int(alpha * 0.7)),
                             (int(center), int(center)), int(actual_size * 1.3))

            # Highlights for wetness
            highlight_offset = int(actual_size * 0.3)
            pygame.draw.circle(glob_surf, (255, 100, 100, int(alpha * 0.4)),
                             (int(center - highlight_offset), int(center - highlight_offset)),
                             int(actual_size * 0.4))

            # Rotate with wobble
            wobble_angle = self.rotation + math.sin(self.wobble_phase) * 20
            rotated = pygame.transform.rotate(glob_surf, wobble_angle)
            rect = rotated.get_rect(center=(int(x), int(y)))
            surface.blit(rotated, rect)


class BoneSplinterProjectile:
    """
    Sharp, dangerous bone fragment with blood coating.
    Spins rapidly and streaks blood during flight.
    """
    def __init__(self, start_x, start_y, end_x, end_y, particle_emitter, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.particle_emitter = particle_emitter
        self.timer = -delay
        self.duration = 0.6
        self.active = True

        # Curved path
        mid_x = (start_x + end_x) / 2 + random.uniform(-25, 25)
        mid_y = (start_y + end_y) / 2 - random.uniform(15, 35)
        self.control_x = mid_x
        self.control_y = mid_y

        # Visual
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(800, 1200)  # High rotation
        self.length = random.randint(10, 16)
        self.width = random.randint(3, 5)

        # Colors
        self.bone_color = (240, 232, 216)
        self.blood_color = (139, 0, 0)

    def update(self, delta_time):
        if not self.active:
            return False

        self.timer += delta_time
        self.rotation += self.rotation_speed * delta_time

        # Emit blood streak trail
        if self.particle_emitter and self.timer > 0:
            x, y, _ = self.get_position()
            if random.random() > 0.5:  # 50% chance each frame
                self.particle_emitter.emit_trail(x, y, self.blood_color, count=1)

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def get_position(self):
        """Calculate position along bezier curve."""
        if self.timer < 0:
            return self.start_x, self.start_y, 0

        raw_progress = min(1.0, self.timer / self.duration)
        progress = raw_progress * raw_progress  # Acceleration

        t = progress
        x = (1-t)**2 * self.start_x + 2*(1-t)*t * self.control_x + t**2 * self.end_x
        y = (1-t)**2 * self.start_y + 2*(1-t)*t * self.control_y + t**2 * self.end_y

        return x, y, raw_progress

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        x, y, progress = self.get_position()

        # Fade in/out
        if progress < 0.15:
            alpha = int(255 * (progress / 0.15))
        elif progress > 0.85:
            alpha = int(255 * (1.0 - (progress - 0.85) / 0.15))
        else:
            alpha = 255

        if alpha > 0:
            # Create sharp splinter shape
            splinter_surf = pygame.Surface((self.length * 2, self.width * 2), pygame.SRCALPHA)

            # Blood coating (darker, slightly larger)
            blood_rect = pygame.Rect(2, 0, self.length - 4, self.width * 2)
            pygame.draw.ellipse(splinter_surf, (*self.blood_color, alpha), blood_rect)

            # Bone core (sharp, angular)
            bone_points = [
                (self.length - 2, self.width),  # Sharp tip
                (4, 0),                          # Top back
                (2, self.width),                 # Blunt end
                (4, self.width * 2),            # Bottom back
            ]
            pygame.draw.polygon(splinter_surf, (*self.bone_color, alpha), bone_points)

            # Glinting edge highlight
            pygame.draw.line(splinter_surf, (255, 255, 255, int(alpha * 0.6)),
                           (self.length - 2, self.width),
                           (self.length // 2, self.width // 2), 1)

            # Rotate at high speed
            rotated = pygame.transform.rotate(splinter_surf, self.rotation)
            rect = rotated.get_rect(center=(int(x), int(y)))
            surface.blit(rotated, rect)


# ============================================================================
# MARROW DIKE ANIMATION
# ============================================================================

class GroundCrack:
    """
    Ground crack appearing at a wall position before eruption.
    Spreading fissure with dark blood glow.
    """
    def __init__(self, screen_x, screen_y, delay=0):
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.timer = -delay  # Negative timer for staggered start
        self.duration = 0.5
        self.active = True

        # Crack properties
        self.crack_length = 0
        self.max_length = 20
        self.pulse_phase = 0

        # Crack lines (4 directions from center)
        self.directions = [
            (1, 0),    # Right
            (-1, 0),   # Left
            (0, 1),    # Down
            (0, -1)    # Up
        ]

    def update(self, delta_time):
        """Update crack spreading."""
        if not self.active:
            return False

        self.timer += delta_time
        self.pulse_phase += delta_time * 8  # Pulsing glow

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw spreading ground crack."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)
        self.crack_length = int(self.max_length * progress)

        # Pulsing glow intensity
        pulse = 0.7 + 0.3 * math.sin(self.pulse_phase)
        alpha = int(200 * progress * pulse)

        if alpha > 0 and self.crack_length > 0:
            # Draw 4 crack lines from center
            for dx, dy in self.directions:
                end_x = self.screen_x + dx * self.crack_length
                end_y = self.screen_y + dy * self.crack_length

                # Main crack line (dark blood red)
                pygame.draw.line(surface, (139, 0, 0, alpha),
                               (int(self.screen_x), int(self.screen_y)),
                               (int(end_x), int(end_y)), 3)

                # Inner glow
                if alpha > 100:
                    pygame.draw.line(surface, (200, 0, 0, alpha // 2),
                                   (int(self.screen_x), int(self.screen_y)),
                                   (int(end_x), int(end_y)), 1)

            # Center glow point
            glow_radius = int(6 + 4 * pulse)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (139, 0, 0, alpha),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.screen_x - glow_radius), int(self.screen_y - glow_radius)))


class MarrowEruptionParticle:
    """
    Single particle from marrow eruption.
    Follows parabolic arc with gravity.
    """
    def __init__(self, start_x, start_y, is_bone_fragment=False):
        self.x = start_x
        self.y = start_y
        self.timer = 0
        self.duration = random.uniform(0.6, 1.0)
        self.active = True

        # Particle type
        self.is_bone_fragment = is_bone_fragment
        if is_bone_fragment:
            self.color = random.choice([(240, 232, 216), (224, 213, 197)])  # Bone colors
            self.size = random.uniform(2, 4)
        else:
            self.color = (139, 0, 0)  # Blood red
            self.size = random.uniform(3, 6)

        # Physics
        self.vx = random.uniform(-60, 60)  # Outward spread
        self.vy = -random.uniform(120, 180)  # Upward velocity
        self.gravity = 300

    def update(self, delta_time):
        """Update particle physics."""
        if not self.active:
            return False

        self.timer += delta_time

        # Apply gravity
        self.vy += self.gravity * delta_time

        # Update position
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw marrow particle."""
        if not self.active:
            return

        progress = self.timer / self.duration

        # Fade in/out
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))
        else:
            alpha = 255

        if alpha > 0:
            particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*self.color, alpha),
                             (int(self.size), int(self.size)), int(self.size))

            # Blood particles get glow
            if not self.is_bone_fragment and alpha > 150:
                glow_size = self.size + 2
                pygame.draw.circle(particle_surf, (200, 0, 0, alpha // 3),
                                 (int(self.size), int(self.size)), int(glow_size))

            surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))


class MarrowEruption:
    """
    Eruption at a single wall position.
    Manages geyser, particles, and wall growth.
    """
    def __init__(self, screen_x, screen_y, delay=0):
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.timer = -delay
        self.duration = 0.8  # Total eruption duration
        self.active = True

        # Sub-phases
        self.phase = "burst"  # burst -> growth -> settle
        self.burst_duration = 0.3
        self.growth_duration = 0.3
        self.settle_duration = 0.2

        # Particles
        self.particles = []
        self.particles_spawned = False

        # Wall growth
        self.wall_height_progress = 0

    def update(self, delta_time):
        """Update eruption phases."""
        if not self.active:
            return False

        self.timer += delta_time

        # Skip update during delay
        if self.timer < 0:
            return True

        # Spawn particles once at burst start
        if not self.particles_spawned:
            num_particles = random.randint(12, 18)
            for i in range(num_particles):
                is_bone = (i % 10 < 3)  # 30% bone, 70% blood
                particle = MarrowEruptionParticle(self.screen_x, self.screen_y, is_bone_fragment=is_bone)
                self.particles.append(particle)
            self.particles_spawned = True

        # Update particles
        self.particles = [p for p in self.particles if p.update(delta_time)]

        # Phase transitions
        if self.phase == "burst" and self.timer >= self.burst_duration:
            self.phase = "growth"
            self.timer -= self.burst_duration
        elif self.phase == "growth":
            # Wall grows from bottom to top
            self.wall_height_progress = min(1.0, self.timer / self.growth_duration)
            if self.timer >= self.growth_duration:
                self.phase = "settle"
                self.timer -= self.growth_duration
        elif self.phase == "settle" and self.timer >= self.settle_duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw eruption effects."""
        if not self.active or self.timer < 0:
            return

        # Draw marrow geyser (during burst phase)
        if self.phase == "burst":
            progress = min(1.0, self.timer / self.burst_duration)
            geyser_height = int(40 * progress)
            alpha = int(200 * progress)

            if alpha > 0 and geyser_height > 0:
                # Upward spray (pale marrow color)
                for i in range(5):
                    offset = (i - 2) * 4
                    start_y = self.screen_y
                    end_y = self.screen_y - geyser_height
                    pygame.draw.line(surface, (184, 112, 96, alpha),
                                   (int(self.screen_x + offset), int(start_y)),
                                   (int(self.screen_x + offset), int(end_y)), 3)

        # Draw particles
        for particle in self.particles:
            particle.draw(surface)

        # Draw wall growth indicator (during growth phase)
        if self.phase == "growth":
            # Visual indicator of wall forming (simplified)
            height = int(TILE_SIZE * self.wall_height_progress)
            alpha = int(180 * self.wall_height_progress)

            if alpha > 0 and height > 0:
                wall_surf = pygame.Surface((TILE_SIZE, height), pygame.SRCALPHA)
                # Gradient from pale marrow at bottom to bone white at top
                for y in range(height):
                    y_progress = y / height
                    color_r = int(184 + (240 - 184) * y_progress)
                    color_g = int(112 + (232 - 112) * y_progress)
                    color_b = int(96 + (216 - 96) * y_progress)
                    pygame.draw.line(wall_surf, (color_r, color_g, color_b, alpha),
                                   (0, y), (TILE_SIZE, y))

                surface.blit(wall_surf, (int(self.screen_x - TILE_SIZE/2), int(self.screen_y - height)))


class WallNetwork:
    """
    Manages solidification effects across all walls.
    Shows connecting glow and sinew fiber shimmer.
    """
    def __init__(self, wall_positions, upgraded=False):
        self.wall_positions = wall_positions  # List of (screen_x, screen_y) tuples
        self.upgraded = upgraded
        self.timer = 0
        self.duration = 0.7
        self.active = True

        # Animation properties
        self.glow_intensity = 0
        self.shimmer_phase = 0

    def update(self, delta_time):
        """Update network solidification."""
        if not self.active:
            return False

        self.timer += delta_time
        self.shimmer_phase += delta_time * 6

        # Glow ramps up then fades
        if self.timer < 0.3:
            self.glow_intensity = self.timer / 0.3
        elif self.timer < 0.5:
            self.glow_intensity = 1.0
        else:
            self.glow_intensity = 1.0 - ((self.timer - 0.5) / 0.2)

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw wall network effects."""
        if not self.active or self.glow_intensity <= 0:
            return

        # Shimmer effect (oscillating)
        shimmer = 0.7 + 0.3 * math.sin(self.shimmer_phase)

        # Draw glow at each wall position
        for screen_x, screen_y in self.wall_positions:
            # Base glow (bone white)
            glow_radius = int(30 * self.glow_intensity * shimmer)
            alpha = int(120 * self.glow_intensity * shimmer)

            if alpha > 0 and glow_radius > 0:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

                # Bone white outer glow
                pygame.draw.circle(glow_surf, (240, 232, 216, alpha // 2),
                                 (glow_radius, glow_radius), glow_radius)

                # Pale cream inner glow
                inner_radius = int(glow_radius * 0.7)
                pygame.draw.circle(glow_surf, (224, 213, 197, alpha),
                                 (glow_radius, glow_radius), inner_radius)

                # If upgraded: Additional bright reinforcement glow
                if self.upgraded:
                    core_radius = int(glow_radius * 0.5)
                    pygame.draw.circle(glow_surf, (255, 255, 255, alpha // 2),
                                     (glow_radius, glow_radius), core_radius)

                surface.blit(glow_surf, (int(screen_x - glow_radius), int(screen_y - glow_radius)))


class MarrowDikeAnimation:
    """
    Marrow Dike skill animation for MARROW CONDENSER.
    Shows violent eruption of bone marrow walls in 5x5 perimeter pattern.

    Phases:
    1. Fracture (0.5s) - Ground cracks appear at wall positions
    2. Eruption (1.3s) - Marrow walls erupt from ground in cascade
    3. Solidification (0.7s) - Walls complete hardening with network glow
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Marrow Dike animation.

        Args:
            caster_unit: The MARROW CONDENSER casting Marrow Dike
            camera: Camera for coordinate conversion
            game: Game instance to calculate wall positions and check upgraded status
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Animation state
        self.phase = "fracture"  # fracture -> eruption -> solidification
        self.timer = 0
        self.active = True

        # Check if upgraded
        self.upgraded = False
        if hasattr(caster_unit, 'passive_skill'):
            self.upgraded = getattr(caster_unit.passive_skill, 'marrow_dike_upgraded', False)

        # Calculate 5x5 perimeter wall positions (16 walls)
        self.wall_positions = []
        center_grid_y = caster_unit.grid_y
        center_grid_x = caster_unit.grid_x

        for dy in range(-2, 3):
            for dx in range(-2, 3):
                # Perimeter only: abs(dy)==2 OR abs(dx)==2
                if abs(dy) == 2 or abs(dx) == 2:
                    grid_y = center_grid_y + dy
                    grid_x = center_grid_x + dx

                    # Check if valid position
                    if game and game.is_valid_position(grid_y, grid_x):
                        screen_x, screen_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

                        # Calculate cascade order (distance from nearest corner)
                        corner_dist = self._calculate_cascade_order(dy, dx)

                        self.wall_positions.append({
                            'grid': (grid_y, grid_x),
                            'screen': (screen_x, screen_y),
                            'cascade_order': corner_dist,
                            'crack': None,
                            'eruption': None
                        })

        # Sort by cascade order (corner → edges, clockwise)
        self.wall_positions.sort(key=lambda w: w['cascade_order'])

        # Sub-effects
        self.network = None
        self.cracks_created = False
        self.eruptions_created = False

        # Start Phase 1
        self._start_fracture()

    def _calculate_cascade_order(self, dy, dx):
        """Calculate order for cascading animation (corner first, then spiral outward)."""
        # Corners get priority (lowest numbers)
        if abs(dy) == 2 and abs(dx) == 2:
            # Map corners to 0-3
            if dy == -2 and dx == -2:
                return 0  # Top-left
            elif dy == -2 and dx == 2:
                return 1  # Top-right
            elif dy == 2 and dx == 2:
                return 2  # Bottom-right
            else:  # dy == 2 and dx == -2
                return 3  # Bottom-left

        # Edges get higher numbers, spiraling outward
        # Top edge
        if dy == -2:
            return 4 + dx + 2  # 4, 5, 6, 7, 8
        # Right edge
        elif dx == 2:
            return 9 + dy + 2  # 9, 10, 11, 12, 13
        # Bottom edge
        elif dy == 2:
            return 14 - (dx + 2)  # 14, 13, 12, 11, 10 (reversed for clockwise)
        # Left edge
        else:  # dx == -2
            return 15 - (dy + 2)  # 15, 14, 13, 12, 11 (reversed for clockwise)

    def _start_fracture(self):
        """Phase 1: Fracture - Ground cracks appear."""
        self.phase = "fracture"
        self.timer = 0

        # Play fracture sound
        play_sound("marrow_dike_fracture")

        # Create cracks with staggered timing
        if not self.cracks_created:
            for i, wall_data in enumerate(self.wall_positions):
                screen_x, screen_y = wall_data['screen']
                delay = i * 0.03  # 0.03s stagger between each crack
                wall_data['crack'] = GroundCrack(screen_x, screen_y, delay=delay)
            self.cracks_created = True

        # Light rumbling shake
        self.screen_shake_callback(3, 0.4)

    def _start_eruption(self):
        """Phase 2: Eruption - Marrow walls erupt from cracks."""
        self.phase = "eruption"
        self.timer = 0

        # Play eruption sound
        play_sound("marrow_dike_erupt")

        # Create eruptions with staggered timing
        if not self.eruptions_created:
            for i, wall_data in enumerate(self.wall_positions):
                screen_x, screen_y = wall_data['screen']
                delay = i * 0.05  # 0.05s stagger between each eruption
                wall_data['eruption'] = MarrowEruption(screen_x, screen_y, delay=delay)
            self.eruptions_created = True

    def _start_solidification(self):
        """Phase 3: Solidification - Walls complete hardening."""
        self.phase = "solidification"
        self.timer = 0

        # Play solidification sound
        play_sound("marrow_dike_solidify")

        # Create wall network effect
        wall_screen_positions = [w['screen'] for w in self.wall_positions]
        self.network = WallNetwork(wall_screen_positions, upgraded=self.upgraded)

        # White flash at solidification (removed — screen flashes reserved for Rail Genesis)

        # Light settling shake
        self.screen_shake_callback(2, 0.3)

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "fracture" and self.timer >= 0.5:
            self._start_eruption()
        elif self.phase == "eruption" and self.timer >= 1.3:
            self._start_solidification()
        elif self.phase == "solidification" and self.timer >= 0.7:
            self.active = False  # Animation complete

        # Update sub-effects
        for wall_data in self.wall_positions:
            if wall_data['crack']:
                wall_data['crack'].update(delta_time)
            if wall_data['eruption']:
                # Trigger screen shake on each eruption start
                eruption = wall_data['eruption']
                was_delayed = eruption.timer < 0
                eruption.update(delta_time)
                # If eruption just started (was delayed, now active)
                if was_delayed and eruption.timer >= 0:
                    # Light shake for each wall eruption
                    self.screen_shake_callback(5, 0.08)

        if self.network:
            self.network.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw ground cracks (Phase 1)
        if self.phase == "fracture":
            for wall_data in self.wall_positions:
                if wall_data['crack']:
                    wall_data['crack'].draw(surface)

        # Draw eruptions (Phase 2)
        if self.phase == "eruption":
            for wall_data in self.wall_positions:
                if wall_data['eruption']:
                    wall_data['eruption'].draw(surface)

        # Draw wall network (Phase 3)
        if self.phase == "solidification" and self.network:
            self.network.draw(surface)


# ============================================================================
# MARROW DIKE WALL DESPAWN ANIMATION
# ============================================================================

class WallCrack:
    """
    Stress fracture appearing on wall surface before crumbling.
    Jagged crack lines with pulsing dark blood glow.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True

        # Crack properties
        self.angle = random.uniform(0, 2 * math.pi)
        self.length = random.uniform(15, 25)
        self.pulse_phase = random.uniform(0, 2 * math.pi)

    def update(self, delta_time):
        """Update crack spreading."""
        if not self.active:
            return False

        self.timer += delta_time
        self.pulse_phase += delta_time * 8

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw spreading crack."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)
        current_length = self.length * progress

        # Pulsing glow
        pulse = 0.6 + 0.4 * math.sin(self.pulse_phase)
        alpha = int(180 * progress * pulse)

        if alpha > 0 and current_length > 5:
            # Main crack line (dark blood red)
            end_x = self.center_x + math.cos(self.angle) * current_length
            end_y = self.center_y + math.sin(self.angle) * current_length

            pygame.draw.line(surface, (139, 0, 0, alpha),
                           (int(self.center_x), int(self.center_y)),
                           (int(end_x), int(end_y)), 2)

            # Inner glow
            if alpha > 100:
                pygame.draw.line(surface, (200, 80, 80, alpha // 2),
                               (int(self.center_x), int(self.center_y)),
                               (int(end_x), int(end_y)), 1)

            # Branch cracks (smaller)
            if current_length > 10:
                branch_point = current_length * 0.6
                branch_x = self.center_x + math.cos(self.angle) * branch_point
                branch_y = self.center_y + math.sin(self.angle) * branch_point

                branch_angle1 = self.angle + math.pi / 4
                branch_angle2 = self.angle - math.pi / 4
                branch_len = current_length * 0.3

                branch_end1_x = branch_x + math.cos(branch_angle1) * branch_len
                branch_end1_y = branch_y + math.sin(branch_angle1) * branch_len
                branch_end2_x = branch_x + math.cos(branch_angle2) * branch_len
                branch_end2_y = branch_y + math.sin(branch_angle2) * branch_len

                pygame.draw.line(surface, (139, 0, 0, alpha // 2),
                               (int(branch_x), int(branch_y)),
                               (int(branch_end1_x), int(branch_end1_y)), 1)
                pygame.draw.line(surface, (139, 0, 0, alpha // 2),
                               (int(branch_x), int(branch_y)),
                               (int(branch_end2_x), int(branch_end2_y)), 1)


class FallingFragment:
    """
    Individual bone fragment falling with gravity and rotation.
    """
    def __init__(self, start_x, start_y, is_large=False):
        self.x = start_x
        self.y = start_y
        self.timer = 0
        self.duration = random.uniform(0.8, 1.2)
        self.active = True

        # Fragment type
        self.is_large = is_large
        if is_large:
            self.size = random.uniform(6, 12)
            self.color = (224, 213, 197)  # Pale bone
        else:
            self.size = random.uniform(3, 6)
            self.color = (208, 197, 181)  # Dark bone

        # Physics
        self.vx = random.uniform(-40, 40)  # Horizontal spread
        self.vy = random.uniform(-80, -20)  # Initial upward kick
        self.gravity = 350  # Downward acceleration

        # Rotation
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-4, 4)

    def update(self, delta_time):
        """Update fragment physics."""
        if not self.active:
            return False

        self.timer += delta_time

        # Apply gravity
        self.vy += self.gravity * delta_time

        # Update position
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        # Update rotation
        self.rotation += self.rotation_speed * delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw falling fragment."""
        if not self.active:
            return

        progress = self.timer / self.duration

        # Fade out over time
        if progress < 0.3:
            alpha = 255
        else:
            alpha = int(255 * (1.0 - (progress - 0.3) / 0.7))

        if alpha > 0:
            # Draw irregular fragment shape
            half_size = self.size / 2
            points = [
                (self.x - half_size * 0.8, self.y - half_size),
                (self.x + half_size * 0.6, self.y - half_size * 0.7),
                (self.x + half_size, self.y + half_size * 0.5),
                (self.x + half_size * 0.3, self.y + half_size),
                (self.x - half_size * 0.9, self.y + half_size * 0.6)
            ]

            # Rotate points
            rotated_points = []
            for px, py in points:
                dx = px - self.x
                dy = py - self.y
                rx = dx * math.cos(self.rotation) - dy * math.sin(self.rotation)
                ry = dx * math.sin(self.rotation) + dy * math.cos(self.rotation)
                rotated_points.append((int(self.x + rx), int(self.y + ry)))

            # Draw fragment
            frag_surf = pygame.Surface((int(self.size * 3), int(self.size * 3)), pygame.SRCALPHA)
            offset_points = [(int(px - self.x + self.size * 1.5), int(py - self.y + self.size * 1.5))
                           for px, py in rotated_points]

            pygame.draw.polygon(frag_surf, (*self.color, alpha), offset_points)
            pygame.draw.polygon(frag_surf, (139, 0, 0, alpha // 2), offset_points, 1)

            surface.blit(frag_surf, (int(self.x - self.size * 1.5), int(self.y - self.size * 1.5)))


class DustParticle:
    """
    Fine dust particle rising upward from crumbling wall.
    """
    def __init__(self, start_x, start_y):
        self.x = start_x
        self.y = start_y
        self.timer = 0
        self.duration = random.uniform(0.4, 0.8)
        self.active = True

        # Particle properties
        self.size = random.uniform(1, 3)
        self.color = (224, 213, 197)  # Pale cream

        # Physics (rises upward)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-70, -50)  # Negative = upward

    def update(self, delta_time):
        """Update particle movement."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update position
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw dust particle."""
        if not self.active:
            return

        progress = self.timer / self.duration

        # Fast fade
        if progress < 0.2:
            alpha = int(180 * (progress / 0.2))
        else:
            alpha = int(180 * (1.0 - (progress - 0.2) / 0.8))

        if alpha > 0:
            particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*self.color, alpha),
                             (int(self.size), int(self.size)), int(self.size))
            surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))


class MarrowDikeWallDespawnAnimation:
    """
    Marrow Dike wall despawn animation.
    Shows a single wall cracking, crumbling into fragments, and dissipating.

    Phases:
    1. Cracking (0.4s) - Stress fractures appear and spread
    2. Crumbling (0.6s) - Wall breaks into falling fragments with rising dust
    3. Dissipation (0.5s) - Fragments fade to nothing
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Marrow Dike wall despawn animation.

        Args:
            target_pos: (grid_y, grid_x) - Position of the wall tile despawning
            camera: Camera for coordinate conversion
            Other args: Standard from AnimationFactory
        """
        # Store references
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Convert wall grid position to screen coords
        grid_y, grid_x = target_pos
        self.center_x, self.center_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "cracking"  # cracking -> crumbling -> dissipation
        self.timer = 0
        self.active = True

        # Sub-effects
        self.cracks = []
        self.fragments = []
        self.dust_particles = []

        # Start Phase 1
        self._start_cracking()

    def _start_cracking(self):
        """Phase 1: Cracking - Stress fractures appear."""
        self.phase = "cracking"
        self.timer = 0

        # Create 5-7 cracks emanating from different points on wall
        num_cracks = random.randint(5, 7)
        for i in range(num_cracks):
            # Random origin points within tile
            offset_x = random.uniform(-TILE_SIZE/4, TILE_SIZE/4)
            offset_y = random.uniform(-TILE_SIZE/4, TILE_SIZE/4)
            crack_x = self.center_x + offset_x
            crack_y = self.center_y + offset_y

            delay = i * 0.05  # Stagger crack appearance
            self.cracks.append(WallCrack(crack_x, crack_y, delay=delay))

        # Light screen shake for stress
        self.screen_shake_callback(2, 0.3)

    def _start_crumbling(self):
        """Phase 2: Crumbling - Wall breaks into fragments."""
        self.phase = "crumbling"
        self.timer = 0

        # Create falling bone fragments
        num_large_fragments = random.randint(8, 12)
        num_small_fragments = random.randint(15, 20)

        for i in range(num_large_fragments):
            offset_x = random.uniform(-TILE_SIZE/3, TILE_SIZE/3)
            offset_y = random.uniform(-TILE_SIZE/3, TILE_SIZE/3)
            frag_x = self.center_x + offset_x
            frag_y = self.center_y + offset_y
            self.fragments.append(FallingFragment(frag_x, frag_y, is_large=True))

        for i in range(num_small_fragments):
            offset_x = random.uniform(-TILE_SIZE/2, TILE_SIZE/2)
            offset_y = random.uniform(-TILE_SIZE/2, TILE_SIZE/2)
            frag_x = self.center_x + offset_x
            frag_y = self.center_y + offset_y
            self.fragments.append(FallingFragment(frag_x, frag_y, is_large=False))

        # Create rising dust particles
        num_dust = random.randint(15, 20)
        for i in range(num_dust):
            offset_x = random.uniform(-TILE_SIZE/3, TILE_SIZE/3)
            offset_y = random.uniform(-TILE_SIZE/3, TILE_SIZE/3)
            dust_x = self.center_x + offset_x
            dust_y = self.center_y + offset_y
            self.dust_particles.append(DustParticle(dust_x, dust_y))

        # Medium screen shake for collapse
        self.screen_shake_callback(4, 0.4)

    def _start_dissipation(self):
        """Phase 3: Dissipation - Fragments fade away."""
        self.phase = "dissipation"
        self.timer = 0

        # No new effects, just let existing particles fade

    def update(self, delta_time):
        """Update animation state. Returns True if active, False when done."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "cracking" and self.timer >= 0.4:
            self._start_crumbling()
        elif self.phase == "crumbling" and self.timer >= 0.6:
            self._start_dissipation()
        elif self.phase == "dissipation" and self.timer >= 0.5:
            self.active = False  # Animation complete

        # Update all sub-effects
        self.cracks = [c for c in self.cracks if c.update(delta_time)]
        self.fragments = [f for f in self.fragments if f.update(delta_time)]
        self.dust_particles = [d for d in self.dust_particles if d.update(delta_time)]

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw cracks (Phase 1)
        if self.phase == "cracking":
            for crack in self.cracks:
                crack.draw(surface)

        # Draw fragments and dust (Phase 2-3)
        if self.phase in ["crumbling", "dissipation"]:
            for fragment in self.fragments:
                fragment.draw(surface)
            for dust in self.dust_particles:
                dust.draw(surface)


# ============================================================================
# MARROW CONDENSER BASIC ATTACK - BONE BALL BASH
# ============================================================================

class MarrowCondenserBoneAttack:
    """
    MARROW CONDENSER basic attack animation - wadded ball of bone chunks and marrow.
    Gathers bone/marrow particles into a rotating mass, launches it at target, explodes on impact.
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
        self.phase = "gather"  # gather → launch → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.gather_duration = 0.2
        self.launch_duration = 0.25
        self.impact_duration = 0.2

        # Ball position and rotation
        self.ball_x = attacker_unit.x
        self.ball_y = attacker_unit.y
        self.ball_rotation = 0.0

        # Bone and marrow colors from MARROW_CONDENSER sprite
        self.color_bone_white = (240, 232, 216)  # #f0e8d8
        self.color_bone_cream = (224, 213, 197)  # #e0d5c5
        self.color_marrow_red = (200, 69, 69)    # #c84545
        self.color_marrow_dark = (184, 69, 69)   # #b84545

    def _trigger_gather(self):
        """Phase 1: Gather bone and marrow chunks."""
        # Gather sound - bone and marrow coalescing
        play_sound("marrow_attack_gather")

        # Spawn gathering particles (swirling toward attacker)
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(30, 50)
            x = self.attacker.x + math.cos(angle) * distance
            y = self.attacker.y + math.sin(angle) * distance

            # Particles move toward center
            vx = -math.cos(angle) * 150
            vy = -math.sin(angle) * 150

            # Mix of bone (white) and marrow (red) particles
            color = random.choice([
                self.color_bone_white,
                self.color_bone_cream,
                self.color_marrow_red,
                self.color_marrow_dark,
            ])

            from .core import Particle
            particle = Particle(x, y, vx, vy, color, size=random.uniform(3, 5), lifetime=0.25)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_launch(self):
        """Phase 2: Launch wadded bone ball toward target."""
        # Launch sound - bone ball hurled
        play_sound("marrow_attack_launch")

        # Create trailing particles as ball moves
        for i in range(12):
            progress = i / 12
            trail_x = self.attacker.x + self.dx * self.distance * progress * 0.3
            trail_y = self.attacker.y + self.dy * self.distance * progress * 0.3

            # Perpendicular spread
            perp_x = -self.dy
            perp_y = self.dx
            spread = random.uniform(-8, 8)

            vx = self.dx * 120 + perp_x * spread
            vy = self.dy * 120 + perp_y * spread

            # Mix of colors
            color = random.choice([
                self.color_bone_cream,
                self.color_marrow_red,
            ])

            from .core import Particle
            particle = Particle(trail_x, trail_y, vx, vy, color,
                              size=random.uniform(2, 4), lifetime=0.2)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Bone and marrow explosion on impact."""
        # Impact sound - bone and marrow explosion
        play_sound("marrow_attack_impact")

        # Impact explosion - mixed bone shards and marrow splatter
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # 60% bone, 40% marrow
            if random.random() < 0.6:
                color = random.choice([self.color_bone_white, self.color_bone_cream])
                size = random.uniform(2, 5)
            else:
                color = random.choice([self.color_marrow_red, self.color_marrow_dark])
                size = random.uniform(3, 6)

            from .core import Particle
            particle = Particle(self.target.x, self.target.y, vx, vy, color,
                              size, lifetime=random.uniform(0.2, 0.35))
            particle.gravity = 180
            self.particle_emitter.particles.append(particle)

        # Strong impact
        self.target.shake_intensity = 13
        self.screen_shake(6, 0.18)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "gather":
            if self.timer == 0 or not hasattr(self, '_gather_triggered'):
                self._trigger_gather()
                self._gather_triggered = True

            if self.timer >= self.gather_duration:
                self.phase = "launch"
                self.timer = 0
                self._trigger_launch()

        elif self.phase == "launch":
            # Update ball position (lerp from attacker to target)
            progress = min(1.0, self.timer / self.launch_duration)
            self.ball_x = self.attacker.x + self.dx * self.distance * progress
            self.ball_y = self.attacker.y + self.dy * self.distance * progress

            # Rotate ball as it travels
            self.ball_rotation += delta_time * 15

            if self.timer >= self.launch_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw the wadded bone ball."""
        import pygame

        # Draw gathering glow
        if self.phase == "gather":
            progress = self.timer / self.gather_duration
            glow_radius = int(25 * progress)

            if glow_radius > 3:
                # Mixed bone/marrow glow
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_bone_white, int(100 * progress)),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(self.attacker.x - glow_radius),
                                        int(self.attacker.y - glow_radius)))

                # Red marrow core
                core_radius = int(glow_radius * 0.6)
                if core_radius > 2:
                    core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(core_surf, (*self.color_marrow_red, int(140 * progress)),
                                     (core_radius, core_radius), core_radius)
                    surface.blit(core_surf, (int(self.attacker.x - core_radius),
                                            int(self.attacker.y - core_radius)))

        # Draw wadded ball during launch
        if self.phase == "launch":
            # Draw ball as cluster of overlapping circles (bone + marrow)
            ball_radius = 15

            # Create surface for ball
            ball_surf = pygame.Surface((ball_radius * 4, ball_radius * 4), pygame.SRCALPHA)
            center = ball_radius * 2

            # Draw 8-10 overlapping chunks at different angles
            num_chunks = 9
            for i in range(num_chunks):
                angle = (i / num_chunks) * 2 * math.pi + self.ball_rotation
                offset_dist = ball_radius * 0.4
                chunk_x = center + math.cos(angle) * offset_dist
                chunk_y = center + math.sin(angle) * offset_dist

                # Alternate bone and marrow chunks
                if i % 3 == 0:
                    color = (*self.color_marrow_red, 220)
                    chunk_size = int(ball_radius * 0.6)
                elif i % 3 == 1:
                    color = (*self.color_bone_white, 240)
                    chunk_size = int(ball_radius * 0.5)
                else:
                    color = (*self.color_bone_cream, 230)
                    chunk_size = int(ball_radius * 0.5)

                pygame.draw.circle(ball_surf, color,
                                 (int(chunk_x), int(chunk_y)), chunk_size)

            # Draw darker marrow core in center
            pygame.draw.circle(ball_surf, (*self.color_marrow_dark, 200),
                             (center, center), int(ball_radius * 0.4))

            # Blit ball to surface
            surface.blit(ball_surf, (int(self.ball_x - ball_radius * 2),
                                    int(self.ball_y - ball_radius * 2)))

        # Draw impact flash
        if self.phase == "impact":
            progress = self.timer / self.impact_duration
            if progress < 0.5:
                flash_alpha = int(255 * (1.0 - progress / 0.5))
                flash_radius = int(40 * (1.0 + progress))

                # Mixed bone/marrow flash
                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                # White outer flash
                pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                # Red marrow center
                center_radius = int(flash_radius * 0.6)
                pygame.draw.circle(flash_surf, (*self.color_marrow_red, flash_alpha),
                                 (flash_radius, flash_radius), center_radius)

                surface.blit(flash_surf, (int(self.target.x - flash_radius),
                                         int(self.target.y - flash_radius)))
