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

# Colors - matching bone/industrial theme
COLOR_BG_TOP = (42, 42, 47)  # Panel top
COLOR_BG_BOTTOM = (26, 26, 31)  # Panel bottom (gradient)
COLOR_BG_SKILL_TOP = (90, 60, 130)  # Purple gradient top for skill queued
COLOR_BG_SKILL_BOTTOM = (60, 40, 90)  # Purple gradient bottom for skill queued
COLOR_BG_ATTACK_TOP = (130, 50, 50)  # Red gradient top for attack queued
COLOR_BG_ATTACK_BOTTOM = (90, 30, 30)  # Red gradient bottom for attack queued
COLOR_PLAYER1 = (100, 255, 100)  # Green
COLOR_PLAYER2 = (100, 150, 255)  # Blue
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_DIM = (180, 160, 165)  # Muted bone
COLOR_BORDER = (90, 84, 79)  # Metal border
COLOR_BORDER_ACTIVE = (184, 168, 149)  # Bone border for active
COLOR_BORDER_ACTED = (70, 70, 70)  # Darker for acted units
COLOR_BORDER_SELECTED = (255, 200, 100)  # Gold for selected
COLOR_BORDER_SKILL = (140, 80, 200)  # Purple border for skill queued (matching spinning tools)
COLOR_BORDER_ATTACK = (255, 80, 80)  # Red border for attack queued (matching spinning glaives)
COLOR_BORDER_DEAD = (60, 60, 60)
COLOR_HP_BAR_BG = (40, 40, 40)
COLOR_HP_BAR_FULL = (100, 255, 100)
COLOR_HP_BAR_MID = (255, 200, 100)
COLOR_HP_BAR_LOW = (255, 100, 100)

# Import scaling utilities
from .scale_utils import scale_manager

# Scale panel dimensions based on resolution
PANEL_WIDTH = scale_manager.left_panel_width
UNIT_CARD_WIDTH = scale_manager.scale(84, 'x')
UNIT_CARD_HEIGHT = scale_manager.scale(70, 'y')
CARD_PADDING = scale_manager.scale(6)
CARDS_PER_ROW = 3
TITLE_HEIGHT = scale_manager.scale(35, 'y')
HP_BAR_HEIGHT = scale_manager.scale(4, 'y')
SPRITE_SIZE = scale_manager.scale(32, 'uniform')


