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


class RipostePelota:
    """
    Small defensive pelota for Riposte counterattack.
    1/4 size of Matador (12px diameter) - cream and royal blue.
    Rapid defensive burst with simplified visual detail.
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the small defensive pelota.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - 1/4 size of Matador
        self.size = TILE_SIZE // 4  # ~12px diameter
        self.glow_size = int(self.size * 1.2)  # ~14px glow
        self.rotation = 0  # Rotation angle for spinning effect
        self.rotation_speed = 180  # degrees per second (half of Matador)

        # Colors from Matador (same palette)
        self.color_cream = (240, 232, 208)  # #f0e8d0
        self.color_white = (255, 255, 255)  # #ffffff
        self.color_royal_blue = (42, 90, 154)  # #2a5a9a
        self.color_med_blue = (74, 122, 186)  # #4a7aba
        self.color_gold = (192, 176, 144)  # #c0b090

        # Motion trail (shorter for smaller pelota)
        self.trail_positions = []
        self.max_trail_length = 4

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
            (x, y, alpha * 0.85) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        return True

    def draw(self, surface):
        """Draw the small defensive pelota with simplified layers."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.5 + 0.5 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 80)

            # Cream trail
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_cream, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Layer 1: Golden glow (outer) - simplified
        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(5):  # Only 5 rings vs 10 for Matador
            radius = self.glow_size - radius_offset * 2
            alpha = int(40 * (1.0 - radius_offset / 5))
            pygame.draw.circle(glow_surf, (*self.color_gold, alpha),
                             (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 2: Main cream ball
        pygame.draw.circle(surface, self.color_cream, (int(cx), int(cy)), self.size // 2)

        # Layer 3: Royal blue rim/stroke
        pygame.draw.circle(surface, self.color_royal_blue, (int(cx), int(cy)),
                         self.size // 2, 1)  # Thinner stroke for small size

        # Layer 4: Bright white core
        core_size = int(self.size * 0.65) // 2
        if core_size > 0:
            pygame.draw.circle(surface, self.color_white, (int(cx), int(cy)), core_size)

        # Layer 5: Single curved seam line (simplified - just one line)
        seam_radius = self.size // 2 - 2
        if seam_radius > 0:
            angle_rad = math.radians(self.rotation)
            seam_points = []
            for i in range(-2, 3):  # Shorter seam
                t = i / 2.0
                angle = angle_rad + t * 0.6
                offset_x = math.sin(angle) * seam_radius * 0.3
                x = cx + offset_x
                y = cy + t * seam_radius
                seam_points.append((int(x), int(y)))

            if len(seam_points) >= 2:
                pygame.draw.lines(surface, self.color_gold, False, seam_points, 1)

        # Layer 6: Highlight glare (top-left)
        glare_offset_x = int(cx - self.size * 0.25)
        glare_offset_y = int(cy - self.size * 0.25)
        glare_size = max(1, self.size // 5)
        pygame.draw.circle(surface, (255, 255, 255, 160),
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


class RiposteAnimation:
    """
    Defensive counterattack animation for PELOTARI's Riposte passive.
    Fires 8 small pelotas simultaneously in all chess directions when hit.
    """

    def __init__(self, caster_unit, trajectories, camera, particle_emitter, game=None):
        """
        Initialize Riposte counter-strike animation.

        Args:
            caster_unit: AnimatedUnit (PELOTARI) that triggered counterattack
            trajectories: List of 8 trajectory lists (one per direction)
            camera: Camera instance
            particle_emitter: ParticleEmitter for effects
            game: Game instance (for debug info)
        """
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.game = game
        self.caster_unit = caster_unit

        # Validate trajectories
        if not trajectories or len(trajectories) != 8:
            # Fallback to empty trajectories
            self.trajectories = [[] for _ in range(8)]
        else:
            self.trajectories = trajectories

        # Get caster world position
        caster_world_x = caster_unit.grid_x * TILE_SIZE + TILE_SIZE // 2
        caster_world_y = caster_unit.grid_y * TILE_SIZE + TILE_SIZE // 2

        # Animation phases
        self.phase = 'flash'  # flash -> flight -> complete
        self.timer = 0
        self.flash_duration = 0.1  # Brief defensive flash
        self.flight_speed = 600  # pixels per second (slower than Matador's 800)

        # Create 8 pelota projectiles (one per direction)
        self.pelotas = []
        for i in range(8):
            pelota = RipostePelota(caster_world_x, caster_world_y, camera)
            self.pelotas.append(pelota)

        # Flight tracking for each pelota
        self.trajectory_indices = [0] * 8  # Current position in each trajectory
        self.segment_starts = [(caster_world_x, caster_world_y)] * 8
        self.segment_ends = [None] * 8
        self.segment_progress = [0.0] * 8
        self.pelota_active = [True] * 8  # Track which pelotas are still flying

        # Calculate first segment end for each pelota
        for i in range(8):
            if self.trajectories[i] and len(self.trajectories[i]) > 0:
                first_target = self.trajectories[i][0]
                self.segment_ends[i] = (
                    first_target[1] * TILE_SIZE + TILE_SIZE // 2,
                    first_target[0] * TILE_SIZE + TILE_SIZE // 2
                )
            else:
                # Empty trajectory - pelota stays at origin
                self.segment_ends[i] = (caster_world_x, caster_world_y)
                self.pelota_active[i] = False

        # Colors
        self.color_royal_blue = (42, 90, 154)
        self.color_med_blue = (74, 122, 186)
        self.color_cream = (240, 232, 208)
        self.color_gold = (192, 176, 144)

        # Impact effects
        self.impact_effects = []  # List of (world_x, world_y, timer, type)

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == 'flash':
            # Brief defensive flash
            if self.timer >= self.flash_duration:
                self.phase = 'flight'
                self.timer = 0

                # Create launch burst
                screen_x = self.caster_unit.grid_x * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = self.caster_unit.grid_y * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if screen_pos:
                    self.particle_emitter.emit_burst(
                        screen_pos[0], screen_pos[1],
                        self.color_royal_blue, count=20
                    )

        elif self.phase == 'flight':
            # Update all active pelotas
            for i in range(8):
                if not self.pelota_active[i]:
                    continue

                # Update pelota animation
                self.pelotas[i].update(delta_time)

                # Safety: If no valid trajectory, deactivate
                if not self.trajectories[i] or len(self.trajectories[i]) == 0:
                    self.pelota_active[i] = False
                    continue

                # Move along trajectory
                if self.segment_ends[i]:
                    # Calculate distance and direction
                    dx = self.segment_ends[i][0] - self.segment_starts[i][0]
                    dy = self.segment_ends[i][1] - self.segment_starts[i][1]
                    distance = math.sqrt(dx**2 + dy**2)

                    if distance > 0:
                        # Move forward
                        move_amount = self.flight_speed * delta_time
                        self.segment_progress[i] += move_amount

                        if self.segment_progress[i] >= distance:
                            # Reached segment end
                            self.pelotas[i].move_to(
                                self.segment_ends[i][0],
                                self.segment_ends[i][1]
                            )

                            # Create small impact effect
                            self.create_impact_effect(
                                self.segment_ends[i][0],
                                self.segment_ends[i][1],
                                'ricochet'
                            )

                            # Move to next segment
                            self.trajectory_indices[i] += 1
                            if self.trajectory_indices[i] < len(self.trajectories[i]):
                                self.segment_starts[i] = self.segment_ends[i]
                                next_target = self.trajectories[i][self.trajectory_indices[i]]
                                self.segment_ends[i] = (
                                    next_target[1] * TILE_SIZE + TILE_SIZE // 2,
                                    next_target[0] * TILE_SIZE + TILE_SIZE // 2
                                )
                                self.segment_progress[i] = 0
                            else:
                                # Trajectory complete for this pelota
                                self.pelota_active[i] = False
                                self.create_impact_effect(
                                    self.segment_ends[i][0],
                                    self.segment_ends[i][1],
                                    'final'
                                )
                        else:
                            # Interpolate position
                            progress_ratio = self.segment_progress[i] / distance
                            new_x = self.segment_starts[i][0] + dx * progress_ratio
                            new_y = self.segment_starts[i][1] + dy * progress_ratio
                            self.pelotas[i].move_to(new_x, new_y)
                    else:
                        # Distance is 0 - skip to next segment immediately
                        self.trajectory_indices[i] += 1
                        if self.trajectory_indices[i] < len(self.trajectories[i]):
                            self.segment_starts[i] = self.segment_ends[i]
                            next_target = self.trajectories[i][self.trajectory_indices[i]]
                            self.segment_ends[i] = (
                                next_target[1] * TILE_SIZE + TILE_SIZE // 2,
                                next_target[0] * TILE_SIZE + TILE_SIZE // 2
                            )
                            self.segment_progress[i] = 0
                        else:
                            # Trajectory complete
                            self.pelota_active[i] = False

            # Update impact effects
            self.impact_effects = [
                (x, y, t - delta_time, etype)
                for x, y, t, etype in self.impact_effects
                if t > delta_time
            ]

            # Check if all pelotas are done
            if not any(self.pelota_active):
                self.phase = 'complete'

        elif self.phase == 'complete':
            # Update lingering impact effects
            self.impact_effects = [
                (x, y, t - delta_time, etype)
                for x, y, t, etype in self.impact_effects
                if t > delta_time
            ]

            # Animation done when all effects fade
            if self.timer > 0.3 and len(self.impact_effects) == 0:
                return False

        return True

    def create_impact_effect(self, world_x, world_y, effect_type):
        """Create impact/ricochet effect at position."""
        duration = 0.2 if effect_type == 'ricochet' else 0.3
        self.impact_effects.append((world_x, world_y, duration, effect_type))

        # Emit small particle burst
        screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if screen_pos:
            particle_count = 10 if effect_type == 'final' else 8
            self.particle_emitter.emit_burst(
                screen_pos[0], screen_pos[1],
                self.color_royal_blue, count=particle_count
            )

    def draw(self, surface):
        """Draw all animation elements."""
        if self.phase == 'flash':
            # Defensive flash at caster
            screen_x = self.caster_unit.grid_x * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.caster_unit.grid_y * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_y + self.camera.shake_offset_y
            screen_pos = (screen_x, screen_y)
            if screen_pos:
                pulse = 1.0 - (self.timer / self.flash_duration)
                flash_size = int(30 * pulse)
                flash_alpha = int(150 * pulse)
                flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_royal_blue, flash_alpha),
                                 (flash_size, flash_size), flash_size)
                surface.blit(flash_surf, (int(screen_pos[0] - flash_size),
                                        int(screen_pos[1] - flash_size)))

        elif self.phase == 'flight' or self.phase == 'complete':
            # Draw all active pelotas
            if self.phase == 'flight':
                for i in range(8):
                    if self.pelota_active[i]:
                        self.pelotas[i].draw(surface)

            # Draw impact effects
            for world_x, world_y, timer, etype in self.impact_effects:
                screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if not screen_pos:
                    continue

                if etype == 'ricochet':
                    # Small expanding blue ring
                    max_radius = 20
                    duration = 0.2
                    progress = 1.0 - (timer / duration)
                    radius = int(max_radius * progress)
                    alpha = int(120 * (timer / duration))

                    ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (*self.color_royal_blue, alpha),
                                     (radius, radius), radius, 2)
                    surface.blit(ring_surf, (int(screen_pos[0] - radius),
                                            int(screen_pos[1] - radius)))

                elif etype == 'final':
                    # Slightly larger impact ring
                    max_radius = 25
                    duration = 0.3
                    progress = 1.0 - (timer / duration)
                    radius = int(max_radius * progress)
                    alpha = int(150 * (timer / duration))

                    # Single ring
                    ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (*self.color_cream, alpha),
                                     (radius, radius), radius, 2)
                    surface.blit(ring_surf, (int(screen_pos[0] - radius),
                                            int(screen_pos[1] - radius)))


# ============================================================================
# POACH ANIMATION
# ============================================================================

class PoachPelota:
    """
    Medium-sized pelota for Poach skill.
    Half size of Matador (23px diameter) - cream and royal blue.
    Has two visual modes: normal (initial) and charged (ricochet).
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the medium poach pelota.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - half size of Matador
        self.size = TILE_SIZE // 2  # ~23px diameter
        self.glow_size = int(self.size * 1.2)  # ~28px glow
        self.rotation = 0  # Rotation angle for spinning effect
        self.rotation_speed = 300  # degrees per second

        # Visual mode: 'normal' (initial shot) or 'charged' (ricochet)
        self.mode = 'normal'

        # Colors from Matador (same palette)
        self.color_cream = (240, 232, 208)  # #f0e8d0
        self.color_white = (255, 255, 255)  # #ffffff
        self.color_royal_blue = (42, 90, 154)  # #2a5a9a
        self.color_gold = (192, 176, 144)  # #c0b090
        self.color_purple = (150, 50, 255)  # Purple for charged mode

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 6

    def set_charged(self):
        """Switch to charged mode (ricochet visual)."""
        self.mode = 'charged'

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
            (x, y, alpha * 0.88) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        return True

    def draw(self, surface):
        """Draw the medium pelota with mode-dependent visuals."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail
        trail_color = self.color_cream if self.mode == 'normal' else self.color_purple
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.5 + 0.5 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 90)

            # Trail with mode-dependent color
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*trail_color, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Choose glow color based on mode
        glow_color = self.color_gold if self.mode == 'normal' else self.color_purple

        # Layer 1: Glow (golden for normal, purple for charged)
        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(7):  # 7 glow rings
            radius = self.glow_size - radius_offset * 2
            alpha = int(50 * (1.0 - radius_offset / 7))
            pygame.draw.circle(glow_surf, (*glow_color, alpha),
                             (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 2: Main cream ball
        pygame.draw.circle(surface, self.color_cream, (int(cx), int(cy)), self.size // 2)

        # Layer 3: Royal blue rim/stroke
        pygame.draw.circle(surface, self.color_royal_blue, (int(cx), int(cy)),
                         self.size // 2, 2)

        # Layer 4: Bright white core
        core_size = int(self.size * 0.6) // 2
        if core_size > 0:
            pygame.draw.circle(surface, self.color_white, (int(cx), int(cy)), core_size)

        # Layer 5: Curved seam line (simplified)
        seam_radius = self.size // 2 - 3
        if seam_radius > 0:
            angle_rad = math.radians(self.rotation)
            seam_points = []
            for i in range(-3, 4):  # 7 points
                t = i / 3.0
                angle = angle_rad + t * 0.7
                offset_x = math.sin(angle) * seam_radius * 0.35
                x = cx + offset_x
                y = cy + t * seam_radius
                seam_points.append((int(x), int(y)))

            if len(seam_points) >= 2:
                pygame.draw.lines(surface, self.color_gold, False, seam_points, 2)

        # Layer 6: Highlight glare (top-left)
        glare_offset_x = int(cx - self.size * 0.22)
        glare_offset_y = int(cy - self.size * 0.22)
        glare_size = max(2, self.size // 5)
        pygame.draw.circle(surface, (255, 255, 255, 170),
                         (glare_offset_x, glare_offset_y), glare_size)

        # Layer 7: Charged mode sparkles
        if self.mode == 'charged':
            # Add orbiting sparkles to show it's powered up
            import time
            sparkle_time = time.time() * 2  # Fast rotation
            for i in range(5):  # 5 sparkles
                angle = (i / 5) * 2 * math.pi + sparkle_time
                sparkle_dist = self.size * 0.7
                sx = int(cx + math.cos(angle) * sparkle_dist)
                sy = int(cy + math.sin(angle) * sparkle_dist)
                # Small purple sparkles
                sparkle_alpha = int(120 + 60 * math.sin(sparkle_time + i))
                sparkle_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surf, (*self.color_purple, sparkle_alpha), (3, 3), 2)
                surface.blit(sparkle_surf, (sx - 3, sy - 3))


class BuffExtractionEffect:
    """
    Visual effect showing a buff being stolen from enemy unit.
    Purple expanding ring + rising sparkles + unit flash.
    """

    def __init__(self, world_x, world_y, camera):
        """
        Initialize buff extraction effect.

        Args:
            world_x, world_y: World coordinates where buff is stolen
            camera: Camera instance
        """
        self.world_x = world_x
        self.world_y = world_y
        self.camera = camera
        self.timer = 0
        self.duration = 0.5  # 0.5 second effect
        self.active = True

        # Colors
        self.color_purple = (150, 50, 255)
        self.color_white = (255, 255, 255)

        # Rising sparkles
        self.sparkles = []
        for i in range(12):  # 12 sparkles
            angle = (i / 12) * 2 * math.pi
            speed = 50 + random.random() * 30  # Variable speed upward
            self.sparkles.append({
                'angle': angle,
                'speed': speed,
                'offset_x': math.cos(angle) * 15,  # Start position
                'offset_y': -i * 2  # Stagger vertically
            })

    def update(self, delta_time):
        """Update extraction effect."""
        self.timer += delta_time

        # Update sparkles (rise upward)
        for sparkle in self.sparkles:
            sparkle['offset_y'] -= sparkle['speed'] * delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw extraction effect."""
        if not self.active:
            return

        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos
        progress = self.timer / self.duration

        # Expanding purple ring
        max_radius = 35
        radius = int(max_radius * progress)
        ring_alpha = int(180 * (1.0 - progress))  # Fade out
        if radius > 0 and ring_alpha > 0:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*self.color_purple, ring_alpha),
                             (radius, radius), radius, 3)
            surface.blit(ring_surf, (int(cx - radius), int(cy - radius)))

        # Rising sparkles
        for sparkle in self.sparkles:
            sparkle_x = cx + sparkle['offset_x']
            sparkle_y = cy + sparkle['offset_y']
            # Fade sparkles as they rise
            sparkle_alpha = int(200 * max(0, 1.0 - abs(sparkle['offset_y']) / 80))
            if sparkle_alpha > 0:
                sparkle_size = 3
                sparkle_surf = pygame.Surface((sparkle_size * 2, sparkle_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surf, (*self.color_purple, sparkle_alpha),
                                 (sparkle_size, sparkle_size), sparkle_size)
                surface.blit(sparkle_surf, (int(sparkle_x - sparkle_size), int(sparkle_y - sparkle_size)))

        # Pulsing glow at center (brief flash)
        if progress < 0.3:  # Only during first 30%
            flash_intensity = (0.3 - progress) / 0.3
            flash_radius = int(20 * flash_intensity)
            flash_alpha = int(150 * flash_intensity)
            if flash_radius > 0:
                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_white, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(cx - flash_radius), int(cy - flash_radius)))


class BuffBall:
    """
    Small cyan glowing ball representing a stolen buff.
    Travels away from PELOTARI, allies can intercept it.
    Smaller than Riposte pelota (15px diameter).
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize buff ball.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - small
        self.size = 15  # 15px diameter
        self.rotation = 0
        self.rotation_speed = 200  # degrees per second

        # Colors
        self.color_cyan = (0, 255, 255)
        self.color_white = (255, 255, 255)
        self.color_blue = (0, 200, 255)

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 5

        # Orbiting sparkles
        self.sparkle_count = 6

    def move_to(self, world_x, world_y):
        """Move buff ball to new world position."""
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
        """Update buff ball animation."""
        # Rotate for orbiting sparkles
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.85) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        return True

    def draw(self, surface):
        """Draw buff ball with orbiting sparkles."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.4 + 0.6 * (i / len(self.trail_positions)))) // 2
            trail_alpha = int(alpha * 100)

            # Cyan trail
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_cyan, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Pulsing cyan glow
        import time
        pulse = 0.8 + 0.2 * math.sin(time.time() * 4)  # Fast pulse
        glow_size = int(self.size * 1.3 * pulse)
        glow_alpha = int(80 * pulse)

        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        for i in range(5):  # 5 glow layers
            radius = glow_size - i * 2
            alpha = int(glow_alpha * (1.0 - i / 5))
            if radius > 0:
                pygame.draw.circle(glow_surf, (*self.color_cyan, alpha),
                                 (glow_size, glow_size), radius)
        surface.blit(glow_surf, (int(cx - glow_size), int(cy - glow_size)))

        # Main cyan ball
        pygame.draw.circle(surface, self.color_cyan, (int(cx), int(cy)), self.size // 2)

        # White core
        core_size = self.size // 3
        if core_size > 0:
            pygame.draw.circle(surface, self.color_white, (int(cx), int(cy)), core_size)

        # Orbiting sparkles
        angle_rad = math.radians(self.rotation)
        for i in range(self.sparkle_count):
            angle = angle_rad + (i / self.sparkle_count) * 2 * math.pi
            orbit_radius = self.size * 0.9
            sx = int(cx + math.cos(angle) * orbit_radius)
            sy = int(cy + math.sin(angle) * orbit_radius)

            # Small blue sparkles
            sparkle_size = 2
            sparkle_alpha = int(180 + 50 * math.sin(angle * 2))
            sparkle_surf = pygame.Surface((sparkle_size * 2, sparkle_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(sparkle_surf, (*self.color_blue, sparkle_alpha),
                             (sparkle_size, sparkle_size), sparkle_size)
            surface.blit(sparkle_surf, (sx - sparkle_size, sy - sparkle_size))


class PoachAnimation:
    """
    Animation for PELOTARI's Poach skill.

    Phases:
    1. Launch - Windup particles
    2. Initial flight - Pelota travels to target (4 damage, no buff steal)
    3. Ricochet - Pelota bounces, switches to charged mode (6 damage, CAN steal)
    4. Buff extraction - If buff stolen from ricochet hit
    5. Buff ball flight - Stolen buff travels away for ally interception
    """

    def __init__(self, caster_unit, target_pos, camera, particle_emitter,
                 screen_shake_callback, screen_flash_callback, game, **kwargs):
        """
        Initialize Poach animation.

        Args:
            caster_unit: AnimatedUnit (PELOTARI)
            target_pos: (grid_y, grid_x) - initial target position
            camera: Camera instance
            particle_emitter: ParticleEmitter
            screen_shake_callback: Function to trigger screen shake
            screen_flash_callback: Function to trigger screen flash
            game: Game instance for trajectory calculation
        """
        self.caster = caster_unit
        self.target_pos = target_pos
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert target grid position to world coords
        grid_y, grid_x = target_pos
        self.target_world_x = grid_x * TILE_SIZE + TILE_SIZE // 2
        self.target_world_y = grid_y * TILE_SIZE + TILE_SIZE // 2

        # Get caster world position
        caster_world_x = caster_unit.grid_x * TILE_SIZE + TILE_SIZE // 2
        caster_world_y = caster_unit.grid_y * TILE_SIZE + TILE_SIZE // 2

        # Animation phases
        self.phase = 'launch'  # launch -> initial_flight -> ricochet_flight -> buff_extraction -> buff_ball -> complete
        self.timer = 0
        self.active = True

        # Pelota
        self.pelota = PoachPelota(caster_world_x, caster_world_y, camera)
        self.pelota_speed = 700  # px/s

        # Trajectories (calculated on demand)
        self.initial_trajectory = []
        self.current_trajectory_index = 0
        self.ricochet_trajectory = []
        self.ricochet_impact_pos = None  # World coords of ricochet start

        # Buff steal tracking
        self.buff_stolen = False
        self.buff_extraction_effect = None
        self.buff_ball = None
        self.buff_ball_trajectory = []
        self.buff_ball_trajectory_index = 0

        # Phase durations
        self.launch_duration = 0.3

        # Colors
        self.color_royal_blue = (42, 90, 154)
        self.color_purple = (150, 50, 255)

        # Start launch phase
        self._start_launch()

    def _start_launch(self):
        """Phase 1: Windup and launch."""
        self.phase = 'launch'
        self.timer = 0

        # Create windup particles at caster
        screen_x = self.caster.grid_x * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.caster.grid_y * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)

        if screen_pos:
            # Windup particle burst at caster position
            self.particle_emitter.emit_burst(
                screen_pos[0], screen_pos[1],
                self.color_royal_blue, count=20
            )

        # Light screen shake
        self.screen_shake_callback(3, 0.4)

    def _start_initial_flight(self):
        """Phase 2: Initial pelota flight to target."""
        self.phase = 'initial_flight'
        self.timer = 0

        # Calculate initial trajectory
        from boneglaive.dlc.pelotari.physics import calculate_linear_trajectory

        # Get caster grid position
        caster_grid_y = self.caster.grid_y
        caster_grid_x = self.caster.grid_x

        # Calculate direction to target
        target_grid_y, target_grid_x = self.target_pos
        dy = target_grid_y - caster_grid_y
        dx = target_grid_x - caster_grid_x

        # Normalize direction
        if dy != 0:
            dy = dy // abs(dy)
        if dx != 0:
            dx = dx // abs(dx)

        direction = (dy, dx)

        # Calculate straight-line trajectory
        self.initial_trajectory = calculate_linear_trajectory(
            start_pos=(caster_grid_y, caster_grid_x),
            direction=direction,
            ricochet_mode=False,  # No ricochet on initial
            max_range=20,
            game=self.game,
            max_bounces=0
        )

        self.current_trajectory_index = 0

        # Flash on launch
        screen_x = self.caster.grid_x * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.caster.grid_y * TILE_SIZE + TILE_SIZE // 2 + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)

        if screen_pos:
            self.particle_emitter.emit_burst(screen_pos[0], screen_pos[1], (255, 255, 150), count=20)

    def _start_ricochet_flight(self):
        """Phase 3: Ricochet flight (charged mode)."""
        self.phase = 'ricochet_flight'
        self.timer = 0

        # Switch pelota to charged mode
        self.pelota.set_charged()

        # Calculate ricochet trajectory from impact position
        # The ricochet should start from where the initial trajectory ended
        if len(self.initial_trajectory) > 0:
            last_pos = self.initial_trajectory[min(self.current_trajectory_index, len(self.initial_trajectory) - 1)]
            ricochet_start_y, ricochet_start_x = last_pos
        else:
            # No initial trajectory (point-blank shot at wall?)
            ricochet_start_y, ricochet_start_x = self.caster.grid_y, self.caster.grid_x

        # Store ricochet impact world coords
        self.ricochet_impact_pos = (
            ricochet_start_x * TILE_SIZE + TILE_SIZE // 2,
            ricochet_start_y * TILE_SIZE + TILE_SIZE // 2
        )

        # Calculate ricochet direction (simplified - bounce back toward caster general direction)
        from boneglaive.dlc.pelotari.physics import calculate_linear_trajectory

        # Calculate direction away from caster (simplified ricochet)
        dy = ricochet_start_y - self.caster.grid_y
        dx = ricochet_start_x - self.caster.grid_x

        # Reverse direction for ricochet
        dy = -dy if dy != 0 else 0
        dx = -dx if dx != 0 else 0

        # Normalize
        if dy != 0:
            dy = dy // abs(dy)
        if dx != 0:
            dx = dx // abs(dx)

        direction = (dy, dx)

        # Calculate ricochet trajectory (up to 6 tiles)
        self.ricochet_trajectory = calculate_linear_trajectory(
            start_pos=(ricochet_start_y, ricochet_start_x),
            direction=direction,
            ricochet_mode=False,
            max_range=6,  # Ricochet range
            game=self.game,
            max_bounces=0
        )

        self.current_trajectory_index = 0

        # Ricochet impact effect
        if self.ricochet_impact_pos:
            impact_x, impact_y = self.ricochet_impact_pos
            screen_x = impact_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = impact_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            screen_pos = (screen_x, screen_y)

            if screen_pos:
                # Purple burst for ricochet
                self.particle_emitter.emit_burst(screen_pos[0], screen_pos[1], self.color_purple, count=25)

        # Medium screen shake for ricochet
        self.screen_shake_callback(5, 0.5)

    def _start_buff_extraction(self):
        """Phase 4: Buff extraction visual effect."""
        self.phase = 'buff_extraction'
        self.timer = 0
        self.buff_stolen = True

        # Create extraction effect at ricochet end position
        if len(self.ricochet_trajectory) > 0:
            last_pos = self.ricochet_trajectory[min(self.current_trajectory_index, len(self.ricochet_trajectory) - 1)]
            extract_y, extract_x = last_pos
            extract_world_x = extract_x * TILE_SIZE + TILE_SIZE // 2
            extract_world_y = extract_y * TILE_SIZE + TILE_SIZE // 2

            self.buff_extraction_effect = BuffExtractionEffect(
                extract_world_x, extract_world_y, self.camera
            )

            # Purple flash
            self.screen_flash_callback(self.color_purple, 0.3)

    def _start_buff_ball_flight(self):
        """Phase 5: Buff ball travels away for ally interception."""
        self.phase = 'buff_ball'
        self.timer = 0

        # Create buff ball at extraction position
        if self.buff_extraction_effect:
            self.buff_ball = BuffBall(
                self.buff_extraction_effect.world_x,
                self.buff_extraction_effect.world_y,
                self.camera
            )

            # Calculate buff ball trajectory (travels away from caster)
            extract_grid_x = int(self.buff_extraction_effect.world_x / TILE_SIZE)
            extract_grid_y = int(self.buff_extraction_effect.world_y / TILE_SIZE)

            # Direction away from caster
            dy = extract_grid_y - self.caster.grid_y
            dx = extract_grid_x - self.caster.grid_x

            # Normalize
            if dy != 0:
                dy = dy // abs(dy)
            if dx != 0:
                dx = dx // abs(dx)

            direction = (dy, dx)

            # Calculate trajectory (up to 15 tiles)
            from boneglaive.dlc.pelotari.physics import calculate_linear_trajectory
            self.buff_ball_trajectory = calculate_linear_trajectory(
                start_pos=(extract_grid_y, extract_grid_x),
                direction=direction,
                ricochet_mode=True,  # Can ricochet once
                max_range=15,
                game=self.game,
                max_bounces=1
            )

            self.buff_ball_trajectory_index = 0

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.phase == 'launch':
            if self.timer >= self.launch_duration:
                self._start_initial_flight()

        elif self.phase == 'initial_flight':
            # Update pelota animation
            self.pelota.update(delta_time)

            # Move pelota along trajectory
            if self.current_trajectory_index < len(self.initial_trajectory):
                target_pos = self.initial_trajectory[self.current_trajectory_index]
                target_world_x = target_pos[1] * TILE_SIZE + TILE_SIZE // 2
                target_world_y = target_pos[0] * TILE_SIZE + TILE_SIZE // 2

                # Calculate distance to next waypoint
                dx = target_world_x - self.pelota.world_x
                dy = target_world_y - self.pelota.world_y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > 0:
                    # Move toward waypoint
                    move_distance = self.pelota_speed * delta_time

                    if move_distance >= distance:
                        # Reached waypoint
                        self.pelota.move_to(target_world_x, target_world_y)
                        self.current_trajectory_index += 1
                    else:
                        # Move partway
                        ratio = move_distance / distance
                        new_x = self.pelota.world_x + dx * ratio
                        new_y = self.pelota.world_y + dy * ratio
                        self.pelota.move_to(new_x, new_y)
                else:
                    self.current_trajectory_index += 1
            else:
                # Initial trajectory complete, start ricochet
                self._start_ricochet_flight()

        elif self.phase == 'ricochet_flight':
            # Update pelota animation
            self.pelota.update(delta_time)

            # Move pelota along ricochet trajectory
            if self.current_trajectory_index < len(self.ricochet_trajectory):
                target_pos = self.ricochet_trajectory[self.current_trajectory_index]
                target_world_x = target_pos[1] * TILE_SIZE + TILE_SIZE // 2
                target_world_y = target_pos[0] * TILE_SIZE + TILE_SIZE // 2

                # Calculate distance to next waypoint
                dx = target_world_x - self.pelota.world_x
                dy = target_world_y - self.pelota.world_y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > 0:
                    # Move toward waypoint
                    move_distance = self.pelota_speed * delta_time

                    if move_distance >= distance:
                        # Reached waypoint
                        self.pelota.move_to(target_world_x, target_world_y)
                        self.current_trajectory_index += 1

                        # Check if we should steal buff (simulate randomly for now - 30% chance)
                        # In real game, this would be determined by game logic
                        if self.current_trajectory_index >= len(self.ricochet_trajectory):
                            # Ricochet complete - randomly decide if buff was stolen
                            if random.random() < 0.3:  # 30% chance for animation demo
                                self._start_buff_extraction()
                                return self.active
                    else:
                        # Move partway
                        ratio = move_distance / distance
                        new_x = self.pelota.world_x + dx * ratio
                        new_y = self.pelota.world_y + dy * ratio
                        self.pelota.move_to(new_x, new_y)
                else:
                    self.current_trajectory_index += 1
            else:
                # Ricochet complete, no buff stolen
                self.active = False

        elif self.phase == 'buff_extraction':
            # Update extraction effect
            if self.buff_extraction_effect:
                self.buff_extraction_effect.update(delta_time)

                if not self.buff_extraction_effect.active:
                    # Extraction complete, start buff ball
                    self._start_buff_ball_flight()

        elif self.phase == 'buff_ball':
            # Update buff ball
            if self.buff_ball:
                self.buff_ball.update(delta_time)

                # Move buff ball along trajectory
                if self.buff_ball_trajectory_index < len(self.buff_ball_trajectory):
                    target_pos = self.buff_ball_trajectory[self.buff_ball_trajectory_index]
                    target_world_x = target_pos[1] * TILE_SIZE + TILE_SIZE // 2
                    target_world_y = target_pos[0] * TILE_SIZE + TILE_SIZE // 2

                    # Calculate distance to next waypoint
                    dx = target_world_x - self.buff_ball.world_x
                    dy = target_world_y - self.buff_ball.world_y
                    distance = math.sqrt(dx**2 + dy**2)

                    if distance > 0:
                        # Move toward waypoint (slower than pelota)
                        move_distance = 500 * delta_time  # 500 px/s for buff ball

                        if move_distance >= distance:
                            # Reached waypoint
                            self.buff_ball.move_to(target_world_x, target_world_y)
                            self.buff_ball_trajectory_index += 1
                        else:
                            # Move partway
                            ratio = move_distance / distance
                            new_x = self.buff_ball.world_x + dx * ratio
                            new_y = self.buff_ball.world_y + dy * ratio
                            self.buff_ball.move_to(new_x, new_y)
                    else:
                        self.buff_ball_trajectory_index += 1
                else:
                    # Buff ball trajectory complete
                    self.active = False
            else:
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        if self.phase == 'launch':
            # Just particles (handled by particle emitter)
            pass

        elif self.phase == 'initial_flight' or self.phase == 'ricochet_flight':
            # Draw pelota
            self.pelota.draw(surface)

        elif self.phase == 'buff_extraction':
            # Draw extraction effect
            if self.buff_extraction_effect:
                self.buff_extraction_effect.draw(surface)

        elif self.phase == 'buff_ball':
            # Draw buff ball
            if self.buff_ball:
                self.buff_ball.draw(surface)


# ============================================================================
# BACKHAND ANIMATION
# ============================================================================

class DefensiveRing:
    """
    Expanding defensive ring for Backhand stance activation.
    Royal blue ring that expands and fades.
    """

    def __init__(self, center_x, center_y, camera):
        """Initialize defensive ring."""
        self.center_x = center_x
        self.center_y = center_y
        self.camera = camera
        self.timer = 0
        self.duration = 0.4  # 0.4 seconds
        self.active = True

        self.start_radius = 20
        self.end_radius = 60

        self.color = (42, 90, 154)  # Royal blue

    def update(self, delta_time):
        """Update ring expansion."""
        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding ring."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expand and fade
        radius = int(self.start_radius + (self.end_radius - self.start_radius) * progress)
        alpha = int(255 * (1 - progress))

        # Get screen position with camera offsets
        screen_x = self.center_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.center_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Draw ring
        ring_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring_surface,
                          (*self.color, alpha),
                          (radius, radius),
                          radius, width=3)
        surface.blit(ring_surface,
                    (screen_x - radius, screen_y - radius),
                    special_flags=pygame.BLEND_ALPHA_SDL2)


class RotatingShield:
    """
    Rotating shield arcs orbiting PELOTARI during Backhand stance.
    4 arc segments in med blue that rotate clockwise.
    """

    def __init__(self, center_x, center_y, camera):
        """Initialize rotating shield."""
        self.center_x = center_x
        self.center_y = center_y
        self.camera = camera
        self.timer = 0
        self.duration = 0.6  # 0.6 seconds
        self.active = True

        self.orbit_radius = 40
        self.arc_length = 60  # degrees
        self.num_arcs = 4
        self.rotation_speed = 180  # degrees per second

        self.rotation = 0
        self.color = (74, 122, 186)  # Med blue

    def update(self, delta_time):
        """Update shield rotation."""
        self.timer += delta_time
        self.rotation += self.rotation_speed * delta_time
        self.rotation = self.rotation % 360

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw rotating shield arcs."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fade in then out
        if progress < 0.3:
            alpha = int(255 * (progress / 0.3))
        elif progress > 0.7:
            alpha = int(255 * ((1 - progress) / 0.3))
        else:
            alpha = 255

        # Get screen position with camera offsets
        screen_x = self.center_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.center_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Draw 4 arc segments
        for i in range(self.num_arcs):
            angle_offset = self.rotation + i * (360 / self.num_arcs)
            start_angle = math.radians(angle_offset)
            end_angle = math.radians(angle_offset + self.arc_length)

            # Create arc points
            arc_points = []
            num_points = 20
            for j in range(num_points):
                t = j / (num_points - 1)
                angle = start_angle + (end_angle - start_angle) * t
                px = screen_x + math.cos(angle) * self.orbit_radius
                py = screen_y + math.sin(angle) * self.orbit_radius
                arc_points.append((px, py))

            # Draw arc
            if len(arc_points) >= 2:
                # Create surface for alpha blending
                arc_surface = pygame.Surface((int(self.orbit_radius * 3), int(self.orbit_radius * 3)), pygame.SRCALPHA)
                offset_x = int(self.orbit_radius * 1.5)
                offset_y = int(self.orbit_radius * 1.5)

                # Adjust points relative to surface
                adjusted_points = [(px - screen_x + offset_x, py - screen_y + offset_y) for px, py in arc_points]
                pygame.draw.lines(arc_surface, (*self.color, alpha), False, adjusted_points, 4)

                surface.blit(arc_surface,
                            (screen_x - offset_x, screen_y - offset_y),
                            special_flags=pygame.BLEND_ALPHA_SDL2)


class ReadyPulse:
    """
    Final readiness pulse for Backhand stance.
    Gold shimmer that pulses and fades, indicating stance is active.
    """

    def __init__(self, center_x, center_y, camera):
        """Initialize ready pulse."""
        self.center_x = center_x
        self.center_y = center_y
        self.camera = camera
        self.timer = 0
        self.duration = 0.5  # 0.5 seconds
        self.active = True

        self.color_gold = (192, 176, 144)

    def update(self, delta_time):
        """Update pulse."""
        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw ready pulse."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Get screen position with camera offsets
        screen_x = self.center_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.center_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Pulse effect (expand and fade)
        radius = int(30 + 20 * progress)
        alpha = int(200 * (1 - progress))

        # Outer glow
        glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface,
                          (*self.color_gold, alpha),
                          (radius, radius),
                          radius)
        surface.blit(glow_surface,
                    (screen_x - radius, screen_y - radius),
                    special_flags=pygame.BLEND_ALPHA_SDL2)

        # Inner ring
        ring_radius = int(radius * 0.7)
        ring_alpha = int(255 * (1 - progress))
        ring_surface = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring_surface,
                          (*self.color_gold, ring_alpha),
                          (ring_radius, ring_radius),
                          ring_radius, width=3)
        surface.blit(ring_surface,
                    (screen_x - ring_radius, screen_y - ring_radius),
                    special_flags=pygame.BLEND_ALPHA_SDL2)


class BackhandAnimation:
    """
    Backhand skill animation for PELOTARI.
    Counter stance activation - PELOTARI assumes defensive position ready to reflect skills.

    Phases:
    1. Stance (0.4s) - Defensive ring expands from unit
    2. Shield (0.6s) - Rotating shield arcs orbit unit
    3. Ready (0.5s) - Final pulse indicating stance is active

    Total duration: ~1.5 seconds
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Backhand animation.

        Args:
            caster_unit: AnimatedUnit (PELOTARI assuming stance)
            target_unit: None (self-buff)
            target_pos: (grid_y, grid_x) - caster position
            is_crit: Unused
            is_infused: Unused
            particle_emitter: ParticleEmitter
            debris_list: Unused
            screen_shake_callback: Function to trigger screen shake
            screen_flash_callback: Function to trigger screen flash
            units_list: Unused
            camera: Camera instance
            game: Game instance (optional)
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback

        # Calculate caster world position (center of tile)
        self.caster_world_x = self.caster.grid_x * TILE_SIZE + TILE_SIZE // 2
        self.caster_world_y = self.caster.grid_y * TILE_SIZE + TILE_SIZE // 2

        # Animation state
        self.phase = 'stance'  # stance -> shield -> ready -> done
        self.timer = 0
        self.active = True

        # Sub-effects
        self.defensive_ring = None
        self.rotating_shield = None
        self.ready_pulse = None

        # Colors
        self.color_royal_blue = (42, 90, 154)
        self.color_med_blue = (74, 122, 186)
        self.color_gold = (192, 176, 144)

        # Start stance phase
        self._start_stance()

    def _start_stance(self):
        """Phase 1: Defensive stance activation."""
        self.phase = 'stance'
        self.timer = 0

        # Create expanding defensive ring
        self.defensive_ring = DefensiveRing(
            self.caster_world_x,
            self.caster_world_y,
            self.camera
        )

        # Particle burst at feet
        screen_x = self.caster_world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.caster_world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        self.particle_emitter.emit_burst(
            screen_x, screen_y,
            self.color_royal_blue, count=15
        )

        # Light screen shake
        self.screen_shake_callback(2, 0.3)

    def _start_shield(self):
        """Phase 2: Rotating shield activation."""
        self.phase = 'shield'
        self.timer = 0

        # Create rotating shield
        self.rotating_shield = RotatingShield(
            self.caster_world_x,
            self.caster_world_y,
            self.camera
        )

        # Screen flash (subtle)
        self.screen_flash_callback(self.color_med_blue, 0.2)

    def _start_ready(self):
        """Phase 3: Ready stance indicator."""
        self.phase = 'ready'
        self.timer = 0

        # Create ready pulse
        self.ready_pulse = ReadyPulse(
            self.caster_world_x,
            self.caster_world_y,
            self.camera
        )

        # Gold particles rising
        screen_x = self.caster_world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.caster_world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        self.particle_emitter.emit_float(
            screen_x, screen_y,
            self.color_gold, count=12
        )

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == 'stance':
            # Stance phase (0.4s)
            if self.defensive_ring:
                self.defensive_ring.update(delta_time)

            if self.timer >= 0.4:
                self._start_shield()

        elif self.phase == 'shield':
            # Shield phase (0.6s)
            if self.rotating_shield:
                self.rotating_shield.update(delta_time)

            if self.timer >= 0.6:
                self._start_ready()

        elif self.phase == 'ready':
            # Ready phase (0.5s)
            if self.ready_pulse:
                self.ready_pulse.update(delta_time)

            if self.timer >= 0.5:
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw the Backhand animation."""
        # Draw defensive ring (phase 1)
        if self.defensive_ring and self.defensive_ring.active:
            self.defensive_ring.draw(surface)

        # Draw rotating shield (phase 2)
        if self.rotating_shield and self.rotating_shield.active:
            self.rotating_shield.draw(surface)

        # Draw ready pulse (phase 3)
        if self.ready_pulse and self.ready_pulse.active:
            self.ready_pulse.draw(surface)
