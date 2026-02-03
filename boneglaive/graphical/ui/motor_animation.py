#!/usr/bin/env python3
"""
Motor Animation UI Component
Animated belt-driven motor that spins during turn execution.
Industrial aesthetic matching BONEGLAIVE's bone/mechanical theme.
"""
import pygame
import math
from typing import Tuple

# Colors - Industrial/Bone theme
COLOR_METAL_DARK = (40, 40, 45)
COLOR_METAL_LIGHT = (80, 85, 90)
COLOR_BRASS = (180, 150, 100)
COLOR_BONE_WHITE = (220, 215, 200)
COLOR_BELT_DARK = (30, 30, 30)
COLOR_BELT_LIGHT = (50, 50, 50)
COLOR_RIVET = (60, 60, 65)

# Base dimensions (at default 1480x800 resolution)
MOTOR_WIDTH_BASE = 250
MOTOR_HEIGHT_BASE = 180


class MotorAnimation:
    """Industrial motor with belt drive animation."""

    def __init__(self, layout=None):
        self.layout = layout
        self.is_running = False
        self.rotation_angle = 0.0  # Current rotation angle in degrees
        self.rotation_speed = 2.0  # Degrees per frame when running
        self.belt_offset = 0.0     # Belt animation offset

    def _get_scaled_dimensions(self):
        """Calculate scaled dimensions based on layout."""
        if self.layout:
            # Scale motor width to fit left panel
            # Base: 250px motor in 280px panel = 89% of panel width
            motor_width = int(self.layout.left_panel_width * 0.89)
            # Maintain aspect ratio
            motor_height = int(motor_width * (MOTOR_HEIGHT_BASE / MOTOR_WIDTH_BASE))
            scale = motor_width / MOTOR_WIDTH_BASE
        else:
            motor_width = MOTOR_WIDTH_BASE
            motor_height = MOTOR_HEIGHT_BASE
            scale = 1.0

        return {
            'width': motor_width,
            'height': motor_height,
            'scale': scale,
            'main_gear_pos': (int(80 * scale), int(90 * scale)),
            'main_gear_radius': int(45 * scale),
            'driven_gear_pos': (int(180 * scale), int(90 * scale)),
            'driven_gear_radius': int(30 * scale),
            'housing_rect': pygame.Rect(int(20 * scale), int(20 * scale),
                                       int(210 * scale), int(140 * scale)),
        }

    def start(self):
        """Start the motor animation."""
        self.is_running = True

    def stop(self):
        """Stop the motor animation."""
        self.is_running = False

    def update(self, dt: float = 1/60):
        """
        Update animation state.

        Args:
            dt: Delta time in seconds
        """
        if self.is_running:
            # Rotate gears
            self.rotation_angle += self.rotation_speed
            if self.rotation_angle >= 360:
                self.rotation_angle -= 360

            # Animate belt
            self.belt_offset += self.rotation_speed * 0.5
            if self.belt_offset >= 10:  # Belt segment length
                self.belt_offset -= 10

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw the motor animation.

        Args:
            surface: Surface to draw on
            x, y: Top-left position
        """
        # Get scaled dimensions
        dims = self._get_scaled_dimensions()

        # Create subsurface for motor area
        motor_surface = pygame.Surface((dims['width'], dims['height']), pygame.SRCALPHA)

        # Draw background panel
        panel_rect = pygame.Rect(0, 0, dims['width'], dims['height'])
        pygame.draw.rect(motor_surface, (*COLOR_METAL_DARK, 200), panel_rect)
        pygame.draw.rect(motor_surface, COLOR_METAL_LIGHT, panel_rect, 2)

        # Draw motor housing
        pygame.draw.rect(motor_surface, COLOR_METAL_DARK, dims['housing_rect'])
        pygame.draw.rect(motor_surface, COLOR_BRASS, dims['housing_rect'], 3)

        # Draw decorative rivets on housing
        scale = dims['scale']
        rivet_positions = [
            (int(30 * scale), int(30 * scale)), (int(200 * scale), int(30 * scale)),
            (int(30 * scale), int(150 * scale)), (int(200 * scale), int(150 * scale)),
            (int(115 * scale), int(25 * scale)), (int(30 * scale), int(90 * scale)),
            (int(200 * scale), int(90 * scale))
        ]
        for rivet_pos in rivet_positions:
            pygame.draw.circle(motor_surface, COLOR_RIVET, rivet_pos, max(1, int(4 * scale)))
            pygame.draw.circle(motor_surface, COLOR_METAL_LIGHT, rivet_pos, max(1, int(2 * scale)))

        # Draw belt connecting the gears
        self._draw_belt(motor_surface, dims)

        # Draw gears
        self._draw_gear(motor_surface, dims['main_gear_pos'], dims['main_gear_radius'],
                       self.rotation_angle, teeth_count=12, scale=scale)
        self._draw_gear(motor_surface, dims['driven_gear_pos'], dims['driven_gear_radius'],
                       -self.rotation_angle * 1.5, teeth_count=8, scale=scale)  # Reverse rotation, faster

        # Draw center shafts
        pygame.draw.circle(motor_surface, COLOR_METAL_LIGHT, dims['main_gear_pos'], max(1, int(10 * scale)))
        pygame.draw.circle(motor_surface, COLOR_METAL_DARK, dims['main_gear_pos'], max(1, int(6 * scale)))
        pygame.draw.circle(motor_surface, COLOR_METAL_LIGHT, dims['driven_gear_pos'], max(1, int(8 * scale)))
        pygame.draw.circle(motor_surface, COLOR_METAL_DARK, dims['driven_gear_pos'], max(1, int(5 * scale)))

        # Blit to main surface
        surface.blit(motor_surface, (x, y))

    def _draw_belt(self, surface: pygame.Surface, dims: dict):
        """Draw the belt connecting the two gears."""
        # Calculate belt path (simplified as straight lines for top and bottom)
        gear1_x, gear1_y = dims['main_gear_pos']
        gear2_x, gear2_y = dims['driven_gear_pos']
        main_radius = dims['main_gear_radius']
        driven_radius = dims['driven_gear_radius']
        scale = dims['scale']

        # Top and bottom belt segments
        belt_width = max(1, int(8 * scale))

        # Top belt line
        top_y = gear1_y - main_radius + int(5 * scale)
        pygame.draw.line(surface, COLOR_BELT_DARK,
                        (gear1_x, top_y), (gear2_x, top_y), belt_width)

        # Bottom belt line
        bottom_y = gear1_y + main_radius - int(5 * scale)
        pygame.draw.line(surface, COLOR_BELT_DARK,
                        (gear1_x, bottom_y), (gear2_x, bottom_y), belt_width)

        # Draw belt segments/stitching pattern when running
        if self.is_running:
            segment_spacing = max(1, int(10 * scale))
            offset = int(self.belt_offset * scale)

            # Top belt stitching
            for i in range(gear1_x + offset, gear2_x, segment_spacing):
                pygame.draw.line(surface, COLOR_BELT_LIGHT,
                               (i, top_y - int(2 * scale)), (i, top_y + int(2 * scale)), max(1, int(2 * scale)))

            # Bottom belt stitching (reverse direction)
            for i in range(gear2_x - offset, gear1_x, -segment_spacing):
                pygame.draw.line(surface, COLOR_BELT_LIGHT,
                               (i, bottom_y - int(2 * scale)), (i, bottom_y + int(2 * scale)), max(1, int(2 * scale)))

        # Draw belt around left gear (arc)
        arc_rect_left = pygame.Rect(
            gear1_x - main_radius,
            gear1_y - main_radius,
            main_radius * 2,
            main_radius * 2
        )
        pygame.draw.arc(surface, COLOR_BELT_DARK, arc_rect_left,
                       math.radians(180), math.radians(360), belt_width)

        # Draw belt around right gear (arc)
        arc_rect_right = pygame.Rect(
            gear2_x - driven_radius,
            gear2_y - driven_radius,
            driven_radius * 2,
            driven_radius * 2
        )
        pygame.draw.arc(surface, COLOR_BELT_DARK, arc_rect_right,
                       math.radians(0), math.radians(180), belt_width)

    def _draw_gear(self, surface: pygame.Surface, pos: Tuple[int, int],
                   radius: int, angle: float, teeth_count: int = 10, scale: float = 1.0):
        """
        Draw an animated gear.

        Args:
            surface: Surface to draw on
            pos: Center position (x, y)
            radius: Gear radius
            angle: Current rotation angle in degrees
            teeth_count: Number of teeth on the gear
            scale: Scale factor for dimensions
        """
        center_x, center_y = pos

        # Draw gear body (circle)
        pygame.draw.circle(surface, COLOR_BRASS, pos, radius)
        pygame.draw.circle(surface, COLOR_METAL_DARK, pos, max(1, radius - int(3 * scale)))

        # Draw gear teeth
        tooth_height = max(1, int(8 * scale))
        tooth_width = max(1, int(15 * scale))
        angle_step = 360 / teeth_count

        for i in range(teeth_count):
            tooth_angle = math.radians(angle + i * angle_step)

            # Calculate tooth position
            tooth_x = center_x + (radius - tooth_height/2) * math.cos(tooth_angle)
            tooth_y = center_y + (radius - tooth_height/2) * math.sin(tooth_angle)

            # Draw tooth as small rectangle
            tooth_rect = pygame.Rect(0, 0, tooth_width, tooth_height)
            tooth_rect.center = (int(tooth_x), int(tooth_y))

            # Rotate tooth to face outward
            tooth_surface = pygame.Surface((tooth_width, tooth_height), pygame.SRCALPHA)
            pygame.draw.rect(tooth_surface, COLOR_BRASS, (0, 0, tooth_width, tooth_height))
            pygame.draw.rect(tooth_surface, COLOR_METAL_LIGHT, (0, 0, tooth_width, tooth_height), max(1, int(1 * scale)))

            rotated_tooth = pygame.transform.rotate(tooth_surface, -angle - i * angle_step)
            rotated_rect = rotated_tooth.get_rect(center=(int(tooth_x), int(tooth_y)))

            surface.blit(rotated_tooth, rotated_rect)

        # Draw inner gear details (spokes)
        spoke_count = 6
        spoke_angle_step = 360 / spoke_count
        inner_radius = radius // 3

        for i in range(spoke_count):
            spoke_angle = math.radians(angle + i * spoke_angle_step)
            end_x = center_x + (radius - int(10 * scale)) * math.cos(spoke_angle)
            end_y = center_y + (radius - int(10 * scale)) * math.sin(spoke_angle)
            start_x = center_x + inner_radius * math.cos(spoke_angle)
            start_y = center_y + inner_radius * math.sin(spoke_angle)

            pygame.draw.line(surface, COLOR_METAL_LIGHT,
                           (start_x, start_y), (end_x, end_y), max(1, int(3 * scale)))