class UnitCard:
    """Individual unit card in the status bar."""

    def __init__(self, game_unit, is_dead: bool = False):
        self.game_unit = game_unit
        self.is_dead = is_dead
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
                png_data = cairosvg.svg2png(url=sprite_path, output_width=SPRITE_SIZE, output_height=SPRITE_SIZE)
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
                self.sprite_surface = pygame.transform.scale(self.sprite_surface, (SPRITE_SIZE, SPRITE_SIZE))
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

            # Special handling for doppelganger units
            if hasattr(unit, 'is_doppelganger') and unit.is_doppelganger:
                return 'ψ'  # Lowercase psi for doppelgangers

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

    def has_queued_actions(self) -> bool:
        """Check if unit has queued attack or skill (not just move)."""
        if self.is_dead:
            return False
        return (
            (hasattr(self.game_unit, 'attack_target') and self.game_unit.attack_target) or
            (hasattr(self.game_unit, 'skill_target') and self.game_unit.skill_target)
        )

    def has_queued_skill(self) -> bool:
        """Check if unit has specifically queued a skill."""
        if self.is_dead:
            return False
        return hasattr(self.game_unit, 'skill_target') and self.game_unit.skill_target

    def has_queued_attack(self) -> bool:
        """Check if unit has specifically queued an attack."""
        if self.is_dead:
            return False
        return hasattr(self.game_unit, 'attack_target') and self.game_unit.attack_target

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

        # Check if unit has queued skill or attack for colored background
        has_skill_queued = self.has_queued_skill()
        has_attack_queued = self.has_queued_attack()

        # Determine border color and background colors based on state
        # Priority: skill takes precedence over attack if both are queued
        if self.is_dead:
            border_color = COLOR_BORDER_DEAD
            bg_alpha = 150
            bg_top = COLOR_BG_TOP
            bg_bottom = COLOR_BG_BOTTOM
        elif is_selected:
            border_color = COLOR_BORDER_SELECTED
            bg_alpha = 220
            # Use purple background if skill queued, red if attack queued
            if has_skill_queued:
                bg_top = COLOR_BG_SKILL_TOP
                bg_bottom = COLOR_BG_SKILL_BOTTOM
            elif has_attack_queued:
                bg_top = COLOR_BG_ATTACK_TOP
                bg_bottom = COLOR_BG_ATTACK_BOTTOM
            else:
                bg_top = COLOR_BG_TOP
                bg_bottom = COLOR_BG_BOTTOM
        elif has_skill_queued:
            # Purple background and border for skill queued
            border_color = COLOR_BORDER_SKILL
            bg_alpha = 220
            bg_top = COLOR_BG_SKILL_TOP
            bg_bottom = COLOR_BG_SKILL_BOTTOM
        elif has_attack_queued:
            # Red background and border for attack queued
            border_color = COLOR_BORDER_ATTACK
            bg_alpha = 220
            bg_top = COLOR_BG_ATTACK_TOP
            bg_bottom = COLOR_BG_ATTACK_BOTTOM
        elif self.is_active():
            border_color = player_color
            bg_alpha = 200
            bg_top = COLOR_BG_TOP
            bg_bottom = COLOR_BG_BOTTOM
        else:
            border_color = COLOR_BORDER_ACTED
            bg_alpha = 180
            bg_top = COLOR_BG_TOP
            bg_bottom = COLOR_BG_BOTTOM

        # Draw shadow (2px offset) - enhanced for more dimensionality
        shadow_rect = self.rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=3)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw gradient background (purple if skill queued, red if attack queued, normal otherwise)
        from .menu_components import draw_gradient_rect, draw_glow_rect
        draw_gradient_rect(surface, self.rect, bg_top, bg_bottom, alpha=bg_alpha)

        # Draw glow effect if hovered or selected
        if self.hovered or is_selected:
            glow_color = (255, 170, 119) if self.hovered else border_color
            draw_glow_rect(surface, self.rect, glow_color, intensity=0.4, width=1)

        # Draw border (thicker if hovered or selected)
        border_width = 3 if (self.hovered or is_selected) else 2
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=3)

        # Draw unit sprite at top (if available)
        sprite_y_offset = 5
        if self.sprite_surface:
            sprite_x = x + (UNIT_CARD_WIDTH - SPRITE_SIZE) // 2
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
        text_y = y + sprite_y_offset + SPRITE_SIZE + 10
        text_surface = render_fitted_text(
            display_text,
            max_width=UNIT_CARD_WIDTH - 6,
            max_height=18,
            color=text_color,
            base_font_size=16,
            min_font_size=12,
            max_font_size=18
        )
        text_rect = text_surface.get_rect(center=(x + UNIT_CARD_WIDTH // 2, text_y))
        surface.blit(text_surface, text_rect)

        # Draw READY badge for units with queued actions
        if not self.is_dead and self.has_queued_actions():
            ready_badge_y = y + UNIT_CARD_HEIGHT - HP_BAR_HEIGHT - 16
            ready_text = render_fitted_text(
                "READY",
                max_width=UNIT_CARD_WIDTH - 10,
                max_height=12,
                color=(150, 255, 150) if self.game_unit.player == 1 else (150, 200, 255),
                base_font_size=12,
                min_font_size=10,
                max_font_size=14
            )
            ready_rect = ready_text.get_rect(
                center=(x + UNIT_CARD_WIDTH // 2, ready_badge_y)
            )
            surface.blit(ready_text, ready_rect)

        # Draw HP bar for alive units
        if not self.is_dead:
            self._draw_hp_bar(surface, x, y + UNIT_CARD_HEIGHT - HP_BAR_HEIGHT - 3)
        else:
            # Draw respawn timer for dead units
            if self.respawn_timer > 0:
                timer_text = render_fitted_text(
                    str(self.respawn_timer),
                    max_width=30,
                    max_height=18,
                    color=COLOR_TEXT_DIM,
                    base_font_size=16,
                    min_font_size=12,
                    max_font_size=20
                )
                timer_rect = timer_text.get_rect(
                    center=(x + UNIT_CARD_WIDTH // 2, y + UNIT_CARD_HEIGHT - 12)
                )
                surface.blit(timer_text, timer_rect)
            else:
                # Ready to respawn
                ready_text = render_fitted_text(
                    "READY",
                    max_width=UNIT_CARD_WIDTH - 10,
                    max_height=18,
                    color=COLOR_HP_BAR_FULL,
                    base_font_size=16,
                    min_font_size=12,
                    max_font_size=18
                )
                ready_rect = ready_text.get_rect(
                    center=(x + UNIT_CARD_WIDTH // 2, y + UNIT_CARD_HEIGHT - 12)
                )
                surface.blit(ready_text, ready_rect)

    def _draw_hp_bar(self, surface: pygame.Surface, x: int, y: int):
        """Draw HP bar for alive units with gradient."""
        if self.is_dead or not hasattr(self.game_unit, 'hp'):
            return

        from .menu_components import draw_gradient_rect

        current_hp = self.game_unit.hp
        max_hp = self.game_unit.max_hp
        hp_percent = current_hp / max_hp if max_hp > 0 else 0

        # Bar dimensions (full card width minus padding)
        bar_width = UNIT_CARD_WIDTH - 10
        bar_x = x + 5

        # Draw background with subtle shadow
        bg_rect = pygame.Rect(bar_x, y, bar_width, HP_BAR_HEIGHT)
        pygame.draw.rect(surface, COLOR_HP_BAR_BG, bg_rect, border_radius=2)

        # Draw HP fill with gradient
        if current_hp > 0:
            fill_width = int(bar_width * hp_percent)
            fill_rect = pygame.Rect(bar_x, y, fill_width, HP_BAR_HEIGHT)

            # Choose gradient colors based on HP percentage
            if hp_percent > 0.6:
                # Green gradient
                color_top = (120, 255, 120)  # Brighter green
                color_bottom = (80, 200, 80)  # Darker green
            elif hp_percent > 0.3:
                # Orange gradient
                color_top = (255, 220, 120)  # Brighter orange
                color_bottom = (200, 160, 80)  # Darker orange
            else:
                # Red gradient
                color_top = (255, 120, 120)  # Brighter red
                color_bottom = (200, 80, 80)  # Darker red

            draw_gradient_rect(surface, fill_rect, color_top, color_bottom)

            # Add subtle highlight on top edge
            if HP_BAR_HEIGHT >= 3:
                pygame.draw.line(surface, (255, 255, 255, 100),
                               (bar_x, y), (bar_x + fill_width, y), 1)

        # Draw border with rounded corners
        pygame.draw.rect(surface, (80, 80, 80), bg_rect, 1, border_radius=2)

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
            else:
                # Create new card and cache it
                card = UnitCard(unit, is_dead=False)
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
            else:
                # Create new card and cache it
                card = UnitCard(dead_unit, is_dead=True)
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

        # Draw title
        player_color = COLOR_PLAYER1 if self.current_player == 1 else COLOR_PLAYER2
        title_text = render_fitted_text(
            "YOUR UNITS",
            max_width=PANEL_WIDTH - 20,
            max_height=25,
            color=player_color,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )
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
