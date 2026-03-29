#!/usr/bin/env python3
"""
Launch script for Boneglaive Graphical Version

Usage:
    python run_graphical.py                # Run with menu
    python run_graphical.py --skip-menu    # Skip menu, start game directly
"""
import sys
import os
import argparse

# Ensure we can import boneglaive modules
from pathlib import Path

# Change to script directory so relative paths work from anywhere
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

sys.path.insert(0, str(script_dir))

from boneglaive.graphical.ui import MenuManager
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.utils.config import ConfigManager


def check_cairo():
    """Verify cairosvg is working. Show a clear error dialog and exit if not."""
    try:
        import cairosvg
        from io import BytesIO
        # Render a minimal SVG to confirm Cairo native libs are loaded
        cairosvg.svg2png(bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', output_width=1, output_height=1)
    except Exception as e:
        import pygame
        import traceback
        pygame.init()
        screen = pygame.display.set_mode((640, 300))
        pygame.display.set_caption("Boneglaive — Missing Dependency")
        font_large = pygame.font.SysFont("Arial", 22, bold=True)
        font_small = pygame.font.SysFont("Arial", 16)
        error_lines = [
            "Boneglaive could not load the Cairo graphics library.",
            "",
            "The game requires Cairo to render its visuals.",
            "Please reinstall the game or contact support.",
            "",
            f"Error: {str(e)[:80]}",
            "",
            "Press any key or close this window to exit.",
        ]
        running = True
        while running:
            screen.fill((20, 20, 30))
            y = 40
            for i, line in enumerate(error_lines):
                font = font_large if i == 0 else font_small
                color = (220, 80, 80) if i == 0 else (200, 200, 200)
                surf = font.render(line, True, color)
                screen.blit(surf, (40, y))
                y += font.get_height() + 6
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN):
                    running = False
        pygame.quit()
        sys.exit(1)


def run_game():
    """Run the game after menu configuration."""
    config = ConfigManager()

    # Get selected map from config
    selected_map = config.get('selected_map', 'edgecase')

    # Initialize DLC system before creating game
    from boneglaive.game.dlc_manager import initialize_dlc_system
    dlc_count = initialize_dlc_system()

    # Create game state adapter
    adapter = GameStateAdapter()

    # Create renderer first (needed for AI animations)
    print("Initializing Boneglaive Graphical Renderer...")
    renderer = GraphicalRenderer(adapter)

    # Create UI adapter for animations
    from boneglaive.graphical.ui_adapter import GraphicalUIAdapter
    ui_adapter = GraphicalUIAdapter(renderer)

    # Get network mode from config
    from boneglaive.utils.config import NetworkMode
    network_mode = config.get('network_mode', NetworkMode.VS_AI.value)

    # Initialize game with selected configuration
    # skip_setup=False means game starts in setup phase
    adapter.initialize_game(skip_setup=False, map_name=selected_map, network_mode=network_mode, ui_adapter=ui_adapter)

    # Set up terrain change callback so renderer marks tiles dirty when terrain changes
    if adapter.game and adapter.game.map:
        adapter.game.map.terrain_change_callback = renderer.mark_tile_dirty
        print("Terrain change callback registered for dynamic terrain updates")

    # Set multiplayer mode based on config
    if network_mode == NetworkMode.LOCAL_MULTIPLAYER.value:
        adapter.game.local_multiplayer = True
    else:
        adapter.game.local_multiplayer = False

    # Set UI reference on game for animations
    adapter.game.set_ui_reference(ui_adapter)

    # Sync units from game
    print("Syncing units from game...")
    renderer.sync_units_from_game()

    # Add welcome messages to combat log
    renderer.combat_log.add_message("Welcome to Boneglaive!", "system")
    renderer.combat_log.add_message(f"Player {adapter.game.current_player}'s turn", "system")

    print("\n" + "="*60)
    print("Boneglaive Graphical Version")
    print("="*60)
    print("Game starting...")
    print("="*60 + "\n")

    # Run game loop
    renderer.run()

    print("Game ended.")

    # Check if we should return to menu
    if hasattr(renderer, 'return_to_menu') and renderer.return_to_menu:
        print("Returning to main menu...")
        return "main_menu"
    else:
        # User closed window or quit
        return None


def main():
    parser = argparse.ArgumentParser(description="Boneglaive Graphical Version")
    parser.add_argument(
        "--skip-menu",
        action="store_true",
        help="Skip menu and start game directly"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    args = parser.parse_args()

    import pygame
    pygame.init()
    check_cairo()

    if args.skip_menu:
        # Skip menu, go directly to game
        print("Skipping menu...")
        run_game()
    else:
        # Show menu first
        while True:
            print("Starting Boneglaive Menu...")
            menu_manager = MenuManager()
            result = menu_manager.run()
            menu_manager.cleanup()

            if result and result[0] == "start_game":
                # Start the game
                game_result = run_game()

                # Check if we should return to menu
                if game_result != "main_menu":
                    break
            else:
                # User quit from menu
                print("Exiting Boneglaive. Goodbye!")
                break

        import pygame
        pygame.quit()


if __name__ == "__main__":
    main()
