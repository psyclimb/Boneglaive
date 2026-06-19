#!/usr/bin/env python3
"""
POTPOURRIST Animation Classes
Skill animations for the POTPOURRIST unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, COLOR_DAMAGE, COLOR_SKILL
from boneglaive.graphical.sound_helper import play_sound


class LunacyEffect:
    """
    Eclipse effect for units afflicted with Lunacy debuff.
    A crescent moon appears above the unit, eclipsing their strength.
    """
    def __init__(self, target_x, target_y, target_unit):
        self.target_x = target_x
        self.target_y = target_y
        self.target = target_unit

        self.phase = "appearing"  # appearing -> orbiting -> complete
        self.timer = 0
        self.active = True
        self.duration = 2.5  # Total effect duration

        # Moon/eclipse properties - centered on tile, not above unit
        self.orbit_angle = 0
        self.orbit_radius = 8
        self.eclipse_progress = 0
        self.pulse_phase = 0

        # Store original position for shudder effect
        if self.target:
            self.target.original_x = target_x
            self.target.original_y = target_y
            self.target.lunacy_shudder = True
            self.target.lunacy_shudder_intensity = 0

    def update(self, delta_time):
        """Update lunacy eclipse effect."""
        if not self.active:
            return False

        self.timer += delta_time

        # Slow pulsing effect
        self.pulse_phase += delta_time * 2

        # Apply shuddering to target unit
        if self.target and hasattr(self.target, 'lunacy_shudder'):
            if self.phase == "appearing":
                # Intense shudder during eclipse appearance
                shudder_freq = 25  # Fast shudder
                shudder_intensity = 3 * self.eclipse_progress  # Build up intensity
            elif self.phase == "orbiting":
                # Periodic shudder during orbit
                shudder_freq = 8  # Slower periodic shudder
                shudder_intensity = 2
            else:
                # Fading shudder
                shudder_freq = 15
                shudder_intensity = 1.5 * (1.0 - self.timer / 0.2)

            # Calculate shudder offset
            shudder_x = math.sin(self.timer * shudder_freq * math.pi) * shudder_intensity
            shudder_y = math.cos(self.timer * shudder_freq * math.pi * 1.3) * shudder_intensity

            # Apply to target
            self.target.x = self.target.original_x + shudder_x
            self.target.y = self.target.original_y + shudder_y
            self.target.lunacy_shudder_intensity = shudder_intensity

        if self.phase == "appearing":
            # Moon fades in and eclipse starts (0.8s)
            if self.timer < 0.8:
                self.eclipse_progress = self.timer / 0.8
            else:
                self.phase = "orbiting"
                self.timer = 0

        elif self.phase == "orbiting":
            # Moon orbits slowly, maintaining eclipse (1.5s)
            self.orbit_angle += delta_time * 2  # Slow rotation

            if self.timer >= 1.5:
                self.phase = "fading"
                self.timer = 0

        elif self.phase == "fading":
            # Eclipse fades out (0.2s)
            if self.timer >= 0.2:
                self.active = False
                # Reset target position
                if self.target and hasattr(self.target, 'lunacy_shudder'):
                    self.target.x = self.target.original_x
                    self.target.y = self.target.original_y
                    self.target.lunacy_shudder = False

        return self.active

    def draw(self, surface):
        """Draw the lunacy eclipse effect."""
        if not self.active:
            return

        # Calculate current position - centered on tile (follows target if it moves)
        if self.target:
            base_x = self.target.x
            base_y = self.target.y
        else:
            base_x = self.target_x
            base_y = self.target_y

        # Add subtle orbit motion around the tile center
        moon_x = base_x + math.cos(self.orbit_angle) * self.orbit_radius
        moon_y = base_y + math.sin(self.orbit_angle) * self.orbit_radius * 0.5

        # Calculate fade
        if self.phase == "appearing":
            fade = self.eclipse_progress
        elif self.phase == "fading":
            fade = 1.0 - (self.timer / 0.2)
        else:
            fade = 1.0

        # Pulsing effect (subtle)
        pulse = 0.9 + math.sin(self.pulse_phase) * 0.1
        fade *= pulse

        # Create surface for the eclipse effect
        effect_size = 80
        eclipse_surf = pygame.Surface((effect_size, effect_size), pygame.SRCALPHA)
        center = effect_size // 2

        # Draw dark aura around the unit (weakening effect)
        aura_alpha = int(40 * fade)
        if aura_alpha > 0:
            aura_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (60, 50, 80, aura_alpha), (50, 50), 50)
            pygame.draw.circle(aura_surf, (40, 30, 60, aura_alpha // 2), (50, 50), 60)
            surface.blit(aura_surf, (int(base_x - 50), int(base_y - 50)))

        # Draw full moon (light gray/white)
        moon_alpha = int(180 * fade)
        if moon_alpha > 0:
            pygame.draw.circle(eclipse_surf, (220, 220, 240, moon_alpha), (center, center), 16)
            # Moon glow
            pygame.draw.circle(eclipse_surf, (200, 200, 220, moon_alpha // 2), (center, center), 20)

        # Draw eclipse shadow (crescent - the eclipsing body)
        # This creates the "moon eclipsing strength" visual
        shadow_alpha = int(200 * fade * self.eclipse_progress)
        if shadow_alpha > 0:
            # Create shadow that slides across the moon
            eclipse_offset = int(10 * math.sin(self.eclipse_progress * math.pi))

            # Dark circular shadow
            pygame.draw.circle(eclipse_surf, (20, 15, 30, shadow_alpha),
                             (center + eclipse_offset + 8, center), 16)

            # Darker core shadow
            pygame.draw.circle(eclipse_surf, (10, 5, 15, shadow_alpha),
                             (center + eclipse_offset + 8, center), 12)

        # Draw crescent moon symbol (open side indicates weakening)
        crescent_alpha = int(220 * fade)
        if crescent_alpha > 0:
            # Outer crescent arc
            crescent_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(crescent_surf, (240, 230, 200, crescent_alpha), (20, 20), 14, 3)

            # Draw "(" shape by covering the right side
            pygame.draw.circle(crescent_surf, (240, 230, 200, crescent_alpha), (26, 20), 14, 3)

            eclipse_surf.blit(crescent_surf, (center - 20, center - 20))

        # Sparkle particles (fading strength)
        if self.phase == "orbiting":
            for i in range(4):
                angle = (self.orbit_angle * 2) + (i * math.pi / 2)
                sparkle_dist = 25 + math.sin(self.pulse_phase + i) * 3
                sx = center + math.cos(angle) * sparkle_dist
                sy = center + math.sin(angle) * sparkle_dist
                sparkle_alpha = int(100 * fade * pulse)

                if sparkle_alpha > 0:
                    pygame.draw.circle(eclipse_surf, (180, 170, 200, sparkle_alpha),
                                     (int(sx), int(sy)), 2)

        # Blit to surface
        surface.blit(eclipse_surf, (int(moon_x - center), int(moon_y - center)))

class PedestalStrike:
    """Impact effects for POTPOURRIST's pedestal strike (shockwave, debris, crater)."""
    def __init__(self, target_x, target_y, target_unit):
        self.target_x = target_x
        self.target_y = target_y
        self.target = target_unit

        self.phase = "impact"  # impact -> shockwave -> crater -> complete
        self.timer = 0
        self.active = True

        # Impact effects
        self.shockwave_radius = 0
        self.crater_particles = []
        self.dust_particles = []
        self.damage_applied = False

    def update(self, delta_time):
        """Update impact effects."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "impact":
            # Impact moment with compression (0.15s)
            if self.timer < 0.15:
                # Target compression
                if self.target:
                    progress = self.timer / 0.15
                    if progress < 0.5:
                        # Compress
                        self.target.pry_stretch_y = 1.0 - (progress * 2 * 0.3)  # Squash to 0.7
                    else:
                        # Rebound
                        rebound = (progress - 0.5) * 2
                        self.target.pry_stretch_y = 0.7 + (rebound * 0.3)

                # Apply damage at start of impact
                if not self.damage_applied:
                    self.damage_applied = True
                    if self.target:
                        self.target.take_damage(4)

            else:
                self.phase = "shockwave"
                self.timer = 0
                # Reset target stretch
                if self.target:
                    self.target.pry_stretch_y = 1.0

        elif self.phase == "shockwave":
            # Expanding shockwave and debris (0.5s)
            if self.timer < 0.5:
                progress = self.timer / 0.5
                self.shockwave_radius = progress * 80  # Expand to 80px

                # Spawn debris particles
                if int(self.timer * 100) % 5 == 0 and len(self.crater_particles) < 40:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(80, 200)
                    self.crater_particles.append({
                        'x': self.target_x,
                        'y': self.target_y,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed - 100,  # Initial upward bias
                        'lifetime': random.uniform(0.4, 0.8),
                        'size': random.uniform(2, 6),
                        'color': (120, 100, 80),  # Brown rock
                        'gravity': 400
                    })

                # Gray dust cloud
                if int(self.timer * 100) % 3 == 0 and len(self.dust_particles) < 30:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(30, 80)
                    self.dust_particles.append({
                        'x': self.target_x,
                        'y': self.target_y,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed - 50,
                        'lifetime': random.uniform(0.6, 1.0),
                        'size': random.uniform(4, 10),
                        'color': (180, 180, 180)
                    })
            else:
                self.phase = "crater"
                self.timer = 0

        elif self.phase == "crater":
            # Crater settling (0.4s)
            if self.timer < 0.4:
                # Particles settle
                pass
            else:
                self.phase = "complete"
                self.active = False

        # Update particles
        for particle in self.crater_particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['vy'] += particle.get('gravity', 0) * delta_time
            particle['lifetime'] -= delta_time
            if particle['lifetime'] <= 0:
                self.crater_particles.remove(particle)

        for particle in self.dust_particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['lifetime'] -= delta_time
            if particle['lifetime'] <= 0:
                self.dust_particles.remove(particle)

        return self.active

    def draw(self, surface):
        """Draw the impact effects."""
        if not self.active and self.phase == "complete":
            return

        # Draw shockwave ring
        if self.phase == "shockwave" or self.phase == "crater":
            alpha = int(255 * (1.0 - (self.shockwave_radius / 80)))
            if alpha > 0:
                shockwave_surf = pygame.Surface((int(self.shockwave_radius * 2), int(self.shockwave_radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(shockwave_surf, (200, 100, 200, alpha),
                                 (int(self.shockwave_radius), int(self.shockwave_radius)),
                                 int(self.shockwave_radius), 4)
                shockwave_rect = shockwave_surf.get_rect(center=(int(self.target_x), int(self.target_y)))
                surface.blit(shockwave_surf, shockwave_rect)

        # Draw crater particles (rock debris)
        for particle in self.crater_particles:
            alpha = int(255 * (particle['lifetime'] / 0.8))
            if alpha > 0:
                color = (*particle['color'], alpha)
                particle_surf = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color,
                                 (int(particle['size']), int(particle['size'])),
                                 int(particle['size']))
                surface.blit(particle_surf, (int(particle['x'] - particle['size']), int(particle['y'] - particle['size'])))

        # Draw dust particles
        for particle in self.dust_particles:
            alpha = int(150 * (particle['lifetime'] / 1.0))
            if alpha > 0:
                color = (*particle['color'], alpha)
                particle_surf = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color,
                                 (int(particle['size']), int(particle['size'])),
                                 int(particle['size']))
                surface.blit(particle_surf, (int(particle['x'] - particle['size']), int(particle['y'] - particle['size'])))


class InfuseEffect:
    """INFUSE - POTPOURRIST creates aromatic potpourri with swirling petals and fragrance."""
    def __init__(self, caster_x, caster_y, caster_unit):
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.caster = caster_unit

        self.phase = "gathering"  # gathering -> swirling -> infusion -> complete
        self.timer = 0
        self.active = True

        # Visual effects
        self.petal_particles = []
        self.fragrance_waves = []
        self.spiral_angle = 0
        self.core_glow_radius = 0

        # Petals beginning to gather
        play_sound("infuse_cast")

    def update(self, delta_time):
        """Update infuse animation."""
        if not self.active:
            return False

        self.timer += delta_time
        self.spiral_angle += delta_time * 360  # Full rotation per second

        if self.phase == "gathering":
            # Petals and particles gather inward (0.5s)
            if self.timer < 0.5:
                progress = self.timer / 0.5

                # Spawn incoming petal particles
                if int(self.timer * 100) % 8 == 0 and len(self.petal_particles) < 30:
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(60, 100)
                    start_x = self.caster_x + math.cos(angle) * distance
                    start_y = self.caster_y + math.sin(angle) * distance

                    # Petals move inward in a spiral - tropical flower colors from shirt
                    self.petal_particles.append({
                        'x': start_x,
                        'y': start_y,
                        'target_x': self.caster_x,
                        'target_y': self.caster_y,
                        'speed': random.uniform(150, 250),
                        'spiral_offset': random.uniform(0, 2 * math.pi),
                        'color': random.choice([
                            (255, 215, 0),    # Gold #ffd700
                            (255, 105, 180),  # Hot pink #ff69b4
                            (255, 99, 71),    # Tomato #ff6347
                            (255, 165, 0),    # Orange #ffa500
                            (147, 112, 219),  # Medium purple #9370db
                            (186, 85, 211),   # Medium orchid #ba55d3
                            (0, 206, 209),    # Dark turquoise #00ced1
                            (255, 20, 147)    # Deep pink #ff1493
                        ]),
                        'size': random.uniform(3, 6),
                        'lifetime': 2.0
                    })

                # Growing core glow
                self.core_glow_radius = progress * 20
            else:
                self.phase = "swirling"
                self.timer = 0

        elif self.phase == "swirling":
            # Petals swirl around caster (0.6s)
            if self.timer < 0.6:
                # All petals orbit in a vortex
                for petal in self.petal_particles:
                    angle_to_center = math.atan2(self.caster_y - petal['y'], self.caster_x - petal['x'])
                    distance = math.sqrt((petal['x'] - self.caster_x)**2 + (petal['y'] - self.caster_y)**2)

                    # Spiral inward while orbiting
                    orbit_angle = angle_to_center + petal['spiral_offset'] + self.spiral_angle * 0.02
                    new_distance = max(10, distance - delta_time * 60)

                    petal['x'] = self.caster_x + math.cos(orbit_angle) * new_distance
                    petal['y'] = self.caster_y + math.sin(orbit_angle) * new_distance

                # Core glow pulses
                self.core_glow_radius = 20 + math.sin(self.timer * 10) * 5
            else:
                self.phase = "infusion"
                self.timer = 0
                play_sound("infuse_burst")

        elif self.phase == "infusion":
            # Petals burst outward and fade, potpourri absorbed (0.5s)
            if self.timer < 0.5:
                progress = self.timer / 0.5

                # Petals expand outward and fade
                for petal in self.petal_particles:
                    angle_from_center = math.atan2(petal['y'] - self.caster_y, petal['x'] - self.caster_x)
                    speed = 100 * (1.0 + progress)
                    petal['x'] += math.cos(angle_from_center) * speed * delta_time
                    petal['y'] += math.sin(angle_from_center) * speed * delta_time
                    petal['lifetime'] -= delta_time * 3

                # Spawn fragrance waves
                if int(self.timer * 100) % 15 == 0 and len(self.fragrance_waves) < 5:
                    self.fragrance_waves.append({
                        'radius': 0,
                        'max_radius': random.uniform(40, 60),
                        'lifetime': 0.8,
                        'color': (220, 20, 60)  # Crimson #dc143c from shirt
                    })

                # Core flash
                self.core_glow_radius = 20 + (1.0 - progress) * 30

                # Caster glows
                if self.caster:
                    self.caster.pry_stretch_y = 1.0 + (math.sin(progress * math.pi) * 0.05)
            else:
                self.phase = "complete"
                self.active = False
                if self.caster:
                    self.caster.pry_stretch_y = 1.0
                    # Activate sustained potpourri aura
                    self.caster.potpourri_aura_active = True
                    self.caster.potpourri_aura_timer = 0

        # Update petal particles
        for petal in self.petal_particles[:]:
            petal['lifetime'] -= delta_time
            if petal['lifetime'] <= 0:
                self.petal_particles.remove(petal)

        # Update fragrance waves
        for wave in self.fragrance_waves[:]:
            wave['radius'] += delta_time * 80
            wave['lifetime'] -= delta_time
            if wave['lifetime'] <= 0:
                self.fragrance_waves.remove(wave)

        return self.active

    def draw(self, surface):
        """Draw the infuse effect."""
        if not self.active and self.phase == "complete":
            return

        # Draw fragrance waves (expanding rings)
        for wave in self.fragrance_waves:
            alpha = int(150 * (wave['lifetime'] / 0.8))
            if alpha > 0 and wave['radius'] > 0:
                wave_surf = pygame.Surface((int(wave['radius'] * 2), int(wave['radius'] * 2)), pygame.SRCALPHA)
                color = (*wave['color'], alpha)
                pygame.draw.circle(wave_surf, color,
                                 (int(wave['radius']), int(wave['radius'])),
                                 int(wave['radius']), 2)
                wave_rect = wave_surf.get_rect(center=(int(self.caster_x), int(self.caster_y)))
                surface.blit(wave_surf, wave_rect)

        # Draw core glow - crimson red from shirt
        if self.core_glow_radius > 0:
            for i in range(3):
                radius = self.core_glow_radius + i * 8
                alpha = int(100 - i * 30)
                if alpha > 0:
                    glow_surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (220, 20, 60, alpha),  # Crimson #dc143c
                                     (int(radius), int(radius)), int(radius))
                    glow_rect = glow_surf.get_rect(center=(int(self.caster_x), int(self.caster_y)))
                    surface.blit(glow_surf, glow_rect)

        # Draw petal particles
        for petal in self.petal_particles:
            if petal['lifetime'] > 0:
                alpha = int(255 * min(1.0, petal['lifetime']))
                if alpha > 0:
                    color = (*petal['color'], alpha)
                    petal_surf = pygame.Surface((int(petal['size'] * 2), int(petal['size'] * 2)), pygame.SRCALPHA)

                    # Draw petal as a rounded shape
                    pygame.draw.circle(petal_surf, color,
                                     (int(petal['size']), int(petal['size'])),
                                     int(petal['size']))
                    # Add highlight
                    pygame.draw.circle(petal_surf, (255, 255, 255, alpha // 2),
                                     (int(petal['size'] * 0.7), int(petal['size'] * 0.7)),
                                     int(petal['size'] * 0.4))

                    surface.blit(petal_surf, (int(petal['x'] - petal['size']), int(petal['y'] - petal['size'])))




class GraniteGeasEffect:
    """
    GRANITE GEAS - Strike enemy with pedestal and mark with aromatic binding.
    Shows oil mark and magical chains/runes on target.
    """
    def __init__(self, target_x, target_y, target_unit, infused=False):
        self.target_x = target_x
        self.target_y = target_y
        self.target = target_unit
        self.infused = infused

        self.phase = "strike"  # strike -> mark_appear -> binding -> complete

        # Pedestal strike landing on target
        play_sound("granite_geas_strike")

        self.timer = 0
        self.active = True

        # Strike properties
        self.strike_progress = 0
        self.impact_flash = 0

        # Geas mark properties
        self.mark_alpha = 0
        self.mark_rotation = 0
        self.chain_segments = []
        self.rune_pulse = 0

        # Oil drip particles (aromatic oils)
        self.oil_drips = []

        # Ethereal fume runes (floating mystical symbols)
        self.fume_runes = []

    def update(self, delta_time):
        """Update granite geas effect."""
        if not self.active:
            return False

        self.timer += delta_time
        self.rune_pulse += delta_time * 3

        if self.phase == "strike":
            # Quick pedestal strike (0.2s)
            if self.timer < 0.2:
                self.strike_progress = self.timer / 0.2

                # Impact flash at peak
                if self.strike_progress > 0.5 and self.impact_flash == 0:
                    self.impact_flash = 1.0
                    # Apply shake to target
                    if self.target:
                        self.target.shake_intensity = 10
            else:
                self.phase = "mark_appear"
                self.timer = 0

        elif self.phase == "mark_appear":
            # Aromatic oil mark appears (0.5s)
            if self.timer < 0.5:
                self.mark_alpha = self.timer / 0.5

                # Spawn oil drip particles
                if random.random() < 0.3:
                    angle = random.uniform(0, 2 * math.pi)
                    # Tropical flower colors for infused, gray/stone for normal
                    if self.infused:
                        drip_color = random.choice([
                            (255, 215, 0),    # Gold
                            (255, 105, 180),  # Hot pink
                            (255, 99, 71),    # Tomato
                            (255, 165, 0),    # Orange
                            (147, 112, 219),  # Medium purple
                            (186, 85, 211),   # Medium orchid
                            (0, 206, 209),    # Dark turquoise
                            (255, 20, 147)    # Deep pink
                        ])
                    else:
                        drip_color = random.choice([
                            (140, 140, 140),  # Gray
                            (160, 160, 160),  # Light gray
                            (120, 120, 120),  # Dark gray
                            (130, 130, 135)   # Blue-gray
                        ])

                    self.oil_drips.append({
                        'x': self.target_x + random.uniform(-15, 15),
                        'y': self.target_y - 20 + random.uniform(-10, 10),
                        'vx': math.cos(angle) * random.uniform(10, 30),
                        'vy': random.uniform(20, 50),  # Drips downward
                        'lifetime': random.uniform(0.8, 1.5),
                        'size': random.uniform(2, 4),
                        'color': drip_color,
                        'gravity': 100
                    })
            else:
                self.phase = "binding"
                self.timer = 0
                play_sound("granite_geas_bind")

        elif self.phase == "binding":
            # Show magical binding (1.5s for normal, 2.5s for infused)
            duration = 2.5 if self.infused else 1.5
            self.mark_rotation += delta_time * 90  # Slow rotation

            # Spawn ethereal fume runes floating upward
            if random.random() < 0.4:
                angle = random.uniform(0, 2 * math.pi)
                spawn_dist = random.uniform(15, 30)
                # Tropical flower colors for infused, gray/stone for normal
                if self.infused:
                    rune_color = random.choice([
                        (255, 215, 0),    # Gold
                        (255, 105, 180),  # Hot pink
                        (255, 99, 71),    # Tomato
                        (255, 165, 0),    # Orange
                        (147, 112, 219),  # Medium purple
                        (186, 85, 211),   # Medium orchid
                        (0, 206, 209),    # Dark turquoise
                        (255, 20, 147)    # Deep pink
                    ])
                else:
                    rune_color = random.choice([
                        (140, 140, 140),  # Gray
                        (160, 160, 160),  # Light gray
                        (120, 120, 120),  # Dark gray
                        (130, 130, 135)   # Blue-gray
                    ])

                self.fume_runes.append({
                    'x': self.target_x + math.cos(angle) * spawn_dist,
                    'y': self.target_y + math.sin(angle) * spawn_dist,
                    'vx': random.uniform(-10, 10),
                    'vy': random.uniform(-40, -20),  # Float upward
                    'lifetime': random.uniform(1.0, 2.0),
                    'size': random.uniform(8, 14),
                    'rotation': random.uniform(0, 360),
                    'rotation_speed': random.uniform(-90, 90),
                    'color': rune_color,
                    'rune_type': random.choice(['circle', 'cross', 'triangle', 'diamond'])
                })

            if self.timer >= duration:
                self.phase = "fading"
                self.timer = 0

        elif self.phase == "fading":
            # Fade out (0.3s)
            if self.timer < 0.3:
                fade = 1.0 - (self.timer / 0.3)
                self.mark_alpha = fade
            else:
                self.active = False

        # Update impact flash decay
        if self.impact_flash > 0:
            self.impact_flash = max(0, self.impact_flash - delta_time * 5)

        # Update oil drips
        for drip in self.oil_drips[:]:
            drip['lifetime'] -= delta_time
            drip['x'] += drip['vx'] * delta_time
            drip['y'] += drip['vy'] * delta_time
            drip['vy'] += drip['gravity'] * delta_time  # Gravity

            if drip['lifetime'] <= 0:
                self.oil_drips.remove(drip)

        # Update fume runes
        for rune in self.fume_runes[:]:
            rune['lifetime'] -= delta_time
            rune['x'] += rune['vx'] * delta_time
            rune['y'] += rune['vy'] * delta_time
            rune['rotation'] += rune['rotation_speed'] * delta_time

            # Slow down horizontal movement (damping)
            rune['vx'] *= 0.98

            if rune['lifetime'] <= 0:
                self.fume_runes.remove(rune)

        return self.active

    def draw(self, surface):
        """Draw the granite geas effect."""
        if not self.active:
            return

        # Calculate target position
        if self.target:
            target_x = self.target.x
            target_y = self.target.y
        else:
            target_x = self.target_x
            target_y = self.target_y

        # Draw impact flash
        if self.impact_flash > 0:
            flash_alpha = int(200 * self.impact_flash)
            flash_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 200, 100, flash_alpha), (40, 40), 40)
            pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha // 2), (40, 40), 30)
            surface.blit(flash_surf, (int(target_x - 40), int(target_y - 40)))

        # Draw geas mark (after strike phase)
        if self.phase in ["mark_appear", "binding", "fading"] and self.mark_alpha > 0:
            mark_size = 60
            mark_surf = pygame.Surface((mark_size, mark_size), pygame.SRCALPHA)
            center = mark_size // 2

            # Base color - tropical flowers for infused, gray stone for normal
            if self.infused:
                # Use a vibrant tropical color for the mark
                mark_color = (255, 20, 147)    # Deep pink
                glow_color = (255, 105, 180)   # Hot pink
            else:
                # Gray/stone colors for normal granite
                mark_color = (140, 140, 140)
                glow_color = (180, 180, 180)

            # Draw circular geas mark/seal
            alpha = int(180 * self.mark_alpha)

            # Outer glow ring
            pygame.draw.circle(mark_surf, (*glow_color, alpha // 2), (center, center), 28, 3)

            # Inner seal circle
            pygame.draw.circle(mark_surf, (*mark_color, alpha), (center, center), 22, 2)

            # Draw rune symbols inside (rotating)
            num_runes = 6
            for i in range(num_runes):
                angle = (self.mark_rotation + i * 60) * math.pi / 180
                rune_dist = 15
                rx = center + math.cos(angle) * rune_dist
                ry = center + math.sin(angle) * rune_dist

                # Pulsing runes
                pulse = 0.8 + math.sin(self.rune_pulse + i) * 0.2
                rune_alpha = int(alpha * pulse)
                pygame.draw.circle(mark_surf, (*mark_color, rune_alpha), (int(rx), int(ry)), 3)

            # Draw binding chains (for infused version)
            if self.infused and self.phase == "binding":
                for i in range(4):
                    angle = (i * 90 + self.mark_rotation) * math.pi / 180
                    chain_length = 20 + math.sin(self.timer * 2 + i) * 5

                    # Chain extends from center
                    start_x = center
                    start_y = center
                    end_x = center + math.cos(angle) * chain_length
                    end_y = center + math.sin(angle) * chain_length

                    pygame.draw.line(mark_surf, (*mark_color, alpha),
                                   (int(start_x), int(start_y)),
                                   (int(end_x), int(end_y)), 2)

                    # Chain end (shackle)
                    pygame.draw.circle(mark_surf, (*mark_color, alpha),
                                     (int(end_x), int(end_y)), 4, 1)

            # Rotate and blit
            rotated = pygame.transform.rotate(mark_surf, -self.mark_rotation)
            rect = rotated.get_rect(center=(int(target_x), int(target_y)))
            surface.blit(rotated, rect)

        # Draw oil drip particles
        for drip in self.oil_drips:
            if drip['lifetime'] > 0:
                alpha = int(200 * min(1.0, drip['lifetime']))
                if alpha > 0:
                    drip_surf = pygame.Surface((int(drip['size'] * 2), int(drip['size'] * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(drip_surf, (*drip['color'], alpha),
                                     (int(drip['size']), int(drip['size'])), int(drip['size']))
                    surface.blit(drip_surf, (int(drip['x'] - drip['size']), int(drip['y'] - drip['size'])))

        # Draw ethereal fume runes (floating mystical symbols)
        for rune in self.fume_runes:
            if rune['lifetime'] > 0:
                # Fade in at start, fade out at end
                fade_in = min(1.0, (2.0 - rune['lifetime']) * 2)  # Fade in over first 0.5s
                fade_out = min(1.0, rune['lifetime'])  # Fade out over last 1s
                fade = min(fade_in, fade_out)
                alpha = int(150 * fade)

                if alpha > 0:
                    rune_size = int(rune['size'])
                    rune_surf = pygame.Surface((rune_size * 2, rune_size * 2), pygame.SRCALPHA)
                    center = rune_size

                    # Draw wispy semi-transparent background glow (fume)
                    glow_alpha = alpha // 3
                    for i in range(3):
                        glow_radius = rune_size + (2 - i) * 4
                        pygame.draw.circle(rune_surf, (*rune['color'], glow_alpha // (i + 1)),
                                         (center, center), glow_radius)

                    # Draw rune symbol based on type
                    rune_color = (*rune['color'], alpha)

                    if rune['rune_type'] == 'circle':
                        # Simple circle rune
                        pygame.draw.circle(rune_surf, rune_color, (center, center), rune_size // 2, 2)

                    elif rune['rune_type'] == 'cross':
                        # Cross/plus symbol
                        line_length = rune_size // 2
                        pygame.draw.line(rune_surf, rune_color,
                                       (center - line_length, center),
                                       (center + line_length, center), 2)
                        pygame.draw.line(rune_surf, rune_color,
                                       (center, center - line_length),
                                       (center, center + line_length), 2)

                    elif rune['rune_type'] == 'triangle':
                        # Triangle symbol
                        size = rune_size // 2
                        points = [
                            (center, center - size),  # Top
                            (center - size, center + size),  # Bottom left
                            (center + size, center + size)  # Bottom right
                        ]
                        pygame.draw.polygon(rune_surf, rune_color, points, 2)

                    elif rune['rune_type'] == 'diamond':
                        # Diamond/rhombus symbol
                        size = rune_size // 2
                        points = [
                            (center, center - size),  # Top
                            (center + size, center),  # Right
                            (center, center + size),  # Bottom
                            (center - size, center)  # Left
                        ]
                        pygame.draw.polygon(rune_surf, rune_color, points, 2)

                    # Rotate the rune
                    rotated = pygame.transform.rotate(rune_surf, rune['rotation'])
                    rect = rotated.get_rect(center=(int(rune['x']), int(rune['y'])))
                    surface.blit(rotated, rect)


class GeasBreakHeal:
    """
    Animation for when Granite Geas breaks and releases fragrant fumes.
    Fumes travel from the marked target to POTPOURRIST who inhales them for healing.
    """
    def __init__(self, target_x, target_y, caster_x, caster_y, caster_unit, heal_amount=4):
        self.target_x = target_x
        self.target_y = target_y
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.caster = caster_unit
        self.heal_amount = heal_amount

        self.phase = "release"  # release -> travel -> inhale -> complete

        # Geas seal shattering
        play_sound("geas_break")
        self.timer = 0
        self.active = True

        # Fragrant fume particles traveling from target to caster
        self.fume_stream = []

        # Burst particles at release
        self.release_burst = []

        # Initial burst of fumes - VIOLENT explosion with tropical flower colors
        for i in range(40):  # More particles
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 200)  # Much faster
            self.release_burst.append({
                'x': target_x,
                'y': target_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.4, 0.8),
                'size': random.uniform(8, 18),  # Larger
                'color': random.choice([
                    (255, 215, 0),    # Gold
                    (255, 105, 180),  # Hot pink
                    (255, 99, 71),    # Tomato
                    (255, 165, 0),    # Orange
                    (147, 112, 219),  # Medium purple
                    (186, 85, 211),   # Medium orchid
                    (0, 206, 209),    # Dark turquoise
                    (255, 20, 147)    # Deep pink
                ])
            })

        # Shockwave ring effect
        self.shockwave_radius = 0
        self.shockwave_active = True

        # Pre-select shockwave colors to avoid random.choice() every frame
        self.shockwave_colors = [
            random.choice([
                (255, 215, 0),    # Gold
                (255, 105, 180),  # Hot pink
                (255, 99, 71),    # Tomato
                (255, 165, 0),    # Orange
                (147, 112, 219),  # Medium purple
                (186, 85, 211),   # Medium orchid
                (0, 206, 209),    # Dark turquoise
                (255, 20, 147)    # Deep pink
            ]) for _ in range(3)  # Pre-select 3 colors for the 3 rings
        ]

        # Screen shake effect
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0

    def update(self, delta_time):
        """Update geas break healing animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "release":
            # Geas seal VIOLENTLY breaks and releases fumes (0.4s)
            if self.timer < 0.4:
                # Expand shockwave
                self.shockwave_radius = (self.timer / 0.4) * 80
                self.shockwave_active = True

                # Screen shake - only during first 0.1s
                if self.timer < 0.1:
                    self.screen_shake_intensity = 8 * (1.0 - self.timer / 0.1)
                    self.screen_shake_duration = 0.1
                else:
                    self.screen_shake_intensity = 0
                    self.screen_shake_duration = 0

                # Spawn fume stream particles traveling toward caster - MORE INTENSE
                if random.random() < 0.9:  # More frequent spawning
                    # Calculate direction from target to caster
                    dx = self.caster_x - self.target_x
                    dy = self.caster_y - self.target_y
                    dist = math.sqrt(dx*dx + dy*dy)

                    if dist > 0:
                        # Normalize and add some variance
                        dir_x = dx / dist
                        dir_y = dy / dist

                        speed = random.uniform(120, 180)
                        angle_variance = random.uniform(-0.3, 0.3)

                        # Rotate direction slightly
                        vx = (dir_x * math.cos(angle_variance) - dir_y * math.sin(angle_variance)) * speed
                        vy = (dir_x * math.sin(angle_variance) + dir_y * math.cos(angle_variance)) * speed

                        self.fume_stream.append({
                            'x': self.target_x + random.uniform(-15, 15),
                            'y': self.target_y + random.uniform(-15, 15),
                            'vx': vx,
                            'vy': vy,
                            'lifetime': 1.5,
                            'size': random.uniform(8, 14),
                            'color': random.choice([
                                (255, 215, 0),    # Gold
                                (255, 105, 180),  # Hot pink
                                (255, 99, 71),    # Tomato
                                (255, 165, 0),    # Orange
                                (147, 112, 219),  # Medium purple
                                (186, 85, 211),   # Medium orchid
                                (0, 206, 209),    # Dark turquoise
                                (255, 20, 147)    # Deep pink
                            ]),
                            'trail_alpha': 1.0
                        })
            else:
                # Deactivate shockwave after full expansion
                self.shockwave_active = False
                self.phase = "travel"
                self.timer = 0

        elif self.phase == "travel":
            # Fumes travel to caster (0.6s)
            if self.timer >= 0.6 or len(self.fume_stream) == 0:
                self.phase = "inhale"
                self.timer = 0

        elif self.phase == "inhale":
            # Caster inhales, healing sparkles appear (0.5s)
            if self.timer < 0.5:
                # Spawn healing sparkles around caster
                if random.random() < 0.5:
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(20, 35)
                    self.fume_stream.append({
                        'x': self.caster_x + math.cos(angle) * dist,
                        'y': self.caster_y + math.sin(angle) * dist,
                        'vx': -math.cos(angle) * 50,  # Pull toward center
                        'vy': -math.sin(angle) * 50 - 30,  # Also float up slightly
                        'lifetime': 0.6,
                        'size': random.uniform(4, 8),
                        'color': (100, 255, 150),  # Green healing color
                        'trail_alpha': 1.0
                    })
            else:
                self.active = False

        # Update release burst particles
        for particle in self.release_burst[:]:
            particle['lifetime'] -= delta_time
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time

            # Slow down
            particle['vx'] *= 0.95
            particle['vy'] *= 0.95

            if particle['lifetime'] <= 0:
                self.release_burst.remove(particle)

        # Update fume stream particles
        for fume in self.fume_stream[:]:
            fume['lifetime'] -= delta_time
            fume['x'] += fume['vx'] * delta_time
            fume['y'] += fume['vy'] * delta_time

            # Check if fume reached caster (within 30 pixels)
            dist_to_caster = math.sqrt((fume['x'] - self.caster_x)**2 + (fume['y'] - self.caster_y)**2)
            if dist_to_caster < 30:
                fume['lifetime'] = 0  # Remove when absorbed

            if fume['lifetime'] <= 0:
                self.fume_stream.remove(fume)

        return self.active

    def draw(self, surface):
        """Draw the geas break healing animation."""
        if not self.active:
            return

        # Draw release burst
        for particle in self.release_burst:
            if particle['lifetime'] > 0:
                alpha = int(180 * (particle['lifetime'] / 0.6))
                if alpha > 0:
                    size = int(particle['size'])
                    particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

                    # Wispy cloud
                    for i in range(3):
                        radius = size - i * 2
                        if radius > 0:
                            pygame.draw.circle(particle_surf, (*particle['color'], alpha // (i + 1)),
                                             (size, size), radius)

                    surface.blit(particle_surf, (int(particle['x'] - size), int(particle['y'] - size)))

        # Draw shockwave ring
        if self.shockwave_active and self.shockwave_radius > 0:
            # Calculate ring fade based on expansion
            ring_fade = 1.0 - (self.shockwave_radius / 80.0)
            if ring_fade > 0:
                ring_alpha = int(200 * ring_fade)

                # Multiple expanding rings for dramatic effect
                for ring_idx, ring_offset in enumerate([0, -5, -10]):
                    radius = int(self.shockwave_radius + ring_offset)
                    if radius > 0:
                        ring_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
                        center = radius + 10

                        # Use pre-selected color for this ring
                        ring_color = self.shockwave_colors[ring_idx]

                        # Draw thick ring with gradient - use same color for all thickness layers
                        for thickness in range(5):
                            layer_alpha = ring_alpha // (thickness + 1)
                            pygame.draw.circle(ring_surf, (*ring_color, layer_alpha),
                                             (center, center), radius + thickness, 2)

                        surface.blit(ring_surf, (int(self.target_x - center), int(self.target_y - center)))

        # Draw fume stream particles
        for fume in self.fume_stream:
            if fume['lifetime'] > 0:
                fade = min(1.0, fume['lifetime'])
                alpha = int(160 * fade * fume['trail_alpha'])

                if alpha > 0:
                    size = int(fume['size'])
                    fume_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
                    center = int(size * 1.5)

                    # Layered wispy fume
                    for i in range(4):
                        radius = size + (3 - i) * 3
                        layer_alpha = alpha // (i + 1)
                        pygame.draw.circle(fume_surf, (*fume['color'], layer_alpha),
                                         (center, center), radius)

                    surface.blit(fume_surf, (int(fume['x'] - center), int(fume['y'] - center)))


class DemiluneSwing:
    """DEMILUNE - Heavy arc swing of granite pedestal with stone impact effects."""
    def __init__(self, caster_x, caster_y, caster_unit, target_x, target_y, infused=False, upgraded=False, targets=None,
                 caster_grid_pos=None, target_grid_pos=None, camera=None):
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.caster = caster_unit
        self.target_x = target_x
        self.target_y = target_y
        self.infused = infused
        self.upgraded = upgraded  # Selenic Backdraft: second swing in opposite direction
        self.targets = targets or []  # List of units that will be hit
        self.camera = camera

        self.phase = "windup"  # windup -> swing -> impact -> settling -> [backdraft_windup -> backdraft_swing -> backdraft_impact -> backdraft_settling ->] complete

        # Pedestal pulling back
        play_sound("demilune_swing")
        self.timer = 0
        self.active = True

        # Track which targets have been hit
        self.targets_hit = set()

        # Calculate arc tiles using grid coordinates (matching the engine's grid logic)
        # This ensures the animation matches the actual game area of effect
        if caster_grid_pos and target_grid_pos:
            caster_grid_y, caster_grid_x = caster_grid_pos
            target_grid_y, target_grid_x = target_grid_pos

            # Determine direction from grid coordinates (cardinal directions only)
            dy = target_grid_y - caster_grid_y
            dx = target_grid_x - caster_grid_x

            # Calculate arc tiles in grid space (matching the engine's grid logic)
            # Explicitly check cardinal directions for clarity
            arc_grid_tiles = []

            if dx == 0 and dy < 0:  # North (target directly above)
                # Forward: NW, N, NE
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x))
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x + 1))
                # Sides: W, E
                arc_grid_tiles.append((caster_grid_y, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x + 1))
                self.swing_direction = "north"
            elif dx == 0 and dy > 0:  # South (target directly below)
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x))
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x + 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x + 1))
                self.swing_direction = "south"
            elif dy == 0 and dx < 0:  # West (target directly left)
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x))
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x))
                self.swing_direction = "west"
            elif dy == 0 and dx > 0:  # East (target directly right)
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x + 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x + 1))
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x + 1))
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x))
                arc_grid_tiles.append((caster_grid_y + 1, caster_grid_x))
                self.swing_direction = "east"
            else:
                # Fallback for non-cardinal (shouldn't happen with new skill restriction)
                # Default to north
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x))
                arc_grid_tiles.append((caster_grid_y - 1, caster_grid_x + 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x - 1))
                arc_grid_tiles.append((caster_grid_y, caster_grid_x + 1))
                self.swing_direction = "north"

            # Convert grid tiles to screen coordinates using camera
            self.arc_tiles = []
            for grid_y, grid_x in arc_grid_tiles:
                if self.camera:
                    screen_x, screen_y = self.camera.grid_to_screen(grid_x, grid_y)
                else:
                    # Fallback to defaults
                    GRID_OFFSET_X = 100
                    GRID_OFFSET_Y = 50
                    screen_x = GRID_OFFSET_X + grid_x * TILE_SIZE + TILE_SIZE // 2
                    screen_y = GRID_OFFSET_Y + grid_y * TILE_SIZE + TILE_SIZE // 2
                self.arc_tiles.append((screen_y, screen_x))
        else:
            # Fallback to old pixel-based calculation
            dy = target_y - caster_y
            dx = target_x - caster_x

            self.arc_tiles = []
            if abs(dy) >= abs(dx):  # Vertical dominant
                if dy < 0:  # North
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x))
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x + TILE_SIZE))
                    self.arc_tiles.append((caster_y, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y, caster_x + TILE_SIZE))
                    self.swing_direction = "north"
                else:  # South
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x))
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x + TILE_SIZE))
                    self.arc_tiles.append((caster_y, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y, caster_x + TILE_SIZE))
                    self.swing_direction = "south"
            else:  # Horizontal dominant
                if dx < 0:  # West
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x - TILE_SIZE))
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x))
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x))
                    self.swing_direction = "west"
                else:  # East
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x + TILE_SIZE))
                    self.arc_tiles.append((caster_y, caster_x + TILE_SIZE))
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x + TILE_SIZE))
                    self.arc_tiles.append((caster_y - TILE_SIZE, caster_x))
                    self.arc_tiles.append((caster_y + TILE_SIZE, caster_x))
                    self.swing_direction = "east"

        # Sweep order for animation
        self.sweep_tiles = list(self.arc_tiles)  # Will be sorted below
        if self.swing_direction == "south":
            # South: sweep left to right (ascending x)
            self.sweep_tiles.sort(key=lambda pos: pos[1])
        elif self.swing_direction == "north":
            # North: sweep right to left (descending x) - inverted from south
            self.sweep_tiles.sort(key=lambda pos: pos[1], reverse=True)
        elif self.swing_direction == "east":
            # East: sweep top to bottom (ascending y)
            self.sweep_tiles.sort(key=lambda pos: pos[0])
        elif self.swing_direction == "west":
            # West: sweep bottom to top (descending y) - inverted from east
            self.sweep_tiles.sort(key=lambda pos: pos[0], reverse=True)

        # Selenic Backdraft: compute back-arc tiles (opposite direction)
        self.back_arc_tiles = []
        self.back_sweep_tiles = []
        if upgraded and caster_grid_pos and target_grid_pos:
            caster_grid_y, caster_grid_x = caster_grid_pos
            target_grid_y, target_grid_x = target_grid_pos
            # Opposite direction
            opp_dy = caster_grid_y - target_grid_y
            opp_dx = caster_grid_x - target_grid_x
            opp_target_y = caster_grid_y + opp_dy
            opp_target_x = caster_grid_x + opp_dx

            back_grid_tiles = []
            # Mirror the direction logic
            opposite_dir = {"north": "south", "south": "north", "east": "west", "west": "east"}
            self.back_swing_direction = opposite_dir.get(self.swing_direction, "south")

            if self.back_swing_direction == "north":
                back_grid_tiles = [
                    (caster_grid_y - 1, caster_grid_x - 1), (caster_grid_y - 1, caster_grid_x),
                    (caster_grid_y - 1, caster_grid_x + 1), (caster_grid_y, caster_grid_x - 1),
                    (caster_grid_y, caster_grid_x + 1)]
            elif self.back_swing_direction == "south":
                back_grid_tiles = [
                    (caster_grid_y + 1, caster_grid_x - 1), (caster_grid_y + 1, caster_grid_x),
                    (caster_grid_y + 1, caster_grid_x + 1), (caster_grid_y, caster_grid_x - 1),
                    (caster_grid_y, caster_grid_x + 1)]
            elif self.back_swing_direction == "west":
                back_grid_tiles = [
                    (caster_grid_y - 1, caster_grid_x - 1), (caster_grid_y, caster_grid_x - 1),
                    (caster_grid_y + 1, caster_grid_x - 1), (caster_grid_y - 1, caster_grid_x),
                    (caster_grid_y + 1, caster_grid_x)]
            elif self.back_swing_direction == "east":
                back_grid_tiles = [
                    (caster_grid_y - 1, caster_grid_x + 1), (caster_grid_y, caster_grid_x + 1),
                    (caster_grid_y + 1, caster_grid_x + 1), (caster_grid_y - 1, caster_grid_x),
                    (caster_grid_y + 1, caster_grid_x)]

            for grid_y, grid_x in back_grid_tiles:
                if self.camera:
                    screen_x, screen_y = self.camera.grid_to_screen(grid_x, grid_y)
                else:
                    GRID_OFFSET_X = 100
                    GRID_OFFSET_Y = 50
                    screen_x = GRID_OFFSET_X + grid_x * TILE_SIZE + TILE_SIZE // 2
                    screen_y = GRID_OFFSET_Y + grid_y * TILE_SIZE + TILE_SIZE // 2
                self.back_arc_tiles.append((screen_y, screen_x))

            self.back_sweep_tiles = list(self.back_arc_tiles)
            if self.back_swing_direction == "south":
                self.back_sweep_tiles.sort(key=lambda pos: pos[1])
            elif self.back_swing_direction == "north":
                self.back_sweep_tiles.sort(key=lambda pos: pos[1], reverse=True)
            elif self.back_swing_direction == "east":
                self.back_sweep_tiles.sort(key=lambda pos: pos[0])
            elif self.back_swing_direction == "west":
                self.back_sweep_tiles.sort(key=lambda pos: pos[0], reverse=True)

        # Selenic Backdraft color scheme (stinky moon potpourri)
        self.backdraft_color_core = (180, 160, 200)     # Dusty lavender
        self.backdraft_color_mid = (140, 100, 160)      # Deep plum
        self.backdraft_color_outer = (100, 80, 120)     # Dark purple haze
        self.backdraft_color_sparkle = (220, 200, 255)  # Pale moonlight glint
        self.backdraft_color_accent = (200, 150, 200)   # Potpourrist purple tint

        # Backdraft fume particles (spawned during swing phase)
        self.backdraft_fumes = [] if upgraded else None

        # Animation state
        self.swing_progress = 0  # 0 to 1 across sweep
        self.pedestal_trail = []  # Trail positions for visualization
        self.impact_effects = []  # Burst particles at each tile
        self.stone_debris = []  # Heavy rock chunks

        # Infused-specific effects
        self.potpourri_trail = [] if infused else None
        self.fragrance_particles = [] if infused else None

    def update(self, delta_time):
        """Update demilune animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "windup":
            # Caster pulls back pedestal (0.3s)
            if self.timer < 0.3:
                progress = self.timer / 0.3
                if self.caster:
                    # Pull back and lift
                    self.caster.wind_up_rotation = -25 * progress
                    self.caster.pry_stretch_y = 1.0 + (progress * 0.15)
            else:
                self.phase = "swing"
                self.timer = 0

        elif self.phase == "swing":
            # Sweeping arc motion (0.25s - faster)
            if self.timer < 0.25:
                progress = self.timer / 0.25
                # Apply easing for smooth entrance and exit
                # Use ease-in-out cubic: smooth acceleration and deceleration
                if progress < 0.5:
                    # Ease in (accelerate)
                    eased = 4 * progress * progress * progress
                else:
                    # Ease out (decelerate)
                    eased = 1 - pow(-2 * progress + 2, 3) / 2
                self.swing_progress = eased

                if self.caster:
                    # Swing through arc
                    self.caster.wind_up_rotation = -25 + (progress * 55)  # -25 to +30
                    self.caster.pry_stretch_y = 1.15 - (progress * 0.15)  # Back to normal

                # Check if swing has reached any targets and apply impact
                for target in self.targets:
                    if id(target) not in self.targets_hit:
                        # Check if target is within the currently swept arc
                        for i in range(int(self.swing_progress * len(self.sweep_tiles))):
                            tile_y, tile_x = self.sweep_tiles[i]
                            # Check if target is close to this swept tile (within 1 tile range)
                            dist = math.sqrt((target.x - tile_x)**2 + (target.y - tile_y)**2)
                            if dist < TILE_SIZE * 1.2:  # Hit detection radius
                                # Apply shake/impact to target
                                target.shake_intensity = 8
                                self.targets_hit.add(id(target))
                                break

                # Spawn impact effects as pedestal sweeps through tiles
                tile_index = int(progress * len(self.sweep_tiles))
                if tile_index < len(self.sweep_tiles) and tile_index not in [e['tile_index'] for e in self.impact_effects]:
                    tile_y, tile_x = self.sweep_tiles[tile_index]

                    # Stone impact burst
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(80, 200)
                        self.stone_debris.append({
                            'x': tile_x,
                            'y': tile_y,
                            'vx': math.cos(angle) * speed,
                            'vy': math.sin(angle) * speed - 100,
                            'lifetime': random.uniform(0.5, 1.0),
                            'size': random.uniform(3, 8),
                            'color': (120, 100, 80),
                            'gravity': 500
                        })

                    self.impact_effects.append({'tile_index': tile_index, 'time': self.timer})

                    # Infused: spawn potpourri trail particles
                    if self.infused and self.potpourri_trail is not None:
                        for _ in range(8):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(20, 60)
                            self.potpourri_trail.append({
                                'x': tile_x,
                                'y': tile_y,
                                'vx': math.cos(angle) * speed,
                                'vy': math.sin(angle) * speed - 40,
                                'lifetime': random.uniform(0.8, 1.5),
                                'size': random.uniform(3, 6),
                                'color': random.choice([
                                    (255, 215, 0),    # Gold #ffd700
                                    (255, 105, 180),  # Hot pink #ff69b4
                                    (255, 99, 71),    # Tomato #ff6347
                                    (255, 165, 0),    # Orange #ffa500
                                    (147, 112, 219),  # Medium purple #9370db
                                    (186, 85, 211),   # Medium orchid #ba55d3
                                    (0, 206, 209),    # Dark turquoise #00ced1
                                    (255, 20, 147)    # Deep pink #ff1493
                                ]),
                                'orbit_angle': angle,
                                'orbit_speed': random.uniform(2.0, 4.0)
                            })

                        # Fragrance fumes (wispy, floating)
                        if self.fragrance_particles is not None:
                            for _ in range(5):
                                offset_x = random.uniform(-20, 20)
                                offset_y = random.uniform(-20, 20)
                                self.fragrance_particles.append({
                                    'x': tile_x + offset_x,
                                    'y': tile_y + offset_y,
                                    'vx': random.uniform(-15, 15),
                                    'vy': random.uniform(-50, -20),
                                    'lifetime': random.uniform(1.0, 2.0),
                                    'size': random.uniform(8, 15),
                                    'color': (220, 200, 180),  # Beige fume
                                    'alpha_mod': 0.3
                                })

                # Selenic Backdraft: spawn perfume fume blast on back-arc tiles simultaneously
                if self.upgraded and self.backdraft_fumes is not None and self.back_sweep_tiles:
                    back_tile_index = int(progress * len(self.back_sweep_tiles))
                    if back_tile_index < len(self.back_sweep_tiles):
                        back_tile_y, back_tile_x = self.back_sweep_tiles[back_tile_index]

                        # Only spawn once per tile (use offset indices)
                        back_key = back_tile_index + 1000
                        if back_key not in [e.get('tile_index', -1) for e in self.impact_effects]:
                            self.impact_effects.append({'tile_index': back_key, 'time': self.timer})

                            # Direction from caster outward to this tile
                            dir_x = back_tile_x - self.caster_x
                            dir_y = back_tile_y - self.caster_y
                            dir_len = math.sqrt(dir_x * dir_x + dir_y * dir_y) or 1
                            dir_x /= dir_len
                            dir_y /= dir_len

                            # Big perfume fume blast — directional cloud
                            for _ in range(18):
                                # Bias velocity outward from caster with spread
                                spread_angle = random.uniform(-0.8, 0.8)
                                cos_a = math.cos(spread_angle)
                                sin_a = math.sin(spread_angle)
                                out_x = dir_x * cos_a - dir_y * sin_a
                                out_y = dir_x * sin_a + dir_y * cos_a
                                speed = random.uniform(60, 180)

                                self.backdraft_fumes.append({
                                    'x': back_tile_x + random.uniform(-8, 8),
                                    'y': back_tile_y + random.uniform(-8, 8),
                                    'vx': out_x * speed + random.uniform(-20, 20),
                                    'vy': out_y * speed + random.uniform(-20, 20),
                                    'lifetime': random.uniform(0.6, 1.2),
                                    'max_lifetime': 0,  # Set below
                                    'size': random.uniform(10, 20),
                                    'color': random.choice([
                                        self.backdraft_color_core,
                                        self.backdraft_color_mid,
                                        self.backdraft_color_outer,
                                        self.backdraft_color_accent,
                                    ]),
                                    'swirl_phase': random.uniform(0, math.pi * 2),
                                    'swirl_speed': random.uniform(2.0, 4.0),
                                })
                                self.backdraft_fumes[-1]['max_lifetime'] = self.backdraft_fumes[-1]['lifetime']

                            # Sparkle accents scattered through the cloud
                            for _ in range(4):
                                spread_angle = random.uniform(-0.6, 0.6)
                                cos_a = math.cos(spread_angle)
                                sin_a = math.sin(spread_angle)
                                out_x = dir_x * cos_a - dir_y * sin_a
                                out_y = dir_x * sin_a + dir_y * cos_a
                                speed = random.uniform(40, 120)

                                self.backdraft_fumes.append({
                                    'x': back_tile_x + random.uniform(-5, 5),
                                    'y': back_tile_y + random.uniform(-5, 5),
                                    'vx': out_x * speed,
                                    'vy': out_y * speed,
                                    'lifetime': random.uniform(0.3, 0.6),
                                    'max_lifetime': 0,
                                    'size': random.uniform(2, 5),
                                    'color': self.backdraft_color_sparkle,
                                    'swirl_phase': 0,
                                    'swirl_speed': 0,
                                })
                                self.backdraft_fumes[-1]['max_lifetime'] = self.backdraft_fumes[-1]['lifetime']

            else:
                self.phase = "impact"
                self.timer = 0
                play_sound("demilune_impact")
                # Reset caster rotation
                if self.caster:
                    self.caster.wind_up_rotation = 0
                    self.caster.pry_stretch_y = 1.0

        elif self.phase == "impact":
            # Final impact hold (0.2s)
            if self.timer >= 0.2:
                self.phase = "settling"
                self.timer = 0

        elif self.phase == "settling":
            # Debris and effects settle (1.0s for regular, 1.5s for infused)
            settle_time = 1.5 if self.infused else 1.0
            if self.timer >= settle_time:
                self.phase = "complete"
                self.active = False

        # Update stone debris
        for debris in self.stone_debris[:]:
            debris['x'] += debris['vx'] * delta_time
            debris['y'] += debris['vy'] * delta_time
            debris['vy'] += debris.get('gravity', 0) * delta_time
            debris['lifetime'] -= delta_time
            if debris['lifetime'] <= 0:
                self.stone_debris.remove(debris)

        # Update infused potpourri trail
        if self.potpourri_trail is not None:
            for particle in self.potpourri_trail[:]:
                # Orbital motion
                particle['orbit_angle'] += particle['orbit_speed'] * delta_time
                particle['vx'] += math.cos(particle['orbit_angle']) * 30 * delta_time * 0.3
                particle['vy'] += math.sin(particle['orbit_angle']) * 30 * delta_time * 0.3

                # Move
                particle['x'] += particle['vx'] * delta_time
                particle['y'] += particle['vy'] * delta_time

                # Age
                particle['lifetime'] -= delta_time
                if particle['lifetime'] <= 0:
                    self.potpourri_trail.remove(particle)

        # Update fragrance fumes
        if self.fragrance_particles is not None:
            for fume in self.fragrance_particles[:]:
                fume['x'] += fume['vx'] * delta_time
                fume['y'] += fume['vy'] * delta_time
                fume['lifetime'] -= delta_time
                if fume['lifetime'] <= 0:
                    self.fragrance_particles.remove(fume)

        # Update backdraft perfume fumes
        if self.backdraft_fumes is not None:
            for fume in self.backdraft_fumes[:]:
                # Swirl drift
                fume['swirl_phase'] += fume['swirl_speed'] * delta_time
                swirl_vx = math.sin(fume['swirl_phase']) * 15
                swirl_vy = math.cos(fume['swirl_phase']) * 10

                # Movement with drag
                fume['x'] += (fume['vx'] + swirl_vx) * delta_time
                fume['y'] += (fume['vy'] + swirl_vy) * delta_time
                fume['vx'] *= (1.0 - 2.5 * delta_time)  # Drag deceleration
                fume['vy'] *= (1.0 - 2.5 * delta_time)

                # Expand over lifetime
                age_ratio = 1.0 - (fume['lifetime'] / fume['max_lifetime']) if fume['max_lifetime'] > 0 else 1.0
                fume['size'] *= (1.0 + 0.8 * delta_time)  # Gradual expansion

                fume['lifetime'] -= delta_time
                if fume['lifetime'] <= 0:
                    self.backdraft_fumes.remove(fume)

        return self.active

    def draw(self, surface):
        """Draw the demilune swing animation."""
        if not self.active and self.phase == "complete":
            return

        # Draw backdraft perfume fumes (behind everything else)
        if self.backdraft_fumes is not None:
            for fume in self.backdraft_fumes:
                if fume['lifetime'] > 0:
                    life_ratio = fume['lifetime'] / fume['max_lifetime'] if fume['max_lifetime'] > 0 else 0
                    alpha = int(160 * life_ratio)
                    if alpha > 0:
                        size = int(fume['size'])
                        surf_size = size * 3
                        fume_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                        center = surf_size // 2

                        is_sparkle = (fume['color'] == self.backdraft_color_sparkle)

                        if is_sparkle:
                            # Sparkle: bright small point
                            pygame.draw.circle(fume_surf, (*fume['color'], alpha),
                                             (center, center), max(1, size // 2))
                        else:
                            # Outer diffuse cloud
                            outer_alpha = alpha // 3
                            pygame.draw.circle(fume_surf, (*self.backdraft_color_outer, outer_alpha),
                                             (center, center), size + 4)

                            # Mid cloud
                            mid_alpha = alpha // 2
                            pygame.draw.circle(fume_surf, (*fume['color'], mid_alpha),
                                             (center, center), size)

                            # Core glow
                            core_alpha = min(255, int(alpha * 0.8))
                            pygame.draw.circle(fume_surf, (*self.backdraft_color_core, core_alpha),
                                             (center, center), max(1, size // 2))

                        surface.blit(fume_surf, (int(fume['x'] - center), int(fume['y'] - center)))

            # Back-arc tile flash during impact
            if self.phase == "impact" and self.back_arc_tiles:
                flash_alpha = int(100 * max(0, 1.0 - self.timer / 0.2))
                if flash_alpha > 0:
                    for tile_y, tile_x in self.back_arc_tiles:
                        flash_size = TILE_SIZE
                        flash_surf = pygame.Surface((flash_size, flash_size), pygame.SRCALPHA)
                        pygame.draw.rect(flash_surf, (*self.backdraft_color_mid, flash_alpha),
                                       (0, 0, flash_size, flash_size))
                        surface.blit(flash_surf, (int(tile_x - flash_size // 2), int(tile_y - flash_size // 2)))

        # Draw clock-hand style swing with motion blur trail
        if self.phase == "swing" or self.phase == "impact":
            if self.swing_progress > 0:
                # POTPOURRIST's center position (origin point of the swing)
                center_x = self.caster_x
                center_y = self.caster_y

                # Radius - reaches to the edge of the furthest affected tile
                radius = TILE_SIZE * 1.5

                # Determine the angular range based on swing direction
                # The arc faces forward, sides sweep across
                if self.swing_direction == "south":
                    # South: arc faces down, sweep left to right
                    start_angle = 0  # Right/East
                    end_angle = math.pi  # Left/West
                elif self.swing_direction == "north":
                    # North: arc faces up, sweep left to right (mirror of south)
                    start_angle = -math.pi  # Left/West
                    end_angle = 0  # Right/East
                elif self.swing_direction == "east":
                    # East: arc faces right, sweep top to bottom
                    start_angle = -math.pi / 2  # Up/North
                    end_angle = math.pi / 2  # Down/South
                elif self.swing_direction == "west":
                    # West: arc faces left, sweep bottom to top through western side
                    start_angle = math.pi / 2  # Down/South
                    end_angle = 3 * math.pi / 2  # Up/North (going through west)

                # Current angle position of the clock hand
                current_angle = start_angle + (end_angle - start_angle) * self.swing_progress

                # Draw the motion blur trail - all the angles that have been swept
                num_trail_samples = 60
                active_samples = int(num_trail_samples * self.swing_progress)

                for i in range(active_samples):
                    # Calculate angle for this trail sample
                    t = i / num_trail_samples

                    # Apply same easing to trail samples for smooth motion
                    if t < 0.5:
                        eased_t = 4 * t * t * t
                    else:
                        eased_t = 1 - pow(-2 * t + 2, 3) / 2

                    angle = start_angle + (end_angle - start_angle) * eased_t

                    # Calculate velocity (speed) at this point for motion blur intensity
                    # Speed is highest at middle (0.5), lowest at start/end
                    speed = 1.0 - abs(eased_t - 0.5) * 2  # 0 at edges, 1 at middle
                    speed = speed * speed  # Square for more dramatic effect

                    # Calculate end point of the line at this angle
                    end_x = center_x + radius * math.cos(angle)
                    end_y = center_y + radius * math.sin(angle)

                    # Calculate fade - older positions fade out
                    # Most recent position (closest to current_angle) is brightest
                    age = self.swing_progress - eased_t
                    trail_fade = max(0, 1.0 - (age * 4))  # Faster fade for quicker swing

                    # Add entrance and exit fade - fade in at start, fade out at end
                    entrance_fade = min(1.0, self.swing_progress * 5)  # Fade in over first 20%
                    exit_fade = min(1.0, (1.0 - self.swing_progress) * 5)  # Fade out over last 20%

                    # Speed-based intensity - brighter during fast parts
                    speed_intensity = 0.4 + (speed * 0.6)  # Range from 40% to 100%

                    # Combine all fade factors
                    fade = trail_fade * entrance_fade * exit_fade * speed_intensity

                    if fade > 0.01:
                        # Calculate perpendicular direction for motion stretch
                        perp_x = -math.sin(angle)
                        perp_y = math.cos(angle)

                        if self.infused:
                            # Infused - draw magical glowing blur along the line with particle streaks
                            # Sample points along the line from center to edge
                            for sample in range(8):
                                sample_t = sample / 7
                                px = center_x + (end_x - center_x) * sample_t
                                py = center_y + (end_y - center_y) * sample_t

                                # Width varies - thicker near center, thinner toward edge
                                width_factor = 1.0 - (sample_t * 0.5)

                                # Stretch factor based on speed - more stretch = more motion blur
                                stretch = 1.0 + (speed * 2.5)

                                # Outer tropical flower glow - stretched ellipse (use hot pink)
                                alpha = int(50 * fade * sample_t)
                                if alpha > 0:
                                    blur_w = int(36 * width_factor)
                                    blur_h = int(36 * width_factor * stretch)
                                    blur_surf = pygame.Surface((blur_w, blur_h), pygame.SRCALPHA)
                                    pygame.draw.ellipse(blur_surf, (255, 105, 180, alpha), (0, 0, blur_w, blur_h))  # Hot pink #ff69b4

                                    # Rotate to align with motion direction
                                    rotated = pygame.transform.rotate(blur_surf, math.degrees(-angle + math.pi/2))
                                    rect = rotated.get_rect(center=(int(px), int(py)))
                                    surface.blit(rotated, rect)

                                # Golden core - stretched ellipse
                                alpha = int(120 * fade * sample_t)
                                if alpha > 0:
                                    blur_w = int(20 * width_factor)
                                    blur_h = int(20 * width_factor * stretch)
                                    blur_surf = pygame.Surface((blur_w, blur_h), pygame.SRCALPHA)
                                    pygame.draw.ellipse(blur_surf, (255, 215, 0, alpha), (0, 0, blur_w, blur_h))  # Gold #ffd700

                                    rotated = pygame.transform.rotate(blur_surf, math.degrees(-angle + math.pi/2))
                                    rect = rotated.get_rect(center=(int(px), int(py)))
                                    surface.blit(rotated, rect)

                                # Particle streaks - emit perpendicular to swing direction (use orange)
                                if sample_t > 0.3 and random.random() < 0.15 * speed * fade:
                                    streak_dist = random.uniform(10, 25)
                                    spark_x = px + perp_x * streak_dist * random.choice([-1, 1])
                                    spark_y = py + perp_y * streak_dist * random.choice([-1, 1])
                                    spark_alpha = int(100 * fade)
                                    if spark_alpha > 0:
                                        spark_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                                        spark_color = random.choice([
                                            (255, 99, 71),   # Tomato #ff6347
                                            (255, 165, 0),   # Orange #ffa500
                                            (255, 20, 147)   # Deep pink #ff1493
                                        ])
                                        pygame.draw.circle(spark_surf, (*spark_color, spark_alpha), (4, 4), 4)
                                        surface.blit(spark_surf, (int(spark_x - 4), int(spark_y - 4)))

                        else:
                            # Regular - draw gray blur along the line with stretch
                            for sample in range(6):
                                sample_t = sample / 5
                                px = center_x + (end_x - center_x) * sample_t
                                py = center_y + (end_y - center_y) * sample_t

                                # Width varies - thicker near center
                                width_factor = 1.0 - (sample_t * 0.4)

                                # Stretch factor based on speed
                                stretch = 1.0 + (speed * 2.0)

                                # Gray blur - stretched ellipse
                                alpha = int(100 * fade * sample_t)
                                if alpha > 0:
                                    blur_w = int(28 * width_factor)
                                    blur_h = int(28 * width_factor * stretch)
                                    blur_surf = pygame.Surface((blur_w, blur_h), pygame.SRCALPHA)
                                    pygame.draw.ellipse(blur_surf, (180, 180, 180, alpha), (0, 0, blur_w, blur_h))

                                    # Rotate to align with motion direction
                                    rotated = pygame.transform.rotate(blur_surf, math.degrees(-angle + math.pi/2))
                                    rect = rotated.get_rect(center=(int(px), int(py)))
                                    surface.blit(rotated, rect)

                # Draw the current clock hand position as blur only (no line)
                current_end_x = center_x + radius * math.cos(current_angle)
                current_end_y = center_y + radius * math.sin(current_angle)

                # Calculate entrance and exit fade for current position
                entrance_fade = min(1.0, self.swing_progress * 5)  # Fade in over first 20%
                exit_fade = min(1.0, (1.0 - self.swing_progress) * 5)  # Fade out over last 20%

                # Current speed for intensity and stretch
                current_speed = 1.0 - abs(self.swing_progress - 0.5) * 2
                current_speed = current_speed * current_speed
                speed_intensity = 0.4 + (current_speed * 0.6)

                current_fade = entrance_fade * exit_fade * speed_intensity

                if self.infused:
                    # Draw brightest blur at current position with stretch
                    for sample in range(8):
                        sample_t = sample / 7
                        px = center_x + (current_end_x - center_x) * sample_t
                        py = center_y + (current_end_y - center_y) * sample_t

                        width_factor = 1.0 - (sample_t * 0.5)
                        stretch = 1.2 + (current_speed * 3.0)  # Even more stretch for current position

                        # Outer hot pink glow (brightest) - stretched
                        alpha = int(100 * sample_t * current_fade)
                        if alpha > 0:
                            blur_w = int(40 * width_factor)
                            blur_h = int(40 * width_factor * stretch)
                            blur_surf = pygame.Surface((blur_w, blur_h), pygame.SRCALPHA)
                            pygame.draw.ellipse(blur_surf, (255, 105, 180, alpha), (0, 0, blur_w, blur_h))  # Hot pink #ff69b4

                            rotated = pygame.transform.rotate(blur_surf, math.degrees(-current_angle + math.pi/2))
                            rect = rotated.get_rect(center=(int(px), int(py)))
                            surface.blit(rotated, rect)

                        # Golden core (brightest) - stretched
                        alpha = int(220 * sample_t * current_fade)
                        if alpha > 0:
                            blur_w = int(24 * width_factor)
                            blur_h = int(24 * width_factor * stretch)
                            blur_surf = pygame.Surface((blur_w, blur_h), pygame.SRCALPHA)
                            pygame.draw.ellipse(blur_surf, (255, 215, 0, alpha), (0, 0, blur_w, blur_h))  # Gold #ffd700

                            rotated = pygame.transform.rotate(blur_surf, math.degrees(-current_angle + math.pi/2))
                            rect = rotated.get_rect(center=(int(px), int(py)))
                            surface.blit(rotated, rect)
                else:
                    # Draw brightest blur at current position with stretch
                    for sample in range(6):
                        sample_t = sample / 5
                        px = center_x + (current_end_x - center_x) * sample_t
                        py = center_y + (current_end_y - center_y) * sample_t

                        width_factor = 1.0 - (sample_t * 0.4)
                        stretch = 1.2 + (current_speed * 2.5)

                        # Gray blur (brightest) - stretched
                        alpha = int(180 * sample_t * current_fade)
                        if alpha > 0:
                            blur_w = int(32 * width_factor)
                            blur_h = int(32 * width_factor * stretch)
                            blur_surf = pygame.Surface((blur_w, blur_h), pygame.SRCALPHA)
                            pygame.draw.ellipse(blur_surf, (180, 180, 180, alpha), (0, 0, blur_w, blur_h))

                            rotated = pygame.transform.rotate(blur_surf, math.degrees(-current_angle + math.pi/2))
                            rect = rotated.get_rect(center=(int(px), int(py)))
                            surface.blit(rotated, rect)

        # Draw stone debris
        for debris in self.stone_debris:
            alpha = int(255 * (debris['lifetime'] / 1.0))
            if alpha > 0:
                color = (*debris['color'], alpha)
                debris_surf = pygame.Surface((int(debris['size'] * 2), int(debris['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(debris_surf, color,
                                 (int(debris['size']), int(debris['size'])),
                                 int(debris['size']))
                surface.blit(debris_surf, (int(debris['x'] - debris['size']), int(debris['y'] - debris['size'])))

        # Draw infused potpourri trail (draw behind other effects)
        if self.potpourri_trail is not None:
            for particle in self.potpourri_trail:
                if particle['lifetime'] > 0:
                    alpha = int(220 * (particle['lifetime'] / 1.5))  # Brighter alpha
                    if alpha > 0:
                        color = (*particle['color'], alpha)
                        particle_surf = pygame.Surface((int(particle['size'] * 3), int(particle['size'] * 3)), pygame.SRCALPHA)

                        # Draw layered glow for more vibrant petals
                        glow_size = particle['size'] + 6
                        pygame.draw.circle(particle_surf, (*particle['color'], alpha // 4),
                                         (int(particle['size'] * 1.5), int(particle['size'] * 1.5)),
                                         int(glow_size))

                        # Middle glow
                        glow_size = particle['size'] + 3
                        pygame.draw.circle(particle_surf, (*particle['color'], alpha // 2),
                                         (int(particle['size'] * 1.5), int(particle['size'] * 1.5)),
                                         int(glow_size))

                        # Core petal
                        pygame.draw.circle(particle_surf, color,
                                         (int(particle['size'] * 1.5), int(particle['size'] * 1.5)),
                                         int(particle['size']))

                        # Highlight for petal shine
                        pygame.draw.circle(particle_surf, (255, 255, 255, alpha // 2),
                                         (int(particle['size'] * 1.2), int(particle['size'] * 1.2)),
                                         int(particle['size'] * 0.4))

                        surface.blit(particle_surf, (int(particle['x'] - particle['size'] * 1.5), int(particle['y'] - particle['size'] * 1.5)))

        # Draw fragrance fumes (wispy, floating clouds)
        if self.fragrance_particles is not None:
            for fume in self.fragrance_particles:
                if fume['lifetime'] > 0:
                    alpha = int(120 * fume['alpha_mod'] * (fume['lifetime'] / 2.0))  # Slightly more visible
                    if alpha > 0:
                        color = (*fume['color'], alpha)
                        fume_surf = pygame.Surface((int(fume['size'] * 2.5), int(fume['size'] * 2.5)), pygame.SRCALPHA)

                        # Draw multiple overlapping circles for wispy cloud effect
                        center = fume['size'] * 1.25

                        # Outer diffuse cloud
                        for i in range(3):
                            offset_x = random.uniform(-fume['size'] * 0.3, fume['size'] * 0.3)
                            offset_y = random.uniform(-fume['size'] * 0.3, fume['size'] * 0.3)
                            cloud_size = fume['size'] * random.uniform(0.6, 0.9)
                            cloud_alpha = alpha // (3 + i)
                            pygame.draw.circle(fume_surf, (*fume['color'], cloud_alpha),
                                             (int(center + offset_x), int(center + offset_y)),
                                             int(cloud_size))

                        # Add purple tint to fumes for potpourri effect
                        tint_alpha = alpha // 3
                        pygame.draw.circle(fume_surf, (200, 150, 200, tint_alpha),
                                         (int(center), int(center)),
                                         int(fume['size'] * 0.7))

                        surface.blit(fume_surf, (int(fume['x'] - center), int(fume['y'] - center)))


class MelangeEminence:
    """
    MELANGE EMINENCE - Passive healing proc animation.
    Aromatic vapors rise from POTPOURRIST and are inhaled for healing.
    Base: 1 HP healing with gentle wisps
    Infused: 2 HP healing with richer, more vibrant fumes
    """
    def __init__(self, caster_x, caster_y, caster_unit, heal_amount=1, infused=False):
        self.caster_x = caster_x
        self.caster_y = caster_y
        self.caster = caster_unit
        self.heal_amount = heal_amount
        self.infused = infused

        self.phase = "rise"  # rise -> inhale -> glow -> complete
        self.timer = 0
        self.active = True

        # Aromatic vapor particles rising from pedestal
        self.vapor_particles = []

        # Potpourri petal particles (for infused only)
        self.petal_particles = []

        # Healing glow around caster
        self.glow_intensity = 0

        # Color scheme - always use potpourri colors
        self.colors = [
            (200, 100, 200),  # Purple
            (255, 150, 200),  # Pink
            (180, 100, 255),  # Violet
            (255, 100, 150),  # Rose
        ]

    def update(self, delta_time):
        """Update melange eminence animation."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "rise":
            # Aromatic vapors rise from pedestal (0.8s)
            if self.timer < 0.8:
                # Spawn wispy smoke/vapor particles
                if random.random() < 0.8:
                    angle = random.uniform(-0.4, 0.4)  # Mostly upward with some drift
                    speed = random.uniform(30, 60) if not self.infused else random.uniform(40, 80)

                    self.vapor_particles.append({
                        'x': self.caster_x + random.uniform(-20, 20),
                        'y': self.caster_y + 20,  # Start below caster
                        'vx': math.sin(angle) * speed * 0.5,
                        'vy': -speed,  # Rise upward
                        'lifetime': 1.5,
                        'size': random.uniform(8, 14) if not self.infused else random.uniform(10, 18),
                        'color': random.choice(self.colors),
                        'rotation': random.uniform(0, 360),
                        'rotation_speed': random.uniform(-40, 40),
                        'dissipate': random.uniform(0.7, 1.0)  # How fast it fades
                    })

                # Spawn potpourri petals (more frequent in infused)
                petal_chance = 0.4 if not self.infused else 0.7
                if random.random() < petal_chance:
                    angle = random.uniform(-0.5, 0.5)
                    speed = random.uniform(25, 50)

                    self.petal_particles.append({
                        'x': self.caster_x + random.uniform(-18, 18),
                        'y': self.caster_y + 20,
                        'vx': math.sin(angle) * speed * 0.6,
                        'vy': -speed * 0.8,  # Float up slower than vapor
                        'lifetime': 1.8,
                        'size': random.uniform(3, 6) if not self.infused else random.uniform(4, 8),
                        'color': random.choice(self.colors),
                        'rotation': random.uniform(0, 360),
                        'rotation_speed': random.uniform(-120, 120),
                        'flutter': random.uniform(0, math.pi * 2)  # For flutter motion
                    })
            else:
                self.phase = "inhale"
                self.timer = 0
                play_sound("melange_inhale")

        elif self.phase == "inhale":
            # Vapors are drawn toward caster's center (0.5s)
            if self.timer < 0.5:
                # Pull vapor particles toward caster
                for particle in self.vapor_particles:
                    dx = self.caster_x - particle['x']
                    dy = self.caster_y - 10 - particle['y']  # Toward head area
                    dist = math.sqrt(dx*dx + dy*dy)

                    if dist > 5:
                        pull_strength = 150 * (self.timer / 0.5)
                        particle['vx'] += (dx / dist) * pull_strength * delta_time
                        particle['vy'] += (dy / dist) * pull_strength * delta_time

                # Pull petal particles too
                for petal in self.petal_particles:
                    dx = self.caster_x - petal['x']
                    dy = self.caster_y - 10 - petal['y']
                    dist = math.sqrt(dx*dx + dy*dy)

                    if dist > 5:
                        pull_strength = 180 * (self.timer / 0.5)  # Petals pull in faster
                        petal['vx'] += (dx / dist) * pull_strength * delta_time
                        petal['vy'] += (dy / dist) * pull_strength * delta_time
            else:
                self.phase = "glow"
                self.timer = 0

        elif self.phase == "glow":
            # Healing glow pulses around caster (0.4s)
            if self.timer < 0.4:
                # Pulse intensity
                progress = self.timer / 0.4
                self.glow_intensity = math.sin(progress * math.pi) * 30
            else:
                self.phase = "complete"
                self.active = False

        # Update all vapor particles
        for particle in self.vapor_particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['rotation'] += particle['rotation_speed'] * delta_time
            particle['lifetime'] -= delta_time * particle['dissipate']

            # Add slight upward drift and horizontal waver
            particle['vy'] -= 20 * delta_time
            particle['vx'] += math.sin(self.timer * 3 + particle['rotation']) * 15 * delta_time

            # Expand as it rises (smoke behavior)
            particle['size'] += delta_time * 3

            if particle['lifetime'] <= 0:
                self.vapor_particles.remove(particle)

        # Update petal particles
        for petal in self.petal_particles[:]:
            petal['x'] += petal['vx'] * delta_time
            petal['y'] += petal['vy'] * delta_time
            petal['rotation'] += petal['rotation_speed'] * delta_time
            petal['lifetime'] -= delta_time

            # Flutter motion (sine wave horizontal)
            petal['flutter'] += delta_time * 4
            petal['vx'] += math.cos(petal['flutter']) * 30 * delta_time

            # Gentle upward drift
            petal['vy'] -= 15 * delta_time

            if petal['lifetime'] <= 0:
                self.petal_particles.remove(petal)

        return self.active

    def draw(self, surface):
        """Draw the melange eminence animation."""
        if not self.active:
            return

        # Draw healing glow
        if self.glow_intensity > 0:
            glow_size = int(40 + self.glow_intensity)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)

            # Multiple glow layers - always potpourri colors
            for i in range(3):
                layer_size = glow_size - i * 10
                if layer_size > 0:
                    glow_color = (200, 100, 200, int(80 / (i + 1)))
                    pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), layer_size)

            surface.blit(glow_surf, (int(self.caster_x - glow_size), int(self.caster_y - glow_size)))

        # Draw wispy vapor/smoke particles
        for particle in self.vapor_particles:
            if particle['lifetime'] > 0:
                fade = min(1.0, particle['lifetime'] / 1.5)
                alpha = int(100 * fade)  # More translucent for smoke

                if alpha > 0:
                    size = int(particle['size'])
                    vapor_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                    center = size * 2

                    # Wispy smoke - multiple overlapping circles with randomness
                    for i in range(5):
                        offset_x = random.uniform(-size * 0.4, size * 0.4)
                        offset_y = random.uniform(-size * 0.4, size * 0.4)
                        cloud_size = size * random.uniform(0.6, 1.0)
                        layer_alpha = alpha // (2 + i)

                        pygame.draw.circle(vapor_surf, (*particle['color'], layer_alpha),
                                         (int(center + offset_x), int(center + offset_y)),
                                         int(cloud_size))

                    surface.blit(vapor_surf, (int(particle['x'] - center), int(particle['y'] - center)))

        # Draw potpourri petals
        for petal in self.petal_particles:
            if petal['lifetime'] > 0:
                fade = min(1.0, petal['lifetime'] / 1.8)
                alpha = int(220 * fade)

                if alpha > 0:
                    size = int(petal['size'])
                    petal_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                    center = size * 2

                    # Petal shape - elongated with glow
                    # Outer glow
                    glow_size = size + 4
                    pygame.draw.circle(petal_surf, (*petal['color'], alpha // 4),
                                     (int(center), int(center)),
                                     int(glow_size))

                    # Middle glow
                    glow_size = size + 2
                    pygame.draw.circle(petal_surf, (*petal['color'], alpha // 2),
                                     (int(center), int(center)),
                                     int(glow_size))

                    # Core petal
                    pygame.draw.circle(petal_surf, (*petal['color'], alpha),
                                     (int(center), int(center)),
                                     size)

                    # Highlight for shine
                    pygame.draw.circle(petal_surf, (255, 255, 255, alpha // 3),
                                     (int(center * 0.8), int(center * 0.8)),
                                     int(size * 0.5))

                    # Rotate petal
                    rotated = pygame.transform.rotate(petal_surf, petal['rotation'])
                    rect = rotated.get_rect(center=(int(petal['x']), int(petal['y'])))
                    surface.blit(rotated, rect)


# ============================================================================
# MELANGE EMINENCE PASSIVE HEALING ANIMATIONS
# ============================================================================

class MelangeEminenceHealAnimation:
    """
    Normal Melange Eminence passive healing animation (1 HP).
    Gentle, soothing green potpourri fumes restoring POTPOURRIST.

    Phases:
    1. Inhale - Particles converge toward POTPOURRIST
    2. Restoration - Green healing aura pulses
    3. Exhale - Particles disperse gently
    """

    # Tropical flower colors (subset of infused colors - softer palette)
    HEAL_COLORS = [
        (255, 215, 0),    # Gold
        (255, 165, 0),    # Orange
        (186, 85, 211),   # Medium orchid
        (147, 112, 219),  # Medium purple
    ]

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None, heal_amount=1):
        """Initialize normal Melange Eminence healing animation."""
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.heal_amount = heal_amount

        # Convert position to screen coords
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "inhale"
        self.timer = 0
        self.active = True

        # Phase durations
        self.inhale_duration = 0.3
        self.restore_duration = 0.6
        self.exhale_duration = 0.3

        # Particle effects
        self.fume_particles = []
        self._spawn_initial_particles()

        # Aura effect
        self.aura_intensity = 0
        self.aura_radius = 0

        # Aromatic vapors drawn in for healing
        play_sound("melange_heal_inhale")

    def _spawn_initial_particles(self):
        """Spawn particles for inhale phase."""
        num_particles = 12
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            distance = random.uniform(40, 60)

            self.fume_particles.append({
                'x': self.target_x + math.cos(angle) * distance,
                'y': self.target_y + math.sin(angle) * distance,
                'target_x': self.target_x,
                'target_y': self.target_y,
                'size': random.uniform(2, 4),
                'color': random.choice(self.HEAL_COLORS),
                'lifetime': 1.2,
                'phase_offset': random.uniform(0, math.pi * 2)
            })

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "inhale":
            if self.timer >= self.inhale_duration:
                self.phase = "restore"
                self.timer = 0
                play_sound("melange_heal_restore")

        elif self.phase == "restore":
            # Pulse aura
            progress = self.timer / self.restore_duration
            pulse = (math.sin(progress * math.pi * 4) + 1) / 2
            self.aura_intensity = 0.7 + 0.3 * pulse
            self.aura_radius = 30 + 10 * pulse

            # Spawn restoration sparkles
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(15, 25)
                self.fume_particles.append({
                    'x': self.target_x + math.cos(angle) * distance,
                    'y': self.target_y + math.sin(angle) * distance,
                    'vx': 0,
                    'vy': random.uniform(-20, -10),
                    'size': random.uniform(2, 3),
                    'color': random.choice(self.HEAL_COLORS),
                    'lifetime': 0.5,
                    'phase_offset': 0
                })

            if self.timer >= self.restore_duration:
                self.phase = "exhale"
                self.timer = 0
                self._spawn_exhale_particles()

        elif self.phase == "exhale":
            # Fade out
            self.aura_intensity = max(0, 1.0 - (self.timer / self.exhale_duration))

            if self.timer >= self.exhale_duration:
                self.active = False

        # Update particles
        for particle in self.fume_particles[:]:
            particle['lifetime'] -= delta_time

            if particle['lifetime'] <= 0:
                self.fume_particles.remove(particle)
                continue

            if self.phase == "inhale":
                # Move toward target
                dx = particle['target_x'] - particle['x']
                dy = particle['target_y'] - particle['y']
                distance = math.sqrt(dx*dx + dy*dy)

                if distance > 1:
                    speed = 80
                    particle['x'] += (dx / distance) * speed * delta_time
                    particle['y'] += (dy / distance) * speed * delta_time

            elif self.phase == "restore":
                # Orbit gently
                if 'vx' in particle and 'vy' in particle:
                    particle['x'] += particle['vx'] * delta_time
                    particle['y'] += particle['vy'] * delta_time

            elif self.phase == "exhale":
                # Disperse outward
                if 'disperse_vx' in particle:
                    particle['x'] += particle['disperse_vx'] * delta_time
                    particle['y'] += particle['disperse_vy'] * delta_time

        return self.active

    def _spawn_exhale_particles(self):
        """Spawn particles dispersing outward."""
        for particle in self.fume_particles:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 50)
            particle['disperse_vx'] = math.cos(angle) * speed
            particle['disperse_vy'] = math.sin(angle) * speed

    def draw(self, surface):
        """Draw the healing animation."""
        if not self.active:
            return

        # Draw healing aura
        if self.phase == "restore" or self.phase == "exhale":
            if self.aura_intensity > 0:
                aura_alpha = int(120 * self.aura_intensity)
                if aura_alpha > 0:
                    aura_surf = pygame.Surface((int(self.aura_radius * 2), int(self.aura_radius * 2)), pygame.SRCALPHA)
                    # Warm golden/purple aura instead of green
                    pygame.draw.circle(aura_surf, (200, 150, 100, aura_alpha),
                                     (int(self.aura_radius), int(self.aura_radius)),
                                     int(self.aura_radius))
                    surface.blit(aura_surf, (int(self.target_x - self.aura_radius),
                                            int(self.target_y - self.aura_radius)))

        # Draw fume particles
        for particle in self.fume_particles:
            fade = min(1.0, particle['lifetime'] / 0.3)
            alpha = int(200 * fade)

            if alpha > 0:
                size = particle['size']
                particle_surf = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*particle['color'], alpha),
                                 (int(size), int(size)), int(size))
                surface.blit(particle_surf, (int(particle['x'] - size), int(particle['y'] - size)))

        # Draw healing text
        if self.phase == "restore":
            progress = self.timer / self.restore_duration
            y_offset = -int(progress * 25)
            text_alpha = int(255 * (1.0 - progress))

            if text_alpha > 0:
                font = pygame.font.Font(None, 28)
                # Golden text instead of green
                text = font.render(f"+{self.heal_amount}", True, (255, 200, 80))
                text.set_alpha(text_alpha)

                text_rect = text.get_rect(center=(int(self.target_x), int(self.target_y + y_offset - 20)))
                surface.blit(text, text_rect)


