#!/usr/bin/env python3
"""
Setup Window UI Component
Modal window for selecting unit types during setup phase.
"""
import pygame
from typing import Optional, Tuple
from pathlib import Path
from .font_utils import render_fitted_text
from .scrollbar import Scrollbar
from .menu_components import draw_gradient_rect, draw_glow_rect
from boneglaive.utils.paths import asset_path, load_svg

# Import unit types
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from boneglaive.utils.constants import UnitType, UNIT_STATS, UNIT_DISPLAY_NAMES
from boneglaive.game.recruitment import RECRUITMENT_ORDER

# Colors - Match main menu bone/industrial theme
COLOR_OVERLAY = (0, 0, 0, 180)  # Semi-transparent black overlay
COLOR_WINDOW_BG = (42, 42, 47)  # Match menu panel
COLOR_WINDOW_BG_DARK = (26, 26, 31)  # Darker gradient
COLOR_WINDOW_BORDER = (90, 90, 90)  # Match menu border
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_TEXT_DISABLED = (120, 120, 120)
COLOR_SELECTED = (106, 90, 95)  # Warmer selection (menu hover color)
COLOR_HOVER = (74, 58, 63)  # Warmer hover (menu pressed color)
COLOR_GOLD = (255, 215, 0)
COLOR_INFO = (180, 160, 165)  # Muted bone color
COLOR_MAXED = (80, 40, 40)  # Red tint for maxed units
COLOR_GREEN = (100, 200, 100)
COLOR_BUTTON = (106, 90, 95)  # Match menu hover
COLOR_BUTTON_HOVER = (184, 168, 149)  # Bone color for hover
COLOR_BUTTON_DISABLED = (50, 50, 50)
COLOR_BONE = (224, 213, 197)  # Bone decorations
COLOR_BONE_DARK = (139, 115, 85)  # Bone shadow

# Import scaling utilities
from .scale_utils import scale_manager

# Scale window dimensions based on resolution
WINDOW_WIDTH = scale_manager.scale(550, 'x')  # Increased from 500 to prevent text cutoff
WINDOW_HEIGHT = scale_manager.scale(700, 'y')
ITEM_HEIGHT = scale_manager.scale(55, 'y')
ITEM_PADDING = scale_manager.scale(8)
SCROLL_SPEED = scale_manager.scale(3, 'y')


def draw_bone_corner(surface: pygame.Surface, x: int, y: int, radius: int):
    """Draw a small bone decoration in a corner."""
    # Draw small circle
    pygame.draw.circle(surface, COLOR_BONE_DARK, (x, y), radius)
    pygame.draw.circle(surface, COLOR_BONE, (x, y), radius - 1)


