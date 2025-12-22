#!/usr/bin/env python3
"""
Animated Background for Main Menu
Dark apocalyptic scene with chemical plant silhouette and rotating skull glaive sun.
"""
import pygame
import math
from typing import Tuple


class AnimatedBackground:
    """Animated background for main menu with rotating skull glaive sun."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.rotation = 0
        self.rotation_speed = 15  # degrees per second

        # Create static background
        self.background_surface = self._create_background()

        # Create skull glaive sun
        self.skull_glaive = self._create_skull_glaive()

    def _create_background(self) -> pygame.Surface:
        """Create the static background layer with sky and chemical plant silhouette."""
        surface = pygame.Surface((self.width, self.height))

        # Dark apocalyptic sky gradient (top to bottom)
        for y in range(self.height):
            progress = y / self.height
            # Dark purple/red sky transitioning to darker horizon
            r = int(40 + (20 - 40) * progress)
            g = int(25 + (15 - 25) * progress)
            b = int(35 + (25 - 35) * progress)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

        # Chemical plant silhouette in the distance
        self._draw_chemical_plant(surface)

        return surface

    def _draw_chemical_plant(self, surface: pygame.Surface):
        """Draw dark silhouette of chemical plant in background."""
        silhouette_color = (10, 10, 15)  # Very dark, almost black
        horizon_y = int(self.height * 0.65)

        # Ground
        pygame.draw.rect(surface, silhouette_color,
                        (0, horizon_y, self.width, self.height - horizon_y))

        # Multiple industrial structures
        structures = [
            # (x, y, width, height)
            (self.width * 0.15, horizon_y - 120, 80, 120),  # Left tower
            (self.width * 0.25, horizon_y - 90, 60, 90),    # Mid-left building
            (self.width * 0.35, horizon_y - 150, 100, 150), # Central tall structure
            (self.width * 0.5, horizon_y - 110, 70, 110),   # Mid-right tower
            (self.width * 0.65, horizon_y - 80, 90, 80),    # Right building
            (self.width * 0.8, horizon_y - 95, 75, 95),     # Far right tower
        ]

        for x, y, w, h in structures:
            # Main structure
            pygame.draw.rect(surface, silhouette_color, (x, y, w, h))

            # Add some vertical detail lines for industrial look
            for i in range(3):
                line_x = x + (i + 1) * w // 4
                pygame.draw.line(surface, (5, 5, 10), (line_x, y), (line_x, y + h), 2)

        # Smokestacks (thin vertical lines rising from structures)
        smokestack_positions = [
            (self.width * 0.15 + 20, horizon_y - 120, 160),
            (self.width * 0.35 + 30, horizon_y - 150, 200),
            (self.width * 0.35 + 60, horizon_y - 150, 180),
            (self.width * 0.65 + 40, horizon_y - 80, 130),
        ]

        for x, base_y, stack_height in smokestack_positions:
            # Smokestack
            pygame.draw.rect(surface, silhouette_color,
                           (x - 8, base_y - stack_height, 16, stack_height))
            # Top cap
            pygame.draw.rect(surface, silhouette_color,
                           (x - 12, base_y - stack_height, 24, 8))

        # Connecting pipes and infrastructure
        pipe_y_positions = [
            horizon_y - 60,
            horizon_y - 90,
            horizon_y - 40,
        ]

        for pipe_y in pipe_y_positions:
            # Horizontal pipes across structures
            pygame.draw.line(surface, silhouette_color,
                           (self.width * 0.15, pipe_y),
                           (self.width * 0.85, pipe_y), 4)

    def _create_skull_glaive(self) -> pygame.Surface:
        """Create rotating skull glaive sun (large, ominous)."""
        size = 200  # Very large sun
        surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = size

        # Outer glow (dark red/orange)
        glow_color = (60, 30, 20, 40)
        for radius in range(size, size - 30, -5):
            alpha = int(40 * (1 - (size - radius) / 30))
            glow = (60, 30, 20, alpha)
            pygame.draw.circle(surface, glow, (center, center), radius)

        # Draw 6 large glaive blades
        blade_length = size - 40
        blade_color = (50, 40, 45)  # Dark metal
        blade_edge_color = (70, 55, 60)  # Slightly lighter edge

        for i in range(6):
            angle = (i * 60) * math.pi / 180

            # Blade tip
            tip_x = center + math.cos(angle) * blade_length
            tip_y = center + math.sin(angle) * blade_length

            # Blade sides (wider blades)
            angle_offset = 18 * math.pi / 180
            side1_x = center + math.cos(angle - angle_offset) * (blade_length * 0.75)
            side1_y = center + math.sin(angle - angle_offset) * (blade_length * 0.75)
            side2_x = center + math.cos(angle + angle_offset) * (blade_length * 0.75)
            side2_y = center + math.sin(angle + angle_offset) * (blade_length * 0.75)

            # Draw blade
            pygame.draw.polygon(surface, blade_color,
                              [(center, center), (tip_x, tip_y), (side1_x, side1_y)])
            pygame.draw.polygon(surface, blade_color,
                              [(center, center), (tip_x, tip_y), (side2_x, side2_y)])

            # Blade edge highlight
            pygame.draw.line(surface, blade_edge_color,
                           (center, center), (tip_x, tip_y), 3)

        # Center skull
        self._draw_skull_center(surface, center, center, 50)

        return surface

    def _draw_skull_center(self, surface: pygame.Surface, center_x: int, center_y: int, radius: int):
        """Draw stylized skull in the center of the glaive."""
        # Skull base (round head)
        skull_color = (80, 75, 75)
        pygame.draw.circle(surface, skull_color, (center_x, center_y), radius)

        # Skull outline
        pygame.draw.circle(surface, (60, 55, 55), (center_x, center_y), radius, 3)

        # Eye sockets (large hollow eyes)
        eye_y = center_y - radius // 4
        left_eye_x = center_x - radius // 3
        right_eye_x = center_x + radius // 3
        eye_radius = radius // 4

        pygame.draw.circle(surface, (20, 15, 15), (left_eye_x, eye_y), eye_radius)
        pygame.draw.circle(surface, (20, 15, 15), (right_eye_x, eye_y), eye_radius)

        # Eye socket outlines
        pygame.draw.circle(surface, (40, 35, 35), (left_eye_x, eye_y), eye_radius, 2)
        pygame.draw.circle(surface, (40, 35, 35), (right_eye_x, eye_y), eye_radius, 2)

        # Nose cavity (triangular)
        nose_y = center_y + radius // 8
        nose_points = [
            (center_x, nose_y - radius // 6),
            (center_x - radius // 8, nose_y + radius // 8),
            (center_x + radius // 8, nose_y + radius // 8),
        ]
        pygame.draw.polygon(surface, (20, 15, 15), nose_points)
        pygame.draw.polygon(surface, (40, 35, 35), nose_points, 2)

        # Teeth/jaw (horizontal lines)
        jaw_y_start = center_y + radius // 2
        jaw_width = radius // 2
        teeth_count = 6

        for i in range(teeth_count):
            tooth_x = center_x - jaw_width // 2 + (i * jaw_width // (teeth_count - 1))
            tooth_y1 = jaw_y_start
            tooth_y2 = jaw_y_start + radius // 6
            pygame.draw.line(surface, (40, 35, 35), (tooth_x, tooth_y1), (tooth_x, tooth_y2), 2)

    def update(self, delta_time: float):
        """Update animation state."""
        self.rotation += self.rotation_speed * delta_time
        if self.rotation >= 360:
            self.rotation -= 360

    def draw(self, surface: pygame.Surface):
        """Draw the animated background."""
        # Draw static background
        surface.blit(self.background_surface, (0, 0))

        # Draw rotating skull glaive sun on right side
        sun_x = int(self.width * 0.75)  # Right side of screen
        sun_y = int(self.height * 0.25)  # Upper third of screen

        # Rotate the skull glaive
        rotated_glaive = pygame.transform.rotate(self.skull_glaive, self.rotation)
        rect = rotated_glaive.get_rect(center=(sun_x, sun_y))
        surface.blit(rotated_glaive, rect)
