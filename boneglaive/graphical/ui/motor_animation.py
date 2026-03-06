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

# Import scaling utilities
from .scale_utils import scale_manager

# Scale motor dimensions based on resolution
MOTOR_WIDTH = scale_manager.scale(250, 'x')
MOTOR_HEIGHT = scale_manager.scale(180, 'y')


class MotorAnimation:
    """Industrial motor with belt drive animation."""

    def __init__(self):
        self.is_running = False
        self.rotation_angle = 0.0  # Current rotation angle in degrees
        self.rotation_speed = 2.0  # Degrees per frame when running
        self.belt_offset = 0.0     # Belt animation offset

        # Scale gear positions and sizes based on resolution
        self.main_gear_pos = (scale_manager.scale(80, 'x'), scale_manager.scale(90, 'y'))     # Left gear (larger)
        self.main_gear_radius = scale_manager.scale(45, 'uniform')
        self.driven_gear_pos = (scale_manager.scale(180, 'x'), scale_manager.scale(90, 'y'))  # Right gear (smaller)
        self.driven_gear_radius = scale_manager.scale(30, 'uniform')

        # Motor housing dimensions (scaled)
        self.housing_rect = pygame.Rect(
            scale_manager.scale(20),
            scale_manager.scale(20),
            scale_manager.scale(210, 'x'),
            scale_manager.scale(140, 'y')
        )

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
        # Create subsurface for motor area
        motor_surface = pygame.Surface((MOTOR_WIDTH, MOTOR_HEIGHT), pygame.SRCALPHA)

        # Draw background panel
        panel_rect = pygame.Rect(0, 0, MOTOR_WIDTH, MOTOR_HEIGHT)
        pygame.draw.rect(motor_surface, (*COLOR_METAL_DARK, 200), panel_rect)
        pygame.draw.rect(motor_surface, COLOR_METAL_LIGHT, panel_rect, 2)

        # Draw motor housing
        pygame.draw.rect(motor_surface, COLOR_METAL_DARK, self.housing_rect)
        pygame.draw.rect(motor_surface, COLOR_BRASS, self.housing_rect, 3)

        # Draw decorative rivets on housing (scaled positions and sizes)
        rivet_positions = [
            (scale_manager.scale(30, 'x'), scale_manager.scale(30, 'y')),
            (scale_manager.scale(200, 'x'), scale_manager.scale(30, 'y')),
            (scale_manager.scale(30, 'x'), scale_manager.scale(150, 'y')),
            (scale_manager.scale(200, 'x'), scale_manager.scale(150, 'y')),
            (scale_manager.scale(115, 'x'), scale_manager.scale(25, 'y')),
            (scale_manager.scale(30, 'x'), scale_manager.scale(90, 'y')),
            (scale_manager.scale(200, 'x'), scale_manager.scale(90, 'y'))
        ]
        rivet_outer_size = scale_manager.scale(4, 'uniform')
        rivet_inner_size = scale_manager.scale(2, 'uniform')

        for rivet_pos in rivet_positions:
            pygame.draw.circle(motor_surface, COLOR_RIVET, rivet_pos, rivet_outer_size)
            pygame.draw.circle(motor_surface, COLOR_METAL_LIGHT, rivet_pos, rivet_inner_size)

        # Draw belt connecting the gears
        self._draw_belt(motor_surface)

        # Draw gears
        self._draw_gear(motor_surface, self.main_gear_pos, self.main_gear_radius,
                       self.rotation_angle, teeth_count=12)
        self._draw_gear(motor_surface, self.driven_gear_pos, self.driven_gear_radius,
                       -self.rotation_angle * 1.5, teeth_count=8)  # Reverse rotation, faster

        # Draw center shafts (scaled radii)
        shaft_outer_main = scale_manager.scale(10, 'uniform')
        shaft_inner_main = scale_manager.scale(6, 'uniform')
        shaft_outer_driven = scale_manager.scale(8, 'uniform')
        shaft_inner_driven = scale_manager.scale(5, 'uniform')

        pygame.draw.circle(motor_surface, COLOR_METAL_LIGHT, self.main_gear_pos, shaft_outer_main)
        pygame.draw.circle(motor_surface, COLOR_METAL_DARK, self.main_gear_pos, shaft_inner_main)
        pygame.draw.circle(motor_surface, COLOR_METAL_LIGHT, self.driven_gear_pos, shaft_outer_driven)
        pygame.draw.circle(motor_surface, COLOR_METAL_DARK, self.driven_gear_pos, shaft_inner_driven)

        # Blit to main surface
        surface.blit(motor_surface, (x, y))

    def _draw_belt(self, surface: pygame.Surface):
        """Draw the belt connecting the two gears."""
        # Calculate belt path (simplified as straight lines for top and bottom)
        gear1_x, gear1_y = self.main_gear_pos
        gear2_x, gear2_y = self.driven_gear_pos

        # Top and bottom belt segments (scaled dimensions)
        belt_width = scale_manager.scale(8, 'uniform')
        belt_offset_from_gear = scale_manager.scale(5, 'uniform')

        # Top belt line
        top_y = gear1_y - self.main_gear_radius + belt_offset_from_gear
        pygame.draw.line(surface, COLOR_BELT_DARK,
                        (gear1_x, top_y), (gear2_x, top_y), belt_width)

        # Bottom belt line
        bottom_y = gear1_y + self.main_gear_radius - belt_offset_from_gear
        pygame.draw.line(surface, COLOR_BELT_DARK,
                        (gear1_x, bottom_y), (gear2_x, bottom_y), belt_width)

        # Draw belt segments/stitching pattern when running (scaled dimensions)
        if self.is_running:
            segment_spacing = scale_manager.scale(10, 'x')
            offset = int(self.belt_offset)
            stitch_height = scale_manager.scale(2, 'uniform')
            stitch_width = scale_manager.scale(2, 'uniform')

            # Top belt stitching
            for i in range(gear1_x + offset, gear2_x, segment_spacing):
                pygame.draw.line(surface, COLOR_BELT_LIGHT,
                               (i, top_y - stitch_height), (i, top_y + stitch_height), stitch_width)

            # Bottom belt stitching (reverse direction)
            for i in range(gear2_x - offset, gear1_x, -segment_spacing):
                pygame.draw.line(surface, COLOR_BELT_LIGHT,
                               (i, bottom_y - stitch_height), (i, bottom_y + stitch_height), stitch_width)

        # Draw belt around left gear (arc)
        arc_rect_left = pygame.Rect(
            gear1_x - self.main_gear_radius,
            gear1_y - self.main_gear_radius,
            self.main_gear_radius * 2,
            self.main_gear_radius * 2
        )
        pygame.draw.arc(surface, COLOR_BELT_DARK, arc_rect_left,
                       math.radians(180), math.radians(360), belt_width)

        # Draw belt around right gear (arc)
        arc_rect_right = pygame.Rect(
            gear2_x - self.driven_gear_radius,
            gear2_y - self.driven_gear_radius,
            self.driven_gear_radius * 2,
            self.driven_gear_radius * 2
        )
        pygame.draw.arc(surface, COLOR_BELT_DARK, arc_rect_right,
                       math.radians(0), math.radians(180), belt_width)

    def _draw_gear(self, surface: pygame.Surface, pos: Tuple[int, int],
                   radius: int, angle: float, teeth_count: int = 10):
        """
        Draw an animated gear.

        Args:
            surface: Surface to draw on
            pos: Center position (x, y)
            radius: Gear radius
            angle: Current rotation angle in degrees
            teeth_count: Number of teeth on the gear
        """
        center_x, center_y = pos

        # Draw gear body (circle) - scale border width
        gear_border_width = scale_manager.scale(3, 'uniform')
        pygame.draw.circle(surface, COLOR_BRASS, pos, radius)
        pygame.draw.circle(surface, COLOR_METAL_DARK, pos, radius - gear_border_width)

        # Draw gear teeth (scaled dimensions)
        tooth_height = scale_manager.scale(8, 'uniform')
        tooth_width = scale_manager.scale(15, 'uniform')
        angle_step = 360 / teeth_count

        for i in range(teeth_count):
            tooth_angle = math.radians(angle + i * angle_step)

            # Calculate tooth position
            tooth_x = center_x + (radius - tooth_height/2) * math.cos(tooth_angle)
            tooth_y = center_y + (radius - tooth_height/2) * math.sin(tooth_angle)

            # Draw tooth as small rectangle
            tooth_rect = pygame.Rect(0, 0, tooth_width, tooth_height)
            tooth_rect.center = (int(tooth_x), int(tooth_y))

            # Rotate tooth to face outward (scale border width)
            tooth_border = scale_manager.scale(1, 'uniform')
            tooth_surface = pygame.Surface((tooth_width, tooth_height), pygame.SRCALPHA)
            pygame.draw.rect(tooth_surface, COLOR_BRASS, (0, 0, tooth_width, tooth_height))
            pygame.draw.rect(tooth_surface, COLOR_METAL_LIGHT, (0, 0, tooth_width, tooth_height), tooth_border)

            rotated_tooth = pygame.transform.rotate(tooth_surface, -angle - i * angle_step)
            rotated_rect = rotated_tooth.get_rect(center=(int(tooth_x), int(tooth_y)))

            surface.blit(rotated_tooth, rotated_rect)

        # Draw inner gear details (spokes) - scaled dimensions
        spoke_count = 6
        spoke_angle_step = 360 / spoke_count
        inner_radius = radius // 3
        spoke_inset = scale_manager.scale(10, 'uniform')
        spoke_width = scale_manager.scale(3, 'uniform')

        for i in range(spoke_count):
            spoke_angle = math.radians(angle + i * spoke_angle_step)
            end_x = center_x + (radius - spoke_inset) * math.cos(spoke_angle)
            end_y = center_y + (radius - spoke_inset) * math.sin(spoke_angle)
            start_x = center_x + inner_radius * math.cos(spoke_angle)
            start_y = center_y + inner_radius * math.sin(spoke_angle)

            pygame.draw.line(surface, COLOR_METAL_LIGHT,
                           (start_x, start_y), (end_x, end_y), spoke_width)
