#!/usr/bin/env python3
"""
Skill Bar UI Component
Displays available skills for the selected unit with hotkeys.
"""
import pygame
from typing import Optional, List, Tuple

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

SKILL_SLOT_WIDTH = 180
SKILL_SLOT_HEIGHT = 60
SKILL_SLOT_PADDING = 10
SKILL_BAR_PADDING = 20


class SkillSlot:
    """Individual skill slot in the skill bar."""

    def __init__(self, skill, hotkey: str, index: int):
        self.skill = skill
        self.hotkey = hotkey
        self.index = index
        self.rect = None
        self.hovered = False

    def is_available(self) -> bool:
        """Check if skill can be used (not on cooldown)."""
        return self.skill.current_cooldown <= 0

    def draw(self, surface: pygame.Surface, x: int, y: int, font, small_font):
        """Draw the skill slot."""
        # Create rect
        self.rect = pygame.Rect(x, y, SKILL_SLOT_WIDTH, SKILL_SLOT_HEIGHT)

        # Determine background color
        if not self.is_available():
            bg_color = COLOR_BG_DISABLED
        elif self.hovered:
            bg_color = COLOR_BG_HOVER
        else:
            bg_color = COLOR_BG

        # Draw background
        pygame.draw.rect(surface, bg_color, self.rect)

        # Draw border
        border_color = COLOR_BORDER_HOVER if self.hovered else COLOR_BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw hotkey in top-left
        text_color = COLOR_TEXT_DISABLED if not self.is_available() else COLOR_HOTKEY
        hotkey_text = small_font.render(f"[{self.hotkey}]", True, text_color)
        surface.blit(hotkey_text, (x + 5, y + 5))

        # Draw skill name
        text_color = COLOR_TEXT_DISABLED if not self.is_available() else COLOR_TEXT
        name_text = font.render(self.skill.name, True, text_color)
        # Center horizontally, position near top
        name_x = x + (SKILL_SLOT_WIDTH - name_text.get_width()) // 2
        surface.blit(name_text, (name_x, y + 20))

        # Draw cooldown if active
        if self.skill.current_cooldown > 0:
            cooldown_text = small_font.render(
                f"CD: {self.skill.current_cooldown}",
                True,
                COLOR_COOLDOWN
            )
            surface.blit(cooldown_text, (x + 5, y + SKILL_SLOT_HEIGHT - 20))

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

        # Hotkey mapping (matches ASCII version)
        self.hotkeys = ['1', '2', '3', '4', 'Q', 'W', 'E', 'R']

    def update(self, selected_unit, game_unit):
        """
        Update skill bar with skills from selected unit.

        Args:
            selected_unit: AnimatedUnit from renderer
            game_unit: Unit from game logic
        """
        self.selected_unit = selected_unit
        self.skill_slots.clear()

        if not selected_unit or not game_unit:
            return

        # Get unit type and skills from registry
        from boneglaive.game.skills.registry import UNIT_SKILLS

        unit_type_name = game_unit.type.name
        if unit_type_name not in UNIT_SKILLS:
            return

        unit_skills = UNIT_SKILLS[unit_type_name]

        # Get active skills only (passive skills don't need UI slots)
        active_skills = unit_skills.get("active", [])

        # Create skill slots
        for i, skill in enumerate(active_skills):
            if i < len(self.hotkeys):
                slot = SkillSlot(skill, self.hotkeys[i], i)
                self.skill_slots.append(slot)

    def draw(self, surface: pygame.Surface, screen_width: int, screen_height: int):
        """Draw skill bar at bottom of screen."""
        if not self.skill_slots:
            return

        # Calculate total width needed
        total_width = (len(self.skill_slots) * (SKILL_SLOT_WIDTH + SKILL_SLOT_PADDING)
                      - SKILL_SLOT_PADDING + 2 * SKILL_BAR_PADDING)

        # Center horizontally
        start_x = (screen_width - total_width) // 2 + SKILL_BAR_PADDING
        y = screen_height - SKILL_SLOT_HEIGHT - 20

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
            slot.draw(surface, x, y, self.font, self.small_font)
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
