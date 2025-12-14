#!/usr/bin/env python3
"""
Status Effects UI Component
Displays status effects for selected unit with tooltips.
"""
import pygame
import os
from typing import List, Dict, Optional, Tuple

# Colors
COLOR_BG = (30, 34, 42)
COLOR_BUFF = (100, 200, 100)
COLOR_DEBUFF = (255, 100, 100)
COLOR_NEUTRAL = (150, 150, 200)
COLOR_SPECIAL = (255, 200, 100)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_HOVER = (60, 64, 72)

PANEL_WIDTH = 350
PANEL_PADDING = 10
EFFECT_HEIGHT = 50
ICON_SIZE = 36
SPACING = 8


# Status effect definitions: maps unit properties to display information
STATUS_EFFECTS = {
    # Debuffs
    "was_pried": {
        "name": "Pried",
        "type": "debuff",
        "icon": "P",
        "description": "Defense reduced by Pry skill",
        "check": lambda u: u.was_pried
    },
    "trapped_by": {
        "name": "Trapped",
        "type": "debuff",
        "icon": "T",
        "description": "Trapped by MANDIBLE_FOREMAN, taking incremental damage",
        "duration_key": "trap_duration",
        "check": lambda u: u.trapped_by is not None
    },
    "jawline_affected": {
        "name": "Jawline",
        "type": "debuff",
        "icon": "J",
        "description": "Affected by Jawline skill network",
        "duration_key": "jawline_duration",
        "check": lambda u: u.jawline_affected
    },
    "estranged": {
        "name": "Estranged",
        "type": "debuff",
        "icon": "E",
        "description": "All stats reduced by 1",
        "check": lambda u: u.estranged
    },
    "mired": {
        "name": "Mired",
        "type": "debuff",
        "icon": "M",
        "description": "Stuck in upgraded Marrow Dike",
        "duration_key": "mired_duration",
        "check": lambda u: u.mired
    },
    "neural_shunt_affected": {
        "name": "Neural Shunt",
        "type": "debuff",
        "icon": "NS",
        "description": "Neural functions disrupted",
        "duration_key": "neural_shunt_duration",
        "check": lambda u: u.neural_shunt_affected
    },
    "derelicted": {
        "name": "Derelicted",
        "type": "debuff",
        "icon": "D",
        "description": "Immobilized, cannot move",
        "duration_key": "derelicted_duration",
        "check": lambda u: u.derelicted
    },
    "demilune_debuffed": {
        "name": "Demilune",
        "type": "debuff",
        "icon": "DM",
        "description": "Attack reduced" + (" / Defense halved" if hasattr(lambda u: u, "demilune_defense_halved") else ""),
        "duration_key": "demilune_debuff_duration",
        "check": lambda u: u.demilune_debuffed
    },
    "taunted_by": {
        "name": "Taunted",
        "type": "debuff",
        "icon": "!",
        "description": "Must attack or skill POTPOURRIST",
        "duration_key": "taunt_duration",
        "check": lambda u: u.taunted_by is not None
    },
    "radiation_stacks": {
        "name": "Radiation",
        "type": "debuff",
        "icon": "R",
        "description": "Taking periodic radiation damage",
        "duration_key": None,  # Special: shows number of stacks
        "check": lambda u: len(u.radiation_stacks) > 0 if hasattr(u, 'radiation_stacks') else False
    },
    "shrapnel_duration": {
        "name": "Shrapnel",
        "type": "debuff",
        "icon": "SH",
        "description": "Taking shrapnel damage over time",
        "duration_key": "shrapnel_duration",
        "check": lambda u: u.shrapnel_duration > 0
    },
    "auction_curse_dot": {
        "name": "Auction Curse",
        "type": "debuff",
        "icon": "AC",
        "description": "Cursed by twisted auction, taking damage from nearby furniture, healing prevented",
        "duration_key": "auction_curse_dot_duration",
        "check": lambda u: hasattr(u, 'auction_curse_dot') and u.auction_curse_dot
    },

    # Buffs
    "can_use_anchor": {
        "name": "Parallax",
        "type": "buff",
        "icon": "PX",
        "description": "Adjacent to Market Futures anchor, can teleport via Parallax skill",
        "check": lambda u: hasattr(u, 'can_use_anchor') and u.can_use_anchor
    },
    "market_futures_bonus_applied": {
        "name": "Investment",
        "type": "buff",
        "icon": "INV",
        "description": "Maturing investment from Market Futures teleport: +1/+2/+3 ATK over 3 turns, +1 Range",
        "duration_key": "market_futures_duration",
        "check": lambda u: hasattr(u, 'market_futures_bonus_applied') and u.market_futures_bonus_applied
    },
    "partition_shield_active": {
        "name": "Partition",
        "type": "buff",
        "icon": "+",
        "description": "Protected by Partition shield",
        "duration_key": "partition_shield_duration",
        "check": lambda u: u.partition_shield_active
    },
    "severance_active": {
        "name": "Severance",
        "type": "buff",
        "icon": "S",
        "description": "+1 movement range",
        "duration_key": "severance_duration",
        "check": lambda u: u.severance_active
    },
    "pumped_up_active": {
        "name": "Pumped Up",
        "type": "buff",
        "icon": "UP",
        "description": "+1 to all stats",
        "duration_key": "pumped_up_duration",
        "check": lambda u: u.pumped_up_active
    },
    "carrier_rave_active": {
        "name": "Karrier Rave",
        "type": "buff",
        "icon": "KR",
        "description": "Phased state, next attack strikes 3 times",
        "duration_key": "carrier_rave_duration",
        "check": lambda u: u.carrier_rave_active
    },
    "trauma_processing_active": {
        "name": "Trauma Processing",
        "type": "buff",
        "icon": "TP",
        "description": "Damage stored for later Abreaction",
        "check": lambda u: u.trauma_processing_active
    },
    "status_site_inspection": {
        "name": "Site Inspection",
        "type": "buff",
        "icon": "SI",
        "description": "+1 attack and +1 movement from clear terrain",
        "duration_key": "status_site_inspection_duration",
        "check": lambda u: hasattr(u, 'status_site_inspection') and u.status_site_inspection
    },
    "status_site_inspection_partial": {
        "name": "Site Inspection",
        "type": "buff",
        "icon": "SI",
        "description": "+1 attack from partially obstructed terrain",
        "duration_key": "status_site_inspection_partial_duration",
        "check": lambda u: hasattr(u, 'status_site_inspection_partial') and u.status_site_inspection_partial
    },
    "ossify_active": {
        "name": "Ossify",
        "type": "buff",
        "icon": "O",
        "description": "Compressed bone structure: +2 defense (+3 when upgraded), -1 movement",
        "duration_key": "ossify_duration",
        "check": lambda u: hasattr(u, 'ossify_active') and u.ossify_active
    },
    "valuation_oracle_buff": {
        "name": "Valuation Oracle",
        "type": "buff",
        "icon": "VO",
        "description": "Adjacent to high-value furniture (≥9): +1 defense and +1 attack range",
        "duration_key": "valuation_oracle_duration",
        "check": lambda u: hasattr(u, 'valuation_oracle_buff') and u.valuation_oracle_buff
    },
    "riposte_active": {
        "name": "Riposte",
        "type": "buff",
        "icon": "X",
        "description": "+2 defense. When hit by basic attack, fires 4 diagonal balls (3 damage each, 1 ricochet). 3 turn CD.",
        "check": lambda u: hasattr(u, 'riposte_active') and u.riposte_active
    },
    "backhand_active": {
        "name": "Backhand",
        "type": "buff",
        "icon": "<",
        "description": "Counter stance. Reflects enemy single-target skills back as ricochet ball (2 bounces). Full effects apply to anyone hit.",
        "duration_key": "backhand_duration",
        "check": lambda u: hasattr(u, 'backhand_active') and u.backhand_active
    },

    # Special/Neutral
    "gaussian_dusk_recharge": {
        "name": "Recharging",
        "type": "debuff",
        "icon": "=",
        "description": "Rail cannon recharging - cannot take any actions",
        "duration_key": "gaussian_dusk_recharge",
        "check": lambda u: hasattr(u, 'gaussian_dusk_recharge') and u.gaussian_dusk_recharge > 0
    },
    "is_echo": {
        "name": "Echo",
        "type": "neutral",
        "icon": "EC",
        "description": "Temporary echo created by Grae Exchange",
        "duration_key": "echo_duration",
        "check": lambda u: u.is_echo
    },
    "potpourri_held": {
        "name": "Potpourri",
        "type": "neutral",
        "icon": "PO",
        "description": "POTPOURRIST holding potpourri",
        "check": lambda u: u.potpourri_held
    },
}


