#!/usr/bin/env python3
"""
Test script to verify unit status bar sprites are working.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
from boneglaive.graphical.game_state import GameStateAdapter
from boneglaive.graphical.ui.unit_status_bar import UnitStatusBar

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Unit Status Bar Sprite Test")

    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)

    # Create game adapter with default units
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True, map_name="hard_pressed")

    # Create unit status bar
    status_bar = UnitStatusBar(font, small_font)
    status_bar.update(adapter.game, None)

    print(f"Created status bar with {len(status_bar.unit_cards)} unit cards")

    # Check if sprites loaded
    sprites_loaded = 0
    for card in status_bar.unit_cards:
        if card.sprite_surface is not None:
            sprites_loaded += 1
            print(f"  ✓ Sprite loaded for {card.get_unit_symbol()}{card.get_greek_id()}")
        else:
            print(f"  ✗ No sprite for {card.get_unit_symbol()}{card.get_greek_id()}")

    print(f"\nSprites loaded: {sprites_loaded}/{len(status_bar.unit_cards)}")

    # Draw for 3 seconds
    clock = pygame.time.Clock()
    running = True
    start_time = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Exit after 3 seconds
        if pygame.time.get_ticks() - start_time > 3000:
            running = False

        screen.fill((40, 44, 52))

        # Draw title
        title = font.render("Unit Status Bar - Sprite Test", True, (255, 255, 255))
        screen.blit(title, (20, 20))

        # Draw status bar
        status_bar.draw(screen, 20, 60)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("\nTest complete!")

if __name__ == "__main__":
    main()
