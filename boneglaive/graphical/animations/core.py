#!/usr/bin/env python3
"""
Modern Graphical Renderer Demo for Boneglaive (Pygame version)
Demonstrates what the game MIGHT look like with modern rendering.

No external dependencies needed (uses pygame from requirements.txt)
Run: python3 demo_modern_renderer_pygame.py
"""
import pygame
import random
import math
from pathlib import Path
from typing import List, Tuple, Optional
import sys
import os


# Constants (shared across all modules)
TILE_SIZE = 46  # Scaled down to fit dedicated UI panels (920px / 20 tiles)

# Attack animation colors
COLOR_MELEE_SLASH = (255, 200, 100)  # Orange-yellow for melee slash
COLOR_IMPACT = (255, 255, 255)  # White for impact flash

# Colors (shared)
COLOR_PLAYER1 = (100, 150, 255)
COLOR_PLAYER2 = (255, 150, 150)
COLOR_DAMAGE = (255, 50, 50)
COLOR_HEAL = (50, 255, 100)
COLOR_SKILL = (200, 100, 255)

class Particle:
    """Simple particle for effects."""
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

        # Create a surface with per-pixel alpha
        particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color, (int(self.size), int(self.size)), int(self.size))
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
        'CUTTING': [(220, 20, 60), (255, 99, 71), (255, 127, 80)]        # Red bottle colors
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

            # Draw particle with glow
            particle_surf = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)

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

        # Draw each eye
        for eye_x in [left_eye_x, right_eye_x]:
            # Outer glow
            glow_size = 8
            glow_alpha = int(80 * pulse)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
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

        # Potpourri aura (for POTPOURRIST)
        self.potpourri_aura_active = False
        self.potpourri_aura_timer = 0
        self.potpourri_aura_particles = []

        # Vapor particle cloud (for HEINOUS VAPOR)
        self.vapor_cloud = None
        self._detect_vapor_type()

        # Stats
        self.max_hp = 20
        self.hp = 20

        # Render
        self.radius = 24
        self.sprite = None
        self.sprite_rect = None

        # Load sprite if path provided
        if sprite_path and os.path.exists(sprite_path):
            try:
                # Try to load SVG using cairosvg if available
                if sprite_path.endswith('.svg'):
                    try:
                        import cairosvg
                        from io import BytesIO
                        # Convert SVG to PNG in memory
                        png_data = cairosvg.svg2png(url=sprite_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
                        self.sprite = pygame.image.load(BytesIO(png_data))
                    except ImportError:
                        print(f"Info: cairosvg not available, rendering SVG with basic rasterization for {sprite_path}")
                        # Fallback: create a colored square placeholder
                        self.sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        # Draw a simple representation
                        pygame.draw.circle(self.sprite, self.color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3)
                        pygame.draw.circle(self.sprite, (255, 255, 255), (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3, 2)
                else:
                    self.sprite = pygame.image.load(sprite_path)
                    # Scale to fit tile size
                    self.sprite = pygame.transform.smoothscale(self.sprite, (TILE_SIZE, TILE_SIZE))

                self.sprite_rect = self.sprite.get_rect()
            except Exception as e:
                print(f"Warning: Could not load sprite {sprite_path}: {e}")
                self.sprite = None

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
                print(f"[VaporCloud] Detected HEINOUS VAPOR of type: {vapor_type}")
                self.vapor_cloud = VaporParticleCloud(vapor_type)
        except Exception as e:
            print(f"[VaporCloud] Error detecting vapor type: {e}")

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

    def draw(self, surface, font):
        # Calculate final position
        final_x = int(self.x + self.shake_x)
        final_y = int(self.y + self.shake_y - self.hop_offset)

        # Draw potpourri aura particles (behind unit)
        if self.potpourri_aura_active:
            for particle in self.potpourri_aura_particles:
                if particle['lifetime'] > 0:
                    alpha = int(200 * (particle['lifetime'] / particle['max_lifetime']))
                    if alpha > 0:
                        color = (*particle['color'], alpha)
                        particle_surf = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
                        pygame.draw.circle(particle_surf, color,
                                         (int(particle['size']), int(particle['size'])),
                                         int(particle['size']))
                        # Add glow
                        glow_size = particle['size'] + 2
                        pygame.draw.circle(particle_surf, (*particle['color'], alpha // 3),
                                         (int(particle['size']), int(particle['size'])),
                                         int(glow_size))
                        surface.blit(particle_surf, (int(particle['x'] - particle['size']), int(particle['y'] - particle['size'])))

        # Draw vapor cloud (for HEINOUS VAPOR) - takes priority over sprite/circle
        if self.vapor_cloud:
            self.vapor_cloud.draw(surface, final_x, final_y)
        # Draw sprite or fallback to circle (for non-vapor units)
        elif self.sprite:
            # Check if this is a GRAYMAN ECHO (ethereal rendering)
            is_echo = (hasattr(self.game_unit, 'is_echo') and
                       self.game_unit.is_echo)

            # Determine which sprite to use and its position
            if hasattr(self, 'wind_up_rotation') and self.wind_up_rotation != 0:
                sprite_to_use = pygame.transform.rotate(self.sprite, -self.wind_up_rotation)
                sprite_rect = sprite_to_use.get_rect(center=(final_x, final_y))
            else:
                sprite_to_use = self.sprite
                sprite_rect = self.sprite_rect.copy()
                sprite_rect.center = (final_x, final_y)

            # Apply echo effect if needed
            if is_echo:
                # Create ethereal purple semi-transparent version
                echo_sprite = sprite_to_use.copy()

                # Create purple tint overlay
                purple_overlay = pygame.Surface(echo_sprite.get_size(), pygame.SRCALPHA)
                purple_color = (170, 119, 255)  # Estrange purple

                # Fill with semi-transparent purple
                purple_overlay.fill((*purple_color, 180))  # ~70% opacity

                # Apply tint using blend mode
                echo_sprite.blit(purple_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                # Reduce overall alpha for ethereal effect
                echo_sprite.set_alpha(160)  # ~63% opacity

                # Draw the ethereal echo sprite
                surface.blit(echo_sprite, sprite_rect)
            else:
                # Draw normal sprite
                surface.blit(sprite_to_use, sprite_rect)
        else:
            # Draw unit circle (fallback)
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


class FloatingText:
    """Floating damage/heal numbers."""
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 1.5
        self.vy = -60
        self.timer = 0  # For delayed text

    def update(self, delta_time):
        # Handle delayed text (negative timer means waiting)
        if self.timer < 0:
            self.timer += delta_time
            return True  # Keep alive but don't move yet

        self.y += self.vy * delta_time
        self.vy += 100 * delta_time
        self.lifetime -= delta_time
        return self.lifetime > 0

    def draw(self, surface, font):
        # Don't draw if still waiting
        if self.timer < 0:
            return
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / 1.5))
        color = (*self.color[:3], alpha)

        # Create text with alpha
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
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

        if os.path.exists(icon_path):
            try:
                # Try to load SVG using cairosvg if available
                try:
                    import cairosvg
                    from io import BytesIO
                    # Convert SVG to PNG in memory
                    png_data = cairosvg.svg2png(url=icon_path, output_width=self.icon_size, output_height=self.icon_size)
                    self.icon_surface = pygame.image.load(BytesIO(png_data))
                except ImportError:
                    print(f"[StatusIcon] cairosvg not available, using fallback for {effect_name}")
                    # Fallback: create colored circle as placeholder
                    self.icon_surface = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
                    pygame.draw.circle(self.icon_surface, (255, 100, 100), (self.icon_size//2, self.icon_size//2), self.icon_size//3)
                    pygame.draw.circle(self.icon_surface, (255, 255, 255), (self.icon_size//2, self.icon_size//2), self.icon_size//3, 2)
            except Exception as e:
                print(f"[StatusIcon] Error loading icon {icon_path}: {e}")
                # Create fallback surface
                self.icon_surface = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
                pygame.draw.circle(self.icon_surface, (255, 100, 100), (self.icon_size//2, self.icon_size//2), self.icon_size//3)
        else:
            print(f"[StatusIcon] Icon not found: {icon_path}")
            # Create fallback surface
            self.icon_surface = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            pygame.draw.circle(self.icon_surface, (255, 100, 100), (self.icon_size//2, self.icon_size//2), self.icon_size//3)

        print(f"  [STATUS_ICON] Flashing {effect_name} icon on {unit.name}")

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

        # Create a copy with the current alpha
        icon_copy = self.icon_surface.copy()
        icon_copy.set_alpha(alpha)

        # Draw centered on unit's position
        icon_rect = icon_copy.get_rect(center=(int(self.unit.x), int(self.unit.y - 10)))  # Slightly above unit center
        surface.blit(icon_copy, icon_rect)


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

        print(f"  [BASIC_ATTACK] Starting melee attack animation: {attacker_unit.name} → target")

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