class StatusEffectIcon:
    """Represents a single status effect icon."""

    def __init__(self, effect_key: str, effect_data: Dict, unit):
        self.key = effect_key
        self.name = effect_data["name"]
        self.type = effect_data["type"]
        self.icon = effect_data["icon"]
        self.description = effect_data["description"]
        self.duration = None

        # Get duration if applicable
        if "duration_key" in effect_data and effect_data["duration_key"]:
            self.duration = getattr(unit, effect_data["duration_key"], None)

        # Special case: radiation stacks
        if effect_key == "radiation_stacks":
            self.duration = len(unit.radiation_stacks)

        # Special case: partition shield strength
        if effect_key == "partition_shield_active":
            shield_str = getattr(unit, "partition_shield_strength", 0)
            if shield_str > 0:
                self.description += f" ({shield_str} HP)"

        # Special case: trauma debt
        if effect_key == "trauma_processing_active":
            trauma_debt = getattr(unit, "trauma_debt", 0)
            if trauma_debt > 0:
                self.description += f" ({trauma_debt} damage stored)"

    def get_color(self) -> Tuple[int, int, int]:
        """Get color based on effect type."""
        if self.type == "buff":
            return COLOR_BUFF
        elif self.type == "debuff":
            return COLOR_DEBUFF
        elif self.type == "special":
            return COLOR_SPECIAL
        else:
            return COLOR_NEUTRAL


