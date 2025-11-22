#!/usr/bin/env python3
"""
GRAYMAN Animation Classes
Skill animations for the GRAYMAN unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, Particle, DebrisParticle


class DeltaConfigAnimation:
    """
    Teleportation animation that 'pulls' the destination point toward the caster,
    then snaps to the destination. Represents bending space-time.
    """

    def __init__(self, caster_unit, target_pos, particle_emitter):
        """
        Args:
            caster_unit: AnimatedUnit teleporting
            target_pos: Target grid position (grid_x, grid_y)
            particle_emitter: ParticleEmitter for spawning particles
        """
        self.caster_unit = caster_unit
        self.target_grid_x, self.target_grid_y = target_pos
        self.particle_emitter = particle_emitter

        # Convert grid to screen coordinates
        from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
        self.source_x = caster_unit.x
        self.source_y = caster_unit.y
        self.target_x = GRID_OFFSET_X + target_pos[0] * TILE_SIZE + TILE_SIZE // 2
        self.target_y = GRID_OFFSET_Y + target_pos[1] * TILE_SIZE + TILE_SIZE // 2

        # Animation phases
        self.phase = "energize"  # energize, pull, hold, snap, appear
        self.timer = 0
        self.energize_duration = 0.4
        self.pull_duration = 0.6
        self.hold_duration = 0.15
        self.snap_duration = 0.1
        self.appear_duration = 0.3

        # Purple/lavender colors from Grayman's orbs
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_bright = (255, 255, 255)

        # Pull chain - points along the path from source to target
        self.pull_chain = []
        self.pull_progress = 0  # How much of the chain has been "pulled"

        # Calculate pull chain points
        dx = self.target_x - self.source_x
        dy = self.target_y - self.source_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            num_points = int(distance / 15) + 2  # Point every 15 pixels
            for i in range(num_points):
                t = i / (num_points - 1) if num_points > 1 else 0
                x = self.source_x + dx * t
                y = self.source_y + dy * t
                self.pull_chain.append((x, y))

        # Flags
        self.energize_particles_spawned = False
        self.snap_particles_spawned = False
        self.teleported = False

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == "energize":
            # Charging up at origin
            if not self.energize_particles_spawned:
                # Spawn energizing particles
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(30, 60)
                    x = self.source_x + math.cos(angle) * distance
                    y = self.source_y + math.sin(angle) * distance
                    # Particles move toward center
                    vx = -math.cos(angle) * 100
                    vy = -math.sin(angle) * 100
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(x, y, vx, vy, lifetime=0.4, size=4, color=color)
                    self.particle_emitter.particles.append(particle)
                self.energize_particles_spawned = True

            if self.timer >= self.energize_duration:
                self.phase = "pull"
                self.timer = 0

        elif self.phase == "pull":
            # Pull destination toward origin
            progress = self.timer / self.pull_duration
            self.pull_progress = min(1.0, progress)

            # Spawn particles along the pull chain
            if random.random() < 0.3 and len(self.pull_chain) > 0:
                idx = int(self.pull_progress * len(self.pull_chain) * 0.8)
                if idx < len(self.pull_chain):
                    x, y = self.pull_chain[idx]
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(x, y, 0, 0, lifetime=0.2, size=3, color=color)
                    self.particle_emitter.particles.append(particle)

            if self.timer >= self.pull_duration:
                self.phase = "hold"
                self.timer = 0

        elif self.phase == "hold":
            # Brief pause at full tension
            if self.timer >= self.hold_duration:
                self.phase = "snap"
                self.timer = 0

        elif self.phase == "snap":
            # Instant snapback - unit disappears from origin
            if not self.teleported:
                # Hide caster temporarily (will reappear at target)
                self.caster_unit.visible = False
                self.teleported = True

            if self.timer >= self.snap_duration:
                self.phase = "appear"
                self.timer = 0

        elif self.phase == "appear":
            # Appear at destination
            if not self.snap_particles_spawned:
                # Move caster to target position
                self.caster_unit.grid_x = self.target_grid_x
                self.caster_unit.grid_y = self.target_grid_y
                self.caster_unit.x = self.target_x
                self.caster_unit.y = self.target_y
                self.caster_unit.visible = True

                # Spawn arrival particles
                for _ in range(30):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(80, 200)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_outer, self.color_inner, self.color_bright])
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.5, size=5, color=color)
                    self.particle_emitter.particles.append(particle)

                # Ring of particles expanding outward
                for i in range(12):
                    angle = (i / 12) * 2 * math.pi
                    vx = math.cos(angle) * 150
                    vy = math.sin(angle) * 150
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.4, size=4, color=self.color_inner)
                    self.particle_emitter.particles.append(particle)

                self.snap_particles_spawned = True

            if self.timer >= self.appear_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the Delta Config animation."""
        if self.phase == "energize":
            # Draw energizing glow at source
            progress = self.timer / self.energize_duration

            # Pulsing outer glow
            glow_radius = int(20 + 10 * math.sin(self.timer * 15))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_outer, int(120 * progress)),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Inner glow
            inner_radius = int(glow_radius * 0.6)
            glow_surf2 = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf2, (*self.color_inner, int(180 * progress)),
                             (inner_radius, inner_radius), inner_radius)
            surface.blit(glow_surf2, (int(self.source_x - inner_radius),
                                     int(self.source_y - inner_radius)))

            # Draw delta symbol at source
            # Draw a triangle (delta shape)
            size = int(15 * progress)
            if size > 3:
                points = [
                    (int(self.source_x), int(self.source_y - size)),
                    (int(self.source_x - size * 0.866), int(self.source_y + size * 0.5)),
                    (int(self.source_x + size * 0.866), int(self.source_y + size * 0.5))
                ]
                pygame.draw.polygon(surface, self.color_bright, points, 2)

        elif self.phase == "pull":
            # Draw pulsing energy at source
            pulse = 0.8 + 0.2 * math.sin(self.timer * 20)
            glow_radius = int(15 * pulse)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_inner, 150),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Draw the pull chain - line from target toward source
            if len(self.pull_chain) > 1:
                visible_points = int(len(self.pull_chain) * self.pull_progress)
                if visible_points > 1:
                    # Draw line segments from target backwards toward source
                    for i in range(len(self.pull_chain) - 1, max(len(self.pull_chain) - visible_points, 0), -1):
                        if i > 0:
                            x1, y1 = self.pull_chain[i]
                            x2, y2 = self.pull_chain[i - 1]

                            # Fade effect based on distance from target
                            fade = (i / len(self.pull_chain))
                            alpha = int(200 * fade)

                            # Draw thick line
                            pygame.draw.line(surface, (*self.color_outer, alpha),
                                          (int(x1), int(y1)), (int(x2), int(y2)), 4)
                            # Draw thin inner line
                            pygame.draw.line(surface, self.color_inner,
                                          (int(x1), int(y1)), (int(x2), int(y2)), 2)

            # Draw small glow at target
            target_glow = int(10 * self.pull_progress)
            if target_glow > 2:
                glow_surf3 = pygame.Surface((target_glow * 2, target_glow * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf3, (*self.color_outer, 120),
                                 (target_glow, target_glow), target_glow)
                surface.blit(glow_surf3, (int(self.target_x - target_glow),
                                         int(self.target_y - target_glow)))

        elif self.phase == "hold":
            # Draw full tension - bright line from source to target
            pygame.draw.line(surface, self.color_bright,
                          (int(self.source_x), int(self.source_y)),
                          (int(self.target_x), int(self.target_y)), 3)

            # Pulsing glow at both ends
            pulse = 0.7 + 0.3 * math.sin(self.timer * 30)
            for x, y in [(self.source_x, self.source_y), (self.target_x, self.target_y)]:
                glow_radius = int(15 * pulse)
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_bright, 200),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(x - glow_radius), int(y - glow_radius)))

        elif self.phase == "appear":
            # Draw arrival flash at destination
            progress = self.timer / self.appear_duration
            if progress < 0.5:
                flash_alpha = int(255 * (1.0 - progress / 0.5))
                flash_radius = int(40 * (1.0 + progress * 2))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_bright, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(self.target_x - flash_radius),
                                         int(self.target_y - flash_radius)))

            # Draw delta symbol at target
            size = int(20 * (1.0 - progress))
            if size > 3:
                points = [
                    (int(self.target_x), int(self.target_y - size)),
                    (int(self.target_x - size * 0.866), int(self.target_y + size * 0.5)),
                    (int(self.target_x + size * 0.866), int(self.target_y + size * 0.5))
                ]
                alpha = int(255 * (1.0 - progress))
                pygame.draw.polygon(surface, (*self.color_inner, alpha), points, 3)


