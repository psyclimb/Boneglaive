#!/usr/bin/env python3
"""
Modern Graphical Renderer Demo for Boneglaive
Demonstrates SVG rendering, particle effects, z-layers, and smooth animations.

Requirements: pip install arcade pillow cairosvg
Run: python3 demo_modern_renderer.py
"""
import arcade
import random
import math
from pathlib import Path
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Boneglaive Modern Renderer Demo"

TILE_SIZE = 64
GRID_WIDTH = 12
GRID_HEIGHT = 8

# Z-Layers
LAYER_TERRAIN = 0
LAYER_FURNITURE = 1
LAYER_GROUND_EFFECTS = 2
LAYER_UNITS = 3
LAYER_PARTICLES = 4
LAYER_UI = 5

# Colors
COLOR_PLAYER1 = arcade.color.LIGHT_BLUE
COLOR_PLAYER2 = arcade.color.LIGHT_CORAL
COLOR_DAMAGE = arcade.color.RED
COLOR_HEAL = arcade.color.GREEN
COLOR_SKILL = arcade.color.PURPLE


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
        self.x += self.vx * delta_time * 60
        self.y += self.vy * delta_time * 60
        self.vy += self.gravity * delta_time * 60
        self.lifetime -= delta_time

    def draw(self):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime)) if self.fade else 255
        color = (*self.color[:3], alpha)
        arcade.draw_circle_filled(self.x, self.y, self.size, color)


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
            particle.gravity = -200
            self.particles.append(particle)

    def emit_trail(self, x, y, color, count=5):
        """Emit trailing particles (movement trails)."""
        for _ in range(count):
            vx = random.uniform(-20, 20)
            vy = random.uniform(-20, 20)
            size = random.uniform(1, 3)
            lifetime = random.uniform(0.2, 0.5)
            particle = Particle(x, y, vx, vy, color, size, lifetime)
            self.particles.append(particle)

    def emit_float(self, x, y, color, count=10):
        """Emit floating particles (healing, buffs)."""
        for _ in range(count):
            vx = random.uniform(-10, 10)
            vy = random.uniform(20, 60)
            size = random.uniform(2, 4)
            lifetime = random.uniform(0.5, 1.5)
            particle = Particle(x, y, vx, vy, color, size, lifetime)
            self.particles.append(particle)

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
            particle = Particle(x, y, vx, vy, color, size, lifetime)
            self.particles.append(particle)

    def update(self, delta_time):
        # Update all particles
        for particle in self.particles[:]:
            particle.update(delta_time)
            if particle.lifetime <= 0:
                self.particles.remove(particle)

    def draw(self):
        for particle in self.particles:
            particle.draw()


