#!/usr/bin/env python3
"""
Lock-Out-Tag-Out (LOTO) System
Checks unit status effects to determine which actions are blocked.
"""
from typing import Optional, Set
import pygame
import os
from boneglaive.utils.paths import asset_path, load_svg
from boneglaive.utils.constants import UnitType


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

        if hasattr(unit, 'is_doppelganger') and unit.is_doppelganger:
            blocked.add('move')
            blocked.add('upgrade')  # Doppelgangers cannot be upgraded

            # Check if Græ Exchange is upgraded
            grae_exchange_upgraded = hasattr(unit, 'upgraded_skills') and 'Græ Exchange' in unit.upgraded_skills

            if not grae_exchange_upgraded:
                # If Græ Exchange NOT upgraded, block all skills
                blocked.add('skill')
            # If Græ Exchange IS upgraded, skills button is NOT blocked
            # but specific skills (Delta Config, Estrange) are blocked
            # (handled separately in is_skill_blocked)

        # Check skill and attack blocking effects (Neural Shunt blocks ALL manual actions)
        if hasattr(unit, 'neural_shunt_affected') and unit.neural_shunt_affected:
            blocked.add('move')
            blocked.add('skill')
            blocked.add('attack')

        # Check disarm effect (Aerosolize Arms)
        if hasattr(unit, 'status_disarmed') and unit.status_disarmed:
            blocked.add('attack')

        # MANDIBLE FOREMAN cannot attack while trapping a unit
        if hasattr(unit, 'type') and unit.type == UnitType.MANDIBLE_FOREMAN:
            game = getattr(unit, '_game', None)
            if game:
                if any(u.is_alive() and u.trapped_by is unit for u in game.units):
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
            action_type: 'move', 'attack', 'skill', or 'upgrade'

        Returns:
            True if the action is blocked
        """
        blocked = LOTOChecker.get_blocked_actions(unit)
        return action_type in blocked or 'all' in blocked

    @staticmethod
    def is_skill_blocked(unit, skill_name: str) -> bool:
        """
        Check if a specific skill is blocked for a unit.

        Args:
            unit: The unit to check
            skill_name: Name of the skill (e.g., "Delta Config", "Estrange")

        Returns:
            True if the skill is blocked
        """
        if not unit:
            return False

        # If all skills are blocked, return True
        if LOTOChecker.is_action_blocked(unit, 'skill'):
            return True

        # Special case: Doppelgangers with upgraded Græ Exchange
        if hasattr(unit, 'is_doppelganger') and unit.is_doppelganger:
            grae_exchange_upgraded = hasattr(unit, 'upgraded_skills') and 'Græ Exchange' in unit.upgraded_skills

            if grae_exchange_upgraded:
                # Delta Config and Estrange are blocked for doppelgangers even with upgraded Græ Exchange
                if skill_name in ["Delta Config", "Estrange"]:
                    return True

        # Special case: Infuse is blocked when POTPOURRIST already has Infused buff
        if skill_name == "Infuse":
            if hasattr(unit, 'potpourri_held') and unit.potpourri_held:
                return True

        return False


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

        chain_path = asset_path('graphics/ui/loto_chain.svg')
        lock_path = asset_path('graphics/ui/loto_lock.svg')
        tag_path = asset_path('graphics/ui/loto_tag.svg')

        self.chain_icon = load_svg(chain_path, icon_size, icon_size)
        if not self.chain_icon:
            self.chain_icon = self._create_fallback_chain()

        self.lock_icon = load_svg(lock_path, icon_size, icon_size)
        if not self.lock_icon:
            self.lock_icon = self._create_fallback_lock()

        self.tag_icon = load_svg(tag_path, icon_size, icon_size)
        if not self.tag_icon:
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
