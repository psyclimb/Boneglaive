#!/usr/bin/env python3
"""
GLAIVEMAN Animation Classes
Skill animations for the GLAIVEMAN unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, Particle, DebrisParticle

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
        gold = (255, 215, 0)
        light_gold = (255, 235, 100)
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
            pygame.draw.polygon(self.base_surface, gold,
                              [(center, center), (tip_x, tip_y), (side1_x, side1_y)])
            pygame.draw.polygon(self.base_surface, gold,
                              [(center, center), (tip_x, tip_y), (side2_x, side2_y)])

            # Highlight edge
            pygame.draw.line(self.base_surface, light_gold,
                           (center, center), (tip_x, tip_y), 2)

        # Center hub
        pygame.draw.circle(self.base_surface, white, (center, center), 6)
        pygame.draw.circle(self.base_surface, gold, (center, center), 6, 2)
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
        pygame.draw.circle(glow_surf, (255, 215, 0, 50),
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

        print(f"  [VAULT] Starting vault from ({caster_unit.grid_x}, {caster_unit.grid_y}) to {target_pos}")

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

        print(f"  [PRY_IMPACT] Starting simplified pry animation on {target_unit.name}")
        print(f"  [PRY_IMPACT] Found {len(self.adjacent_targets)} adjacent targets for splash")

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


