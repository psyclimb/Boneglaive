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


# ============================================================================
# BACKHAND REFLECTION ANIMATION
# ============================================================================

class EstrangeBall:
    """
    Reality-warping pelota for reflected Estrange skill.
    Size between Riposte (18px) and Poach (23px) - ~19px diameter.
    Purple/lavender/white theme with dimensional distortion effects.
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the Estrange reflection ball.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - small-medium size
        self.size = 19  # 19px diameter (between Riposte 18px and Poach 23px)
        self.glow_size = int(self.size * 1.3)  # ~25px glow
        self.rotation = 0  # Rotation angle for orbiting particles
        self.rotation_speed = 240  # degrees per second

        # Estrange color palette (from estrange.svg icon)
        # Purple/lavender/white reality-warping beam theme
        self.color_purple = (170, 119, 255)      # #aa77ff - main purple
        self.color_lavender = (221, 187, 255)    # #ddbbff - lighter lavender
        self.color_white = (255, 255, 255)       # #ffffff - core/highlights
        self.color_purple_dark = (130, 80, 200)  # Darker purple for depth

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 7

        # Orbiting dimensional tear particles
        self.particle_count = 5
        self.orbit_phase = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
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
        """Update ball animation."""
        # Rotate for orbiting particles
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Update orbit phase for wave effect
        self.orbit_phase += delta_time * 3
        self.orbit_phase %= (2 * math.pi)

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.86) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        return True

    def draw(self, surface):
        """Draw the Estrange ball with reality-warping effects."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail with reality distortion
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.4 + 0.6 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 110)

            # Purple trail with wave distortion
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_purple, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

            # Add lavender inner trail
            inner_trail_size = trail_size // 2
            if inner_trail_size > 0:
                inner_alpha = int(alpha * 60)
                inner_surf = pygame.Surface((inner_trail_size * 2, inner_trail_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(inner_surf, (*self.color_lavender, inner_alpha),
                                 (inner_trail_size, inner_trail_size), inner_trail_size)
                surface.blit(inner_surf, (int(tx - inner_trail_size), int(ty - inner_trail_size)))

        # Layer 1: Pulsing purple glow (reality distortion aura)
        import time
        pulse = 0.7 + 0.3 * math.sin(time.time() * 5)
        glow_alpha = int(100 * pulse)

        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(6):  # 6 glow rings
            radius = self.glow_size - radius_offset * 2
            alpha = int(glow_alpha * (1.0 - radius_offset / 6))
            if radius > 0:
                pygame.draw.circle(glow_surf, (*self.color_purple, alpha),
                                 (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 2: Reality distortion waves (expanding/contracting rings)
        wave_time = time.time() * 4
        for i in range(3):
            wave_offset = (wave_time + i * 0.5) % 1.0
            wave_radius = int(self.size * (0.6 + wave_offset * 0.8))
            wave_alpha = int(120 * (1.0 - wave_offset))

            if wave_radius > 0 and wave_alpha > 0:
                wave_surf = pygame.Surface((wave_radius * 2, wave_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(wave_surf, (*self.color_lavender, wave_alpha),
                                 (wave_radius, wave_radius), wave_radius, 1)
                surface.blit(wave_surf, (int(cx - wave_radius), int(cy - wave_radius)))

        # Layer 3: Main purple ball
        pygame.draw.circle(surface, self.color_purple, (int(cx), int(cy)), self.size // 2)

        # Layer 4: Lavender inner layer (gradient effect)
        inner_size = int(self.size * 0.6)
        if inner_size > 0:
            pygame.draw.circle(surface, self.color_lavender, (int(cx), int(cy)), inner_size // 2)

        # Layer 5: White core (bright center)
        core_size = int(self.size * 0.3)
        if core_size > 0:
            # Pulsing white core
            core_alpha = int(220 + 35 * math.sin(time.time() * 6))
            core_surf = pygame.Surface((core_size * 2, core_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (*self.color_white, core_alpha),
                             (core_size, core_size), core_size)
            surface.blit(core_surf, (int(cx - core_size), int(cy - core_size)))

        # Layer 6: Orbiting dimensional tear particles
        angle_rad = math.radians(self.rotation)
        for i in range(self.particle_count):
            angle = angle_rad + (i / self.particle_count) * 2 * math.pi

            # Variable orbit radius (wave effect)
            base_orbit = self.size * 0.85
            orbit_variation = math.sin(self.orbit_phase + i) * 3
            orbit_radius = base_orbit + orbit_variation

            px = int(cx + math.cos(angle) * orbit_radius)
            py = int(cy + math.sin(angle) * orbit_radius)

            # Alternating lavender and white particles
            particle_color = self.color_lavender if i % 2 == 0 else self.color_white
            particle_size = 2 if i % 2 == 0 else 1
            particle_alpha = int(200 + 40 * math.sin(angle * 3))

            particle_surf = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*particle_color, particle_alpha),
                             (particle_size, particle_size), particle_size)
            surface.blit(particle_surf, (px - particle_size, py - particle_size))

        # Layer 7: Spacetime distortion lines (phase effect)
        # Vertical wavy lines suggesting dimensional instability
        line_count = 4
        for i in range(line_count):
            angle = (i / line_count) * 2 * math.pi
            line_x = int(cx + math.cos(angle) * self.size * 0.5)
            line_y = int(cy + math.sin(angle) * self.size * 0.5)

            # Short distortion lines
            line_end_x = int(cx + math.cos(angle) * self.size * 0.7)
            line_end_y = int(cy + math.sin(angle) * self.size * 0.7)

            line_alpha = int(100 + 50 * math.sin(time.time() * 4 + i))
            pygame.draw.line(surface, (*self.color_purple_dark, line_alpha),
                           (line_x, line_y), (line_end_x, line_end_y), 1)


class ExpediteBall:
    """
    Mechanical pelota with gnashing jaws for reflected Expedite skill.
    Size ~19px diameter with animated mechanical jaw components.
    Gray/brown metallic theme with steam/pressure effects.
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the Expedite reflection ball.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - small-medium size
        self.size = 19  # 19px diameter
        self.glow_size = int(self.size * 1.2)  # Subtle glow
        self.rotation = 0  # Overall rotation
        self.rotation_speed = 180  # degrees per second

        # Jaw animation
        self.jaw_phase = 0  # 0 to 2*pi for open/close cycle
        self.jaw_speed = 10  # radians per second (~0.3s cycle)
        self.max_jaw_angle = math.pi / 3  # 60 degrees max opening

        # Expedite color palette - mechanical/hydraulic
        self.color_dark_gray = (105, 105, 105)    # #696969 - main body
        self.color_gray = (139, 139, 139)         # #8b8b8b - highlights
        self.color_light_gray = (169, 169, 169)   # #a9a9a9 - lighter accents
        self.color_brown = (139, 105, 20)         # #8b6914 - MANDIBLE brown theme
        self.color_orange = (255, 140, 0)         # #ff8c00 - pressure glow
        self.color_white = (255, 255, 255)        # Steam

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 6

        # Steam particles
        self.steam_particles = []
        self.steam_timer = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
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
        """Update ball animation."""
        # Rotate ball
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Update jaw phase (gnashing animation)
        self.jaw_phase += self.jaw_speed * delta_time
        self.jaw_phase %= (2 * math.pi)

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.87) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        # Update steam particles
        self.steam_timer += delta_time
        if self.steam_timer >= 0.08:  # Emit steam every 0.08s
            self.steam_timer = 0
            # Add steam particle at current position
            screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            self.steam_particles.append({
                'x': screen_x,
                'y': screen_y,
                'vx': random.uniform(-15, 15),
                'vy': random.uniform(-30, -10),
                'life': 0.5,
                'max_life': 0.5,
                'size': random.randint(2, 4)
            })

        # Update existing steam particles
        for particle in self.steam_particles:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time

        # Remove dead particles
        self.steam_particles = [p for p in self.steam_particles if p['life'] > 0]

        return True

    def draw(self, surface):
        """Draw the Expedite ball with gnashing jaws and steam."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail (metallic gray)
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.4 + 0.6 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 100)

            # Gray metallic trail
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_gray, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Layer 1: Steam particles
        for particle in self.steam_particles:
            alpha = int(180 * (particle['life'] / particle['max_life']))
            size = particle['size']
            steam_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(steam_surf, (*self.color_white, alpha),
                             (size, size), size)
            surface.blit(steam_surf, (int(particle['x'] - size), int(particle['y'] - size)))

        # Layer 2: Pressure glow (orange/brown)
        import time
        pulse = 0.6 + 0.4 * math.sin(time.time() * 6)  # Fast pulse (pressure)
        glow_alpha = int(80 * pulse)

        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(5):
            radius = self.glow_size - radius_offset * 2
            alpha = int(glow_alpha * (1.0 - radius_offset / 5))
            if radius > 0:
                pygame.draw.circle(glow_surf, (*self.color_orange, alpha),
                                 (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 3: Main dark gray ball body
        pygame.draw.circle(surface, self.color_dark_gray, (int(cx), int(cy)), self.size // 2)

        # Layer 4: Gray highlight (gradient effect)
        inner_size = int(self.size * 0.7)
        if inner_size > 0:
            highlight_offset_x = -self.size // 6
            highlight_offset_y = -self.size // 6
            pygame.draw.circle(surface, self.color_gray,
                             (int(cx + highlight_offset_x), int(cy + highlight_offset_y)),
                             inner_size // 2)

        # Layer 5: Brown accent ring (MANDIBLE theme)
        ring_radius = int(self.size * 0.45)
        ring_thickness = 2
        if ring_radius > 0:
            pygame.draw.circle(surface, self.color_brown, (int(cx), int(cy)),
                             ring_radius, ring_thickness)

        # Layer 6: ANIMATED GNASHING JAWS
        # Calculate jaw opening based on sine wave (0 = closed, 1 = fully open)
        jaw_opening = (math.sin(self.jaw_phase) + 1) / 2  # 0 to 1
        current_jaw_angle = jaw_opening * self.max_jaw_angle

        # Jaw parameters
        jaw_radius = self.size // 2 - 2  # Slightly smaller than ball
        jaw_thickness = 3

        # Upper jaw (top half arc)
        # Arc from left to right, opening upward
        upper_jaw_start_angle = math.pi - current_jaw_angle / 2
        upper_jaw_end_angle = current_jaw_angle / 2
        upper_jaw_rect = pygame.Rect(cx - jaw_radius, cy - jaw_radius,
                                     jaw_radius * 2, jaw_radius * 2)

        # Draw upper jaw arc
        pygame.draw.arc(surface, self.color_light_gray, upper_jaw_rect,
                       upper_jaw_end_angle, upper_jaw_start_angle, jaw_thickness)

        # Lower jaw (bottom half arc)
        # Arc from left to right, opening downward
        lower_jaw_start_angle = math.pi + current_jaw_angle / 2
        lower_jaw_end_angle = 2 * math.pi - current_jaw_angle / 2
        lower_jaw_rect = pygame.Rect(cx - jaw_radius, cy - jaw_radius,
                                     jaw_radius * 2, jaw_radius * 2)

        # Draw lower jaw arc
        pygame.draw.arc(surface, self.color_light_gray, lower_jaw_rect,
                       lower_jaw_start_angle, lower_jaw_end_angle, jaw_thickness)

        # Add jaw "teeth" - small protrusions on jaw edges
        tooth_count = 6
        tooth_size = 2
        for i in range(tooth_count):
            # Upper teeth
            angle = math.pi - current_jaw_angle / 2 + (i / (tooth_count - 1)) * current_jaw_angle
            tooth_x = int(cx + math.cos(angle) * jaw_radius)
            tooth_y = int(cy + math.sin(angle) * jaw_radius)
            pygame.draw.circle(surface, self.color_white, (tooth_x, tooth_y), tooth_size)

            # Lower teeth
            angle = math.pi + current_jaw_angle / 2 + (i / (tooth_count - 1)) * current_jaw_angle
            tooth_x = int(cx + math.cos(angle) * jaw_radius)
            tooth_y = int(cy + math.sin(angle) * jaw_radius)
            pygame.draw.circle(surface, self.color_white, (tooth_x, tooth_y), tooth_size)

        # Layer 7: Rotating rivets/bolts (mechanical detail)
        angle_rad = math.radians(self.rotation)
        rivet_count = 4
        for i in range(rivet_count):
            angle = angle_rad + (i / rivet_count) * 2 * math.pi
            rivet_radius = self.size * 0.6
            rx = int(cx + math.cos(angle) * rivet_radius)
            ry = int(cy + math.sin(angle) * rivet_radius)

            # Dark gray rivets
            pygame.draw.circle(surface, self.color_dark_gray, (rx, ry), 2)
            pygame.draw.circle(surface, self.color_light_gray, (rx, ry), 1)


class AuctionCurseBall:
    """
    Skeletal pelota with glowing gold eyes for reflected Auction Curse skill.
    Size ~19px diameter with skull motif, gold eyes, and currency symbols.
    Black/gold theme matching the skeletal auctioneer.
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the Auction Curse reflection ball.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - small-medium size
        self.size = 19  # 19px diameter
        self.glow_size = int(self.size * 1.4)  # Prominent gold glow
        self.rotation = 0  # For orbiting currency symbols
        self.rotation_speed = 150  # degrees per second

        # Gavel strike animation
        self.gavel_phase = 0  # 0 to 2*pi for strike cycle
        self.gavel_speed = 8  # radians per second (~0.4s cycle)

        # Eye pulse animation
        self.eye_pulse_phase = 0

        # Auction Curse color palette - skeletal auctioneer theme
        self.color_black = (26, 26, 26)           # #1a1a1a - skeleton
        self.color_dark_gray = (44, 44, 44)       # #2c2c2c - skull fill
        self.color_gold = (255, 215, 0)           # #ffd700 - eyes, currency
        self.color_dark_gold = (218, 165, 32)     # #daa520 - glow, accents
        self.color_brown = (139, 69, 19)          # #8b4513 - gavel handle
        self.color_white = (255, 255, 255)        # Eye highlights

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 6

        # Orbiting currency symbols
        self.currency_count = 4

        # Dark curse tendrils
        self.tendril_points = []
        self.tendril_timer = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
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
        """Update ball animation."""
        # Rotate currency symbols
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Update gavel strike phase
        self.gavel_phase += self.gavel_speed * delta_time
        self.gavel_phase %= (2 * math.pi)

        # Update eye pulse
        self.eye_pulse_phase += delta_time * 5
        self.eye_pulse_phase %= (2 * math.pi)

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.86) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        # Update curse tendrils
        self.tendril_timer += delta_time
        if self.tendril_timer >= 0.1:  # New tendril every 0.1s
            self.tendril_timer = 0
            # Add tendril point at current position with random offset
            screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            self.tendril_points.append({
                'x': screen_x + random.uniform(-self.size//2, self.size//2),
                'y': screen_y + random.uniform(-self.size//2, self.size//2),
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(-20, 20),
                'life': 0.6,
                'max_life': 0.6,
                'size': random.randint(2, 4)
            })

        # Update existing tendrils
        for tendril in self.tendril_points:
            tendril['x'] += tendril['vx'] * delta_time
            tendril['y'] += tendril['vy'] * delta_time
            tendril['life'] -= delta_time

        # Remove dead tendrils
        self.tendril_points = [t for t in self.tendril_points if t['life'] > 0]

        return True

    def draw(self, surface):
        """Draw the Auction Curse ball with skull, gold eyes, and gavel."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail (dark with gold tint)
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.4 + 0.6 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 100)

            # Black trail with gold edge
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_black, trail_alpha),
                             (trail_size, trail_size), trail_size)
            pygame.draw.circle(trail_surf, (*self.color_dark_gold, trail_alpha // 2),
                             (trail_size, trail_size), trail_size, 1)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Layer 1: Dark curse tendrils
        for tendril in self.tendril_points:
            alpha = int(120 * (tendril['life'] / tendril['max_life']))
            size = tendril['size']
            tendril_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(tendril_surf, (*self.color_black, alpha),
                             (size, size), size)
            surface.blit(tendril_surf, (int(tendril['x'] - size), int(tendril['y'] - size)))

        # Layer 2: Golden astral glow (auction energy)
        import time
        pulse = 0.7 + 0.3 * math.sin(time.time() * 4)
        glow_alpha = int(90 * pulse)

        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(6):
            radius = self.glow_size - radius_offset * 2
            alpha = int(glow_alpha * (1.0 - radius_offset / 6))
            if radius > 0:
                pygame.draw.circle(glow_surf, (*self.color_gold, alpha),
                                 (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 3: Main black skull ball body
        pygame.draw.circle(surface, self.color_black, (int(cx), int(cy)), self.size // 2)

        # Layer 4: Dark gray inner skull
        inner_size = int(self.size * 0.8)
        if inner_size > 0:
            pygame.draw.circle(surface, self.color_dark_gray, (int(cx), int(cy)), inner_size // 2)

        # Layer 5: GLOWING GOLD EYES (main feature)
        eye_offset_x = self.size // 6
        eye_offset_y = -self.size // 8
        eye_radius = 2

        # Eye pulse
        eye_pulse = 0.8 + 0.2 * math.sin(self.eye_pulse_phase)
        eye_glow_radius = int(4 * eye_pulse)

        # Left eye
        left_eye_x = int(cx - eye_offset_x)
        left_eye_y = int(cy + eye_offset_y)

        # Eye glow
        eye_glow_surf = pygame.Surface((eye_glow_radius * 2, eye_glow_radius * 2), pygame.SRCALPHA)
        for i in range(4):
            glow_r = eye_glow_radius - i
            glow_a = int(100 * (1.0 - i / 4) * eye_pulse)
            if glow_r > 0:
                pygame.draw.circle(eye_glow_surf, (*self.color_gold, glow_a),
                                 (eye_glow_radius, eye_glow_radius), glow_r)
        surface.blit(eye_glow_surf, (left_eye_x - eye_glow_radius, left_eye_y - eye_glow_radius))

        # Eye socket (black)
        pygame.draw.circle(surface, (0, 0, 0), (left_eye_x, left_eye_y), eye_radius + 1)
        # Eye (gold)
        pygame.draw.circle(surface, self.color_gold, (left_eye_x, left_eye_y), eye_radius)
        # Eye highlight
        pygame.draw.circle(surface, self.color_white, (left_eye_x, left_eye_y - 1), 1)

        # Right eye
        right_eye_x = int(cx + eye_offset_x)
        right_eye_y = int(cy + eye_offset_y)

        # Eye glow
        surface.blit(eye_glow_surf, (right_eye_x - eye_glow_radius, right_eye_y - eye_glow_radius))

        # Eye socket (black)
        pygame.draw.circle(surface, (0, 0, 0), (right_eye_x, right_eye_y), eye_radius + 1)
        # Eye (gold)
        pygame.draw.circle(surface, self.color_gold, (right_eye_x, right_eye_y), eye_radius)
        # Eye highlight
        pygame.draw.circle(surface, self.color_white, (right_eye_x, right_eye_y - 1), 1)

        # Layer 6: Skull features (nose cavity, jaw line)
        # Nose cavity
        nose_y = int(cy + self.size // 10)
        pygame.draw.circle(surface, (0, 0, 0), (int(cx), nose_y), 1)

        # Jaw line (subtle)
        jaw_y = int(cy + self.size // 4)
        pygame.draw.arc(surface, self.color_black,
                       pygame.Rect(int(cx - self.size//4), jaw_y - 2, self.size//2, 4),
                       0, math.pi, 2)

        # Layer 7: Orbiting currency symbols (¤)
        angle_rad = math.radians(self.rotation)
        for i in range(self.currency_count):
            angle = angle_rad + (i / self.currency_count) * 2 * math.pi
            orbit_radius = self.size * 0.85
            symbol_x = int(cx + math.cos(angle) * orbit_radius)
            symbol_y = int(cy + math.sin(angle) * orbit_radius)

            # Render currency symbol ¤
            # Draw as a circle with crosshairs
            symbol_radius = 3
            symbol_alpha = int(200 + 55 * math.sin(angle * 2))

            # Outer circle
            symbol_surf = pygame.Surface((symbol_radius * 2, symbol_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(symbol_surf, (*self.color_gold, symbol_alpha),
                             (symbol_radius, symbol_radius), symbol_radius, 1)
            # Crosshairs
            pygame.draw.line(symbol_surf, (*self.color_gold, symbol_alpha),
                           (0, symbol_radius), (symbol_radius * 2, symbol_radius), 1)
            pygame.draw.line(symbol_surf, (*self.color_gold, symbol_alpha),
                           (symbol_radius, 0), (symbol_radius, symbol_radius * 2), 1)
            surface.blit(symbol_surf, (symbol_x - symbol_radius, symbol_y - symbol_radius))

        # Layer 8: Golden gavel (strikes rhythmically)
        # Gavel position oscillates up/down to simulate striking
        gavel_strike = math.sin(self.gavel_phase)  # -1 to 1
        gavel_offset_y = int(gavel_strike * 3)  # 3px oscillation

        gavel_x = int(cx + self.size // 3)
        gavel_y = int(cy - self.size // 3 + gavel_offset_y)

        # Gavel head (small rectangle)
        gavel_head_width = 4
        gavel_head_height = 2
        gavel_rect = pygame.Rect(gavel_x - gavel_head_width // 2, gavel_y - gavel_head_height // 2,
                                  gavel_head_width, gavel_head_height)
        pygame.draw.rect(surface, self.color_gold, gavel_rect)
        pygame.draw.rect(surface, self.color_dark_gold, gavel_rect, 1)

        # Gavel handle (small vertical line)
        handle_start_y = gavel_y + gavel_head_height // 2
        handle_end_y = handle_start_y + 3
        pygame.draw.line(surface, self.color_brown,
                        (gavel_x, handle_start_y), (gavel_x, handle_end_y), 1)

        # Strike impact lines (when gavel is at bottom of strike)
        if gavel_strike < -0.5:  # Bottom half of strike
            impact_alpha = int(180 * abs(gavel_strike + 0.5) / 0.5)
            # Two impact lines
            pygame.draw.line(surface, (*self.color_gold, impact_alpha),
                           (gavel_x - 4, gavel_y), (gavel_x - 7, gavel_y), 1)
            pygame.draw.line(surface, (*self.color_gold, impact_alpha),
                           (gavel_x + 4, gavel_y), (gavel_x + 7, gavel_y), 1)


class PryBall:
    """
    Leverage-themed pelota with pulsing fulcrum point for reflected Pry skill.
    Size ~19px diameter with orange energy burst, rotating rays, and force arrows.
    Orange/white theme matching the critical leverage moment.
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the Pry reflection ball.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - small-medium size
        self.size = 19  # 19px diameter
        self.glow_size = int(self.size * 1.5)  # Prominent orange glow
        self.rotation = 0  # For rotating energy rays
        self.rotation_speed = 200  # degrees per second (fast rotation)

        # Fulcrum pulse animation
        self.pulse_phase = 0
        self.pulse_speed = 6  # Fast pulsing (energy buildup)

        # Force arrow animation
        self.arrow_phase = 0
        self.arrow_speed = 5  # Oscillating force indicators

        # Pry color palette - leverage/force theme
        self.color_orange = (255, 102, 0)         # #ff6600 - main energy
        self.color_light_orange = (255, 153, 68)  # #ff9944 - glow, rays
        self.color_white = (255, 255, 255)        # Core, highlights
        self.color_dark_orange = (204, 85, 0)     # Darker accents

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 7

        # Energy ray count
        self.ray_count = 4  # 4 diagonal rays

        # Stress particles (tension indicators)
        self.stress_particles = []
        self.stress_timer = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
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
        """Update ball animation."""
        # Rotate energy rays
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Update fulcrum pulse
        self.pulse_phase += self.pulse_speed * delta_time
        self.pulse_phase %= (2 * math.pi)

        # Update arrow oscillation
        self.arrow_phase += self.arrow_speed * delta_time
        self.arrow_phase %= (2 * math.pi)

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.88) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        # Update stress particles
        self.stress_timer += delta_time
        if self.stress_timer >= 0.06:  # New stress particle every 0.06s
            self.stress_timer = 0
            # Add stress particle at edge
            screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

            # Spawn at random angle on edge
            angle = random.uniform(0, 2 * math.pi)
            spawn_radius = self.size // 2
            self.stress_particles.append({
                'x': screen_x + math.cos(angle) * spawn_radius,
                'y': screen_y + math.sin(angle) * spawn_radius,
                'vx': math.cos(angle) * 40,
                'vy': math.sin(angle) * 40,
                'life': 0.4,
                'max_life': 0.4,
                'size': 2
            })

        # Update existing stress particles
        for particle in self.stress_particles:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time

        # Remove dead particles
        self.stress_particles = [p for p in self.stress_particles if p['life'] > 0]

        return True

    def draw(self, surface):
        """Draw the Pry ball with fulcrum energy burst and force indicators."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail (orange energy)
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.4 + 0.6 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 120)

            # Orange trail with white core
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_light_orange, trail_alpha),
                             (trail_size, trail_size), trail_size)
            pygame.draw.circle(trail_surf, (*self.color_white, trail_alpha // 2),
                             (trail_size, trail_size), trail_size // 2)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Layer 1: Stress particles (tension indicators)
        for particle in self.stress_particles:
            alpha = int(180 * (particle['life'] / particle['max_life']))
            size = particle['size']
            stress_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(stress_surf, (*self.color_light_orange, alpha),
                             (size, size), size)
            surface.blit(stress_surf, (int(particle['x'] - size), int(particle['y'] - size)))

        # Layer 2: Orange energy glow (fulcrum aura)
        import time
        pulse = 0.6 + 0.4 * math.sin(self.pulse_phase)
        glow_alpha = int(100 * pulse)

        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(7):
            radius = self.glow_size - radius_offset * 2
            alpha = int(glow_alpha * (1.0 - radius_offset / 7))
            if radius > 0:
                pygame.draw.circle(glow_surf, (*self.color_orange, alpha),
                                 (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 3: Pulsing orange rings (energy waves)
        ring_pulse = (time.time() * 3) % 1.0  # 0 to 1
        ring_radius = int(self.size * (0.7 + ring_pulse * 0.5))
        ring_alpha = int(150 * (1.0 - ring_pulse))
        if ring_alpha > 0:
            pygame.draw.circle(surface, (*self.color_light_orange, ring_alpha),
                             (int(cx), int(cy)), ring_radius, 2)

        # Layer 4: Main orange ball body
        pygame.draw.circle(surface, self.color_orange, (int(cx), int(cy)), self.size // 2)

        # Layer 5: Light orange inner layer (gradient effect)
        inner_size = int(self.size * 0.7)
        if inner_size > 0:
            pygame.draw.circle(surface, self.color_light_orange, (int(cx), int(cy)), inner_size // 2)

        # Layer 6: White pulsing core (critical fulcrum point)
        core_pulse = 0.5 + 0.5 * math.sin(self.pulse_phase * 1.5)
        core_size = int(self.size * 0.4 * core_pulse)
        if core_size > 0:
            core_surf = pygame.Surface((core_size * 2, core_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (*self.color_white, 255),
                             (core_size, core_size), core_size)
            surface.blit(core_surf, (int(cx - core_size), int(cy - core_size)))

            # Bright center point
            center_size = max(2, int(core_size * 0.5))
            pygame.draw.circle(surface, self.color_white, (int(cx), int(cy)), center_size)

        # Layer 7: ROTATING ENERGY RAYS (main feature)
        angle_rad = math.radians(self.rotation)
        for i in range(self.ray_count):
            # Diagonal rays at 45° intervals
            angle = angle_rad + (i / self.ray_count) * 2 * math.pi

            # Ray extends from center outward
            ray_inner_radius = self.size * 0.3
            ray_outer_radius = self.size * 0.7

            inner_x = int(cx + math.cos(angle) * ray_inner_radius)
            inner_y = int(cy + math.sin(angle) * ray_inner_radius)
            outer_x = int(cx + math.cos(angle) * ray_outer_radius)
            outer_y = int(cy + math.sin(angle) * ray_outer_radius)

            # Draw ray with pulse effect
            ray_alpha = int(200 + 55 * math.sin(self.pulse_phase + i))

            # Thick orange base
            pygame.draw.line(surface, (*self.color_light_orange, ray_alpha),
                           (inner_x, inner_y), (outer_x, outer_y), 3)
            # Thin white highlight
            pygame.draw.line(surface, (*self.color_white, ray_alpha),
                           (inner_x, inner_y), (outer_x, outer_y), 1)

        # Layer 8: Force arrows (leverage indicators)
        arrow_oscillation = math.sin(self.arrow_phase)  # -1 to 1

        # Upward force arrow (top)
        up_arrow_offset = int(arrow_oscillation * 2)
        arrow_y_top = int(cy - self.size * 0.6 + up_arrow_offset)
        arrow_size = 4

        # Arrow shaft
        pygame.draw.line(surface, (*self.color_white, 200),
                        (int(cx), arrow_y_top + arrow_size), (int(cx), arrow_y_top), 2)
        # Arrow head (pointing up)
        arrow_head_points = [
            (int(cx), arrow_y_top),
            (int(cx - 3), arrow_y_top + 3),
            (int(cx + 3), arrow_y_top + 3)
        ]
        pygame.draw.polygon(surface, (*self.color_white, 220), arrow_head_points)
        pygame.draw.polygon(surface, self.color_light_orange, arrow_head_points, 1)

        # Downward force arrow (bottom)
        down_arrow_offset = int(-arrow_oscillation * 2)  # Opposite phase
        arrow_y_bottom = int(cy + self.size * 0.6 + down_arrow_offset)

        # Arrow shaft
        pygame.draw.line(surface, (*self.color_white, 200),
                        (int(cx), arrow_y_bottom - arrow_size), (int(cx), arrow_y_bottom), 2)
        # Arrow head (pointing down)
        arrow_head_points_down = [
            (int(cx), arrow_y_bottom),
            (int(cx - 3), arrow_y_bottom - 3),
            (int(cx + 3), arrow_y_bottom - 3)
        ]
        pygame.draw.polygon(surface, (*self.color_white, 220), arrow_head_points_down)
        pygame.draw.polygon(surface, self.color_light_orange, arrow_head_points_down, 1)

        # Layer 9: Stress lines (dashed tension indicators)
        # Draw 2 curved dashed lines showing leverage tension
        dash_alpha = int(120 + 60 * math.sin(time.time() * 4))

        # Left stress line
        for t in range(0, 10, 2):  # Dashed pattern
            t_frac = t / 10.0
            arc_x = int(cx - self.size * 0.5 + t_frac * self.size * 0.3)
            arc_y = int(cy - self.size * 0.4 * (1 - (t_frac - 0.5) ** 2 * 4))
            pygame.draw.circle(surface, (*self.color_light_orange, dash_alpha), (arc_x, arc_y), 1)


class NeuralShuntBall:
    """
    Neural hijack pelota with triangulating signals for reflected Neural Shunt skill.
    Size ~19px diameter with pulsing orange disruption core, three converging cyan beams,
    electromagnetic interference waves, and confusion symbols.
    Cyan/sky blue theme with orange disruption core (matches neural_shunt.svg icon).
    """

    def __init__(self, start_x, start_y, camera):
        """
        Initialize the Neural Shunt reflection ball.

        Args:
            start_x, start_y: Starting world coordinates
            camera: Camera instance for coordinate conversion
        """
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Visual properties - small-medium size
        self.size = 19  # 19px diameter
        self.glow_size = int(self.size * 1.4)  # Prominent cyan glow
        self.rotation = 0  # For orbiting towers and confusion symbols
        self.rotation_speed = 120  # degrees per second

        # Core disruption pulse
        self.core_pulse_phase = 0
        self.core_pulse_speed = 7  # Fast pulsing (neural disruption)

        # Radio wave rings animation
        self.wave_phase = 0
        self.wave_speed = 4

        # Neural Shunt color palette - from icon (cyan/blue/orange only)
        self.color_cyan = (0, 206, 209)           # #00ced1 - main cyan
        self.color_sky_blue = (0, 191, 255)       # #00bfff - signal beams
        self.color_orange = (255, 102, 0)         # #ff6600 - disruption core
        self.color_dark_gray = (42, 42, 42)       # #2a2a2a - brain structure
        self.color_white = (255, 255, 255)        # Highlights

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 6

        # Three tower positions (triangulation)
        self.tower_count = 3
        self.tower_distance = self.size * 0.95  # Orbit distance

        # Confusion symbols (? and !)
        self.confusion_symbols = ['?', '!', '?', '!']

        # Neural pathway particles
        self.neural_particles = []
        self.neural_timer = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
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
        """Update ball animation."""
        # Rotate towers and confusion symbols
        self.rotation += self.rotation_speed * delta_time
        self.rotation %= 360

        # Update core disruption pulse
        self.core_pulse_phase += self.core_pulse_speed * delta_time
        self.core_pulse_phase %= (2 * math.pi)

        # Update wave rings
        self.wave_phase += self.wave_speed * delta_time
        self.wave_phase %= (2 * math.pi)

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.87) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        # Update neural particles
        self.neural_timer += delta_time
        if self.neural_timer >= 0.1:  # New neural particle every 0.1s
            self.neural_timer = 0
            # Add neural particle at edge
            screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

            # Spawn at random angle on edge
            angle = random.uniform(0, 2 * math.pi)
            spawn_radius = self.size // 2
            self.neural_particles.append({
                'x': screen_x + math.cos(angle) * spawn_radius,
                'y': screen_y + math.sin(angle) * spawn_radius,
                'vx': math.cos(angle) * 30,
                'vy': math.sin(angle) * 30,
                'life': 0.5,
                'max_life': 0.5,
                'size': 2
            })

        # Update existing neural particles
        for particle in self.neural_particles:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time

        # Remove dead particles
        self.neural_particles = [p for p in self.neural_particles if p['life'] > 0]

        return True

    def draw(self, surface):
        """Draw the Neural Shunt ball with triangulating beams and disruption core."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if not screen_pos:
            return

        cx, cy = screen_pos

        # Draw motion trail (cyan)
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.4 + 0.6 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 120)

            # Cyan trail
            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_cyan, trail_alpha),
                             (trail_size, trail_size), trail_size)
            surface.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Layer 1: Neural pathway particles (cyan energy)
        for particle in self.neural_particles:
            alpha = int(200 * (particle['life'] / particle['max_life']))
            size = particle['size']
            neural_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(neural_surf, (*self.color_cyan, alpha),
                             (size, size), size)
            surface.blit(neural_surf, (int(particle['x'] - size), int(particle['y'] - size)))

        # Layer 2: Cyan electromagnetic glow
        import time
        pulse = 0.6 + 0.4 * math.sin(time.time() * 5)
        glow_alpha = int(90 * pulse)

        glow_surf = pygame.Surface((self.glow_size * 2, self.glow_size * 2), pygame.SRCALPHA)
        for radius_offset in range(6):
            radius = self.glow_size - radius_offset * 2
            alpha = int(glow_alpha * (1.0 - radius_offset / 6))
            if radius > 0:
                pygame.draw.circle(glow_surf, (*self.color_cyan, alpha),
                                 (self.glow_size, self.glow_size), radius)
        surface.blit(glow_surf, (int(cx - self.glow_size), int(cy - self.glow_size)))

        # Layer 3: Electromagnetic disruption waves (expanding rings)
        for i in range(3):
            wave_offset = (self.wave_phase + i * 0.7) % (2 * math.pi)
            ring_progress = wave_offset / (2 * math.pi)  # 0 to 1
            ring_radius = int(self.size * (0.6 + ring_progress * 0.6))
            ring_alpha = int(150 * (1.0 - ring_progress))

            if ring_alpha > 0:
                pygame.draw.circle(surface, (*self.color_sky_blue, ring_alpha),
                                 (int(cx), int(cy)), ring_radius, 1)

        # Layer 4: THREE ORBITING TOWER POSITIONS (triangulation points)
        angle_rad = math.radians(self.rotation)
        tower_positions = []
        for i in range(self.tower_count):
            angle = angle_rad + (i / self.tower_count) * 2 * math.pi
            tx = int(cx + math.cos(angle) * self.tower_distance)
            ty = int(cy + math.sin(angle) * self.tower_distance)
            tower_positions.append((tx, ty))

            # Draw small tower marker (pulsing dot)
            tower_pulse = 0.7 + 0.3 * math.sin(time.time() * 6 + i)
            tower_size = int(3 * tower_pulse)
            tower_alpha = int(200 * tower_pulse)

            tower_surf = pygame.Surface((tower_size * 2, tower_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(tower_surf, (*self.color_cyan, tower_alpha),
                             (tower_size, tower_size), tower_size)
            pygame.draw.circle(tower_surf, (*self.color_white, tower_alpha),
                             (tower_size, tower_size), max(1, tower_size // 2))
            surface.blit(tower_surf, (tx - tower_size, ty - tower_size))

        # Layer 5: CONVERGING SIGNAL BEAMS from towers to center
        for i, (tx, ty) in enumerate(tower_positions):
            # Animate beam along path from tower to center
            beam_progress = (time.time() * 2 + i * 0.5) % 1.0  # 0 to 1

            # Draw beam line with gradient effect
            beam_alpha = int(180 * (0.5 + 0.5 * math.sin(time.time() * 4 + i)))

            # Thick cyan base
            pygame.draw.line(surface, (*self.color_cyan, beam_alpha // 2),
                           (tx, ty), (int(cx), int(cy)), 2)
            # Thin white highlight
            pygame.draw.line(surface, (*self.color_white, beam_alpha),
                           (tx, ty), (int(cx), int(cy)), 1)

            # Moving pulse along beam
            pulse_x = int(tx + (cx - tx) * beam_progress)
            pulse_y = int(ty + (cy - ty) * beam_progress)
            pygame.draw.circle(surface, (*self.color_cyan, 220), (pulse_x, pulse_y), 2)

        # Layer 6: Main cyan ball body
        pygame.draw.circle(surface, self.color_cyan, (int(cx), int(cy)), self.size // 2)

        # Layer 7: Sky blue inner layer (gradient effect)
        inner_size = int(self.size * 0.75)
        if inner_size > 0:
            pygame.draw.circle(surface, self.color_sky_blue, (int(cx), int(cy)), inner_size // 2)

        # Layer 8: PULSING ORANGE DISRUPTION CORE (hijacked brain center)
        core_pulse = 0.6 + 0.4 * math.sin(self.core_pulse_phase)
        core_size = int(self.size * 0.35 * core_pulse)
        if core_size > 0:
            # Orange disruption core
            core_surf = pygame.Surface((core_size * 2, core_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (*self.color_orange, 200),
                             (core_size, core_size), core_size)
            surface.blit(core_surf, (int(cx - core_size), int(cy - core_size)))

            # Bright white center
            center_size = max(2, int(core_size * 0.5))
            pygame.draw.circle(surface, self.color_white, (int(cx), int(cy)), center_size)

        # Layer 9: Neural pathway lines inside ball (cyan energy)
        # Draw 2 crossing neural pathways
        pathway_length = self.size // 3
        pathway_alpha = int(150 + 50 * math.sin(time.time() * 6))

        # Horizontal pathway
        pygame.draw.line(surface, (*self.color_sky_blue, pathway_alpha),
                        (int(cx - pathway_length), int(cy)),
                        (int(cx + pathway_length), int(cy)), 1)

        # Vertical pathway
        pygame.draw.line(surface, (*self.color_sky_blue, pathway_alpha),
                        (int(cx), int(cy - pathway_length)),
                        (int(cx), int(cy + pathway_length)), 1)

        # Layer 10: Orbiting confusion symbols (? and !)
        symbol_angle_rad = math.radians(self.rotation * 1.5)  # Faster rotation
        for i, symbol in enumerate(self.confusion_symbols):
            angle = symbol_angle_rad + (i / len(self.confusion_symbols)) * 2 * math.pi
            symbol_radius = self.size * 0.75
            sx = int(cx + math.cos(angle) * symbol_radius)
            sy = int(cy + math.sin(angle) * symbol_radius)

            # Draw confusion symbol (? or !)
            symbol_alpha = int(180 + 75 * math.sin(angle * 2))

            # Use pygame font to render symbol
            try:
                font = pygame.font.Font(None, 10)  # Small monospace font
                symbol_color = (*self.color_orange, symbol_alpha)
                text_surf = font.render(symbol, True, symbol_color)
                text_rect = text_surf.get_rect(center=(sx, sy))
                surface.blit(text_surf, text_rect)
            except:
                # Fallback: draw as small circle if font fails
                pygame.draw.circle(surface, (*self.color_orange, symbol_alpha), (sx, sy), 2)


class GraniteGeasBall:
    """
    Stone curse pelota with gray aromatic vapors for reflected Granite Geas skill.
    Size ~19px diameter with rough granite texture, binding chains, and gray vapor wisps.
    Gray stone theme with cracks and runes (matches granite_geas.svg icon).
    """

    def __init__(self, start_x, start_y, camera):
        self.size = 19
        # Granite Geas color palette - gray stone theme
        self.color_gray = (140, 140, 140)         # Main gray
        self.color_light_gray = (160, 160, 160)   # Light gray
        self.color_dark_gray = (120, 120, 120)    # Dark gray
        self.color_blue_gray = (130, 130, 135)    # Blue-gray
        self.color_white = (255, 255, 255)        # Highlights
        self.color_black = (0, 0, 0)              # Shadow

        # Stone texture
        self.crack_lines = []
        for _ in range(6):
            angle = random.uniform(0, math.pi * 2)
            length = random.uniform(self.size * 0.3, self.size * 0.6)
            self.crack_lines.append({
                'angle': angle,
                'length': length,
                'thickness': random.randint(1, 2)
            })

        # Binding chains/runes
        self.rune_count = 4
        self.rune_angle_offset = 0

        # Gray vapor wisps
        self.vapor_wisps = []
        for _ in range(5):
            self.vapor_wisps.append({
                'angle': random.uniform(0, math.pi * 2),
                'distance': random.uniform(self.size * 0.6, self.size * 1.2),
                'size': random.uniform(3, 6),
                'alpha': random.randint(100, 200),
                'rotation_speed': random.uniform(-0.05, 0.05)
            })

        # Position
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Animation timing
        self.age = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
        self.world_x = world_x
        self.world_y = world_y

    def update(self, dt):
        """Update animation state."""
        self.age += dt

        # Rotate runes
        self.rune_angle_offset += dt * 0.5

        # Update vapor wisps
        for wisp in self.vapor_wisps:
            wisp['angle'] += wisp['rotation_speed']
            wisp['distance'] += dt * 10
            wisp['alpha'] = max(0, wisp['alpha'] - dt * 100)

        # Remove faded wisps and add new ones
        self.vapor_wisps = [w for w in self.vapor_wisps if w['alpha'] > 0]
        if len(self.vapor_wisps) < 5:
            self.vapor_wisps.append({
                'angle': random.uniform(0, math.pi * 2),
                'distance': self.size * 0.6,
                'size': random.uniform(3, 6),
                'alpha': random.randint(100, 200),
                'rotation_speed': random.uniform(-0.05, 0.05)
            })

    def draw(self, screen):
        """Draw the Granite Geas ball."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Draw gray vapor wisps behind ball
        for wisp in self.vapor_wisps:
            wisp_x = screen_x + math.cos(wisp['angle']) * wisp['distance']
            wisp_y = screen_y + math.sin(wisp['angle']) * wisp['distance']
            wisp_color = random.choice([self.color_gray, self.color_light_gray,
                                       self.color_dark_gray, self.color_blue_gray])
            wisp_surf = pygame.Surface((int(wisp['size'] * 2), int(wisp['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(wisp_surf, (*wisp_color, int(wisp['alpha'])),
                             (int(wisp['size']), int(wisp['size'])), int(wisp['size']))
            screen.blit(wisp_surf, (int(wisp_x - wisp['size']), int(wisp_y - wisp['size'])))

        # Draw main stone ball (dark gray base)
        pygame.draw.circle(screen, self.color_dark_gray,
                          (int(screen_x), int(screen_y)), self.size)

        # Draw granite texture layer (main gray)
        pygame.draw.circle(screen, self.color_gray,
                          (int(screen_x), int(screen_y)), int(self.size * 0.85))

        # Draw light gray inner layer
        pygame.draw.circle(screen, self.color_light_gray,
                          (int(screen_x), int(screen_y)), int(self.size * 0.6))

        # Draw crack lines
        for crack in self.crack_lines:
            start_x = screen_x + math.cos(crack['angle']) * self.size * 0.2
            start_y = screen_y + math.sin(crack['angle']) * self.size * 0.2
            end_x = screen_x + math.cos(crack['angle']) * crack['length']
            end_y = screen_y + math.sin(crack['angle']) * crack['length']
            pygame.draw.line(screen, self.color_black,
                           (int(start_x), int(start_y)),
                           (int(end_x), int(end_y)), crack['thickness'])

        # Draw binding runes/chains (rotating around ball)
        for i in range(self.rune_count):
            angle = (i / self.rune_count) * math.pi * 2 + self.rune_angle_offset
            rune_x = screen_x + math.cos(angle) * self.size * 0.7
            rune_y = screen_y + math.sin(angle) * self.size * 0.7
            # Draw small gray rectangle as rune symbol
            rune_size = 3
            pygame.draw.rect(screen, self.color_blue_gray,
                           (int(rune_x - rune_size/2), int(rune_y - rune_size/2),
                            rune_size, rune_size))

        # Draw highlight
        highlight_offset_x = -self.size * 0.3
        highlight_offset_y = -self.size * 0.3
        pygame.draw.circle(screen, self.color_white,
                          (int(screen_x + highlight_offset_x),
                           int(screen_y + highlight_offset_y)),
                          int(self.size * 0.2))

    def is_complete(self):
        """Ball is never complete on its own - controlled by parent animation."""
        return False


class InfusedGraniteGeasBall:
    """
    Infused stone curse pelota with tropical potpourri fumes for reflected Infused Granite Geas.
    Size ~19px diameter with gray stone core and multi-colored aromatic fumes.
    Uses 8 tropical flower colors: gold, hot pink, tomato, orange, medium purple,
    medium orchid, dark turquoise, deep pink (matches GraniteGeasEffect infused colors).
    """

    def __init__(self, start_x, start_y, camera):
        self.size = 19
        # Gray stone core colors
        self.color_gray = (140, 140, 140)
        self.color_light_gray = (160, 160, 160)
        self.color_dark_gray = (120, 120, 120)
        self.color_white = (255, 255, 255)
        self.color_black = (0, 0, 0)

        # Tropical potpourri fume colors (from GraniteGeasEffect infused palette)
        self.potpourri_colors = [
            (255, 215, 0),    # Gold
            (255, 105, 180),  # Hot pink
            (255, 99, 71),    # Tomato
            (255, 165, 0),    # Orange
            (147, 112, 219),  # Medium purple
            (186, 85, 211),   # Medium orchid
            (0, 206, 209),    # Dark turquoise
            (255, 20, 147)    # Deep pink
        ]

        # Stone texture
        self.crack_lines = []
        for _ in range(5):
            angle = random.uniform(0, math.pi * 2)
            length = random.uniform(self.size * 0.3, self.size * 0.5)
            self.crack_lines.append({
                'angle': angle,
                'length': length,
                'thickness': 1
            })

        # Colorful potpourri fumes
        self.fumes = []
        for _ in range(8):
            self.fumes.append({
                'angle': random.uniform(0, math.pi * 2),
                'distance': random.uniform(self.size * 0.7, self.size * 1.3),
                'size': random.uniform(4, 7),
                'alpha': random.randint(120, 220),
                'color': random.choice(self.potpourri_colors),
                'rotation_speed': random.uniform(-0.08, 0.08)
            })

        # Colorful rune particles
        self.rune_particles = []
        for i in range(6):
            angle = (i / 6) * math.pi * 2
            self.rune_particles.append({
                'angle': angle,
                'distance': self.size * 0.8,
                'color': random.choice(self.potpourri_colors),
                'size': 3
            })
        self.rune_rotation = 0

        # Position
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Animation timing
        self.age = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
        self.world_x = world_x
        self.world_y = world_y

    def update(self, dt):
        """Update animation state."""
        self.age += dt

        # Rotate colorful rune particles
        self.rune_rotation += dt * 0.8

        # Update potpourri fumes
        for fume in self.fumes:
            fume['angle'] += fume['rotation_speed']
            fume['distance'] += dt * 15
            fume['alpha'] = max(0, fume['alpha'] - dt * 120)

        # Remove faded fumes and add new colorful ones
        self.fumes = [f for f in self.fumes if f['alpha'] > 0]
        if len(self.fumes) < 8:
            self.fumes.append({
                'angle': random.uniform(0, math.pi * 2),
                'distance': self.size * 0.7,
                'size': random.uniform(4, 7),
                'alpha': random.randint(120, 220),
                'color': random.choice(self.potpourri_colors),
                'rotation_speed': random.uniform(-0.08, 0.08)
            })

    def draw(self, screen):
        """Draw the Infused Granite Geas ball."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Draw colorful potpourri fumes behind ball
        for fume in self.fumes:
            fume_x = screen_x + math.cos(fume['angle']) * fume['distance']
            fume_y = screen_y + math.sin(fume['angle']) * fume['distance']
            fume_surf = pygame.Surface((int(fume['size'] * 2), int(fume['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(fume_surf, (*fume['color'], int(fume['alpha'])),
                             (int(fume['size']), int(fume['size'])), int(fume['size']))
            screen.blit(fume_surf, (int(fume_x - fume['size']), int(fume_y - fume['size'])))

        # Draw main stone ball (dark gray base)
        pygame.draw.circle(screen, self.color_dark_gray,
                          (int(screen_x), int(screen_y)), self.size)

        # Draw granite texture layer (main gray)
        pygame.draw.circle(screen, self.color_gray,
                          (int(screen_x), int(screen_y)), int(self.size * 0.85))

        # Draw light gray inner layer
        pygame.draw.circle(screen, self.color_light_gray,
                          (int(screen_x), int(screen_y)), int(self.size * 0.6))

        # Draw crack lines
        for crack in self.crack_lines:
            start_x = screen_x + math.cos(crack['angle']) * self.size * 0.2
            start_y = screen_y + math.sin(crack['angle']) * self.size * 0.2
            end_x = screen_x + math.cos(crack['angle']) * crack['length']
            end_y = screen_y + math.sin(crack['angle']) * crack['length']
            pygame.draw.line(screen, self.color_black,
                           (int(start_x), int(start_y)),
                           (int(end_x), int(end_y)), crack['thickness'])

        # Draw colorful rune particles (rotating around ball)
        for particle in self.rune_particles:
            angle = particle['angle'] + self.rune_rotation
            particle_x = screen_x + math.cos(angle) * particle['distance']
            particle_y = screen_y + math.sin(angle) * particle['distance']
            pygame.draw.circle(screen, particle['color'],
                             (int(particle_x), int(particle_y)), particle['size'])

        # Draw highlight
        highlight_offset_x = -self.size * 0.3
        highlight_offset_y = -self.size * 0.3
        pygame.draw.circle(screen, self.color_white,
                          (int(screen_x + highlight_offset_x),
                           int(screen_y + highlight_offset_y)),
                          int(self.size * 0.2))

    def is_complete(self):
        """Ball is never complete on its own - controlled by parent animation."""
        return False


class JudgementBall:
    """
    Sacred glaive pelota for reflected Judgement skill.
    Size ~19px diameter with spinning 6-bladed glaive and golden divine aura.
    Gold/orange/white theme (matches judgement.svg icon).
    """

    def __init__(self, start_x, start_y, camera):
        self.size = 19
        # Judgement color palette - divine gold/orange theme
        self.color_gold = (255, 215, 0)           # #ffd700 - divine gold
        self.color_orange_gold = (255, 153, 68)   # #ff9944 - orange-gold
        self.color_orange = (255, 102, 0)         # #ff6600 - impact orange
        self.color_white = (255, 255, 255)        # Highlights
        self.color_silver = (192, 192, 192)       # #c0c0c0 - glaive metal
        self.color_light_silver = (208, 208, 208) # #d0d0d0 - lighter silver
        self.color_dark_gray = (106, 106, 106)    # #6a6a6a - glaive shadow

        # Spinning glaive animation
        self.rotation = 0  # Current rotation angle (degrees)
        self.rotation_speed = 720  # Degrees per second (2 full rotations/sec)

        # Golden aura pulsing
        self.pulse_timer = 0
        self.pulse_speed = 4  # Hz

        # Orbiting spark particles (sacred energy)
        self.spark_count = 6
        self.spark_offset = 0

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 5

        # Position
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Animation timing
        self.age = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
        # Store trail position
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        self.trail_positions.append((screen_x, screen_y, 1.0))

        # Trim trail
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)

        self.world_x = world_x
        self.world_y = world_y

    def update(self, dt):
        """Update animation state."""
        self.age += dt

        # Rotate glaive
        self.rotation += self.rotation_speed * dt
        self.rotation %= 360

        # Update pulse timer
        self.pulse_timer += dt * self.pulse_speed

        # Update spark orbit
        self.spark_offset += dt * 2

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.85) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        return True

    def draw(self, screen):
        """Draw the Judgement ball with spinning glaive and golden aura."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Draw golden motion trail
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.5 + 0.5 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 120)

            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_gold, trail_alpha),
                             (trail_size, trail_size), trail_size)
            screen.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # Pulsing golden aura (3 layers)
        pulse = 0.7 + 0.3 * math.sin(self.pulse_timer * math.pi * 2)

        # Outer glow (gold)
        glow_radius = int(self.size * 1.4 * pulse)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color_gold, int(80 * pulse)),
                         (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surf, (int(screen_x - glow_radius), int(screen_y - glow_radius)))

        # Mid layer (orange-gold)
        mid_radius = int(self.size * 1.1 * pulse)
        mid_surf = pygame.Surface((mid_radius * 2, mid_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(mid_surf, (*self.color_orange_gold, int(120 * pulse)),
                         (mid_radius, mid_radius), mid_radius)
        screen.blit(mid_surf, (int(screen_x - mid_radius), int(screen_y - mid_radius)))

        # Core white energy
        core_radius = int(self.size * 0.8)
        core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, (*self.color_white, int(150 * pulse)),
                         (core_radius, core_radius), core_radius)
        screen.blit(core_surf, (int(screen_x - core_radius), int(screen_y - core_radius)))

        # Draw spinning 6-bladed glaive shuriken
        glaive_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        center = self.size

        # Draw 6 blades
        for i in range(6):
            angle_deg = self.rotation + (i * 60)  # 60 degrees apart
            angle_rad = math.radians(angle_deg)

            # Blade points (triangle from center)
            blade_length = self.size * 0.7
            blade_width = self.size * 0.25

            # Tip of blade
            tip_x = center + math.cos(angle_rad) * blade_length
            tip_y = center + math.sin(angle_rad) * blade_length

            # Base corners
            perp_angle = angle_rad + math.pi / 2
            base1_x = center + math.cos(perp_angle) * blade_width
            base1_y = center + math.sin(perp_angle) * blade_width
            base2_x = center - math.cos(perp_angle) * blade_width
            base2_y = center - math.sin(perp_angle) * blade_width

            # Draw blade layers (shadow → silver → highlight)
            blade_points = [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]
            pygame.draw.polygon(glaive_surf, self.color_dark_gray, blade_points)
            # Slightly smaller silver layer
            blade_points_silver = [
                (tip_x * 0.95 + center * 0.05, tip_y * 0.95 + center * 0.05),
                (base1_x * 0.9 + center * 0.1, base1_y * 0.9 + center * 0.1),
                (base2_x * 0.9 + center * 0.1, base2_y * 0.9 + center * 0.1)
            ]
            pygame.draw.polygon(glaive_surf, self.color_silver, blade_points_silver)
            # Center line highlight
            pygame.draw.line(glaive_surf, self.color_white,
                           (center, center), (tip_x, tip_y), 1)

        # Central hub
        pygame.draw.circle(glaive_surf, self.color_dark_gray, (center, center), int(self.size * 0.25))
        pygame.draw.circle(glaive_surf, self.color_silver, (center, center), int(self.size * 0.2))
        pygame.draw.circle(glaive_surf, self.color_light_silver, (center, center), int(self.size * 0.15))

        screen.blit(glaive_surf, (int(screen_x - self.size), int(screen_y - self.size)))

        # Orbiting golden spark particles (sacred energy)
        for i in range(self.spark_count):
            angle = (i / self.spark_count) * math.pi * 2 + self.spark_offset
            spark_distance = self.size * 1.2
            spark_x = screen_x + math.cos(angle) * spark_distance
            spark_y = screen_y + math.sin(angle) * spark_distance
            spark_size = 2
            pygame.draw.circle(screen, self.color_gold,
                             (int(spark_x), int(spark_y)), spark_size)

    def is_complete(self):
        """Ball is never complete on its own - controlled by parent animation."""
        return False


class JudgementCritBall:
    """
    Critical sacred glaive pelota for reflected Judgement crit.
    Same as JudgementBall but with lightning bolts striking it during flight.
    Size ~19px diameter with divine lightning effects.
    """

    def __init__(self, start_x, start_y, camera):
        self.size = 19
        # Judgement color palette
        self.color_gold = (255, 215, 0)
        self.color_orange_gold = (255, 153, 68)
        self.color_orange = (255, 102, 0)
        self.color_white = (255, 255, 255)
        self.color_silver = (192, 192, 192)
        self.color_light_silver = (208, 208, 208)
        self.color_dark_gray = (106, 106, 106)

        # Spinning glaive animation
        self.rotation = 0
        self.rotation_speed = 720

        # Golden aura pulsing (more intense than regular)
        self.pulse_timer = 0
        self.pulse_speed = 6  # Faster pulse for crit

        # Orbiting spark particles
        self.spark_count = 8  # More sparks for crit
        self.spark_offset = 0

        # Lightning strike timing
        self.lightning_timer = 0
        self.lightning_interval = 0.25  # Strike every 0.25 seconds
        self.lightning_active = False
        self.lightning_duration = 0.1
        self.lightning_flash_timer = 0

        # Lightning bolt paths (random jagged lines)
        self.lightning_bolts = []

        # Motion trail
        self.trail_positions = []
        self.max_trail_length = 5

        # Position
        self.world_x = start_x
        self.world_y = start_y
        self.camera = camera

        # Animation timing
        self.age = 0

    def move_to(self, world_x, world_y):
        """Move ball to new world position."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        self.trail_positions.append((screen_x, screen_y, 1.0))

        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)

        self.world_x = world_x
        self.world_y = world_y

    def _generate_lightning_bolt(self, start_x, start_y, end_x, end_y):
        """Generate a jagged lightning bolt path."""
        points = [(start_x, start_y)]
        segments = 4

        for i in range(1, segments):
            progress = i / segments
            base_x = start_x + (end_x - start_x) * progress
            base_y = start_y + (end_y - start_y) * progress

            # Add random zigzag
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-5, 5)
            points.append((base_x + offset_x, base_y + offset_y))

        points.append((end_x, end_y))
        return points

    def update(self, dt):
        """Update animation state."""
        self.age += dt

        # Rotate glaive
        self.rotation += self.rotation_speed * dt
        self.rotation %= 360

        # Update pulse timer
        self.pulse_timer += dt * self.pulse_speed

        # Update spark orbit
        self.spark_offset += dt * 3

        # Update lightning timing
        self.lightning_timer += dt
        if self.lightning_timer >= self.lightning_interval:
            self.lightning_timer = 0
            self.lightning_active = True
            self.lightning_flash_timer = self.lightning_duration

            # Generate new lightning bolt striking the ball
            screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

            # Lightning comes from above
            bolt_start_x = screen_x + random.uniform(-20, 20)
            bolt_start_y = screen_y - 40
            self.lightning_bolts = [self._generate_lightning_bolt(bolt_start_x, bolt_start_y, screen_x, screen_y)]

        # Update lightning flash
        if self.lightning_flash_timer > 0:
            self.lightning_flash_timer -= dt
            if self.lightning_flash_timer <= 0:
                self.lightning_active = False
                self.lightning_bolts = []

        # Fade trail
        self.trail_positions = [
            (x, y, alpha * 0.85) for x, y, alpha in self.trail_positions
            if alpha > 0.1
        ]

        return True

    def draw(self, screen):
        """Draw the critical Judgement ball with lightning effects."""
        screen_x = self.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = self.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y

        # Draw golden motion trail
        for i, (tx, ty, alpha) in enumerate(self.trail_positions):
            trail_size = int(self.size * (0.5 + 0.5 * (i / len(self.trail_positions))))
            trail_alpha = int(alpha * 150)  # Brighter trail for crit

            trail_surf = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color_gold, trail_alpha),
                             (trail_size, trail_size), trail_size)
            screen.blit(trail_surf, (int(tx - trail_size), int(ty - trail_size)))

        # More intense pulsing aura for crit
        pulse = 0.7 + 0.3 * math.sin(self.pulse_timer * math.pi * 2)

        # Extra white flash during lightning strike
        if self.lightning_active:
            flash_radius = int(self.size * 2)
            flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            flash_alpha = int(200 * (self.lightning_flash_timer / self.lightning_duration))
            pygame.draw.circle(flash_surf, (*self.color_white, flash_alpha),
                             (flash_radius, flash_radius), flash_radius)
            screen.blit(flash_surf, (int(screen_x - flash_radius), int(screen_y - flash_radius)))

        # Outer glow (gold)
        glow_radius = int(self.size * 1.5 * pulse)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color_gold, int(100 * pulse)),
                         (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surf, (int(screen_x - glow_radius), int(screen_y - glow_radius)))

        # Mid layer (orange-gold)
        mid_radius = int(self.size * 1.2 * pulse)
        mid_surf = pygame.Surface((mid_radius * 2, mid_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(mid_surf, (*self.color_orange_gold, int(150 * pulse)),
                         (mid_radius, mid_radius), mid_radius)
        screen.blit(mid_surf, (int(screen_x - mid_radius), int(screen_y - mid_radius)))

        # Core white energy (brighter for crit)
        core_radius = int(self.size * 0.9)
        core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, (*self.color_white, int(180 * pulse)),
                         (core_radius, core_radius), core_radius)
        screen.blit(core_surf, (int(screen_x - core_radius), int(screen_y - core_radius)))

        # Draw spinning 6-bladed glaive (same as regular)
        glaive_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        center = self.size

        for i in range(6):
            angle_deg = self.rotation + (i * 60)
            angle_rad = math.radians(angle_deg)
            blade_length = self.size * 0.7
            blade_width = self.size * 0.25

            tip_x = center + math.cos(angle_rad) * blade_length
            tip_y = center + math.sin(angle_rad) * blade_length

            perp_angle = angle_rad + math.pi / 2
            base1_x = center + math.cos(perp_angle) * blade_width
            base1_y = center + math.sin(perp_angle) * blade_width
            base2_x = center - math.cos(perp_angle) * blade_width
            base2_y = center - math.sin(perp_angle) * blade_width

            blade_points = [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]
            pygame.draw.polygon(glaive_surf, self.color_dark_gray, blade_points)
            blade_points_silver = [
                (tip_x * 0.95 + center * 0.05, tip_y * 0.95 + center * 0.05),
                (base1_x * 0.9 + center * 0.1, base1_y * 0.9 + center * 0.1),
                (base2_x * 0.9 + center * 0.1, base2_y * 0.9 + center * 0.1)
            ]
            pygame.draw.polygon(glaive_surf, self.color_silver, blade_points_silver)
            pygame.draw.line(glaive_surf, self.color_white,
                           (center, center), (tip_x, tip_y), 1)

        pygame.draw.circle(glaive_surf, self.color_dark_gray, (center, center), int(self.size * 0.25))
        pygame.draw.circle(glaive_surf, self.color_silver, (center, center), int(self.size * 0.2))
        pygame.draw.circle(glaive_surf, self.color_light_silver, (center, center), int(self.size * 0.15))

        screen.blit(glaive_surf, (int(screen_x - self.size), int(screen_y - self.size)))

        # Draw lightning bolts if active
        if self.lightning_active and self.lightning_bolts:
            for bolt_points in self.lightning_bolts:
                # Draw multiple layers for glow effect
                # White outer glow
                for i in range(len(bolt_points) - 1):
                    pygame.draw.line(screen, self.color_white,
                                   bolt_points[i], bolt_points[i + 1], 4)
                # Orange-gold mid layer
                for i in range(len(bolt_points) - 1):
                    pygame.draw.line(screen, self.color_orange_gold,
                                   bolt_points[i], bolt_points[i + 1], 2)
                # Bright white core
                for i in range(len(bolt_points) - 1):
                    pygame.draw.line(screen, self.color_white,
                                   bolt_points[i], bolt_points[i + 1], 1)

        # Electric arcs around ball (when lightning is active)
        if self.lightning_active:
            arc_count = 4
            for i in range(arc_count):
                angle = (i / arc_count) * math.pi * 2
                arc_start_x = screen_x + math.cos(angle) * self.size
                arc_start_y = screen_y + math.sin(angle) * self.size
                arc_end_x = screen_x + math.cos(angle + 0.5) * self.size * 1.3
                arc_end_y = screen_y + math.sin(angle + 0.5) * self.size * 1.3
                pygame.draw.line(screen, self.color_white,
                               (int(arc_start_x), int(arc_start_y)),
                               (int(arc_end_x), int(arc_end_y)), 2)

        # Orbiting golden spark particles (more for crit)
        for i in range(self.spark_count):
            angle = (i / self.spark_count) * math.pi * 2 + self.spark_offset
            spark_distance = self.size * 1.3
            spark_x = screen_x + math.cos(angle) * spark_distance
            spark_y = screen_y + math.sin(angle) * spark_distance
            spark_size = 2
            # Alternate gold and white sparks
            spark_color = self.color_white if i % 2 == 0 else self.color_gold
            pygame.draw.circle(screen, spark_color,
                             (int(spark_x), int(spark_y)), spark_size)

    def is_complete(self):
        """Ball is never complete on its own - controlled by parent animation."""
        return False


class BackhandReflectionAnimation:
    """
    Animation for PELOTARI reflecting a skill back with Backhand counter.

    Phases:
    1. Windup (0.3s) - PELOTARI winds up to serve the reflected ball
    2. Launch (0.2s) - Bright flash as ball launches
    3. Flight (variable) - Ball travels along trajectory with ricochets
    4. Complete - Lingering impact effects

    Duration: ~0.5s + flight time (~0.8-1.5s) = ~1.3-2.0s total
    """

    def __init__(self, caster_unit, target_pos, camera, particle_emitter,
                 screen_shake_callback, screen_flash_callback, game,
                 trajectory=None, skill_name=None, bounce_count=0, is_infused=False, is_crit=False, **kwargs):
        """
        Initialize Backhand reflection animation.

        Args:
            caster_unit: AnimatedUnit (PELOTARI)
            target_pos: (grid_y, grid_x) - not used (uses trajectory instead)
            camera: Camera instance
            particle_emitter: ParticleEmitter
            screen_shake_callback: Function to trigger screen shake
            screen_flash_callback: Function to trigger screen flash
            game: Game instance
            trajectory: List of (grid_y, grid_x) positions ball travels through
            skill_name: Name of reflected skill (determines ball type)
            bounce_count: Number of bounces in trajectory (for impact effects)
            is_infused: Whether skill was infused (for Granite Geas variant)
            is_crit: Whether skill was critical (for Judgement variant)
        """
        print(f"  caster: {caster_unit}")
        print(f"  trajectory: {trajectory}")
        print(f"  skill_name: {skill_name}")
        print(f"  bounce_count: {bounce_count}")
        print(f"  is_infused: {is_infused}")
        print(f"  is_crit: {is_crit}")

        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game
        self.trajectory = trajectory if trajectory else []
        self.skill_name = skill_name
        self.bounce_count = bounce_count
        self.is_infused = is_infused
        self.is_crit = is_crit


        # Get caster world position
        caster_world_x = caster_unit.grid_x * TILE_SIZE + TILE_SIZE // 2
        caster_world_y = caster_unit.grid_y * TILE_SIZE + TILE_SIZE // 2

        # Animation phases
        self.phase = 'windup'  # windup -> launch -> flight -> complete
        self.timer = 0
        self.active = True

        # Create skill-specific ball
        self.ball = self._create_ball(skill_name, caster_world_x, caster_world_y, is_infused, is_crit)
        self.ball_speed = 650  # px/s (slightly slower than Matador for visibility)

        # Trajectory navigation
        self.trajectory_index = 0
        self.current_segment_start = (caster_world_x, caster_world_y)
        self.current_segment_end = None
        self.segment_progress = 0

        if self.trajectory:
            # Set first target
            first_target = self.trajectory[0]
            self.current_segment_end = (
                first_target[1] * TILE_SIZE + TILE_SIZE // 2,
                first_target[0] * TILE_SIZE + TILE_SIZE // 2
            )

        # Impact effects
        self.impact_effects = []  # (world_x, world_y, timer, effect_type)
        self.bounce_positions = []  # Track where bounces occur

        # Windup particles (orbiting charge effect)
        self.windup_particles = []
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            self.windup_particles.append({
                'world_x': caster_world_x,
                'world_y': caster_world_y,
                'angle': angle,
                'radius': 20 + (i % 3) * 5,
                'speed': 2 + (i % 2),
                'size': 3,
                'color': self._get_skill_color(skill_name)
            })

        # Phase durations
        self.windup_duration = 0.3
        self.launch_duration = 0.2

        # Colors
        self.color_royal_blue = (42, 90, 154)
        self.color_white = (255, 255, 255)

    def _create_ball(self, skill_name, start_x, start_y, is_infused=False, is_crit=False):
        """Create skill-specific ball projectile."""
        # Handle Granite Geas infusion variant
        if skill_name == 'Granite Geas':
            ball_class = InfusedGraniteGeasBall if is_infused else GraniteGeasBall
            return ball_class(start_x, start_y, self.camera)

        # Handle Judgement critical variant
        if skill_name == 'Judgement':
            ball_class = JudgementCritBall if is_crit else JudgementBall
            return ball_class(start_x, start_y, self.camera)

        ball_classes = {
            'Estrange': EstrangeBall,
            'Expedite': ExpediteBall,
            'Auction Curse': AuctionCurseBall,
            'Pry': PryBall,
            'Neural Shunt': NeuralShuntBall,
            # TODO: Add other ball classes as they're implemented
            # 'Fragcrest': FragcrestBall,
        }

        ball_class = ball_classes.get(skill_name, EstrangeBall)  # Default to Estrange
        return ball_class(start_x, start_y, self.camera)

    def _get_skill_color(self, skill_name):
        """Get primary color for skill-specific effects."""
        skill_colors = {
            'Judgement': (255, 215, 0),      # Gold (divine)
            'Estrange': (170, 119, 255),     # Purple (reality warp)
            'Neural Shunt': (0, 206, 209),   # Cyan (radio tower signals)
            'Granite Geas': (139, 137, 137), # Gray (stone)
            'Pry': (255, 140, 0),            # Orange (launch force)
            'Auction Curse': (255, 215, 0),  # Gold (cursed wealth)
            'Fragcrest': (255, 69, 0),       # Red-orange (fragmentation)
            'Expedite': (139, 90, 43),       # Brown (mandible rush)
        }
        return skill_colors.get(skill_name, (170, 119, 255))  # Default to Estrange purple

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == 'windup':
            # Update orbiting charge particles
            for p in self.windup_particles:
                p['angle'] += p['speed'] * delta_time
                p['radius'] -= 15 * delta_time  # Particles spiral inward
                if p['radius'] < 5:
                    p['radius'] = 30  # Reset to outer orbit

            # Transition to launch
            if self.timer >= self.windup_duration:
                self.phase = 'launch'
                self.timer = 0

                # Emit launch burst
                screen_x = self.ball.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = self.ball.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if screen_pos:
                    self.particle_emitter.emit_burst(
                        screen_pos[0], screen_pos[1],
                        self._get_skill_color(self.skill_name), count=30
                    )

        elif self.phase == 'launch':
            # Brief flash before flight
            if self.timer >= self.launch_duration:
                self.phase = 'flight'
                self.timer = 0

        elif self.phase == 'flight':
            # Update ball
            self.ball.update(delta_time)

            # Move ball along trajectory
            if self.trajectory_index < len(self.trajectory) and self.current_segment_end:
                # Calculate distance to travel this frame
                distance_to_travel = self.ball_speed * delta_time

                # Get current and target positions
                start_x, start_y = self.current_segment_start
                end_x, end_y = self.current_segment_end

                # Calculate segment length
                dx = end_x - start_x
                dy = end_y - start_y
                segment_length = math.sqrt(dx * dx + dy * dy)

                if segment_length > 0:
                    # Update progress
                    self.segment_progress += distance_to_travel

                    # Check if we reached the target
                    if self.segment_progress >= segment_length:
                        # Reached waypoint
                        self.ball.move_to(end_x, end_y)

                        # Create impact effect at waypoint
                        current_waypoint = self.trajectory[self.trajectory_index]
                        is_final = (self.trajectory_index == len(self.trajectory) - 1)

                        if is_final:
                            self.create_final_explosion(end_x, end_y)
                        else:
                            self.create_ricochet_effect(end_x, end_y)

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
                    else:
                        # Interpolate position
                        t = self.segment_progress / segment_length
                        new_x = start_x + dx * t
                        new_y = start_y + dy * t
                        self.ball.move_to(new_x, new_y)
                else:
                    # Distance is 0 - skip to next segment
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
                        self.phase = 'complete'

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
            if self.timer > 0.4 and len(self.impact_effects) == 0:
                return False

        return True

    def create_ricochet_effect(self, world_x, world_y):
        """Create ricochet impact effect."""
        self.impact_effects.append((world_x, world_y, 0.25, 'ricochet'))

        # Emit particles
        screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if screen_pos:
            self.particle_emitter.emit_burst(
                screen_pos[0], screen_pos[1],
                self._get_skill_color(self.skill_name), count=15
            )

    def create_final_explosion(self, world_x, world_y):
        """Create final impact explosion."""
        self.impact_effects.append((world_x, world_y, 0.4, 'final'))

        # Emit large particle burst
        screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
        screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
        screen_pos = (screen_x, screen_y)
        if screen_pos:
            skill_color = self._get_skill_color(self.skill_name)
            self.particle_emitter.emit_burst(
                screen_pos[0], screen_pos[1],
                skill_color, count=35
            )
            # Add white burst for impact
            self.particle_emitter.emit_burst(
                screen_pos[0], screen_pos[1],
                self.color_white, count=20
            )

        # Screen shake for final impact
        if self.screen_shake_callback:
            self.screen_shake_callback(4, 0.15)

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
            screen_x = self.ball.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.ball.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            screen_pos = (screen_x, screen_y)
            if screen_pos:
                pulse = 0.5 + 0.5 * math.sin(self.timer * 10)
                glow_size = int(35 * pulse)
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                glow_color = self._get_skill_color(self.skill_name)
                pygame.draw.circle(glow_surf, (*glow_color, int(120 * pulse)),
                                 (glow_size, glow_size), glow_size)
                surface.blit(glow_surf, (int(screen_pos[0] - glow_size),
                                        int(screen_pos[1] - glow_size)))

        elif self.phase == 'launch':
            # Bright flash
            screen_x = self.ball.world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
            screen_y = self.ball.world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
            screen_pos = (screen_x, screen_y)
            if screen_pos:
                flash_size = 45
                flash_alpha = int(240 * (1.0 - self.timer / self.launch_duration))
                flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 255, 255, flash_alpha),
                                 (flash_size, flash_size), flash_size)
                surface.blit(flash_surf, (int(screen_pos[0] - flash_size),
                                         int(screen_pos[1] - flash_size)))

        elif self.phase == 'flight' or self.phase == 'complete':
            # Draw the ball
            if self.phase == 'flight':
                self.ball.draw(surface)

            # Draw impact effects
            for world_x, world_y, timer, etype in self.impact_effects:
                screen_x = world_x + self.camera.grid_offset_x + self.camera.shake_offset_x
                screen_y = world_y + self.camera.grid_offset_y + self.camera.shake_offset_y
                screen_pos = (screen_x, screen_y)
                if not screen_pos:
                    continue

                skill_color = self._get_skill_color(self.skill_name)

                if etype == 'ricochet':
                    # Expanding skill-colored ring
                    max_radius = 30
                    duration = 0.25
                    progress = 1.0 - (timer / duration)
                    radius = int(max_radius * progress)
                    alpha = int(140 * (timer / duration))

                    ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (*skill_color, alpha),
                                     (radius, radius), radius, 2)
                    surface.blit(ring_surf, (int(screen_pos[0] - radius),
                                            int(screen_pos[1] - radius)))

                elif etype == 'final':
                    # Large expanding ring + flash
                    max_radius = 50
                    duration = 0.4
                    progress = 1.0 - (timer / duration)
                    radius = int(max_radius * progress)
                    alpha = int(180 * (timer / duration))

                    # Multiple rings
                    for offset in [0, 8, 16]:
                        r = radius - offset
                        if r > 0:
                            a = int(alpha * (1.0 - offset / 16))
                            ring_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                            ring_color = skill_color if offset == 0 else self.color_white
                            pygame.draw.circle(ring_surf, (*ring_color, a),
                                             (r, r), r, 3)
                            surface.blit(ring_surf, (int(screen_pos[0] - r),
                                                    int(screen_pos[1] - r)))
