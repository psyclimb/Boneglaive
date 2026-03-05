#!/usr/bin/env python3
"""
Scaling utilities for UI components
Provides centralized scaling factors for all UI elements based on resolution.
"""
from boneglaive.utils.config import ConfigManager


class ScaleManager:
    """Manages scaling factors for UI components based on resolution."""

    # Base resolution that all UI was designed for
    BASE_WIDTH = 1480
    BASE_HEIGHT = 800

    def __init__(self):
        """Initialize scaling factors from current resolution."""
        # Always create fresh config manager to get latest values
        self.config = ConfigManager()
        self.update_scale()

    def update_scale(self):
        """Update scaling factors based on current resolution in config."""
        self.screen_width = self.config.get('window_width', self.BASE_WIDTH)
        self.screen_height = self.config.get('window_height', self.BASE_HEIGHT)

        # Calculate scaling factors
        self.scale_x = self.screen_width / self.BASE_WIDTH
        self.scale_y = self.screen_height / self.BASE_HEIGHT

        # Use uniform scaling (average) for elements that should maintain aspect ratio
        self.scale_uniform = (self.scale_x + self.scale_y) / 2

        # Pre-calculate common scaled values
        self._calculate_common_values()

    def _calculate_common_values(self):
        """Pre-calculate commonly used scaled values."""
        # Panel dimensions
        self.left_panel_width = int(280 * self.scale_x)
        self.right_panel_width = int(280 * self.scale_x)
        self.top_bar_height = int(50 * self.scale_y)
        self.bottom_bar_height = int(80 * self.scale_y)

        # Button dimensions
        self.button_width = int(264 * self.scale_x)
        self.button_height = int(40 * self.scale_y)
        self.button_spacing = int(6 * self.scale_y)

        # Skill bar dimensions
        self.skill_slot_width = int(220 * self.scale_x)
        self.skill_slot_height = int(70 * self.scale_y)
        self.skill_slot_padding = int(10 * self.scale_uniform)
        self.skill_icon_size = int(50 * self.scale_uniform)

        # Font sizes
        self.font_size = max(12, int(22 * self.scale_y))
        self.small_font_size = max(10, int(16 * self.scale_y))
        self.large_font_size = max(16, int(32 * self.scale_y))

        # Combat log dimensions
        self.combat_log_width = int(264 * self.scale_x)
        self.combat_log_height = int(200 * self.scale_y)

        # Status panel dimensions
        self.status_panel_width = int(264 * self.scale_x)
        self.status_panel_height = int(150 * self.scale_y)

        # Unit info dimensions
        self.unit_info_width = int(264 * self.scale_x)
        self.unit_info_height = int(250 * self.scale_y)

        # Icon sizes
        self.status_icon_size = int(32 * self.scale_uniform)
        self.small_icon_size = int(24 * self.scale_uniform)

    def scale(self, value, axis='uniform'):
        """
        Scale a value based on the specified axis.

        Args:
            value: The base value to scale
            axis: 'x', 'y', or 'uniform' (default)

        Returns:
            Scaled integer value
        """
        if axis == 'x':
            return int(value * self.scale_x)
        elif axis == 'y':
            return int(value * self.scale_y)
        else:  # uniform
            return int(value * self.scale_uniform)

    def scale_tuple(self, values, axis='uniform'):
        """Scale a tuple of values."""
        if axis == 'uniform':
            return tuple(int(v * self.scale_uniform) for v in values)
        elif axis == 'xy':
            return (int(values[0] * self.scale_x), int(values[1] * self.scale_y))
        else:
            scale_factor = self.scale_x if axis == 'x' else self.scale_y
            return tuple(int(v * scale_factor) for v in values)


# Create a new instance each time the module is imported to ensure fresh config values
# UI components should import this as: from .scale_utils import scale_manager
scale_manager = ScaleManager()