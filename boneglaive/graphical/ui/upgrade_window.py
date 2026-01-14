#!/usr/bin/env python3
"""
Upgrade Window UI Component
Modal window for selecting unit skill upgrades during gameplay.
"""
import pygame
from typing import Optional, List, Dict

# Colors
COLOR_OVERLAY = (0, 0, 0, 180)  # Semi-transparent black overlay
COLOR_WINDOW_BG = (30, 34, 42)
COLOR_WINDOW_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_SELECTED = (60, 100, 140)
COLOR_HOVER = (50, 54, 62)
COLOR_BUTTON = (60, 70, 80)
COLOR_BUTTON_HOVER = (80, 90, 100)
COLOR_GREEN = (100, 255, 150)
COLOR_GOLD = (255, 215, 0)
COLOR_BLUE = (100, 150, 255)

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 650
ITEM_HEIGHT = 110
ITEM_PADDING = 15


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
        filename = skill_name.lower().replace(' ', '_').replace('-', '_')
        icon_path = f"graphics/skill_icons/{filename}.svg"

        try:
            import cairosvg
            import io
            from PIL import Image

            # Render SVG to PNG in memory
            png_data = cairosvg.svg2png(url=icon_path, output_width=64, output_height=64)

            # Load PNG data into PIL Image
            pil_image = Image.open(io.BytesIO(png_data))

            # Convert PIL Image to pygame Surface
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()

            surface = pygame.image.fromstring(data, size, mode)

            # Cache it
            self.icon_cache[skill_name] = surface
            return surface
        except Exception as e:
            print(f"Failed to load skill icon for {skill_name}: {e}")
            # Return a placeholder surface
            placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
            placeholder.fill((60, 60, 60))
            self.icon_cache[skill_name] = placeholder
            return placeholder

    def draw(self, surface: pygame.Surface):
        """Draw the upgrade window."""
        if not self.visible or not self.unit:
            return

        screen_width = surface.get_width()
        screen_height = surface.get_height()

        # Center window
        window_x = (screen_width - WINDOW_WIDTH) // 2
        window_y = (screen_height - WINDOW_HEIGHT) // 2

        # Draw semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        surface.blit(overlay, (0, 0))

        # Draw window background
        self.window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(surface, COLOR_WINDOW_BG, self.window_rect)
        pygame.draw.rect(surface, COLOR_WINDOW_BORDER, self.window_rect, 2)

        # Draw title bar
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 40)
        pygame.draw.rect(surface, COLOR_TITLE_BG, title_rect)

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

            # Determine background color
            if i == self.selected_index:
                bg_color = COLOR_SELECTED
                border_color = COLOR_GREEN
                border_width = 3
            elif i == self.hovered_index:
                bg_color = COLOR_HOVER
                border_color = COLOR_WINDOW_BORDER
                border_width = 2
            else:
                bg_color = COLOR_BUTTON
                border_color = COLOR_WINDOW_BORDER
                border_width = 1

            # Draw upgrade box
            pygame.draw.rect(surface, bg_color, upgrade_rect)
            pygame.draw.rect(surface, border_color, upgrade_rect, border_width)

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
        confirm_color = COLOR_BUTTON_HOVER if self.hover_confirm else COLOR_GREEN
        pygame.draw.rect(surface, confirm_color, self.confirm_button_rect)
        pygame.draw.rect(surface, COLOR_WINDOW_BORDER, self.confirm_button_rect, 2)
        confirm_text = self.font.render("CONFIRM", True, COLOR_TEXT)
        text_rect = confirm_text.get_rect(center=self.confirm_button_rect.center)
        surface.blit(confirm_text, text_rect)

        # Cancel button
        self.cancel_button_rect = pygame.Rect(window_x + WINDOW_WIDTH - 220, button_y, 200, 40)
        cancel_color = COLOR_BUTTON_HOVER if self.hover_cancel else COLOR_BUTTON
        pygame.draw.rect(surface, cancel_color, self.cancel_button_rect)
        pygame.draw.rect(surface, COLOR_WINDOW_BORDER, self.cancel_button_rect, 2)
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