class SetupWindow:
    """Modal window for selecting unit types during setup phase."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False

        # Cache overlay surface (performance)
        self._overlay_cache = None

        # Selectable unit types and display names are derived from the single
        # canonical roster (RECRUITMENT_ORDER) and name table (UNIT_DISPLAY_NAMES)
        # so the setup screen never drifts from the actual recruitment pool.
        self.unit_types = list(RECRUITMENT_ORDER)
        self.unit_names = {ut: UNIT_DISPLAY_NAMES[ut] for ut in RECRUITMENT_ORDER}

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

        # Scrollbar component
        self.scrollbar = Scrollbar()
        self.max_scroll = 0

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

    def get_selected_unit_type(self):
        """Get currently selected unit type."""
        if self.unit_types and 0 <= self.selected_index < len(self.unit_types):
            return self.unit_types[self.selected_index]
        return None

    def is_unit_type_maxed(self, unit_type) -> bool:
        """Check if a unit type has reached the max limit (1)."""
        # Check if placed count >= 1
        return self.unit_counts.get(unit_type, 0) >= 1

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

        try:
            sprite_name = unit_type.name.lower()
        except AttributeError:
            self.sprite_cache[unit_type] = None
            return None

        sprite_path = asset_path(f"graphics/units/{sprite_name}.svg")

        sprite = load_svg(sprite_path, 40, 40)
        self.sprite_cache[unit_type] = sprite
        return sprite

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
        total_height = len(self.unit_types) * (ITEM_HEIGHT + ITEM_PADDING) + ITEM_PADDING
        list_height = WINDOW_HEIGHT - 220

        # Only scroll if content is larger than visible area
        if total_height > list_height:
            # Scroll by one item at a time
            scroll_delta = (ITEM_HEIGHT + ITEM_PADDING) * scroll_amount
            self.scroll_offset = max(0, min(self.scroll_offset - scroll_delta, total_height - list_height))

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
                self.scroll_offset = int(result * self.max_scroll)
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            # If result is None, thumb was clicked and drag started automatically
            return True
        return False

    def handle_mouse_up(self):
        """Handle mouse button up event for scrollbar."""
        self.scrollbar.handle_mouse_up()

    def handle_mouse_drag(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion for scrollbar dragging."""
        new_scroll = self.scrollbar.handle_mouse_motion(mouse_pos, self.scroll_offset, self.max_scroll)
        if new_scroll is not None:
            self.scroll_offset = new_scroll

    def get_display_unit(self) -> Optional[UnitType]:
        """
        Get the unit type that should be displayed in help panel.
        Returns selected unit only (not hovered).
        """
        if 0 <= self.selected_index < len(self.unit_types):
            return self.unit_types[self.selected_index]
        return None

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int, window_x: int = None):
        """
        Draw the setup window.

        Args:
            screen: Pygame screen surface
            screen_width: Screen width
            screen_height: Screen height
            window_x: Optional x position (if None, will be centered with help panel)
        """
        if not self.visible:
            return

        # Draw overlay (cached for performance)
        if self._overlay_cache is None or self._overlay_cache.get_size() != (screen_width, screen_height):
            self._overlay_cache = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            self._overlay_cache.fill(COLOR_OVERLAY)
        screen.blit(self._overlay_cache, (0, 0))

        # Calculate window position (centered with help panel, vertically centered)
        if window_x is None:
            # Calculate centered position
            help_panel_width = scale_manager.scale(550, 'x')
            spacing = scale_manager.scale(30)
            total_width = WINDOW_WIDTH + spacing + help_panel_width
            window_x = (screen_width - total_width) // 2

        window_y = (screen_height - WINDOW_HEIGHT) // 2
        self.window_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Draw window background with gradient effect
        pygame.draw.rect(screen, COLOR_WINDOW_BG, self.window_rect)
        pygame.draw.rect(screen, COLOR_WINDOW_BORDER, self.window_rect, 2)

        # Add bone corner decorations
        padding = 8
        corner_radius = 6
        draw_bone_corner(screen, window_x + padding, window_y + padding, corner_radius)
        draw_bone_corner(screen, window_x + WINDOW_WIDTH - padding, window_y + padding, corner_radius)
        draw_bone_corner(screen, window_x + padding, window_y + WINDOW_HEIGHT - padding, corner_radius)
        draw_bone_corner(screen, window_x + WINDOW_WIDTH - padding, window_y + WINDOW_HEIGHT - padding, corner_radius)

        # Draw title bar
        title_rect = pygame.Rect(window_x, window_y, WINDOW_WIDTH, 60)
        pygame.draw.rect(screen, COLOR_TITLE_BG, title_rect)
        pygame.draw.line(screen, COLOR_WINDOW_BORDER,
                        (window_x, window_y + 60),
                        (window_x + WINDOW_WIDTH, window_y + 60), 2)

        # Draw title with muted bone color for "Select Units", player color for player number
        title_color = (180, 160, 165)  # Muted bone
        player_color = (100, 255, 100) if self.setup_player == 1 else (100, 150, 255)  # Green for P1, Blue for P2

        # Render player number in player color, rest in bone color
        player_text = render_fitted_text(
            f"Player {self.setup_player}",
            max_width=WINDOW_WIDTH - 40,
            max_height=30,
            color=player_color,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )
        select_text = render_fitted_text(
            " - Select Units",
            max_width=WINDOW_WIDTH - 40,
            max_height=30,
            color=title_color,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )

        # Calculate combined width and center
        total_width = player_text.get_width() + select_text.get_width()
        start_x = window_x + (WINDOW_WIDTH - total_width) // 2

        screen.blit(player_text, (start_x, window_y + 12))
        screen.blit(select_text, (start_x + player_text.get_width(), window_y + 12))

        # Draw units remaining
        remaining_text = render_fitted_text(
            f"{self.units_remaining} unit{'s' if self.units_remaining != 1 else ''} remaining",
            max_width=WINDOW_WIDTH - 40,
            max_height=22,
            color=COLOR_INFO,
            base_font_size=16,
            min_font_size=12,
            max_font_size=18
        )
        remaining_rect = remaining_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, window_y + 48))
        screen.blit(remaining_text, remaining_rect)

        # Draw unit list
        list_y = window_y + 80
        list_height = WINDOW_HEIGHT - 220  # Leave room for stats and button

        # Create clip rect for scrolling (scrollbar now outside, so use full width)
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

            # Determine background colors and style (matching main menu buttons)
            if is_maxed:
                bg_top = COLOR_MAXED
                bg_bottom = (60, 30, 30)
                border_color = COLOR_WINDOW_BORDER
                show_glow = False
            elif i == self.selected_index:
                # Selected: use warm hover colors like menu buttons
                bg_top = (106, 90, 95)  # COLOR_BG_HOVER
                bg_bottom = (74, 58, 63)
                border_color = (184, 168, 149)  # COLOR_BORDER_HOVER
                show_glow = True
            elif i == self.hovered_index:
                # Hovered: lighter version
                bg_top = (90, 74, 79)
                bg_bottom = (64, 48, 53)
                border_color = (150, 140, 130)
                show_glow = True
            else:
                # Normal: metal gradient like menu buttons
                bg_top = (74, 74, 79)  # COLOR_METAL
                bg_bottom = (50, 50, 55)  # Darker bottom
                border_color = COLOR_WINDOW_BORDER
                show_glow = False

            # Draw shadow
            shadow_rect = item_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
            screen.blit(shadow_surf, shadow_rect.topleft)

            # Draw gradient background
            draw_gradient_rect(screen, item_rect, bg_top, bg_bottom)

            # Draw glow effect on selected/hover
            if show_glow:
                draw_glow_rect(screen, item_rect, (255, 170, 119), intensity=0.5, width=1)

            # Draw border
            pygame.draw.rect(screen, border_color, item_rect, 2, border_radius=5)

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

            # Draw count (x/1) - only 1 of each unit allowed
            count_color = (255, 100, 100) if is_maxed else COLOR_INFO
            count_text = self.small_font.render(f"({unit_count}/1)", True, count_color)
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

        # Draw scrollbar if needed (positioned outside panel, to the right)
        total_height = len(self.unit_types) * (ITEM_HEIGHT + ITEM_PADDING) + ITEM_PADDING
        self.max_scroll = max(0, total_height - list_height)
        if self.max_scroll > 0:
            scrollbar_x = window_x + WINDOW_WIDTH + scale_manager.scale(5)  # Position outside panel
            scrollbar_y = list_y
            self.scrollbar.draw(screen, scrollbar_x, scrollbar_y, list_height,
                               self.scroll_offset, self.max_scroll, list_height, total_height)

        # Draw confirm button
        self._draw_confirm_button(screen, window_x, window_y)

        # Draw instructions
        instructions_y = window_y + WINDOW_HEIGHT - 30
        instructions = "Click unit to select | Double-click to place | Scroll to navigate"
        instr_text = self.small_font.render(instructions, True, COLOR_TEXT_DIM)
        instr_rect = instr_text.get_rect(center=(window_x + WINDOW_WIDTH // 2, instructions_y))
        screen.blit(instr_text, instr_rect)

    def _draw_confirm_button(self, screen: pygame.Surface, window_x: int, window_y: int):
        """Draw the confirm setup button."""
        button_width = scale_manager.scale(250)  # Wider button
        button_height = scale_manager.scale(50)  # Taller button

        # Calculate position: centered between bottom of unit list and instructions text
        # List ends at: window_y + 80 + (WINDOW_HEIGHT - 220) = window_y + WINDOW_HEIGHT - 140
        list_bottom = window_y + WINDOW_HEIGHT - 140
        instructions_y = window_y + WINDOW_HEIGHT - 30

        # Center button vertically in the gap
        button_y = list_bottom + ((instructions_y - list_bottom - button_height) // 2)

        self.confirm_button_rect = pygame.Rect(
            window_x + WINDOW_WIDTH // 2 - button_width // 2,
            button_y,
            button_width,
            button_height
        )

        # Determine button colors and style (matching main menu)
        if not self.can_confirm:
            bg_top = COLOR_BUTTON_DISABLED
            bg_bottom = COLOR_BUTTON_DISABLED
            border_color = COLOR_WINDOW_BORDER
            text_color = COLOR_TEXT_DISABLED
            show_glow = False
        elif self.hovered_button:
            bg_top = (106, 90, 95)  # COLOR_BG_HOVER
            bg_bottom = (74, 58, 63)
            border_color = (184, 168, 149)  # COLOR_BORDER_HOVER
            text_color = COLOR_TEXT
            show_glow = True
        else:
            bg_top = (74, 74, 79)  # COLOR_METAL
            bg_bottom = (138, 138, 138)  # COLOR_METAL_LIGHT
            border_color = COLOR_WINDOW_BORDER
            text_color = (192, 181, 165)
            show_glow = False

        # Draw shadow
        shadow_rect = self.confirm_button_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Draw gradient background
        draw_gradient_rect(screen, self.confirm_button_rect, bg_top, bg_bottom)

        # Draw glow effect on hover
        if show_glow:
            draw_glow_rect(screen, self.confirm_button_rect, (255, 170, 119), intensity=0.6, width=1)

        # Draw border
        pygame.draw.rect(screen, border_color, self.confirm_button_rect, 2, border_radius=5)

        # Draw button text
        button_text = "Confirm Setup" if self.can_confirm else "Place All Units First"
        text = self.small_font.render(button_text, True, text_color)
        text_rect = text.get_rect(center=self.confirm_button_rect.center)
        screen.blit(text, text_rect)


class SetupPlacementBar:
    """
    Minimized bar shown during unit placement phase of setup.
    Allows player to change unit selection without using ESC key.
    """

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font

        # Button state
        self.hovered_button = False
        self.button_rect = None

        # Bar dimensions (scale with resolution)
        from .scale_utils import scale_manager
        self.bar_height = scale_manager.scale(70, 'y')
        self.button_width = scale_manager.scale(200, 'x')
        self.button_height = scale_manager.scale(40, 'y')

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int, unit_name: str, current_player: int = 1):
        """
        Draw the setup placement bar.

        Args:
            screen: Surface to draw on
            screen_width: Screen width
            screen_height: Screen height
            unit_name: Name of unit being placed
            current_player: Current player (1 or 2) for border color
        """
        # Calculate bar dimensions (fits in center game board area)
        # Use dynamic values from renderer that scale with resolution
        from .scale_utils import scale_manager
        from boneglaive.graphical.renderer import LEFT_PANEL_WIDTH, GAME_BOARD_WIDTH, TOP_BAR_HEIGHT

        # Scale spacing values
        margin = scale_manager.scale(10)
        top_spacing = scale_manager.scale(20, 'y')

        bar_width = GAME_BOARD_WIDTH - margin * 2  # Leave margins on both sides
        bar_x = LEFT_PANEL_WIDTH + margin  # Start after left panel with margin
        bar_y = TOP_BAR_HEIGHT + top_spacing  # Below top bar with spacing
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, self.bar_height)

        # Draw bar background with bone theme
        pygame.draw.rect(screen, COLOR_WINDOW_BG, bar_rect)
        # Border color matches current player (green for P1, blue for P2)
        COLOR_PLAYER1 = (100, 255, 100)  # Green
        COLOR_PLAYER2 = (100, 150, 255)  # Blue
        player_color = COLOR_PLAYER1 if current_player == 1 else COLOR_PLAYER2
        pygame.draw.rect(screen, player_color, bar_rect, 3)

        # Add bone corners to bar (scale decoration sizes)
        corner_padding = scale_manager.scale(8)
        corner_radius = scale_manager.scale(5)
        draw_bone_corner(screen, bar_x + corner_padding, bar_y + corner_padding, corner_radius)
        draw_bone_corner(screen, bar_x + bar_width - corner_padding, bar_y + corner_padding, corner_radius)
        draw_bone_corner(screen, bar_x + corner_padding, bar_y + self.bar_height - corner_padding, corner_radius)
        draw_bone_corner(screen, bar_x + bar_width - corner_padding, bar_y + self.bar_height - corner_padding, corner_radius)

        # Draw text on left side of bar
        text_padding = scale_manager.scale(20)
        text_x = bar_x + text_padding
        text_y = bar_y + (self.bar_height - self.font.get_height()) // 2

        # Title text (use player color)
        placing_text = f"PLACING: {unit_name}"
        placing_surface = self.font.render(placing_text, True, player_color)
        screen.blit(placing_surface, (text_x, text_y))

        # Draw button on right side of bar
        button_padding = scale_manager.scale(20)
        button_x = bar_x + bar_width - self.button_width - button_padding
        button_y = bar_y + (self.bar_height - self.button_height) // 2
        self.button_rect = pygame.Rect(button_x, button_y, self.button_width, self.button_height)

        # Button styling (matching main menu)
        if self.hovered_button:
            bg_top = (106, 90, 95)  # COLOR_BG_HOVER
            bg_bottom = (74, 58, 63)
            border_color = (184, 168, 149)  # COLOR_BORDER_HOVER
            button_text_color = COLOR_TEXT
            show_glow = True
        else:
            bg_top = (74, 74, 79)  # COLOR_METAL
            bg_bottom = (138, 138, 138)  # COLOR_METAL_LIGHT
            border_color = COLOR_WINDOW_BORDER
            button_text_color = (192, 181, 165)
            show_glow = False

        # Draw shadow
        shadow_rect = self.button_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=5)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Draw gradient background
        draw_gradient_rect(screen, self.button_rect, bg_top, bg_bottom)

        # Draw glow effect on hover
        if show_glow:
            draw_glow_rect(screen, self.button_rect, (255, 170, 119), intensity=0.6, width=1)

        # Draw border
        pygame.draw.rect(screen, border_color, self.button_rect, 2)

        # Button text
        button_text = "Change Unit (ESC)"
        button_surface = self.small_font.render(button_text, True, button_text_color)
        button_text_x = button_x + (self.button_width - button_surface.get_width()) // 2
        button_text_y = button_y + (self.button_height - button_surface.get_height()) // 2
        screen.blit(button_surface, (button_text_x, button_text_y))

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion events to update hover state."""
        if self.button_rect:
            self.hovered_button = self.button_rect.collidepoint(mouse_pos)
        else:
            self.hovered_button = False

    def handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click events.

        Args:
            mouse_pos: Mouse position tuple

        Returns:
            "change_unit" if button was clicked, None otherwise
        """
        if self.button_rect and self.button_rect.collidepoint(mouse_pos):
            return "change_unit"
        return None
