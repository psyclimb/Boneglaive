#!/usr/bin/env python3
import curses

from boneglaive.utils.constants import WIDTH
from boneglaive.utils.input_handler import GameAction
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.coordinates import Position
from boneglaive.utils.event_system import (
    EventType, EventData, UIRedrawEventData, MessageDisplayEventData
)
from boneglaive.game.skills.core import TargetType
from boneglaive.ui.components.base import UIComponent

class ActionMenuComponent(UIComponent):
    """Component for displaying and handling the unit action menu."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.visible = False
        self.actions = []
        self.selected_index = 0
        self.menu_mode = "standard"  # Can be "standard" or "skills"
        self.jawline_shown_units = set()  # Track units that have shown Jawline messages
        
        # Need to import UnitType for unit-specific skill checks
        from boneglaive.utils.constants import UnitType
        self.UnitType = UnitType
        
    def _setup_event_handlers(self):
        """Set up event handlers for action menu."""
        # Subscribe to unit selection/deselection events
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
        
    def _on_unit_selected(self, event_type, event_data):
        """Handle unit selection events."""
        unit = event_data.unit
        # Show menu and populate actions
        self.visible = True
        self.populate_actions(unit)
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
    def _on_unit_deselected(self, event_type, event_data):
        """Handle unit deselection events."""
        # Hide menu
        self.visible = False
        # Reset action list and selection
        self.actions = []
        self.selected_index = 0
        
    def populate_actions(self, unit):
        """
        Populate available actions for the selected unit.
        
        Note: Action labels should follow the [K]ey format convention:
        - The key is shown in brackets and capitalized
        - The rest of the label is lowercase and without spaces
        - Example: [M]ove, [A]ttack, [S]kills
        This convention is used throughout the game UI.
        """
        self.actions = []
        self.menu_mode = "standard"
        
        # Add standard actions with consistent labeling
        # Disable move for trapped units or echoes (echoes can't move)
        unit_can_move = unit is not None and unit.trapped_by is None and not unit.is_echo
        self.actions.append({
            'key': 'm',
            'label': 'ove',  # Will be displayed as [M]ove without space
            'action': GameAction.MOVE_MODE,
            'enabled': unit_can_move  # Enabled only if unit is not trapped and not an echo
        })
        
        self.actions.append({
            'key': 'a',
            'label': 'ttack',  # Will be displayed as [A]ttack without space
            'action': GameAction.ATTACK_MODE,
            'enabled': True
        })
        
        # Add skill action
        unit_has_skills = unit is not None and hasattr(unit, 'active_skills') and len(unit.get_available_skills()) > 0
        unit_can_use_skills = unit_has_skills and unit.trapped_by is None and not unit.is_echo
        self.actions.append({
            'key': 's',
            'label': 'kills',  # Will be displayed as [S]kills without space
            'action': GameAction.SKILL_MODE,
            'enabled': unit_can_use_skills  # Enabled if unit has available skills, is not trapped, and not an echo
        })
        
        # Reset selected index
        self.selected_index = 0
        
    def show_skill_menu(self, unit):
        """
        Show a menu of available skills for the selected unit.
        Only shows skills specific to that unit type.
        
        Args:
            unit: The unit whose skills to display
        """
        self.actions = []
        self.menu_mode = "skills"
        
        # Get available skills
        available_skills = []
        if unit and hasattr(unit, 'active_skills'):
            available_skills = unit.get_available_skills()
        
        # GLAIVEMAN skills
        if unit.type == self.UnitType.GLAIVEMAN:
            # Add Pry skill
            pry_skill = next((skill for skill in available_skills if skill.name == "Pry"), None)
            self.actions.append({
                'key': 'p',
                'label': 'ry',  # Will be displayed as [P]ry
                'action': 'pry_skill',
                'enabled': pry_skill is not None,
                'skill': pry_skill
            })
            
            # Add Vault skill
            vault_skill = next((skill for skill in available_skills if skill.name == "Vault"), None)
            self.actions.append({
                'key': 'v',
                'label': 'ault',  # Will be displayed as [V]ault
                'action': 'vault_skill',
                'enabled': vault_skill is not None,
                'skill': vault_skill
            })
            
            # Add Judgement Throw skill
            judgement_skill = next((skill for skill in available_skills if skill.name == "Judgement Throw"), None)
            self.actions.append({
                'key': 'j',
                'label': 'udgement',  # Will be displayed as [J]udgement
                'action': 'judgement_skill',
                'enabled': judgement_skill is not None,
                'skill': judgement_skill
            })
        
        # MANDIBLE_FOREMAN skills
        elif unit.type == self.UnitType.MANDIBLE_FOREMAN:
            
            # Add Expedite skill (previously Discharge)
            expedite_skill = next((skill for skill in available_skills if skill.name == "Expedite"), None)
            self.actions.append({
                'key': 'e',
                'label': 'xpedite',  # Will be displayed as [E]xpedite
                'action': 'expedite_skill',
                'enabled': expedite_skill is not None,
                'skill': expedite_skill
            })
            
            # Add Site Inspection skill
            site_inspection_skill = next((skill for skill in available_skills if skill.name == "Site Inspection"), None)
            self.actions.append({
                'key': 's',
                'label': 'ite Inspection',  # Will be displayed as [S]ite Inspection
                'action': 'site_inspection_skill',
                'enabled': site_inspection_skill is not None,
                'skill': site_inspection_skill
            })
            
            # Add Jawline skill
            jawline_skill = next((skill for skill in available_skills if skill.name == "Jawline"), None)
            self.actions.append({
                'key': 'j',
                'label': 'awline',  # Will be displayed as [J]awline
                'action': 'jawline_skill',
                'enabled': jawline_skill is not None,
                'skill': jawline_skill
            })
        
        # GRAYMAN skills
        elif unit.type == self.UnitType.GRAYMAN:
            
            # Add Delta Config skill
            delta_config_skill = next((skill for skill in available_skills if skill.name == "Delta Config"), None)
            self.actions.append({
                'key': 'd',
                'label': 'elta Config',  # Will be displayed as [D]elta Config
                'action': 'delta_config_skill',
                'enabled': delta_config_skill is not None,
                'skill': delta_config_skill
            })
            
            # Add Estrange skill
            estrange_skill = next((skill for skill in available_skills if skill.name == "Estrange"), None)
            self.actions.append({
                'key': 'e',
                'label': 'strange',  # Will be displayed as [E]strange
                'action': 'estrange_skill',
                'enabled': estrange_skill is not None,
                'skill': estrange_skill
            })
            
            # Add Græ Exchange skill
            grae_exchange_skill = next((skill for skill in available_skills if skill.name == "Græ Exchange"), None)
            self.actions.append({
                'key': 'g',
                'label': 'ræ Exchange',  # Will be displayed as [G]ræ Exchange
                'action': 'grae_exchange_skill',
                'enabled': grae_exchange_skill is not None,
                'skill': grae_exchange_skill
            })
        
        # Reset selected index
        self.selected_index = 0
        
    def draw(self):
        """Draw the action menu."""
        if not self.visible or not self.actions:
            return
            
        # Get unit info for header
        unit = self.game_ui.cursor_manager.selected_unit
        if not unit:
            return
            
        # Calculate menu position
        menu_x = WIDTH * 2 + 2  # Position to the right of the map
        menu_y = 2              # Start higher up to avoid collision with bottom UI elements
        
        # Calculate menu dimensions
        menu_width = 25  # Width that comfortably fits content
        menu_height = len(self.actions) + 4  # Add extra space to ensure all items fit within borders
        
        # Draw menu border
        # Top border
        self.renderer.draw_text(menu_y, menu_x, "┌" + "─" * (menu_width - 2) + "┐", 1)
        
        # Side borders
        for i in range(1, menu_height - 1):
            self.renderer.draw_text(menu_y + i, menu_x, "│", 1)
            self.renderer.draw_text(menu_y + i, menu_x + menu_width - 1, "│", 1)
        
        # Bottom border
        self.renderer.draw_text(menu_y + menu_height - 1, menu_x, "└" + "─" * (menu_width - 2) + "┘", 1)
        
        # Draw menu header with unit player color
        player_color = 3 if unit.player == 1 else 4
        
        # Set header text based on menu mode
        if self.menu_mode == "standard":
            header = f" {unit.get_display_name()} Actions "
        else:
            header = f" {unit.get_display_name()} Skills "
        
        # Center the header
        header_x = menu_x + (menu_width - len(header)) // 2
        self.renderer.draw_text(menu_y + 1, header_x, header, player_color, curses.A_BOLD)
        
        # Draw a separator line
        self.renderer.draw_text(menu_y + 2, menu_x + 1, "─" * (menu_width - 2), 1)
        
        # Draw menu items
        for i, action in enumerate(self.actions):
            y_pos = menu_y + i + 3  # Position after header and separator
            
            # Format action label with capitalized key directly followed by lowercase label: [K]ey
            # Combined into a single string for consistent spacing
            if 'key_display' in action:
                # Use key_display for special keys like ESC
                key_display = action['key_display']
            else:
                # For regular keys, capitalize
                key_display = action['key'].upper()
                
            action_text = f"[{key_display}]{action['label']}"
            
            # Calculate x position with consistent left margin
            action_x = menu_x + 3  # Left margin for all actions
            
            # Choose color based on whether action is enabled
            key_color = player_color if action['enabled'] else 8  # Player color or gray
            
            # Special handling for placeholder skills (marked as not implemented)
            if 'placeholder' in action and action['placeholder']:
                label_color = 7  # Yellow for placeholders
            else:
                label_color = 1 if action['enabled'] else 8  # Normal color or gray
            
            # Set attributes based on enabled status
            attr = curses.A_BOLD if action['enabled'] else curses.A_DIM
            
            # Draw the action text
            key_length = 3  # Length of "[X]" part
            
            # Draw the key part with key color
            self.renderer.draw_text(y_pos, action_x, action_text[:key_length], key_color, attr)
            
            # Draw the label part with label color
            self.renderer.draw_text(y_pos, action_x + key_length, action_text[key_length:], label_color, attr)
            
        # No ESC cancel text per user request
        
    def handle_input(self, key: int) -> bool:
        """Handle input specific to the action menu."""
        if not self.visible:
            return False
            
        # Exit if no actions
        if not self.actions:
            return False
        
        # Handle escape key for the skills menu (return to standard menu)
        if self.menu_mode == "skills" and key == 27:  # Escape key
            # Return to standard menu
            self.publish_event(EventType.CANCEL_REQUESTED, EventData())
            return True
            
        # Handle direct key selection based on menu mode
        for action in self.actions:
            # Check if key matches - handle both char and int keys
            key_match = False
            if isinstance(action['key'], str) and len(action['key']) == 1:
                key_match = (key == ord(action['key']))
            elif isinstance(action['key'], str) and len(action['key']) > 1:
                # Special escape sequence
                if action['key'] == '\x1b' and key == 27:  # ESC key
                    key_match = True
            else:
                key_match = (key == action['key'])
            
            # For standard menu, key must match and action must be enabled    
            if key_match and action['enabled']:
                # Standard menu actions
                if self.menu_mode == "standard":
                    if action['action'] == GameAction.MOVE_MODE:
                        self.publish_event(EventType.MOVE_MODE_REQUESTED, EventData())
                    elif action['action'] == GameAction.ATTACK_MODE:
                        self.publish_event(EventType.ATTACK_MODE_REQUESTED, EventData())
                    elif action['action'] == GameAction.SKILL_MODE:
                        self.publish_event(EventType.SKILL_MODE_REQUESTED, EventData())
                    return True
                
                # Skills menu actions
                elif self.menu_mode == "skills":
                    # For placeholder skills, show message but don't select
                    if 'placeholder' in action and action['placeholder']:
                        self.publish_event(
                            EventType.MESSAGE_DISPLAY_REQUESTED,
                            MessageDisplayEventData(
                                message=f"{action['key'].upper()}{action['label']} not yet implemented",
                                message_type=MessageType.WARNING
                            )
                        )
                        return True
                    
                    # Handle specific skill selection - simplified to handle any action['action']
                    skill = action.get('skill')
                    if skill:
                        self._select_skill(skill)
                        return True
                
        # All other keys pass through - this allows movement keys to still work
        return False
        
    def _select_skill(self, skill):
        """
        Select a skill to use and enter targeting mode.
        
        Args:
            skill: The skill to use
        """
        cursor_manager = self.game_ui.cursor_manager
        mode_manager = self.game_ui.mode_manager
        
        # Set the selected skill
        if cursor_manager.selected_unit:
            cursor_manager.selected_unit.selected_skill = skill
            
            # Change to skill targeting mode
            mode_manager.set_mode("skill")
            
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message=f"Using skill: {skill.name}. Select target."
                )
            )
            
            # Highlight valid targets for the skill based on target type
            game = self.game_ui.game
            targets = []
            from boneglaive.utils.constants import HEIGHT, WIDTH
            
            # Get the unit's current or planned position
            from_y = cursor_manager.selected_unit.y
            from_x = cursor_manager.selected_unit.x
            
            # If unit has a planned move, use that position instead
            if cursor_manager.selected_unit.move_target:
                from_y, from_x = cursor_manager.selected_unit.move_target
            
            # Different targeting logic based on skill target type
            if skill.target_type == TargetType.SELF:
                # For self-targeted skills like Recalibrate or Jawline, use immediately without targeting
                if skill.can_use(cursor_manager.selected_unit, (from_y, from_x), game):
                    # Set the skill target to self
                    cursor_manager.selected_unit.skill_target = (from_y, from_x)
                    # Actually use the skill now
                    skill.use(cursor_manager.selected_unit, (from_y, from_x), game)
                    # Show message
                    unit = cursor_manager.selected_unit
                    
                    # Special message for Jawline skill
                    if skill.name == "Jawline":
                        # Only show the Jawline message once per unit (until skill is used)
                        # Check if this unit already has the jawline_message_shown property set
                        jawline_shown = hasattr(unit, 'jawline_message_shown') and unit.jawline_message_shown
                        
                        if not jawline_shown:
                            message = f"{unit.get_display_name()} prepares to deploy JAWLINE network!"
                            # Mark that we've shown this message
                            unit.jawline_message_shown = True
                            
                            # Add the message directly to the message log with player information
                            # This ensures it will be colored according to the player
                            message_log.add_message(
                                text=message,
                                msg_type=MessageType.ABILITY,
                                player=unit.player,
                                attacker_name=unit.get_display_name()
                            )
                    else:
                        message = f"{skill.name} will be used at end of turn"
                        
                        # Add the message directly to the message log with player information
                        # This ensures it will be colored according to the player
                        message_log.add_message(
                            text=message,
                            msg_type=MessageType.ABILITY,
                            player=unit.player,
                            attacker_name=unit.get_display_name()
                        )
                    
                    # Request a UI redraw to show the message immediately
                    self.publish_event(
                        EventType.UI_REDRAW_REQUESTED,
                        UIRedrawEventData()
                    )
                    # Return to select mode
                    mode_manager.set_mode("select")
                    return
                else:
                    # If can't use, don't show an error message
                    # Reset selected skill
                    cursor_manager.selected_unit.selected_skill = None
                    # Return to select mode
                    mode_manager.set_mode("select")
                    return
            elif skill.target_type == TargetType.ENEMY:
                # For enemy-targeted skills, highlight enemy units in range
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        # Check if there's an enemy unit at this position
                        target = game.get_unit_at(y, x)
                        if target and target.player != cursor_manager.selected_unit.player:
                            # Check if target is within skill range
                            distance = game.chess_distance(from_y, from_x, y, x)
                            
                            if distance <= skill.range:
                                # Check if skill can be used on this target
                                if skill.can_use(cursor_manager.selected_unit, (y, x), game):
                                    targets.append((y, x))
            
            elif skill.target_type == TargetType.AREA:
                # For area-targeted skills like Vault, highlight all valid positions
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        # Skip current position
                        if y == from_y and x == from_x:
                            continue
                            
                        # Check if position is within skill range
                        distance = game.chess_distance(from_y, from_x, y, x)
                        if distance <= skill.range:
                            # Check if skill can be used on this position (will check for obstacles, etc.)
                            if skill.can_use(cursor_manager.selected_unit, (y, x), game):
                                targets.append((y, x))
            
            # Convert targets to Position objects
            cursor_manager.highlighted_positions = [Position(y, x) for y, x in targets]
            
            if not cursor_manager.highlighted_positions:
                # No valid targets, reset skill selection and exit skill mode
                cursor_manager.selected_unit.selected_skill = None
                mode_manager.set_mode("select")
                
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="No valid targets for this skill",
                        message_type=MessageType.WARNING
                    )
                )