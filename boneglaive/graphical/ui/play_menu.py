#!/usr/bin/env python3
"""
Play Menu Screens
Screens for game mode selection and map selection.
"""
import pygame
import os
from typing import Optional, List
from .menu_components import MenuScreen, Button, COLOR_TEXT, COLOR_BG
from boneglaive.utils.config import ConfigManager, NetworkMode
from boneglaive.game.map import MapFactory


class PlaySubmenu(MenuScreen):
    """Submenu for selecting game mode."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Play Game", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()

        # Use shared kaleidoscope background
        self.background = shared_background
        self.background_alpha = 0.15  # Very dim

        # Button dimensions
        button_width = 300
        button_height = 60
        button_spacing = 20

        # Calculate center position
        start_x = (screen_width - button_width) // 2
        start_y = 280

        # Create buttons
        self.buttons = [
            Button(
                start_x, start_y,
                button_width, button_height,
                "VS AI",
                font,
                lambda: self._set_action("vs_ai")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing),
                button_width, button_height,
                "Local Multiplayer",
                font,
                lambda: self._set_action("local_mp")
            ),
            Button(
                start_x, start_y + (button_height + button_spacing) * 2,
                button_width, button_height,
                "Back",
                font,
                lambda: self._set_action("back"),
                glaive_direction="left"
            )
        ]

        self._action_result = None

    def _set_action(self, action: str):
        """Set the action result and configure game mode."""
        if action == "vs_ai":
            self.config.set('network_mode', NetworkMode.VS_AI.value)
            self.config.save_config()
        elif action == "local_mp":
            self.config.set('network_mode', NetworkMode.LOCAL_MULTIPLAYER.value)
            self.config.save_config()

        self._action_result = action

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update screen state."""
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.background.update(delta_time)

    def draw(self, surface: pygame.Surface):
        """Draw the menu with dimmed background."""
        # Draw dimmed kaleidoscope
        self.background.draw(surface)

        # Draw dark overlay to dim it
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, int(255 * (1.0 - self.background_alpha))))
        surface.blit(overlay, (0, 0))

        # Draw menu elements
        super().draw(surface)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events and return action if triggered."""
        super().handle_event(event)

        # Check if action was set by button
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action

        return None


class MapSelectionMenu(MenuScreen):
    """Menu for selecting a map to play on."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Select Map", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = ConfigManager()

        # Use shared kaleidoscope background
        self.background = shared_background
        self.background_alpha = 0.15  # Very dim

        # Get available maps
        self.available_maps = MapFactory.list_available_maps()

        # Button dimensions (larger to accommodate icons)
        self.button_width = 500
        self.button_height = 90
        self.button_spacing = 15
        button_width = self.button_width
        button_height = self.button_height
        button_spacing = self.button_spacing

        # Calculate layout
        start_x = (screen_width - button_width) // 2
        start_y = 200

        # Create buttons for each map
        self.buttons = []
        for i, map_name in enumerate(self.available_maps):
            # Create display name
            display_name = map_name.replace('_', ' ').title()

            # Load map icon
            map_icon = self._load_map_icon(map_name)

            y_pos = start_y + i * (button_height + button_spacing)

            self.buttons.append(
                Button(
                    start_x, y_pos,
                    button_width, button_height,
                    display_name,
                    font,
                    lambda mn=map_name: self._select_map(mn),
                    image=map_icon
                )
            )

        # Add Back button
        back_y = start_y + len(self.available_maps) * (button_height + button_spacing) + 30
        self.buttons.append(
            Button(
                start_x, back_y,
                button_width, button_height,
                "Back",
                font,
                lambda: self._set_action("back"),
                glaive_direction="left"
            )
        )

        self._action_result = None
        self.scroll_offset = 0
        self.max_visible_buttons = 8

    def _select_map(self, map_name: str):
        """Select a map and proceed to game."""
        self.config.set('selected_map', map_name)
        self.config.save_config()
        self._action_result = "start_game"

    def _set_action(self, action: str):
        """Set the action result."""
        self._action_result = action

    def _load_map_icon(self, map_name: str) -> Optional[pygame.Surface]:
        """Load SVG icon for a map."""
        # Map names to icon filenames
        icon_map = {
            'lime_foyer': 'lime_foyer_icon.svg',
            'hard_pressed': 'hard_pressed_icon.svg',
            'stained_stones': 'stained_stones_icon.svg'
        }

        icon_filename = icon_map.get(map_name)
        if not icon_filename:
            return None

        icon_path = f"graphics/map_icons/{icon_filename}"
        if not os.path.exists(icon_path):
            return None

        try:
            # Try to load SVG using cairosvg
            try:
                import cairosvg
                from io import BytesIO
                # Convert SVG to PNG in memory (128x128 as that's the icon size)
                png_data = cairosvg.svg2png(url=icon_path, output_width=128, output_height=128)
                surface = pygame.image.load(BytesIO(png_data))
                surface = surface.convert_alpha()
                return surface
            except ImportError:
                return None
        except Exception as e:
            pass
            return None

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update screen state."""
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.background.update(delta_time)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events and return action if triggered."""
        # Handle scrolling if needed
        if event.type == pygame.MOUSEWHEEL:
            if len(self.buttons) > self.max_visible_buttons:
                self.scroll_offset -= event.y * 30
                # Use actual button height + spacing for scroll calculation
                button_step = self.button_height + self.button_spacing
                self.scroll_offset = max(0, min(self.scroll_offset,
                    (len(self.buttons) - self.max_visible_buttons) * button_step))

        super().handle_event(event)

        # Check if action was set by button
        if self._action_result:
            action = self._action_result
            self._action_result = None
            return action

        return None

    def draw(self, surface: pygame.Surface):
        """Draw the map selection menu with scroll support."""
        # Draw dimmed kaleidoscope
        self.background.draw(surface)

        # Draw dark overlay to dim it
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, int(255 * (1.0 - self.background_alpha))))
        surface.blit(overlay, (0, 0))

        # Draw menu elements
        super().draw(surface)

        # Draw scroll hint if needed
        if len(self.buttons) > self.max_visible_buttons:
            hint_text = "Scroll to see more maps"
            hint_surface = self.font.render(hint_text, True, (150, 150, 150))
            hint_rect = hint_surface.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 20)
            surface.blit(hint_surface, hint_rect)
