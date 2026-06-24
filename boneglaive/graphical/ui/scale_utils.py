#!/usr/bin/env python3
"""
Scaling utilities for UI components
Provides centralized scaling factors for all UI elements based on resolution.
"""
from boneglaive.utils.config import ConfigManager


class ScaleManager:
    """Manages scaling factors for UI components based on resolution."""

    # Base resolution that all UI was designed for
    BASE_WIDTH = 1280
    BASE_HEIGHT = 720

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
        self.button_width = int(234 * self.scale_x)
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

# Singleton instance — UI components import this as: from .scale_utils import scale_manager
scale_manager = ScaleManager()


def refresh_all_module_constants():
    """Re-evaluate module-level constants in all UI files that cache scale_manager values.

    Must be called after scale_manager.update_scale() whenever the resolution
    changes so that stale module-level constants are replaced with fresh values.
    """
    import boneglaive.graphical.ui.skill_bar as _skill_bar
    _skill_bar.SKILL_SLOT_WIDTH = scale_manager.skill_slot_width
    _skill_bar.SKILL_SLOT_HEIGHT = scale_manager.skill_slot_height
    _skill_bar.SKILL_SLOT_PADDING = scale_manager.skill_slot_padding
    _skill_bar.SKILL_BAR_PADDING = scale_manager.scale(20)
    _skill_bar.SKILL_ICON_SIZE = scale_manager.skill_icon_size

    import boneglaive.graphical.ui.action_menu as _action_menu
    _action_menu.BUTTON_WIDTH = scale_manager.button_width
    _action_menu.BUTTON_HEIGHT = scale_manager.button_height
    _action_menu.BUTTON_SPACING = scale_manager.button_spacing
    _action_menu.MENU_PADDING = scale_manager.scale(8)

    import boneglaive.graphical.ui.combat_log as _combat_log
    _combat_log.LOG_WIDTH = scale_manager.scale(900, 'x')
    _combat_log.LOG_HEIGHT = scale_manager.scale(90, 'y')
    _combat_log.LOG_PADDING = scale_manager.scale(8)
    _combat_log.LINE_HEIGHT = scale_manager.scale(16, 'y')

    import boneglaive.graphical.ui.unit_status_bar as _usb
    _usb.PANEL_WIDTH = scale_manager.left_panel_width
    _usb.UNIT_CARD_WIDTH = scale_manager.scale(84, 'x')
    _usb.UNIT_CARD_HEIGHT = scale_manager.scale(70, 'y')
    _usb.CARD_PADDING = scale_manager.scale(6)
    _usb.TITLE_HEIGHT = scale_manager.scale(35, 'y')
    _usb.HP_BAR_HEIGHT = scale_manager.scale(4, 'y')
    _usb.SPRITE_SIZE = scale_manager.scale(32, 'uniform')

    import boneglaive.graphical.ui.respawn_window as _rw
    _rw.WINDOW_WIDTH = scale_manager.scale(500, 'x')
    _rw.WINDOW_HEIGHT = scale_manager.scale(400, 'y')
    _rw.ITEM_HEIGHT = scale_manager.scale(60, 'y')
    _rw.ITEM_PADDING = scale_manager.scale(10)
    _rw.SCROLL_SPEED = scale_manager.scale(3, 'y')

    import boneglaive.graphical.ui.upgrade_window as _uw
    _uw.WINDOW_WIDTH = scale_manager.scale(800, 'x')
    _uw.WINDOW_HEIGHT = scale_manager.scale(650, 'y')
    _uw.ITEM_HEIGHT = scale_manager.scale(110, 'y')
    _uw.ITEM_PADDING = scale_manager.scale(15)

    import boneglaive.graphical.ui.top_bar as _tb
    _tb.TOP_BAR_HEIGHT = scale_manager.scale(60, 'y')
    _tb.SECTION_PADDING = scale_manager.scale(20)
    _tb.TEXT_PADDING = scale_manager.scale(15)

    import boneglaive.graphical.ui.unit_info as _ui
    _ui.PANEL_WIDTH = scale_manager.unit_info_width
    _ui.PANEL_HEIGHT = scale_manager.scale(440, 'y')
    _ui.PANEL_PADDING = scale_manager.scale(10)
    _ui.LINE_HEIGHT = scale_manager.scale(18, 'y')
    _ui.HP_BAR_HEIGHT = scale_manager.scale(20, 'y')

    import boneglaive.graphical.ui.help_page as _hp
    _hp.MARGIN = scale_manager.scale(30)
    _hp.CONTENT_WIDTH = scale_manager.scale(700, 'x')
    _hp.ICON_SIZE = scale_manager.scale(40, 'uniform')
    _hp.LINE_SPACING = scale_manager.scale(24, 'y')
    _hp.PARAGRAPH_SPACING = scale_manager.scale(12, 'y')
    _hp.SECTION_SPACING = scale_manager.scale(20, 'y')

    import boneglaive.graphical.ui.status_effects as _se
    _se.PANEL_WIDTH = scale_manager.scale(350, 'x')
    _se.PANEL_PADDING = scale_manager.scale(10)
    _se.EFFECT_HEIGHT = scale_manager.scale(50, 'y')
    _se.ICON_SIZE = scale_manager.status_icon_size
    _se.SPACING = scale_manager.scale(8)

    import boneglaive.graphical.ui.message_log_window as _mlw
    _mlw.LINE_HEIGHT = scale_manager.scale(20, 'y')
    _mlw.PADDING = scale_manager.scale(20)
    _mlw.SCROLLBAR_WIDTH = scale_manager.scale(12, 'x')

    import boneglaive.graphical.ui.motor_animation as _ma
    _ma.MOTOR_WIDTH = scale_manager.scale(250, 'x')
    _ma.MOTOR_HEIGHT = scale_manager.scale(180, 'y')

    import boneglaive.graphical.ui.setup_window as _sw
    _sw.WINDOW_WIDTH = scale_manager.scale(550, 'x')
    _sw.WINDOW_HEIGHT = scale_manager.scale(700, 'y')
    _sw.ITEM_HEIGHT = scale_manager.scale(55, 'y')
    _sw.ITEM_PADDING = scale_manager.scale(8)
    _sw.SCROLL_SPEED = scale_manager.scale(3, 'y')

    # Refresh TILE_SIZE in animations/core.py and all animation modules that
    # imported it at module level (from .core import TILE_SIZE copies the value)
    import boneglaive.graphical.animations.core as _anim_core
    screen_width = scale_manager.screen_width
    left_panel_ratio = 0.21875
    game_board_width = screen_width * (1 - 2 * left_panel_ratio)
    new_tile_size = int(game_board_width // 20)
    _anim_core.TILE_SIZE = new_tile_size

    # Update all animation modules that copied TILE_SIZE via top-level import
    _anim_modules = [
        'boneglaive.graphical.animations.derelictionist',
        'boneglaive.graphical.animations.interferer',
        'boneglaive.graphical.animations.glaiveman',
        'boneglaive.graphical.animations.marrow_condenser',
        'boneglaive.graphical.animations.grayman',
        'boneglaive.graphical.animations.potpourrist',
        'boneglaive.graphical.animations.core_animations',
        'boneglaive.graphical.animations.animation_factory',
        'boneglaive.graphical.animations.fowl_contrivance',
        'boneglaive.graphical.animations.gas_machinist',
        'boneglaive.graphical.animations.delphic_appraiser',
        'boneglaive.graphical.animations.mandible_foreman',
    ]
    import sys
    for mod_name in _anim_modules:
        mod = sys.modules.get(mod_name)
        if mod and hasattr(mod, 'TILE_SIZE'):
            mod.TILE_SIZE = new_tile_size

    # Also refresh in game_state.py if loaded (uses TILE_SIZE in functions)
    _gs = sys.modules.get('boneglaive.graphical.game_state')
    if _gs and hasattr(_gs, 'TILE_SIZE'):
        _gs.TILE_SIZE = new_tile_size