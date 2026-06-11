#!/usr/bin/env python3
"""
Menu Components
Core reusable components for the graphical menu system.
"""
import pygame
from typing import Optional, Callable, Tuple

# Colors matching the bone/industrial theme
COLOR_BG = (26, 26, 31)  # Dark background
COLOR_BG_DARK = (10, 10, 15)  # Very dark for gradients
COLOR_BG_HOVER = (106, 90, 95)  # Warmer hover
COLOR_BG_PRESSED = (74, 58, 63)  # Pressed state
COLOR_BG_DISABLED = (40, 40, 40)
COLOR_PANEL = (42, 42, 47)  # Panel backgrounds
COLOR_PANEL_DARK = (26, 26, 31)  # Panel gradient bottom
COLOR_BORDER = (90, 90, 90)  # Default border
COLOR_BORDER_HOVER = (184, 168, 149)  # Bone color for hover
COLOR_BORDER_GLOW = (255, 170, 119)  # Orange glow for hover
COLOR_TEXT = (240, 232, 216)  # Bone white text
COLOR_TEXT_HOVER = (240, 232, 216)  # Same but with glow
COLOR_TEXT_DISABLED = (120, 120, 120)
COLOR_TEXT_INPUT_BG = (45, 49, 57)
COLOR_TEXT_INPUT_CURSOR = (100, 200, 255)
COLOR_BONE = (224, 213, 197)  # Bone decorations
COLOR_BONE_DARK = (139, 115, 85)  # Bone shadow
COLOR_METAL = (74, 74, 79)  # Metal elements
COLOR_METAL_LIGHT = (138, 138, 138)  # Metal highlights
COLOR_TITLE = (180, 160, 165)  # Muted bone pink — canonical submenu title color

# Background dimming constants for submenus
BACKGROUND_DIM_ALPHA = 0.15  # Fraction of background visible through overlay
BACKGROUND_DIM_COLOR = (10, 10, 15)  # Overlay tint color


# --- Menu layout scaling functions ---
# All take screen dimensions and return pixel values that scale with resolution.

def menu_button_width(screen_width):
    return max(200, int(screen_width * 0.23))

def menu_button_height(screen_height):
    return max(40, int(screen_height * 0.07))

def menu_button_spacing(screen_height):
    return max(10, int(screen_height * 0.015))

def menu_start_y(screen_height):
    return int(screen_height * 0.35)

def map_button_width(screen_width):
    return max(350, int(screen_width * 0.39))

def map_button_height(screen_height):
    return max(60, int(screen_height * 0.11))


def draw_gradient_rect(surface: pygame.Surface, rect: pygame.Rect, color_top: Tuple[int, int, int],
                       color_bottom: Tuple[int, int, int], alpha: int = 255):
    """Draw a rectangle with vertical gradient."""
    temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

    for y in range(rect.height):
        ratio = y / rect.height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(temp_surface, (r, g, b, alpha), (0, y), (rect.width, y))

    surface.blit(temp_surface, rect.topleft)


def draw_glow_rect(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int],
                   intensity: float = 0.6, width: int = 1):
    """Draw a glowing border around a rectangle."""
    glow_surf = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
    glow_rect = pygame.Rect(5, 5, rect.width, rect.height)

    # Draw multiple layers for glow effect
    for i in range(3):
        alpha = int(intensity * 255 * (3 - i) / 3)
        offset = i + 1
        inflated = glow_rect.inflate(offset * 2, offset * 2)
        pygame.draw.rect(glow_surf, (*color, alpha), inflated, width)

    surface.blit(glow_surf, (rect.x - 5, rect.y - 5))


