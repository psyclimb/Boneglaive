#!/usr/bin/env python3
import curses
import argparse
import sys
from boneglaive.ui.game_ui import GameUI
from boneglaive.utils.debug import debug_config, LogLevel

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Boneglaive - Tactical Combat Game")
    
    # Debug options
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug', action='store_true', help='Enable debug mode')
    debug_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                             default='INFO', help='Set logging level')
    debug_group.add_argument('--log-file', action='store_true', help='Enable logging to file')
    debug_group.add_argument('--perf', action='store_true', help='Enable performance tracking')
    debug_group.add_argument('--overlay', action='store_true', help='Show debug overlay')
    
    return parser.parse_args()

def configure_debug(args):
    """Configure debug settings based on command line arguments"""
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

def main(stdscr):
    # Setup
    curses.curs_set(0)  # Hide cursor
    stdscr.timeout(-1)  # No timeout for getch
    
    # Create and start game
    ui = GameUI(stdscr)
    
    running = True
    while running:
        ui.draw_board()
        key = stdscr.getch()
        running = ui.handle_input(key)

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Configure debug settings
    configure_debug(args)
    
    # Start the game
    curses.wrapper(main)