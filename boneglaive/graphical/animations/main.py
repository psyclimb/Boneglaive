#!/usr/bin/env python3
"""
Modern Graphical Renderer Demo for Boneglaive (Modular version)
Demonstrates what the game MIGHT look like with modern rendering.

Run: python3 -m demo_animations.main
     OR: python3 demo_animations/main.py
"""
import pygame
import random
import math
from pathlib import Path
from typing import List, Tuple, Optional
import sys
import os

# Import all animation classes from modules
from .core import (
    Particle, ParticleEmitter, AnimatedUnit, FloatingText, DebrisParticle,
    TILE_SIZE, COLOR_PLAYER1, COLOR_PLAYER2, COLOR_DAMAGE, COLOR_HEAL, COLOR_SKILL,
)
from .glaiveman import SpinningGlaiveProjectile, LightningBolt, CrossBeam
from .mandible_foreman import (
    JawClamp, ViseroyTrap, ViseroyRelease, SiteInspectionBuff, 
    SiteInspectionScan, ExpediteRush, JawlineNetwork
)
from .potpourrist import PedestalStrike, InfuseEffect, DemiluneSwing, LunacyEffect, GraniteGeasEffect, GeasBreakHeal, MelangeEminence

# Screen constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Boneglaive Modern Renderer Demo"

# Grid constants
GRID_WIDTH = 12
GRID_HEIGHT = 8

# Colors
COLOR_BG = (40, 44, 52)
COLOR_GRID_DARK = (50, 54, 62)
COLOR_GRID_LIGHT = (60, 64, 72)

