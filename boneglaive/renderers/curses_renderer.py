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
        
        # Center the tile in its cell for better aesthetics
        # If tile_id is a single character, pad it with a space to center
        if len(tile_id) == 1:
            display_tile = f"{tile_id} "
        else:
            display_tile = tile_id[:self.tile_width]
            
        try:
            # Draw to the buffer instead of directly to the screen
            if self.buffer:
                self.buffer.addstr(screen_y, screen_x, display_tile, curses.color_pair(color_id) | attributes)
            else:
                self.stdscr.addstr(screen_y, screen_x, display_tile, curses.color_pair(color_id) | attributes)
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
        # Initialize color support and use colors if available
        curses.start_color()
        curses.use_default_colors()  # Use terminal's default colors
        
        # Try to enable 256 color mode if available
        try:
            # Check if terminal supports 256 colors
            if curses.can_change_color() and curses.COLORS >= 256:
                self.has_extended_colors = True
            else:
                self.has_extended_colors = False
        except:
            self.has_extended_colors = False
        
        # UI and gameplay colors
        curses.init_pair(1, curses.COLOR_WHITE, -1)        # Default text (terminal default bg)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Cursor
        curses.init_pair(3, curses.COLOR_GREEN, -1)        # Player 1 units (bright green)
        curses.init_pair(4, curses.COLOR_BLUE, -1)         # Player 2 units (bright blue)
        curses.init_pair(5, curses.COLOR_GREEN, -1)        # Move highlight (with bold attr)
        curses.init_pair(6, curses.COLOR_RED, -1)          # Attack highlight (with bold attr)
        curses.init_pair(7, curses.COLOR_YELLOW, -1)       # Attack animation (bright yellow)
        curses.init_pair(8, curses.COLOR_WHITE, -1)        # Preview (with dim attr)
        curses.init_pair(9, curses.COLOR_YELLOW, -1)       # Selected unit (with bold attr)
        curses.init_pair(10, curses.COLOR_RED, -1)         # Attack target (with bold attr)
        
        # Terrain colors - more distinct and vibrant
        curses.init_pair(11, curses.COLOR_WHITE, -1)       # Dust (with dim attr)
        curses.init_pair(12, curses.COLOR_YELLOW, -1)      # Limestone (bright yellow)
        curses.init_pair(13, curses.COLOR_MAGENTA, -1)     # Pillar (bright magenta)
        curses.init_pair(14, curses.COLOR_CYAN, -1)        # Furniture (bright cyan)
        
        # Additional UI element colors
        curses.init_pair(15, curses.COLOR_BLACK, curses.COLOR_CYAN)     # Header bar
        curses.init_pair(16, curses.COLOR_CYAN, -1)                     # Info text
        curses.init_pair(17, curses.COLOR_BLACK, curses.COLOR_GREEN)    # Success/positive
        curses.init_pair(18, curses.COLOR_BLACK, curses.COLOR_RED)      # Error/negative
        curses.init_pair(19, curses.COLOR_BLACK, curses.COLOR_YELLOW)   # Warning/caution
        curses.init_pair(20, curses.COLOR_WHITE, curses.COLOR_BLUE)     # Menu highlight
        
        # Game element colors
        curses.init_pair(21, curses.COLOR_RED, -1)         # Health/HP
        curses.init_pair(22, curses.COLOR_YELLOW, -1)      # Attack power
        curses.init_pair(23, curses.COLOR_CYAN, -1)        # Defense
        curses.init_pair(24, curses.COLOR_GREEN, -1)       # Movement
        curses.init_pair(25, curses.COLOR_MAGENTA, -1)     # Special abilities
    
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 7, duration: float = 0.5) -> None:
        """
        Animate a projectile from start to end position with motion blur and trail effects.
        Creates a more dynamic and visually appealing animation.
        """
        from boneglaive.game.animations import get_line
        
        # Get path from start to end
        start_y, start_x = start_pos
        end_y, end_x = end_pos
        path = get_line(start_y, start_x, end_y, end_x)
        
        # For short paths, slow down the animation slightly
        step_duration = min(duration / max(len(path), 1), 0.1)
        
        # Create trail effects - store positions of trailing particles
        trail_length = min(3, len(path) // 2)
        
        # Get alternate character for trail effect
        if tile_id == '➶':  # Arrow
            trail_chars = ['·', '·']
        elif tile_id == '✦':  # Magic
            trail_chars = ['⋆', '·']
        else:  # Default/melee
            trail_chars = ['·', '·']
            
        # Animate with trail effect
        for i, (pos_y, pos_x) in enumerate(path):
            # Skip the start position for cleaner animation
            if (pos_y, pos_x) == start_pos:
                continue
                
            # Skip the end position - let combat animation handle it
            if (pos_y, pos_x) == end_pos:
                break
                
            # Draw the projectile at current position with bright color
            self.draw_tile(pos_y, pos_x, tile_id, color_id, curses.A_BOLD)
            
            # Draw trail at previous positions
            for t in range(1, min(trail_length + 1, i + 1)):
                if i - t < len(path):
                    trail_y, trail_x = path[i - t]
                    # Skip if trail would overlap with start or end
                    if (trail_y, trail_x) != start_pos and (trail_y, trail_x) != end_pos:
                        # Use different trail character based on position in trail
                        trail_char = trail_chars[min(t-1, len(trail_chars)-1)]
                        # Fade the trail as it gets further from projectile
                        trail_color = color_id
                        trail_attr = curses.A_DIM
                        self.draw_tile(trail_y, trail_x, trail_char, trail_color, trail_attr)
            
            # Refresh the screen with this frame
            self.refresh()
            
            # Add slight pause between frames for animation speed
            time.sleep(step_duration)
            
            # Clear the current position for next frame (unless we're at the end)
            if i < len(path) - 1:
                # Only clear if not part of trail for next position
                next_trail_positions = []
                next_i = i + 1
                for t in range(1, min(trail_length + 1, next_i + 1)):
                    if next_i - t < len(path):
                        next_trail_positions.append(path[next_i - t])
                
                # If current position won't be part of next trail, clear it
                if (pos_y, pos_x) not in next_trail_positions:
                    self.draw_tile(pos_y, pos_x, ' ', 1)
                    
        # Add final impact effect at target position
        if len(path) > 2:  # Only if path is long enough
            # Flash effect at target
            self.draw_tile(end_y, end_x, '*', color_id, curses.A_BOLD)
            self.refresh()
            time.sleep(0.1)
            
        # No need to restore tiles as the next full redraw will handle it
    
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """
        Flash a tile with different characters and colors in sequence.
        Enhanced to create a more dynamic and attractive effect with surrounding glow.
        """
        # Directions for surrounding tiles (including diagonals)
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        # Flash sequence with glow effect
        for i in range(len(tile_ids)):
            # First, draw soft glow around the target tile
            if i > 0:  # Skip glow on first frame for cleaner effect
                for dy, dx in directions:
                    glow_y, glow_x = y + dy, x + dx
                    # Only draw glow if position is valid game board cell
                    if 0 <= glow_y < self.height - self.ui_offset_y and 0 <= glow_x < self.width:
                        # Use smaller, dimmer character for glow
                        self.draw_tile(glow_y, glow_x, '·', color_ids[i], curses.A_DIM)
            
            # Draw the main flashing tile with full brightness and specified attributes
            attrs = curses.A_BOLD if i % 2 == 0 else 0  # Alternate between bold and normal
            self.draw_tile(y, x, tile_ids[i], color_ids[i], attrs)
            
            # For key frames, add an impact effect
            if i == 0 or i == len(tile_ids) // 2:
                # Draw small expanding circle as impact
                self.draw_tile(y, x, '*', color_ids[i], curses.A_BOLD | curses.A_BLINK)
            
            # Refresh and pause for this frame
            self.refresh()
            time.sleep(durations[i])
            
            # Clean up glow effect after pause
            if i > 0 and i < len(tile_ids) - 1:  # Skip cleanup on last frame
                for dy, dx in directions:
                    glow_y, glow_x = y + dy, x + dx
                    if 0 <= glow_y < self.height - self.ui_offset_y and 0 <= glow_x < self.width:
                        self.draw_tile(glow_y, glow_x, ' ', 1)
        
        # No need to restore tiles as the next full redraw will handle it