#!/usr/bin/env python3

# Base imports to avoid circular dependencies
# Note: Do not import game_ui here since it imports from this module
from boneglaive.ui.menu_ui import MenuUI

# Expose UI components
from boneglaive.ui.components import (
    UIComponent, CursorManager, GameModeManager, 
    ActionMenuComponent, InputManager
)

# Expose information components
from boneglaive.ui.information import (
    MessageLogComponent, HelpComponent, ChatComponent
)

# Debug and Animation
from boneglaive.ui.debug.debug_component import DebugComponent
from boneglaive.ui.animation import AnimationComponent
from boneglaive.ui.ui_renderer import UIRenderer

# Import game_ui at the end to avoid circular import
from boneglaive.ui.game_ui import GameUI

# For backward compatibility
__all__ = [
    'GameUI',
    'MenuUI',
    'UIComponent',
    'MessageLogComponent',
    'HelpComponent',
    'ChatComponent',
    'CursorManager',
    'GameModeManager',
    'DebugComponent',
    'AnimationComponent',
    'ActionMenuComponent',
    'InputManager',
    'UIRenderer'
]