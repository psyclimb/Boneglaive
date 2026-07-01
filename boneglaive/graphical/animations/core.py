#!/usr/bin/env python3
"""Core animation classes, particles, and shared constants for the graphical renderer."""
import pygame
import random
import math
from typing import List, Tuple
from boneglaive.utils.paths import load_svg


# Constants (shared across all modules)
# TILE_SIZE is now dynamically calculated based on resolution
# Import it from the renderer to stay in sync
def _get_tile_size():
    """Get dynamic tile size from config-based calculations."""
    from boneglaive.utils.config import ConfigManager
    config = ConfigManager()
    screen_width = config.get('window_width', 1280)
    left_panel_ratio = 0.21875  # 280/1280
    game_board_width = screen_width * (1 - 2 * left_panel_ratio)
    return int(game_board_width // 20)  # 20 tiles wide

TILE_SIZE = _get_tile_size()

# Attack animation colors

# Colors (shared)
COLOR_PLAYER1 = (100, 150, 255)
COLOR_PLAYER2 = (255, 150, 150)
COLOR_DAMAGE = (255, 50, 50)
COLOR_HEAL = (50, 255, 100)
COLOR_SKILL = (200, 100, 255)

class Particle:
    """Simple particle for effects."""
    # Class-level cache for particle surfaces (shared across all particles)
    _surface_cache = {}

    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = 0
        self.fade = True

    def update(self, delta_time):
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.vy += self.gravity * delta_time
        self.lifetime -= delta_time
        return self.lifetime > 0

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime)) if self.fade else 255
        color = (*self.color[:3], alpha)

        # Performance: Use cached surface for this particle size
        size_int = int(self.size)
        if size_int not in Particle._surface_cache:
            surf_size = size_int * 2
            Particle._surface_cache[size_int] = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

        # Get cached surface and clear it
        particle_surf = Particle._surface_cache[size_int]
        particle_surf.fill((0, 0, 0, 0))

        # Draw particle on cached surface
        pygame.draw.circle(particle_surf, color, (size_int, size_int), size_int)
        surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))


