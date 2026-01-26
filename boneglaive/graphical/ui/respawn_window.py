#!/usr/bin/env python3
"""
Respawn Window UI Component
Modal window for selecting dead units to respawn.
"""
import pygame
from typing import Optional, List, Tuple
from .scrollbar import Scrollbar

# Colors
COLOR_OVERLAY = (0, 0, 0, 180)  # Semi-transparent black overlay
COLOR_WINDOW_BG = (30, 34, 42)
COLOR_WINDOW_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_SELECTED = (60, 100, 140)
COLOR_HOVER = (50, 54, 62)
COLOR_GOLD = (255, 215, 0)
COLOR_INFO = (180, 200, 220)

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 400
ITEM_HEIGHT = 60
ITEM_PADDING = 10
SCROLL_SPEED = 3


class RespawnWindow:
    """Modal window showing dead units available for respawn."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False

        # State
        self.dead_units = []  # List of DeadUnit objects
        self.selected_index = 0
        self.hovered_index = None
        self.scroll_offset = 0

        # Calculated positions
        self.window_rect = None
        self.item_rects = []

        # Scrollbar component
        self.scrollbar = Scrollbar()
        self.max_scroll = 0

        # Unit sprite cache
        self.sprite_cache = {}  # {unit_type: pygame.Surface}

        # Cache overlay surface (performance)
        self._overlay_cache = None

    def show(self, dead_units: List):
        """
        Show the respawn window with available dead units.

        Args:
            dead_units: List of DeadUnit objects ready for respawn
        """
        self.visible = True
        self.dead_units = dead_units
        self.selected_index = 0
        self.scroll_offset = 0
        self.hovered_index = None

        # Pre-load sprites for all units in the list (only load ones not cached)
        for dead_unit in dead_units:
            if dead_unit.unit_type not in self.sprite_cache:
                self._load_unit_sprite(dead_unit.unit_type)

    def hide(self):
        """Hide the respawn window."""
        self.visible = False
        self.dead_units = []
        self.selected_index = 0

    def select_next(self):
        """Select next unit in list."""
        if self.dead_units:
            self.selected_index = (self.selected_index + 1) % len(self.dead_units)
            self._ensure_visible(self.selected_index)

    def select_prev(self):
        """Select previous unit in list."""
        if self.dead_units:
            self.selected_index = (self.selected_index - 1) % len(self.dead_units)
            self._ensure_visible(self.selected_index)

    def get_selected_unit(self):
        """Get currently selected dead unit."""
        if self.dead_units and 0 <= self.selected_index < len(self.dead_units):
            return self.dead_units[self.selected_index]
        return None

    def _load_unit_sprite(self, unit_type):
        """
        Load unit sprite from SVG file.

        Args:
            unit_type: UnitType enum value

        Returns:
            pygame.Surface or None if sprite cannot be loaded
        """
        # Check cache first
        if unit_type in self.sprite_cache:
            return self.sprite_cache[unit_type]

        # Convert unit type to filename
        # Handle both base units (UnitType enum) and DLC units (integers >= 100)
        if isinstance(unit_type, int) and unit_type >= 100:
            # DLC unit - get name from DLC manager
            from boneglaive.game.dlc_manager import get_dlc_manager
            dlc_manager = get_dlc_manager()
            sprite_name = None
            for unit_id, unit_data in dlc_manager.loaded_units.items():
                if unit_data['enum_value'] == unit_type:
                    sprite_name = unit_id  # unit_id is already lowercase
                    break
            if not sprite_name:
                self.sprite_cache[unit_type] = None
                return None
        else:
            # Base unit - use enum name
            try:
                sprite_name = unit_type.name.lower()
            except AttributeError:
                self.sprite_cache[unit_type] = None
                return None

        sprite_path = f"graphics/units/{sprite_name}.svg"

        try:
            import cairosvg
            import io

            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=sprite_path, output_width=48, output_height=48)

            # Load PNG data into pygame surface
            png_bytes = io.BytesIO(png_data)
            sprite = pygame.image.load(png_bytes)

            # Cache the sprite
            self.sprite_cache[unit_type] = sprite
            return sprite

        except Exception as e:
            # Cache None to avoid repeated attempts
            self.sprite_cache[unit_type] = None
            return None

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Update hovered item based on mouse position."""
        if not self.visible:
            return

        self.hovered_index = None
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_index = i
                break

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle mouse click. Returns True if a unit was selected.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            True if a unit was clicked and should be confirmed
        """
        if not self.visible:
            return False

        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_index = i
                return True

        return False

    def handle_mouse_down(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle mouse button down event for scrollbar.
        Returns True if scrollbar was clicked.
        """
        if not self.visible:
            return False

        result = self.scrollbar.handle_mouse_down(mouse_pos)
        if result is not None:
            if isinstance(result, float):
                # Track was clicked, jump to position
                scroll_offset_px = int(result * self.max_scroll * ITEM_HEIGHT)
                self.scroll_offset = scroll_offset_px // ITEM_HEIGHT
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            # If result is None, thumb was clicked and drag started automatically
            return True
        return False

    def handle_mouse_up(self):
        """Handle mouse button up event for scrollbar."""
        self.scrollbar.handle_mouse_up()

    def handle_mouse_drag(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion for scrollbar dragging."""
        scroll_offset_px = self.scroll_offset * ITEM_HEIGHT
        max_scroll_px = self.max_scroll * ITEM_HEIGHT
        new_scroll_px = self.scrollbar.handle_mouse_motion(mouse_pos, scroll_offset_px, max_scroll_px)
        if new_scroll_px is not None:
            self.scroll_offset = new_scroll_px // ITEM_HEIGHT
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def _ensure_visible(self, index: int):
        """Ensure the given index is visible in the scrollable area."""
        if not self.window_rect:
            return

        # Calculate content area height
        content_height = self.window_rect.height - 100  # Account for title and padding
        visible_items = content_height // ITEM_HEIGHT

        # Scroll if selected item is out of view
        if index < self.scroll_offset:
            self.scroll_offset = index
        elif index >= self.scroll_offset + visible_items:
            self.scroll_offset = index - visible_items + 1

    def draw(self, surface: pygame.Surface, screen_width: int, screen_height: int):
        """
        Draw the respawn window.

        Args:
            surface: Surface to draw on
            screen_width: Screen width for centering
            screen_height: Screen height for centering
        """
        if not self.visible:
            return

        # Draw semi-transparent overlay (cached for performance)
        if self._overlay_cache is None or self._overlay_cache.get_size() != (screen_width, screen_height):
            self._overlay_cache = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            self._overlay_cache.fill(COLOR_OVERLAY)
        surface.blit(self._overlay_cache, (0, 0))

        # Calculate window position (centered)
        window_x = (screen_width - WINDOW_WIDTH) // 2
        window_y = (screen_height - WINDOW_HEIGHT) // 2
        self.window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Draw window background
        pygame.draw.rect(surface, COLOR_WINDOW_BG, self.window_rect)
        pygame.draw.rect(surface, COLOR_WINDOW_BORDER, self.window_rect, 3)

        # Draw title bar
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 50)
        pygame.draw.rect(surface, COLOR_TITLE_BG, title_rect)
        pygame.draw.line(surface, COLOR_WINDOW_BORDER,
                        (window_x, window_y + 50),
                        (window_x + WINDOW_WIDTH, window_y + 50), 2)

        # Draw title text
        title_text = self.font.render("SELECT UNIT TO RESPAWN", True, COLOR_GOLD)
        title_rect_text = title_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + 25))
        surface.blit(title_text, title_rect_text)

        # Draw unit list
        self._draw_unit_list(surface, window_x, window_y + 60)

        # Draw instructions at bottom
        self._draw_instructions(surface, window_x, window_y + WINDOW_HEIGHT - 40)

    def _draw_unit_list(self, surface: pygame.Surface, x: int, y: int):
        """Draw the scrollable list of dead units."""
        content_height = WINDOW_HEIGHT - 110  # Space for title and instructions
        visible_items = content_height // ITEM_HEIGHT

        self.item_rects = []

        # Draw each visible unit
        for i in range(len(self.dead_units)):
            if i < self.scroll_offset or i >= self.scroll_offset + visible_items:
                continue

            dead_unit = self.dead_units[i]
            item_y = y + (i - self.scroll_offset) * ITEM_HEIGHT
            item_rect = pygame.Rect(x + ITEM_PADDING, item_y,
                                   WINDOW_WIDTH - ITEM_PADDING * 2, ITEM_HEIGHT - 5)

            self.item_rects.append(item_rect)

            # Determine background color
            if i == self.selected_index:
                bg_color = COLOR_SELECTED
            elif i == self.hovered_index:
                bg_color = COLOR_HOVER
            else:
                bg_color = COLOR_WINDOW_BG

            # Draw item background
            pygame.draw.rect(surface, bg_color, item_rect)
            pygame.draw.rect(surface, COLOR_WINDOW_BORDER, item_rect, 2)

            # Draw unit sprite (left side) - get from cache, don't load
            sprite = self.sprite_cache.get(dead_unit.unit_type)
            sprite_x = item_rect.x + 8
            sprite_y = item_rect.y + (ITEM_HEIGHT - 48) // 2  # Center vertically (48px sprite height)

            if sprite:
                surface.blit(sprite, (sprite_x, sprite_y))
                # Add border around sprite
                sprite_rect = pygame.Rect(sprite_x - 1, sprite_y - 1, 50, 50)
                pygame.draw.rect(surface, COLOR_WINDOW_BORDER, sprite_rect, 1)

            # Draw unit info (offset to right of sprite)
            text_x = item_rect.x + 65  # 8 + 48 + 9 spacing
            text_y = item_rect.y + 10

            # Unit name and Greek ID
            name_text = self.font.render(f"{dead_unit.greek_id}", True, COLOR_TEXT)
            surface.blit(name_text, (text_x, text_y))

            # Unit type (smaller text below)
            # Handle both UnitType enum and int (for DLC units)
            unit_type_name = dead_unit.unit_type.name if hasattr(dead_unit.unit_type, 'name') else str(dead_unit.unit_type)
            type_text = self.small_font.render(f"{unit_type_name}", True, COLOR_TEXT_DIM)
            surface.blit(type_text, (text_x, text_y + 22))

            # Respawn timer info (right side)
            if dead_unit.ready_for_respawn:
                status_text = self.small_font.render("READY", True, (100, 255, 100))
            else:
                status_text = self.small_font.render(
                    f"Ready in {dead_unit.respawn_timer} turn{'s' if dead_unit.respawn_timer != 1 else ''}",
                    True, COLOR_INFO
                )
            status_rect = status_text.get_rect(right=item_rect.right - 15, centery=item_rect.centery)
            surface.blit(status_text, status_rect)

        # Draw scrollbar if needed
        visible_items = content_height // ITEM_HEIGHT
        total_height = len(self.dead_units) * ITEM_HEIGHT
        self.max_scroll = max(0, len(self.dead_units) - visible_items)
        if self.max_scroll > 0:
            scrollbar_x = x + WINDOW_WIDTH
            scrollbar_y = y
            # Convert scroll_offset (in items) to pixels
            scroll_offset_px = self.scroll_offset * ITEM_HEIGHT
            max_scroll_px = self.max_scroll * ITEM_HEIGHT
            self.scrollbar.draw(surface, scrollbar_x, scrollbar_y, content_height,
                               scroll_offset_px, max_scroll_px, content_height, total_height)

    def _draw_instructions(self, surface: pygame.Surface, x: int, y: int):
        """Draw control instructions at bottom of window."""
        instructions = [
            "[↑/↓] Navigate",
            "[ENTER] Confirm",
            "[ESC] Cancel"
        ]

        instruction_text = " • ".join(instructions)
        text_surface = self.small_font.render(instruction_text, True, COLOR_TEXT_DIM)
        text_rect = text_surface.get_rect(center=(x + WINDOW_WIDTH // 2, y + 20))
        surface.blit(text_surface, text_rect)
