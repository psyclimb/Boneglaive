#!/usr/bin/env python3
"""
Skill Bar UI Component
Displays available skills for the selected unit with hotkeys.
"""
import pygame
import os
from typing import Optional, List, Tuple, Dict, Set
from .font_utils import render_fitted_text
from .loto_system import LOTORenderer

# Colors
COLOR_BG = (30, 34, 42)
COLOR_BG_HOVER = (50, 54, 62)
COLOR_BG_SELECTED = (60, 100, 140)
COLOR_BG_DISABLED = (40, 40, 40)
COLOR_BORDER = (100, 100, 100)
COLOR_BORDER_HOVER = (150, 150, 150)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DISABLED = (120, 120, 120)
COLOR_HOTKEY = (255, 200, 100)
COLOR_COOLDOWN = (255, 100, 100)

SKILL_SLOT_WIDTH = 220
SKILL_SLOT_HEIGHT = 70
SKILL_SLOT_PADDING = 10
SKILL_BAR_PADDING = 20
SKILL_ICON_SIZE = 50  # Size of skill icons


class SkillSlot:
    """Individual skill slot in the skill bar."""

    def __init__(self, skill, hotkey: str, index: int, icon_cache: Dict, game_unit=None):
        self.skill = skill
        self.hotkey = hotkey
        self.index = index
        self.rect = None
        self.hovered = False
        self.icon_cache = icon_cache
        self.icon_surface = self._load_icon()
        self.blocked_actions = set()  # LOTO: Set of blocked action types
        self.game_unit = game_unit  # Reference to game unit for checking upgrades

    def _load_icon(self) -> Optional[pygame.Surface]:
        """Load skill icon from file."""
        skill_name = self.skill.name.lower().replace(' ', '_')

        # Check cache first
        if skill_name in self.icon_cache:
            return self.icon_cache[skill_name]

        icon_path = f"graphics/skill_icons/{skill_name}.svg"

        if not os.path.exists(icon_path):
            return None

        try:
            # Try to load SVG using cairosvg
            import cairosvg
            from io import BytesIO
            png_data = cairosvg.svg2png(url=icon_path, output_width=SKILL_ICON_SIZE, output_height=SKILL_ICON_SIZE)
            icon_surface = pygame.image.load(BytesIO(png_data))
            icon_surface = icon_surface.convert_alpha()
            self.icon_cache[skill_name] = icon_surface
            return icon_surface
        except ImportError:
            pass  # cairosvg not available, try PNG fallback
        except Exception as e:
            pass

        # Fallback: Try PNG version
        png_path = f"graphics/skill_icons/{skill_name}.png"
        if os.path.exists(png_path):
            try:
                icon_surface = pygame.image.load(png_path)
                icon_surface = pygame.transform.scale(icon_surface, (SKILL_ICON_SIZE, SKILL_ICON_SIZE))
                icon_surface = icon_surface.convert_alpha()
                self.icon_cache[skill_name] = icon_surface
                return icon_surface
            except Exception:
                pass

        return None

    def is_available(self) -> bool:
        """Check if skill can be used (not on cooldown)."""
        return self.skill.current_cooldown <= 0 and not self.blocked_actions

    def draw(self, surface: pygame.Surface, x: int, y: int, font, small_font, loto_renderer: Optional[LOTORenderer] = None):
        """Draw the skill slot."""
        # Create rect
        self.rect = pygame.Rect(x, y, SKILL_SLOT_WIDTH, SKILL_SLOT_HEIGHT)

        # Check if this skill has been upgraded
        is_upgraded = False
        if self.game_unit and hasattr(self.game_unit, 'upgraded_skills'):
            is_upgraded = self.skill.name in self.game_unit.upgraded_skills

        # Determine background color
        if not self.is_available():
            bg_color = COLOR_BG_DISABLED
        elif self.hovered:
            bg_color = COLOR_BG_HOVER
        else:
            bg_color = COLOR_BG

        # Draw background
        pygame.draw.rect(surface, bg_color, self.rect)

        # Draw border (gold if upgraded)
        if is_upgraded:
            border_color = (255, 215, 0)  # Gold
        elif self.hovered:
            border_color = COLOR_BORDER_HOVER
        else:
            border_color = COLOR_BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw hotkey in top-left
        text_color = COLOR_TEXT_DISABLED if not self.is_available() else COLOR_HOTKEY
        hotkey_text = render_fitted_text(
            f"[{self.hotkey}]",
            max_width=50,
            max_height=20,
            color=text_color,
            base_font_size=16,
            min_font_size=12,
            max_font_size=16
        )
        surface.blit(hotkey_text, (x + 5, y + 5))

        # Draw skill icon on the left side
        icon_x = x + 10
        icon_y = y + (SKILL_SLOT_HEIGHT - SKILL_ICON_SIZE) // 2

        if self.icon_surface:
            # Apply grayscale if on cooldown
            if not self.is_available():
                # Create grayscale version
                gray_icon = self.icon_surface.copy()
                arr = pygame.surfarray.pixels3d(gray_icon)
                gray = (arr[:,:,0] * 0.3 + arr[:,:,1] * 0.59 + arr[:,:,2] * 0.11).astype('uint8')
                arr[:,:,0] = gray
                arr[:,:,1] = gray
                arr[:,:,2] = gray
                del arr
                surface.blit(gray_icon, (icon_x, icon_y))
            else:
                surface.blit(self.icon_surface, (icon_x, icon_y))

            # Draw upgrade indicator if skill is upgraded
            if is_upgraded:
                # Small star/diamond indicator in top-right corner of icon
                indicator_size = 12
                indicator_x = icon_x + SKILL_ICON_SIZE - indicator_size - 2
                indicator_y = icon_y + 2

                # Draw small circle with "UP" text
                pygame.draw.circle(surface, (255, 215, 0), (indicator_x + indicator_size // 2, indicator_y + indicator_size // 2), indicator_size // 2)
                pygame.draw.circle(surface, (0, 0, 0), (indicator_x + indicator_size // 2, indicator_y + indicator_size // 2), indicator_size // 2, 1)

                # Draw small "+" symbol
                plus_color = (0, 0, 0)
                center_x = indicator_x + indicator_size // 2
                center_y = indicator_y + indicator_size // 2
                pygame.draw.line(surface, plus_color, (center_x - 3, center_y), (center_x + 3, center_y), 2)
                pygame.draw.line(surface, plus_color, (center_x, center_y - 3), (center_x, center_y + 3), 2)

        # Draw skill name to the right of the icon
        text_color = COLOR_TEXT_DISABLED if not self.is_available() else COLOR_TEXT
        # Available width: slot width - icon area - padding
        available_width = SKILL_SLOT_WIDTH - (SKILL_ICON_SIZE + 30)
        name_text = render_fitted_text(
            self.skill.name,
            max_width=available_width,
            max_height=SKILL_SLOT_HEIGHT - 10,
            color=text_color,
            base_font_size=20,
            min_font_size=14,
            max_font_size=22
        )
        # Position to the right of icon
        name_x = icon_x + SKILL_ICON_SIZE + 10
        name_y = y + (SKILL_SLOT_HEIGHT - name_text.get_height()) // 2
        surface.blit(name_text, (name_x, name_y))

        # Draw cooldown if active
        if self.skill.current_cooldown > 0:
            cooldown_text = render_fitted_text(
                f"CD: {self.skill.current_cooldown}",
                max_width=80,
                max_height=18,
                color=COLOR_COOLDOWN,
                base_font_size=16,
                min_font_size=12,
                max_font_size=16
            )
            surface.blit(cooldown_text, (x + 5, y + SKILL_SLOT_HEIGHT - 20))

        # Draw LOTO overlay if skill is blocked
        if loto_renderer and self.blocked_actions:
            loto_renderer.draw_loto_overlay(surface, self.rect, self.blocked_actions, scale=0.5)

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if position is inside this slot."""
        if self.rect:
            return self.rect.collidepoint(pos)
        return False


class SkillBar:
    """Skill bar UI component showing available skills."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.selected_unit = None
        self.skill_slots: List[SkillSlot] = []
        self.hovered_slot: Optional[SkillSlot] = None
        self.selected_skill = None
        self.icon_cache: Dict[str, pygame.Surface] = {}  # Cache for loaded icons

        # Hotkey mapping (E and R reserved for Execute and Respawn in action menu)
        self.hotkeys = ['1', '2', '3', '4', 'Q', 'W']

        # LOTO system
        self.loto_renderer = LOTORenderer()

    def update(self, selected_unit, game_unit):
        """
        Update skill bar with skills from selected unit.

        Args:
            selected_unit: AnimatedUnit from renderer
            game_unit: Unit from game logic
        """
        from .loto_system import LOTOChecker

        self.selected_unit = selected_unit
        self.skill_slots.clear()

        if not selected_unit or not game_unit:
            return

        # Get active skills from the actual unit instance (not registry templates)
        # This ensures we display the correct current_cooldown values
        # Use get_active_skills() to include dynamic skills like Parallax
        active_skills = game_unit.get_active_skills()

        # Check for LOTO blocked actions
        blocked_actions = LOTOChecker.get_blocked_actions(game_unit)

        # Create skill slots
        for i, skill in enumerate(active_skills):
            if i < len(self.hotkeys):
                slot = SkillSlot(skill, self.hotkeys[i], i, self.icon_cache, game_unit)
                # Check if skills are blocked
                if LOTOChecker.is_action_blocked(game_unit, 'skill'):
                    slot.blocked_actions = blocked_actions
                self.skill_slots.append(slot)

    def draw(self, surface: pygame.Surface, screen_width: int, screen_height: int, top_bar_height: int):
        """Draw skill bar above the map (below top bar)."""
        if not self.skill_slots:
            return

        # Calculate total width needed
        total_width = (len(self.skill_slots) * (SKILL_SLOT_WIDTH + SKILL_SLOT_PADDING)
                      - SKILL_SLOT_PADDING + 2 * SKILL_BAR_PADDING)

        # Center horizontally in middle section (between left and right panels)
        start_x = (screen_width - total_width) // 2 + SKILL_BAR_PADDING
        y = top_bar_height + 15  # Below top bar with more spacing

        # Draw background panel
        panel_rect = pygame.Rect(
            start_x - SKILL_BAR_PADDING,
            y - 10,
            total_width,
            SKILL_SLOT_HEIGHT + 20
        )
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((*COLOR_BG, 200))
        surface.blit(panel_surface, (panel_rect.x, panel_rect.y))

        # Draw each skill slot
        x = start_x
        for slot in self.skill_slots:
            slot.draw(surface, x, y, self.font, self.small_font, self.loto_renderer)
            x += SKILL_SLOT_WIDTH + SKILL_SLOT_PADDING

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Update hovered slot based on mouse position."""
        self.hovered_slot = None
        for slot in self.skill_slots:
            slot.hovered = slot.contains_point(mouse_pos)
            if slot.hovered:
                self.hovered_slot = slot

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[object]:
        """
        Handle click on skill bar.

        Returns:
            Skill object if a skill was clicked and is available, None otherwise
        """
        for slot in self.skill_slots:
            if slot.contains_point(mouse_pos):
                if slot.is_available():
                    self.selected_skill = slot.skill
                    return slot.skill
                else:
                    # Skill on cooldown, can't use
                    return None
        return None

    def handle_hotkey(self, key: int) -> Optional[object]:
        """
        Handle hotkey press.

        Args:
            key: pygame key constant (e.g., pygame.K_1)

        Returns:
            Skill object if hotkey matches available skill, None otherwise
        """
        # Map pygame keys to hotkey strings
        key_map = {
            pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3', pygame.K_4: '4',
            pygame.K_q: 'Q', pygame.K_w: 'W', pygame.K_e: 'E', pygame.K_r: 'R',
        }

        hotkey_str = key_map.get(key)
        if not hotkey_str:
            return None

        # Find skill with matching hotkey
        for slot in self.skill_slots:
            if slot.hotkey == hotkey_str:
                if slot.is_available():
                    self.selected_skill = slot.skill
                    return slot.skill
                else:
                    # Skill on cooldown
                    return None

        return None

    def get_tooltip(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """
        Get tooltip text for hovered skill.

        Returns:
            Tooltip string or None
        """
        for slot in self.skill_slots:
            if slot.contains_point(mouse_pos):
                skill = slot.skill
                tooltip = f"{skill.name}\n{skill.description}"
                if skill.current_cooldown > 0:
                    tooltip += f"\nCooldown: {skill.current_cooldown} turns"
                if skill.range > 0:
                    tooltip += f"\nRange: {skill.range}"
                return tooltip
        return None
