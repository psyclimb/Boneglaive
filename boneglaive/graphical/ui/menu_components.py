#!/usr/bin/env python3
"""
Menu Components
Core reusable components for the graphical menu system.
"""
import pygame
from typing import Optional, Callable, Tuple

# Colors matching the in-game UI theme
COLOR_BG = (30, 34, 42)
COLOR_BG_HOVER = (50, 54, 62)
COLOR_BG_PRESSED = (40, 44, 52)
COLOR_BG_DISABLED = (40, 40, 40)
COLOR_BORDER = (100, 100, 100)
COLOR_BORDER_HOVER = (150, 150, 150)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DISABLED = (120, 120, 120)
COLOR_TEXT_INPUT_BG = (45, 49, 57)
COLOR_TEXT_INPUT_CURSOR = (100, 200, 255)


class Button:
    """
    A clickable button with hover and pressed states.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        font: pygame.font.Font,
        action: Optional[Callable] = None,
        enabled: bool = True
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.enabled = enabled

        # State
        self.hovered = False
        self.pressed = False

    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool):
        """Update button state based on mouse."""
        if not self.enabled:
            self.hovered = False
            self.pressed = False
            return

        # Check hover
        self.hovered = self.rect.collidepoint(mouse_pos)

        # Check pressed state
        if self.hovered and mouse_pressed:
            if not self.pressed:
                self.pressed = True
        else:
            # Button was released
            if self.pressed and self.hovered:
                # Trigger action on release
                if self.action:
                    self.action()
            self.pressed = False

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle a mouse click. Returns True if button was clicked.
        """
        if self.enabled and self.rect.collidepoint(mouse_pos):
            if self.action:
                self.action()
            return True
        return False

    def draw(self, surface: pygame.Surface):
        """Draw the button."""
        # Determine colors based on state
        if not self.enabled:
            bg_color = COLOR_BG_DISABLED
            border_color = COLOR_BORDER
            text_color = COLOR_TEXT_DISABLED
        elif self.pressed:
            bg_color = COLOR_BG_PRESSED
            border_color = COLOR_BORDER_HOVER
            text_color = COLOR_TEXT
        elif self.hovered:
            bg_color = COLOR_BG_HOVER
            border_color = COLOR_BORDER_HOVER
            text_color = COLOR_TEXT
        else:
            bg_color = COLOR_BG
            border_color = COLOR_BORDER
            text_color = COLOR_TEXT

        # Draw background
        pygame.draw.rect(surface, bg_color, self.rect)

        # Draw border
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw text (centered)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class MenuScreen:
    """
    Base class for menu screens.
    Provides common functionality for all menu screens.
    """

    def __init__(self, title: str, font: pygame.font.Font, large_font: pygame.font.Font):
        self.title = title
        self.font = font
        self.large_font = large_font
        self.buttons = []

    def on_enter(self):
        """Called when screen becomes active."""
        pass

    def on_exit(self):
        """Called when leaving screen."""
        pass

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle pygame event.
        Returns action string if an action should be taken, None otherwise.
        """
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Left click release - prevents click-through to next screen
            for button in self.buttons:
                if button.handle_click(event.pos):
                    break
        elif event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            # ESC key to go back - use KEYUP to prevent key-through
            return "back"
        return None

    def update(self, delta_time: float, mouse_pos: Tuple[int, int], mouse_pressed: bool):
        """Update screen state."""
        for button in self.buttons:
            button.update(mouse_pos, mouse_pressed)

    def draw(self, surface: pygame.Surface):
        """Draw the screen."""
        # Clear with background color
        surface.fill(COLOR_BG)

        # Draw title
        self._draw_title(surface)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

    def _draw_title(self, surface: pygame.Surface):
        """Draw screen title."""
        title_surface = self.large_font.render(self.title, True, COLOR_TEXT)
        title_rect = title_surface.get_rect(centerx=surface.get_width() // 2, top=40)
        surface.blit(title_surface, title_rect)


class TextInputDialog:
    """
    A dialog for text input (e.g., profile name entry).
    """

    def __init__(
        self,
        prompt: str,
        font: pygame.font.Font,
        max_length: int = 8,
        on_confirm: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable] = None
    ):
        self.prompt = prompt
        self.font = font
        self.max_length = max_length
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.text = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_rate = 0.5  # Seconds

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.
        Returns True if dialog should close, False otherwise.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Cancel
                if self.on_cancel:
                    self.on_cancel()
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Confirm
                if self.text.strip():
                    if self.on_confirm:
                        self.on_confirm(self.text.strip().upper())
                    return True
            elif event.key == pygame.K_BACKSPACE:
                # Delete character
                if self.text:
                    self.text = self.text[:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.text) < self.max_length:
                # Add character
                self.text += event.unicode.upper()

        return False

    def update(self, delta_time: float):
        """Update cursor blink."""
        self.cursor_timer += delta_time
        if self.cursor_timer >= self.cursor_blink_rate:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface: pygame.Surface):
        """Draw the input dialog."""
        width = surface.get_width()
        height = surface.get_height()

        # Draw semi-transparent overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Draw dialog box
        dialog_width = 500
        dialog_height = 200
        dialog_x = (width - dialog_width) // 2
        dialog_y = (height - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

        pygame.draw.rect(surface, COLOR_BG, dialog_rect)
        pygame.draw.rect(surface, COLOR_BORDER, dialog_rect, 2)

        # Draw prompt
        prompt_surface = self.font.render(self.prompt, True, COLOR_TEXT)
        prompt_rect = prompt_surface.get_rect(centerx=width // 2, top=dialog_y + 30)
        surface.blit(prompt_surface, prompt_rect)

        # Draw input box
        input_box_width = 250
        input_box_height = 40
        input_box_x = (width - input_box_width) // 2
        input_box_y = dialog_y + 80
        input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)

        pygame.draw.rect(surface, COLOR_TEXT_INPUT_BG, input_box_rect)
        pygame.draw.rect(surface, COLOR_BORDER, input_box_rect, 2)

        # Draw text
        text_surface = self.font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(centery=input_box_y + input_box_height // 2, left=input_box_x + 10)
        surface.blit(text_surface, text_rect)

        # Draw cursor
        if self.cursor_visible and len(self.text) < self.max_length:
            cursor_x = text_rect.right + 5
            cursor_y = input_box_y + 8
            pygame.draw.line(
                surface,
                COLOR_TEXT_INPUT_CURSOR,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + input_box_height - 16),
                2
            )

        # Draw instructions
        instructions = "(ENTER to confirm, ESC to cancel)"
        instr_surface = self.font.render(instructions, True, (180, 180, 180))
        instr_rect = instr_surface.get_rect(centerx=width // 2, top=input_box_y + input_box_height + 20)
        surface.blit(instr_surface, instr_rect)
