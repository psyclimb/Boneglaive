#!/usr/bin/env python3
"""
DELPHIC APPRAISER Animation Classes
Skill animations for the DELPHIC APPRAISER unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, COLOR_DAMAGE, COLOR_SKILL


class FractureLines:
    """
    Reality fracture lines radiating from target furniture.
    White cracks spreading outward in a web pattern.
    """
    def __init__(self, center_x, center_y, camera):
        self.center_x = center_x  # Already in screen/world space
        self.center_y = center_y  # Already in screen/world space
        self.camera = camera
        self.timer = 0
        self.duration = 0.8
        self.active = True

        # Generate fracture line endpoints
        self.fractures = []
        num_fractures = 12
        for i in range(num_fractures):
            angle = (i / num_fractures) * 2 * math.pi
            length = random.uniform(40, 80)
            self.fractures.append({
                'angle': angle,
                'length': length,
                'offset': random.uniform(0, 0.2)  # Stagger appearance
            })

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        # Use screen coords directly (center_x, center_y are already in world/screen space)
        screen_x, screen_y = self.center_x, self.center_y

        # Progress from 0 to 1
        progress = min(1.0, self.timer / self.duration)

        # Draw each fracture line
        for fracture in self.fractures:
            # Apply offset for staggered appearance
            line_progress = max(0, (progress - fracture['offset']) / (1 - fracture['offset']))

            if line_progress > 0:
                # Calculate end point
                end_dist = fracture['length'] * line_progress
                end_x = screen_x + math.cos(fracture['angle']) * end_dist
                end_y = screen_y + math.sin(fracture['angle']) * end_dist

                # Dark gray cursed fracture
                alpha = int(200 * (1.0 - progress * 0.5))  # Fade as they spread
                color = (44, 44, 44, alpha)  # Dark gray curse energy

                # Draw line with alpha
                fracture_surf = pygame.Surface((abs(int(end_x - screen_x)) + 2,
                                               abs(int(end_y - screen_y)) + 2),
                                              pygame.SRCALPHA)
                local_start = (min(0, int(end_x - screen_x)), min(0, int(end_y - screen_y)))
                local_end = (max(0, int(end_x - screen_x)), max(0, int(end_y - screen_y)))
                pygame.draw.line(fracture_surf, color, local_start, local_end, 2)
                surface.blit(fracture_surf, (min(screen_x, end_x), min(screen_y, end_y)))


class VortexEffect:
    """
    Black hole vortex effect - particles spiral inward.
    Gold particles getting sucked into the center.
    """
    def __init__(self, center_x, center_y, camera, particle_emitter):
        self.center_x = center_x  # Already in screen/world space
        self.center_y = center_y  # Already in screen/world space
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.timer = 0
        self.duration = 1.2
        self.active = True

        # Vortex particles
        self.particles = []

        # Spawn initial particles
        for _ in range(80):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(30, 100)
            self.particles.append({
                'angle': angle,
                'distance': distance,
                'speed': random.uniform(60, 120),  # How fast it spirals in
                'rotation_speed': random.uniform(2, 4),  # Angular velocity
                'size': random.uniform(2, 5),
                'color': (255, 215, 0) if random.random() > 0.5 else (42, 42, 42)  # Gold or dark curse
            })

    def update(self, delta_time):
        self.timer += delta_time

        # Update particles - spiral inward
        for p in self.particles:
            p['distance'] -= p['speed'] * delta_time
            p['angle'] += p['rotation_speed'] * delta_time

            # Shrink as they approach center
            if p['distance'] < 30:
                p['size'] *= 0.95

        # Remove particles that reached center
        self.particles = [p for p in self.particles if p['distance'] > 2]

        if self.timer >= self.duration:
            self.active = False

        return self.active

    def draw(self, surface):
        if not self.active:
            return

        # Use screen coords directly (center_x, center_y are already in world/screen space)
        screen_x, screen_y = self.center_x, self.center_y

        # Draw vortex particles
        for p in self.particles:
            # Calculate particle position (polar to cartesian)
            px = screen_x + math.cos(p['angle']) * p['distance']
            py = screen_y + math.sin(p['angle']) * p['distance']

            # Alpha based on distance (fade as approaching center)
            alpha = int(255 * min(1.0, p['distance'] / 30))
            color = (*p['color'], alpha)

            # Draw particle
            if p['size'] > 0.5:
                particle_surf = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color, (int(p['size']), int(p['size'])), int(p['size']))
                surface.blit(particle_surf, (int(px - p['size']), int(py - p['size'])))


class ShockwaveRing:
    """
    Expanding concentric shockwave ring.
    Multiple rings create implosion effect.
    """
    def __init__(self, center_x, center_y, camera, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.camera = camera
        self.timer = -delay  # Negative timer for delay
        self.duration = 0.8
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return  # Don't draw during delay

        # Use screen coords directly
        screen_x, screen_y = self.center_x, self.center_y

        # Expand outward
        progress = self.timer / self.duration
        radius = int(progress * 224)  # Expand to 224px (7 tiles × 64px / 2 = edges of 7×7 area)

        # Fade out as expanding
        alpha = int(255 * (1.0 - progress))

        # Brown curse color
        color = (139, 69, 19, alpha)

        # Draw ring
        if radius > 0:
            ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, color, (radius + 5, radius + 5), radius, 4)
            surface.blit(ring_surf, (int(screen_x - radius - 5), int(screen_y - radius - 5)))


class ValuePlummetNumber:
    """
    Number that plummets from its current value down to 1.
    Used for the target furniture in Divine Depreciation.
    """
    def __init__(self, x, y, camera, start_value, start_delay=0.0):
        self.x = x
        self.y = y
        self.camera = camera
        self.start_value = start_value if start_value > 1 else 9  # Start at 9 if already 1
        self.start_delay = start_delay
        self.timer = -start_delay
        self.duration = 1.2  # 1.2 seconds to plummet
        self.active = True

        # Create descending sequence from start to 1
        self.sequence = list(range(self.start_value, 0, -1))  # e.g., [7, 6, 5, 4, 3, 2, 1]

        self.current_index = 0
        self.frame_time = self.duration / len(self.sequence) if len(self.sequence) > 0 else 0.1

    def update(self, delta_time):
        self.timer += delta_time

        if self.timer < 0:
            return

        # Update which number to show
        self.current_index = min(len(self.sequence) - 1, int(self.timer / self.frame_time))

        if self.timer >= self.duration + 0.5:
            self.active = False

        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        screen_x, screen_y = self.x, self.y

        # Current number
        current_num = self.sequence[self.current_index]

        # Large, dramatic font
        font_size = 48

        # Color shifts from gold to dark gray as it plummets
        progress = min(1.0, self.timer / self.duration)  # Clamp to 1.0
        # Gold (255, 215, 0) → Dark gray (44, 44, 44)
        red = int(255 - (255 - 44) * progress)
        green = int(215 - (215 - 44) * progress)
        blue = int(0 + (44 - 0) * progress)
        color = (red, green, blue)

        # Pulsing alpha
        alpha = int(200 + 55 * math.sin(self.timer * 8))

        # Render number
        font = pygame.font.Font(None, font_size)
        text = font.render(str(current_num), True, color)
        text.set_alpha(alpha)

        # Center on tile
        rect = text.get_rect(center=(int(screen_x), int(screen_y)))

        # Dark outline
        outline_font = pygame.font.Font(None, font_size + 2)
        outline = outline_font.render(str(current_num), True, (0, 0, 0))
        outline.set_alpha(alpha // 2)
        outline_rect = outline.get_rect(center=(int(screen_x), int(screen_y)))

        surface.blit(outline, outline_rect)
        surface.blit(text, rect)


class CosmicRerollNumber:
    """
    Rapidly cycling number on a furniture piece.
    Shows 12 frames of random values before settling.
    """
    def __init__(self, x, y, camera, final_value, start_delay=0.0):
        self.x = x
        self.y = y
        self.camera = camera
        self.final_value = final_value
        self.start_delay = start_delay  # Delay before starting animation
        self.timer = -start_delay  # Start negative to create delay
        self.duration = 1.0  # 1 second of cycling
        self.active = True

        # Generate sequence of random numbers
        self.sequence = [random.randint(1, 9) for _ in range(12)]
        self.sequence.append(final_value)  # End with final value

        self.current_index = 0
        self.frame_time = self.duration / len(self.sequence)

    def update(self, delta_time):
        self.timer += delta_time

        # Don't show anything during delay period
        if self.timer < 0:
            return

        # Update which number to show
        self.current_index = min(len(self.sequence) - 1, int(self.timer / self.frame_time))

        if self.timer >= self.duration + 0.5:  # Hold final value for 0.5s
            self.active = False

        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return  # Don't draw during delay period

        # Use screen coords directly (x, y are already in world/screen space)
        screen_x, screen_y = self.x, self.y

        # Current number to display
        current_num = self.sequence[self.current_index]

        # Same size as plummet animation
        font_size = 48

        # Gold color with pulsing alpha
        alpha = int(200 + 55 * math.sin(self.timer * 8))

        # Render number
        font = pygame.font.Font(None, font_size)
        text = font.render(str(current_num), True, (255, 215, 0))
        text.set_alpha(alpha)

        # Center on tile
        rect = text.get_rect(center=(int(screen_x), int(screen_y)))

        # Dark outline
        outline_font = pygame.font.Font(None, font_size + 2)
        outline = outline_font.render(str(current_num), True, (0, 0, 0))
        outline.set_alpha(alpha // 2)
        outline_rect = outline.get_rect(center=(int(screen_x), int(screen_y)))

        surface.blit(outline, outline_rect)
        surface.blit(text, rect)


class DivineDrepreciationAnimation:
    """
    Ultimate animation for DELPHIC APPRAISER's Divine Depreciation skill.
    The most dramatic animation - reality-warping furniture reappraisal.

    Phases:
    1. Reality Fracture - Cracks appear, furniture glows
    2. Value Collapse - Number counts down, vortex forms
    3. Reality Implosion - Flash, shockwaves, peak shake
    4. Cosmic Reroll - All furniture values cycle and settle
    5. Aftermath - Distortion field fades
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Divine Depreciation animation.

        Args:
            target_pos: (grid_y, grid_x) - the furniture being depreciated
            game: Game instance to access map/furniture data
            Other args standard from AnimationFactory
        """
        self.caster = caster_unit
        self.target_pos = target_pos  # (grid_y, grid_x) furniture position
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert target grid position to screen coords using Camera
        # target_pos is (grid_y, grid_x)
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "fracture"  # fracture -> collapse -> implosion -> reroll -> aftermath
        self.timer = 0
        self.active = True

        # Sub-effects
        self.fracture_lines = None
        self.vortex = None
        self.shockwaves = []
        self.reroll_numbers = []

        # Glow effect on target
        self.glow_intensity = 0

        # Start Phase 1: Reality Fracture
        self._start_fracture_phase()

    def _start_fracture_phase(self):
        """Phase 1: Reality fractures around target."""
        self.fracture_lines = FractureLines(self.target_x, self.target_y, self.camera)
        self.screen_shake_callback(2, 0.8)  # Light shake building up

    def _start_collapse_phase(self):
        """Phase 2: Value collapses into vortex."""
        self.phase = "collapse"
        self.timer = 0
        self.vortex = VortexEffect(self.target_x, self.target_y, self.camera, self.particle_emitter)
        self.screen_shake_callback(6, 1.2)  # Stronger shake

    def _start_implosion_phase(self):
        """Phase 3: Reality implodes with massive flash."""
        self.phase = "implosion"
        self.timer = 0

        # Create multiple shockwaves
        self.shockwaves = [
            ShockwaveRing(self.target_x, self.target_y, self.camera, delay=0),
            ShockwaveRing(self.target_x, self.target_y, self.camera, delay=0.15),
            ShockwaveRing(self.target_x, self.target_y, self.camera, delay=0.3),
            ShockwaveRing(self.target_x, self.target_y, self.camera, delay=0.45),
        ]

        # Massive screen effects
        self.screen_flash_callback((139, 69, 19), 0.3)  # Brown curse flash
        self.screen_shake_callback(15, 0.6)  # Peak shake

    def _start_reroll_phase(self):
        """Phase 4: All furniture rerolls values."""
        self.phase = "reroll"
        self.timer = 0

        # Create reroll effects for all tiles in 7×7 AoE that have furniture
        # Center is target_pos, so check ±3 grid tiles in each direction
        grid_y, grid_x = self.target_pos

        for dy in range(-3, 4):  # -3 to +3 = 7 tiles
            for dx in range(-3, 4):  # -3 to +3 = 7 tiles
                tile_grid_x = grid_x + dx
                tile_grid_y = grid_y + dy

                # Check if this tile has furniture (only actual furniture, not terrain)
                has_furniture = False
                if self.game and hasattr(self.game, 'map') and self.game.map:
                    # Check if tile is in bounds
                    if (0 <= tile_grid_y < self.game.map.height and
                        0 <= tile_grid_x < self.game.map.width):
                        # Check if tile has furniture (actual furniture only, not terrain/walls)
                        from boneglaive.game.map import TerrainType
                        tile_terrain = self.game.map.terrain.get((tile_grid_y, tile_grid_x), TerrainType.EMPTY)
                        # Only actual furniture types (not terrain/walls)
                        furniture_types = {
                            TerrainType.RADIO_CONSOLE, TerrainType.COAT_RACK, TerrainType.OTTOMAN,
                            TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF, TerrainType.TIFFANY_LAMP,
                            TerrainType.EASEL, TerrainType.SCULPTURE, TerrainType.BENCH,
                            TerrainType.PODIUM, TerrainType.VASE, TerrainType.WORKBENCH,
                            TerrainType.COUCH, TerrainType.TOOLBOX, TerrainType.COT,
                            TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN, TerrainType.POTPOURRI_BOWL
                        }
                        has_furniture = tile_terrain in furniture_types

                if not has_furniture:
                    continue  # Skip non-furniture tiles

                # Convert to screen coords
                tile_screen_x, tile_screen_y = self.camera.grid_to_screen(
                    tile_grid_x, tile_grid_y, centered=True
                )

                # Create reroll number with slight delay based on distance from center
                distance = abs(dx) + abs(dy)
                delay = distance * 0.05  # Stagger the start times slightly

                # Check if this is the target furniture
                is_target = (tile_grid_x == grid_x and tile_grid_y == grid_y)

                if is_target:
                    # Target furniture: plummet to 1
                    # Get current astral value (cosmetic, game handles actual value)
                    start_value = random.randint(2, 9)  # Start at 2-9 so it can plummet to 1
                    self.reroll_numbers.append(
                        ValuePlummetNumber(tile_screen_x, tile_screen_y, self.camera,
                                         start_value, start_delay=0)  # No delay for target
                    )
                else:
                    # Other furniture: random reroll
                    final_value = random.randint(1, 9)
                    self.reroll_numbers.append(
                        CosmicRerollNumber(tile_screen_x, tile_screen_y, self.camera,
                                         final_value, start_delay=delay)
                    )

    def _start_aftermath_phase(self):
        """Phase 5: Effects fade out."""
        self.phase = "aftermath"
        self.timer = 0

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update glow
        if self.phase in ["fracture", "collapse"]:
            # Glow increases
            self.glow_intensity = min(1.0, self.timer / 0.5)
        elif self.phase == "aftermath":
            # Glow fades
            self.glow_intensity = max(0, 1.0 - self.timer / 0.5)

        # Phase transitions
        if self.phase == "fracture" and self.timer >= 0.8:
            self._start_collapse_phase()
        elif self.phase == "collapse" and self.timer >= 1.2:
            self._start_implosion_phase()
        elif self.phase == "implosion" and self.timer >= 0.6:
            self._start_reroll_phase()
        elif self.phase == "reroll" and self.timer >= 1.5:
            self._start_aftermath_phase()
        elif self.phase == "aftermath" and self.timer >= 0.5:
            self.active = False

        # Update sub-effects
        if self.fracture_lines:
            self.fracture_lines.update(delta_time)

        if self.vortex:
            self.vortex.update(delta_time)

        for wave in self.shockwaves:
            wave.update(delta_time)

        for num in self.reroll_numbers:
            num.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        # Draw glow on target
        if self.glow_intensity > 0:
            # Use screen coords directly (target_x, target_y are already in world/screen space)
            screen_x, screen_y = self.target_x, self.target_y

            # Color shifts from gold to dark gray during collapse
            if self.phase == "fracture":
                color = (255, 215, 0)  # Gold
            elif self.phase == "collapse":
                # Interpolate to dark gray
                t = self.timer / 1.2
                color = (
                    int(255 - (255 - 44) * t),
                    int(215 - (215 - 44) * t),
                    int(0 + (44 - 0) * t)
                )
            else:
                color = (44, 44, 44)  # Dark gray

            # Pulsing glow
            radius = int(40 + 10 * math.sin(self.timer * 5))
            alpha = int(self.glow_intensity * 150)

            # Draw glow circle
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, alpha), (radius, radius), radius)
            surface.blit(glow_surf, (int(screen_x - radius), int(screen_y - radius)))

        # Draw phase-specific effects
        if self.fracture_lines:
            self.fracture_lines.draw(surface)

        if self.vortex:
            self.vortex.draw(surface)

        for wave in self.shockwaves:
            wave.draw(surface)

        for num in self.reroll_numbers:
            num.draw(surface)

        # Draw aftermath distortion field
        if self.phase == "aftermath":
            # Use screen coords directly (target_x, target_y are already in world/screen space)
            screen_x, screen_y = self.target_x, self.target_y
            overlay_size = TILE_SIZE * 7
            alpha = int(self.glow_intensity * 60)  # Faint overlay

            overlay_surf = pygame.Surface((overlay_size, overlay_size), pygame.SRCALPHA)
            pygame.draw.rect(overlay_surf, (42, 42, 42, alpha), overlay_surf.get_rect())  # Dark curse aftermath
            surface.blit(overlay_surf, (int(screen_x - overlay_size // 2), int(screen_y - overlay_size // 2)))


# ============================================================================
# AUCTION CURSE ANIMATION
# ============================================================================

class PodiumRise:
    """
    Brown wooden podium rising from the ground with dust particles and ground cracks.
    """
    def __init__(self, x, y, camera, start_delay=0.0):
        self.x = x
        self.y = y
        self.camera = camera
        self.start_delay = start_delay
        self.timer = -start_delay
        self.duration = 0.8
        self.active = True
        # Generate random crack angles for consistency
        self.crack_angles = [random.uniform(0, 2 * math.pi) for _ in range(4)]

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        screen_x, screen_y = self.x, self.y

        # Progress from ground to full height
        progress = min(1.0, self.timer / self.duration)

        # Ground cracks radiating outward (early phase)
        if progress < 0.4:
            crack_progress = progress / 0.4
            crack_alpha = int(120 * crack_progress * (1 - crack_progress) * 4)  # Fade in then out

            if crack_alpha > 0:
                for angle in self.crack_angles:
                    # Crack extends outward
                    crack_length = 15 + crack_progress * 10
                    end_x = screen_x + math.cos(angle) * crack_length
                    end_y = screen_y + math.sin(angle) * crack_length

                    # Draw jagged crack
                    pygame.draw.line(surface, (60, 50, 40, crack_alpha),
                                   (int(screen_x), int(screen_y)),
                                   (int(end_x), int(end_y)), 2)

        # Podium rises from ground
        podium_height = int(progress * 30)  # 30px tall when fully risen

        # Brown wood color from icon
        wood_color = (139, 69, 19)
        dark_wood = (101, 67, 33)
        light_wood = (160, 82, 45)

        # Draw podium base (wider at bottom)
        base_width = 24
        top_width = 16

        if podium_height > 0:
            # Create trapezoid shape for podium
            podium_surf = pygame.Surface((base_width, podium_height), pygame.SRCALPHA)

            # Draw main body with enhanced wood grain
            for i in range(podium_height):
                # Width tapers from base to top
                y_progress = i / podium_height
                current_width = int(base_width - (base_width - top_width) * y_progress)
                x_offset = (base_width - current_width) // 2

                # More detailed wood grain effect
                if i % 4 == 0:
                    color = light_wood
                elif i % 3 == 0:
                    color = dark_wood
                else:
                    color = wood_color
                pygame.draw.line(podium_surf, color, (x_offset, i), (x_offset + current_width, i), 1)

            surface.blit(podium_surf, (int(screen_x - base_width // 2), int(screen_y - podium_height)))

        # Enhanced dust particles
        if progress < 0.6:
            num_particles = 12
            for i in range(num_particles):
                # Circular spread pattern
                angle = (i / num_particles) * 2 * math.pi + progress * 2
                dist = random.uniform(8, 25) * progress * 2
                px = screen_x + math.cos(angle) * dist
                py = screen_y - progress * 20 - random.uniform(0, 5)  # Rise up with variation

                alpha = int(140 * (0.6 - progress) / 0.6)  # Fade as podium rises
                if alpha > 0:
                    size = random.choice([2, 3, 4])
                    dust_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dust_surf, (101, 67, 33, alpha), (size, size), size)
                    surface.blit(dust_surf, (int(px - size), int(py - size)))

        # Larger debris chunks early on
        if progress < 0.3:
            debris_alpha = int(180 * (0.3 - progress) / 0.3)
            for i in range(4):
                angle = (i / 4) * 2 * math.pi
                dist = 18 + progress * 12
                px = screen_x + math.cos(angle) * dist
                py = screen_y - progress * 8

                debris_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
                pygame.draw.rect(debris_surf, (76, 50, 25, debris_alpha), (0, 0, 4, 4))
                surface.blit(debris_surf, (int(px), int(py)))


class AuctioneerGhost:
    """
    Dark ghostly auctioneer figure with detailed skull, cloak, and wispy trails.
    """
    def __init__(self, x, y, camera, start_delay=0.0):
        self.x = x
        self.y = y
        self.camera = camera
        self.start_delay = start_delay
        self.timer = -start_delay
        self.duration = 0.6
        self.active = True
        self.gavel_raised = False
        # Random wisp offsets for organic motion
        self.wisp_offsets = [random.uniform(0, 2 * math.pi) for _ in range(6)]

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def raise_gavel(self):
        """Trigger gavel raising animation."""
        self.gavel_raised = True

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        screen_x, screen_y = self.x, self.y

        # Fade in
        progress = min(1.0, self.timer / self.duration)
        alpha = int(200 * progress)

        # Ghostly auctioneer above podium with floating motion
        float_offset = math.sin(self.timer * 2) * 3
        auctioneer_y = screen_y - 30 - int(progress * 10) + float_offset  # Float above podium

        # Dark skull/ghost colors with crimson tint
        skull_color = (52, 42, 42, alpha)
        darker_skull = (36, 26, 26, alpha)
        bone_color = (180, 180, 160, alpha)

        # Wispy trails around auctioneer
        if progress > 0.2:
            wisp_alpha = int(alpha * 0.4)
            for i, offset in enumerate(self.wisp_offsets):
                angle = offset + self.timer * 3
                radius = 15 + i * 2
                wisp_x = screen_x + math.cos(angle) * radius
                wisp_y = auctioneer_y + 10 + math.sin(angle) * radius

                wisp_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(wisp_surf, (42, 42, 52, wisp_alpha), (3, 3), 3)
                surface.blit(wisp_surf, (int(wisp_x - 3), int(wisp_y - 3)))

        # Draw ghostly cloak (flowing shape below skull)
        cloak_surf = pygame.Surface((32, 40), pygame.SRCALPHA)
        cloak_alpha = int(alpha * 0.7)

        # Cloak billows slightly
        billow = math.sin(self.timer * 4) * 2
        cloak_points = [
            (16, 5),  # Top (at skull base)
            (8 + billow, 15),  # Left shoulder
            (6 + billow, 30),  # Left bottom
            (16, 35),  # Center bottom
            (26 - billow, 30),  # Right bottom
            (24 - billow, 15),  # Right shoulder
        ]
        pygame.draw.polygon(cloak_surf, (32, 32, 42, cloak_alpha), cloak_points)

        surface.blit(cloak_surf, (int(screen_x - 16), int(auctioneer_y + 5)))

        # Draw skull with more detail
        skull_surf = pygame.Surface((24, 28), pygame.SRCALPHA)

        # Skull main shape (oval)
        pygame.draw.ellipse(skull_surf, bone_color, (2, 0, 20, 24))

        # Darker shadows on skull
        pygame.draw.ellipse(skull_surf, darker_skull, (4, 2, 16, 20))

        # Eye sockets (dark hollows)
        if progress > 0.2:
            pygame.draw.ellipse(skull_surf, (0, 0, 0, alpha), (5, 8, 5, 6))
            pygame.draw.ellipse(skull_surf, (0, 0, 0, alpha), (14, 8, 5, 6))

        # Golden glowing eyes (smaller, inside sockets)
        if progress > 0.3:
            eye_alpha = int(alpha * 0.9)
            # Left eye
            pygame.draw.circle(skull_surf, (255, 215, 0, eye_alpha), (7, 11), 2)
            pygame.draw.circle(skull_surf, (255, 235, 100, eye_alpha), (7, 11), 1)  # Bright center
            # Right eye
            pygame.draw.circle(skull_surf, (255, 215, 0, eye_alpha), (17, 11), 2)
            pygame.draw.circle(skull_surf, (255, 235, 100, eye_alpha), (17, 11), 1)  # Bright center

        # Nasal cavity
        if progress > 0.4:
            nose_points = [(12, 16), (10, 19), (14, 19)]
            pygame.draw.polygon(skull_surf, (0, 0, 0, alpha), nose_points)

        # Jaw line
        if progress > 0.4:
            pygame.draw.arc(skull_surf, darker_skull, (6, 18, 12, 8), 0, math.pi, 2)

        surface.blit(skull_surf, (int(screen_x - 12), int(auctioneer_y)))

        # Gavel (enhanced hammer)
        if self.gavel_raised and progress > 0.5:
            gavel_y = auctioneer_y + 24  # Below skull
            # Gavel raised high with slight pulse
            gavel_offset = -12 if self.gavel_raised else 0

            # Draw gavel handle (thicker)
            pygame.draw.line(surface, (101, 67, 33),
                           (int(screen_x + 6), int(gavel_y + gavel_offset)),
                           (int(screen_x + 6), int(gavel_y + gavel_offset + 10)), 3)

            # Draw gavel head (larger and more detailed)
            gavel_head_x = int(screen_x + 2)
            gavel_head_y = int(gavel_y + gavel_offset - 3)
            # Main hammer head
            pygame.draw.rect(surface, (139, 69, 19), (gavel_head_x, gavel_head_y, 8, 5))
            # Darker edge
            pygame.draw.rect(surface, (101, 67, 33), (gavel_head_x, gavel_head_y, 8, 5), 1)


class GavelSlam:
    """
    Impact rings and visual effects when gavel slams down.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 0.5
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Multiple expanding rings
        num_rings = 3
        for i in range(num_rings):
            ring_progress = (progress + i * 0.15) % 1.0
            radius = int(10 + ring_progress * 25)
            alpha = int(180 * (1 - ring_progress))

            if alpha > 0 and radius < 40:
                ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                # Gold/brown impact rings
                pygame.draw.circle(ring_surf, (218, 165, 32, alpha), (radius, radius), radius, 3)
                surface.blit(ring_surf, (int(self.x - radius), int(self.y - radius)))


