#!/usr/bin/env python3
"""
GLAIVEMAN Animation Classes
Skill animations for the GLAIVEMAN unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, Particle, DebrisParticle
from boneglaive.graphical.sound_helper import play_sound

class LightningBolt:
    """A lightning bolt effect that strikes from above."""
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.segments = []
        self.lifetime = 0.4
        self.max_lifetime = 0.4
        self.flash_intensity = 255
        self.generate_bolt()

    def generate_bolt(self):
        """Generate jagged lightning path from top of screen to target."""
        # Start from top of screen
        start_y = 0
        current_x = self.target_x
        current_y = start_y

        # Generate segments with random jagged offsets
        while current_y < self.target_y:
            # Move down
            next_y = current_y + random.uniform(15, 40)
            # Random horizontal offset for jagged effect
            next_x = current_x + random.uniform(-25, 25)

            # Clamp next_y to target
            if next_y > self.target_y:
                next_y = self.target_y
                next_x = self.target_x

            self.segments.append(((current_x, current_y), (next_x, next_y)))
            current_x = next_x
            current_y = next_y

    def update(self, delta_time):
        """Update lightning animation."""
        self.lifetime -= delta_time
        # Flash effect - flicker intensity
        self.flash_intensity = int(255 * (self.lifetime / self.max_lifetime))
        if self.lifetime < 0.2:
            self.flash_intensity = int(255 * random.uniform(0.5, 1.0) * (self.lifetime / self.max_lifetime))
        return self.lifetime > 0

    def draw(self, surface):
        """Draw the lightning bolt with multiple layers."""
        if self.lifetime <= 0:
            return

        alpha = int(255 * (self.lifetime / self.max_lifetime))

        # Draw multiple bolts for thickness/glow effect
        for thickness, color_mod in [(6, 0.3), (4, 0.6), (2, 1.0)]:
            for (x1, y1), (x2, y2) in self.segments:
                # Main bolt color (bright white/yellow)
                color = (
                    int(255 * color_mod),
                    int(255 * color_mod),
                    int(200 * color_mod),
                    min(alpha, 255)
                )

                # Create a surface for this segment with alpha
                segment_surf = pygame.Surface((abs(x2-x1)+thickness*2, abs(y2-y1)+thickness*2), pygame.SRCALPHA)
                local_x1 = thickness
                local_y1 = thickness
                local_x2 = local_x1 + (x2 - x1)
                local_y2 = local_y1 + (y2 - y1)

                pygame.draw.line(segment_surf, color,
                               (local_x1, local_y1), (local_x2, local_y2), thickness)

                # Blit to main surface
                segment_rect = segment_surf.get_rect(topleft=(min(x1, x2) - thickness, min(y1, y2) - thickness))
                surface.blit(segment_surf, segment_rect)

        # Draw bright core
        for (x1, y1), (x2, y2) in self.segments:
            pygame.draw.line(surface, (255, 255, 255, alpha), (int(x1), int(y1)), (int(x2), int(y2)), 1)


class CrossBeam:
    """Expanding cross-shaped beam for Autoclave skill."""
    def __init__(self, center_x, center_y, direction, max_range=3):
        """
        direction: 0=up, 1=right, 2=down, 3=left
        max_range: number of tiles to expand
        """
        self.center_x = center_x
        self.center_y = center_y
        self.direction = direction
        self.max_range = max_range * TILE_SIZE
        self.current_range = 0
        self.expand_speed = 600  # pixels per second
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.width = 20
        self.active = True

    def update(self, delta_time):
        """Update beam expansion."""
        if self.current_range < self.max_range:
            self.current_range += self.expand_speed * delta_time
            if self.current_range > self.max_range:
                self.current_range = self.max_range
        else:
            self.lifetime -= delta_time
        return self.lifetime > 0 and self.active

    def get_beam_rect(self):
        """Get the current beam rectangle."""
        if self.direction == 0:  # Up
            return (self.center_x - self.width // 2, self.center_y - self.current_range,
                   self.width, self.current_range)
        elif self.direction == 1:  # Right
            return (self.center_x, self.center_y - self.width // 2,
                   self.current_range, self.width)
        elif self.direction == 2:  # Down
            return (self.center_x - self.width // 2, self.center_y,
                   self.width, self.current_range)
        else:  # Left
            return (self.center_x - self.current_range, self.center_y - self.width // 2,
                   self.current_range, self.width)

    def draw(self, surface):
        """Draw the cross beam as jets of steam with spinning glaive shuriken."""
        if self.lifetime <= 0:
            return

        alpha = int(255 * min(1.0, self.lifetime / self.max_lifetime))

        # Draw steam particles along the beam
        if self.current_range > 10:
            num_steam_particles = int(self.current_range / 15)
            for i in range(num_steam_particles):
                progress = (i / num_steam_particles) if num_steam_particles > 0 else 0

                # Calculate position along beam
                if self.direction == 0:  # Up
                    px = self.center_x + random.uniform(-self.width//2, self.width//2)
                    py = self.center_y - progress * self.current_range
                elif self.direction == 1:  # Right
                    px = self.center_x + progress * self.current_range
                    py = self.center_y + random.uniform(-self.width//2, self.width//2)
                elif self.direction == 2:  # Down
                    px = self.center_x + random.uniform(-self.width//2, self.width//2)
                    py = self.center_y + progress * self.current_range
                else:  # Left
                    px = self.center_x - progress * self.current_range
                    py = self.center_y + random.uniform(-self.width//2, self.width//2)

                # Steam puffs - wispy and white
                steam_size = random.uniform(8, 16) * (1.0 - progress * 0.3)  # Smaller at the end
                steam_alpha = int(alpha * 0.4 * (1.0 - progress * 0.5))  # Fade toward end

                # Multiple overlapping circles for wispy steam effect
                for _ in range(3):
                    offset_x = random.uniform(-steam_size * 0.3, steam_size * 0.3)
                    offset_y = random.uniform(-steam_size * 0.3, steam_size * 0.3)
                    steam_surf = pygame.Surface((int(steam_size * 3), int(steam_size * 3)), pygame.SRCALPHA)
                    pygame.draw.circle(steam_surf, (240, 240, 255, steam_alpha),
                                     (int(steam_size * 1.5 + offset_x), int(steam_size * 1.5 + offset_y)),
                                     int(steam_size))
                    surface.blit(steam_surf, (int(px - steam_size * 1.5), int(py - steam_size * 1.5)))

        # Draw spinning glaive shuriken along the beam path
        if self.current_range > 20:
            num_glaives = max(1, int(self.current_range / 80))  # Fewer glaives
            for i in range(num_glaives):
                progress = ((i + 0.5) / num_glaives) if num_glaives > 0 else 0.5

                # Position along beam
                if self.direction == 0:  # Up
                    gx = self.center_x
                    gy = self.center_y - progress * self.current_range
                elif self.direction == 1:  # Right
                    gx = self.center_x + progress * self.current_range
                    gy = self.center_y
                elif self.direction == 2:  # Down
                    gx = self.center_x
                    gy = self.center_y + progress * self.current_range
                else:  # Left
                    gx = self.center_x - progress * self.current_range
                    gy = self.center_y

                # Draw spinning six-pointed glaive (like in Judgement)
                glaive_size = 16
                rotation = (pygame.time.get_ticks() * 0.5 + i * 60) % 360  # Spinning

                glaive_surf = pygame.Surface((glaive_size * 2, glaive_size * 2), pygame.SRCALPHA)
                center = glaive_size

                # Six blades
                for blade in range(6):
                    angle = math.radians(rotation + blade * 60)
                    # Outer point
                    px1 = center + math.cos(angle) * glaive_size
                    py1 = center + math.sin(angle) * glaive_size
                    # Inner left
                    angle_l = math.radians(rotation + blade * 60 - 15)
                    px2 = center + math.cos(angle_l) * (glaive_size * 0.4)
                    py2 = center + math.sin(angle_l) * (glaive_size * 0.4)
                    # Inner right
                    angle_r = math.radians(rotation + blade * 60 + 15)
                    px3 = center + math.cos(angle_r) * (glaive_size * 0.4)
                    py3 = center + math.sin(angle_r) * (glaive_size * 0.4)

                    # Draw blade triangle
                    pygame.draw.polygon(glaive_surf, (200, 200, 220, alpha),
                                      [(px1, py1), (px2, py2), (px3, py3)])
                    pygame.draw.polygon(glaive_surf, (255, 255, 255, alpha),
                                      [(px1, py1), (px2, py2), (px3, py3)], 1)

                # Center hub
                pygame.draw.circle(glaive_surf, (180, 180, 200, alpha), (center, center), int(glaive_size * 0.3))
                pygame.draw.circle(glaive_surf, (255, 255, 255, alpha), (center, center), int(glaive_size * 0.3), 2)

                surface.blit(glaive_surf, (int(gx - glaive_size), int(gy - glaive_size)))


class AutoclaveAnimation:
    """Full Autoclave animation with 4 expanding cross beams."""
    def __init__(self, center_x, center_y, max_range=3):
        """
        Create all 4 beams (up, right, down, left) for Autoclave passive.

        Args:
            center_x, center_y: Screen pixel coordinates of GLAIVEMAN
            max_range: Number of tiles to expand (default 3)
        """
        self.center_x = center_x
        self.center_y = center_y
        self.beams = []

        # Create 4 cross beams (one in each direction)
        for direction in range(4):
            beam = CrossBeam(center_x, center_y, direction, max_range)
            self.beams.append(beam)

        # Central flash effect
        self.flash_timer = 0.3
        self.max_flash_timer = 0.3

    def update(self, delta_time):
        """Update all beams."""
        # Update flash timer
        if self.flash_timer > 0:
            self.flash_timer -= delta_time

        # Update all beams
        all_finished = True
        for beam in self.beams:
            if beam.update(delta_time):
                all_finished = False

        return not all_finished

    def draw(self, surface):
        """Draw central flash and all 4 beams."""
        # Draw central activation flash
        if self.flash_timer > 0:
            flash_alpha = int(255 * (self.flash_timer / self.max_flash_timer))
            flash_radius = int(40 * (1.0 - self.flash_timer / self.max_flash_timer))

            # Create flash surface
            flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)

            # Draw multiple overlapping circles for glow effect
            for i in range(3):
                radius = flash_radius - i * 5
                alpha = flash_alpha // (i + 1)
                pygame.draw.circle(flash_surf, (255, 255, 255, alpha),
                                 (flash_radius, flash_radius), radius)

            flash_rect = flash_surf.get_rect(center=(int(self.center_x), int(self.center_y)))
            surface.blit(flash_surf, flash_rect)

        # Draw all beams
        for beam in self.beams:
            beam.draw(surface)


class SpinningGlaiveProjectile:
    """A spinning glaive projectile that travels from attacker to target."""
    def __init__(self, start_x, start_y, target_x, target_y, speed=600, is_crit=False):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.rotation = 0
        self.rotation_speed = 1080  # degrees per second (3 full rotations)
        self.active = True
        self.trail_positions = []
        self.is_crit = is_crit
        self.impact_triggered = False  # Track if impact effect has been triggered

        # Calculate direction
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            self.vx = (dx / distance) * speed
            self.vy = (dy / distance) * speed
        else:
            self.vx = 0
            self.vy = 0

        # Create glaive sprite (six-pointed spinning blade)
        self.size = 32
        self.create_glaive_surface()

    def create_glaive_surface(self):
        """Create the spinning glaive sprite."""
        self.base_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2

        # Golden/white color scheme
        bright_yellow = (255, 255, 204)  # #ffffcc
        white = (255, 255, 255)
        white = (255, 255, 255)

        # Draw six pointed blades radiating from center
        blade_length = self.size // 2 - 2
        for i in range(6):
            angle = (i * 60) * math.pi / 180

            # Blade tip
            tip_x = center + math.cos(angle) * blade_length
            tip_y = center + math.sin(angle) * blade_length

            # Blade sides (slightly offset for width)
            angle_offset = 15 * math.pi / 180
            side1_x = center + math.cos(angle - angle_offset) * (blade_length * 0.7)
            side1_y = center + math.sin(angle - angle_offset) * (blade_length * 0.7)
            side2_x = center + math.cos(angle + angle_offset) * (blade_length * 0.7)
            side2_y = center + math.sin(angle + angle_offset) * (blade_length * 0.7)

            # Draw blade triangle
            pygame.draw.polygon(self.base_surface, bright_yellow,
                              [(center, center), (tip_x, tip_y), (side1_x, side1_y)])
            pygame.draw.polygon(self.base_surface, bright_yellow,
                              [(center, center), (tip_x, tip_y), (side2_x, side2_y)])

            # Highlight edge
            pygame.draw.line(self.base_surface, white,
                           (center, center), (tip_x, tip_y), 2)

        # Center hub
        pygame.draw.circle(self.base_surface, white, (center, center), 6)
        pygame.draw.circle(self.base_surface, bright_yellow, (center, center), 6, 2)
        pygame.draw.circle(self.base_surface, (200, 180, 0), (center, center), 3)

    def update(self, delta_time):
        """Update projectile position and rotation."""
        if not self.active:
            return False

        # Store position for trail
        self.trail_positions.append((self.x, self.y, self.rotation))
        if len(self.trail_positions) > 8:
            self.trail_positions.pop(0)

        # Move towards target
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        # Rotate
        self.rotation += self.rotation_speed * delta_time

        # Check if reached target (within small distance)
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance < self.speed * delta_time:
            # Reached target - trigger impact
            if not self.impact_triggered:
                self.impact_triggered = True
                # Set flag for renderer to create impact effects
                self.trigger_impact = True
            self.active = False
            return False

        return True

    def draw(self, surface):
        """Draw the spinning glaive with motion blur trail."""
        if not self.active:
            return

        # Draw motion blur trail
        for i, (trail_x, trail_y, trail_rot) in enumerate(self.trail_positions):
            alpha = int(100 * (i / len(self.trail_positions)))
            trail_surface = pygame.transform.rotate(self.base_surface, trail_rot)
            trail_surface.set_alpha(alpha)
            trail_rect = trail_surface.get_rect(center=(int(trail_x), int(trail_y)))
            surface.blit(trail_surface, trail_rect)

        # Draw main glaive
        rotated_surface = pygame.transform.rotate(self.base_surface, self.rotation)
        rect = rotated_surface.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_surface, rect)

        # Add glow effect
        glow_surf = pygame.Surface((self.size + 20, self.size + 20), pygame.SRCALPHA)
        glow_radius = self.size // 2 + 10
        pygame.draw.circle(glow_surf, (255, 255, 204, 50),
                          (glow_radius, glow_radius), glow_radius)
        glow_rect = glow_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(glow_surf, glow_rect)


class VaultAnimationController:
    """
    Controller for VAULT animation - acrobatic leap with 360-degree flip.
    Uses attribute-based animation (manipulates caster position during vault).
    """

    def __init__(self, caster_unit, target_pos, particle_emitter, screen_shake_callback, camera=None):
        """
        Args:
            caster_unit: AnimatedUnit performing the vault
            target_pos: Tuple (grid_x, grid_y) destination
            particle_emitter: ParticleEmitter for effects
            screen_shake_callback: Function(intensity, duration)
            camera: Camera instance for coordinate conversion (optional, will use defaults)
        """
        self.caster = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.camera = camera

        # Set up vault animation state
        self.caster.vault_phase = "vaulting"
        self.caster.vault_timer = 0
        self.caster.vault_duration = 0.6  # Total vault time
        self.caster.vault_start_x = caster_unit.x
        self.caster.vault_start_y = caster_unit.y
        self.caster.wind_up_rotation = 0  # Initialize rotation for flip

        # Calculate target screen position using camera
        # NOTE: target_pos is (grid_y, grid_x) format from renderer
        target_grid_y, target_grid_x = target_pos
        if self.camera:
            self.caster.vault_target_x, self.caster.vault_target_y = self.camera.grid_to_screen(target_grid_x, target_grid_y)
        else:
            # Fallback to defaults
            from .core import TILE_SIZE
            GRID_OFFSET_X = 100
            GRID_OFFSET_Y = 50
            self.caster.vault_target_x = GRID_OFFSET_X + target_grid_x * TILE_SIZE + TILE_SIZE // 2
            self.caster.vault_target_y = GRID_OFFSET_Y + target_grid_y * TILE_SIZE + TILE_SIZE // 2
        self.caster.vault_target_grid_x = target_grid_x
        self.caster.vault_target_grid_y = target_grid_y


        # Launch sound - leap off ground
        play_sound("vault_launch")

        # Launch particles
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particle_emitter.particles.append(
                Particle(caster_unit.x, caster_unit.y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        (100, 200, 255), random.uniform(2, 5), 0.4)
            )

        self.active = True

    def update(self, delta_time):
        """Update vault animation - returns True if still active."""
        if not self.active:
            return False

        if hasattr(self.caster, 'vault_phase') and self.caster.vault_phase == "vaulting":
            self.caster.vault_timer += delta_time
            progress = min(1.0, self.caster.vault_timer / self.caster.vault_duration)

            # Horizontal movement (linear interpolation)
            self.caster.x = self.caster.vault_start_x + (self.caster.vault_target_x - self.caster.vault_start_x) * progress
            base_y = self.caster.vault_start_y + (self.caster.vault_target_y - self.caster.vault_start_y) * progress

            # Vertical arc (parabolic jump)
            arc_height = 120  # Peak height of jump
            vertical_offset = math.sin(progress * math.pi) * arc_height
            self.caster.y = base_y - vertical_offset

            # FLIP ROTATION - Complete 360 degree rotation during vault
            self.caster.wind_up_rotation = progress * 360  # Full rotation

            # Landing phase
            if progress >= 1.0:
                self.caster.vault_phase = "landing"
                self.caster.vault_timer = 0
                # Snap to target grid position
                self.caster.grid_x = self.caster.vault_target_grid_x
                self.caster.grid_y = self.caster.vault_target_grid_y
                self.caster.x = self.caster.vault_target_x
                self.caster.y = self.caster.vault_target_y
                self.caster.wind_up_rotation = 0  # Reset rotation

                # Landing sound
                play_sound("vault_land")

                # Landing effects
                self.particle_emitter.emit_burst(self.caster.x, self.caster.y, (100, 200, 255), 30)
                self.screen_shake(5, 0.2)

                # Dust cloud on landing
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(30, 80)
                    particle = Particle(self.caster.x, self.caster.y + 20,
                                       math.cos(angle) * speed, math.sin(angle) * speed - 10,
                                       (180, 180, 200), random.uniform(4, 8), 0.6)
                    particle.gravity = 100
                    self.particle_emitter.particles.append(particle)

        elif hasattr(self.caster, 'vault_phase') and self.caster.vault_phase == "landing":
            # Brief landing recovery (0.1s)
            self.caster.vault_timer += delta_time
            if self.caster.vault_timer >= 0.1:
                self.caster.vault_phase = None
                self.active = False

        return self.active

    def draw(self, surface):
        """No additional drawing needed - unit renders itself with rotation."""
        pass


class VaultAnimationControllerUpgraded:
    """
    Controller for UPGRADED VAULT animation - extended acrobatic leap with double flip.
    Enhanced version with 720-degree rotation, higher arc, enhanced trail, and stronger landing.
    Uses attribute-based animation (manipulates caster position during vault).
    """

    def __init__(self, caster_unit, target_pos, particle_emitter, screen_shake_callback, camera=None):
        """
        Args:
            caster_unit: AnimatedUnit performing the vault
            target_pos: Tuple (grid_x, grid_y) destination
            particle_emitter: ParticleEmitter for effects
            screen_shake_callback: Function(intensity, duration)
            camera: Camera instance for coordinate conversion (optional, will use defaults)
        """
        self.caster = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.camera = camera

        # Set up vault animation state
        self.caster.vault_phase = "vaulting"
        self.caster.vault_timer = 0
        self.caster.vault_duration = 0.8  # Longer duration for extended vault (was 0.6)
        self.caster.vault_start_x = caster_unit.x
        self.caster.vault_start_y = caster_unit.y
        self.caster.wind_up_rotation = 0  # Initialize rotation for double flip

        # Calculate target screen position using camera
        # NOTE: target_pos is (grid_y, grid_x) format from renderer
        target_grid_y, target_grid_x = target_pos
        if self.camera:
            self.caster.vault_target_x, self.caster.vault_target_y = self.camera.grid_to_screen(target_grid_x, target_grid_y)
        else:
            # Fallback to defaults
            from .core import TILE_SIZE
            GRID_OFFSET_X = 100
            GRID_OFFSET_Y = 50
            self.caster.vault_target_x = GRID_OFFSET_X + target_grid_x * TILE_SIZE + TILE_SIZE // 2
            self.caster.vault_target_y = GRID_OFFSET_Y + target_grid_y * TILE_SIZE + TILE_SIZE // 2
        self.caster.vault_target_grid_x = target_grid_x
        self.caster.vault_target_grid_y = target_grid_y


        # Launch sound (upgraded version)
        play_sound("vault_launch_upgraded")

        # Enhanced launch particles (more particles, brighter colors)
        for _ in range(35):  # Was 20
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(70, 200)  # Faster particles
            self.particle_emitter.particles.append(
                Particle(caster_unit.x, caster_unit.y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        (150, 220, 255), random.uniform(3, 7), 0.5)  # Brighter blue, larger
            )

        # Launch screen shake (stronger than regular vault)
        self.screen_shake(6, 0.3)

        self.active = True
        self.trail_timer = 0  # Timer for continuous particle trail

    def update(self, delta_time):
        """Update vault animation - returns True if still active."""
        if not self.active:
            return False

        if hasattr(self.caster, 'vault_phase') and self.caster.vault_phase == "vaulting":
            self.caster.vault_timer += delta_time
            self.trail_timer += delta_time
            progress = min(1.0, self.caster.vault_timer / self.caster.vault_duration)

            # Horizontal movement (linear interpolation)
            self.caster.x = self.caster.vault_start_x + (self.caster.vault_target_x - self.caster.vault_start_x) * progress
            base_y = self.caster.vault_start_y + (self.caster.vault_target_y - self.caster.vault_start_y) * progress

            # ENHANCED vertical arc (higher peak for extended vault)
            arc_height = 180  # Increased from 120 for more dramatic arc
            vertical_offset = math.sin(progress * math.pi) * arc_height
            self.caster.y = base_y - vertical_offset

            # DOUBLE FLIP ROTATION - Complete 720 degree rotation (two full spins)
            self.caster.wind_up_rotation = progress * 720  # Double rotation (was 360)

            # Enhanced continuous particle trail during flight
            if self.trail_timer >= 0.02:  # Emit trail every 0.02 seconds
                self.trail_timer = 0
                # Bright trail particles following the arc
                for _ in range(3):  # More particles per emission
                    self.particle_emitter.particles.append(
                        Particle(self.caster.x, self.caster.y,
                                random.uniform(-20, 20), random.uniform(-20, 20),
                                (100, 200, 255), random.uniform(4, 6), 0.3)
                    )

            # Landing phase
            if progress >= 1.0:
                self.caster.vault_phase = "landing"
                self.caster.vault_timer = 0
                # Snap to target grid position
                self.caster.grid_x = self.caster.vault_target_grid_x
                self.caster.grid_y = self.caster.vault_target_grid_y
                self.caster.x = self.caster.vault_target_x
                self.caster.y = self.caster.vault_target_y
                self.caster.wind_up_rotation = 0  # Reset rotation

                # Landing sound (upgraded version - stronger impact)
                play_sound("vault_impact")

                # ENHANCED landing effects (stronger impact)
                self.particle_emitter.emit_burst(self.caster.x, self.caster.y, (100, 200, 255), 50)  # More particles (was 30)
                self.screen_shake(8, 0.3)  # Stronger shake (was 5, 0.2)

                # Larger dust cloud on landing
                for _ in range(25):  # More dust (was 15)
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 120)  # Faster spread
                    particle = Particle(self.caster.x, self.caster.y + 20,
                                       math.cos(angle) * speed, math.sin(angle) * speed - 10,
                                       (180, 180, 200), random.uniform(5, 10), 0.7)  # Larger particles
                    particle.gravity = 100
                    self.particle_emitter.particles.append(particle)

                # Shockwave ring (expanding ring of particles)
                for i in range(30):  # Ring of particles
                    angle = (i / 30) * 2 * math.pi
                    speed = 200
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    particle = Particle(self.caster.x, self.caster.y, vx, vy,
                                      (150, 220, 255), 4, 0.4)
                    self.particle_emitter.particles.append(particle)

                # AOE impact effects on all 8 adjacent tiles
                # Calculate adjacent tile positions using camera
                adjacent_offsets = [
                    (-1, -1), (-1, 0), (-1, 1),  # Top row
                    (0, -1),           (0, 1),   # Middle row (skip center)
                    (1, -1),  (1, 0),  (1, 1)    # Bottom row
                ]

                if self.camera:
                    for dy, dx in adjacent_offsets:
                        adj_grid_x = self.caster.vault_target_grid_x + dx
                        adj_grid_y = self.caster.vault_target_grid_y + dy
                        adj_x, adj_y = self.camera.grid_to_screen(adj_grid_x, adj_grid_y, centered=True)

                        # Impact burst on each adjacent tile
                        self.particle_emitter.emit_burst(adj_x, adj_y, (120, 200, 255), 15)

                        # Ground crack particles radiating from center tile to adjacent
                        for _ in range(5):
                            # Particles travel from center to adjacent tile
                            t = random.uniform(0.3, 0.7)
                            start_x = self.caster.x + (adj_x - self.caster.x) * t
                            start_y = self.caster.y + (adj_y - self.caster.y) * t
                            vx = (adj_x - self.caster.x) * 0.3
                            vy = (adj_y - self.caster.y) * 0.3
                            particle = Particle(start_x, start_y, vx, vy,
                                              (160, 160, 180), random.uniform(3, 6), 0.5)
                            particle.gravity = 50
                            self.particle_emitter.particles.append(particle)

        elif hasattr(self.caster, 'vault_phase') and self.caster.vault_phase == "landing":
            # Brief landing recovery (0.15s, slightly longer for upgraded)
            self.caster.vault_timer += delta_time
            if self.caster.vault_timer >= 0.15:
                self.caster.vault_phase = None
                self.active = False

        return self.active

    def draw(self, surface):
        """No additional drawing needed - unit renders itself with rotation."""
        pass


class GlaiveSweepAnimation:
    """
    Glaive Sweep animation - wide circular arc attack hitting all 8 adjacent tiles.
    Triggered by upgraded Autoclave's second activation.

    Phases:
    1. Windup (0.2s) - GLAIVEMAN pulls back
    2. Sweep (0.6s) - Circular blade arc sweeps through all 8 adjacent tiles
    3. Impact (0.3s) - Impact flashes on all hit tiles

    Total duration: 1.1s
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Glaive Sweep animation.

        Args:
            caster_unit: GLAIVEMAN performing the sweep
            units_list: All units (to find adjacent targets)
            camera: Camera instance for coordinate conversion
        """
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.game = game

        # Get caster screen position
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                             caster_unit.grid_y,
                                                             centered=True)

        # Find all adjacent tiles and enemy units
        self.adjacent_tiles = []
        self.hit_units = []
        adjacent_offsets = [
            (-1, -1), (-1, 0), (-1, 1),  # Top row
            (0, -1),           (0, 1),   # Middle row
            (1, -1),  (1, 0),  (1, 1)    # Bottom row
        ]

        for dy, dx in adjacent_offsets:
            adj_grid_x = caster_unit.grid_x + dx
            adj_grid_y = caster_unit.grid_y + dy
            adj_x, adj_y = camera.grid_to_screen(adj_grid_x, adj_grid_y, centered=True)

            self.adjacent_tiles.append({
                'x': adj_x,
                'y': adj_y,
                'grid_x': adj_grid_x,
                'grid_y': adj_grid_y,
                'dx': dx,
                'dy': dy
            })

            # Check for enemy units at this position
            if units_list:
                for unit in units_list:
                    if (unit.grid_x == adj_grid_x and unit.grid_y == adj_grid_y and
                        unit.player != caster_unit.player):
                        self.hit_units.append(unit)

        # Animation state
        self.phase = "windup"
        self.timer = 0
        self.active = True

        # Phase durations
        self.windup_duration = 0.2
        self.sweep_duration = 0.6
        self.impact_duration = 0.3

        # Arc sweep state
        self.sweep_angle = 0  # Current angle of the sweeping blade (in degrees)
        self.arc_particles = []


        # Start windup
        self._start_windup()

    def _start_windup(self):
        """Phase 1: Windup - pull back the glaive."""
        self.phase = "windup"
        self.timer = 0

        # Windup sound
        play_sound("glaive_sweep_windup")

        # Slight screen shake
        self.screen_shake_callback(4, 0.15)

        # Windup particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (192, 192, 192), count=15)

    def _start_sweep(self):
        """Phase 2: Circular sweep - blade arcs through all adjacent tiles."""
        self.phase = "sweep"
        self.timer = 0
        self.sweep_angle = 0

        # Sweep sound - whooshing blade
        play_sound("glaive_sweep_swing")

        # Medium screen shake during sweep
        self.screen_shake_callback(6, 0.4)

    def _start_impact(self):
        """Phase 3: Impact on all hit tiles."""
        self.phase = "impact"
        self.timer = 0

        # Impact sound
        play_sound("glaive_sweep_impact")

        # Impact effects on each hit unit
        for unit in self.hit_units:
            unit_x, unit_y = self.camera.grid_to_screen(unit.grid_x, unit.grid_y, centered=True)

            # Impact burst
            if self.particle_emitter:
                self.particle_emitter.emit_burst(unit_x, unit_y, (255, 255, 255), count=20)

            # Shake hit units
            unit.shake_intensity = 12

        # Strong final shake
        self.screen_shake_callback(7, 0.2)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "windup":
            if self.timer >= self.windup_duration:
                self._start_sweep()

        elif self.phase == "sweep":
            # Update sweep angle (full 360° rotation)
            progress = self.timer / self.sweep_duration
            self.sweep_angle = progress * 360

            # Emit arc particles continuously
            if self.timer % 0.03 < delta_time:  # Every ~30ms
                # Create particles along the arc
                num_particles = 8
                for i in range(num_particles):
                    angle_offset = (i / num_particles) * 30 - 15  # Spread over 30°
                    angle_rad = math.radians(self.sweep_angle + angle_offset)

                    # Arc radius - reaches diagonal corners of 3x3 grid (sqrt(2) ≈ 1.414)
                    radius = TILE_SIZE * 1.414

                    px = self.caster_x + math.cos(angle_rad) * radius
                    py = self.caster_y + math.sin(angle_rad) * radius

                    # Velocity continues in arc direction
                    speed = 150
                    vx = math.cos(angle_rad) * speed
                    vy = math.sin(angle_rad) * speed

                    # Silver/white blade trail
                    color = random.choice([
                        (192, 192, 192),  # Silver
                        (232, 232, 232),  # Light silver
                        (255, 255, 255),  # White
                    ])

                    particle = Particle(px, py, vx, vy, color, random.uniform(5, 8), 0.2)
                    particle.gravity = 0
                    self.particle_emitter.particles.append(particle)

            if self.timer >= self.sweep_duration:
                self._start_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw the sweeping blade arc."""
        if not self.active:
            return

        if self.phase == "sweep":
            # Draw the sweeping blade as a thick arc
            progress = self.timer / self.sweep_duration

            # Draw thick blade arc
            arc_surf = pygame.Surface((TILE_SIZE * 4, TILE_SIZE * 4), pygame.SRCALPHA)
            center = TILE_SIZE * 2

            # Calculate arc parameters - reaches diagonal corners of 3x3 grid (sqrt(2) ≈ 1.414)
            radius = int(TILE_SIZE * 1.414)
            start_angle = math.radians(self.sweep_angle - 15)  # Arc width
            end_angle = math.radians(self.sweep_angle + 15)

            # Draw thick white/silver arc
            thickness = 8
            for i in range(thickness):
                r = radius - i
                alpha = int(200 * (1 - i / thickness))
                color = (255, 255, 255, alpha)

                # Draw arc segments
                segments = 20
                for j in range(segments):
                    t = j / segments
                    angle = start_angle + (end_angle - start_angle) * t
                    x = center + math.cos(angle) * r
                    y = center + math.sin(angle) * r

                    if j > 0:
                        pygame.draw.line(arc_surf, color, (prev_x, prev_y), (x, y), 3)
                    prev_x, prev_y = x, y

            # Blit arc surface centered on caster
            arc_rect = arc_surf.get_rect(center=(int(self.caster_x), int(self.caster_y)))
            surface.blit(arc_surf, arc_rect)

        elif self.phase == "impact":
            # Flash white rings on each adjacent tile
            alpha = int(255 * (1 - self.timer / self.impact_duration))

            for tile in self.adjacent_tiles:
                ring_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                center = TILE_SIZE // 2
                pygame.draw.circle(ring_surf, (255, 255, 255, alpha), (center, center), TILE_SIZE // 3, 3)

                ring_rect = ring_surf.get_rect(center=(int(tile['x']), int(tile['y'])))
                surface.blit(ring_surf, ring_rect)


class PryImpactAnimation:
    """
    NEW simplified PRY animation - instant impact with particle effects only.
    No unit displacement, faster execution, handles multiple prys cleanly.

    Animation phases:
    1. Flash burst at target (impact flash + upward particles)
    2. Ceiling debris rain (particles fall from above)
    3. Splash damage effects on adjacent units
    """

    def __init__(self, target_unit, caster_unit, particle_emitter,
                 screen_shake_callback, units_list):
        """
        Args:
            target_unit: AnimatedUnit being hit by pry
            caster_unit: AnimatedUnit doing the prying
            particle_emitter: ParticleEmitter for effects
            screen_shake_callback: Function(intensity, duration)
            units_list: List of all units (to find adjacent targets)
        """
        self.target = target_unit
        self.caster = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback

        # Find adjacent enemy units for splash effects
        self.adjacent_targets = []
        for unit in units_list:
            if unit != target_unit and unit.player != caster_unit.player:
                dx = abs(unit.grid_x - target_unit.grid_x)
                dy = abs(unit.grid_y - target_unit.grid_y)
                if dx <= 1 and dy <= 1:
                    self.adjacent_targets.append(unit)

        # Animation state
        self.phase = "flash"  # flash → debris → splash → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.flash_duration = 0.15
        self.debris_duration = 0.4
        self.splash_duration = 0.3


        # Start phase 1: Impact flash
        self._trigger_flash()

    def _trigger_flash(self):
        """Phase 1: Impact flash burst at target."""
        # Bright white/blue flash particles shooting upward
        for _ in range(30):
            angle = random.uniform(-math.pi/3, -2*math.pi/3)  # Upward cone
            speed = random.uniform(200, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([
                (200, 220, 255),  # Light blue
                (255, 255, 255),  # White
                (180, 200, 255),  # Sky blue
            ])
            size = random.uniform(4, 8)
            particle = Particle(self.target.x, self.target.y, vx, vy,
                              color, size, random.uniform(0.3, 0.6))
            particle.gravity = 300
            self.particle_emitter.particles.append(particle)

        # Shockwave ring (expanding circle particles)
        for i in range(20):
            angle = (i / 20) * 2 * math.pi
            speed = 150
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            particle = Particle(self.target.x, self.target.y, vx, vy,
                              (180, 200, 255), 3, 0.4)
            self.particle_emitter.particles.append(particle)

        # Screen shake for impact
        self.screen_shake(8, 0.2)

        # Target shake
        self.target.shake_intensity = 15

    def _trigger_debris(self):
        """Phase 2: Ceiling debris raining down on target."""
        # Debris particles falling from above target
        for _ in range(25):
            # Start above the target
            start_x = self.target.x + random.uniform(-40, 40)
            start_y = self.target.y - 200  # High above
            vx = random.uniform(-30, 30)
            vy = random.uniform(150, 250)  # Falling downward
            color = random.choice([
                (150, 150, 150),  # Gray
                (180, 180, 180),  # Light gray
                (120, 120, 130),  # Dark gray
                (200, 190, 180),  # Dusty
            ])
            size = random.uniform(4, 10)
            particle = Particle(start_x, start_y, vx, vy, color, size, 0.8)
            particle.gravity = 400  # Heavy gravity for debris
            self.particle_emitter.particles.append(particle)

        # Dust cloud at impact point
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 20  # Slight upward bias
            particle = Particle(self.target.x, self.target.y, vx, vy,
                              (160, 150, 140), random.uniform(5, 9), 0.6)
            particle.gravity = 100
            self.particle_emitter.particles.append(particle)

        # Target continues shaking
        self.target.shake_intensity = 8

    def _trigger_splash(self):
        """Phase 3: Splash damage effects on adjacent units."""
        for adj_unit in self.adjacent_targets:
            # Dust burst at each adjacent unit
            for _ in range(10):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(30, 70)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                color = random.choice([
                    (180, 140, 100),  # Brown
                    (160, 130, 90),   # Dark brown
                    (140, 120, 80),   # Dusty brown
                ])
                particle = Particle(adj_unit.x, adj_unit.y, vx, vy,
                                  color, random.uniform(3, 6), 0.5)
                particle.gravity = 200
                self.particle_emitter.particles.append(particle)

            # Shake adjacent units
            adj_unit.shake_intensity = 6

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "flash":
            if self.timer >= self.flash_duration:
                self.phase = "debris"
                self.timer = 0
                self._trigger_debris()

        elif self.phase == "debris":
            if self.timer >= self.debris_duration:
                self.phase = "splash"
                self.timer = 0
                if self.adjacent_targets:
                    self._trigger_splash()
                else:
                    # Skip splash phase if no adjacents
                    self.phase = "done"

        elif self.phase == "splash":
            if self.timer >= self.splash_duration:
                self.phase = "done"

        elif self.phase == "done":
            self.active = False

        return self.active

    def draw(self, surface):
        """No additional drawing needed - particles handle visuals."""
        pass


# ============================================================================
# PRY ANIMATION (New Version - Follows Skill Description)
# ============================================================================

class PryLeverEffect:
    """
    Glaive lever at caster position prying target upward.
    Orange/brown beam showing the prying motion.
    """
    def __init__(self, caster_x, caster_y, target_x, target_y):
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.target_x = target_x
        self.target_y = target_y
        self.timer = 0
        self.duration = 0.35
        self.active = True

    def update(self, delta_time):
        """Update lever animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw glaive lever beam."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(220 * (1.0 - progress))  # Fade out

        if alpha > 20:
            # Orange/brown lever beam (GLAIVEMAN colors)
            lever_surf = pygame.Surface((abs(int(self.target_x - self.caster_x)) + 20,
                                        abs(int(self.target_y - self.caster_y)) + 20), pygame.SRCALPHA)

            # Calculate local coordinates
            start_local = (10, 10)
            end_local = (int(self.target_x - self.caster_x + 10), int(self.target_y - self.caster_y + 10))

            # Outer bright yellow glow (#ffffcc from GLAIVEMAN cross emblem)
            pygame.draw.line(lever_surf, (255, 255, 204, alpha // 2),
                           start_local, end_local, 10)
            # Inner bright orange (#ff9944 glow)
            pygame.draw.line(lever_surf, (255, 255, 255, alpha),
                           start_local, end_local, 6)
            # Core white line
            pygame.draw.line(lever_surf, (255, 255, 255, alpha),
                           start_local, end_local, 2)

            surface.blit(lever_surf, (int(min(self.caster_x, self.target_x)) - 10,
                                     int(min(self.caster_y, self.target_y)) - 10))


class PryLaunchTrail:
    """
    Particle trail as target is launched upward.
    Gray/white particles matching armor colors.
    """
    def __init__(self, start_x, start_y):
        self.start_x = start_x
        self.start_y = start_y
        self.timer = 0
        self.duration = 0.4
        self.active = True
        self.particles = []

    def update(self, delta_time):
        """Update launch trail particles."""
        if not self.active:
            return False

        self.timer += delta_time

        # Spawn trail particles as target moves up
        if self.timer < self.duration and len(self.particles) < 20:
            # Calculate current target position (moving upward)
            progress = self.timer / self.duration
            current_y = self.start_y - 200 * progress  # Moving up 200 pixels

            self.particles.append({
                'x': self.start_x + random.uniform(-10, 10),
                'y': current_y,
                'lifetime': 0.3,
                'age': 0,
                'size': random.uniform(3, 6),
                'color': random.choice([
                    (192, 192, 192),  # Silver (#c0c0c0 from glaive)
                    (138, 138, 138),  # Gray (#8a8a8a from rivets)
                    (106, 106, 106),  # Darker gray (#6a6a6a from armor)
                ])
            })

        # Age particles
        for particle in self.particles:
            particle['age'] += delta_time

        self.particles = [p for p in self.particles if p['age'] < p['lifetime']]

        if self.timer >= self.duration and not self.particles:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw trail particles."""
        if not self.active:
            return

        for particle in self.particles:
            alpha = int(200 * (1.0 - particle['age'] / particle['lifetime']))
            if alpha > 20:
                particle_surf = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*particle['color'], alpha),
                                 (int(particle['size']), int(particle['size'])), int(particle['size']))
                surface.blit(particle_surf, (int(particle['x'] - particle['size']), int(particle['y'] - particle['size'])))


