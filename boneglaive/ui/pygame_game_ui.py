#!/usr/bin/env python3
"""
Pygame-based game UI implementation.
Simplified game UI for pygame that replicates core functionality.
"""

import pygame
from typing import Optional, Tuple
from boneglaive.renderers.pygame_renderer import PygameRenderer
from boneglaive.utils.debug import logger
from boneglaive.game.engine import Game
from boneglaive.game.multiplayer_manager import MultiplayerManager
from boneglaive.utils.config import ConfigManager
from boneglaive.utils.constants import HEIGHT, WIDTH

class PygameGameUI:
    """Simplified pygame-based game UI."""
    
    def __init__(self, width: int = 800, height: int = 600):
        """Initialize the pygame game UI."""
        # Create pygame renderer
        self.renderer = PygameRenderer(width, height)
        self.renderer.initialize()
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Create game instance
        selected_map = self.config_manager.get('selected_map', 'lime_foyer')
        self.game = Game(skip_setup=False, map_name=selected_map)
        
        # Set up multiplayer manager for AI support
        self.multiplayer = MultiplayerManager(self.game)
        
        # Set UI reference in game engine for AI animations
        self.game.set_ui_reference(self)
        
        # Simple cursor position
        self.cursor_y = HEIGHT // 2
        self.cursor_x = WIDTH // 2
        
        # Selected unit
        self.selected_unit = None
        
        logger.info(f"PygameGameUI initialized with map: {selected_map}")
    
    def is_vs_ai_mode(self) -> bool:
        """Check if currently in VS AI mode."""
        return self.multiplayer.is_vs_ai()
    
    def get_current_player_info(self) -> str:
        """Get display string for current player."""
        return self.game.get_player_name(self.game.current_player)
        
    def draw_board(self):
        """Draw the game board with pygame."""
        self.renderer.clear_screen()
        
        # Draw map terrain using sprite-based rendering
        game_map = self.game.map
        for y in range(game_map.height):
            for x in range(game_map.width):
                terrain = game_map.get_terrain_at(y, x)
                
                # Map terrain names to asset keys
                terrain_mapping = {
                    'EMPTY': 'empty',
                    'WALL': 'wall',
                    'LIMESTONE': 'limestone',
                    'PILLAR': 'pillar',
                    'MARROW_WALL': 'marrow_wall',
                    'FURNITURE': 'furniture',
                    'RAIL': 'rail',
                    'TIFFANY_LAMP': 'tiffany_lamp',
                    'STAINED_STONE': 'stained_stone',
                    'EASEL': 'easel',
                    'SCULPTURE': 'sculpture',
                    'BENCH': 'bench',
                    'PODIUM': 'podium',
                    'VASE': 'vase',
                    'HYDRAULIC_PRESS': 'hydraulic_press',
                    'WORKBENCH': 'workbench',
                    'COUCH': 'couch',
                    'TOOLBOX': 'toolbox',
                    'COT': 'cot',
                    'CONVEYOR': 'conveyor',
                    'CONCRETE_FLOOR': 'concrete_floor',
                    'CANYON_FLOOR': 'canyon_floor'
                }
                
                terrain_key = terrain_mapping.get(terrain.name, terrain.name.lower())
                self.renderer.draw_tile(y, x, terrain_key, 8)
        
        # Draw units using sprite-based rendering
        for unit in self.game.units:
            if unit.is_alive():
                self.renderer.draw_unit_sprite(unit.y, unit.x, unit.unit_type, unit.player)
        
        # Draw selection highlight for selected unit
        if self.selected_unit and self.selected_unit.is_alive():
            self.renderer.draw_ui_element(self.selected_unit.y, self.selected_unit.x, 'selected', 3)
        
        # Draw cursor
        self.renderer.draw_ui_element(self.cursor_y, self.cursor_x, 'cursor', 6)
        
        # Draw simple UI info
        player_info = self.get_current_player_info()
        self.renderer.draw_text(0, 0, f"Turn: {self.game.turn} {player_info}", 7)
        
        # Show AI thinking indicator
        if self.is_vs_ai_mode() and self.game.current_player == 2:
            self.renderer.draw_text(1, 0, "AI is thinking...", 6)
        
        if self.selected_unit:
            y_offset = 2 if (self.is_vs_ai_mode() and self.game.current_player == 2) else 1
            self.renderer.draw_text(y_offset, 0, f"Selected: {self.selected_unit.get_display_name()}", 3)
            self.renderer.draw_text(y_offset + 1, 0, f"HP: {self.selected_unit.hp}/{self.selected_unit.max_hp}", 7)
        
        self.renderer.refresh()
            
    def handle_input(self, key: int) -> bool:
        """Handle user input. Returns False to quit."""
        # Movement keys
        if key == ord('h'):  # Left
            self.cursor_x = max(0, self.cursor_x - 1)
        elif key == ord('l'):  # Right
            self.cursor_x = min(WIDTH - 1, self.cursor_x + 1)
        elif key == ord('k'):  # Up
            self.cursor_y = max(0, self.cursor_y - 1)
        elif key == ord('j'):  # Down
            self.cursor_y = min(HEIGHT - 1, self.cursor_y + 1)
        elif key == 10 or key == ord(' '):  # Enter or Space - select
            unit = self.game.get_unit_at(self.cursor_y, self.cursor_x)
            if unit and unit.is_alive():
                self.selected_unit = unit
                logger.info(f"Selected unit: {unit.get_display_name()}")
        elif key == ord('q') or key == 27:  # Quit
            return False
        elif key == ord('t'):  # End turn
            if self.game.setup_phase:
                # Simple setup phase handling
                self.game.check_setup_completion()
            else:
                # Use multiplayer manager for proper AI integration
                self.multiplayer.end_turn()
                logger.info(f"Turn ended, now player {self.game.current_player}")
        
        # Redraw after any input
        self.draw_board()
        return True
        
    def run_game_loop(self) -> None:
        """Run the main pygame game loop."""
        logger.info("Starting pygame game loop")
        
        # Draw initial board
        self.draw_board()
        
        running = True
        while running and self.renderer.running:
            # Get input from pygame
            key = self.renderer.get_input()
            
            if key == -1:  # No input
                continue
                
            # Handle input
            running = self.handle_input(key)
            
        logger.info("Pygame game loop ended")
        
    def cleanup(self):
        """Clean up pygame resources."""
        if self.renderer:
            self.renderer.cleanup()
            
