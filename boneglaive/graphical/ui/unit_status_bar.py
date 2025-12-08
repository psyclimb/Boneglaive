#!/usr/bin/env python3
"""
Unit Status Bar UI Component
Displays grid of unit cards showing alive/dead/selected status.
"""
import pygame
from typing import List, Optional, Tuple, Dict
from boneglaive.utils.constants import UNIT_SYMBOLS

# Colors
COLOR_BG = (30, 34, 42)
COLOR_PLAYER1 = (100, 255, 100)  # Green
COLOR_PLAYER2 = (100, 150, 255)  # Blue
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_BORDER_ACTIVE = (150, 150, 150)
COLOR_BORDER_ACTED = (80, 80, 80)
COLOR_BORDER_SELECTED = (255, 200, 100)
COLOR_BORDER_DEAD = (60, 60, 60)
COLOR_HP_BAR_BG = (40, 40, 40)
COLOR_HP_BAR_FULL = (100, 255, 100)
COLOR_HP_BAR_MID = (255, 200, 100)
COLOR_HP_BAR_LOW = (255, 100, 100)

PANEL_WIDTH = 280  # Narrower panel
UNIT_CARD_WIDTH = 84  # Slightly smaller cards
UNIT_CARD_HEIGHT = 40  # Compact height
CARD_PADDING = 6  # Tighter spacing
CARDS_PER_ROW = 3
TITLE_HEIGHT = 25  # Smaller title
HP_BAR_HEIGHT = 4