class CurseBeam:
    """
    Twisted crimson curse energy beam with spiral pattern and particles.
    """
    def __init__(self, start_x, start_y, target_x, target_y, camera, start_delay=0.0):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.camera = camera
        self.start_delay = start_delay
        self.timer = -start_delay
        self.duration = 0.8
        self.active = True
        # Particle trail storage
        self.particles = []

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        # Beam shoots from start to target
        progress = min(1.0, self.timer / self.duration)

        # Calculate current end point
        current_end_x = self.start_x + (self.target_x - self.start_x) * progress
        current_end_y = self.start_y + (self.target_y - self.start_y) * progress

        # Dark gray curse color (shifts from brown to dark gray)
        red = int(139 - (139 - 44) * progress)  # Brown → dark gray
        green = int(69 - (69 - 44) * progress)  # Brown → dark gray
        blue = int(19 + (44 - 19) * progress)   # Brown → dark gray
        alpha = int(220 * progress)
        color = (red, green, blue, alpha)

        # Calculate beam direction for perpendicular offset
        dx = current_end_x - self.start_x
        dy = current_end_y - self.start_y
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            # Normalized perpendicular vector
            perp_x = -dy / length
            perp_y = dx / length

            # Draw main beam with spiral/helix pattern
            num_segments = 30
            for i in range(num_segments):
                t1 = i / num_segments
                t2 = (i + 1) / num_segments

                # Spiral effect: rotate offset around beam axis
                spiral_angle = t1 * math.pi * 6 + self.timer * 8
                spiral_radius = 4 + math.sin(t1 * math.pi * 3) * 2

                offset1_x = perp_x * math.cos(spiral_angle) * spiral_radius
                offset1_y = perp_y * math.cos(spiral_angle) * spiral_radius

                spiral_angle2 = t2 * math.pi * 6 + self.timer * 8
                offset2_x = perp_x * math.cos(spiral_angle2) * spiral_radius
                offset2_y = perp_y * math.cos(spiral_angle2) * spiral_radius

                x1 = self.start_x + (current_end_x - self.start_x) * t1 + offset1_x
                y1 = self.start_y + (current_end_y - self.start_y) * t1 + offset1_y

                x2 = self.start_x + (current_end_x - self.start_x) * t2 + offset2_x
                y2 = self.start_y + (current_end_y - self.start_y) * t2 + offset2_y

                # Pulsing width
                width = int(3 + math.sin(self.timer * 10 + t1 * 5) * 1)
                pygame.draw.line(surface, color, (int(x1), int(y1)), (int(x2), int(y2)), width)

            # Draw core beam (brighter gray, thinner)
            core_alpha = int(255 * progress)
            pygame.draw.line(surface, (80, 80, 80, core_alpha),
                           (int(self.start_x), int(self.start_y)),
                           (int(current_end_x), int(current_end_y)), 1)

            # Dark energy particles along beam
            if progress > 0.1:
                num_particles = int(progress * 8)
                for i in range(num_particles):
                    t = (i / num_particles + self.timer * 0.5) % 1.0
                    if t < progress:  # Only show particles on traveled portion
                        px = self.start_x + (current_end_x - self.start_x) * t
                        py = self.start_y + (current_end_y - self.start_y) * t

                        # Orbital offset
                        orbit_angle = t * math.pi * 8 + self.timer * 6
                        orbit_radius = 6
                        px += math.cos(orbit_angle) * orbit_radius
                        py += math.sin(orbit_angle) * orbit_radius

                        particle_alpha = int(180 * (1 - t) * progress)
                        if particle_alpha > 0:
                            particle_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                            pygame.draw.circle(particle_surf, (42, 42, 42, particle_alpha), (2, 2), 2)
                            surface.blit(particle_surf, (int(px - 2), int(py - 2)))

            # Lightning branches (occasional splits)
            if progress > 0.3 and int(self.timer * 10) % 3 == 0:
                branch_progress = (progress - 0.3) / 0.7
                for i in range(2):
                    branch_t = 0.4 + i * 0.2
                    if branch_t < progress:
                        branch_x = self.start_x + (current_end_x - self.start_x) * branch_t
                        branch_y = self.start_y + (current_end_y - self.start_y) * branch_t

                        # Branch splits off at angle
                        angle_offset = (i * 2 - 1) * math.pi / 6  # ±30 degrees
                        branch_length = 15 * branch_progress
                        branch_end_x = branch_x + math.cos(angle_offset) * branch_length * perp_x
                        branch_end_y = branch_y + math.cos(angle_offset) * branch_length * perp_y

                        branch_alpha = int(150 * branch_progress)
                        pygame.draw.line(surface, (58, 58, 58, branch_alpha),
                                       (int(branch_x), int(branch_y)),
                                       (int(branch_end_x), int(branch_end_y)), 2)


