#!/usr/bin/env python3
"""
PELOTARI Animation Classes
Skill animations for the PELOTARI DLC unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, Particle


class MatadorPelota:
    """
    MASSIVE animated pelota projectile for Matador skill.
    Full tile-sized (46px diameter) cream and royal blue ball with golden glow.
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the huge pelota.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties
        self.size = TILE_SIZE  # HUGE: full tile diameter (46px)
        self.glow_size = int(self.size * 1.3)  # 60px glow
        self.rotation = 0  # Rotation angle for spinning effect
        self.rotation_speed = 360  # degrees per second

        # Colors from Matador.svg
        self.color_cream = (240, 232, 208)  # #f0e8d0
        self.color_white = (255, 255, 255)  # #ffffff
        self.color_royal_blue = (42, 90, 154)  # #2a5a9a
        self.color_med_blue = (74, 122, 186)  # #4a7aba
        self.color_gold = (192, 176, 144)  # #c0b090

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 8

    def move_to(self, world_x, world_y):
        """Move pelota to new world position."""
        # Store trail position
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if screen_pos:
            self.trail_positions.append((screen_pos[0], screen_pos[1], 1.0))

        # Trim trail
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)

        self.world_x = world_x
        self.world_y = world_y

    def update(self, delta_time):
        """Update pelota animation."""
        # Rotate for spinning effect
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.9) for x, y, alpha in self.trail_positions
            if alpha > 0.05
        ]

        return True

    def draw(self, surface):
        """Draw the massive pelota with all layers."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.5 + 0.5 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 100)

            # Cream trail
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_cream, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Layer 1: Golden glow (outer)
        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(10):
            radius = self.glow_size - radius_offset * 2
            alpha = int(50 * (1.0 - radius_offset / 10))
            pygame.draw.circle(glow_surf, (*self.color_gold, alpha),
                             (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 2: Main cream ball
        pygame.draw.circle(surface, self.color_cream, (int(cx), int(cy)), self.size // 2)

        # Layer 3: Royal blue rim/stroke
        pygame.draw.circle(surface, self.color_royal_blue, (int(cx), int(cy)),
                         self.size // 2, 2)

        # Layer 4: Bright white core
        core_size = int(self.size * 0.7) // 2
        pygame.draw.circle(surface, self.color_white, (int(cx), int(cy)), core_size)

        # Layer 5: Seam details (curved stitching lines)
        # Draw curved lines to simulate jai alai ball stitching
        seam_radius = self.size // 2 - 4
        angle_rad = math.radians(self.rotation)

        # Vertical-ish seam
        seam_points_1 = []
        for i in range(-4, 5):
            t = i / 4.0
            angle = angle_rad + t * 0.8
            offset_x = math.sin(angle) * seam_radius * 0.3
            x = cx + offset_x
            y = cy + t * seam_radius
            seam_points_1.append((int(x), int(y)))

        if len(seam_points_1) >= 2:
            pygame.draw.lines(surface, self.color_gold, False, seam_points_1, 2)

        # Horizontal-ish seam
        seam_points_2 = []
        for i in range(-4, 5):
            t = i / 4.0
            angle = angle_rad + math.pi / 2 + t * 0.8
            offset_y = math.sin(angle) * seam_radius * 0.3
            x = cx + t * seam_radius
            y = cy + offset_y
            seam_points_2.append((int(x), int(y)))

        if len(seam_points_2) >= 2:
            pygame.draw.lines(surface, self.color_gold, False, seam_points_2, 2)

        # Layer 6: Highlight glare (top-left)
        glare_offset_x = int(cx - self.size * 0.2)
        glare_offset_y = int(cy - self.size * 0.2)
        glare_size = self.size // 6
        pygame.draw.circle(surface, (255, 255, 255, 180),
                         (glare_offset_x, glare_offset_y), glare_size)


class MatadorAnimation:
    """
    Epic animation for PELOTARI's Matador skill.
    Game-ending finisher with MASSIVE pelota projectile.
    """

    def __init__(self, caster_unit, target_pos, camera, particle_emitter, game=None, bounce_count=2):
        """
        Initialize Matador animation.

        Args:
            caster_unit: AnimatedUnit casting the skill
            target_pos: (grid_y, grid_x) target position
            camera: Camera instance
            particle_emitter: ParticleEmitter for effects
            game: Game instance (needed for ricochet physics/wall detection)
            bounce_count: Number of bounces (dynamically calculated by skill, default 2)
        """
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.game = game
        self.caster_unit = caster_unit

        # Calculate trajectory from caster to target WITH ricochets
        self.caster_pos = (caster_unit.grid_y, caster_unit.grid_x) if caster_unit else (0, 0)
        self.target_pos = target_pos if target_pos else self.caster_pos

        # Calculate bounce count dynamically based on enemy HP (matches Matador skill logic)
        if self.game and bounce_count == 2:  # If default value, calculate dynamically
            self.bounce_count = self._calculate_dynamic_bounce_count()
        else:
            self.bounce_count = bounce_count

        self.trajectory = self._calculate_multi_bounce_trajectory()

        # Convert positions to world coordinates
        caster_world_x = self.caster_pos[1] * TILE_SIZE + TILE_SIZE // 2
        caster_world_y = self.caster_pos[0] * TILE_SIZE + TILE_SIZE // 2

        # Animation phases
        self.phase = 'windup'  # windup -> launch -> flight -> complete
        self.timer = 0
        self.windup_duration = 0.6
        self.launch_duration = 0.15
        self.flight_speed = 800  # pixels per second

        # Pelota projectile
        self.pelota = MatadorPelota(caster_world_x, caster_world_y, camera)

        # Flight tracking
        self.trajectory_index = 0
        self.current_segment_start = (caster_world_x, caster_world_y)
        self.current_segment_end = None
        self.segment_progress = 0

        # Calculate first segment
        if self.trajectory and len(self.trajectory) > 0:
            first_target = self.trajectory[0]
            self.current_segment_end = (
                first_target[1] * TILE_SIZE + TILE_SIZE // 2,
                first_target[0] * TILE_SIZE + TILE_SIZE // 2
            )
        else:
            # Empty trajectory - complete immediately after launch
            self.trajectory = []  # Ensure empty
            self.current_segment_end = (caster_world_x, caster_world_y)

        # Colors (define BEFORE creating particles)
        self.color_royal_blue = (42, 90, 154)
        self.color_med_blue = (74, 122, 186)
        self.color_cream = (240, 232, 208)
        self.color_gold = (192, 176, 144)

        # Wind-up effect particles
        self.windup_particles = []
        self.create_windup_particles(caster_world_x, caster_world_y)

        # Impact effects
        self.impact_effects = []  # List of (world_x, world_y, timer, type)

    def _calculate_dynamic_bounce_count(self):
        """
        Calculate bounce count based on enemy team HP loss.
        Replicates Matador skill logic: boneglaive/dlc/pelotari/skills.py Matador._calculate_matador_bounces()

        Returns:
            int: Bounce count (2-8)
        """
        if not self.game or not self.caster_unit or not hasattr(self.caster_unit, 'player'):
            return 2  # Base bounces

        base_bounces = 2
        max_bounces = 8
        hp_percent_per_bounce = 15  # 15% HP lost = +1 bounce

        # Get caster's player number
        caster_player = self.caster_unit.player

        # Get all enemy units (excluding summons and echoes)
        all_enemy_units = [
            u for u in self.game.units
            if u.player != caster_player
            and not getattr(u, 'is_summon', False)
            and not getattr(u, 'is_echo', False)
        ]

        if not all_enemy_units:
            return base_bounces

        # Calculate total max HP and current HP
        total_max_hp = sum(u.max_hp for u in all_enemy_units)
        alive_enemies = [u for u in all_enemy_units if u.is_alive()]
        total_current_hp = sum(u.hp for u in alive_enemies)

        # Calculate HP loss percentage
        hp_lost_percent = ((total_max_hp - total_current_hp) / total_max_hp) * 100 if total_max_hp > 0 else 0

        # Calculate bonus bounces
        bonus_bounces = int(hp_lost_percent // hp_percent_per_bounce)
        total_bounces = min(base_bounces + bonus_bounces, max_bounces)

        return total_bounces

    def _calculate_multi_bounce_trajectory(self):
        """
        Calculate complete multi-bounce trajectory matching Matador skill ricochet physics.
        Uses same logic as boneglaive/dlc/pelotari/skills.py Matador skill.

        Returns:
            List of (y, x) grid positions including all bounces
        """
        # Fallback to simple trajectory if no game instance
        if not self.game:
            return self._calculate_simple_trajectory()

        trajectory = []
        bounces_used = 0

        # Starting position and direction
        current_pos = self.caster_pos
        direction = self._normalize_direction((
            self.target_pos[0] - self.caster_pos[0],
            self.target_pos[1] - self.caster_pos[1]
        ))

        # Calculate segments with bounces
        for bounce_iteration in range(self.bounce_count + 1):  # Initial + bounces
            # Trace segment until collision
            segment_positions, collision_pos, collision_type = self._trace_segment(
                current_pos, direction, max_range=50
            )

            # Add segment positions to trajectory
            trajectory.extend(segment_positions)

            # Check if we hit something
            if not collision_pos:
                # Reached map edge or no collision - stop
                break

            # Check if we've used all bounces
            if bounces_used >= self.bounce_count:
                break

            # Calculate ricochet direction for next segment
            new_direction = self._calculate_ricochet_direction(
                collision_pos, direction, collision_type
            )

            if not new_direction:
                # Can't ricochet - stop
                break

            # Set up for next segment
            current_pos = collision_pos
            direction = new_direction
            bounces_used += 1

        return trajectory if trajectory else [(self.caster_pos[0], self.caster_pos[1])]

    def _calculate_simple_trajectory(self):
        """Fallback simple straight-line trajectory (used if no game instance)."""
        trajectory = []
        start_y, start_x = self.caster_pos
        end_y, end_x = self.target_pos

        # Calculate direction
        dy = end_y - start_y
        dx = end_x - start_x
        distance = max(abs(dy), abs(dx))

        if distance == 0:
            return [(start_y, start_x)]

        # Generate points along the line
        for i in range(1, distance + 1):
            progress = i / distance
            y = int(start_y + dy * progress)
            x = int(start_x + dx * progress)
            trajectory.append((y, x))

        return trajectory

    def _normalize_direction(self, direction):
        """
        Normalize direction to unit vector (quantized to 8 chess directions).

        Args:
            direction: Direction tuple (dy, dx)

        Returns:
            Normalized direction tuple
        """
        dy, dx = direction

        if dy == 0 and dx == 0:
            return (0, 1)  # Default direction

        # Quantize to -1, 0, 1
        norm_dy = 0 if dy == 0 else (1 if dy > 0 else -1)
        norm_dx = 0 if dx == 0 else (1 if dx > 0 else -1)

        return (norm_dy, norm_dx)

    def _trace_segment(self, start_pos, direction, max_range=50):
        """
        Trace segment from start_pos in direction until collision or max_range.

        Args:
            start_pos: Starting (y, x) position
            direction: Direction tuple (dy, dx)
            max_range: Maximum tiles to trace

        Returns:
            Tuple of (positions_list, collision_pos, collision_type)
            collision_type: 'wall', 'edge', or None
        """
        positions = []
        current_y, current_x = start_pos
        dy, dx = direction

        for step in range(max_range):
            # Calculate next position
            next_y = current_y + dy
            next_x = current_x + dx

            # Check if out of bounds (map edge)
            if not self.game.is_valid_position(next_y, next_x):
                # Hit map edge
                return (positions, (current_y, current_x), 'edge')

            # Check if impassable (wall)
            if not self.game.map.is_passable(next_y, next_x):
                # Hit wall - return last valid position as collision point
                return (positions, (next_y, next_x), 'wall')

            # Position is valid, add to trajectory
            positions.append((next_y, next_x))
            current_y, current_x = next_y, next_x

        # Reached max range without collision
        return (positions, None, None)

    def _calculate_ricochet_direction(self, collision_pos, incoming_dir, collision_type):
        """
        Calculate ricochet direction at collision point.
        Uses same logic as Matador skill: boneglaive/dlc/pelotari/skills.py

        Args:
            collision_pos: Position where collision occurred (y, x)
            incoming_dir: Incoming direction (dy, dx)
            collision_type: 'wall', 'edge', or None

        Returns:
            New direction tuple (dy, dx) or None if can't ricochet
        """
        dy, dx = incoming_dir

        if collision_type == 'wall':
            # Wall bounce - check which edges face open space
            at_left_edge = collision_pos[1] == 0 or \
                          (collision_pos[1] > 0 and self.game.map.is_passable(collision_pos[0], collision_pos[1] - 1))
            at_right_edge = collision_pos[1] == self.game.map.width - 1 or \
                           (collision_pos[1] < self.game.map.width - 1 and self.game.map.is_passable(collision_pos[0], collision_pos[1] + 1))
            at_top_edge = collision_pos[0] == 0 or \
                         (collision_pos[0] > 0 and self.game.map.is_passable(collision_pos[0] - 1, collision_pos[1]))
            at_bottom_edge = collision_pos[0] == self.game.map.height - 1 or \
                            (collision_pos[0] < self.game.map.height - 1 and self.game.map.is_passable(collision_pos[0] + 1, collision_pos[1]))

            # Flip direction based on exposed edges
            new_dx = -dx if (at_left_edge or at_right_edge) else dx
            new_dy = -dy if (at_top_edge or at_bottom_edge) else dy

            return (new_dy, new_dx)

        elif collision_type == 'edge':
            # Map edge bounce
            new_dx = -dx if collision_pos[1] in [0, self.game.map.width - 1] else dx
            new_dy = -dy if collision_pos[0] in [0, self.game.map.height - 1] else dy

            return (new_dy, new_dx)

        # Unknown collision type or can't bounce
        return None

    def create_windup_particles(self, world_x, world_y):
        """Create orbiting charge-up particles around caster."""
        for i in range(20):
            angle = (i / 20) * math.pi * 2
            radius = 30
            self.windup_particles.append({
                'angle': angle,
                'radius': radius,
                'speed': 180,  # degrees per second
                'world_x': world_x,
                'world_y': world_y,
                'size': random.uniform(3, 6),
                'color': self.color_royal_blue if random.random() > 0.5 else self.color_med_blue
            })

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == 'windup':
            # Update orbiting particles
            for p in self.windup_particles:
                p['angle'] += math.radians(p['speed']) * delta_time
                p['radius'] += 20 * delta_time  # Spiral outward

            # Transition to launch
            if self.timer >= self.windup_duration:
                self.phase = 'launch'
                self.timer = 0

                # Create launch explosion
                screen_x = self.pelota.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = self.pelota.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if screen_pos:
                    self.particle_emitter.emit_burst(
                        screen_pos[0], screen_pos[1],
                        self.color_royal_blue, count=40
                    )

        elif self.phase == 'launch':
            # Brief launch flash
            if self.timer >= self.launch_duration:
                self.phase = 'flight'
                self.timer = 0

        elif self.phase == 'flight':
            # Update pelota
            self.pelota.update(delta_time)

            # Safety: If no valid trajectory, complete immediately
            if not self.trajectory or len(self.trajectory) == 0:
                self.phase = 'complete'
                self.create_final_explosion(
                    self.pelota.world_x,
                    self.pelota.world_y
                )
                return True

            # Move along trajectory
            if self.current_segment_end:
                # Calculate distance and direction
                dx = self.current_segment_end[0] - self.current_segment_start[0]
                dy = self.current_segment_end[1] - self.current_segment_start[1]
                distance = math.sqrt(dx**2 + dy**2)

                if distance > 0:
                    # Move forward
                    move_amount = self.flight_speed * delta_time
                    self.segment_progress += move_amount

                    if self.segment_progress >= distance:
                        # Reached segment end
                        self.pelota.move_to(
                            self.current_segment_end[0],
                            self.current_segment_end[1]
                        )

                        # Create impact effect at this position
                        self.create_impact_effect(
                            self.current_segment_end[0],
                            self.current_segment_end[1]
                        )

                        # Move to next segment
                        self.trajectory_index += 1
                        if self.trajectory_index < len(self.trajectory):
                            self.current_segment_start = self.current_segment_end
                            next_target = self.trajectory[self.trajectory_index]
                            self.current_segment_end = (
                                next_target[1] * TILE_SIZE + TILE_SIZE // 2,
                                next_target[0] * TILE_SIZE + TILE_SIZE // 2
                            )
                            self.segment_progress = 0
                        else:
                            # Trajectory complete
                            self.phase = 'complete'
                            self.create_final_explosion(
                                self.current_segment_end[0],
                                self.current_segment_end[1]
                            )
                    else:
                        # Interpolate position
                        progress_ratio = self.segment_progress / distance
                        new_x = self.current_segment_start[0] + dx * progress_ratio
                        new_y = self.current_segment_start[1] + dy * progress_ratio
                        self.pelota.move_to(new_x, new_y)
                else:
                    # Distance is 0 - we're already at target, skip to next segment immediately
                    self.trajectory_index += 1
                    if self.trajectory_index < len(self.trajectory):
                        self.current_segment_start = self.current_segment_end
                        next_target = self.trajectory[self.trajectory_index]
                        self.current_segment_end = (
                            next_target[1] * TILE_SIZE + TILE_SIZE // 2,
                            next_target[0] * TILE_SIZE + TILE_SIZE // 2
                        )
                        self.segment_progress = 0
                    else:
                        # Trajectory complete
                        self.phase = 'complete'
                        self.create_final_explosion(
                            self.current_segment_end[0],
                            self.current_segment_end[1]
                        )

            # Update impact effects
            self.impact_effects = [
                (x, y, t - delta_time, etype)
                for x, y, t, etype in self.impact_effects
                if t > delta_time
            ]

        elif self.phase == 'complete':
            # Update lingering impact effects
            self.impact_effects = [
                (x, y, t - delta_time, etype)
                for x, y, t, etype in self.impact_effects
                if t > delta_time
            ]

            # Animation done when all effects fade
            if self.timer > 0.5 and len(self.impact_effects) == 0:
                return False

        return True

    def create_impact_effect(self, world_x, world_y):
        """Create impact/ricochet effect at position."""
        self.impact_effects.append((world_x, world_y, 0.3, 'ricochet'))

        # Emit particles
        screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if screen_pos:
            self.particle_emitter.emit_burst(
                screen_pos[0], screen_pos[1],
                self.color_royal_blue, count=25
            )

    def create_final_explosion(self, world_x, world_y):
        """Create massive final impact explosion."""
        self.impact_effects.append((world_x, world_y, 0.5, 'final'))

        # Emit massive particle burst
        screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if screen_pos:
            # Multiple colors
            for color in [self.color_cream, self.color_royal_blue, self.color_gold]:
                self.particle_emitter.emit_burst(
                    screen_pos[0], screen_pos[1],
                    color, count=40
                )

    def draw(self, surface):
        """Draw all animation elements."""
        if self.phase == 'windup':
            # Draw orbiting charge particles
            for p in self.windup_particles:
                world_x = p['world_x'] + math.cos(p['angle']) * p['radius']
                world_y = p['world_y'] + math.sin(p['angle']) * p['radius']
                screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if screen_pos:
                    size = int(p['size'])
                    pygame.draw.circle(surface, p['color'],
                                     (int(screen_pos[0]), int(screen_pos[1])), size)

            # Pulsing glow at caster
            screen_x = self.pelota.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.pelota.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            screen_pos = (screen_x, screen_y)
            if screen_pos:
                pulse = 0.5 + 0.5 * math.sin(self.timer * 10)
                glow_size = int(40 * pulse)
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_med_blue, int(100 * pulse)),
                                 (glow_size, glow_size), glow_size)
                surface.blit(glow_surf, (int(screen_pos[0] - glow_size),
                                        int(screen_pos[1] - glow_size)))

        elif self.phase == 'launch':
            # Bright flash
            screen_x = self.pelota.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.pelota.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            screen_pos = (screen_x, screen_y)
            if screen_pos:
                flash_size = 60
                flash_alpha = int(255 * (1.0 - self.timer / self.launch_duration))
                flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                 (flash_size, flash_size), flash_size)
                surface.blit(flash_surf, (int(screen_pos[0] - flash_size),
                                         int(screen_pos[1] - flash_size)))

        elif self.phase == 'flight' or self.phase == 'complete':
            # Draw the MASSIVE pelota
            if self.phase == 'flight':
                self.pelota.draw(surface)

            # Draw impact effects
            for world_x, world_y, timer, etype in self.impact_effects:
                screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if not screen_pos:
                    continue

                if etype == 'ricochet':
                    # Expanding blue shockwave ring
                    max_radius = 40
                    progress = 1.0 - (timer / 0.3)
                    radius = int(max_radius * progress)
                    alpha = int(150 * (timer / 0.3))

                    ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (*self.color_royal_blue, alpha),
                                     (radius, radius), radius, 3)
                    surface.blit(ring_surf, (int(screen_pos[0] - radius),
                                            int(screen_pos[1] - radius)))

                elif etype == 'final':
                    # Massive expanding ring + flash
                    max_radius = 80
                    progress = 1.0 - (timer / 0.5)
                    radius = int(max_radius * progress)
                    alpha = int(200 * (timer / 0.5))

                    # Multiple rings
                    for offset in [0, 10, 20]:
                        r = radius - offset
                        if r > 0:
                            ring_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                            pygame.draw.circle(ring_surf, (*self.color_cream, alpha // 2),
                                             (r, r), r, 4)
                            surface.blit(ring_surf, (int(screen_pos[0] - r),
                                                    int(screen_pos[1] - r)))

                    # White flash
                    flash_alpha = int(255 * (timer / 0.5))
                    flash_size = int(60 * (1.0 - progress))
                    if flash_size > 0:
                        flash_surf = pygame.Surface((flash_size * 2, flash_size * 2),
                                                   pygame.SRCALPHA)
                        pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                         (flash_size, flash_size), flash_size)
                        surface.blit(flash_surf, (int(screen_pos[0] - flash_size),
                                                 int(screen_pos[1] - flash_size)))
