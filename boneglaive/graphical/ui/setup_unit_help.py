#!/usr/bin/env python3
"""
Setup Unit Help Panel
Side panel showing detailed unit information during setup phase.
"""
import pygame
from typing import Optional, Tuple
from pathlib import Path
import sys

# Import unit types and skills
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from boneglaive.utils.constants import UnitType, UNIT_STATS

# Colors
COLOR_BG = (30, 34, 42)
COLOR_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_GOLD = (255, 215, 0)
COLOR_SECTION = (50, 54, 62)


class SetupUnitHelp:
    """Help panel showing unit details during setup."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.unit_type = None
        self.scroll_offset = 0
        self.max_scroll = 0
        self.content_surface = None
        self.has_focus = False

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

        # Sprite cache
        self.sprite_cache = {}

        # Skill icon cache
        self.skill_icon_cache = {}

        # Load unit help data from ASCII help component
        self.unit_help_data = self._load_unit_help_data()

    def _load_unit_help_data(self):
        """Load unit help data - reuses data from ASCII help component."""
        from boneglaive.ui.ui_components import UnitHelpComponent

        # Create a dummy component just to get the help data
        class DummyRenderer:
            pass
        class DummyUI:
            pass

        dummy_component = UnitHelpComponent(DummyRenderer(), DummyUI())
        return dummy_component.unit_help_data

    def update(self, unit_type: Optional[UnitType]):
        """Update the displayed unit type."""
        if unit_type != self.unit_type:
            self.unit_type = unit_type
            self.scroll_offset = 0
            self.content_surface = None

    def handle_click(self, mouse_pos: Tuple[int, int], panel_rect: pygame.Rect) -> bool:
        """
        Handle click on the help panel.
        Returns True if click was inside the panel.
        """
        return panel_rect.collidepoint(mouse_pos)

    def handle_scroll(self, scroll_amount: int):
        """
        Handle mouse wheel scroll.

        Args:
            scroll_amount: Positive for scroll up, negative for scroll down
        """
        if self.content_surface:
            scroll_delta = 30 * scroll_amount
            self.scroll_offset = max(0, min(self.scroll_offset - scroll_delta, self.max_scroll))

    def _load_unit_sprite(self, unit_type: UnitType) -> Optional[pygame.Surface]:
        """Load unit sprite from SVG."""
        if unit_type in self.sprite_cache:
            return self.sprite_cache[unit_type]

        sprite_name = unit_type.name.lower()
        sprite_path = f"graphics/units/{sprite_name}.svg"

        try:
            import cairosvg
            import io
            png_data = cairosvg.svg2png(url=sprite_path, output_width=80, output_height=80)
            png_bytes = io.BytesIO(png_data)
            sprite = pygame.image.load(png_bytes)
            self.sprite_cache[unit_type] = sprite
            return sprite
        except Exception as e:
            print(f"[SetupUnitHelp] Could not load sprite for {unit_type.name}: {e}")
            self.sprite_cache[unit_type] = None
            return None

    def _load_skill_icon(self, skill_name: str) -> Optional[pygame.Surface]:
        """Load skill icon from SVG."""
        if skill_name in self.skill_icon_cache:
            return self.skill_icon_cache[skill_name]

        # Convert skill name to filename
        icon_name = skill_name.lower().replace(' ', '_').replace('-', '_')
        icon_path = f"graphics/skill_icons/{icon_name}.svg"

        try:
            import cairosvg
            import io
            png_data = cairosvg.svg2png(url=icon_path, output_width=32, output_height=32)
            png_bytes = io.BytesIO(png_data)
            icon = pygame.image.load(png_bytes)
            self.skill_icon_cache[skill_name] = icon
            return icon
        except Exception as e:
            # Silently fail for missing icons
            self.skill_icon_cache[skill_name] = None
            return None

    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> list:
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, COLOR_TEXT)

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else ['']

    def _render_content(self, width: int):
        """Render help content to a surface."""
        if not self.unit_type or self.unit_type not in self.unit_help_data:
            return None

        unit_data = self.unit_help_data[self.unit_type]

        # Estimate content height
        estimated_height = 2500
        content_surface = pygame.Surface((width, estimated_height), pygame.SRCALPHA)
        content_width = width - 30
        current_y = 0

        # Draw unit sprite (centered at top)
        sprite = self._load_unit_sprite(self.unit_type)
        if sprite:
            sprite_rect = sprite.get_rect(center=(width // 2, current_y + 40))
            content_surface.blit(sprite, sprite_rect)
        current_y += 90

        # Draw unit title
        title_text = self.font.render(unit_data['title'], True, COLOR_GOLD)
        title_rect = title_text.get_rect(center=(width // 2, current_y))
        content_surface.blit(title_text, title_rect)
        current_y += 30

        # Draw overview
        for line in unit_data.get('overview', []):
            if line:
                wrapped_lines = self._wrap_text(line, content_width, self.small_font)
                for wrapped in wrapped_lines:
                    text_surface = self.small_font.render(wrapped, True, COLOR_TEXT_DIM)
                    content_surface.blit(text_surface, (15, current_y))
                    current_y += 18
            else:
                current_y += 10
        current_y += 15

        # Draw stats
        stats_heading = self.font.render("BASE STATS", True, COLOR_GOLD)
        content_surface.blit(stats_heading, (15, current_y))
        current_y += 25

        for stat in unit_data.get('stats', []):
            stat_text = self.small_font.render(stat, True, COLOR_TEXT_DIM)
            content_surface.blit(stat_text, (20, current_y))
            current_y += 18

        current_y += 20

        # Draw separator
        pygame.draw.line(content_surface, COLOR_BORDER, (10, current_y), (width - 10, current_y), 2)
        current_y += 20

        # Draw skills
        skills_heading = self.font.render("SKILLS", True, COLOR_GOLD)
        content_surface.blit(skills_heading, (15, current_y))
        current_y += 25

        for skill_data in unit_data.get('skills', []):
            # Skill name and icon
            skill_name = skill_data['name']
            # Extract skill name without (Passive/Active) and [Key: X]
            skill_icon_name = skill_name.split(' (')[0]
            skill_icon = self._load_skill_icon(skill_icon_name)

            icon_x = 20
            if skill_icon:
                content_surface.blit(skill_icon, (icon_x, current_y))
                icon_x += 38

            skill_name_text = self.font.render(skill_name, True, (100, 200, 255))
            content_surface.blit(skill_name_text, (icon_x, current_y + 5))
            current_y += 35

            # Skill description
            desc = skill_data.get('description', '')
            desc_lines = self._wrap_text(desc, content_width - 10, self.small_font)
            for line in desc_lines:
                desc_text = self.small_font.render(line, True, COLOR_TEXT)
                content_surface.blit(desc_text, (25, current_y))
                current_y += 18

            current_y += 5

            # Skill details (bullets)
            for detail in skill_data.get('details', []):
                detail_text = self.small_font.render(f"  • {detail}", True, COLOR_TEXT_DIM)
                content_surface.blit(detail_text, (30, current_y))
                current_y += 18

            current_y += 15

        # Draw separator
        pygame.draw.line(content_surface, COLOR_BORDER, (10, current_y), (width - 10, current_y), 2)
        current_y += 20

        # Draw combat tips
        if 'tips' in unit_data and unit_data['tips']:
            tips_heading = self.font.render("COMBAT TIPS", True, COLOR_GOLD)
            content_surface.blit(tips_heading, (15, current_y))
            current_y += 25

            for tip in unit_data['tips']:
                wrapped_tip = self._wrap_text(tip, content_width - 10, self.small_font)
                for wrapped in wrapped_tip:
                    tip_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                    content_surface.blit(tip_text, (20, current_y))
                    current_y += 18
                current_y += 5

            current_y += 15

        # Draw tactical notes
        if 'tactical' in unit_data and unit_data['tactical']:
            tactical_heading = self.font.render("TACTICAL NOTES", True, COLOR_GOLD)
            content_surface.blit(tactical_heading, (15, current_y))
            current_y += 25

            for note in unit_data['tactical']:
                wrapped_note = self._wrap_text(note, content_width - 10, self.small_font)
                for wrapped in wrapped_note:
                    note_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                    content_surface.blit(note_text, (20, current_y))
                    current_y += 18
                current_y += 5

        # Trim to actual height
        actual_height = current_y + 20
        trimmed_surface = pygame.Surface((width, actual_height), pygame.SRCALPHA)
        trimmed_surface.blit(content_surface, (0, 0))

        return trimmed_surface

    def draw(self, screen: pygame.Surface, x: int, y: int, width: int, height: int) -> pygame.Rect:
        """
        Draw the help panel.

        Args:
            screen: Pygame screen surface
            x, y: Position (top-left)
            width, height: Panel dimensions

        Returns:
            Panel rectangle for click detection
        """
        # Always draw the panel background
        panel_rect = pygame.Rect(x, y, width, height)

        # Highlight border if focused
        border_color = (150, 200, 255) if self.has_focus else COLOR_BORDER
        pygame.draw.rect(screen, COLOR_BG, panel_rect)
        pygame.draw.rect(screen, border_color, panel_rect, 2)

        if not self.unit_type:
            # Show "Click a unit" message
            no_unit_text = self.font.render("Click a unit to view details", True, COLOR_TEXT_DIM)
            no_unit_rect = no_unit_text.get_rect(center=(x + width // 2, y + height // 2))
            screen.blit(no_unit_text, no_unit_rect)
            return panel_rect

        # Get unit help data
        if self.unit_type not in self.unit_help_data:
            # Show error message
            error_text = self.small_font.render(f"No help data for {self.unit_type.name}", True, (255, 100, 100))
            screen.blit(error_text, (x + 15, y + 15))
            return panel_rect

        # Render content if needed
        if not self.content_surface:
            self.content_surface = self._render_content(width)

        if not self.content_surface:
            return panel_rect

        # Calculate scroll limits
        content_height = self.content_surface.get_height()
        visible_height = height - 20
        self.max_scroll = max(0, content_height - visible_height)

        # Set up clipping region
        content_rect = pygame.Rect(x + 10, y + 10, width - 20, visible_height)
        screen.set_clip(content_rect)

        # Draw content with scroll offset
        screen.blit(self.content_surface, (x + 10, y + 10 - self.scroll_offset))

        # Clear clipping
        screen.set_clip(None)

        # Draw scroll indicator if needed
        if self.max_scroll > 0:
            scroll_pct = self.scroll_offset / self.max_scroll if self.max_scroll > 0 else 0
            indicator_height = max(20, int(visible_height * (visible_height / content_height)))
            indicator_y = y + 10 + int((visible_height - indicator_height) * scroll_pct)

            scroll_bar_rect = pygame.Rect(x + width - 8, indicator_y, 6, indicator_height)
            pygame.draw.rect(screen, (100, 150, 200), scroll_bar_rect, border_radius=3)

        return panel_rect
