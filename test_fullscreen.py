#!/usr/bin/env python3
"""
Test script for fullscreen mode
Tests that fullscreen setting can be toggled and persisted.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.utils.config import ConfigManager

def test_fullscreen_toggle():
    """Test toggling fullscreen in config."""
    config = ConfigManager()

    # Save original state
    original_fullscreen = config.get('fullscreen', False)
    print(f"Original fullscreen setting: {original_fullscreen}")

    # Test toggling on
    config.set('fullscreen', True)
    config.save_config()

    # Reload config to verify persistence
    config2 = ConfigManager()
    assert config2.get('fullscreen') == True, "Fullscreen should be True after setting"
    print("✓ Fullscreen ON persisted correctly")

    # Test toggling off
    config2.set('fullscreen', False)
    config2.save_config()

    # Reload again
    config3 = ConfigManager()
    assert config3.get('fullscreen') == False, "Fullscreen should be False after toggling"
    print("✓ Fullscreen OFF persisted correctly")

    # Test with different resolutions
    resolutions = [(1280, 720), (1920, 1080), (2560, 1440)]

    for width, height in resolutions:
        config3.set('window_width', width)
        config3.set('window_height', height)
        config3.set('fullscreen', True)
        config3.save_config()

        # Verify all settings persist together
        config4 = ConfigManager()
        assert config4.get('window_width') == width
        assert config4.get('window_height') == height
        assert config4.get('fullscreen') == True
        print(f"✓ Fullscreen with {width}x{height} persisted correctly")

    # Restore original state
    config.set('fullscreen', original_fullscreen)
    config.set('window_width', 1480)
    config.set('window_height', 800)
    config.save_config()

    print(f"\nRestored original settings: fullscreen={original_fullscreen}")
    print("\n✅ All fullscreen tests passed!")

def test_pygame_fullscreen():
    """Test pygame fullscreen mode creation."""
    import pygame

    pygame.init()

    try:
        # Test windowed mode
        screen = pygame.display.set_mode((800, 600))
        assert screen is not None, "Failed to create windowed display"
        print("✓ Windowed mode works")

        # Test fullscreen mode
        screen = pygame.display.set_mode((800, 600), pygame.FULLSCREEN)
        assert screen is not None, "Failed to create fullscreen display"
        print("✓ Fullscreen mode works")

        # Back to windowed
        screen = pygame.display.set_mode((800, 600))
        print("✓ Can switch back to windowed")

        print("\n✅ Pygame fullscreen tests passed!")

    finally:
        pygame.quit()

if __name__ == "__main__":
    print("Testing Fullscreen Mode for Boneglaive")
    print("=" * 50)

    print("\n1. Testing Config Persistence:")
    print("-" * 30)
    test_fullscreen_toggle()

    print("\n2. Testing Pygame Fullscreen:")
    print("-" * 30)
    test_pygame_fullscreen()

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! ✅")
    print("\nTo use fullscreen in game:")
    print("1. Run: python run_graphical.py")
    print("2. Go to Settings → Display Settings")
    print("3. Toggle 'Fullscreen: On/Off'")
    print("4. Click 'Apply Changes' and restart")
    print("5. Or press F11 during gameplay to toggle instantly")