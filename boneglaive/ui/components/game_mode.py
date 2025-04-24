#!/usr/bin/env python3
from typing import List, Tuple

from boneglaive.utils.constants import UnitType
from boneglaive.utils.coordinates import Position
from boneglaive.utils.message_log import MessageType, message_log
from boneglaive.utils.event_system import (
    EventType, EventData, ModeChangedEventData, 
    MoveEventData, AttackEventData, MessageDisplayEventData,
    TurnEventData
)
from boneglaive.ui.components.base import UIComponent

# Game mode manager component
class GameModeManager(UIComponent):
    """Component for managing game modes and turn handling."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.mode = "select"  # select, move, attack, setup
        self.show_setup_instructions = False  # Don't show setup instructions by default
        self.setup_unit_type = UnitType.GLAIVEMAN  # Default unit type for setup phase
    
    def _setup_event_handlers(self):
        """Set up event handlers for game mode manager."""
        # Subscribe to unit selection events to update UI as needed
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
        
        # Subscribe to mode request events
        self.subscribe_to_event(EventType.MOVE_MODE_REQUESTED, self._on_move_mode_requested)
        self.subscribe_to_event(EventType.ATTACK_MODE_REQUESTED, self._on_attack_mode_requested)
        self.subscribe_to_event(EventType.SKILL_MODE_REQUESTED, self._on_skill_mode_requested)
        self.subscribe_to_event(EventType.SELECT_MODE_REQUESTED, self._on_select_mode_requested)
        self.subscribe_to_event(EventType.CANCEL_REQUESTED, self._on_cancel_requested)
    
    def _on_unit_selected(self, event_type, event_data):
        """Handle unit selection events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_unit_deselected(self, event_type, event_data):
        """Handle unit deselection events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
        
    def _on_move_mode_requested(self, event_type, event_data):
        """Handle move mode request events."""
        # Delegate to handle_move_mode which already has the logic
        self.handle_move_mode()
        
    def _on_attack_mode_requested(self, event_type, event_data):
        """Handle attack mode request events."""
        # Delegate to handle_attack_mode which already has the logic
        self.handle_attack_mode()
        
    def _on_skill_mode_requested(self, event_type, event_data):
        """Handle skill mode request events."""
        # Delegate to handle_skill_mode which we'll implement
        self.handle_skill_mode()
        
    def _on_select_mode_requested(self, event_type, event_data):
        """Handle select mode request events."""
        # Simply change to select mode
        self.set_mode("select")
        
    def _on_cancel_requested(self, event_type, event_data):
        """Handle cancel request events."""
        # Delegate to handle_cancel which already has the logic
        self.handle_cancel()
    
    def set_mode(self, new_mode):
        """Set the game mode with event notification."""
        if new_mode != self.mode:
            old_mode = self.mode
            self.mode = new_mode
            
            # Publish mode changed event
            self.publish_event(
                EventType.MODE_CHANGED,
                ModeChangedEventData(new_mode=new_mode, previous_mode=old_mode)
            )
    
    def handle_cancel(self):
        """Handle cancel action (Escape key or 'c' key).
        Cancels the current action based on the current state.
        """
        cursor_manager = self.game_ui.cursor_manager
        
        # First check if log history screen is showing - cancel it
        if self.game_ui.message_log_component.show_log_history:
            self.game_ui.message_log_component.show_log_history = False
            self.game_ui.message_log_component.log_history_scroll = 0  # Reset scroll position
            self.game_ui.message = "Log history closed"
            self.game_ui.draw_board()
            return
            
        # Next check if help screen is showing - cancel it
        if self.game_ui.help_component.show_help:
            self.game_ui.help_component.show_help = False
            self.game_ui.message = "Help screen closed"
            self.game_ui.draw_board()
            return
            
        # If in chat mode, cancel chat
        if self.game_ui.chat_component.chat_mode:
            self.game_ui.chat_component.chat_mode = False
            self.game_ui.message = "Chat cancelled"
            self.game_ui.draw_board()
            return
            
        # If in attack, move or skill mode, cancel the mode but keep unit selected
        if self.mode in ["attack", "move", "skill"] and cursor_manager.selected_unit:
            cursor_manager.highlighted_positions = []
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            self.game_ui.message = f"{self.mode.capitalize()} mode cancelled, unit still selected"
            self.game_ui.draw_board()
            return
            
        # If in skill_select mode, return to normal menu
        if self.mode == "skill_select" and cursor_manager.selected_unit:
            # Return to standard menu
            self.set_mode("select")
            # Reset action menu to standard mode
            self.game_ui.action_menu_component.populate_actions(cursor_manager.selected_unit)
            self.game_ui.message = "Skill selection cancelled"
            self.game_ui.draw_board()
            return
            
        # If unit is selected with a planned move, cancel the move
        if cursor_manager.selected_unit and cursor_manager.selected_unit.move_target:
            # Store position info for event before canceling move
            from_position = Position(cursor_manager.selected_unit.y, cursor_manager.selected_unit.x)
            to_position = Position(
                cursor_manager.selected_unit.move_target[0],
                cursor_manager.selected_unit.move_target[1]
            )
            unit = cursor_manager.selected_unit
            
            # Cancel the move
            cursor_manager.selected_unit.move_target = None
            
            # Publish move canceled event - could be useful for UI components
            self.publish_event(
                EventType.MOVE_CANCELLED,
                MoveEventData(
                    unit=unit,
                    from_position=from_position,
                    to_position=to_position
                )
            )
            
            self.game_ui.message = "Move order cancelled"
            self.game_ui.draw_board()
            return
            
        # If unit is selected with a planned attack, cancel the attack
        if cursor_manager.selected_unit and cursor_manager.selected_unit.attack_target:
            # Get target unit for event data
            target_position = cursor_manager.selected_unit.attack_target
            target = self.game_ui.game.get_unit_at(target_position[0], target_position[1])
            attacker = cursor_manager.selected_unit
            
            # Cancel the attack
            cursor_manager.selected_unit.attack_target = None
            
            # Publish attack canceled event - could be useful for UI components
            if target:
                self.publish_event(
                    EventType.ATTACK_CANCELLED,
                    AttackEventData(
                        attacker=attacker,
                        target=target
                    )
                )
            
            self.game_ui.message = "Attack order cancelled"
            self.game_ui.draw_board()
            return
            
        # Otherwise, clear the selection entirely
        cursor_manager.clear_selection()
        # Ensure we're in select mode
        self.set_mode("select")
        self.game_ui.message = "Selection cleared"
        
        # Redraw the board to immediately update selection visuals
        self.game_ui.draw_board()
    
    def handle_move_mode(self):
        """Enter move mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn!",
                    message_type=MessageType.WARNING
                )
            )
            return
                
        if cursor_manager.selected_unit:
            current_player = self.game_ui.multiplayer.get_current_player()
            
            # Check if unit belongs to current player or test mode is on
            # Also allow control in local multiplayer for the active player
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if unit has already planned an attack or skill use
                if cursor_manager.selected_unit.attack_target:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned an attack and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit has already planned a skill use
                if cursor_manager.selected_unit.skill_target and cursor_manager.selected_unit.selected_skill:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned a skill use and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is trapped
                if cursor_manager.selected_unit.trapped_by is not None:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is trapped and cannot move",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is an echo (cannot move)
                if cursor_manager.selected_unit.is_echo:
                    # Don't show a message, just silently return
                    return
                    
                # Change mode (will publish mode changed event)
                self.set_mode("move")
                
                # Convert positions to Position objects
                cursor_manager.highlighted_positions = [
                    Position(y, x) for y, x in self.game_ui.game.get_possible_moves(cursor_manager.selected_unit)
                ]
                
                if not cursor_manager.highlighted_positions:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No valid moves available",
                            message_type=MessageType.WARNING
                        )
                    )
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only move your own units!",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No unit selected",
                    message_type=MessageType.WARNING
                )
            )
    
    def handle_skill_mode(self):
        """Enter skill mode to select from available skills."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn!",
                    message_type=MessageType.WARNING
                )
            )
            return
                
        if cursor_manager.selected_unit:
            # Check if unit belongs to current player or test mode is on
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if unit has already planned an attack
                if cursor_manager.selected_unit.attack_target:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned an attack and cannot use a skill",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is trapped
                if cursor_manager.selected_unit.trapped_by is not None:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is trapped and cannot use skills",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is an echo (cannot use skills)
                if cursor_manager.selected_unit.is_echo:
                    # Don't show a message, just silently return
                    return
                    
                # Previously there was a restriction that prevented using skills after moving
                # This has been removed to allow move+skill combinations
                
                # Get available skills (not on cooldown)
                available_skills = cursor_manager.selected_unit.get_available_skills()
                
                if not available_skills:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No available skills to use",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Change mode to skill selection
                self.set_mode("skill_select")
                
                # Update the action menu to show skills
                self.game_ui.action_menu_component.show_skill_menu(cursor_manager.selected_unit)
                
                # Use event system for message
                # If the unit has a planned move, indicate that the skill will be used from the move position
                if cursor_manager.selected_unit.move_target:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select a skill to use from planned move position"
                        )
                    )
                else:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select a skill to use"
                        )
                    )
                
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only use skills with your own units!",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No unit selected",
                    message_type=MessageType.WARNING
                )
            )
            
    def handle_attack_mode(self):
        """Enter attack mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn!",
                    message_type=MessageType.WARNING
                )
            )
            return
                
        if cursor_manager.selected_unit:
            # Check if unit belongs to current player or test mode is on
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if the unit has already queued a skill
                if cursor_manager.selected_unit.skill_target and cursor_manager.selected_unit.selected_skill:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned a skill use and cannot attack",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is trapped
                if cursor_manager.selected_unit.trapped_by is not None:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is trapped and cannot attack",
                            message_type=MessageType.WARNING
                        )
                    )
                    return
                
                # Check if unit is an echo (cannot attack)
                if cursor_manager.selected_unit.is_echo:
                    # Don't show a message, just silently return
                    return
                    
                # Change mode (will publish mode changed event)
                self.set_mode("attack")
                
                # Calculate attack positions
                attack_positions = []
                # Use actual unit position if not moving, otherwise use move target position
                origin_y, origin_x = (
                    cursor_manager.selected_unit.move_target 
                    if cursor_manager.selected_unit.move_target 
                    else (cursor_manager.selected_unit.y, cursor_manager.selected_unit.x)
                )
                
                # Get units within attack range
                targets = self.game_ui.game.get_attackable_units(
                    cursor_manager.selected_unit,
                    from_position=(origin_y, origin_x)
                )
                
                # Add positions of attackable units
                for target in targets:
                    attack_positions.append(Position(target.y, target.x))
                    
                cursor_manager.highlighted_positions = attack_positions
                
                if not cursor_manager.highlighted_positions:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No valid attack targets in range",
                            message_type=MessageType.WARNING
                        )
                    )
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only attack with your own units!",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No unit selected",
                    message_type=MessageType.WARNING
                )
            )
    
    def handle_end_turn(self):
        """End the current turn."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Publish turn ended event
        self.publish_event(
            EventType.TURN_ENDED,
            TurnEventData(
                player=self.game_ui.multiplayer.get_current_player(),
                turn_number=self.game_ui.game.turn
            )
        )
        
        # Pass UI to execute_turn for animations
        self.game_ui.game.execute_turn(self.game_ui)
        
        # Clear selection after executing turn
        cursor_manager.clear_selection()
        
        # Set mode back to select mode
        self.set_mode("select")
        
        # Handle multiplayer turn switching
        if not self.game_ui.game.winner:
            # End turn in multiplayer manager
            self.game_ui.multiplayer.end_turn()
            self.game_ui.update_player_message()
            
        # Redraw the board to update visuals
        self.game_ui.draw_board()
    
    def handle_test_mode(self):
        """Toggle test mode or cycle unit types in setup phase."""
        # During setup phase, backspace cycles through unit types
        if self.game_ui.game.setup_phase:
            self._cycle_setup_unit_type()
        # Otherwise toggle test mode
        else:
            self.game_ui.game.toggle_test_mode()
            if self.game_ui.game.test_mode:
                self.game_ui.message = "Test mode enabled - all units can be controlled"
            else:
                self.game_ui.message = "Test mode disabled - normal unit control"
            
            # Update the player message
            self.game_ui.update_player_message()
        
        # Redraw the board to update visual indicators
        self.game_ui.draw_board()
        
    def _cycle_setup_unit_type(self):
        """Cycle through unit types during setup phase."""
        # Get all unit types
        unit_types = list(UnitType)
        
        # Find current index
        current_index = unit_types.index(self.setup_unit_type)
        
        # Move to next unit type (cycle back to start if at end)
        next_index = (current_index + 1) % len(unit_types)
        self.setup_unit_type = unit_types[next_index]
        
        # Update message to show selected unit type
        self.game_ui.message = f"Selected unit type: {self.setup_unit_type.name}"
        
        # Update the player message (includes setup info)
        self.game_ui.update_player_message()
        
    def handle_confirm(self):
        """Handle confirmation action (mainly for setup phase)."""
        # Handle special case for setup phase confirmation
        if self.game_ui.game.setup_phase:
            # Try to confirm the current setup
            if self.game_ui.game.confirm_setup():
                self.game_ui.message = "Setup phase complete!"
                # Update the player message
                self.game_ui.update_player_message()
                # Reset the mode
                self.set_mode("select")
            else:
                self.game_ui.message = "Cannot confirm yet - all units must be placed!"
                
            # Redraw the board to update visuals
            self.game_ui.draw_board()
            
    def handle_setup_select(self):
        """Handle unit placement during setup phase."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Get cursor position
        y, x = cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x
        
        # Attempt to place a unit at the cursor position
        if self.game_ui.game.place_setup_unit(y, x, self.setup_unit_type):
            # Unit was placed successfully
            self.game_ui.message = f"Unit placed at ({y}, {x})"
            message_log.add_system_message(f"Player {self.game_ui.game.setup_player} placed a {self.setup_unit_type.name}")
            
            # Check if player has placed all units
            remaining = self.game_ui.game.setup_units_remaining[self.game_ui.game.setup_player]
            if remaining > 0:
                self.game_ui.message = f"Place {remaining} more unit{'s' if remaining > 1 else ''}"
            else:
                self.game_ui.message = "All units placed - press 'y' to confirm"
        else:
            # Unit could not be placed
            # Check why placement failed
            if not self.game_ui.game.is_valid_position(y, x):
                self.game_ui.message = "Invalid position - out of bounds"
            elif not self.game_ui.game.map.can_place_unit(y, x):
                self.game_ui.message = "Cannot place unit on this terrain"
            elif self.game_ui.game.setup_units_remaining[self.game_ui.game.setup_player] <= 0:
                self.game_ui.message = "No more units to place - press 'y' to confirm"
            elif self.game_ui.game.get_unit_at(y, x) is not None:
                self.game_ui.message = "Position already occupied"
            else:
                self.game_ui.message = "Cannot place unit here"
                
        # Redraw the board to show the new unit or provide feedback
        self.game_ui.draw_board()
        
        # Check if player should be prompted to confirm setup
        return self.check_confirmation_needed()
            
    def check_confirmation_needed(self):
        """Check if the player should be prompted to confirm their setup."""
        # If all units have been placed, return true to indicate confirmation is needed
        return self.game_ui.game.setup_units_remaining[self.game_ui.game.setup_player] <= 0
        
    def handle_select_in_select_mode(self):
        """Handle selection action when in select mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # First check if there's a real unit at the cursor position
        unit = self.game_ui.game.get_unit_at(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
        
        # If not, check if there's a ghost unit (planned move) at this position
        if not unit:
            unit = cursor_manager.find_unit_by_ghost(
                cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            
        current_player = self.game_ui.multiplayer.get_current_player()
        
        # Check if unit belongs to current player or test mode is on
        if unit and cursor_manager.can_select_unit(unit):
            # Set the selection
            cursor_manager.selected_unit = unit
            
            # Check if we're selecting a ghost (unit with a move_target at current position)
            is_ghost = (unit.move_target == (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x))
            
            # Clear the message to avoid redundancy with unit info display
            # Use event system for message (empty message clears it)
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="",
                    log_message=False
                )
            )
            
            # Publish unit selected event
            from boneglaive.utils.event_system import UnitSelectedEventData
            self.publish_event(
                EventType.UNIT_SELECTED,
                UnitSelectedEventData(
                    unit=unit,
                    is_ghost=is_ghost
                )
            )
            
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No valid unit selected",
                    message_type=MessageType.WARNING
                )
            )
            
            if unit:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Cannot select {unit.type.name} - belongs to Player {unit.player}",
                        message_type=MessageType.WARNING
                    )
                )
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="No unit at that position",
                        message_type=MessageType.WARNING
                    )
                )
                
    def handle_select_in_move_mode(self):
        """Handle selection action when in move mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Import Position to use get_line
        from boneglaive.utils.coordinates import Position, get_line
        
        # Check if the position is a valid move target
        if Position(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x) in cursor_manager.highlighted_positions:
            cursor_manager.selected_unit.move_target = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message=f"Move set to ({cursor_manager.cursor_pos.y}, {cursor_manager.cursor_pos.x})",
                    log_message=False
                )
            )
            
            # Publish move planned event
            from boneglaive.utils.event_system import MoveEventData
            self.publish_event(
                EventType.MOVE_PLANNED,
                MoveEventData(
                    unit=cursor_manager.selected_unit,
                    from_position=Position(cursor_manager.selected_unit.y, cursor_manager.selected_unit.x),
                    to_position=Position(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
                )
            )
            
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            cursor_manager.highlighted_positions = []
        else:
            # Check why the position isn't valid
            y, x = cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x
            
            # Check if the position is in range
            distance = self.game_ui.game.chess_distance(cursor_manager.selected_unit.y, cursor_manager.selected_unit.x, y, x)
            if distance > cursor_manager.selected_unit.move_range:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Position is out of movement range",
                        message_type=MessageType.WARNING
                    )
                )
            # Check if there's an enemy unit blocking the path
            elif distance > 1:
                # Check the path for enemy units
                start_pos = Position(cursor_manager.selected_unit.y, cursor_manager.selected_unit.x)
                end_pos = Position(y, x)
                path = get_line(start_pos, end_pos)
                
                for pos in path[1:-1]:  # Skip start and end positions
                    blocking_unit = self.game_ui.game.get_unit_at(pos.y, pos.x)
                    if blocking_unit:
                        # Determine if it's an ally or enemy for the message
                        if blocking_unit.player == cursor_manager.selected_unit.player:
                            # Use event system for message
                            self.publish_event(
                                EventType.MESSAGE_DISPLAY_REQUESTED,
                                MessageDisplayEventData(
                                    message="Path blocked by allied unit",
                                    message_type=MessageType.WARNING
                                )
                            )
                            
                            # Add a more detailed message to the log
                            self.publish_event(
                                EventType.MESSAGE_DISPLAY_REQUESTED,
                                MessageDisplayEventData(
                                    message="You cannot move through other units",
                                    message_type=MessageType.WARNING,
                                    log_message=True
                                )
                            )
                        else:
                            # Use event system for message
                            self.publish_event(
                                EventType.MESSAGE_DISPLAY_REQUESTED,
                                MessageDisplayEventData(
                                    message="Path blocked by enemy unit",
                                    message_type=MessageType.WARNING
                                )
                            )
                            
                            # Add a more detailed message to the log
                            self.publish_event(
                                EventType.MESSAGE_DISPLAY_REQUESTED,
                                MessageDisplayEventData(
                                    message="You cannot move through other units",
                                    message_type=MessageType.WARNING,
                                    log_message=True
                                )
                            )
                        return
            # Check if there's a unit at the destination
            elif self.game_ui.game.get_unit_at(y, x):
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Position is occupied by another unit",
                        message_type=MessageType.WARNING
                    )
                )
            # Check if the terrain is blocking
            elif not self.game_ui.game.map.is_passable(y, x):
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Terrain is impassable",
                        message_type=MessageType.WARNING
                    )
                )
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Invalid move target",
                        message_type=MessageType.WARNING
                    )
                )
    
    def handle_select_in_attack_mode(self):
        """Handle selection action when in attack mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Import Position for position checking
        from boneglaive.utils.coordinates import Position
        
        if Position(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x) in cursor_manager.highlighted_positions:
            cursor_manager.selected_unit.attack_target = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            target = self.game_ui.game.get_unit_at(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message=f"Attack set against {target.type.name}",
                    log_message=False
                )
            )
            
            # Publish attack planned event
            from boneglaive.utils.event_system import AttackEventData
            self.publish_event(
                EventType.ATTACK_PLANNED,
                AttackEventData(
                    attacker=cursor_manager.selected_unit,
                    target=target
                )
            )
            
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            cursor_manager.highlighted_positions = []
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Invalid attack target",
                    message_type=MessageType.WARNING
                )
            )
            
    def handle_select_in_skill_mode(self):
        """Handle selection action when in skill mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Import Position for position checking
        from boneglaive.utils.coordinates import Position
        
        # Check if the selected position is in the highlighted positions (valid targets)
        if Position(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x) in cursor_manager.highlighted_positions:
            # Set the skill target on the unit
            cursor_manager.selected_unit.skill_target = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            
            # Try to get the target unit (may be None for ground-targeted skills)
            target = self.game_ui.game.get_unit_at(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            
            # Generate message based on whether there's a target unit or just a position
            if target:
                target_desc = f"{target.type.name}"
            else:
                target_desc = f"position ({cursor_manager.cursor_pos.y}, {cursor_manager.cursor_pos.x})"
                
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message=f"{cursor_manager.selected_unit.selected_skill.name} set against {target_desc}",
                    log_message=False
                )
            )
            
            # Publish skill planned event (would need to be defined in event_system.py)
            from boneglaive.utils.event_system import SkillEventData
            self.publish_event(
                EventType.SKILL_PLANNED,
                SkillEventData(
                    unit=cursor_manager.selected_unit,
                    skill=cursor_manager.selected_unit.selected_skill,
                    target_position=Position(cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x),
                    target_unit=target
                )
            )
            
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            cursor_manager.highlighted_positions = []
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Invalid skill target",
                    message_type=MessageType.WARNING
                )
            )