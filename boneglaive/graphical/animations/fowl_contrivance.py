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
    Individual mortar shell following parabolic arc trajectory.
    Orange trail showing shell path through the air.
    """
    def __init__(self, start_x, start_y, target_x, target_y, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.timer = -delay  # Negative for staggered start
        self.duration = 0.6  # Arc travel time
        self.active = True

        # Calculate arc parameters
        self.dx = target_x - start_x
        self.dy = target_y - start_y
        self.distance = math.sqrt(self.dx * self.dx + self.dy * self.dy)

        # Arc height based on distance (higher arc for longer shots)
        self.arc_height = min(100, self.distance * 0.4)

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
                'lifetime': 0.2,  # Trail fades quickly
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
        """Draw shell and its trail."""
        if not self.active or self.timer < 0:
            return

        # Draw trail as fading orange line segments
        if len(self.trail_points) > 1:
            for i in range(len(self.trail_points) - 1):
                p1 = self.trail_points[i]
                p2 = self.trail_points[i + 1]

                # Fade based on age
                alpha = int(200 * (1.0 - p1['age'] / p1['lifetime']))

                if alpha > 20:
                    trail_surf = pygame.Surface((abs(int(p2['x'] - p1['x'])) + 10,
                                                abs(int(p2['y'] - p1['y'])) + 10), pygame.SRCALPHA)

                    # Bright orange trail
                    start_local = (5, 5)
                    end_local = (int(p2['x'] - p1['x'] + 5), int(p2['y'] - p1['y'] + 5))

                    pygame.draw.line(trail_surf, (255, 150, 0, alpha),
                                   start_local, end_local, 3)

                    surface.blit(trail_surf, (int(p1['x']) - 5, int(p1['y']) - 5))

        # Draw shell as bright orange circle at current position
        if self.trail_points:
            current = self.trail_points[-1]
            shell_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(shell_surf, (255, 204, 0, 255), (6, 6), 4)
            pygame.draw.circle(shell_surf, (255, 150, 0, 200), (6, 6), 6)
            surface.blit(shell_surf, (int(current['x']) - 6, int(current['y']) - 6))


class ExplosionFireball:
    """
    Orange/yellow fireball explosion at impact point.
    Rapidly expands then fades out.
    """
    def __init__(self, center_x, center_y, is_primary=False):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.3
        self.active = True

        # Primary (center) explosion is larger
        self.max_radius = 35 if is_primary else 28
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


class ParabolAnimation:
    """
    Parabol (mortar barrage) skill animation for FOWL CONTRIVANCE.
    Launches explosive mortar shells in a 3x3 area with indirect fire.

    Phases:
    1. Launch - Smoke puff at caster, screen shake
    2. Arc Travel - 9 shells following parabolic trajectories
    3. Impact - Sequential explosions with fireballs and shockwaves
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

        # Launch screen shake
        self.screen_shake_callback(3, 0.3)

        # Emit smoke particles at launch
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (90, 90, 90), count=15)

    def _start_arc_travel(self):
        """Phase 2: Arc Travel - Shells fly through the air."""
        self.phase = "arc_travel"
        self.timer = 0

        # Create mortar shells for each impact position
        for i, impact in enumerate(self.impact_positions):
            # Stagger shell launches slightly
            delay = i * 0.05
            shell = MortarShell(self.caster_x, self.caster_y,
                              impact['x'], impact['y'], delay=delay)
            self.mortar_shells.append(shell)

    def _start_impact(self):
        """Phase 3: Impact - Explosions at each target position."""
        self.phase = "impact"
        self.timer = 0

        # Create explosions and shockwaves for each impact
        for impact in self.impact_positions:
            # Fireball explosion
            explosion = ExplosionFireball(impact['x'], impact['y'], is_primary=impact['is_primary'])
            # Delay matches shell delay
            explosion.timer = -impact['delay']
            self.explosions.append(explosion)

            # Shockwave ring
            shockwave = ShockwaveRing(impact['x'], impact['y'], delay=impact['delay'])
            self.shockwaves.append(shockwave)

            # Emit burst particles at each impact (delayed to match)
            if self.particle_emitter and impact['delay'] == 0:  # Primary impact immediate
                self.particle_emitter.emit_burst(impact['x'], impact['y'], (255, 150, 0), count=30)

        # Impact screen shake (heavier)
        self.screen_shake_callback(5, 0.4)

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

        # Phase transitions
        if self.phase == "launch" and self.timer >= 0.4:
            self._start_arc_travel()
        elif self.phase == "arc_travel" and self.timer >= 0.6:
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.8:
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.4:
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


