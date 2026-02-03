#!/usr/bin/env python3
"""
Unit Status Bar UI Component
Displays grid of unit cards showing alive/dead/selected status.
"""
import pygame
import os
from typing import List, Optional, Tuple, Dict
from boneglaive.utils.constants import UNIT_SYMBOLS
from .font_utils import render_fitted_text

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

PANEL_WIDTH_BASE = 280  # Base panel width
UNIT_CARD_WIDTH_BASE = 84  # Base card width
UNIT_CARD_HEIGHT_BASE = 70  # Base card height
CARD_PADDING_BASE = 6  # Base spacing
CARDS_PER_ROW = 3
TITLE_HEIGHT_BASE = 35  # Base space between title and cards
HP_BAR_HEIGHT_BASE = 4
SPRITE_SIZE_BASE = 32  # Base size of unit sprite in card


class UnitCard:
    """Individual unit card in the status bar."""

    def __init__(self, game_unit, is_dead: bool = False, layout=None):
        self.game_unit = game_unit
        self.is_dead = is_dead
        self.layout = layout
        self.rect = None
        self.hovered = False
        self.sprite_surface = None  # Cached sprite

        # Dead unit attributes (from DeadUnit class)
        self.respawn_timer = 0
        if is_dead and hasattr(game_unit, 'respawn_timer'):
            self.respawn_timer = game_unit.respawn_timer

        # Load sprite
        self._load_sprite()

    def _load_sprite(self):
        """Load and cache the unit's sprite."""
        try:
            # Calculate sprite size based on layout
            sprite_size = int(SPRITE_SIZE_BASE * self.layout.get_font_scale()) if self.layout else SPRITE_SIZE_BASE

            # Get unit type
            if self.is_dead:
                unit_type = self.game_unit.unit_type
            else:
                unit_type = self.game_unit.type

            # Convert unit type to sprite filename
            unit_type_name = str(unit_type).split('.')[-1].lower()
            sprite_path = f"graphics/units/{unit_type_name}.svg"

            if not os.path.exists(sprite_path):
                return

            # Try to load SVG using cairosvg
            try:
                import cairosvg
                from io import BytesIO
                # Convert SVG to PNG in memory
                png_data = cairosvg.svg2png(url=sprite_path, output_width=sprite_size, output_height=sprite_size)
                self.sprite_surface = pygame.image.load(BytesIO(png_data))
                self.sprite_surface = self.sprite_surface.convert_alpha()
                return
            except ImportError:
                pass  # cairosvg not available, try PNG fallback below
            except Exception as e:
                pass  # SVG loading failed, try PNG fallback below

            # Fallback: Try to load PNG version if it exists
            png_path = f"graphics/units/{unit_type_name}.png"
            if os.path.exists(png_path):
                self.sprite_surface = pygame.image.load(png_path)
                self.sprite_surface = pygame.transform.scale(self.sprite_surface, (sprite_size, sprite_size))
                self.sprite_surface = self.sprite_surface.convert_alpha()
        except Exception as e:
            pass  # Sprite loading failed, will fall back to text-only

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
        # Calculate dynamic dimensions
        card_width = int(UNIT_CARD_WIDTH_BASE * self.layout.get_font_scale()) if self.layout else UNIT_CARD_WIDTH_BASE
        card_height = int(UNIT_CARD_HEIGHT_BASE * self.layout.get_font_scale()) if self.layout else UNIT_CARD_HEIGHT_BASE
        sprite_size = int(SPRITE_SIZE_BASE * self.layout.get_font_scale()) if self.layout else SPRITE_SIZE_BASE
        hp_bar_height = int(HP_BAR_HEIGHT_BASE * self.layout.get_font_scale()) if self.layout else HP_BAR_HEIGHT_BASE

        self.rect = pygame.Rect(x, y, card_width, card_height)

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
        bg_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        bg_surface.fill((*COLOR_BG, bg_alpha))
        surface.blit(bg_surface, (x, y))

        # Draw border (thicker if hovered or selected)
        border_width = 3 if (self.hovered or is_selected) else 2
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw unit sprite at top (if available)
        sprite_y_offset = int(5 * self.layout.get_font_scale()) if self.layout else 5
        if self.sprite_surface:
            sprite_x = x + (card_width - sprite_size) // 2
            sprite_y = y + sprite_y_offset

            # Apply gray tint for dead units
            if self.is_dead:
                # Create grayscale version
                gray_sprite = self.sprite_surface.copy()
                arr = pygame.surfarray.pixels3d(gray_sprite)
                gray = (arr[:,:,0] * 0.3 + arr[:,:,1] * 0.59 + arr[:,:,2] * 0.11).astype('uint8')
                arr[:,:,0] = gray
                arr[:,:,1] = gray
                arr[:,:,2] = gray
                del arr
                surface.blit(gray_sprite, (sprite_x, sprite_y))
            else:
                surface.blit(self.sprite_surface, (sprite_x, sprite_y))

        # Draw unit symbol and Greek ID below sprite
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

        # Position text below sprite with more spacing
        text_y = y + sprite_y_offset + sprite_size + int(10 * self.layout.get_font_scale() if self.layout else 10)
        text_surface = render_fitted_text(
            display_text,
            max_width=card_width - int(6 * self.layout.get_font_scale() if self.layout else 6),
            max_height=int(18 * self.layout.get_font_scale() if self.layout else 18),
            color=text_color,
            base_font_size=int(16 * self.layout.get_font_scale() if self.layout else 16),
            min_font_size=int(12 * self.layout.get_font_scale() if self.layout else 12),
            max_font_size=int(18 * self.layout.get_font_scale() if self.layout else 18)
        )
        text_rect = text_surface.get_rect(center=(x + card_width // 2, text_y))
        surface.blit(text_surface, text_rect)

        # Draw HP bar for alive units
        if not self.is_dead:
            self._draw_hp_bar(surface, x, y + card_height - hp_bar_height - int(3 * self.layout.get_font_scale() if self.layout else 3), card_width, hp_bar_height)
        else:
            # Draw respawn timer for dead units
            if self.respawn_timer > 0:
                timer_text = render_fitted_text(
                    str(self.respawn_timer),
                    max_width=int(30 * self.layout.get_font_scale() if self.layout else 30),
                    max_height=int(18 * self.layout.get_font_scale() if self.layout else 18),
                    color=COLOR_TEXT_DIM,
                    base_font_size=int(16 * self.layout.get_font_scale() if self.layout else 16),
                    min_font_size=int(12 * self.layout.get_font_scale() if self.layout else 12),
                    max_font_size=int(20 * self.layout.get_font_scale() if self.layout else 20)
                )
                timer_rect = timer_text.get_rect(
                    center=(x + card_width // 2, y + card_height - int(12 * self.layout.get_font_scale() if self.layout else 12))
                )
                surface.blit(timer_text, timer_rect)
            else:
                # Ready to respawn
                ready_text = render_fitted_text(
                    "READY",
                    max_width=card_width - int(10 * self.layout.get_font_scale() if self.layout else 10),
                    max_height=int(18 * self.layout.get_font_scale() if self.layout else 18),
                    color=COLOR_HP_BAR_FULL,
                    base_font_size=int(16 * self.layout.get_font_scale() if self.layout else 16),
                    min_font_size=int(12 * self.layout.get_font_scale() if self.layout else 12),
                    max_font_size=int(18 * self.layout.get_font_scale() if self.layout else 18)
                )
                ready_rect = ready_text.get_rect(
                    center=(x + card_width // 2, y + card_height - int(12 * self.layout.get_font_scale() if self.layout else 12))
                )
                surface.blit(ready_text, ready_rect)

    def _draw_hp_bar(self, surface: pygame.Surface, x: int, y: int, card_width: int, bar_height: int):
        """Draw HP bar for alive units."""
        if self.is_dead or not hasattr(self.game_unit, 'hp'):
            return

        current_hp = self.game_unit.hp
        max_hp = self.game_unit.max_hp
        hp_percent = current_hp / max_hp if max_hp > 0 else 0

        # Bar dimensions (full card width minus padding)
        padding = int(10 * self.layout.get_font_scale() if self.layout else 10)
        bar_width = card_width - padding
        bar_x = x + padding // 2

        # Draw background
        pygame.draw.rect(surface, COLOR_HP_BAR_BG,
                        (bar_x, y, bar_width, bar_height))

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
                           (bar_x, y, fill_width, bar_height))

    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if position is inside this card."""
        if self.rect:
            return self.rect.collidepoint(pos)
        return False


class UnitStatusBar:
    """Status bar showing grid of unit cards for current player."""

    def __init__(self, font, small_font, layout=None):
        self.font = font
        self.small_font = small_font
        self.layout = layout
        self.current_player = 1
        self.unit_cards: List[UnitCard] = []
        self.hovered_card: Optional[UnitCard] = None
        self.selected_unit = None  # Reference to selected game unit

        # PERFORMANCE FIX: Cache unit cards to avoid recreating them every frame
        self._unit_card_cache: Dict[int, UnitCard] = {}  # id(unit) -> UnitCard

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

        # PERFORMANCE FIX: Only rebuild cards when units actually change
        # Instead of clearing and recreating every frame, reuse cached cards

        # Get alive units for current player
        alive_units = [u for u in game.units
                      if u.is_alive() and u.player == self.current_player]

        # Get dead units for current player
        dead_units = [du for du in game.dead_units
                     if du.player == self.current_player]

        # Build set of current unit IDs
        current_unit_ids = set()

        # Collect cards (reuse from cache or create new)
        new_unit_cards = []

        # Process alive units
        for unit in alive_units:
            unit_id = id(unit)
            current_unit_ids.add(unit_id)

            if unit_id in self._unit_card_cache:
                # Reuse existing card
                card = self._unit_card_cache[unit_id]
                card.is_dead = False  # Update status
                card.layout = self.layout  # Update layout reference
            else:
                # Create new card and cache it
                card = UnitCard(unit, is_dead=False, layout=self.layout)
                self._unit_card_cache[unit_id] = card

            new_unit_cards.append(card)

        # Process dead units
        for dead_unit in dead_units:
            unit_id = id(dead_unit)
            current_unit_ids.add(unit_id)

            if unit_id in self._unit_card_cache:
                # Reuse existing card
                card = self._unit_card_cache[unit_id]
                card.is_dead = True  # Update status
                card.respawn_timer = getattr(dead_unit, 'respawn_timer', 0)
                card.layout = self.layout  # Update layout reference
            else:
                # Create new card and cache it
                card = UnitCard(dead_unit, is_dead=True, layout=self.layout)
                self._unit_card_cache[unit_id] = card

            new_unit_cards.append(card)

        # Clean up cache - remove cards for units that no longer exist
        cached_ids = set(self._unit_card_cache.keys())
        stale_ids = cached_ids - current_unit_ids
        for stale_id in stale_ids:
            del self._unit_card_cache[stale_id]

        # Update card list
        self.unit_cards = new_unit_cards

        # Sort by greek_id for consistent display
        # During setup phase, greek_id might be None, so handle that case
        def sort_key(card):
            greek_id = getattr(card.game_unit, 'greek_id', None)
            if greek_id is None:
                # Use position as fallback during setup phase
                return (999, getattr(card.game_unit, 'y', 0), getattr(card.game_unit, 'x', 0))
            return (0, greek_id)

        self.unit_cards.sort(key=sort_key)

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw the unit status bar.

        Args:
            surface: Surface to draw on
            x, y: Position (top-left)
        """
        if not self.unit_cards:
            return

        # Calculate dynamic dimensions
        panel_width = int(PANEL_WIDTH_BASE * self.layout.get_font_scale()) if self.layout else PANEL_WIDTH_BASE
        title_height = int(TITLE_HEIGHT_BASE * self.layout.get_font_scale()) if self.layout else TITLE_HEIGHT_BASE
        card_width = int(UNIT_CARD_WIDTH_BASE * self.layout.get_font_scale()) if self.layout else UNIT_CARD_WIDTH_BASE
        card_height = int(UNIT_CARD_HEIGHT_BASE * self.layout.get_font_scale()) if self.layout else UNIT_CARD_HEIGHT_BASE
        card_padding = int(CARD_PADDING_BASE * self.layout.get_font_scale()) if self.layout else CARD_PADDING_BASE

        # Draw title
        player_color = COLOR_PLAYER1 if self.current_player == 1 else COLOR_PLAYER2
        title_text = render_fitted_text(
            "YOUR UNITS",
            max_width=panel_width - int(20 * self.layout.get_font_scale() if self.layout else 20),
            max_height=int(25 * self.layout.get_font_scale() if self.layout else 25),
            color=player_color,
            base_font_size=int(20 * self.layout.get_font_scale() if self.layout else 20),
            min_font_size=int(16 * self.layout.get_font_scale() if self.layout else 16),
            max_font_size=int(24 * self.layout.get_font_scale() if self.layout else 24)
        )
        surface.blit(title_text, (x + int(10 * self.layout.get_font_scale() if self.layout else 10), y + int(5 * self.layout.get_font_scale() if self.layout else 5)))

        # Calculate card grid starting position
        card_start_y = y + title_height

        # Draw unit cards in grid
        for i, card in enumerate(self.unit_cards):
            row = i // CARDS_PER_ROW
            col = i % CARDS_PER_ROW

            card_x = x + col * (card_width + card_padding) + card_padding
            card_y = card_start_y + row * (card_height + card_padding)

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
        title_height = int(TITLE_HEIGHT_BASE * self.layout.get_font_scale()) if self.layout else TITLE_HEIGHT_BASE
        card_height = int(UNIT_CARD_HEIGHT_BASE * self.layout.get_font_scale()) if self.layout else UNIT_CARD_HEIGHT_BASE
        card_padding = int(CARD_PADDING_BASE * self.layout.get_font_scale()) if self.layout else CARD_PADDING_BASE

        if not self.unit_cards:
            return title_height

        num_rows = (len(self.unit_cards) + CARDS_PER_ROW - 1) // CARDS_PER_ROW
        return title_height + num_rows * (card_height + card_padding) + card_padding
