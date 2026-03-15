#!/usr/bin/env python3
"""
Help Page UI Component for Graphical Mode
Displays unit help pages with skill icons and status effect icons.
"""
import pygame
import os
from typing import Optional, Dict, List, Tuple
from boneglaive.utils.constants import UnitType
from .scrollbar import Scrollbar

# Colors
COLOR_BG = (25, 28, 32)
COLOR_BG_OVERLAY = (20, 23, 27)
COLOR_BORDER = (80, 84, 92)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (160, 160, 160)
COLOR_HEADING = (255, 200, 100)
COLOR_SKILL_NAME = (100, 200, 255)
COLOR_SEPARATOR = (60, 64, 72)

# Import scaling utilities
from .scale_utils import scale_manager

# Scale layout constants based on resolution
MARGIN = scale_manager.scale(30)
CONTENT_WIDTH = scale_manager.scale(700, 'x')
ICON_SIZE = scale_manager.scale(40, 'uniform')
LINE_SPACING = scale_manager.scale(24, 'y')
PARAGRAPH_SPACING = scale_manager.scale(12, 'y')
SECTION_SPACING = scale_manager.scale(20, 'y')


class HelpPage:
    """Help page component showing unit information with icons."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False
        self.scroll_offset = 0
        self.max_scroll = 0
        self.unit_type = None
        self.content_surface = None
        self.icon_cache: Dict[str, pygame.Surface] = {}

        # Scrollbar component
        self.scrollbar = Scrollbar()

        # Load unit help data from ASCII help component
        self.unit_help_data = self._load_unit_help_data()

    def _load_unit_help_data(self):
        """Load unit help data - reuses data from ASCII help component."""
        # Import here to avoid circular dependency
        from boneglaive.ui.ui_components import UnitHelpComponent

        # Create a dummy component just to get the help data
        class DummyRenderer:
            pass
        class DummyUI:
            pass

        dummy_component = UnitHelpComponent(DummyRenderer(), DummyUI())
        return dummy_component.unit_help_data

    def _load_icon(self, icon_name: str, icon_type: str = "skill") -> Optional[pygame.Surface]:
        """
        Load an icon from file (skill or status effect).

        Args:
            icon_name: Name of the icon file (without extension)
            icon_type: "skill" or "status"
        """
        cache_key = f"{icon_type}_{icon_name}"

        # Check cache
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        # Determine path based on type
        if icon_type == "skill":
            icon_path = f"graphics/skill_icons/{icon_name}.svg"
        else:  # status
            icon_path = f"graphics/status_icons/{icon_name}.svg"

        if not os.path.exists(icon_path):
            return None

        try:
            # Try SVG first
            import cairosvg
            from io import BytesIO
            png_data = cairosvg.svg2png(url=icon_path, output_width=ICON_SIZE, output_height=ICON_SIZE)
            icon_surface = pygame.image.load(BytesIO(png_data))
            icon_surface = icon_surface.convert_alpha()
            self.icon_cache[cache_key] = icon_surface
            return icon_surface
        except ImportError:
            pass
        except Exception:
            pass

        # Try PNG fallback
        png_path = icon_path.replace('.svg', '.png')
        if os.path.exists(png_path):
            try:
                icon_surface = pygame.image.load(png_path)
                icon_surface = pygame.transform.scale(icon_surface, (ICON_SIZE, ICON_SIZE))
                icon_surface = icon_surface.convert_alpha()
                self.icon_cache[cache_key] = icon_surface
                return icon_surface
            except Exception:
                pass

        return None

    def _wrap_text(self, text: str, max_width: int, font) -> List[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = font.render(test_line, True, COLOR_TEXT)

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def _render_content(self):
        """Render the help page content to a surface."""
        if not self.unit_type or self.unit_type not in self.unit_help_data:
            return

        unit_data = self.unit_help_data[self.unit_type]

        # Estimate height needed - increased to handle units with many skills
        estimated_height = 4000  # Generous estimate to prevent cutoff
        self.content_surface = pygame.Surface((CONTENT_WIDTH, estimated_height), pygame.SRCALPHA)

        y = 0

        # Title
        title_text = self.font.render(unit_data['title'], True, COLOR_HEADING)
        self.content_surface.blit(title_text, (0, y))
        y += title_text.get_height() + SECTION_SPACING

        # Overview
        for line in unit_data['overview']:
            if line:
                wrapped_lines = self._wrap_text(line, CONTENT_WIDTH, self.small_font)
                for wrapped in wrapped_lines:
                    text_surface = self.small_font.render(wrapped, True, COLOR_TEXT)
                    self.content_surface.blit(text_surface, (0, y))
                    y += text_surface.get_height() + 8
            else:
                y += PARAGRAPH_SPACING

        y += SECTION_SPACING

        # Stats
        stats_heading = self.font.render("BASE STATS", True, COLOR_HEADING)
        self.content_surface.blit(stats_heading, (0, y))
        y += stats_heading.get_height() + 12

        for stat in unit_data['stats']:
            stat_text = self.small_font.render(stat, True, COLOR_TEXT_DIM)
            self.content_surface.blit(stat_text, (10, y))
            y += stat_text.get_height() + 8

        y += SECTION_SPACING

        # Separator
        pygame.draw.line(self.content_surface, COLOR_SEPARATOR, (0, y), (CONTENT_WIDTH, y), 2)
        y += SECTION_SPACING

        # Skills
        skills_heading = self.font.render("SKILLS", True, COLOR_HEADING)
        self.content_surface.blit(skills_heading, (0, y))
        y += skills_heading.get_height() + 12

        for skill in unit_data['skills']:
            # Skill name with icon
            skill_name_text = self.font.render(skill['name'], True, COLOR_SKILL_NAME)

            # Try to load skill icon
            # Extract skill name without (Passive/Active) and [Key: X]
            skill_icon_name = skill['name'].split(' (')[0].lower().replace(' ', '_')
            skill_icon = self._load_icon(skill_icon_name, "skill")

            if skill_icon:
                self.content_surface.blit(skill_icon, (0, y))
                self.content_surface.blit(skill_name_text, (ICON_SIZE + 10, y + (ICON_SIZE - skill_name_text.get_height()) // 2))
                y += max(ICON_SIZE, skill_name_text.get_height()) + 10
            else:
                self.content_surface.blit(skill_name_text, (0, y))
                y += skill_name_text.get_height() + 10

            # Description
            wrapped_desc = self._wrap_text(skill['description'], CONTENT_WIDTH - 20, self.small_font)
            for wrapped in wrapped_desc:
                desc_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                self.content_surface.blit(desc_text, (10, y))
                y += desc_text.get_height() + 8

            y += 8

            # Details
            for detail in skill['details']:
                # Check if this detail mentions a status effect icon
                detail_text = self.small_font.render(f"  • {detail}", True, COLOR_TEXT_DIM)
                self.content_surface.blit(detail_text, (20, y))
                y += detail_text.get_height() + 8

            y += SECTION_SPACING

        # Separator
        pygame.draw.line(self.content_surface, COLOR_SEPARATOR, (0, y), (CONTENT_WIDTH, y), 2)
        y += SECTION_SPACING

        # Tips
        tips_heading = self.font.render("COMBAT TIPS", True, COLOR_HEADING)
        self.content_surface.blit(tips_heading, (0, y))
        y += tips_heading.get_height() + 12

        for tip in unit_data['tips']:
            wrapped_tip = self._wrap_text(tip, CONTENT_WIDTH - 20, self.small_font)
            for wrapped in wrapped_tip:
                tip_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                self.content_surface.blit(tip_text, (10, y))
                y += tip_text.get_height() + 8

        y += SECTION_SPACING

        # Tactical
        tactical_heading = self.font.render("TACTICAL NOTES", True, COLOR_HEADING)
        self.content_surface.blit(tactical_heading, (0, y))
        y += tactical_heading.get_height() + 12

        for note in unit_data['tactical']:
            wrapped_note = self._wrap_text(note, CONTENT_WIDTH - 20, self.small_font)
            for wrapped in wrapped_note:
                note_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                self.content_surface.blit(note_text, (10, y))
                y += note_text.get_height() + 8

        # Trim surface to actual height
        actual_height = y + MARGIN
        trimmed_surface = pygame.Surface((CONTENT_WIDTH, actual_height), pygame.SRCALPHA)
        trimmed_surface.blit(self.content_surface, (0, 0))
        self.content_surface = trimmed_surface

    def show(self, unit_type: UnitType):
        """Show help page for the given unit type."""
        self.unit_type = unit_type
        self.scroll_offset = 0
        self.visible = True
        self._render_content()

    def hide(self):
        """Hide the help page."""
        self.visible = False
        self.unit_type = None
        self.content_surface = None

    def handle_scroll(self, direction: int):
        """Handle scrolling (direction: -1 for up, 1 for down)."""
        if not self.content_surface:
            return

        scroll_speed = 30
        self.scroll_offset += direction * scroll_speed
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def handle_mouse_down(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle mouse button down event.
        Returns True if the event was handled (clicked on scrollbar).
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
        """Handle mouse button up event."""
        self.scrollbar.handle_mouse_up()

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion for scrollbar dragging."""
        new_scroll = self.scrollbar.handle_mouse_motion(mouse_pos, self.scroll_offset, self.max_scroll)
        if new_scroll is not None:
            self.scroll_offset = new_scroll

    def draw(self, surface: pygame.Surface, screen_width: int, screen_height: int):
        """Draw the help page."""
        if not self.visible or not self.content_surface:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((*COLOR_BG_OVERLAY, 220))
        surface.blit(overlay, (0, 0))

        # Help panel dimensions
        panel_width = CONTENT_WIDTH + 2 * MARGIN
        panel_height = screen_height - 100
        panel_x = (screen_width - panel_width) // 2
        panel_y = 50

        # Calculate max scroll
        content_height = self.content_surface.get_height()
        visible_height = panel_height - 2 * MARGIN - 60  # Space for title and instructions
        self.max_scroll = max(0, content_height - visible_height)

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, COLOR_BG, panel_rect)
        pygame.draw.rect(surface, COLOR_BORDER, panel_rect, 3)

        # Draw title bar
        title_bar_rect = pygame.Rect(panel_x, panel_y, panel_width, 50)
        pygame.draw.rect(surface, (40, 44, 52), title_bar_rect)
        pygame.draw.line(surface, COLOR_BORDER, (panel_x, panel_y + 50), (panel_x + panel_width, panel_y + 50), 2)

        title = self.font.render("UNIT HELP", True, COLOR_HEADING)
        surface.blit(title, (panel_x + 20, panel_y + 15))

        # Draw close instruction
        close_text = self.small_font.render("[ESC] Close  [↑/↓] Scroll", True, COLOR_TEXT_DIM)
        surface.blit(close_text, (panel_x + panel_width - close_text.get_width() - 20, panel_y + 18))

        # Set up clipping region for scrollable content
        content_rect = pygame.Rect(panel_x + MARGIN, panel_y + 60, CONTENT_WIDTH, visible_height)
        surface.set_clip(content_rect)

        # Draw content with scroll offset
        if self.content_surface:
            surface.blit(self.content_surface, (panel_x + MARGIN, panel_y + 60 - self.scroll_offset))

        # Clear clipping
        surface.set_clip(None)

        # Draw scrollbar if needed
        scroll_bar_height = visible_height - 20
        scroll_bar_y = panel_y + 70
        scrollbar_x = panel_x + panel_width
        self.scrollbar.draw(surface, scrollbar_x, scroll_bar_y, scroll_bar_height,
                           self.scroll_offset, self.max_scroll, visible_height, content_height)
