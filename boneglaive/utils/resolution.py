#!/usr/bin/env python3
"""
Resolution and Layout Management
Defines common resolutions and calculates layout dimensions dynamically.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Resolution:
    """Represents a screen resolution."""
    width: int
    height: int
    name: str

    def __str__(self):
        return f"{self.name} ({self.width}x{self.height})"

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width/height)."""
        return self.width / self.height


class ResolutionPresets:
    """Common resolution presets."""

    # 16:9 resolutions (most common)
    RES_1280x720 = Resolution(1280, 720, "720p (HD)")
    RES_1600x900 = Resolution(1600, 900, "900p (HD+)")
    RES_1920x1080 = Resolution(1920, 1080, "1080p (Full HD)")
    RES_2560x1440 = Resolution(2560, 1440, "1440p (2K)")
    RES_3840x2160 = Resolution(3840, 2160, "2160p (4K)")

    # 16:10 resolutions
    RES_1280x800 = Resolution(1280, 800, "1280x800 (16:10)")
    RES_1440x900 = Resolution(1440, 900, "1440x900 (16:10)")
    RES_1680x1050 = Resolution(1680, 1050, "1680x1050 (16:10)")
    RES_1920x1200 = Resolution(1920, 1200, "1920x1200 (16:10)")

    # Custom/current default
    RES_1480x800 = Resolution(1480, 800, "1480x800 (Default)")

    @classmethod
    def get_all_presets(cls) -> list[Resolution]:
        """Get all available resolution presets sorted by pixel count."""
        presets = [
            cls.RES_1280x720,
            cls.RES_1280x800,
            cls.RES_1440x900,
            cls.RES_1480x800,
            cls.RES_1600x900,
            cls.RES_1680x1050,
            cls.RES_1920x1080,
            cls.RES_1920x1200,
            cls.RES_2560x1440,
            cls.RES_3840x2160,
        ]
        return sorted(presets, key=lambda r: r.width * r.height)

    @classmethod
    def find_preset(cls, width: int, height: int) -> Resolution:
        """Find a preset matching the given dimensions, or create custom."""
        for preset in cls.get_all_presets():
            if preset.width == width and preset.height == height:
                return preset
        return Resolution(width, height, f"{width}x{height} (Custom)")


@dataclass
class LayoutConfig:
    """
    Dynamic layout configuration based on screen resolution.
    All values calculated as proportions of screen dimensions.
    """
    screen_width: int
    screen_height: int

    # Panel proportions (as fraction of screen width)
    left_panel_ratio: float = 0.189  # ~280/1480 = 0.189
    right_panel_ratio: float = 0.189

    # Bar proportions (as fraction of screen height)
    top_bar_ratio: float = 0.0625  # 50/800 = 0.0625
    bottom_bar_ratio: float = 0.1  # 80/800 = 0.1

    # Grid dimensions (fixed game logic)
    grid_cols: int = 20
    grid_rows: int = 10

    @property
    def left_panel_width(self) -> int:
        """Calculate left panel width."""
        return int(self.screen_width * self.left_panel_ratio)

    @property
    def right_panel_width(self) -> int:
        """Calculate right panel width."""
        return int(self.screen_width * self.right_panel_ratio)

    @property
    def top_bar_height(self) -> int:
        """Calculate top bar height."""
        return int(self.screen_height * self.top_bar_ratio)

    @property
    def bottom_bar_height(self) -> int:
        """Calculate bottom bar height."""
        return int(self.screen_height * self.bottom_bar_ratio)

    @property
    def game_board_width(self) -> int:
        """Calculate game board width (space between panels)."""
        return self.screen_width - self.left_panel_width - self.right_panel_width

    @property
    def tile_size(self) -> int:
        """Calculate tile size to fit game board."""
        return self.game_board_width // self.grid_cols

    @property
    def game_board_height(self) -> int:
        """Calculate actual game board height based on tile size."""
        return self.grid_rows * self.tile_size

    @property
    def grid_offset_x(self) -> int:
        """Calculate X offset for grid (after left panel)."""
        return self.left_panel_width

    @property
    def grid_offset_y(self) -> int:
        """Calculate Y offset for grid (centered vertically)."""
        available_height = self.screen_height - self.top_bar_height - self.bottom_bar_height
        return self.top_bar_height + (available_height - self.game_board_height) // 2

    def get_font_scale(self) -> float:
        """
        Get font scaling factor relative to default resolution (1480x800).
        Uses average of width and height scaling.
        """
        width_scale = self.screen_width / 1480
        height_scale = self.screen_height / 800
        return (width_scale + height_scale) / 2

    def scale_font_size(self, base_size: int) -> int:
        """Scale a font size based on resolution."""
        return max(8, int(base_size * self.get_font_scale()))


def create_layout(width: int, height: int) -> LayoutConfig:
    """Create a layout configuration for the given resolution."""
    return LayoutConfig(screen_width=width, screen_height=height)