def draw_bone_corner(surface: pygame.Surface, x: int, y: int, radius: int = 8):
    """Draw a bone joint decoration at a corner."""
    # Main bone circle
    pygame.draw.circle(surface, COLOR_BONE, (x, y), radius)
    pygame.draw.circle(surface, COLOR_BONE_DARK, (x, y), radius, 2)
    # Inner detail
    pygame.draw.circle(surface, COLOR_BONE_DARK, (x, y), radius // 2, 1)


def draw_glaive_icon(surface: pygame.Surface, x: int, y: int, color: Tuple[int, int, int],
                     length: int = 20, pointing_right: bool = True):
    """Draw a small glaive icon (arrow/blade)."""
    if pointing_right:
        # Horizontal line
        pygame.draw.line(surface, color, (x, y), (x + length, y), 2)
        # Arrow head
        pygame.draw.polygon(surface, color, [
            (x + length, y),
            (x + length - 4, y - 3),
            (x + length - 4, y + 3)
        ])
    else:
        # Pointing left (for back buttons)
        pygame.draw.line(surface, color, (x + length, y), (x, y), 2)
        pygame.draw.polygon(surface, color, [
            (x, y),
            (x + 4, y - 3),
            (x + 4, y + 3)
        ])


def draw_glaive_star_icon(surface: pygame.Surface, x: int, y: int, size: float = 1.0):
    """Draw a six-pointed glaive star icon. x, y is center position."""
    import math

    # Scale factor
    s = size
    cx = int(x)
    cy = int(y)

    # Glaive dimensions (scaled)
    outer_radius = 15 * s
    inner_radius = 6 * s
    hub_radius = 4.5 * s

    # Metal colors
    blade_fill = (168, 168, 176)  # #A8A8B0
    blade_edge = (192, 192, 200)  # #C0C0C8
    hub_fill = (139, 111, 71)     # #8B6F47 (wood)
    hub_stroke = (107, 83, 53)    # #6B5335 (dark wood)

    # Draw 6 blades at 60-degree intervals
    for i in range(6):
        angle = math.radians(i * 60)

        # Outer point
        outer_x = cx + outer_radius * math.cos(angle)
        outer_y = cy + outer_radius * math.sin(angle)

        # Inner left point (perpendicular)
        left_angle = angle - math.radians(90)
        left_x = cx + inner_radius * math.cos(left_angle)
        left_y = cy + inner_radius * math.sin(left_angle)

        # Inner right point (perpendicular)
        right_angle = angle + math.radians(90)
        right_x = cx + inner_radius * math.cos(right_angle)
        right_y = cy + inner_radius * math.sin(right_angle)

        # Draw blade triangle
        blade_points = [
            (outer_x, outer_y),
            (left_x, left_y),
            (right_x, right_y)
        ]
        pygame.draw.polygon(surface, blade_fill, blade_points)
        pygame.draw.polygon(surface, blade_edge, blade_points, max(1, int(1 * s)))

    # Draw wooden center hub
    pygame.draw.circle(surface, hub_fill, (cx, cy), int(hub_radius))
    pygame.draw.circle(surface, hub_stroke, (cx, cy), int(hub_radius), max(1, int(1 * s)))


class MenuPanel:
    """A decorated panel with bone corners and gradient background."""

    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.corner_radius = 8
        self.bone_corner_radius = 8

    def draw(self, surface: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """Draw the panel with decorations."""
        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=self.corner_radius)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Main panel with gradient
        draw_gradient_rect(surface, self.rect, COLOR_PANEL, COLOR_PANEL_DARK, alpha=242)

        # Border
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, 2, border_radius=self.corner_radius)

        # Bone corner decorations
        padding = 8
        draw_bone_corner(surface, self.rect.left + padding, self.rect.top + padding, self.bone_corner_radius)
        draw_bone_corner(surface, self.rect.right - padding, self.rect.top + padding, self.bone_corner_radius)
        draw_bone_corner(surface, self.rect.left + padding, self.rect.bottom - padding, self.bone_corner_radius)
        draw_bone_corner(surface, self.rect.right - padding, self.rect.bottom - padding, self.bone_corner_radius)

        # Title bar if title provided
        if self.title and font:
            title_height = 70
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, title_height)

            # Title background (darker)
            title_surf = pygame.Surface((title_rect.width, title_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(title_surf, (26, 26, 31, 153), title_surf.get_rect(),
                           border_top_left_radius=self.corner_radius,
                           border_top_right_radius=self.corner_radius)
            surface.blit(title_surf, title_rect.topleft)

            title_surface = font.render(self.title, True, COLOR_TITLE)
            title_text_rect = title_surface.get_rect(center=(title_rect.centerx, title_rect.centery))

            # Glow effect
            glow_surface = font.render(self.title, True, COLOR_TITLE)
            for offset in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                glow_rect = title_text_rect.copy()
                glow_rect.x += offset[0]
                glow_rect.y += offset[1]
                surface.blit(glow_surface, glow_rect)

            surface.blit(title_surface, title_text_rect)

            # Decorative line under title
            line_y = title_rect.bottom + 10
            line_margin = 50
            pygame.draw.line(surface, COLOR_BONE_DARK,
                           (self.rect.x + line_margin, line_y),
                           (self.rect.right - line_margin, line_y), 1)
            pygame.draw.line(surface, COLOR_BONE,
                           (self.rect.x + line_margin, line_y + 1),
                           (self.rect.right - line_margin, line_y + 1), 1)


class Button:
    """
    A clickable button with hover and pressed states.
    Supports optional image/icon display.
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
        enabled: bool = True,
        image: Optional[pygame.Surface] = None,
        show_glaive: bool = True,
        glaive_direction: str = "right"  # "right" or "left"
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.enabled = enabled
        self.image = image
        self.show_glaive = show_glaive
        self.glaive_direction = glaive_direction

        # State
        self.hovered = False
        self.pressed = False
        self.clicked_this_frame = False  # Prevent double-triggering

    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool):
        """Update button state based on mouse."""
        if not self.enabled:
            self.hovered = False
            self.pressed = False
            self.clicked_this_frame = False
            return

        # Check hover
        self.hovered = self.rect.collidepoint(mouse_pos)

        # Check pressed state
        if self.hovered and mouse_pressed:
            if not self.pressed:
                self.pressed = True
        else:
            # Button was released
            if self.pressed and self.hovered and not self.clicked_this_frame:
                # Trigger action on release (only if not already clicked via handle_click)
                if self.action:
                    self.action()
            self.pressed = False
            self.clicked_this_frame = False  # Reset for next frame

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle a mouse click. Returns True if button was clicked.
        """
        if self.enabled and self.rect.collidepoint(mouse_pos):
            self.clicked_this_frame = True  # Mark as clicked to prevent double-trigger in update()
            if self.action:
                self.action()
            return True
        return False

    def draw(self, surface: pygame.Surface):
        """Draw the button with enhanced styling."""
        # Determine colors and styles based on state
        if not self.enabled:
            bg_top = COLOR_BG_DISABLED
            bg_bottom = COLOR_BG_DISABLED
            border_color = COLOR_BORDER
            text_color = COLOR_TEXT_DISABLED
            glaive_color = COLOR_METAL
            show_glow = False
        elif self.pressed:
            bg_top = COLOR_BG_PRESSED
            bg_bottom = (50, 40, 45)
            border_color = COLOR_BORDER_HOVER
            text_color = COLOR_TEXT_HOVER
            glaive_color = COLOR_BONE
            show_glow = False
        elif self.hovered:
            bg_top = COLOR_BG_HOVER
            bg_bottom = (74, 58, 63)
            border_color = COLOR_BORDER_HOVER
            text_color = COLOR_TEXT_HOVER
            glaive_color = COLOR_TEXT
            show_glow = True
        else:
            bg_top = COLOR_METAL
            bg_bottom = COLOR_METAL_LIGHT
            border_color = COLOR_BORDER
            text_color = (192, 181, 165)  # Slightly dimmed
            glaive_color = COLOR_METAL_LIGHT
            show_glow = False

        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 76), shadow_surf.get_rect(), border_radius=6)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw gradient background
        draw_gradient_rect(surface, self.rect, bg_top, bg_bottom)

        # Draw glow effect on hover
        if show_glow:
            draw_glow_rect(surface, self.rect, COLOR_BORDER_GLOW, intensity=0.6, width=1)

        # Draw border
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)

        # Draw glaive icon if enabled
        icon_x_offset = 20
        if self.show_glaive and not self.image:
            glaive_x = self.rect.x + icon_x_offset
            glaive_y = self.rect.centery
            pointing_right = self.glaive_direction == "right"
            draw_glaive_icon(surface, glaive_x, glaive_y, glaive_color, length=20, pointing_right=pointing_right)
            text_x_offset = 50  # Leave room for glaive
        else:
            text_x_offset = 20

        # Draw image if provided (left side)
        if self.image:
            # Scale image to fit button height with some padding
            img_height = int(self.rect.height * 0.8)
            img_width = int(self.image.get_width() * (img_height / self.image.get_height()))
            scaled_image = pygame.transform.smoothscale(self.image, (img_width, img_height))

            # Position image on left side with padding
            img_x = self.rect.x + 10
            img_y = self.rect.centery - img_height // 2
            surface.blit(scaled_image, (img_x, img_y))

            # Draw text to the right of image
            text_surface = self.font.render(self.text, True, text_color)
            text_x = img_x + img_width + 15
            text_y = self.rect.centery
            text_rect = text_surface.get_rect(midleft=(text_x, text_y))

            # Text glow on hover
            if show_glow:
                glow_surface = self.font.render(self.text, True, COLOR_BORDER_GLOW)
                for offset in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    glow_rect = text_rect.copy()
                    glow_rect.x += offset[0]
                    glow_rect.y += offset[1]
                    surface.blit(glow_surface, glow_rect)

            surface.blit(text_surface, text_rect)
        else:
            # Draw text (left-aligned with glaive icon)
            text_surface = self.font.render(self.text, True, text_color)
            text_rect = text_surface.get_rect(midleft=(self.rect.x + text_x_offset, self.rect.centery))

            # Text glow on hover
            if show_glow:
                glow_surface = self.font.render(self.text, True, COLOR_BORDER_GLOW)
                for offset in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    glow_rect = text_rect.copy()
                    glow_rect.x += offset[0]
                    glow_rect.y += offset[1]
                    surface.blit(glow_surface, glow_rect)

            surface.blit(text_surface, text_rect)