class GraeExchangeAnimation:
    """
    Græ Exchange animation - splits into an echo and teleports away.
    The unit appears to phase/split, leaving a ghostly echo behind.
    """

    def __init__(self, caster_unit, target_pos, particle_emitter):
        """
        Args:
            caster_unit: AnimatedUnit performing the exchange
            target_pos: Target grid position (grid_x, grid_y)
            particle_emitter: ParticleEmitter for spawning particles
        """
        self.caster_unit = caster_unit
        self.target_grid_x, self.target_grid_y = target_pos
        self.particle_emitter = particle_emitter

        # Convert grid to screen coordinates
        from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
        self.source_x = caster_unit.x
        self.source_y = caster_unit.y
        self.target_x = GRID_OFFSET_X + target_pos[0] * TILE_SIZE + TILE_SIZE // 2
        self.target_y = GRID_OFFSET_Y + target_pos[1] * TILE_SIZE + TILE_SIZE // 2

        # Animation phases
        self.phase = "ritual"  # ritual, split, teleport_out, teleport_in
        self.timer = 0
        self.ritual_duration = 0.4
        self.split_duration = 0.5
        self.teleport_out_duration = 0.2
        self.teleport_in_duration = 0.3

        # Purple/lavender colors from Grayman's orbs
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_ghost = (170, 119, 255, 120)  # Semi-transparent for echo
        self.color_bright = (255, 255, 255)

        # Split effect - dual images offset from center
        self.split_offset = 0  # How far apart the split images are

        # Flags
        self.ritual_particles_spawned = False
        self.split_particles_spawned = False
        self.teleported = False
        self.teleport_particles_spawned = False

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == "ritual":
            # Ritual phase - building energy
            if not self.ritual_particles_spawned:
                # Spawn ritual particles swirling around
                for i in range(16):
                    angle = (i / 16) * 2 * math.pi
                    distance = 40
                    x = self.source_x + math.cos(angle) * distance
                    y = self.source_y + math.sin(angle) * distance
                    # Particles orbit around caster
                    vx = -math.sin(angle) * 80
                    vy = math.cos(angle) * 80
                    color = self.color_outer if i % 2 == 0 else self.color_inner
                    particle = Particle(x, y, vx, vy, lifetime=0.4, size=3, color=color)
                    self.particle_emitter.particles.append(particle)
                self.ritual_particles_spawned = True

            if self.timer >= self.ritual_duration:
                self.phase = "split"
                self.timer = 0

        elif self.phase == "split":
            # Split phase - unit appears to duplicate/phase
            progress = self.timer / self.split_duration
            self.split_offset = 20 * progress  # Max 20 pixel offset

            # Spawn particles during split
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                offset = random.uniform(5, 25)
                x = self.source_x + math.cos(angle) * offset
                y = self.source_y + math.sin(angle) * offset
                vx = math.cos(angle) * 50
                vy = math.sin(angle) * 50
                color = self.color_inner
                particle = Particle(x, y, vx, vy, lifetime=0.3, size=3, color=color)
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.split_duration:
                self.phase = "teleport_out"
                self.timer = 0

        elif self.phase == "teleport_out":
            # Teleport out - one copy vanishes (the real unit leaves)
            if not self.teleported:
                # Hide caster (will reappear at target)
                self.caster_unit.visible = False
                self.teleported = True

                # Spawn vanishing particles
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(80, 150)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = self.color_outer
                    particle = Particle(self.source_x, self.source_y, vx, vy,
                                      lifetime=0.4, size=4, color=color)
                    self.particle_emitter.particles.append(particle)

            if self.timer >= self.teleport_out_duration:
                self.phase = "teleport_in"
                self.timer = 0

        elif self.phase == "teleport_in":
            # Appear at destination
            if not self.teleport_particles_spawned:
                # Move caster to target position
                self.caster_unit.grid_x = self.target_grid_x
                self.caster_unit.grid_y = self.target_grid_y
                self.caster_unit.x = self.target_x
                self.caster_unit.y = self.target_y
                self.caster_unit.visible = True

                # Spawn arrival particles
                for _ in range(25):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(60, 180)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_outer, self.color_inner, self.color_bright])
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.5, size=4, color=color)
                    self.particle_emitter.particles.append(particle)

                # Ring of particles
                for i in range(10):
                    angle = (i / 10) * 2 * math.pi
                    vx = math.cos(angle) * 120
                    vy = math.sin(angle) * 120
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.4, size=3, color=self.color_inner)
                    self.particle_emitter.particles.append(particle)

                self.teleport_particles_spawned = True

            if self.timer >= self.teleport_in_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the Græ Exchange animation."""
        if self.phase == "ritual":
            # Draw swirling energy around caster
            progress = self.timer / self.ritual_duration

            # Pulsing glow
            glow_radius = int(25 + 10 * math.sin(self.timer * 12))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_outer, int(100 * progress)),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Draw rotating circle
            num_dots = 8
            for i in range(num_dots):
                angle = (i / num_dots) * 2 * math.pi + self.timer * 5
                radius = 30
                x = self.source_x + math.cos(angle) * radius
                y = self.source_y + math.sin(angle) * radius
                pygame.draw.circle(surface, self.color_inner, (int(x), int(y)), 3)

        elif self.phase == "split":
            # Draw two overlapping copies of the unit position (indicating split)
            progress = self.timer / self.split_duration

            # Left copy (will become echo - more transparent)
            left_x = self.source_x - self.split_offset
            left_y = self.source_y
            left_alpha = int(180 - 100 * progress)  # Fades to echo transparency
            left_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(left_surf, (*self.color_outer, left_alpha), (20, 20), 15)
            surface.blit(left_surf, (int(left_x - 20), int(left_y - 20)))

            # Right copy (will teleport - solid)
            right_x = self.source_x + self.split_offset
            right_y = self.source_y
            right_alpha = 255
            right_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(right_surf, (*self.color_inner, right_alpha), (20, 20), 15)
            surface.blit(right_surf, (int(right_x - 20), int(right_y - 20)))

            # Draw connecting energy between the two
            if self.split_offset > 5:
                pygame.draw.line(surface, self.color_bright,
                              (int(left_x), int(left_y)),
                              (int(right_x), int(right_y)), 2)

        elif self.phase == "teleport_out":
            # Draw fading echo at source (the copy that stays)
            progress = self.timer / self.teleport_out_duration
            echo_alpha = int(120 * (1.0 - progress * 0.5))  # Fades but remains visible

            echo_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            # Draw ghostly echo
            pygame.draw.circle(echo_surf, (*self.color_outer, echo_alpha), (25, 25), 18)
            pygame.draw.circle(echo_surf, (*self.color_inner, echo_alpha), (25, 25), 12, 2)
            surface.blit(echo_surf, (int(self.source_x - 25), int(self.source_y - 25)))

        elif self.phase == "teleport_in":
            # Draw arrival flash at destination
            progress = self.timer / self.teleport_in_duration
            if progress < 0.5:
                flash_alpha = int(255 * (1.0 - progress / 0.5))
                flash_radius = int(35 * (1.0 + progress * 2))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_bright, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(self.target_x - flash_radius),
                                         int(self.target_y - flash_radius)))


class EstrangeBeam:
    """
    Reality-warping beam that phases target out of normal spacetime.
    Uses purple/lavender colors matching Grayman's glowing orbs.
    """

    def __init__(self, source_x, source_y, target_x, target_y, particle_emitter):
        self.source_x = source_x
        self.source_y = source_y
        self.target_x = target_x
        self.target_y = target_y
        self.particle_emitter = particle_emitter

        # Animation timing
        self.phase = "charge"  # charge, beam, impact, fade
        self.timer = 0
        self.charge_duration = 0.3
        self.beam_duration = 0.4
        self.impact_duration = 0.3
        self.fade_duration = 0.2

        # Visual properties
        self.beam_width = 0
        self.max_beam_width = 12  # Thinner beam

        # Purple/lavender colors from Grayman's orbs
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_bright = (255, 255, 255)  # bright flash

        # Pulsation effect
        self.pulse_timer = 0

        # Warping effect
        self.warp_offset = []
        self.generate_warp_points()

        # Impact particles spawned flag
        self.impact_spawned = False

    def generate_warp_points(self):
        """Generate sine wave distortion points along beam path."""
        # Calculate vector from source to target
        dx = self.target_x - self.source_x
        dy = self.target_y - self.source_y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance == 0:
            return

        # Generate warp points along the beam
        num_points = int(distance / 10) + 2
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            # Multiple sine waves for complex waving motion
            # Combine two sine waves with different frequencies for more organic movement
            wave1 = math.sin(t * math.pi * 4 + self.timer * 15) * 15
            wave2 = math.sin(t * math.pi * 2.5 - self.timer * 8) * 10
            offset = wave1 + wave2
            self.warp_offset.append(offset)

    def update(self, delta_time):
        """Update beam animation state."""
        self.timer += delta_time
        self.pulse_timer += delta_time

        # Update warp points for animated distortion
        self.generate_warp_points()

        if self.phase == "charge":
            # Charging phase - building up energy
            if self.timer >= self.charge_duration:
                self.phase = "beam"
                self.timer = 0

                # Spawn charging particles at source
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    # Purple/lavender particle colors
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(self.source_x, self.source_y, vx, vy,
                                      lifetime=0.3, size=4, color=color)
                    self.particle_emitter.particles.append(particle)

        elif self.phase == "beam":
            # Beam firing phase - grow beam width
            progress = self.timer / self.beam_duration
            self.beam_width = self.max_beam_width * min(1.0, progress * 2)

            # Spawn beam particles along path
            if random.random() < 0.3:
                t = random.uniform(0.2, 0.8)
                x = self.source_x + (self.target_x - self.source_x) * t
                y = self.source_y + (self.target_y - self.source_y) * t

                # Perpendicular offset
                dx = self.target_x - self.source_x
                dy = self.target_y - self.source_y
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length
                    perp_y = dx / length
                    offset = random.uniform(-15, 15)
                    x += perp_x * offset
                    y += perp_y * offset

                color = self.color_outer if random.random() > 0.3 else self.color_inner
                particle = Particle(x, y, 0, 0, lifetime=0.2, size=3, color=color)
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.beam_duration:
                self.phase = "impact"
                self.timer = 0

        elif self.phase == "impact":
            # Impact phase - hit target
            if not self.impact_spawned:
                # Spawn impact particles
                for _ in range(25):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(100, 250)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_outer, self.color_inner, self.color_bright])
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.4, size=5, color=color)
                    self.particle_emitter.particles.append(particle)

                # Spawn warping/phasing particles that spiral
                for i in range(20):
                    angle = (i / 20) * 2 * math.pi
                    distance = random.uniform(20, 60)
                    x = self.target_x + math.cos(angle) * distance
                    y = self.target_y + math.sin(angle) * distance
                    # Particles move inward toward target
                    vx = -math.cos(angle) * 80
                    vy = -math.sin(angle) * 80
                    color = self.color_inner
                    particle = Particle(x, y, vx, vy, lifetime=0.5, size=3, color=color)
                    self.particle_emitter.particles.append(particle)

                self.impact_spawned = True

            if self.timer >= self.impact_duration:
                self.phase = "fade"
                self.timer = 0

        elif self.phase == "fade":
            # Fade out phase
            progress = self.timer / self.fade_duration
            self.beam_width = self.max_beam_width * (1.0 - progress)

            if self.timer >= self.fade_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the estrangement beam with warping effect."""
        if self.phase == "charge":
            # Draw charging glow at source
            progress = self.timer / self.charge_duration
            glow_radius = int(15 * progress)

            # Outer glow
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_outer, int(100 * progress)),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Inner glow
            inner_radius = int(glow_radius * 0.6)
            glow_surf2 = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf2, (*self.color_inner, int(150 * progress)),
                             (inner_radius, inner_radius), inner_radius)
            surface.blit(glow_surf2, (int(self.source_x - inner_radius),
                                     int(self.source_y - inner_radius)))

        elif self.phase in ["beam", "impact", "fade"]:
            # Draw warped beam
            if self.beam_width > 2:
                # Calculate pulsating brightness (oscillates between 0.6 and 1.0)
                pulse_factor = 0.6 + 0.4 * (math.sin(self.pulse_timer * 20) * 0.5 + 0.5)

                # Calculate beam direction
                dx = self.target_x - self.source_x
                dy = self.target_y - self.source_y
                distance = math.sqrt(dx*dx + dy*dy)

                if distance > 0:
                    # Perpendicular vector for width
                    perp_x = -dy / distance
                    perp_y = dx / distance

                    # Draw beam as series of warped segments
                    num_segments = len(self.warp_offset)
                    if num_segments > 1:
                        for i in range(num_segments - 1):
                            t1 = i / (num_segments - 1)
                            t2 = (i + 1) / (num_segments - 1)

                            # Base positions along beam
                            x1 = self.source_x + dx * t1
                            y1 = self.source_y + dy * t1
                            x2 = self.source_x + dx * t2
                            y2 = self.source_y + dy * t2

                            # Apply warp offset
                            offset1 = self.warp_offset[i]
                            offset2 = self.warp_offset[i + 1]

                            x1 += perp_x * offset1
                            y1 += perp_y * offset1
                            x2 += perp_x * offset2
                            y2 += perp_y * offset2

                            # Apply pulse factor to colors
                            pulsed_outer = tuple(int(c * pulse_factor) for c in self.color_outer)
                            pulsed_inner = tuple(int(c * pulse_factor) for c in self.color_inner)
                            pulsed_bright = tuple(int(c * pulse_factor) for c in self.color_bright)

                            # Draw thick outer beam
                            pygame.draw.line(surface, pulsed_outer,
                                          (int(x1), int(y1)), (int(x2), int(y2)),
                                          int(self.beam_width))

                            # Draw thinner inner beam
                            pygame.draw.line(surface, pulsed_inner,
                                          (int(x1), int(y1)), (int(x2), int(y2)),
                                          int(self.beam_width * 0.5))

                            # Draw bright core
                            if self.phase == "beam":
                                pygame.draw.line(surface, pulsed_bright,
                                              (int(x1), int(y1)), (int(x2), int(y2)), 2)

        # Draw impact flash
        if self.phase == "impact":
            flash_progress = self.timer / self.impact_duration
            if flash_progress < 0.3:  # Flash for first 30% of impact phase
                flash_alpha = int(255 * (1.0 - flash_progress / 0.3))
                flash_radius = int(30 * (1.0 + flash_progress))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_bright, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(self.target_x - flash_radius),
                                         int(self.target_y - flash_radius)))