class PygameMenuUI:
    """Simple pygame-based menu UI."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.renderer = PygameRenderer(width, height)
        self.renderer.initialize()
        self.selected_option = 0
        self.menu_options = [
            "VS AI",
            "Settings", 
            "Quit"
        ]
        
    def draw_menu(self):
        """Draw the main menu."""
        self.renderer.clear_screen()
        
        # Title
        self.renderer.draw_text(5, 10, "BONEGLAIVE2", 6, 1)  # Cyan, bold
        self.renderer.draw_text(6, 10, "Tactical Combat Game", 7)
        
        # Menu options
        for i, option in enumerate(self.menu_options):
            color = 3 if i == self.selected_option else 7  # Yellow if selected, white otherwise
            self.renderer.draw_text(10 + i * 2, 10, f"{i + 1}. {option}", color)
            
        # Instructions
        self.renderer.draw_text(18, 10, "Use UP/DOWN arrows to navigate, ENTER to select", 8)
        
        self.renderer.refresh()
        
    def run(self) -> Optional[Tuple[str, None]]:
        """Run the menu and return the selected option."""
        logger.info("Starting pygame menu")
        
        while self.renderer.running:
            self.draw_menu()
            
            key = self.renderer.get_input()
            
            if key == ord('k'):  # Up arrow (mapped from pygame)
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif key == ord('j'):  # Down arrow (mapped from pygame)
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif key == 10:  # Enter
                if self.selected_option == 0:  # VS AI
                    return ("vs_ai", None)
                elif self.selected_option == 1:  # Settings
                    # TODO: Implement settings menu
                    continue
                elif self.selected_option == 2:  # Quit
                    return None
            elif key == ord('q') or key == 27:  # Q or Escape
                return None
                
        return None
    
    # Methods needed for AI animations and UI integration
    def animate_projectile(self, start_pos, end_pos, tile_id, color_id=1, duration=0.5):
        """Animate a projectile for AI actions."""
        self.renderer.animate_projectile(start_pos, end_pos, tile_id, color_id, duration)
        
    def flash_tile(self, y, x, tile_ids, color_ids, durations):
        """Flash a tile for AI actions."""
        self.renderer.flash_tile(y, x, tile_ids, color_ids, durations)
        
    def animate_attack_sequence(self, y, x, sequence, color_id=1, duration=0.5):
        """Animate an attack sequence for AI actions."""
        self.renderer.animate_attack_sequence(y, x, sequence, color_id, duration)
        
    def cleanup(self):
        """Clean up pygame resources."""
        if self.renderer:
            self.renderer.cleanup()