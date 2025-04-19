#!/usr/bin/env python3
"""
Abstract rendering interface to support multiple rendering backends.
This allows switching between text-based (curses) and graphical (pygame/etc) rendering.
"""

import abc
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

class RenderBackend(Enum):
    CURSES = "curses"
    PYGAME = "pygame"
    # Could add other backends like: PYGLET, SDL, etc.

class RenderInterface(abc.ABC):
    """Abstract base class for different rendering implementations."""
    
    @abc.abstractmethod
    def initialize(self) -> None:
        """Initialize the rendering system."""
        pass
    
    @abc.abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the rendering system."""
        pass
    
    @abc.abstractmethod
    def clear_screen(self) -> None:
        """Clear the screen."""
        pass
    
    @abc.abstractmethod
    def refresh(self) -> None:
        """Refresh/update the display."""
        pass
    
    @abc.abstractmethod
    def draw_text(self, y: int, x: int, text: str, color_id: int = 1, 
                 attributes: int = 0) -> None:
        """Draw text at the specified position with optional formatting."""
        pass
    
    @abc.abstractmethod
    def draw_tile(self, y: int, x: int, tile_id: str, color_id: int = 1) -> None:
        """Draw a tile at the specified position."""
        pass
    
    @abc.abstractmethod
    def get_input(self) -> int:
        """Get user input as a key code."""
        pass
    
    @abc.abstractmethod
    def set_cursor(self, visible: bool) -> None:
        """Set cursor visibility."""
        pass
    
    @abc.abstractmethod
    def get_size(self) -> Tuple[int, int]:
        """Get the size of the rendering area as (height, width)."""
        pass
    
    @abc.abstractmethod
    def setup_colors(self) -> None:
        """Set up color pairs for the rendering system."""
        pass
    
    # Animation-specific methods
    @abc.abstractmethod
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 1, duration: float = 0.5) -> None:
        """Animate a projectile from start to end position."""
        pass
    
    @abc.abstractmethod
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """Flash a tile with different characters and colors in sequence."""
        pass