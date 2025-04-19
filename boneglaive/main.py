#!/usr/bin/env python3
"""
Main entry point for the game.
Handles argument parsing and starts the game.
"""
import curses
import argparse
import sys
from typing import Optional, Tuple

from boneglaive.ui.game_ui import GameUI
from boneglaive.ui.menu_ui import MenuUI
from boneglaive.utils.debug import debug_config, logger, LogLevel
from boneglaive.utils.config import ConfigManager, NetworkMode, DisplayMode

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Boneglaive - Tactical Combat Game")
    
    # Game mode options
    mode_group = parser.add_argument_group('Game Mode Options')
    mode_group.add_argument('--skip-menu', action='store_true', help='Skip menu and start game directly')
    mode_group.add_argument('--mode', choices=['single', 'local', 'lan_host', 'lan_client'],
                        default='single', help='Game mode (single, local, lan_host, lan_client)')
    mode_group.add_argument('--server', default='127.0.0.1', help='Server IP address for LAN mode')
    mode_group.add_argument('--port', type=int, default=7777, help='Server port for LAN mode')
    
    # Display options
    display_group = parser.add_argument_group('Display Options')
    display_group.add_argument('--display', choices=['text', 'graphical'],
                            default='text', help='Display mode (text or graphical)')
    
    # Debug options
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug', action='store_true', help='Enable debug mode')
    debug_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                             default='INFO', help='Set logging level')
    debug_group.add_argument('--log-file', action='store_true', help='Enable logging to file')
    debug_group.add_argument('--perf', action='store_true', help='Enable performance tracking')
    debug_group.add_argument('--overlay', action='store_true', help='Show debug overlay')
    
    return parser.parse_args()

def configure_settings(args):
    """Configure game settings based on command line arguments"""
    # Create or load configuration
    config = ConfigManager()
    
    # Network mode
    if args.mode:
        network_mode_map = {
            'single': NetworkMode.SINGLE_PLAYER.value,
            'local': NetworkMode.LOCAL_MULTIPLAYER.value,
            'lan_host': NetworkMode.LAN_HOST.value,
            'lan_client': NetworkMode.LAN_CLIENT.value
        }
        config.set('network_mode', network_mode_map[args.mode])
    
    # Server settings
    if args.mode in ['lan_host', 'lan_client']:
        config.set('server_ip', args.server)
        config.set('server_port', args.port)
    
    # Display mode
    if args.display:
        display_mode_map = {
            'text': DisplayMode.TEXT.value,
            'graphical': DisplayMode.GRAPHICAL.value
        }
        config.set('display_mode', display_mode_map[args.display])
    
    # Save configuration
    config.save_config()
    
    # Configure debug settings
    if args.debug:
        debug_config.enabled = True
    
    # Set log level
    log_level_map = {
        'DEBUG': LogLevel.DEBUG,
        'INFO': LogLevel.INFO,
        'WARNING': LogLevel.WARNING,
        'ERROR': LogLevel.ERROR,
        'CRITICAL': LogLevel.CRITICAL
    }
    debug_config.log_level = log_level_map[args.log_level]
    
    # Other debug settings
    debug_config.log_to_file = args.log_file
    debug_config.perf_tracking = args.perf
    debug_config.show_debug_overlay = args.overlay

def run_menu(stdscr) -> Optional[Tuple[str, None]]:
    """Run the menu system."""
    menu_ui = MenuUI(stdscr)
    return menu_ui.run()

def run_game(stdscr) -> None:
    """Run the game."""
    game_ui = GameUI(stdscr)
    
    running = True
    while running:
        game_ui.draw_board()
        key = stdscr.getch()
        running = game_ui.handle_input(key)

def main(stdscr):
    """Main function that coordinates menu and game."""
    # Setup
    curses.curs_set(0)  # Hide cursor
    stdscr.timeout(-1)  # No timeout for getch
    
    # Get arguments
    args = parse_args()
    
    # Configure settings
    configure_settings(args)
    
    # Initialize logging
    logger.info("Starting Boneglaive")
    
    # Run menu or skip to game
    if args.skip_menu:
        logger.info("Skipping menu")
        run_game(stdscr)
    else:
        # Run menu
        logger.info("Starting menu")
        menu_result = run_menu(stdscr)
        
        # Process menu result
        if menu_result and menu_result[0] == "start_game":
            logger.info("Starting game from menu")
            run_game(stdscr)
        else:
            logger.info("Quitting from menu")

if __name__ == "__main__":
    # Start the application
    curses.wrapper(main)