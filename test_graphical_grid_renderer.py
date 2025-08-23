#!/usr/bin/env python3
"""
Test script for the new graphical grid system tile-based ASCII renderer.
This demonstrates the cross-platform graphical ASCII rendering system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boneglaive'))

import pygame
from boneglaive.renderers.pygame_renderer import PygameRenderer
from boneglaive.utils.constants import UnitType

def test_renderer():
    """Test the enhanced PygameRenderer with character grid system."""
    print("Testing graphical grid system ASCII renderer...")
    
    # Initialize renderer
    renderer = PygameRenderer(800, 600)
    renderer.initialize()
    
    print(f"Grid size: {renderer.grid_width} x {renderer.grid_height} characters")
    print(f"Character cell size: {renderer.char_width} x {renderer.char_height} pixels")
    print(f"Font: {renderer.font.get_name() if hasattr(renderer.font, 'get_name') else 'Default'}")
    
    # Clear screen
    renderer.clear_screen()
    
    # Test character grid rendering
    renderer.draw_char(0, 0, "B", 7)  # Title
    renderer.draw_char(0, 1, "o", 7)
    renderer.draw_char(0, 2, "n", 7)
    renderer.draw_char(0, 3, "e", 7)
    renderer.draw_char(0, 4, "g", 7)
    renderer.draw_char(0, 5, "l", 7)
    renderer.draw_char(0, 6, "a", 7)
    renderer.draw_char(0, 7, "i", 7)
    renderer.draw_char(0, 8, "v", 7)
    renderer.draw_char(0, 9, "e", 7)
    
    # Test text rendering
    renderer.draw_text(2, 0, "Cross-Platform ASCII Test", 6)
    renderer.draw_text(3, 0, "Character Grid: Fixed Width", 2)
    
    # Test unit rendering
    renderer.draw_text(5, 0, "Unit Types:", 3)
    renderer.draw_unit_sprite(6, 2, UnitType.GLAIVEMAN, 1)
    renderer.draw_text(6, 4, "Glaiveman (Player 1)", 1)
    
    renderer.draw_unit_sprite(7, 2, UnitType.GRAYMAN, 2) 
    renderer.draw_text(7, 4, "Grayman (Player 2)", 4)
    
    # Test terrain tiles
    renderer.draw_text(9, 0, "Terrain:", 3)
    renderer.draw_tile(10, 2, "#", 8)  # Wall
    renderer.draw_text(10, 4, "Wall", 8)
    
    renderer.draw_tile(11, 2, ".", 7)  # Floor
    renderer.draw_text(11, 4, "Floor", 7)
    
    # Test UI elements
    renderer.draw_text(13, 0, "UI Elements:", 3)
    renderer.draw_ui_element(14, 2, 'cursor', 6)
    renderer.draw_text(14, 4, "Cursor", 6)
    
    renderer.draw_ui_element(15, 2, 'selected', 5)
    renderer.draw_text(15, 4, "Selection", 5)
    
    # Test effects
    renderer.draw_text(17, 0, "Effects:", 3)
    renderer.draw_effect_sprite(18, 2, '*', 1)
    renderer.draw_text(18, 4, "Explosion", 1)
    
    # Instructions
    renderer.draw_text(20, 0, "Press any key to test animation, ESC to quit", 7)
    
    # Refresh display
    renderer.refresh()
    
    # Simple event loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # Test animation
                    renderer.animate_attack_sequence(18, 6, ['*', '+', 'x', '.'], 1, 1.0)
        
        clock.tick(60)
    
    # Cleanup
    renderer.cleanup()
    print("Test completed successfully!")

if __name__ == "__main__":
    try:
        test_renderer()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()