class AnimatedSprite(arcade.Sprite):
    """Sprite with smooth animation support."""
    def __init__(self, texture, scale=1.0):
        super().__init__()
        self.texture = texture
        self.scale = scale

        # Grid position
        self.grid_x = 0
        self.grid_y = 0

        # Animation state
        self.target_x = 0
        self.target_y = 0
        self.is_moving = False
        self.move_speed = 400  # pixels per second

        # Visual effects
        self.shake_offset_x = 0
        self.shake_offset_y = 0
        self.shake_intensity = 0
        self.hop_offset = 0
        self.hop_speed = 0

        # Stats for demo
        self.max_hp = 20
        self.hp = 20
        self.unit_name = "Unit"
        self.player = 1

    def move_to_grid(self, grid_x, grid_y):
        """Start smooth movement to grid position."""
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.target_x = grid_x * TILE_SIZE + TILE_SIZE // 2
        self.target_y = grid_y * TILE_SIZE + TILE_SIZE // 2
        self.is_moving = True
        self.hop_speed = 8  # Start hop animation

    def take_damage(self, amount):
        """Apply damage and trigger shake effect."""
        self.hp = max(0, self.hp - amount)
        self.shake_intensity = 10

    def heal(self, amount):
        """Apply healing."""
        self.hp = min(self.max_hp, self.hp + amount)

    def update_animation(self, delta_time):
        # Smooth movement
        if self.is_moving:
            dx = self.target_x - self.center_x
            dy = self.target_y - self.center_y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance < 2:
                self.center_x = self.target_x
                self.center_y = self.target_y
                self.is_moving = False
            else:
                move_amount = self.move_speed * delta_time
                if move_amount > distance:
                    move_amount = distance
                self.center_x += (dx / distance) * move_amount
                self.center_y += (dy / distance) * move_amount

        # Hop animation (sine wave)
        if self.hop_speed > 0:
            self.hop_offset = abs(math.sin(self.hop_speed)) * 15
            self.hop_speed -= delta_time * 10
            if self.hop_speed < 0:
                self.hop_speed = 0
                self.hop_offset = 0

        # Shake effect
        if self.shake_intensity > 0:
            self.shake_offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity -= delta_time * 50
            if self.shake_intensity < 0:
                self.shake_intensity = 0
                self.shake_offset_x = 0
                self.shake_offset_y = 0

    def draw(self):
        # Apply visual offsets
        final_x = self.center_x + self.shake_offset_x
        final_y = self.center_y + self.shake_offset_y + self.hop_offset

        # Draw sprite
        self.center_x = final_x
        self.center_y = final_y
        super().draw()

        # Draw HP bar above unit
        bar_width = 50
        bar_height = 6
        bar_x = final_x - bar_width // 2
        bar_y = final_y + 40

        # Background (black)
        arcade.draw_rectangle_filled(bar_x + bar_width // 2, bar_y, bar_width, bar_height, arcade.color.BLACK)

        # HP fill (colored by player)
        hp_ratio = self.hp / self.max_hp
        fill_width = bar_width * hp_ratio
        color = COLOR_PLAYER1 if self.player == 1 else COLOR_PLAYER2
        if hp_ratio < 0.3:
            color = arcade.color.RED
        arcade.draw_rectangle_filled(bar_x + fill_width // 2, bar_y, fill_width, bar_height - 2, color)

        # Unit name
        arcade.draw_text(self.unit_name, final_x, final_y + 50, arcade.color.WHITE, 10,
                        anchor_x="center", bold=True)


class FloatingText:
    """Floating damage/heal numbers."""
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 1.5
        self.vy = 60

    def update(self, delta_time):
        self.y += self.vy * delta_time
        self.vy -= 100 * delta_time  # Gravity
        self.lifetime -= delta_time

    def draw(self):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / 1.5))
        color = (*self.color[:3], alpha)
        arcade.draw_text(self.text, self.x, self.y, color, 20,
                        anchor_x="center", bold=True)


