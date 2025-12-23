#!/usr/bin/env python3
"""
Camera/Viewport System
Handles coordinate conversion between grid space and screen space.
Centralizes all offset and scaling logic for resize-safe animations.
"""


class Camera:
    """
    Camera for converting between grid coordinates and screen pixel coordinates.
    This allows animations to work in logical grid space while supporting
    zoom, pan, and screen shake effects.
    """

    def __init__(self, grid_offset_x=100, grid_offset_y=50, tile_size=64):
        """
        Initialize camera with grid positioning.

        Args:
            grid_offset_x: X offset for grid rendering (pixels from left edge)
            grid_offset_y: Y offset for grid rendering (pixels from top edge)
            tile_size: Size of each grid tile in pixels
        """
        self.grid_offset_x = grid_offset_x
        self.grid_offset_y = grid_offset_y
        self.tile_size = tile_size

        # Screen shake offset (applied temporarily)
        self.shake_offset_x = 0
        self.shake_offset_y = 0

        # Zoom level (1.0 = normal, 2.0 = 2x zoom, etc.)
        self.zoom = 1.0

    def grid_to_screen(self, grid_x, grid_y, centered=True):
        """
        Convert grid coordinates to screen pixel coordinates.

        Args:
            grid_x: Grid column (0-indexed)
            grid_y: Grid row (0-indexed)
            centered: If True, returns center of tile. If False, returns top-left corner.

        Returns:
            (screen_x, screen_y) tuple in pixels
        """
        screen_x = self.grid_offset_x + grid_x * self.tile_size
        screen_y = self.grid_offset_y + grid_y * self.tile_size

        if centered:
            screen_x += self.tile_size // 2
            screen_y += self.tile_size // 2

        # Apply screen shake
        screen_x += self.shake_offset_x
        screen_y += self.shake_offset_y

        return screen_x, screen_y

    def screen_to_grid(self, screen_x, screen_y):
        """
        Convert screen pixel coordinates to grid coordinates.

        Args:
            screen_x: Screen X position in pixels
            screen_y: Screen Y position in pixels

        Returns:
            (grid_x, grid_y) tuple
        """
        # Remove shake offset
        screen_x -= self.shake_offset_x
        screen_y -= self.shake_offset_y

        grid_x = (screen_x - self.grid_offset_x) // self.tile_size
        grid_y = (screen_y - self.grid_offset_y) // self.tile_size

        return int(grid_x), int(grid_y)

    def set_shake(self, offset_x, offset_y):
        """Set screen shake offset (called by screen shake system)."""
        self.shake_offset_x = offset_x
        self.shake_offset_y = offset_y

    def get_tile_size(self):
        """Get current tile size (useful for animations that need to scale)."""
        return self.tile_size

    def set_zoom(self, zoom_level):
        """
        Set zoom level (1.0 = normal).
        Note: This would require additional changes to tile rendering.
        """
        self.zoom = zoom_level

    def update_layout(self, grid_offset_x=None, grid_offset_y=None, tile_size=None):
        """
        Update camera layout parameters.
        This allows dynamic repositioning/resizing of the game view.

        Args:
            grid_offset_x: New X offset (None = keep current)
            grid_offset_y: New Y offset (None = keep current)
            tile_size: New tile size (None = keep current)
        """
        if grid_offset_x is not None:
            self.grid_offset_x = grid_offset_x
        if grid_offset_y is not None:
            self.grid_offset_y = grid_offset_y
        if tile_size is not None:
            self.tile_size = tile_size