class AuctionCurseAnimation:
    """
    Auction Curse skill animation for DELPHIC APPRAISER.
    Ghostly auction house with cursed bidding war.

    Phases:
    1. Podium Ascension - Brown podiums rise at furniture locations
    2. Auctioneer Manifestation - Ghostly auctioneers appear
    3. Bidding Frenzy - Gavels raise, curse energy sparks
    4. Curse Convergence - Red beams converge on target
    5. Aftermath - Curse aura remains on target
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Auction Curse animation.

        Args:
            target_pos: (grid_y, grid_x) - the cursed enemy unit
            game: Game instance to access map/furniture data
        """
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert target position to screen coords
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "podiums"  # podiums -> auctioneers -> bidding -> convergence -> aftermath
        self.timer = 0
        self.active = True

        # Sub-effects
        self.podiums = []
        self.auctioneers = []
        self.curse_beams = []
        self.gavel_slams = []
        self.furniture_positions = []  # Screen coords of furniture

        # Find furniture within 2 tiles of target
        self._find_nearby_furniture()

        # Start Phase 1
        self._start_podium_phase()

    def _find_nearby_furniture(self):
        """Find all furniture within 2 tiles of target."""
        if not self.game or not hasattr(self.game, 'map') or not self.game.map:
            return

        grid_y, grid_x = self.target_pos

        from boneglaive.game.map import TerrainType
        furniture_types = {
            TerrainType.RADIO_CONSOLE, TerrainType.COAT_RACK, TerrainType.OTTOMAN,
            TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF, TerrainType.TIFFANY_LAMP,
            TerrainType.EASEL, TerrainType.SCULPTURE, TerrainType.BENCH,
            TerrainType.PODIUM, TerrainType.VASE, TerrainType.WORKBENCH,
            TerrainType.COUCH, TerrainType.TOOLBOX, TerrainType.COT,
            TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN, TerrainType.POTPOURRI_BOWL
        }

        # Check 2-tile radius (5×5 area)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                tile_grid_x = grid_x + dx
                tile_grid_y = grid_y + dy

                # Check bounds
                if (0 <= tile_grid_y < self.game.map.height and
                    0 <= tile_grid_x < self.game.map.width):

                    terrain = self.game.map.terrain.get((tile_grid_y, tile_grid_x), TerrainType.EMPTY)
                    if terrain in furniture_types:
                        # Convert to screen coords
                        screen_x, screen_y = self.camera.grid_to_screen(
                            tile_grid_x, tile_grid_y, centered=True
                        )
                        self.furniture_positions.append((screen_x, screen_y))

    def _start_podium_phase(self):
        """Phase 1: Podiums rise at furniture locations."""
        self.phase = "podiums"
        self.timer = 0

        # Create podium for each furniture
        for i, (fx, fy) in enumerate(self.furniture_positions):
            delay = i * 0.05  # Stagger slightly
            self.podiums.append(PodiumRise(fx, fy, self.camera, start_delay=delay))

    def _start_auctioneer_phase(self):
        """Phase 2: Ghostly auctioneers manifest."""
        self.phase = "auctioneers"
        self.timer = 0

        # Create auctioneer for each podium
        for i, (fx, fy) in enumerate(self.furniture_positions):
            delay = i * 0.04
            self.auctioneers.append(AuctioneerGhost(fx, fy, self.camera, start_delay=delay))

    def _start_bidding_phase(self):
        """Phase 3: Bidding frenzy - gavels raise and slam."""
        self.phase = "bidding"
        self.timer = 0

        # Raise all gavels
        for auctioneer in self.auctioneers:
            auctioneer.raise_gavel()

        # Create gavel slam impact rings at each podium (slight delay)
        for i, (fx, fy) in enumerate(self.furniture_positions):
            # Slams happen shortly after gavels raise
            self.gavel_slams.append(GavelSlam(fx, fy - 10))  # Slightly above podium

        # Screen shake for dramatic effect
        self.screen_shake_callback(4, 1.0)

    def _start_convergence_phase(self):
        """Phase 4: Curse beams converge on target."""
        self.phase = "convergence"
        self.timer = 0

        # Create curse beam from each auctioneer to target
        for i, (fx, fy) in enumerate(self.furniture_positions):
            delay = i * 0.03
            # Beam starts from auctioneer position (above podium)
            start_y = fy - 40
            self.curse_beams.append(CurseBeam(fx, start_y, self.target_x, self.target_y,
                                             self.camera, start_delay=delay))

        # Screen shake on impact (no flash)
        self.screen_shake_callback(8, 0.8)

    def _start_aftermath_phase(self):
        """Phase 5: Curse aura remains."""
        self.phase = "aftermath"
        self.timer = 0

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "podiums" and self.timer >= 0.8:
            self._start_auctioneer_phase()
        elif self.phase == "auctioneers" and self.timer >= 0.6:
            self._start_bidding_phase()
        elif self.phase == "bidding" and self.timer >= 1.0:
            self._start_convergence_phase()
        elif self.phase == "convergence" and self.timer >= 0.8:
            self._start_aftermath_phase()
        elif self.phase == "aftermath" and self.timer >= 0.8:  # Extended duration
            self.active = False

        # Update sub-effects
        for podium in self.podiums:
            podium.update(delta_time)

        for auctioneer in self.auctioneers:
            auctioneer.update(delta_time)

        for slam in self.gavel_slams:
            slam.update(delta_time)

        for beam in self.curse_beams:
            beam.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        # Draw podiums
        for podium in self.podiums:
            podium.draw(surface)

        # Draw auctioneers
        for auctioneer in self.auctioneers:
            auctioneer.draw(surface)

        # Draw gavel slam impact rings
        for slam in self.gavel_slams:
            slam.draw(surface)

        # Draw curse beams
        for beam in self.curse_beams:
            beam.draw(surface)

        # Draw curse aura on target (aftermath phase)
        if self.phase == "aftermath":
            aftermath_progress = self.timer / 0.8

            # Pulsing crimson aura (multiple rings)
            pulse = (math.sin(self.timer * 8) + 1) / 2
            base_alpha = int(180 * (1.0 - aftermath_progress))  # Fade out gradually

            # Inner golden aura
            if base_alpha > 0:
                inner_radius = int(25 + 8 * pulse)
                inner_surf = pygame.Surface((inner_radius * 2, inner_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(inner_surf, (218, 165, 32, base_alpha), (inner_radius, inner_radius), inner_radius)
                surface.blit(inner_surf, (int(self.target_x - inner_radius), int(self.target_y - inner_radius)))

                # Outer golden expanding ring
                outer_radius = int(35 + 12 * pulse)
                outer_alpha = int(base_alpha * 0.6)
                outer_surf = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(outer_surf, (255, 215, 0, outer_alpha), (outer_radius, outer_radius), outer_radius, 3)
                surface.blit(outer_surf, (int(self.target_x - outer_radius), int(self.target_y - outer_radius)))

                # Pulsing dark gray rings expanding from target
                num_rings = 3
                for i in range(num_rings):
                    ring_progress = (aftermath_progress + i * 0.2) % 1.0
                    ring_radius = int(20 + ring_progress * 40)
                    ring_alpha = int(base_alpha * (1 - ring_progress) * 0.5)

                    if ring_alpha > 0:
                        ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(ring_surf, (44, 44, 44, ring_alpha), (ring_radius, ring_radius), ring_radius, 2)
                        surface.blit(ring_surf, (int(self.target_x - ring_radius), int(self.target_y - ring_radius)))

                # Enhanced heal-block symbol (larger, pulsing golden X)
                x_size = int(15 + 3 * pulse)
                x_alpha = int(base_alpha * 1.2)
                x_color = (255, 215, 0, min(255, x_alpha))

                # Draw X with outline for visibility
                for offset in [(0, 0), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                    ox, oy = offset
                    if ox == 0 and oy == 0:
                        width = 4  # Main X is thicker
                    else:
                        width = 2  # Outline is thinner
                        x_color = (218, 165, 32, x_alpha)

                    pygame.draw.line(surface, x_color,
                                   (int(self.target_x - x_size + ox), int(self.target_y - x_size + oy)),
                                   (int(self.target_x + x_size + ox), int(self.target_y + x_size + oy)), width)
                    pygame.draw.line(surface, x_color,
                                   (int(self.target_x + x_size + ox), int(self.target_y - x_size + oy)),
                                   (int(self.target_x - x_size + ox), int(self.target_y + x_size + oy)), width)

                # Furniture DoT visual: dark energy from furniture to target
                if len(self.furniture_positions) > 0 and aftermath_progress < 0.7:
                    # Show periodic "damage ticks" from furniture
                    tick_cycle = int(self.timer * 4) % 2
                    if tick_cycle == 0:
                        for i, (fx, fy) in enumerate(self.furniture_positions):
                            # Limit to closest 3 furniture pieces for clarity
                            if i < 3:
                                # Dark sparkles from furniture
                                spark_progress = (self.timer * 4) % 1.0
                                spark_x = fx + (self.target_x - fx) * spark_progress
                                spark_y = fy + (self.target_y - fy) * spark_progress

                                spark_alpha = int(120 * (1 - spark_progress) * (1 - aftermath_progress))
                                if spark_alpha > 0:
                                    spark_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                                    pygame.draw.circle(spark_surf, (139, 69, 19, spark_alpha), (3, 3), 3)
                                    surface.blit(spark_surf, (int(spark_x - 3), int(spark_y - 3)))

                # Furniture pulsing with gray curse energy
                for i, (fx, fy) in enumerate(self.furniture_positions):
                    if i < 4:  # Show on nearest furniture
                        furniture_pulse = (math.sin(self.timer * 6 + i) + 1) / 2
                        furniture_alpha = int(100 * furniture_pulse * (1 - aftermath_progress))

                        if furniture_alpha > 0:
                            furniture_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                            pygame.draw.circle(furniture_surf, (58, 58, 58, furniture_alpha), (10, 10), 8)
                            surface.blit(furniture_surf, (int(fx - 10), int(fy - 10)))


# ============================================================================
# MARKET FUTURES ANIMATION
# ============================================================================

class GoldenScannerBeam:
    """
    Golden appraiser beam that sweeps across the furniture during assessment phase.
    """
    def __init__(self, center_x, center_y, angle, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.angle = angle
        self.timer = -delay
        self.duration = 0.6
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Beam sweeps outward
        beam_length = 60 * progress
        end_x = self.center_x + math.cos(self.angle) * beam_length
        end_y = self.center_y + math.sin(self.angle) * beam_length

        # Golden scanner beam with fade
        alpha = int(200 * (1 - progress * 0.5))
        color = (255, 215, 0, alpha)  # Gold

        # Draw beam
        pygame.draw.line(surface, color,
                        (int(self.center_x), int(self.center_y)),
                        (int(end_x), int(end_y)), 3)

        # Bright point at end
        if beam_length > 10:
            point_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(point_surf, (255, 235, 100, alpha), (4, 4), 4)
            surface.blit(point_surf, (int(end_x - 4), int(end_y - 4)))


class TemporalRift:
    """
    Swirling golden portal/rift opening with clock particles and temporal distortion.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.8
        self.active = True

        # Clock particles - arrows and symbols
        self.clock_particles = []
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            self.clock_particles.append({
                'angle': angle,
                'base_distance': 25,
                'symbol': i % 4  # 0: up arrow, 1: right, 2: down, 3: left
            })

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expanding rift rings
        num_rings = 3
        for i in range(num_rings):
            ring_offset = i * 0.2
            ring_progress = min(1.0, max(0, (progress - ring_offset) / (1 - ring_offset)))

            if ring_progress > 0:
                radius = int(15 + ring_progress * 35)
                alpha = int(180 * (1 - ring_progress * 0.7))

                # Gold to goldenrod gradient
                if ring_progress < 0.5:
                    color = (255, 215, 0, alpha)
                else:
                    color = (218, 165, 32, alpha)

                ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, color, (radius, radius), radius, 3)
                surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))

        # Rotating clock particles
        if progress > 0.2:
            for p in self.clock_particles:
                # Spiral inward
                distance = p['base_distance'] * (1 + progress)
                angle = p['angle'] + progress * math.pi * 2

                px = self.center_x + math.cos(angle) * distance
                py = self.center_y + math.sin(angle) * distance

                alpha = int(220 * progress)

                # Draw arrow based on symbol
                arrow_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                if p['symbol'] == 0:  # Up arrow
                    points = [(3, 1), (1, 4), (5, 4)]
                elif p['symbol'] == 1:  # Right arrow
                    points = [(5, 3), (2, 1), (2, 5)]
                elif p['symbol'] == 2:  # Down arrow
                    points = [(3, 5), (1, 2), (5, 2)]
                else:  # Left arrow
                    points = [(1, 3), (4, 1), (4, 5)]

                pygame.draw.polygon(arrow_surf, (255, 215, 0, alpha), points)
                surface.blit(arrow_surf, (int(px - 3), int(py - 3)))


class InvestmentAnchor:
    """
    Golden anchor symbol that materializes and embeds into furniture.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.7
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Anchor descends and solidifies
        y_offset = int(-30 * (1 - progress))  # Descends from above
        alpha = int(255 * progress)

        anchor_y = self.center_y + y_offset

        # Draw anchor symbol (T shape)
        anchor_surf = pygame.Surface((20, 20), pygame.SRCALPHA)

        # Horizontal bar
        pygame.draw.line(anchor_surf, (255, 215, 0, alpha),
                        (4, 6), (16, 6), 3)
        # Vertical bar
        pygame.draw.line(anchor_surf, (255, 215, 0, alpha),
                        (10, 6), (10, 16), 3)
        # Bottom hooks
        pygame.draw.line(anchor_surf, (255, 215, 0, alpha),
                        (10, 16), (7, 14), 2)
        pygame.draw.line(anchor_surf, (255, 215, 0, alpha),
                        (10, 16), (13, 14), 2)

        # Outline for visibility
        pygame.draw.line(anchor_surf, (218, 165, 32, alpha),
                        (4, 6), (16, 6), 4)
        pygame.draw.line(anchor_surf, (218, 165, 32, alpha),
                        (10, 6), (10, 16), 4)

        surface.blit(anchor_surf, (int(self.center_x - 10), int(anchor_y - 10)))

        # Radiating waves when anchor embeds
        if progress > 0.6:
            embed_progress = (progress - 0.6) / 0.4
            wave_radius = int(20 + embed_progress * 25)
            wave_alpha = int(150 * (1 - embed_progress))

            wave_surf = pygame.Surface((wave_radius * 2, wave_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(wave_surf, (255, 215, 0, wave_alpha),
                             (wave_radius, wave_radius), wave_radius, 2)
            surface.blit(wave_surf, (int(self.center_x - wave_radius),
                                    int(anchor_y - wave_radius)))


class CurrencyOrbit:
    """
    Currency symbols ($, £, €, ¥) orbiting the furniture.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 1.0  # Continues for a while
        self.active = True

        # Currency symbols at different orbital positions
        self.symbols = [
            {'char': '$', 'offset': 0, 'radius': 30},
            {'char': '£', 'offset': math.pi / 2, 'radius': 35},
            {'char': '€', 'offset': math.pi, 'radius': 32},
            {'char': '¥', 'offset': 3 * math.pi / 2, 'radius': 37}
        ]

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Fade in, then stay visible
        if progress < 0.3:
            alpha = int(200 * (progress / 0.3))
        else:
            alpha = 200

        font = pygame.font.Font(None, 24)

        for sym in self.symbols:
            # Orbital rotation
            angle = sym['offset'] + self.timer * 2  # Rotate over time
            sx = self.center_x + math.cos(angle) * sym['radius']
            sy = self.center_y + math.sin(angle) * sym['radius']

            # Render currency symbol
            text = font.render(sym['char'], True, (255, 215, 0))
            text.set_alpha(alpha)

            # Outline for visibility
            outline = font.render(sym['char'], True, (139, 69, 19))
            outline.set_alpha(alpha // 2)

            rect = text.get_rect(center=(int(sx), int(sy)))
            outline_rect = outline.get_rect(center=(int(sx) + 1, int(sy) + 1))

            surface.blit(outline, outline_rect)
            surface.blit(text, rect)


class MarketFuturesAnimation:
    """
    Market Futures skill animation for DELPHIC APPRAISER.
    Infuses furniture with temporal investment energy, creating a teleportation anchor.

    Phases:
    1. Investment Assessment - Golden scanner beams sweep furniture
    2. Temporal Rift Opening - Swirling golden portal opens
    3. Anchor Manifestation - Anchor symbol descends and embeds
    4. Investment Glow - Sustained golden aura with currency symbols
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Market Futures animation.

        Args:
            target_pos: (grid_y, grid_x) - the furniture being infused
            game: Game instance to access map/furniture data
            Other args standard from AnimationFactory
        """
        self.caster = caster_unit
        self.target_pos = target_pos  # (grid_y, grid_x) furniture position
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert target grid position to screen coords using Camera
        # target_pos is (grid_y, grid_x)
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "assessment"  # assessment -> rift -> anchor -> glow
        self.timer = 0
        self.active = True

        # Sub-effects
        self.scanner_beams = []
        self.rift = None
        self.anchor = None
        self.currency_orbit = None

        # Glow effect
        self.glow_intensity = 0

        # Start Phase 1: Investment Assessment
        self._start_assessment_phase()

    def _start_assessment_phase(self):
        """Phase 1: Golden scanner beams assess the furniture."""
        self.phase = "assessment"
        self.timer = 0

        # Create scanner beams from multiple angles
        num_beams = 8
        for i in range(num_beams):
            angle = (i / num_beams) * 2 * math.pi
            delay = i * 0.05  # Stagger beams
            self.scanner_beams.append(
                GoldenScannerBeam(self.target_x, self.target_y, angle, delay)
            )

        # Light shake for assessment
        self.screen_shake_callback(2, 0.6)

    def _start_rift_phase(self):
        """Phase 2: Temporal rift opens."""
        self.phase = "rift"
        self.timer = 0

        self.rift = TemporalRift(self.target_x, self.target_y)

        # Medium shake for rift opening
        self.screen_shake_callback(4, 0.8)

    def _start_anchor_phase(self):
        """Phase 3: Anchor manifests and embeds."""
        self.phase = "anchor"
        self.timer = 0

        self.anchor = InvestmentAnchor(self.target_x, self.target_y)

        # Light shake on anchor embedding
        self.screen_shake_callback(3, 0.5)

    def _start_glow_phase(self):
        """Phase 4: Sustained investment glow."""
        self.phase = "glow"
        self.timer = 0

        self.currency_orbit = CurrencyOrbit(self.target_x, self.target_y)

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update glow intensity based on phase
        if self.phase == "assessment":
            self.glow_intensity = min(0.3, self.timer / 0.6)
        elif self.phase == "rift":
            self.glow_intensity = 0.3 + min(0.4, self.timer / 0.8)
        elif self.phase == "anchor":
            self.glow_intensity = 0.7 + min(0.3, self.timer / 0.7)
        elif self.phase == "glow":
            # Full glow, then fade
            if self.timer < 0.2:
                self.glow_intensity = 1.0
            else:
                self.glow_intensity = max(0.4, 1.0 - (self.timer - 0.2) / 0.2)

        # Phase transitions
        if self.phase == "assessment" and self.timer >= 0.6:
            self._start_rift_phase()
        elif self.phase == "rift" and self.timer >= 0.8:
            self._start_anchor_phase()
        elif self.phase == "anchor" and self.timer >= 0.7:
            self._start_glow_phase()
        elif self.phase == "glow" and self.timer >= 0.4:
            self.active = False

        # Update sub-effects
        for beam in self.scanner_beams:
            beam.update(delta_time)

        if self.rift:
            self.rift.update(delta_time)

        if self.anchor:
            self.anchor.update(delta_time)

        if self.currency_orbit:
            self.currency_orbit.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        # Draw glow on furniture
        if self.glow_intensity > 0:
            # Pulsing golden glow
            radius = int(35 + 8 * math.sin(self.timer * 5))
            alpha = int(self.glow_intensity * 140)

            # Gold color
            color = (255, 215, 0)

            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, alpha), (radius, radius), radius)
            surface.blit(glow_surf, (int(self.target_x - radius), int(self.target_y - radius)))

            # Outer ring
            outer_radius = int(radius * 1.3)
            outer_alpha = int(alpha * 0.5)
            outer_surf = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(outer_surf, (218, 165, 32, outer_alpha),
                             (outer_radius, outer_radius), outer_radius, 3)
            surface.blit(outer_surf, (int(self.target_x - outer_radius),
                                     int(self.target_y - outer_radius)))

        # Draw phase-specific effects
        for beam in self.scanner_beams:
            beam.draw(surface)

        if self.rift:
            self.rift.draw(surface)

        if self.anchor:
            self.anchor.draw(surface)

        if self.currency_orbit:
            self.currency_orbit.draw(surface)

        # Draw lingering sparkles in glow phase
        if self.phase == "glow":
            num_sparkles = 6
            for i in range(num_sparkles):
                angle = (i / num_sparkles) * 2 * math.pi + self.timer * 3
                distance = 25 + 10 * math.sin(self.timer * 4 + i)
                sx = self.target_x + math.cos(angle) * distance
                sy = self.target_y + math.sin(angle) * distance

                sparkle_alpha = int(180 * self.glow_intensity *
                                  (0.5 + 0.5 * math.sin(self.timer * 8 + i)))

                if sparkle_alpha > 0:
                    sparkle_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                    pygame.draw.circle(sparkle_surf, (255, 235, 100, sparkle_alpha), (2, 2), 2)
                    surface.blit(sparkle_surf, (int(sx - 2), int(sy - 2)))


# ============================================================================
# MARKET FUTURES TELEPORT ANIMATION (Parallax Skill)
# ============================================================================

class CurrencyParticle:
    """
    Currency symbol particle that streams from start to destination.
    Dissolves unit into golden currency, streams along path, reconstitutes at destination.
    """
    def __init__(self, start_x, start_y, end_x, end_y, symbol, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.symbol = symbol  # '$', '£', '€', '¥'
        self.timer = -delay
        self.duration = 0.6
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Spiral motion along path
        base_x = self.start_x + (self.end_x - self.start_x) * progress
        base_y = self.start_y + (self.end_y - self.start_y) * progress

        # Add spiral offset
        spiral_radius = 15 * (0.5 - abs(progress - 0.5))  # Spiral outward then inward
        spiral_angle = progress * math.pi * 4
        px = base_x + math.cos(spiral_angle) * spiral_radius
        py = base_y + math.sin(spiral_angle) * spiral_radius

        # Alpha fades in and out
        alpha = int(255 * (1.0 - abs(progress - 0.5) * 2))

        # Render currency symbol
        font = pygame.font.Font(None, 28)
        text = font.render(self.symbol, True, (255, 215, 0))  # Gold
        text.set_alpha(alpha)

        rect = text.get_rect(center=(int(px), int(py)))
        surface.blit(text, rect)


class InvestmentOrbitParticle:
    """
    Orbiting currency symbol for investment buff visual.
    """
    def __init__(self, center_x, center_y, symbol, angle_offset, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.symbol = symbol
        self.angle_offset = angle_offset
        self.timer = -delay
        self.duration = 1.0  # Continues orbiting
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Orbital motion
        angle = self.angle_offset + self.timer * 2
        radius = 30 + 5 * math.sin(self.timer * 4)
        px = self.center_x + math.cos(angle) * radius
        py = self.center_y + math.sin(angle) * radius

        # Fade in
        alpha = int(200 * min(1.0, progress / 0.3))

        # Render currency symbol
        font = pygame.font.Font(None, 24)
        text = font.render(self.symbol, True, (255, 215, 0))  # Gold
        text.set_alpha(alpha)

        rect = text.get_rect(center=(int(px), int(py)))
        surface.blit(text, rect)


class MarketFuturesTeleportAnimation:
    """
    Market Futures teleportation animation for Parallax skill.
    Unit dissolves into golden currency particles, streams to destination, reconstitutes.

    Phases:
    1. Anchor Glow - Pulsing golden energy at anchor
    2. Dissolve - Unit dissolves into golden currency particles
    3. Transit - Particles stream along path with spiral pattern
    4. Rematerialize - Particles converge and reform at destination
    5. Investment Aura - Golden investment buff visual
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Market Futures Teleport animation.

        Args:
            caster_unit: Unit being teleported
            target_pos: (grid_y, grid_x) - destination position
            camera: Camera instance for coordinate conversion
            Other args standard from AnimationFactory
        """
        self.caster = caster_unit
        self.target_pos = target_pos  # (grid_y, grid_x) destination
        self.camera = camera
        self.particle_emitter = particle_emitter
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert positions to screen coords
        # Start position (caster's current location)
        self.start_x, self.start_y = camera.grid_to_screen(caster_unit.grid_x, caster_unit.grid_y, centered=True)

        # End position (destination)
        grid_y, grid_x = target_pos
        self.end_x, self.end_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Find the anchor position for anchor glow
        self.anchor_x = None
        self.anchor_y = None
        if game and hasattr(game, 'teleport_anchors'):
            for anchor_pos, anchor in game.teleport_anchors.items():
                if anchor['active'] and anchor['creator'].player == caster_unit.player:
                    # Check if caster is adjacent
                    if game.chess_distance(caster_unit.grid_y, caster_unit.grid_x, anchor_pos[0], anchor_pos[1]) <= 1:
                        anchor_grid_y, anchor_grid_x = anchor_pos
                        self.anchor_x, self.anchor_y = camera.grid_to_screen(anchor_grid_x, anchor_grid_y, centered=True)
                        break

        # Animation state
        self.phase = "anchor_glow"  # anchor_glow -> dissolve -> transit -> rematerialize -> investment
        self.timer = 0
        self.active = True

        # Sub-effects
        self.currency_particles = []
        self.investment_particles = []
        self.glow_intensity = 0

        # Start Phase 1: Anchor Glow
        self._start_anchor_glow_phase()

    def _start_anchor_glow_phase(self):
        """Phase 1: Anchor glows with golden energy."""
        self.phase = "anchor_glow"
        self.timer = 0
        self.screen_shake_callback(2, 0.4)  # Light shake

    def _start_dissolve_phase(self):
        """Phase 2: Unit dissolves into currency particles."""
        self.phase = "dissolve"
        self.timer = 0

        # Hide unit while dissolving (will reappear at destination)
        self.caster.visible = False

        # Create currency particles at start position
        symbols = ['$', '£', '€', '¥']
        for i in range(20):
            symbol = symbols[i % len(symbols)]
            delay = i * 0.02
            # Particles will stream from start to end
            self.currency_particles.append(
                CurrencyParticle(self.start_x, self.start_y, self.end_x, self.end_y, symbol, delay)
            )

    def _start_transit_phase(self):
        """Phase 3: Currency particles stream to destination."""
        self.phase = "transit"
        self.timer = 0

    def _start_rematerialize_phase(self):
        """Phase 4: Particles converge at destination."""
        self.phase = "rematerialize"
        self.timer = 0

        # Move caster unit to destination position
        grid_y, grid_x = self.target_pos
        self.caster.grid_x = grid_x
        self.caster.grid_y = grid_y
        self.caster.x, self.caster.y = self.camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Show unit at new position
        self.caster.visible = True

    def _start_investment_phase(self):
        """Phase 5: Investment buff visual with orbiting currency."""
        self.phase = "investment"
        self.timer = 0

        # Create investment orbit particles
        symbols = ['$', '£', '€', '¥']
        for i, symbol in enumerate(symbols):
            angle_offset = (i / len(symbols)) * 2 * math.pi
            self.investment_particles.append(
                InvestmentOrbitParticle(self.end_x, self.end_y, symbol, angle_offset, delay=0)
            )

        self.screen_shake_callback(3, 0.5)  # Medium shake on arrival

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Update glow intensity
        if self.phase == "anchor_glow":
            self.glow_intensity = min(1.0, self.timer / 0.4)
        elif self.phase == "dissolve":
            self.glow_intensity = max(0, 1.0 - self.timer / 0.3)
        elif self.phase == "investment":
            self.glow_intensity = min(1.0, self.timer / 0.3)

        # Phase transitions
        if self.phase == "anchor_glow" and self.timer >= 0.4:
            self._start_dissolve_phase()
        elif self.phase == "dissolve" and self.timer >= 0.3:
            self._start_transit_phase()
        elif self.phase == "transit" and self.timer >= 0.6:
            self._start_rematerialize_phase()
        elif self.phase == "rematerialize" and self.timer >= 0.3:
            self._start_investment_phase()
        elif self.phase == "investment" and self.timer >= 1.0:
            self.active = False

        # Update sub-effects
        for particle in self.currency_particles:
            particle.update(delta_time)

        for particle in self.investment_particles:
            particle.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        # Draw anchor glow (if anchor position is known)
        if self.anchor_x and self.anchor_y and self.phase in ["anchor_glow", "dissolve"]:
            radius = int(40 + 10 * math.sin(self.timer * 8))
            alpha = int(self.glow_intensity * 150)
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (radius, radius), radius)
            surface.blit(glow_surf, (int(self.anchor_x - radius), int(self.anchor_y - radius)))

        # Draw dissolve/rematerialize glow at start/end positions
        if self.phase in ["dissolve", "transit"]:
            # Glow at start position (fading)
            radius = int(35 + 8 * math.sin(self.timer * 6))
            alpha = int(self.glow_intensity * 120)
            if alpha > 0:
                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (radius, radius), radius)
                surface.blit(glow_surf, (int(self.start_x - radius), int(self.start_y - radius)))

        if self.phase in ["rematerialize", "investment"]:
            # Glow at end position (brightening)
            radius = int(40 + 10 * math.sin(self.timer * 7))
            alpha = int(self.glow_intensity * 160)
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (radius, radius), radius)
            surface.blit(glow_surf, (int(self.end_x - radius), int(self.end_y - radius)))

        # Draw currency particles
        for particle in self.currency_particles:
            particle.draw(surface)

        # Draw investment orbit particles
        for particle in self.investment_particles:
            particle.draw(surface)

        # Draw connecting golden line during transit
        if self.phase == "transit":
            line_alpha = int(100 * (0.5 + 0.5 * math.sin(self.timer * 10)))
            if line_alpha > 0:
                pygame.draw.line(surface, (218, 165, 32, line_alpha),
                               (int(self.start_x), int(self.start_y)),
                               (int(self.end_x), int(self.end_y)), 2)


# ============================================================================
# AUCTION CURSE TICK ANIMATION (DOT Effect)
# ============================================================================

class CurseSeethingEffect:
    """
    Dark curse energy seething and bubbling around the afflicted unit.
    Particles orbit and pulse with malevolent energy.
    """
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = 0
        self.duration = 0.5
        self.active = True

        # Create orbiting curse particles
        self.particles = []
        num_particles = 12
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            self.particles.append({
                'base_angle': angle,
                'orbit_radius': random.uniform(20, 35),
                'orbit_speed': random.uniform(3, 5),
                'size': random.uniform(3, 6),
                'pulse_offset': random.uniform(0, math.pi * 2)
            })

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        progress = min(1.0, self.timer / self.duration)

        # Pulsing dark aura around cursed unit
        pulse = (math.sin(self.timer * 12) + 1) / 2
        aura_radius = int(30 + 10 * pulse * progress)
        aura_alpha = int(140 * progress)

        if aura_alpha > 0:
            aura_surf = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (44, 44, 44, aura_alpha), (aura_radius, aura_radius), aura_radius)
            surface.blit(aura_surf, (int(self.center_x - aura_radius), int(self.center_y - aura_radius)))

        # Orbiting curse particles
        for p in self.particles:
            angle = p['base_angle'] + self.timer * p['orbit_speed']
            radius = p['orbit_radius'] * progress

            px = self.center_x + math.cos(angle) * radius
            py = self.center_y + math.sin(angle) * radius

            # Pulsing size
            size_pulse = (math.sin(self.timer * 8 + p['pulse_offset']) + 1) / 2
            size = p['size'] * (0.7 + 0.3 * size_pulse) * progress

            alpha = int(200 * progress)

            if size > 0.5 and alpha > 0:
                particle_surf = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (42, 42, 42, alpha), (int(size), int(size)), int(size))
                surface.blit(particle_surf, (int(px - size), int(py - size)))


class CurseRadiationWave:
    """
    Expanding wave of curse energy radiating from the afflicted unit.
    Shows corruption spreading outward to furniture.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.6
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Expanding ring of dark curse energy
        radius = int(progress * 160)  # Expands to reach 2.5 tiles (160px = ~2.5 tiles)
        alpha = int(180 * (1.0 - progress * 0.7))  # Fade as expanding

        if radius > 0 and alpha > 0:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            # Dark gray curse color
            pygame.draw.circle(ring_surf, (44, 44, 44, alpha), (radius, radius), radius, 4)
            surface.blit(ring_surf, (int(self.center_x - radius), int(self.center_y - radius)))

            # Inner darker ring for depth
            inner_radius = int(radius * 0.8)
            inner_alpha = int(alpha * 0.6)
            if inner_radius > 0:
                pygame.draw.circle(ring_surf, (42, 42, 42, inner_alpha), (radius, radius), inner_radius, 2)


class CurseTendril:
    """
    Dark energy tendril reaching from cursed unit to furniture piece.
    Shows curse corrupting and inflating furniture value.
    """
    def __init__(self, start_x, start_y, end_x, end_y, delay=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Tendril extends from cursed unit to furniture
        current_end_x = self.start_x + (self.end_x - self.start_x) * progress
        current_end_y = self.start_y + (self.end_y - self.start_y) * progress

        # Dark curse color with fade
        alpha = int(200 * progress * (1.0 - progress * 0.5))

        if alpha > 0:
            # Wavy tendril effect
            num_segments = 10
            points = []
            for i in range(num_segments + 1):
                t = i / num_segments
                base_x = self.start_x + (current_end_x - self.start_x) * t
                base_y = self.start_y + (current_end_y - self.start_y) * t

                # Sine wave perpendicular to direction
                wave_offset = math.sin(t * math.pi * 3 + self.timer * 10) * 3
                dx = current_end_y - self.start_y
                dy = -(current_end_x - self.start_x)
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    dx /= length
                    dy /= length
                    base_x += dx * wave_offset
                    base_y += dy * wave_offset

                points.append((int(base_x), int(base_y)))

            # Draw tendril as connected line segments
            for i in range(len(points) - 1):
                pygame.draw.line(surface, (44, 44, 44, alpha), points[i], points[i+1], 2)


class FurnitureCorruptionFlash:
    """
    Furniture piece pulses when hit by curse energy.
    Shows corruption affecting the furniture.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.4
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # Flash effect: quick bright pulse then fade
        if progress < 0.3:
            # Initial flash (bright)
            flash_progress = progress / 0.3
            alpha = int(220 * flash_progress)
            color = (139, 69, 19, alpha)  # Brown curse corruption
        else:
            # Fade out
            fade_progress = (progress - 0.3) / 0.7
            alpha = int(180 * (1.0 - fade_progress))
            # Shift to darker color
            color = (int(139 - 95 * fade_progress), int(69 - 25 * fade_progress), int(19 + 25 * fade_progress), alpha)

        if alpha > 0:
            # Pulsing circle
            pulse = (math.sin(self.timer * 15) + 1) / 2
            radius = int(25 + 8 * pulse)

            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, color, (radius, radius), radius)
            surface.blit(glow_surf, (int(self.center_x - radius), int(self.center_y - radius)))


class ValueInflationNumber:
    """
    Shows "+1" inflation effect on furniture.
    Gold/brown colors showing value being corrupted upward.
    """
    def __init__(self, center_x, center_y, delay=0):
        self.center_x = center_x
        self.center_y = center_y
        self.timer = -delay
        self.duration = 0.6
        self.active = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.timer < 0:
            return

        progress = min(1.0, self.timer / self.duration)

        # +1 rises and fades
        y_offset = -int(progress * 20)  # Rise upward
        alpha = int(255 * (1.0 - progress))

        if alpha > 0:
            # Gold color for greed/inflation
            font = pygame.font.Font(None, 32)
            text = font.render("+1", True, (255, 215, 0))
            text.set_alpha(alpha)

            # Outline for visibility
            outline = font.render("+1", True, (139, 69, 19))
            outline.set_alpha(alpha // 2)

            text_rect = text.get_rect(center=(int(self.center_x), int(self.center_y + y_offset)))
            outline_rect = outline.get_rect(center=(int(self.center_x + 1), int(self.center_y + y_offset + 1)))

            surface.blit(outline, outline_rect)
            surface.blit(text, text_rect)


class AuctionCurseTickAnimation:
    """
    Auction Curse periodic damage tick animation.
    Shows curse seething from afflicted unit, radiating to furniture, inflating values.

    Phases:
    1. Curse Seething - Dark energy bubbles around cursed unit
    2. Curse Radiation - Energy waves expand outward to furniture
    3. Furniture Corruption - Furniture pulses and values inflate
    4. Damage Feedback - Energy contracts, damage dealt
    """

    def __init__(self, caster_unit, target_unit, target_pos, is_crit, is_infused,
                 particle_emitter, debris_list, screen_shake_callback,
                 screen_flash_callback, units_list, camera, game=None):
        """
        Initialize Auction Curse Tick animation.

        Args:
            target_pos: (grid_y, grid_x) - position of cursed unit taking damage
            game: Game instance to find nearby furniture
        """
        self.caster = caster_unit
        self.target_unit = target_unit
        self.target_pos = target_pos
        self.camera = camera
        self.screen_shake_callback = screen_shake_callback
        self.screen_flash_callback = screen_flash_callback
        self.game = game

        # Convert cursed unit position to screen coords
        grid_y, grid_x = target_pos
        self.target_x, self.target_y = camera.grid_to_screen(grid_x, grid_y, centered=True)

        # Animation state
        self.phase = "seething"  # seething -> radiation -> corruption -> feedback
        self.timer = 0
        self.active = True

        # Sub-effects
        self.seething_effect = None
        self.radiation_waves = []
        self.curse_tendrils = []
        self.corruption_flashes = []
        self.inflation_numbers = []
        self.furniture_positions = []  # Screen coords of nearby furniture

        # Find nearby furniture
        self._find_nearby_furniture()

        # Start Phase 1
        self._start_seething_phase()

    def _find_nearby_furniture(self):
        """Find all furniture within 2 tiles of cursed unit."""
        if not self.game or not hasattr(self.game, 'map') or not self.game.map:
            return

        grid_y, grid_x = self.target_pos

        from boneglaive.game.map import TerrainType
        furniture_types = {
            TerrainType.RADIO_CONSOLE, TerrainType.COAT_RACK, TerrainType.OTTOMAN,
            TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF, TerrainType.TIFFANY_LAMP,
            TerrainType.EASEL, TerrainType.SCULPTURE, TerrainType.BENCH,
            TerrainType.PODIUM, TerrainType.VASE, TerrainType.WORKBENCH,
            TerrainType.COUCH, TerrainType.TOOLBOX, TerrainType.COT,
            TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN, TerrainType.POTPOURRI_BOWL
        }

        # Check 2-tile radius (5×5 area)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                tile_grid_x = grid_x + dx
                tile_grid_y = grid_y + dy

                # Check bounds
                if (0 <= tile_grid_y < self.game.map.height and
                    0 <= tile_grid_x < self.game.map.width):

                    terrain = self.game.map.terrain.get((tile_grid_y, tile_grid_x), TerrainType.EMPTY)
                    if terrain in furniture_types:
                        # Convert to screen coords
                        screen_x, screen_y = self.camera.grid_to_screen(
                            tile_grid_x, tile_grid_y, centered=True
                        )
                        # Store with distance for staggering
                        distance = abs(dx) + abs(dy)
                        self.furniture_positions.append((screen_x, screen_y, distance))

    def _start_seething_phase(self):
        """Phase 1: Curse seethes around afflicted unit."""
        self.phase = "seething"
        self.timer = 0

        self.seething_effect = CurseSeethingEffect(self.target_x, self.target_y)
        self.screen_shake_callback(3, 0.5)

    def _start_radiation_phase(self):
        """Phase 2: Curse radiates outward to furniture."""
        self.phase = "radiation"
        self.timer = 0

        # Create radiation waves
        self.radiation_waves = [
            CurseRadiationWave(self.target_x, self.target_y, delay=0),
            CurseRadiationWave(self.target_x, self.target_y, delay=0.15),
            CurseRadiationWave(self.target_x, self.target_y, delay=0.3),
        ]

        # Create tendrils to furniture (staggered by distance)
        for fx, fy, distance in self.furniture_positions:
            delay = distance * 0.05
            self.curse_tendrils.append(
                CurseTendril(self.target_x, self.target_y, fx, fy, delay=delay)
            )

    def _start_corruption_phase(self):
        """Phase 3: Furniture corrupted, values inflate."""
        self.phase = "corruption"
        self.timer = 0

        # Create corruption effects on furniture
        for fx, fy, distance in self.furniture_positions:
            delay = distance * 0.05
            self.corruption_flashes.append(
                FurnitureCorruptionFlash(fx, fy, delay=delay)
            )
            self.inflation_numbers.append(
                ValueInflationNumber(fx, fy, delay=delay + 0.1)
            )

        self.screen_shake_callback(2, 0.3)

    def _start_feedback_phase(self):
        """Phase 4: Damage feedback to cursed unit."""
        self.phase = "feedback"
        self.timer = 0

    def update(self, delta_time):
        """Update animation state."""
        if not self.active:
            return False

        self.timer += delta_time

        # Phase transitions
        if self.phase == "seething" and self.timer >= 0.5:
            self._start_radiation_phase()
        elif self.phase == "radiation" and self.timer >= 0.6:
            self._start_corruption_phase()
        elif self.phase == "corruption" and self.timer >= 0.5:
            self._start_feedback_phase()
        elif self.phase == "feedback" and self.timer >= 0.2:
            self.active = False

        # Update sub-effects
        if self.seething_effect:
            self.seething_effect.update(delta_time)

        for wave in self.radiation_waves:
            wave.update(delta_time)

        for tendril in self.curse_tendrils:
            tendril.update(delta_time)

        for flash in self.corruption_flashes:
            flash.update(delta_time)

        for number in self.inflation_numbers:
            number.update(delta_time)

        return self.active

    def draw(self, surface):
        """Draw animation."""
        if not self.active:
            return

        # Draw radiation waves
        for wave in self.radiation_waves:
            wave.draw(surface)

        # Draw seething effect
        if self.seething_effect:
            self.seething_effect.draw(surface)

        # Draw curse tendrils
        for tendril in self.curse_tendrils:
            tendril.draw(surface)

        # Draw corruption flashes
        for flash in self.corruption_flashes:
            flash.draw(surface)

        # Draw inflation numbers
        for number in self.inflation_numbers:
            number.draw(surface)

        # Draw damage feedback (golden X on cursed unit)
        if self.phase == "feedback":
            progress = self.timer / 0.2
            alpha = int(220 * (1.0 - progress))

            if alpha > 0:
                # Pulsing golden X (heal-block indicator)
                x_size = 12
                pygame.draw.line(surface, (255, 215, 0, alpha),
                               (int(self.target_x - x_size), int(self.target_y - x_size)),
                               (int(self.target_x + x_size), int(self.target_y + x_size)), 4)
                pygame.draw.line(surface, (255, 215, 0, alpha),
                               (int(self.target_x + x_size), int(self.target_y - x_size)),
                               (int(self.target_x - x_size), int(self.target_y + x_size)), 4)
