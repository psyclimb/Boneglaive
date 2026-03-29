#!/usr/bin/env python3
"""
Kaleidoscope Background for Main Menu
Infinite scrolling grid of symmetrical patterns using game graphics.
"""
import pygame
import random
import os
from typing import List, Tuple
from boneglaive.utils.paths import asset_path


class KaleidoscopeBackground:
    """Animated background with symmetrical scrolling icon patterns."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Grid settings
        self.cell_size = 80  # Size of each grid cell
        self.grid_cols = (width // self.cell_size) + 3  # Extra for scrolling
        self.grid_rows = (height // self.cell_size) + 3

        # Scrolling offset
        self.scroll_x = 0
        self.scroll_y = 0
        self.scroll_speed_x = 15  # pixels per second
        self.scroll_speed_y = 10  # pixels per second

        # Load all available icons
        self.icons = self._load_icons()

        # Generate symmetrical pattern grid
        self.pattern_grid = self._generate_symmetrical_grid()

        # Background color (dark)
        self.bg_color = (15, 10, 15)

    def _load_icons(self) -> List[pygame.Surface]:
        """Load all unit, furniture, and skill icons."""
        icons = []

        graphics_base = asset_path("graphics")

        # Try to import cairosvg for SVG support
        try:
            import cairosvg
            from io import BytesIO
            has_cairosvg = True
        except Exception:
            has_cairosvg = False

        # Directories to load from
        icon_dirs = [
            "units",
            "furniture",
            "skill_icons",
        ]

        icon_size = self.cell_size - 10

        for dir_name in icon_dirs:
            dir_path = os.path.join(graphics_base, dir_name)
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                for filename in files:
                    if filename.endswith('.svg') and has_cairosvg:
                        filepath = os.path.join(dir_path, filename)
                        try:
                            # Load SVG using cairosvg (same method as game)
                            png_data = cairosvg.svg2png(url=filepath, output_width=icon_size, output_height=icon_size)
                            icon = pygame.image.load(BytesIO(png_data))
                            icons.append(icon)
                        except Exception:
                            pass
                    elif filename.endswith('.png'):
                        filepath = os.path.join(dir_path, filename)
                        try:
                            icon = pygame.image.load(filepath)
                            # Scale to fit cell with padding
                            icon = pygame.transform.scale(icon, (icon_size, icon_size))
                            icons.append(icon)
                        except Exception:
                            pass

        # If no icons loaded, create placeholder patterns
        if not icons:
            icons = self._create_placeholder_icons()

        return icons

    def _create_placeholder_icons(self) -> List[pygame.Surface]:
        """Create simple geometric placeholder icons."""
        icons = []
        colors = [
            (60, 40, 45),   # Dark red
            (40, 50, 60),   # Dark blue
            (50, 60, 40),   # Dark green
            (60, 50, 40),   # Dark orange
            (50, 40, 60),   # Dark purple
        ]

        for i, color in enumerate(colors):
            surface = pygame.Surface((self.cell_size - 10, self.cell_size - 10), pygame.SRCALPHA)
            surface.fill((0, 0, 0, 0))

            # Draw different shapes
            if i % 5 == 0:
                # Circle
                pygame.draw.circle(surface, color,
                                 (self.cell_size // 2 - 5, self.cell_size // 2 - 5),
                                 self.cell_size // 3)
            elif i % 5 == 1:
                # Square
                pygame.draw.rect(surface, color,
                               (10, 10, self.cell_size - 30, self.cell_size - 30))
            elif i % 5 == 2:
                # Triangle
                points = [
                    (self.cell_size // 2 - 5, 5),
                    (5, self.cell_size - 15),
                    (self.cell_size - 15, self.cell_size - 15)
                ]
                pygame.draw.polygon(surface, color, points)
            elif i % 5 == 3:
                # Diamond
                points = [
                    (self.cell_size // 2 - 5, 5),
                    (self.cell_size - 15, self.cell_size // 2 - 5),
                    (self.cell_size // 2 - 5, self.cell_size - 15),
                    (5, self.cell_size // 2 - 5)
                ]
                pygame.draw.polygon(surface, color, points)
            else:
                # Plus sign
                pygame.draw.rect(surface, color,
                               (self.cell_size // 2 - 10, 10, 10, self.cell_size - 30))
                pygame.draw.rect(surface, color,
                               (10, self.cell_size // 2 - 10, self.cell_size - 30, 10))

            icons.append(surface)

        return icons

    def _generate_symmetrical_grid(self) -> List[List[Tuple[int, bool, bool]]]:
        """Generate a symmetrical pattern grid.

        Returns grid where each cell contains (icon_index, flip_h, flip_v).
        Pattern is mirrored both horizontally and vertically from center.
        Ensures no adjacent cells have the same icon.
        """
        grid = []

        # Generate only one quadrant, mirror the rest
        half_rows = self.grid_rows // 2 + 1
        half_cols = self.grid_cols // 2 + 1

        quadrant = []
        for row in range(half_rows):
            quadrant_row = []
            for col in range(half_cols):
                # Get icon that's different from neighbors
                attempts = 0
                max_attempts = 50
                while attempts < max_attempts:
                    icon_idx = random.randint(0, len(self.icons) - 1)

                    # Check if different from left neighbor
                    if col > 0 and quadrant_row[col - 1][0] == icon_idx:
                        attempts += 1
                        continue

                    # Check if different from top neighbor
                    if row > 0 and quadrant[row - 1][col][0] == icon_idx:
                        attempts += 1
                        continue

                    # Found valid icon
                    break

                # Don't flip icons - keep them upright
                flip_h = False
                flip_v = False
                quadrant_row.append((icon_idx, flip_h, flip_v))
            quadrant.append(quadrant_row)

        # Build full grid with symmetry
        for row in range(self.grid_rows):
            grid_row = []
            for col in range(self.grid_cols):
                # Calculate quadrant position
                quad_row = min(row, self.grid_rows - 1 - row)
                quad_col = min(col, self.grid_cols - 1 - col)

                # Clamp to quadrant size
                quad_row = min(quad_row, half_rows - 1)
                quad_col = min(quad_col, half_cols - 1)

                icon_idx, flip_h, flip_v = quadrant[quad_row][quad_col]

                # Keep icons upright - no flipping
                actual_flip_h = False
                actual_flip_v = False

                grid_row.append((icon_idx, actual_flip_h, actual_flip_v))
            grid.append(grid_row)

        return grid

    def update(self, delta_time: float):
        """Update scrolling animation."""
        self.scroll_x += self.scroll_speed_x * delta_time
        self.scroll_y += self.scroll_speed_y * delta_time

        # Don't wrap - just keep accumulating for smooth infinite scroll
        # The grid is large enough to handle wrapping visually

    def draw(self, surface: pygame.Surface):
        """Draw the kaleidoscope background."""
        # Fill background
        surface.fill(self.bg_color)

        # Calculate which cell we've scrolled to (for grid wrapping)
        cell_offset_x = int(self.scroll_x // self.cell_size)
        cell_offset_y = int(self.scroll_y // self.cell_size)

        # Calculate position within current cell
        pixel_offset_x = self.scroll_x % self.cell_size
        pixel_offset_y = self.scroll_y % self.cell_size

        # Draw enough tiles to cover screen with scrolling
        start_col = -2
        end_col = self.grid_cols + 1
        start_row = -2
        end_row = self.grid_rows + 1

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                # Calculate screen position
                x = col * self.cell_size - pixel_offset_x
                y = row * self.cell_size - pixel_offset_y

                # Skip if off screen
                if x + self.cell_size < 0 or x > self.width:
                    continue
                if y + self.cell_size < 0 or y > self.height:
                    continue

                # Wrap grid indices to create infinite tiling pattern
                grid_col = (col + cell_offset_x) % self.grid_cols
                grid_row = (row + cell_offset_y) % self.grid_rows

                # Get icon from wrapped grid position
                icon_idx, flip_h, flip_v = self.pattern_grid[grid_row][grid_col]
                icon = self.icons[icon_idx]

                # Draw with some transparency for subtle effect
                icon_copy = icon.copy()
                icon_copy.set_alpha(80)  # Semi-transparent

                # Center icon in cell
                icon_x = x + 5
                icon_y = y + 5
                surface.blit(icon_copy, (icon_x, icon_y))

        # Draw subtle vignette overlay
        self._draw_vignette(surface)

    def _draw_vignette(self, surface: pygame.Surface):
        """Draw dark vignette around edges."""
        vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Dark gradient from edges to center
        center_x = self.width // 2
        center_y = self.height // 2
        max_dist = ((center_x ** 2 + center_y ** 2) ** 0.5)

        # Only darken edges, keep center visible
        for y in range(0, self.height, 20):
            for x in range(0, self.width, 20):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                alpha = int((dist / max_dist) * 180)
                pygame.draw.rect(vignette, (0, 0, 0, alpha), (x, y, 20, 20))

        surface.blit(vignette, (0, 0))