class StatusEffectsPanel:
    """UI panel showing status effects for selected unit."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.effects: List[StatusEffectIcon] = []
        self.hovered_effect: Optional[StatusEffectIcon] = None
        self.panel_rect = None

    def update(self, game_unit):
        """Update panel with effects from selected unit."""
        self.effects.clear()
        self.hovered_effect = None

        if not game_unit:
            return

        # Check each status effect
        for effect_key, effect_data in STATUS_EFFECTS.items():
            try:
                if effect_data["check"](game_unit):
                    icon = StatusEffectIcon(effect_key, effect_data, game_unit)
                    self.effects.append(icon)
            except AttributeError:
                # Unit doesn't have this property (different unit type)
                continue

    def draw(self, surface: pygame.Surface, x: int, y: int) -> int:
        """
        Draw the status effects panel.

        Args:
            surface: Surface to draw on
            x, y: Position to draw at (top-left)

        Returns:
            Height of panel drawn
        """
        if not self.effects:
            return 0

        # Calculate panel height
        panel_height = PANEL_PADDING * 2 + len(self.effects) * (EFFECT_HEIGHT + SPACING) - SPACING
        self.panel_rect = pygame.Rect(x, y, PANEL_WIDTH, panel_height)

        # Draw background
        panel_surface = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((*COLOR_BG, 200))
        surface.blit(panel_surface, (self.panel_rect.x, self.panel_rect.y))

        # Draw border
        pygame.draw.rect(surface, (100, 100, 100), self.panel_rect, 2)

        # Draw effects
        current_y = y + PANEL_PADDING
        for effect in self.effects:
            self._draw_effect(surface, x + PANEL_PADDING, current_y, effect)
            current_y += EFFECT_HEIGHT + SPACING

        # Draw tooltip for hovered effect
        if self.hovered_effect:
            self._draw_tooltip(surface, x, y + panel_height + 5)

        return panel_height

    def _draw_effect(self, surface: pygame.Surface, x: int, y: int, effect: StatusEffectIcon):
        """Draw a single status effect."""
        # Check if mouse is over this effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        effect_rect = pygame.Rect(x, y, PANEL_WIDTH - PANEL_PADDING * 2, EFFECT_HEIGHT)
        is_hovered = effect_rect.collidepoint(mouse_x, mouse_y)

        if is_hovered:
            self.hovered_effect = effect
            # Draw hover highlight
            hover_surf = pygame.Surface((effect_rect.width, effect_rect.height), pygame.SRCALPHA)
            hover_surf.fill((*COLOR_HOVER, 100))
            surface.blit(hover_surf, (effect_rect.x, effect_rect.y))

        # Draw icon background
        icon_rect = pygame.Rect(x, y, ICON_SIZE, ICON_SIZE)
        pygame.draw.rect(surface, effect.get_color(), icon_rect)
        pygame.draw.rect(surface, (0, 0, 0), icon_rect, 2)

        # Draw icon text
        icon_text = self.small_font.render(effect.icon, True, (0, 0, 0))
        icon_text_rect = icon_text.get_rect(center=icon_rect.center)
        surface.blit(icon_text, icon_text_rect)

        # Draw effect name
        name_text = self.font.render(effect.name, True, COLOR_TEXT)
        surface.blit(name_text, (x + ICON_SIZE + SPACING, y + 2))

        # Draw duration if applicable
        if effect.duration is not None and effect.duration > 0:
            if effect.key == "radiation_stacks":
                duration_str = f"{effect.duration} stacks"
            else:
                duration_str = f"{effect.duration} turns"

            duration_text = self.small_font.render(duration_str, True, COLOR_TEXT_DIM)
            surface.blit(duration_text, (x + ICON_SIZE + SPACING, y + 22))

    def _draw_tooltip(self, surface: pygame.Surface, x: int, y: int):
        """Draw tooltip for hovered effect."""
        if not self.hovered_effect:
            return

        # Prepare text
        desc_lines = self._wrap_text(self.hovered_effect.description, 40)

        # Calculate tooltip size
        tooltip_width = PANEL_WIDTH
        tooltip_height = 20 + len(desc_lines) * 18

        # Draw tooltip background
        tooltip_rect = pygame.Rect(x, y, tooltip_width, tooltip_height)
        tooltip_surf = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        tooltip_surf.fill((*COLOR_BG, 240))
        surface.blit(tooltip_surf, (tooltip_rect.x, tooltip_rect.y))

        # Draw border
        pygame.draw.rect(surface, self.hovered_effect.get_color(), tooltip_rect, 2)

        # Draw description
        text_y = y + 10
        for line in desc_lines:
            line_text = self.small_font.render(line, True, COLOR_TEXT)
            surface.blit(line_text, (x + 10, text_y))
            text_y += 18

    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """Wrap text to multiple lines."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            if current_length + word_length + len(current_line) > max_chars:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    lines.append(word)
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse motion for hover effects."""
        # Hover is calculated in draw method
        pass

    def handle_click(self, pos: Tuple[int, int]) -> Optional[StatusEffectIcon]:
        """
        Handle click on status effect.

        Returns:
            Clicked effect icon, or None
        """
        if not self.panel_rect or not self.effects:
            return None

        if not self.panel_rect.collidepoint(pos):
            return None

        # Check which effect was clicked
        x = self.panel_rect.x + PANEL_PADDING
        current_y = self.panel_rect.y + PANEL_PADDING

        for effect in self.effects:
            effect_rect = pygame.Rect(x, current_y, PANEL_WIDTH - PANEL_PADDING * 2, EFFECT_HEIGHT)
            if effect_rect.collidepoint(pos):
                return effect
            current_y += EFFECT_HEIGHT + SPACING

        return None
