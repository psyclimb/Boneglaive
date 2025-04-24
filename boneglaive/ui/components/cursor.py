#!/usr/bin/env python3
from typing import Optional, List, Tuple

from boneglaive.utils.constants import HEIGHT, WIDTH
from boneglaive.utils.coordinates import Position
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.event_system import (
    EventType, CursorMovedEventData, UnitSelectedEventData, 
    UnitDeselectedEventData, MoveEventData, AttackEventData, 
    MessageDisplayEventData, UIRedrawEventData
)
from boneglaive.ui.components.base import UIComponent

# Cursor manager component
class CursorManager(UIComponent):
    """Component for managing cursor movement and selection."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)
        self.selected_unit = None
        self.highlighted_positions = []
    
    def _setup_event_handlers(self):
        """Set up event handlers for cursor manager."""
        # No event handlers needed initially - CursorManager is primarily an event publisher
        pass
    
    def move_cursor(self, dy: int, dx: int):
        """Move the cursor by the given delta."""
        previous_pos = self.cursor_pos
        new_y = max(0, min(HEIGHT-1, self.cursor_pos.y + dy))
        new_x = max(0, min(WIDTH-1, self.cursor_pos.x + dx))
        new_pos = Position(new_y, new_x)
        
        # Only publish event if position actually changed
        if new_pos != self.cursor_pos:
            self.cursor_pos = new_pos
            # Publish cursor moved event
            self.publish_event(
                EventType.CURSOR_MOVED, 
                CursorMovedEventData(position=self.cursor_pos, previous_position=previous_pos)
            )
            
    def move_cursor_diagonal(self, direction: str):
        """Move the cursor diagonally.
        
        Args:
            direction: One of "up-left", "up-right", "down-left", "down-right"
        """
        dy, dx = 0, 0
        
        if direction == "up-left":
            dy, dx = -1, -1
        elif direction == "up-right":
            dy, dx = -1, 1
        elif direction == "down-left":
            dy, dx = 1, -1
        elif direction == "down-right":
            dy, dx = 1, 1
            
        # Use the existing move_cursor method
        self.move_cursor(dy, dx)
    
    def can_act_this_turn(self):
        """Check if the player can act on the current turn."""
        # Always allow in test mode
        if self.game_ui.game.test_mode:
            return True
        
        # In multiplayer, check if it's the player's turn
        if self.game_ui.multiplayer.is_multiplayer():
            # In local multiplayer, can control active player's units
            if self.game_ui.multiplayer.is_local_multiplayer():
                return True
            # In network multiplayer, can only act on own turn
            return self.game_ui.multiplayer.is_current_player_turn()
        
        # Single player can always act
        return True
    
    def get_unit_at_cursor(self):
        """Get the unit at the current cursor position."""
        # First check for a real unit
        unit = self.game_ui.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
        
        # If no real unit, check for a ghost unit
        if not unit:
            unit = self.find_unit_by_ghost(self.cursor_pos.y, self.cursor_pos.x)
            
        return unit
    
    def can_select_unit(self, unit):
        """Check if the unit can be selected by the current player."""
        if not unit:
            return False
            
        current_player = self.game_ui.multiplayer.get_current_player()
        
        # Test mode can select any unit
        if self.game_ui.game.test_mode:
            return True
            
        # Local multiplayer can select current player's units
        if self.game_ui.multiplayer.is_local_multiplayer():
            return unit.player == self.game_ui.game.current_player
            
        # Otherwise, can only select own units
        return unit.player == current_player
    
    def select_unit_at_cursor(self):
        """Select the unit at the current cursor position.
        Returns True if a unit was selected, False otherwise.
        """
        # If there's already a selected unit, deselect it first
        if self.selected_unit:
            self._deselect_unit()
            
        unit = self.get_unit_at_cursor()
        
        if not unit or not self.can_select_unit(unit):
            if unit:
                # Show information about enemy unit instead of selection error
                # Use the unit's display name (includes Greek identifier) instead of "Player X's UNITTYPE"
                unit_info = f"{unit.get_display_name()} - HP: {unit.hp}/{unit.max_hp}"
                
                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=unit_info,
                        message_type=MessageType.SYSTEM,
                        log_message=False  # Don't add to message log
                    )
                )
            else:
                # Get information about what's at this position
                y, x = self.cursor_pos.y, self.cursor_pos.x
                
                # Check terrain type - we don't need to check for units again since that's handled in the 'if unit:' case above
                terrain = self.game_ui.game.map.get_terrain_at(y, x)
                terrain_name = terrain.name.lower().replace('_', ' ')
                
                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Tile: {terrain_name}",
                        message_type=MessageType.SYSTEM,
                        log_message=False  # Don't add to message log
                    )
                )
                
                # No message in log - this is just UI feedback
            return False
        
        # Select the unit
        self.selected_unit = unit
        
        # Check if we're selecting a ghost (unit with a move_target at current position)
        is_ghost = (unit.move_target == (self.cursor_pos.y, self.cursor_pos.x))
        
        # Clear the message by sending empty message event
        self.publish_event(
            EventType.MESSAGE_DISPLAY_REQUESTED,
            MessageDisplayEventData(message="")
        )
        
        # Publish unit selected event
        self.publish_event(
            EventType.UNIT_SELECTED,
            UnitSelectedEventData(unit=unit, position=self.cursor_pos)
        )
        
        # Request UI redraw to immediately show the selection
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        return True
    
    def _deselect_unit(self):
        """Deselect the currently selected unit."""
        if self.selected_unit:
            unit = self.selected_unit
            self.selected_unit = None
            self.highlighted_positions = []
            
            # Publish unit deselected event
            self.publish_event(
                EventType.UNIT_DESELECTED,
                UnitDeselectedEventData(unit=unit)
            )
    
    def select_move_target(self):
        """Select the current cursor position as a move target for the selected unit.
        Returns True if a move target was set, False otherwise.
        """
        # Import Position to use get_line
        from boneglaive.utils.coordinates import Position, get_line
        
        cursor_position = Position(self.cursor_pos.y, self.cursor_pos.x)
        
        # Check if the position is a valid move target
        if cursor_position in self.highlighted_positions:
            # Store the original position before changing it
            from_position = Position(self.selected_unit.y, self.selected_unit.x)
            to_position = cursor_position
            
            # Set the move target
            self.selected_unit.move_target = (to_position.y, to_position.x)
            
            # Track action order
            self.selected_unit.action_timestamp = self.game_ui.game.action_counter
            self.game_ui.game.action_counter += 1
            
            # Publish move planned event
            self.publish_event(
                EventType.MOVE_PLANNED,
                MoveEventData(
                    unit=self.selected_unit,
                    from_position=from_position,
                    to_position=to_position
                )
            )
            
            self.game_ui.message = f"Move set to ({to_position.y}, {to_position.x})"
            # No message added to log for planned movements
            self.highlighted_positions = []
            return True
        else:
            # Check why the position isn't valid
            y, x = self.cursor_pos.y, self.cursor_pos.x
            
            # Check if the position is in range
            distance = self.game_ui.game.chess_distance(self.selected_unit.y, self.selected_unit.x, y, x)
            if distance > self.selected_unit.move_range:
                self.game_ui.message = "Position is out of movement range"
            # Check if there's a unit blocking the path
            elif distance > 1:
                # Check the path for blocking units
                start_pos = Position(self.selected_unit.y, self.selected_unit.x)
                end_pos = Position(y, x)
                path = get_line(start_pos, end_pos)
                
                for pos in path[1:-1]:  # Skip start and end positions
                    blocking_unit = self.game_ui.game.get_unit_at(pos.y, pos.x)
                    if blocking_unit:
                        # Determine if it's an ally or enemy for the message
                        if blocking_unit.player == self.selected_unit.player:
                            self.game_ui.message = "Path blocked by allied unit"
                            message_log.add_message("You cannot move through other units", MessageType.WARNING)
                        else:
                            self.game_ui.message = "Path blocked by enemy unit"
                            message_log.add_message("You cannot move through other units", MessageType.WARNING)
                        return False
            # Check if there's a unit at the destination
            elif self.game_ui.game.get_unit_at(y, x):
                self.game_ui.message = "Position is occupied by another unit"
            # Check if the terrain is blocking
            elif not self.game_ui.game.map.is_passable(y, x):
                self.game_ui.message = "Terrain is impassable"
            else:
                self.game_ui.message = "Invalid move target"
            return False
    
    def select_attack_target(self):
        """Select the current cursor position as an attack target for the selected unit.
        Returns True if an attack target was set, False otherwise.
        """
        # Import Position for position checking
        from boneglaive.utils.coordinates import Position
        
        cursor_position = Position(self.cursor_pos.y, self.cursor_pos.x)
        
        if cursor_position in self.highlighted_positions:
            # Set the attack target
            self.selected_unit.attack_target = (self.cursor_pos.y, self.cursor_pos.x)
            
            # Track action order
            self.selected_unit.action_timestamp = self.game_ui.game.action_counter
            self.game_ui.game.action_counter += 1
            
            # Get the target unit for the event data
            target = self.game_ui.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            
            # Publish attack planned event
            self.publish_event(
                EventType.ATTACK_PLANNED,
                AttackEventData(
                    attacker=self.selected_unit,
                    target=target
                )
            )
            
            self.game_ui.message = f"Attack set against {target.get_display_name()}"
            # Add message to log for planned attacks, similar to skill messages
            from boneglaive.utils.message_log import message_log, MessageType
            message_log.add_message(
                f"{self.selected_unit.get_display_name()} readies attack against {target.get_display_name()}!",
                MessageType.COMBAT,
                player=self.selected_unit.player,
                attacker_name=self.selected_unit.get_display_name(),
                target_name=target.get_display_name()
            )
            self.highlighted_positions = []
            return True
        else:
            self.game_ui.message = "Invalid attack target"
            return False
    
    def clear_selection(self):
        """Clear the current unit selection and highlighted positions."""
        # Deselect unit (which will publish the appropriate event)
        if self.selected_unit:
            self._deselect_unit()
        else:
            # If no unit was selected, just clear the highlighted positions
            self.highlighted_positions = []
    
    def cycle_units_internal(self, reverse=False):
        """Cycle through the player's units.
        
        Args:
            reverse: If True, cycle backward through the units
        """
        # Skip if in help or chat mode
        if self.game_ui.help_component.show_help or self.game_ui.chat_component.chat_mode:
            return
            
        # Get the current player
        current_player = self.game_ui.multiplayer.get_current_player()
        
        # Get a list of units belonging to the current player
        player_units = [unit for unit in self.game_ui.game.units 
                      if unit.is_alive() and 
                         (unit.player == current_player or 
                          (self.game_ui.game.test_mode and unit.player in [1, 2]))]
        
        if not player_units:
            self.game_ui.message = "No units available to cycle through"
            return
        
        # Store reference to currently selected unit before deselecting
        previously_selected_unit = self.selected_unit
        
        # If no unit was selected, select the first or last one depending on direction
        if not previously_selected_unit:
            # In reverse mode, start from the last unit
            next_unit = player_units[-1 if reverse else 0]
        else:
            # Find the index of the currently selected unit
            try:
                current_index = player_units.index(previously_selected_unit)
                
                # Calculate the next index based on direction
                if reverse:
                    # Select the previous unit (loop back to last if at the beginning)
                    next_index = (current_index - 1) % len(player_units)
                else:
                    # Select the next unit (loop back to first if at the end)
                    next_index = (current_index + 1) % len(player_units)
                    
                next_unit = player_units[next_index]
            except ValueError:
                # If the selected unit isn't in the player's units (could happen in test mode)
                # In reverse mode, start from the last unit
                next_unit = player_units[-1 if reverse else 0]
        
        # Only deselect the current unit after finding the next one
        if previously_selected_unit:
            self._deselect_unit()
            
        # Move cursor to the next unit's position
        previous_pos = self.cursor_pos
        
        # Set position based on whether unit has a move target
        if next_unit.move_target:
            self.cursor_pos = Position(next_unit.move_target[0], next_unit.move_target[1])
        else:
            self.cursor_pos = Position(next_unit.y, next_unit.x)
            
        # Publish cursor moved event if position changed
        if self.cursor_pos != previous_pos:
            self.publish_event(
                EventType.CURSOR_MOVED, 
                CursorMovedEventData(position=self.cursor_pos, previous_position=previous_pos)
            )
        
        # Select the unit
        self.selected_unit = next_unit
        
        # Publish unit selected event
        self.publish_event(
            EventType.UNIT_SELECTED,
            UnitSelectedEventData(unit=next_unit, position=self.cursor_pos)
        )
        
        # Clear message to avoid redundancy with unit info display
        self.game_ui.message = ""
        
        # Redraw the board to show the new selection
        self.game_ui.draw_board()
    
    def cycle_units(self):
        """Cycle forward through player's units (Tab key)."""
        self.cycle_units_internal(reverse=False)
    
    def cycle_units_reverse(self):
        """Cycle backward through player's units (Shift+Tab key)."""
        self.cycle_units_internal(reverse=True)
        
    def find_unit_by_ghost(self, y, x):
        """Find a unit that has a move target at the given position.
        
        Args:
            y, x: The position to check for a ghost unit
            
        Returns:
            The unit that has a move target at (y, x), or None if no such unit exists
        """
        for unit in self.game_ui.game.units:
            if unit.is_alive() and unit.move_target == (y, x):
                return unit
        return None