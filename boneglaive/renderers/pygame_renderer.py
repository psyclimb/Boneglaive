#!/usr/bin/env python3
"""
Pygame-based renderer implementation for graphical display.
"""

import pygame
import sys
import time
from typing import Dict, List, Optional, Tuple, Any
from boneglaive.utils.render_interface import RenderInterface
from boneglaive.utils.debug import debug_config, logger
from boneglaive.utils.animation_helpers import sleep_with_animation_speed
from boneglaive.utils.asset_manager import AssetManager
from boneglaive.utils.config import ConfigManager
from boneglaive.utils.constants import UnitType

class PygameRenderer(RenderInterface):
    """Renderer implementation using pygame for graphical display."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.screen = None
        self.clock = None
        self.font = None
        
        # Character grid system (like Dwarf Fortress)
        self.char_width = 12   # Width of each character cell in pixels
        self.char_height = 20  # Height of each character cell in pixels
        
        # Match curses renderer spacing: tile_width = 2 (each game tile uses 2 character columns)
        self.tile_width = 2
        self.tile_pixel_width = self.char_width * self.tile_width  # 2 characters wide per game tile
        
        # Match curses renderer UI offset to leave room for header
        self.ui_offset_y = 1  # Same offset as curses renderer
        
        self.grid_width = width // self.tile_pixel_width   # Game tiles per row
        self.grid_height = height // self.char_height # Characters per column
        
        # Legacy tile_size for compatibility
        self.tile_size = 32  # Keep for sprite fallbacks
        self.colors = {}
        self.running = True
        
        # Font system with fallbacks
        self.monospace_fonts = [
            "DejaVu Sans Mono",
            "Consolas", 
            "Courier New",
            "Liberation Mono",
            "monospace"
        ]
        
        # Asset management - force text mode for character-based rendering
        self.config_manager = ConfigManager()
        # Create a temporary config that forces text mode for asset loading
        text_config = ConfigManager()
        text_config.set('display_mode', 'text')
        self.asset_manager = AssetManager(text_config)
        
        # Will be initialized after pygame.init()
        self.key_map = {}
    
    def initialize(self) -> None:
        """Initialize the pygame renderer."""
        pygame.init()
        
        # Create the display
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Boneglaive2")
        
        # Create clock for FPS control
        self.clock = pygame.time.Clock()
        
        # Initialize monospace font with fallbacks
        self.font = self._load_best_monospace_font()
        
        # Recalculate grid based on actual font metrics
        char_metrics = self.font.size("W")  # Use wide character for measurement
        self.char_width = char_metrics[0]
        self.char_height = char_metrics[1]
        
        # Update tile pixel width with actual font metrics
        self.tile_pixel_width = self.char_width * self.tile_width
        
        # Grid dimensions in character columns (for UI compatibility)
        self.grid_width = self.width // self.char_width   # Character columns per row
        self.grid_height = self.height // self.char_height # Character rows
        
        # Set up colors
        self.setup_colors()
        
        # Set up key mapping after pygame init
        self.setup_key_mapping()
        
        # Clear screen initially
        self.clear_screen()
        
    def _load_best_monospace_font(self, size: int = 16) -> pygame.font.Font:
        """Load the best available monospace font with fallbacks."""
        # Try system monospace fonts first
        for font_name in self.monospace_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                if font:
                    logger.info(f"Using monospace font: {font_name}")
                    return font
            except:
                continue
        
        # Fallback to default pygame font
        logger.warning("No system monospace font found, using pygame default")
        return pygame.font.Font(None, size)
    
    def draw_char(self, y: int, x: int, char: str, fg_color_id: int = 7, 
                  bg_color_id: Optional[int] = None, attributes: int = 0) -> None:
        """Draw a single character at exact grid position (Dwarf Fortress style)."""
        if x >= self.grid_width or y >= self.grid_height or x < 0 or y < 0:
            return  # Outside grid bounds
        
        # Calculate exact pixel position (for individual character positioning)
        pixel_x = x * self.char_width
        pixel_y = y * self.char_height
        
        # Draw background if specified
        if bg_color_id is not None:
            bg_color = self.colors.get(bg_color_id, self.colors[0])
            bg_rect = pygame.Rect(pixel_x, pixel_y, self.char_width, self.char_height)
            pygame.draw.rect(self.screen, bg_color, bg_rect)
        
        # Draw character
        if char and char != ' ':
            fg_color = self.colors.get(fg_color_id, self.colors[7])
            
            # Handle attributes - map curses constants to pygame
            font = self.font
            if attributes:
                try:
                    # Check for curses attribute constants
                    is_bold = bool(attributes & 2097152) or bool(attributes & 1)  # curses.A_BOLD or simple bold bit
                    is_dim = bool(attributes & 1048576)  # curses.A_DIM
                    
                    if is_bold or is_dim:
                        font = pygame.font.Font(self.font.get_name(), self.font.get_height())
                        font.set_bold(is_bold)
                        # For dim, we'll adjust color instead of font
                        if is_dim:
                            # Dim the color by reducing brightness
                            r, g, b = fg_color
                            fg_color = (r//2, g//2, b//2)
                except:
                    font = self.font
            
            char_surface = font.render(char, True, fg_color)
            
            # Center character in cell
            char_rect = char_surface.get_rect()
            char_rect.center = (pixel_x + self.char_width // 2, pixel_y + self.char_height // 2)
            
            self.screen.blit(char_surface, char_rect)
        
    def setup_key_mapping(self):
        """Set up key mapping from pygame to curses-like key codes."""
        self.key_map = {
            # Arrow keys - map to both curses constants and vim keys
            pygame.K_UP: 259,     # curses.KEY_UP
            pygame.K_DOWN: 258,   # curses.KEY_DOWN  
            pygame.K_LEFT: 260,   # curses.KEY_LEFT
            pygame.K_RIGHT: 261,  # curses.KEY_RIGHT
            pygame.K_k: 259,      # Also map k to UP
            pygame.K_j: 258,      # Also map j to DOWN
            pygame.K_h: 260,      # Also map h to LEFT  
            pygame.K_l: 261,      # Also map l to RIGHT
            
            # Special keys
            pygame.K_RETURN: 343,  # curses.KEY_ENTER
            pygame.K_BACKSPACE: 263,  # curses.KEY_BACKSPACE
            pygame.K_SPACE: ord(' '),
            pygame.K_ESCAPE: 27,  # Escape
            pygame.K_TAB: ord('\t'),
            
            # Letter keys  
            pygame.K_q: ord('q'),
            pygame.K_m: ord('m'),
            pygame.K_s: ord('s'),
            pygame.K_a: ord('a'),
            pygame.K_r: ord('r'),
            pygame.K_t: ord('t'),
            pygame.K_e: ord('e'),
            pygame.K_w: ord('w'),
            pygame.K_d: ord('d'),
            pygame.K_f: ord('f'),
            pygame.K_g: ord('g'),
            pygame.K_b: ord('b'),
            pygame.K_c: ord('c'),
            pygame.K_v: ord('v'),
            pygame.K_x: ord('x'),
            pygame.K_z: ord('z'),
            
            # Missing important keys
            pygame.K_p: ord('p'),        # Teleport mode
            pygame.K_y: ord('y'),        # Diagonal movement (up-left)
            pygame.K_u: ord('u'),        # Diagonal movement (up-right)  
            pygame.K_i: ord('i'),        # Diagonal movement 
            pygame.K_o: ord('o'),        # Diagonal movement
            pygame.K_n: ord('n'),        # Diagonal movement (down-left)
            pygame.K_SLASH: ord('/'),    # Often used in games
            pygame.K_QUESTION: ord('?'), # Help system (SHIFT+/)
            
            # Special character keys
            pygame.K_PERIOD: ord('.'),
            pygame.K_COMMA: ord(','),
            pygame.K_SEMICOLON: ord(';'),
            pygame.K_QUOTE: ord("'"),
            
            # Number keys
            pygame.K_1: ord('1'),
            pygame.K_2: ord('2'),
            pygame.K_3: ord('3'),
            pygame.K_4: ord('4'),
            pygame.K_5: ord('5'),
            pygame.K_6: ord('6'),
            pygame.K_7: ord('7'),
            pygame.K_8: ord('8'),
            pygame.K_9: ord('9'),
            pygame.K_0: ord('0'),
        }
        
    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()
        
    def setup_colors(self) -> None:
        """Set up color mappings similar to curses colors."""
        self.colors = {
            0: (0, 0, 0),         # Black
            1: (255, 0, 0),       # Red
            2: (0, 255, 0),       # Green
            3: (255, 255, 0),     # Yellow
            4: (0, 0, 255),       # Blue
            5: (255, 0, 255),     # Magenta
            6: (0, 255, 255),     # Cyan
            7: (255, 255, 255),   # White
            8: (128, 128, 128),   # Gray
        }
        
    def clear_screen(self) -> None:
        """Clear the screen."""
        self.screen.fill(self.colors[0])  # Fill with black
        
    def refresh(self) -> None:
        """Refresh/update the display."""
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS
        
    def draw_text(self, y: int, x: int, text: str, color_id: int = 7, 
                 attributes: int = 0) -> None:
        """Draw text at the specified grid position using fixed character grid."""
        color = self.colors.get(color_id, self.colors[7])
        
        # Handle attributes - map curses constants to pygame
        font = self.font
        if attributes:
            try:
                # Check for curses attribute constants
                is_bold = bool(attributes & 2097152) or bool(attributes & 1)  # curses.A_BOLD or simple bold bit
                is_dim = bool(attributes & 1048576)  # curses.A_DIM
                
                if is_bold or is_dim:
                    font = pygame.font.Font(self.font.get_name(), self.font.get_height())
                    font.set_bold(is_bold)
                    # For dim, we'll adjust color in the render loop
            except:
                font = self.font  # Fallback to regular font
            
        # Check if we need to dim the color
        render_color = color
        if attributes and (attributes & 1048576):  # curses.A_DIM
            r, g, b = color
            render_color = (r//2, g//2, b//2)
        
        # Render each character individually for perfect grid alignment
        for i, char in enumerate(text):
            if x + i >= self.grid_width or y >= self.grid_height:
                break  # Don't render outside grid bounds
                
            char_surface = font.render(char, True, render_color)
            
            # Calculate exact pixel position in character grid and center like draw_char
            pixel_x = (x + i) * self.char_width
            pixel_y = y * self.char_height
            
            # Center character in cell (consistent with draw_char)
            char_rect = char_surface.get_rect()
            char_rect.center = (pixel_x + self.char_width // 2, pixel_y + self.char_height // 2)
            
            self.screen.blit(char_surface, char_rect)
        
    def draw_tile(self, y: int, x: int, tile_id: str, color_id: int = 7, attributes: int = 0) -> None:
        """Draw a tile using character grid system (Dwarf Fortress style)."""
        # Calculate screen position like curses renderer: screen_x = x * tile_width, screen_y = y + ui_offset_y
        # Each game tile gets 2 character columns (tile_width = 2)
        screen_x = x * self.tile_width
        screen_y = y + self.ui_offset_y  # Leave room for UI header
        
        # The tile_id is already a character from the UI renderer, so draw it directly
        # Handle multi-character tiles (like unit + status effect symbols)
        if tile_id and len(tile_id) > 0:
            # Draw each character in the tile_id string at consecutive character positions
            for i, char in enumerate(tile_id):
                char_x = screen_x + i
                # Check bounds in character space
                if char_x >= self.grid_width or char_x < 0:
                    break  # Don't draw outside character grid bounds
                self.draw_char(screen_y, char_x, char, color_id, attributes=attributes)
        else:
            # Draw empty/unknown tile as a dot
            self.draw_char(screen_y, screen_x, '.', 8, attributes=attributes)  # Gray dot
    
    def draw_unit_sprite(self, y: int, x: int, unit_type: UnitType, player: int = 1) -> None:
        """Draw a unit using character grid system."""
        # Use character-based rendering (AssetManager provides characters, not sprites)
        unit_char = self.asset_manager.get_unit_tile(unit_type)
        color_id = 1 if player == 1 else 4  # Red for player 1, blue for player 2
        self.draw_char(y, x, unit_char, color_id, attributes=1)  # Bold for units
    
    def draw_ui_element(self, y: int, x: int, element_type: str, color_id: int = 6) -> None:
        """Draw a UI element using character grid system."""
        # Use character-based rendering with background for UI elements
        if element_type == 'cursor':
            # Draw cursor as bright character with background
            self.draw_char(y, x, '█', color_id, bg_color_id=0)
        elif element_type == 'selected':
            # Draw selection as background highlight
            self.draw_char(y, x, ' ', 7, bg_color_id=color_id)
        else:
            # Default to character rendering
            ui_char = self.asset_manager.get_ui_tile(element_type)
            self.draw_char(y, x, ui_char, color_id)
    
    def draw_effect_sprite(self, y: int, x: int, effect_type: str, color_id: int = 1) -> None:
        """Draw an effect using character grid system."""
        # Use character-based rendering
        effect_char = self.asset_manager.get_effect_tile(effect_type)
        self.draw_char(y, x, effect_char, color_id)
            
    def get_input(self) -> int:
        """Get user input as a key code."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return ord('q')  # Quit
                elif event.type == pygame.KEYDOWN:
                    # Check for modifier keys
                    mods = pygame.key.get_pressed()
                    shift_held = mods[pygame.K_LSHIFT] or mods[pygame.K_RSHIFT]
                    
                    # Handle special modifier combinations
                    if shift_held:
                        if event.key == pygame.K_TAB:
                            # SHIFT+TAB for unit cycling - return curses KEY_BTAB
                            return 353  # curses.KEY_BTAB
                        elif event.key == pygame.K_SLASH:
                            # SHIFT+/ = ? for help
                            return ord('?')
                        elif event.key in [pygame.K_l]:
                            # SHIFT+L for uppercase L 
                            return ord('L')
                    
                    # Map pygame keys to curses-like key codes
                    return self.key_map.get(event.key, -1)
            
            # If no events, continue polling
            self.clock.tick(60)
            
    def set_cursor(self, visible: bool) -> None:
        """Set cursor visibility (not applicable for pygame)."""
        pass
        
    def get_size(self) -> Tuple[int, int]:
        """Get the size of the rendering area as (height, width) in character grid units."""
        return (self.grid_height, self.grid_width)
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get the current terminal size (pygame window size in character units).
        
        Returns:
            Tuple of (height, width) in character grid units
        """
        return (self.grid_height, self.grid_width)
        
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 1, duration: float = 0.5) -> None:
        """Animate a projectile from start to end position using character grid."""
        start_y, start_x = start_pos
        end_y, end_x = end_pos
        
        # Calculate step counts
        steps = max(abs(end_y - start_y), abs(end_x - start_x), 10)
        
        for i in range(steps + 1):
            progress = i / steps if steps > 0 else 1
            
            # Interpolate position
            current_y = int(start_y + (end_y - start_y) * progress)
            current_x = int(start_x + (end_x - start_x) * progress)
            
            # Clear and redraw (simplified)
            self.clear_screen()
            
            # Draw projectile using tile-based positioning like draw_tile
            if tile_id:
                screen_x = current_x * self.tile_width  # Apply tile spacing
                screen_y = current_y + self.ui_offset_y  # Apply UI offset
                self.draw_char(screen_y, screen_x, tile_id[0], color_id)
            
            self.refresh()
            sleep_with_animation_speed(duration / steps)
            
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """Flash a tile with different characters and colors in sequence."""
        for tile_id, color_id, duration in zip(tile_ids, color_ids, durations):
            if tile_id:
                screen_x = x * self.tile_width  # Apply tile spacing
                screen_y = y + self.ui_offset_y  # Apply UI offset
                self.draw_char(screen_y, screen_x, tile_id[0], color_id)
            self.refresh()
            sleep_with_animation_speed(duration)
            
    def animate_attack_sequence(self, y: int, x: int, sequence: List[str], 
                              color_id: int = 1, duration: float = 0.5) -> None:
        """Animate an attack sequence at the specified position using character grid."""
        frame_duration = duration / len(sequence) if sequence else 0
        
        for frame in sequence:
            if frame:
                screen_x = x * self.tile_width  # Apply tile spacing
                screen_y = y + self.ui_offset_y  # Apply UI offset
                self.draw_char(screen_y, screen_x, frame[0], color_id)
            self.refresh()
            sleep_with_animation_speed(frame_duration)
            
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

            # Draw the current frame at the current position with tile spacing
            if frame:
                screen_x = x * self.tile_width  # Apply tile spacing
                screen_y = y + self.ui_offset_y  # Apply UI offset
                self.draw_char(screen_y, screen_x, frame[0], color_id)
            
            self.refresh()
            sleep_with_animation_speed(step_duration)