class Slider:
    """
    A horizontal slider with draggable handle for value selection.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        min_value: float = 0.0,
        max_value: float = 1.0,
        initial_value: float = 0.5,
        on_change: Optional[Callable[[float], None]] = None,
        label: str = "",
        font: Optional[pygame.font.Font] = None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.on_change = on_change
        self.label = label
        self.font = font

        # Handle dimensions
        self.handle_radius = height // 2 + 2
        self.track_height = height // 3

        # State
        self.dragging = False
        self.hovered = False

    def _value_to_position(self) -> int:
        """Convert current value to handle x position."""
        normalized = (self.value - self.min_value) / (self.max_value - self.min_value)
        return int(self.rect.x + normalized * self.rect.width)

    def _position_to_value(self, x: int) -> float:
        """Convert x position to value."""
        normalized = (x - self.rect.x) / self.rect.width
        normalized = max(0.0, min(1.0, normalized))
        return self.min_value + normalized * (self.max_value - self.min_value)

    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool):
        """Update slider state based on mouse."""
        handle_x = self._value_to_position()
        handle_rect = pygame.Rect(
            handle_x - self.handle_radius,
            self.rect.centery - self.handle_radius,
            self.handle_radius * 2,
            self.handle_radius * 2
        )

        # Check if mouse is over handle
        self.hovered = handle_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos)

        # Handle dragging
        if mouse_pressed:
            if self.hovered or self.dragging:
                self.dragging = True
                # Update value based on mouse position
                new_value = self._position_to_value(mouse_pos[0])
                if abs(new_value - self.value) > 0.001:  # Threshold to avoid spam
                    self.value = new_value
                    if self.on_change:
                        self.on_change(self.value)
        else:
            self.dragging = False

    def draw(self, surface: pygame.Surface):
        """Draw the slider."""
        # Draw label if provided
        if self.label and self.font:
            label_surface = self.font.render(self.label, True, COLOR_TEXT)
            label_rect = label_surface.get_rect(midleft=(self.rect.x, self.rect.y - 20))
            surface.blit(label_surface, label_rect)

        # Draw track background
        track_rect = pygame.Rect(
            self.rect.x,
            self.rect.centery - self.track_height // 2,
            self.rect.width,
            self.track_height
        )
        pygame.draw.rect(surface, COLOR_BG_HOVER, track_rect)
        pygame.draw.rect(surface, COLOR_BORDER, track_rect, 1)

        # Draw filled portion
        handle_x = self._value_to_position()
        filled_width = handle_x - self.rect.x
        if filled_width > 0:
            filled_rect = pygame.Rect(
                self.rect.x,
                self.rect.centery - self.track_height // 2,
                filled_width,
                self.track_height
            )
            pygame.draw.rect(surface, (100, 150, 200), filled_rect)

        # Draw handle (glaive star matching the attack button)
        glaive_size = 0.8  # Scaled to fit nicely on slider
        draw_glaive_star_icon(surface, handle_x, self.rect.centery, glaive_size)

        # Draw value percentage
        if self.font:
            percentage = int(self.value * 100)
            value_text = f"{percentage}%"
            value_surface = self.font.render(value_text, True, COLOR_TEXT)
            value_rect = value_surface.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
            surface.blit(value_surface, value_rect)


class Checkbox:
    """
    A clickable checkbox with checked/unchecked states.
    """

    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        label: str,
        font: pygame.font.Font,
        initial_checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None
    ):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.font = font
        self.checked = initial_checked
        self.on_change = on_change

        # State
        self.hovered = False

    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool):
        """Update checkbox state based on mouse."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle a mouse click. Returns True if checkbox was clicked."""
        if self.rect.collidepoint(mouse_pos):
            self.checked = not self.checked
            if self.on_change:
                self.on_change(self.checked)
            return True
        return False

    def draw(self, surface: pygame.Surface):
        """Draw the checkbox."""
        # Draw box
        bg_color = COLOR_BG_HOVER if self.hovered else COLOR_BG
        border_color = COLOR_BORDER_HOVER if self.hovered else COLOR_BORDER
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw checkmark if checked
        if self.checked:
            # Draw an X checkmark
            padding = 4
            pygame.draw.line(
                surface, COLOR_TEXT,
                (self.rect.left + padding, self.rect.top + padding),
                (self.rect.right - padding, self.rect.bottom - padding),
                3
            )
            pygame.draw.line(
                surface, COLOR_TEXT,
                (self.rect.right - padding, self.rect.top + padding),
                (self.rect.left + padding, self.rect.bottom - padding),
                3
            )

        # Draw label
        label_surface = self.font.render(self.label, True, COLOR_TEXT)
        label_rect = label_surface.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
        surface.blit(label_surface, label_rect)


