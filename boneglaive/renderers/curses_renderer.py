#!/usr/bin/env python3
"""
Curses-based renderer implementation.
"""

import time
from boneglaive.utils.animation_helpers import sleep_with_animation_speed
from boneglaive.utils.platform_compat import get_curses_module

import os

# Get platform-appropriate curses module
curses = get_curses_module()
if curses is None:
    raise ImportError("Curses module not available for this platform. On Windows, install: pip install windows-curses")
from typing import Dict, List, Optional, Tuple

from boneglaive.utils.render_interface import RenderInterface
from boneglaive.utils.debug import debug_config, logger

class CursesRenderer(RenderInterface):
    """Renderer implementation using the curses library."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height = 0
        self.width = 0
        self.ui_offset_y = 1  # Reduced header space to ensure bottom row is visible
        self.tile_width = 2   # Width of each tile in characters
        
        # Create a buffer pad for double buffering to reduce flicker
        self.buffer = None
    
    def initialize(self) -> None:
        """Initialize the curses renderer."""
        # Hide cursor
        curses.curs_set(0)
        
        # Set timeout
        self.stdscr.timeout(-1)
        
        # Use erase() instead of clear() to avoid flicker - clear() forces complete redraw
        self.stdscr.erase()
        
        # Set up colors
        self.setup_colors()
        
        # Get terminal dimensions
        self.height, self.width = self.stdscr.getmaxyx()
        
        # Clean up any existing buffer first
        if hasattr(self, 'buffer') and self.buffer:
            try:
                del self.buffer
            except:
                pass
        
        # Initialize buffer for double buffering - make it slightly larger than screen
        # to avoid issues with terminal boundaries
        self.buffer = curses.newpad(self.height + 5, self.width + 5)
        
        # Clear the new buffer
        self.buffer.clear()
        
        # Enable non-blocking mode
        self.stdscr.nodelay(1)
        
        # Turn off echoing of keys
        curses.noecho()
        
        # Enable the keypad (for arrow keys etc)
        self.stdscr.keypad(1)
        
        # Tell curses not to delay ESC sequences
        os.environ.setdefault('ESCDELAY', '25')
        
        # Do one refresh to make sure the screen is ready
        self.stdscr.refresh()
        
        logger.debug(f"Initialized curses renderer with dimensions {self.height}x{self.width}")
    
    def cleanup(self) -> None:
        """Clean up the curses renderer."""
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    
    def clear_screen(self) -> None:
        """Clear the screen buffer."""
        # Clear the buffer instead of the screen directly to avoid flicker
        if self.buffer:
            self.buffer.erase()
    
    def refresh(self) -> None:
        """Refresh the display using the buffer."""
        if self.buffer:
            # Copy the buffer to the screen
            # Params: buffer_minrow, buffer_mincol, screen_minrow, screen_mincol, screen_maxrow, screen_maxcol
            try:
                # Refresh the buffer to the screen
                self.buffer.refresh(0, 0, 0, 0, self.height - 1, self.width - 1)
            except curses.error as e:
                # Log the error but continue
                logger.error(f"Error refreshing screen: {e}")
                
                # Try a direct refresh as a fallback
                try:
                    self.stdscr.refresh()
                except:
                    pass
    
    def draw_text(self, y: int, x: int, text: str, color_id: int = 1, attributes: int = 0) -> None:
        """Draw text at the specified position with optional formatting."""
        try:
            # Draw to the buffer instead of directly to the screen
            if self.buffer:
                self.buffer.addstr(y, x, text, curses.color_pair(color_id) | attributes)
            else:
                self.stdscr.addstr(y, x, text, curses.color_pair(color_id) | attributes)
        except KeyboardInterrupt:
            # Let KeyboardInterrupt propagate up for graceful shutdown
            raise
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

        try:
            # Try to get input without blocking
            key = self.stdscr.getch()

            # If there's no input, return a special value
            if key == curses.ERR:
                # Switch back to blocking mode for waiting
                self.stdscr.nodelay(0)
                # Wait for real input
                key = self.stdscr.getch()

            return key
        except KeyboardInterrupt:
            # Convert Ctrl+C to quit action (ord('q'))
            return ord('q')
    
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
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Message log text (gray with dim attribute)
        # Yellow background for selected unit
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_YELLOW) # Selected unit highlight
        # Red background for attack targets
        curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_RED)   # Attack target
        
        # Terrain colors - different shades of white for the Lime Foyer
        curses.init_pair(11, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Dust (normal white)
        # For color_pair(12), use bright white by using A_BOLD attribute when drawing
        curses.init_pair(12, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Limestone (bright white, applied with A_BOLD)
        curses.init_pair(13, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Pillar (white, different symbol)
        # For dim white (gray), we'll use a lower intensity of white
        curses.init_pair(14, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Furniture (will use dim white/gray)
        # Marrow Wall color - red to stand out
        curses.init_pair(20, curses.COLOR_RED, curses.COLOR_BLACK)      # Marrow Wall (red)
        
        # Skill target color - blue background to differentiate from attack targets (red)
        curses.init_pair(15, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Skill target
        
        # Player-specific move highlight colors
        curses.init_pair(17, curses.COLOR_BLACK, curses.COLOR_GREEN)     # Player 1 move highlight - green background
        curses.init_pair(18, curses.COLOR_BLACK, curses.COLOR_BLUE)      # Player 2 move highlight - blue background
        
        # Message log special colors for critical events
        curses.init_pair(19, curses.COLOR_RED, curses.COLOR_BLACK)       # Wretch messages - bright red
        curses.init_pair(20, curses.COLOR_RED, curses.COLOR_BLACK)       # Death messages - dark red (will use dim attribute)
        curses.init_pair(21, curses.COLOR_YELLOW, curses.COLOR_BLACK)    # Canyon floor (tan/brown)
        curses.init_pair(22, curses.COLOR_WHITE, curses.COLOR_BLACK)     # Estranged unit effect - gray (white with dim attribute)
        curses.init_pair(23, curses.COLOR_MAGENTA, curses.COLOR_BLACK)   # Damage numbers - magenta
        curses.init_pair(24, curses.COLOR_WHITE, curses.COLOR_BLACK)     # Healing numbers - white (bright with A_BOLD)
        curses.init_pair(25, curses.COLOR_RED, curses.COLOR_BLACK)       # Red text (for critical HP)
    
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 7, duration: float = 0.5) -> None:
        """Animate a projectile from start to end position."""
        from boneglaive.game.animations import get_line
        
        # Apply the global animation speed multiplier from config
        from boneglaive.utils.config import ConfigManager
        config = ConfigManager()
        animation_speed = config.get('animation_speed', 1.0)
        adjusted_duration = duration / animation_speed if animation_speed > 0 else duration
        
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
                sleep_with_animation_speed(adjusted_duration / len(path))
        
        # No need to restore tiles as the next full redraw will handle it
    
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """Flash a tile with different characters and colors in sequence."""
        # Save the original tile to restore later (not actually implemented)
        
        # Apply the global animation speed multiplier from config
        from boneglaive.utils.config import ConfigManager
        config = ConfigManager()
        animation_speed = config.get('animation_speed', 1.0)
        
        # Flash sequence
        for i in range(len(tile_ids)):
            # Adjust duration using animation speed
            adjusted_duration = durations[i] / animation_speed if animation_speed > 0 else durations[i]
            
            # Each flash is a separate buffer update
            self.draw_tile(y, x, tile_ids[i], color_ids[i])
            self.refresh()
            sleep_with_animation_speed(adjusted_duration)
            
        # No need to restore tile as the next full redraw will handle it
        
    def draw_damage_text(self, y: int, x: int, text: str, color_id: int = 7, 
                        attributes: int = 0) -> None:
        """Draw damage/healing text (same as draw_text for curses renderer)."""
        self.draw_text(y, x, text, color_id, attributes)
        
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

        # Apply the global animation speed multiplier from config
        from boneglaive.utils.config import ConfigManager
        config = ConfigManager()
        animation_speed = config.get('animation_speed', 1.0)
        adjusted_duration = duration / animation_speed if animation_speed > 0 else duration

        # Calculate time per frame
        frame_duration = adjusted_duration / len(sequence)

        # Show each frame in sequence
        for frame in sequence:
            self.draw_tile(y, x, frame, color_id)
            self.refresh()
            sleep_with_animation_speed(frame_duration)

        # No need to restore tile as the next full redraw will handle it

    def animate_path(self, start_y: int, start_x: int, end_y: int, end_x: int,
                    sequence: List[str], color_id: int = 7, duration: float = 0.5) -> None:
        """Animate an effect moving along a path from start to end position.

        Args:
            start_y, start_x: The starting position of the animation
            end_y, end_x: The ending position of the animation
            sequence: List of characters to show in sequence along the path
            color_id: Color to use for the animation
            duration: Total duration of the animation
        """
        if not sequence:
            return

        # Get the path from start to end using get_line function
        # Need to import and call it directly since we changed parameter order
        from boneglaive.game.animations import get_line
        path = get_line(start_y, start_x, end_y, end_x)

        if not path:
            return

        # Apply the global animation speed multiplier from config
        from boneglaive.utils.config import ConfigManager
        config = ConfigManager()
        animation_speed = config.get('animation_speed', 1.0)
        adjusted_duration = duration / animation_speed if animation_speed > 0 else duration

        # Calculate time per step along the path
        step_duration = adjusted_duration / len(path)

        # Use a repeating sequence pattern if the path is longer than the sequence
        sequence_length = len(sequence)

        # Animate along the path
        for i, (y, x) in enumerate(path):
            # Get the appropriate frame from the sequence (loop if needed)
            frame = sequence[i % sequence_length]

            # Draw the current frame at the current position
            self.draw_tile(y, x, frame, color_id)
            self.refresh()
            sleep_with_animation_speed(step_duration)

            # Clear the previous position (except the start and end points)
            if (y != start_y or x != start_x) and (y != end_y or x != end_x) and i < len(path) - 1:
                # Just draw a space to clear it - the next redraw will restore the proper tile
                self.draw_tile(y, x, ' ', 0)

        # No need to restore tiles as the next full redraw will handle it