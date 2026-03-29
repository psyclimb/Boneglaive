#!/usr/bin/env python3
"""
Path utilities for PyInstaller-compatible asset loading.

Under a normal Python run, assets live relative to the project root.
Under PyInstaller, files are unpacked to sys._MEIPASS at runtime.
asset_path() resolves both cases transparently.
"""
import os
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


def load_svg(svg_path: str, width: int, height: int):
    """
    Load an SVG as a pygame Surface. Tries pre-rendered PNG first (same path
    with .png extension), then falls back to cairosvg runtime conversion.

    Args:
        svg_path: Absolute path to the .svg file
        width: Desired output width in pixels
        height: Desired output height in pixels

    Returns:
        pygame.Surface with alpha, or None if loading failed
    """
    import pygame

    # Try PNG version first (works everywhere, no native deps)
    png_path = svg_path.rsplit('.svg', 1)[0] + '.png' if svg_path.endswith('.svg') else svg_path
    if os.path.exists(png_path):
        try:
            surface = pygame.image.load(png_path)
            surface = pygame.transform.smoothscale(surface, (width, height))
            return surface.convert_alpha()
        except Exception:
            pass

    # Fall back to cairosvg runtime conversion
    if os.path.exists(svg_path):
        try:
            import cairosvg
            from io import BytesIO
            png_data = cairosvg.svg2png(url=svg_path, output_width=width, output_height=height)
            surface = pygame.image.load(BytesIO(png_data))
            return surface.convert_alpha()
        except Exception:
            pass

    return None


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