class MenuScreen:
    """
    Base class for menu screens.
    Provides common functionality for all menu screens with enhanced styling.
    """

    def __init__(self, title: str, font: pygame.font.Font, large_font: pygame.font.Font):
        self.title = title
        self.font = font
        self.large_font = large_font
        self.buttons = []
        self.use_panel = True  # Whether to use a decorated panel
        self.panel = None  # Will be created if needed

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
            # Left click release - handle immediately for responsive UI
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
        if hasattr(self, 'background') and self.background is not None:
            self.background.update(delta_time)

    def _draw_dimmed_background(self, surface: pygame.Surface):
        """Draw shared kaleidoscope background with dimmed overlay, or flat fill as fallback."""
        if hasattr(self, 'background') and self.background is not None:
            self.background.draw(surface)
            overlay = pygame.Surface(
                (surface.get_width(), surface.get_height()), pygame.SRCALPHA
            )
            overlay.fill((*BACKGROUND_DIM_COLOR, int(255 * (1.0 - BACKGROUND_DIM_ALPHA))))
            surface.blit(overlay, (0, 0))
        else:
            surface.fill(COLOR_BG)

    def draw(self, surface: pygame.Surface):
        """Draw the screen with enhanced styling."""
        self._draw_dimmed_background(surface)

        # Draw decorative background elements (subtle)
        self._draw_background_decorations(surface)

        # Draw panel if enabled
        if self.use_panel and self.buttons:
            self._draw_panel(surface)

        # Draw title (if not using panel with title)
        if not self.use_panel:
            self._draw_title(surface)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # Draw bottom decorations
        self._draw_bottom_decorations(surface)

    def _draw_background_decorations(self, surface: pygame.Surface):
        """Draw subtle decorative elements in background."""
        width = surface.get_width()
        height = surface.get_height()

        # Subtle kaleidoscope-style shapes
        # Top left corner glaives
        draw_glaive_icon(surface, 40, 40, COLOR_METAL, length=60, pointing_right=True)

        # Top right corner glaive
        draw_glaive_icon(surface, width - 100, 40, COLOR_METAL, length=60, pointing_right=False)

    def _draw_panel(self, surface: pygame.Surface):
        """Draw the decorated panel behind content."""
        if not self.buttons:
            return

        width = surface.get_width()
        height = surface.get_height()

        # Calculate panel size based on buttons
        if self.buttons:
            # Find the bounding box of all buttons
            min_y = min(btn.rect.y for btn in self.buttons)
            max_y = max(btn.rect.bottom for btn in self.buttons)
            min_x = min(btn.rect.x for btn in self.buttons)
            max_x = max(btn.rect.right for btn in self.buttons)

            # Add padding
            padding = 40
            title_space = 100  # Extra space for title

            panel_x = min_x - padding
            panel_y = min_y - padding - title_space
            panel_width = max_x - min_x + padding * 2
            panel_height = max_y - min_y + padding * 2 + title_space

            # Create and draw panel
            self.panel = MenuPanel(panel_x, panel_y, panel_width, panel_height, self.title)
            self.panel.draw(surface, self.large_font)

    def _draw_title(self, surface: pygame.Surface):
        """Draw screen title (used when not using panel)."""
        title_surface = self.large_font.render(self.title, True, COLOR_TITLE)
        title_rect = title_surface.get_rect(centerx=surface.get_width() // 2, top=40)

        # Title glow
        glow_surface = self.large_font.render(self.title, True, COLOR_TITLE)
        for offset in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            glow_rect = title_rect.copy()
            glow_rect.x += offset[0]
            glow_rect.y += offset[1]
            surface.blit(glow_surface, glow_rect)

        surface.blit(title_surface, title_rect)

    def _draw_bottom_decorations(self, surface: pygame.Surface):
        """Draw decorative elements at bottom of screen."""
        width = surface.get_width()
        height = surface.get_height()

        # Decorative line for hints
        # This will be used if there's hint text
        pass


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
