#!/usr/bin/env python3
"""
Lock-Out-Tag-Out (LOTO) System
Checks unit status effects to determine which actions are blocked.
"""
from typing import Optional, Set
import pygame
import os


class LOTOChecker:
    """Checks which actions are locked out by status effects."""

    @staticmethod
    def get_blocked_actions(unit) -> Set[str]:
        """
        Check which actions are blocked for a unit.

        Returns:
            Set of blocked action types: 'move', 'attack', 'skill', 'all'
        """
        if not unit:
            return set()

        blocked = set()

        # Check movement-blocking effects
        if hasattr(unit, 'derelicted') and unit.derelicted:
            blocked.add('move')

        if hasattr(unit, 'mired') and unit.mired:
            blocked.add('move')

        if hasattr(unit, 'jawline_affected') and unit.jawline_affected:
            blocked.add('move')

        if unit.trapped_by is not None:
            blocked.add('move')
            blocked.add('skill')  # Viseroy trap blocks both movement and skills

        if unit.is_echo:
            blocked.add('move')

        # Check skill and attack blocking effects
        if hasattr(unit, 'neural_shunt_affected') and unit.neural_shunt_affected:
            blocked.add('skill')
            blocked.add('attack')

        # Check all-action-blocking effects
        if hasattr(unit, 'gaussian_dusk_recharge') and unit.gaussian_dusk_recharge:
            blocked.add('all')  # Blocks everything during recharge

        if hasattr(unit, 'gaussian_charging') and unit.gaussian_charging:
            blocked.add('all')  # Blocks everything while charging

        # TODO: Add Viseroy skill blocking when implemented
        # if hasattr(unit, 'viseroyblocked') and unit.viseroy_blocked:
        #     blocked.add('skill')
        #     blocked.add('move')

        return blocked

    @staticmethod
    def is_action_blocked(unit, action_type: str) -> bool:
        """
        Check if a specific action type is blocked.

        Args:
            unit: The unit to check
            action_type: 'move', 'attack', or 'skill'

        Returns:
            True if the action is blocked
        """
        blocked = LOTOChecker.get_blocked_actions(unit)
        return action_type in blocked or 'all' in blocked