class FragcrestAnimation:
    """
    Fragcrest (directional fragmentation cone) skill animation for FOWL CONTRIVANCE.
    Unfolds mechanical tail and fires explosive shrapnel in a 90-degree cone.

    Phases:
    1. Tail Unfold - Mechanical tail fans out
    2. Charge - Orange energy builds up
    3. Burst - Explosive cone release with shrapnel
    4. Impact - Fragments hit targets with embedded shrapnel effects
    5. Aftermath - Tail retracts, embers fade
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Fragcrest animation.

        Args:
            target_pos: (grid_y, grid_x) - primary target position
            target_unit: Primary target unit (for cone direction calculation)
            camera: Camera instance for coordinate conversion
            game: Game instance to calculate cone positions
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

        # Calculate cone positions using the skill's logic
        # Need to calculate cone from caster to target
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

        # Animation state
        self.phase = "tail_unfold"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.tail_fan = None
        self.charge_glow = None
        self.cone_burst = None
        self.shrapnel_fragments = []
        self.embedded_shrapnel = []

        # Start Phase 1: Tail Unfold
        self._start_tail_unfold()

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

    def _start_tail_unfold(self):
        """Phase 1: Tail Unfold - Mechanical tail fans out."""
        self.phase = "tail_unfold"
        self.timer = 0

        # Create tail fan mechanism
        self.tail_fan = TailFanMechanism(self.caster_x, self.caster_y)

        # Light screen shake for mechanical deployment
        self.screen_shake_callback(2, 0.2)

    def _start_charge(self):
        """Phase 2: Charge - Energy builds up."""
        self.phase = "charge"
        self.timer = 0

        # Create charge glow
        self.charge_glow = ChargeGlow(self.caster_x, self.caster_y)

        # Emit charging particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (255, 150, 0), count=12)

    def _start_burst(self):
        """Phase 3: Burst - Explosive cone release."""
        self.phase = "burst"
        self.timer = 0

        # Calculate direction from caster to target
        direction_x = self.target_x - self.caster_x
        direction_y = self.target_y - self.caster_y

        # Create cone burst effect
        self.cone_burst = ConeBurst(self.caster_x, self.caster_y, direction_x, direction_y)

        # Create shrapnel fragments for each cone position
        for i, pos in enumerate(self.cone_screen_positions):
            # Stagger fragment launches slightly
            delay = 0.05 * i if not pos['is_primary'] else 0
            fragment = ShrapnelFragment(
                self.caster_x, self.caster_y,
                pos['x'], pos['y'],
                delay=delay,
                is_primary=pos['is_primary']
            )
            self.shrapnel_fragments.append(fragment)

        # Heavy screen shake for burst
        self.screen_shake_callback(6, 0.3)

        # Emit burst particles
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.caster_x, self.caster_y, (255, 102, 0), count=40)

    def _start_impact(self):
        """Phase 4: Impact - Fragments hit targets."""
        self.phase = "impact"
        self.timer = 0

        # Create embedded shrapnel at each impact position
        for i, pos in enumerate(self.cone_screen_positions):
            delay = 0.05 * i if not pos['is_primary'] else 0
            embedded = EmbeddedShrapnel(pos['x'], pos['y'], delay=delay)
            self.embedded_shrapnel.append(embedded)

            # Emit impact particles
            if self.particle_emitter and delay == 0:  # Primary impact immediate
                self.particle_emitter.emit_burst(pos['x'], pos['y'], (255, 102, 0), count=20)

    def _start_aftermath(self):
        """Phase 5: Aftermath - Effects fade."""
        self.phase = "aftermath"
        self.timer = 0

        # Emit floating embers at impact sites
        if self.particle_emitter:
            for pos in self.cone_screen_positions:
                self.particle_emitter.emit_float(pos['x'], pos['y'], (255, 102, 0), count=5)

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update sub-effects
        if self.tail_fan:
            self.tail_fan.update(delta_time)

        if self.charge_glow:
            self.charge_glow.update(delta_time)

        if self.cone_burst:
            self.cone_burst.update(delta_time)

        for fragment in self.shrapnel_fragments:
            fragment.update(delta_time)

        for embedded in self.embedded_shrapnel:
            embedded.update(delta_time)

        # Phase transitions
        if self.phase == "tail_unfold" and self.timer >= 0.3:
            self._start_charge()
        elif self.phase == "charge" and self.timer >= 0.4:
            self._start_burst()
        elif self.phase == "burst" and self.timer >= 0.5:
            self._start_impact()
        elif self.phase == "impact" and self.timer >= 0.6:
            self._start_aftermath()
        elif self.phase == "aftermath" and self.timer >= 0.4:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Draw phase-specific effects
        if self.phase == "tail_unfold":
            if self.tail_fan:
                self.tail_fan.draw(surface)

        elif self.phase == "charge":
            if self.tail_fan:
                self.tail_fan.draw(surface)
            if self.charge_glow:
                self.charge_glow.draw(surface)

        elif self.phase == "burst":
            if self.cone_burst:
                self.cone_burst.draw(surface)
            for fragment in self.shrapnel_fragments:
                fragment.draw(surface)

        elif self.phase in ["impact", "aftermath"]:
            # Draw fragments still traveling
            for fragment in self.shrapnel_fragments:
                fragment.draw(surface)

            # Draw embedded shrapnel
            for embedded in self.embedded_shrapnel:
                embedded.draw(surface)
