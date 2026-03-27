#!/usr/bin/env python3
"""
Path utilities for PyInstaller-compatible asset loading.

Under a normal Python run, assets live relative to the project root.
Under PyInstaller, files are unpacked to sys._MEIPASS at runtime.
asset_path() resolves both cases transparently.
"""
import sys
from pathlib import Path


def asset_path(relative: str) -> str:
    """
    Return an absolute path to a bundled asset.

    Args:
        relative: Path relative to the project root, e.g. "graphics/units/glaiveman.svg"

    Returns:
        Absolute path string usable with open(), pygame.image.load(), cairosvg, etc.
    """
    base = getattr(sys, '_MEIPASS', None)
    if base is None:
        # Running from source: project root is three levels up from this file
        # boneglaive/utils/paths.py -> boneglaive/utils -> boneglaive -> project root
        base = Path(__file__).parent.parent.parent
    return str(Path(base) / relative)


def user_config_dir() -> Path:
    """
    Return a writable directory for user configuration.

    Uses XDG_CONFIG_HOME on Unix, %APPDATA% on Windows.
    Creates the directory if it doesn't exist.
    """
    import os
    import platform

    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        config_dir = Path(base) / "boneglaive"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            config_dir = Path(xdg) / "boneglaive"
        else:
            config_dir = Path.home() / ".config" / "boneglaive"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
