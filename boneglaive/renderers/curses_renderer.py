#!/usr/bin/env python3
"""
Curses-based renderer implementation.
"""

import curses
import time
from typing import Dict, List, Optional, Tuple

from boneglaive.utils.render_interface import RenderInterface
from boneglaive.utils.debug import debug_config, logger

class CursesRenderer(RenderInterface):
    """Renderer implementation using the curses library."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height = 0
        self.width = 0
        self.ui_offset_y = 2  # Header space
        self.tile_width = 2   # Width of each tile in characters
    
    def initialize(self) -> None:
        """Initialize the curses renderer."""
        # Hide cursor
        curses.curs_set(0)
        
        # Set timeout
        self.stdscr.timeout(-1)
        
        # Set up colors
        self.setup_colors()
        
        # Get terminal dimensions
        self.height, self.width = self.stdscr.getmaxyx()
        
        logger.debug(f"Initialized curses renderer with dimensions {self.height}x{self.width}")
    
    def cleanup(self) -> None:
        """Clean up the curses renderer."""
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    
    def clear_screen(self) -> None:
        """Clear the screen."""
        self.stdscr.clear()
    
    def refresh(self) -> None:
        """Refresh the display."""
        self.stdscr.refresh()
    
    def draw_text(self, y: int, x: int, text: str, color_id: int = 1, attributes: int = 0) -> None:
        """Draw text at the specified position with optional formatting."""
        try:
            self.stdscr.addstr(y, x, text, curses.color_pair(color_id) | attributes)
        except curses.error:
            # Catch errors from writing outside window bounds
            pass
    
    def draw_tile(self, y: int, x: int, tile_id: str, color_id: int = 1, attributes: int = 0) -> None:
        """Draw a tile (character) at the specified position."""
        # In curses mode, tile_id is just a character
        screen_y = y + self.ui_offset_y
        screen_x = x * self.tile_width
        try:
            self.stdscr.addstr(screen_y, screen_x, tile_id, curses.color_pair(color_id) | attributes)
        except curses.error:
            # Catch errors from writing outside window bounds
            pass
    
    def get_input(self) -> int:
        """Get user input as a key code."""
        return self.stdscr.getch()
    
    def set_cursor(self, visible: bool) -> None:
        """Set cursor visibility."""
        curses.curs_set(1 if visible else 0)
    
    def get_size(self) -> Tuple[int, int]:
        """Get the size of the rendering area."""
        return self.height, self.width
        
    def get_terminal_size(self) -> Tuple[int, int]:
        """
        Get the current terminal size (updates each time it's called).
        
        Returns:
            Tuple of (height, width)
        """
        height, width = self.stdscr.getmaxyx()
        return height, width
    
    def setup_colors(self) -> None:
        """Set up color pairs for the renderer."""
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Cursor
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Player 1 (changed to green)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Player 2
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Highlighted move
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)    # Highlighted attack
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Attack animation
        # Use dim white (appears gray in most terminals) for move target preview
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Move target preview (gray)
        # Yellow background for selected unit
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_YELLOW) # Selected unit highlight
        # Red background for attack targets
        curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_RED)   # Attack target
        
        # Terrain colors
        curses.init_pair(11, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Dust (light white)
        curses.init_pair(12, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Limestone (yellow)
        curses.init_pair(13, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Pillar (magenta)
        curses.init_pair(14, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Furniture (cyan)
    
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 7, duration: float = 0.5) -> None:
        """Animate a projectile from start to end position."""
        from boneglaive.game.animations import get_line
        
        # Get path from start to end
        start_y, start_x = start_pos
        end_y, end_x = end_pos
        path = get_line(start_y, start_x, end_y, end_x)
        
        # Animate along the path
        for pos_y, pos_x in path:
            # Skip the start and end positions
            if (pos_y, pos_x) != start_pos and (pos_y, pos_x) != end_pos:
                self.draw_tile(pos_y, pos_x, tile_id, color_id)
                self.refresh()
                time.sleep(duration / len(path))
    
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """Flash a tile with different characters and colors in sequence."""
        for i in range(len(tile_ids)):
            self.draw_tile(y, x, tile_ids[i], color_ids[i])
            self.refresh()
            time.sleep(durations[i])