class PryCeilingImpact:
    """
    Impact flash at ceiling when target hits.
    White/bright yellow flash matching GLAIVEMAN colors.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y - 200  # At ceiling height
        self.timer = 0
        self.duration = 0.25
        self.active = True
        self.max_radius = 40

    def update(self, delta_time):
        """Update ceiling impact flash."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw ceiling impact flash."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Flash expands quickly then fades
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        alpha = int(255 * (1.0 - progress))

        if alpha > 20 and radius > 0:
            flash_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Outer bright yellow glow (#ffffcc)
            pygame.draw.circle(flash_surf, (255, 255, 204, alpha // 3), (center, center), radius + 8)
            # Inner white flash
            pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (center, center), radius)
            # Bright core
            if progress < 0.2:
                pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (center, center), radius // 2)

            surface.blit(flash_surf, (int(self.center_x - center), int(self.center_y - center)))


class PryDebrisChunk:
    """
    Individual debris chunk falling from ceiling.
    Gray stone colors matching armor/structure.
    Lands on ground and creates impact, then fades out.
    """
    def __init__(self, x, y, vx, vy, size, delay=0, ground_y=None, target_x=None, target_y=None, impact_callback=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-500, 500)
        self.timer = -delay
        self.lifetime = 2.0
        self.gravity = 600
        self.active = True
        self.has_landed = False
        self.land_timer = 0
        self.land_fade_duration = 0.3  # Fade out over 0.3s after landing
        # Ground Y position (where debris should land)
        self.ground_y = ground_y if ground_y else y + 200
        # Target position (where debris is aiming for)
        self.target_x = target_x if target_x is not None else x
        self.target_y = target_y if target_y is not None else self.ground_y
        # Callback to trigger impact effect when landing
        self.impact_callback = impact_callback
        self.impact_triggered = False
        # Gray stone colors (#6a6a6a, #5a5a5a, #8a8a8a)
        self.color = random.choice([
            (106, 106, 106),  # #6a6a6a
            (90, 90, 90),     # #5a5a5a
            (138, 138, 138),  # #8a8a8a
        ])

    def update(self, delta_time):
        """Update debris falling with gravity, landing, and fade out."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:  # Only move after delay
            if not self.has_landed:
                # Still falling - aim toward target position
                self.x += self.vx * delta_time
                self.y += self.vy * delta_time
                self.vy += self.gravity * delta_time  # Gravity acceleration

                # Subtle homing toward target (slight course correction)
                dx_to_target = self.target_x - self.x
                if abs(dx_to_target) > 5:  # Only correct if significantly off course
                    correction = dx_to_target * 0.3  # Gentle correction
                    self.vx += correction * delta_time

                self.rotation += self.rotation_speed * delta_time

                # Check if reached ground
                if self.y >= self.ground_y:
                    self.y = self.ground_y  # Snap to ground
                    self.x = self.target_x  # Snap to target X for clean impact
                    self.has_landed = True
                    self.land_timer = 0
                    # Stop horizontal movement, slow rotation
                    self.vx = 0
                    self.vy = 0
                    self.rotation_speed *= 0.1  # Slow down rotation on landing

                    # Trigger impact callback when landing
                    if self.impact_callback and not self.impact_triggered:
                        self.impact_callback(self.target_x, self.target_y)
                        self.impact_triggered = True
            else:
                # Landed - fade out
                self.land_timer += delta_time
                self.rotation += self.rotation_speed * delta_time  # Slight rotation while fading

                if self.land_timer >= self.land_fade_duration:
                    self.active = False

        if self.timer >= self.lifetime:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw spinning debris chunk with fade out on landing."""
        if not self.active or self.timer < 0:
            return

        # Calculate alpha - fade out when landed
        if self.has_landed:
            fade_progress = min(1.0, self.land_timer / self.land_fade_duration)
            alpha = int(255 * (1.0 - fade_progress))
        else:
            alpha = 255

        if alpha <= 10:
            return

        # Draw as jagged rock chunk
        debris_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        center = int(self.size)

        # Main chunk
        pygame.draw.circle(debris_surf, (*self.color, alpha), (center, center), int(self.size))
        # Darker outline
        pygame.draw.circle(debris_surf, (80, 70, 60, alpha), (center, center), int(self.size), 2)

        # Rotate
        rotated = pygame.transform.rotate(debris_surf, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class PryDebrisImpact:
    """
    Debris impact effect - rocks scatter and dust puffs up on landing.
    This creates a clear visual of debris hitting the ground, not a ground explosion.
    """
    def __init__(self, center_x, center_y, is_primary=False, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.6
        self.active = True
        self.is_primary = is_primary

        # Impact particles - rock chunks scattering outward
        self.rock_particles = []
        self.dust_particles = []

        # Don't create particles yet - wait for timer to reach 0
        self.particles_created = False

    def _create_particles(self):
        """Create impact particles when impact happens."""
        if self.particles_created:
            return
        self.particles_created = True

        # Rock chunks scatter outward from impact
        num_rocks = 12 if self.is_primary else 6
        for i in range(num_rocks):
            angle = (i / num_rocks) * 360
            speed = random.uniform(80, 150) if self.is_primary else random.uniform(50, 100)
            vx = math.cos(math.radians(angle)) * speed
            vy = math.sin(math.radians(angle)) * speed - random.uniform(100, 200)  # Initial upward velocity

            self.rock_particles.append({
                'x': self.center_x,
                'y': self.center_y,
                'vx': vx,
                'vy': vy,
                'size': random.uniform(3, 6) if self.is_primary else random.uniform(2, 4),
                'lifetime': random.uniform(0.4, 0.6),
                'timer': 0,
                'color': random.choice([(106, 106, 106), (90, 90, 90), (138, 138, 138)]),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-500, 500)
            })

        # Dust cloud puffing up
        num_dust = 20 if self.is_primary else 10
        for i in range(num_dust):
            angle = random.uniform(0, 360)
            speed = random.uniform(20, 60)
            vx = math.cos(math.radians(angle)) * speed
            vy = math.sin(math.radians(angle)) * speed - random.uniform(30, 80)  # Slight upward drift

            self.dust_particles.append({
                'x': self.center_x + random.uniform(-10, 10),
                'y': self.center_y + random.uniform(-5, 5),
                'vx': vx,
                'vy': vy,
                'size': random.uniform(4, 10) if self.is_primary else random.uniform(3, 7),
                'lifetime': random.uniform(0.5, 0.7),
                'timer': 0,
                'alpha_start': random.randint(120, 180),
                'color': random.choice([(140, 140, 140), (120, 120, 120), (160, 160, 160)])
            })

    def update(self, delta_time):
        """Update debris impact particles."""
        if not self.active:
            return False

        self.timer += delta_time

        # Create particles when timer reaches 0
        if self.timer >= 0 and not self.particles_created:
            self._create_particles()

        if self.timer >= self.duration:
            self.active = False

        if self.particles_created:
            # Update rock particles
            gravity = 400
            for rock in self.rock_particles:
                rock['timer'] += delta_time
                rock['x'] += rock['vx'] * delta_time
                rock['y'] += rock['vy'] * delta_time
                rock['vy'] += gravity * delta_time  # Gravity
                rock['rotation'] += rock['rotation_speed'] * delta_time
                # Slow down horizontal movement
                rock['vx'] *= 0.95

            # Update dust particles
            for dust in self.dust_particles:
                dust['timer'] += delta_time
                dust['x'] += dust['vx'] * delta_time
                dust['y'] += dust['vy'] * delta_time
                # Dust slows down and drifts up slightly
                dust['vx'] *= 0.92
                dust['vy'] *= 0.95

        return self.active

    def draw(self, surface):
        """Draw debris impact - rock scatter and dust clouds."""
        if not self.active or self.timer < 0 or not self.particles_created:
            return

        # Draw dust particles (behind rocks)
        for dust in self.dust_particles:
            if dust['timer'] < dust['lifetime']:
                progress = dust['timer'] / dust['lifetime']
                alpha = int(dust['alpha_start'] * (1.0 - progress))

                if alpha > 10:
                    size = int(dust['size'] * (1.0 + progress * 0.5))  # Dust expands
                    dust_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dust_surf, (*dust['color'], alpha), (size, size), size)
                    surface.blit(dust_surf, (int(dust['x'] - size), int(dust['y'] - size)))

        # Draw rock particles (in front of dust)
        for rock in self.rock_particles:
            if rock['timer'] < rock['lifetime']:
                progress = rock['timer'] / rock['lifetime']
                alpha = int(255 * (1.0 - progress))

                if alpha > 20:
                    rock_surf = pygame.Surface((int(rock['size'] * 2), int(rock['size'] * 2)), pygame.SRCALPHA)
                    center = int(rock['size'])
                    # Main rock chunk
                    pygame.draw.circle(rock_surf, (*rock['color'], alpha), (center, center), int(rock['size']))
                    # Darker outline
                    pygame.draw.circle(rock_surf, (80, 70, 60, alpha), (center, center), int(rock['size']), 1)

                    # Rotate
                    rotated = pygame.transform.rotate(rock_surf, rock['rotation'])
                    rect = rotated.get_rect(center=(int(rock['x']), int(rock['y'])))
                    surface.blit(rotated, rect)


class PryGroundExplosion:
    """
    Ground impact explosion with orange fireball + gray dust.
    Uses GLAIVEMAN orange colors.
    """
    def __init__(self, center_x, center_y, is_primary=False):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5 if is_primary else 0.35
        self.active = True
        self.max_radius = 50 if is_primary else 30
        self.is_primary = is_primary

    def update(self, delta_time):
        """Update explosion expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw orange fireball explosion."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fast expansion
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        # Fade out
        alpha = int(255 * (1.0 - progress))

        if alpha > 20 and radius > 0:
            explosion_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Outer bright yellow glow (#ffffcc from GLAIVEMAN cross)
            pygame.draw.circle(explosion_surf, (255, 255, 204, alpha // 3), (center, center), radius + 8)
            # Main bright yellow glow (#ffffff glow)
            pygame.draw.circle(explosion_surf, (255, 255, 255, alpha), (center, center), radius)
            # Inner bright core
            if progress < 0.4:
                inner_radius = int(radius * 0.5)
                pygame.draw.circle(explosion_surf, (255, 255, 255, alpha), (center, center), inner_radius)

            surface.blit(explosion_surf, (int(self.center_x - center), int(self.center_y - center)))


class PryShockwave:
    """
    Expanding shockwave ring on ground impact.
    Orange/brown colors from GLAIVEMAN theme.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.6
        self.active = True
        self.max_radius = 60

    def update(self, delta_time):
        """Update shockwave expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding shockwave ring."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        radius = int(self.max_radius * progress)
        alpha = int(200 * (1.0 - progress))

        if alpha > 20 and radius > 5:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Bright yellow shockwave ring (#ffffcc)
            pygame.draw.circle(ring_surf, (255, 255, 204, alpha), (radius, radius), radius, 4)
            # Inner darker ring (brown #8b4513 from shaft)
            if alpha > 60:
                pygame.draw.circle(ring_surf, (139, 69, 19, alpha // 2), (radius, radius), radius - 2, 2)

            surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class PryAnimation:
    """
    Pry skill animation for GLAIVEMAN - New version following skill description exactly.

    "Pry forces an enemy unit straight up into the air where they slam into
    the ceiling or skybox, breaking loose debris that crashes down with them."

    Uses GLAIVEMAN color scheme from SVG sprite:
    - Bright yellow (#ffffcc) for impacts and lever
    - Gray/silver (#6a6a6a, #c0c0c0, #8a8a8a) for debris and trails
    - Brown (#8b4513) for shockwave accents

    Phases:
    1. Prying Up (0.4s) - Lever appears, target launches upward with trail
    2. Ceiling Impact (0.5s) - Target hits ceiling, debris spawns
    3. Falling (0.8s) - Target and debris fall together
    4. Ground Impact (0.6s) - Orange explosion + gray dust, splash damage to adjacents, DAMAGE TRIGGERS

    Total duration: 2.3 seconds
    Damage timing: 1.7s (start of Phase 4 - ground impact, delayed execution like Parabol)
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Pry animation.

        Args:
            target_pos: (grid_y, grid_x) - primary target position
            camera: Camera instance for coordinate conversion
            units_list: All units for finding adjacents
            screen_shake_callback: For prying, ceiling, and ground impacts
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.game = game

        # Convert caster position to screen coords
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                             caster_unit.grid_y,
                                                             centered=True)

        # Convert target grid position to screen coords
        # CRITICAL: target_pos is (grid_y, grid_x), but grid_to_screen takes (grid_x, grid_y)!
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Calculate adjacent positions for splash damage (3x3 around target)
        self.splash_positions = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue  # Skip center (primary target)

                splash_grid_y = grid_y + dy
                splash_grid_x = grid_x + dx
                splash_x, splash_y = camera.grid_to_screen(splash_grid_x, splash_grid_y, centered=True)

                self.splash_positions.append({
                    'x': splash_x,
                    'y': splash_y,
                    'delay': 0.05 * (abs(dy) + abs(dx))  # Slight stagger
                })

        # Animation state
        self.phase = "prying_up"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.lever = None
        self.launch_trail = None
        self.ceiling_impact = None
        self.debris_chunks = []
        self.debris_impacts = []  # NEW: debris impact effects when chunks land
        self.ground_explosion = None
        self.splash_explosions = []
        self.shockwaves = []

        # Damage trigger flag
        self.damage_triggered = False

        # Target unit movement state (attribute-based animation like Vault)
        if self.target_unit:
            self.target_unit.pry_start_x = self.target_unit.x
            self.target_unit.pry_start_y = self.target_unit.y
            self.target_unit.pry_phase = "launching"
            self.target_unit.pry_timer = 0
            self.target_unit.pry_duration = 0.32  # Phase 1: launching duration (20% faster)

        # Start Phase 1
        self._start_prying_up()

    def _start_prying_up(self):
        """Phase 1: Prying Up - Glaive lever pries target upward."""
        self.phase = "prying_up"
        self.timer = 0

        # Lever prying sound - metallic scraping/leveraging
        play_sound("pry_lever")

        # Create lever effect from caster to target
        self.lever = PryLeverEffect(self.caster_x, self.caster_y, self.target_x, self.target_y)

        # Create launch trail
        self.launch_trail = PryLaunchTrail(self.target_x, self.target_y)

        # Prying screen shake (light)
        self.screen_shake_callback(4, 0.3)

        # Launch dust particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.target_x, self.target_y, (138, 138, 138), count=15)

    def _start_ceiling_impact(self):
        """Phase 2: Ceiling Impact - Target hits ceiling, debris spawns aimed at affected tiles."""
        self.phase = "ceiling_impact"
        self.timer = 0

        # Ceiling crash sound - heavy impact
        play_sound("pry_ceiling")

        # Create ceiling impact flash
        self.ceiling_impact = PryCeilingImpact(self.target_x, self.target_y)

        # Spawn debris chunks falling from ceiling - aim at primary target (8-10 chunks)
        for _ in range(random.randint(8, 10)):
            # Start above target with some spread
            debris_x = self.target_x + random.uniform(-50, 50)
            debris_y = self.target_y - 200  # Start at ceiling
            # Initial velocity aims toward target
            dx_to_target = self.target_x - debris_x
            debris_vx = dx_to_target * 0.5 + random.uniform(-20, 20)  # Aim toward target with variance
            debris_vy = random.uniform(20, 60)  # Initial downward velocity
            debris_size = random.uniform(5, 10)
            delay = random.uniform(0, 0.15)  # Slight stagger

            # Create impact callback that will be triggered when debris lands
            def create_impact_callback(x, y):
                return lambda impact_x, impact_y: self.debris_impacts.append(
                    PryDebrisImpact(impact_x, impact_y, is_primary=True, delay=0)
                )

            # Pass target position so debris aims for it
            self.debris_chunks.append(PryDebrisChunk(
                debris_x, debris_y, debris_vx, debris_vy, debris_size, delay,
                ground_y=self.target_y,
                target_x=self.target_x,
                target_y=self.target_y,
                impact_callback=create_impact_callback(self.target_x, self.target_y)
            ))

        # Spawn debris chunks aimed at splash positions (2-3 chunks per adjacent tile)
        for splash in self.splash_positions:
            for _ in range(random.randint(2, 3)):
                # Start above splash position with spread
                debris_x = splash['x'] + random.uniform(-40, 40)
                debris_y = splash['y'] - 200  # Start at ceiling
                # Initial velocity aims toward splash tile
                dx_to_splash = splash['x'] - debris_x
                debris_vx = dx_to_splash * 0.5 + random.uniform(-15, 15)
                debris_vy = random.uniform(20, 60)
                debris_size = random.uniform(3, 7)
                delay = random.uniform(0, 0.2) + splash['delay']  # Stagger with splash delay

                # Create impact callback for splash position
                def create_splash_impact_callback(x, y):
                    return lambda impact_x, impact_y: self.debris_impacts.append(
                        PryDebrisImpact(impact_x, impact_y, is_primary=False, delay=0)
                    )

                self.debris_chunks.append(PryDebrisChunk(
                    debris_x, debris_y, debris_vx, debris_vy, debris_size, delay,
                    ground_y=splash['y'],
                    target_x=splash['x'],
                    target_y=splash['y'],
                    impact_callback=create_splash_impact_callback(splash['x'], splash['y'])
                ))

        # Ceiling impact screen shake (medium)
        self.screen_shake_callback(6, 0.4)

        # Ceiling impact particles
        if self.particle_emitter:
            ceiling_y = self.target_y - 200
            self.particle_emitter.emit_burst(self.target_x, ceiling_y, (192, 192, 192), count=25)

    def _start_falling(self):
        """Phase 3: Falling - Target and debris fall together."""
        self.phase = "falling"
        self.timer = 0

        # No new effects - debris already falling from Phase 2
        # Just let gravity do its work

    def _start_ground_impact(self):
        """Phase 4: Ground Impact - Debris impacts create effects as they land."""
        self.phase = "ground_impact"
        self.timer = 0

        # Ground explosion sound - heavy impact with debris
        play_sound("pry_impact")

        # **DAMAGE TRIGGER: This is when damage happens (delayed execution like Parabol)**
        # Game logic will apply damage at this moment (1.7s into animation)
        self.damage_triggered = True

        # NOTE: Ground explosions REMOVED - impacts are now created by falling debris
        # Debris chunks trigger PryDebrisImpact effects when they land via callbacks

        # Keep shockwaves for visual impact (they look good and aren't the problem)
        # Primary shockwave
        self.shockwaves.append(PryShockwave(self.target_x, self.target_y, delay=0.1))

        # Splash shockwaves at adjacent tiles
        for splash in self.splash_positions:
            shockwave = PryShockwave(splash['x'], splash['y'], delay=splash['delay'] + 0.15)
            self.shockwaves.append(shockwave)

        # Ground impact screen shake (heavy)
        self.screen_shake_callback(8, 0.5)

        # Reduced particle burst - let debris impacts do the work
        if self.particle_emitter:
            # Just a small initial dust cloud, not a massive explosion
            self.particle_emitter.emit_burst(self.target_x, self.target_y, (106, 106, 106), count=15)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update target unit position (attribute-based animation, like VaultAnimationController)
        if self.target_unit and hasattr(self.target_unit, 'pry_phase') and self.target_unit.pry_phase:
            # Increment unit's own timer
            self.target_unit.pry_timer += delta_time
            progress = min(1.0, self.target_unit.pry_timer / self.target_unit.pry_duration)

            if self.target_unit.pry_phase == "launching":
                # Phase 1: Moving upward - smooth linear interpolation
                self.target_unit.y = self.target_unit.pry_start_y - (200 * progress)

            elif self.target_unit.pry_phase == "at_ceiling":
                # Phase 2: At ceiling - hold position
                self.target_unit.y = self.target_unit.pry_start_y - 200

            elif self.target_unit.pry_phase == "falling":
                # Phase 3: Falling down - accelerating fall (gravity simulation)
                self.target_unit.y = (self.target_unit.pry_start_y - 200) + (200 * progress * progress)

            elif self.target_unit.pry_phase == "landed":
                # Phase 4: Back at ground - hold at original position
                self.target_unit.y = self.target_unit.pry_start_y

        # Update sub-effects
        if self.lever:
            self.lever.update(delta_time)

        if self.launch_trail:
            self.launch_trail.update(delta_time)

        if self.ceiling_impact:
            self.ceiling_impact.update(delta_time)

        for debris in self.debris_chunks:
            debris.update(delta_time)

        if self.ground_explosion:
            self.ground_explosion.update(delta_time)

        # Update debris impact effects
        self.debris_impacts = [impact for impact in self.debris_impacts if impact.update(delta_time)]

        for shockwave in self.shockwaves:
            shockwave.update(delta_time)

        # Phase transitions (20% faster - durations multiplied by 0.8)
        if self.phase == "prying_up" and self.timer >= 0.32:  # was 0.4
            if self.target_unit and hasattr(self.target_unit, 'pry_phase'):
                self.target_unit.pry_phase = "at_ceiling"
                self.target_unit.pry_timer = 0  # Reset timer for new phase
                self.target_unit.pry_duration = 0.4  # was 0.5
            self._start_ceiling_impact()
        elif self.phase == "ceiling_impact" and self.timer >= 0.4:  # was 0.5
            if self.target_unit and hasattr(self.target_unit, 'pry_phase'):
                self.target_unit.pry_phase = "falling"
                self.target_unit.pry_timer = 0  # Reset timer for new phase
                self.target_unit.pry_duration = 0.64  # was 0.8
            self._start_falling()
        elif self.phase == "falling" and self.timer >= 0.64:  # was 0.8
            if self.target_unit and hasattr(self.target_unit, 'pry_phase'):
                self.target_unit.pry_phase = "landed"
                self.target_unit.pry_timer = 0  # Reset timer for new phase
                self.target_unit.pry_duration = 0.48  # was 0.6
            self._start_ground_impact()
        elif self.phase == "ground_impact" and self.timer >= 0.48:  # was 0.6
            # Reset target unit state - animation complete
            if self.target_unit and hasattr(self.target_unit, 'pry_phase'):
                self.target_unit.pry_phase = None
                self.target_unit.pry_timer = 0
                self.target_unit.y = self.target_unit.pry_start_y
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "prying_up":
            if self.lever:
                self.lever.draw(surface)
            if self.launch_trail:
                self.launch_trail.draw(surface)

        elif self.phase == "ceiling_impact":
            if self.ceiling_impact:
                self.ceiling_impact.draw(surface)
            # Start drawing falling debris
            for debris in self.debris_chunks:
                debris.draw(surface)

        elif self.phase == "falling":
            # Draw falling debris
            for debris in self.debris_chunks:
                debris.draw(surface)

        elif self.phase == "ground_impact":
            # Draw continuing debris chunks that are still falling/landing
            for debris in self.debris_chunks:
                debris.draw(surface)

            # Draw debris impact effects (rock scatter and dust clouds)
            for impact in self.debris_impacts:
                impact.draw(surface)

            # Draw shockwaves
            for shockwave in self.shockwaves:
                shockwave.draw(surface)


# ============================================================================
# JUDGEMENT ANIMATION (New Version - Follows Skill Description)
# ============================================================================

class JudgementGlaiveProjectile:
    """
    Sacred spinning glaive projectile for Judgement skill.
    Golden six-bladed glaive with motion blur trail.
    Reuses visual design from SpinningGlaiveProjectile.
    """
    def __init__(self, start_x, start_y, target_x, target_y, speed=700):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.rotation = 0
        self.rotation_speed = 1080  # 3 full rotations per second
        self.active = True
        self.trail_positions = []

        # Calculate direction
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            self.vx = (dx / distance) * speed
            self.vy = (dy / distance) * speed
        else:
            self.vx = 0
            self.vy = 0

        # Create glaive sprite
        self.size = 32
        self.create_glaive_surface()

    def create_glaive_surface(self):
        """Create the spinning golden glaive sprite (same as SpinningGlaiveProjectile)."""
        self.base_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = self.size // 2

        # Bright yellow/white color scheme (#ffffcc, #ffffff)
        bright_yellow = (255, 255, 204)  # #ffffcc
        white = (255, 255, 255)
        white = (255, 255, 255)

        # Draw six pointed blades
        blade_length = self.size // 2 - 2
        for i in range(6):
            angle = (i * 60) * math.pi / 180

            tip_x = center + math.cos(angle) * blade_length
            tip_y = center + math.sin(angle) * blade_length

            angle_offset = 15 * math.pi / 180
            side1_x = center + math.cos(angle - angle_offset) * (blade_length * 0.7)
            side1_y = center + math.sin(angle - angle_offset) * (blade_length * 0.7)
            side2_x = center + math.cos(angle + angle_offset) * (blade_length * 0.7)
            side2_y = center + math.sin(angle + angle_offset) * (blade_length * 0.7)

            pygame.draw.polygon(self.base_surface, bright_yellow,
                              [(center, center), (tip_x, tip_y), (side1_x, side1_y)])
            pygame.draw.polygon(self.base_surface, bright_yellow,
                              [(center, center), (tip_x, tip_y), (side2_x, side2_y)])
            pygame.draw.line(self.base_surface, white,
                           (center, center), (tip_x, tip_y), 2)

        # Center hub
        pygame.draw.circle(self.base_surface, white, (center, center), 6)
        pygame.draw.circle(self.base_surface, bright_yellow, (center, center), 6, 2)
        pygame.draw.circle(self.base_surface, (200, 180, 0), (center, center), 3)

    def update(self, delta_time):
        """Update projectile position and rotation."""
        if not self.active:
            return False

        # Store position for trail
        self.trail_positions.append((self.x, self.y, self.rotation))
        if len(self.trail_positions) > 8:
            self.trail_positions.pop(0)

        # Move towards target
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.rotation += self.rotation_speed * delta_time

        # Check if reached target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance < self.speed * delta_time:
            self.active = False
            return False

        return True

    def draw(self, surface):
        """Draw spinning glaive with motion blur trail."""
        if not self.active:
            return

        # Draw motion blur trail
        for i, (trail_x, trail_y, trail_rot) in enumerate(self.trail_positions):
            alpha = int(100 * (i / len(self.trail_positions)))
            trail_surface = pygame.transform.rotate(self.base_surface, trail_rot)
            trail_surface.set_alpha(alpha)
            trail_rect = trail_surface.get_rect(center=(int(trail_x), int(trail_y)))
            surface.blit(trail_surface, trail_rect)

        # Draw main glaive
        rotated_surface = pygame.transform.rotate(self.base_surface, self.rotation)
        rect = rotated_surface.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_surface, rect)

        # Add golden glow
        glow_surf = pygame.Surface((self.size + 20, self.size + 20), pygame.SRCALPHA)
        glow_radius = self.size // 2 + 10
        pygame.draw.circle(glow_surf, (255, 255, 204, 50), (glow_radius, glow_radius), glow_radius)
        glow_rect = glow_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(glow_surf, glow_rect)


class JudgementImpactFlash:
    """
    Impact flash when glaive hits target.
    Golden/white/orange burst.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.25
        self.active = True
        self.max_radius = 45

    def update(self, delta_time):
        """Update flash expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw golden impact flash."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fast expansion
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        alpha = int(255 * (1.0 - progress))

        if alpha > 20 and radius > 0:
            flash_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Outer bright yellow glow (#ffffcc)
            pygame.draw.circle(flash_surf, (255, 255, 204, alpha // 3), (center, center), radius + 8)
            # Main bright yellow flash (#ffffcc)
            pygame.draw.circle(flash_surf, (255, 255, 204, alpha), (center, center), radius)
            # Inner white core
            if progress < 0.4:
                inner_radius = int(radius * 0.6)
                pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (center, center), inner_radius)

            surface.blit(flash_surf, (int(self.center_x - center), int(self.center_y - center)))


class JudgementShockwave:
    """
    Expanding shockwave ring on impact.
    Orange/brown colors from GLAIVEMAN theme.
    """
    def __init__(self, center_x, center_y, delay=0, is_crit=False):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True
        self.max_radius = 70 if is_crit else 50
        self.is_crit = is_crit

    def update(self, delta_time):
        """Update shockwave expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding shockwave ring."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)
        radius = int(self.max_radius * progress)
        alpha = int(220 * (1.0 - progress))

        if alpha > 20 and radius > 5:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Bright yellow shockwave ring (#ffffcc)
            thickness = 5 if self.is_crit else 3
            pygame.draw.circle(ring_surf, (255, 255, 204, alpha), (radius, radius), radius, thickness)
            # Inner bright yellow accent (#ffffcc)
            if alpha > 60:
                pygame.draw.circle(ring_surf, (255, 255, 204, alpha // 2), (radius, radius), radius - 2, 2)

            surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class JudgementCriticalEffect:
    """
    Critical hit effect - lightning bolt strikes glaive on impact.
    Uses existing LightningBolt class.
    """
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.lightning = LightningBolt(target_x, target_y)
        self.flash_timer = 0.3
        self.active = True

    def update(self, delta_time):
        """Update lightning and flash."""
        if not self.active:
            return False

        self.flash_timer -= delta_time
        lightning_active = self.lightning.update(delta_time)

        if not lightning_active and self.flash_timer <= 0:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw lightning bolt and bright flash."""
        if not self.active:
            return

        # Draw lightning
        self.lightning.draw(surface)

        # Draw bright white flash at impact point
        if self.flash_timer > 0:
            flash_alpha = int(255 * (self.flash_timer / 0.3))
            flash_radius = int(60 * (1.0 - self.flash_timer / 0.3))

            flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha), (flash_radius, flash_radius), flash_radius)
            flash_rect = flash_surf.get_rect(center=(int(self.target_x), int(self.target_y)))
            surface.blit(flash_surf, flash_rect)


class JudgementAnimation:
    """
    Judgement skill animation for GLAIVEMAN - New version following skill description.

    "Throw a sacred glaive at an enemy. Deals pierce damage that ignores defense.
    Against targets at critical health, deals double damage."

    Uses GLAIVEMAN color scheme:
    - Bright yellow (#ffffcc) for glaive
    - Bright yellow (#ffffcc) for impact flash and shockwave
    - White/Yellow lightning for critical hits

    Phases:
    1. Wind-up (0.3s) - GLAIVEMAN prepares throw, glaive glows
    2. Flight (0.7s) - Golden spinning glaive flies to target with trail
    3. Impact (0.5s) - Golden flash + shockwave (or LIGHTNING BOLT for critical), DAMAGE TRIGGERS

    Total duration: 1.5 seconds
    Damage timing: 1.0s (start of Phase 3 - impact, delayed execution like Parabol)
    Critical: Lightning strikes glaive when target is at critical HP
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Judgement animation.

        Args:
            is_crit: True if target is at critical health (doubles damage, triggers lightning)
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.game = game

        # Get caster's game logic unit to use its actual position (post-move)
        # The AnimatedUnit's grid_x/y might not be updated yet, so use the game unit's position
        if hasattr(caster_unit, 'game_unit') and caster_unit.game_unit:
            # Use game unit's actual position (post-move)
            caster_grid_x = caster_unit.game_unit.x
            caster_grid_y = caster_unit.game_unit.y
        else:
            # Fall back to AnimatedUnit's position
            caster_grid_x = caster_unit.grid_x
            caster_grid_y = caster_unit.grid_y

        # Convert positions to screen coords
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_grid_x,
                                                             caster_grid_y,
                                                             centered=True)

        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Determine if critical hit (target at critical HP)
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        critical_threshold = int(target_unit.max_hp * CRITICAL_HEALTH_PERCENT) if target_unit else 0
        self.is_crit = is_crit or (target_unit and target_unit.hp <= critical_threshold)

        # Animation state
        self.phase = "wind_up"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.projectile = None
        self.impact_flash = None
        self.shockwave = None
        self.critical_effect = None

        # Damage trigger flag
        self.damage_triggered = False

        # Start Phase 1
        self._start_wind_up()

    def _start_wind_up(self):
        """Phase 1: Wind-up - GLAIVEMAN prepares to throw."""
        self.phase = "wind_up"
        self.timer = 0

        # Wind-up sound (optional - for dramatic effect)
        play_sound("judgement_windup")

        # Light screen shake for wind-up
        self.screen_shake_callback(3, 0.2)

        # Glow particles at caster
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (255, 255, 204), count=10)

    def _start_flight(self):
        """Phase 2: Flight - Glaive flies toward target."""
        self.phase = "flight"
        self.timer = 0

        # Throw sound - glaive leaving hand
        play_sound("judgement_throw")

        # Create projectile
        self.projectile = JudgementGlaiveProjectile(self.caster_x, self.caster_y,
                                                    self.target_x, self.target_y)

    def _start_impact(self):
        """Phase 3: Impact - Glaive hits target."""
        self.phase = "impact"
        self.timer = 0

        # **DAMAGE TRIGGER: This is when damage happens (delayed execution like Parabol)**
        self.damage_triggered = True

        # Impact sound - different for critical vs normal
        if self.is_crit:
            play_sound("judgement_critical")
        else:
            play_sound("judgement_impact")

        # Create impact flash
        self.impact_flash = JudgementImpactFlash(self.target_x, self.target_y)

        # Create shockwave
        self.shockwave = JudgementShockwave(self.target_x, self.target_y, is_crit=self.is_crit)

        # Critical effect - LIGHTNING BOLT
        if self.is_crit:
            self.critical_effect = JudgementCriticalEffect(self.target_x, self.target_y)
            # Stronger screen shake for critical
            self.screen_shake_callback(7, 0.4)
        else:
            # Regular screen shake
            self.screen_shake_callback(5, 0.3)

        # Impact particles
        if self.particle_emitter:
            # Golden burst
            self.particle_emitter.emit_burst(self.target_x, self.target_y, (255, 255, 204), count=25)
            if self.is_crit:
                # Extra white particles for critical
                self.particle_emitter.emit_burst(self.target_x, self.target_y, (255, 255, 255), count=15)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update sub-effects
        if self.projectile:
            self.projectile.update(delta_time)

        if self.impact_flash:
            self.impact_flash.update(delta_time)

        if self.shockwave:
            self.shockwave.update(delta_time)

        if self.critical_effect:
            self.critical_effect.update(delta_time)

        # Phase transitions
        if self.phase == "wind_up" and self.timer >= 0.3:
            self._start_flight()
        elif self.phase == "flight" and self.timer >= 0.7:
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "wind_up":
            # Wind-up is primarily particles (handled by particle emitter)
            pass

        elif self.phase == "flight":
            if self.projectile:
                self.projectile.draw(surface)

        elif self.phase == "impact":
            # Draw in order: shockwave, impact flash, critical effect (lightning on top)
            if self.shockwave:
                self.shockwave.draw(surface)

            if self.impact_flash:
                self.impact_flash.draw(surface)

            if self.critical_effect:
                self.critical_effect.draw(surface)


# ============================================================================
# AUTOCLAVE ANIMATION V2 (New Version - Enhanced with Fire Burst & Tile Glaives)
# ============================================================================

class AutoclaveFireBurst:
    """
    Fire burst explosion at GLAIVEMAN's center tile.
    Orange/red fireball with white core.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.4
        self.active = True
        self.max_radius = 60

    def update(self, delta_time):
        """Update fire burst expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw orange/red fireball explosion."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fast expansion then fade
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        alpha = int(255 * (1.0 - progress))

        if alpha > 20 and radius > 0:
            fire_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Outer red glow (#ff0000)
            pygame.draw.circle(fire_surf, (255, 0, 0, alpha // 3), (center, center), radius + 10)
            # Main orange fireball (#ff6600)
            pygame.draw.circle(fire_surf, (255, 255, 204, alpha), (center, center), radius)
            # Inner bright core (white)
            if progress < 0.5:
                inner_radius = int(radius * 0.6)
                pygame.draw.circle(fire_surf, (255, 255, 255, alpha), (center, center), inner_radius)

            surface.blit(fire_surf, (int(self.center_x - center), int(self.center_y - center)))


class AutoclaveSteamJet:
    """
    Steam jet particles expanding in one direction.
    White/blue wispy particles (similar to CrossBeam).
    """
    def __init__(self, center_x, center_y, direction, max_range_tiles=3):
        """
        direction: 0=up, 1=right, 2=down, 3=left
        max_range_tiles: number of tiles to expand
        """
        self.center_x = center_x
        self.center_y = center_y
        self.direction = direction
        self.max_range = max_range_tiles * TILE_SIZE
        self.current_range = 0
        self.expand_speed = 600  # pixels per second
        self.timer = 0
        self.duration = 1.5
        self.width = 20
        self.active = True

    def update(self, delta_time):
        """Update steam jet expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        # Expand
        if self.current_range < self.max_range:
            self.current_range += self.expand_speed * delta_time
            if self.current_range > self.max_range:
                self.current_range = self.max_range

        # Fade out after expansion
        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw wispy steam particles along jet."""
        if not self.active or self.current_range < 10:
            return

        # Alpha based on lifetime
        alpha_mult = 1.0 if self.timer < 0.8 else (1.5 - self.timer) / 0.7
        alpha_mult = max(0, min(1.0, alpha_mult))

        # Steam particles along the jet
        num_steam = int(self.current_range / 15)
        for i in range(num_steam):
            progress = (i / num_steam) if num_steam > 0 else 0

            # Calculate position along jet
            if self.direction == 0:  # Up
                px = self.center_x + random.uniform(-self.width//2, self.width//2)
                py = self.center_y - progress * self.current_range
            elif self.direction == 1:  # Right
                px = self.center_x + progress * self.current_range
                py = self.center_y + random.uniform(-self.width//2, self.width//2)
            elif self.direction == 2:  # Down
                px = self.center_x + random.uniform(-self.width//2, self.width//2)
                py = self.center_y + progress * self.current_range
            else:  # Left
                px = self.center_x - progress * self.current_range
                py = self.center_y + random.uniform(-self.width//2, self.width//2)

            # Steam puffs
            steam_size = random.uniform(8, 16) * (1.0 - progress * 0.3)
            steam_alpha = int(alpha_mult * 100 * (1.0 - progress * 0.5))

            # Multiple overlapping circles for wispy effect
            for _ in range(3):
                offset_x = random.uniform(-steam_size * 0.3, steam_size * 0.3)
                offset_y = random.uniform(-steam_size * 0.3, steam_size * 0.3)
                steam_surf = pygame.Surface((int(steam_size * 3), int(steam_size * 3)), pygame.SRCALPHA)
                pygame.draw.circle(steam_surf, (240, 240, 255, steam_alpha),
                                 (int(steam_size * 1.5 + offset_x), int(steam_size * 1.5 + offset_y)),
                                 int(steam_size))
                surface.blit(steam_surf, (int(px - steam_size * 1.5), int(py - steam_size * 1.5)))


class AutoclaveGlaive:
    """
    Spinning glaive at a specific tile position.
    Silver/white coloring (Autoclave theme).
    6-bladed design.
    """
    def __init__(self, tile_x, tile_y, delay=0):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.timer = -delay
        self.duration = 1.5
        self.active = False  # Activates after delay
        self.size = 24  # Larger than Judgement glaives

        # Create glaive sprite
        self.create_glaive_surface()

    def create_glaive_surface(self):
        """Create silver/white spinning glaive sprite."""
        self.base_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        center = self.size

        # Silver/white color scheme (Autoclave theme)
        silver = (192, 192, 192)  # #c0c0c0
        light_silver = (224, 224, 224)  # #e0e0e0
        white = (255, 255, 255)

        # Draw six pointed blades
        blade_length = self.size - 2
        for i in range(6):
            angle = (i * 60) * math.pi / 180

            tip_x = center + math.cos(angle) * blade_length
            tip_y = center + math.sin(angle) * blade_length

            angle_offset = 15 * math.pi / 180
            side1_x = center + math.cos(angle - angle_offset) * (blade_length * 0.7)
            side1_y = center + math.sin(angle - angle_offset) * (blade_length * 0.7)
            side2_x = center + math.cos(angle + angle_offset) * (blade_length * 0.7)
            side2_y = center + math.sin(angle + angle_offset) * (blade_length * 0.7)

            pygame.draw.polygon(self.base_surface, silver,
                              [(center, center), (tip_x, tip_y), (side1_x, side1_y)])
            pygame.draw.polygon(self.base_surface, silver,
                              [(center, center), (tip_x, tip_y), (side2_x, side2_y)])
            pygame.draw.line(self.base_surface, light_silver,
                           (center, center), (tip_x, tip_y), 2)

        # Center hub
        pygame.draw.circle(self.base_surface, white, (center, center), 6)
        pygame.draw.circle(self.base_surface, silver, (center, center), 6, 2)
        pygame.draw.circle(self.base_surface, (160, 160, 160), (center, center), 3)

    def update(self, delta_time):
        """Update glaive state."""
        if not self.active and self.timer < 0:
            self.timer += delta_time
            if self.timer >= 0:
                self.active = True
            return True

        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False
            return False

        return True

    def draw(self, surface, rotation):
        """Draw spinning glaive at tile position."""
        if not self.active:
            return

        # Alpha fade in/out
        if self.timer < 0.2:
            alpha = int(255 * (self.timer / 0.2))
        elif self.timer > self.duration - 0.3:
            alpha = int(255 * ((self.duration - self.timer) / 0.3))
        else:
            alpha = 255

        if alpha <= 10:
            return

        # Rotate glaive (synchronized with all others)
        rotated = pygame.transform.rotate(self.base_surface, rotation)
        rotated.set_alpha(alpha)
        rect = rotated.get_rect(center=(int(self.tile_x), int(self.tile_y)))
        surface.blit(rotated, rect)


class AutoclaveHealingEffect:
    """
    Healing effect at GLAIVEMAN position.
    Green glow and rising particles.
    """
    def __init__(self, center_x, center_y, heal_amount):
        self.center_x = center_x
        self.center_y = center_y
        self.heal_amount = heal_amount
        self.timer = 0
        self.duration = 0.8
        self.active = True
        self.particles = []

        # Create rising heal particles
        for _ in range(15):
            self.particles.append({
                'x': center_x + random.uniform(-20, 20),
                'y': center_y + random.uniform(-10, 10),
                'vy': random.uniform(-80, -40),  # Rising speed
                'lifetime': random.uniform(0.5, 0.8),
                'age': 0,
                'size': random.uniform(3, 6)
            })

    def update(self, delta_time):
        """Update healing glow and particles."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particles
        for particle in self.particles:
            particle['age'] += delta_time
            particle['y'] += particle['vy'] * delta_time

        # Remove old particles
        self.particles = [p for p in self.particles if p['age'] < p['lifetime']]

        if self.timer >= self.duration and not self.particles:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw green healing glow and rising particles."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Green glow at center
        if self.timer < 0.6:
            glow_alpha = int(150 * (1.0 - self.timer / 0.6))
            glow_radius = int(40 + (self.timer / 0.6) * 20)

            if glow_alpha > 20:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (0, 255, 0, glow_alpha),
                                 (glow_radius, glow_radius), glow_radius)
                pygame.draw.circle(glow_surf, (136, 255, 136, glow_alpha // 2),
                                 (glow_radius, glow_radius), glow_radius - 5)
                surface.blit(glow_surf, (int(self.center_x - glow_radius), int(self.center_y - glow_radius)))

        # Rising green particles
        for particle in self.particles:
            alpha = int(200 * (1.0 - particle['age'] / particle['lifetime']))
            if alpha > 20:
                p_surf = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (0, 255, 0, alpha),
                                 (int(particle['size']), int(particle['size'])), int(particle['size']))
                surface.blit(p_surf, (int(particle['x'] - particle['size']), int(particle['y'] - particle['size'])))


class AutoclaveImpactFlash:
    """
    Flash at hit tile positions.
    White/bright yellow flash.
    """
    def __init__(self, tile_x, tile_y, delay=0):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.timer = -delay
        self.duration = 0.25
        self.active = False  # Activates after delay

    def update(self, delta_time):
        """Update flash."""
        self.timer += delta_time

        if self.timer >= 0:
            self.active = True

        if self.timer >= self.duration:
            self.active = False
            return False

        return True

    def draw(self, surface):
        """Draw white/bright yellow flash."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)
        radius = int(25 * (1.0 - progress * 0.5))  # Shrinks slightly
        alpha = int(255 * (1.0 - progress))

        if alpha > 20 and radius > 0:
            flash_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            # Bright yellow flash (#ffffcc)
            pygame.draw.circle(flash_surf, (255, 255, 204, alpha), (radius, radius), radius)
            # White core
            pygame.draw.circle(flash_surf, (255, 255, 255, alpha), (radius, radius), radius // 2)
            surface.blit(flash_surf, (int(self.tile_x - radius), int(self.tile_y - radius)))


class AutoclaveAnimationV2:
    """
    Autoclave passive animation for GLAIVEMAN - Enhanced version.

    "When GLAIVEMAN reaches critical HP, unleashes cross-shaped attack in 4 directions (range 3).
    Deals 8 damage to all enemies, heals for half damage dealt."

    Enhancements:
    - Fire burst at GLAIVEMAN's center tile (eruption source)
    - Steam jets expanding in 4 directions (cross pattern)
    - Spinning glaive on EVERY tile in AOE (not just scattered)
    - Healing effect with green glow and rising particles
    - Delayed damage execution

    Phases:
    1. Ignition (0.32s) - Fire burst at center, cross emblem flash, steam starts
    2. Cross Expansion (0.64s) - Steam expands, glaive appears on each tile
    3. Impact & Healing (0.64s) - Impacts flash, DAMAGE TRIGGERS, healing glow

    Total duration: 1.6 seconds (20% faster)
    Damage timing: 0.96s (start of Phase 3, delayed execution like Parabol)
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Autoclave animation.

        Args:
            caster_unit: GLAIVEMAN triggering Autoclave
            camera: Camera instance for coordinate conversion
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.game = game

        # Convert caster position to screen coords
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                             caster_unit.grid_y,
                                                             centered=True)

        # Calculate affected tiles (cross pattern, range 3, stops at terrain)
        self.affected_tiles = self._calculate_affected_tiles()

        # Animation state
        self.phase = "ignition"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.fire_burst = None
        self.steam_jets = []
        self.glaives = []
        self.impact_flashes = []
        self.healing_effect = None

        # Glaive rotation (synchronized for all glaives)
        self.glaive_rotation = 0

        # Damage trigger flag
        self.damage_triggered = False

        # Healing amount (will be set by game logic)
        self.heal_amount = 0

        # Start Phase 1
        self._start_ignition()

    def _calculate_affected_tiles(self):
        """Calculate all tiles in cross pattern AOE."""
        tiles = []
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # up, right, down, left

        for direction_idx, (dy, dx) in enumerate(directions):
            for distance in range(1, 4):  # Range 1-3
                grid_y = self.caster.grid_y + (dy * distance)
                grid_x = self.caster.grid_x + (dx * distance)

                # Check if position is valid
                if self.game and not self.game.is_valid_position(grid_y, grid_x):
                    break

                # Check terrain passability
                if self.game and not self.game.map.is_passable(grid_y, grid_x):
                    # Add this tile but stop beam here
                    tile_x, tile_y = self.camera.grid_to_screen(grid_x, grid_y, centered=True)
                    tiles.append({
                        'x': tile_x,
                        'y': tile_y,
                        'grid_x': grid_x,
                        'grid_y': grid_y,
                        'direction': direction_idx,
                        'distance': distance
                    })
                    break

                # Convert to screen coords
                tile_x, tile_y = self.camera.grid_to_screen(grid_x, grid_y, centered=True)
                tiles.append({
                    'x': tile_x,
                    'y': tile_y,
                    'grid_x': grid_x,
                    'grid_y': grid_y,
                    'direction': direction_idx,
                    'distance': distance
                })

        return tiles

    def _start_ignition(self):
        """Phase 1: Ignition - Fire burst erupts at center."""
        self.phase = "ignition"
        self.timer = 0

        # Ignition sound - initial fire burst
        play_sound("autoclave_ignition")

        # Create fire burst at GLAIVEMAN
        self.fire_burst = AutoclaveFireBurst(self.caster_x, self.caster_y)

        # Strong screen shake
        self.screen_shake_callback(8, 0.3)

        # Fire particles at center
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (255, 255, 204), count=30)

    def _start_cross_expansion(self):
        """Phase 2: Cross Expansion - Steam and glaives expand outward."""
        self.phase = "cross_expansion"
        self.timer = 0

        # Steam expansion sound - hissing steam jets
        play_sound("autoclave_steam")

        # Create steam jets in 4 directions
        for direction in range(4):
            steam = AutoclaveSteamJet(self.caster_x, self.caster_y, direction, max_range_tiles=3)
            self.steam_jets.append(steam)

        # Create glaive at each affected tile
        for tile in self.affected_tiles:
            # Stagger glaive appearance by distance
            delay = tile['distance'] * 0.15
            glaive = AutoclaveGlaive(tile['x'], tile['y'], delay=delay)
            self.glaives.append(glaive)

    def _start_impact_healing(self):
        """Phase 3: Impact & Healing - Damage triggers, healing begins."""
        self.phase = "impact_healing"
        self.timer = 0

        # **DAMAGE TRIGGER: This is when damage happens (delayed execution like Parabol)**
        self.damage_triggered = True

        # Removed: Impact sound (no autoclave_impact.wav)
        # Removed: Impact flashes at each tile (no longer creating fireball explosions)

        # Healing effect will be created when heal_amount is set by game
        # (This happens after damage is calculated)

        # Screen shake for impacts
        self.screen_shake_callback(6, 0.4)

    def set_heal_amount(self, amount):
        """Set healing amount (called by game after damage calculation)."""
        self.heal_amount = amount
        if amount > 0 and not self.healing_effect:
            self.healing_effect = AutoclaveHealingEffect(self.caster_x, self.caster_y, amount)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update glaive rotation (synchronized for all)
        self.glaive_rotation = (self.glaive_rotation + 720 * delta_time) % 360

        # Update sub-effects
        if self.fire_burst:
            self.fire_burst.update(delta_time)

        for steam in self.steam_jets:
            steam.update(delta_time)

        for glaive in self.glaives:
            glaive.update(delta_time)

        # Removed: Impact flash updates (no longer used)

        if self.healing_effect:
            self.healing_effect.update(delta_time)

        # Phase transitions (20% faster: 0.4→0.32, 0.8→0.64)
        if self.phase == "ignition" and self.timer >= 0.32:
            self._start_cross_expansion()
        elif self.phase == "cross_expansion" and self.timer >= 0.64:
            self._start_impact_healing()
        elif self.phase == "impact_healing" and self.timer >= 0.64:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "ignition":
            if self.fire_burst:
                self.fire_burst.draw(surface)

        elif self.phase == "cross_expansion":
            # Draw steam jets
            for steam in self.steam_jets:
                steam.draw(surface)

            # Draw glaives (on top of steam)
            for glaive in self.glaives:
                glaive.draw(surface, self.glaive_rotation)

        elif self.phase == "impact_healing":
            # Continue drawing steam (fading out)
            for steam in self.steam_jets:
                steam.draw(surface)

            # Draw glaives (still spinning)
            for glaive in self.glaives:
                glaive.draw(surface, self.glaive_rotation)

            # Removed: Impact flashes drawing (no longer used)

            # Draw healing effect
            if self.healing_effect:
                self.healing_effect.draw(surface)


