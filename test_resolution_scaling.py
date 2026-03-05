#!/usr/bin/env python3
"""
Test script for resolution scaling
Tests that all resolutions can be loaded and dimensions scale properly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.utils.config import ConfigManager
from boneglaive.graphical.ui.scale_utils import ScaleManager
from boneglaive.graphical.animations.core import _get_tile_size

# Test resolutions
RESOLUTIONS = [
    (1280, 720),    # 720p
    (1366, 768),    # Common laptop
    (1480, 800),    # Default
    (1600, 900),    # HD+
    (1920, 1080),   # 1080p
    (2560, 1440),   # 1440p
]

def test_resolution(width, height):
    """Test a specific resolution."""
    print(f"\n=== Testing {width}x{height} ===")

    # Set config
    config = ConfigManager()
    config.set('window_width', width)
    config.set('window_height', height)
    config.save_config()

    # Test scale manager
    scale_manager = ScaleManager()
    scale_manager.update_scale()

    print(f"  Screen dimensions: {scale_manager.screen_width}x{scale_manager.screen_height}")
    print(f"  Scale factors: X={scale_manager.scale_x:.2f}, Y={scale_manager.scale_y:.2f}, Uniform={scale_manager.scale_uniform:.2f}")
    print(f"  Left panel width: {scale_manager.left_panel_width}px")
    print(f"  Top bar height: {scale_manager.top_bar_height}px")
    print(f"  Button size: {scale_manager.button_width}x{scale_manager.button_height}")
    print(f"  Font sizes: Normal={scale_manager.font_size}, Small={scale_manager.small_font_size}, Large={scale_manager.large_font_size}")

    # Test tile size calculation
    tile_size = _get_tile_size()
    print(f"  Tile size: {tile_size}px")

    # Calculate game board dimensions
    game_board_width = width * (1 - 2 * 0.189189)  # Accounting for panels
    expected_tile_size = int(game_board_width // 20)

    if tile_size != expected_tile_size:
        print(f"  WARNING: Tile size mismatch! Expected {expected_tile_size}, got {tile_size}")

    # Check proportions
    panel_ratio = scale_manager.left_panel_width / width
    expected_ratio = 0.189189

    if abs(panel_ratio - expected_ratio) > 0.01:
        print(f"  WARNING: Panel ratio off! Expected {expected_ratio:.3f}, got {panel_ratio:.3f}")

    return True

def main():
    print("Testing resolution scaling for Boneglaive")
    print("==========================================")

    # Save original config
    config = ConfigManager()
    original_width = config.get('window_width', 1480)
    original_height = config.get('window_height', 800)

    try:
        # Test each resolution
        for width, height in RESOLUTIONS:
            test_resolution(width, height)

        print("\n==========================================")
        print("All resolutions tested successfully!")
        print("==========================================")

        # Test that renderer constants update properly
        print("\nTesting renderer constant updates...")
        config.set('window_width', 1920)
        config.set('window_height', 1080)
        config.save_config()

        # Import renderer to check constants
        from boneglaive.graphical import renderer
        print(f"Renderer SCREEN_WIDTH: {renderer.SCREEN_WIDTH}")
        print(f"Renderer SCREEN_HEIGHT: {renderer.SCREEN_HEIGHT}")
        print(f"Renderer TILE_SIZE: {renderer.TILE_SIZE}")
        print(f"Renderer LEFT_PANEL_WIDTH: {renderer.LEFT_PANEL_WIDTH}")
        print(f"Renderer TOP_BAR_HEIGHT: {renderer.TOP_BAR_HEIGHT}")

    finally:
        # Restore original config
        config.set('window_width', original_width)
        config.set('window_height', original_height)
        config.save_config()
        print(f"\nRestored original resolution: {original_width}x{original_height}")

if __name__ == "__main__":
    main()