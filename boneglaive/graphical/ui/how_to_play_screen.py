#!/usr/bin/env python3
"""
How to Play Screen
Game manual explaining core mechanics and objectives.
"""
import pygame
from typing import Optional, Tuple
from .menu_components import COLOR_BG, COLOR_TEXT, COLOR_BONE, draw_glaive_icon, COLOR_METAL
from .scrollbar import Scrollbar


# Colors for sections
COLOR_HEADING = (255, 200, 100)
COLOR_SUBHEADING = (180, 160, 165)
COLOR_BODY = (220, 220, 220)
COLOR_BORDER = (80, 84, 92)


class HowToPlayScreen:
    """Screen displaying game manual and mechanics."""

    def __init__(self, font: pygame.font.Font, large_font: pygame.font.Font, screen_width: int, screen_height: int):
        self.font = font
        self.large_font = large_font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.activation_timer = 0.0

        # Scrolling
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scrollbar = Scrollbar()

        # Content surface (rendered once)
        self.content_surface = None
        self.content_width = 700
        self.line_height = 28

    def _render_content(self):
        """Render the manual content to a surface."""
        # Content sections with (text, font, color) tuples
        sections = [
            # Title
            ("HOW TO PLAY", self.large_font, COLOR_HEADING),
            ("", self.font, COLOR_BODY),  # Spacing

            # Victory Condition
            ("Victory Condition", self.font, COLOR_SUBHEADING),
            ("The first player to reach 7 GP wins the match.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            # Setup Phase
            ("Setup Phase", self.font, COLOR_SUBHEADING),
            ("Before the battle begins, each player selects 3 units to deploy. You must choose 3 different unit types. Duplicate units are not allowed during setup.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Position your units carefully on your side of the battlefield. Your starting positions can greatly influence your early game strategy and control of key areas.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            # Earning GP
            ("Earning GP", self.font, COLOR_SUBHEADING),
            ("Each time you kill an enemy main unit, you are awarded 1 GP. The match continues until one player reaches 7 GP. Summoned units do not award GP when destroyed.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            # Turn Structure
            ("Turn Structure", self.font, COLOR_SUBHEADING),
            ("Each turn consists of two phases. During the Planning Phase, you issue commands to your units. You can set movement destinations, select attack targets, and choose skills to activate.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Once you finish planning and execute your turn, the Execution Phase begins. All planned actions resolve in sequence based on the order in which they were issued. After all actions complete, control passes to your opponent for their turn.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            # Upgrade Points
            ("Upgrade Point Thresholds", self.font, COLOR_SUBHEADING),
            ("When the combined GP of both players reaches certain milestones, both players receive Upgrade Points. These thresholds occur at 2, 4, and 6 combined GP.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("At the first threshold (2 combined GP), each player receives 2 Upgrade Points. The player currently in the lead receives a bonus of 1 additional Upgrade Point for a total of 3. At the second and third thresholds (4 and 6 combined GP), each player receives 1 Upgrade Point, with the leader receiving a bonus of 1 additional Upgrade Point for a total of 2. If the players are tied at a threshold, both players receive only the base Upgrade Points with no bonus.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Upgrade Points are used to permanently enhance your units' skills during the match. Each threshold only triggers once per game.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            # Respawn System
            ("Respawn System", self.font, COLOR_SUBHEADING),
            ("When a unit is killed, it is not permanently removed from the battle. Instead, dead units enter a respawn queue with a 3 turn countdown timer. Once the timer expires, you may select a spawn location to return the unit to the battlefield.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),
            ("Units return with full health and retain any skill upgrades they earned before death. This system keeps battles dynamic and prevents early leads from becoming insurmountable.", self.font, COLOR_BODY),
            ("", self.font, COLOR_BODY),

            # Controls hint
            ("Basic Controls", self.font, COLOR_SUBHEADING),
            ("Use the mouse to select units, choose targets, and navigate menus. Skills can be activated using hotkeys 1 through 4, Q, and R. Press E to execute your planned turn. Press ESC to cancel selections or return to previous menus.", self.font, COLOR_BODY),
        ]

        # Calculate total height needed
        y = 30
        line_heights = []
        for text, font, color in sections:
            if text:
                # Wrap text
                words = text.split()
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_width = font.size(test_line)[0]

                    if test_width <= self.content_width - 40:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word

                if current_line:
                    lines.append(current_line)

                # Each wrapped line takes line_height
                for line in lines:
                    line_heights.append((line, font, color, self.line_height))
                    y += self.line_height
            else:
                # Blank line spacing
                line_heights.append(("", font, color, 15))
                y += 15

        # Create surface with calculated height
        total_height = y + 30
        self.content_surface = pygame.Surface((self.content_width, total_height), pygame.SRCALPHA)
        self.content_surface.fill((0, 0, 0, 0))

        # Render all lines
        y_pos = 30
        for text, font, color, height in line_heights:
            if text:
                text_surface = font.render(text, True, color)
                self.content_surface.blit(text_surface, (20, y_pos))
            y_pos += height

    def on_enter(self):
        """Called when screen becomes active."""
        self.activation_timer = 0.0
        self.scroll_offset = 0
        if not self.content_surface:
            self._render_content()

    def on_exit(self):
        """Called when leaving screen."""
        pass

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events."""
        # Only accept input after 200ms to prevent click-through
        if self.activation_timer < 0.2:
            return None

        # Keyboard controls
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_UP:
                # Scroll up
                self.scroll_offset -= 40
                self.scroll_offset = max(0, self.scroll_offset)
                return None
            elif event.key == pygame.K_DOWN:
                # Scroll down
                self.scroll_offset += 40
                self.scroll_offset = min(self.max_scroll, self.scroll_offset)
                return None

        # Scrolling with mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            scroll_speed = 40
            self.scroll_offset -= event.y * scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            return None

        # Scrollbar interaction
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            result = self.scrollbar.handle_mouse_down(mouse_pos)
            if result is not None:
                if isinstance(result, float):
                    self.scroll_offset = int(result * self.max_scroll)
                    self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                return None

        if event.type == pygame.MOUSEBUTTONUP:
            self.scrollbar.handle_mouse_up()
            return None

        return None

    def _is_click_on_scrollbar(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if a click position is on the scrollbar."""
        panel_width = self.content_width + 60
        panel_x = (self.screen_width - panel_width) // 2
        scrollbar_x = panel_x + panel_width - 10

        # Simple check if x is near scrollbar
        return mouse_pos[0] >= scrollbar_x - 20

    def update(self, delta_time: float, mouse_pos, mouse_pressed):
        """Update screen state."""
        self.activation_timer += delta_time

        # Handle scrollbar dragging
        if mouse_pressed:  # Left mouse button (already extracted as bool)
            new_scroll = self.scrollbar.handle_mouse_motion(mouse_pos, self.scroll_offset, self.max_scroll)
            if new_scroll is not None:
                self.scroll_offset = new_scroll

    def draw(self, surface: pygame.Surface):
        """Draw the how to play screen."""
        surface.fill(COLOR_BG)

        # Draw decorative corner glaives
        draw_glaive_icon(surface, 40, 40, COLOR_METAL, length=60, pointing_right=True)
        draw_glaive_icon(surface, self.screen_width - 100, 40, COLOR_METAL, length=60, pointing_right=False)

        # Panel dimensions
        panel_width = self.content_width + 60
        panel_height = self.screen_height - 100
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 50

        # Calculate max scroll
        if self.content_surface:
            content_height = self.content_surface.get_height()
            visible_height = panel_height - 100
            self.max_scroll = max(0, content_height - visible_height)

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, (25, 28, 32), panel_rect)
        pygame.draw.rect(surface, COLOR_BORDER, panel_rect, 3)

        # Draw title bar
        title_bar_rect = pygame.Rect(panel_x, panel_y, panel_width, 60)
        pygame.draw.rect(surface, (40, 44, 52), title_bar_rect)
        pygame.draw.line(surface, COLOR_BORDER, (panel_x, panel_y + 60), (panel_x + panel_width, panel_y + 60), 2)

        title = self.large_font.render("GAME MANUAL", True, COLOR_HEADING)
        title_rect = title.get_rect(centerx=panel_x + panel_width // 2, centery=panel_y + 30)
        surface.blit(title, title_rect)

        # Draw instructions
        instructions = "[ESC] Close  [↑/↓/Scroll] Navigate"
        instr_surface = self.font.render(instructions, True, (150, 150, 150))
        instr_rect = instr_surface.get_rect(centerx=panel_x + panel_width // 2, top=panel_y + panel_height - 35)
        surface.blit(instr_surface, instr_rect)

        # Set up clipping region for scrollable content
        content_y = panel_y + 70
        visible_height = panel_height - 110
        content_rect = pygame.Rect(panel_x + 30, content_y, self.content_width, visible_height)
        surface.set_clip(content_rect)

        # Draw content with scroll offset
        if self.content_surface:
            surface.blit(self.content_surface, (panel_x + 30, content_y - self.scroll_offset))

        # Clear clipping
        surface.set_clip(None)

        # Draw scrollbar
        scrollbar_x = panel_x + panel_width - 10
        scrollbar_y = content_y
        if self.content_surface:
            content_height = self.content_surface.get_height()
            self.scrollbar.draw(surface, scrollbar_x, scrollbar_y, visible_height,
                               self.scroll_offset, self.max_scroll, visible_height, content_height)
