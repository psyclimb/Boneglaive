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
        self.tile_size = 32  # Size of each tile in pixels
        self.colors = {}
        self.running = True
        
        # Asset management
        self.config_manager = ConfigManager()
        self.asset_manager = AssetManager(self.config_manager)
        
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
        
        # Initialize font
        self.font = pygame.font.Font(None, 24)
        
        # Set up colors
        self.setup_colors()
        
        # Set up key mapping after pygame init
        self.setup_key_mapping()
        
        # Clear screen initially
        self.clear_screen()
        
    def setup_key_mapping(self):
        """Set up key mapping from pygame to curses-like key codes."""
        self.key_map = {
            pygame.K_UP: ord('k'),
            pygame.K_DOWN: ord('j'), 
            pygame.K_LEFT: ord('h'),
            pygame.K_RIGHT: ord('l'),
            pygame.K_RETURN: 10,  # Enter
            pygame.K_SPACE: ord(' '),
            pygame.K_ESCAPE: 27,  # Escape
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
        """Draw text at the specified position."""
        color = self.colors.get(color_id, self.colors[7])
        
        # Handle attributes (simplified)
        font = self.font
        if attributes:  # Any attribute makes it bold for now
            font = pygame.font.Font(None, 26)
            
        text_surface = font.render(text, True, color)
        
        # Convert grid coordinates to pixel coordinates
        pixel_x = x * 8  # Approximate character width
        pixel_y = y * 20  # Approximate character height
        
        self.screen.blit(text_surface, (pixel_x, pixel_y))
        
    def draw_tile(self, y: int, x: int, tile_id: str, color_id: int = 7) -> None:
        """Draw a tile at the specified position using sprites when available."""
        color = self.colors.get(color_id, self.colors[7])
        
        # Convert grid coordinates to pixel coordinates  
        pixel_x = x * self.tile_size
        pixel_y = y * self.tile_size
        
        rect = pygame.Rect(pixel_x, pixel_y, self.tile_size, self.tile_size)
        
        # Try to load terrain sprite first (for map tiles)
        sprite = self.asset_manager.get_sprite('terrain', tile_id)
        
        if sprite:
            # Scale sprite to tile size if needed
            if sprite.get_size() != (self.tile_size, self.tile_size):
                sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
            self.screen.blit(sprite, (pixel_x, pixel_y))
        else:
            # Fallback to character rendering for missing sprites
            pygame.draw.rect(self.screen, (50, 50, 50), rect)
            pygame.draw.rect(self.screen, color, rect, 2)
            
            if tile_id and len(tile_id) > 0:
                text_surface = self.font.render(tile_id[0], True, color)
                text_rect = text_surface.get_rect()
                text_rect.center = rect.center
                self.screen.blit(text_surface, text_rect)
    
    def draw_unit_sprite(self, y: int, x: int, unit_type: UnitType, player: int = 1) -> None:
        """Draw a unit sprite at the specified position."""
        pixel_x = x * self.tile_size
        pixel_y = y * self.tile_size
        
        # Try to load unit sprite
        sprite = self.asset_manager.get_sprite('unit', unit_type)
        
        if sprite:
            # Scale sprite to tile size if needed
            if sprite.get_size() != (self.tile_size, self.tile_size):
                sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
            
            # Apply team coloring if needed (simple color overlay)
            if player == 2:
                # Create a blue tint for player 2
                tint_surface = pygame.Surface((self.tile_size, self.tile_size))
                tint_surface.fill((0, 0, 100))
                tint_surface.set_alpha(50)
                sprite = sprite.copy()
                sprite.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_ADD)
            
            self.screen.blit(sprite, (pixel_x, pixel_y))
        else:
            # Fallback to generated placeholder sprite
            placeholder = self.asset_manager.create_placeholder_sprite(unit_type, (self.tile_size, self.tile_size))
            if placeholder:
                # Apply team coloring for placeholder
                if player == 2:
                    tint_surface = pygame.Surface((self.tile_size, self.tile_size))
                    tint_surface.fill((0, 0, 100))
                    tint_surface.set_alpha(50)
                    placeholder.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_ADD)
                
                self.screen.blit(placeholder, (pixel_x, pixel_y))
            else:
                # Final fallback to character rendering
                color = (255, 0, 0) if player == 1 else (0, 0, 255)
                unit_char = self.asset_manager.get_unit_tile(unit_type)
                text_surface = self.font.render(unit_char, True, color)
                text_rect = text_surface.get_rect()
                text_rect.center = (pixel_x + self.tile_size//2, pixel_y + self.tile_size//2)
                self.screen.blit(text_surface, text_rect)
    
    def draw_ui_element(self, y: int, x: int, element_type: str, color_id: int = 6) -> None:
        """Draw a UI element (cursor, selection, etc.) at the specified position."""
        pixel_x = x * self.tile_size
        pixel_y = y * self.tile_size
        
        # Try to load UI sprite
        sprite = self.asset_manager.get_sprite('ui', element_type)
        
        if sprite:
            # Scale sprite to tile size if needed
            if sprite.get_size() != (self.tile_size, self.tile_size):
                sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
            self.screen.blit(sprite, (pixel_x, pixel_y))
        else:
            # Fallback to simple colored overlay
            color = self.colors.get(color_id, self.colors[6])
            if element_type == 'cursor':
                # Draw cursor as hollow square
                pygame.draw.rect(self.screen, color, (pixel_x, pixel_y, self.tile_size, self.tile_size), 3)
            elif element_type == 'selected':
                # Draw selection as filled translucent overlay
                overlay = pygame.Surface((self.tile_size, self.tile_size))
                overlay.fill(color)
                overlay.set_alpha(100)
                self.screen.blit(overlay, (pixel_x, pixel_y))
            else:
                # Default to character rendering
                ui_char = self.asset_manager.get_ui_tile(element_type)
                text_surface = self.font.render(ui_char, True, color)
                text_rect = text_surface.get_rect()
                text_rect.center = (pixel_x + self.tile_size//2, pixel_y + self.tile_size//2)
                self.screen.blit(text_surface, text_rect)
    
    def draw_effect_sprite(self, y: int, x: int, effect_type: str, color_id: int = 1) -> None:
        """Draw an effect sprite at the specified position."""
        pixel_x = x * self.tile_size
        pixel_y = y * self.tile_size
        
        # Try to load effect sprite
        sprite = self.asset_manager.get_sprite('effect', effect_type)
        
        if sprite:
            # Scale sprite to tile size if needed
            if sprite.get_size() != (self.tile_size, self.tile_size):
                sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
            self.screen.blit(sprite, (pixel_x, pixel_y))
        else:
            # Fallback to character rendering
            color = self.colors.get(color_id, self.colors[1])
            effect_char = self.asset_manager.get_effect_tile(effect_type)
            text_surface = self.font.render(effect_char, True, color)
            text_rect = text_surface.get_rect()
            text_rect.center = (pixel_x + self.tile_size//2, pixel_y + self.tile_size//2)
            self.screen.blit(text_surface, text_rect)
            
    def get_input(self) -> int:
        """Get user input as a key code."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return ord('q')  # Quit
                elif event.type == pygame.KEYDOWN:
                    # Map pygame keys to curses-like key codes
                    return self.key_map.get(event.key, -1)
            
            # If no events, continue polling
            self.clock.tick(60)
            
    def set_cursor(self, visible: bool) -> None:
        """Set cursor visibility (not applicable for pygame)."""
        pass
        
    def get_size(self) -> Tuple[int, int]:
        """Get the size of the rendering area as (height, width) in grid units."""
        # Calculate grid size based on tile size
        grid_height = self.height // self.tile_size
        grid_width = self.width // self.tile_size
        return (grid_height, grid_width)
        
    def animate_projectile(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                          tile_id: str, color_id: int = 1, duration: float = 0.5) -> None:
        """Animate a projectile from start to end position."""
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
            
            # Draw projectile
            self.draw_tile(current_y, current_x, tile_id, color_id)
            
            self.refresh()
            sleep_with_animation_speed(duration / steps)
            
    def flash_tile(self, y: int, x: int, tile_ids: List[str], color_ids: List[int], 
                  durations: List[float]) -> None:
        """Flash a tile with different characters and colors in sequence."""
        for tile_id, color_id, duration in zip(tile_ids, color_ids, durations):
            self.draw_tile(y, x, tile_id, color_id)
            self.refresh()
            sleep_with_animation_speed(duration)
            
    def animate_attack_sequence(self, y: int, x: int, sequence: List[str], 
                              color_id: int = 1, duration: float = 0.5) -> None:
        """Animate an attack sequence at the specified position."""
        frame_duration = duration / len(sequence) if sequence else 0
        
        for frame in sequence:
            self.draw_tile(y, x, frame, color_id)
            self.refresh()
            sleep_with_animation_speed(frame_duration)