class MelangeEminenceInfusedHealAnimation:
    """
    Infused Melange Eminence passive healing animation (2 HP).
    Vibrant, tropical potpourri burst with aromatic power.

    Phases:
    1. Inhale - Colorful particles swirl inward dramatically
    2. Restoration - Multicolor aura pulses with tropical colors
    3. Flourish - Explosive burst of petals radiating outward
    """

    # Tropical flower colors (from infused Demilune)
    TROPICAL_COLORS = [
        (255, 215, 0),    # Gold
        (255, 105, 180),  # Hot pink
        (255, 99, 71),    # Tomato
        (255, 165, 0),    # Orange
        (147, 112, 219),  # Medium purple
        (186, 85, 211),   # Medium orchid
        (0, 206, 209),    # Dark turquoise
        (255, 20, 147)    # Deep pink
    ]

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None, heal_amount=2):
        """Initialize infused Melange Eminence healing animation."""
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.heal_amount = heal_amount

        # Convert position to screen coords
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "inhale"
        self.timer = 0
        self.active = True

        # Phase durations
        self.inhale_duration = 0.4
        self.restore_duration = 0.8
        self.flourish_duration = 0.6

        # Particle effects
        self.petal_particles = []
        self._spawn_initial_petals()

        # Aura effect
        self.aura_intensity = 0
        self.aura_radius = 0
        self.color_cycle = 0

        # Rich infused vapors drawn in
        play_sound("melange_heal_infused_inhale")

    def _spawn_initial_petals(self):
        """Spawn petal particles for inhale phase."""
        num_petals = 20
        for i in range(num_petals):
            angle = (i / num_petals) * 2 * math.pi + random.uniform(-0.2, 0.2)
            distance = random.uniform(50, 80)

            self.petal_particles.append({
                'x': self.target_x + math.cos(angle) * distance,
                'y': self.target_y + math.sin(angle) * distance,
                'target_x': self.target_x,
                'target_y': self.target_y,
                'size': random.uniform(3, 6),
                'color': random.choice(self.TROPICAL_COLORS),
                'lifetime': 1.8,
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-180, 180),
                'phase_offset': random.uniform(0, math.pi * 2)
            })

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time
        self.color_cycle += delta_time * 3

        # Phase transitions
        if self.phase == "inhale":
            if self.timer >= self.inhale_duration:
                self.phase = "restore"
                self.timer = 0
                play_sound("melange_heal_infused_restore")

        elif self.phase == "restore":
            # Strong pulsing aura
            progress = self.timer / self.restore_duration
            pulse = (math.sin(progress * math.pi * 6) + 1) / 2
            self.aura_intensity = 0.8 + 0.2 * pulse
            self.aura_radius = 35 + 15 * pulse

            # Spawn restoration sparkles (more frequent than normal)
            if random.random() < 0.5:
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(20, 30)
                self.petal_particles.append({
                    'x': self.target_x + math.cos(angle) * distance,
                    'y': self.target_y + math.sin(angle) * distance,
                    'vx': random.uniform(-10, 10),
                    'vy': random.uniform(-30, -15),
                    'size': random.uniform(3, 5),
                    'color': random.choice(self.TROPICAL_COLORS),
                    'lifetime': 0.6,
                    'rotation': random.uniform(0, 360),
                    'rotation_speed': random.uniform(-180, 180),
                    'phase_offset': 0
                })

            if self.timer >= self.restore_duration:
                self.phase = "flourish"
                self.timer = 0
                self._spawn_flourish_burst()

        elif self.phase == "flourish":
            # Fade out
            self.aura_intensity = max(0, 1.0 - (self.timer / self.flourish_duration))

            if self.timer >= self.flourish_duration:
                self.active = False

        # Update particles
        for particle in self.petal_particles[:]:
            particle['lifetime'] -= delta_time
            particle['rotation'] += particle['rotation_speed'] * delta_time

            if particle['lifetime'] <= 0:
                self.petal_particles.remove(particle)
                continue

            if self.phase == "inhale":
                # Spiral toward target
                dx = particle['target_x'] - particle['x']
                dy = particle['target_y'] - particle['y']
                distance = math.sqrt(dx*dx + dy*dy)

                if distance > 1:
                    speed = 120
                    # Add spiral motion
                    angle = math.atan2(dy, dx) + math.sin(self.timer * 8) * 0.3
                    particle['x'] += math.cos(angle) * speed * delta_time
                    particle['y'] += math.sin(angle) * speed * delta_time

            elif self.phase == "restore":
                # Orbit with slight drift
                if 'vx' in particle and 'vy' in particle:
                    particle['x'] += particle['vx'] * delta_time
                    particle['y'] += particle['vy'] * delta_time

            elif self.phase == "flourish":
                # Burst outward
                if 'burst_vx' in particle:
                    particle['x'] += particle['burst_vx'] * delta_time
                    particle['y'] += particle['burst_vy'] * delta_time

        return self.active

    def _spawn_flourish_burst(self):
        """Spawn explosive burst of petals."""
        num_burst = 15
        for i in range(num_burst):
            angle = (i / num_burst) * 2 * math.pi
            speed = random.uniform(80, 120)

            self.petal_particles.append({
                'x': self.target_x,
                'y': self.target_y,
                'burst_vx': math.cos(angle) * speed,
                'burst_vy': math.sin(angle) * speed,
                'size': random.uniform(4, 7),
                'color': random.choice(self.TROPICAL_COLORS),
                'lifetime': 0.6,
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-360, 360),
                'phase_offset': 0
            })

        # Set burst velocities for existing particles
        for particle in self.petal_particles:
            if 'burst_vx' not in particle:
                dx = particle['x'] - self.target_x
                dy = particle['y'] - self.target_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > 0:
                    speed = random.uniform(60, 100)
                    particle['burst_vx'] = (dx / distance) * speed
                    particle['burst_vy'] = (dy / distance) * speed

    def draw(self, surface):
        """Draw the infused healing animation."""
        if not self.active:
            return

        # Draw multicolor healing aura
        if self.phase == "restore" or self.phase == "flourish":
            if self.aura_intensity > 0:
                # Cycle through colors
                color_index = int(self.color_cycle) % len(self.TROPICAL_COLORS)
                next_color_index = (color_index + 1) % len(self.TROPICAL_COLORS)

                blend = (self.color_cycle % 1.0)
                color1 = self.TROPICAL_COLORS[color_index]
                color2 = self.TROPICAL_COLORS[next_color_index]

                blended_color = tuple(int(c1 * (1 - blend) + c2 * blend) for c1, c2 in zip(color1, color2))

                aura_alpha = int(150 * self.aura_intensity)
                if aura_alpha > 0:
                    aura_surf = pygame.Surface((int(self.aura_radius * 2), int(self.aura_radius * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(aura_surf, (*blended_color, aura_alpha),
                                     (int(self.aura_radius), int(self.aura_radius)),
                                     int(self.aura_radius))
                    # Add golden glow layer
                    pygame.draw.circle(aura_surf, (255, 215, 0, aura_alpha // 3),
                                     (int(self.aura_radius), int(self.aura_radius)),
                                     int(self.aura_radius * 1.2))
                    surface.blit(aura_surf, (int(self.target_x - self.aura_radius),
                                            int(self.target_y - self.aura_radius)))

        # Draw petal particles
        for particle in self.petal_particles:
            fade = min(1.0, particle['lifetime'] / 0.4)
            alpha = int(220 * fade)

            if alpha > 0:
                size = particle['size']
                petal_surf = pygame.Surface((int(size * 3), int(size * 3)), pygame.SRCALPHA)
                center = size * 1.5

                # Draw petal shape
                pygame.draw.circle(petal_surf, (*particle['color'], alpha),
                                 (int(center), int(center)), int(size))
                # Add shine
                pygame.draw.circle(petal_surf, (255, 255, 255, alpha // 2),
                                 (int(center * 0.7), int(center * 0.7)), int(size * 0.4))

                # Rotate petal
                rotated = pygame.transform.rotate(petal_surf, particle['rotation'])
                rect = rotated.get_rect(center=(int(particle['x']), int(particle['y'])))
                surface.blit(rotated, rect)

        # Draw healing text with golden glow
        if self.phase == "restore":
            progress = self.timer / self.restore_duration
            y_offset = -int(progress * 30)
            text_alpha = int(255 * (1.0 - progress))

            if text_alpha > 0:
                font = pygame.font.Font(None, 36)
                # Golden text
                text = font.render(f"+{self.heal_amount}", True, (255, 215, 0))
                text.set_alpha(text_alpha)

                # Outline for visibility
                outline = font.render(f"+{self.heal_amount}", True, (200, 100, 50))
                outline.set_alpha(text_alpha // 2)

                text_rect = text.get_rect(center=(int(self.target_x), int(self.target_y + y_offset - 25)))
                outline_rect = outline.get_rect(center=(int(self.target_x + 1), int(self.target_y + y_offset - 24)))

                surface.blit(outline, outline_rect)
                surface.blit(text, text_rect)




# ============================================================================
# POTPOURRIST BASIC ATTACK - PEDESTAL SWING WITH AROMATIC SCATTER
# ============================================================================

class PotpourristAromaticAttack:
    """
    POTPOURRIST basic attack animation - swings massive granite pedestal.
    Pedestal arc swing releases colorful potpourri scatter on impact.
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
        self.phase = "windup"  # windup → swing → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.windup_duration = 0.12
        self.swing_duration = 0.28
        self.impact_duration = 0.2

        # Swing progress for weapon drawing
        self.swing_progress = 0.0

        # Vibrant potpourri colors from the bowl
        self.colors = [
            (255, 215, 0),    # Gold
            (147, 112, 219),  # Purple/Lavender
            (255, 99, 71),    # Red/Tomato
            (255, 105, 180),  # Pink/Hot Pink
            (0, 206, 209),    # Cyan/Turquoise
            (255, 165, 0),    # Orange
            (218, 112, 214),  # Orchid
            (255, 255, 0),    # Yellow
        ]

    def _trigger_windup(self):
        """Phase 1: Windup pedestal swing."""

        # Small dust particles as pedestal pulls back

        for _ in range(6):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 60)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Gray granite dust
            color = random.choice([(169, 169, 169), (128, 128, 128)])

            from .core import Particle
            particle = Particle(self.attacker.x, self.attacker.y, vx, vy, color,
                              size=random.uniform(1, 2), lifetime=0.15)
            particle.gravity = 150
            self.particle_emitter.particles.append(particle)

    def _trigger_swing(self):
        """Phase 2: Swing pedestal (no particles during swing)."""
        play_sound("aromatic_attack_swing")
        # Just the visual arc swing - no potpourri flies out until impact

    def _trigger_impact(self):
        """Phase 3: Potpourri impact burst."""
        play_sound("aromatic_attack_impact")

        # Colorful aromatic burst at target
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = random.choice(self.colors)

            from .core import Particle
            particle = Particle(self.target.x, self.target.y, vx, vy, color,
                              size=random.uniform(3, 7), lifetime=random.uniform(0.2, 0.4))
            particle.gravity = 120
            self.particle_emitter.particles.append(particle)

        # Moderate impact
        self.target.shake_intensity = 10
        self.screen_shake(5, 0.16)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "windup":
            if self.timer == 0 or not hasattr(self, "_windup_triggered"):
                self._trigger_windup()
                self._windup_triggered = True

            if self.timer >= self.windup_duration:
                self.phase = "swing"
                self.timer = 0
                self._trigger_swing()

        elif self.phase == "swing":
            # Update swing progress for weapon drawing
            self.swing_progress = min(1.0, self.timer / self.swing_duration)

            if self.timer >= self.swing_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw pedestal swing with potpourri scatter."""
        import pygame

        # Draw windup tension (slight gray aura)
        if self.phase == "windup":
            progress = self.timer / self.windup_duration
            glow_radius = int(15 * progress)

            if glow_radius > 2:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (128, 128, 128, int(80 * progress)),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(self.attacker.x - glow_radius),
                                        int(self.attacker.y - glow_radius)))

        # Draw visible pedestal swing arc during swing phase
        if self.phase == "swing":
            # Calculate perpendicular vector for arc sweep
            perp_x = -self.dy
            perp_y = self.dx

            # Draw the pedestal as it swings
            arc_width = 35  # Wide arc for heavy pedestal
            pedestal_length = self.distance + 25

            # Calculate arc points along the swing
            points = []
            num_segments = 15

            for i in range(num_segments):
                progress = (i / (num_segments - 1)) * self.swing_progress

                # Position along attack vector
                base_x = self.attacker.x + self.dx * pedestal_length * progress
                base_y = self.attacker.y + self.dy * pedestal_length * progress

                # Arc offset (sine curve for natural weapon sweep)
                arc_offset = math.sin(progress * math.pi) * arc_width

                # Calculate point position
                point_x = base_x + perp_x * arc_offset
                point_y = base_y + perp_y * arc_offset

                points.append((int(point_x), int(point_y)))

            # Draw the pedestal arc
            if len(points) >= 2:
                # Draw granite pedestal arc - gray stone color matching the sprite
                # Outer darker outline
                pygame.draw.lines(surface, (105, 105, 105), False, points, 10)  # #696969 - darker gray outline
                # Inner lighter granite
                pygame.draw.lines(surface, (169, 169, 169), False, points, 6)   # #a9a9a9 - lighter gray core

        # Draw impact burst (multi-colored explosion)
        if self.phase == "impact":
            progress = self.timer / self.impact_duration
            if progress < 0.6:
                flash_alpha = int(200 * (1.0 - progress / 0.6))
                flash_radius = int(30 * (1.0 + progress * 0.6))

                # Multi-colored potpourri burst
                for i, color in enumerate(self.colors):
                    angle_offset = (i / len(self.colors)) * 2 * math.pi
                    offset_x = math.cos(angle_offset) * 10 * progress
                    offset_y = math.sin(angle_offset) * 10 * progress

                    layer_radius = int(flash_radius * (1.0 - i * 0.08))
                    if layer_radius > 2:
                        flash_surf = pygame.Surface((layer_radius * 2, layer_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(flash_surf, (*color, flash_alpha // (i + 1)),
                                         (layer_radius, layer_radius), layer_radius)
                        surface.blit(flash_surf, (int(self.target.x - layer_radius + offset_x),
                                                 int(self.target.y - layer_radius + offset_y)))


# ============================================================================
# SELENIC BACKDRAFT ZONE ANIMATION (Upgraded Demilune)
# ============================================================================

class SelenicBackdraftZone:
    """
    Selenic Backdraft Zone - Persistent ground effect for upgraded Demilune.
    Shows moonlight shining up from beneath the ground with dark fuming fog.

    The zone appears in the mirrored arc opposite to the Demilune swing direction.
    Enemies within the zone cannot attack POTPOURRIST.

    Visual: White/cream light emerging from ground + dark wispy smoke rising
    Color scheme from demilune.svg icon.
    """

    def __init__(self, zone_tiles, caster_unit, camera, game):
        """
        Initialize Selenic Backdraft Zone.

        Args:
            zone_tiles: List of (grid_y, grid_x) tuples for zone coverage
            caster_unit: AnimatedUnit reference to check zone duration
            camera: Camera for coordinate conversion
            game: Game instance to check zone_duration attribute
        """
        self.zone_tiles = zone_tiles  # Grid coordinates
        self.caster = caster_unit
        self.camera = camera
        self.game = game

        # Animation state
        self.phase = "fade_in"  # fade_in -> active -> fade_out -> complete
        self.timer = 0
        self.active = True

        # Phase durations
        self.fade_in_duration = 0.4
        self.fade_out_duration = 0.6

        # Moonlight zone appearing
        play_sound("selenic_backdraft_appear")

        # Color scheme from demilune.svg
        self.color_light_core = (255, 255, 255)      # #ffffff - bright white
        self.color_light_mid = (232, 232, 216)       # #e8e8d8 - pale cream
        self.color_light_edge = (216, 200, 184)      # #d8c8b8 - warm cream
        self.color_fume_dark1 = (26, 26, 26)         # #1a1a1a - deep shadow
        self.color_fume_dark2 = (42, 42, 42)         # #2a2a2a - medium shadow
        self.color_fume_dark3 = (58, 58, 58)         # #3a3a3a - lighter shadow

        # Convert zone tiles to screen coordinates
        self.screen_tiles = []
        for grid_y, grid_x in zone_tiles:
            screen_x, screen_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
            self.screen_tiles.append((screen_x, screen_y))

        # Fume particles (dark smoke rising from each tile)
        self.fume_particles = []

        # Global fade for fade in/out
        self.global_alpha = 0.0

        # Pulsing effect timer
        self.pulse_timer = 0

    def _spawn_fume_particles(self, delta_time):
        """Spawn dark smoke particles rising from zone tiles."""
        import random
        import math

        # Spawn rate: smaller but more frequent particles
        if self.phase == "fade_in":
            spawn_rate = 7  # particles per tile per second
        elif self.phase == "active":
            spawn_rate = 3  # particles per tile per second
        else:  # fade_out
            spawn_rate = 1.5  # particles per tile per second

        for screen_x, screen_y in self.screen_tiles:
            # Spawn particles based on delta_time
            spawn_count = int(spawn_rate * delta_time)
            if random.random() < (spawn_rate * delta_time - spawn_count):
                spawn_count += 1

            for _ in range(spawn_count):
                # Randomize spawn position within tile
                offset_x = random.uniform(-20, 20)
                offset_y = random.uniform(-15, 15)

                self.fume_particles.append({
                    'x': screen_x + offset_x,
                    'y': screen_y + offset_y,
                    'vx': random.uniform(-8, 8),  # Slow horizontal drift
                    'vy': random.uniform(-40, -60),  # Rising upward
                    'lifetime': random.uniform(0.8, 1.4),  # Even shorter lifetime
                    'max_lifetime': random.uniform(0.8, 1.4),
                    'size': random.uniform(4, 10),  # Much smaller particles (was 8-16)
                    'color': random.choice([
                        self.color_fume_dark1,
                        self.color_fume_dark2,
                        self.color_fume_dark3
                    ]),
                    'swirl_phase': random.uniform(0, math.pi * 2),
                    'swirl_speed': random.uniform(1.5, 3.0)
                })


    def update(self, delta_time):
        """Update zone animation. Returns True if still active."""
        if not self.active:
            return False

        import math

        self.timer += delta_time
        self.pulse_timer += delta_time

        # Check if zone still exists on caster
        zone_active = False
        if self.caster and hasattr(self.caster, 'game_unit'):
            game_unit = self.caster.game_unit
            if hasattr(game_unit, 'demilune_zone_duration') and game_unit.demilune_zone_duration > 0:
                zone_active = True

        # Phase management
        if self.phase == "fade_in":
            # Fade in the zone
            progress = min(1.0, self.timer / self.fade_in_duration)
            self.global_alpha = progress

            if self.timer >= self.fade_in_duration:
                self.phase = "active"
                self.timer = 0

        elif self.phase == "active":
            self.global_alpha = 1.0

            # Check if zone expired
            if not zone_active:
                self.phase = "fade_out"
                self.timer = 0

        elif self.phase == "fade_out":
            # Fade out the zone
            progress = min(1.0, self.timer / self.fade_out_duration)
            self.global_alpha = 1.0 - progress

            if self.timer >= self.fade_out_duration:
                self.phase = "complete"
                self.active = False

        # Spawn fume particles
        self._spawn_fume_particles(delta_time)

        # Update fume particles
        for fume in self.fume_particles[:]:
            # Swirling motion
            fume['swirl_phase'] += fume['swirl_speed'] * delta_time
            swirl_x = math.sin(fume['swirl_phase']) * 8

            # Move particle
            fume['x'] += (fume['vx'] + swirl_x) * delta_time
            fume['y'] += fume['vy'] * delta_time

            # Age particle
            fume['lifetime'] -= delta_time
            if fume['lifetime'] <= 0:
                self.fume_particles.remove(fume)

        return self.active

    def draw(self, surface):
        """Draw the selenic backdraft zone."""
        if not self.active or self.global_alpha <= 0:
            return

        import pygame
        import math

        # Pulsing intensity (breathing effect - high intensity)
        pulse = 0.5 + 0.5 * math.sin(self.pulse_timer * 2.0)

        # Draw ground light on each tile (balanced for visibility)
        for screen_x, screen_y in self.screen_tiles:
            # Large outer glow (cream) - increased slightly
            outer_radius = 32
            outer_alpha = int(30 * self.global_alpha * pulse)
            if outer_alpha > 0:
                glow_surf = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf,
                    (*self.color_light_edge, outer_alpha),
                    (outer_radius, outer_radius),
                    outer_radius
                )
                surface.blit(glow_surf, (int(screen_x - outer_radius), int(screen_y - outer_radius)))

            # Medium glow (pale cream) - increased slightly
            mid_radius = 22
            mid_alpha = int(50 * self.global_alpha * pulse)
            if mid_alpha > 0:
                glow_surf = pygame.Surface((mid_radius * 2, mid_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf,
                    (*self.color_light_mid, mid_alpha),
                    (mid_radius, mid_radius),
                    mid_radius
                )
                surface.blit(glow_surf, (int(screen_x - mid_radius), int(screen_y - mid_radius)))

            # Bright core (white) - increased slightly
            core_radius = 12
            core_alpha = int(70 * self.global_alpha * pulse)
            if core_alpha > 0:
                glow_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf,
                    (*self.color_light_core, core_alpha),
                    (core_radius, core_radius),
                    core_radius
                )
                surface.blit(glow_surf, (int(screen_x - core_radius), int(screen_y - core_radius)))

        # Draw dark fume particles (on top of light)
        for fume in self.fume_particles:
            # Calculate fade based on lifetime
            age_progress = 1.0 - (fume['lifetime'] / fume['max_lifetime'])

            # Fade in quickly, fade out slowly
            if age_progress < 0.2:
                alpha_factor = age_progress / 0.2  # Fade in over first 20%
            else:
                alpha_factor = 1.0 - ((age_progress - 0.2) / 0.8) * 0.7  # Fade out over remaining 80%

            alpha = int(80 * alpha_factor * self.global_alpha)  # reduced from 140

            if alpha > 5:
                size = int(fume['size'])
                fume_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

                # Draw wispy smoke blob (soft circle)
                pygame.draw.circle(
                    fume_surf,
                    (*fume['color'], alpha),
                    (size, size),
                    size
                )

                surface.blit(fume_surf, (int(fume['x'] - size), int(fume['y'] - size)))