class UnitCard:
    """Individual unit card in the status bar."""

    def __init__(self, game_unit, is_dead: bool = False):
        self.game_unit = game_unit
        self.is_dead = is_dead
        self.rect = None
        self.hovered = False

        # Dead unit attributes (from DeadUnit class)
        self.respawn_timer = 0
        if is_dead and hasattr(game_unit, 'respawn_timer'):
            self.respawn_timer = game_unit.respawn_timer

    def get_unit_symbol(self) -> str:
        """Get the display symbol for this unit."""
        if self.is_dead:
            # Dead unit
            unit_type = self.game_unit.unit_type
            return UNIT_SYMBOLS.get(unit_type, '?')
        else:
            # Alive unit
            unit = self.game_unit

            # Special handling for echo units
            if hasattr(unit, 'is_echo') and unit.is_echo:
                return 'ψ'  # Lowercase psi for echoes

            # Special handling for HEINOUS_VAPOR
            from boneglaive.utils.constants import UnitType
            if unit.type == UnitType.HEINOUS_VAPOR and hasattr(unit, 'vapor_symbol') and unit.vapor_symbol:
                return unit.vapor_symbol

            return UNIT_SYMBOLS.get(unit.type, '?')

    def get_greek_id(self) -> str:
        """Get the Greek letter ID."""
        return getattr(self.game_unit, 'greek_id', '?')

    def is_active(self) -> bool:
        """Check if unit is active (alive and hasn't acted)."""
        if self.is_dead:
            return False
        return not self.game_unit.is_done_acting()

    def draw(self, surface: pygame.Surface, x: int, y: int, font, small_font,
             is_selected: bool, player_color: tuple):
        """
        Draw the unit card.

        Args:
            surface: Surface to draw on
            x, y: Position
            font: Font for unit symbol
            small_font: Font for small text
            is_selected: Whether this unit is selected
            player_color: Color for this player's units
        """
        self.rect = pygame.Rect(x, y, UNIT_CARD_WIDTH, UNIT_CARD_HEIGHT)

        # Determine border color based on state
        if self.is_dead:
            border_color = COLOR_BORDER_DEAD
            bg_alpha = 150
        elif is_selected:
            border_color = COLOR_BORDER_SELECTED
            bg_alpha = 220
        elif self.is_active():
            border_color = player_color
            bg_alpha = 200
        else:
            border_color = COLOR_BORDER_ACTED
            bg_alpha = 180

        # Draw background
        bg_surface = pygame.Surface((UNIT_CARD_WIDTH, UNIT_CARD_HEIGHT), pygame.SRCALPHA)
        bg_surface.fill((*COLOR_BG, bg_alpha))
        surface.blit(bg_surface, (x, y))

        # Draw border (thicker if hovered or selected)
        border_width = 3 if (self.hovered or is_selected) else 2
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw unit symbol (large)
        symbol = self.get_unit_symbol()
        greek_id = self.get_greek_id()

        # Combine symbol and ID
        display_text = f"{symbol}{greek_id}"

        # Choose text color
        if self.is_dead:
            text_color = COLOR_TEXT_DIM
        elif is_selected:
            text_color = COLOR_BORDER_SELECTED
        else:
            text_color = player_color

        text_surface = font.render(display_text, True, text_color)
        text_rect = text_surface.get_rect(center=(x + UNIT_CARD_WIDTH // 2, y + 15))
        surface.blit(text_surface, text_rect)

        # Draw HP bar for alive units
        if not self.is_dead:
            self._draw_hp_bar(surface, x, y + UNIT_CARD_HEIGHT - HP_BAR_HEIGHT - 3)
        else:
            # Draw respawn timer for dead units
            if self.respawn_timer > 0:
                timer_text = small_font.render(str(self.respawn_timer), True, COLOR_TEXT_DIM)
                timer_rect = timer_text.get_rect(
                    center=(x + UNIT_CARD_WIDTH // 2, y + UNIT_CARD_HEIGHT - 12)
                )
                surface.blit(timer_text, timer_rect)
            else:
                # Ready to respawn
                ready_text = small_font.render("READY", True, COLOR_HP_BAR_FULL)
                ready_rect = ready_text.get_rect(
                    center=(x + UNIT_CARD_WIDTH // 2, y + UNIT_CARD_HEIGHT - 12)
                )
                surface.blit(ready_text, ready_rect)

    def _draw_hp_bar(self, surface: pygame.Surface, x: int, y: int):
        """Draw HP bar for alive units."""
        if self.is_dead or not hasattr(self.game_unit, 'hp'):
            return

        current_hp = self.game_unit.hp
        max_hp = self.game_unit.max_hp
        hp_percent = current_hp / max_hp if max_hp > 0 else 0

        # Bar dimensions (full card width minus padding)
        bar_width = UNIT_CARD_WIDTH - 10
        bar_x = x + 5

        # Draw background
        pygame.draw.rect(surface, COLOR_HP_BAR_BG,
                        (bar_x, y, bar_width, HP_BAR_HEIGHT))

        # Draw HP fill
        if current_hp > 0:
            fill_width = int(bar_width * hp_percent)

            # Choose color based on HP percentage
            if hp_percent > 0.6:
                hp_color = COLOR_HP_BAR_FULL
            elif hp_percent > 0.3:
                hp_color = COLOR_HP_BAR_MID
            else:
                hp_color = COLOR_HP_BAR_LOW

            pygame.draw.rect(surface, hp_color,
                           (bar_x, y, fill_width, HP_BAR_HEIGHT))

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if position is inside this card."""
        if self.rect:
            return self.rect.collidepoint(pos)
        return False


class UnitStatusBar:
    """Status bar showing grid of unit cards for current player."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.current_player = 1
        self.unit_cards: List[UnitCard] = []
        self.hovered_card: Optional[UnitCard] = None
        self.selected_unit = None  # Reference to selected game unit

    def update(self, game, selected_unit):
        """
        Update unit status bar with current game state.

        Args:
            game: Game instance from engine
            selected_unit: Currently selected unit (from game logic)
        """
        if not game:
            return

        self.current_player = game.current_player
        self.selected_unit = selected_unit
        self.unit_cards.clear()

        # Get alive units for current player
        alive_units = [u for u in game.units
                      if u.is_alive() and u.player == self.current_player]

        # Get dead units for current player
        dead_units = [du for du in game.dead_units
                     if du.player == self.current_player]

        # Create cards for alive units
        for unit in alive_units:
            self.unit_cards.append(UnitCard(unit, is_dead=False))

        # Create cards for dead units
        for dead_unit in dead_units:
            self.unit_cards.append(UnitCard(dead_unit, is_dead=True))

        # Sort by greek_id for consistent display
        self.unit_cards.sort(key=lambda card: getattr(card.game_unit, 'greek_id', 'ω'))

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw the unit status bar.

        Args:
            surface: Surface to draw on
            x, y: Position (top-left)
        """
        if not self.unit_cards:
            return

        # Draw title
        player_color = COLOR_PLAYER1 if self.current_player == 1 else COLOR_PLAYER2
        title_text = self.font.render("YOUR UNITS", True, player_color)
        surface.blit(title_text, (x + 10, y + 5))

        # Calculate card grid starting position
        card_start_y = y + TITLE_HEIGHT

        # Draw unit cards in grid
        for i, card in enumerate(self.unit_cards):
            row = i // CARDS_PER_ROW
            col = i % CARDS_PER_ROW

            card_x = x + col * (UNIT_CARD_WIDTH + CARD_PADDING) + CARD_PADDING
            card_y = card_start_y + row * (UNIT_CARD_HEIGHT + CARD_PADDING)

            # Check if this card's unit is selected
            is_selected = (self.selected_unit is not None and
                          not card.is_dead and
                          card.game_unit == self.selected_unit)

            card.draw(surface, card_x, card_y, self.font, self.small_font,
                     is_selected, player_color)

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Update hovered card based on mouse position."""
        self.hovered_card = None
        for card in self.unit_cards:
            card.hovered = card.contains_point(mouse_pos)
            if card.hovered:
                self.hovered_card = card

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[object]:
        """
        Handle click on unit status bar.

        Returns:
            Game unit if a card was clicked, None otherwise
        """
        for card in self.unit_cards:
            if card.contains_point(mouse_pos):
                # Don't select dead units
                if not card.is_dead:
                    return card.game_unit
        return None

    def get_height(self) -> int:
        """Calculate total height needed for this component."""
        if not self.unit_cards:
            return TITLE_HEIGHT

        num_rows = (len(self.unit_cards) + CARDS_PER_ROW - 1) // CARDS_PER_ROW
        return TITLE_HEIGHT + num_rows * (UNIT_CARD_HEIGHT + CARD_PADDING) + CARD_PADDING
