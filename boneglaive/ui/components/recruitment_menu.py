#!/usr/bin/env python3
"""
Recruitment menu UI component for unit selection during setup phase.
"""

import curses
from typing import List, Optional, Tuple
from boneglaive.utils.constants import UnitType, UNIT_STATS, UNIT_DISPLAY_NAMES, HEIGHT, WIDTH
from boneglaive.game.recruitment import recruitment_system
from boneglaive.utils.debug import logger
from boneglaive.game.units import Unit


class RecruitmentMenuComponent:
    """UI component for managing unit recruitment during setup phase."""
    
    def __init__(self, renderer, game_ui):
        self.renderer = renderer
        self.game_ui = game_ui
        self.selected_index = 0
        
        # Scrolling parameters
        self.scroll_offset = 0
        self.visible_items = 8  # Number of items visible in the panel at once
        
    def draw_recruitment_menu(self, y_offset=0, x_offset=0):
        """Draw the recruitment menu interface in side panel."""
        try:
            current_player = recruitment_system.get_current_player()
            if not current_player:
                self.renderer.draw_text(y_offset, x_offset, "Recruitment complete!", 1, curses.A_BOLD)
                return
            
            # Side panel width constraint
            panel_width = 30
            
            # Header with border
            header = f"┌─ PLAYER {current_player.player_id} RECRUITMENT ─────┐"
            self.renderer.draw_text(y_offset, x_offset, header[:panel_width], 1, curses.A_BOLD)
            y_offset += 1
            
            # Progress line
            progress = f"│ Units: {len(current_player.recruited_units)}/{current_player.max_units}"
            progress += " " * (panel_width - len(progress) - 1) + "│"
            self.renderer.draw_text(y_offset, x_offset, progress, 1)
            y_offset += 1
            
            # Separator
            separator = "├" + "─" * (panel_width - 2) + "┤"
            self.renderer.draw_text(y_offset, x_offset, separator, 1)
            y_offset += 1
            
            # Draw available units panel
            y_offset = self._draw_available_units_panel(y_offset, x_offset, panel_width)
            
            # Bottom border
            bottom = "└" + "─" * (panel_width - 2) + "┘"
            self.renderer.draw_text(y_offset, x_offset, bottom, 1)
                    
        except Exception as e:
            logger.error(f"Error drawing recruitment menu: {e}")
            self.renderer.draw_text(y_offset, x_offset, f"Error: {e}", 1)
    
    def _draw_available_units_panel(self, y_offset, x_offset, panel_width):
        """Draw the available units for recruitment in side panel format with scrolling."""
        # Available units header
        header = "│ Available Units:"
        header += " " * (panel_width - len(header) - 1) + "│"
        self.renderer.draw_text(y_offset, x_offset, header, 1, curses.A_BOLD)
        y_offset += 1
        
        current_pool = recruitment_system.get_current_player_pool()
        available_types = current_pool.get_available_types() if current_pool else []
        
        if not available_types:
            line = "│  No units available"
            line += " " * (panel_width - len(line) - 1) + "│"
            self.renderer.draw_text(y_offset, x_offset, line, 1)
            return y_offset + 1
        
        # Calculate scrolling parameters
        total_items = len(available_types)
        start_index = self.scroll_offset
        end_index = min(start_index + self.visible_items, total_items)
        
        # Show scroll indicator if needed
        if total_items > self.visible_items:
            scroll_info = f"│ ({start_index + 1}-{end_index}/{total_items})"
            scroll_info += " " * (panel_width - len(scroll_info) - 1) + "│"
            self.renderer.draw_text(y_offset, x_offset, scroll_info, 1)
            y_offset += 1
        
        # Draw visible items
        items_drawn = 0
        for i in range(start_index, end_index):
            if items_drawn >= self.visible_items:
                break
                
            unit_type = available_types[i]
            
            # Selection indicator and unit name
            selected = (i == self.selected_index)
            prefix = "▶" if selected else " "
            count = current_pool.get_available_count(unit_type) if current_pool else 0
            
            # Get shortened display name
            display_name = UNIT_DISPLAY_NAMES.get(unit_type, unit_type.name)
            
            unit_line = f"│ {prefix} {display_name} ({count})"
            unit_line += " " * (panel_width - len(unit_line) - 1) + "│"
            
            # Color coding - no highlight, just arrow indicator
            self.renderer.draw_text(y_offset, x_offset, unit_line, 1)
            y_offset += 1
            items_drawn += 1
            
        
        # Fill remaining space if needed
        while items_drawn < self.visible_items:
            empty_line = "│" + " " * (panel_width - 2) + "│"
            self.renderer.draw_text(y_offset, x_offset, empty_line, 1)
            y_offset += 1
            items_drawn += 1
        
        return y_offset
    
    
    def handle_input(self, key):
        """Handle input for the recruitment menu."""
        try:
            current_player = recruitment_system.get_current_player()
            if not current_player:
                return False
            
            return self._handle_available_panel_input(key, current_player)
                
        except Exception as e:
            logger.error(f"Error handling recruitment input: {e}")
            return False
    
    def _handle_available_panel_input(self, key, current_player):
        """Handle input for the available units panel with scrolling."""
        current_pool = recruitment_system.get_current_player_pool()
        available_types = current_pool.get_available_types() if current_pool else []
        
        # Debug: check if Player 2 has any units
        if key == 353 or key == ord('\t'):
            logger.debug(f"Player {current_player.player_id} pool: {current_pool}")
            logger.debug(f"Available types: {[ut.name for ut in available_types]}")
        
        if key == 353:  # Shift+Tab - move up in list
            if available_types:
                self.selected_index = (self.selected_index - 1) % len(available_types)
                # Adjust scroll offset if selection moves out of view
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
                return True
            return False
            
        elif key == ord('\t'):  # Tab - move down in list
            if available_types:
                self.selected_index = (self.selected_index + 1) % len(available_types)
                # Adjust scroll offset if selection moves out of view
                if self.selected_index >= self.scroll_offset + self.visible_items:
                    self.scroll_offset = self.selected_index - self.visible_items + 1
                return True
            return False
            
        elif key == ord('\n') or key == ord('\r'):  # Enter key - place unit at cursor
            if (available_types and 
                self.selected_index < len(available_types) and
                current_player.can_recruit_more()):
                
                unit_type = available_types[self.selected_index]
                return self._place_unit_at_cursor(unit_type, current_player, current_pool)
            return False
            
        elif key == ord('y') or key == ord('Y'):  # Confirm recruitment
            if current_player.is_complete():
                recruitment_system.confirm_current_player()
                # If this was player 2 confirming, start the game
                if recruitment_system.can_start_game():
                    self.game_ui.game.setup_phase = False
                    self.game_ui.game.resolve_unit_conflicts()
                    logger.info("Starting game after recruitment completion")
                return True
            return False
            
        return False
    
    def _place_unit_at_cursor(self, unit_type, current_player, current_pool):
        """Place a unit at the current cursor position, like the old setup phase."""
        cursor_pos = self.game_ui.cursor_manager.cursor_pos
        
        try:
            # Place unit using game's method (includes all validation)
            self.game_ui.game.add_unit(unit_type, current_player.player_id, cursor_pos.y, cursor_pos.x)
            
            # Update recruitment tracking
            current_pool.recruit_unit(unit_type)
            current_player.recruit_unit(unit_type)
            
            # Update menu selection if this type is exhausted
            if not current_pool.is_available(unit_type):
                available_types = current_pool.get_available_types()
                if available_types and self.selected_index >= len(available_types):
                    self.selected_index = len(available_types) - 1
            
            logger.info(f"Placed {unit_type.name} for player {current_player.player_id} at ({cursor_pos.y}, {cursor_pos.x})")
            return True
            
        except Exception as e:
            self.game_ui.message = f"Cannot place unit: {str(e)}"
            logger.error(f"Failed to place unit: {e}")
            return False
    
    def reset(self):
        """Reset the menu state."""
        self.selected_index = 0
        self.scroll_offset = 0