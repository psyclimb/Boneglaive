#!/usr/bin/env python3
"""
Status Effects UI Component
Displays status effects for selected unit with tooltips.
"""
import pygame
import os
from typing import List, Dict, Optional, Tuple
from .font_utils import render_fitted_text

# Colors - matching bone/industrial theme
COLOR_BG_TOP = (42, 42, 47)  # Panel top
COLOR_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_BUFF = (100, 200, 100)
COLOR_DEBUFF = (255, 100, 100)
COLOR_NEUTRAL = (150, 150, 200)
COLOR_SPECIAL = (255, 200, 100)
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_HOVER_TOP = (90, 74, 79)  # Hover gradient top
COLOR_HOVER_BOTTOM = (64, 48, 53)  # Hover gradient bottom
COLOR_BORDER = (90, 84, 79)  # Metal border

# Import scaling utilities
from .scale_utils import scale_manager

# Scale panel dimensions based on resolution
PANEL_WIDTH = scale_manager.scale(350, 'x')
PANEL_PADDING = scale_manager.scale(10)
EFFECT_HEIGHT = scale_manager.scale(50, 'y')
ICON_SIZE = scale_manager.status_icon_size
SPACING = scale_manager.scale(8)


# Status effect definitions: maps unit properties to display information
STATUS_EFFECTS = {
    # Debuffs
    "was_pried": {
        "name": "Pried",
        "type": "debuff",
        "icon": "P",
        "description": "Movement reduced by Pry skill",
        "duration_key": "pry_duration",
        "check": lambda u: hasattr(u, 'was_pried') and u.was_pried
    },
    "was_pried_upgraded": {
        "name": "Pried",
        "type": "debuff",
        "icon": "P",
        "description": "Movement reduced by upgraded Pry skill",
        "duration_key": "pry_upgraded_duration",
        "check": lambda u: hasattr(u, 'was_pried_upgraded') and u.was_pried_upgraded
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
        "duration_key": "estranged_duration",
        "check": lambda u: u.estranged
    },
    "mired": {
        "name": "Mired",
        "type": "debuff",
        "icon": "M",
        "description": "Attack and movement reduced by 1 from Marrow Dike",
        "duration_key": "mired_duration",
        "check": lambda u: u.mired
    },
    "shredded": {
        "name": "Shredded",
        "type": "debuff",
        "icon": "SD",
        "description": "Defense set to 0 by rail cannon",
        "duration_key": "shredded_duration",
        "check": lambda u: hasattr(u, 'shredded') and u.shredded
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
    "disarmed": {
        "name": "Disarmed",
        "type": "debuff",
        "icon": "DA",
        "description": "Cannot attack",
        "duration_key": "status_disarmed_duration",
        "check": lambda u: getattr(u, 'status_disarmed', False)
    },
    "topiary": {
        "name": "Topiary",
        "type": "debuff",
        "icon": "T",
        "description": "Transformed into terrain, cannot act",
        "duration_key": "topiary_duration",
        "check": lambda u: getattr(u, 'is_topiary', False)
    },
    "bola": {
        "name": "Bola",
        "type": "debuff",
        "icon": "Ø",
        "description": "Grafted bombs; detonate for percent-max-HP damage",
        "duration_key": "bola_stacks",  # shows the stack count, not a turn timer
        "check": lambda u: getattr(u, 'bola_stacks', 0) > 0
    },
    "selenic_backdraft": {
        "name": "Selenic Backdraft",
        "type": "debuff",
        "icon": "SB",
        "description": "Cannot basic attack POTPOURRIST",
        "duration_key": "selenic_backdraft_duration",
        "check": lambda u: getattr(u, 'selenic_backdraft', False)
    },
    "demilune_debuffed": {
        "name": "Lunacy",
        "type": "debuff",
        "icon": "DM",
        "description": "Attack reduced",
        "duration_key": "demilune_debuff_duration",
        "check": lambda u: u.demilune_debuffed
    },
    "taunted_by": {
        "name": "Geas",
        "type": "debuff",
        "icon": "!",
        "description": "Must attack or skill POTPOURRIST",
        "duration_key": "taunt_duration",
        "check": lambda u: u.taunted_by is not None
    },
    "radiation_stacks": {
        "name": "RF Burn",
        "type": "debuff",
        "icon": "R",
        "description": "Taking periodic RF burn damage",
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
    "status_imbued": {
        "name": "Imbued",
        "type": "debuff",
        "icon": "¤",
        "description": "Imbued with Market Futures energy, acts as teleportation anchor",
        "duration_key": "status_imbued_duration",
        "check": lambda u: hasattr(u, 'status_imbued') and u.status_imbued
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
    "first_turn_move_bonus": {
        "name": "First Turn Bonus",
        "type": "buff",
        "icon": "1st",
        "description": "+1 movement range (Player 2's first turn compensation for going second)",
        "duration_key": "first_turn_move_bonus_duration",
        "check": lambda u: hasattr(u, 'first_turn_move_bonus') and u.first_turn_move_bonus
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
    "is_doppelganger": {
        "name": "Doppelganger",
        "type": "buff",
        "icon": "DG",
        "description": "Temporary doppelganger created by Grae Exchange",
        "duration_key": "doppelganger_duration",
        "check": lambda u: u.is_doppelganger
    },
    "potpourri_held": {
        "name": "Infused",
        "type": "buff",
        "icon": "PO",
        "description": "POTPOURRIST holding potpourri, enhances next skill",
        "duration_key": "potpourri_duration",
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

        # Draw background with gradient
        from .menu_components import draw_gradient_rect
        draw_gradient_rect(surface, self.panel_rect, COLOR_BG_TOP, COLOR_BG_BOTTOM, alpha=200)

        # Draw border
        pygame.draw.rect(surface, COLOR_BORDER, self.panel_rect, 2, border_radius=5)

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
            # Draw hover highlight with gradient
            from .menu_components import draw_gradient_rect
            draw_gradient_rect(surface, effect_rect, COLOR_HOVER_TOP, COLOR_HOVER_BOTTOM, alpha=100)

        # Draw icon background
        icon_rect = pygame.Rect(x, y, ICON_SIZE, ICON_SIZE)
        pygame.draw.rect(surface, effect.get_color(), icon_rect)
        pygame.draw.rect(surface, (0, 0, 0), icon_rect, 2)

        # Draw icon text
        icon_text = render_fitted_text(
            effect.icon,
            max_width=ICON_SIZE - 4,
            max_height=ICON_SIZE - 4,
            color=(0, 0, 0),
            base_font_size=16,
            min_font_size=10,
            max_font_size=18
        )
        icon_text_rect = icon_text.get_rect(center=icon_rect.center)
        surface.blit(icon_text, icon_text_rect)

        # Draw effect name
        available_width = PANEL_WIDTH - ICON_SIZE - SPACING - 10
        name_text = render_fitted_text(
            effect.name,
            max_width=available_width,
            max_height=20,
            color=COLOR_TEXT,
            base_font_size=18,
            min_font_size=14,
            max_font_size=20
        )
        surface.blit(name_text, (x + ICON_SIZE + SPACING, y + 2))

        # Draw duration if applicable
        if effect.duration is not None and effect.duration > 0:
            if effect.key == "radiation_stacks":
                duration_str = f"{effect.duration} stacks"
            else:
                duration_str = f"{effect.duration} turns"

            duration_text = render_fitted_text(
                duration_str,
                max_width=available_width,
                max_height=18,
                color=COLOR_TEXT_DIM,
                base_font_size=16,
                min_font_size=12,
                max_font_size=18
            )
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

        # Draw tooltip background with gradient
        from .menu_components import draw_gradient_rect
        tooltip_rect = pygame.Rect(x, y, tooltip_width, tooltip_height)
        draw_gradient_rect(surface, tooltip_rect, COLOR_BG_TOP, COLOR_BG_BOTTOM, alpha=240)

        # Draw border
        pygame.draw.rect(surface, self.hovered_effect.get_color(), tooltip_rect, 2, border_radius=3)

        # Draw description
        text_y = y + 10
        for line in desc_lines:
            line_text = render_fitted_text(
                line,
                max_width=tooltip_width - 20,
                max_height=18,
                color=COLOR_TEXT,
                base_font_size=16,
                min_font_size=12,
                max_font_size=18
            )
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
