#!/usr/bin/env python3
"""
Scrollbar Component for Graphical UI
Reusable scrollbar with click-and-drag support.
"""
import pygame
from typing import Optional, Tuple


# Colors
COLOR_SEPARATOR = (60, 64, 72)
COLOR_BORDER = (80, 84, 92)


class Scrollbar:
    """
    Reusable scrollbar component with drag support.

    Usage:
        scrollbar = Scrollbar()

        # In draw method:
        scrollbar.draw(surface, x, y, height, scroll_offset, max_scroll, visible_height, content_height)

        # In event handling:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            scrollbar.handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            scrollbar.handle_mouse_up()
        elif event.type == pygame.MOUSEMOTION:
            new_offset = scrollbar.handle_mouse_motion(event.pos, scroll_offset, max_scroll)
            if new_offset is not None:
                scroll_offset = new_offset
    """

    def __init__(self):
        """Initialize scrollbar component."""
        self.dragging = False
        self.drag_offset_in_thumb = 0  # Offset of click within thumb
        self.thumb_rect: Optional[pygame.Rect] = None
        self.track_rect: Optional[pygame.Rect] = None

    def draw(self, surface: pygame.Surface, x: int, y: int, height: int,
             scroll_offset: int, max_scroll: int, visible_height: int,
             content_height: int) -> None:
        """
        Draw the scrollbar.

        Args:
            surface: Surface to draw on
            x: X position of scrollbar (right edge)
            y: Y position of scrollbar (top)
            height: Height of scrollbar track
            scroll_offset: Current scroll offset
            max_scroll: Maximum scroll offset
            visible_height: Height of visible area
            content_height: Total content height
        """
        if max_scroll <= 0 or content_height <= visible_height:
            self.thumb_rect = None
            self.track_rect = None
            return

        scroll_pct = scroll_offset / max_scroll if max_scroll > 0 else 0

        # Track (thin line)
        track_rect = pygame.Rect(x - 15, y, 5, height)
        pygame.draw.rect(surface, COLOR_SEPARATOR, track_rect)
        self.track_rect = track_rect

        # Thumb (draggable handle)
        thumb_height = max(30, int(height * (visible_height / content_height)))
        thumb_y = y + int((height - thumb_height) * scroll_pct)
        thumb_rect = pygame.Rect(x - 18, thumb_y, 11, thumb_height)
        pygame.draw.rect(surface, COLOR_BORDER, thumb_rect)
        self.thumb_rect = thumb_rect

    def handle_mouse_down(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """
        Handle mouse button down event.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            New scroll offset if track was clicked (for jump-to), None otherwise
        """
        if not self.thumb_rect or not self.track_rect:
            return None

        # Check if clicked on thumb (start drag)
        if self.thumb_rect.collidepoint(mouse_pos):
            self.dragging = True
            # Store where in the thumb the user clicked
            self.drag_offset_in_thumb = mouse_pos[1] - self.thumb_rect.y
            return None

        # Check if clicked on track (jump to position)
        if self.track_rect.collidepoint(mouse_pos):
            track_click_y = mouse_pos[1] - self.track_rect.y
            scroll_pct = track_click_y / self.track_rect.height
            return scroll_pct  # Return percentage for caller to convert to scroll offset

        return None

    def handle_mouse_up(self) -> None:
        """Handle mouse button up event (stop dragging)."""
        self.dragging = False

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int],
                           current_scroll: int, max_scroll: int) -> Optional[int]:
        """
        Handle mouse motion for dragging.

        Args:
            mouse_pos: Mouse position (x, y)
            current_scroll: Current scroll offset (unused, kept for compatibility)
            max_scroll: Maximum scroll offset

        Returns:
            New scroll offset if dragging, None otherwise
        """
        if not self.dragging or not self.track_rect or not self.thumb_rect or max_scroll <= 0:
            return None

        # Calculate where the thumb center should be based on cursor position
        # Account for where the user grabbed the thumb
        desired_thumb_y = mouse_pos[1] - self.drag_offset_in_thumb

        # Convert thumb position to scroll percentage
        # The thumb can move within the track
        track_start = self.track_rect.y
        track_end = self.track_rect.y + self.track_rect.height
        thumb_height = self.thumb_rect.height

        # Available space for thumb movement
        available_space = self.track_rect.height - thumb_height

        if available_space <= 0:
            return 0

        # Calculate thumb position within available space
        thumb_pos_in_track = desired_thumb_y - track_start
        thumb_pos_in_track = max(0, min(thumb_pos_in_track, available_space))

        # Convert to scroll offset
        scroll_pct = thumb_pos_in_track / available_space if available_space > 0 else 0
        new_scroll = int(scroll_pct * max_scroll)
        return max(0, min(new_scroll, max_scroll))
