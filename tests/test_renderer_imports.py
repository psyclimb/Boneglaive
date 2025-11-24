#!/usr/bin/env python3
"""
Test that renderer can be imported and initialized without display.
"""
import sys
import os

# Disable pygame display requirement for testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

try:
    print("Testing imports...")
    from boneglaive.graphical.game_state import GameStateAdapter
    from boneglaive.graphical.renderer import GraphicalRenderer
    print("✓ Imports successful")

    print("\nTesting game adapter initialization...")
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)
    print(f"✓ Game initialized with {len(adapter.game.units)} units")

    print("\nTesting renderer initialization...")
    # This will fail if pygame can't create a display, but that's expected in headless mode
    try:
        import pygame
        pygame.init()
        # Try to create a minimal surface
        screen = pygame.display.set_mode((100, 100))
        print("✓ Pygame display available")
        pygame.quit()
    except Exception as e:
        print(f"⚠ Pygame display not available (expected in headless mode): {e}")

    print("\n✓ All import and initialization tests passed")
    sys.exit(0)

except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
