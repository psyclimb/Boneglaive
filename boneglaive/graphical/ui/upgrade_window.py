#!/usr/bin/env python3
"""
Upgrade Window UI Component
Modal window for selecting unit skill upgrades during gameplay.
"""
import pygame
from typing import Optional, List, Dict
from boneglaive.utils.paths import asset_path, load_svg

# Colors - matching bone/industrial theme
COLOR_OVERLAY = (0, 0, 0, 180)  # Semi-transparent black overlay
COLOR_WINDOW_BG_TOP = (42, 42, 47)  # Panel top
COLOR_WINDOW_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_WINDOW_BORDER = (90, 84, 79)  # Metal border
COLOR_TITLE_BG_TOP = (50, 50, 55)  # Title bar gradient top
COLOR_TITLE_BG_BOTTOM = (38, 38, 43)  # Title bar gradient bottom
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_ITEM_BG_TOP = (74, 74, 79)  # Item gradient top
COLOR_ITEM_BG_BOTTOM = (50, 50, 55)  # Item gradient bottom
COLOR_ITEM_HOVER_TOP = (90, 74, 79)  # Item hover gradient top
COLOR_ITEM_HOVER_BOTTOM = (64, 48, 53)  # Item hover gradient bottom
COLOR_ITEM_SELECTED_TOP = (106, 90, 95)  # Item selected gradient top
COLOR_ITEM_SELECTED_BOTTOM = (74, 58, 63)  # Item selected gradient bottom
COLOR_BUTTON_TOP = (74, 74, 79)  # Button gradient top
COLOR_BUTTON_BOTTOM = (50, 50, 55)  # Button gradient bottom
COLOR_BUTTON_HOVER_TOP = (90, 74, 79)  # Button hover gradient top
COLOR_BUTTON_HOVER_BOTTOM = (64, 48, 53)  # Button hover gradient bottom
COLOR_BORDER_HOVER = (184, 168, 149)  # Bone border on hover
COLOR_BORDER_GLOW = (255, 170, 119)  # Orange glow
COLOR_GREEN = (100, 255, 150)
COLOR_GOLD = (255, 215, 0)
COLOR_BLUE = (100, 150, 255)

# Import scaling utilities
from .scale_utils import scale_manager

# Scale window dimensions based on resolution
WINDOW_WIDTH = scale_manager.scale(800, 'x')
WINDOW_HEIGHT = scale_manager.scale(650, 'y')
ITEM_HEIGHT = scale_manager.scale(110, 'y')
ITEM_PADDING = scale_manager.scale(15)


