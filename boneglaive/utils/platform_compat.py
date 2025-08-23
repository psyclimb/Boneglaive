#!/usr/bin/env python3
"""
Platform compatibility utilities for cross-platform support.
Handles differences between Windows, Linux, and other operating systems.
"""

import platform
import sys


def get_curses_module():
    """
    Get the appropriate curses module for the current platform.
    
    Returns:
        curses module or None if unavailable
    """
    if platform.system() == 'Windows':
        try:
            # Try to import windows-curses package
            import windows_curses as curses
            return curses
        except ImportError:
            # windows-curses not installed
            return None
    else:
        # Unix-like systems (Linux, macOS, etc.)
        try:
            import curses
            return curses
        except ImportError:
            return None


def is_windows():
    """Check if running on Windows."""
    return platform.system() == 'Windows'


def is_unix_like():
    """Check if running on Unix-like system (Linux, macOS, etc.)."""
    return platform.system() in ['Linux', 'Darwin', 'FreeBSD', 'OpenBSD']


def get_platform_name():
    """Get a human-readable platform name."""
    system = platform.system()
    if system == 'Windows':
        return 'Windows'
    elif system == 'Linux':
        return 'Linux'
    elif system == 'Darwin':
        return 'macOS'
    else:
        return system


def setup_terminal_optimizations():
    """
    Set up platform-specific terminal optimizations.
    
    Returns:
        bool: True if optimizations were applied, False otherwise
    """
    if is_unix_like():
        try:
            import os
            # Set escape key delay for faster ESC key response
            os.environ.setdefault('ESCDELAY', '25')
            return True
        except Exception:
            return False
    else:
        # Windows doesn't use ESCDELAY
        return False


def get_requirements_for_platform():
    """
    Get platform-specific requirements.
    
    Returns:
        list: List of packages needed for current platform
    """
    requirements = []
    
    if is_windows():
        requirements.append('windows-curses')
    
    # pygame is optional for all platforms
    requirements.append('pygame')
    
    return requirements


def print_platform_info():
    """Print platform information for debugging."""
    print(f"Platform: {get_platform_name()}")
    print(f"System: {platform.system()}")
    print(f"Python version: {sys.version}")
    print(f"Architecture: {platform.architecture()[0]}")
    
    # Test curses availability
    curses_module = get_curses_module()
    if curses_module:
        print("✓ Curses module available")
    else:
        print("✗ Curses module not available")
        if is_windows():
            print("  Install with: pip install windows-curses")