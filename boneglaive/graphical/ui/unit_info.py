#!/usr/bin/env python3
"""
Unit Info Panel UI Component
Displays detailed information about selected unit.
"""
import pygame
from typing import Optional
from .font_utils import render_fitted_text

# Colors
COLOR_BG = (30, 34, 42)
COLOR_PLAYER1 = (100, 255, 100)  # Green
COLOR_PLAYER2 = (100, 150, 255)  # Blue
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_HP_BAR_BG = (60, 60, 60)
COLOR_HP_BAR_FULL = (100, 255, 100)
COLOR_HP_BAR_MID = (255, 200, 100)
COLOR_HP_BAR_LOW = (255, 100, 100)
COLOR_STAT_LABEL = (150, 150, 150)

PANEL_WIDTH = 264  # Fits in 280px panel width
PANEL_HEIGHT = 440  # Expanded to fill available space below unit status bar
PANEL_PADDING = 10
LINE_HEIGHT = 18
HP_BAR_HEIGHT = 20


class UnitInfoPanel:
    """UI panel showing detailed information about selected unit or furniture."""

    def __init__(self, font, small_font, large_font):
        self.font = font
        self.small_font = small_font
        self.large_font = large_font
        self.selected_unit = None  # AnimatedUnit
        self.game_unit = None  # Game unit from engine
        self.furniture_info = None  # Dict with furniture data

    def update(self, selected_unit, game_unit):
        """
        Update panel with unit information.

        Args:
            selected_unit: AnimatedUnit (visual representation)
            game_unit: Unit from game engine (has stats)
        """
        self.selected_unit = selected_unit
        self.game_unit = game_unit
        self.furniture_info = None  # Clear furniture when showing unit

    def update_furniture(self, furniture_info):
        """
        Update panel with furniture information.

        Args:
            furniture_info: Dict with keys: 'name', 'astral_value' (or None), 'position'
        """
        self.selected_unit = None  # Clear unit when showing furniture
        self.game_unit = None
        self.furniture_info = furniture_info

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw the unit info panel.

        Args:
            surface: Surface to draw on
            x, y: Position to draw at (top-left)
        """
        # Check if showing furniture instead of unit
        if self.furniture_info:
            self._draw_furniture_info(surface, x, y)
            return

        if not self.selected_unit or not self.game_unit:
            return

        # Draw background panel
        panel_rect = pygame.Rect(x, y, PANEL_WIDTH, PANEL_HEIGHT)
        panel_surface = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
        panel_surface.fill((*COLOR_BG, 220))
        surface.blit(panel_surface, (panel_rect.x, panel_rect.y))

        # Draw border with player color
        player_color = COLOR_PLAYER1 if self.game_unit.player == 1 else COLOR_PLAYER2
        pygame.draw.rect(surface, player_color, panel_rect, 3)

        current_y = y + PANEL_PADDING

        # Draw unit name (large)
        # Handle both base units (with .name) and DLC units (integers)
        if hasattr(self.game_unit.type, 'name'):
            unit_name = self.game_unit.type.name.replace('_', ' ')
        else:
            # DLC unit - use display name from unit class
            from boneglaive.utils.constants import UNIT_DISPLAY_NAMES
            unit_name = UNIT_DISPLAY_NAMES.get(self.game_unit.type, f"Unit-{self.game_unit.type}")
        name_text = render_fitted_text(
            unit_name,
            max_width=PANEL_WIDTH - PANEL_PADDING * 2,
            max_height=35,
            color=COLOR_TEXT,
            base_font_size=28,
            min_font_size=20,
            max_font_size=32
        )
        surface.blit(name_text, (x + PANEL_PADDING, current_y))
        current_y += 32

        # Draw player indicator
        player_text = render_fitted_text(
            f"Player {self.game_unit.player}",
            max_width=120,
            max_height=20,
            color=player_color,
            base_font_size=16,
            min_font_size=12,
            max_font_size=18
        )
        surface.blit(player_text, (x + PANEL_PADDING, current_y))
        current_y += 22

        # Draw Greek ID if available
        if hasattr(self.game_unit, 'greek_id') and self.game_unit.greek_id:
            id_text = render_fitted_text(
                f"ID: {self.game_unit.greek_id}",
                max_width=75,
                max_height=20,
                color=COLOR_TEXT_DIM,
                base_font_size=16,
                min_font_size=12,
                max_font_size=18
            )
            surface.blit(id_text, (x + PANEL_WIDTH - 80, current_y - 22))

        # Draw HP bar
        current_y = self._draw_hp_bar(surface, x + PANEL_PADDING, current_y, PANEL_WIDTH - PANEL_PADDING * 2)
        current_y += 15

        # Draw stats
        current_y = self._draw_stats(surface, x + PANEL_PADDING, current_y)

        # Draw status effects
        current_y = self._draw_status_effects(surface, x + PANEL_PADDING, current_y)

    def _draw_hp_bar(self, surface: pygame.Surface, x: int, y: int, width: int) -> int:
        """
        Draw HP bar with current/max HP.

        Returns:
            y position after drawing
        """
        if not self.game_unit:
            return y

        current_hp = self.game_unit.hp
        max_hp = self.game_unit.max_hp
        hp_percent = current_hp / max_hp if max_hp > 0 else 0

        # Draw background
        bg_rect = pygame.Rect(x, y, width, HP_BAR_HEIGHT)
        pygame.draw.rect(surface, COLOR_HP_BAR_BG, bg_rect)

        # Draw HP fill
        if current_hp > 0:
            fill_width = int(width * hp_percent)
            fill_rect = pygame.Rect(x, y, fill_width, HP_BAR_HEIGHT)

            # Choose color based on HP percentage
            if hp_percent > 0.6:
                hp_color = COLOR_HP_BAR_FULL
            elif hp_percent > 0.3:
                hp_color = COLOR_HP_BAR_MID
            else:
                hp_color = COLOR_HP_BAR_LOW

            pygame.draw.rect(surface, hp_color, fill_rect)

        # Draw border
        pygame.draw.rect(surface, (100, 100, 100), bg_rect, 2)

        # Draw HP text
        hp_text = render_fitted_text(
            f"HP: {current_hp}/{max_hp}",
            max_width=width - 10,
            max_height=HP_BAR_HEIGHT - 2,
            color=COLOR_TEXT,
            base_font_size=18,
            min_font_size=14,
            max_font_size=20
        )
        text_rect = hp_text.get_rect(center=(x + width // 2, y + HP_BAR_HEIGHT // 2))
        surface.blit(hp_text, text_rect)

        return y + HP_BAR_HEIGHT

    def _draw_stats(self, surface: pygame.Surface, x: int, y: int) -> int:
        """
        Draw unit stats (ATK, DEF, Move, Attack Range).

        Returns:
            y position after drawing
        """
        if not self.game_unit:
            return y

        # Get effective stats
        stats = self.game_unit.get_effective_stats()

        # Define stats to display
        stat_lines = [
            ("Attack", stats['attack'], self.game_unit.attack),
            ("Defense", stats['defense'], self.game_unit.defense),
            ("Move Range", stats['move_range'], self.game_unit.move_range),
            ("Attack Range", stats['attack_range'], self.game_unit.attack_range),
        ]

        # Draw each stat line
        for label, effective_value, base_value in stat_lines:
            # Draw label
            label_text = render_fitted_text(
                f"{label}:",
                max_width=145,
                max_height=LINE_HEIGHT,
                color=COLOR_STAT_LABEL,
                base_font_size=18,
                min_font_size=14,
                max_font_size=20
            )
            surface.blit(label_text, (x, y))

            # Draw value (colored if different from base)
            if effective_value != base_value:
                # Stat is modified - show the bonus/penalty amount
                bonus = effective_value - base_value
                if effective_value > base_value:
                    value_color = COLOR_HP_BAR_FULL  # Green for buff
                else:
                    value_color = COLOR_HP_BAR_LOW  # Red for debuff
                value_str = f"{effective_value} ({bonus:+})"
            else:
                value_color = COLOR_TEXT
                value_str = str(effective_value)

            value_text = render_fitted_text(
                value_str,
                max_width=85,
                max_height=LINE_HEIGHT,
                color=value_color,
                base_font_size=18,
                min_font_size=14,
                max_font_size=20
            )
            surface.blit(value_text, (x + 150, y))

            y += LINE_HEIGHT

        # Add PRT if unit has it
        if hasattr(self.game_unit, 'prt') and self.game_unit.prt > 0:
            y += 5
            prt_label = render_fitted_text(
                "PRT:",
                max_width=145,
                max_height=LINE_HEIGHT,
                color=COLOR_STAT_LABEL,
                base_font_size=18,
                min_font_size=14,
                max_font_size=20
            )
            surface.blit(prt_label, (x, y))

            prt_value = render_fitted_text(
                str(self.game_unit.prt),
                max_width=85,
                max_height=LINE_HEIGHT,
                color=COLOR_PLAYER1,
                base_font_size=18,
                min_font_size=14,
                max_font_size=20
            )
            surface.blit(prt_value, (x + 150, y))

            y += LINE_HEIGHT

        # Add Level/XP if enabled
        if hasattr(self.game_unit, 'level') and self.game_unit.level > 1:
            y += 5
            level_text = render_fitted_text(
                f"Level {self.game_unit.level}",
                max_width=95,
                max_height=16,
                color=COLOR_TEXT_DIM,
                base_font_size=16,
                min_font_size=12,
                max_font_size=18
            )
            surface.blit(level_text, (x, y))

            if hasattr(self.game_unit, 'xp'):
                from boneglaive.utils.constants import XP_PER_LEVEL
                next_level_xp = self.game_unit.level * XP_PER_LEVEL
                xp_text = render_fitted_text(
                    f"XP: {self.game_unit.xp}/{next_level_xp}",
                    max_width=130,
                    max_height=16,
                    color=COLOR_TEXT_DIM,
                    base_font_size=16,
                    min_font_size=12,
                    max_font_size=18
                )
                surface.blit(xp_text, (x + 100, y))

            y += LINE_HEIGHT

        return y

    def _draw_status_effects(self, surface: pygame.Surface, x: int, y: int) -> int:
        """
        Draw status effects list.

        Returns:
            y position after drawing
        """
        if not self.game_unit:
            return y

        # Import status effects definitions
        from .status_effects import STATUS_EFFECTS

        # Collect active status effects with type info and duration
        active_effects = []
        for effect_key, effect_data in STATUS_EFFECTS.items():
            try:
                if effect_data["check"](self.game_unit):
                    effect_info = {
                        "name": effect_data["name"],
                        "type": effect_data["type"],
                        "duration": None
                    }

                    # Get duration if applicable
                    if "duration_key" in effect_data and effect_data["duration_key"]:
                        duration = getattr(self.game_unit, effect_data["duration_key"], None)
                        if duration is not None and duration > 0:
                            effect_info["duration"] = duration

                    # Special case: radiation stacks
                    if effect_key == "radiation_stacks":
                        if hasattr(self.game_unit, 'radiation_stacks'):
                            effect_info["duration"] = len(self.game_unit.radiation_stacks)

                    active_effects.append(effect_info)
            except AttributeError:
                # Unit doesn't have this property
                continue

        # Draw status effects if any
        if active_effects:
            y += 10  # Add spacing

            # Draw section label
            label_text = render_fitted_text(
                "Status Effects:",
                max_width=PANEL_WIDTH - PANEL_PADDING * 2,
                max_height=18,
                color=COLOR_STAT_LABEL,
                base_font_size=16,
                min_font_size=12,
                max_font_size=18
            )
            surface.blit(label_text, (x, y))
            y += 18

            # Draw each effect name with color based on type
            for effect in active_effects:
                # Choose color based on effect type
                if effect["type"] == "buff":
                    effect_color = COLOR_HP_BAR_FULL  # Green
                elif effect["type"] == "debuff":
                    effect_color = COLOR_HP_BAR_LOW  # Red
                else:
                    effect_color = COLOR_TEXT_DIM  # Gray for neutral

                # Format effect name with duration if available
                effect_name = effect['name']
                if effect['duration'] is not None:
                    effect_name = f"{effect_name} ({effect['duration']})"

                effect_text = render_fitted_text(
                    f"  • {effect_name}",
                    max_width=PANEL_WIDTH - PANEL_PADDING * 2,
                    max_height=16,
                    color=effect_color,
                    base_font_size=16,
                    min_font_size=12,
                    max_font_size=18
                )
                surface.blit(effect_text, (x, y))
                y += 16

        return y

    def _draw_stat_line(self, surface: pygame.Surface, x: int, y: int,
                       label: str, value: int, base_value: int = None) -> int:
        """
        Draw a single stat line.

        Args:
            surface: Surface to draw on
            x, y: Position
            label: Stat label
            value: Current effective value
            base_value: Base value (if different, show as buff/debuff)

        Returns:
            y position after drawing
        """
        # Draw label
        label_text = render_fitted_text(
            f"{label}:",
            max_width=145,
            max_height=LINE_HEIGHT,
            color=COLOR_STAT_LABEL,
            base_font_size=18,
            min_font_size=14,
            max_font_size=20
        )
        surface.blit(label_text, (x, y))

        # Draw value
        if base_value is not None and value != base_value:
            # Stat is modified
            if value > base_value:
                value_color = COLOR_HP_BAR_FULL  # Green for buff
                modifier = f"+{value - base_value}"
            else:
                value_color = COLOR_HP_BAR_LOW  # Red for debuff
                modifier = f"{value - base_value}"

            value_str = f"{value} ({modifier})"
        else:
            value_color = COLOR_TEXT
            value_str = str(value)

        value_text = render_fitted_text(
            value_str,
            max_width=85,
            max_height=LINE_HEIGHT,
            color=value_color,
            base_font_size=18,
            min_font_size=14,
            max_font_size=20
        )
        surface.blit(value_text, (x + 150, y))

        return y + LINE_HEIGHT

    def _draw_furniture_info(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw furniture information panel.

        Args:
            surface: Surface to draw on
            x, y: Position to draw at (top-left)
        """
        if not self.furniture_info:
            return

        # Smaller panel for furniture (no stats to show)
        panel_height = 150 if self.furniture_info.get('astral_value') else 120
        panel_rect = pygame.Rect(x, y, PANEL_WIDTH, panel_height)
        panel_surface = pygame.Surface((PANEL_WIDTH, panel_height), pygame.SRCALPHA)
        panel_surface.fill((*COLOR_BG, 220))
        surface.blit(panel_surface, (panel_rect.x, panel_rect.y))

        # Draw border (neutral color for furniture)
        furniture_color = (180, 150, 100)  # Brown/tan color
        pygame.draw.rect(surface, furniture_color, panel_rect, 3)

        current_y = y + PANEL_PADDING

        # Draw furniture name
        furniture_name = self.furniture_info['name']
        name_text = render_fitted_text(
            furniture_name,
            max_width=PANEL_WIDTH - PANEL_PADDING * 2,
            max_height=35,
            color=COLOR_TEXT,
            base_font_size=28,
            min_font_size=20,
            max_font_size=32
        )
        surface.blit(name_text, (x + PANEL_PADDING, current_y))
        current_y += 32

        # Draw type label
        type_text = render_fitted_text(
            "Furniture",
            max_width=120,
            max_height=20,
            color=COLOR_TEXT_DIM,
            base_font_size=16,
            min_font_size=12,
            max_font_size=18
        )
        surface.blit(type_text, (x + PANEL_PADDING, current_y))
        current_y += 25

        # Draw position
        pos = self.furniture_info['position']
        pos_text = render_fitted_text(
            f"Position: ({pos[0]}, {pos[1]})",
            max_width=PANEL_WIDTH - PANEL_PADDING * 2,
            max_height=20,
            color=COLOR_TEXT_DIM,
            base_font_size=16,
            min_font_size=12,
            max_font_size=18
        )
        surface.blit(pos_text, (x + PANEL_PADDING, current_y))
        current_y += 25

        # Draw astral value if present
        astral_value = self.furniture_info.get('astral_value')
        if astral_value is not None:
            current_y += 5
            # Draw label
            label_text = render_fitted_text(
                "Astral Value:",
                max_width=140,
                max_height=22,
                color=COLOR_STAT_LABEL,
                base_font_size=18,
                min_font_size=14,
                max_font_size=20
            )
            surface.blit(label_text, (x + PANEL_PADDING, current_y))

            # Draw value (golden color for mystical value)
            value_color = (255, 215, 0)  # Gold
            value_text = render_fitted_text(
                str(astral_value),
                max_width=55,
                max_height=30,
                color=value_color,
                base_font_size=28,
                min_font_size=20,
                max_font_size=32
            )
            surface.blit(value_text, (x + PANEL_WIDTH - 60, current_y - 5))
            current_y += 25
        elif self.furniture_info.get('has_appraiser') == False:
            # Player doesn't have DELPHIC APPRAISER
            current_y += 5
            hint_text = render_fitted_text(
                "(Requires DELPHIC APPRAISER)",
                max_width=PANEL_WIDTH - PANEL_PADDING * 2,
                max_height=18,
                color=COLOR_TEXT_DIM,
                base_font_size=16,
                min_font_size=12,
                max_font_size=18
            )
            surface.blit(hint_text, (x + PANEL_PADDING, current_y))
            current_y += 20
