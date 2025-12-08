#!/usr/bin/env python3
"""
Launch script for Boneglaive Graphical Version

Usage:
    python run_graphical.py                # Run with menu
    python run_graphical.py --skip-menu    # Skip menu, start game directly
"""
import sys
import argparse

# Ensure we can import boneglaive modules
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.ui import MenuManager
from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.utils.config import ConfigManager


def run_game():
    """Run the game after menu configuration."""
    config = ConfigManager()

    # Get selected map from config
    selected_map = config.get('selected_map', 'edgecase')

    # Create game state adapter
    adapter = GameStateAdapter()

    # Initialize game with selected configuration
    print(f"Initializing game on map: {selected_map}...")
    adapter.initialize_game(skip_setup=True, map_name=selected_map)
    print(f"Game created with {len(adapter.game.units)} units")

    # Create renderer
    print("Initializing Boneglaive Graphical Renderer...")
    renderer = GraphicalRenderer(adapter)

    # Create UI adapter and set it on the game for animations
    from boneglaive.graphical.ui_adapter import GraphicalUIAdapter
    ui_adapter = GraphicalUIAdapter(renderer)
    adapter.game.set_ui_reference(ui_adapter)

    # Sync units from game
    print("Syncing units from game...")
    renderer.sync_units_from_game()
    print(f"Created {len(renderer.units)} visual units")

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
    return "main_menu"  # Could return to menu


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


if __name__ == "__main__":
    main()
