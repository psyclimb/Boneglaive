#!/usr/bin/env python3
"""
Curses-based renderer implementation.
"""

import curses
import time
import os
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
        
        # Create a buffer pad for double buffering to reduce flicker
        self.buffer = None
    
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
        
        # Initialize buffer for double buffering - make it slightly larger than screen
        # to avoid issues with terminal boundaries
        self.buffer = curses.newpad(self.height + 5, self.width + 5)
        
        # Enable non-blocking mode
        self.stdscr.nodelay(1)
        
        # Turn off echoing of keys
        curses.noecho()
        
        # Enable the keypad (for arrow keys etc)
        self.stdscr.keypad(1)
        
        # Tell curses not to delay ESC sequences
        os.environ.setdefault('ESCDELAY', '25')
        
        logger.debug(f"Initialized curses renderer with dimensions {self.height}x{self.width}")
    
    def cleanup(self) -> None:
        """Clean up the curses renderer."""
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    
    def clear_screen(self) -> None:
        """Clear the screen buffer."""
        # Clear the buffer instead of the screen directly
        if self.buffer:
            self.buffer.erase()
    
    def refresh(self) -> None:
        """Refresh the display using the buffer."""
        if self.buffer:
            # Copy the buffer to the screen
            # Params: buffer_minrow, buffer_mincol, screen_minrow, screen_mincol, screen_maxrow, screen_maxcol
            try:
                self.buffer.refresh(0, 0, 0, 0, self.height - 1, self.width - 1)
            except curses.error:
                # Handle any curses errors gracefully
                pass
    
    def draw_text(self, y: int, x: int, text: str, color_id: int = 1, attributes: int = 0) -> None:
        """Draw text at the specified position with optional formatting."""
        try:
            # Draw to the buffer instead of directly to the screen
            if self.buffer:
                self.buffer.addstr(y, x, text, curses.color_pair(color_id) | attributes)
            else:
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
            # Draw to the buffer instead of directly to the screen
            if self.buffer:
                self.buffer.addstr(screen_y, screen_x, tile_id, curses.color_pair(color_id) | attributes)
            else:
                self.stdscr.addstr(screen_y, screen_x, tile_id, curses.color_pair(color_id) | attributes)
        except curses.error:
            # Catch errors from writing outside window bounds
            pass
    
    def get_input(self) -> int:
        """Get user input as a key code."""
        # Make sure we're in non-blocking mode
        self.stdscr.nodelay(1)
        
        # Try to get input without blocking
        key = self.stdscr.getch()
        
        # If there's no input, return a special value
        if key == curses.ERR:
            # Switch back to blocking mode for waiting
            self.stdscr.nodelay(0)
            # Wait for real input
            key = self.stdscr.getch()
            
        return key
    
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
        # Get new terminal dimensions
        height, width = self.stdscr.getmaxyx()
        
        # Check if size has changed
        if height != self.height or width != self.width:
            # Update stored dimensions
            self.height = height
            self.width = width
            
            # Recreate the buffer with new size
            try:
                self.buffer = curses.newpad(self.height + 5, self.width + 5)
            except curses.error:
                # Handle errors gracefully
                pass
                
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
        curses.init_pair(16, curses.COLOR_BLACK, curses.COLOR_BLUE)  # Highlighted skill target
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
        
        # Skill target color - blue background to differentiate from attack targets (red)
        curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Skill target
    
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 7, duration: float = 0.5) -> None:
        """Animate a projectile from start to end position."""
        from boneglaive.game.animations import get_line
        
        # Get path from start to end
        start_y, start_x = start_pos
        end_y, end_x = end_pos
        path = get_line(start_y, start_x, end_y, end_x)
        
        # Save tiles along the path to restore later
        saved_tiles = []
        for pos_y, pos_x in path:
            # Skip the start and end positions
            if (pos_y, pos_x) != start_pos and (pos_y, pos_x) != end_pos:
                # Save the current tile content to restore later
                # We can't actually save it, so we'll just use empty for now
                saved_tiles.append((pos_y, pos_x, '.', 1))
                
        # Animate along the path
        for pos_y, pos_x in path:
            # Skip the start and end positions
            if (pos_y, pos_x) != start_pos and (pos_y, pos_x) != end_pos:
                # We'll create a temporary animation buffer for each frame
                if self.buffer:
                    # Clear a small region around the projectile
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            ny, nx = pos_y + dy, pos_x + dx
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                screen_y = ny + self.ui_offset_y
                                screen_x = nx * self.tile_width
                                try:
                                    # Use a blank space to clear
                                    self.buffer.addstr(screen_y, screen_x, ' ', curses.color_pair(1))
                                except curses.error:
                                    pass
                
                # Draw the projectile
                self.draw_tile(pos_y, pos_x, tile_id, color_id)
                self.refresh()
                time.sleep(duration / len(path))
        
        # No need to restore tiles as the next full redraw will handle it
    
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """Flash a tile with different characters and colors in sequence."""
        # Save the original tile to restore later (not actually implemented)
        
        # Flash sequence
        for i in range(len(tile_ids)):
            # Each flash is a separate buffer update
            self.draw_tile(y, x, tile_ids[i], color_ids[i])
            self.refresh()
            time.sleep(durations[i])
            
        # No need to restore tile as the next full redraw will handle it
        
    def animate_attack_sequence(self, y: int, x: int, sequence: List[str], 
                             color_id: int = 7, duration: float = 0.5) -> None:
        """Animate an attack sequence at the specified position.
        
        Args:
            y, x: The position to show the animation
            sequence: List of characters to show in sequence
            color_id: Color to use for the animation
            duration: Total duration of the animation
        """
        if not sequence:
            return
            
        # Calculate time per frame
        frame_duration = duration / len(sequence)
        
        # Show each frame in sequence
        for frame in sequence:
            self.draw_tile(y, x, frame, color_id)
            self.refresh()
            time.sleep(frame_duration)
            
        # No need to restore tile as the next full redraw will handle it