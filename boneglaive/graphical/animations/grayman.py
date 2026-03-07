#!/usr/bin/env python3
"""
GRAYMAN Animation Classes
Skill animations for the GRAYMAN unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, Particle, DebrisParticle
from boneglaive.graphical.sound_helper import play_sound


class DeltaConfigAnimation:
    """
    Teleportation animation that 'pulls' the destination point toward the caster,
    then snaps to the destination. Represents bending space-time.

    When upgraded: Abducts all adjacent enemies and synchronizes their animations
    with the GRAYMAN's teleport.
    """

    def __init__(self, caster_unit, target_pos, particle_emitter, camera=None, game=None, units_list=None):
        """
        Args:
            caster_unit: AnimatedUnit teleporting
            target_pos: Target grid position (grid_x, grid_y)
            particle_emitter: ParticleEmitter for spawning particles
            camera: Camera instance for coordinate conversion (optional)
            game: Game instance for checking upgrade status
            units_list: List of all AnimatedUnits (for enemy abduction)
        """
        self.caster_unit = caster_unit
        # NOTE: target_pos is (grid_y, grid_x) format from renderer - UNPACK CORRECTLY!
        self.target_grid_y, self.target_grid_x = target_pos
        self.particle_emitter = particle_emitter
        self.camera = camera
        self.game = game
        self.units_list = units_list if units_list else []

        # Check if skill is upgraded
        self.is_upgraded = False
        if game and hasattr(caster_unit, 'game_unit') and caster_unit.game_unit:
            from boneglaive.game.upgrades import UpgradeManager
            self.is_upgraded = UpgradeManager.is_skill_upgraded(caster_unit.game_unit, "Delta Config")

        # Convert grid to screen coordinates using camera
        self.source_x = caster_unit.x
        self.source_y = caster_unit.y
        self.source_grid_x = caster_unit.grid_x
        self.source_grid_y = caster_unit.grid_y

        if self.camera:
            self.target_x, self.target_y = self.camera.grid_to_screen(self.target_grid_x, self.target_grid_y)
        else:
            # Fallback to defaults
            GRID_OFFSET_X = 100
            GRID_OFFSET_Y = 50
            self.target_x = GRID_OFFSET_X + self.target_grid_x * TILE_SIZE + TILE_SIZE // 2
            self.target_y = GRID_OFFSET_Y + self.target_grid_y * TILE_SIZE + TILE_SIZE // 2

        # Collect abducted enemies if upgraded
        self.abducted_enemies = []
        if self.is_upgraded:
            self._collect_abducted_enemies()

        # Animation phases
        self.phase = "energize"  # energize, pull, hold, snap, appear
        self.timer = 0
        self.energize_duration = 0.4
        self.pull_duration = 0.6
        self.hold_duration = 0.15
        self.snap_duration = 0.1
        self.appear_duration = 0.3

        # Purple/lavender colors from Grayman's orbs
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_bright = (255, 255, 255)

        # Pull chain - points along the path from source to target
        self.pull_chain = []
        self.pull_progress = 0  # How much of the chain has been "pulled"

        # Calculate pull chain points
        dx = self.target_x - self.source_x
        dy = self.target_y - self.source_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            num_points = int(distance / 15) + 2  # Point every 15 pixels
            for i in range(num_points):
                t = i / (num_points - 1) if num_points > 1 else 0
                x = self.source_x + dx * t
                y = self.source_y + dy * t
                self.pull_chain.append((x, y))

        # Create pull chains for abducted enemies
        self.enemy_pull_chains = []
        for enemy_data in self.abducted_enemies:
            enemy_unit = enemy_data['unit']
            enemy_chain = []

            # Calculate enemy's target position (maintaining relative offset)
            enemy_target_x, enemy_target_y = self._calculate_enemy_target_screen(enemy_data)

            # Calculate pull chain for this enemy
            dx_enemy = enemy_target_x - enemy_unit.x
            dy_enemy = enemy_target_y - enemy_unit.y
            dist_enemy = math.sqrt(dx_enemy*dx_enemy + dy_enemy*dy_enemy)

            if dist_enemy > 0:
                num_pts = int(dist_enemy / 15) + 2
                for i in range(num_pts):
                    t = i / (num_pts - 1) if num_pts > 1 else 0
                    x = enemy_unit.x + dx_enemy * t
                    y = enemy_unit.y + dy_enemy * t
                    enemy_chain.append((x, y))

            self.enemy_pull_chains.append({
                'unit': enemy_unit,
                'chain': enemy_chain,
                'source_x': enemy_unit.x,
                'source_y': enemy_unit.y,
                'target_x': enemy_target_x,
                'target_y': enemy_target_y,
                'relative_offset': enemy_data['relative_offset']
            })

        # Electromagnetic well state (upgraded only)
        self.well_tiles = []  # List of 8 adjacent tile positions (screen coords)
        if self.is_upgraded and self.camera:
            # Calculate 3x3 grid around source (excluding center)
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dy, dx in offsets:
                well_x, well_y = self.camera.grid_to_screen(
                    self.source_grid_x + dx,
                    self.source_grid_y + dy,
                    centered=True
                )
                self.well_tiles.append((well_x, well_y))

        # Flags
        self.energize_particles_spawned = False
        self.snap_particles_spawned = False
        self.teleported = False

    def _collect_abducted_enemies(self):
        """Collect all adjacent enemy units for upgraded Delta Config."""
        if not hasattr(self.caster_unit, 'game_unit') or not self.caster_unit.game_unit:
            return

        caster_player = self.caster_unit.game_unit.player

        # Check all 8 adjacent positions
        adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for animated_unit in self.units_list:
            if not hasattr(animated_unit, 'game_unit') or not animated_unit.game_unit:
                continue

            # Check if enemy (different player) and adjacent to caster
            if animated_unit.game_unit.player != caster_player:
                dy = animated_unit.grid_y - self.source_grid_y
                dx = animated_unit.grid_x - self.source_grid_x

                if (dy, dx) in adjacent_offsets:
                    self.abducted_enemies.append({
                        'unit': animated_unit,
                        'relative_offset': (dy, dx)  # Store relative position
                    })

    def _calculate_enemy_target_screen(self, enemy_data):
        """Calculate screen position where enemy should end up (maintaining relative offset)."""
        dy, dx = enemy_data['relative_offset']
        target_grid_y = self.target_grid_y + dy
        target_grid_x = self.target_grid_x + dx

        if self.camera:
            return self.camera.grid_to_screen(target_grid_x, target_grid_y)
        else:
            # Fallback
            GRID_OFFSET_X = 100
            GRID_OFFSET_Y = 50
            screen_x = GRID_OFFSET_X + target_grid_x * TILE_SIZE + TILE_SIZE // 2
            screen_y = GRID_OFFSET_Y + target_grid_y * TILE_SIZE + TILE_SIZE // 2
            return screen_x, screen_y

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == "energize":
            # Charging up at origin
            if not self.energize_particles_spawned:
                play_sound("delta_config_energize")

                # Spawn energizing particles
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(30, 60)
                    x = self.source_x + math.cos(angle) * distance
                    y = self.source_y + math.sin(angle) * distance
                    # Particles move toward center
                    vx = -math.cos(angle) * 100
                    vy = -math.sin(angle) * 100
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(x, y, vx, vy, lifetime=0.4, size=4, color=color)
                    self.particle_emitter.particles.append(particle)
                self.energize_particles_spawned = True

            if self.timer >= self.energize_duration:
                self.phase = "pull"
                self.timer = 0
                play_sound("delta_config_pull")

        elif self.phase == "pull":
            # Pull destination toward origin
            progress = self.timer / self.pull_duration
            self.pull_progress = min(1.0, progress)

            # Spawn particles along the pull chain
            if random.random() < 0.3 and len(self.pull_chain) > 0:
                idx = int(self.pull_progress * len(self.pull_chain) * 0.8)
                if idx < len(self.pull_chain):
                    x, y = self.pull_chain[idx]
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(x, y, 0, 0, lifetime=0.2, size=3, color=color)
                    self.particle_emitter.particles.append(particle)

            if self.timer >= self.pull_duration:
                self.phase = "hold"
                self.timer = 0

        elif self.phase == "hold":
            # Brief pause at full tension
            if self.timer >= self.hold_duration:
                self.phase = "snap"
                self.timer = 0
                play_sound("delta_config_snap")

        elif self.phase == "snap":
            # Instant snapback - unit disappears from origin
            if not self.teleported:
                # Hide caster temporarily (will reappear at target)
                self.caster_unit.visible = False

                # Hide abducted enemies if upgraded
                if self.is_upgraded:
                    for enemy_chain in self.enemy_pull_chains:
                        enemy_chain['unit'].visible = False

                self.teleported = True

            if self.timer >= self.snap_duration:
                self.phase = "appear"
                self.timer = 0

        elif self.phase == "appear":
            # Appear at destination
            if not self.snap_particles_spawned:
                play_sound("delta_config_appear")

                # Move caster to target position
                self.caster_unit.grid_x = self.target_grid_x
                self.caster_unit.grid_y = self.target_grid_y
                self.caster_unit.x = self.target_x
                self.caster_unit.y = self.target_y
                self.caster_unit.visible = True

                # Move abducted enemies to their target positions if upgraded
                if self.is_upgraded:
                    for enemy_chain in self.enemy_pull_chains:
                        enemy_unit = enemy_chain['unit']
                        dy, dx = enemy_chain['relative_offset']

                        # Update grid position
                        enemy_unit.grid_x = self.target_grid_x + dx
                        enemy_unit.grid_y = self.target_grid_y + dy

                        # Update screen position
                        enemy_unit.x = enemy_chain['target_x']
                        enemy_unit.y = enemy_chain['target_y']
                        enemy_unit.visible = True

                        # Spawn arrival particles for each enemy
                        for _ in range(15):  # Fewer particles per enemy
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(80, 200)
                            vx = math.cos(angle) * speed
                            vy = math.sin(angle) * speed
                            color = random.choice([self.color_outer, self.color_inner])
                            particle = Particle(enemy_unit.x, enemy_unit.y, vx, vy,
                                              lifetime=0.4, size=4, color=color)
                            self.particle_emitter.particles.append(particle)

                # Spawn arrival particles for caster
                for _ in range(30):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(80, 200)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_outer, self.color_inner, self.color_bright])
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.5, size=5, color=color)
                    self.particle_emitter.particles.append(particle)

                # Ring of particles expanding outward
                for i in range(12):
                    angle = (i / 12) * 2 * math.pi
                    vx = math.cos(angle) * 150
                    vy = math.sin(angle) * 150
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.4, size=4, color=self.color_inner)
                    self.particle_emitter.particles.append(particle)

                self.snap_particles_spawned = True

            if self.timer >= self.appear_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the Delta Config animation."""
        if self.phase == "energize":
            # Draw energizing glow at source
            progress = self.timer / self.energize_duration

            # Pulsing outer glow
            glow_radius = int(20 + 10 * math.sin(self.timer * 15))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_outer, int(120 * progress)),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Inner glow
            inner_radius = int(glow_radius * 0.6)
            glow_surf2 = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf2, (*self.color_inner, int(180 * progress)),
                             (inner_radius, inner_radius), inner_radius)
            surface.blit(glow_surf2, (int(self.source_x - inner_radius),
                                     int(self.source_y - inner_radius)))

            # Draw delta symbol at source
            # Draw a triangle (delta shape)
            size = int(15 * progress)
            if size > 3:
                points = [
                    (int(self.source_x), int(self.source_y - size)),
                    (int(self.source_x - size * 0.866), int(self.source_y + size * 0.5)),
                    (int(self.source_x + size * 0.866), int(self.source_y + size * 0.5))
                ]
                pygame.draw.polygon(surface, self.color_bright, points, 2)

            # Draw expanding electromagnetic well (upgraded only)
            if self.is_upgraded:
                # Draw expanding electromagnetic field (bubble effect)
                well_progress = min(1.0, progress * 1.5)  # Faster expansion
                for tile_x, tile_y in self.well_tiles:
                    # Expanding circles on each adjacent tile
                    well_radius = int(TILE_SIZE * 0.3 * well_progress)
                    if well_radius > 2:
                        well_surf = pygame.Surface((well_radius * 2, well_radius * 2), pygame.SRCALPHA)
                        alpha = int(100 * well_progress)
                        pygame.draw.circle(well_surf, (*self.color_outer, alpha),
                                         (well_radius, well_radius), well_radius, 2)
                        surface.blit(well_surf, (int(tile_x - well_radius), int(tile_y - well_radius)))

        elif self.phase == "pull":
            # Draw pulsing energy at source
            pulse = 0.8 + 0.2 * math.sin(self.timer * 20)
            glow_radius = int(15 * pulse)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_inner, 150),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Draw the pull chain - line from target toward source
            if len(self.pull_chain) > 1:
                visible_points = int(len(self.pull_chain) * self.pull_progress)
                if visible_points > 1:
                    # Draw line segments from target backwards toward source
                    for i in range(len(self.pull_chain) - 1, max(len(self.pull_chain) - visible_points, 0), -1):
                        if i > 0:
                            x1, y1 = self.pull_chain[i]
                            x2, y2 = self.pull_chain[i - 1]

                            # Fade effect based on distance from target
                            fade = (i / len(self.pull_chain))
                            alpha = int(200 * fade)

                            # Draw thick line
                            pygame.draw.line(surface, (*self.color_outer, alpha),
                                          (int(x1), int(y1)), (int(x2), int(y2)), 4)
                            # Draw thin inner line
                            pygame.draw.line(surface, self.color_inner,
                                          (int(x1), int(y1)), (int(x2), int(y2)), 2)

            # Draw pull chains for abducted enemies if upgraded
            if self.is_upgraded:
                for enemy_chain_data in self.enemy_pull_chains:
                    enemy_chain = enemy_chain_data['chain']
                    enemy_unit = enemy_chain_data['unit']
                    enemy_source_x = enemy_chain_data['source_x']
                    enemy_source_y = enemy_chain_data['source_y']
                    enemy_target_x = enemy_chain_data['target_x']
                    enemy_target_y = enemy_chain_data['target_y']

                    # Draw pulsing energy at enemy source
                    enemy_glow_radius = int(12 * pulse)
                    enemy_glow_surf = pygame.Surface((enemy_glow_radius * 2, enemy_glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(enemy_glow_surf, (*self.color_outer, 120),
                                     (enemy_glow_radius, enemy_glow_radius), enemy_glow_radius)
                    surface.blit(enemy_glow_surf, (int(enemy_source_x - enemy_glow_radius),
                                                  int(enemy_source_y - enemy_glow_radius)))

                    # Draw enemy pull chain
                    if len(enemy_chain) > 1:
                        visible_points_enemy = int(len(enemy_chain) * self.pull_progress)
                        if visible_points_enemy > 1:
                            for i in range(len(enemy_chain) - 1, max(len(enemy_chain) - visible_points_enemy, 0), -1):
                                if i > 0:
                                    x1, y1 = enemy_chain[i]
                                    x2, y2 = enemy_chain[i - 1]

                                    # Fade effect
                                    fade = (i / len(enemy_chain))
                                    alpha = int(180 * fade)  # Slightly dimmer than main chain

                                    # Draw thinner lines for enemies
                                    pygame.draw.line(surface, (*self.color_outer, alpha),
                                                  (int(x1), int(y1)), (int(x2), int(y2)), 3)
                                    pygame.draw.line(surface, (*self.color_inner, alpha),
                                                  (int(x1), int(y1)), (int(x2), int(y2)), 1)

                    # Draw small glow at enemy target
                    enemy_target_glow = int(8 * self.pull_progress)
                    if enemy_target_glow > 2:
                        enemy_target_glow_surf = pygame.Surface((enemy_target_glow * 2, enemy_target_glow * 2), pygame.SRCALPHA)
                        pygame.draw.circle(enemy_target_glow_surf, (*self.color_outer, 100),
                                         (enemy_target_glow, enemy_target_glow), enemy_target_glow)
                        surface.blit(enemy_target_glow_surf, (int(enemy_target_x - enemy_target_glow),
                                                             int(enemy_target_y - enemy_target_glow)))

            # Draw electromagnetic well moving during pull (upgraded only)
            if self.is_upgraded:
                # Draw electromagnetic well moving with pull progress
                # Interpolate well position from source to target
                offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for i, (source_tile_x, source_tile_y) in enumerate(self.well_tiles):
                    # Calculate corresponding target tile position
                    dy, dx = offsets[i]
                    if self.camera:
                        target_tile_x, target_tile_y = self.camera.grid_to_screen(
                            self.target_grid_x + dx,
                            self.target_grid_y + dy,
                            centered=True
                        )
                    else:
                        target_tile_x = self.target_x + dx * TILE_SIZE
                        target_tile_y = self.target_y + dy * TILE_SIZE

                    # Interpolate position based on pull progress
                    interp_x = source_tile_x + (target_tile_x - source_tile_x) * self.pull_progress
                    interp_y = source_tile_y + (target_tile_y - source_tile_y) * self.pull_progress

                    # Draw pulsing hexagonal well boundary
                    hex_radius = int(TILE_SIZE * 0.35)
                    hex_points = []
                    for angle_i in range(6):
                        angle = (angle_i / 6) * 2 * math.pi + self.timer * 2  # Rotating
                        px = interp_x + math.cos(angle) * hex_radius
                        py = interp_y + math.sin(angle) * hex_radius
                        hex_points.append((int(px), int(py)))

                    # Draw hexagon outline with pulsing alpha
                    alpha = int(120 + 50 * math.sin(self.timer * 10))
                    pygame.draw.polygon(surface, (*self.color_outer, alpha), hex_points, 2)

                    # Inner glow
                    inner_glow_surf = pygame.Surface((hex_radius * 2, hex_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(inner_glow_surf, (*self.color_inner, 60),
                                     (hex_radius, hex_radius), hex_radius)
                    surface.blit(inner_glow_surf, (int(interp_x - hex_radius), int(interp_y - hex_radius)))

            # Draw small glow at target
            target_glow = int(10 * self.pull_progress)
            if target_glow > 2:
                glow_surf3 = pygame.Surface((target_glow * 2, target_glow * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf3, (*self.color_outer, 120),
                                 (target_glow, target_glow), target_glow)
                surface.blit(glow_surf3, (int(self.target_x - target_glow),
                                         int(self.target_y - target_glow)))

        elif self.phase == "hold":
            # Draw full tension - bright line from source to target
            pygame.draw.line(surface, self.color_bright,
                          (int(self.source_x), int(self.source_y)),
                          (int(self.target_x), int(self.target_y)), 3)

            # Draw lines for abducted enemies if upgraded
            if self.is_upgraded:
                for enemy_chain_data in self.enemy_pull_chains:
                    enemy_source_x = enemy_chain_data['source_x']
                    enemy_source_y = enemy_chain_data['source_y']
                    enemy_target_x = enemy_chain_data['target_x']
                    enemy_target_y = enemy_chain_data['target_y']

                    # Draw bright line for each enemy
                    pygame.draw.line(surface, (*self.color_inner, 200),
                                  (int(enemy_source_x), int(enemy_source_y)),
                                  (int(enemy_target_x), int(enemy_target_y)), 2)

            # Pulsing glow at both ends
            pulse = 0.7 + 0.3 * math.sin(self.timer * 30)
            for x, y in [(self.source_x, self.source_y), (self.target_x, self.target_y)]:
                glow_radius = int(15 * pulse)
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_bright, 200),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(x - glow_radius), int(y - glow_radius)))

            # Pulsing glows at enemy endpoints if upgraded
            if self.is_upgraded:
                for enemy_chain_data in self.enemy_pull_chains:
                    for x, y in [(enemy_chain_data['source_x'], enemy_chain_data['source_y']),
                                 (enemy_chain_data['target_x'], enemy_chain_data['target_y'])]:
                        glow_radius = int(12 * pulse)
                        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*self.color_inner, 150),
                                         (glow_radius, glow_radius), glow_radius)
                        surface.blit(glow_surf, (int(x - glow_radius), int(y - glow_radius)))

            # Draw electromagnetic field at maximum tension (upgraded only)
            if self.is_upgraded:
                offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for i, (source_tile_x, source_tile_y) in enumerate(self.well_tiles):
                    dy, dx = offsets[i]
                    if self.camera:
                        target_tile_x, target_tile_y = self.camera.grid_to_screen(
                            self.target_grid_x + dx, self.target_grid_y + dy, centered=True
                        )
                    else:
                        target_tile_x = self.target_x + dx * TILE_SIZE
                        target_tile_y = self.target_y + dy * TILE_SIZE

                    # Well stretched between source and target
                    pygame.draw.line(surface, (*self.color_inner, 150),
                                    (int(source_tile_x), int(source_tile_y)),
                                    (int(target_tile_x), int(target_tile_y)), 1)

                    # Pulsing nodes at both ends
                    for pos_x, pos_y in [(source_tile_x, source_tile_y), (target_tile_x, target_tile_y)]:
                        node_radius = int(8 * pulse)
                        node_surf = pygame.Surface((node_radius * 2, node_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(node_surf, (*self.color_bright, 180),
                                         (node_radius, node_radius), node_radius)
                        surface.blit(node_surf, (int(pos_x - node_radius), int(pos_y - node_radius)))

        elif self.phase == "appear":
            # Draw arrival flash at destination
            progress = self.timer / self.appear_duration
            if progress < 0.5:
                flash_alpha = int(255 * (1.0 - progress / 0.5))
                flash_radius = int(40 * (1.0 + progress * 2))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_bright, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(self.target_x - flash_radius),
                                         int(self.target_y - flash_radius)))

            # Draw delta symbol at target
            size = int(20 * (1.0 - progress))
            if size > 3:
                points = [
                    (int(self.target_x), int(self.target_y - size)),
                    (int(self.target_x - size * 0.866), int(self.target_y + size * 0.5)),
                    (int(self.target_x + size * 0.866), int(self.target_y + size * 0.5))
                ]
                alpha = int(255 * (1.0 - progress))
                pygame.draw.polygon(surface, (*self.color_inner, alpha), points, 3)

            # Draw collapsing electromagnetic well at destination (upgraded only)
            if self.is_upgraded:
                # Draw collapsing electromagnetic well at destination
                collapse_progress = progress  # 0 to 1 over appear_duration
                offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

                for i in range(len(offsets)):
                    dy, dx = offsets[i]
                    if self.camera:
                        dest_tile_x, dest_tile_y = self.camera.grid_to_screen(
                            self.target_grid_x + dx, self.target_grid_y + dy, centered=True
                        )
                    else:
                        dest_tile_x = self.target_x + dx * TILE_SIZE
                        dest_tile_y = self.target_y + dy * TILE_SIZE

                    # Collapsing circle effect (shrinks from full size to nothing)
                    collapse_radius = int(TILE_SIZE * 0.4 * (1.0 - collapse_progress))
                    if collapse_radius > 2:
                        collapse_surf = pygame.Surface((collapse_radius * 2, collapse_radius * 2), pygame.SRCALPHA)
                        alpha = int(150 * (1.0 - collapse_progress))  # Fades as it shrinks
                        pygame.draw.circle(collapse_surf, (*self.color_outer, alpha),
                                         (collapse_radius, collapse_radius), collapse_radius, 2)

                        # Inner fill that pulses
                        fill_alpha = int(80 * (1.0 - collapse_progress) * (0.5 + 0.5 * math.sin(self.timer * 20)))
                        pygame.draw.circle(collapse_surf, (*self.color_inner, fill_alpha),
                                         (collapse_radius, collapse_radius), collapse_radius)

                        surface.blit(collapse_surf, (int(dest_tile_x - collapse_radius),
                                                    int(dest_tile_y - collapse_radius)))

                # Add shockwave burst at 50% collapse
                if 0.45 < collapse_progress < 0.55:
                    shockwave_radius = int(TILE_SIZE * 1.5)
                    for i in range(len(offsets)):
                        dy, dx = offsets[i]
                        if self.camera:
                            dest_tile_x, dest_tile_y = self.camera.grid_to_screen(
                                self.target_grid_x + dx, self.target_grid_y + dy, centered=True
                            )
                        else:
                            dest_tile_x = self.target_x + dx * TILE_SIZE
                            dest_tile_y = self.target_y + dy * TILE_SIZE

                        shockwave_surf = pygame.Surface((shockwave_radius * 2, shockwave_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(shockwave_surf, (*self.color_bright, 100),
                                         (shockwave_radius, shockwave_radius), shockwave_radius, 3)
                        surface.blit(shockwave_surf, (int(dest_tile_x - shockwave_radius),
                                                     int(dest_tile_y - shockwave_radius)))


class GraeExchangeAnimation:
    """
    Græ Exchange animation - banish target enemy and replace with echo.
    Reality-tearing beam that banishes the target and spawns a GRAYMAN echo.
    """

    def __init__(self, caster_unit, target_pos, particle_emitter, camera=None, game=None, units_list=None):
        """
        Args:
            caster_unit: AnimatedUnit performing the exchange
            target_pos: Target grid position (grid_y, grid_x)
            particle_emitter: ParticleEmitter for spawning particles
            camera: Camera instance for coordinate conversion (optional)
            game: Game instance (optional)
            units_list: List of units (optional)
        """
        self.caster_unit = caster_unit
        # NOTE: target_pos is (grid_y, grid_x) format from renderer - UNPACK CORRECTLY!
        self.target_grid_y, self.target_grid_x = target_pos
        self.particle_emitter = particle_emitter
        self.camera = camera

        # Get caster's game logic unit to use its actual position (post-move)
        # The AnimatedUnit's grid_x/y might not be updated yet, so use the game unit's position
        if hasattr(caster_unit, 'game_unit') and caster_unit.game_unit:
            # Use game unit's actual position (post-move)
            caster_grid_x = caster_unit.game_unit.x
            caster_grid_y = caster_unit.game_unit.y
            # Convert grid to screen coordinates using camera
            if self.camera:
                self.source_x, self.source_y = self.camera.grid_to_screen(caster_grid_x, caster_grid_y, centered=True)
            else:
                # Fallback to defaults
                GRID_OFFSET_X = 100
                GRID_OFFSET_Y = 50
                self.source_x = GRID_OFFSET_X + caster_grid_x * TILE_SIZE + TILE_SIZE // 2
                self.source_y = GRID_OFFSET_Y + caster_grid_y * TILE_SIZE + TILE_SIZE // 2
        else:
            # Fall back to AnimatedUnit's screen position
            self.source_x = caster_unit.x
            self.source_y = caster_unit.y

        # Convert target position to screen coordinates
        if self.camera:
            self.target_x, self.target_y = self.camera.grid_to_screen(self.target_grid_x, self.target_grid_y, centered=True)
        else:
            # Fallback to defaults
            GRID_OFFSET_X = 100
            GRID_OFFSET_Y = 50
            self.target_x = GRID_OFFSET_X + self.target_grid_x * TILE_SIZE + TILE_SIZE // 2
            self.target_y = GRID_OFFSET_Y + self.target_grid_y * TILE_SIZE + TILE_SIZE // 2

        # Animation phases - keeping same total duration (1.4s) for sound sync
        self.phase = "charge"  # charge, beam, banish, echo_spawn
        self.timer = 0
        self.charge_duration = 0.4  # Same as old ritual duration
        self.beam_duration = 0.5    # Same as old split duration
        self.banish_duration = 0.3   # Combines old teleport_out + part of in
        self.echo_spawn_duration = 0.2  # Remaining time

        # Purple/lavender colors from Grayman's orbs
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_bright = (255, 255, 255)
        self.color_cloak = (74, 74, 90)     # #4a4a5a - Cloak fabric
        self.color_skin = (154, 154, 170)   # #9a9aaa - Gray skin

        # Beam effect properties
        self.beam_width = 0
        self.max_beam_width = 15

        # Flags
        self.charge_particles_spawned = False
        self.beam_particles_spawned = False
        self.banish_particles_spawned = False
        self.echo_particles_spawned = False

    def update(self, delta_time):
        """Update animation state."""
        self.timer += delta_time

        if self.phase == "charge":
            # Charge phase - building energy at caster
            if not self.charge_particles_spawned:
                play_sound("grae_exchange_ritual")  # Keep same sound timing

                # Spawn charging particles at caster
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(30, 60)
                    x = self.source_x + math.cos(angle) * distance
                    y = self.source_y + math.sin(angle) * distance
                    # Particles move toward center
                    vx = -math.cos(angle) * 100
                    vy = -math.sin(angle) * 100
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(x, y, vx, vy, lifetime=0.4, size=4, color=color)
                    self.particle_emitter.particles.append(particle)
                self.charge_particles_spawned = True

            if self.timer >= self.charge_duration:
                self.phase = "beam"
                self.timer = 0
                play_sound("grae_exchange_split")  # Keep same sound timing

        elif self.phase == "beam":
            # Beam phase - fire reality-tearing beam at target
            progress = self.timer / self.beam_duration
            self.beam_width = self.max_beam_width * min(1.0, progress * 2)

            # Spawn beam particles along path
            if random.random() < 0.4:
                t = random.uniform(0.2, 0.8)
                x = self.source_x + (self.target_x - self.source_x) * t
                y = self.source_y + (self.target_y - self.source_y) * t

                # Add perpendicular offset for beam width
                dx = self.target_x - self.source_x
                dy = self.target_y - self.source_y
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length
                    perp_y = dx / length
                    offset = random.uniform(-20, 20)
                    x += perp_x * offset
                    y += perp_y * offset

                color = random.choice([self.color_outer, self.color_inner, self.color_cloak])
                particle = Particle(x, y, 0, 0, lifetime=0.3, size=4, color=color)
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.beam_duration:
                self.phase = "banish"
                self.timer = 0
                play_sound("grae_exchange_teleport")  # Keep same sound timing

        elif self.phase == "banish":
            # Banish phase - target implodes and vanishes
            if not self.banish_particles_spawned:
                # Implosion particles - move inward
                for i in range(30):
                    angle = (i / 30) * 2 * math.pi
                    distance = random.uniform(40, 80)
                    x = self.target_x + math.cos(angle) * distance
                    y = self.target_y + math.sin(angle) * distance
                    # Particles move toward center
                    vx = -math.cos(angle) * 150
                    vy = -math.sin(angle) * 150
                    color = random.choice([self.color_outer, self.color_inner, self.color_skin])
                    particle = Particle(x, y, vx, vy, lifetime=0.4, size=5, color=color)
                    self.particle_emitter.particles.append(particle)

                self.banish_particles_spawned = True

            if self.timer >= self.banish_duration:
                self.phase = "echo_spawn"
                self.timer = 0

        elif self.phase == "echo_spawn":
            # Echo spawn phase - purple materialization at target position
            if not self.echo_particles_spawned:
                # Spawn materialization particles
                for _ in range(25):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_outer, self.color_inner, self.color_bright])
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.4, size=4, color=color)
                    self.particle_emitter.particles.append(particle)

                # Ring of particles expanding
                for i in range(12):
                    angle = (i / 12) * 2 * math.pi
                    vx = math.cos(angle) * 100
                    vy = math.sin(angle) * 100
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.3, size=3, color=self.color_inner)
                    self.particle_emitter.particles.append(particle)

                self.echo_particles_spawned = True

            if self.timer >= self.echo_spawn_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the Græ Exchange animation."""
        if self.phase == "charge":
            # Draw charging glow at caster
            progress = self.timer / self.charge_duration

            # Pulsing glow
            glow_radius = int(20 + 10 * math.sin(self.timer * 15))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_outer, int(120 * progress)),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Inner glow
            inner_radius = int(glow_radius * 0.6)
            glow_surf2 = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf2, (*self.color_inner, int(180 * progress)),
                             (inner_radius, inner_radius), inner_radius)
            surface.blit(glow_surf2, (int(self.source_x - inner_radius),
                                     int(self.source_y - inner_radius)))

            # Draw psi symbol at source
            size = int(15 * progress)
            if size > 3:
                # Draw triangular psi shape
                points = [
                    (int(self.source_x), int(self.source_y - size)),
                    (int(self.source_x - size * 0.5), int(self.source_y + size * 0.3)),
                    (int(self.source_x + size * 0.5), int(self.source_y + size * 0.3))
                ]
                pygame.draw.lines(surface, self.color_bright, False, points, 2)

        elif self.phase == "beam":
            # Draw reality-tearing beam
            progress = self.timer / self.beam_duration

            if self.beam_width > 2:
                # Calculate beam direction
                dx = self.target_x - self.source_x
                dy = self.target_y - self.source_y
                distance = math.sqrt(dx*dx + dy*dy)

                if distance > 0:
                    # Draw thick outer beam with pulsing
                    pulse = 0.7 + 0.3 * math.sin(self.timer * 20)

                    # Outer purple beam
                    pygame.draw.line(surface, tuple(int(c * pulse) for c in self.color_outer),
                                  (int(self.source_x), int(self.source_y)),
                                  (int(self.target_x), int(self.target_y)),
                                  int(self.beam_width))

                    # Inner lighter beam
                    pygame.draw.line(surface, tuple(int(c * pulse) for c in self.color_inner),
                                  (int(self.source_x), int(self.source_y)),
                                  (int(self.target_x), int(self.target_y)),
                                  int(self.beam_width * 0.6))

                    # Bright core
                    pygame.draw.line(surface, self.color_bright,
                                  (int(self.source_x), int(self.source_y)),
                                  (int(self.target_x), int(self.target_y)), 2)

                    # Reality tear effect - jagged lines alongside beam
                    perpendicular_x = -dy / distance
                    perpendicular_y = dx / distance

                    for i in range(3):
                        offset = (i - 1) * 25
                        tear_x1 = self.source_x + perpendicular_x * offset
                        tear_y1 = self.source_y + perpendicular_y * offset
                        tear_x2 = self.target_x + perpendicular_x * offset
                        tear_y2 = self.target_y + perpendicular_y * offset

                        # Draw jagged line
                        num_segments = 8
                        points = []
                        for j in range(num_segments + 1):
                            t = j / num_segments
                            x = tear_x1 + (tear_x2 - tear_x1) * t
                            y = tear_y1 + (tear_y2 - tear_y1) * t
                            # Add random offset for jaggedness
                            jitter = math.sin(t * math.pi * 3 + self.timer * 10) * 5
                            x += perpendicular_x * jitter
                            y += perpendicular_y * jitter
                            points.append((int(x), int(y)))

                        if len(points) >= 2:
                            pygame.draw.lines(surface, self.color_cloak, False, points, 1)

        elif self.phase == "banish":
            # Draw implosion at target
            progress = self.timer / self.banish_duration

            # Collapsing vortex
            vortex_radius = int(40 * (1.0 - progress))
            if vortex_radius > 2:
                # Draw spiral
                num_spirals = 3
                for spiral in range(num_spirals):
                    points = []
                    for i in range(20):
                        angle = (i / 20) * 2 * math.pi + (spiral * 2 * math.pi / num_spirals) + self.timer * 10
                        r = vortex_radius * (1.0 - i / 20)
                        x = self.target_x + math.cos(angle) * r
                        y = self.target_y + math.sin(angle) * r
                        points.append((int(x), int(y)))

                    if len(points) >= 2:
                        color = self.color_outer if spiral % 2 == 0 else self.color_inner
                        pygame.draw.lines(surface, color, False, points, 2)

                # Central void
                void_radius = int(15 * progress)
                if void_radius > 0:
                    void_surf = pygame.Surface((void_radius * 2, void_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(void_surf, (0, 0, 0, int(200 * progress)),
                                     (void_radius, void_radius), void_radius)
                    surface.blit(void_surf, (int(self.target_x - void_radius),
                                            int(self.target_y - void_radius)))

        elif self.phase == "echo_spawn":
            # Draw echo materialization
            progress = self.timer / self.echo_spawn_duration

            # Growing echo form
            echo_radius = int(25 * progress)
            if echo_radius > 2:
                echo_surf = pygame.Surface((echo_radius * 2, echo_radius * 2), pygame.SRCALPHA)

                # Outer glow
                pygame.draw.circle(echo_surf, (*self.color_outer, int(100 * progress)),
                                 (echo_radius, echo_radius), echo_radius)

                # Inner form
                inner_radius = int(echo_radius * 0.6)
                pygame.draw.circle(echo_surf, (*self.color_inner, int(150 * progress)),
                                 (echo_radius, echo_radius), inner_radius)

                surface.blit(echo_surf, (int(self.target_x - echo_radius),
                                        int(self.target_y - echo_radius)))

            # Psi symbol forming
            if progress > 0.5:
                symbol_alpha = int((progress - 0.5) * 2 * 255)
                symbol_size = 15
                points = [
                    (int(self.target_x), int(self.target_y - symbol_size)),
                    (int(self.target_x - symbol_size * 0.5), int(self.target_y + symbol_size * 0.3)),
                    (int(self.target_x + symbol_size * 0.5), int(self.target_y + symbol_size * 0.3))
                ]
                pygame.draw.lines(surface, (*self.color_bright, symbol_alpha), False, points, 2)


class EstrangeBeam:
    """
    Reality-warping beam that phases target out of normal spacetime.
    Uses purple/lavender colors matching Grayman's glowing orbs.
    """

    def __init__(self, source_x, source_y, target_x, target_y, particle_emitter):
        self.source_x = source_x
        self.source_y = source_y
        self.target_x = target_x
        self.target_y = target_y
        self.particle_emitter = particle_emitter

        # Animation timing
        self.phase = "charge"  # charge, beam, impact, fade
        self.timer = 0
        self.charge_duration = 0.3
        self.beam_duration = 0.4
        self.impact_duration = 0.3
        self.fade_duration = 0.2

        # Visual properties
        self.beam_width = 0
        self.max_beam_width = 12  # Thinner beam

        # Purple/lavender colors from Grayman's orbs
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_bright = (255, 255, 255)  # bright flash

        # Pulsation effect
        self.pulse_timer = 0

        # Warping effect
        self.warp_offset = []
        self.generate_warp_points()

        # Impact particles spawned flag
        self.impact_spawned = False

    def generate_warp_points(self):
        """Generate sine wave distortion points along beam path."""
        # Calculate vector from source to target
        dx = self.target_x - self.source_x
        dy = self.target_y - self.source_y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance == 0:
            return

        # Generate warp points along the beam
        num_points = int(distance / 10) + 2
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            # Multiple sine waves for complex waving motion
            # Combine two sine waves with different frequencies for more organic movement
            wave1 = math.sin(t * math.pi * 4 + self.timer * 15) * 15
            wave2 = math.sin(t * math.pi * 2.5 - self.timer * 8) * 10
            offset = wave1 + wave2
            self.warp_offset.append(offset)

    def update(self, delta_time):
        """Update beam animation state."""
        self.timer += delta_time
        self.pulse_timer += delta_time

        # Update warp points for animated distortion
        self.generate_warp_points()

        if self.phase == "charge":
            # Charging phase - building up energy
            if self.timer == 0 or self.timer < delta_time:
                play_sound("estrange_charge")

            if self.timer >= self.charge_duration:
                self.phase = "beam"
                self.timer = 0
                play_sound("estrange_beam")

                # Spawn charging particles at source
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    # Purple/lavender particle colors
                    color = self.color_outer if random.random() > 0.5 else self.color_inner
                    particle = Particle(self.source_x, self.source_y, vx, vy,
                                      lifetime=0.3, size=4, color=color)
                    self.particle_emitter.particles.append(particle)

        elif self.phase == "beam":
            # Beam firing phase - grow beam width
            progress = self.timer / self.beam_duration
            self.beam_width = self.max_beam_width * min(1.0, progress * 2)

            # Spawn beam particles along path
            if random.random() < 0.3:
                t = random.uniform(0.2, 0.8)
                x = self.source_x + (self.target_x - self.source_x) * t
                y = self.source_y + (self.target_y - self.source_y) * t

                # Perpendicular offset
                dx = self.target_x - self.source_x
                dy = self.target_y - self.source_y
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length
                    perp_y = dx / length
                    offset = random.uniform(-15, 15)
                    x += perp_x * offset
                    y += perp_y * offset

                color = self.color_outer if random.random() > 0.3 else self.color_inner
                particle = Particle(x, y, 0, 0, lifetime=0.2, size=3, color=color)
                self.particle_emitter.particles.append(particle)

            if self.timer >= self.beam_duration:
                self.phase = "impact"
                self.timer = 0
                play_sound("estrange_impact")

        elif self.phase == "impact":
            # Impact phase - hit target
            if not self.impact_spawned:
                # Spawn impact particles
                for _ in range(25):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(100, 250)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    color = random.choice([self.color_outer, self.color_inner, self.color_bright])
                    particle = Particle(self.target_x, self.target_y, vx, vy,
                                      lifetime=0.4, size=5, color=color)
                    self.particle_emitter.particles.append(particle)

                # Spawn warping/phasing particles that spiral
                for i in range(20):
                    angle = (i / 20) * 2 * math.pi
                    distance = random.uniform(20, 60)
                    x = self.target_x + math.cos(angle) * distance
                    y = self.target_y + math.sin(angle) * distance
                    # Particles move inward toward target
                    vx = -math.cos(angle) * 80
                    vy = -math.sin(angle) * 80
                    color = self.color_inner
                    particle = Particle(x, y, vx, vy, lifetime=0.5, size=3, color=color)
                    self.particle_emitter.particles.append(particle)

                self.impact_spawned = True

            if self.timer >= self.impact_duration:
                self.phase = "fade"
                self.timer = 0

        elif self.phase == "fade":
            # Fade out phase
            progress = self.timer / self.fade_duration
            self.beam_width = self.max_beam_width * (1.0 - progress)

            if self.timer >= self.fade_duration:
                return False  # Animation complete

        return True  # Animation still active

    def draw(self, surface):
        """Draw the estrangement beam with warping effect."""
        if self.phase == "charge":
            # Draw charging glow at source
            progress = self.timer / self.charge_duration
            glow_radius = int(15 * progress)

            # Outer glow
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color_outer, int(100 * progress)),
                             (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(self.source_x - glow_radius),
                                    int(self.source_y - glow_radius)))

            # Inner glow
            inner_radius = int(glow_radius * 0.6)
            glow_surf2 = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf2, (*self.color_inner, int(150 * progress)),
                             (inner_radius, inner_radius), inner_radius)
            surface.blit(glow_surf2, (int(self.source_x - inner_radius),
                                     int(self.source_y - inner_radius)))

        elif self.phase in ["beam", "impact", "fade"]:
            # Draw warped beam
            if self.beam_width > 2:
                # Calculate pulsating brightness (oscillates between 0.6 and 1.0)
                pulse_factor = 0.6 + 0.4 * (math.sin(self.pulse_timer * 20) * 0.5 + 0.5)

                # Calculate beam direction
                dx = self.target_x - self.source_x
                dy = self.target_y - self.source_y
                distance = math.sqrt(dx*dx + dy*dy)

                if distance > 0:
                    # Perpendicular vector for width
                    perp_x = -dy / distance
                    perp_y = dx / distance

                    # Draw beam as series of warped segments
                    num_segments = len(self.warp_offset)
                    if num_segments > 1:
                        for i in range(num_segments - 1):
                            t1 = i / (num_segments - 1)
                            t2 = (i + 1) / (num_segments - 1)

                            # Base positions along beam
                            x1 = self.source_x + dx * t1
                            y1 = self.source_y + dy * t1
                            x2 = self.source_x + dx * t2
                            y2 = self.source_y + dy * t2

                            # Apply warp offset
                            offset1 = self.warp_offset[i]
                            offset2 = self.warp_offset[i + 1]

                            x1 += perp_x * offset1
                            y1 += perp_y * offset1
                            x2 += perp_x * offset2
                            y2 += perp_y * offset2

                            # Apply pulse factor to colors
                            pulsed_outer = tuple(int(c * pulse_factor) for c in self.color_outer)
                            pulsed_inner = tuple(int(c * pulse_factor) for c in self.color_inner)
                            pulsed_bright = tuple(int(c * pulse_factor) for c in self.color_bright)

                            # Draw thick outer beam
                            pygame.draw.line(surface, pulsed_outer,
                                          (int(x1), int(y1)), (int(x2), int(y2)),
                                          int(self.beam_width))

                            # Draw thinner inner beam
                            pygame.draw.line(surface, pulsed_inner,
                                          (int(x1), int(y1)), (int(x2), int(y2)),
                                          int(self.beam_width * 0.5))

                            # Draw bright core
                            if self.phase == "beam":
                                pygame.draw.line(surface, pulsed_bright,
                                              (int(x1), int(y1)), (int(x2), int(y2)), 2)

        # Draw impact flash
        if self.phase == "impact":
            flash_progress = self.timer / self.impact_duration
            if flash_progress < 0.3:  # Flash for first 30% of impact phase
                flash_alpha = int(255 * (1.0 - flash_progress / 0.3))
                flash_radius = int(30 * (1.0 + flash_progress))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_bright, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(self.target_x - flash_radius),
                                         int(self.target_y - flash_radius)))


# ============================================================================
# GRAYMAN ECHO DEATH EXPLOSION ANIMATION
# ============================================================================

class TileExplosionBurst:
    """
    Explosion burst effect on individual tiles in the 3x3 AOE.
    Purple expanding circle with fade.
    """
    def __init__(self, tile_x, tile_y, delay=0):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.timer = -delay
        self.duration = 0.6
        self.active = True
        self.max_radius = 35

        # Purple colors
        self.color_outer = (170, 119, 255)
        self.color_inner = (221, 187, 255)

    def update(self, delta_time):
        """Update explosion burst."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw explosion burst on tile."""
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, max(0, self.timer) / self.duration)

        # Expand quickly then fade
        if progress < 0.3:
            radius = int(self.max_radius * (progress / 0.3))
        else:
            radius = self.max_radius

        # Fade out
        alpha = int(200 * (1.0 - progress))

        if alpha < 20 or radius < 2:
            return

        burst_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        center = radius + 10

        # Outer purple ring
        pygame.draw.circle(burst_surf, (*self.color_outer, alpha // 2),
                         (center, center), radius + 8)

        # Main burst
        pygame.draw.circle(burst_surf, (*self.color_inner, alpha),
                         (center, center), radius)

        # Bright center (early in animation)
        if progress < 0.4:
            inner_alpha = int(alpha * (1.0 - progress / 0.4))
            inner_radius = int(radius * 0.5)
            pygame.draw.circle(burst_surf, (255, 255, 255, inner_alpha),
                             (center, center), inner_radius)

        surface.blit(burst_surf, (int(self.tile_x - center), int(self.tile_y - center)))


class PsychicWave:
    """
    Expanding wave from center across all tiles.
    Shows the explosion propagating outward.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5
        self.active = True
        self.max_radius = TILE_SIZE * 2  # Covers 3x3 area

        # Purple colors
        self.color_outer = (170, 119, 255)
        self.color_inner = (221, 187, 255)

    def update(self, delta_time):
        """Update wave expansion."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw expanding wave."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Wave expands outward
        radius = int(self.max_radius * progress)

        # Fade as it expands
        alpha = int(180 * (1.0 - progress * 0.7))

        if alpha < 20 or radius < 5:
            return

        # Draw expanding ring
        ring_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        center = radius + 10

        # Outer ring
        pygame.draw.circle(ring_surf, (*self.color_outer, alpha // 2),
                         (center, center), radius, 8)

        # Inner ring
        pygame.draw.circle(ring_surf, (*self.color_inner, alpha),
                         (center, center), max(5, radius - 8), 4)

        surface.blit(ring_surf, (int(self.center_x - center), int(self.center_y - center)))


class ExplosionParticles:
    """
    Particles spreading outward from center during explosion.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.8
        self.active = True

        # Generate particles
        self.particles = []
        num_particles = 40
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            speed = random.uniform(100, 250)
            self.particles.append({
                'angle': angle,
                'speed': speed,
                'size': random.randint(2, 4),
                'color_type': random.choice(['outer', 'inner', 'white'])
            })

        self.colors = {
            'outer': (170, 119, 255),
            'inner': (221, 187, 255),
            'white': (255, 255, 255)
        }

    def update(self, delta_time):
        """Update particles."""
        if not self.active:
            return False

        self.timer += delta_time

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        """Draw explosion particles."""
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        for particle in self.particles:
            # Calculate position
            distance = particle['speed'] * self.timer
            px = self.center_x + math.cos(particle['angle']) * distance
            py = self.center_y + math.sin(particle['angle']) * distance

            # Fade out
            alpha = int(220 * (1.0 - progress))

            if alpha < 20:
                continue

            color = (*self.colors[particle['color_type']], alpha)

            # Draw particle
            particle_surf = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color,
                             (particle['size'], particle['size']), particle['size'])

            surface.blit(particle_surf, (int(px - particle['size']), int(py - particle['size'])))


class GraymanEchoDeathExplosionAnimation:
    """
    GRAYMAN ECHO death explosion - psychic explosion affecting 3x3 AOE.
    Simple explosion that expands outward and affects all tiles in range 1.

    Phases:
    1. Charge (0.3s) - Brief buildup at center
    2. Explosion (0.6s) - Main burst with wave and tile effects
    3. Dissipate (0.5s) - Particles fade
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize GRAYMAN ECHO death explosion animation.

        Args:
            caster_unit: Dead echo unit (at death position)
            target_pos: (grid_y, grid_x) - echo death position
            camera: Camera instance for coordinate conversion
            particle_emitter: Particle emitter for effects
            screen_shake_callback: Callback for screen shake
        """
        # Store references
        self.caster = caster_unit
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.game = game

        # Convert echo position to screen coords
        # CRITICAL: target_pos is (grid_y, grid_x), but grid_to_screen takes (grid_x, grid_y)!
        grid_y, grid_x = target_pos
        self.center_x, self.center_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Calculate 3x3 tile positions (9 tiles total)
        self.tile_positions = []
        tile_offsets = [
            (-TILE_SIZE, -TILE_SIZE), (0, -TILE_SIZE), (TILE_SIZE, -TILE_SIZE),
            (-TILE_SIZE, 0),          (0, 0),          (TILE_SIZE, 0),
            (-TILE_SIZE, TILE_SIZE),  (0, TILE_SIZE),  (TILE_SIZE, TILE_SIZE)
        ]

        for offset_x, offset_y in tile_offsets:
            tile_x = self.center_x + offset_x
            tile_y = self.center_y + offset_y
            distance = math.sqrt(offset_x**2 + offset_y**2)
            self.tile_positions.append({
                'x': tile_x,
                'y': tile_y,
                'distance': distance,
                'delay': distance / 300.0  # Stagger based on distance
            })

        # Purple colors
        self.color_outer = (170, 119, 255)
        self.color_inner = (221, 187, 255)

        # Animation state
        self.phase = "charge"
        self.timer = 0
        self.active = True

        # Sub-effects
        self.charge_glow_radius = 0
        self.psychic_wave = None
        self.tile_bursts = []
        self.explosion_particles = None

        # Start Phase 1: Charge
        self._start_charge()

    def _start_charge(self):
        """Phase 1: Charge - Brief buildup."""
        self.phase = "charge"
        self.timer = 0
        play_sound("echo_death_charge")

        # Light screen shake
        self.screen_shake_callback(3, 0.3)

    def _start_explosion(self):
        """Phase 2: Explosion - Main burst."""
        self.phase = "explosion"
        self.timer = 0
        play_sound("echo_death_explosion")

        # Create expanding wave from center
        self.psychic_wave = PsychicWave(self.center_x, self.center_y)

        # Create explosion bursts on all 9 tiles (staggered)
        for tile_info in self.tile_positions:
            burst = TileExplosionBurst(tile_info['x'], tile_info['y'], tile_info['delay'])
            self.tile_bursts.append(burst)

        # Explosion particles spreading outward
        self.explosion_particles = ExplosionParticles(self.center_x, self.center_y)

        # Heavy screen shake
        self.screen_shake_callback(7, 0.5)

        # Emit particle burst
        if self.particle_emitter:
            self.particle_emitter.emit_burst(self.center_x, self.center_y,
                                            self.color_inner, count=30)

    def _start_dissipate(self):
        """Phase 3: Dissipate - Fade out."""
        self.phase = "dissipate"
        self.timer = 0
        play_sound("echo_death_dissipate")

    def update(self, delta_time):
        """Update animation state. MUST return True/False."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update charge glow
        if self.phase == "charge":
            # Glow builds up
            progress = min(1.0, self.timer / 0.3)
            self.charge_glow_radius = 30 * progress

        # Update sub-effects
        if self.psychic_wave:
            self.psychic_wave.update(delta_time)

        for burst in self.tile_bursts:
            burst.update(delta_time)

        if self.explosion_particles:
            self.explosion_particles.update(delta_time)

        # Phase transitions
        if self.phase == "charge" and self.timer >= 0.3:
            self._start_explosion()
        elif self.phase == "explosion" and self.timer >= 0.6:
            self._start_dissipate()
        elif self.phase == "dissipate" and self.timer >= 0.5:
            self.active = False  # Animation complete

        return self.active

    def draw(self, surface):
        """Draw animation to pygame surface."""
        if not self.active:
            return

        # Phase 1: Charge - Pulsing glow at center
        if self.phase == "charge":
            progress = self.timer / 0.3
            alpha = int(150 * progress)
            pulse = 0.8 + 0.2 * math.sin(self.timer * 20)

            radius = int(self.charge_glow_radius * pulse)

            if radius > 2 and alpha > 20:
                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

                # Outer glow
                pygame.draw.circle(glow_surf, (*self.color_outer, alpha // 2),
                                 (radius, radius), radius)

                # Inner glow
                inner_radius = int(radius * 0.6)
                pygame.draw.circle(glow_surf, (*self.color_inner, alpha),
                                 (radius, radius), inner_radius)

                surface.blit(glow_surf, (int(self.center_x - radius),
                                        int(self.center_y - radius)))

        # Phase 2 & 3: Explosion effects
        if self.phase in ["explosion", "dissipate"]:
            # Draw expanding wave
            if self.psychic_wave:
                self.psychic_wave.draw(surface)

            # Draw tile bursts
            for burst in self.tile_bursts:
                burst.draw(surface)

            # Draw explosion particles (top layer)
            if self.explosion_particles:
                self.explosion_particles.draw(surface)


class GraymanPsychicAttack:
    """
    GRAYMAN basic attack animation - psychic/psionic energy projection.
    Purple/violet energy wave that travels from attacker to target.
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
        self.phase = "charge"  # charge → project → impact → done
        self.timer = 0
        self.active = True

        # Phase durations
        self.charge_duration = 0.15
        self.project_duration = 0.3
        self.impact_duration = 0.2

        # Psychic wave drawing state
        self.wave_progress = 0.0  # 0.0 to 1.0 during project phase

        # Purple/violet colors matching GRAYMAN's Psi symbol
        self.color_outer = (170, 119, 255)  # #aa77ff
        self.color_inner = (221, 187, 255)  # #ddbbff
        self.color_bright = (255, 255, 255)

    def _trigger_charge(self):
        """Phase 1: Charge psychic energy."""
        play_sound("grayman_attack_charge")

        # Spawn charging particles at attacker
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(25, 40)
            x = self.attacker.x + math.cos(angle) * distance
            y = self.attacker.y + math.sin(angle) * distance
            # Particles move toward center
            vx = -math.cos(angle) * 120
            vy = -math.sin(angle) * 120
            color = self.color_outer if random.random() > 0.5 else self.color_inner
            particle = Particle(x, y, vx, vy, color, size=3, lifetime=0.2)
            self.particle_emitter.particles.append(particle)

    def _trigger_project(self):
        """Phase 2: Project psychic wave toward target."""
        play_sound("grayman_attack_project")

        # Create trailing particles along the wave
        for i in range(15):
            progress = i / 15
            x = self.attacker.x + self.dx * self.distance * progress
            y = self.attacker.y + self.dy * self.distance * progress

            # Add some perpendicular spread
            perp_x = -self.dy
            perp_y = self.dx
            spread = random.uniform(-15, 15)

            vx = self.dx * 200 + perp_x * spread * 2
            vy = self.dy * 200 + perp_y * spread * 2

            color = random.choice([self.color_outer, self.color_inner])
            size = random.uniform(3, 5)
            lifetime = random.uniform(0.2, 0.3)

            particle = Particle(x, y, vx, vy, color, size, lifetime)
            particle.gravity = 0  # No gravity for psychic energy
            self.particle_emitter.particles.append(particle)

    def _trigger_impact(self):
        """Phase 3: Psychic impact at target."""
        play_sound("grayman_attack_impact")

        # Impact burst - purple/violet explosion
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 220)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = random.choice([
                self.color_outer,
                self.color_inner,
                self.color_bright,
            ])

            size = random.uniform(3, 6)
            lifetime = random.uniform(0.15, 0.25)

            particle = Particle(self.target.x, self.target.y, vx, vy, color, size, lifetime)
            particle.gravity = 120
            self.particle_emitter.particles.append(particle)

        # Psychic impact shake
        self.target.shake_intensity = 12
        self.screen_shake(6, 0.18)

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
                self.phase = "project"
                self.timer = 0
                self._trigger_project()

        elif self.phase == "project":
            # Update wave progress for drawing
            self.wave_progress = min(1.0, self.timer / self.project_duration)

            if self.timer >= self.project_duration:
                self.phase = "impact"
                self.timer = 0
                self._trigger_impact()

        elif self.phase == "impact":
            if self.timer >= self.impact_duration:
                self.phase = "done"
                self.active = False

        return self.active

    def draw(self, surface):
        """Draw the psychic energy wave during project phase."""
        import pygame

        # Draw charging glow
        if self.phase == "charge":
            progress = self.timer / self.charge_duration
            glow_radius = int(20 * progress)

            if glow_radius > 3:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color_outer, int(120 * progress)),
                                 (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surf, (int(self.attacker.x - glow_radius),
                                        int(self.attacker.y - glow_radius)))

                # Inner glow
                inner_radius = int(glow_radius * 0.6)
                if inner_radius > 2:
                    inner_surf = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(inner_surf, (*self.color_inner, int(180 * progress)),
                                     (inner_radius, inner_radius), inner_radius)
                    surface.blit(inner_surf, (int(self.attacker.x - inner_radius),
                                             int(self.attacker.y - inner_radius)))

        # Draw psychic wave during project phase
        if self.phase == "project":
            # Calculate perpendicular vector for wave width
            perp_x = -self.dy
            perp_y = self.dx

            # Draw the energy wave as expanding oval/ellipse
            wave_length = self.distance * self.wave_progress
            wave_width = 25  # Width of the wave

            # Create wave front points
            points = []
            num_segments = 12

            for i in range(num_segments + 1):
                # Parameter from -1 to 1 (across wave width)
                t = (i / num_segments) * 2 - 1

                # Calculate position at wave front
                front_x = self.attacker.x + self.dx * wave_length
                front_y = self.attacker.y + self.dy * wave_length

                # Add perpendicular offset
                offset = t * wave_width
                point_x = front_x + perp_x * offset
                point_y = front_y + perp_y * offset

                points.append((int(point_x), int(point_y)))

            # Draw the wave as filled polygon with transparency
            if len(points) >= 3:
                # Create transparent surface for wave
                wave_surf = pygame.Surface((int(self.distance + 100), int(wave_width * 3)), pygame.SRCALPHA)

                # Transform points to local coordinates
                min_x = min(p[0] for p in points)
                min_y = min(p[1] for p in points)
                local_points = [(p[0] - min_x + 50, p[1] - min_y + wave_width) for p in points]

                # Draw outer glow
                pygame.draw.polygon(wave_surf, (*self.color_outer, 100), local_points)

                # Draw inner bright core (narrower)
                inner_points = []
                for i in range(num_segments + 1):
                    t = (i / num_segments) * 2 - 1
                    front_x = self.attacker.x + self.dx * wave_length
                    front_y = self.attacker.y + self.dy * wave_length
                    offset = t * wave_width * 0.5
                    point_x = front_x + perp_x * offset
                    point_y = front_y + perp_y * offset
                    inner_points.append((int(point_x - min_x + 50), int(point_y - min_y + wave_width)))

                if len(inner_points) >= 3:
                    pygame.draw.polygon(wave_surf, (*self.color_inner, 160), inner_points)

                # Draw bright center line
                center_start = (int(self.attacker.x - min_x + 50), int(self.attacker.y - min_y + wave_width))
                center_end = (int(front_x - min_x + 50), int(front_y - min_y + wave_width))
                pygame.draw.line(wave_surf, self.color_bright, center_start, center_end, 3)

                surface.blit(wave_surf, (min_x - 50, min_y - wave_width))

        # Draw impact flash
        if self.phase == "impact":
            progress = self.timer / self.impact_duration
            if progress < 0.4:
                flash_alpha = int(255 * (1.0 - progress / 0.4))
                flash_radius = int(35 * (1.0 + progress))

                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*self.color_bright, flash_alpha),
                                 (flash_radius, flash_radius), flash_radius)
                surface.blit(flash_surf, (int(self.target.x - flash_radius),
                                         int(self.target.y - flash_radius)))