class LOTORenderer:
    """Renders lock-out-tag-out visual overlays on buttons."""

    def __init__(self):
        self.chain_icon = None
        self.lock_icon = None
        self.tag_icon = None
        self._load_icons()

    def _load_icons(self):
        """Load LOTO SVG icons."""
        icon_size = 64  # Base size for LOTO icons

        graphics_dir = os.path.join(os.path.dirname(__file__), '../../../graphics/ui')

        chain_path = os.path.join(graphics_dir, 'loto_chain.svg')
        lock_path = os.path.join(graphics_dir, 'loto_lock.svg')
        tag_path = os.path.join(graphics_dir, 'loto_tag.svg')

        # Try loading SVGs with cairosvg
        try:
            import cairosvg
            from io import BytesIO

            # Load chain icon
            if os.path.exists(chain_path):
                png_data = cairosvg.svg2png(url=chain_path, output_width=icon_size, output_height=icon_size)
                self.chain_icon = pygame.image.load(BytesIO(png_data)).convert_alpha()
            else:
                print(f"[LOTO] Chain SVG not found: {chain_path}")
                self.chain_icon = self._create_fallback_chain()

            # Load lock icon
            if os.path.exists(lock_path):
                png_data = cairosvg.svg2png(url=lock_path, output_width=icon_size, output_height=icon_size)
                self.lock_icon = pygame.image.load(BytesIO(png_data)).convert_alpha()
            else:
                print(f"[LOTO] Lock SVG not found: {lock_path}")
                self.lock_icon = self._create_fallback_lock()

            # Load tag icon
            if os.path.exists(tag_path):
                png_data = cairosvg.svg2png(url=tag_path, output_width=icon_size, output_height=icon_size)
                self.tag_icon = pygame.image.load(BytesIO(png_data)).convert_alpha()
            else:
                print(f"[LOTO] Tag SVG not found: {tag_path}")
                self.tag_icon = self._create_fallback_tag()

        except ImportError:
            print("[LOTO] cairosvg not available, using fallback graphics")
            self.chain_icon = self._create_fallback_chain()
            self.lock_icon = self._create_fallback_lock()
            self.tag_icon = self._create_fallback_tag()
        except Exception as e:
            print(f"[LOTO] Error loading SVG icons: {e}")
            self.chain_icon = self._create_fallback_chain()
            self.lock_icon = self._create_fallback_lock()
            self.tag_icon = self._create_fallback_tag()

    def _create_fallback_chain(self) -> pygame.Surface:
        """Create a simple chain icon as fallback."""
        size = 32
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        # Draw diagonal chain links
        gray = (140, 140, 140)
        dark_gray = (80, 80, 80)

        # Chain links
        for i in range(3):
            x = 8 + i * 8
            y = 8 + i * 8
            pygame.draw.ellipse(surf, gray, (x, y, 12, 16), 3)
            pygame.draw.ellipse(surf, dark_gray, (x, y, 12, 16), 1)

        return surf

    def _create_fallback_lock(self) -> pygame.Surface:
        """Create a simple lock icon as fallback."""
        size = 32
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        # Red padlock
        red = (204, 0, 0)
        dark_red = (136, 0, 0)
        gray = (140, 140, 140)

        # Shackle (U-shape on top)
        pygame.draw.arc(surf, gray, (10, 6, 12, 12), 0, 3.14159, 3)

        # Lock body
        pygame.draw.rect(surf, red, (8, 14, 16, 12), border_radius=2)
        pygame.draw.rect(surf, dark_red, (8, 14, 16, 12), 1, border_radius=2)

        # Keyhole
        pygame.draw.circle(surf, dark_red, (16, 19), 2)
        pygame.draw.line(surf, dark_red, (16, 19), (16, 23), 2)

        return surf

    def _create_fallback_tag(self) -> pygame.Surface:
        """Create a simple danger tag icon as fallback."""
        size = 32
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        # Yellow/red danger tag
        yellow = (255, 255, 0)
        red = (255, 0, 0)
        black = (0, 0, 0)

        # Tag body
        pygame.draw.rect(surf, yellow, (6, 10, 20, 16), border_radius=1)
        pygame.draw.rect(surf, black, (6, 10, 20, 16), 1, border_radius=1)

        # Danger stripe
        pygame.draw.line(surf, red, (8, 12), (24, 12), 2)
        pygame.draw.line(surf, red, (8, 16), (24, 16), 2)
        pygame.draw.line(surf, red, (8, 20), (24, 20), 2)

        # Hole for tag
        pygame.draw.circle(surf, black, (10, 14), 2)
        pygame.draw.circle(surf, yellow, (10, 14), 1)

        return surf

    def draw_loto_overlay(self, surface: pygame.Surface, rect: pygame.Rect,
                         blocked_actions: Set[str], scale: float = 0.5):
        """
        Draw LOTO overlay on a button.

        Args:
            surface: Surface to draw on
            rect: Button rectangle
            blocked_actions: Set of blocked action types
            scale: Scale factor for the overlay (0.0-1.0)
        """
        if not blocked_actions:
            return

        # Determine overlay size
        overlay_size = int(min(rect.width, rect.height) * scale)

        # Position in top-right corner of button
        overlay_x = rect.right - overlay_size - 4
        overlay_y = rect.top + 4

        # Draw semi-transparent background
        bg_surf = pygame.Surface((overlay_size, overlay_size), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), border_radius=4)
        surface.blit(bg_surf, (overlay_x, overlay_y))

        # Always show just the lock icon (simple, clean look)
        if self.lock_icon:
            icon_scaled = pygame.transform.scale(self.lock_icon, (overlay_size - 4, overlay_size - 4))
            surface.blit(icon_scaled, (overlay_x + 2, overlay_y + 2))
