#!/usr/bin/env python3
"""
Font Utilities
Dynamic font sizing to fit text within UI element bounds.
"""
import pygame
from typing import Tuple, Optional


class FontCache:
    """Cache for dynamically sized fonts to avoid recreation."""

    def __init__(self):
        self._cache = {}  # (font_name, size) -> pygame.Font

    def get_font(self, font_name: str, size: int) -> pygame.font.Font:
        """
        Get or create a font.

        Args:
            font_name: Font name (e.g., 'arial') or None for default
            size: Font size in points

        Returns:
            pygame.Font object
        """
        key = (font_name, size)
        if key not in self._cache:
            if font_name:
                try:
                    self._cache[key] = pygame.font.SysFont(font_name, size)
                except:
                    # Fallback to default font
                    self._cache[key] = pygame.font.Font(None, size)
            else:
                self._cache[key] = pygame.font.Font(None, size)

        return self._cache[key]

    def clear(self):
        """Clear the font cache."""
        self._cache.clear()


# Global font cache instance
_font_cache = FontCache()


def get_fitted_font(text: str,
                   max_width: int,
                   max_height: Optional[int] = None,
                   base_font_size: int = 20,
                   min_font_size: int = 12,
                   max_font_size: int = 32,
                   font_name: str = 'arial') -> pygame.font.Font:
    """
    Get a font sized to fit text within constraints.

    Args:
        text: Text to render
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels (optional)
        base_font_size: Starting font size to try
        min_font_size: Minimum allowed font size
        max_font_size: Maximum allowed font size
        font_name: Font name (e.g., 'arial')

    Returns:
        pygame.Font object sized to fit constraints
    """
    if not text:
        return _font_cache.get_font(font_name, base_font_size)

    # Start with base size
    current_size = base_font_size

    # Try base size first
    font = _font_cache.get_font(font_name, current_size)
    text_surface = font.render(text, True, (255, 255, 255))
    width, height = text_surface.get_size()

    # If text fits, try larger sizes up to max
    if width <= max_width and (max_height is None or height <= max_height):
        while current_size < max_font_size:
            test_size = current_size + 1
            test_font = _font_cache.get_font(font_name, test_size)
            test_surface = test_font.render(text, True, (255, 255, 255))
            test_width, test_height = test_surface.get_size()

            if test_width <= max_width and (max_height is None or test_height <= max_height):
                current_size = test_size
                font = test_font
            else:
                break

    # If text doesn't fit, reduce size
    elif width > max_width or (max_height is not None and height > max_height):
        while current_size > min_font_size:
            test_size = current_size - 1
            test_font = _font_cache.get_font(font_name, test_size)
            test_surface = test_font.render(text, True, (255, 255, 255))
            test_width, test_height = test_surface.get_size()

            if test_width <= max_width and (max_height is None or test_height <= max_height):
                current_size = test_size
                font = test_font
                break
            else:
                current_size = test_size
                font = test_font

    return font


def render_fitted_text(text: str,
                       max_width: int,
                       max_height: Optional[int] = None,
                       color: Tuple[int, int, int] = (255, 255, 255),
                       base_font_size: int = 20,
                       min_font_size: int = 12,
                       max_font_size: int = 32,
                       font_name: str = 'arial',
                       antialias: bool = True) -> pygame.Surface:
    """
    Render text with dynamically sized font to fit within constraints.

    Args:
        text: Text to render
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels (optional)
        color: RGB color tuple
        base_font_size: Starting font size to try
        min_font_size: Minimum allowed font size
        max_font_size: Maximum allowed font size
        font_name: Font name (e.g., 'arial')
        antialias: Whether to use antialiasing

    Returns:
        pygame.Surface with rendered text
    """
    font = get_fitted_font(
        text=text,
        max_width=max_width,
        max_height=max_height,
        base_font_size=base_font_size,
        min_font_size=min_font_size,
        max_font_size=max_font_size,
        font_name=font_name
    )

    return font.render(text, antialias, color)


def clear_font_cache():
    """Clear the global font cache."""
    _font_cache.clear()
