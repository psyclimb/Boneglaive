#!/usr/bin/env python3
"""
Panel Decorations
Provides textures, borders, and decorative elements for UI panels.
BONEGLAIVE aesthetic: bone/dust/industrial theme.
"""
import pygame
import random
from typing import Tuple

# Color palette - Bone/Industrial theme
COLOR_BONE_WHITE = (220, 215, 200)
COLOR_BONE_DARK = (180, 175, 160)
COLOR_BRASS = (180, 150, 100)
COLOR_BRASS_DARK = (140, 110, 60)
COLOR_METAL_LIGHT = (90, 95, 100)
COLOR_METAL_DARK = (40, 42, 45)
COLOR_DUST_OVERLAY = (50, 48, 45)


def create_dust_texture(width: int, height: int, intensity: int = 30) -> pygame.Surface:
    """
    Create a subtle dust/grain texture overlay.

    Args:
        width: Texture width
        height: Texture height
        intensity: Opacity of dust particles (0-255)

    Returns:
        Surface with dust texture
    """
    texture = pygame.Surface((width, height), pygame.SRCALPHA)

    # Add random dust particles
    num_particles = (width * height) // 100  # Density

    for _ in range(num_particles):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        size = random.choice([1, 1, 1, 2])  # Mostly single pixels
        alpha = random.randint(intensity // 2, intensity)

        color = (*COLOR_DUST_OVERLAY, alpha)

        if size == 1:
            texture.set_at((x, y), color)
        else:
            pygame.draw.circle(texture, color, (x, y), size)

    return texture


def create_bone_texture_overlay(width: int, height: int) -> pygame.Surface:
    """
    Create a subtle bone-like texture with cracks and irregularities.

    Args:
        width: Texture width
        height: Texture height

    Returns:
        Surface with bone texture
    """
    texture = pygame.Surface((width, height), pygame.SRCALPHA)

    # Add subtle horizontal striations (like bone grain)
    for y in range(0, height, 3):
        if random.random() < 0.3:  # 30% chance per line
            alpha = random.randint(5, 15)
            color = (*COLOR_BONE_DARK, alpha)
            pygame.draw.line(texture, color, (0, y), (width, y), 1)

    # Add small crack patterns
    num_cracks = random.randint(2, 5)
    for _ in range(num_cracks):
        start_x = random.randint(0, width)
        start_y = random.randint(0, height)

        # Draw irregular crack
        points = [(start_x, start_y)]
        current_x, current_y = start_x, start_y

        for _ in range(random.randint(10, 30)):
            current_x += random.randint(-5, 5)
            current_y += random.randint(-5, 5)
            current_x = max(0, min(width, current_x))
            current_y = max(0, min(height, current_y))
            points.append((current_x, current_y))

        # Draw crack with low opacity
        if len(points) > 1:
            for i in range(len(points) - 1):
                alpha = random.randint(10, 25)
                color = (*COLOR_BONE_DARK, alpha)
                pygame.draw.line(texture, color, points[i], points[i+1], 1)

    return texture


def draw_industrial_border(surface: pygame.Surface, rect: pygame.Rect,
                          color_outer: Tuple[int, int, int] = COLOR_BRASS,
                          color_inner: Tuple[int, int, int] = COLOR_METAL_DARK,
                          rivet_spacing: int = 60):
    """
    Draw an industrial-style border with rivets and layered lines.

    Args:
        surface: Surface to draw on
        rect: Rectangle to border
        color_outer: Outer border color
        color_inner: Inner border color
        rivet_spacing: Spacing between rivets in pixels
    """
    # Draw outer border (thick)
    pygame.draw.rect(surface, color_outer, rect, 3)

    # Draw inner border (thin, inset)
    inner_rect = rect.inflate(-6, -6)
    pygame.draw.rect(surface, color_inner, inner_rect, 1)

    # Add rivets at corners and along edges
    rivet_radius = 4

    # Corners
    corner_positions = [
        (rect.left + 10, rect.top + 10),
        (rect.right - 10, rect.top + 10),
        (rect.left + 10, rect.bottom - 10),
        (rect.right - 10, rect.bottom - 10)
    ]

    for pos in corner_positions:
        _draw_rivet(surface, pos, rivet_radius)

    # Top edge rivets
    for x in range(rect.left + rivet_spacing, rect.right, rivet_spacing):
        _draw_rivet(surface, (x, rect.top + 10), rivet_radius)

    # Bottom edge rivets
    for x in range(rect.left + rivet_spacing, rect.right, rivet_spacing):
        _draw_rivet(surface, (x, rect.bottom - 10), rivet_radius)

    # Left edge rivets
    for y in range(rect.top + rivet_spacing, rect.bottom, rivet_spacing):
        _draw_rivet(surface, (rect.left + 10, y), rivet_radius)

    # Right edge rivets
    for y in range(rect.top + rivet_spacing, rect.bottom, rivet_spacing):
        _draw_rivet(surface, (rect.right - 10, y), rivet_radius)


def _draw_rivet(surface: pygame.Surface, pos: Tuple[int, int], radius: int = 4):
    """Draw a single rivet (bolt/screw)."""
    # Outer ring (darker)
    pygame.draw.circle(surface, COLOR_METAL_DARK, pos, radius)
    # Inner circle (lighter, creates depth)
    pygame.draw.circle(surface, COLOR_METAL_LIGHT, pos, radius - 1)
    # Center dot (screw hole)
    pygame.draw.circle(surface, COLOR_METAL_DARK, pos, max(1, radius // 2))


def draw_furniture_motif(surface: pygame.Surface, x: int, y: int,
                         furniture_type: str = "curiosity_table"):
    """
    Draw a small decorative furniture motif.

    Args:
        surface: Surface to draw on
        x, y: Position
        furniture_type: Type of furniture ("curiosity_table", "hydraulic_press", "podium")
    """
    if furniture_type == "curiosity_table":
        _draw_table_motif(surface, x, y)
    elif furniture_type == "hydraulic_press":
        _draw_press_motif(surface, x, y)
    elif furniture_type == "podium":
        _draw_podium_motif(surface, x, y)


def _draw_table_motif(surface: pygame.Surface, x: int, y: int):
    """Draw a small table icon."""
    # Table top
    pygame.draw.rect(surface, COLOR_BONE_WHITE, (x, y, 30, 4))
    pygame.draw.rect(surface, COLOR_BONE_DARK, (x, y, 30, 4), 1)

    # Table legs
    pygame.draw.rect(surface, COLOR_BONE_DARK, (x + 2, y + 4, 3, 12))
    pygame.draw.rect(surface, COLOR_BONE_DARK, (x + 25, y + 4, 3, 12))

    # Object on table (curiosity)
    pygame.draw.circle(surface, COLOR_BRASS, (x + 15, y - 3), 4)
    pygame.draw.circle(surface, COLOR_BRASS_DARK, (x + 15, y - 3), 4, 1)


def _draw_press_motif(surface: pygame.Surface, x: int, y: int):
    """Draw a small hydraulic press icon."""
    # Base
    pygame.draw.rect(surface, COLOR_METAL_DARK, (x, y + 15, 30, 5))
    pygame.draw.rect(surface, COLOR_METAL_LIGHT, (x, y + 15, 30, 5), 1)

    # Vertical supports
    pygame.draw.rect(surface, COLOR_METAL_LIGHT, (x + 2, y + 5, 3, 10))
    pygame.draw.rect(surface, COLOR_METAL_LIGHT, (x + 25, y + 5, 3, 10))

    # Press head
    pygame.draw.rect(surface, COLOR_BRASS, (x + 5, y, 20, 6))
    pygame.draw.rect(surface, COLOR_BRASS_DARK, (x + 5, y, 20, 6), 1)

    # Piston
    pygame.draw.rect(surface, COLOR_METAL_LIGHT, (x + 13, y + 6, 4, 9))


def _draw_podium_motif(surface: pygame.Surface, x: int, y: int):
    """Draw a small podium icon."""
    # Base (wide)
    pygame.draw.rect(surface, COLOR_BONE_DARK, (x, y + 15, 30, 5))

    # Column (tapered)
    points = [
        (x + 10, y + 15),
        (x + 20, y + 15),
        (x + 18, y + 5),
        (x + 12, y + 5)
    ]
    pygame.draw.polygon(surface, COLOR_BONE_WHITE, points)
    pygame.draw.polygon(surface, COLOR_BONE_DARK, points, 1)

    # Top platform
    pygame.draw.rect(surface, COLOR_BRASS, (x + 8, y, 14, 5))
    pygame.draw.rect(surface, COLOR_BRASS_DARK, (x + 8, y, 14, 5), 1)


def draw_corner_decoration(surface: pygame.Surface, x: int, y: int,
                          corner: str = "top_left"):
    """
    Draw a decorative corner element (bone/industrial motif).

    Args:
        surface: Surface to draw on
        x, y: Position
        corner: Which corner ("top_left", "top_right", "bottom_left", "bottom_right")
    """
    size = 20

    if corner == "top_left":
        # L-shaped bracket
        pygame.draw.line(surface, COLOR_BRASS, (x, y), (x + size, y), 2)
        pygame.draw.line(surface, COLOR_BRASS, (x, y), (x, y + size), 2)
        # Rivet at corner
        _draw_rivet(surface, (x + 5, y + 5), 3)

    elif corner == "top_right":
        pygame.draw.line(surface, COLOR_BRASS, (x - size, y), (x, y), 2)
        pygame.draw.line(surface, COLOR_BRASS, (x, y), (x, y + size), 2)
        _draw_rivet(surface, (x - 5, y + 5), 3)

    elif corner == "bottom_left":
        pygame.draw.line(surface, COLOR_BRASS, (x, y - size), (x, y), 2)
        pygame.draw.line(surface, COLOR_BRASS, (x, y), (x + size, y), 2)
        _draw_rivet(surface, (x + 5, y - 5), 3)

    elif corner == "bottom_right":
        pygame.draw.line(surface, COLOR_BRASS, (x, y - size), (x, y), 2)
        pygame.draw.line(surface, COLOR_BRASS, (x - size, y), (x, y), 2)
        _draw_rivet(surface, (x - 5, y - 5), 3)