class AutoclaveFailureAnimation:
    """
    Failed Autoclave activation animation - GLAIVEMAN charges energy but it fizzles.
    Shows when Autoclave would trigger but has no eligible targets.

    Phases:
    1. Charge (0.4s) - Shake builds, glow appears, steam rises
    2. Warning (0.3s) - Intense shake, alternating !?!?! symbols
    3. Fizzle (0.3s) - Effects fade, energy dissipates

    Total duration: 1.0s
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """Initialize failed Autoclave animation."""
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter

        # Convert caster position to screen coords
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                             caster_unit.grid_y,
                                                             centered=True)

        # Animation state
        self.phase = "charge"
        self.timer = 0
        self.phase_timer = 0
        self.active = True

        # Visual effects
        self.glow_radius = 0
        self.glow_alpha = 0
        self.shake_intensity = 0
        self.symbol_index = 0  # For alternating ! and ?
        self.symbol_alpha = 0

        # Steam particles
        self.steam_particles = []
        self.last_steam_spawn = 0

        # Phase durations
        self.charge_duration = 0.4
        self.warning_duration = 0.3
        self.fizzle_duration = 0.3

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time
        self.phase_timer += delta_time

        # Update phase
        if self.phase == "charge":
            if self.phase_timer >= self.charge_duration:
                self._start_warning()
        elif self.phase == "warning":
            if self.phase_timer >= self.warning_duration:
                self._start_fizzle()
        elif self.phase == "fizzle":
            if self.phase_timer >= self.fizzle_duration:
                self.active = False
                # Clear shake on caster
                if self.caster:
                    self.caster.shake_intensity = 0
                    self.caster.shake_x = 0
                    self.caster.shake_y = 0
                return False

        # Update visual effects based on phase
        self._update_effects(delta_time)

        # Update steam particles
        self.steam_particles = [p for p in self.steam_particles if p.update(delta_time)]

        return self.active

    def _start_warning(self):
        """Phase 2: Warning symbols appear."""
        self.phase = "warning"
        self.phase_timer = 0

    def _start_fizzle(self):
        """Phase 3: Energy fizzles out."""
        self.phase = "fizzle"
        self.phase_timer = 0

    def _update_effects(self, delta_time):
        """Update visual effects for current phase."""
        progress = self.phase_timer / self._get_phase_duration()

        if self.phase == "charge":
            # Build up glow and shake (smaller fireball)
            self.glow_radius = int(25 * progress)
            self.glow_alpha = int(180 * progress)
            self.shake_intensity = 3 * progress

            # Spawn rising steam particles
            self.last_steam_spawn += delta_time
            if self.last_steam_spawn > 0.05:
                self.last_steam_spawn = 0
                # White/blue steam particles rising upward
                for _ in range(2):
                    angle = random.uniform(-0.3, 0.3)
                    vx = math.cos(angle) * 30
                    vy = -random.uniform(60, 100)  # Rising upward
                    size = random.uniform(3, 6)
                    lifetime = random.uniform(0.5, 0.8)
                    color = (200, 220, 255)  # Light blue-white
                    particle = Particle(self.caster_x, self.caster_y, vx, vy, color, size, lifetime)
                    self.steam_particles.append(particle)

        elif self.phase == "warning":
            # Peak intensity (smaller fireball)
            self.glow_radius = 30
            self.glow_alpha = int(200 * (1.0 - progress * 0.3))  # Slight fade
            self.shake_intensity = 6

            # Alternating symbols fade in/out
            symbol_cycle_speed = 8  # symbols per second
            self.symbol_index = int(self.phase_timer * symbol_cycle_speed) % 2
            flash_progress = (self.phase_timer * symbol_cycle_speed) % 1.0
            self.symbol_alpha = int(255 * (1.0 - abs(flash_progress - 0.5) * 2))

            # More steam
            self.last_steam_spawn += delta_time
            if self.last_steam_spawn > 0.03:
                self.last_steam_spawn = 0
                for _ in range(3):
                    angle = random.uniform(-0.5, 0.5)
                    vx = math.cos(angle) * 40
                    vy = -random.uniform(80, 120)
                    size = random.uniform(4, 7)
                    lifetime = random.uniform(0.4, 0.6)
                    color = (200, 220, 255)
                    particle = Particle(self.caster_x, self.caster_y, vx, vy, color, size, lifetime)
                    self.steam_particles.append(particle)

        elif self.phase == "fizzle":
            # Fade out (smaller fireball)
            fade = 1.0 - progress
            self.glow_radius = int(30 * fade)
            self.glow_alpha = int(200 * fade)
            self.shake_intensity = 6 * fade
            self.symbol_alpha = int(255 * fade)

        # Apply shake to caster unit
        if self.caster and self.shake_intensity > 0:
            self.caster.shake_intensity = self.shake_intensity
            self.caster.shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.caster.shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)

    def _get_phase_duration(self):
        """Get duration of current phase."""
        if self.phase == "charge":
            return self.charge_duration
        elif self.phase == "warning":
            return self.warning_duration
        else:
            return self.fizzle_duration

    def draw(self, surface):
        """Draw failed Autoclave effects."""
        if not self.active:
            return

        # Draw steam particles first (behind unit)
        for particle in self.steam_particles:
            particle.draw(surface)

        # Draw fire/orange glow around GLAIVEMAN
        if self.glow_alpha > 20 and self.glow_radius > 0:
            glow_surf = pygame.Surface((self.glow_radius * 2 + 20, self.glow_radius * 2 + 20), pygame.SRCALPHA)
            center = self.glow_radius + 10

            # Outer red glow (matching Autoclave colors)
            pygame.draw.circle(glow_surf, (255, 0, 0, self.glow_alpha // 3), (center, center), self.glow_radius + 10)
            # Main orange glow
            pygame.draw.circle(glow_surf, (255, 255, 204, self.glow_alpha), (center, center), self.glow_radius)

            surface.blit(glow_surf, (int(self.caster_x - center), int(self.caster_y - center)))

        # Draw warning symbols (! and ?) above unit during warning and fizzle phases
        if self.phase in ["warning", "fizzle"] and self.symbol_alpha > 20:
            # Create larger, bolder font for symbols
            font_size = 48  # Increased from 32
            try:
                symbol_font = pygame.font.Font(None, font_size)
            except:
                symbol_font = pygame.font.SysFont('Arial', font_size, bold=True)

            # Alternate between ! and ?
            symbol = "!" if self.symbol_index == 0 else "?"

            # Brighter red color for warning
            text_surf = symbol_font.render(symbol, True, (255, 20, 20))
            text_surf.set_alpha(self.symbol_alpha)

            # Position above unit (oscillate more prominently)
            offset_y = -50 + math.sin(self.timer * 10) * 5  # Higher position, more movement
            text_rect = text_surf.get_rect(center=(int(self.caster_x), int(self.caster_y + offset_y)))

            # Draw subtle outline/shadow for visibility
            outline_surf = symbol_font.render(symbol, True, (100, 0, 0))
            outline_surf.set_alpha(self.symbol_alpha // 2)
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                outline_rect = outline_surf.get_rect(center=(int(self.caster_x + dx), int(self.caster_y + offset_y + dy)))
                surface.blit(outline_surf, outline_rect)

            surface.blit(text_surf, text_rect)


class GlaivemanPolearmAttack:
    """
    GLAIVEMAN basic attack animation - simple, impactful polearm sweep.
    Clean metallic blade arc with solid impact. No magic effects.
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
        self.phase = "windup"  # windup → sweep → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.windup_duration = 0.1
        self.sweep_duration = 0.25
        self.impact_duration = 0.15

        # Weapon arc drawing state
        self.sweep_progress = 0.0  # 0.0 to 1.0 during sweep phase

    def _trigger_windup(self):
        """Phase 1: Pull back polearm."""
        # Windup sound - pulling back weapon
        play_sound("glaiveman_attack_windup")

        self.attacker.shake_intensity = 5

    def _trigger_sweep(self):
        """Phase 2: Wide sweeping arc - silver blade trail."""
        # Sweep sound - blade whoosh
        play_sound("glaiveman_attack_sweep")

        # Calculate perpendicular vector for arc
        perp_x = -self.dy
        perp_y = self.dx

        # Create wide arc sweep (25 particles)
        particle_count = 25
        arc_width = 30  # Width of arc in pixels

        for i in range(particle_count):
            progress = i / particle_count

            # Position along attack vector
            base_x = self.attacker.x + self.dx * self.distance * progress
            base_y = self.attacker.y + self.dy * self.distance * progress

            # Arc offset (sine curve for natural sweep)
            arc_offset = math.sin(progress * math.pi) * arc_width

            # Final particle position
            particle_x = base_x + perp_x * arc_offset
            particle_y = base_y + perp_y * arc_offset

            # Velocity continues in sweep direction
            speed = random.uniform(300, 500)
            vx = self.dx * speed + perp_x * arc_offset * 3
            vy = self.dy * speed + perp_y * arc_offset * 3

            # Silver/white metallic colors only
            color = random.choice([
                (192, 192, 192),  # Silver
                (232, 232, 232),  # Light silver
                (255, 255, 255),  # White
            ])

            size = random.uniform(4, 7)
            lifetime = random.uniform(0.15, 0.25)

            particle = Particle(particle_x, particle_y, vx, vy, color, size, lifetime)
            particle.gravity = 0  # No gravity for blade sweep
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Metal impact sparks at target."""
        # Impact sound - metal hitting
        play_sound("glaiveman_attack_impact")

        # Impact sparks - white/silver only (metal on metal)
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Metallic impact colors
            color = random.choice([
                (255, 255, 255),  # White
                (240, 240, 240),  # Bright white
                (200, 200, 200),  # Silver
            ])

            size = random.uniform(3, 6)
            lifetime = random.uniform(0.1, 0.2)

            particle = Particle(self.target.x, self.target.y, vx, vy, color, size, lifetime)
            particle.gravity = 150
            self.particle_emitter.particles.append(particle)

        # Strong impact feel
        self.target.shake_intensity = 14
        self.screen_shake(7, 0.15)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "windup":
            if self.timer >= self.windup_duration:
                self.phase = "sweep"
                self.timer = 0
                self._trigger_sweep()

        elif self.phase == "sweep":
            # Update sweep progress for weapon drawing
            self.sweep_progress = min(1.0, self.timer / self.sweep_duration)

            if self.timer >= self.sweep_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw the actual polearm blade arc during sweep phase."""
        import pygame

        # Only draw weapon during sweep phase
        if self.phase != "sweep":
            return

        # Calculate perpendicular vector for arc sweep
        perp_x = -self.dy
        perp_y = self.dx

        # Draw the blade arc as a thick line/polygon
        # The blade sweeps from one side to the other
        arc_width = 35  # How wide the arc spreads
        blade_length = self.distance + 20  # Extend past target slightly

        # Calculate arc points along the sweep
        points = []
        num_segments = 15

        for i in range(num_segments):
            progress = (i / (num_segments - 1)) * self.sweep_progress

            # Position along attack vector
            base_x = self.attacker.x + self.dx * blade_length * progress
            base_y = self.attacker.y + self.dy * blade_length * progress

            # Arc offset (sine curve for natural weapon sweep)
            arc_offset = math.sin(progress * math.pi) * arc_width

            # Calculate point position
            point_x = base_x + perp_x * arc_offset
            point_y = base_y + perp_y * arc_offset

            points.append((int(point_x), int(point_y)))

        # Draw the blade arc as a thick line
        if len(points) >= 2:
            # Draw white core (the blade itself)
            pygame.draw.lines(surface, (255, 255, 255), False, points, 4)
            # Draw silver outline for depth
            pygame.draw.lines(surface, (180, 180, 180), False, points, 6)


