#!/usr/bin/env python3
"""
Platform compatibility utilities for Boneglaive.
*nix terminal gaming optimizations.
"""

import sys
import platform
import os
import curses

def get_curses_module():
    """
    Get the curses module for *nix systems.
    Returns the curses module.
    """
    return curses

def get_platform_name():
    """Get a human-readable platform name."""
    system = platform.system()
    if system == "Linux":
        # Try to get distribution info
        try:
            import distro
            return f"Linux ({distro.name()})"
        except ImportError:
            return "Linux"
    elif "BSD" in system or system in ["FreeBSD", "OpenBSD", "NetBSD", "DragonFly"]:
        return system
    else:
        return system

def setup_terminal_optimizations():
    """
    Set up terminal optimizations for *nix systems.
    """
    # Optimize for better curses performance on Unix systems
    os.environ.setdefault('TERM', 'xterm-256color')
    os.environ.setdefault('ESCDELAY', '25')  # Faster ESC key response

def get_config_directory():
    """Get the configuration directory following XDG standards."""
    # Use XDG_CONFIG_HOME or ~/.config (Unix standard)
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        return os.path.join(xdg_config, 'boneglaive')
    else:
        return os.path.expanduser('~/.config/boneglaive')

def is_color_terminal():
    """Check if the terminal supports colors."""
    # Check COLORTERM environment variable
    if os.environ.get('COLORTERM'):
        return True
    
    # Check TERM environment variable
    term = os.environ.get('TERM', '').lower()
    color_terms = ['color', '256color', 'truecolor', 'xterm', 'screen']
    
    return any(color_term in term for color_term in color_terms)

def get_terminal_size():
    """Get terminal size using standard Unix methods."""
    try:
        # Try the modern way first
        size = os.get_terminal_size()
        return size.columns, size.lines
    except (AttributeError, OSError):
        # Fallback for older Python versions or if stdout is redirected
        try:
            import shutil
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except:
            # Default fallback
            return 80, 24