class ParticleEmitter:
    """Manages particle effects."""
    def __init__(self):
        self.particles: List[Particle] = []

    def emit_burst(self, x, y, color, count=20):
        """Emit a burst of particles (explosions, impacts)."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 5)
            lifetime = random.uniform(0.3, 0.8)
            particle = Particle(x, y, vx, vy, color, size, lifetime)
            particle.gravity = 200
            self.particles.append(particle)

    def emit_trail(self, x, y, color, count=5):
        """Emit trailing particles (movement trails)."""
        for _ in range(count):
            vx = random.uniform(-20, 20)
            vy = random.uniform(-20, 20)
            size = random.uniform(1, 3)
            lifetime = random.uniform(0.2, 0.5)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def emit_float(self, x, y, color, count=10):
        """Emit floating particles (healing, buffs)."""
        for _ in range(count):
            vx = random.uniform(-10, 10)
            vy = random.uniform(-60, -20)
            size = random.uniform(2, 4)
            lifetime = random.uniform(0.5, 1.5)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def emit_beam(self, x1, y1, x2, y2, color, count=30):
        """Emit particles along a beam (ranged attacks)."""
        for i in range(count):
            t = i / count
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            vx = random.uniform(-5, 5)
            vy = random.uniform(-5, 5)
            size = random.uniform(2, 4)
            lifetime = random.uniform(0.1, 0.3)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def emit_blood_explosion(self, x, y, count=80):
        """Emit a blood explosion (death animation)."""
        # Blood color palette (various shades of red/crimson)
        blood_colors = [
            (180, 0, 0),    # Dark red
            (220, 20, 20),  # Blood red
            (160, 10, 10),  # Deep crimson
            (200, 30, 30),  # Bright blood
            (140, 0, 0),    # Very dark red
        ]

        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            # Explosive outward burst with variation
            speed = random.uniform(100, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            # Varied particle sizes for chunky blood splatter
            size = random.uniform(3, 8)
            lifetime = random.uniform(0.5, 1.2)
            color = random.choice(blood_colors)
            particle = Particle(x, y, vx, vy, color, size, lifetime)
            # Heavy gravity for realistic blood drops
            particle.gravity = 400
            self.particles.append(particle)

        # Add some slower drifting blood mist
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 60)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 4)
            lifetime = random.uniform(0.8, 1.5)
            color = (120, 0, 0)  # Darker mist
            particle = Particle(x, y, vx, vy, color, size, lifetime)
            particle.gravity = 100
            self.particles.append(particle)

    def update(self, delta_time):
        self.particles = [p for p in self.particles if p.update(delta_time)]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


class VaporParticleCloud:
    """
    Procedural particle-based rendering for HEINOUS VAPOR entities.
    Creates swirling gaseous cloud with glowing eyes.
    """

    # Color palettes for different vapor types (matching GAS MACHINIST sprite bottles)
    VAPOR_COLORS = {
        'BROACHING': [(34, 139, 34), (50, 205, 50), (144, 238, 144)],    # Green bottle colors
        'SAFETY': [(30, 144, 255), (65, 105, 225), (135, 206, 250)],     # Blue bottle colors
        'COOLANT': [(240, 248, 255), (255, 255, 255), (248, 248, 255)],  # White
        'CUTTING': [(220, 20, 60), (255, 99, 71), (255, 127, 80)],       # Red bottle colors
        'CALIBRATION': [(255, 215, 0), (218, 165, 32), (255, 223, 0)],  # Yellow (safety glasses)
        'LIVING_AEROSOL': [(106, 106, 106), (139, 139, 139), (176, 176, 176)]  # Gray (matching icon)
    }

    def __init__(self, vapor_type='BROACHING'):
        """
        Initialize vapor particle cloud.

        Args:
            vapor_type: Type of vapor (BROACHING, SAFETY, COOLANT, CUTTING)
        """
        self.vapor_type = vapor_type
        self.colors = self.VAPOR_COLORS.get(vapor_type, self.VAPOR_COLORS['BROACHING'])

        # Animation timers
        self.time = 0
        self.breathing_phase = 0
        self.swirl_phase = 0
        self.eye_pulse_phase = 0

        # Particle system
        self.particles = []
        self._initialize_particles()

        # Performance: Cache particle and glow surfaces
        self._particle_surface_cache = {}  # size -> surface
        self._eye_glow_surface = None  # Cached eye glow surface

    def _initialize_particles(self):
        """Create initial particle cloud."""
        particle_count = 70  # Increased from 50 for denser clouds
        for i in range(particle_count):
            # Distribute particles in layers (varying radii)
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(8, 28)

            self.particles.append({
                'angle': angle,
                'base_radius': radius,
                'radius': radius,
                'orbit_speed': random.uniform(0.5, 1.5),
                'size': random.uniform(2, 5),
                'color': random.choice(self.colors),
                'opacity': random.uniform(0.4, 0.8),
                'z': random.uniform(0, 1),  # Depth layering
                'drift_x': random.uniform(-5, 5),
                'drift_y': random.uniform(-5, 5)
            })

    def update(self, delta_time):
        """Update vapor cloud animation."""
        self.time += delta_time
        self.breathing_phase += delta_time * 1.5  # Breathing cycle
        self.swirl_phase += delta_time * 0.8      # Swirling motion
        self.eye_pulse_phase += delta_time * 3.0   # Eye pulsing

        # Breathing effect (expand/contract)
        breathing_scale = 1.0 + math.sin(self.breathing_phase) * 0.15

        # Update each particle
        for particle in self.particles:
            # Orbital swirling motion
            particle['angle'] += particle['orbit_speed'] * delta_time

            # Apply breathing
            particle['radius'] = particle['base_radius'] * breathing_scale

            # Gentle drifting
            particle['drift_x'] += random.uniform(-2, 2) * delta_time
            particle['drift_y'] += random.uniform(-2, 2) * delta_time
            # Clamp drift
            particle['drift_x'] = max(-10, min(10, particle['drift_x']))
            particle['drift_y'] = max(-10, min(10, particle['drift_y']))

    def draw(self, surface, center_x, center_y):
        """
        Draw the vapor cloud at specified position.

        Args:
            surface: Pygame surface to draw on
            center_x: Center X coordinate
            center_y: Center Y coordinate
        """
        # Sort particles by z-depth for proper layering
        sorted_particles = sorted(self.particles, key=lambda p: p['z'])

        # Draw vapor particles
        for particle in sorted_particles:
            # Calculate particle position
            px = center_x + math.cos(particle['angle']) * particle['radius'] + particle['drift_x']
            py = center_y + math.sin(particle['angle']) * particle['radius'] + particle['drift_y']

            # Calculate alpha based on depth and base opacity
            alpha = int(255 * particle['opacity'] * (0.6 + 0.4 * particle['z']))
            if alpha <= 0:
                continue

            color = (*particle['color'], alpha)
            size = particle['size']

            # Performance: Use cached surface for this particle size
            size_int = int(size)
            if size_int not in self._particle_surface_cache:
                surf_size = size_int * 4
                self._particle_surface_cache[size_int] = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

            # Get cached surface and clear it
            particle_surf = self._particle_surface_cache[size_int]
            particle_surf.fill((0, 0, 0, 0))

            # Outer glow
            glow_radius = size * 1.5
            pygame.draw.circle(particle_surf, (*particle['color'], alpha // 3),
                             (int(size * 2), int(size * 2)), int(glow_radius))

            # Core particle
            pygame.draw.circle(particle_surf, color,
                             (int(size * 2), int(size * 2)), int(size))

            surface.blit(particle_surf, (int(px - size * 2), int(py - size * 2)))

        # Draw glowing eyes on top
        self._draw_eyes(surface, center_x, center_y)

    def _draw_eyes(self, surface, center_x, center_y):
        """Draw glowing eyes within the vapor cloud."""
        # Eye pulsing (0.7 to 1.0)
        pulse = 0.7 + math.sin(self.eye_pulse_phase) * 0.15

        # Eye positions (slightly offset from center)
        eye_spacing = 10
        left_eye_x = center_x - eye_spacing
        right_eye_x = center_x + eye_spacing
        eye_y = center_y - 3

        # Eye color (bright yellow-green)
        eye_color = (173, 255, 47)

        # Performance: Create cached eye glow surface once
        if self._eye_glow_surface is None:
            glow_size = 8
            self._eye_glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)

        # Draw each eye
        for eye_x in [left_eye_x, right_eye_x]:
            # Outer glow (using cached surface)
            glow_size = 8
            glow_alpha = int(80 * pulse)
            glow_surf = self._eye_glow_surface
            glow_surf.fill((0, 0, 0, 0))
            pygame.draw.circle(glow_surf, (*eye_color, glow_alpha),
                             (glow_size, glow_size), glow_size)
            surface.blit(glow_surf, (int(eye_x - glow_size), int(eye_y - glow_size)))

            # Main eye
            eye_radius = 4
            eye_alpha = int(230 * pulse)
            pygame.draw.circle(surface, (*eye_color, eye_alpha),
                             (int(eye_x), int(eye_y)), eye_radius)

            # Bright highlight
            highlight_radius = 2
            highlight_alpha = int(255 * pulse)
            pygame.draw.circle(surface, (255, 255, 200, highlight_alpha),
                             (int(eye_x - 1), int(eye_y - 1)), highlight_radius)


class AnimatedUnit:
    """Unit with smooth animation support."""
    def __init__(self, name, player, grid_x, grid_y, color, sprite_path=None, game_unit=None):
        self.name = name
        self.player = player
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.color = color
        self.game_unit = game_unit  # Reference to game logic unit

        # Position
        self.x = grid_x * TILE_SIZE + TILE_SIZE // 2
        self.y = grid_y * TILE_SIZE + TILE_SIZE // 2

        # Animation
        self.target_x = self.x
        self.target_y = self.y
        self.is_moving = False
        self.move_speed = 400

        # Visual effects
        self.shake_x = 0
        self.shake_y = 0
        self.shake_intensity = 0
        self.hop_offset = 0
        self.hop_phase = 0
        self.glaive_rotation = 0  # For spinning attack glaive effect
        self.tool_orbit_angle = 0  # For orbiting skill tools effect

        # Potpourri aura (for POTPOURRIST)
        self.potpourri_aura_active = False
        self.potpourri_aura_timer = 0
        self.potpourri_aura_particles = []

        # Vapor particle cloud (for HEINOUS VAPOR)
        self.vapor_cloud = None
        self._detect_vapor_type()

        # Performance: Cache particle surfaces to avoid creating new ones every frame
        self._particle_surface_cache = {}  # size -> surface mapping

        # Status effect cycling display
        self.status_active_effects = []  # List of effect name strings
        self.status_cycle_timer = 0.0    # Time since last flash
        self.status_cycle_index = 0      # Current index in effects list
        self.status_flash_timer = None   # None = idle, float = flash in progress
        self.status_flash_icon = None    # Cached surface for current flash
        self._status_icon_cache = {}     # {effect_name: surface}

        # Stats
        self.max_hp = 20
        self.hp = 20

        # Render
        self.radius = 24
        self.sprite = None
        self.sprite_rect = None

        # Load sprite if path provided
        if sprite_path:
            self.sprite = load_svg(sprite_path, TILE_SIZE, TILE_SIZE)
            if self.sprite is None:
                # Fallback: create a colored circle placeholder
                self.sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(self.sprite, self.color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3)
                pygame.draw.circle(self.sprite, (255, 255, 255), (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3, 2)
            if self.sprite:
                self.sprite_rect = self.sprite.get_rect()

    def _detect_vapor_type(self):
        """Detect if this unit is a HEINOUS VAPOR and initialize particle cloud."""
        if not self.game_unit:
            return

        # Check if this is a HEINOUS_VAPOR unit
        try:
            from boneglaive.utils.constants import UnitType
            if hasattr(self.game_unit, 'type') and self.game_unit.type == UnitType.HEINOUS_VAPOR:
                # Get vapor type from game unit
                vapor_type = getattr(self.game_unit, 'vapor_type', 'BROACHING')
                self.vapor_cloud = VaporParticleCloud(vapor_type)
        except Exception as e:
            pass

    def _create_red_glaive_sprites(self):
        """Create red six-pointed glaive sprites for attack indication (3 glaives to match tool orbit pattern)."""
        glaives = []
        size = 24  # Match tool size for consistency

        # Create 3 identical glaive sprites
        for _ in range(3):
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            center = size // 2

            # Red color scheme
            blade_color = (255, 80, 80)  # Crimson red
            blade_highlight = (255, 120, 120)  # Bright red
            hub_color = (180, 40, 40)  # Dark red/maroon

            # Draw six pointed blades radiating from center (scaled down for 24x24)
            blade_length = size // 2 - 2
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
                pygame.draw.polygon(surface, blade_color,
                                  [(center, center), (tip_x, tip_y), (side1_x, side1_y)])
                pygame.draw.polygon(surface, blade_color,
                                  [(center, center), (tip_x, tip_y), (side2_x, side2_y)])

                # Highlight edge
                pygame.draw.line(surface, blade_highlight,
                               (center, center), (tip_x, tip_y), 1)

            # Center hub (scaled down)
            pygame.draw.circle(surface, blade_highlight, (center, center), 3)
            pygame.draw.circle(surface, blade_color, (center, center), 3, 1)
            pygame.draw.circle(surface, hub_color, (center, center), 2)

            glaives.append(surface)

        return glaives

    def _create_purple_tool_sprites(self):
        """Create purple tool sprites (wrench, hammer, screwdriver) for skill indication."""
        tools = []
        size = 24

        # Darker purple color scheme (matching pip colors)
        tool_color = (140, 80, 200)  # Darker purple
        tool_dark = (100, 50, 150)  # Very dark purple
        tool_highlight = (180, 120, 230)  # Medium purple

        # Tool 1: Wrench
        wrench = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        # Wrench handle (diagonal)
        pygame.draw.line(wrench, tool_color, (6, 18), (14, 10), 4)
        # Wrench head (open end)
        pygame.draw.circle(wrench, tool_dark, (17, 7), 5, 2)
        pygame.draw.rect(wrench, tool_dark, (17, 4, 3, 6))
        tools.append(wrench)

        # Tool 2: Hammer
        hammer = pygame.Surface((size, size), pygame.SRCALPHA)
        # Hammer handle
        pygame.draw.line(hammer, tool_color, (12, 18), (12, 8), 3)
        # Hammer head
        pygame.draw.rect(hammer, tool_dark, (7, 6, 10, 5))
        pygame.draw.rect(hammer, tool_highlight, (7, 6, 10, 2))
        tools.append(hammer)

        # Tool 3: Screwdriver
        screwdriver = pygame.Surface((size, size), pygame.SRCALPHA)
        # Screwdriver handle (fat)
        pygame.draw.line(screwdriver, tool_color, (12, 16), (12, 10), 5)
        # Screwdriver shaft
        pygame.draw.line(screwdriver, tool_dark, (12, 10), (12, 5), 2)
        # Screwdriver tip
        pygame.draw.line(screwdriver, tool_highlight, (10, 5), (14, 5), 2)
        tools.append(screwdriver)

        return tools

    def move_to_grid(self, grid_x, grid_y):
        """Start smooth movement to grid position."""
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.target_x = grid_x * TILE_SIZE + TILE_SIZE // 2
        self.target_y = grid_y * TILE_SIZE + TILE_SIZE // 2
        self.is_moving = True
        self.hop_phase = math.pi

    def take_damage(self, amount):
        """Apply damage and trigger shake effect."""
        self.hp = max(0, self.hp - amount)
        self.shake_intensity = 10

    def heal(self, amount):
        """Apply healing."""
        self.hp = min(self.max_hp, self.hp + amount)

    def update(self, delta_time):
        # Smooth movement
        if self.is_moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance < 2:
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
                self.hop_offset = 0
            else:
                move_amount = self.move_speed * delta_time
                if move_amount > distance:
                    move_amount = distance
                self.x += (dx / distance) * move_amount
                self.y += (dy / distance) * move_amount

                # Hop animation
                self.hop_phase -= delta_time * 10
                self.hop_offset = abs(math.sin(self.hop_phase)) * 15

        # Shake effect
        if self.shake_intensity > 0:
            self.shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity -= delta_time * 50
            if self.shake_intensity < 0:
                self.shake_intensity = 0
                self.shake_x = 0
                self.shake_y = 0

        # Glaive rotation for attack effect
        self.glaive_rotation += 360 * delta_time  # 1 full rotation per second
        if self.glaive_rotation >= 360:
            self.glaive_rotation -= 360

        # Tool orbit for skill effect
        self.tool_orbit_angle += 180 * delta_time  # Slower orbit - half rotation per second
        if self.tool_orbit_angle >= 360:
            self.tool_orbit_angle -= 360

        # Potpourri aura effect
        if self.potpourri_aura_active:
            self.potpourri_aura_timer += delta_time

            # Spawn new aura particles periodically
            if int(self.potpourri_aura_timer * 20) % 3 == 0 and len(self.potpourri_aura_particles) < 15:
                # Random position around unit
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(15, 30)
                px = self.x + math.cos(angle) * distance
                py = self.y + math.sin(angle) * distance

                self.potpourri_aura_particles.append({
                    'x': px,
                    'y': py,
                    'vx': random.uniform(-10, 10),
                    'vy': random.uniform(-30, -10),  # Float upward
                    'lifetime': random.uniform(1.0, 2.0),
                    'max_lifetime': 2.0,
                    'size': random.uniform(2, 4),
                    'color': random.choice([
                        (200, 100, 200),  # Purple
                        (255, 150, 200),  # Pink
                        (180, 100, 255),  # Violet
                        (255, 100, 150)   # Rose
                    ]),
                    'orbit_angle': angle,
                    'orbit_speed': random.uniform(1.0, 2.0)
                })

            # Update aura particles
            for particle in self.potpourri_aura_particles[:]:
                # Gentle orbiting motion
                particle['orbit_angle'] += particle['orbit_speed'] * delta_time
                orbit_influence = 0.3
                particle['vx'] += math.cos(particle['orbit_angle']) * 20 * delta_time * orbit_influence
                particle['vy'] += math.sin(particle['orbit_angle']) * 20 * delta_time * orbit_influence

                # Move
                particle['x'] += particle['vx'] * delta_time
                particle['y'] += particle['vy'] * delta_time

                # Age
                particle['lifetime'] -= delta_time
                if particle['lifetime'] <= 0:
                    self.potpourri_aura_particles.remove(particle)

        # Update vapor cloud (for HEINOUS VAPOR)
        if self.vapor_cloud:
            self.vapor_cloud.update(delta_time)

        # Update status effect cycling
        if self.status_active_effects:
            self.status_cycle_timer += delta_time

            # Advance flash timer if a flash is in progress
            if self.status_flash_timer is not None:
                self.status_flash_timer += delta_time
                if self.status_flash_timer >= 0.9:
                    self.status_flash_timer = None

            # Trigger next flash when interval expires and no flash is active
            if self.status_flash_timer is None and self.status_cycle_timer >= 4.0:
                self.status_cycle_timer = 0.0
                effect_name = self.status_active_effects[self.status_cycle_index]
                self.status_flash_icon = self._load_status_icon(effect_name)
                self.status_flash_timer = 0.0
                self.status_cycle_index = (self.status_cycle_index + 1) % len(self.status_active_effects)
        else:
            self.status_cycle_timer = 0.0
            self.status_flash_timer = None
            self.status_cycle_index = 0

    def _load_status_icon(self, effect_name):
        """Load and cache a status effect icon SVG at cycling display size."""
        if effect_name in self._status_icon_cache:
            return self._status_icon_cache[effect_name]

        icon_size = 64
        icon_path = f"graphics/status_icons/{effect_name}.svg"
        icon_surface = load_svg(icon_path, icon_size, icon_size)
        if icon_surface is None:
            # Fallback: colored circle placeholder
            icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            pygame.draw.circle(icon_surface, (255, 100, 100),
                               (icon_size // 2, icon_size // 2), icon_size // 3)
            pygame.draw.circle(icon_surface, (255, 255, 255),
                               (icon_size // 2, icon_size // 2), icon_size // 3, 2)

        self._status_icon_cache[effect_name] = icon_surface
        return icon_surface

    def draw(self, surface, font):
        # Calculate final position
        final_x = int(self.x + self.shake_x)
        final_y = int(self.y + self.shake_y - self.hop_offset)

        # Apply respawn animation offset (if active)
        if hasattr(self, 'respawn_y_offset') and self.respawn_y_offset > 0:
            final_y += int(self.respawn_y_offset)

        # Draw potpourri aura particles (behind unit)
        if self.potpourri_aura_active:
            for particle in self.potpourri_aura_particles:
                if particle['lifetime'] > 0:
                    alpha = int(200 * (particle['lifetime'] / particle['max_lifetime']))
                    if alpha > 0:
                        # Performance: Use cached surface for this particle size
                        size_key = int(particle['size'])
                        if size_key not in self._particle_surface_cache:
                            # Create and cache a base surface for this size
                            surf_size = size_key * 2 + 8  # Extra space for glow
                            base_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                            self._particle_surface_cache[size_key] = base_surf

                        # Get cached surface and clear it
                        particle_surf = self._particle_surface_cache[size_key]
                        particle_surf.fill((0, 0, 0, 0))  # Clear previous frame

                        # Draw particle and glow on cached surface
                        center = particle_surf.get_width() // 2
                        color = (*particle['color'], alpha)
                        pygame.draw.circle(particle_surf, color, (center, center), size_key)

                        # Add glow
                        glow_size = size_key + 2
                        pygame.draw.circle(particle_surf, (*particle['color'], alpha // 3),
                                         (center, center), glow_size)

                        surface.blit(particle_surf, (int(particle['x'] - center), int(particle['y'] - center)))

        # Check if unit has queued attack or skill
        has_attack = False
        has_skill = False
        if self.game_unit:
            has_attack = hasattr(self.game_unit, 'attack_target') and self.game_unit.attack_target
            has_skill = hasattr(self.game_unit, 'skill_target') and self.game_unit.skill_target

        # Draw different glow effects for attack vs skill
        import time
        import math

        # Attack glow: Red glaives orbiting around unit (opposite direction from tools)
        if has_attack:
            # Create/cache red glaive sprites
            if not hasattr(self, '_red_glaive_sprites'):
                self._red_glaive_sprites = self._create_red_glaive_sprites()

            # Draw 3 glaives orbiting around the unit at different positions (opposite direction from tools)
            orbit_radius = self.radius + 15  # Same orbit as tools
            num_glaives = 3

            for i, glaive_sprite in enumerate(self._red_glaive_sprites):
                # Each glaive is offset by 120 degrees (360/3)
                angle_offset = (360 / num_glaives) * i
                # Negative glaive_rotation for opposite direction from tools
                glaive_angle = -self.glaive_rotation + angle_offset

                # Calculate position on orbit
                angle_rad = math.radians(glaive_angle)
                glaive_x = final_x + math.cos(angle_rad) * orbit_radius
                glaive_y = final_y + math.sin(angle_rad) * orbit_radius

                # Each glaive also spins on its own axis (opposite direction)
                glaive_self_rotation = -self.glaive_rotation * 2  # Spin faster than orbit (opposite direction)
                rotated_glaive = pygame.transform.rotate(glaive_sprite, -glaive_self_rotation)
                rotated_glaive.set_alpha(200)

                # Draw glaive
                glaive_rect = rotated_glaive.get_rect(center=(int(glaive_x), int(glaive_y)))
                surface.blit(rotated_glaive, glaive_rect)

            # Add subtle red glow in center
            glow_size = 60
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 100, 100, 30),
                             (glow_size // 2, glow_size // 2), glow_size // 2)
            glow_rect = glow_surf.get_rect(center=(final_x, final_y))
            surface.blit(glow_surf, glow_rect)

        # Skill glow: Purple tools orbiting around unit
        elif has_skill:
            # Create/cache purple tool sprites
            if not hasattr(self, '_purple_tool_sprites'):
                self._purple_tool_sprites = self._create_purple_tool_sprites()

            # Draw 3 tools orbiting around the unit at different positions
            orbit_radius = self.radius + 15  # Smaller orbit
            num_tools = 3

            for i, tool_sprite in enumerate(self._purple_tool_sprites):
                # Each tool is offset by 120 degrees (360/3)
                angle_offset = (360 / num_tools) * i
                tool_angle = self.tool_orbit_angle + angle_offset

                # Calculate position on orbit
                angle_rad = math.radians(tool_angle)
                tool_x = final_x + math.cos(angle_rad) * orbit_radius
                tool_y = final_y + math.sin(angle_rad) * orbit_radius

                # Each tool also spins on its own axis
                tool_rotation = self.tool_orbit_angle * 2  # Spin faster than orbit
                rotated_tool = pygame.transform.rotate(tool_sprite, -tool_rotation)
                rotated_tool.set_alpha(200)

                # Draw tool
                tool_rect = rotated_tool.get_rect(center=(int(tool_x), int(tool_y)))
                surface.blit(rotated_tool, tool_rect)

            # Add subtle darker purple glow in center
            glow_size = 60
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (140, 80, 200, 30),
                             (glow_size // 2, glow_size // 2), glow_size // 2)
            glow_rect = glow_surf.get_rect(center=(final_x, final_y))
            surface.blit(glow_surf, glow_rect)

        # Check if unit is under Karrier Rave effect (phased out of reality)
        is_karrier_rave = (hasattr(self.game_unit, 'carrier_rave_active') and
                          self.game_unit.carrier_rave_active)

        # Draw vapor cloud (for HEINOUS VAPOR) - takes priority over sprite/circle
        if self.vapor_cloud:
            self.vapor_cloud.draw(surface, final_x, final_y)
        # Draw sprite or fallback to circle (for non-vapor units)
        elif self.sprite:
            # Check if this is a GRAYMAN ECHO (ethereal rendering)
            is_doppelganger = (hasattr(self.game_unit, 'is_doppelganger') and
                       self.game_unit.is_doppelganger)

            # Determine which sprite to use and its position
            # Combine wind_up_rotation and respawn_rotation if both are active
            total_rotation = 0
            if hasattr(self, 'wind_up_rotation') and self.wind_up_rotation != 0:
                total_rotation += self.wind_up_rotation
            if hasattr(self, 'respawn_rotation') and self.respawn_rotation != 0:
                total_rotation += self.respawn_rotation

            if total_rotation != 0:
                sprite_to_use = pygame.transform.rotate(self.sprite, -total_rotation)
                sprite_rect = sprite_to_use.get_rect(center=(final_x, final_y))
            else:
                sprite_to_use = self.sprite
                # Performance: reuse sprite_rect instead of copying
                self.sprite_rect.center = (final_x, final_y)
                sprite_rect = self.sprite_rect

            # Apply Karrier Rave effect (phased out of reality)
            if is_karrier_rave:
                # Create semi-transparent cyan-tinted sprite with scan lines
                karrier_sprite = sprite_to_use.copy()

                # Apply cyan tint overlay (brighter)
                cyan_overlay = pygame.Surface(karrier_sprite.get_size(), pygame.SRCALPHA)
                cyan_color = (120, 220, 255)  # Brighter electric cyan
                cyan_overlay.fill((*cyan_color, 140))  # ~55% cyan tint
                karrier_sprite.blit(cyan_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

                # Set to 70% opacity for better visibility (was 50%)
                karrier_sprite.set_alpha(180)

                # Draw the translucent sprite
                surface.blit(karrier_sprite, sprite_rect)

                # Draw horizontal scan lines (carrier wave effect) - brighter
                scan_line_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                current_time = time.time()
                scan_offset = int((current_time * 30) % 4)  # Moving scan lines

                for i in range(0, TILE_SIZE, 4):
                    line_y = (i + scan_offset) % TILE_SIZE
                    # Alternating opacity for scan lines (brighter)
                    alpha = 140 if (i // 4) % 2 == 0 else 80
                    pygame.draw.line(scan_line_surface, (180, 240, 255, alpha),
                                   (0, line_y), (TILE_SIZE, line_y), 2)  # Thicker lines

                scan_rect = scan_line_surface.get_rect(center=(final_x, final_y))
                surface.blit(scan_line_surface, scan_rect)

                # Occasional static glitch effect (10% chance per frame)
                if random.random() < 0.1:
                    glitch_alpha = random.randint(140, 200)  # Brighter glitch range
                    karrier_sprite.set_alpha(glitch_alpha)

            # Apply doppelganger effect if needed
            elif is_doppelganger:
                # Performance: Cache EVERYTHING about doppelganger sprites, including the loaded sprite
                banished_unit_type_name = "fallback"

                if hasattr(self.game_unit, 'banished_unit') and self.game_unit.banished_unit:
                    banished_unit = self.game_unit.banished_unit
                    banished_unit_type = banished_unit.type
                    banished_unit_type_name = str(banished_unit_type).split('.')[-1].lower()

                # Create cache key for this specific doppelganger
                cache_key = f'_doppelganger_final_{banished_unit_type_name}_{total_rotation}'

                # Check if we already have this exact doppelganger sprite cached
                if not hasattr(self, cache_key):
                    # Load or use default sprite
                    doppelganger_base_sprite = sprite_to_use  # Default

                    # Only try to load banished sprite if we have the info
                    if banished_unit_type_name != "fallback":
                        # Check if we've already loaded this base sprite before
                        base_cache_key = f'_doppelganger_base_{banished_unit_type_name}'
                        if hasattr(self, base_cache_key):
                            # Reuse previously loaded sprite
                            doppelganger_base_sprite = getattr(self, base_cache_key)
                        else:
                            # Load the sprite ONCE and cache it
                            sprite_path = f"graphics/units/{banished_unit_type_name}.svg"
                            loaded_sprite = load_svg(sprite_path, TILE_SIZE, TILE_SIZE)
                            if loaded_sprite:
                                doppelganger_base_sprite = loaded_sprite
                                # Cache the loaded base sprite
                                setattr(self, base_cache_key, doppelganger_base_sprite)

                    # Apply rotation if needed
                    if total_rotation != 0:
                        doppelganger_base_sprite = pygame.transform.rotate(doppelganger_base_sprite, -total_rotation)

                    # Create flipped doppelganger version
                    doppelganger_sprite = pygame.transform.flip(doppelganger_base_sprite, True, False)
                    doppelganger_sprite.set_alpha(180)  # ~70% opacity

                    # Cache the final processed sprite
                    setattr(self, cache_key, doppelganger_sprite)
                    setattr(self, f'{cache_key}_rect', doppelganger_sprite.get_rect())

                # Use cached doppelganger sprite
                cached_sprite = getattr(self, cache_key)
                cached_rect = getattr(self, f'{cache_key}_rect')
                cached_rect.center = (final_x, final_y)
                surface.blit(cached_sprite, cached_rect)
            else:
                # Draw normal sprite
                surface.blit(sprite_to_use, sprite_rect)
        else:
            # Draw unit circle (fallback)
            if is_karrier_rave:
                # Draw semi-transparent cyan circle for Karrier Rave (brighter)
                circle_surface = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
                center = self.radius * 2
                pygame.draw.circle(circle_surface, (*self.color, 180), (center, center), self.radius)
                pygame.draw.circle(circle_surface, (120, 220, 255, 200), (center, center), self.radius, 3)
                circle_rect = circle_surface.get_rect(center=(final_x, final_y))
                surface.blit(circle_surface, circle_rect)
            else:
                # Draw normal unit circle
                pygame.draw.circle(surface, self.color, (final_x, final_y), self.radius)
                pygame.draw.circle(surface, (255, 255, 255), (final_x, final_y), self.radius, 2)

        # Draw player-colored tile-sized box around unit
        # Green for Player 1, Blue for Player 2
        # Calculate tile position (units already have offsets baked into x,y)
        # So we need to calculate the tile corner from the unit's center position
        outline_color = (100, 255, 100) if self.player == 1 else (100, 150, 255)
        tile_x = self.x - TILE_SIZE // 2
        tile_y = self.y - TILE_SIZE // 2
        tile_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, outline_color, tile_rect, 2)

        # Draw cycling status effect icon
        if self.status_flash_timer is not None and self.status_flash_icon is not None:
            ft = self.status_flash_timer
            # Fade in 0.2s → hold 0.5s → fade out 0.2s, fully opaque at peak
            if ft < 0.2:
                alpha = int(255 * (ft / 0.2))
            elif ft < 0.7:
                alpha = 255
            else:
                alpha = int(255 * (1.0 - (ft - 0.7) / 0.2))
            alpha = max(0, min(255, alpha))
            self.status_flash_icon.set_alpha(alpha)
            icon_rect = self.status_flash_icon.get_rect(center=(final_x, final_y))
            surface.blit(self.status_flash_icon, icon_rect)

        # HP bar and name hidden for cleaner demo
        # bar_width = 50
        # bar_height = 6
        # bar_x = final_x - bar_width // 2
        # bar_y = final_y - 40

        # # Background
        # pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # # HP fill
        # hp_ratio = self.hp / self.max_hp
        # fill_width = int(bar_width * hp_ratio)
        # color = self.color if hp_ratio >= 0.3 else COLOR_DAMAGE
        # pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))

        # # Unit name
        # name_text = font.render(self.name, True, (255, 255, 255))
        # name_rect = name_text.get_rect(center=(final_x, final_y - 50))
        # surface.blit(name_text, name_rect)


class WalkIn:
    """A short walk-in that movement-skill animations prepend when the player queued a move
    before the skill.

    Several movement skills (Vault, Delta Config, Expedite, Jaunt) clear/ignore the queued
    move and resolve the unit straight to the skill's destination, so the visual layer never
    plays the walk to the move tile and the skill animation fires from the unit's PRE-MOVE
    tile. This helper walks the sprite from its pre-move tile (A) to the launch tile (B = the
    queued move destination) first; the owning controller then runs its own phases with the
    origin at B. With no queued move (B is None or equals A) it's inert: ``active`` is False
    from the start and ``duration`` is 0, so the controller behaves exactly as before.

    Usage (in a controller):
        self._walk = WalkIn(caster_unit, launch_from_grid)   # launch_from_grid = (y, x) or None
        # compute the controller's origin from (self._walk.bx, self._walk.by)
        ...
        def update(self, dt):
            if self._walk.update(dt, self.particle_emitter):
                return True            # still walking — hold the skill's own clock
            ... run the existing phase logic, which now starts from B ...
    """

    PIXELS_PER_SEC = 520.0      # walk speed; duration scales with distance
    MAX_DURATION = 0.45         # cap so a long reposition doesn't drag
    _DUST = (194, 178, 128)     # tan kick-up under the stride

    def __init__(self, caster_unit, launch_from_grid):
        self.caster = caster_unit
        self.start_x, self.start_y = caster_unit.x, caster_unit.y
        # Launch screen position B = the queued move destination, else the current tile.
        if launch_from_grid is not None:
            from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
            ly, lx = launch_from_grid
            self.bx = lx * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
            self.by = ly * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y
        else:
            self.bx, self.by = self.start_x, self.start_y
        dist = math.hypot(self.bx - self.start_x, self.by - self.start_y)
        self.duration = min(self.MAX_DURATION, dist / self.PIXELS_PER_SEC) if dist > 1.0 else 0.0
        self.had_walk = self.duration > 0.0
        self.active = self.had_walk
        self.elapsed = 0.0

    def update(self, delta_time, particle_emitter=None):
        """Advance the walk. Returns True while still walking (the caller should hold its own
        animation clock), False once the sprite has arrived at B (or immediately if inert)."""
        if not self.active:
            return False
        self.elapsed += delta_time
        if self.elapsed < self.duration:
            mt = self.elapsed / self.duration
            ease = mt * mt * (3 - 2 * mt)  # smoothstep stride
            self.caster.x = self.start_x + (self.bx - self.start_x) * ease
            self.caster.y = self.start_y + (self.by - self.start_y) * ease
            # Point the sprite's own smooth-move target at B too, so the unit's per-frame
            # update (which runs before the controller) pulls the same way and the walk-cycle
            # plays; the controller then sets the exact eased position.
            self.caster.target_x, self.caster.target_y = self.bx, self.by
            self.caster.is_moving = True
            if particle_emitter and random.random() < 0.3:
                particle_emitter.emit_trail(self.caster.x + random.uniform(-4, 4),
                                            self.caster.y + 12, self._DUST, count=1)
            return True
        # Arrived at the launch tile.
        self.active = False
        self.caster.x, self.caster.y = self.bx, self.by
        self.caster.is_moving = False
        # Clear the walk-cycle hop. Because we stop the walk by forcing is_moving=False
        # (rather than letting AnimatedUnit.update reach its arrival branch, the only place
        # that zeroes it), a non-zero hop_offset would otherwise stay frozen and draw the
        # sprite shifted upward on its tile for the rest of the game.
        self.caster.hop_offset = 0
        return False


class FloatingText:
    """Floating damage/heal numbers with Autoclave-style animation."""
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 1.5
        self.max_lifetime = 1.5
        self.vy = -60
        self.timer = 0  # For delayed text and oscillation timing

    def update(self, delta_time):
        # Handle delayed text (negative timer means waiting)
        if self.timer < 0:
            self.timer += delta_time
            return True  # Keep alive but don't move yet

        # Update position with arc trajectory
        self.y += self.vy * delta_time
        self.vy += 100 * delta_time
        self.lifetime -= delta_time
        self.timer += delta_time  # Track time for oscillation
        return self.lifetime > 0

    def draw(self, surface, font):
        # Don't draw if still waiting
        if self.timer < 0:
            return
        if self.lifetime <= 0:
            return

        # Fully opaque (no transparency)
        alpha = 255

        # Flashing outline effect
        flash_speed = 6  # flashes per second
        flash_progress = (self.timer * flash_speed) % 1.0
        outline_intensity = (1.0 - abs(flash_progress - 0.5) * 2)  # 0 to 1 to 0

        # Oscillating vertical offset (sine wave bounce)
        oscillation = math.sin(self.timer * 10) * 5
        display_y = int(self.y + oscillation)

        # Create larger, bolder font (matching Autoclave style)
        font_size = 48
        try:
            display_font = pygame.font.Font(None, font_size)
        except:
            display_font = pygame.font.SysFont('Arial', font_size, bold=True)

        # Calculate outline color that flashes (dark to bright)
        outline_base_dark = (
            max(0, self.color[0] // 4),
            max(0, self.color[1] // 4),
            max(0, self.color[2] // 4)
        )
        outline_base_bright = (
            min(255, self.color[0] // 2),
            min(255, self.color[1] // 2),
            min(255, self.color[2] // 2)
        )
        # Interpolate between dark and bright based on flash
        outline_color = (
            int(outline_base_dark[0] + (outline_base_bright[0] - outline_base_dark[0]) * outline_intensity),
            int(outline_base_dark[1] + (outline_base_bright[1] - outline_base_dark[1]) * outline_intensity),
            int(outline_base_dark[2] + (outline_base_bright[2] - outline_base_dark[2]) * outline_intensity)
        )

        # Draw 4-corner outline/shadow with flashing effect
        outline_surf = display_font.render(self.text, True, outline_color)
        outline_surf.set_alpha(alpha)
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            outline_rect = outline_surf.get_rect(center=(int(self.x + dx), display_y + dy))
            surface.blit(outline_surf, outline_rect)

        # Draw main text
        text_surf = display_font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(int(self.x), display_y))
        surface.blit(text_surf, text_rect)


class DebrisParticle:
    """Falling debris chunks from PRY impact."""
    def __init__(self, x, y, vx, vy, size, color, target_unit=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-500, 500)
        self.lifetime = 1.0
        self.gravity = 400
        self.target_unit = target_unit  # The unit this debris is falling toward
        self.has_hit = False  # Track if we've already hit the target

    def update(self, delta_time):
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.vy += self.gravity * delta_time
        self.rotation += self.rotation_speed * delta_time
        self.lifetime -= delta_time
        return self.lifetime > 0

    def check_collision(self, units, particle_emitter):
        """Check if debris has hit its target unit and create impact effect."""
        if self.has_hit or not self.target_unit:
            return False

        # Check if debris has reached the target unit's position
        dx = self.x - self.target_unit.x
        dy = self.y - self.target_unit.y
        distance = math.sqrt(dx*dx + dy*dy)

        # If debris is within collision range of the target
        if distance < 25 and self.y >= self.target_unit.y - 20:
            self.has_hit = True

            # Create impact effects at the target location
            # Dust burst
            particle_emitter.emit_burst(self.target_unit.x, self.target_unit.y, (150, 130, 100), 15)

            # Ground dust on tile
            for _ in range(10):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(30, 80)
                particle = Particle(self.target_unit.x, self.target_unit.y + 15,
                                   math.cos(angle) * speed, math.sin(angle) * speed - 20,
                                   (120, 100, 80), random.uniform(3, 6), 0.6)
                particle.gravity = 150
                particle_emitter.particles.append(particle)

            # Mark debris for removal
            self.lifetime = 0
            return True

        return False

    def draw(self, surface):
        if self.lifetime <= 0:
            return

        alpha = 255  # Full opacity for visibility

        # Draw as jagged rock chunk
        debris_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)

        # Create rough rock shape
        center = int(self.size)
        pygame.draw.circle(debris_surf, (*self.color, alpha), (center, center), int(self.size))
        pygame.draw.circle(debris_surf, (80, 70, 60, alpha), (center, center), int(self.size), 2)

        # Rotate
        rotated = pygame.transform.rotate(debris_surf, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class StatusIconFlash:
    """
    Flashes a status effect icon on a unit's tile.
    Icon fades in, holds, then fades out with semi-transparency.
    """

    def __init__(self, unit, effect_name):
        """
        Args:
            unit: AnimatedUnit to flash icon on
            effect_name: Name of the status effect (maps to icon filename)
        """
        self.unit = unit
        self.effect_name = effect_name
        self.active = True

        # Animation timing
        self.timer = 0
        self.fade_in_duration = 0.2
        self.hold_duration = 0.4
        self.fade_out_duration = 0.3
        self.total_duration = self.fade_in_duration + self.hold_duration + self.fade_out_duration

        # Load icon
        self.icon_surface = None
        self.icon_size = 96  # Icon size in pixels
        icon_path = f"graphics/status_icons/{effect_name}.svg"

        self.icon_surface = load_svg(icon_path, self.icon_size, self.icon_size)
        if self.icon_surface is None:
            # Fallback: create colored circle as placeholder
            self.icon_surface = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            pygame.draw.circle(self.icon_surface, (255, 100, 100), (self.icon_size//2, self.icon_size//2), self.icon_size//3)
            pygame.draw.circle(self.icon_surface, (255, 255, 255), (self.icon_size//2, self.icon_size//2), self.icon_size//3, 2)


    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.total_duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw the icon on the unit's tile with fade in/out."""
        if not self.active or not self.icon_surface:
            return

        # Calculate alpha based on phase
        if self.timer < self.fade_in_duration:
            # Fade in
            progress = self.timer / self.fade_in_duration
            alpha = int(180 * progress)  # Max 180 for semi-transparency
        elif self.timer < self.fade_in_duration + self.hold_duration:
            # Hold
            alpha = 180  # Semi-transparent
        else:
            # Fade out
            fade_out_progress = (self.timer - self.fade_in_duration - self.hold_duration) / self.fade_out_duration
            alpha = int(180 * (1.0 - fade_out_progress))

        # Performance: Set alpha directly on original surface instead of copying
        # Note: This modifies the surface but it's acceptable for status icons
        # as they're animated temporarily and alpha changes each frame anyway
        self.icon_surface.set_alpha(alpha)

        # Draw centered on unit's position
        if not hasattr(self, '_icon_rect'):
            self._icon_rect = self.icon_surface.get_rect()
        self._icon_rect.center = (int(self.unit.x), int(self.unit.y - 10))  # Slightly above unit center
        surface.blit(self.icon_surface, self._icon_rect)


