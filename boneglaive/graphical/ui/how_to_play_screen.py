#!/usr/bin/env python3
"""
How To Play Screen
Game manual with scrollable content.
"""
import pygame
from typing import Optional, Tuple
from .menu_components import (
    MenuScreen, MenuPanel, COLOR_TEXT, COLOR_TITLE,
    menu_button_width
)
from .scrollbar import Scrollbar

# In-content heading colors (not screen title — that uses COLOR_TITLE via MenuPanel)
COLOR_HEADING = (255, 200, 100)
COLOR_SUBHEADING = COLOR_TITLE
COLOR_BODY = (220, 220, 220)


class HowToPlayScreen(MenuScreen):
    """Screen displaying game manual and mechanics."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int, shared_background):
        super().__init__("Game Manual", font, large_font)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background = shared_background
        self.use_panel = False
        self.activation_timer = 0.0
        self.buttons = []

        # Scrolling
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scrollbar = Scrollbar()

        # Scale content dimensions
        self.content_width = max(500, int(screen_width * 0.55))
        self.line_height = max(24, int(screen_height * 0.045))
        self.content_surface = None

    def _render_content(self):
        """Render the manual content to a surface."""
        sections = [
            ("HOW TO PLAY", self.large_font, COLOR_HEADING),
            ("", self.font, COLOR_BODY),

            ("Victory Condition", self.font, COLOR_SUBHEADING),
            ("The first player to reach 7 GP wins the match.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            ("Setup Phase", self.font, COLOR_SUBHEADING),
            ("Before the battle begins, each player selects 3 units to deploy. You must choose 3 different unit types. You cannot field two of the same unit on your team.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Position your units carefully on your side of the battlefield. Your starting positions can greatly influence your early game strategy and control of key areas.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            ("Earning GP", self.font, COLOR_SUBHEADING),
            ("Each time you kill an enemy main unit, you are awarded 1 GP. The match continues until one player reaches 7 GP. Summoned units do not award GP when destroyed.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            ("Turn Structure", self.font, COLOR_SUBHEADING),
            ("Each turn consists of two phases. During the Planning Phase, you issue commands to your units. You can set movement destinations, select attack targets, and choose skills to activate.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Once you finish planning and execute your turn, the Execution Phase begins. All planned actions resolve in sequence based on the order in which they were issued. After all actions complete, control passes to your opponent for their turn.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Important: Movement must be issued before attacks or skills. Once a unit is assigned an attack or skill, it is locked in and cannot be moved that turn.", self.font, COLOR_HEADING),
            ("", self.font, COLOR_BODY),

            ("Upgrade Point Thresholds", self.font, COLOR_SUBHEADING),
            ("When the combined GP of both players reaches certain milestones, both players receive Upgrade Points. These thresholds occur at 2, 4, and 6 combined GP.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("At the first threshold (2 combined GP), each player receives 2 Upgrade Points. The player currently in the lead receives a bonus of 1 additional Upgrade Point for a total of 3. At the second and third thresholds (4 and 6 combined GP), each player receives 1 Upgrade Point, with the leader receiving a bonus of 1 additional Upgrade Point for a total of 2. If the players are tied at a threshold, both players receive only the base Upgrade Points with no bonus.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Upgrade Points are used to permanently enhance your units' skills during the match. Each threshold only triggers once per game.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            ("Respawn System", self.font, COLOR_SUBHEADING),
            ("When a unit is killed, it is not permanently removed from the battle. Instead, dead units enter a respawn queue with a 3 turn countdown timer. Once the timer expires, you may select a spawn location to return the unit to the battlefield.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Important: Respawning a unit takes effect when you execute your turn, not immediately. Select your spawn location during the Planning Phase, then execute to place the unit.", self.font, COLOR_HEADING),
            ("", self.font, COLOR_BODY),
            ("Units return with full health and retain any skill upgrades they earned before death. This system keeps battles dynamic and prevents early leads from becoming insurmountable.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            ("Basic Controls", self.font, COLOR_SUBHEADING),
            ("Use the mouse to select units, choose targets, and navigate menus. Skills can be activated using hotkeys 1 through 4, Q, and R. Press E to execute your planned turn. Press ESC to cancel selections or return to previous menus.", self.font, COLOR_BODY),
        ]

        # Word-wrap and calculate height
        blank_spacing = max(10, int(self.screen_height * 0.02))
        wrap_width = self.content_width - 40
        y = 30
        line_data = []

        for text, font, color in sections:
            if text:
                words = text.split()
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if font.size(test_line)[0] <= wrap_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)

                for line in lines:
                    line_data.append((line, font, color, self.line_height))
                    y += self.line_height
            else:
                line_data.append(("", font, color, blank_spacing))
                y += blank_spacing

        total_height = y + 30
        self.content_surface = pygame.Surface((self.content_width, total_height), pygame.SRCALPHA)
        self.content_surface.fill((0, 0, 0, 0))

        y_pos = 30
        for text, font, color, height in line_data:
            if text:
                text_surface = font.render(text, True, color)
                self.content_surface.blit(text_surface, (20, y_pos))
            y_pos += height

    def on_enter(self):
        self.activation_timer = 0.0
        self.scroll_offset = 0
        self.content_surface = None
        self._render_content()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.activation_timer < 0.2:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 40)
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 40)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * 40
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            result = self.scrollbar.handle_mouse_down(pygame.mouse.get_pos())
            if result is not None and isinstance(result, float):
                self.scroll_offset = int(result * self.max_scroll)
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

        if event.type == pygame.MOUSEBUTTONUP:
            self.scrollbar.handle_mouse_up()

        return None

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        super().update(delta_time, mouse_pos, mouse_pressed)
        self.activation_timer += delta_time

        if mouse_pressed:
            new_scroll = self.scrollbar.handle_mouse_motion(mouse_pos, self.scroll_offset, self.max_scroll)
            if new_scroll is not None:
                self.scroll_offset = new_scroll

    def draw(self, surface: pygame.Surface):
        self._draw_dimmed_background(surface)
        self._draw_background_decorations(surface)

        # Panel dimensions — scaled
        panel_padding = max(40, int(self.screen_width * 0.03))
        panel_width = self.content_width + panel_padding * 2
        panel_height = self.screen_height - int(self.screen_height * 0.125)
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = int(self.screen_height * 0.0625)

        # Draw panel
        panel = MenuPanel(panel_x, panel_y, panel_width, panel_height, "Game Manual")
        panel.draw(surface, self.large_font)

        # Calculate scroll bounds
        title_bar_h = 80
        footer_h = 40
        content_y = panel_y + title_bar_h
        visible_height = panel_height - title_bar_h - footer_h

        if self.content_surface:
            content_height = self.content_surface.get_height()
            self.max_scroll = max(0, content_height - visible_height)

        # Instructions at bottom of panel
        instructions = "[ESC] Close  [↑/↓/Scroll] Navigate"
        instr_surface = self.font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_surface.get_rect(centerx=panel_x + panel_width // 2, top=panel_y + panel_height - footer_h + 5)
        surface.blit(instr_surface, instr_rect)

        # Clip and draw scrollable content
        content_rect = pygame.Rect(panel_x + panel_padding, content_y, self.content_width, visible_height)
        surface.set_clip(content_rect)

        if self.content_surface:
            surface.blit(self.content_surface, (panel_x + panel_padding, content_y - self.scroll_offset))

        surface.set_clip(None)

        # Scrollbar
        scrollbar_x = panel_x + panel_width - 10
        if self.content_surface:
            content_height = self.content_surface.get_height()
            self.scrollbar.draw(surface, scrollbar_x, content_y, visible_height,
                               self.scroll_offset, self.max_scroll, visible_height, content_height)
