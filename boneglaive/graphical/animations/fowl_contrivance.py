#!/usr/bin/env python3
"""
FOWL CONTRIVANCE Animation Classes
Skill animations for the FOWL CONTRIVANCE unit (mechanical peacock rail artillery platform).
"""
import pygame
import random
import math
from .core import TILE_SIZE, COLOR_DAMAGE, COLOR_SKILL


# ============================================================================
# PARABOL ANIMATION (Mortar Barrage)
# ============================================================================

class LaunchSmoke:
    """
    Smoke puff at launch position when mortars fire.
    Grey smoke expanding and fading out.
    """
    def __init__(self, launch_x, launch_y):
        self.center_x = launch_x
        self.center_y = launch_y
        self.timer = 0
        self.duration = 0.4
        self.active = True
        self.max_radius = 25

    def update(self, delta_time):
        """Update smoke expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding smoke puff."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expand with ease-out
        radius = int(self.max_radius * progress)

        # Fade out as it expands
        alpha = int(150 * (1.0 - progress))

        if alpha > 0 and radius > 0:
            smoke_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Dark grey smoke - multiple layers for depth
            for i in range(3):
                layer_radius = radius - (i * 5)
                if layer_radius > 0:
                    layer_alpha = alpha - (i * 30)
                    if layer_alpha > 0:
                        pygame.draw.circle(smoke_surf, (90, 90, 90, layer_alpha),
                                         (radius, radius), layer_radius)

            surface.blit(smoke_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class MortarShell:
    """
    Massive single mortar shell following parabolic arc trajectory.
    Thick glowing orange/yellow trail showing the shell's devastating path.
    """
    def __init__(self, start_x, start_y, target_x, target_y, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.timer = -delay  # Negative for staggered start
        self.duration = 0.7  # Slower arc for massive shell
        self.active = True

        # Calculate arc parameters
        self.dx = target_x - start_x
        self.dy = target_y - start_y
        self.distance = math.sqrt(self.dx * self.dx + self.dy * self.dy)

        # Higher arc for dramatic impact
        self.arc_height = min(150, self.distance * 0.5)

        # Trail particles
        self.trail_points = []

    def update(self, delta_time):
        """Update shell position along arc."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:  # Only update if delay has passed
            # Add current position to trail
            progress = min(1.0, self.timer / self.duration)
            current_x = self.start_x + self.dx * progress

            # Parabolic arc: y = -4h(x-0.5)^2 + h, where h is arc_height
            arc_progress = progress - 0.5
            arc_y_offset = -4 * self.arc_height * (arc_progress * arc_progress) + self.arc_height
            current_y = self.start_y + self.dy * progress - arc_y_offset

            self.trail_points.append({
                'x': current_x,
                'y': current_y,
                'lifetime': 0.3,  # Longer trail lifetime for visibility
                'age': 0
            })

            # Age and remove old trail points
            for point in self.trail_points:
                point['age'] += delta_time

            self.trail_points = [p for p in self.trail_points if p['age'] < p['lifetime']]

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw massive shell and its thick glowing trail."""
        if not self.active or self.timer < 0:
            return

        # Draw thick trail as fading orange line segments with glow
        if len(self.trail_points) > 1:
            for i in range(len(self.trail_points) - 1):
                p1 = self.trail_points[i]
                p2 = self.trail_points[i + 1]

                # Fade based on age
                alpha = int(220 * (1.0 - p1['age'] / p1['lifetime']))

                if alpha > 20:
                    trail_surf = pygame.Surface((abs(int(p2['x'] - p1['x'])) + 24,
                                                abs(int(p2['y'] - p1['y'])) + 24), pygame.SRCALPHA)

                    # Thick glowing trail with multiple layers
                    start_local = (12, 12)
                    end_local = (int(p2['x'] - p1['x'] + 12), int(p2['y'] - p1['y'] + 12))

                    # Outer glow (widest)
                    pygame.draw.line(trail_surf, (255, 150, 0, alpha // 3),
                                   start_local, end_local, 12)
                    # Mid layer
                    pygame.draw.line(trail_surf, (255, 180, 0, alpha // 2),
                                   start_local, end_local, 8)
                    # Inner bright layer
                    pygame.draw.line(trail_surf, (255, 220, 100, alpha),
                                   start_local, end_local, 4)

                    surface.blit(trail_surf, (int(p1['x']) - 12, int(p1['y']) - 12))

        # Draw massive shell as large glowing orb at current position
        if self.trail_points:
            current = self.trail_points[-1]
            shell_surf = pygame.Surface((32, 32), pygame.SRCALPHA)

            # Outer glow (largest)
            pygame.draw.circle(shell_surf, (255, 150, 0, 100), (16, 16), 16)
            # Mid glow
            pygame.draw.circle(shell_surf, (255, 180, 0, 150), (16, 16), 12)
            # Main shell body
            pygame.draw.circle(shell_surf, (255, 200, 50, 220), (16, 16), 9)
            # Inner core
            pygame.draw.circle(shell_surf, (255, 230, 150, 255), (16, 16), 6)
            # Hot center
            pygame.draw.circle(shell_surf, (255, 255, 255, 255), (16, 16), 3)

            surface.blit(shell_surf, (int(current['x']) - 16, int(current['y']) - 16))


class ExplosionFireball:
    """
    Orange/yellow fireball explosion at impact point.
    Rapidly expands then fades out.
    Primary explosion is massive, splash explosions are smaller.
    """
    def __init__(self, center_x, center_y, is_primary=False):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.4 if is_primary else 0.3  # Primary lasts longer
        self.active = True

        # Primary (center) explosion is much larger for massive shell
        self.max_radius = 55 if is_primary else 30
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
        """Draw expanding fireball."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fast expansion, then fade
        if progress < 0.4:
            radius = int(self.max_radius * (progress / 0.4))
        else:
            radius = self.max_radius

        # Fade out
        alpha = int(255 * (1.0 - progress))

        if alpha > 0 and radius > 0:
            fireball_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Multiple layers for depth
            # Outer orange glow
            outer_radius = radius + 8
            pygame.draw.circle(fireball_surf, (255, 102, 0, alpha // 3),
                             (center, center), outer_radius)

            # Main orange fireball
            pygame.draw.circle(fireball_surf, (255, 102, 0, alpha),
                             (center, center), radius)

            # Inner yellow core
            inner_radius = int(radius * 0.6)
            pygame.draw.circle(fireball_surf, (255, 204, 0, alpha),
                             (center, center), inner_radius)

            # Bright center
            if progress < 0.3:
                core_radius = int(radius * 0.3)
                pygame.draw.circle(fireball_surf, (255, 255, 200, alpha),
                                 (center, center), core_radius)

            surface.blit(fireball_surf, (int(self.center_x - center), int(self.center_y - center)))


class ShockwaveRing:
    """
    Expanding shockwave ring from impact.
    Darkened orange ring expanding outward.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.5
        self.active = True
        self.max_radius = 50

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

        # Expand outward
        radius = int(self.max_radius * progress)

        # Fade out as expanding
        alpha = int(180 * (1.0 - progress))

        if alpha > 20 and radius > 5:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Darkened orange shockwave ring
            pygame.draw.circle(ring_surf, (200, 100, 0, alpha),
                             (radius, radius), radius, 4)

            # Inner darker ring
            if alpha > 60:
                pygame.draw.circle(ring_surf, (180, 80, 0, alpha // 2),
                                 (radius, radius), radius - 2, 2)

            surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class CyanExplosionFireball:
    """
    Cyan/blue fireball explosion for underground emergence.
    Matches the underground projectile color (#00ccff from Parabol icon).
    Same structure as ExplosionFireball but with cyan color palette.
    """
    def __init__(self, center_x, center_y, is_primary=False):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.4 if is_primary else 0.3
        self.active = True
        self.max_radius = 55 if is_primary else 30
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
        """Draw expanding cyan fireball."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fast expansion, then fade
        if progress < 0.4:
            radius = int(self.max_radius * (progress / 0.4))
        else:
            radius = self.max_radius

        # Fade out
        alpha = int(255 * (1.0 - progress))

        if alpha > 0 and radius > 0:
            fireball_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Multiple layers for depth - cyan color scheme
            # Outer cyan glow
            outer_radius = radius + 8
            pygame.draw.circle(fireball_surf, (0, 204, 255, alpha // 3),  # #00ccff
                             (center, center), outer_radius)

            # Main cyan fireball
            pygame.draw.circle(fireball_surf, (0, 204, 255, alpha),  # #00ccff
                             (center, center), radius)

            # Inner light cyan/white core
            inner_radius = int(radius * 0.6)
            pygame.draw.circle(fireball_surf, (102, 238, 255, alpha),  # Lighter cyan
                             (center, center), inner_radius)

            # Bright white center
            if progress < 0.3:
                core_radius = int(radius * 0.3)
                pygame.draw.circle(fireball_surf, (255, 255, 255, alpha),
                                 (center, center), core_radius)

            surface.blit(fireball_surf, (int(self.center_x - center), int(self.center_y - center)))


class CyanShockwaveRing:
    """
    Expanding cyan shockwave ring from underground impact.
    Matches the cyan underground projectile color.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.5
        self.active = True
        self.max_radius = 50

    def update(self, delta_time):
        """Update shockwave expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding cyan shockwave ring."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expand outward
        radius = int(self.max_radius * progress)

        # Fade out as expanding
        alpha = int(180 * (1.0 - progress))

        if alpha > 20 and radius > 5:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Cyan shockwave ring
            pygame.draw.circle(ring_surf, (0, 204, 255, alpha),  # #00ccff
                             (radius, radius), radius, 4)

            # Inner brighter cyan ring
            if alpha > 60:
                pygame.draw.circle(ring_surf, (102, 238, 255, alpha // 2),  # Lighter cyan
                                 (radius, radius), radius - 2, 2)

            surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class ParabolAnimation:
    """
    Parabol (massive mortar) skill animation for FOWL CONTRIVANCE.
    Launches one huge explosive shell that creates splash damage in a 3x3 area.

    Phases:
    1. Launch - Heavy smoke puff at caster, screen shake
    2. Arc Travel - Single massive shell following dramatic parabolic arc
    3. Impact - Central explosion with rippling splash damage to surrounding tiles
    4. Aftermath - Smoke dissipation and ember particles
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Parabol animation.

        Args:
            target_pos: (grid_y, grid_x) - center of 3x3 impact area
            camera: Camera instance for coordinate conversion
            particle_emitter: For smoke and ember effects
            screen_shake_callback: For launch and impact shakes
        """
        # Store references
        self.caster = caster_unit
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

        # Calculate 3x3 grid of impact positions
        self.impact_positions = []
        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                impact_grid_y = grid_y + dy
                impact_grid_x = grid_x + dx

                # Convert each impact position to screen coords
                impact_x, impact_y = camera.grid_to_screen(impact_grid_x, impact_grid_y, centered=True)

                is_primary = (dy == 0 and dx == 0)  # Center tile is primary

                self.impact_positions.append({
                    'x': impact_x,
                    'y': impact_y,
                    'is_primary': is_primary,
                    'delay': 0 if is_primary else 0.1 * (abs(dy) + abs(dx))  # Stagger outer impacts
                })

        # Animation state
        self.phase = "launch"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.launch_smoke = None
        self.mortar_shells = []
        self.explosions = []
        self.shockwaves = []

        # Start Phase 1: Launch
        self._start_launch()

    def _start_launch(self):
        """Phase 1: Launch - Mortars fire from caster position."""
        self.phase = "launch"
        self.timer = 0

        # Create launch smoke at caster
        self.launch_smoke = LaunchSmoke(self.caster_x, self.caster_y)

        # Heavier launch screen shake for massive shell
        self.screen_shake_callback(5, 0.4)

        # Emit more smoke particles at launch
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (90, 90, 90), count=25)

    def _start_arc_travel(self):
        """Phase 2: Arc Travel - Single massive shell flies through the air."""
        self.phase = "arc_travel"
        self.timer = 0

        # Create ONE massive mortar shell aimed at center target
        shell = MortarShell(self.caster_x, self.caster_y,
                          self.target_x, self.target_y, delay=0)
        self.mortar_shells.append(shell)

    def _start_impact(self):
        """Phase 3: Impact - Central explosion with rippling splash damage."""
        self.phase = "impact"
        self.timer = 0

        # Create explosions and shockwaves for each impact position
        # Central explosion is immediate and massive, others ripple outward
        for impact in self.impact_positions:
            # Fireball explosion
            explosion = ExplosionFireball(impact['x'], impact['y'], is_primary=impact['is_primary'])
            # Delay matches distance from center (ripple effect)
            explosion.timer = -impact['delay']
            self.explosions.append(explosion)

            # Shockwave ring
            shockwave = ShockwaveRing(impact['x'], impact['y'], delay=impact['delay'])
            self.shockwaves.append(shockwave)

            # Emit burst particles - more at center
            if self.particle_emitter:
                if impact['delay'] == 0:  # Central impact - massive particle burst
                    self.particle_emitter.emit_burst(impact['x'], impact['y'], (255, 150, 0), count=50)
                else:  # Splash damage - smaller bursts
                    # Delay particle emission to match explosion delay
                    pass  # Particles handled by aftermath phase

        # Massive impact screen shake
        self.screen_shake_callback(8, 0.5)

    def _start_aftermath(self):
        """Phase 4: Aftermath - Smoke and embers dissipate."""
        self.phase = "aftermath"
        self.timer = 0

        # Emit floating ember particles at each impact
        if self.particle_emitter:
            for impact in self.impact_positions:
                self.particle_emitter.emit_float(impact['x'], impact['y'], (255, 102, 0), count=8)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update sub-effects
        if self.launch_smoke:
            self.launch_smoke.update(delta_time)

        for shell in self.mortar_shells:
            shell.update(delta_time)

        for explosion in self.explosions:
            explosion.update(delta_time)

        for shockwave in self.shockwaves:
            shockwave.update(delta_time)

        # Phase transitions (adjusted timing for slower massive shell)
        if self.phase == "launch" and self.timer >= 0.4:
            self._start_arc_travel()
        elif self.phase == "arc_travel" and self.timer >= 0.7:  # Wait for slower shell
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.9:  # Longer impact for ripple effect
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "launch":
            if self.launch_smoke:
                self.launch_smoke.draw(surface)

        elif self.phase == "arc_travel":
            # Draw all mortar shells and their trails
            for shell in self.mortar_shells:
                shell.draw(surface)

        elif self.phase in ["impact", "aftermath"]:
            # Draw explosions and shockwaves
            for shockwave in self.shockwaves:
                shockwave.draw(surface)

            for explosion in self.explosions:
                explosion.draw(surface)


# ============================================================================
# PARABOL UPGRADED ANIMATION COMPONENTS
# ============================================================================

class BurrowEffect:
    """
    Shell burrows into ground at first explosion site.
    Spiral particles sinking into a dark vortex.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True

        # Create spiral particle positions
        self.particles = []
        for i in range(20):
            angle = (i / 20) * 2 * math.pi
            radius = 30 + (i * 2)
            self.particles.append({
                'angle': angle,
                'radius': radius,
                'spiral_speed': 3.0  # Radians per second
            })

    def update(self, delta_time):
        """Update spiral particles sinking inward."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update particle spiral
        for particle in self.particles:
            particle['angle'] += particle['spiral_speed'] * delta_time
            particle['radius'] -= 80 * delta_time  # Shrink inward

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw spiral burrow effect."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Draw dark vortex at center
        vortex_radius = int(25 * (1.0 - progress * 0.5))  # Shrinks slightly
        if vortex_radius > 0:
            vortex_surf = pygame.Surface((vortex_radius * 2, vortex_radius * 2), pygame.SRCALPHA)
            alpha = int(180 * progress)
            # Dark brown/black vortex
            pygame.draw.circle(vortex_surf, (40, 20, 10, alpha),
                             (vortex_radius, vortex_radius), vortex_radius)
            pygame.draw.circle(vortex_surf, (20, 10, 5, alpha),
                             (vortex_radius, vortex_radius), vortex_radius // 2)
            surface.blit(vortex_surf, (int(self.center_x - vortex_radius),
                                      int(self.center_y - vortex_radius)))

        # Draw spiral particles (brown/orange)
        for particle in self.particles:
            if particle['radius'] > 0:
                x = self.center_x + math.cos(particle['angle']) * particle['radius']
                y = self.center_y + math.sin(particle['angle']) * particle['radius']

                # Particle alpha based on radius (fade as they approach center)
                alpha = min(255, int(200 * (particle['radius'] / 50)))
                if alpha > 0:
                    particle_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    # Brown earth particles with orange accents (from Parabol icon)
                    if particle['radius'] > 15:
                        color = (204, 51, 0, alpha)  # #cc3300 - red-orange from icon
                    else:
                        color = (255, 102, 0, alpha)  # #ff6600 - orange from icon
                    pygame.draw.circle(particle_surf, color, (4, 4), 4)
                    surface.blit(particle_surf, (int(x - 4), int(y - 4)))


class UndergroundPath:
    """
    Visualizes underground shell travel from first to second explosion.
    Follows an inverted parabolic arc (mirrored downward) with cyan glow pulse.
    """
    def __init__(self, start_x, start_y, end_x, end_y):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.timer = 0
        self.duration = 0.6
        self.active = True

        # Calculate parabolic arc parameters
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)

        # Inverted arc height (goes DOWN instead of up, representing underground travel)
        # Match the magnitude of the surface arc but invert it
        self.arc_height = min(150, distance * 0.5)  # Same as MortarShell

        # Create dash points along inverted parabolic path
        self.dash_points = []
        num_dashes = int(distance / 20) + 1
        for i in range(num_dashes):
            t = i / (num_dashes - 1) if num_dashes > 1 else 0

            # Linear interpolation for x
            x = start_x + dx * t

            # Inverted parabolic arc for y (mirrored downward)
            # Surface uses: y = start_y + dy*t - arc_y_offset (where offset = -4h(t-0.5)² + h)
            # Underground inverts by ADDING the arc instead of subtracting
            arc_progress = t - 0.5
            arc_y_offset = -4 * self.arc_height * (arc_progress * arc_progress) + self.arc_height
            y = start_y + dy * t + arc_y_offset  # ADD the arc (inverts it downward)

            self.dash_points.append((x, y))

    def update(self, delta_time):
        """Update traveling glow."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw underground path with traveling pulse."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Draw dashed line (deep purple/magenta)
        for i, (x, y) in enumerate(self.dash_points):
            # Dash visibility
            if i % 3 != 0:  # Every third dash for dotted effect
                continue

            dash_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
            # Cyan underground color (from Parabol icon - axis of symmetry)
            # More transparent to show it's underground
            pygame.draw.circle(dash_surf, (0, 204, 255, 80), (6, 6), 6)  # #00ccff - semi-transparent
            surface.blit(dash_surf, (int(x - 6), int(y - 6)))

        # Draw traveling glow pulse
        glow_index = int(len(self.dash_points) * progress)
        if 0 <= glow_index < len(self.dash_points):
            glow_x, glow_y = self.dash_points[glow_index]

            glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            # Bright cyan/blue glow for underground projectile (from Parabol icon)
            # More transparent to emphasize underground travel
            pygame.draw.circle(glow_surf, (0, 204, 255, 100), (20, 20), 20)  # #00ccff - outer glow
            pygame.draw.circle(glow_surf, (102, 238, 255, 140), (20, 20), 14)  # Lighter cyan - mid layer
            pygame.draw.circle(glow_surf, (255, 255, 255, 180), (20, 20), 8)  # White core - brightest but still transparent
            surface.blit(glow_surf, (int(glow_x - 20), int(glow_y - 20)))


class GroundRumble:
    """
    Brown particle bursts along underground path.
    Simulates ground shaking above the traveling shell.
    """
    def __init__(self, path_points, delay=0):
        self.path_points = path_points
        self.timer = -delay
        self.duration = 0.6
        self.active = True
        self.rumble_sites = []

        # Select random points along path for rumbles
        for i in range(0, len(path_points), max(1, len(path_points) // 5)):
            if i < len(path_points):
                x, y = path_points[i]
                self.rumble_sites.append({
                    'x': x,
                    'y': y,
                    'trigger_time': (i / len(path_points)) * 0.5,
                    'active': False,
                    'timer': 0
                })

    def update(self, delta_time):
        """Update rumble bursts."""
        if not self.active:
            return False

        self.timer += delta_time

        # Trigger rumbles at appropriate times
        for rumble in self.rumble_sites:
            if not rumble['active'] and self.timer >= rumble['trigger_time']:
                rumble['active'] = True

            if rumble['active']:
                rumble['timer'] += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw ground rumble particle bursts."""
        if not self.active or self.timer < 0:
            return

        for rumble in self.rumble_sites:
            if rumble['active'] and rumble['timer'] < 0.3:
                # Small brown particle burst
                burst_progress = rumble['timer'] / 0.3
                offset_y = -15 * burst_progress  # Rise upward
                alpha = int(150 * (1.0 - burst_progress))

                if alpha > 0:
                    for i in range(3):
                        angle = (i / 3) * 2 * math.pi
                        x = rumble['x'] + math.cos(angle) * 10 * burst_progress
                        y = rumble['y'] + offset_y + math.sin(angle) * 5 * burst_progress

                        particle_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                        # Earth brown particles complementing Parabol's orange palette
                        pygame.draw.circle(particle_surf, (139, 69, 19, alpha), (3, 3), 3)
                        surface.blit(particle_surf, (int(x - 3), int(y - 3)))


class GroundRupture:
    """
    Ground cracks spreading from second explosion center before eruption.
    Dark lines radiating outward with brown particles.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.15
        self.active = True

        # Create crack lines radiating outward
        self.cracks = []
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            self.cracks.append({
                'angle': angle,
                'length': 0,
                'max_length': 35 + random.randint(-5, 5)
            })

    def update(self, delta_time):
        """Update spreading cracks."""
        if not self.active:
            return False

        self.timer += delta_time

        # Grow cracks outward
        growth_rate = 200  # pixels per second
        for crack in self.cracks:
            crack['length'] = min(crack['max_length'],
                                 crack['length'] + growth_rate * delta_time)

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw spreading crack lines."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(200 * progress)

        # Draw crack lines
        for crack in self.cracks:
            if crack['length'] > 0:
                end_x = self.center_x + math.cos(crack['angle']) * crack['length']
                end_y = self.center_y + math.sin(crack['angle']) * crack['length']

                # Dark gray crack
                pygame.draw.line(surface, (64, 64, 64, alpha),
                               (int(self.center_x), int(self.center_y)),
                               (int(end_x), int(end_y)), 2)

                # Orange/brown debris at crack tip (from Parabol palette)
                if crack['length'] > 10:
                    debris_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    pygame.draw.circle(debris_surf, (204, 51, 0, alpha), (4, 4), 4)  # #cc3300
                    surface.blit(debris_surf, (int(end_x - 4), int(end_y - 4)))


class TerrainGhost:
    """
    Semi-transparent ghost of terrain piece fading at source position.
    """
    def __init__(self, x, y, terrain_type):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.timer = 0
        self.duration = 0.3
        self.active = True

    def update(self, delta_time):
        """Fade out ghost."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw fading terrain ghost."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)
        alpha = int(100 * (1.0 - progress))  # Fade from 100 to 0

        if alpha > 5:
            # Simple rectangle representing terrain
            ghost_surf = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4), pygame.SRCALPHA)
            # White ghost
            pygame.draw.rect(ghost_surf, (255, 255, 255, alpha),
                           (0, 0, TILE_SIZE - 4, TILE_SIZE - 4), 2)
            surface.blit(ghost_surf, (int(self.x - (TILE_SIZE - 4) // 2),
                                     int(self.y - (TILE_SIZE - 4) // 2)))


class TerrainSlide:
    """
    Animated terrain piece sliding from source to target position.
    """
    def __init__(self, source_x, source_y, target_x, target_y, terrain_type, delay=0):
        self.source_x = source_x
        self.source_y = source_y
        self.target_x = target_x
        self.target_y = target_y
        self.terrain_type = terrain_type
        self.timer = -delay
        self.duration = 0.4
        self.active = True

        self.current_x = source_x
        self.current_y = source_y

    def update(self, delta_time):
        """Update sliding position."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:
            # Interpolate position
            progress = min(1.0, self.timer / self.duration)
            # Ease-out for smooth deceleration
            eased_progress = 1.0 - (1.0 - progress) ** 2

            self.current_x = self.source_x + (self.target_x - self.source_x) * eased_progress
            self.current_y = self.source_y + (self.target_y - self.source_y) * eased_progress

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw sliding terrain piece with dust trail."""
        if not self.active or self.timer < 0:
            return

        progress = max(0.0, min(1.0, self.timer / self.duration))

        # Draw terrain piece (simple colored rectangle)
        terrain_surf = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4), pygame.SRCALPHA)
        # Gray/brown for furniture
        terrain_color = (128, 128, 128, 220)
        if 'MARROW' in str(self.terrain_type):
            terrain_color = (208, 197, 181, 220)  # Bone color
        elif any(wood in str(self.terrain_type) for wood in ['OTTOMAN', 'BENCH', 'COUCH', 'COT']):
            terrain_color = (139, 90, 43, 220)  # Wood brown

        pygame.draw.rect(terrain_surf, terrain_color,
                        (0, 0, TILE_SIZE - 4, TILE_SIZE - 4))
        pygame.draw.rect(terrain_surf, (80, 80, 80, 220),
                        (0, 0, TILE_SIZE - 4, TILE_SIZE - 4), 1)

        surface.blit(terrain_surf, (int(self.current_x - (TILE_SIZE - 4) // 2),
                                   int(self.current_y - (TILE_SIZE - 4) // 2)))

        # Draw dust trail particles behind sliding object
        if progress > 0.1:
            trail_x = self.current_x - (self.target_x - self.source_x) * 0.2
            trail_y = self.current_y - (self.target_y - self.source_y) * 0.2

            dust_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
            dust_alpha = int(120 * (1.0 - progress))
            pygame.draw.circle(dust_surf, (210, 180, 140, dust_alpha), (6, 6), 6)
            surface.blit(dust_surf, (int(trail_x - 6), int(trail_y - 6)))


class ParabolAnimationUpgraded(ParabolAnimation):
    """
    Upgraded Parabol skill animation for FOWL CONTRIVANCE.
    Extends base Parabol with:
    - Underground travel phase after first explosion
    - Second explosion at mirrored parabolic location
    - Terrain rearrangement matching enemy formation imprint

    Phases:
    1. Launch (0.4s) - Same as base
    2. Arc Travel (0.7s) - Same as base
    3. Impact (0.9s) - First explosion (same as base)
    4. Underground Travel (0.6s) - Shell burrows and travels underground
    5. Second Impact (0.9s) - Eruption and explosion at second location
    6. Terrain Manipulation (0.7s) - Terrain pieces slide to match enemy formation
    7. Aftermath (0.5s) - Final dissipation
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize upgraded Parabol animation.

        Args:
            Same as ParabolAnimation, with game required for calculations
        """
        # Initialize base animation
        super().__init__(caster_unit, target_unit, target_pos, is_crit, is_infused,
                        particle_emitter, debris_list, screen_shake_callback,
                        screen_flash_callback, units_list, camera, game)

        # Calculate second explosion position
        self.second_explosion_pos = None
        self.second_impact_positions = []

        if game:
            self.second_explosion_pos = self._calculate_second_explosion(target_pos, game)
            self._calculate_second_impact_positions()

        # Underground travel effects
        self.burrow_effect = None
        self.underground_path = None
        self.ground_rumble = None

        # Second explosion effects
        self.ground_rupture = None
        self.second_explosions = []
        self.second_shockwaves = []

        # Terrain manipulation effects
        self.terrain_ghosts = []
        self.terrain_slides = []
        self.terrain_movements = []

        # Calculate terrain movements if game available
        if game and units_list:
            self.terrain_movements = self._calculate_terrain_movements(
                target_pos, self.second_explosion_pos, game, units_list
            )

    def _calculate_second_explosion(self, first_pos, game):
        """Calculate second explosion center using mirrored parabola logic."""
        grid_y, grid_x = first_pos
        caster_y = self.caster.grid_y
        caster_x = self.caster.grid_x

        # Calculate distance vector from caster to first explosion
        dist_y = grid_y - caster_y
        dist_x = grid_x - caster_x

        # Second explosion continues same distance/direction, wrapping around map
        second_y = (grid_y + dist_y) % game.map.height
        second_x = (grid_x + dist_x) % game.map.width

        return (second_y, second_x)

    def _calculate_second_impact_positions(self):
        """Calculate 3x3 grid of second impact positions."""
        if not self.second_explosion_pos:
            return

        grid_y, grid_x = self.second_explosion_pos

        for dy in range(-1, 2):
            for dx in range(-1, 2):
                impact_grid_y = grid_y + dy
                impact_grid_x = grid_x + dx

                # Convert to screen coords
                impact_x, impact_y = self.camera.grid_to_screen(impact_grid_x, impact_grid_y, centered=True)

                is_primary = (dy == 0 and dx == 0)

                self.second_impact_positions.append({
                    'x': impact_x,
                    'y': impact_y,
                    'is_primary': is_primary,
                    'delay': 0 if is_primary else 0.1 * (abs(dy) + abs(dx))
                })

    def _calculate_terrain_movements(self, first_pos, second_pos, game, units_list):
        """
        Calculate terrain rearrangement to match enemy formation.
        Returns list of terrain movement data.
        """
        movements = []

        if not second_pos:
            return movements

        # Scan first explosion for enemy positions (relative offsets)
        first_grid_y, first_grid_x = first_pos
        enemy_offsets = []

        for dy in range(-1, 2):
            for dx in range(-1, 2):
                check_y = first_grid_y + dy
                check_x = first_grid_x + dx

                # Check if enemy unit at this position
                for unit in units_list:
                    if (hasattr(unit, 'game_unit') and unit.game_unit and
                        unit.game_unit.is_alive() and
                        unit.grid_y == check_y and unit.grid_x == check_x and
                        unit.game_unit.player != self.caster.game_unit.player):
                        enemy_offsets.append((dy, dx))
                        break

        # Scan second explosion area for destructible terrain
        from boneglaive.game.map import TerrainType
        second_grid_y, second_grid_x = second_pos
        terrain_pieces = []

        destructible_terrain = [
            TerrainType.LIMESTONE, TerrainType.PILLAR, TerrainType.MARROW_WALL,
            TerrainType.LECTERN, TerrainType.COAT_RACK, TerrainType.OTTOMAN,
            TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF, TerrainType.TIFFANY_LAMP,
            TerrainType.STAINED_STONE, TerrainType.EASEL, TerrainType.SCULPTURE,
            TerrainType.BENCH, TerrainType.PODIUM, TerrainType.VASE,
            TerrainType.HYDRAULIC_PRESS, TerrainType.WORKBENCH, TerrainType.COUCH,
            TerrainType.TOOLBOX, TerrainType.COT, TerrainType.CONVEYOR,
            TerrainType.MINI_PUMPKIN, TerrainType.POTPOURRI_BOWL
        ]

        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue  # Skip center (will be destroyed)

                check_y = second_grid_y + dy
                check_x = second_grid_x + dx

                if game.is_valid_position(check_y, check_x):
                    terrain = game.map.get_terrain_at(check_y, check_x)
                    if terrain in destructible_terrain:
                        source_x, source_y = self.camera.grid_to_screen(check_x, check_y, centered=True)
                        terrain_pieces.append({
                            'grid_y': check_y,
                            'grid_x': check_x,
                            'screen_x': source_x,
                            'screen_y': source_y,
                            'terrain_type': terrain
                        })

        # Match terrain to enemy offsets
        for i, (offset_y, offset_x) in enumerate(enemy_offsets):
            if i >= len(terrain_pieces):
                break  # More enemies than terrain

            terrain = terrain_pieces[i]
            target_grid_y = second_grid_y + offset_y
            target_grid_x = second_grid_x + offset_x
            target_x, target_y = self.camera.grid_to_screen(target_grid_x, target_grid_y, centered=True)

            movements.append({
                'source_x': terrain['screen_x'],
                'source_y': terrain['screen_y'],
                'target_x': target_x,
                'target_y': target_y,
                'terrain_type': terrain['terrain_type']
            })

        return movements

    def _start_underground_travel(self):
        """Phase 4: Shell burrows and travels underground."""
        self.phase = "underground_travel"
        self.timer = 0

        # Create burrow effect at first explosion center
        self.burrow_effect = BurrowEffect(self.target_x, self.target_y)

        # Create underground path from first to second explosion
        if self.second_explosion_pos and self.game:
            second_grid_y, second_grid_x = self.second_explosion_pos
            second_screen_x, second_screen_y = self.camera.grid_to_screen(
                second_grid_x, second_grid_y, centered=True
            )

            # Detect map wrapping and adjust path to go off-screen properly
            first_grid_y, first_grid_x = self.target_pos

            # Calculate screen dimensions based on map size and tile size
            map_screen_width = self.game.map.width * self.camera.tile_size
            map_screen_height = self.game.map.height * self.camera.tile_size

            # Check if we wrapped horizontally
            wrapped_x = False
            if abs(second_grid_x - first_grid_x) > self.game.map.width / 2:
                wrapped_x = True
                # Determine which direction to wrap
                if second_grid_x < first_grid_x:
                    # Wrapped to left side, path should go right off screen
                    # Adjust target to be off the right edge
                    second_screen_x += map_screen_width
                else:
                    # Wrapped to right side, path should go left off screen
                    # Adjust target to be off the left edge
                    second_screen_x -= map_screen_width

            # Check if we wrapped vertically
            wrapped_y = False
            if abs(second_grid_y - first_grid_y) > self.game.map.height / 2:
                wrapped_y = True
                # Determine which direction to wrap
                if second_grid_y < first_grid_y:
                    # Wrapped to top side, path should go down off screen
                    second_screen_y += map_screen_height
                else:
                    # Wrapped to bottom side, path should go up off screen
                    second_screen_y -= map_screen_height

            self.underground_path = UndergroundPath(
                self.target_x, self.target_y,
                second_screen_x, second_screen_y
            )

            # Create ground rumble along path
            if self.underground_path:
                self.ground_rumble = GroundRumble(self.underground_path.dash_points, delay=0.2)

    def _start_second_impact(self):
        """Phase 5: Second explosion erupts from underground."""
        self.phase = "second_impact"
        self.timer = 0

        if not self.second_explosion_pos:
            return

        # Get second explosion center screen coords
        center_x, center_y = self.camera.grid_to_screen(
            self.second_explosion_pos[1], self.second_explosion_pos[0], centered=True
        )

        # Create ground rupture
        self.ground_rupture = GroundRupture(center_x, center_y)

        # Create CYAN explosions for each impact position (matching underground projectile)
        for impact in self.second_impact_positions:
            # Cyan explosion matching the underground projectile color
            explosion = CyanExplosionFireball(impact['x'], impact['y'], is_primary=impact['is_primary'])
            explosion.timer = -impact['delay'] - 0.15  # Delay for rupture
            self.second_explosions.append(explosion)

            # Cyan shockwave
            shockwave = CyanShockwaveRing(impact['x'], impact['y'], delay=impact['delay'] + 0.15)
            self.second_shockwaves.append(shockwave)

            # Emit upward-biased particles (erupting from below)
            if self.particle_emitter and impact['delay'] == 0:
                for _ in range(30):
                    angle = random.uniform(-math.pi/3, -2*math.pi/3)  # Upward bias
                    speed = random.uniform(100, 250)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    # Cyan/blue particles with brown debris (Parabol icon colors)
                    color = random.choice([(0, 204, 255), (139, 69, 19), (204, 51, 0)])
                    from .core import Particle
                    particle = Particle(impact['x'], impact['y'], vx, vy,
                                      lifetime=0.5, size=5, color=color)
                    self.particle_emitter.particles.append(particle)

        # Heavy screen shake for underground eruption
        self.screen_shake_callback(7, 0.5)

    def _start_terrain_manipulation(self):
        """Phase 6: Terrain pieces rearrange to match enemy formation."""
        self.phase = "terrain_manipulation"
        self.timer = 0

        # Create terrain ghosts at source positions
        for movement in self.terrain_movements:
            ghost = TerrainGhost(movement['source_x'], movement['source_y'],
                               movement['terrain_type'])
            self.terrain_ghosts.append(ghost)

            # Create sliding terrain with staggered delays
            delay = random.uniform(0, 0.2)
            slide = TerrainSlide(movement['source_x'], movement['source_y'],
                               movement['target_x'], movement['target_y'],
                               movement['terrain_type'], delay=delay)
            self.terrain_slides.append(slide)

    def _start_aftermath(self):
        """Phase 7: Aftermath - Floating particles at both impact sites (mirrored)."""
        self.phase = "aftermath"
        self.timer = 0

        # Emit floating ORANGE ember particles at FIRST impact (rising upward - normal)
        if self.particle_emitter:
            for impact in self.impact_positions:
                self.particle_emitter.emit_float(impact['x'], impact['y'], (255, 102, 0), count=8)

        # Emit floating CYAN particles at SECOND impact (sinking downward - inverted/mirrored)
        if self.particle_emitter and self.second_impact_positions:
            from .core import Particle
            for impact in self.second_impact_positions:
                # Manually create particles with DOWNWARD velocity (inverted from emit_float)
                for _ in range(8):
                    vx = random.uniform(-10, 10)
                    vy = random.uniform(20, 60)  # POSITIVE = downward (mirrored from emit_float's -60 to -20)
                    size = random.uniform(2, 4)
                    lifetime = random.uniform(0.5, 1.5)
                    # Cyan color matching underground projectile
                    particle = Particle(impact['x'], impact['y'], vx, vy, (0, 204, 255), size, lifetime)
                    self.particle_emitter.particles.append(particle)

    def update(self, delta_time):
        """Update animation state with extended phases."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update base effects
        if self.launch_smoke:
            self.launch_smoke.update(delta_time)

        for shell in self.mortar_shells:
            shell.update(delta_time)

        for explosion in self.explosions:
            explosion.update(delta_time)

        for shockwave in self.shockwaves:
            shockwave.update(delta_time)

        # Update upgraded effects
        if self.burrow_effect:
            self.burrow_effect.update(delta_time)

        if self.underground_path:
            self.underground_path.update(delta_time)

        if self.ground_rumble:
            self.ground_rumble.update(delta_time)

        if self.ground_rupture:
            self.ground_rupture.update(delta_time)

        for explosion in self.second_explosions:
            explosion.update(delta_time)

        for shockwave in self.second_shockwaves:
            shockwave.update(delta_time)

        for ghost in self.terrain_ghosts:
            ghost.update(delta_time)

        for slide in self.terrain_slides:
            slide.update(delta_time)

        # Phase transitions (extended for upgraded)
        if self.phase == "launch" and self.timer >= 0.4:
            self._start_arc_travel()
        elif self.phase == "arc_travel" and self.timer >= 0.7:
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.9:
            self._start_underground_travel()  # NEW PHASE
        elif self.phase == "underground_travel" and self.timer >= 0.6:
            self._start_second_impact()  # NEW PHASE
        elif self.phase == "second_impact" and self.timer >= 0.9:
            self._start_terrain_manipulation()  # NEW PHASE
        elif self.phase == "terrain_manipulation" and self.timer >= 0.7:
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation with extended phases."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "launch":
            if self.launch_smoke:
                self.launch_smoke.draw(surface)

        elif self.phase == "arc_travel":
            for shell in self.mortar_shells:
                shell.draw(surface)

        elif self.phase == "impact":
            # First explosion
            for shockwave in self.shockwaves:
                shockwave.draw(surface)
            for explosion in self.explosions:
                explosion.draw(surface)

        elif self.phase == "underground_travel":
            # Underground phase
            if self.burrow_effect:
                self.burrow_effect.draw(surface)
            if self.underground_path:
                self.underground_path.draw(surface)
            if self.ground_rumble:
                self.ground_rumble.draw(surface)

        elif self.phase == "second_impact":
            # Second explosion with rupture
            if self.ground_rupture:
                self.ground_rupture.draw(surface)
            for shockwave in self.second_shockwaves:
                shockwave.draw(surface)
            for explosion in self.second_explosions:
                explosion.draw(surface)

        elif self.phase == "terrain_manipulation":
            # Terrain rearrangement
            for ghost in self.terrain_ghosts:
                ghost.draw(surface)
            for slide in self.terrain_slides:
                slide.draw(surface)

        elif self.phase == "aftermath":
            # Final dissipation (particles handled by particle emitter)
            pass


# ============================================================================
# FRAGCREST ANIMATION (Directional Fragmentation Cone)
# ============================================================================

class TailFanMechanism:
    """
    Mechanical peacock tail deploying radially.
    Shows grey/orange struts extending outward.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True
        self.max_extension = 35

        # Create radial struts
        self.struts = []
        num_struts = 7
        for i in range(num_struts):
            angle = (i / (num_struts - 1)) * math.pi - math.pi / 2  # Fan spread
            self.struts.append({'angle': angle})

    def update(self, delta_time):
        """Update tail extension."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw extending tail mechanism."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Ease-out extension
        extension = self.max_extension * (1.0 - (1.0 - progress) ** 2)

        # Draw each strut
        for strut in self.struts:
            angle = strut['angle']
            end_x = self.center_x + math.cos(angle) * extension
            end_y = self.center_y + math.sin(angle) * extension

            # Grey strut with orange highlight
            pygame.draw.line(surface, (106, 106, 106),
                           (int(self.center_x), int(self.center_y)),
                           (int(end_x), int(end_y)), 3)

            # Orange highlight on top
            pygame.draw.line(surface, (255, 150, 0),
                           (int(self.center_x), int(self.center_y)),
                           (int(end_x), int(end_y)), 1)

            # End nodes (cyan accent)
            if progress > 0.5:
                node_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(node_surf, (0, 204, 255, 200), (4, 4), 3)
                surface.blit(node_surf, (int(end_x) - 4, int(end_y) - 4))


class ChargeGlow:
    """
    Pulsing orange energy buildup at tail center.
    Intensifies before burst release.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.4
        self.active = True

    def update(self, delta_time):
        """Update charge intensity."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw pulsing charge glow."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Pulse frequency increases as charge builds
        pulse_freq = 8 + progress * 12
        pulse = 0.5 + 0.5 * math.sin(self.timer * pulse_freq)

        # Growing intensity
        intensity = progress * pulse

        # Expanding radius
        base_radius = 15 + progress * 20
        radius = int(base_radius + 5 * pulse)
        alpha = int(220 * intensity)

        if alpha > 20:
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Outer orange glow
            pygame.draw.circle(glow_surf, (255, 102, 0, alpha // 3),
                             (radius, radius), radius)

            # Middle glow
            mid_radius = int(radius * 0.6)
            pygame.draw.circle(glow_surf, (255, 150, 0, alpha // 2),
                             (radius, radius), mid_radius)

            # Bright center
            core_radius = int(radius * 0.3)
            pygame.draw.circle(glow_surf, (255, 204, 0, alpha),
                             (radius, radius), core_radius)

            surface.blit(glow_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class ShrapnelFragment:
    """
    Individual jagged metal shard projectile.
    Orange/grey fragment flying through cone.
    """
    def __init__(self, start_x, start_y, target_x, target_y, delay=0, is_primary=False):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.timer = -delay
        self.duration = 0.4  # Travel time
        self.active = True
        self.is_primary = is_primary

        # Random rotation for visual variety
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-10, 10)

        # Size varies
        self.size = random.randint(3, 6) if is_primary else random.randint(2, 4)

    def update(self, delta_time):
        """Update fragment position."""
        if not self.active:
            return False

        self.timer += delta_time
        self.rotation += self.rotation_speed * delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw flying shrapnel fragment."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Current position
        current_x = self.start_x + (self.target_x - self.start_x) * progress
        current_y = self.start_y + (self.target_y - self.start_y) * progress

        # Fade in at start, fade out at end
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))
        else:
            alpha = 255

        if alpha > 20:
            # Draw jagged fragment shape
            frag_surf = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            center = self.size * 2

            # Create jagged polygon
            points = []
            num_points = 5
            for i in range(num_points):
                angle = self.rotation + (i / num_points) * 2 * math.pi
                radius = self.size if i % 2 == 0 else self.size * 0.5
                px = center + math.cos(angle) * radius
                py = center + math.sin(angle) * radius
                points.append((px, py))

            # Draw fragment (orange with grey edge)
            pygame.draw.polygon(frag_surf, (255, 102, 0, alpha), points)
            pygame.draw.polygon(frag_surf, (90, 90, 90, alpha), points, 1)

            surface.blit(frag_surf, (int(current_x) - center, int(current_y) - center))


class ConeBurst:
    """
    Cone-shaped explosion effect at release point.
    Directional orange burst spreading into cone.
    """
    def __init__(self, center_x, center_y, direction_x, direction_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True

        # Calculate cone direction
        length = math.sqrt(direction_x * direction_x + direction_y * direction_y)
        if length > 0:
            self.dir_x = direction_x / length
            self.dir_y = direction_y / length
        else:
            self.dir_x = 1
            self.dir_y = 0

        # Cone angle (90 degrees = π/2 radians, so ±π/4 from center)
        self.base_angle = math.atan2(self.dir_y, self.dir_x)
        self.cone_half_angle = math.pi / 4

    def update(self, delta_time):
        """Update burst expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw cone burst effect."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expanding cone
        cone_length = int(60 * progress)
        alpha = int(200 * (1.0 - progress))

        if alpha > 20 and cone_length > 5:
            # Create cone shape as polygon
            cone_surf = pygame.Surface((cone_length * 2, cone_length * 2), pygame.SRCALPHA)
            center = cone_length

            # Calculate cone polygon points
            points = [(center, center)]  # Start at center

            # Left edge of cone
            angle_left = self.base_angle - self.cone_half_angle
            end_x_left = center + math.cos(angle_left) * cone_length
            end_y_left = center + math.sin(angle_left) * cone_length
            points.append((end_x_left, end_y_left))

            # Arc along cone width
            num_arc_points = 8
            for i in range(num_arc_points + 1):
                t = i / num_arc_points
                angle = angle_left + t * (2 * self.cone_half_angle)
                arc_x = center + math.cos(angle) * cone_length
                arc_y = center + math.sin(angle) * cone_length
                points.append((arc_x, arc_y))

            # Close back to center
            points.append((center, center))

            # Draw filled cone (semi-transparent orange)
            pygame.draw.polygon(cone_surf, (255, 102, 0, alpha // 2), points)

            # Draw cone edge highlight
            pygame.draw.lines(cone_surf, (255, 204, 0, alpha), False, points[1:-1], 2)

            surface.blit(cone_surf, (int(self.center_x - center), int(self.center_y - center)))


class EmbeddedShrapnel:
    """
    Lingering orange particles showing shrapnel DOT effect.
    Small glowing fragments embedded at impact site.
    """
    def __init__(self, target_x, target_y, delay=0):
        self.center_x = target_x
        self.center_y = target_y
        self.timer = -delay
        self.duration = 0.4  # How long to show embedded effect
        self.active = True

        # Create small fragment particles around impact point
        self.fragments = []
        num_fragments = 6
        for i in range(num_fragments):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(5, 15)
            self.fragments.append({
                'x': target_x + math.cos(angle) * distance,
                'y': target_y + math.sin(angle) * distance,
                'size': random.randint(2, 4)
            })

    def update(self, delta_time):
        """Update embedded shrapnel visibility."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw embedded shrapnel particles."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Pulse effect
        pulse = 0.7 + 0.3 * math.sin(self.timer * 8)
        alpha = int(180 * pulse * (1.0 - progress * 0.5))  # Fade slowly

        if alpha > 30:
            for frag in self.fragments:
                frag_surf = pygame.Surface((frag['size'] * 3, frag['size'] * 3), pygame.SRCALPHA)
                center = int(frag['size'] * 1.5)

                # Orange glowing fragment
                pygame.draw.circle(frag_surf, (255, 102, 0, alpha),
                                 (center, center), frag['size'])

                # Bright center
                pygame.draw.circle(frag_surf, (255, 204, 0, alpha),
                                 (center, center), max(1, frag['size'] // 2))

                surface.blit(frag_surf, (int(frag['x']) - center, int(frag['y']) - center))


class ClaymoreGroundExplosion:
    """
    Ground-level claymore mine detonation effect.
    Conical peacock tail explosion burst, mimicking the base Fragcrest visual.
    """
    def __init__(self, center_x, center_y, direction_x, direction_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True

        # Calculate direction for cone
        length = math.sqrt(direction_x * direction_x + direction_y * direction_y)
        if length > 0:
            self.dir_x = direction_x / length
            self.dir_y = direction_y / length
        else:
            self.dir_x = 1
            self.dir_y = 0

        self.blast_angle = math.atan2(self.dir_y, self.dir_x)

        # Cone parameters (90 degree spread like base skill)
        self.cone_half_angle = math.pi / 4  # 45 degrees on each side = 90 total

        # Create radial struts (peacock tail fan pattern)
        self.struts = []
        num_struts = 9
        for i in range(num_struts):
            # Spread struts across cone angle
            angle_offset = ((i / (num_struts - 1)) - 0.5) * (2 * self.cone_half_angle)
            strut_angle = self.blast_angle + angle_offset
            self.struts.append({
                'angle': strut_angle,
                'length_mult': random.uniform(0.85, 1.0)  # Slight variation
            })

        # Create debris particles (metal fragments)
        self.debris = []
        for i in range(15):
            # Bias debris forward in cone
            angle_offset = random.uniform(-self.cone_half_angle, self.cone_half_angle)
            angle = self.blast_angle + angle_offset
            speed = random.uniform(100, 180)
            self.debris.append({
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'x': center_x,
                'y': center_y,
                'size': random.randint(2, 4),
                'rotation': random.uniform(0, 2 * math.pi),
                'rot_speed': random.uniform(-15, 15)
            })

    def update(self, delta_time):
        """Update explosion expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update debris
        for d in self.debris:
            d['x'] += d['vx'] * delta_time
            d['y'] += d['vy'] * delta_time
            d['rotation'] += d['rot_speed'] * delta_time
            # Slow down debris
            d['vx'] *= 0.93
            d['vy'] *= 0.93

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw ground explosion effect."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expanding cone burst (like base skill's ConeBurst)
        max_cone_length = 70
        cone_length = int(max_cone_length * progress)
        alpha = int(200 * (1.0 - progress))

        if alpha > 20 and cone_length > 5:
            # Draw semi-transparent cone fill
            cone_surf = pygame.Surface((cone_length * 2 + 20, cone_length * 2 + 20), pygame.SRCALPHA)
            center = cone_length + 10

            # Calculate cone polygon
            points = [(center, center)]  # Start at center

            # Left edge
            angle_left = self.blast_angle - self.cone_half_angle
            left_x = center + math.cos(angle_left) * cone_length
            left_y = center + math.sin(angle_left) * cone_length
            points.append((left_x, left_y))

            # Arc along cone width
            num_arc_points = 12
            for i in range(num_arc_points + 1):
                t = i / num_arc_points
                angle = angle_left + t * (2 * self.cone_half_angle)
                arc_x = center + math.cos(angle) * cone_length
                arc_y = center + math.sin(angle) * cone_length
                points.append((arc_x, arc_y))

            points.append((center, center))

            # Draw cone (orange/yellow like base skill)
            pygame.draw.polygon(cone_surf, (255, 102, 0, alpha // 2), points)
            pygame.draw.lines(cone_surf, (255, 204, 0, alpha), False, points[1:-1], 2)

            surface.blit(cone_surf, (int(self.center_x - center), int(self.center_y - center)))

        # Draw peacock tail struts expanding (like base skill's tail mechanism)
        strut_alpha = int(220 * (1.0 - progress * 0.8))
        if strut_alpha > 30:
            max_strut_length = 50
            strut_length = max_strut_length * progress

            for strut in self.struts:
                # Calculate strut end position
                angle = strut['angle']
                length = strut_length * strut['length_mult']
                end_x = self.center_x + math.cos(angle) * length
                end_y = self.center_y + math.sin(angle) * length

                # Draw strut (grey metal with orange highlight)
                pygame.draw.line(surface, (120, 120, 120, strut_alpha),
                               (int(self.center_x), int(self.center_y)),
                               (int(end_x), int(end_y)), 3)

                # Orange highlight on top
                pygame.draw.line(surface, (255, 150, 0, strut_alpha),
                               (int(self.center_x), int(self.center_y)),
                               (int(end_x), int(end_y)), 1)

                # Cyan accent nodes at ends (peacock eye spots)
                if progress > 0.4:
                    node_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    node_alpha = min(strut_alpha, 200)
                    pygame.draw.circle(node_surf, (0, 204, 255, node_alpha), (4, 4), 3)
                    surface.blit(node_surf, (int(end_x) - 4, int(end_y) - 4))

        # Draw flying debris (metal fragments)
        debris_alpha = int(220 * (1.0 - progress * 0.7))
        if debris_alpha > 30:
            for d in self.debris:
                debris_surf = pygame.Surface((d['size'] * 3, d['size'] * 3), pygame.SRCALPHA)
                center = int(d['size'] * 1.5)

                # Create jagged metal fragment
                points = []
                for j in range(5):
                    angle = d['rotation'] + (j / 5) * 2 * math.pi
                    radius = d['size'] if j % 2 == 0 else d['size'] * 0.5
                    px = center + math.cos(angle) * radius
                    py = center + math.sin(angle) * radius
                    points.append((px, py))

                # Orange/grey fragments (like base skill shrapnel)
                pygame.draw.polygon(debris_surf, (255, 102, 0, debris_alpha), points)
                pygame.draw.polygon(debris_surf, (90, 90, 90, debris_alpha), points, 1)

                surface.blit(debris_surf, (int(d['x']) - center, int(d['y']) - center))


class FragcrestAnimation:
    """
    Fragcrest (directional fragmentation cone) skill animation for FOWL CONTRIVANCE.
    Ground-level conical explosion in peacock tail pattern with directional shrapnel.

    Phases:
    1. Ground Explosion - Claymore-style detonation with conical burst
    2. Burst - Explosive cone release with shrapnel fragments
    3. Impact - Fragments hit targets with embedded shrapnel effects
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None, is_trap=False,
                 trap_cone_positions=None):
        """
        Initialize Fragcrest animation.

        Args:
            target_pos: (grid_y, grid_x) - primary target position (or trap position if is_trap=True)
            target_unit: Primary target unit (for cone direction calculation)
            camera: Camera instance for coordinate conversion
            game: Game instance to calculate cone positions
            is_trap: If True, animation originates from trap position (target_pos) instead of caster
            trap_cone_positions: Pre-calculated cone positions for trap mode (list of (y, x, is_primary) tuples)
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.game = game
        self.is_trap = is_trap

        # Convert target grid position to screen coords
        # CRITICAL: target_pos is (grid_y, grid_x), but grid_to_screen takes (grid_x, grid_y)!
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Determine origin position for animation and cone positions
        if is_trap and trap_cone_positions:
            # Trap mode: Animation originates from trap position (target_pos)
            # Use pre-calculated cone positions from trap trigger
            self.caster_x, self.caster_y = self.target_x, self.target_y
            cone_positions = trap_cone_positions
        else:
            # Normal mode: Animation originates from caster position
            self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                                 caster_unit.grid_y,
                                                                 centered=True)
            # Calculate cone positions using the skill's logic
            cone_positions = self._calculate_cone_positions(
                caster_unit.grid_y, caster_unit.grid_x,
                grid_y, grid_x
            )

        # Convert all cone positions to screen coords
        self.cone_screen_positions = []
        for pos_grid_y, pos_grid_x, is_primary in cone_positions:
            pos_x, pos_y = camera.grid_to_screen(pos_grid_x, pos_grid_y, centered=True)
            self.cone_screen_positions.append({
                'x': pos_x,
                'y': pos_y,
                'is_primary': is_primary
            })

        # Calculate direction from caster to target for explosion
        direction_x = self.target_x - self.caster_x
        direction_y = self.target_y - self.caster_y
        self.direction_x = direction_x
        self.direction_y = direction_y

        # Animation state
        self.phase = "ground_explosion"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.ground_explosion = None
        self.cone_burst = None
        self.shrapnel_fragments = []
        self.embedded_shrapnel = []

        # Start Phase 1: Ground Explosion
        self._start_ground_explosion()

    def _calculate_cone_positions(self, caster_y, caster_x, target_y, target_x):
        """Calculate all positions in the 90-degree cone (from skill logic)."""
        positions = []

        # Calculate direction vector
        dy = target_y - caster_y
        dx = target_x - caster_x

        # Normalize direction for cone calculation
        if abs(dx) > abs(dy):
            main_dir = (0, 1 if dx > 0 else -1)
        elif abs(dy) > abs(dx):
            main_dir = (1 if dy > 0 else -1, 0)
        else:
            main_dir = (1 if dy > 0 else -1, 1 if dx > 0 else -1)

        # Generate cone positions (range 4)
        skill_range = 4
        for range_step in range(1, skill_range + 1):
            # Calculate width at this range (cone gets wider with distance)
            width = min(3, 1 + range_step // 2)

            # Calculate center position at this range
            center_y = caster_y + main_dir[0] * range_step
            center_x = caster_x + main_dir[1] * range_step

            # Add positions around the center based on width
            for offset in range(-(width//2), (width//2) + 1):
                if main_dir[0] == 0:  # Horizontal cone
                    pos_y = center_y + offset
                    pos_x = center_x
                else:  # Vertical cone
                    pos_y = center_y
                    pos_x = center_x + offset

                is_primary = (pos_y == target_y and pos_x == target_x)
                positions.append((pos_y, pos_x, is_primary))

        return positions

    def _start_ground_explosion(self):
        """Phase 1: Ground Explosion - Claymore-style detonation."""
        self.phase = "ground_explosion"
        self.timer = 0

        # Create ground explosion effect
        self.ground_explosion = ClaymoreGroundExplosion(
            self.caster_x, self.caster_y,
            self.direction_x, self.direction_y
        )

        # Medium screen shake for explosion
        self.screen_shake_callback(4, 0.25)

        # Emit explosion particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (255, 102, 0), count=25)

    def _start_burst(self):
        """Phase 2: Burst - Explosive cone release."""
        self.phase = "burst"
        self.timer = 0

        # Create cone burst effect
        self.cone_burst = ConeBurst(self.caster_x, self.caster_y, self.direction_x, self.direction_y)

        # Create shrapnel fragments for each cone position
        for i, pos in enumerate(self.cone_screen_positions):
            # Slight stagger for realism
            delay = 0.03 * i if not pos['is_primary'] else 0
            fragment = ShrapnelFragment(
                self.caster_x, self.caster_y,
                pos['x'], pos['y'],
                delay=delay,
                is_primary=pos['is_primary']
            )
            self.shrapnel_fragments.append(fragment)

        # Additional shake for shrapnel burst
        self.screen_shake_callback(3, 0.2)

        # Burst particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (255, 150, 0), count=30)

    def _start_impact(self):
        """Phase 3: Impact - Fragments hit targets."""
        self.phase = "impact"
        self.timer = 0

        # Create embedded shrapnel at each impact position
        for i, pos in enumerate(self.cone_screen_positions):
            delay = 0.03 * i if not pos['is_primary'] else 0
            embedded = EmbeddedShrapnel(pos['x'], pos['y'], delay=delay)
            self.embedded_shrapnel.append(embedded)

            # Impact particles at primary targets
            if self.particle_emitter and delay == 0:
                self.particle_emitter.emit_burst(pos['x'], pos['y'], (255, 102, 0), count=15)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update sub-effects
        if self.ground_explosion:
            self.ground_explosion.update(delta_time)

        if self.cone_burst:
            self.cone_burst.update(delta_time)

        for fragment in self.shrapnel_fragments:
            fragment.update(delta_time)

        for embedded in self.embedded_shrapnel:
            embedded.update(delta_time)

        # Phase transitions (same timing as trap)
        if self.phase == "ground_explosion" and self.timer >= 0.2:
            self._start_burst()
        elif self.phase == "burst" and self.timer >= 0.4:
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "ground_explosion":
            if self.ground_explosion:
                self.ground_explosion.draw(surface)

        elif self.phase == "burst":
            # Ground explosion still fading
            if self.ground_explosion:
                self.ground_explosion.draw(surface)

            if self.cone_burst:
                self.cone_burst.draw(surface)
            for fragment in self.shrapnel_fragments:
                fragment.draw(surface)

        elif self.phase == "impact":
            # Draw fragments still traveling
            for fragment in self.shrapnel_fragments:
                fragment.draw(surface)

            # Draw embedded shrapnel
            for embedded in self.embedded_shrapnel:
                embedded.draw(surface)


class FragcrestTrapAnimation:
    """
    Fragcrest trap detonation animation for FOWL CONTRIVANCE.
    Instant claymore mine explosion with directional fragmentation cone.

    Phases:
    1. Ground Explosion - Claymore detonation at trap position
    2. Burst - Explosive cone release with shrapnel
    3. Impact - Fragments hit targets with embedded shrapnel effects
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None, is_trap=False,
                 trap_cone_positions=None):
        """
        Initialize Fragcrest trap animation.

        Args:
            target_pos: (grid_y, grid_x) - trap position
            target_unit: Target unit (for direction)
            trap_cone_positions: Pre-calculated cone positions
        """
        # Store references
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback

        # Trap position is the origin
        grid_y, grid_x = target_pos
        self.trap_x, self.trap_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Calculate direction from trap to triggering unit
        if target_unit:
            target_screen_x, target_screen_y = camera.grid_to_screen(
                target_unit.grid_x, target_unit.grid_y, centered=True
            )
            direction_x = target_screen_x - self.trap_x
            direction_y = target_screen_y - self.trap_y
        else:
            direction_x = 1
            direction_y = 0

        self.direction_x = direction_x
        self.direction_y = direction_y

        # Convert cone positions to screen coords
        self.cone_screen_positions = []
        if trap_cone_positions:
            for pos_grid_y, pos_grid_x, is_primary in trap_cone_positions:
                pos_x, pos_y = camera.grid_to_screen(pos_grid_x, pos_grid_y, centered=True)
                self.cone_screen_positions.append({
                    'x': pos_x,
                    'y': pos_y,
                    'is_primary': is_primary
                })

        # Animation state
        self.phase = "ground_explosion"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.ground_explosion = None
        self.cone_burst = None
        self.shrapnel_fragments = []
        self.embedded_shrapnel = []

        # Start Phase 1: Ground Explosion
        self._start_ground_explosion()

    def _start_ground_explosion(self):
        """Phase 1: Ground Explosion - Claymore detonation."""
        self.phase = "ground_explosion"
        self.timer = 0

        # Create ground explosion effect
        self.ground_explosion = ClaymoreGroundExplosion(
            self.trap_x, self.trap_y,
            self.direction_x, self.direction_y
        )

        # Medium screen shake for trap detonation
        self.screen_shake_callback(4, 0.25)

        # Emit explosion particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.trap_x, self.trap_y, (255, 102, 0), count=25)

    def _start_burst(self):
        """Phase 2: Burst - Explosive cone release."""
        self.phase = "burst"
        self.timer = 0

        # Create cone burst effect
        self.cone_burst = ConeBurst(
            self.trap_x, self.trap_y,
            self.direction_x, self.direction_y
        )

        # Create shrapnel fragments for each cone position
        for i, pos in enumerate(self.cone_screen_positions):
            # Slight stagger for realism
            delay = 0.03 * i if not pos['is_primary'] else 0
            fragment = ShrapnelFragment(
                self.trap_x, self.trap_y,
                pos['x'], pos['y'],
                delay=delay,
                is_primary=pos['is_primary']
            )
            self.shrapnel_fragments.append(fragment)

        # Additional shake for shrapnel burst
        self.screen_shake_callback(3, 0.2)

        # Burst particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.trap_x, self.trap_y, (255, 150, 0), count=30)

    def _start_impact(self):
        """Phase 3: Impact - Fragments hit targets."""
        self.phase = "impact"
        self.timer = 0

        # Create embedded shrapnel at each impact position
        for i, pos in enumerate(self.cone_screen_positions):
            delay = 0.03 * i if not pos['is_primary'] else 0
            embedded = EmbeddedShrapnel(pos['x'], pos['y'], delay=delay)
            self.embedded_shrapnel.append(embedded)

            # Impact particles at primary targets
            if self.particle_emitter and delay == 0:
                self.particle_emitter.emit_burst(pos['x'], pos['y'], (255, 102, 0), count=15)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update sub-effects
        if self.ground_explosion:
            self.ground_explosion.update(delta_time)

        if self.cone_burst:
            self.cone_burst.update(delta_time)

        for fragment in self.shrapnel_fragments:
            fragment.update(delta_time)

        for embedded in self.embedded_shrapnel:
            embedded.update(delta_time)

        # Phase transitions (faster than original)
        if self.phase == "ground_explosion" and self.timer >= 0.2:
            self._start_burst()
        elif self.phase == "burst" and self.timer >= 0.4:
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "ground_explosion":
            if self.ground_explosion:
                self.ground_explosion.draw(surface)

        elif self.phase == "burst":
            # Ground explosion still fading
            if self.ground_explosion:
                self.ground_explosion.draw(surface)

            # Cone burst and shrapnel
            if self.cone_burst:
                self.cone_burst.draw(surface)

            for fragment in self.shrapnel_fragments:
                fragment.draw(surface)

        elif self.phase == "impact":
            # Draw fragments still traveling
            for fragment in self.shrapnel_fragments:
                fragment.draw(surface)

            # Draw embedded shrapnel
            for embedded in self.embedded_shrapnel:
                embedded.draw(surface)


# ============================================================================
# GAUSSIAN DUSK ANIMATIONS (Rail Gun Charging and Firing)
# ============================================================================

class ChargingCoil:
    """
    Pulsing cyan electromagnetic coil ring around the rail gun.
    Expands and contracts with increasing intensity.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 2.0  # Lasts through entire charge
        self.active = True
        self.base_radius = 30
        self.pulse_speed = 6.0

    def update(self, delta_time):
        """Update coil pulsing."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw pulsing electromagnetic coil."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Pulsing radius
        pulse = math.sin(self.timer * self.pulse_speed) * 0.3 + 0.7
        radius = int(self.base_radius * progress * pulse)

        # Intensity increases over time
        alpha = int(200 * progress * pulse)

        if alpha > 20 and radius > 5:
            coil_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
            center = radius + 5

            # Outer glow (cyan)
            pygame.draw.circle(coil_surf, (0, 204, 255, alpha // 3),
                             (center, center), radius + 5, 2)

            # Main coil ring (bright cyan)
            pygame.draw.circle(coil_surf, (0, 204, 255, alpha),
                             (center, center), radius, 3)

            # Inner bright ring
            pygame.draw.circle(coil_surf, (100, 230, 255, min(255, alpha + 55)),
                             (center, center), max(1, radius - 3), 2)

            surface.blit(coil_surf, (int(self.center_x - center), int(self.center_y - center)))


class EnergyParticle:
    """
    Small cyan particle spiraling into the rail gun.
    Represents energy being drawn in during charging.
    """
    def __init__(self, start_x, start_y, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 1.2
        self.active = True

        # Start position (offset from center)
        angle = random.uniform(0, math.pi * 2)
        distance = random.uniform(60, 100)
        self.start_x = center_x + math.cos(angle) * distance
        self.start_y = center_y + math.sin(angle) * distance

        # Spiral parameters
        self.rotation_speed = random.uniform(4, 8)
        self.initial_angle = angle

    def update(self, delta_time):
        """Update particle spiral motion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw spiraling energy particle."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Spiral inward
        distance = (1.0 - progress) * 80
        angle = self.initial_angle + progress * self.rotation_speed

        x = self.center_x + math.cos(angle) * distance
        y = self.center_y + math.sin(angle) * distance

        # Fade in then out
        if progress < 0.3:
            alpha = int(255 * (progress / 0.3))
        else:
            alpha = int(255 * (1.0 - (progress - 0.3) / 0.7))

        if alpha > 20:
            size = 4
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

            # Cyan glow
            pygame.draw.circle(particle_surf, (0, 204, 255, alpha // 2),
                             (size, size), size)
            pygame.draw.circle(particle_surf, (100, 230, 255, alpha),
                             (size, size), size // 2)

            surface.blit(particle_surf, (int(x - size), int(y - size)))


class RailChargeGlow:
    """
    Expanding cyan aura around the rail gun during charging.
    Grows more intense as charge builds.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 2.5
        self.active = True
        self.max_radius = 50

    def update(self, delta_time):
        """Update glow expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding charge glow."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Pulsing effect
        pulse = math.sin(self.timer * 8) * 0.2 + 0.8

        # Expand to full size
        radius = int(self.max_radius * progress)

        # Alpha increases with progress
        alpha = int(180 * progress * pulse)

        if alpha > 20 and radius > 0:
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Multiple layers for depth
            # Outer layer
            pygame.draw.circle(glow_surf, (0, 150, 200, alpha // 4),
                             (radius, radius), radius)
            # Mid layer
            pygame.draw.circle(glow_surf, (0, 204, 255, alpha // 2),
                             (radius, radius), int(radius * 0.7))
            # Inner bright core
            pygame.draw.circle(glow_surf, (100, 230, 255, alpha),
                             (radius, radius), int(radius * 0.4))

            surface.blit(glow_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class GaussianDuskChargeAnimation:
    """
    Gaussian Dusk charging animation for FOWL CONTRIVANCE.
    Rail gun charges with electromagnetic energy, dimming the map like sunset.

    Phases:
    1. Charge Start (0.5s) - Energy gathering, coils appear
    2. Charge Sustain (1.5s) - Pulsing glow, map dims to sunset colors
    3. Charge Ready (0.5s) - Intense glow, fully charged
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Gaussian Dusk charging animation.

        Args:
            caster_unit: Unit charging the rail gun
            camera: Camera instance for coordinate conversion
            screen_flash_callback: For creating persistent sunset dimming effect
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert caster position to screen coords
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                             caster_unit.grid_y,
                                                             centered=True)

        # Animation state
        self.phase = "charge_start"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.charging_coils = []
        self.energy_particles = []
        self.charge_glow = None

        # Start Phase 1
        self._start_charge_start()

    def _start_charge_start(self):
        """Phase 1: Charge Start - Energy gathering."""
        self.phase = "charge_start"
        self.timer = 0

        # Create charging coil
        coil = ChargingCoil(self.caster_x, self.caster_y)
        self.charging_coils.append(coil)

        # Create spiraling energy particles
        for i in range(12):
            delay = i * 0.04
            particle = EnergyParticle(self.caster_x, self.caster_y,
                                     self.caster_x, self.caster_y, delay=delay)
            self.energy_particles.append(particle)

        # Light screen shake
        self.screen_shake_callback(2, 0.4)

    def _start_charge_sustain(self):
        """Phase 2: Charge Sustain - Pulsing glow."""
        self.phase = "charge_sustain"
        self.timer = 0

        # Create charge glow
        self.charge_glow = RailChargeGlow(self.caster_x, self.caster_y)

        # Continue particles
        for i in range(8):
            delay = i * 0.08
            particle = EnergyParticle(self.caster_x, self.caster_y,
                                     self.caster_x, self.caster_y, delay=delay)
            self.energy_particles.append(particle)

        # Sustained shake
        self.screen_shake_callback(3, 1.2)

    def _start_charge_ready(self):
        """Phase 3: Charge Ready - Intense glow, fully charged."""
        self.phase = "charge_ready"
        self.timer = 0

        # Add more intense particles
        for i in range(6):
            delay = i * 0.05
            particle = EnergyParticle(self.caster_x, self.caster_y,
                                     self.caster_x, self.caster_y, delay=delay)
            self.energy_particles.append(particle)

        # Heavier shake
        self.screen_shake_callback(4, 0.5)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update all sub-effects
        for coil in self.charging_coils:
            coil.update(delta_time)

        for particle in self.energy_particles:
            particle.update(delta_time)

        if self.charge_glow:
            self.charge_glow.update(delta_time)

        # Phase transitions
        if self.phase == "charge_start" and self.timer >= 0.5:
            self._start_charge_sustain()
        elif self.phase == "charge_sustain" and self.timer >= 1.5:
            self._start_charge_ready()
        elif self.phase == "charge_ready" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw charge glow first (background)
        if self.charge_glow:
            self.charge_glow.draw(surface)

        # Draw charging coils
        for coil in self.charging_coils:
            coil.draw(surface)

        # Draw energy particles (foreground)
        for particle in self.energy_particles:
            particle.draw(surface)


# Rail Beam and Fire Animation classes
class HypersonicProjectile:
    """
    Hypersonic rail projectile that travels across the entire map at extreme speed.
    Leaves a bright glowing trail and shockwave effects as it moves.
    """
    def __init__(self, start_x, start_y, direction, positions, camera):
        self.start_x = start_x
        self.start_y = start_y
        self.direction = direction  # (dy, dx) tuple
        self.positions = positions  # List of (grid_y, grid_x) hit positions
        self.camera = camera
        self.timer = 0
        self.duration = 0.25  # Much faster - travels full map in 0.25s
        self.active = True

        # Convert all grid positions to screen coordinates
        self.screen_positions = []
        for grid_y, grid_x in positions:
            screen_x, screen_y = camera.grid_to_screen(grid_x, grid_y, centered=True)
            self.screen_positions.append((screen_x, screen_y))

        # Calculate end position (last position in line)
        if self.screen_positions:
            self.end_x, self.end_y = self.screen_positions[-1]
        else:
            # Fallback if no positions
            self.end_x, self.end_y = start_x, start_y

        # Calculate total distance for speed
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        self.total_distance = math.sqrt(dx * dx + dy * dy)

        # Trail points for motion blur
        self.trail_points = []
        self.max_trail_length = 8  # Number of trail segments

    def update(self, delta_time):
        """Update projectile movement."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw hypersonic projectile with motion blur trail."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Current projectile position
        current_x = self.start_x + (self.end_x - self.start_x) * progress
        current_y = self.start_y + (self.end_y - self.start_y) * progress

        # Calculate projectile direction vector for elongation
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            dir_x = dx / length
            dir_y = dy / length
        else:
            dir_x, dir_y = 0, 0

        # Projectile is elongated in direction of travel (like a streak)
        projectile_length = 40
        tail_x = current_x - dir_x * projectile_length
        tail_y = current_y - dir_y * projectile_length

        # Add current position to trail
        self.trail_points.append((current_x, current_y))
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop(0)

        # Draw motion blur trail (fading segments behind projectile)
        for i, (tx, ty) in enumerate(self.trail_points[:-1]):
            fade = (i + 1) / len(self.trail_points)  # Fade from 0 to 1
            alpha = int(120 * fade)

            # Trail segments get thinner and dimmer
            trail_width = int(8 * fade)
            pygame.draw.circle(surface, (0, 204, 255, alpha),
                             (int(tx), int(ty)), trail_width)

        # Draw shockwave rings at intervals
        if progress < 0.9:  # Don't draw at the very end
            # Create expanding ring effect
            ring_progress = (progress * 5) % 1.0  # Multiple rings
            ring_radius = int(20 + ring_progress * 30)
            ring_alpha = int(180 * (1.0 - ring_progress))
            if ring_alpha > 0:
                pygame.draw.circle(surface, (200, 230, 255, ring_alpha),
                                 (int(current_x), int(current_y)), ring_radius, 2)

        # Draw the hypersonic projectile itself (elongated streak)
        # Outer glow
        pygame.draw.line(surface, (0, 204, 255, 100),
                        (int(tail_x), int(tail_y)),
                        (int(current_x), int(current_y)), 12)

        # Mid layer (bright cyan)
        pygame.draw.line(surface, (0, 230, 255, 200),
                        (int(tail_x), int(tail_y)),
                        (int(current_x), int(current_y)), 8)

        # Inner core (white-cyan)
        pygame.draw.line(surface, (200, 250, 255, 255),
                        (int(tail_x), int(tail_y)),
                        (int(current_x), int(current_y)), 4)

        # Bright core
        pygame.draw.line(surface, (255, 255, 255, 255),
                        (int(tail_x), int(tail_y)),
                        (int(current_x), int(current_y)), 2)

        # Projectile head (bright point)
        pygame.draw.circle(surface, (255, 255, 255, 255),
                         (int(current_x), int(current_y)), 4)
        pygame.draw.circle(surface, (200, 250, 255, 200),
                         (int(current_x), int(current_y)), 6)


class BeamImpact:
    """
    Explosion effect where the beam hits terrain or units.
    Cyan/white burst with sparks.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True
        self.max_radius = 35

    def update(self, delta_time):
        """Update impact explosion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw impact explosion."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Fast expansion
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        # Fade out
        alpha = int(255 * (1.0 - progress))

        if alpha > 20 and radius > 0:
            impact_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Outer cyan glow
            pygame.draw.circle(impact_surf, (0, 204, 255, alpha // 3),
                             (center, center), radius + 10)

            # Main cyan explosion
            pygame.draw.circle(impact_surf, (0, 230, 255, alpha),
                             (center, center), radius)

            # Inner white core
            inner_radius = int(radius * 0.6)
            pygame.draw.circle(impact_surf, (200, 250, 255, alpha),
                             (center, center), inner_radius)

            # Bright center
            if progress < 0.4:
                core_radius = int(radius * 0.3)
                pygame.draw.circle(impact_surf, (255, 255, 255, alpha),
                                 (center, center), core_radius)

            surface.blit(impact_surf, (int(self.center_x - center), int(self.center_y - center)))


class ElectricArc:
    """
    Sparking electric arc along the beam path.
    Random jagged lightning bolts.
    """
    def __init__(self, x, y, delay=0):
        self.x = x
        self.y = y
        self.timer = -delay
        self.duration = 0.3
        self.active = True

        # Random arc direction
        angle = random.uniform(0, math.pi * 2)
        length = random.uniform(15, 30)
        self.end_x = x + math.cos(angle) * length
        self.end_y = y + math.sin(angle) * length

    def update(self, delta_time):
        """Update arc."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw electric arc."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Fade out
        alpha = int(255 * (1.0 - progress))

        if alpha > 30:
            # Jagged lightning effect (simple)
            pygame.draw.line(surface, (100, 230, 255, alpha),
                           (int(self.x), int(self.y)),
                           (int(self.end_x), int(self.end_y)), 2)


class GaussianDuskFireAnimation:
    """
    Gaussian Dusk firing animation for FOWL CONTRIVANCE.
    Massive rail gun beam pierces across the entire map.

    Phases:
    1. Pre-Fire (0.2s) - Bright flash, clear dimming
    2. Beam Travel (0.8s) - Beam extends across map, impacts appear
    3. Aftermath (0.6s) - Sparks, smoke, rail visual effects
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Gaussian Dusk firing animation.

        Args:
            caster_unit: Unit firing the rail gun
            target_pos: Direction vector (dy, dx) for firing line
            camera: Camera instance for coordinate conversion
            game: Game instance to calculate firing line positions
        """
        # Store references
        self.caster = caster_unit
        self.target_pos = target_pos  # This is actually the direction vector!
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert caster position to screen coords
        self.caster_x, self.caster_y = camera.grid_to_screen(caster_unit.grid_x,
                                                             caster_unit.grid_y,
                                                             centered=True)

        # Calculate firing line positions
        self.firing_positions = []
        if game:
            dy, dx = target_pos  # Direction vector
            y, x = caster_unit.grid_y, caster_unit.grid_x

            # Trace the line across the entire map
            while 0 <= y + dy < game.map.height and 0 <= x + dx < game.map.width:
                y += dy
                x += dx
                self.firing_positions.append((y, x))

        # Animation state
        self.phase = "pre_fire"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.projectile = None
        self.impacts = []
        self.electric_arcs = []
        self.passed_positions = []  # Track which positions the projectile has passed

        # Start Phase 1
        self._start_pre_fire()

    def _start_pre_fire(self):
        """Phase 1: Pre-Fire - Brief muzzle flash."""
        self.phase = "pre_fire"
        self.timer = 0

        # Brief bright flash on firing
        self.screen_flash_callback((200, 230, 255), 0.05)

    def _start_beam_travel(self):
        """Phase 2: Projectile Travel - Hypersonic projectile screams across map."""
        self.phase = "beam_travel"
        self.timer = 0

        # Create hypersonic projectile
        if self.firing_positions:
            self.projectile = HypersonicProjectile(self.caster_x, self.caster_y,
                                                   self.target_pos, self.firing_positions,
                                                   self.camera)

        # Pre-create all impact objects but they'll activate as projectile passes
        for i, (grid_y, grid_x) in enumerate(self.firing_positions):
            screen_x, screen_y = self.camera.grid_to_screen(grid_x, grid_y, centered=True)
            impact = BeamImpact(screen_x, screen_y, delay=999)  # Huge delay, will be triggered manually
            self.impacts.append(impact)

            # Add electric arcs
            for _ in range(2):
                arc = ElectricArc(screen_x, screen_y, delay=999)  # Huge delay, will be triggered manually
                self.electric_arcs.append(arc)

        # Emit particles at caster position (muzzle flash)
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y,
                                            (0, 204, 255), count=50)

        # Strong screen shake on firing (shorter but intense)
        self.screen_shake_callback(12, 0.3)

        # Bright cyan flash
        self.screen_flash_callback((0, 204, 255), 0.15)

    def _start_aftermath(self):
        """Phase 3: Aftermath - Sparks, smoke, effects."""
        self.phase = "aftermath"
        self.timer = 0

        # Emit particles along beam path
        if self.particle_emitter:
            for grid_y, grid_x in self.firing_positions[::3]:  # Every 3rd position
                screen_x, screen_y = self.camera.grid_to_screen(grid_x, grid_y, centered=True)
                self.particle_emitter.emit_burst(screen_x, screen_y,
                                                (100, 230, 255), count=10)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update projectile
        if self.projectile:
            self.projectile.update(delta_time)

            # Check which positions the projectile has passed and trigger impacts
            if self.phase == "beam_travel":
                progress = min(1.0, self.projectile.timer / self.projectile.duration)
                positions_passed = int(progress * len(self.firing_positions))

                # Trigger impacts for newly passed positions
                for i in range(len(self.passed_positions), positions_passed):
                    if i < len(self.impacts):
                        # Trigger this impact and arcs
                        self.impacts[i].delay = 0  # Activate immediately
                        # Activate corresponding arcs (2 per impact)
                        arc_start = i * 2
                        if arc_start < len(self.electric_arcs):
                            self.electric_arcs[arc_start].delay = 0
                        if arc_start + 1 < len(self.electric_arcs):
                            self.electric_arcs[arc_start + 1].delay = 0
                        self.passed_positions.append(i)

        # Update all sub-effects
        for impact in self.impacts:
            impact.update(delta_time)

        for arc in self.electric_arcs:
            arc.update(delta_time)

        # Phase transitions (much faster)
        if self.phase == "pre_fire" and self.timer >= 0.1:
            self._start_beam_travel()
        elif self.phase == "beam_travel" and self.timer >= 0.35:  # 0.1 pre + 0.25 travel
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.5:  # Shorter aftermath
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "pre_fire":
            # Brief flash only (handled by screen flash)
            pass

        elif self.phase == "beam_travel":
            # Draw impacts first (background)
            for impact in self.impacts:
                impact.draw(surface)

            # Draw electric arcs
            for arc in self.electric_arcs:
                arc.draw(surface)

            # Draw hypersonic projectile on top (foreground)
            if self.projectile:
                self.projectile.draw(surface)

        elif self.phase == "aftermath":
            # Draw fading impacts and arcs
            for arc in self.electric_arcs:
                arc.draw(surface)

            for impact in self.impacts:
                impact.draw(surface)


# ============================================================================
# RAIL GENESIS DEATH EXPLOSION ANIMATION
# ============================================================================

class RailGlowPulse:
    """
    Pulsing orange energy glow on a rail tile during charge phase.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True
        self.max_radius = 20

    def update(self, delta_time):
        """Update pulse."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw pulsing glow on rail."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Pulsing effect
        pulse = 0.5 + 0.5 * math.sin(progress * math.pi * 4)

        # Growing intensity
        intensity = progress * pulse
        radius = int(self.max_radius * (0.5 + 0.5 * pulse))
        alpha = int(180 * intensity)

        if alpha > 20 and radius > 0:
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Orange glow layers
            pygame.draw.circle(glow_surf, (255, 102, 0, alpha // 3),
                             (radius, radius), radius)
            pygame.draw.circle(glow_surf, (255, 150, 0, alpha // 2),
                             (radius, radius), int(radius * 0.6))
            pygame.draw.circle(glow_surf, (255, 200, 50, alpha),
                             (radius, radius), int(radius * 0.3))

            surface.blit(glow_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class RailExplosion:
    """
    Orange fireball explosion on a rail tile.
    Rapidly expands then fades.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.35
        self.active = True
        self.max_radius = 30

    def update(self, delta_time):
        """Update explosion expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding fireball."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Fast expansion
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        # Fade out
        alpha = int(255 * (1.0 - progress))

        if alpha > 0 and radius > 0:
            fireball_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            center = radius + 10

            # Outer orange glow
            pygame.draw.circle(fireball_surf, (255, 80, 0, alpha // 3),
                             (center, center), radius + 8)

            # Main orange fireball
            pygame.draw.circle(fireball_surf, (255, 102, 0, alpha),
                             (center, center), radius)

            # Inner yellow-orange core
            inner_radius = int(radius * 0.6)
            pygame.draw.circle(fireball_surf, (255, 150, 0, alpha),
                             (center, center), inner_radius)

            # Bright center
            if progress < 0.3:
                core_radius = int(radius * 0.3)
                pygame.draw.circle(fireball_surf, (255, 200, 100, alpha),
                                 (center, center), core_radius)

            surface.blit(fireball_surf, (int(self.center_x - center), int(self.center_y - center)))


class RailShockwave:
    """
    Expanding dark orange shockwave ring from rail explosion.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True
        self.max_radius = 40

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

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Expand outward
        radius = int(self.max_radius * progress)

        # Fade out as expanding
        alpha = int(180 * (1.0 - progress))

        if alpha > 20 and radius > 5:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Dark orange shockwave ring
            pygame.draw.circle(ring_surf, (200, 100, 0, alpha),
                             (radius, radius), radius, 4)

            # Inner darker ring
            if alpha > 60:
                pygame.draw.circle(ring_surf, (180, 80, 0, alpha // 2),
                                 (radius, radius), radius - 2, 2)

            surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class RailSmoke:
    """
    Grey smoke puff rising from rail explosion site.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.5
        self.active = True
        self.max_radius = 25

    def update(self, delta_time):
        """Update smoke expansion and rise."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding smoke puff."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Expand and rise
        radius = int(self.max_radius * progress)
        rise_offset = int(15 * progress)  # Smoke rises up

        # Fade out
        alpha = int(150 * (1.0 - progress))

        if alpha > 0 and radius > 0:
            smoke_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            # Dark grey smoke layers
            for i in range(3):
                layer_radius = radius - (i * 5)
                if layer_radius > 0:
                    layer_alpha = alpha - (i * 30)
                    if layer_alpha > 0:
                        pygame.draw.circle(smoke_surf, (90, 90, 90, layer_alpha),
                                         (radius, radius), layer_radius)

            surface.blit(smoke_surf, (int(self.center_x - radius),
                                     int(self.center_y - radius - rise_offset)))


class EmberParticle:
    """
    Small orange ember particle floating upward from explosion.
    """
    def __init__(self, start_x, start_y, delay=0):
        self.x = start_x + random.uniform(-10, 10)
        self.y = start_y
        self.timer = -delay
        self.duration = 0.6
        self.active = True
        self.size = random.randint(2, 4)
        self.rise_speed = random.uniform(20, 40)
        self.drift_x = random.uniform(-5, 5)

    def update(self, delta_time):
        """Update ember position."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= 0:
            # Rise upward
            self.y -= self.rise_speed * delta_time
            self.x += self.drift_x * delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw floating ember."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Fade out
        alpha = int(220 * (1.0 - progress))

        if alpha > 30:
            ember_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            center = int(self.size * 1.5)

            # Orange glow
            pygame.draw.circle(ember_surf, (255, 102, 0, alpha // 2),
                             (center, center), self.size)
            pygame.draw.circle(ember_surf, (255, 150, 0, alpha),
                             (center, center), max(1, self.size // 2))

            surface.blit(ember_surf, (int(self.x - center), int(self.y - center)))


class RailGenesisDeathExplosionAnimation:
    """
    Rail Genesis death explosion animation for FOWL CONTRIVANCE.
    When a FOWL CONTRIVANCE dies, the entire rail network detonates,
    dealing damage to enemies standing on rails.

    Phases:
    1. Charge (0.4s) - Rails pulse with orange energy
    2. Detonation (0.6s) - Staggered explosions along all rails
    3. Shockwave (0.5s) - Orange shockwaves expand from each rail
    4. Aftermath (0.5s) - Smoke and embers dissipate
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Rail Genesis death explosion animation.

        Args:
            caster_unit: FOWL CONTRIVANCE unit that died (at death position)
            game: Game instance to access rail positions
            camera: Camera instance for coordinate conversion
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Get all rail positions from the game map
        self.rail_positions = []
        if game and game.map.has_rails():
            rail_grid_positions = game.map.get_rail_positions()

            # Convert all rail positions to screen coordinates
            for rail_y, rail_x in rail_grid_positions:
                screen_x, screen_y = camera.grid_to_screen(rail_x, rail_y, centered=True)
                self.rail_positions.append((screen_x, screen_y))

        # Animation state
        self.phase = "charge"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.rail_glows = []
        self.explosions = []
        self.shockwaves = []
        self.smoke_puffs = []
        self.embers = []

        # Start Phase 1: Charge
        self._start_charge()

    def _start_charge(self):
        """Phase 1: Charge - Rails pulse with orange energy."""
        self.phase = "charge"
        self.timer = 0

        # Create pulsing glows on all rails (staggered slightly)
        for i, (rail_x, rail_y) in enumerate(self.rail_positions):
            delay = (i % 10) * 0.02  # Stagger every 10th rail
            glow = RailGlowPulse(rail_x, rail_y, delay=delay)
            self.rail_glows.append(glow)

        # Light screen shake
        self.screen_shake_callback(3, 0.4)

    def _start_detonation(self):
        """Phase 2: Detonation - Explosions along all rails."""
        self.phase = "detonation"
        self.timer = 0

        # Create explosions at all rail positions (staggered for visual spread)
        for i, (rail_x, rail_y) in enumerate(self.rail_positions):
            # Stagger explosions to create wave effect
            delay = (i % 15) * 0.02
            explosion = RailExplosion(rail_x, rail_y, delay=delay)
            self.explosions.append(explosion)

        # Heavy screen shake on detonation
        self.screen_shake_callback(8, 0.6)

        # Orange flash
        self.screen_flash_callback((255, 102, 0), 0.3)

        # Emit burst particles at random rail positions
        if self.particle_emitter and len(self.rail_positions) > 0:
            # Emit at a subset of rails for performance
            sample_size = min(20, len(self.rail_positions))
            sample_rails = random.sample(self.rail_positions, sample_size)
            for rail_x, rail_y in sample_rails:
                self.particle_emitter.emit_burst(rail_x, rail_y, (255, 102, 0), count=8)

    def _start_shockwave(self):
        """Phase 3: Shockwave - Orange shockwaves expand."""
        self.phase = "shockwave"
        self.timer = 0

        # Create shockwaves at all rail positions (staggered)
        for i, (rail_x, rail_y) in enumerate(self.rail_positions):
            delay = (i % 15) * 0.02
            shockwave = RailShockwave(rail_x, rail_y, delay=delay)
            self.shockwaves.append(shockwave)

    def _start_aftermath(self):
        """Phase 4: Aftermath - Smoke and embers dissipate."""
        self.phase = "aftermath"
        self.timer = 0

        # Create smoke puffs at rail positions (subset for performance)
        if len(self.rail_positions) > 0:
            sample_size = min(30, len(self.rail_positions))
            sample_rails = random.sample(self.rail_positions, sample_size)

            for i, (rail_x, rail_y) in enumerate(sample_rails):
                delay = i * 0.01
                smoke = RailSmoke(rail_x, rail_y, delay=delay)
                self.smoke_puffs.append(smoke)

                # Add ember particles
                for _ in range(3):
                    ember = EmberParticle(rail_x, rail_y, delay=delay)
                    self.embers.append(ember)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update all sub-effects
        for glow in self.rail_glows:
            glow.update(delta_time)

        for explosion in self.explosions:
            explosion.update(delta_time)

        for shockwave in self.shockwaves:
            shockwave.update(delta_time)

        for smoke in self.smoke_puffs:
            smoke.update(delta_time)

        for ember in self.embers:
            ember.update(delta_time)

        # Phase transitions
        if self.phase == "charge" and self.timer >= 0.4:
            self._start_detonation()
        elif self.phase == "detonation" and self.timer >= 0.6:
            self._start_shockwave()
        elif self.phase == "shockwave" and self.timer >= 0.5:
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "charge":
            for glow in self.rail_glows:
                glow.draw(surface)

        elif self.phase == "detonation":
            for explosion in self.explosions:
                explosion.draw(surface)

        elif self.phase == "shockwave":
            # Draw explosions still fading
            for explosion in self.explosions:
                explosion.draw(surface)

            # Draw shockwaves
            for shockwave in self.shockwaves:
                shockwave.draw(surface)

        elif self.phase == "aftermath":
            # Draw smoke puffs
            for smoke in self.smoke_puffs:
                smoke.draw(surface)

            # Draw embers
            for ember in self.embers:
                ember.draw(surface)


# ============================================================================
# FOWL CONTRIVANCE BASIC ATTACK - ELECTROMAGNETIC BOLT
# ============================================================================

class FowlContrivanceElectromagneticAttack:
    """
    FOWL CONTRIVANCE basic attack animation - electromagnetic bolt from rail gun.
    Quick cyan energy shot that travels straight to target.
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
        self.phase = "charge"  # charge → fire → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.charge_duration = 0.1
        self.fire_duration = 0.2
        self.impact_duration = 0.15

        # Bolt position
        self.bolt_progress = 0.0

        # Cyan electromagnetic colors
        self.color_cyan = (0, 204, 255)      # #00ccff
        self.color_light_cyan = (100, 230, 255)
        self.color_white = (255, 255, 255)

    def _trigger_charge(self):
        """Phase 1: Brief electromagnetic charge."""
        # Small cyan particles converge at attacker
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(15, 25)
            x = self.attacker.x + math.cos(angle) * distance
            y = self.attacker.y + math.sin(angle) * distance

            # Particles move toward gun
            vx = -math.cos(angle) * 200
            vy = -math.sin(angle) * 200

            color = self.color_cyan if random.random() > 0.5 else self.color_light_cyan

            from .core import Particle
            particle = Particle(x, y, vx, vy, color, size=2, lifetime=0.12)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_fire(self):
        """Phase 2: Fire electromagnetic bolt."""
        # Create trailing particles along bolt path
        for i in range(8):
            progress = i / 8
            trail_x = self.attacker.x + self.dx * self.distance * progress * 0.2
            trail_y = self.attacker.y + self.dy * self.distance * progress * 0.2

            vx = self.dx * 150
            vy = self.dy * 150

            color = random.choice([self.color_cyan, self.color_light_cyan])

            from .core import Particle
            particle = Particle(trail_x, trail_y, vx, vy, color,
                              size=random.uniform(2, 3), lifetime=0.15)
            particle.gravity = 0
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Electromagnetic impact."""
        # Cyan spark burst
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = random.choice([
                self.color_cyan,
                self.color_light_cyan,
                self.color_white,
            ])

            from .core import Particle
            particle = Particle(self.target.x, self.target.y, vx, vy, color,
                              size=random.uniform(2, 4), lifetime=random.uniform(0.15, 0.25))
            particle.gravity = 100
            self.particle_emitter.particles.append(particle)

        # Light impact
        self.target.shake_intensity = 8
        self.screen_shake(4, 0.12)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == "charge":
            if self.timer == 0 or not hasattr(self, '_charge_triggered'):
                self._trigger_charge()
                self._charge_triggered = True

            if self.timer >= self.charge_duration:
                self.phase = "fire"
                self.timer = 0
                self._trigger_fire()

        elif self.phase == "fire":
            # Update bolt progress
            self.bolt_progress = min(1.0, self.timer / self.fire_duration)

            if self.timer >= self.fire_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw electromagnetic bolt."""
        import pygame

        # Draw charging glow
        if self.phase == "charge":
            progress = self.timer / self.charge_duration
            glow_radius = int(15 * progress)

            if glow_radius > 2:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_cyan, int(100 * progress)),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(self.attacker.x - glow_radius),
                                        int(self.attacker.y - glow_radius)))

                # Bright center
                core_radius = int(glow_radius * 0.5)
                if core_radius > 1:
                    core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(core_surf, (*self.color_light_cyan, int(180 * progress)),
                                     (core_radius, core_radius), core_radius)
                    surface.blit(core_surf, (int(self.attacker.x - core_radius),
                                            int(self.attacker.y - core_radius)))

        # Draw electromagnetic bolt during fire phase
        if self.phase == "fire":
            # Calculate bolt position
            bolt_x = self.attacker.x + self.dx * self.distance * self.bolt_progress
            bolt_y = self.attacker.y + self.dy * self.distance * self.bolt_progress

            # Draw bolt as elongated streak
            bolt_length = 20
            tail_x = bolt_x - self.dx * bolt_length
            tail_y = bolt_y - self.dy * bolt_length

            # Outer glow (widest)
            pygame.draw.line(surface, (*self.color_cyan, 80),
                           (int(tail_x), int(tail_y)),
                           (int(bolt_x), int(bolt_y)), 10)

            # Mid layer (bright cyan)
            pygame.draw.line(surface, (*self.color_light_cyan, 160),
                           (int(tail_x), int(tail_y)),
                           (int(bolt_x), int(bolt_y)), 6)

            # Inner core (white-cyan)
            pygame.draw.line(surface, self.color_white,
                           (int(tail_x), int(tail_y)),
                           (int(bolt_x), int(bolt_y)), 3)

            # Bolt head (bright point)
            pygame.draw.circle(surface, self.color_white,
                             (int(bolt_x), int(bolt_y)), 4)
            pygame.draw.circle(surface, (*self.color_light_cyan, 180),
                             (int(bolt_x), int(bolt_y)), 6)

        # Draw impact flash
        if self.phase == "impact":
            progress = self.timer / self.impact_duration
            if progress < 0.5:
                flash_alpha = int(255 * (1.0 - progress / 0.5))
                flash_radius = int(25 * (1.0 + progress))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                # White outer flash
                pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                # Cyan center
                center_radius = int(flash_radius * 0.6)
                pygame.draw.circle(flash_surf, (*self.color_cyan, flash_alpha),
                                 (flash_radius, flash_radius), center_radius)

                surface.blit(flash_surf, (int(self.target.x - flash_radius),
                                         int(self.target.y - flash_radius)))
