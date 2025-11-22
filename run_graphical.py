#!/usr/bin/env python3
"""
Launch script for Boneglaive Graphical Version

Usage:
    python run_graphical.py          # Run with demo scene
    python run_graphical.py --game   # Run with actual game logic (TODO)
"""
import sys
import argparse

# Ensure we can import boneglaive modules
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from boneglaive.graphical.renderer import GraphicalRenderer
from boneglaive.graphical.game_state import GameStateAdapter


def main():
    parser = argparse.ArgumentParser(description="Boneglaive Graphical Version")
    parser.add_argument(
        "--game",
        action="store_true",
        help="Run with actual game logic (not yet implemented)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    args = parser.parse_args()

    # Create game state adapter
    adapter = GameStateAdapter()

    if args.game:
        # Use full game logic (not yet fully implemented)
        print("Initializing game with full logic...")
        adapter.initialize_game(skip_setup=False)  # Will use setup phase
        mode = "Game Mode (Setup Phase)"
    else:
        # Use quick start with default units
        print("Initializing game with default units...")
        adapter.initialize_game(skip_setup=True)  # Default units
        mode = "Quick Start Mode"

    print(f"Game created with {len(adapter.game.units)} units")

    # Create renderer
    print("Initializing Boneglaive Graphical Renderer...")
    renderer = GraphicalRenderer(adapter)

    # Sync units from game
    print("Syncing units from game...")
    renderer.sync_units_from_game()
    print(f"Created {len(renderer.units)} visual units")

    print("\n" + "="*60)
    print(f"Boneglaive Graphical Version - {mode}")
    print("="*60)
    print("Controls:")
    print("  ESC        - Quit")
    print("  SPACE      - Pause/Unpause")
    print("  Left Click - Select unit / Click tile")
    print("  Right Click- Cancel selection")
    print("\nNOTE: Game logic connected! Units from real game.")
    print("="*60 + "\n")

    # Run game loop
    print("Starting renderer...")
    renderer.run()

    print("Renderer closed. Goodbye!")


if __name__ == "__main__":
    main()