class ModernRendererDemo(arcade.Window):
    """Demo window showing modern rendering capabilities."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Camera for smooth panning
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.ui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Sprite lists with z-ordering
        self.terrain_list = arcade.SpriteList()
        self.furniture_list = arcade.SpriteList()
        self.unit_list = arcade.SpriteList()

        # Effects
        self.particle_emitter = ParticleEmitter()
        self.floating_texts: List[FloatingText] = []

        # Demo units
        self.units: List[AnimatedSprite] = []

        # Animation state
        self.demo_state = "idle"
        self.demo_timer = 0

        self.setup()

    def setup(self):
        """Set up the demo scene."""
        # Create grid background
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                # Checkerboard pattern
                color = arcade.color.DARK_GRAY if (x + y) % 2 == 0 else arcade.color.DIM_GRAY
                sprite = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, color)
                sprite.center_x = x * TILE_SIZE + TILE_SIZE // 2
                sprite.center_y = y * TILE_SIZE + TILE_SIZE // 2
                self.terrain_list.append(sprite)

        # Add some furniture obstacles
        for _ in range(5):
            sprite = arcade.SpriteSolidColor(TILE_SIZE - 4, TILE_SIZE - 4, arcade.color.BROWN)
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            sprite.center_x = x * TILE_SIZE + TILE_SIZE // 2
            sprite.center_y = y * TILE_SIZE + TILE_SIZE // 2
            self.furniture_list.append(sprite)

        # Create demo units (would load SVGs in real implementation)
        # Player 1 units
        for i in range(3):
            sprite = AnimatedSprite(None, scale=1.0)
            # Create a simple circle sprite
            sprite.texture = arcade.make_soft_circle_texture(60, COLOR_PLAYER1, 255, 255)
            sprite.unit_name = f"GLAIVEMAN α"
            sprite.player = 1
            sprite.grid_x = i * 2
            sprite.grid_y = 1
            sprite.center_x = sprite.grid_x * TILE_SIZE + TILE_SIZE // 2
            sprite.center_y = sprite.grid_y * TILE_SIZE + TILE_SIZE // 2
            self.units.append(sprite)
            self.unit_list.append(sprite)

        # Player 2 units
        for i in range(3):
            sprite = AnimatedSprite(None, scale=1.0)
            sprite.texture = arcade.make_soft_circle_texture(60, COLOR_PLAYER2, 255, 255)
            sprite.unit_name = f"GRAYMAN β"
            sprite.player = 2
            sprite.grid_x = i * 2 + 1
            sprite.grid_y = 6
            sprite.center_x = sprite.grid_x * TILE_SIZE + TILE_SIZE // 2
            sprite.center_y = sprite.grid_y * TILE_SIZE + TILE_SIZE // 2
            self.units.append(sprite)
            self.unit_list.append(sprite)

        # Start first demo sequence
        self.schedule_next_demo()

    def schedule_next_demo(self):
        """Schedule the next demo action."""
        demos = ["move", "attack", "skill", "heal"]
        self.demo_state = random.choice(demos)
        self.demo_timer = random.uniform(1.5, 3.0)

    def execute_demo_action(self):
        """Execute a demo action to show off rendering."""
        if not self.units:
            return

        if self.demo_state == "move":
            # Random unit moves
            unit = random.choice(self.units)
            new_x = random.randint(0, GRID_WIDTH - 1)
            new_y = random.randint(0, GRID_HEIGHT - 1)
            unit.move_to_grid(new_x, new_y)

            # Emit trail particles
            for _ in range(10):
                self.particle_emitter.emit_trail(
                    unit.center_x, unit.center_y,
                    COLOR_PLAYER1 if unit.player == 1 else COLOR_PLAYER2
                )

        elif self.demo_state == "attack":
            # Random attack between units
            if len(self.units) >= 2:
                attacker = random.choice(self.units)
                target = random.choice([u for u in self.units if u.player != attacker.player])

                # Beam particles
                self.particle_emitter.emit_beam(
                    attacker.center_x, attacker.center_y,
                    target.center_x, target.center_y,
                    arcade.color.ORANGE
                )

                # Impact burst
                self.particle_emitter.emit_burst(
                    target.center_x, target.center_y,
                    COLOR_DAMAGE, 15
                )

                # Damage
                damage = random.randint(2, 6)
                target.take_damage(damage)
                self.floating_texts.append(
                    FloatingText(target.center_x, target.center_y + 20, f"-{damage}", COLOR_DAMAGE)
                )

        elif self.demo_state == "skill":
            # Random skill effect
            unit = random.choice(self.units)

            # Large burst of purple particles
            self.particle_emitter.emit_burst(
                unit.center_x, unit.center_y,
                COLOR_SKILL, 30
            )

            # Add "SKILL" floating text
            self.floating_texts.append(
                FloatingText(unit.center_x, unit.center_y + 30, "SKILL!", COLOR_SKILL)
            )

        elif self.demo_state == "heal":
            # Random heal
            unit = random.choice(self.units)
            if unit.hp < unit.max_hp:
                heal = random.randint(2, 5)
                unit.heal(heal)

                # Float particles upward
                self.particle_emitter.emit_float(
                    unit.center_x, unit.center_y,
                    COLOR_HEAL, 15
                )

                self.floating_texts.append(
                    FloatingText(unit.center_x, unit.center_y + 20, f"+{heal}", COLOR_HEAL)
                )

    def on_update(self, delta_time):
        """Update animations and effects."""
        # Update demo timer
        self.demo_timer -= delta_time
        if self.demo_timer <= 0:
            self.execute_demo_action()
            self.schedule_next_demo()

        # Update units
        for unit in self.units:
            unit.update_animation(delta_time)

            # Emit idle particles occasionally
            if random.random() < 0.05:
                color = COLOR_PLAYER1 if unit.player == 1 else COLOR_PLAYER2
                self.particle_emitter.emit_trail(unit.center_x, unit.center_y, color, 1)

        # Update particles
        self.particle_emitter.update(delta_time)

        # Update floating texts
        for text in self.floating_texts[:]:
            text.update(delta_time)
            if text.lifetime <= 0:
                self.floating_texts.remove(text)

    def on_draw(self):
        """Render the scene."""
        self.clear()

        # Activate game camera
        self.camera.use()

        # Draw layers in z-order
        self.terrain_list.draw()
        self.furniture_list.draw()

        # Draw units with custom rendering
        for unit in self.units:
            unit.draw()

        # Draw particles on top
        self.particle_emitter.draw()

        # Draw floating texts
        for text in self.floating_texts:
            text.draw()

        # Activate UI camera (fixed position)
        self.ui_camera.use()

        # Draw UI
        self.draw_ui()

    def draw_ui(self):
        """Draw modern UI elements."""
        # Semi-transparent panel at bottom
        panel_height = 120
        arcade.draw_lrtb_rectangle_filled(
            0, SCREEN_WIDTH, panel_height, 0,
            (*arcade.color.BLACK, 180)
        )

        # Title
        arcade.draw_text(
            "Boneglaive - Modern Renderer Demo",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 24, anchor_x="center", bold=True
        )

        # Instructions
        instructions = [
            "Demonstrating:",
            "• SVG sprite rendering (simulated with circles)",
            "• Particle effects for skills/attacks",
            "• Smooth movement with hop animation",
            "• HP bars and floating damage numbers",
            "• Z-layer rendering (terrain → units → particles)",
            "",
            "Watch the automated demo or press SPACE to trigger random action"
        ]

        y = panel_height - 20
        for line in instructions:
            arcade.draw_text(line, 20, y, arcade.color.WHITE, 11)
            y -= 15

        # Stats
        arcade.draw_text(
            f"Particles: {len(self.particle_emitter.particles)}",
            SCREEN_WIDTH - 150, panel_height - 30,
            arcade.color.YELLOW, 12
        )
        arcade.draw_text(
            f"Units: {len(self.units)}",
            SCREEN_WIDTH - 150, panel_height - 50,
            arcade.color.YELLOW, 12
        )

    def on_key_press(self, key, modifiers):
        """Handle key presses."""
        if key == arcade.key.SPACE:
            self.execute_demo_action()
            self.schedule_next_demo()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()


def main():
    """Run the demo."""
    print("=" * 60)
    print("BONEGLAIVE MODERN RENDERER DEMO")
    print("=" * 60)
    print()
    print("This demo shows what the game MIGHT look like with:")
    print("  - SVG sprite rendering")
    print("  - Particle effects for skills/attacks")
    print("  - Smooth animations and movement")
    print("  - Z-layer rendering")
    print("  - Modern UI with transparency")
    print()
    print("Note: In production, the colored circles would be")
    print("      replaced with your actual SVG graphics.")
    print()
    print("Press SPACE to trigger random actions")
    print("Press ESC to exit")
    print()

    window = ModernRendererDemo()
    arcade.run()


if __name__ == "__main__":
    main()
