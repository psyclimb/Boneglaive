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
TILE_SIZE = 64

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

    def update(self, delta_time):
        self.particles = [p for p in self.particles if p.update(delta_time)]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


class AnimatedUnit:
    """Unit with smooth animation support."""
    def __init__(self, name, player, grid_x, grid_y, color, sprite_path=None):
        self.name = name
        self.player = player
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.color = color

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

        # Draw sprite or fallback to circle
        if self.sprite:
            # Position sprite centered at final position
            self.sprite_rect.center = (final_x, final_y)
            surface.blit(self.sprite, self.sprite_rect)
        else:
            # Draw unit circle (fallback)
            pygame.draw.circle(surface, self.color, (final_x, final_y), self.radius)
            pygame.draw.circle(surface, (255, 255, 255), (final_x, final_y), self.radius, 2)

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

        alpha = int(255 * min(1.0, self.lifetime))

        # Create debris sprite (jagged rock)
        debris_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        points = []
        num_points = 5
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            distance = self.size * random.uniform(0.7, 1.0)
            px = self.size + math.cos(angle) * distance
            py = self.size + math.sin(angle) * distance
            points.append((px, py))

        pygame.draw.polygon(debris_surf, (*self.color, alpha), points)
        pygame.draw.polygon(debris_surf, (100, 80, 60, alpha), points, 2)

        # Rotate
        rotated = pygame.transform.rotate(debris_surf, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