class UpgradeWindow:
    """Modal window for selecting skill upgrades for a unit."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False
        self.unit = None
        self.available_upgrades = []

        # State
        self.selected_index = 0
        self.hovered_index = None
        self.hover_confirm = False
        self.hover_cancel = False

        # Calculated positions
        self.window_rect = None
        self.item_rects = []
        self.confirm_button_rect = None
        self.cancel_button_rect = None

        # Icon cache
        self.icon_cache = {}  # {skill_name: pygame.Surface}

        # Cache overlay surface (performance)
        self._overlay_cache = None

    def show(self, unit):
        """
        Open the upgrade window for a unit.

        Args:
            unit: Unit object to show upgrades for

        Returns:
            bool: True if window opened successfully, False if no upgrades available
        """
        from boneglaive.game.upgrades import UpgradeManager

        self.unit = unit
        self.available_upgrades = UpgradeManager.get_available_upgrades(unit)

        if len(self.available_upgrades) == 0:
            return False  # Can't open if no upgrades available

        self.visible = True
        self.selected_index = 0
        self.hovered_index = None
        self.hover_confirm = False
        self.hover_cancel = False

        return True

    def hide(self):
        """Close the upgrade window."""
        self.visible = False
        self.unit = None
        self.available_upgrades = []
        self.selected_index = 0

    def select_next(self):
        """Select next upgrade in list."""
        if self.available_upgrades:
            self.selected_index = (self.selected_index + 1) % len(self.available_upgrades)

    def select_prev(self):
        """Select previous upgrade in list."""
        if self.available_upgrades:
            self.selected_index = (self.selected_index - 1) % len(self.available_upgrades)

    def get_selected_upgrade(self) -> Optional[Dict]:
        """Get the currently selected upgrade."""
        if 0 <= self.selected_index < len(self.available_upgrades):
            return self.available_upgrades[self.selected_index]
        return None

    def _load_skill_icon(self, skill_name: str) -> Optional[pygame.Surface]:
        """Load skill icon from SVG file."""
        if skill_name in self.icon_cache:
            return self.icon_cache[skill_name]

        # Convert skill name to filename (e.g., "Marrow Dike" -> "marrow_dike")
        filename = skill_name.lower().replace(' ', '_')
        filename = ''.join(c for c in filename if c not in r'\/:*?"<>|()')
        icon_path = asset_path(f"graphics/skill_icons/{filename}.svg")

        surface = load_svg(icon_path, 64, 64)
        if surface is None:
            # Return a placeholder surface
            surface = pygame.Surface((64, 64), pygame.SRCALPHA)
            surface.fill((60, 60, 60))
        self.icon_cache[skill_name] = surface
        return surface

    def draw(self, surface: pygame.Surface):
        """Draw the upgrade window."""
        if not self.visible or not self.unit:
            return

        screen_width = surface.get_width()
        screen_height = surface.get_height()

        # Center window
        window_x = (screen_width - WINDOW_WIDTH) // 2
        window_y = (screen_height - WINDOW_HEIGHT) // 2

        # Draw semi-transparent overlay (cached for performance)
        if self._overlay_cache is None or self._overlay_cache.get_size() != (screen_width, screen_height):
            self._overlay_cache = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            self._overlay_cache.fill(COLOR_OVERLAY)
        surface.blit(self._overlay_cache, (0, 0))

        # Draw window background with gradient
        from .menu_components import draw_gradient_rect, draw_glow_rect

        self.window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Draw shadow for window
        shadow_rect = self.window_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 120), shadow_surf.get_rect(), border_radius=8)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw gradient background
        draw_gradient_rect(surface, self.window_rect, COLOR_WINDOW_BG_TOP, COLOR_WINDOW_BG_BOTTOM)
        pygame.draw.rect(surface, COLOR_WINDOW_BORDER, self.window_rect, 3, border_radius=8)

        # Draw title bar with gradient
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 40)
        draw_gradient_rect(surface, title_rect, COLOR_TITLE_BG_TOP, COLOR_TITLE_BG_BOTTOM)

        title_text = f"Upgrade {self.unit.get_display_name()}"
        title_surface = self.font.render(title_text, True, COLOR_TEXT)
        surface.blit(title_surface, (window_x + 20, window_y + 10))

        # Draw upgrade points available
        game = self.unit._game
        points = game.player1_upgrade_points if self.unit.player == 1 else game.player2_upgrade_points
        points_text = f"Upgrade Points: {points}"
        points_surface = self.small_font.render(points_text, True, COLOR_GOLD)
        surface.blit(points_surface, (window_x + 20, window_y + 50))

        # Draw available upgrades
        self.item_rects = []
        y_offset = 90

        for i, upgrade in enumerate(self.available_upgrades):
            # Upgrade box
            upgrade_rect = pygame.Rect(
                window_x + 20,
                window_y + y_offset,
                WINDOW_WIDTH - 40,
                ITEM_HEIGHT
            )
            self.item_rects.append(upgrade_rect)

            # Determine gradient colors and effects
            if i == self.selected_index:
                bg_top = COLOR_ITEM_SELECTED_TOP
                bg_bottom = COLOR_ITEM_SELECTED_BOTTOM
                border_color = COLOR_BORDER_HOVER
                show_glow = True
                glow_color = COLOR_GREEN
            elif i == self.hovered_index:
                bg_top = COLOR_ITEM_HOVER_TOP
                bg_bottom = COLOR_ITEM_HOVER_BOTTOM
                border_color = COLOR_BORDER_HOVER
                show_glow = True
                glow_color = COLOR_BORDER_GLOW
            else:
                bg_top = COLOR_ITEM_BG_TOP
                bg_bottom = COLOR_ITEM_BG_BOTTOM
                border_color = COLOR_WINDOW_BORDER
                show_glow = False
                glow_color = None

            # Draw shadow for upgrade box
            shadow_rect = upgrade_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
            surface.blit(shadow_surf, shadow_rect.topleft)

            # Draw gradient background
            draw_gradient_rect(surface, upgrade_rect, bg_top, bg_bottom)

            # Draw glow effect if selected or hovered
            if show_glow and glow_color:
                draw_glow_rect(surface, upgrade_rect, glow_color, intensity=0.5, width=1)

            # Draw border
            pygame.draw.rect(surface, border_color, upgrade_rect, 2, border_radius=5)

            # Load and draw skill icon
            icon = self._load_skill_icon(upgrade['skill_name'])
            if icon:
                icon_x = upgrade_rect.x + 10
                icon_y = upgrade_rect.y + 10
                surface.blit(icon, (icon_x, icon_y))

            # Draw upgrade name (to the right of icon)
            name_surface = self.font.render(upgrade['name'], True, COLOR_TEXT)
            surface.blit(name_surface, (upgrade_rect.x + 85, upgrade_rect.y + 10))

            # Draw upgrade description (below name, to the right of icon)
            desc_text = upgrade['description']
            self._draw_wrapped_text(
                surface,
                desc_text,
                upgrade_rect.x + 85,
                upgrade_rect.y + 45,
                WINDOW_WIDTH - 120,
                COLOR_TEXT_DIM
            )

            y_offset += ITEM_HEIGHT + ITEM_PADDING

        # Draw buttons at bottom
        button_y = window_y + WINDOW_HEIGHT - 60

        # Confirm button
        self.confirm_button_rect = pygame.Rect(window_x + 20, button_y, 200, 40)

        # Shadow for confirm button
        shadow_rect = self.confirm_button_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Gradient for confirm button
        if self.hover_confirm:
            confirm_top = COLOR_BUTTON_HOVER_TOP
            confirm_bottom = COLOR_BUTTON_HOVER_BOTTOM
            confirm_border = COLOR_BORDER_HOVER
        else:
            confirm_top = COLOR_BUTTON_TOP
            confirm_bottom = COLOR_BUTTON_BOTTOM
            confirm_border = COLOR_WINDOW_BORDER

        draw_gradient_rect(surface, self.confirm_button_rect, confirm_top, confirm_bottom)

        # Add green overlay for confirm button
        overlay_surf = pygame.Surface((self.confirm_button_rect.width, self.confirm_button_rect.height), pygame.SRCALPHA)
        overlay_alpha = 100 if self.hover_confirm else 60
        overlay_surf.fill((*COLOR_GREEN, overlay_alpha))
        surface.blit(overlay_surf, self.confirm_button_rect.topleft)

        # Glow for confirm button on hover
        if self.hover_confirm:
            draw_glow_rect(surface, self.confirm_button_rect, COLOR_BORDER_GLOW, intensity=0.5, width=1)

        pygame.draw.rect(surface, confirm_border, self.confirm_button_rect, 2, border_radius=5)
        confirm_text = self.font.render("CONFIRM", True, COLOR_TEXT)
        text_rect = confirm_text.get_rect(center=self.confirm_button_rect.center)
        surface.blit(confirm_text, text_rect)

        # Cancel button
        self.cancel_button_rect = pygame.Rect(window_x + WINDOW_WIDTH - 220, button_y, 200, 40)

        # Shadow for cancel button
        shadow_rect = self.cancel_button_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Gradient for cancel button
        if self.hover_cancel:
            cancel_top = COLOR_BUTTON_HOVER_TOP
            cancel_bottom = COLOR_BUTTON_HOVER_BOTTOM
            cancel_border = COLOR_BORDER_HOVER
        else:
            cancel_top = COLOR_BUTTON_TOP
            cancel_bottom = COLOR_BUTTON_BOTTOM
            cancel_border = COLOR_WINDOW_BORDER

        draw_gradient_rect(surface, self.cancel_button_rect, cancel_top, cancel_bottom)

        # Glow for cancel button on hover
        if self.hover_cancel:
            draw_glow_rect(surface, self.cancel_button_rect, COLOR_BORDER_GLOW, intensity=0.5, width=1)

        pygame.draw.rect(surface, cancel_border, self.cancel_button_rect, 2, border_radius=5)
        cancel_text = self.font.render("CANCEL", True, COLOR_TEXT)
        text_rect = cancel_text.get_rect(center=self.cancel_button_rect.center)
        surface.blit(cancel_text, text_rect)

    def _draw_wrapped_text(self, surface, text, x, y, max_width, color):
        """Draw text with word wrapping."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.small_font.render(test_line, True, color)

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Draw lines (max 2 lines)
        for i, line in enumerate(lines[:2]):
            line_surface = self.small_font.render(line, True, color)
            surface.blit(line_surface, (x, y + i * 15))

    def handle_mouse_motion(self, pos: tuple):
        """Handle mouse motion to update hover states."""
        if not self.visible:
            return

        # Check upgrade items
        self.hovered_index = None
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(pos):
                self.hovered_index = i
                break

        # Check buttons
        self.hover_confirm = self.confirm_button_rect and self.confirm_button_rect.collidepoint(pos)
        self.hover_cancel = self.cancel_button_rect and self.cancel_button_rect.collidepoint(pos)

    def handle_click(self, pos: tuple) -> Optional[str]:
        """
        Handle mouse click in upgrade window.

        Returns:
            'confirm', 'cancel', 'consumed' (click on window but no action), or None
        """
        if not self.visible:
            return None

        # Check if click is within window bounds - consume it even if not on a specific element
        if self.window_rect and self.window_rect.collidepoint(pos):
            # Check upgrade selection
            for i, rect in enumerate(self.item_rects):
                if rect.collidepoint(pos):
                    self.selected_index = i
                    return 'consumed'

            # Check confirm button
            if self.confirm_button_rect and self.confirm_button_rect.collidepoint(pos):
                return 'confirm'

            # Check cancel button
            if self.cancel_button_rect and self.cancel_button_rect.collidepoint(pos):
                return 'cancel'

            # Click was on window but not on any interactive element - consume it anyway
            return 'consumed'

        return None

    def handle_key(self, key: int) -> Optional[str]:
        """
        Handle keyboard input.

        Returns:
            'confirm', 'cancel', or None
        """
        if not self.visible:
            return None

        # ESC to cancel
        if key == pygame.K_ESCAPE:
            return 'cancel'

        # Enter to confirm
        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            return 'confirm'

        # Arrow keys to navigate
        if key == pygame.K_UP:
            self.select_prev()
        elif key == pygame.K_DOWN:
            self.select_next()

        # Number keys 1-4 for quick selection
        if key == pygame.K_1:
            if len(self.available_upgrades) > 0:
                self.selected_index = 0
                return 'confirm'
        elif key == pygame.K_2:
            if len(self.available_upgrades) > 1:
                self.selected_index = 1
                return 'confirm'
        elif key == pygame.K_3:
            if len(self.available_upgrades) > 2:
                self.selected_index = 2
                return 'confirm'
        elif key == pygame.K_4:
            if len(self.available_upgrades) > 3:
                self.selected_index = 3
                return 'confirm'

        return None