class BasicMeleeAttackAnimation:
    """
    Generic melee attack animation for all units.
    Shows a quick slash arc from attacker to target, followed by impact effects.

    Animation phases:
    1. Wind-up: Attacker leans back slightly (0.1s)
    2. Slash: Slash arc particles fly from attacker to target (0.2s)
    3. Impact: Flash and impact particles at target (0.15s)
    """

    def __init__(self, attacker_unit, target_unit, particle_emitter, screen_shake_callback):
        """
        Args:
            attacker_unit: AnimatedUnit doing the attacking
            target_unit: AnimatedUnit being attacked (or None for position-based)
            particle_emitter: ParticleEmitter for effects
            screen_shake_callback: Function(intensity, duration)
        """
        self.attacker = attacker_unit
        self.target = target_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback

        # Animation state
        self.phase = "windup"  # windup → slash → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.windup_duration = 0.1
        self.slash_duration = 0.2
        self.impact_duration = 0.15

        # Calculate attack direction
        if target_unit:
            self.target_x = target_unit.x
            self.target_y = target_unit.y
        else:
            # Fallback if no target unit (shouldn't happen for melee)
            self.target_x = attacker_unit.x + 64
            self.target_y = attacker_unit.y

        self.dx = self.target_x - attacker_unit.x
        self.dy = self.target_y - attacker_unit.y
        distance = math.sqrt(self.dx * self.dx + self.dy * self.dy)
        if distance > 0:
            self.dx /= distance
            self.dy /= distance


    def _trigger_windup(self):
        """Phase 1: Wind-up lean back."""
        # No particles, just attacker leans back (handled by attacker shake)
        self.attacker.shake_intensity = 5

    def _trigger_slash(self):
        """Phase 2: Slash arc particles."""
        # Create slash arc particles traveling from attacker to target
        for i in range(15):
            # Spawn particles along the attack vector
            progress = i / 15.0
            start_x = self.attacker.x + self.dx * 20
            start_y = self.attacker.y + self.dy * 20

            # Add some perpendicular spread for slash width
            perp_x = -self.dy
            perp_y = self.dx
            spread = random.uniform(-15, 15)

            particle_x = start_x + spread * perp_x
            particle_y = start_y + spread * perp_y

            # Velocity toward target with some spread
            speed = random.uniform(400, 600)
            vx = self.dx * speed + random.uniform(-50, 50)
            vy = self.dy * speed + random.uniform(-50, 50)

            # Slash particles (orange-yellow)
            color = random.choice([
                (255, 200, 100),  # Bright slash
                (255, 180, 80),   # Orange slash
                (255, 220, 120),  # Yellow slash
            ])
            size = random.uniform(3, 7)
            lifetime = random.uniform(0.15, 0.25)

            particle = Particle(particle_x, particle_y, vx, vy, color, size, lifetime)
            particle.gravity = 0  # No gravity for slash
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Impact flash and particles at target."""
        # Impact flash particles
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = random.choice([
                (255, 255, 255),  # White flash
                (255, 200, 100),  # Orange
                (255, 230, 150),  # Light yellow
            ])
            size = random.uniform(3, 6)
            lifetime = random.uniform(0.1, 0.2)

            particle = Particle(self.target_x, self.target_y, vx, vy, color, size, lifetime)
            particle.gravity = 100
            self.particle_emitter.particles.append(particle)

        # Target shake and screen shake
        if self.target:
            self.target.shake_intensity = 12
        self.screen_shake(6, 0.15)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "windup":
            if self.timer >= self.windup_duration:
                self.phase = "slash"
                self.timer = 0
                self._trigger_slash()

        elif self.phase == "slash":
            if self.timer >= self.slash_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """No additional drawing needed - particles handle visuals."""
        pass


class RetchAnimation:
    """
    Animation for when a unit reaches critical health and retches.
    Shows a sickly yellow-green particle burst and unit recoil.
    """

    # Sickly yellow-green colors for retching
    RETCH_COLORS = [
        (154, 205, 50),   # Yellow-green (#9ACD32)
        (173, 255, 47),   # Green-yellow (#ADFF2F)
        (127, 255, 0),    # Chartreuse (#7FFF00)
        (218, 165, 32),   # Goldenrod (sickly yellow)
        (184, 134, 11)    # Dark goldenrod
    ]

    def __init__(self, center_x, center_y, camera=None):
        """
        Initialize retch animation.

        Args:
            center_x: Screen X position of unit center
            center_y: Screen Y position of unit center
            camera: Camera object for shake effects
        """
        self.center_x = center_x
        self.center_y = center_y
        self.camera = camera
        self.timer = 0
        self.duration = 0.8  # Total animation duration
        self.active = True

        # Animation phases
        self.phase = "recoil"  # recoil -> burst -> recovery
        self.recoil_duration = 0.15
        self.burst_duration = 0.4
        self.recovery_duration = 0.25

        # Recoil parameters
        self.recoil_offset_y = 0
        self.max_recoil = -4  # Pixels to shift up

        # Particle list for burst effect
        self.particles = []

    def update(self, delta_time) -> bool:
        """
        Update animation state.

        Args:
            delta_time: Time elapsed since last frame

        Returns:
            True if animation is still active, False if finished
        """
        if not self.active:
            return False

        self.timer += delta_time

        # Phase: Recoil
        if self.phase == "recoil":
            # Ease into recoil
            progress = min(1.0, self.timer / self.recoil_duration)
            # Quadratic ease-in
            self.recoil_offset_y = self.max_recoil * (progress * progress)

            if self.timer >= self.recoil_duration:
                self.phase = "burst"
                self.timer = 0
                self._create_particle_burst()

        # Phase: Burst
        elif self.phase == "burst":
            # Hold recoil briefly, then ease back
            burst_progress = self.timer / self.burst_duration

            if burst_progress < 0.3:
                # Hold recoil for first 30% of burst
                self.recoil_offset_y = self.max_recoil
            else:
                # Ease back to normal
                ease_progress = (burst_progress - 0.3) / 0.7
                self.recoil_offset_y = self.max_recoil * (1 - ease_progress)

            # Update particles
            self.particles = [p for p in self.particles if p.update(delta_time)]

            if self.timer >= self.burst_duration:
                self.phase = "recovery"
                self.timer = 0

        # Phase: Recovery
        elif self.phase == "recovery":
            # Unit fully back to normal, just wait for particles to fade
            self.recoil_offset_y = 0

            # Update remaining particles
            self.particles = [p for p in self.particles if p.update(delta_time)]

            if self.timer >= self.recovery_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def _create_particle_burst(self):
        """Create cone-shaped projectile vomit effect."""
        particle_count = 25  # More particles for denser vomit stream

        # Vomit shoots downward in a cone
        cone_center_angle = math.pi / 2  # 90 degrees (straight down)
        cone_spread = math.pi / 4  # 45 degree cone spread (total)

        for i in range(particle_count):
            # Create cone shape - particles spread within cone angle
            spread_ratio = (i / particle_count) - 0.5  # -0.5 to 0.5
            angle = cone_center_angle + (spread_ratio * cone_spread) + random.uniform(-0.15, 0.15)

            # Vary speed to create stream effect (faster = further)
            # Inner cone particles go further, outer particles spread more
            distance_from_center = abs(spread_ratio)
            speed = random.uniform(100, 180) * (1.2 - distance_from_center * 0.5)

            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Random sickly color with more variety
            color = random.choice(self.RETCH_COLORS)

            # Larger chunks for projectile vomit
            size = random.uniform(3.5, 7.0)

            # Longer lifetime for projectile effect
            lifetime = random.uniform(0.5, 0.9)

            particle = Particle(
                self.center_x,
                self.center_y,
                vx, vy,
                color,
                size,
                lifetime
            )
            particle.gravity = 150  # Stronger gravity for arc trajectory
            self.particles.append(particle)

    def get_recoil_offset(self) -> Tuple[float, float]:
        """
        Get current recoil offset for unit rendering.

        Returns:
            (offset_x, offset_y) tuple
        """
        return (0, self.recoil_offset_y)

    def draw(self, surface):
        """
        Draw retch particles.

        Args:
            surface: Pygame surface to draw on
        """
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)


