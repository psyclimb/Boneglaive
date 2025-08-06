#!/usr/bin/env python3
"""
Main entry point for the game.
Handles argument parsing and starts the game.
"""
import curses
import argparse
import os
import sys
import logging
from typing import Optional, Tuple

from boneglaive.ui.game_ui import GameUI
from boneglaive.ui.menu_ui import MenuUI
from boneglaive.utils.debug import debug_config, logger, LogLevel
from boneglaive.utils.config import ConfigManager, NetworkMode, DisplayMode
from boneglaive.utils.platform_compat import setup_terminal_optimizations, get_platform_name

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Boneglaive - Tactical Combat Game")
    
    # Game mode options
    mode_group = parser.add_argument_group('Game Mode Options')
    mode_group.add_argument('--skip-menu', action='store_true', help='Skip menu and start game directly')
    mode_group.add_argument('--mode', choices=['single', 'local', 'lan_host', 'lan_client', 'vs_ai'],
                        default='vs_ai', help='Game mode (single, local, lan_host, lan_client, vs_ai)')
    mode_group.add_argument('--server', default='127.0.0.1', help='Server IP address for LAN mode')
    mode_group.add_argument('--port', type=int, default=7777, help='Server port for LAN mode')
    mode_group.add_argument('--ai-difficulty', choices=['easy', 'medium', 'hard'],
                        default='medium', help='AI difficulty level when playing against AI')
    
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
            'lan_client': NetworkMode.LAN_CLIENT.value,
            'vs_ai': NetworkMode.VS_AI.value
        }
        config.set('network_mode', network_mode_map[args.mode])
    
    # Server settings
    if args.mode in ['lan_host', 'lan_client']:
        config.set('server_ip', args.server)
        config.set('server_port', args.port)
        
    # AI settings
    if args.mode == 'vs_ai':
        config.set('ai_difficulty', args.ai_difficulty)
        logger.info(f"Setting AI difficulty to {args.ai_difficulty}")
    
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
    # Create the menu UI (the constructor will handle initial drawing)
    menu_ui = MenuUI(stdscr)
    
    # Run the menu loop
    return menu_ui.run()

def run_game(stdscr) -> None:
    """Run the game with appropriate UI based on display mode."""
    config = ConfigManager()
    
    # Check display mode and use appropriate UI
    if config.get('display_mode') == 'graphical':
        # Use pygame UI for graphical mode (Dwarf Fortress-style)
        from boneglaive.ui.pygame_game_ui import PygameGameUI
        
        # Get window size from config or use defaults
        width = config.get('window_width', 1000)
        height = config.get('window_height', 700)
        
        game_ui = PygameGameUI(width, height)
        
        # Main pygame game loop
        running = True
        while running and game_ui.renderer.running:
            # Get user input (this handles pygame events)
            key = game_ui.renderer.get_input()
            if key == -1:  # No input
                continue
                
            # Handle input - this will update the game state and redraw
            running = game_ui.handle_input(key)
            
        # Clean up pygame resources
        game_ui.renderer.cleanup()
    else:
        # Use curses UI for text mode (traditional terminal)
        game_ui = GameUI(stdscr)
        
        # Draw initial board
        game_ui.draw_board()
        
        running = True
        while running:
            # Get user input
            key = stdscr.getch()
            
            # Handle input - this will update the game state and redraw
            running = game_ui.handle_input(key)

def main(stdscr):
    """Main function that coordinates menu and game."""
    # Initial setup for the curses screen
    curses.curs_set(0)  # Hide cursor
    stdscr.timeout(-1)  # No timeout for getch
    
    # Set up platform-specific terminal optimizations
    setup_terminal_optimizations()
    
    # Set escape key delay if supported by curses
    try:
        if hasattr(curses, 'set_escdelay'):
            curses.set_escdelay(25)
    except:
        pass  # Ignore if not supported on this system
    
    # Get arguments
    args = parse_args()
    
    # Configure settings
    configure_settings(args)
    
    # Initialize logging
    logger.setLevel(debug_config.log_level.value)
    if debug_config.log_to_file:
        # If we're logging to a file, make sure the root logger is set up properly
        os.makedirs('logs', exist_ok=True)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('logs/boneglaive.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Otherwise use a null handler to prevent stdout logging
        logger.addHandler(logging.NullHandler())
    
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

def main_graphical(args):
    """Main function for graphical mode (pygame) - bypasses curses."""
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
    
    # Initialize logging
    logger.setLevel(debug_config.log_level.value)
    if debug_config.log_to_file:
        # If we're logging to a file, make sure the root logger is set up properly
        os.makedirs('logs', exist_ok=True)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('logs/boneglaive.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Otherwise use a null handler to prevent stdout logging
        logger.addHandler(logging.NullHandler())
    
    logger.info("Starting Boneglaive in graphical mode")
    
    # Run menu or skip to game
    if args.skip_menu:
        logger.info("Skipping menu in graphical mode")
        run_game_graphical()
    else:
        # Run pygame menu using existing MenuUI
        logger.info("Starting graphical menu")
        
        config = ConfigManager()
        width = config.get('window_width', 1000)
        height = config.get('window_height', 700)
        
        # Create pygame renderer for menu
        from boneglaive.renderers.pygame_renderer import PygameRenderer
        renderer = PygameRenderer(width, height)
        renderer.initialize()
        
        try:
            from boneglaive.ui.menu_ui import MenuUI
            menu_ui = MenuUI(renderer=renderer)
            menu_result = menu_ui.run()
            
            # Process menu result
            if menu_result and menu_result[0] == "start_game":
                logger.info("Starting game from graphical menu")
                renderer.cleanup()  # Clean up menu renderer
                run_game_graphical()
            else:
                logger.info("Quitting from graphical menu")
        finally:
            renderer.cleanup()

def run_game_graphical():
    """Run the game in graphical (pygame) mode."""
    config = ConfigManager()
    
    # Get window size from config or use defaults
    width = config.get('window_width', 1000)
    height = config.get('window_height', 700)
    
    # Create pygame renderer
    from boneglaive.renderers.pygame_renderer import PygameRenderer
    renderer = PygameRenderer(width, height)
    renderer.initialize()
    
    try:
        # Use existing GameUI with pygame renderer
        from boneglaive.ui.game_ui import GameUI
        game_ui = GameUI(renderer=renderer)
        
        # Set UI reference in renderer for animation support
        renderer.set_ui_reference(game_ui)
        
        # Draw initial board
        game_ui.draw_board()
        
        # Run game loop using existing input handling
        running = True
        while running and renderer.running:
            # Get input from pygame renderer
            key = renderer.get_input()
            
            if key == -1:  # No input
                continue
                
            # Handle input using existing GameUI logic
            running = game_ui.handle_input(key)
            
    finally:
        # Clean up pygame resources
        renderer.cleanup()

if __name__ == "__main__":
    # Set up platform-specific terminal optimizations before starting curses
    setup_terminal_optimizations()
    
    # Log platform information
    logger.info(f"Starting Boneglaive on {get_platform_name()}")
    
    # Parse args early to check display mode
    args = parse_args()
    configure_settings(args)
    
    # Check if we should run in graphical mode (bypass curses)
    config = ConfigManager()
    if config.get('display_mode') == 'graphical':
        # Run graphical mode directly without curses
        main_graphical(args)
    else:
        # Start the application with curses for text mode
        curses.wrapper(main)