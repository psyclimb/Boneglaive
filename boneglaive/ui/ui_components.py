#!/usr/bin/env python3
"""
Components for the Boneglaive UI.

This module is maintained for backward compatibility.
New code should import directly from the component modules.
"""

# Import base UIComponent
from boneglaive.ui.components.base import UIComponent

# Import information components
from boneglaive.ui.information.message_log import MessageLogComponent
from boneglaive.ui.information.help import HelpComponent
from boneglaive.ui.information.chat import ChatComponent

# Import UI components
from boneglaive.ui.components.cursor import CursorManager
from boneglaive.ui.components.game_mode import GameModeManager
from boneglaive.ui.components.action_menu import ActionMenuComponent
from boneglaive.ui.components.input_manager import InputManager

# Import debug component
from boneglaive.ui.debug.debug_component import DebugComponent

# Import animation component
from boneglaive.ui.animation import AnimationComponent

# Re-export all components
__all__ = [
    'UIComponent',
    'MessageLogComponent',
    'HelpComponent',
    'ChatComponent',
    'CursorManager',
    'GameModeManager',
    'DebugComponent',
    'AnimationComponent',
    'ActionMenuComponent',
    'InputManager'
]