#!/usr/bin/env python3
"""
Setup Window UI Component
Modal window for selecting unit types during setup phase.
"""
import pygame
from typing import Optional, List, Tuple
from pathlib import Path

# Import unit types
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from boneglaive.utils.constants import UnitType, UNIT_STATS

# Colors - Match respawn window style
COLOR_OVERLAY = (0, 0, 0, 180)  # Semi-transparent black overlay
COLOR_WINDOW_BG = (30, 34, 42)
COLOR_WINDOW_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_TEXT_DISABLED = (100, 100, 100)
COLOR_SELECTED = (60, 100, 140)
COLOR_HOVER = (50, 54, 62)
COLOR_GOLD = (255, 215, 0)
COLOR_INFO = (180, 200, 220)
COLOR_MAXED = (80, 40, 40)  # Red tint for maxed units
COLOR_GREEN = (100, 200, 100)
COLOR_BUTTON = (70, 110, 150)
COLOR_BUTTON_HOVER = (90, 130, 170)
COLOR_BUTTON_DISABLED = (50, 50, 50)

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 700
ITEM_HEIGHT = 55
ITEM_PADDING = 8
SCROLL_SPEED = 3


class SetupWindow:
    """Modal window for selecting unit types during setup phase."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False

        # Unit types in order
        self.unit_types = [
            UnitType.GLAIVEMAN,
            UnitType.MANDIBLE_FOREMAN,
            UnitType.GRAYMAN,
            UnitType.MARROW_CONDENSER,
            UnitType.FOWL_CONTRIVANCE,
            UnitType.GAS_MACHINIST,
            UnitType.DELPHIC_APPRAISER,
            UnitType.INTERFERER,
            UnitType.DERELICTIONIST,
            UnitType.POTPOURRIST
        ]

        # Unit display names
        self.unit_names = {
            UnitType.GLAIVEMAN: "GLAIVEMAN",
            UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
            UnitType.GRAYMAN: "GRAYMAN",
            UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
            UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
            UnitType.GAS_MACHINIST: "GAS MACHINIST",
            UnitType.DELPHIC_APPRAISER: "DELPHIC APPRAISER",
            UnitType.INTERFERER: "INTERFERER",
            UnitType.DERELICTIONIST: "DERELICTIONIST",
            UnitType.POTPOURRIST: "POTPOURRIST"
        }

        # State
        self.selected_index = 0
        self.hovered_index = None
        self.hovered_button = False
        self.scroll_offset = 0
        self.units_remaining = 3
        self.unit_counts = {}  # {UnitType: count} - how many placed
        self.setup_player = 1
        self.can_confirm = False

        # Calculated positions
        self.window_rect = None
        self.item_rects = []
        self.confirm_button_rect = None

        # Unit sprite cache
        self.sprite_cache = {}  # {unit_type: pygame.Surface}

    def show(self, setup_player: int, units_remaining: int, unit_counts: dict):
        """
        Show the setup window.

        Args:
            setup_player: Player number (1 or 2)
            units_remaining: How many units left to place
            unit_counts: Dict of {UnitType: count} showing how many of each type placed
        """
        self.visible = True
        self.setup_player = setup_player
        self.units_remaining = units_remaining
        self.unit_counts = unit_counts.copy()
        self.selected_index = 0
        self.scroll_offset = 0
        self.hovered_index = None
        self.can_confirm = (units_remaining == 0)

        # Pre-load sprites for all units
        for unit_type in self.unit_types:
            if unit_type not in self.sprite_cache:
                self._load_unit_sprite(unit_type)

    def hide(self):
        """Hide the setup window."""
        self.visible = False
        self.selected_index = 0

    def update_state(self, units_remaining: int, unit_counts: dict):
        """Update the window state with current placement info."""
        self.units_remaining = units_remaining
        self.unit_counts = unit_counts.copy()
        self.can_confirm = (units_remaining == 0)

    def select_next(self):
        """Select next unit type in list."""
        if self.unit_types:
            self.selected_index = (self.selected_index + 1) % len(self.unit_types)
            self._ensure_visible(self.selected_index)

    def select_prev(self):
        """Select previous unit type in list."""
        if self.unit_types:
            self.selected_index = (self.selected_index - 1) % len(self.unit_types)
            self._ensure_visible(self.selected_index)

    def get_selected_unit_type(self):
        """Get currently selected unit type."""
        if self.unit_types and 0 <= self.selected_index < len(self.unit_types):
            return self.unit_types[self.selected_index]
        return None

    def is_unit_type_maxed(self, unit_type: UnitType) -> bool:
        """Check if a unit type has reached the max limit (2)."""
        return self.unit_counts.get(unit_type, 0) >= 2

    def _load_unit_sprite(self, unit_type: UnitType):
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
        sprite_name = unit_type.name.lower()
        sprite_path = f"graphics/units/{sprite_name}.svg"

        try:
            import cairosvg
            import io

            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=sprite_path, output_width=40, output_height=40)

            # Load PNG data into pygame surface
            png_bytes = io.BytesIO(png_data)
            sprite = pygame.image.load(png_bytes)

            # Cache the sprite
            self.sprite_cache[unit_type] = sprite
            return sprite

        except Exception as e:
            print(f"[SetupWindow] Could not load sprite for {unit_type.name}: {e}")
            # Cache None to avoid repeated attempts
            self.sprite_cache[unit_type] = None
            return None

    def _ensure_visible(self, index: int):
        """Ensure the item at index is visible in the scroll view."""
        if not self.window_rect:
            return

        # Calculate item position
        item_y = index * (ITEM_HEIGHT + ITEM_PADDING)

        # Get visible area (excluding header and footer)
        list_start = 80  # After header
        list_height = WINDOW_HEIGHT - 200  # Room for header + stats + button

        # Check if item is above visible area
        if item_y < self.scroll_offset:
            self.scroll_offset = item_y

        # Check if item is below visible area
        if item_y + ITEM_HEIGHT > self.scroll_offset + list_height:
            self.scroll_offset = item_y + ITEM_HEIGHT - list_height

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Update hovered item based on mouse position."""
        if not self.visible:
            return

        self.hovered_index = None
        self.hovered_button = False

        # Check items
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_index = i
                break

        # Check confirm button
        if self.confirm_button_rect and self.confirm_button_rect.collidepoint(mouse_pos):
            self.hovered_button = True

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Tuple[bool, bool, Optional[UnitType]]:
        """
        Handle mouse click.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            Tuple of (unit_selected, confirm_clicked, unit_type_to_place)
            - unit_selected: True if a unit was clicked and selected
            - confirm_clicked: True if confirm button was clicked
            - unit_type_to_place: UnitType if user double-clicked/wants to place immediately, else None
        """
        if not self.visible:
            return (False, False, None)

        # Check item clicks
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                unit_type = self.unit_types[i]
                # Don't allow selecting maxed units
                if not self.is_unit_type_maxed(unit_type):
                    # If clicking already selected unit, start placement immediately
                    if self.selected_index == i:
                        return (True, False, unit_type)
                    else:
                        # Just select the unit
                        self.selected_index = i
                        return (True, False, None)

        # Check confirm button click
        if self.confirm_button_rect and self.confirm_button_rect.collidepoint(mouse_pos):
            if self.can_confirm:
                return (False, True, None)

        return (False, False, None)

    def handle_scroll(self, scroll_amount: int):
        """
        Handle mouse wheel scroll.

        Args:
            scroll_amount: Positive for scroll up, negative for scroll down
        """
        if not self.visible:
            return

        # Calculate total scrollable height
        total_height = len(self.unit_types) * (ITEM_HEIGHT + ITEM_PADDING)
        list_height = WINDOW_HEIGHT - 200

        # Only scroll if content is larger than visible area
        if total_height > list_height:
            # Scroll by one item at a time
            scroll_delta = (ITEM_HEIGHT + ITEM_PADDING) * scroll_amount
            self.scroll_offset = max(0, min(self.scroll_offset - scroll_delta, total_height - list_height))

    def get_display_unit(self) -> Optional[UnitType]:
        """
        Get the unit type that should be displayed in help panel.
        Returns selected unit only (not hovered).
        """
        if 0 <= self.selected_index < len(self.unit_types):
            return self.unit_types[self.selected_index]
        return None

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """
        Draw the setup window.

        Args:
            screen: Pygame screen surface
            screen_width: Screen width
            screen_height: Screen height
        """
        if not self.visible:
            return

        # Draw overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        screen.blit(overlay, (0, 0))

        # Calculate window position (left side, vertically centered)
        window_x = 100  # Position on left side
        window_y = (screen_height - WINDOW_HEIGHT) // 2
        self.window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Draw window background
        pygame.draw.rect(screen, COLOR_WINDOW_BG, self.window_rect)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, self.window_rect, 2)

        # Draw title bar
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 60)
        pygame.draw.rect(screen, COLOR_TITLE_BG, title_rect)
        pygame.draw.line(screen, COLOR_WINDOW_BORDER,
                        (window_x, window_y + 60),
                        (window_x + WINDOW_WIDTH, window_y + 60), 2)

        # Draw title
        player_color = COLOR_GOLD if self.setup_player == 1 else (100, 200, 255)
        title_text = self.font.render(f"Player {self.setup_player} - Select Units", True, player_color)
        title_rect_center = title_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + 25))
        screen.blit(title_text, title_rect_center)

        # Draw units remaining
        remaining_text = self.small_font.render(
            f"{self.units_remaining} unit{'s' if self.units_remaining != 1 else ''} remaining",
            True, COLOR_INFO
        )
        remaining_rect = remaining_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + 48))
        screen.blit(remaining_text, remaining_rect)

        # Draw unit list
        list_y = window_y + 80
        list_height = WINDOW_HEIGHT - 220  # Leave room for stats and button

        # Create clip rect for scrolling
        clip_rect = pygame.Rect(window_x + 10, list_y, WINDOW_WIDTH - 20, list_height)
        screen.set_clip(clip_rect)

        self.item_rects = []
        for i, unit_type in enumerate(self.unit_types):
            item_y = list_y + i * (ITEM_HEIGHT + ITEM_PADDING) - self.scroll_offset

            # Skip if not visible
            if item_y + ITEM_HEIGHT < list_y or item_y > list_y + list_height:
                self.item_rects.append(pygame.Rect(0, 0, 0, 0))
                continue

            item_rect = pygame.Rect(window_x + 15, item_y, WINDOW_WIDTH - 30, ITEM_HEIGHT)
            self.item_rects.append(item_rect)

            # Check if maxed
            is_maxed = self.is_unit_type_maxed(unit_type)
            unit_count = self.unit_counts.get(unit_type, 0)

            # Determine background color
            if is_maxed:
                bg_color = COLOR_MAXED
            elif i == self.selected_index:
                bg_color = COLOR_SELECTED
            elif i == self.hovered_index:
                bg_color = COLOR_HOVER
            else:
                bg_color = (40, 44, 52)

            # Draw item background
            pygame.draw.rect(screen, bg_color, item_rect, border_radius=5)
            pygame.draw.rect(screen, COLOR_WINDOW_BORDER, item_rect, 1, border_radius=5)

            # Draw sprite
            sprite = self.sprite_cache.get(unit_type)
            if sprite:
                sprite_rect = sprite.get_rect(midleft=(item_rect.left + 10, item_rect.centery))
                screen.blit(sprite, sprite_rect)

            # Draw unit name
            text_color = COLOR_TEXT_DISABLED if is_maxed else COLOR_TEXT
            name_text = self.small_font.render(self.unit_names[unit_type], True, text_color)
            name_rect = name_text.get_rect(midleft=(item_rect.left + 60, item_rect.centery - 10))
            screen.blit(name_text, name_rect)

            # Draw count (x/2)
            count_color = (255, 100, 100) if is_maxed else COLOR_INFO
            count_text = self.small_font.render(f"({unit_count}/2)", True, count_color)
            count_rect = count_text.get_rect(midright=(item_rect.right - 10, item_rect.centery - 10))
            screen.blit(count_text, count_rect)

            # Draw stats for this unit
            hp, atk, defense, move_range, attack_range = UNIT_STATS[unit_type]
            stats_text = self.small_font.render(
                f"HP:{hp} ATK:{atk} DEF:{defense} MV:{move_range} RNG:{attack_range}",
                True, text_color
            )
            stats_rect = stats_text.get_rect(midleft=(item_rect.left + 60, item_rect.centery + 12))
            screen.blit(stats_text, stats_rect)

        # Remove clipping
        screen.set_clip(None)

        # Draw selected unit stats in detail
        self._draw_selected_stats(screen, window_x, window_y)

        # Draw confirm button
        self._draw_confirm_button(screen, window_x, window_y)

        # Draw instructions
        instructions_y = window_y + WINDOW_HEIGHT - 30
        instructions = "Click unit to select | Double-click to place | Scroll to navigate"
        instr_text = self.small_font.render(instructions, True, COLOR_TEXT_DIM)
        instr_rect = instr_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, instructions_y))
        screen.blit(instr_text, instr_rect)

    def _draw_selected_stats(self, screen: pygame.Surface, window_x: int, window_y: int):
        """Draw detailed stats for selected unit."""
        if not (0 <= self.selected_index < len(self.unit_types)):
            return

        unit_type = self.unit_types[self.selected_index]
        hp, atk, defense, move_range, attack_range = UNIT_STATS[unit_type]

        # Stats area
        stats_y = window_y + WINDOW_HEIGHT - 140
        stats_rect = pygame.Rect(window_x + 15, stats_y, WINDOW_WIDTH - 30, 60)
        pygame.draw.rect(screen, COLOR_TITLE_BG, stats_rect, border_radius=5)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, stats_rect, 1, border_radius=5)

        # Draw "Selected:" label
        label_text = self.small_font.render("Selected:", True, COLOR_INFO)
        screen.blit(label_text, (stats_rect.left + 10, stats_rect.top + 5))

        # Draw unit name
        name_text = self.small_font.render(self.unit_names[unit_type], True, COLOR_GOLD)
        screen.blit(name_text, (stats_rect.left + 10, stats_rect.top + 25))

        # Draw stats on second line
        stats_lines = [
            f"HP: {hp}",
            f"ATK: {atk}",
            f"DEF: {defense}",
            f"Move: {move_range}",
            f"Range: {attack_range}"
        ]

        x_offset = stats_rect.left + 10
        for stat in stats_lines:
            stat_text = self.small_font.render(stat, True, COLOR_TEXT)
            screen.blit(stat_text, (x_offset, stats_rect.top + 43))
            x_offset += stat_text.get_width() + 15

    def _draw_confirm_button(self, screen: pygame.Surface, window_x: int, window_y: int):
        """Draw the confirm setup button."""
        button_y = window_y + WINDOW_HEIGHT - 70
        self.confirm_button_rect = pygame.Rect(
            window_x + WINDOW_WIDTH // 2 - 100,
            button_y,
            200,
            35
        )

        # Determine button color
        if not self.can_confirm:
            bg_color = COLOR_BUTTON_DISABLED
            text_color = COLOR_TEXT_DISABLED
        elif self.hovered_button:
            bg_color = COLOR_BUTTON_HOVER
            text_color = COLOR_TEXT
        else:
            bg_color = COLOR_BUTTON
            text_color = COLOR_TEXT

        # Draw button
        pygame.draw.rect(screen, bg_color, self.confirm_button_rect, border_radius=5)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, self.confirm_button_rect, 2, border_radius=5)

        # Draw button text
        button_text = "Confirm Setup" if self.can_confirm else "Place All Units First"
        text = self.small_font.render(button_text, True, text_color)
        text_rect = text.get_rect(center=self.confirm_button_rect.center)
        screen.blit(text, text_rect)