class ModernRendererDemo:
    """Demo showing modern rendering capabilities."""

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 36)

        # Effects
        self.particle_emitter = ParticleEmitter()
        self.floating_texts: List[FloatingText] = []
        self.projectiles: List[SpinningGlaiveProjectile] = []
        self.lightning_bolts: List[LightningBolt] = []
        self.debris_particles: List[DebrisParticle] = []
        self.cross_beams: List[CrossBeam] = []
        self.jaw_clamps: List[JawClamp] = []
        self.jawline_networks: List[JawlineNetwork] = []
        self.expedite_rushes: List[ExpediteRush] = []
        self.viseroy_traps: List[ViseroyTrap] = []
        self.viseroy_releases: List[ViseroyRelease] = []
        self.site_inspections: List[SiteInspectionScan] = []
        self.site_inspection_buffs: List[SiteInspectionBuff] = []
        self.pedestal_strikes: List[PedestalStrike] = []
        self.infuse_effects: List[InfuseEffect] = []
        self.demilune_swings: List[DemiluneSwing] = []
        self.lunacy_effects: List[LunacyEffect] = []
        self.granite_geas_effects: List[GraniteGeasEffect] = []
        self.geas_break_heals: List[GeasBreakHeal] = []
        self.melange_eminence_effects: List[MelangeEminence] = []

        # Units
        self.units: List[AnimatedUnit] = []

        # Demo state
        self.demo_timer = 0
        self.demo_state = "idle"
        self.demo_skill_index = 0  # Alternate between skills

        # Active unit mode (which unit's animations to demo)
        self.active_unit_mode = "POTPOURRIST"  # Can be "GLAIVEMAN", "MANDIBLE_FOREMAN", or "POTPOURRIST"

        # Screen shake
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0

        self.setup()
        self.running = True

    def load_svg(self, sprite_path, size):
        """Load an SVG file and return a pygame surface."""
        if not os.path.exists(sprite_path):
            return None

        try:
            # Try to load SVG using cairosvg if available
            if sprite_path.endswith('.svg'):
                try:
                    import cairosvg
                    from io import BytesIO
                    # Convert SVG to PNG in memory
                    png_data = cairosvg.svg2png(url=sprite_path, output_width=size, output_height=size)
                    return pygame.image.load(BytesIO(png_data))
                except ImportError:
                    print(f"Info: cairosvg not available for {sprite_path}")
                    # Return None, will be filtered out
                    return None
            else:
                sprite = pygame.image.load(sprite_path)
                return pygame.transform.smoothscale(sprite, (size, size))
        except Exception as e:
            print(f"Warning: Could not load {sprite_path}: {e}")
            return None

    def setup(self):
        """Set up the demo scene."""
        # Get path to graphics directory
        base_path = Path(__file__).parent.parent / "graphics" / "units"

        # Player 1 units - load based on active mode
        if self.active_unit_mode == "GLAIVEMAN":
            unit_sprites = [
                ("GLAIVEMAN α", base_path / "glaiveman.svg"),
                ("MANDIBLE FOREMAN β", base_path / "mandible_foreman.svg"),
                ("POTPOURRIST γ", base_path / "potpourrist.svg")
            ]
            for i, (name, sprite_path) in enumerate(unit_sprites):
                # Place GLAIVEMAN in center, 4 tiles in front of targets
                if "GLAIVEMAN" in name:
                    unit = AnimatedUnit(name, 1, 6, 2, COLOR_PLAYER1, str(sprite_path))
                else:
                    unit = AnimatedUnit(name, 1, i * 2, 1, COLOR_PLAYER1, str(sprite_path))
                self.units.append(unit)

        elif self.active_unit_mode == "MANDIBLE_FOREMAN":
            unit_sprites = [
                ("MANDIBLE FOREMAN α", base_path / "mandible_foreman.svg"),
                ("GLAIVEMAN β", base_path / "glaiveman.svg"),
                ("POTPOURRIST γ", base_path / "potpourrist.svg")
            ]
            for i, (name, sprite_path) in enumerate(unit_sprites):
                # Place MANDIBLE FOREMAN in center, 4 tiles in front of targets
                if "MANDIBLE FOREMAN" in name:
                    unit = AnimatedUnit(name, 1, 6, 2, COLOR_PLAYER1, str(sprite_path))
                else:
                    unit = AnimatedUnit(name, 1, i * 2, 1, COLOR_PLAYER1, str(sprite_path))
                self.units.append(unit)

        elif self.active_unit_mode == "POTPOURRIST":
            unit_sprites = [
                ("POTPOURRIST α", base_path / "potpourrist.svg"),
                ("GLAIVEMAN β", base_path / "glaiveman.svg"),
                ("MANDIBLE FOREMAN γ", base_path / "mandible_foreman.svg")
            ]
            for i, (name, sprite_path) in enumerate(unit_sprites):
                # Place POTPOURRIST directly in front of center enemy target (grid position 6, 5)
                if "POTPOURRIST" in name:
                    unit = AnimatedUnit(name, 1, 6, 5, COLOR_PLAYER1, str(sprite_path))
                else:
                    unit = AnimatedUnit(name, 1, i * 2, 1, COLOR_PLAYER1, str(sprite_path))
                self.units.append(unit)

        # Player 2 units - create fallback target dummies with high HP
        target_names = ["TARGET α", "TARGET β", "TARGET γ"]

        # Place them at grid positions 5, 6, 7 on row 6 (next to each other)
        # Center target at grid 6, 6 - POTPOURRIST will be at 6, 5 (directly in front)
        for i, name in enumerate(target_names):
            # Create unit without sprite (will use fallback circle)
            unit = AnimatedUnit(name, 2, 5 + i, 6, COLOR_PLAYER2, sprite_path=None)
            unit.max_hp = 9999
            unit.hp = 9999
            self.units.append(unit)

        self.schedule_next_demo()

    def schedule_next_demo(self):
        """Schedule the next demo action."""
        # Cycle through skills based on active unit mode
        if self.active_unit_mode == "GLAIVEMAN":
            skills = ["glaive_melee", "glaive_judgement", "glaive_judgement_crit", "glaive_pry", "glaive_autoclave", "glaive_vault"]
        elif self.active_unit_mode == "MANDIBLE_FOREMAN":
            skills = ["mandible_site_inspection", "mandible_expedite", "mandible_viseroy", "mandible_release", "mandible_melee", "mandible_viseroy", "mandible_release", "mandible_jawline"]
        elif self.active_unit_mode == "POTPOURRIST":
            skills = ["potpourrist_melee", "potpourrist_melange_eminence", "potpourrist_demilune", "potpourrist_lunacy", "potpourrist_infuse", "potpourrist_melange_eminence_infused", "potpourrist_demilune_infused", "potpourrist_lunacy", "potpourrist_granite_geas", "potpourrist_geas_break_heal", "potpourrist_infuse", "potpourrist_granite_geas_infused", "potpourrist_geas_break_heal", "potpourrist_geas_break_heal"]
        else:
            skills = ["idle"]

        # Get current skill index
        current_skill_index = self.demo_skill_index % len(skills)

        self.demo_state = skills[current_skill_index]
        self.demo_skill_index += 1
        self.demo_timer = random.uniform(2.5, 4.0)

    def execute_demo_action(self):
        """Execute a demo action to show off rendering."""
        if not self.units:
            return

        # Find GLAIVEMAN for skill demos
        glaiveman = None
        for unit in self.units:
            if "GLAIVEMAN" in unit.name:
                glaiveman = unit
                break

        if self.demo_state == "move":
            unit = random.choice(self.units)
            new_x = random.randint(0, GRID_WIDTH - 1)
            new_y = random.randint(0, GRID_HEIGHT - 1)
            unit.move_to_grid(new_x, new_y)

            # Trail particles
            for _ in range(10):
                self.particle_emitter.emit_trail(unit.x, unit.y, unit.color)

        elif self.demo_state == "attack":
            if len(self.units) >= 2:
                attacker = random.choice(self.units)
                targets = [u for u in self.units if u.player != attacker.player]
                if targets:
                    target = random.choice(targets)

                    # Beam
                    self.particle_emitter.emit_beam(
                        attacker.x, attacker.y,
                        target.x, target.y,
                        (255, 150, 50)
                    )

                    # Impact
                    self.particle_emitter.emit_burst(target.x, target.y, COLOR_DAMAGE, 15)

                    # Damage
                    damage = random.randint(2, 6)
                    target.take_damage(damage)
                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 20, f"-{damage}", COLOR_DAMAGE)
                    )

        elif self.demo_state == "skill":
            unit = random.choice(self.units)
            self.particle_emitter.emit_burst(unit.x, unit.y, COLOR_SKILL, 30)
            self.floating_texts.append(
                FloatingText(unit.x, unit.y - 30, "SKILL!", COLOR_SKILL)
            )

        elif self.demo_state == "heal":
            unit = random.choice(self.units)
            if unit.hp < unit.max_hp:
                heal = random.randint(2, 5)
                unit.heal(heal)
                self.particle_emitter.emit_float(unit.x, unit.y, COLOR_HEAL, 15)
                self.floating_texts.append(
                    FloatingText(unit.x, unit.y - 20, f"+{heal}", COLOR_HEAL)
                )

        elif self.demo_state == "glaive_pry" and glaiveman:
            # PRY: Launch enemy into ceiling, slam down with debris and splash damage
            targets = [u for u in self.units if u.player != glaiveman.player and u.hp > 0]
            if targets:
                target = random.choice(targets)

                # GLAIVEMAN prying lever motion
                glaiveman.pry_lever_phase = "inserting"
                glaiveman.pry_lever_timer = 0
                glaiveman.original_x = glaiveman.x
                glaiveman.original_y = glaiveman.y

                # Mark target for PRY animation
                target.pry_phase = "launching"
                target.pry_timer = 0
                target.pry_max_time = 1.5
                target.original_y = target.y
                target.pry_attacker = glaiveman

                # Store adjacent units for splash damage
                target.pry_adjacent_targets = []
                for unit in self.units:
                    if unit != target and unit.player != glaiveman.player and unit.hp > 0:
                        dx = abs(unit.grid_x - target.grid_x)
                        dy = abs(unit.grid_y - target.grid_y)
                        if dx <= 1 and dy <= 1:  # Adjacent (including diagonals)
                            target.pry_adjacent_targets.append(unit)

                # Launch particles
                for _ in range(30):
                    angle = random.uniform(-math.pi/3, -2*math.pi/3)  # Upward cone
                    speed = random.uniform(150, 300)
                    self.particle_emitter.particles.append(
                        Particle(target.x, target.y,
                                math.cos(angle) * speed, math.sin(angle) * speed,
                                (150, 200, 255), random.uniform(3, 7), 0.6)
                    )

                self.floating_texts.append(
                    FloatingText(glaiveman.x, glaiveman.y - 30, "PRY!", (255, 150, 50))
                )

        elif self.demo_state == "glaive_vault" and glaiveman:
            # VAULT: Leap with a flip animation (range 2 tiles)
            # Find a target location 2 tiles away
            possible_targets = []
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    # Check if exactly 2 tiles away (chess distance)
                    if max(abs(dx), abs(dy)) == 2:
                        new_grid_x = glaiveman.grid_x + dx
                        new_grid_y = glaiveman.grid_y + dy
                        if 0 <= new_grid_x < GRID_WIDTH and 0 <= new_grid_y < GRID_HEIGHT:
                            possible_targets.append((new_grid_x, new_grid_y))

            if possible_targets:
                new_grid_x, new_grid_y = random.choice(possible_targets)
                target_x = new_grid_x * TILE_SIZE + TILE_SIZE // 2
                target_y = new_grid_y * TILE_SIZE + TILE_SIZE // 2

                # Set up vault animation
                glaiveman.vault_phase = "vaulting"
                glaiveman.vault_timer = 0
                glaiveman.vault_duration = 0.6  # Total vault time
                glaiveman.vault_start_x = glaiveman.x
                glaiveman.vault_start_y = glaiveman.y
                glaiveman.vault_target_x = target_x
                glaiveman.vault_target_y = target_y
                glaiveman.vault_target_grid_x = new_grid_x
                glaiveman.vault_target_grid_y = new_grid_y

                # Launch particles
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    particle = Particle(glaiveman.x, glaiveman.y,
                                       math.cos(angle) * speed, math.sin(angle) * speed,
                                       (100, 200, 255), random.uniform(2, 5), 0.4)
                    self.particle_emitter.particles.append(particle)

                self.floating_texts.append(
                    FloatingText(glaiveman.x, glaiveman.y - 30, "VAULT!", COLOR_SKILL)
                )

        elif self.demo_state == "glaive_melee" and glaiveman:
            # MELEE: Basic polearm glaive slash attack
            targets = [u for u in self.units if u.player != glaiveman.player and u.hp > 0]
            if targets:
                # Find closest target
                target = min(targets, key=lambda t:
                           math.sqrt((t.x - glaiveman.x)**2 + (t.y - glaiveman.y)**2))

                # Wind-up: Tilt back and to the side
                glaiveman.melee_phase = "windup"
                glaiveman.melee_timer = 0
                glaiveman.melee_target = target
                glaiveman.original_x = glaiveman.x
                glaiveman.original_y = glaiveman.y

                # Quick forward lunge
                # Calculate direction toward target
                dx = target.x - glaiveman.x
                dy = target.y - glaiveman.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    glaiveman.melee_lunge_x = (dx / dist) * 30  # Lunge 30 pixels forward
                    glaiveman.melee_lunge_y = (dy / dist) * 30
                else:
                    glaiveman.melee_lunge_x = 30
                    glaiveman.melee_lunge_y = 0

                # Wind-up particles (gathering energy)
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(20, 40)
                    px = glaiveman.x + math.cos(angle) * distance
                    py = glaiveman.y + math.sin(angle) * distance
                    particle = Particle(px, py,
                                       -math.cos(angle) * 50, -math.sin(angle) * 50,
                                       (200, 200, 220), 3, 0.4)
                    self.particle_emitter.particles.append(particle)

        elif self.demo_state == "glaive_judgement" and glaiveman:
            # JUDGEMENT: Spinning sacred glaive projectile with ALL advanced techniques
            targets = [u for u in self.units if u.player != glaiveman.player and u.hp > 0]
            if targets:
                target = random.choice(targets)

                # 1. SPRITE TRANSFORMATION - Wind-up rotation for GLAIVEMAN
                glaiveman.wind_up_rotation = 0
                glaiveman.wind_up_phase = 0.3  # Duration in seconds

                # 2. Create and launch SPINNING GLAIVE PROJECTILE
                projectile = SpinningGlaiveProjectile(
                    glaiveman.x, glaiveman.y,
                    target.x, target.y,
                    speed=500
                )
                self.projectiles.append(projectile)

                # 3. SPARKLE PARTICLES around attacker during wind-up
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(20, 40)
                    px = glaiveman.x + math.cos(angle) * distance
                    py = glaiveman.y + math.sin(angle) * distance
                    self.particle_emitter.particles.append(
                        Particle(px, py, 0, -30, (255, 235, 150), 2, 0.6)
                    )

                # Store impact data for when projectile hits
                glaiveman.judgement_target = target
                glaiveman.judgement_pending = True

                self.floating_texts.append(
                    FloatingText(glaiveman.x, glaiveman.y - 30, "JUDGEMENT!", (255, 215, 0))
                )

        elif self.demo_state == "glaive_judgement_crit" and glaiveman:
            # JUDGEMENT CRITICAL: Spinning sacred glaive with critical hit
            targets = [u for u in self.units if u.player != glaiveman.player and u.hp > 0]
            if targets:
                target = random.choice(targets)

                # Wind-up rotation for GLAIVEMAN
                glaiveman.wind_up_rotation = 0
                glaiveman.wind_up_phase = 0.3

                # Create and launch SPINNING GLAIVE PROJECTILE with critical flag
                projectile = SpinningGlaiveProjectile(
                    glaiveman.x, glaiveman.y,
                    target.x, target.y,
                    speed=500,
                    is_crit=True  # Critical hit!
                )
                self.projectiles.append(projectile)

                # More intense sparkle particles for critical
                for _ in range(25):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(20, 50)
                    px = glaiveman.x + math.cos(angle) * distance
                    py = glaiveman.y + math.sin(angle) * distance
                    self.particle_emitter.particles.append(
                        Particle(px, py, 0, -40, (255, 215, 0), 3, 0.8)
                    )

                # Store impact data for when projectile hits
                glaiveman.judgement_target = target
                glaiveman.judgement_pending = True
                glaiveman.judgement_is_crit = True

                self.floating_texts.append(
                    FloatingText(glaiveman.x, glaiveman.y - 30, "CRITICAL!", (255, 100, 100))
                )

        elif self.demo_state == "glaive_autoclave" and glaiveman:
            # AUTOCLAVE: Cross-shaped retaliation with expanding beams
            # Reduce GLAIVEMAN to critical health to trigger it
            if glaiveman.hp > glaiveman.max_hp * 0.3:
                glaiveman.hp = int(glaiveman.max_hp * 0.25)  # Bring to critical

            # White flash effect at GLAIVEMAN's position
            self.golden_flash_alpha = 255
            self.golden_flash_duration = 0.2

            # Central explosion burst
            self.particle_emitter.emit_burst(glaiveman.x, glaiveman.y, (255, 255, 255), 50)

            # Create four expanding beams (up, right, down, left)
            for direction in range(4):
                beam = CrossBeam(glaiveman.x, glaiveman.y, direction, max_range=3)
                self.cross_beams.append(beam)

            # Energy ring expanding from center
            for angle_deg in range(0, 360, 15):
                angle = math.radians(angle_deg)
                speed = 150
                particle = Particle(glaiveman.x, glaiveman.y,
                                   math.cos(angle) * speed, math.sin(angle) * speed,
                                   (255, 200, 200), 4, 0.8)
                self.particle_emitter.particles.append(particle)

            # Screen shake
            self.screen_shake_intensity = 10
            self.screen_shake_duration = 0.4

            # Mark units for damage (will be applied when beams reach them)
            glaiveman.autoclave_targets = []
            glaiveman.autoclave_total_damage = 0

            # Check all units in cross pattern
            for target in self.units:
                if target.player != glaiveman.player and target.hp > 0:
                    # Check if target is in cardinal directions
                    dx = abs(target.x - glaiveman.x)
                    dy = abs(target.y - glaiveman.y)
                    max_range = 3 * TILE_SIZE + TILE_SIZE // 2

                    # In cross pattern: either same column or same row, within range
                    if (dx < TILE_SIZE // 2 and dy <= max_range) or (dy < TILE_SIZE // 2 and dx <= max_range):
                        # Don't apply damage immediately - wait for beam to reach
                        target.autoclave_hit_timer = 0.3  # Delay before damage
                        glaiveman.autoclave_targets.append(target)

            self.floating_texts.append(
                FloatingText(glaiveman.x, glaiveman.y - 30, "AUTOCLAVE!", (255, 100, 100))
            )

        # MANDIBLE FOREMAN skills
        elif self.demo_state == "mandible_melee":
            # Find MANDIBLE FOREMAN
            mandible = None
            for unit in self.units:
                if "MANDIBLE FOREMAN" in unit.name:
                    mandible = unit
                    break

            if mandible:
                targets = [u for u in self.units if u.player != mandible.player and u.hp > 0]
                if targets:
                    target = random.choice(targets)

                    # MANDIBLE BITE ATTACK - mechanical jaws AND mandibles snapping shut
                    # Create jaw clamp at target position
                    jaw_clamp = JawClamp(target.x, target.y)
                    self.jaw_clamps.append(jaw_clamp)

                    # Save target reference for damage application
                    jaw_clamp.damage_target = target
                    target.original_x = target.x
                    target.original_y = target.y

                    # Store target for subsequent viseroy/release
                    mandible.last_target = target

                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 40, "BITE!", (180, 160, 140))
                    )

        elif self.demo_state == "mandible_expedite":
            # Find MANDIBLE FOREMAN
            mandible = None
            for unit in self.units:
                if "MANDIBLE FOREMAN" in unit.name:
                    mandible = unit
                    break

            if mandible:
                # EXPEDITE - Rush forward in a line, stopping at first enemy
                targets = [u for u in self.units if u.player != mandible.player and u.hp > 0]
                if targets:
                    # Pick closest target for dramatic effect
                    target = min(targets, key=lambda t: math.sqrt((t.x - mandible.x)**2 + (t.y - mandible.y)**2))

                    # Calculate stop position (one tile before target)
                    dx = target.x - mandible.x
                    dy = target.y - mandible.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        # Stop one tile (64 pixels) before target
                        stop_distance = max(0, dist - TILE_SIZE)
                        stop_x = mandible.x + (dx / dist) * stop_distance
                        stop_y = mandible.y + (dy / dist) * stop_distance
                    else:
                        stop_x = mandible.x
                        stop_y = mandible.y

                    # Create expedite rush animation
                    rush = ExpediteRush(mandible.x, mandible.y, stop_x, stop_y, mandible)
                    rush.target_unit = target
                    self.expedite_rushes.append(rush)

                    # Store target for subsequent viseroy/release
                    mandible.last_target = target

                    self.floating_texts.append(
                        FloatingText(mandible.x, mandible.y - 40, "EXPEDITE!", (220, 220, 255))
                    )

        elif self.demo_state == "mandible_jawline":
            # Find MANDIBLE FOREMAN
            mandible = None
            for unit in self.units:
                if "MANDIBLE FOREMAN" in unit.name:
                    mandible = unit
                    break

            if mandible:
                # JAWLINE - Deploy network of bear trap jaws in 3x3 grid
                # Self-targeted skill centered on MANDIBLE FOREMAN
                jawline = JawlineNetwork(mandible.x, mandible.y)
                self.jawline_networks.append(jawline)

                # Find all enemy units in 3x3 grid for damage
                for target in self.units:
                    if target.player != mandible.player and target.hp > 0:
                        # Check if target is within 3x3 grid (1 tile in each direction)
                        dx = abs(target.grid_x - mandible.grid_x)
                        dy = abs(target.grid_y - mandible.grid_y)
                        if dx <= 1 and dy <= 1 and not (dx == 0 and dy == 0):  # Adjacent, not center
                            jawline.damage_targets.append(target)
                            target.original_x = target.x
                            target.original_y = target.y

                # Central explosion burst at FOREMAN's position
                self.particle_emitter.emit_burst(mandible.x, mandible.y, (255, 102, 0), 30)

                # Orange spark ring expanding from center
                for angle_deg in range(0, 360, 30):
                    angle = math.radians(angle_deg)
                    speed = 100
                    particle = Particle(mandible.x, mandible.y,
                                       math.cos(angle) * speed, math.sin(angle) * speed,
                                       (255, 150, 0), 3, 0.6)
                    self.particle_emitter.particles.append(particle)

                # Screen shake on deployment
                self.screen_shake_intensity = 6
                self.screen_shake_duration = 0.3

                self.floating_texts.append(
                    FloatingText(mandible.x, mandible.y - 40, "JAWLINE!", (255, 102, 0))
                )

        elif self.demo_state == "mandible_viseroy":
            # Find MANDIBLE FOREMAN
            mandible = None
            for unit in self.units:
                if "MANDIBLE FOREMAN" in unit.name:
                    mandible = unit
                    break

            if mandible:
                # Try to use the last targeted enemy from melee/expedite
                target = None
                if hasattr(mandible, 'last_target') and mandible.last_target and mandible.last_target.hp > 0:
                    target = mandible.last_target
                else:
                    # Fallback to random enemy
                    targets = [u for u in self.units if u.player != mandible.player and u.hp > 0]
                    if targets:
                        target = random.choice(targets)

                if target:
                    # VISEROY TRAP - grinding jaws that chew the target
                    # Create Viseroy trap at target position
                    trap = ViseroyTrap(target.x, target.y)
                    self.viseroy_traps.append(trap)

                    # Save target reference for damage application
                    trap.damage_target = target
                    target.original_x = target.x
                    target.original_y = target.y

                    # Store this target for the next release
                    mandible.last_viseroy_target = target

                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 40, "VISEROY!", (180, 160, 140))
                    )

        elif self.demo_state == "mandible_release":
            # Find MANDIBLE FOREMAN
            mandible = None
            for unit in self.units:
                if "MANDIBLE FOREMAN" in unit.name:
                    mandible = unit
                    break

            if mandible:
                # Try to use the last viseroy target
                target = None
                if hasattr(mandible, 'last_viseroy_target') and mandible.last_viseroy_target and mandible.last_viseroy_target.hp > 0:
                    target = mandible.last_viseroy_target
                else:
                    # Fallback to random enemy
                    targets = [u for u in self.units if u.player != mandible.player and u.hp > 0]
                    if targets:
                        target = random.choice(targets)

                if target:
                    # VISEROY RELEASE - jaws spring open to release the victim
                    # Create release animation at target position
                    release = ViseroyRelease(target.x, target.y)
                    self.viseroy_releases.append(release)

                    # Save target reference for position tracking
                    release.damage_target = target
                    target.original_x = target.x
                    target.original_y = target.y

                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 40, "RELEASED!", (140, 200, 140))
                    )

        elif self.demo_state == "mandible_site_inspection":
            # Find MANDIBLE FOREMAN
            mandible = None
            for unit in self.units:
                if "MANDIBLE FOREMAN" in unit.name:
                    mandible = unit
                    break

            if mandible:
                # Pick a location within skill range (3 tiles from FOREMAN)
                skill_range = 3
                # Random offset within range
                offset_tiles_x = random.randint(-skill_range, skill_range)
                offset_tiles_y = random.randint(-skill_range, skill_range)

                # Calculate target position in pixels
                target_x = mandible.x + offset_tiles_x * TILE_SIZE
                target_y = mandible.y + offset_tiles_y * TILE_SIZE

                # Clamp to screen bounds
                target_x = max(TILE_SIZE, min(SCREEN_WIDTH - TILE_SIZE, target_x))
                target_y = max(TILE_SIZE, min(SCREEN_HEIGHT - TILE_SIZE, target_y))

                # SITE INSPECTION - laser level scanning a 3x3 area
                scan = SiteInspectionScan(target_x, target_y)
                self.site_inspections.append(scan)

                self.floating_texts.append(
                    FloatingText(target_x, target_y - 50, "SITE INSPECTION", (255, 200, 0))
                )

                # Show power-up animations on allies after scan completes
                allies = [u for u in self.units if u.player == mandible.player]
                for ally in allies:
                    # Randomly decide buff type for demo
                    is_full = random.random() < 0.6  # 60% chance of full buff
                    # Delay buff indicator to trigger after scan completes
                    buff = SiteInspectionBuff(ally.x, ally.y, is_full)
                    buff.trigger_delay = 1.2  # Wait for scan to nearly complete
                    buff.timer = -buff.trigger_delay  # Negative timer = waiting
                    buff.phase = "waiting"
                    self.site_inspection_buffs.append(buff)

                    # Add floating text when buff triggers
                    if is_full:
                        # Full buff gets green text
                        text = FloatingText(ally.x, ally.y - 30, "+ATK +MOV", (0, 255, 100))
                    else:
                        # Partial buff gets orange text
                        text = FloatingText(ally.x, ally.y - 30, "+ATK", (255, 150, 0))
                    # Delay the text to match buff appearance
                    text.lifetime = 2.0 + 1.2  # Normal lifetime + delay
                    text.timer = -1.2  # Start delayed
                    self.floating_texts.append(text)

        elif self.demo_state == "potpourrist_demilune":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                if targets:
                    # Find closest target for direction
                    target = min(targets, key=lambda t:
                               math.sqrt((t.x - potpourrist.x)**2 + (t.y - potpourrist.y)**2))

                    # Create regular DEMILUNE swing animation with targets
                    demilune = DemiluneSwing(potpourrist.x, potpourrist.y, potpourrist,
                                            target.x, target.y, infused=False, targets=targets)
                    self.demilune_swings.append(demilune)

                    # Damage will be applied by the animation when swing reaches targets
                    # Store damage info on the animation for later application
                    demilune.damage_amount = 3
                    demilune.damage_color = COLOR_DAMAGE
                    demilune.damage_pending = True

        elif self.demo_state == "potpourrist_demilune_infused":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                if targets:
                    # Find closest target for direction
                    target = min(targets, key=lambda t:
                               math.sqrt((t.x - potpourrist.x)**2 + (t.y - potpourrist.y)**2))

                    # Create INFUSED DEMILUNE swing animation (with potpourri trail)
                    demilune = DemiluneSwing(potpourrist.x, potpourrist.y, potpourrist,
                                            target.x, target.y, infused=True, targets=targets)
                    self.demilune_swings.append(demilune)

                    # Damage will be applied by the animation when swing reaches targets
                    demilune.damage_amount = 4
                    demilune.damage_color = COLOR_SKILL
                    demilune.damage_pending = True

                    # Deactivate aura after consuming potpourri
                    potpourrist.potpourri_aura_active = False

        elif self.demo_state == "potpourrist_lunacy":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                # Apply Lunacy eclipse effect to enemy units only (not POTPOURRIST's team)
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                for target in targets:
                    # Create lunacy effect on each enemy
                    lunacy = LunacyEffect(target.x, target.y, target)
                    self.lunacy_effects.append(lunacy)

                    # Floating text
                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 40, "LUNACY", (180, 170, 200))
                    )

        elif self.demo_state == "potpourrist_granite_geas":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                if targets:
                    # Find closest target
                    target = min(targets, key=lambda t:
                               math.sqrt((t.x - potpourrist.x)**2 + (t.y - potpourrist.y)**2))

                    # Create GRANITE GEAS effect (normal)
                    geas = GraniteGeasEffect(target.x, target.y, target, infused=False)
                    self.granite_geas_effects.append(geas)

                    # Apply damage
                    target.take_damage(4)
                    self.floating_texts.append(FloatingText(target.x, target.y - 30, "-4", COLOR_DAMAGE))

                    # Floating text for geas
                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 50, "GEAS", (140, 100, 60))
                    )

        elif self.demo_state == "potpourrist_granite_geas_infused":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                if targets:
                    # Find closest target
                    target = min(targets, key=lambda t:
                               math.sqrt((t.x - potpourrist.x)**2 + (t.y - potpourrist.y)**2))

                    # Create GRANITE GEAS effect (infused - longer duration)
                    geas = GraniteGeasEffect(target.x, target.y, target, infused=True)
                    self.granite_geas_effects.append(geas)

                    # Apply damage
                    target.take_damage(4)
                    self.floating_texts.append(FloatingText(target.x, target.y - 30, "-4", COLOR_SKILL))

                    # Floating text for geas
                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 50, "GEAS+", (180, 100, 255))
                    )

                    # Deactivate aura after consuming potpourri
                    potpourrist.potpourri_aura_active = False

        elif self.demo_state == "potpourrist_geas_break_heal":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                if targets:
                    # Find closest target (where geas was applied)
                    target = min(targets, key=lambda t:
                               math.sqrt((t.x - potpourrist.x)**2 + (t.y - potpourrist.y)**2))

                    # Create geas break healing effect
                    heal_effect = GeasBreakHeal(target.x, target.y, potpourrist.x, potpourrist.y, potpourrist, heal_amount=4)
                    self.geas_break_heals.append(heal_effect)

                    # Apply healing to POTPOURRIST
                    potpourrist.hp = min(potpourrist.max_hp, potpourrist.hp + 4)
                    self.floating_texts.append(
                        FloatingText(potpourrist.x, potpourrist.y - 30, "+4", (100, 255, 150))
                    )

        elif self.demo_state == "potpourrist_melange_eminence":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                # Create melange eminence effect (normal - 1 HP healing)
                melange_effect = MelangeEminence(potpourrist.x, potpourrist.y, potpourrist, heal_amount=1, infused=False)
                self.melange_eminence_effects.append(melange_effect)

                # Apply healing
                potpourrist.hp = min(potpourrist.max_hp, potpourrist.hp + 1)
                self.floating_texts.append(
                    FloatingText(potpourrist.x, potpourrist.y - 30, "+1", (150, 200, 150))
                )

        elif self.demo_state == "potpourrist_melange_eminence_infused":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                # Create melange eminence effect (infused - 2 HP healing)
                melange_effect = MelangeEminence(potpourrist.x, potpourrist.y, potpourrist, heal_amount=2, infused=True)
                self.melange_eminence_effects.append(melange_effect)

                # Apply healing
                potpourrist.hp = min(potpourrist.max_hp, potpourrist.hp + 2)
                self.floating_texts.append(
                    FloatingText(potpourrist.x, potpourrist.y - 30, "+2", (200, 100, 200))
                )

        elif self.demo_state == "potpourrist_melee":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                targets = [u for u in self.units if u.player != potpourrist.player and u.hp > 0]
                if targets:
                    # Find closest target
                    target = min(targets, key=lambda t:
                               math.sqrt((t.x - potpourrist.x)**2 + (t.y - potpourrist.y)**2))

                    # Wind-up: Lift pedestal overhead
                    potpourrist.melee_phase = "windup"
                    potpourrist.melee_timer = 0
                    potpourrist.melee_target = target
                    potpourrist.original_x = potpourrist.x
                    potpourrist.original_y = potpourrist.y

                    # No lunge forward - stays in place for overhead slam
                    potpourrist.melee_lunge_x = 0
                    potpourrist.melee_lunge_y = 0

                    # Wind-up particles (gathering energy - purple potpourri theme)
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        distance = random.uniform(20, 40)
                        px = potpourrist.x + math.cos(angle) * distance
                        py = potpourrist.y + math.sin(angle) * distance
                        particle = Particle(px, py,
                                           -math.cos(angle) * 50, -math.sin(angle) * 50,
                                           (200, 100, 200), 3, 0.5)
                        self.particle_emitter.particles.append(particle)

        elif self.demo_state == "potpourrist_infuse":
            # Find POTPOURRIST
            potpourrist = None
            for unit in self.units:
                if "POTPOURRIST" in unit.name:
                    potpourrist = unit
                    break

            if potpourrist:
                # INFUSE - Create potpourri with swirling petals
                infuse = InfuseEffect(potpourrist.x, potpourrist.y, potpourrist)
                self.infuse_effects.append(infuse)

                # Floating text
                self.floating_texts.append(
                    FloatingText(potpourrist.x, potpourrist.y - 40, "INFUSE!", (200, 100, 200))
                )

    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.execute_demo_action()
                    self.schedule_next_demo()
                elif event.key == pygame.K_TAB:
                    # Cycle between unit modes
                    if self.active_unit_mode == "GLAIVEMAN":
                        self.active_unit_mode = "MANDIBLE_FOREMAN"
                    elif self.active_unit_mode == "MANDIBLE_FOREMAN":
                        self.active_unit_mode = "POTPOURRIST"
                    else:
                        self.active_unit_mode = "GLAIVEMAN"

                    # Reset and rebuild the scene
                    self.units.clear()
                    self.particle_emitter.particles.clear()
                    self.floating_texts.clear()
                    self.projectiles.clear()
                    self.lightning_bolts.clear()
                    self.debris_particles.clear()
                    self.cross_beams.clear()
                    self.jaw_clamps.clear()
                    self.jawline_networks.clear()
                    self.expedite_rushes.clear()
                    self.viseroy_traps.clear()
                    self.viseroy_releases.clear()
                    self.site_inspections.clear()
                    self.site_inspection_buffs.clear()
                    self.pedestal_strikes.clear()
                    self.infuse_effects.clear()
                    self.demilune_swings.clear()
                    self.demo_skill_index = 0
                    self.setup()

                    print(f"Switched to {self.active_unit_mode} demo mode")

    def update(self, delta_time):
        """Update game state."""
        # Demo timer
        self.demo_timer -= delta_time
        if self.demo_timer <= 0:
            # Check if we need to reset unit positions before next action
            if hasattr(self, 'previous_demo_state'):
                # Reset MANDIBLE FOREMAN after jawline (last skill)
                if self.active_unit_mode == "MANDIBLE_FOREMAN" and self.previous_demo_state == "mandible_jawline":
                    for unit in self.units:
                        if "MANDIBLE FOREMAN" in unit.name:
                            unit.grid_x = 6
                            unit.grid_y = 2
                            unit.x = 6 * TILE_SIZE + TILE_SIZE // 2
                            unit.y = 2 * TILE_SIZE + TILE_SIZE // 2
                            break

                # Reset GLAIVEMAN after vault (last skill)
                elif self.active_unit_mode == "GLAIVEMAN" and self.previous_demo_state == "glaive_vault":
                    for unit in self.units:
                        if "GLAIVEMAN" in unit.name:
                            unit.grid_x = 6
                            unit.grid_y = 2
                            unit.x = 6 * TILE_SIZE + TILE_SIZE // 2
                            unit.y = 2 * TILE_SIZE + TILE_SIZE // 2
                            break

            # Store current state before executing next action
            if hasattr(self, 'demo_state'):
                self.previous_demo_state = self.demo_state

            self.execute_demo_action()
            self.schedule_next_demo()

        # Update screen shake
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= delta_time
            if self.screen_shake_duration <= 0:
                self.screen_shake_intensity = 0

        # Update golden flash
        if hasattr(self, 'golden_flash_duration') and self.golden_flash_duration > 0:
            self.golden_flash_duration -= delta_time
            self.golden_flash_alpha = int(255 * (self.golden_flash_duration / 0.15))

        # Update units
        for unit in self.units:
            unit.update(delta_time)

            # Update melee attack animation
            if hasattr(unit, 'melee_phase') and unit.melee_phase:
                unit.melee_timer += delta_time

                # Check if this is POTPOURRIST (overhead pedestal swing)
                is_potpourrist = "POTPOURRIST" in unit.name

                if unit.melee_phase == "windup":
                    if is_potpourrist:
                        # POTPOURRIST: Lift pedestal overhead (0.25s)
                        if unit.melee_timer < 0.25:
                            progress = unit.melee_timer / 0.25
                            unit.wind_up_rotation = -15 * progress  # Tilt back more
                            # Stretch up slightly (anticipation)
                            unit.pry_stretch_y = 1.0 + (progress * 0.1)
                        else:
                            unit.melee_phase = "lunge"
                            unit.melee_timer = 0
                            unit.pry_stretch_y = 1.0
                    else:
                        # GLAIVEMAN: Pull back and rotate slightly (0.15s)
                        if unit.melee_timer < 0.15:
                            progress = unit.melee_timer / 0.15
                            unit.wind_up_rotation = -10 * progress  # Tilt back
                            # Pull back slightly
                            unit.x = unit.original_x - unit.melee_lunge_x * 0.2 * progress
                            unit.y = unit.original_y - unit.melee_lunge_y * 0.2 * progress
                        else:
                            unit.melee_phase = "lunge"
                            unit.melee_timer = 0

                elif unit.melee_phase == "lunge":
                    if is_potpourrist:
                        # POTPOURRIST: Overhead slam straight down (0.15s)
                        if unit.melee_timer < 0.15:
                            progress = unit.melee_timer / 0.15
                            # Accelerate (ease-in)
                            eased = progress * progress
                            unit.wind_up_rotation = -15 + eased * 35  # Swing to +20 degrees

                            # Gray dust particles during slam
                            if random.random() < 0.6:
                                speed = random.uniform(80, 150)
                                angle = math.atan2(unit.melee_target.y - unit.y,
                                                   unit.melee_target.x - unit.x) + random.uniform(-0.3, 0.3)
                                particle = Particle(unit.x, unit.y - 20,
                                                   math.cos(angle) * speed,
                                                   math.sin(angle) * speed,
                                                   (150, 150, 150), random.uniform(4, 8), 0.4)
                                self.particle_emitter.particles.append(particle)
                        else:
                            unit.melee_phase = "impact"
                            unit.melee_timer = 0

                            # POTPOURRIST impact - create PedestalStrike for effects
                            if unit.melee_target and unit.melee_target.hp > 0:
                                strike = PedestalStrike(unit.melee_target.x, unit.melee_target.y, unit.melee_target)
                                self.pedestal_strikes.append(strike)

                                # Damage number will be shown by PedestalStrike
                                self.floating_texts.append(
                                    FloatingText(unit.x, unit.y - 40, "PEDESTAL!", (200, 100, 200))
                                )

                                # Massive impact
                                unit.melee_target.shake_intensity = 12
                                self.screen_shake_intensity = 10
                                self.screen_shake_duration = 0.35
                    else:
                        # GLAIVEMAN: Fast lunge forward (0.1s)
                        if unit.melee_timer < 0.1:
                            progress = unit.melee_timer / 0.1
                            unit.wind_up_rotation = -10 + progress * 30  # Swing through
                            # Lunge forward
                            unit.x = unit.original_x + unit.melee_lunge_x * progress
                            unit.y = unit.original_y + unit.melee_lunge_y * progress

                            # Slash arc particles
                            if random.random() < 0.5:
                                arc_angle = math.atan2(unit.melee_target.y - unit.y,
                                                       unit.melee_target.x - unit.x)
                                arc_angle += random.uniform(-0.5, 0.5)
                                speed = random.uniform(100, 200)
                                particle = Particle(unit.x, unit.y,
                                                   math.cos(arc_angle) * speed,
                                                   math.sin(arc_angle) * speed,
                                                   (220, 230, 255), random.uniform(3, 6), 0.3)
                                self.particle_emitter.particles.append(particle)
                        else:
                            unit.melee_phase = "impact"
                            unit.melee_timer = 0

                            # Apply damage on impact
                            if unit.melee_target and unit.melee_target.hp > 0:
                                damage = random.randint(3, 5)
                                unit.melee_target.take_damage(damage)
                                self.floating_texts.append(
                                    FloatingText(unit.melee_target.x, unit.melee_target.y - 20,
                                               f"-{damage}", COLOR_DAMAGE)
                                )
                                # Impact effects
                                self.particle_emitter.emit_burst(unit.melee_target.x,
                                                                unit.melee_target.y,
                                                                (255, 200, 150), 25)
                                unit.melee_target.shake_intensity = 6
                                self.screen_shake_intensity = 4
                                self.screen_shake_duration = 0.15

                elif unit.melee_phase == "impact":
                    # Brief pause at full extension (0.05s)
                    if unit.melee_timer >= 0.05:
                        unit.melee_phase = "recovery"
                        unit.melee_timer = 0

                elif unit.melee_phase == "recovery":
                    # Return to original position (0.2s)
                    if unit.melee_timer < 0.2:
                        progress = unit.melee_timer / 0.2
                        # Smoothly return to original position
                        if not is_potpourrist:
                            unit.x = unit.original_x + unit.melee_lunge_x * (1.0 - progress)
                            unit.y = unit.original_y + unit.melee_lunge_y * (1.0 - progress)
                        unit.wind_up_rotation = 20 * (1.0 - progress)  # Return rotation
                    else:
                        # End animation
                        unit.melee_phase = None
                        unit.wind_up_rotation = 0
                        unit.x = unit.original_x
                        unit.y = unit.original_y

            # Update vault animation with flip
            if hasattr(unit, 'vault_phase') and unit.vault_phase == "vaulting":
                unit.vault_timer += delta_time
                progress = min(1.0, unit.vault_timer / unit.vault_duration)

                # Horizontal movement (linear interpolation)
                unit.x = unit.vault_start_x + (unit.vault_target_x - unit.vault_start_x) * progress
                unit.y = unit.vault_start_y + (unit.vault_target_y - unit.vault_start_y) * progress

                # Vertical arc (parabolic jump)
                arc_height = 120  # Peak height of jump
                vertical_offset = math.sin(progress * math.pi) * arc_height
                unit.y -= vertical_offset

                # FLIP ROTATION - Complete 360 degree rotation during vault
                unit.wind_up_rotation = progress * 360  # Full rotation

                # Trail particles along the arc
                if random.random() < 0.3:
                    # Leave trail particles at current position
                    particle = Particle(unit.x, unit.y + vertical_offset,
                                       random.uniform(-20, 20), random.uniform(-20, 20),
                                       (100, 200, 255), random.uniform(3, 6), 0.5)
                    self.particle_emitter.particles.append(particle)

                # Landing phase
                if progress >= 1.0:
                    unit.vault_phase = "landing"
                    unit.vault_timer = 0
                    # Snap to target grid position
                    unit.grid_x = unit.vault_target_grid_x
                    unit.grid_y = unit.vault_target_grid_y
                    unit.x = unit.vault_target_x
                    unit.y = unit.vault_target_y
                    unit.wind_up_rotation = 0  # Reset rotation

                    # Landing effects
                    self.particle_emitter.emit_burst(unit.x, unit.y, (100, 200, 255), 30)
                    self.screen_shake_intensity = 5
                    self.screen_shake_duration = 0.2

                    # Dust cloud on landing
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(30, 80)
                        particle = Particle(unit.x, unit.y + 20,
                                           math.cos(angle) * speed, math.sin(angle) * speed - 10,
                                           (180, 180, 200), random.uniform(4, 8), 0.6)
                        particle.gravity = 100
                        self.particle_emitter.particles.append(particle)

            elif hasattr(unit, 'vault_phase') and unit.vault_phase == "landing":
                # Brief landing recovery (0.1s)
                unit.vault_timer += delta_time
                if unit.vault_timer >= 0.1:
                    unit.vault_phase = None

            # Update PRY lever motion (GLAIVEMAN prying animation)
            if hasattr(unit, 'pry_lever_phase') and unit.pry_lever_phase:
                unit.pry_lever_timer += delta_time

                if unit.pry_lever_phase == "inserting":
                    # Phase 1: Insert polearm under target (0.15s)
                    # Lean forward and down, rotate forward
                    if unit.pry_lever_timer < 0.15:
                        progress = unit.pry_lever_timer / 0.15
                        unit.wind_up_rotation = progress * -20  # Lean forward
                        # Move slightly toward target
                        unit.y = unit.original_y + progress * 10  # Slight downward
                    else:
                        unit.pry_lever_phase = "levering"
                        unit.pry_lever_timer = 0

                elif unit.pry_lever_phase == "levering":
                    # Phase 2: Pull back on lever to pry upward (0.2s)
                    # Lean back strongly, polearm acts as fulcrum
                    if unit.pry_lever_timer < 0.2:
                        progress = unit.pry_lever_timer / 0.2
                        # Rotate backward (levering motion)
                        unit.wind_up_rotation = -20 + progress * 50  # Swing back from -20 to +30
                        # Pull back position
                        unit.y = unit.original_y + 10 - progress * 15  # Pull up and back

                        # Strain particles (effort)
                        if random.random() < 0.2:
                            particle = Particle(unit.x, unit.y - 10,
                                               random.uniform(-30, 30), random.uniform(-50, -20),
                                               (255, 200, 100), random.uniform(2, 4), 0.3)
                            self.particle_emitter.particles.append(particle)
                    else:
                        unit.pry_lever_phase = "release"
                        unit.pry_lever_timer = 0

                elif unit.pry_lever_phase == "release":
                    # Phase 3: Release and return to stance (0.15s)
                    if unit.pry_lever_timer < 0.15:
                        progress = unit.pry_lever_timer / 0.15
                        # Return to normal
                        unit.wind_up_rotation = 30 * (1.0 - progress)
                        unit.y = unit.original_y - 5 + progress * 5
                        unit.x = unit.original_x
                    else:
                        # End animation
                        unit.pry_lever_phase = None
                        unit.wind_up_rotation = 0
                        unit.x = unit.original_x
                        unit.y = unit.original_y

            # Old mandible bite animation removed - now using JawClamp class
            # (kept for reference but disabled)
            if False and hasattr(unit, 'mandible_bite_phase') and unit.mandible_bite_phase:
                unit.mandible_bite_timer += delta_time

                if unit.mandible_bite_phase == "opening":
                    # Phase 1: Crushing jaws materialize and open around target (0.2s)
                    if unit.mandible_bite_timer < 0.2:
                        progress = unit.mandible_bite_timer / 0.2

                        # Create/update jaw visualization
                        if not hasattr(unit, 'jaw_opening'):
                            unit.jaw_opening = 0
                        unit.jaw_opening = progress * 50  # Jaws open to 50 pixels apart

                        # Jaw materialization particles (from target position outward)
                        if random.random() < 0.4:
                            # Upper jaw particles
                            particle = Particle(
                                unit.mandible_bite_target.x + random.uniform(-20, 20),
                                unit.mandible_bite_target.y - unit.jaw_opening,
                                random.uniform(-10, 10), random.uniform(-20, 0),
                                (150, 150, 160), random.uniform(3, 6), 0.3
                            )
                            self.particle_emitter.particles.append(particle)

                            # Lower jaw particles
                            particle = Particle(
                                unit.mandible_bite_target.x + random.uniform(-20, 20),
                                unit.mandible_bite_target.y + unit.jaw_opening,
                                random.uniform(-10, 10), random.uniform(0, 20),
                                (150, 150, 160), random.uniform(3, 6), 0.3
                            )
                            self.particle_emitter.particles.append(particle)
                    else:
                        unit.mandible_bite_phase = "crushing"
                        unit.mandible_bite_timer = 0

                elif unit.mandible_bite_phase == "crushing":
                    # Phase 2: Jaws SLAM shut on target (0.1s) - VERY FAST
                    if unit.mandible_bite_timer < 0.1:
                        progress = unit.mandible_bite_timer / 0.1

                        # Jaws closing rapidly
                        unit.jaw_opening = 50 * (1.0 - progress)

                        # Compression particles as jaws close
                        if random.random() < 0.6:
                            # Particles squeezed out from closing jaws
                            side = random.choice([-1, 1])
                            particle = Particle(
                                unit.mandible_bite_target.x + side * random.uniform(10, 25),
                                unit.mandible_bite_target.y,
                                side * random.uniform(100, 200), random.uniform(-50, 50),
                                (220, 200, 180), random.uniform(3, 7), 0.4
                            )
                            self.particle_emitter.particles.append(particle)
                    else:
                        unit.mandible_bite_phase = "clamped"
                        unit.mandible_bite_timer = 0
                        unit.jaw_opening = 0

                        # IMPACT - jaws have closed completely
                        if unit.mandible_bite_target and unit.mandible_bite_target.hp > 0:
                            damage = random.randint(3, 5)
                            unit.mandible_bite_target.take_damage(damage)
                            self.floating_texts.append(
                                FloatingText(unit.mandible_bite_target.x,
                                           unit.mandible_bite_target.y - 20,
                                           f"-{damage}", COLOR_DAMAGE)
                            )

                            # Massive impact burst
                            self.particle_emitter.emit_burst(
                                unit.mandible_bite_target.x,
                                unit.mandible_bite_target.y,
                                (255, 220, 150), 40
                            )

                            # Jaw teeth impact particles (radial)
                            for i in range(20):
                                angle = (i / 20) * 2 * math.pi
                                speed = random.uniform(80, 150)
                                particle = Particle(
                                    unit.mandible_bite_target.x,
                                    unit.mandible_bite_target.y,
                                    math.cos(angle) * speed,
                                    math.sin(angle) * speed,
                                    (180, 160, 140), random.uniform(4, 8), 0.5
                                )
                                self.particle_emitter.particles.append(particle)

                            # Heavy shake
                            unit.mandible_bite_target.shake_intensity = 12
                            self.screen_shake_intensity = 8
                            self.screen_shake_duration = 0.2

                elif unit.mandible_bite_phase == "clamped":
                    # Phase 3: Jaws grind and crush (0.15s)
                    if unit.mandible_bite_timer < 0.15:
                        # Grinding vibration on target
                        vibration_x = math.sin(unit.mandible_bite_timer * 80) * 3
                        vibration_y = math.cos(unit.mandible_bite_timer * 80) * 3
                        unit.mandible_bite_target.x = unit.mandible_bite_target.original_x + vibration_x
                        unit.mandible_bite_target.y = unit.mandible_bite_target.original_y + vibration_y

                        # Crushing pressure particles
                        if random.random() < 0.5:
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(20, 50)
                            particle = Particle(
                                unit.mandible_bite_target.x,
                                unit.mandible_bite_target.y,
                                math.cos(angle) * speed,
                                math.sin(angle) * speed,
                                (200, 180, 150), random.uniform(2, 5), 0.4
                            )
                            self.particle_emitter.particles.append(particle)

                        # Metal grinding sparks
                        if random.random() < 0.3:
                            particle = Particle(
                                unit.mandible_bite_target.x + random.uniform(-10, 10),
                                unit.mandible_bite_target.y + random.uniform(-10, 10),
                                random.uniform(-40, 40),
                                random.uniform(-60, -20),
                                (255, 240, 100), random.uniform(2, 4), 0.25
                            )
                            self.particle_emitter.particles.append(particle)
                    else:
                        unit.mandible_bite_phase = "releasing"
                        unit.mandible_bite_timer = 0

                elif unit.mandible_bite_phase == "releasing":
                    # Phase 4: Jaws open and dissipate (0.15s)
                    if unit.mandible_bite_timer < 0.15:
                        progress = unit.mandible_bite_timer / 0.15

                        # Jaws opening back up
                        unit.jaw_opening = progress * 40

                        # Reset target position
                        if hasattr(unit.mandible_bite_target, 'original_x'):
                            unit.mandible_bite_target.x = unit.mandible_bite_target.original_x
                            unit.mandible_bite_target.y = unit.mandible_bite_target.original_y

                        # Jaw dissipation particles
                        if random.random() < 0.3:
                            # Upper and lower jaw fading
                            for offset in [-1, 1]:
                                particle = Particle(
                                    unit.mandible_bite_target.x + random.uniform(-15, 15),
                                    unit.mandible_bite_target.y + offset * unit.jaw_opening,
                                    random.uniform(-20, 20),
                                    offset * random.uniform(10, 30),
                                    (140, 140, 150), random.uniform(3, 6), 0.4
                                )
                                particle.fade = True
                                self.particle_emitter.particles.append(particle)
                    else:
                        # End animation
                        unit.mandible_bite_phase = None
                        unit.jaw_opening = 0
                        if hasattr(unit.mandible_bite_target, 'original_x'):
                            unit.mandible_bite_target.x = unit.mandible_bite_target.original_x
                            unit.mandible_bite_target.y = unit.mandible_bite_target.original_y

            # Update wind-up rotation
            if hasattr(unit, 'wind_up_phase') and unit.wind_up_phase > 0:
                unit.wind_up_phase -= delta_time
                unit.wind_up_rotation = (1 - unit.wind_up_phase / 0.3) * 15
                # Reset rotation when wind-up completes
                if unit.wind_up_phase <= 0:
                    unit.wind_up_rotation = 0

            # Update jawline impact animation (compression from trap)
            if hasattr(unit, 'jawline_impact_phase') and unit.jawline_impact_phase:
                unit.jawline_impact_timer += delta_time

                if unit.jawline_impact_phase == "compression":
                    # Fast compression (0.1s)
                    if unit.jawline_impact_timer < 0.1:
                        progress = unit.jawline_impact_timer / 0.1
                        # Squash vertically, expand horizontally
                        unit.pry_stretch_y = 1.0 - progress * 0.4  # Compress to 0.6 height
                    else:
                        unit.jawline_impact_phase = "rebound"
                        unit.jawline_impact_timer = 0
                        unit.pry_stretch_y = 0.6

                elif unit.jawline_impact_phase == "rebound":
                    # Quick rebound back (0.15s)
                    if unit.jawline_impact_timer < 0.15:
                        progress = unit.jawline_impact_timer / 0.15
                        # Elastic rebound - overshoot slightly then settle
                        if progress < 0.7:
                            # Expand back fast
                            unit.pry_stretch_y = 0.6 + (progress / 0.7) * 0.5  # Go to 1.1
                        else:
                            # Settle back to 1.0
                            overshoot_progress = (progress - 0.7) / 0.3
                            unit.pry_stretch_y = 1.1 - overshoot_progress * 0.1
                    else:
                        # End animation
                        unit.jawline_impact_phase = None
                        unit.pry_stretch_y = 1.0

            # Update cross decal
            if hasattr(unit, 'cross_decal_duration') and unit.cross_decal_duration > 0:
                unit.cross_decal_duration -= delta_time
                unit.cross_decal_alpha = int(255 * (unit.cross_decal_duration / 1.0))

            # Update Autoclave hit timer
            if hasattr(unit, 'autoclave_hit_timer') and unit.autoclave_hit_timer > 0:
                unit.autoclave_hit_timer -= delta_time
                if unit.autoclave_hit_timer <= 0:
                    # Apply damage when timer expires
                    damage = max(1, 8 - unit.defense) if hasattr(unit, 'defense') else 8
                    unit.take_damage(damage)
                    self.floating_texts.append(
                        FloatingText(unit.x, unit.y - 20, f"-{damage}", COLOR_DAMAGE)
                    )
                    # Impact burst
                    self.particle_emitter.emit_burst(unit.x, unit.y, (255, 100, 100), 25)
                    unit.shake_intensity = 8

                    # Track damage for healing (find the glaiveman who cast it)
                    for u in self.units:
                        if hasattr(u, 'autoclave_targets') and unit in u.autoclave_targets:
                            u.autoclave_total_damage += damage
                            # If this was the last target, heal the glaiveman
                            remaining_targets = sum(1 for t in u.autoclave_targets
                                                   if hasattr(t, 'autoclave_hit_timer') and t.autoclave_hit_timer > 0)
                            if remaining_targets == 0 and u.autoclave_total_damage > 0:
                                heal = u.autoclave_total_damage // 2
                                u.heal(heal)
                                self.particle_emitter.emit_float(u.x, u.y, COLOR_HEAL, 30)
                                self.floating_texts.append(
                                    FloatingText(u.x, u.y - 20, f"+{heal}", COLOR_HEAL)
                                )
                                # Clean up
                                del u.autoclave_targets
                                del u.autoclave_total_damage

            # Update PRY animation
            if hasattr(unit, 'pry_phase') and unit.pry_phase:
                unit.pry_timer += delta_time
                progress = unit.pry_timer / unit.pry_max_time

                if unit.pry_phase == "launching":
                    # Launch upward MUCH faster and higher with stretch effect
                    # Use exponential curve for faster initial velocity
                    launch_curve = math.pow(progress, 0.6)  # Accelerating curve
                    unit.pry_stretch_y = 1.0 + launch_curve * 0.8  # More stretch
                    unit.y = unit.original_y - launch_curve * 400  # Much higher (was 150)

                    if progress >= 0.25:  # Hit ceiling earlier (was 0.4)
                        unit.pry_phase = "ceiling_impact"
                        unit.pry_timer = 0
                        # Ceiling impact flash (white, more intense)
                        self.golden_flash_alpha = 255
                        self.golden_flash_duration = 0.15
                        # Impact particles at top (more dramatic)
                        for _ in range(30):
                            self.particle_emitter.particles.append(
                                Particle(unit.x, unit.y,
                                        random.uniform(-150, 150), random.uniform(-80, 80),
                                        (255, 255, 255), random.uniform(3, 7), 0.5)
                            )

                        # DEBRIS KNOCKED DOWN FROM CEILING - spawn at zenith
                        for _ in range(25):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(100, 250)
                            size = random.uniform(6, 12)
                            self.debris_particles.append(
                                DebrisParticle(unit.x, unit.y,
                                             math.cos(angle) * speed,
                                             math.sin(angle) * speed + 50,  # Initial downward velocity
                                             size, (120, 100, 80))
                            )

                elif unit.pry_phase == "ceiling_impact":
                    # Brief pause at ceiling
                    if unit.pry_timer >= 0.2:
                        unit.pry_phase = "falling"
                        unit.pry_timer = 0

                elif unit.pry_phase == "falling":
                    # Fall back down from much higher position
                    fall_progress = min(1.0, unit.pry_timer / 0.4)
                    unit.y = unit.original_y - 400 + fall_progress * 400  # Fall from 400 up

                    if fall_progress >= 1.0:  # Impact ground
                        unit.pry_phase = "impact"
                        unit.pry_timer = 0
                        unit.y = unit.original_y

                        # SCREEN SHAKE
                        self.screen_shake_intensity = 12
                        self.screen_shake_duration = 0.4

                        # Impact dust cloud
                        self.particle_emitter.emit_burst(unit.x, unit.y, (150, 130, 100), 30)

                        # Primary damage
                        damage = 6
                        unit.take_damage(damage)
                        self.floating_texts.append(
                            FloatingText(unit.x, unit.y - 20, f"-{damage}", COLOR_DAMAGE)
                        )

                        # Mark adjacent targets for delayed debris splash
                        if hasattr(unit, 'pry_adjacent_targets'):
                            unit.pry_splash_phase = "delay"
                            unit.pry_splash_timer = 0

                elif unit.pry_phase == "impact":
                    # Squash effect on impact
                    if unit.pry_timer < 0.15:
                        squash = 1.0 - (unit.pry_timer / 0.15) * 0.3
                        unit.pry_stretch_y = squash
                    else:
                        # End animation
                        unit.pry_phase = None
                        unit.pry_stretch_y = 1.0

            # Handle delayed splash damage phase
            if hasattr(unit, 'pry_splash_phase') and unit.pry_splash_phase:
                unit.pry_splash_timer += delta_time

                if unit.pry_splash_phase == "delay":
                    # Delay before debris falls
                    if unit.pry_splash_timer >= 0.3:  # 0.3s delay
                        unit.pry_splash_phase = "raining"
                        unit.pry_splash_timer = 0

                        # Create falling debris from ceiling for each adjacent target
                        if hasattr(unit, 'pry_adjacent_targets'):
                            for adj_unit in unit.pry_adjacent_targets:
                                # Mark adjacent unit for incoming debris
                                adj_unit.pry_debris_incoming = True
                                adj_unit.pry_debris_timer = 0
                                adj_unit.pry_debris_hit_count = 0  # Track how many debris have hit

                                # Spawn debris at top of screen above adjacent unit
                                for _ in range(8):
                                    # Start debris from ceiling
                                    start_x = adj_unit.x + random.uniform(-30, 30)
                                    start_y = 0  # Top of screen
                                    vx = random.uniform(-20, 20)
                                    vy = random.uniform(200, 300)  # Fast downward
                                    size = random.uniform(5, 10)
                                    debris = DebrisParticle(start_x, start_y, vx, vy, size, (120, 100, 80), target_unit=adj_unit)
                                    debris.lifetime = 2.0  # Longer lifetime
                                    self.debris_particles.append(debris)

                elif unit.pry_splash_phase == "raining":
                    # Check if all debris has hit targets or timeout
                    all_debris_hit = True
                    if hasattr(unit, 'pry_adjacent_targets'):
                        for adj_unit in unit.pry_adjacent_targets:
                            # Check if this unit has been hit by debris
                            if not hasattr(adj_unit, 'pry_debris_hit_count') or adj_unit.pry_debris_hit_count == 0:
                                all_debris_hit = False
                                break

                    # End after debris hits or 1 second timeout
                    if all_debris_hit or unit.pry_splash_timer >= 1.0:
                        # End splash phase
                        unit.pry_splash_phase = None

        # Update projectiles
        for projectile in self.projectiles[:]:
            still_active = projectile.update(delta_time)
            if not still_active:
                self.handle_judgement_impact(projectile)
                self.projectiles.remove(projectile)

        # Update lightning bolts
        self.lightning_bolts = [bolt for bolt in self.lightning_bolts if bolt.update(delta_time)]

        # Update cross beams (Autoclave)
        self.cross_beams = [beam for beam in self.cross_beams if beam.update(delta_time)]

        # Update jaw clamps (Mandible Foreman)
        remaining_clamps = []
        for jaw_clamp in self.jaw_clamps:
            jaw_clamp.update(delta_time)

            # Apply damage when jaws reach "clamped" phase
            if jaw_clamp.phase == "clamped" and hasattr(jaw_clamp, 'damage_target'):
                # Only apply damage once
                if not hasattr(jaw_clamp, 'damage_applied'):
                    target = jaw_clamp.damage_target
                    if target and target.hp > 0:
                        damage = random.randint(4, 6)
                        target.take_damage(damage)
                        self.floating_texts.append(
                            FloatingText(target.x, target.y - 20, f"-{damage}", COLOR_DAMAGE)
                        )

                        # Massive crushing impact burst
                        self.particle_emitter.emit_burst(target.x, target.y, (255, 220, 150), 40)

                        # Metallic impact particles (radial)
                        for i in range(25):
                            angle = (i / 25) * 2 * math.pi
                            speed = random.uniform(100, 180)
                            particle = Particle(
                                target.x, target.y,
                                math.cos(angle) * speed,
                                math.sin(angle) * speed,
                                (180, 160, 140), random.uniform(4, 8), 0.5
                            )
                            self.particle_emitter.particles.append(particle)

                        # Heavy shake
                        target.shake_intensity = 14
                        self.screen_shake_intensity = 10
                        self.screen_shake_duration = 0.25

                        jaw_clamp.damage_applied = True

            # Grinding sparks, pressure particles, and target vibration during clamped phase
            if jaw_clamp.phase == "clamped" and hasattr(jaw_clamp, 'damage_target'):
                target = jaw_clamp.damage_target

                # Apply grinding vibration to target
                if hasattr(target, 'original_x'):
                    vibration_x = math.sin(jaw_clamp.timer * 100) * 4
                    vibration_y = math.cos(jaw_clamp.timer * 100) * 4
                    target.x = target.original_x + vibration_x
                    target.y = target.original_y + vibration_y

                # Metal grinding sparks
                if random.random() < 0.4:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 120)
                    particle = Particle(
                        jaw_clamp.target_x + random.uniform(-15, 15),
                        jaw_clamp.target_y + random.uniform(-15, 15),
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        (255, 240, 100), random.uniform(2, 4), 0.3
                    )
                    self.particle_emitter.particles.append(particle)

                # Crushing pressure particles
                if random.random() < 0.5:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(30, 70)
                    particle = Particle(
                        jaw_clamp.target_x,
                        jaw_clamp.target_y,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        (200, 180, 150), random.uniform(2, 5), 0.4
                    )
                    self.particle_emitter.particles.append(particle)

            # Reset target position when releasing
            if jaw_clamp.phase == "releasing" and hasattr(jaw_clamp, 'damage_target'):
                target = jaw_clamp.damage_target
                if hasattr(target, 'original_x'):
                    target.x = target.original_x
                    target.y = target.original_y

            # Keep clamp if still active
            if jaw_clamp.active:
                remaining_clamps.append(jaw_clamp)
        self.jaw_clamps = remaining_clamps

        # Update Pedestal Strikes (POTPOURRIST melee)
        remaining_strikes = []
        for strike in self.pedestal_strikes:
            strike.update(delta_time)

            # Display damage number when damage is applied
            if strike.damage_applied and not hasattr(strike, 'damage_displayed'):
                if strike.target and strike.target.hp >= 0:
                    self.floating_texts.append(
                        FloatingText(strike.target_x, strike.target_y - 20, "-4", COLOR_DAMAGE)
                    )
                strike.damage_displayed = True

            # Keep strike if still active
            if strike.active:
                remaining_strikes.append(strike)
        self.pedestal_strikes = remaining_strikes

        # Update Infuse Effects (POTPOURRIST INFUSE skill)
        remaining_infuse = []
        for infuse in self.infuse_effects:
            infuse.update(delta_time)
            if infuse.active:
                remaining_infuse.append(infuse)

        # Update Demilune Swings (POTPOURRIST)
        for demilune in self.demilune_swings[:]:
            # Check if any new targets were hit this frame
            if hasattr(demilune, 'damage_pending') and demilune.damage_pending:
                for target in demilune.targets:
                    if id(target) in demilune.targets_hit:
                        # Apply damage and floating text when target is first hit
                        if not hasattr(target, 'demilune_damage_applied'):
                            target.take_damage(demilune.damage_amount)
                            self.floating_texts.append(
                                FloatingText(target.x, target.y - 30, f"-{demilune.damage_amount}", demilune.damage_color)
                            )
                            target.demilune_damage_applied = True

            if not demilune.update(delta_time):
                # Clean up damage tracking flags when animation ends
                if hasattr(demilune, 'targets'):
                    for target in demilune.targets:
                        if hasattr(target, 'demilune_damage_applied'):
                            delattr(target, 'demilune_damage_applied')
                self.demilune_swings.remove(demilune)
        self.infuse_effects = remaining_infuse

        # Update Lunacy Effects (POTPOURRIST)
        for lunacy in self.lunacy_effects[:]:
            if not lunacy.update(delta_time):
                self.lunacy_effects.remove(lunacy)

        # Update Granite Geas Effects (POTPOURRIST)
        for geas in self.granite_geas_effects[:]:
            if not geas.update(delta_time):
                self.granite_geas_effects.remove(geas)

        # Update Geas Break Heals (POTPOURRIST)
        for heal in self.geas_break_heals[:]:
            if not heal.update(delta_time):
                self.geas_break_heals.remove(heal)
            # Apply screen shake from heal effect
            if heal.screen_shake_intensity > 0:
                self.screen_shake_intensity = max(self.screen_shake_intensity, heal.screen_shake_intensity)
                self.screen_shake_duration = max(self.screen_shake_duration, heal.screen_shake_duration)

        # Update Melange Eminence effects (POTPOURRIST)
        for melange in self.melange_eminence_effects[:]:
            if not melange.update(delta_time):
                self.melange_eminence_effects.remove(melange)

        # Update Jawline networks (MANDIBLE FOREMAN JAWLINE skill)
        remaining_jawlines = []
        for jawline in self.jawline_networks:
            jawline.update(delta_time)

            # Apply damage when jaws snap shut
            if jawline.phase == "snapping" and jawline.damage_applied and not hasattr(jawline, 'damage_dealt'):
                for target in jawline.damage_targets:
                    if target.hp > 0:
                        damage = 4
                        target.take_damage(damage)
                        self.floating_texts.append(
                            FloatingText(target.x, target.y - 20, f"-{damage}", COLOR_DAMAGE)
                        )

                        # Major impact burst at each trapped enemy
                        self.particle_emitter.emit_burst(target.x, target.y, (255, 102, 0), 30)

                        # Metallic impact particles radiating outward
                        for i in range(15):
                            angle = (i / 15) * 2 * math.pi
                            speed = random.uniform(80, 150)
                            particle = Particle(
                                target.x, target.y,
                                math.cos(angle) * speed,
                                math.sin(angle) * speed,
                                (255, 150, 50), random.uniform(3, 6), 0.4
                            )
                            self.particle_emitter.particles.append(particle)

                        # Teeth impact sparks (golden/white)
                        for _ in range(10):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(100, 200)
                            particle = Particle(
                                target.x, target.y,
                                math.cos(angle) * speed,
                                math.sin(angle) * speed,
                                (255, 240, 150), random.uniform(2, 4), 0.3
                            )
                            self.particle_emitter.particles.append(particle)

                        # Heavy shake the unit
                        target.shake_intensity = 12

                        # Compression impact animation - unit gets squished by trap
                        target.jawline_impact_phase = "compression"
                        target.jawline_impact_timer = 0
                        if not hasattr(target, 'pry_stretch_y'):
                            target.pry_stretch_y = 1.0

                # Mark damage as dealt to prevent repeated application
                jawline.damage_dealt = True

                # Strong screen shake when all traps snap shut
                self.screen_shake_intensity = 10
                self.screen_shake_duration = 0.3

            # Metal snapping sounds (sparks during snap phase)
            if jawline.phase == "snapping":
                for trap in jawline.trap_positions:
                    if trap['deploy_progress'] >= 1.0 and random.random() < 0.3:
                        # Sparks from each trap snapping shut
                        trap_x = jawline.center_x + (trap['x'] - jawline.center_x)
                        trap_y = jawline.center_y + (trap['y'] - jawline.center_y)
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(40, 80)
                        particle = Particle(
                            trap_x, trap_y,
                            math.cos(angle) * speed,
                            math.sin(angle) * speed,
                            (255, 200, 100), random.uniform(2, 4), 0.25
                        )
                        self.particle_emitter.particles.append(particle)

            # Apply vibration/grinding to trapped units during active phase
            if jawline.phase == "active":
                for target in jawline.damage_targets:
                    if target.hp > 0 and hasattr(target, 'original_x'):
                        # Violent vibration from trap grinding
                        vibration_x = math.sin(jawline.timer * 100) * 3
                        vibration_y = math.cos(jawline.timer * 100) * 3
                        target.x = target.original_x + vibration_x
                        target.y = target.original_y + vibration_y

                # Pulsing orange particles during active phase
                if random.random() < 0.15:
                    # Random trap position
                    trap = random.choice(jawline.trap_positions)
                    trap_x = trap['x']
                    trap_y = trap['y']
                    # Small orange glow particles
                    particle = Particle(
                        trap_x + random.uniform(-15, 15),
                        trap_y + random.uniform(-15, 15),
                        random.uniform(-20, 20),
                        random.uniform(-20, 20),
                        (255, 150, 0), random.uniform(2, 3), 0.4
                    )
                    self.particle_emitter.particles.append(particle)

            # Reset target positions when fading
            if jawline.phase == "fading" and jawline.timer < 0.05:  # Once at start of fade
                for target in jawline.damage_targets:
                    if hasattr(target, 'original_x'):
                        target.x = target.original_x
                        target.y = target.original_y

            # Keep jawline if still active
            if jawline.active:
                remaining_jawlines.append(jawline)
        self.jawline_networks = remaining_jawlines

        # Update Expedite rushes (MANDIBLE FOREMAN EXPEDITE skill)
        remaining_rushes = []
        for rush in self.expedite_rushes:
            rush.update(delta_time)

            # Apply damage and trap when impact occurs
            if rush.phase == "impact" and not rush.damage_applied:
                target = rush.target_unit
                if target and target.hp > 0:
                    damage = 6
                    target.take_damage(damage)
                    self.floating_texts.append(
                        FloatingText(target.x, target.y - 20, f"-{damage}", COLOR_DAMAGE)
                    )

                    # Impact burst at target
                    self.particle_emitter.emit_burst(target.x, target.y, (255, 100, 100), 30)

                    # Create jaw trap at target position
                    jaw_clamp = JawClamp(target.x, target.y)
                    self.jaw_clamps.append(jaw_clamp)
                    jaw_clamp.damage_target = None  # Don't apply damage again - already dealt by rush

                    # Shake effects
                    target.shake_intensity = 10
                    self.screen_shake_intensity = 8
                    self.screen_shake_duration = 0.25

                    rush.damage_applied = True

            # Keep rush if still active
            if rush.active:
                remaining_rushes.append(rush)
        self.expedite_rushes = remaining_rushes

        # Update Viseroy traps (grinding chewing animation)
        remaining_traps = []
        for trap in self.viseroy_traps:
            trap.update(delta_time)

            # Apply damage when trap transitions to grinding phase (single tick)
            if trap.phase == "grinding" and not trap.damage_applied:
                if hasattr(trap, 'damage_target'):
                    target = trap.damage_target
                    if target.hp > 0:
                        damage = random.randint(2, 4)
                        target.take_damage(damage)
                        self.floating_texts.append(
                            FloatingText(target.x, target.y - 20, f"-{damage}", COLOR_DAMAGE)
                        )
                        trap.damage_applied = True

            # Grinding particles during chewing phase
            if trap.phase == "grinding" or trap.phase == "clamped":
                # Violent grinding sparks (less frequent when fully clamped)
                spark_chance = 0.5 if trap.phase == "grinding" else 0.15
                if random.random() < spark_chance:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(60, 140)
                    particle = Particle(
                        trap.target_x + random.uniform(-12, 12),
                        trap.target_y + random.uniform(-12, 12),
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        (255, 240, 100), random.uniform(2, 5), 0.35
                    )
                    self.particle_emitter.particles.append(particle)

                # Crushed material particles (only during grinding)
                if trap.phase == "grinding" and random.random() < 0.4:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(40, 90)
                    particle = Particle(
                        trap.target_x,
                        trap.target_y,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        (180, 160, 140), random.uniform(2, 4), 0.5
                    )
                    self.particle_emitter.particles.append(particle)

            # Target vibration during grinding and clamped phases
            if (trap.phase == "grinding" or trap.phase == "clamped") and hasattr(trap, 'damage_target'):
                if hasattr(trap.damage_target, 'original_x'):
                    target = trap.damage_target
                    if trap.phase == "grinding":
                        # More intense vibration during grinding
                        vibration_x = math.sin(trap.timer * 120) * 5
                        vibration_y = math.cos(trap.timer * 120) * 5
                    else:  # clamped
                        # Subtle persistent vibration when clamped
                        vibration_x = math.sin(trap.timer * 80) * 2
                        vibration_y = math.cos(trap.timer * 80) * 2
                    target.x = target.original_x + vibration_x
                    target.y = target.original_y + vibration_y

            # Reset target position when fading ends
            if trap.phase == "fading" and hasattr(trap, 'damage_target'):
                target = trap.damage_target
                if hasattr(target, 'original_x'):
                    target.x = target.original_x
                    target.y = target.original_y

            # Keep trap if still active
            if trap.active:
                remaining_traps.append(trap)
        self.viseroy_traps = remaining_traps

        # Update Viseroy releases (jaws opening animation)
        remaining_releases = []
        for release in self.viseroy_releases:
            release.update(delta_time)

            # Release particles during opening phase
            if release.phase == "opening":
                # Mechanical steam/pressure release particles
                if random.random() < 0.4:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(30, 80)
                    particle = Particle(
                        release.target_x + random.uniform(-15, 15),
                        release.target_y + random.uniform(-15, 15),
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        (200, 200, 210), random.uniform(2, 4), 0.4
                    )
                    self.particle_emitter.particles.append(particle)

            # Reset target position when animation ends
            if not release.active and hasattr(release, 'damage_target'):
                target = release.damage_target
                if hasattr(target, 'original_x'):
                    target.x = target.original_x
                    target.y = target.original_y

            # Keep release if still active
            if release.active:
                remaining_releases.append(release)
        self.viseroy_releases = remaining_releases

        # Update site inspections (laser scanning)
        remaining_scans = []
        for scan in self.site_inspections:
            scan.update(delta_time)

            # Scanning particles
            if scan.phase == "scanning":
                # Laser sweep particles
                if random.random() < 0.3:
                    # Calculate current sweep position
                    sweep_y = scan.center_y - scan.grid_size * 1.5 + scan.scan_progress * (scan.grid_size * 3)
                    sweep_x = scan.center_x - scan.grid_size * 1.5 + scan.scan_progress * (scan.grid_size * 3)

                    # Particles at sweep intersection
                    particle = Particle(
                        sweep_x + random.uniform(-5, 5),
                        sweep_y + random.uniform(-5, 5),
                        random.uniform(-20, 20),
                        random.uniform(-20, 20),
                        (255, 200, 100), random.uniform(1, 3), 0.3
                    )
                    self.particle_emitter.particles.append(particle)

            # Keep scan if still active
            if scan.active:
                remaining_scans.append(scan)
        self.site_inspections = remaining_scans

        # Update site inspection buffs
        remaining_buffs = []
        for buff in self.site_inspection_buffs:
            buff.update(delta_time)

            # Keep buff if still active
            if buff.active:
                remaining_buffs.append(buff)
        self.site_inspection_buffs = remaining_buffs

        # Update debris particles with collision detection
        remaining_debris = []
        for debris in self.debris_particles:
            still_alive = debris.update(delta_time)
            if still_alive:
                # Check collision with target unit
                if debris.check_collision(self.units, self.particle_emitter):
                    # Debris hit the target - apply damage
                    if debris.target_unit and debris.target_unit.hp > 0:
                        # Only apply damage on first hit from each debris chunk
                        if not hasattr(debris, 'damage_applied'):
                            splash_damage = 3
                            debris.target_unit.take_damage(splash_damage)
                            self.floating_texts.append(
                                FloatingText(debris.target_unit.x, debris.target_unit.y - 20,
                                           f"-{splash_damage}", (255, 150, 100))
                            )
                            # Shake the unit
                            debris.target_unit.shake_intensity = 6

                            # Track that this unit was hit
                            if not hasattr(debris.target_unit, 'pry_debris_hit_count'):
                                debris.target_unit.pry_debris_hit_count = 0
                            debris.target_unit.pry_debris_hit_count += 1

                            debris.damage_applied = True
                    # Debris is removed after collision (lifetime set to 0)
                else:
                    remaining_debris.append(debris)
        self.debris_particles = remaining_debris

        # Update particles
        self.particle_emitter.update(delta_time)

        # Update floating texts
        self.floating_texts = [t for t in self.floating_texts if t.update(delta_time)]

    def handle_judgement_impact(self, projectile):
        """Handle all the impact effects when JUDGEMENT hits."""
        # Find the attacker and target
        glaiveman = None
        target = None
        forced_crit = False
        for unit in self.units:
            if hasattr(unit, 'judgement_pending') and unit.judgement_pending:
                glaiveman = unit
                target = unit.judgement_target
                unit.judgement_pending = False
                # Check if this was a forced critical hit
                if hasattr(unit, 'judgement_is_crit') and unit.judgement_is_crit:
                    forced_crit = True
                    unit.judgement_is_crit = False
                break

        if not target or not glaiveman:
            return

        # Screen shake
        self.screen_shake_intensity = 8
        self.screen_shake_duration = 0.3

        # Golden flash
        self.golden_flash_alpha = 255
        self.golden_flash_duration = 0.15

        # Impact burst
        self.particle_emitter.emit_burst(target.x, target.y, (255, 215, 0), 40)

        # Additional sparkles
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 250)
            self.particle_emitter.particles.append(
                Particle(target.x, target.y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        (255, 255, 200), random.uniform(3, 6), 0.5)
            )

        # Check if critical (either low HP or forced)
        is_critical = target.hp < target.max_hp * 0.3 or forced_crit
        damage = 8 if is_critical else 4

        # Cross decal and LIGHTNING on critical
        if is_critical:
            target.cross_decal_alpha = 255
            target.cross_decal_duration = 1.0

            # DIVINE LIGHTNING STRIKE!
            lightning = LightningBolt(target.x, target.y)
            self.lightning_bolts.append(lightning)

            # White screen flash for lightning
            self.golden_flash_alpha = 255
            self.golden_flash_duration = 0.2

            self.floating_texts.append(
                FloatingText(target.x, target.y - 40, "DIVINE JUDGMENT!", (255, 215, 0))
            )
            self.screen_shake_intensity = 15
            self.screen_shake_duration = 0.5

            # Extra electric particles
            for _ in range(30):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(150, 300)
                self.particle_emitter.particles.append(
                    Particle(target.x, target.y,
                            math.cos(angle) * speed, math.sin(angle) * speed,
                            (200, 220, 255), random.uniform(2, 5), 0.4)
                )

        # Apply damage
        target.take_damage(damage)
        self.floating_texts.append(
            FloatingText(target.x, target.y - 20, f"-{damage}", COLOR_DAMAGE)
        )

    def draw(self):
        """Render the scene."""
        # Apply screen shake offset
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake_intensity > 0:
            shake_offset_x = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_offset_y = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)

        # Create main surface with potential offset
        main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        main_surface.fill(COLOR_BG)

        # Draw grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = COLOR_GRID_DARK if (x + y) % 2 == 0 else COLOR_GRID_LIGHT
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(main_surface, color, rect)
                pygame.draw.rect(main_surface, (30, 34, 42), rect, 1)

        # Draw units
        for unit in self.units:
            # Save original sprite
            original_sprite = unit.sprite
            original_rect = unit.sprite_rect if unit.sprite else None

            # Apply wind-up rotation if active
            if hasattr(unit, 'wind_up_rotation') and unit.wind_up_rotation != 0 and unit.sprite:
                rotated = pygame.transform.rotate(unit.sprite, unit.wind_up_rotation)
                unit.sprite = rotated
                unit.sprite_rect = rotated.get_rect()

            # Apply PRY stretch/squash if active
            if hasattr(unit, 'pry_stretch_y') and unit.pry_stretch_y != 1.0 and unit.sprite:
                new_height = int(TILE_SIZE * unit.pry_stretch_y)
                new_width = int(TILE_SIZE * (2.0 - unit.pry_stretch_y))  # Inverse stretch horizontally
                stretched = pygame.transform.scale(unit.sprite, (new_width, new_height))
                unit.sprite = stretched
                unit.sprite_rect = stretched.get_rect()

            unit.draw(main_surface, self.small_font)

            # Restore original sprite
            if original_sprite:
                unit.sprite = original_sprite
                unit.sprite_rect = original_rect

            # Draw cross decal overlay on critical hits
            if hasattr(unit, 'cross_decal_alpha') and unit.cross_decal_alpha > 0:
                cross_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
                alpha = unit.cross_decal_alpha
                # Draw golden cross
                pygame.draw.line(cross_surf, (255, 215, 0, alpha),
                               (32, 10), (32, 54), 4)
                pygame.draw.line(cross_surf, (255, 215, 0, alpha),
                               (10, 32), (54, 32), 4)
                # Outer glow
                pygame.draw.line(cross_surf, (255, 235, 150, alpha // 2),
                               (32, 10), (32, 54), 6)
                pygame.draw.line(cross_surf, (255, 235, 150, alpha // 2),
                               (10, 32), (54, 32), 6)
                cross_rect = cross_surf.get_rect(center=(int(unit.x), int(unit.y)))
                main_surface.blit(cross_surf, cross_rect)

        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(main_surface)

        # Draw cross beams (Autoclave skill)
        for beam in self.cross_beams:
            beam.draw(main_surface)

        # Draw jaw clamps (Mandible Foreman)
        for jaw_clamp in self.jaw_clamps:
            jaw_clamp.draw(main_surface)

        # Draw Pedestal Strikes (POTPOURRIST)
        for strike in self.pedestal_strikes:
            strike.draw(main_surface)

        # Draw Infuse Effects (POTPOURRIST)
        for infuse in self.infuse_effects:
            infuse.draw(main_surface)

        # Draw Demilune Swings (POTPOURRIST)
        for demilune in self.demilune_swings:
            demilune.draw(main_surface)

        # Draw Lunacy Effects (POTPOURRIST)
        for lunacy in self.lunacy_effects:
            lunacy.draw(main_surface)

        # Draw Granite Geas Effects (POTPOURRIST)
        for geas in self.granite_geas_effects:
            geas.draw(main_surface)

        # Draw Geas Break Heals (POTPOURRIST)
        for heal in self.geas_break_heals:
            heal.draw(main_surface)

        # Draw Melange Eminence effects (POTPOURRIST)
        for melange in self.melange_eminence_effects:
            melange.draw(main_surface)

        # Draw Jawline networks (Mandible Foreman)
        for jawline in self.jawline_networks:
            jawline.draw(main_surface)

        # Draw Expedite rushes (Mandible Foreman)
        for rush in self.expedite_rushes:
            rush.draw(main_surface)

        # Draw Viseroy traps (Mandible Foreman)
        for trap in self.viseroy_traps:
            trap.draw(main_surface)

        # Draw Viseroy releases (Mandible Foreman)
        for release in self.viseroy_releases:
            release.draw(main_surface)

        # Draw site inspections (Mandible Foreman)
        for scan in self.site_inspections:
            scan.draw(main_surface)

        # Draw site inspection buffs (Mandible Foreman)
        for buff in self.site_inspection_buffs:
            buff.draw(main_surface)

        # Draw lightning bolts (on top of everything else)
        for lightning in self.lightning_bolts:
            lightning.draw(main_surface)

        # Draw debris particles (falling rocks)
        for debris in self.debris_particles:
            debris.draw(main_surface)

        # Draw particles
        self.particle_emitter.draw(main_surface)

        # Draw floating texts
        for text in self.floating_texts:
            text.draw(main_surface, self.font)

        # Apply golden flash overlay
        if hasattr(self, 'golden_flash_alpha') and self.golden_flash_alpha > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 215, 0, self.golden_flash_alpha // 4))
            main_surface.blit(flash_surf, (0, 0))

        # Blit main surface to screen with shake offset
        self.screen.blit(main_surface, (int(shake_offset_x), int(shake_offset_y)))

        # Draw UI (not affected by shake)
        self.draw_ui()

        pygame.display.flip()

    def draw_ui(self):
        """Draw UI overlay."""
        # Bottom panel
        panel_height = 140
        panel_surf = pygame.Surface((SCREEN_WIDTH, panel_height), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 180))
        self.screen.blit(panel_surf, (0, SCREEN_HEIGHT - panel_height))

        # Title
        title = self.title_font.render("Boneglaive - Modern Renderer Demo", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 10))

        # Instructions
        instructions = [
            "GLAIVEMAN's Skill Showcase:",
            "JUDGEMENT: Spinning glaive + lightning on crits",
            "PRY: Launch enemy up, slam down with debris",
            "",
            "Advanced Techniques:",
            "• Projectile sprites with motion blur",
            "• Sprite transformations (rotation, stretch/squash)",
            "• Screen shake & flash effects",
            "• Debris physics with rotation",
            "• Splash damage visualization",
            "",
            "Press SPACE to cast | ESC to exit"
        ]

        y = SCREEN_HEIGHT - panel_height + 10
        for line in instructions:
            text = self.small_font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (20, y))
            y += 16

        # Stats
        stats = [
            f"Particles: {len(self.particle_emitter.particles)}",
            f"Units: {len(self.units)}",
            f"FPS: {int(self.clock.get_fps())}"
        ]
        y = SCREEN_HEIGHT - panel_height + 10
        for stat in stats:
            text = self.small_font.render(stat, True, (255, 255, 100))
            self.screen.blit(text, (SCREEN_WIDTH - 150, y))
            y += 20

    def run(self):
        """Main game loop."""
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(delta_time)
            self.draw()

        pygame.quit()


def main():
    """Run the demo."""
    print("=" * 60)
    print("BONEGLAIVE MODERN RENDERER DEMO (Modular)")
    print("=" * 60)
    print()
    print("This demo shows what the game MIGHT look like with:")
    print("  - SVG sprite rendering")
    print("  - Particle effects for skills/attacks/healing")
    print("  - Smooth animations and movement")
    print("  - Z-layer rendering")
    print("  - Modern UI with transparency")
    print()
    print("Note: The colored circles would be replaced with actual SVG graphics.")
    print()
    print("Controls:")
    print("  SPACE - Trigger random action")
    print("  TAB   - Switch unit mode")
    print("  ESC   - Exit")
    print()

    demo = ModernRendererDemo()
    demo.run()


if __name__ == "__main__":
    main()
