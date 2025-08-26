#!/usr/bin/env python3
import curses
import time
import os
import json
from typing import Optional, List, Tuple, Dict, Callable

from boneglaive.utils.constants import HEIGHT, WIDTH, UnitType
from boneglaive.utils.coordinates import Position
from boneglaive.utils.debug import debug_config, measure_perf, logger
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.input_handler import GameAction
from boneglaive.game.skills.core import TargetType
from boneglaive.utils.event_system import (
    get_event_manager, EventType, EventData,
    UnitSelectedEventData, UnitDeselectedEventData,
    CursorMovedEventData, ModeChangedEventData,
    MoveEventData, AttackEventData, TurnEventData,
    MessageDisplayEventData, UIRedrawEventData,
    GameOverEventData
)

# Base class for UI components
class UIComponent:
    """Base class for UI components."""
    
    def __init__(self, renderer, game_ui):
        """Initialize the component."""
        self.renderer = renderer
        self.game_ui = game_ui
        self.event_manager = get_event_manager()
        self._event_subscriptions = []
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """
        Set up event handlers for this component.
        Override this in subclasses to subscribe to events.
        """
        pass
    
    def subscribe_to_event(self, event_type, handler):
        """
        Subscribe to an event and track the subscription.
        
        Args:
            event_type: The event type to subscribe to
            handler: The event handler function
        """
        self.event_manager.subscribe(event_type, handler)
        self._event_subscriptions.append((event_type, handler))
    
    def publish_event(self, event_type, event_data=None):
        """
        Publish an event.
        
        Args:
            event_type: The event type to publish
            event_data: The event data to pass to handlers
        """
        self.event_manager.publish(event_type, event_data)
    
    def unsubscribe_all(self):
        """Unsubscribe from all events this component is subscribed to."""
        for event_type, handler in self._event_subscriptions:
            self.event_manager.unsubscribe(event_type, handler)
        self._event_subscriptions = []
    
    def draw(self):
        """Draw the component."""
        pass
        
    def handle_input(self, key: int) -> bool:
        """Handle input for this component.
        Returns True if the input was handled, False otherwise.
        """
        return False

# Message log component
class MessageLogComponent(UIComponent):
    """Component for displaying and managing the message log."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.show_log = True  # Whether to show the message log
        self.log_height = 7   # Number of log lines to display
        self.show_log_history = False  # Whether to show the full log history screen
        self.log_history_scroll = 0    # Scroll position in log history
    
    def _setup_event_handlers(self):
        """Set up event handlers for the message log component."""
        # Subscribe to help and chat toggle events to handle conflicts
        self.subscribe_to_event(EventType.HELP_TOGGLED, self._on_help_toggled)
        self.subscribe_to_event(EventType.CHAT_TOGGLED, self._on_chat_toggled)
    
    def _on_help_toggled(self, event_type, event_data):
        """Handle help screen toggle events."""
        # If help screen is shown and log history is open, close log history
        show_help = event_data.show_help if hasattr(event_data, 'show_help') else False
        if show_help and self.show_log_history:
            self.show_log_history = False
            self.log_history_scroll = 0
            
    def _on_chat_toggled(self, event_type, event_data):
        """Handle chat mode toggle events."""
        # If chat mode is enabled and log is hidden, show it
        chat_enabled = event_data.chat_enabled if hasattr(event_data, 'chat_enabled') else False
        if chat_enabled and not self.show_log:
            self.show_log = True
            self.publish_event(
                EventType.LOG_TOGGLED, 
                EventData(show_log=self.show_log)
            )
        
    def toggle_message_log(self):
        """Toggle the message log display."""
        self.show_log = not self.show_log
        
        # Publish event that log was toggled
        self.publish_event(
            EventType.LOG_TOGGLED, 
            EventData(show_log=self.show_log)
        )
        
        # Display message through event system, but don't add to log
        self.publish_event(
            EventType.MESSAGE_DISPLAY_REQUESTED,
            MessageDisplayEventData(
                message=f"Message log {'shown' if self.show_log else 'hidden'}",
                message_type=MessageType.SYSTEM,
                log_message=False  # Prevent adding to message log
            )
        )
        
    def toggle_log_history(self):
        """Toggle the full log history screen."""
        # Don't show log history while in help or chat mode
        if self.game_ui.help_component.show_help or self.game_ui.chat_component.chat_mode:
            return
            
        # Toggle log history screen
        self.show_log_history = not self.show_log_history
        
        # Set scroll position to bottom when opening
        if self.show_log_history:
            # Set to a high value - the actual max will be clamped in the draw method
            self.log_history_scroll = 999999
        
        # Request UI redraw through event system
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
    # Removed colored text handling methods as they're no longer needed
    
    def _wrap_text(self, text: str, max_width: int, indent: str = "") -> list:
        """Wrap text to fit within max_width, preserving word boundaries."""
        if not text or max_width <= 0:
            return [text] if text else [""]
            
        words = text.split()
        if not words:
            return [""]
            
        wrapped_lines = []
        current_line = indent
        
        for word in words:
            # Check if adding this word would exceed the width
            test_line = current_line + (" " if current_line != indent else "") + word
            
            if len(test_line) <= max_width:
                current_line = test_line
            else:
                # If current line has content, save it and start a new line
                if current_line != indent:
                    wrapped_lines.append(current_line)
                    current_line = indent + word
                else:
                    # Word is too long even by itself - truncate it
                    if len(word) > max_width - len(indent):
                        wrapped_lines.append(indent + word[:max_width - len(indent) - 3] + "...")
                        current_line = indent
                    else:
                        current_line = indent + word
        
        # Add the last line if it has content
        if current_line != indent:
            wrapped_lines.append(current_line)
        
        return wrapped_lines if wrapped_lines else [indent]
    
    def draw_message_log(self):
        """Draw the message log in the game UI."""
        try:
            # Get formatted messages (with colors)
            messages = message_log.get_formatted_messages(self.log_height)
            
            # Calculate position for the log (closer to the game info)
            start_y = HEIGHT + 6
            
            # Get terminal width for drawing borders
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Draw message log border and header
            # Top border with title
            border_top = "┌─── MESSAGE LOG " + "─" * (term_width - 19) + "┐"
            self.renderer.draw_text(start_y, 0, border_top, 1, curses.A_BOLD)
            
            # Draw side borders and clear message area
            for i in range(1, self.log_height + 1):
                # Left border
                self.renderer.draw_text(start_y + i, 0, "│", 1)
                # Clear line
                self.renderer.draw_text(start_y + i, 1, " " * (term_width - 2), 1)
                # Right border
                self.renderer.draw_text(start_y + i, term_width - 1, "│", 1)
            
            # Bottom border
            border_bottom = "└" + "─" * (term_width - 2) + "┘"
            self.renderer.draw_text(start_y + self.log_height + 1, 0, border_bottom, 1)
            
            # Process messages with text wrapping to create content lines
            content_lines = []
            max_text_width = term_width - 4  # Allow for borders
            
            import re
            damage_pattern = re.compile(r'#DAMAGE_(\d+)#')
            heal_pattern = re.compile(r'#HEAL_(\d+)#')
            
            for text, color_id in messages:
                # Add bold attribute for player messages to make them stand out more
                attributes = 0
                if "[Player " in text:  # It's a chat message
                    attributes = curses.A_BOLD
                
                # Format the message with timestamp prefix if not already formatted
                if not text.startswith("[") and not text.startswith("»"):
                    text = "» " + text

                # Process special placeholders to highlight damage/heal numbers
                damage_num = None
                heal_num = None
                original_text = text
                has_special_numbers = False

                # Check if the message contains damage placeholder
                if '#DAMAGE_' in text:
                    match = damage_pattern.search(text)
                    if match:
                        damage_num = match.group(1)
                        text = damage_pattern.sub(damage_num, text)
                        has_special_numbers = True

                # Check if the message contains heal placeholder
                elif '#HEAL_' in text:
                    match = heal_pattern.search(text)
                    if match:
                        heal_num = match.group(1)
                        text = heal_pattern.sub(heal_num, text)
                        has_special_numbers = True
                
                # Set appropriate attributes based on color
                if color_id == 8:  # Gray message log text
                    attributes |= curses.A_DIM  # Add dim attribute to make it gray
                elif color_id in [3, 4]:  # Player colors (green or blue)
                    attributes |= curses.A_BOLD  # Make player text bold
                elif color_id == 7:  # Yellow debuff text
                    attributes |= curses.A_BOLD  # Make debuff text bold for emphasis
                elif color_id == 17:  # Wretch messages (red)
                    attributes |= curses.A_BOLD  # Make wretch messages bold red
                elif color_id == 18:  # Death messages (dark red)
                    attributes |= curses.A_DIM  # Make death messages dim red

                # Apply text wrapping
                wrapped_lines = self._wrap_text(text, max_text_width)
                
                # Store each wrapped line with its metadata
                for line in wrapped_lines:
                    content_lines.append({
                        'text': line,
                        'color_id': color_id,
                        'attributes': attributes,
                        'original_text': original_text,
                        'damage_num': damage_num,
                        'heal_num': heal_num,
                        'has_special_numbers': has_special_numbers
                    })
            
            # Take only the last N lines that fit in the log height
            # (newest messages at the end, so we want the tail)
            visible_lines = content_lines[-self.log_height:] if len(content_lines) > self.log_height else content_lines
            
            # Draw wrapped message lines (newest at bottom)
            for i, line_data in enumerate(visible_lines):
                y_pos = start_y + 1 + i  # +1 to account for the header border
                text = line_data['text']
                color_id = line_data['color_id']
                attributes = line_data['attributes']
                damage_num = line_data['damage_num']
                heal_num = line_data['heal_num']
                has_special_numbers = line_data['has_special_numbers']

                # Draw the message, with special handling for damage or heal numbers
                if has_special_numbers and damage_num is not None and damage_num in text:
                    # Render with damage numbers in magenta
                    parts = text.split(damage_num)
                    pos_x = 2

                    # Draw the first part with the regular color
                    if parts[0]:
                        self.renderer.draw_text(y_pos, pos_x, parts[0], color_id, attributes)
                        pos_x += len(parts[0])

                    # Draw the damage number in magenta
                    self.renderer.draw_text(y_pos, pos_x, damage_num, 21, curses.A_BOLD)  # 21 is the magenta color pair
                    pos_x += len(damage_num)

                    # Draw any remaining part with the regular color
                    if len(parts) > 1 and parts[1]:
                        self.renderer.draw_text(y_pos, pos_x, parts[1], color_id, attributes)
                elif has_special_numbers and heal_num is not None and heal_num in text:
                    # Render with heal numbers in white
                    parts = text.split(heal_num)
                    pos_x = 2

                    # Draw the first part with the regular color
                    if parts[0]:
                        self.renderer.draw_text(y_pos, pos_x, parts[0], color_id, attributes)
                        pos_x += len(parts[0])

                    # Draw the heal number in bright white
                    self.renderer.draw_text(y_pos, pos_x, heal_num, 22, curses.A_BOLD)  # 22 is the white color pair with bold
                    pos_x += len(heal_num)

                    # Draw any remaining part with the regular color
                    if len(parts) > 1 and parts[1]:
                        self.renderer.draw_text(y_pos, pos_x, parts[1], color_id, attributes)
                else:
                    # Regular message without colored numbers
                    self.renderer.draw_text(y_pos, 2, text, color_id, attributes)
                
        except Exception as e:
            # Never let message log crash the game
            logger.error(f"Error displaying message log: {str(e)}")
    
    def draw_log_history_screen(self):
        """Draw the full log history screen with scrolling."""
        try:
            # Calculate available height for messages (terminal height minus headers/footers)
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Clear the screen first
            for y in range(term_height):
                self.renderer.draw_text(y, 0, " " * term_width, 1)
            
            # Draw border around the entire screen
            # Top border with title
            border_top = "┌─── BONEGLAIVE MESSAGE HISTORY " + "─" * (term_width - 32) + "┐"
            self.renderer.draw_text(0, 0, border_top, 1, curses.A_BOLD)
            
            # Side borders
            for y in range(1, term_height - 1):
                self.renderer.draw_text(y, 0, "│", 1)
                self.renderer.draw_text(y, term_width - 1, "│", 1)
            
            # Bottom border
            border_bottom = "└" + "─" * (term_width - 2) + "┘"
            self.renderer.draw_text(term_height - 1, 0, border_bottom, 1)
            
            # Define content area dimensions
            content_start_y = 3  # After the navigation bar
            content_end_y = term_height - 3  # Before the status bar
            available_height = content_end_y - content_start_y
            
            # Draw navigation instructions in a bar
            nav_bar = "│ " + "─" * (term_width - 4) + " │"
            self.renderer.draw_text(1, 0, nav_bar, 1)
            nav_text = "↑/↓: Scroll | g/G: Start/End | ESC: Close | L: Toggle regular log"
            self.renderer.draw_text(1, 2, nav_text, 1, curses.A_BOLD)
            
            # Draw a separator below the navigation
            separator = "├" + "─" * (term_width - 2) + "┤"
            self.renderer.draw_text(2, 0, separator, 1)
            
            # Get all messages from the log (we'll format and scroll them)
            # Avoid filtering when viewing full history - get all messages
            all_messages = message_log.get_formatted_messages(count=message_log.MAX_MESSAGES, filter_types=None)
            
            # Process all messages with text wrapping to create content lines
            content_lines = []
            max_text_width = term_width - 4  # Leave margin for borders
            
            import re
            damage_pattern = re.compile(r'#DAMAGE_(\d+)#')
            heal_pattern = re.compile(r'#HEAL_(\d+)#')
            
            for text, color_id in all_messages:
                # Add bold attribute for player messages
                attributes = 0
                if "[Player " in text:  # It's a chat message
                    attributes = curses.A_BOLD
                
                # Format the message with timestamp prefix if not already formatted
                if not text.startswith("[") and not text.startswith("»"):
                    text = "» " + text

                # Process special placeholders to highlight damage/heal numbers
                damage_num = None
                heal_num = None
                original_text = text
                has_special_numbers = False

                # Check if the message contains damage placeholder
                if '#DAMAGE_' in text:
                    match = damage_pattern.search(text)
                    if match:
                        damage_num = match.group(1)
                        text = damage_pattern.sub(damage_num, text)
                        has_special_numbers = True

                # Check if the message contains heal placeholder
                elif '#HEAL_' in text:
                    match = heal_pattern.search(text)
                    if match:
                        heal_num = match.group(1)
                        text = heal_pattern.sub(heal_num, text)
                        has_special_numbers = True
                
                # Set appropriate attributes based on color
                if color_id == 8:  # Gray message log text
                    attributes |= curses.A_DIM  # Add dim attribute to make it gray
                elif color_id in [3, 4]:  # Player colors (green or blue)
                    attributes |= curses.A_BOLD  # Make player text bold
                elif color_id == 7:  # Yellow debuff text
                    attributes |= curses.A_BOLD  # Make debuff text bold for emphasis
                elif color_id == 17:  # Wretch messages (red)
                    attributes |= curses.A_BOLD  # Make wretch messages bold red
                elif color_id == 18:  # Death messages (dark red)
                    attributes |= curses.A_DIM  # Make death messages dim red

                # Apply text wrapping
                wrapped_lines = self._wrap_text(text, max_text_width)
                
                # Store each wrapped line with its metadata
                for line in wrapped_lines:
                    content_lines.append({
                        'text': line,
                        'color_id': color_id,
                        'attributes': attributes,
                        'original_text': original_text,
                        'damage_num': damage_num,
                        'heal_num': heal_num,
                        'has_special_numbers': has_special_numbers
                    })
            
            # Calculate max scroll position based on wrapped lines
            max_scroll = max(0, len(content_lines) - available_height)
            # Clamp scroll position
            self.log_history_scroll = max(0, min(self.log_history_scroll, max_scroll))
            
            # Draw a separator above the status bar
            separator_bottom = "├" + "─" * (term_width - 2) + "┤"
            self.renderer.draw_text(term_height - 2, 0, separator_bottom, 1)
            
            # Draw scroll indicator in status bar
            if len(content_lines) > available_height:
                scroll_pct = int((self.log_history_scroll / max_scroll) * 100) if max_scroll > 0 else 0
                scroll_text = f"Showing {self.log_history_scroll+1}-{min(self.log_history_scroll+available_height, len(content_lines))} " \
                             f"of {len(content_lines)} lines ({scroll_pct}%)"
                self.renderer.draw_text(term_height - 2, 2, scroll_text, 1, curses.A_BOLD)
            else:
                self.renderer.draw_text(term_height - 2, 2, f"Showing all {len(content_lines)} lines", 1, curses.A_BOLD)
            
            # Slice content lines based on scroll position
            visible_lines = content_lines[self.log_history_scroll:self.log_history_scroll+available_height]
            
            # Draw wrapped message lines
            for i, line_data in enumerate(visible_lines):
                y_pos = content_start_y + i
                text = line_data['text']
                color_id = line_data['color_id']
                attributes = line_data['attributes']
                damage_num = line_data['damage_num']
                heal_num = line_data['heal_num']
                original_text = line_data['original_text']
                has_special_numbers = line_data['has_special_numbers']

                # Draw the message, with special handling for damage or heal numbers
                if has_special_numbers and damage_num is not None and damage_num in text:
                    # Render with damage numbers in magenta
                    parts = text.split(damage_num)
                    pos_x = 2

                    # Draw the first part with the regular color
                    if parts[0]:
                        self.renderer.draw_text(y_pos, pos_x, parts[0], color_id, attributes)
                        pos_x += len(parts[0])

                    # Draw the damage number in magenta
                    self.renderer.draw_text(y_pos, pos_x, damage_num, 21, curses.A_BOLD)  # 21 is the magenta color pair
                    pos_x += len(damage_num)

                    # Draw any remaining part with the regular color
                    if len(parts) > 1 and parts[1]:
                        self.renderer.draw_text(y_pos, pos_x, parts[1], color_id, attributes)
                elif has_special_numbers and heal_num is not None and heal_num in text:
                    # Render with heal numbers in white
                    parts = text.split(heal_num)
                    pos_x = 2

                    # Draw the first part with the regular color
                    if parts[0]:
                        self.renderer.draw_text(y_pos, pos_x, parts[0], color_id, attributes)
                        pos_x += len(parts[0])

                    # Draw the heal number in bright white
                    self.renderer.draw_text(y_pos, pos_x, heal_num, 22, curses.A_BOLD)  # 22 is the white color pair with bold
                    pos_x += len(heal_num)

                    # Draw any remaining part with the regular color
                    if len(parts) > 1 and parts[1]:
                        self.renderer.draw_text(y_pos, pos_x, parts[1], color_id, attributes)
                else:
                    # Regular message without colored numbers
                    self.renderer.draw_text(y_pos, 2, text, color_id, attributes)
                
        except Exception as e:
            # Never let log history crash the game
            logger.error(f"Error displaying log history: {str(e)}")
    
    def handle_input(self, key: int) -> bool:
        """Handle input for log history screen."""
        if self.show_log_history:
            if key == curses.KEY_UP:
                # Scroll up
                self.log_history_scroll = max(0, self.log_history_scroll - 1)
                self.game_ui.draw_board()
                return True
            elif key == curses.KEY_DOWN:
                # Scroll down (max scroll is enforced in draw method)
                self.log_history_scroll += 1
                self.game_ui.draw_board()
                return True
            elif key == ord('l'):
                # Toggle regular log view while in history
                self.toggle_message_log()
                self.game_ui.draw_board()
                return True
            elif key == ord('G'):  # Shift+g - go to end
                # Jump to bottom of log
                self.log_history_scroll = 999999  # Value will be clamped in draw method
                self.game_ui.draw_board()
                return True
            elif key == ord('g'):  # g - go to start
                # Jump to top of log
                self.log_history_scroll = 0
                self.game_ui.draw_board()
                return True
                
        return False

# Unit help screen component  
class UnitHelpComponent(UIComponent):
    """Component for displaying unit-specific help pages."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.show_unit_help = False  # Whether to show unit help screen
        self.help_scroll = 0  # Scroll position in help content
        self.unit_help_data = self._load_unit_help_data()
        
    def _wrap_text(self, text: str, max_width: int, indent: str = "") -> list:
        """Wrap text to fit within max_width, preserving word boundaries."""
        if not text or max_width <= 0:
            return [text] if text else [""]
            
        words = text.split()
        if not words:
            return [""]
            
        wrapped_lines = []
        current_line = indent
        
        for word in words:
            # Check if adding this word would exceed the width
            test_line = current_line + (" " if current_line != indent else "") + word
            
            if len(test_line) <= max_width:
                current_line = test_line
            else:
                # If current line has content, save it and start a new line
                if current_line != indent:
                    wrapped_lines.append(current_line)
                    current_line = indent + word
                else:
                    # Word is too long even by itself - truncate it
                    if len(word) > max_width - len(indent):
                        wrapped_lines.append(indent + word[:max_width - len(indent) - 3] + "...")
                        current_line = indent
                    else:
                        current_line = indent + word
        
        # Add the last line if it has content
        if current_line != indent:
            wrapped_lines.append(current_line)
        
        return wrapped_lines if wrapped_lines else [indent]
        
    def _load_unit_help_data(self):
        """Load unit help data for all units."""
        return {
            UnitType.GLAIVEMAN: {
                'title': 'GLAIVEMAN',
                'overview': [
                    'The GLAIVEMAN is a versatile melee warrior wielding a polearm and sacred spinning glaives.',
                    'Balanced between offense and defense, this unit excels at close combat with mobility options',
                    'and area control. The GLAIVEMAN serves as a reliable frontline fighter with powerful',
                    'retaliatory abilities.',
                    '',
                    'Role: Frontline Fighter / Area Controller'
                ],
                'stats': [
                    'HP: 22',
                    'Attack: 4',
                    'Defense: 1', 
                    'Movement: 2',
                    'Range: 2',
                    'Symbol: G'
                ],
                'skills': [
                    {
                        'name': 'AUTOCLAVE (Passive)',
                        'description': 'When near death, unleashes a desperate retaliatory burst of energy in four directions.',
                        'details': [
                            'Type: Passive',
                            'Range: 3',
                            'Target: Enemy units',
                            'Line of Sight: No',
                            'Damage: 8',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: Once per game',
                            'Special: Triggers on critical health damage, heals for half damage dealt'
                        ]
                    },
                    {
                        'name': 'PRY (Active) [Key: P]',
                        'description': 'Uses the glaive as a lever to launch an enemy into the ceiling, causing debris to rain down.',
                        'details': [
                            'Type: Active',
                            'Range: 1',
                            'Target: Enemy unit',
                            'Line of Sight: Yes',
                            'Damage: 6 primary, 3 splash to adjacent enemies',
                            'Pierce: No',
                            'Effects: Pried, -1 movement for 2 turns',
                            'Cooldown: 3 turns'
                        ]
                    },
                    {
                        'name': 'VAULT (Active) [Key: V]',
                        'description': 'Performs an athletic leap to cross obstacles and units.',
                        'details': [
                            'Type: Active',
                            'Range: 2',
                            'Target: Empty terrain',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: 4 turns'
                        ]
                    },
                    {
                        'name': 'JUDGEMENT (Active) [Key: J]',
                        'description': 'Hurls a sacred spinning glaive that pierces through enemy defenses and deals double damage on enemies at critical health',
                        'details': [
                            'Type: Active',
                            'Range: 4',
                            'Target: Enemy unit',
                            'Line of Sight: Yes',
                            'Damage: 4, 8 on critical health enemies',
                            'Pierce: Yes',
                            'Effects: None',
                            'Cooldown: 4 turns'
                        ]
                    }
                ],
                'tips': [
                    '- Use Pry to control enemy positioning and reduce their mobility',
                    '- Vault provides excellent positioning and escape options',
                    '- Judgement is devastating against wounded enemies (double damage at critical health)',
                    '- Autoclave makes the GLAIVEMAN dangerous even when near death',
                    '- Maintain front-line position to threaten multiple enemies with Pry range'
                ],
                'tactical': [
                    '- Strong against: Clustered enemies (Pry splash), high-defense units (Judgement piercing)',
                    '- Vulnerable to: Long-range attacks, status effects',
                    '- Best positioning: Front-center to maximize Autoclave coverage'
                ]
            },
            UnitType.MANDIBLE_FOREMAN: {
                'title': 'MANDIBLE FOREMAN',
                'overview': [
                    'The MANDIBLE FOREMAN is a mechanical supervisor wielding industrial jaw contraptions for area',
                    'control and battlefield management. This durable frontline unit excels at trapping and immobilizing',
                    'enemies while providing tactical support to allies in open terrain. The MANDIBLE FOREMAN serves',
                    'as a close-range specialist focused on movement denial and crowd control.',
                    '',
                    'Role: Frontline Fighter / Area Controller / Disabler'
                ],
                'stats': [
                    'HP: 22',
                    'Attack: 3',
                    'Defense: 1',
                    'Movement: 2',
                    'Range: 1',
                    'Symbol: F'
                ],
                'skills': [
                    {
                        'name': 'VISEROY (Passive)',
                        'description': 'When attacking, traps enemy units in hydraulic mechanical jaws.',
                        'details': [
                            'Type: Passive',
                            'Range: 1',
                            'Target: Enemy unit',
                            'Line of Sight: Yes',
                            'Damage: 3',
                            'Pierce: No',
                            'Effects: Trapped, cannot move, cannot use skills, takes incremental damage over time',
                            'Cooldown: None',
                            'Special: Automatic when attacking'
                        ]
                    },
                    {
                        'name': 'EXPEDITE (Active) [Key: E]',
                        'description': 'Rush up to 4 tiles in a straight line, trapping and damaging the first enemy encountered.',
                        'details': [
                            'Type: Active',
                            'Range: 4',
                            'Target: Line movement',
                            'Line of Sight: Yes',
                            'Damage: 6',
                            'Pierce: No',
                            'Effects: Trapped, cannot move, cannot use skills, takes incremental damage over time',
                            'Cooldown: 3 turns',
                            'Special: Stops at first enemy, must move in straight lines, applies Viseroy trap'
                        ]
                    },
                    {
                        'name': 'SITE INSPECTION (Active) [Key: S]',
                        'description': 'Survey a 3x3 area for tactical analysis, granting scaled bonuses based on terrain obstacles.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: 3x3 area',
                            'Line of Sight: Yes',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Scaled bonuses to allies in area for 3 turns:',
                            '  • 0 terrain: +1 attack & +1 movement (full effect)',
                            '  • 1 terrain: +1 attack only (partial effect)',
                            '  • 2+ terrain: No effect',
                            'Cooldown: 3 turns',
                            'Special: Reveals hidden traps, effect strength depends on terrain count'
                        ]
                    },
                    {
                        'name': 'JAWLINE (Active) [Key: J]',
                        'description': 'Deploy network of mechanical jaws in 3x3 area around yourself, damaging and completely immobilizing adjacent enemies.',
                        'details': [
                            'Type: Active',
                            'Range: 0',
                            'Target: 3x3 area around self',
                            'Line of Sight: No',
                            'Damage: 4',
                            'Pierce: No',
                            'Effects: Jawline, Immobilized for 2 turns',
                            'Cooldown: 3 turns',
                            'Special: Affects all adjacent enemies, complete movement lockdown'
                        ]
                    }
                ],
                'tips': [
                    '- Use Viseroy to control enemy positioning with every attack',
                    '- Expedite provides both gap-closing and guaranteed trap application',
                    '- Position teams strategically: clear areas give full bonuses, lightly obstructed areas give partial',
                    '- Jawline is strong in chokepoints or when surrounded by multiple enemies',
                    '- High HP allows aggressive frontline positioning despite low attack range'
                ],
                'tactical': [
                    '- Strong against: Isolated units',
                    '- Vulnerable to: Ranged attackers, immunity effects, extremely cluttered terrain',
                    '- Best positioning: Frontline in moderately open areas, near chokepoints to maximize Jawline effectiveness'
                ]
            },
            UnitType.GRAYMAN: {
                'title': 'GRAYMAN',
                'overview': [
                    'The GRAYMAN is a psychic entity that manipulates spacetime. This highly mobile unit excels at',
                    'long-range harassment, teleportation tactics, and applying permanent debuffs to enemies. The',
                    'GRAYMAN serves as an elusive skirmisher that phases in and out of combat while weakening foes',
                    'through reality distortion and defense piercing attacks.',
                    '',
                    'Role: Reality Manipulator / Disabler'
                ],
                'stats': [
                    'HP: 18',
                    'Attack: 3',
                    'Defense: 0',
                    'Movement: 2',
                    'Range: 5',
                    'Symbol: Ψ'
                ],
                'skills': [
                    {
                        'name': 'STASIALITY (Passive)',
                        'description': 'Exists outside normal spacetime, granting complete immunity to all external effects and manipulations.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Immunity to all status effects, forced movement, and stat changes',
                            'Cooldown: None',
                            'Special: Cannot be buffed, debuffed, or displaced'
                        ]
                    },
                    {
                        'name': 'DELTA CONFIG (Active) [Key: D]',
                        'description': 'Instantly teleports across spacetime to any unoccupied location on the battlefield.',
                        'details': [
                            'Type: Active',
                            'Range: 99',
                            'Target: Empty passable terrain',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Instant teleportation',
                            'Cooldown: 12 turns',
                            'Special: Unlimited range'
                        ]
                    },
                    {
                        'name': 'ESTRANGE (Active) [Key: E]',
                        'description': 'Fires a reality-warping beam that phases the target partially out of spacetime, permanently weakening them.',
                        'details': [
                            'Type: Active',
                            'Range: 5',
                            'Target: Enemy unit',
                            'Line of Sight: Yes',
                            'Damage: 3',
                            'Pierce: Yes',
                            'Effects: Estranged - -1 to all stats',
                            'Cooldown: 3 turns',
                            'Special: This effect does not wear off'
                        ]
                    },
                    {
                        'name': 'GRÆ EXCHANGE (Active) [Key: G]',
                        'description': 'Creates an echo at current position and teleports to target location, maintaining presence in two places.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: Empty passable terrain',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Creates echo with 5 HP, 3 attack, immobile, lasts 2 turns',
                            'Cooldown: 4 turns',
                            'Special: Expires on owner\'s turns'
                        ]
                    }
                ],
                'tips': [
                    '- Use Stasiality immunity to ignore enemy control abilities and debuffs',
                    '- Delta Config provides unmatched repositioning - use for flanking or escaping danger',
                    '- Estrange permanently weakens key enemy units - prioritize high-value targets',
                    '- Græ Exchange allows attacking from two positions simultaneously',
                    '- Stay at maximum range (5) to avoid retaliation due to 0 defense'
                ],
                'tactical': [
                    '- Strong against: Control-heavy teams, stationary units, long-term engagements',
                    '- Vulnerable to: High direct damage',
                    '- Best positioning: Back lines with escape routes, flanking positions using teleportation'
                ]
            },
            'GRAYMAN_ECHO': {
                'title': 'GRAYMAN ECHO',
                'overview': [
                    'GRAYMAN echoes are temporary psychic projections created by the Græ Exchange skill.',
                    'These immobile entities explode when destroyed, serving as area denial units that',
                    'provide basic combat presence in key locations.',
                    '',
                    'Role: Area Controller'
                ],
                'stats': [
                    'HP: 5',
                    'Attack: 3',
                    'Defense: 0',
                    'Movement: 0',
                    'Range: 1',
                    'Symbol: ψ'
                ],
                'skills': [
                    {
                        'name': 'IMMOBILITY (Passive)',
                        'description': 'Cannot move from creation position.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cannot move',
                            'Cooldown: None',
                            'Special: Fixed position for 2-turn duration'
                        ]
                    },
                    {
                        'name': 'DEATH EXPLOSION (On Death)',
                        'description': 'When destroyed, explodes dealing 4 damage to all adjacent enemy units.',
                        'details': [
                            'Type: On Death',
                            'Range: All adjacent tiles',
                            'Target: Enemy units',
                            'Line of Sight: No',
                            'Damage: 4',
                            'Pierce: No',
                            'Effects: Explosion on death',
                            'Cooldown: None',
                            'Special: Triggers when HP reaches 0'
                        ]
                    }
                ],
                'tips': [
                    '- Plan placement carefully since echoes cannot move',
                    '- Explosion threat forces enemies to keep distance',
                    '- Best placed in chokepoints or near valuable targets',
                    '- Cannot use skills, only basic attacks'
                ],
                'tactical': [
                    '- Strong against: Melee units, clustered formations',
                    '- Limitations: Cannot move, no skills, 2-turn duration, low HP',
                    '- Best positioning: Chokepoints, objective areas, enemy approach routes'
                ]
            },
            UnitType.MARROW_CONDENSER: {
                'title': 'MARROW CONDENSER',
                'overview': [
                    'The MARROW CONDENSER is a quadrupedal fortress builder that manipulates bone matter to create',
                    'defensive structures and enhance its own capabilities. This high-HP tank excels at area',
                    'control through wall creation while growing stronger from enemy deaths within its domain.',
                    'The MARROW CONDENSER serves as a defensive anchor that transforms the battlefield through',
                    'bone manipulation.',
                    '',
                    'Role: Tank / Frontline Fighter / Area Controller'
                ],
                'stats': [
                    'HP: 24',
                    'Attack: 4',
                    'Defense: 2',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: C'
                ],
                'skills': [
                    {
                        'name': 'DOMINION (Passive)',
                        'description': 'Gains permanent upgrades when units die within Marrow Dike walls, becoming stronger with each kill.',
                        'details': [
                            'Type: Passive',
                            'Range: Marrow Dike interior',
                            'Target: Self enhancement',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: First kill: +1 defense, Second kill: +1 attack, Third kill: +1 movement',
                            'Cooldown: None',
                            'Special: Also upgrades active skills in sequence, tracks kill count for Bone Tithe scaling'
                        ]
                    },
                    {
                        'name': 'OSSIFY (Active) [Key: O]',
                        'description': 'Hardens skeletal structure to gain defense bonus at the cost of mobility.',
                        'details': [
                            'Type: Active',
                            'Range: 0',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Ossified, +2 defense, -1 movement for 2 turns',
                            'Cooldown: 3 turns',
                            'Special: +3 defense when upgraded'
                        ]
                    },
                    {
                        'name': 'MARROW DIKE (Active) [Key: M]',
                        'description': 'Creates a 5x5 perimeter of marrow walls around itself, pulling enemies inward.',
                        'details': [
                            'Type: Active',
                            'Range: self',
                            'Target: 5x5 area around self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Mired, -1 move when inside the interior (upgrade only)',
                            'Cooldown: 4 turns',
                            'Special: Upgraded walls have 3 HP and apply Mired to enemies'
                        ]
                    },
                    {
                        'name': 'BONE TITHE (Active) [Key: B]',
                        'description': 'Drains life force from nearby enemies through bone manipulation, healing self.',
                        'details': [
                            'Type: Active',
                            'Range: self',
                            'Target: adjacent tiles around self',
                            'Line of Sight: No',
                            'Damage: 1 (scales with kill count when upgraded)',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: 1 turn',
                            'Special: +1 max HP and current HP per enemy hit (+2 when upgraded)'
                        ]
                    }
                ],
                'tips': [
                    '- Use Marrow Dike to trap enemies and control battlefield positioning',
                    '- Bone Tithe frequently for sustained healing and HP growth',
                    '- Ossify when expecting heavy damage to maximize survivability',
                    '- Position centrally to maximize Bone Tithe hits and Dominion kill opportunities',
                    '- High HP allows aggressive frontline positioning'
                ],
                'tactical': [
                    '- Strong against: Melee units, sustained engagements, clustered enemies',
                    '- Vulnerable to: Long-range attackers, high mobility units, piercing damage',
                    '- Best positioning: Center of enemy groups, chokepoints for wall placement, interior of Marrow Dike'
                ]
            },
            UnitType.FOWL_CONTRIVANCE: {
                'title': 'FOWL CONTRIVANCE',
                'overview': [
                    'The FOWL CONTRIVANCE is a mechanical peacock rail artillery platform that specializes in',
                    'long-range devastation and battlefield control. This unit excels at indirect fire support',
                    'while establishing an explosive rail network.',
                    '',
                    'Role: Artillery / Glass Cannon'
                ],
                'stats': [
                    'HP: 18',
                    'Attack: 5',
                    'Defense: 0',
                    'Movement: 4',
                    'Range: 2',
                    'Symbol: T'
                ],
                'skills': [
                    {
                        'name': 'RAIL GENESIS (Passive)',
                        'description': 'The first FOWL_CONTRIVANCE to deploy establishes a permanent rail network.',
                        'details': [
                            'Type: Passive',
                            'Range: Map-wide',
                            'Target: Battlefield terrain',
                            'Line of Sight: No',
                            'Damage: 4 on death explosion',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: None',
                            'Special: Rail network persists until the last FOWL CONTRIVANCE dies'
                        ]
                    },
                    {
                        'name': 'GAUSSIAN DUSK (Active) [Key: G]',
                        'description': 'Charges a devastating rail gun shot that pierces everything in its path.',
                        'details': [
                            'Type: Active (Two-phase: Charging → Firing)',
                            'Range: Entire map',
                            'Target: Line of destruction',
                            'Line of Sight: No',
                            'Damage: 12',
                            'Pierce: Yes',
                            'Effects: Charging, self, disables move, attack, and skills',
                            'Cooldown: 4 turns, after firing',
                            'Special: Destroys terrain'
                        ]
                    },
                    {
                        'name': 'BIG ARC (Active) [Key: B]',
                        'description': 'Launches explosive mortar shells in a 3x3 area.',
                        'details': [
                            'Type: Active',
                            'Range: 6',
                            'Target: 3x3 area',
                            'Line of Sight: No',
                            'Damage: 8 primary, 5 adjacent',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: 4 turns',
                            'Special: Cannot target adjacent tiles'
                        ]
                    },
                    {
                        'name': 'FRAGCREST (Active) [Key: F]',
                        'description': 'Deploys a directional fragmentation burst that fans out in a cone, firing explosive shrapnel that blasts enemies backward and embeds fragments for ongoing damage.',
                        'details': [
                            'Type: Active',
                            'Range: 4',
                            'Target: Cone area (90-degree spread)',
                            'Line of Sight: Yes',
                            'Damage: 4 primary, 2 secondary',
                            'Pierce: No',
                            'Effects: Shrapnel, 1 damage per turn for 3 turns',
                            'Cooldown: 3 turns',
                            'Special: Pushes enemies away'
                        ]
                    }
                ],
                'tips': [
                    '- Use Gaussian Dusk for maximum damage output but plan the charging turn carefully',
                    '- Big Arc excels against clustered enemies and ignores line of sight restrictions',
                    '- Fragcrest provides crowd control through knockback and area denial via shrapnel',
                    '- High movement allows for repositioning between artillery strikes'
                ],
                'tactical': [
                    '- Strong against: Clustered enemies, static formations, low-mobility units, units with high defence',
                    '- Vulnerable to: High-mobility rushers, units that can close distance quickly, area denial, high burst damage',
                    '- Best positioning: Behind cover, near rail network access points for quick repositioning'
                ]
            },
            UnitType.GAS_MACHINIST: {
                'title': 'GAS MACHINIST',
                'overview': [
                    'The GAS MACHINIST is a vapor-controlling technician that specializes in battlefield',
                    'manipulation through chemical entities. This support unit excels at creating HEINOUS VAPOR',
                    'minions that provide area control, healing, and damage over time.',
                    '',
                    'Role: Summoner / Utility / Area Controller'
                ],
                'stats': [
                    'HP: 18',
                    'Attack: 4',
                    'Defense: 1',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: M'
                ],
                'skills': [
                    {
                        'name': 'EFFLUVIUM LATHE (Passive)',
                        'description': 'Generates 1 Effluvium charge per turn (max 4). Charges extend HEINOUS VAPOR duration by 1 turn each.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Charge generation',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Generates charges, extends vapor duration',
                            'Cooldown: None',
                            'Special: Does not generate charges while diverged, starts with 1 charge'
                        ]
                    },
                    {
                        'name': 'BROACHING GAS (Active) [Key: B]',
                        'description': 'Summons a HEINOUS VAPOR (Φ) that deals damage to enemies and cleanses allies of negative status effects.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: Empty tile',
                            'Line of Sight: No',
                            'Damage: 2',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: 2 turns',
                            'Special: Vapor cleanses ally status effects, invulnerable unit'
                        ]
                    },
                    {
                        'name': 'SAFT-E-GAS (Active) [Key: S]',
                        'description': 'Summons a HEINOUS VAPOR (Θ) that blocks enemy targeting and heals allies.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: Empty tile',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: 3 turns',
                            'Special: Prevents being targetted from outside of the area of effect, heals allies, invulnerable unit'
                        ]
                    },
                    {
                        'name': 'DIVERGE (Active) [Key: D]',
                        'description': 'Splits an existing HEINOUS VAPOR or self into Coolant Gas and Cutting Gas.',
                        'details': [
                            'Type: Active',
                            'Range: 5',
                            'Target: Self or owned HEINOUS VAPOR',
                            'Line of Sight: No',
                            'Damage: 3',
                            'Pierce: Yes',
                            'Effects: None',
                            'Cooldown: 4 turns',
                            'Special: Self-targeting removes GAS MACHINIST until vapors expire. Coolant gas heals allied units for 3 HP'
                        ]
                    }
                ],
                'tips': [
                    '- Build up Effluvium charges early to maximize vapor duration',
                    '- Use Broaching Gas for enemy damage and ally cleansing',
                    '- Deploy Saft-E-Gas defensively to block ranged attacks and heal',
                    '- Diverge gasses to extend their effectiveness',
                    '- Self-diverge to become invulernable, maximize area control, or escape'
                ],
                'tactical': [
                    '- Strong against: Status effect users, ranged attackers, sustained damage teams',
                    '- Vulnerable to: Burst damage, high mobility units that can avoid vapors, area denial',
                    '- Best positioning: Behind frontlines, near allies for vapor support, central locations for maximum vapor coverage'
                ]
            },
            UnitType.DELPHIC_APPRAISER: {
                'title': 'DELPHIC APPRAISER',
                'overview': [
                    'The DELPHIC APPRAISER is a furniture evaluator with cosmic value perception that',
                    'specializes in exploiting the metaphysical properties of terrain. This support unit excels',
                    'at creating tactical advantages through furniture manipulation, teleportation networks,',
                    'and reality distortion effects.',
                    '',
                    'Role: Utility / Reality Manipulator / Gambler'
                ],
                'stats': [
                    'HP: 20',
                    'Attack: 4',
                    'Defense: 0',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: A'
                ],
                'skills': [
                    {
                        'name': 'VALUATION ORACLE (Passive)',
                        'description': 'Perceives the \'cosmic value\' of furniture at spawn.',
                        'details': [
                            'Type: Passive',
                            'Range: Adjacent tiles',
                            'Target: Furniture terrain',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Valuation Oracle, gains +1 to defense and attack range',
                            'Cooldown: None',
                            'Special: Bonuses last while adjacent to any furniture'
                        ]
                    },
                    {
                        'name': 'MARKET FUTURES (Active) [Key: M]',
                        'description': 'Imbues a furniture piece with temporal investment energy, turning it into a portal.',
                        'details': [
                            'Type: Active',
                            'Range: 4',
                            'Target: Furniture piece',
                            'Line of Sight: Yes',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Parallax, applied when adjacent to the anchor. Investment, applied on teleport',
                            'Cooldown: 6 turns',
                            'Special: Teleport range equals cosmic value. Maturing investment grants +1 ATK per turn'
                        ]
                    },
                    {
                        'name': 'AUCTION CURSE (Active) [Key: A]',
                        'description': 'Curse target enemy with a twisted auction.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: Enemy unit',
                            'Line of Sight: Yes',
                            'Damage: 1 per turn (based on cosmic values)',
                            'Pierce: No',
                            'Effects: Auction Curse, each tick inflates nearby furniture by +1, heals allies within 2 tiles by 1 HP, and prevents healing',
                            'Cooldown: 4 turns',
                            'Special: Duration equals average cosmic value of furniture within 2 tiles'
                        ]
                    },
                    {
                        'name': 'DIVINE DEPRECIATION (Active) [Key: D]',
                        'description': 'Dramatically reappraises a furniture piece as cosmically worthless, creating a 7×7 reality sinkhole.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: Furniture piece (7×7 area effect)',
                            'Line of Sight: Yes',
                            'Damage: Based on cosmic value difference',
                            'Pierce: Yes',
                            'Effects: None',
                            'Cooldown: 6 turns',
                            'Special: Sets target furniture to cosmic value 1. Damage equals average cosmic value of other furniture minus1. Pull distance equals average enemy movement minus 1. Rerolls all other furniture cosmic values'
                        ]
                    }
                ],
                'tips': [
                    '- Position near furniture to maintain Valuation Oracle bonuses',
                    '- Use Market Futures to create tactical teleports for team mobility',
                    '- Auction Curse works best in furniture-dense areas for maximum damage over time',
                    '- Divine Depreciation is devastating in furniture-heavy zones - plan positioning carefully'
                ],
                'tactical': [
                    '- Strong against: Static formations, low-mobility units, position-reliant strategies',
                    '- Vulnerable to: High burst damage, open area engagements, mobility-based counters',
                    '- Best positioning: Central furniture clusters, defensive positions near valuable terrain'
                ]
            },
            UnitType.INTERFERER: {
                'title': 'INTERFERER',
                'overview': [
                    'The INTERFERER is a telecommunications engineer turned assassin who weaponized a remote',
                    'radio tower array into a directed energy system. This glass cannon "phones home" to coordinate',
                    'precise strikes, neural interference, and electromagnetic warfare through triangulated',
                    'transmissions from the tower network. Also attacks with plutonium tipped carabiners.',
                    '',
                    'Role: Glass Cannon / Disabler'
                ],
                'stats': [
                    'HP: 18',
                    'Attack: 4', 
                    'Defense: 0',
                    'Movement: 2',
                    'Range: 1 (Melee)',
                    'Symbol: R',
                    'Attack Symbol: x'
                ],
                'skills': [
                    {
                        'name': 'NEUTRON ILLUMINANT (Passive)',
                        'description': 'Directional radiation spreads around the INTERFERER when attacking.',
                        'details': [
                            'Type: Passive',
                            'Trigger: On attack (no cooldown)',
                            'Effect: Creates radiation pattern around INTERFERER',
                            'Radiation Damage: 1 per stack per turn',
                            'Radiation Duration: 2 turns per stack',
                            'Special: Cardinal attacks radiate diagonally, diagonal attacks radiate cardinally'
                        ]
                    },
                    {
                        'name': 'NEURAL SHUNT (Active) [Key: N]',
                        'description': 'Tower array transmits neural interference signal to hijack target\'s mind.',
                        'details': [
                            'Type: Active',
                            'Range: 1',
                            'Target: Any unit',
                            'Line of Sight: Yes',
                            'Damage: 8',
                            'Pierce: No',
                            'Effects: Neural control for 2 turns',
                            'Cooldown: 4 turns',
                            'Special: Affected unit performs random moves, attacks, or skills for 2 turns'
                        ]
                    },
                    {
                        'name': 'KARRIER RAVE (Active) [Key: K]',
                        'description': 'Rides karrier wave transmission to phase out, becoming untargetable.',
                        'details': [
                            'Type: Active',
                            'Range: Self-target',
                            'Target: Self',
                            'Line of Sight: N/A',
                            'Damage: None',
                            'Pierce: N/A',
                            'Effects: Untargetable for 2 turns, next attack strikes 3 times',
                            'Cooldown: 5 turns',
                            'Special: Cannot be targeted by any attacks or skills while phased'
                        ]
                    },
                    {
                        'name': 'SCALAR NODE (Active) [Key: S]',
                        'description': 'Triangulates coordinates to create standing wave energy trap.',
                        'details': [
                            'Type: Active',
                            'Range: 3',
                            'Target: Empty tile',
                            'Line of Sight: Yes',
                            'Damage: 12 pierce',
                            'Pierce: Yes',
                            'Effects: Invisible trap, silent warfare',
                            'Cooldown: 3 turns',
                            'Special: No message log entries, triggers when enemies end turn on trap'
                        ]
                    }
                ],
                'tips': [
                    '- Use radiation spread to control enemy positioning and create damage zones',
                    '- Neural Shunt can disrupt enemy plans by forcing random actions',
                    '- Time Karrier Rave carefully to avoid counterattacks and set up triple strikes',
                    '- Place Scalar Nodes on likely enemy movement paths for maximum effectiveness'
                ],
                'tactical': [
                    '- Strong against: High-HP units (radiation damage), ranged units (closing distance), predictable formations',
                    '- Vulnerable to: Area attacks (low defense), burst damage (glass cannon), detection abilities',
                    '- Best positioning: Behind cover, flanking positions, near enemy movement corridors'
                ]
            },
            'HEINOUS_VAPOR_BROACHING': {
                'title': 'BROACHING GAS (Φ)',
                'overview': [
                    'BROACHING GAS is a HEINOUS VAPOR entity summoned by the GAS MACHINIST using the Broaching',
                    'Gas skill. This vapor specializes in dual-purpose area control, dealing 2 damage to enemies',
                    'while cleansing allies of negative status effects within its 3×3 area of influence.',
                    '',
                    'Role: Utility / Area Controller'
                ],
                'stats': [
                    'HP: 10',
                    'Attack: 0',
                    'Defense: 0',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: Φ'
                ],
                'skills': [
                    {
                        'name': 'INVULNERABILITY (Passive)',
                        'description': 'Complete immunity to all damage sources and status effects.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cannot take damage, immune to all debuffs',
                            'Cooldown: None',
                            'Special: Can only be removed through natural expiration'
                        ]
                    },
                    {
                        'name': 'ENEMY DAMAGE (Area Damage)',
                        'description': 'Deals 2 damage to all enemy units within the 3×3 area each turn.',
                        'details': [
                            'Type: Area Damage',
                            'Range: 3×3 centered on vapor',
                            'Target: Enemy units in area',
                            'Line of Sight: No',
                            'Damage: 2 per turn',
                            'Pierce: No',
                            'Effects: None',
                            'Cooldown: None',
                            'Special: Activates during owner\'s turn'
                        ]
                    },
                    {
                        'name': 'ALLY CLEANSING (Status Cleansing)',
                        'description': 'Removes negative status effects from allied units within the area.',
                        'details': [
                            'Type: Status Cleansing',
                            'Range: 3×3 centered on vapor',
                            'Target: Allied units in area',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cleansing (Estrangement, Pry penalty, Jawline immobilization)',
                            'Cooldown: None',
                            'Special: Immediate upon entering area or start of turn'
                        ]
                    }
                ],
                'tips': [
                    '- Position to maximize enemy exposure while protecting allies',
                    '- Use movement to chase retreating enemies or reposition for optimal coverage',
                    '- Coordinate with team movement to ensure allies benefit from cleansing',
                    '- Build maximum Effluvium charges before summoning for longest duration'
                ],
                'tactical': [
                    '- Strong against: Debuff-heavy teams, clustered formations, low-mobility enemies',
                    '- Limitations: Cannot directly attack, requires positioning for effectiveness',
                    '- Best positioning: Chokepoints, objective areas, ally support zones'
                ]
            },
            'HEINOUS_VAPOR_SAFT_E': {
                'title': 'SAFT-E-GAS (Θ)',
                'overview': [
                    'SAFT-E-GAS is a HEINOUS VAPOR entity summoned by the GAS MACHINIST using the Saft-E-Gas',
                    'skill. This vapor specializes in defensive area control, blocking ranged attacks while',
                    'healing allied units within its 3×3 protective area.',
                    '',
                    'Role: Utility / Area Controller'
                ],
                'stats': [
                    'HP: 10',
                    'Attack: 0',
                    'Defense: 0',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: Θ'
                ],
                'skills': [
                    {
                        'name': 'INVULNERABILITY (Passive)',
                        'description': 'Complete immunity to all damage sources and status effects.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cannot take damage, immune to all debuffs',
                            'Cooldown: None',
                            'Special: Can only be removed through natural expiration'
                        ]
                    },
                    {
                        'name': 'RANGED ATTACK BLOCKING (Defensive Barrier)',
                        'description': 'Prevents enemies outside the vapor cloud from targeting allies within the protected area.',
                        'details': [
                            'Type: Defensive Barrier',
                            'Range: 3×3 centered on vapor',
                            'Target: Allied units in area',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Protection from external ranged attacks',
                            'Cooldown: None',
                            'Special: Enemies inside same vapor cloud can still target protected allies'
                        ]
                    },
                    {
                        'name': 'ALLY HEALING (Area Healing)',
                        'description': 'Heals allied units within the area for 1 HP per turn.',
                        'details': [
                            'Type: Area Healing',
                            'Range: 3×3 centered on vapor',
                            'Target: Allied units below max HP',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Healing +1 HP per turn',
                            'Cooldown: None',
                            'Special: Activates during owner\'s turn'
                        ]
                    }
                ],
                'tips': [
                    '- Position to cover the maximum number of vulnerable allies',
                    '- Use movement to maintain protection as allies advance or retreat',
                    '- Place strategically to force enemies into melee engagement',
                    '- Build maximum Effluvium charges before summoning for longest duration'
                ],
                'tactical': [
                    '- Strong against: Ranged attackers, sustained damage teams, area denial strategies',
                    '- Limitations: Cannot directly damage enemies, requires positioning for effectiveness',
                    '- Best positioning: Between allies and enemy ranged units, near damaged allies'
                ]
            },
            'HEINOUS_VAPOR_COOLANT': {
                'title': 'COOLANT GAS (Σ)',
                'overview': [
                    'COOLANT GAS is a HEINOUS VAPOR entity created by the GAS MACHINIST using the Diverge',
                    'skill. This vapor specializes in healing, providing 3 HP healing per turn to allies',
                    'within its 3×3 area of influence.',
                    '',
                    'Role: Utility / Area Controller'
                ],
                'stats': [
                    'HP: 10',
                    'Attack: 0',
                    'Defense: 0',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: Σ'
                ],
                'skills': [
                    {
                        'name': 'INVULNERABILITY (Passive)',
                        'description': 'Complete immunity to all damage sources and status effects.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cannot take damage, immune to all debuffs',
                            'Cooldown: None',
                            'Special: Can only be removed through natural expiration'
                        ]
                    },
                    {
                        'name': 'ALLY HEALING (Area Healing)',
                        'description': 'Heals allied units within the area for 3 HP per turn.',
                        'details': [
                            'Type: Area Healing',
                            'Range: 3×3 centered on vapor',
                            'Target: Allied units below max HP',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Healing +3 HP per turn',
                            'Cooldown: None',
                            'Special: Activates during owner\'s turn'
                        ]
                    }
                ],
                'tips': [
                    '- Build maximum Effluvium charges before using Diverge for longest healing duration',
                    '- Position to cover the most critically wounded allies',
                    '- Use movement to maintain healing coverage as battle lines shift',
                    '- Coordinate with CUTTING GAS for simultaneous healing and damage pressure'
                ],
                'tactical': [
                    '- Strong against: Attrition strategies, sustained damage, low-healing teams',
                    '- Limitations: No protective or offensive capabilities, requires positioning',
                    '- Best positioning: Central ally clusters, objective defense points, critical unit support zones'
                ]
            },
            'HEINOUS_VAPOR_CUTTING': {
                'title': 'CUTTING GAS (%)',
                'overview': [
                    'CUTTING GAS is a HEINOUS VAPOR entity created by the GAS MACHINIST using the Diverge',
                    'skill. This vapor specializes in offensive area control, dealing 3 piercing damage per',
                    'turn to all enemies within its 3×3 area of influence.',
                    '',
                    'Role: Utility / Area Controller'
                ],
                'stats': [
                    'HP: 10',
                    'Attack: 0',
                    'Defense: 0',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: %'
                ],
                'skills': [
                    {
                        'name': 'INVULNERABILITY (Passive)',
                        'description': 'Complete immunity to all damage sources and status effects.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cannot take damage, immune to all debuffs',
                            'Cooldown: None',
                            'Special: Can only be removed through natural expiration'
                        ]
                    },
                    {
                        'name': 'PIERCING DAMAGE (Area Damage)',
                        'description': 'Deals 3 piercing damage per turn to all enemy units in the area.',
                        'details': [
                            'Type: Area Damage',
                            'Range: 3×3 centered on vapor',
                            'Target: Enemy units in area',
                            'Line of Sight: No',
                            'Damage: 3 piercing per turn',
                            'Pierce: Yes',
                            'Effects: Bypasses all defense',
                            'Cooldown: None',
                            'Special: Activates during owner\'s turn'
                        ]
                    }
                ],
                'tips': [
                    '- Build maximum Effluvium charges before using Diverge for longest damage duration',
                    '- Position to cover enemy clusters or chokepoints',
                    '- Use movement to chase retreating enemies or deny key areas',
                    '- Coordinate with COOLANT GAS for simultaneous healing and damage pressure'
                ],
                'tactical': [
                    '- Strong against: High-defense units, clustered enemies, static formations',
                    '- Limitations: Cannot heal or protect allies, requires positioning for effectiveness',
                    '- Best positioning: Enemy clusters, chokepoints, high-value target areas'
                ]
            },
            UnitType.HEINOUS_VAPOR: {
                'title': 'HEINOUS VAPOR',
                'overview': [
                    'HEINOUS VAPOR entities are summoned by the GAS MACHINIST and serve as battlefield',
                    'manipulators with diverse abilities. Each vapor type has unique properties and',
                    'effects based on the skill used to create it.',
                    '',
                    'Role: Summoned Entity / Area Control / Support'
                ],
                'stats': [
                    'HP: 10',
                    'Attack: 0',
                    'Defense: 0',
                    'Movement: 3',
                    'Range: 1',
                    'Symbol: V (varies by type)'
                ],
                'skills': [
                    {
                        'name': 'INVULNERABILITY (Passive)',
                        'description': 'Complete immunity to all damage sources and status effects.',
                        'details': [
                            'Type: Passive',
                            'Range: Self',
                            'Target: Self',
                            'Line of Sight: No',
                            'Damage: None',
                            'Pierce: No',
                            'Effects: Cannot take damage, immune to all debuffs',
                            'Cooldown: None',
                            'Special: Can only be removed through natural expiration or Diverge skill'
                        ]
                    }
                ],
                'tips': [
                    '- Each vapor type has unique area effects and abilities',
                    '- Duration depends on GAS MACHINIST\'s Effluvium charges when summoned',
                    '- Can be targeted by Diverge skill to split into two different vapor types',
                    '- Move strategically to maximize area coverage and effects'
                ],
                'tactical': [
                    '- Abilities vary by vapor type - check specific vapor help for details',
                    '- Generally strong against: Status effect users, clustered enemies',
                    '- Best positioning: Strategic locations for maximum area control'
                ]
            }
        }
    
    def toggle_unit_help(self, unit_type=None):
        """Toggle the unit help screen for a specific unit type."""
        # Can't use unit help screen while in chat mode
        if self.game_ui.chat_component.chat_mode:
            return
            
        # If already showing, hide it
        if self.show_unit_help:
            self.show_unit_help = False
            self.help_scroll = 0
        # If unit_type provided and we have data for it, show it
        elif unit_type and unit_type in self.unit_help_data:
            self.show_unit_help = True
            self.current_unit_type = unit_type
            self.help_scroll = 0
        else:
            return
        
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
        # Display message in UI only, don't add to message log
        if self.show_unit_help:
            self.game_ui.message = f"{self.unit_help_data[unit_type]['title']} help shown"
        else:
            self.game_ui.message = "Unit help hidden"
    
    def handle_input(self, key: int) -> bool:
        """Handle input while unit help screen is active."""
        if not self.show_unit_help:
            return False
            
        if key == 27:  # ESC key
            self.toggle_unit_help()
            self.game_ui.draw_board()
            return True
        elif key == ord('?'):
            self.toggle_unit_help()
            self.game_ui.draw_board()
            return True
        elif key == curses.KEY_UP:
            # Scroll up
            self.help_scroll = max(0, self.help_scroll - 1)
            self.game_ui.draw_board()
            return True
        elif key == curses.KEY_DOWN:
            # Scroll down (max scroll is enforced in draw method)
            self.help_scroll += 1
            self.game_ui.draw_board()
            return True
        elif key == ord('G'):  # Shift+g - go to end
            # Jump to bottom
            self.help_scroll = 999999  # Value will be clamped in draw method
            self.game_ui.draw_board()
            return True
        elif key == ord('g'):  # g - go to start
            # Jump to top
            self.help_scroll = 0
            self.game_ui.draw_board()
            return True
                
        return False
    
    def draw_unit_help_screen(self):
        """Draw the unit help screen with scrolling."""
        if not self.show_unit_help or not hasattr(self, 'current_unit_type'):
            return
            
        try:
            # Get terminal size
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Clear the screen first
            for y in range(term_height):
                self.renderer.draw_text(y, 0, " " * term_width, 1)
            
            # Get unit data
            unit_data = self.unit_help_data[self.current_unit_type]
            
            # Draw border around the entire screen
            # Top border with title
            border_top = f"┌─── {unit_data['title']} HELP " + "─" * (term_width - len(unit_data['title']) - 8) + "┐"
            self.renderer.draw_text(0, 0, border_top, 1, curses.A_BOLD)
            
            # Side borders
            for y in range(1, term_height - 1):
                self.renderer.draw_text(y, 0, "│", 1)
                self.renderer.draw_text(y, term_width - 1, "│", 1)
            
            # Bottom border
            border_bottom = "└" + "─" * (term_width - 2) + "┘"
            self.renderer.draw_text(term_height - 1, 0, border_bottom, 1)
            
            # Define content area dimensions
            content_start_y = 3  # After the navigation bar
            content_end_y = term_height - 3  # Before the status bar
            available_height = content_end_y - content_start_y
            
            # Draw navigation instructions in a bar
            nav_bar = "│ " + "─" * (term_width - 4) + " │"
            self.renderer.draw_text(1, 0, nav_bar, 1)
            nav_text = "↑/↓: Scroll | g/G: Start/End | ESC/?: Close"
            self.renderer.draw_text(1, 2, nav_text, 1, curses.A_BOLD)
            
            # Draw a separator below the navigation
            separator = "├" + "─" * (term_width - 2) + "┤"
            self.renderer.draw_text(2, 0, separator, 1)
            
            # Build content lines with text wrapping
            content_lines = []
            max_text_width = term_width - 4  # Leave margin for borders
            
            # Overview section
            for line in unit_data['overview']:
                if line:  # Non-empty line
                    wrapped_lines = self._wrap_text(line, max_text_width)
                    content_lines.extend(wrapped_lines)
                else:  # Empty line
                    content_lines.append('')
            content_lines.append('')
            
            # Base Stats section
            content_lines.append('BASE STATS')
            content_lines.extend(unit_data['stats'])
            content_lines.append('')
            content_lines.append('─' * max_text_width)
            content_lines.append('')
            
            # Skills section
            content_lines.append('SKILLS')
            content_lines.append('')
            for skill in unit_data['skills']:
                # Skill name
                content_lines.append(f"● {skill['name']}")
                
                # Skill description with wrapping
                wrapped_desc = self._wrap_text(skill['description'], max_text_width)
                content_lines.extend(wrapped_desc)
                content_lines.append('')
                
                # Skill details with wrapping
                for detail in skill['details']:
                    wrapped_detail = self._wrap_text(detail, max_text_width, "  - ")
                    # For wrapped lines after the first, use continuation indent
                    for i, line in enumerate(wrapped_detail):
                        if i > 0:
                            # Replace "  - " with "    " for continuation lines
                            line = "    " + line[4:]
                        content_lines.append(line)
                content_lines.append('')
            
            content_lines.append('─' * max_text_width)
            content_lines.append('')
            
            # Combat Tips section
            content_lines.append('COMBAT TIPS')
            for tip in unit_data['tips']:
                wrapped_tip = self._wrap_text(tip, max_text_width)
                content_lines.extend(wrapped_tip)
            content_lines.append('')
            
            # Tactical Notes section  
            content_lines.append('TACTICAL NOTES')
            for note in unit_data['tactical']:
                wrapped_note = self._wrap_text(note, max_text_width)
                content_lines.extend(wrapped_note)
            
            # Calculate max scroll position
            max_scroll = max(0, len(content_lines) - available_height)
            # Clamp scroll position
            self.help_scroll = max(0, min(self.help_scroll, max_scroll))
            
            # Draw a separator above the status bar
            separator_bottom = "├" + "─" * (term_width - 2) + "┤"
            self.renderer.draw_text(term_height - 2, 0, separator_bottom, 1)
            
            # Draw scroll indicator in status bar
            if len(content_lines) > available_height:
                scroll_pct = int((self.help_scroll / max_scroll) * 100) if max_scroll > 0 else 0
                scroll_text = f"Showing {self.help_scroll+1}-{min(self.help_scroll+available_height, len(content_lines))} " \
                             f"of {len(content_lines)} lines ({scroll_pct}%)"
                self.renderer.draw_text(term_height - 2, 2, scroll_text, 1, curses.A_BOLD)
            else:
                self.renderer.draw_text(term_height - 2, 2, f"Showing all {len(content_lines)} lines", 1, curses.A_BOLD)
            
            # Slice content based on scroll position
            visible_lines = content_lines[self.help_scroll:self.help_scroll+available_height]
            
            # Draw content lines
            for i, line in enumerate(visible_lines):
                y_pos = content_start_y + i
                
                # Set appropriate styling
                attributes = 0
                color_id = 1
                
                if line.startswith('●'):  # Skill names
                    attributes = curses.A_BOLD
                    color_id = 3  # Green
                elif line.startswith('BASE STATS') or line.startswith('SKILLS') or line.startswith('COMBAT TIPS') or line.startswith('TACTICAL NOTES'):
                    attributes = curses.A_BOLD
                    color_id = 7  # Yellow
                elif line.startswith('  - ') or line.startswith('    '):  # Skill details and continuation lines
                    color_id = 8  # Gray
                elif line.startswith('─'):  # Section separators
                    color_id = 8  # Gray
                
                # Draw the line
                self.renderer.draw_text(y_pos, 2, line, color_id, attributes)
                
        except Exception as e:
            # Never let unit help crash the game
            from boneglaive.utils.debug import logger
            logger.error(f"Error displaying unit help: {str(e)}")

# Help screen component
class HelpComponent(UIComponent):
    """Component for displaying the help screen."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.show_help = False  # Whether to show help screen
        self.help_scroll = 0  # Scroll position in help content
    
    def _setup_event_handlers(self):
        """Set up event handlers for the help component."""
        # Subscribe to chat toggle events to handle conflicts
        self.subscribe_to_event(EventType.CHAT_TOGGLED, self._on_chat_toggled)
        
    def _on_chat_toggled(self, event_type, event_data):
        """Handle chat mode toggle events."""
        # If chat is enabled and help is showing, hide help
        chat_enabled = event_data.chat_enabled if hasattr(event_data, 'chat_enabled') else False
        if chat_enabled and self.show_help:
            self.show_help = False
            self.publish_event(
                EventType.HELP_TOGGLED,
                EventData(show_help=False)
            )
            
    def toggle_help_screen(self):
        """Toggle the help screen display."""
        # Can't use help screen while in chat mode
        if self.game_ui.chat_component.chat_mode:
            return
            
        self.show_help = not self.show_help
        
        # Reset scroll when toggling
        if self.show_help:
            self.help_scroll = 0
        
        # Publish help toggled event
        self.publish_event(
            EventType.HELP_TOGGLED,
            EventData(show_help=self.show_help)
        )
        
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
        # Display message in UI only, don't add to message log
        self.game_ui.message = f"Help screen {'shown' if self.show_help else 'hidden'}"
    
    def handle_input(self, key: int) -> bool:
        """Handle input while help screen is active."""
        if not self.show_help:
            return False
            
        if key == 27:  # ESC key
            self.toggle_help_screen()
            self.game_ui.draw_board()
            return True
        elif key == ord('?'):
            self.toggle_help_screen()
            self.game_ui.draw_board()
            return True
        elif key == curses.KEY_UP:
            # Scroll up
            self.help_scroll = max(0, self.help_scroll - 1)
            self.game_ui.draw_board()
            return True
        elif key == curses.KEY_DOWN:
            # Scroll down (max scroll is enforced in draw method)
            self.help_scroll += 1
            self.game_ui.draw_board()
            return True
        elif key == ord('G'):  # Shift+g - go to end
            # Jump to bottom
            self.help_scroll = 999999  # Value will be clamped in draw method
            self.game_ui.draw_board()
            return True
        elif key == ord('g'):  # g - go to start
            # Jump to top
            self.help_scroll = 0
            self.game_ui.draw_board()
            return True
                
        return False
    
    def draw_help_screen(self):
        """Draw the help screen overlay with improved formatting and scrolling."""
        try:
            # Get terminal size
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Clear the screen first
            for y in range(term_height):
                self.renderer.draw_text(y, 0, " " * term_width, 1)
            
            # Draw border around the entire screen
            # Top border with title
            border_top = "┌─── BONEGLAIVE HELP " + "─" * (term_width - 21) + "┐"
            self.renderer.draw_text(0, 0, border_top, 1, curses.A_BOLD)
            
            # Side borders
            for y in range(1, term_height - 1):
                self.renderer.draw_text(y, 0, "│", 1)
                self.renderer.draw_text(y, term_width - 1, "│", 1)
            
            # Bottom border with controls
            controls_text = "ESC/? to close | ↑/↓ to scroll | g/G to start/end"
            border_bottom = "└─ " + controls_text + " " + "─" * (term_width - len(controls_text) - 5) + "┘"
            self.renderer.draw_text(term_height - 1, 0, border_bottom, 1, curses.A_BOLD)
            
            # Build all content lines first
            content_lines = []
            
            # Movement Controls section
            content_lines.append(("MOVEMENT CONTROLS:", 1, curses.A_BOLD))
            content_lines.append(("Arrow Keys        Move cursor around the battlefield", 1, 0))
            content_lines.append(("Tab               Cycle forward through your units", 1, 0))
            content_lines.append(("Shift+Tab         Cycle backward through your units", 1, 0))
            content_lines.append(("", 1, 0))  # Empty line
            
            # Unit Actions section
            content_lines.append(("UNIT ACTIONS:", 1, curses.A_BOLD))
            content_lines.append(("Enter/Space       Select unit or confirm action", 1, 0))
            content_lines.append(("m                 Enter movement mode for selected unit", 1, 0))
            content_lines.append(("a                 Enter attack mode for selected unit", 1, 0))
            content_lines.append(("s                 Use selected unit's active skill", 1, 0))
            content_lines.append(("p                 Use a teleport anchor created by Market Futures", 1, 0))
            content_lines.append(("t                 End current player's turn", 1, 0))
            content_lines.append(("", 1, 0))  # Empty line
            
            # Interface Controls section
            content_lines.append(("INTERFACE CONTROLS:", 1, curses.A_BOLD))
            content_lines.append(("Esc/c             Cancel current action or clear selection", 1, 0))
            content_lines.append(("l                 Toggle message log display", 1, 0))
            content_lines.append(("L                 Show full message history (Shift+L)", 1, 0))
            content_lines.append(("r                 Enter chat/message mode", 1, 0))
            content_lines.append(("?                 Toggle this help screen", 1, 0))
            content_lines.append(("q                 Quit game", 1, 0))
            content_lines.append(("", 1, 0))  # Empty line
            
            # Game Information section
            content_lines.append(("GAME INFORMATION:", 1, curses.A_BOLD))
            content_lines.append(("• Select a unit and press a key to see detailed help for that unit type", 7, 0))
            content_lines.append(("• Units have unique skills - experiment with 's' key when units are selected", 7, 0))
            content_lines.append(("• Some units have multiple skills - check unit help for complete abilities", 7, 0))
            content_lines.append(("• Game mode: VS AI - defeat all enemy units to win", 7, 0))
            content_lines.append(("• Turn-based: complete your moves and actions, then press 't' to end turn", 7, 0))
            
            # Calculate content display area
            content_start_y = 2
            content_height = term_height - 3  # Reserve space for top border and bottom border
            
            # Enforce scroll limits
            max_scroll = max(0, len(content_lines) - content_height)
            self.help_scroll = max(0, min(self.help_scroll, max_scroll))
            
            # Draw visible content lines
            for i, (text, color, attrs) in enumerate(content_lines[self.help_scroll:]):
                display_y = content_start_y + i
                if display_y >= term_height - 1:  # Don't overlap bottom border
                    break
                    
                # Determine indent based on content type
                indent = 2 if attrs == curses.A_BOLD else 4
                self.renderer.draw_text(display_y, indent, text, color, attrs)
            
        except Exception as e:
            logger.error(f"Error displaying help screen: {str(e)}")

# Chat component
class ChatComponent(UIComponent):
    """Component for handling chat input and display."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.chat_mode = False  # Whether in chat input mode
        self.chat_input = ""  # Current chat input text
        self.player_colors = {1: 3, 2: 4}  # Player colors (matching message_log)
    
    def _setup_event_handlers(self):
        """Set up event handlers for the chat component."""
        # Subscribe to help toggle events to handle conflicts
        self.subscribe_to_event(EventType.HELP_TOGGLED, self._on_help_toggled)
        
    def _on_help_toggled(self, event_type, event_data):
        """Handle help screen toggle events."""
        # If help is enabled and chat is active, exit chat mode
        show_help = event_data.show_help if hasattr(event_data, 'show_help') else False
        if show_help and self.chat_mode:
            self.chat_mode = False
            self.publish_event(
                EventType.CHAT_TOGGLED,
                EventData(chat_enabled=False)
            )
            
    def toggle_chat_mode(self):
        """Toggle chat input mode."""
        # Can't use chat while help screen is shown
        if self.game_ui.help_component.show_help:
            return
            
        # Toggle chat mode
        self.chat_mode = not self.chat_mode
        
        # Publish chat toggled event
        self.publish_event(
            EventType.CHAT_TOGGLED,
            EventData(chat_enabled=self.chat_mode)
        )
        
        # Clear any existing input when entering chat mode
        if self.chat_mode:
            self.chat_input = ""
            # Display message through event system
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Chat mode: Type message and press Enter to send, Escape to cancel"
                )
            )
        else:
            # Display message through event system
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(message="Chat mode exited")
            )
            
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
    
    def draw_chat_input(self):
        """Draw the chat input field at the bottom of the message log."""
        try:
            # Calculate position for the chat input (below the message log)
            input_y = HEIGHT + 6 + self.game_ui.message_log_component.log_height + 1
            
            # Calculate the current player
            current_player = self.game_ui.multiplayer.get_current_player()
            player_color = self.player_colors.get(current_player, 1)
            
            # Draw the input prompt with player-specific color
            prompt = f"[Player {current_player}]> "
            self.renderer.draw_text(input_y, 0, prompt, player_color)
            
            # Draw the input text with a cursor at the end
            current_input = self.chat_input + "_"  # Add a simple cursor
            self.renderer.draw_text(input_y, len(prompt), current_input, player_color)
        except Exception as e:
            # Never let chat input crash the game
            logger.error(f"Error displaying chat input: {str(e)}")
    
    def handle_chat_input(self, key: int) -> bool:
        """Handle input while in chat mode.
        Returns True to continue running, False to quit.
        """
        # Check for special keys
        if key == 27:  # Escape key - exit chat mode (handled separately from CANCEL action)
            self.chat_mode = False
            self.game_ui.message = "Chat cancelled"
            self.game_ui.draw_board()
            return True
            
        elif key == 10 or key == 13:  # Enter key - send message
            if self.chat_input.strip():  # Only send non-empty messages
                # Get current player
                current_player = self.game_ui.multiplayer.get_current_player()
                
                # Add message to local log first
                message_log.add_player_message(current_player, self.chat_input)
                
                # Send message over network if in multiplayer mode
                if self.game_ui.multiplayer.is_network_multiplayer():
                    from boneglaive.networking.network_interface import MessageType
                    network_interface = self.game_ui.multiplayer.network_interface
                    if network_interface and network_interface.connected:
                        success = network_interface.send_message(MessageType.CHAT, {
                            "player": current_player,
                            "message": self.chat_input
                        })
                        if not success:
                            message_log.add_system_message("Failed to send message over network")
                
                # Clear input and exit chat mode
                self.chat_input = ""
                self.chat_mode = False
                self.game_ui.message = "Message sent"
            else:
                # Empty message, just exit chat mode
                self.chat_mode = False
                self.game_ui.message = "Chat cancelled"
                
            self.game_ui.draw_board()
            return True
            
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
            # Remove last character
            if self.chat_input:
                self.chat_input = self.chat_input[:-1]
                self.game_ui.draw_board()
            return True
            
        elif 32 <= key <= 126:  # Printable ASCII characters
            # Add character to input (limit to reasonable length)
            if len(self.chat_input) < 60:  # Limit message length
                self.chat_input += chr(key)
                self.game_ui.draw_board()
            return True
            
        # Ignore other keys in chat mode
        return True

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
        # Block cursor movement during setup phase when it's not this player's turn
        if self.game_ui.game.setup_phase and self.game_ui.multiplayer.is_network_multiplayer():
            game_state_sync = self.game_ui.multiplayer.game_state_sync
            if game_state_sync and not game_state_sync.can_act_in_setup():
                current_setup_player = self.game_ui.game.setup_player
                self.game_ui.message = f"Player {current_setup_player} is placing units..."
                return
        
        # Block cursor movement during main game when it's not this player's turn
        if not self.game_ui.game.setup_phase and not self.can_act_this_turn():
            current_player = self.game_ui.multiplayer.get_current_player()
            self.game_ui.message = f"Player {current_player} is thinking..."
            return
        
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

        # Allow selection of units for UI purposes even if they have actions queued
        # The action menu will handle preventing additional actions

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

                # Check if terrain is furniture and player has DELPHIC_APPRAISER
                message = f"Tile: {terrain_name}"
                if self.game_ui.game.map.is_furniture(y, x):
                    # Get the current player
                    current_player = self.game_ui.game.current_player

                    # Get cosmic value if visible to current player
                    cosmic_value = self.game_ui.game.map.get_cosmic_value(y, x, player=current_player, game=self.game_ui.game)

                    # If cosmic value is available, add it to the message
                    if cosmic_value is not None:
                        message = f"Tile: {terrain_name} | Cosmic Value: {cosmic_value}"

                # Send message through event system
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=message,
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
            
            # For all games (local and network), apply move locally during planning
            # Network sync happens only during turn execution for fog of war
            
            # Set the move target
            self.selected_unit.move_target = (to_position.y, to_position.x)
            
            # Mark that this unit is taking an action (won't regenerate HP)
            self.selected_unit.took_no_actions = False
            
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
            target_position = (self.cursor_pos.y, self.cursor_pos.x)
            
            # For all games (local and network), apply attack locally during planning
            # Network sync happens only during turn execution for fog of war
            
            self.selected_unit.attack_target = target_position
            
            # Mark that this unit is taking an action (won't regenerate HP)
            self.selected_unit.took_no_actions = False
            
            # Track action order
            self.selected_unit.action_timestamp = self.game_ui.game.action_counter
            self.game_ui.game.action_counter += 1
            
            # Check if the target is a unit or a wall
            from boneglaive.utils.message_log import message_log, MessageType
            target_unit = self.game_ui.game.get_unit_at(self.cursor_pos.y, self.cursor_pos.x)
            
            # Check if target is under KARRIER_RAVE (untargetable)
            if target_unit and hasattr(target_unit, 'carrier_rave_active') and target_unit.carrier_rave_active:
                self.game_ui.message = "Invalid target"
                return False
            
            is_wall_target = False
            wall_owner = None
            
            # Check if it's a wall tile
            if hasattr(self.game_ui.game, 'marrow_dike_tiles') and target_position in self.game_ui.game.marrow_dike_tiles:
                is_wall_target = True
                wall_info = self.game_ui.game.marrow_dike_tiles[target_position]
                wall_owner = wall_info['owner']
            
            # Publish attack planned event
            self.publish_event(
                EventType.ATTACK_PLANNED,
                AttackEventData(
                    attacker=self.selected_unit,
                    target=target_unit  # May be None for wall targets
                )
            )
            
            # Set appropriate message based on target type
            if is_wall_target:
                self.game_ui.message = f"Attack set against Marrow Dike wall"
                # Add message to log for planned wall attacks
                message_log.add_message(
                    f"{self.selected_unit.get_display_name()} readies attack against {wall_owner.get_display_name()}'s Marrow Dike wall",
                    MessageType.COMBAT,
                    player=self.selected_unit.player,
                    attacker_name=self.selected_unit.get_display_name()
                )
            elif target_unit:
                self.game_ui.message = f"Attack set against {target_unit.get_display_name()}"
                # Add message to log for planned unit attacks
                message_log.add_message(
                    f"{self.selected_unit.get_display_name()} readies attack against {target_unit.get_display_name()}",
                    MessageType.COMBAT,
                    player=self.selected_unit.player,
                    attacker_name=self.selected_unit.get_display_name(),
                    target_name=target_unit.get_display_name()
                )
            else:
                # This shouldn't happen, but handle it just in case
                self.game_ui.message = "Attack target set"
                message_log.add_message(
                    f"{self.selected_unit.get_display_name()} readies an attack",
                    MessageType.COMBAT,
                    player=self.selected_unit.player,
                    attacker_name=self.selected_unit.get_display_name()
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

# Game mode manager component
class GameOverPrompt(UIComponent):
    """
    Component responsible for showing a game over prompt when the game ends.
    Allows player to start a new round or exit the game.
    """

    def __init__(self, renderer, game_ui):
        """Initialize the component."""
        super().__init__(renderer, game_ui)
        self.visible = False
        self.selected_option = 0
        self.options = ["Exit Game"]

    def show(self, winner):
        """Show the game over prompt."""
        self.visible = True
        self.selected_option = 0
        self.winner = winner

        # Clear the screen buffer once when showing the prompt
        if hasattr(self.renderer, 'clear_screen'):
            self.renderer.clear_screen()

        # Force a board redraw to show the prompt
        self.game_ui.draw_board()

    def hide(self):
        """Hide the game over prompt."""
        self.visible = False

    def move_selection(self, direction):
        """Move the selection up or down."""
        self.selected_option = (self.selected_option + direction) % len(self.options)
        self.game_ui.draw_board()

    def select_option(self):
        """Select the currently highlighted option."""
        # Only Exit Game option remains
        return False

    def draw(self):
        """Draw the game over prompt."""
        if not self.visible:
            return

        # Get screen dimensions - handle both renderer types
        if hasattr(self.renderer, 'height') and hasattr(self.renderer, 'width'):
            # Curses renderer
            height, width = self.renderer.height, self.renderer.width
        elif hasattr(self.renderer, 'grid_height') and hasattr(self.renderer, 'grid_width'):
            # Pygame renderer
            height, width = self.renderer.grid_height, self.renderer.grid_width
        else:
            # Fallback - get from get_size method
            height, width = self.renderer.get_size()

        # Screen is cleared once in show() method - no need to clear on every draw

        # Import game board constants
        from boneglaive.utils.constants import HEIGHT as BOARD_HEIGHT

        # Calculate prompt dimensions and position
        prompt_width = 40
        prompt_height = 8
        prompt_x = (width - prompt_width) // 2

        # Position the prompt in the middle of the game board area, not the entire screen
        # This ensures it's not cut off by bottom UI elements
        prompt_y = BOARD_HEIGHT // 2 - prompt_height // 2

        # Make sure the prompt doesn't go off the top of the screen
        prompt_y = max(prompt_y, 1)

        # Draw border and background - use simple ASCII characters for compatibility
        for y in range(prompt_y, prompt_y + prompt_height):
            for x in range(prompt_x, prompt_x + prompt_width):
                if (y == prompt_y or y == prompt_y + prompt_height - 1 or
                    x == prompt_x or x == prompt_x + prompt_width - 1):
                    self.renderer.draw_text(y, x, "#", 7)  # Border with white color
                else:
                    self.renderer.draw_text(y, x, " ", 7)  # Background with white color

        # Draw title
        title = f"Player {self.winner} Wins!"
        title_x = prompt_x + (prompt_width - len(title)) // 2
        # Use bright white color with bold attribute
        self.renderer.draw_text(prompt_y + 1, title_x, title, 7, 1)

        # Draw options
        for i, option in enumerate(self.options):
            option_x = prompt_x + (prompt_width - len(option)) // 2
            color = 3 if i == self.selected_option else 7  # Yellow for selected, white for normal
            attr = 1 if i == self.selected_option else 0  # Bold for selected option
            self.renderer.draw_text(prompt_y + 3 + i, option_x, option, color, attr)

        # Draw controls
        controls = "UP/DOWN: Navigate | ENTER: Select"
        controls_x = prompt_x + (prompt_width - len(controls)) // 2
        self.renderer.draw_text(prompt_y + 6, controls_x, controls, 7)
        
        # Refresh the display to make sure the prompt is visible
        self.renderer.refresh()


class ConcedePrompt(UIComponent):
    """
    Component for showing a concede confirmation dialog when 'q' is pressed.
    Allows player to concede (lose game), resume, or go to main menu.
    """

    def __init__(self, renderer, game_ui):
        """Initialize the component."""
        super().__init__(renderer, game_ui)
        self.visible = False
        self.selected_option = 0
        self.options = ["Resume Game", "Concede"]

    def show(self):
        """Show the concede prompt."""
        self.visible = True
        self.selected_option = 0

        # Force a board redraw to show the prompt
        self.game_ui.draw_board()

    def hide(self):
        """Hide the concede prompt."""
        self.visible = False

    def move_selection(self, direction):
        """Move the selection up or down."""
        self.selected_option = (self.selected_option + direction) % len(self.options)
        self.game_ui.draw_board()

    def select_option(self):
        """Select the currently highlighted option."""
        if self.selected_option == 0:  # Resume Game
            # Just hide and continue playing
            self.hide()
            return True
        else:  # Exit Game
            # Return False to exit
            return False

    def draw(self):
        """Draw the concede prompt."""
        if not self.visible:
            return

        # Get screen dimensions - handle both renderer types
        if hasattr(self.renderer, 'height') and hasattr(self.renderer, 'width'):
            # Curses renderer
            height, width = self.renderer.height, self.renderer.width
        elif hasattr(self.renderer, 'grid_height') and hasattr(self.renderer, 'grid_width'):
            # Pygame renderer
            height, width = self.renderer.grid_height, self.renderer.grid_width
        else:
            # Fallback - get from get_size method
            height, width = self.renderer.get_size()

        # Screen should be cleared when prompt is shown, not on every draw

        # Import game board constants
        from boneglaive.utils.constants import HEIGHT as BOARD_HEIGHT

        # Calculate prompt dimensions and position
        prompt_width = 45
        prompt_height = 10
        prompt_x = (width - prompt_width) // 2

        # Position the prompt in the middle of the game board area
        prompt_y = BOARD_HEIGHT // 2 - prompt_height // 2

        # Make sure the prompt doesn't go off the top of the screen
        prompt_y = max(prompt_y, 1)

        # Draw border and background - use simple ASCII characters for compatibility
        for y in range(prompt_y, prompt_y + prompt_height):
            for x in range(prompt_x, prompt_x + prompt_width):
                if (y == prompt_y or y == prompt_y + prompt_height - 1 or
                    x == prompt_x or x == prompt_x + prompt_width - 1):
                    self.renderer.draw_text(y, x, "#", 7)  # Border with white color
                else:
                    self.renderer.draw_text(y, x, " ", 7)  # Background with white color

        # Draw title
        title = "Confirm Action"
        title_x = prompt_x + (prompt_width - len(title)) // 2
        # Use bright white color with bold attribute
        self.renderer.draw_text(prompt_y + 1, title_x, title, 7, 1)

        # Draw description
        desc1 = "Are you sure you want to quit?"
        desc2 = "Select 'Concede' to lose the current game."
        desc1_x = prompt_x + (prompt_width - len(desc1)) // 2
        desc2_x = prompt_x + (prompt_width - len(desc2)) // 2
        self.renderer.draw_text(prompt_y + 3, desc1_x, desc1, 7)
        self.renderer.draw_text(prompt_y + 4, desc2_x, desc2, 7)

        # Draw options
        for i, option in enumerate(self.options):
            option_y = prompt_y + 6 + i
            option_x = prompt_x + (prompt_width - len(option)) // 2

            if i == self.selected_option:
                # Highlight selected option
                self.renderer.draw_text(option_y, option_x - 2, ">", 7)
                self.renderer.draw_text(option_y, option_x, option, 7, 1)  # Bold
                self.renderer.draw_text(option_y, option_x + len(option), "<", 7)
            else:
                self.renderer.draw_text(option_y, option_x, option, 7)

        # Refresh the screen
        self.renderer.refresh()


class GameModeManager(UIComponent):
    """Component for managing game modes and turn handling."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.mode = "select"  # select, move, attack, setup, target_vapor, teleport
        self.show_setup_instructions = False  # Don't show setup instructions by default
        self.setup_unit_type = UnitType.GLAIVEMAN  # Default unit type for setup phase
        self.targeting_vapor = False  # Flag for Diverge skill targeting mode
        self.teleport_anchor = None  # Active teleport anchor
    
    def _setup_event_handlers(self):
        """Set up event handlers for game mode manager."""
        # Subscribe to unit selection events to update UI as needed
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
    
    def _on_unit_selected(self, event_type, event_data):
        """Handle unit selection events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_unit_deselected(self, event_type, event_data):
        """Handle unit deselection events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
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
            # Reset selected skill if it was being used
            if self.mode == "skill" and cursor_manager.selected_unit.selected_skill:
                cursor_manager.selected_unit.selected_skill = None
                cursor_manager.selected_unit.skill_target = None
            # Change to select mode (will publish mode changed event)
            self.set_mode("select")
            self.game_ui.message = f"{self.mode.capitalize()} mode cancelled, unit still selected"
            self.game_ui.draw_board()
            return
            
        # If in skill_select mode, return to normal menu
        if self.mode == "skill_select" and cursor_manager.selected_unit:
            # Reset any partially selected skill
            if cursor_manager.selected_unit.selected_skill:
                cursor_manager.selected_unit.selected_skill = None
                cursor_manager.selected_unit.skill_target = None
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
    
    def _setup_event_handlers(self):
        """Set up event handlers for game mode manager."""
        # Subscribe to unit selection events to update UI as needed
        self.subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self.subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
        
        # Subscribe to mode request events
        self.subscribe_to_event(EventType.MOVE_MODE_REQUESTED, self._on_move_mode_requested)
        self.subscribe_to_event(EventType.ATTACK_MODE_REQUESTED, self._on_attack_mode_requested)
        self.subscribe_to_event(EventType.SKILL_MODE_REQUESTED, self._on_skill_mode_requested)
        self.subscribe_to_event(EventType.TELEPORT_MODE_REQUESTED, self._on_teleport_mode_requested)
        self.subscribe_to_event(EventType.SELECT_MODE_REQUESTED, self._on_select_mode_requested)
        self.subscribe_to_event(EventType.CANCEL_REQUESTED, self._on_cancel_requested)
        
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

    def _on_teleport_mode_requested(self, event_type, event_data):
        """Handle teleport mode request events."""
        # Delegate to handle_teleport_mode
        self.handle_teleport_mode()

    def _on_select_mode_requested(self, event_type, event_data):
        """Handle select mode request events."""
        # Simply change to select mode
        self.set_mode("select")
        
    def _on_cancel_requested(self, event_type, event_data):
        """Handle cancel request events."""
        # Delegate to handle_cancel which already has the logic
        self.handle_cancel()
        
    def handle_move_mode(self):
        """Enter move mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn",
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
                
                # Check if unit is affected by Jawline
                if hasattr(cursor_manager.selected_unit, 'jawline_affected') and cursor_manager.selected_unit.jawline_affected:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit is immobilized by Jawline and cannot move",
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
                    # Skip showing "No valid moves available" message
                    pass
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only move your own units",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            # Show message in UI only, not in message log
            self.game_ui.message = "No unit selected"
    
    def handle_skill_mode(self):
        """Enter skill mode to select from available skills."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn",
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
                # Only show the warning message for human players, not AI
                # Check if the current player is a human player
                if self.game_ui.multiplayer.get_current_player() == 1:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="You can only use skills with your own units",
                            message_type=MessageType.WARNING,
                            log_message=False  # Don't add to message log, only show in UI
                        )
                    )
        else:
            # Use event system for message
            # Show message in UI only, not in message log
            self.game_ui.message = "No unit selected"
            
    def handle_attack_mode(self):
        """Enter attack mode."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn",
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
                
                # Change mode (will publish mode changed event)
                self.set_mode("attack")
                
                # If we selected a unit directly, use its position
                # If we selected a ghost, always use the ghost position
                from_pos = None
                if cursor_manager.selected_unit.move_target:
                    from_pos = cursor_manager.selected_unit.move_target
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select attack from planned move position"
                        )
                    )
                else:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select attack target"
                        )
                    )
                
                # Convert positions to Position objects, using move destination if set
                cursor_manager.highlighted_positions = [
                    Position(y, x) for y, x in self.game_ui.game.get_possible_attacks(
                        cursor_manager.selected_unit, from_pos)
                ]
                
                if not cursor_manager.highlighted_positions:
                    # No message when there are no valid targets
                    pass
            else:
                # Only show the warning message for human players, not AI
                if self.game_ui.multiplayer.get_current_player() == 1:
                    # Use event system for message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="You can only attack with your own units",
                            message_type=MessageType.WARNING
                        )
                    )
        else:
            # Use event system for message
            # Show message in UI only, not in message log
            self.game_ui.message = "No unit selected"
    
    def handle_select_in_select_mode(self):
        """Handle selection when in select mode."""
        return self.game_ui.cursor_manager.select_unit_at_cursor()
    
    def handle_select_in_move_mode(self):
        """Handle selection when in move mode."""
        result = self.game_ui.cursor_manager.select_move_target()
        if result:
            # Return to select mode after successful move (publishes mode changed event)
            self.set_mode("select")
        return result

    def handle_teleport_mode(self):
        """Enter teleport mode to activate Market Futures teleportation anchors."""
        cursor_manager = self.game_ui.cursor_manager
        game = self.game_ui.game

        # Check if player can act this turn
        if not cursor_manager.can_act_this_turn():
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Not your turn",
                    message_type=MessageType.WARNING
                )
            )
            return

        if cursor_manager.selected_unit:
            # Check if unit belongs to current player or test mode is on
            if cursor_manager.can_select_unit(cursor_manager.selected_unit):
                # Check if unit has Parallax status (can_use_anchor)
                if not (hasattr(cursor_manager.selected_unit, 'can_use_anchor') and 
                        cursor_manager.selected_unit.can_use_anchor):
                    return
                    
                # Cannot use teleport if the unit has already planned an attack or used a skill
                if cursor_manager.selected_unit.attack_target or cursor_manager.selected_unit.skill_target:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Unit has already planned an action and cannot teleport",
                            message_type=MessageType.WARNING
                        )
                    )
                    return

                # Check if there are any teleport anchors
                if not hasattr(game, 'teleport_anchors') or len(game.teleport_anchors) == 0:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No teleport anchors available",
                            message_type=MessageType.WARNING
                        )
                    )
                    return

                # Find active teleport anchors that are adjacent to the unit
                active_anchors = []
                unit = cursor_manager.selected_unit

                for pos, anchor in game.teleport_anchors.items():
                    if anchor['active']:
                        # Check if the anchor is adjacent to the unit
                        distance = game.chess_distance(unit.y, unit.x, pos[0], pos[1])
                        if distance <= 1:  # Adjacent (including diagonals)
                            active_anchors.append(pos)

                if not active_anchors:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="No adjacent teleport anchors available. Move next to a teleport anchor to use it.",
                            message_type=MessageType.WARNING
                        )
                    )
                    return

                # Highlight teleport anchors
                cursor_manager.highlighted_positions = [Position(y, x) for y, x in active_anchors]

                # Set teleport mode
                self.set_mode("teleport")
                self.teleport_anchor = None

                # Show user instruction in UI
                self.game_ui.message = "Select a teleport anchor"
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="You can only teleport with your own units",
                        message_type=MessageType.WARNING
                    )
                )
        else:
            # Use event system for message
            # Show message in UI only, not in message log
            self.game_ui.message = "No unit selected"
    
    def handle_select_in_attack_mode(self):
        """Handle selection when in attack mode."""
        result = self.game_ui.cursor_manager.select_attack_target()
        if result:
            # Return to select mode after successful attack (publishes mode changed event)
            self.set_mode("select")
        return result
        
    def handle_select_in_skill_mode(self):
        """Handle selection when in skill mode."""
        result = self.select_skill_target()
        if result:
            # Return to select mode after successful skill use (publishes mode changed event)
            self.set_mode("select")
            # Don't clear selection - allow players to continue selecting units normally
        return result
        
    def handle_select_in_vapor_targeting_mode(self):
        """Handle selection when targeting with the Diverge skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.constants import UnitType

        cursor_manager = self.game_ui.cursor_manager
        game = self.game_ui.game
        pos = cursor_manager.cursor_pos

        # Check if there's a unit selected with Diverge skill
        if not cursor_manager.selected_unit or not cursor_manager.selected_unit.selected_skill:
            # Return to select mode
            self.set_mode("select")
            self.targeting_vapor = False
            return False

        # Get the selected skill
        skill = cursor_manager.selected_unit.selected_skill
        if skill.name != "Diverge":
            # Return to select mode if not Diverge skill
            self.set_mode("select")
            self.targeting_vapor = False
            return False

        # Check what's at the cursor position
        unit_at_cursor = game.get_unit_at(pos.y, pos.x)

        # Check if this is the current position or the planned move position (ghost)
        # If a move order is issued, only the ghost position is a valid target, not the current position
        if cursor_manager.selected_unit.move_target:
            # If there's a move target, only the ghost position is valid for self-targeting
            is_self_target = (pos.y == cursor_manager.selected_unit.move_target[0] and
                             pos.x == cursor_manager.selected_unit.move_target[1])
        else:
            # If no move target, the current position is valid
            is_self_target = (unit_at_cursor and unit_at_cursor == cursor_manager.selected_unit)

        is_valid_vapor = (unit_at_cursor and unit_at_cursor.type == UnitType.HEINOUS_VAPOR and
                         unit_at_cursor.player == cursor_manager.selected_unit.player)

        # Handle targeting self
        if is_self_target:
            # Use the skill on self
            if skill.can_use(cursor_manager.selected_unit, (pos.y, pos.x), game):
                skill.use(cursor_manager.selected_unit, (pos.y, pos.x), game)
                # Return to select mode
                self.set_mode("select")
                self.targeting_vapor = False
                # Clear the unit selection to prevent multiple actions
                self.game_ui.cursor_manager.clear_selection()
                return True
            else:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Cannot use {skill.name} on self here",
                        message_type=MessageType.WARNING
                    )
                )
                return False
        # Handle targeting a vapor
        elif is_valid_vapor:
            # Use the skill on the vapor
            if skill.can_use(cursor_manager.selected_unit, (pos.y, pos.x), game):
                skill.use(cursor_manager.selected_unit, (pos.y, pos.x), game)
                # Return to select mode
                self.set_mode("select")
                self.targeting_vapor = False
                # Clear the unit selection to prevent multiple actions
                self.game_ui.cursor_manager.clear_selection()
                return True
            else:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Cannot use {skill.name} on this vapor",
                        message_type=MessageType.WARNING
                    )
                )
                return False
        else:
            # Invalid target
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Select yourself or a HEINOUS VAPOR to use Diverge",
                    message_type=MessageType.WARNING
                )
            )
            return False

    def handle_select_in_teleport_mode(self):
        """Handle selection when in teleport mode."""
        from boneglaive.utils.message_log import message_log, MessageType

        cursor_manager = self.game_ui.cursor_manager
        game = self.game_ui.game
        pos = cursor_manager.cursor_pos

        # Get the selected unit
        unit = cursor_manager.selected_unit
        if not unit:
            self.set_mode("select")
            return False

        # Check if there's a teleport anchor at the cursor position
        if not hasattr(game, 'teleport_anchors'):
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="No teleport anchors available",
                    message_type=MessageType.WARNING
                )
            )
            self.set_mode("select")
            return False

        # If we're selecting an anchor
        if self.teleport_anchor is None:
            # Check if there's a teleport anchor at the cursor position
            cursor_pos_tuple = (pos.y, pos.x)
            if cursor_pos_tuple not in game.teleport_anchors or not game.teleport_anchors[cursor_pos_tuple]['active']:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="No teleport anchor at this location",
                        message_type=MessageType.WARNING
                    )
                )
                return False

            # Store the selected anchor
            self.teleport_anchor = cursor_pos_tuple

            # Update highlighted positions to show valid teleport destinations
            cursor_manager.highlighted_positions = []
            cosmic_value = game.teleport_anchors[cursor_pos_tuple]['cosmic_value']

            # Highlight all positions within the cosmic value range
            for y in range(max(0, pos.y - cosmic_value), min(game.map.height, pos.y + cosmic_value + 1)):
                for x in range(max(0, pos.x - cosmic_value), min(game.map.width, pos.x + cosmic_value + 1)):
                    # Check if position is valid and within range
                    if game.chess_distance(pos.y, pos.x, y, x) <= cosmic_value:
                        # Check if position is passable and empty
                        if game.map.is_passable(y, x) and not game.get_unit_at(y, x):
                            cursor_manager.highlighted_positions.append(Position(y, x))

            # Show instruction in UI
            self.game_ui.message = f"Select teleport destination (range {cosmic_value})"

            return True

        else:
            # We already have an anchor selected, now selecting the destination
            anchor_pos = self.teleport_anchor
            destination_pos = (pos.y, pos.x)

            # Check if the destination is valid (in highlighted positions)
            if cursor_manager.cursor_pos not in cursor_manager.highlighted_positions:
                # Show error in UI instead of message log
                self.game_ui.message = "Invalid teleport destination"
                return False

            # Get the Market Futures skill from the anchor's creator
            if not game.teleport_anchors[anchor_pos]['creator']:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Teleport anchor creator not found",
                        message_type=MessageType.WARNING
                    )
                )
                self.teleport_anchor = None
                self.set_mode("select")
                return False

            creator = game.teleport_anchors[anchor_pos]['creator']
            market_futures_skill = None

            # Find the Market Futures skill on the creator's active skills
            if hasattr(creator, 'active_skills'):
                for skill in creator.active_skills:
                    if hasattr(skill, 'name') and skill.name == "Market Futures":
                        market_futures_skill = skill
                        break

            if not market_futures_skill:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Market Futures skill not found",
                        message_type=MessageType.WARNING
                    )
                )
                self.teleport_anchor = None
                self.set_mode("select")
                return False

            # Activate the teleport
            if market_futures_skill.activate_teleport(unit, anchor_pos, destination_pos, game, self.game_ui):
                # Teleport successful
                message_log.add_message(
                    f"{unit.get_display_name()} teleports via Market Futures to ({destination_pos[0]}, {destination_pos[1]})",
                    MessageType.ABILITY,
                    player=unit.player
                )

                # Clear teleport state and return to select mode
                self.teleport_anchor = None
                cursor_manager.highlighted_positions = []
                self.set_mode("select")

                # Clear selection
                cursor_manager.clear_selection()

                return True
            else:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Failed to activate teleport",
                        message_type=MessageType.WARNING
                    )
                )
                return False
        
    def select_skill_target(self):
        """Select a target for the currently selected skill."""
        cursor_manager = self.game_ui.cursor_manager

        # Get the selected unit and skill
        unit = cursor_manager.selected_unit
        if not unit or not unit.selected_skill:
            return False

        skill = unit.selected_skill

        # Special handling for Auction Curse with awaiting_ally_target flag
        if skill.name == "Auction Curse" and hasattr(unit, 'awaiting_ally_target') and unit.awaiting_ally_target:
            # In this case, we're selecting an ally to receive the tokens
            target_pos = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
            target = self.game_ui.game.get_unit_at(target_pos[0], target_pos[1])

            # Check if the target is a valid ally
            if not target or target.player != unit.player:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Select an ally to receive the tokens",
                        message_type=MessageType.WARNING
                    )
                )
                return False

            # Check if ally is within range 3
            distance = self.game_ui.game.chess_distance(unit.y, unit.x, target_pos[0], target_pos[1])
            if distance > 3:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Ally must be within range 3",
                        message_type=MessageType.WARNING
                    )
                )
                return False

            # Set the ally target via the set_ally_target method
            if skill.set_ally_target(unit, target_pos, self.game_ui.game):
                # Mark that this unit is taking an action (won't regenerate HP)
                unit.took_no_actions = False
                # Targets set successfully
                cursor_manager.highlighted_positions = []
                return True
            else:
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Failed to set ally target",
                        message_type=MessageType.WARNING
                    )
                )
                return False

        # Check if target is in highlighted positions - if not, may be due to protection
        target_pos = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)
        if cursor_manager.cursor_pos not in cursor_manager.highlighted_positions:
            # Check if there's an enemy unit at this position and within range
            target = self.game_ui.game.get_unit_at(target_pos[0], target_pos[1])
            if target and target.player != unit.player:
                # Check if target is under CARRIER_RAVE (untargetable)
                if hasattr(target, 'carrier_rave_active') and target.carrier_rave_active:
                    self.game_ui.message = "Invalid target"
                    return False
                # Get the skill origination position (current or planned move)
                from_y, from_x = unit.y, unit.x
                if unit.move_target:
                    from_y, from_x = unit.move_target

                # Check if the target is in range and protected
                if (self.game_ui.game.chess_distance(from_y, from_x, target_pos[0], target_pos[1]) <= skill.range and
                    hasattr(self.game_ui.game, 'is_protected_from') and
                    self.game_ui.game.is_protected_from(target, unit)):
                    # Show "Invalid target" message like with attacks
                    self.game_ui.message = "Invalid skill target"
            return False

        # Special handling for Marrow Dike and Slough
        # These are self-targeted area skills that were pre-confirmed in _select_skill
        if skill.name in ["Marrow Dike", "Slough"] and unit.skill_target:
            # Use the skill with the pre-set target
            if skill.use(unit, unit.skill_target, self.game_ui.game):
                # Mark that this unit is taking an action (won't regenerate HP)
                unit.took_no_actions = False
                # Clear selection
                cursor_manager.highlighted_positions = []

                # Skill used successfully
                return True
            else:
                # Use event system for message
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message=f"Failed to use {skill.name}",
                        message_type=MessageType.WARNING
                    )
                )
                return False

        # For normal skills, get the target position from cursor
        target_pos = (cursor_manager.cursor_pos.y, cursor_manager.cursor_pos.x)

        # Check if the target position is valid for this skill
        if cursor_manager.cursor_pos not in cursor_manager.highlighted_positions:
            # Simply return false without showing a message
            return False

        # Check if target is under KARRIER_RAVE (untargetable)
        target = self.game_ui.game.get_unit_at(target_pos[0], target_pos[1])
        if target and hasattr(target, 'carrier_rave_active') and target.carrier_rave_active:
            self.game_ui.message = "Invalid target"
            return False

        # Use the skill
        if skill.use(unit, target_pos, self.game_ui.game):
            # Mark that this unit is taking an action (won't regenerate HP)
            unit.took_no_actions = False
            # For Auction Curse, if we now need to select an ally, don't clear the selection
            if skill.name == "Auction Curse" and hasattr(unit, 'awaiting_ally_target') and unit.awaiting_ally_target:
                # Update highlighted positions to show valid allies (all allies within range 3)
                cursor_manager.highlighted_positions = []
                for ally_unit in self.game_ui.game.units:
                    if ally_unit.is_alive() and ally_unit.player == unit.player:
                        distance = self.game_ui.game.chess_distance(unit.y, unit.x, ally_unit.y, ally_unit.x)
                        if distance <= 3:
                            cursor_manager.highlighted_positions.append(Position(ally_unit.y, ally_unit.x))

                # Don't return True yet - we'll return to skill mode for ally selection
                self.publish_event(
                    EventType.MESSAGE_DISPLAY_REQUESTED,
                    MessageDisplayEventData(
                        message="Now select an ally to receive the tokens",
                        message_type=MessageType.SYSTEM
                    )
                )
                return False
            else:
                # Clear selection for all other skills
                cursor_manager.highlighted_positions = []
                # Skill used successfully
                return True
        else:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Failed to use skill",
                    message_type=MessageType.WARNING
                )
            )
            return False
    
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
        
        # Route turn execution through multiplayer manager for network sync
        if self.game_ui.multiplayer.is_network_multiplayer():
            # Collect all planned actions for this player before ending turn
            planned_actions = self._collect_planned_actions()
            
            # For networked games, send end_turn action through GameStateSync with planned actions
            self.game_ui.multiplayer.send_player_action("end_turn", {
                "ui": id(self.game_ui),  # Send UI reference ID for animations
                "planned_actions": planned_actions  # Include all planned actions for fog of war
            })
        else:
            # For local games, execute turn directly with animations
            self.game_ui.game.execute_turn(self.game_ui)
        
        # Clear selection after executing turn
        cursor_manager.clear_selection()
        # Return to select mode
        self.set_mode("select")
        
        # Handle multiplayer turn switching
        if not self.game_ui.game.winner:
            # End turn in multiplayer manager
            self.game_ui.multiplayer.end_turn()
            self.game_ui.update_player_message()
            
            # Publish turn started event for the new player
            self.publish_event(
                EventType.TURN_STARTED,
                TurnEventData(
                    player=self.game_ui.multiplayer.get_current_player(),
                    turn_number=self.game_ui.game.turn
                )
            )
        else:
            # Publish game over event
            self.publish_event(
                EventType.GAME_OVER,
                GameOverEventData(winner=self.game_ui.game.winner)
            )
            
        # Redraw the board to update visuals
        self.game_ui.draw_board()
    
    def _collect_planned_actions(self):
        """Collect all planned actions for the current player for network sync."""
        current_player = self.game_ui.multiplayer.get_current_player()
        network_player = self.game_ui.multiplayer.network_interface.get_player_number()
        
        # Only collect actions if it's actually your turn
        if current_player != network_player:
            return []
        
        planned_actions = []
        
        # Collect all units with planned actions for this player
        for unit in self.game_ui.game.units:
            if unit.is_alive() and unit.player == network_player:
                unit_actions = {}
                
                # Check for move target
                if hasattr(unit, 'move_target') and unit.move_target is not None:
                    unit_actions['move'] = {
                        "unit_id": id(unit),
                        "target": unit.move_target
                    }
                
                # Check for attack target
                if hasattr(unit, 'attack_target') and unit.attack_target is not None:
                    unit_actions['attack'] = {
                        "unit_id": id(unit), 
                        "target": unit.attack_target
                    }
                
                # Include other action metadata
                if unit_actions:
                    unit_actions['metadata'] = {
                        "took_no_actions": getattr(unit, 'took_no_actions', True),
                        "action_timestamp": getattr(unit, 'action_timestamp', 0)
                    }
                    planned_actions.append(unit_actions)
        
        return planned_actions
    
    def handle_test_mode(self):
        """
        Toggle test mode or toggle unit type during setup phase.
        The 't' key serves dual purpose - in setup phase it toggles unit type,
        during gameplay it toggles test mode.
        """
        # In setup phase, use the 't' key to toggle unit type instead of test mode
        # but only if we haven't enabled the actual test mode yet
        if self.game_ui.game.setup_phase and not self.game_ui.game.test_mode:
            self.toggle_setup_unit_type()
            return
            
        # Continue with normal test mode functionality
        self.game_ui.game.toggle_test_mode()
        if self.game_ui.game.test_mode:
            # If in setup phase, skip it and use test units
            if self.game_ui.game.setup_phase:
                self.game_ui.game.setup_phase = False
                self.game_ui.game.setup_initial_units()
                self.game_ui.message = "Test mode ON - setup phase skipped, using test units"
                
                # Add welcome messages when skipping setup phase
                # Use UI message only for test mode notifications
                self.game_ui.message = f"Test mode enabled, using predefined units on {self.game_ui.game.map.name}"
            else:
                self.game_ui.message = "Test mode ON - both players can control all units"
                # Display via UI message only
        else:
            self.game_ui.message = "Test mode OFF"
            # Display via UI message only
    
    def toggle_setup_unit_type(self):
        """
        Toggle between unit types during the setup phase.
        Cycles between GLAIVEMAN, MANDIBLE FOREMAN, GRAYMAN, MARROW_CONDENSER,
        FOWL_CONTRIVANCE, GAS_MACHINIST, DELPHIC_APPRAISER, and INTERFERER.
        """
        if self.setup_unit_type == UnitType.GLAIVEMAN:
            self.setup_unit_type = UnitType.MANDIBLE_FOREMAN
            self.game_ui.message = "Setup unit type: MANDIBLE FOREMAN"
        elif self.setup_unit_type == UnitType.MANDIBLE_FOREMAN:
            self.setup_unit_type = UnitType.GRAYMAN
            self.game_ui.message = "Setup unit type: GRAYMAN"
        elif self.setup_unit_type == UnitType.GRAYMAN:
            self.setup_unit_type = UnitType.MARROW_CONDENSER
            self.game_ui.message = "Setup unit type: MARROW CONDENSER"
        elif self.setup_unit_type == UnitType.MARROW_CONDENSER:
            self.setup_unit_type = UnitType.FOWL_CONTRIVANCE
            self.game_ui.message = "Setup unit type: FOWL CONTRIVANCE"
        elif self.setup_unit_type == UnitType.FOWL_CONTRIVANCE:
            self.setup_unit_type = UnitType.GAS_MACHINIST
            self.game_ui.message = "Setup unit type: GAS MACHINIST"
        elif self.setup_unit_type == UnitType.GAS_MACHINIST:
            self.setup_unit_type = UnitType.DELPHIC_APPRAISER
            self.game_ui.message = "Setup unit type: DELPHIC APPRAISER"
        elif self.setup_unit_type == UnitType.DELPHIC_APPRAISER:
            self.setup_unit_type = UnitType.INTERFERER
            self.game_ui.message = "Setup unit type: INTERFERER"
        else:
            self.setup_unit_type = UnitType.GLAIVEMAN
            self.game_ui.message = "Setup unit type: GLAIVEMAN"
        
        # Sync the unit selection menu with the new unit type
        self.game_ui.unit_selection_menu.set_selected_unit_type(self.setup_unit_type)
        
        # Redraw the board to show the message
        self.game_ui.draw_board()
    
    def navigate_setup_unit_next(self):
        """Navigate to the next unit type in the setup menu (TAB)."""
        if not self.game_ui.game.setup_phase:
            return
        
        # Block unit cycling during setup phase when it's not this player's turn
        if self.game_ui.multiplayer.is_network_multiplayer():
            game_state_sync = self.game_ui.multiplayer.game_state_sync
            if game_state_sync and not game_state_sync.can_act_in_setup():
                current_setup_player = self.game_ui.game.setup_player
                self.game_ui.message = f"Player {current_setup_player} is placing units..."
                return
            
        # Get current index in unit types list
        unit_types = [
            UnitType.GLAIVEMAN, UnitType.MANDIBLE_FOREMAN, UnitType.GRAYMAN,
            UnitType.MARROW_CONDENSER, UnitType.FOWL_CONTRIVANCE, UnitType.GAS_MACHINIST,
            UnitType.DELPHIC_APPRAISER, UnitType.INTERFERER
        ]
        
        try:
            current_index = unit_types.index(self.setup_unit_type)
            # Move to next unit type, wrapping around to beginning
            next_index = (current_index + 1) % len(unit_types)
            self.setup_unit_type = unit_types[next_index]
        except ValueError:
            # Fallback if current type not found
            self.setup_unit_type = UnitType.GLAIVEMAN
        
        # Update message and sync menu
        unit_name = self.setup_unit_type.name.replace('_', ' ')
        self.game_ui.message = f"Setup unit type: {unit_name}"
        self.game_ui.unit_selection_menu.set_selected_unit_type(self.setup_unit_type)
        self.game_ui.draw_board()
    
    def navigate_setup_unit_prev(self):
        """Navigate to the previous unit type in the setup menu (SHIFT+TAB)."""
        if not self.game_ui.game.setup_phase:
            return
        
        # Block unit cycling during setup phase when it's not this player's turn
        if self.game_ui.multiplayer.is_network_multiplayer():
            game_state_sync = self.game_ui.multiplayer.game_state_sync
            if game_state_sync and not game_state_sync.can_act_in_setup():
                current_setup_player = self.game_ui.game.setup_player
                self.game_ui.message = f"Player {current_setup_player} is placing units..."
                return
            
        # Get current index in unit types list
        unit_types = [
            UnitType.GLAIVEMAN, UnitType.MANDIBLE_FOREMAN, UnitType.GRAYMAN,
            UnitType.MARROW_CONDENSER, UnitType.FOWL_CONTRIVANCE, UnitType.GAS_MACHINIST,
            UnitType.DELPHIC_APPRAISER, UnitType.INTERFERER
        ]
        
        try:
            current_index = unit_types.index(self.setup_unit_type)
            # Move to previous unit type, wrapping around to end
            prev_index = (current_index - 1) % len(unit_types)
            self.setup_unit_type = unit_types[prev_index]
        except ValueError:
            # Fallback if current type not found
            self.setup_unit_type = UnitType.GLAIVEMAN
        
        # Update message and sync menu
        unit_name = self.setup_unit_type.name.replace('_', ' ')
        self.game_ui.message = f"Setup unit type: {unit_name}"
        self.game_ui.unit_selection_menu.set_selected_unit_type(self.setup_unit_type)
        self.game_ui.draw_board()
        
    def handle_setup_select(self):
        """Handle unit placement during setup phase."""
        # Check if this player can act during setup in network games
        if self.game_ui.multiplayer.is_network_multiplayer():
            game_state_sync = self.game_ui.multiplayer.game_state_sync
            if game_state_sync and not game_state_sync.can_act_in_setup():
                current_setup_player = self.game_ui.game.setup_player
                self.game_ui.message = f"Player {current_setup_player} is placing units..."
                return
        
        # Get the current setup player
        setup_player = self.game_ui.game.setup_player
        cursor_pos = self.game_ui.cursor_manager.cursor_pos

        # Check if cursor position is in bounds
        if not self.game_ui.game.is_valid_position(cursor_pos.y, cursor_pos.x):
            self.game_ui.message = f"Cannot place unit here: out of bounds"
            return

        # Check if cursor position has blocking terrain
        if not self.game_ui.game.map.can_place_unit(cursor_pos.y, cursor_pos.x):
            self.game_ui.message = f"Cannot place unit here: blocked by terrain"
            return

        # Check if there are units remaining to place
        if self.game_ui.game.setup_units_remaining[setup_player] <= 0:
            self.game_ui.message = f"All units placed. Press 'y' to confirm."
            return

        # For network games, route through GameStateSync
        if self.game_ui.multiplayer.is_network_multiplayer() and self.game_ui.multiplayer.game_state_sync:
            # Send setup action through network
            self.game_ui.multiplayer.game_state_sync.send_setup_action("place_unit", {
                "y": cursor_pos.y,
                "x": cursor_pos.x,
                "unit_type": self.setup_unit_type.name
            })
            return
        
        # For local games, place unit directly
        result = self.game_ui.game.place_setup_unit(cursor_pos.y, cursor_pos.x, self.setup_unit_type)

        # Map for unit type names with proper spacing/display
        unit_type_name = {
            UnitType.GLAIVEMAN: "GLAIVEMAN",
            UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
            UnitType.GRAYMAN: "GRAYMAN",
            UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
            UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
            UnitType.GAS_MACHINIST: "GAS MACHINIST",
            UnitType.DELPHIC_APPRAISER: "DELPHIC APPRAISER",
            UnitType.INTERFERER: "INTERFERER"
        }.get(self.setup_unit_type, "UNKNOWN")

        # Check specific error cases based on return value
        if result == "max_unit_type_limit":
            self.game_ui.message = f"Cannot place more than 2 {unit_type_name} units"
        elif result == "position_occupied":
            self.game_ui.message = "Cannot place unit here - position occupied"
        elif result is True:
            # Unit was placed successfully
            self.game_ui.message = f"{unit_type_name} placed. {self.game_ui.game.setup_units_remaining[setup_player]} remaining."
        elif result is False:
            self.game_ui.message = "Cannot place unit here - invalid position"
        else:
            self.game_ui.message = "Cannot place unit - please try a different position"

        # Redraw the board
        self.game_ui.draw_board()
    
    def handle_confirm(self):
        """Handle confirmation action (mainly for setup phase)."""
        if not self.game_ui.game.setup_phase:
            return  # Ignore outside of setup
        
        # Check if this player can act during setup in network games
        if self.game_ui.multiplayer.is_network_multiplayer():
            game_state_sync = self.game_ui.multiplayer.game_state_sync
            if game_state_sync and not game_state_sync.can_act_in_setup():
                current_setup_player = self.game_ui.game.setup_player
                self.game_ui.message = f"Player {current_setup_player} is placing units..."
                return
            
        # Check if all units have been placed
        setup_player = self.game_ui.game.setup_player
        if self.game_ui.game.setup_units_remaining[setup_player] > 0:
            # Use event system for message
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message=f"Place all units before confirming ({self.game_ui.game.setup_units_remaining[setup_player]} remaining)",
                    message_type=MessageType.WARNING
                )
            )
            return
        
        # For network games, route through GameStateSync
        if self.game_ui.multiplayer.is_network_multiplayer() and self.game_ui.multiplayer.game_state_sync:
            # Send setup confirmation through network
            self.game_ui.multiplayer.game_state_sync.send_setup_action("confirm_setup", {})
            return
        
        # Check if we're in single player mode
        is_single_player = not self.game_ui.multiplayer.is_multiplayer()
            
        # Confirm the current player's setup
        game_start = self.game_ui.game.confirm_setup()
        
        # No special handling for VS_AI mode yet - it's not implemented
        is_vs_ai_mode = False
        
        # Add appropriate status message through event system
        if setup_player == 1:
            # Show game start message if game is started
            if game_start:
                # In single player mode, we automatically placed units for player 2
                if is_single_player:
                    # Publish turn started event to properly initialize the game
                    self.publish_event(
                        EventType.TURN_STARTED,
                        TurnEventData(
                            player=1,
                            turn_number=1
                        )
                    )
                    
                    # Notify the player about single player mode
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Game starting in single player mode. Player 1 - Turn 1",
                            message_type=MessageType.SYSTEM
                        )
                    )
                else:
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Player 1 - Turn 1",
                            message_type=MessageType.SYSTEM
                        )
                    )
            else:
                # Normal local multiplayer mode - message shown in UI only, not in log
                self.game_ui.message = "Player 2's turn to place units"
                # Start player 2 with cursor in center
                self.game_ui.cursor_manager.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)
                # Publish cursor moved event
                self.publish_event(
                    EventType.CURSOR_MOVED, 
                    CursorMovedEventData(position=self.game_ui.cursor_manager.cursor_pos)
                )
        elif game_start:
            self.publish_event(
                EventType.MESSAGE_DISPLAY_REQUESTED,
                MessageDisplayEventData(
                    message="Player 1 - Turn 1",
                    message_type=MessageType.SYSTEM
                )
            )
            
        # Request UI redraw
        self.publish_event(
            EventType.UI_REDRAW_REQUESTED,
            UIRedrawEventData()
        )
        
    # This function would be implemented later for AI mode
    def _placeholder_for_ai_setup(self):
        """Placeholder for future AI unit auto-setup functionality."""
        from boneglaive.utils.debug import logger
        logger.info("AI setup functionality not implemented yet")
        
    def check_confirmation_needed(self):
        """Check if confirmation is needed in setup phase."""
        if not self.game_ui.game.setup_phase:
            return False
        
        # Check if all units have been placed
        setup_player = self.game_ui.game.setup_player
        return self.game_ui.game.setup_units_remaining[setup_player] == 0
            
    def is_valid_setup_position(self, y, x):
        """Check if a position is valid for unit placement during setup."""
        # Check if position is in bounds
        if not self.game_ui.game.is_valid_position(y, x):
            return False
            
        # Check if position has blocking terrain (like limestone)
        if not self.game_ui.game.map.can_place_unit(y, x):
            return False
            
        return True
    
    def draw_setup_instructions(self):
        """Draw the setup phase instructions screen."""
        try:
            # Get terminal size
            term_height, term_width = self.renderer.get_terminal_size()
            
            # Draw title
            self.renderer.draw_text(2, 2, "=== BONEGLAIVE SETUP PHASE ===", 1, curses.A_BOLD)
            
            # Draw instructions
            setup_player = self.game_ui.game.setup_player
            player_color = self.game_ui.chat_component.player_colors.get(setup_player, 1)
            
            # Map UnitType to display name
            unit_type_display = {
                UnitType.GLAIVEMAN: "GLAIVEMAN",
                UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
                UnitType.GRAYMAN: "GRAYMAN",
                UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
                UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
                UnitType.GAS_MACHINIST: "GAS MACHINIST",
                UnitType.DELPHIC_APPRAISER: "DELPHIC APPRAISER",
                UnitType.INTERFERER: "INTERFERER"
            }
            current_unit_type = unit_type_display.get(self.setup_unit_type, "UNKNOWN")
            
            instructions = [
                f"Player {setup_player}, place your units on the battlefield.",
                "",
                f"Each player must place 3 units (Current unit type: {current_unit_type}).",
                "",
                "Controls:",
                "- Arrow keys or HJKL: Move cursor",
                "- YUBN: Move cursor diagonally",
                "- Enter/Space: Place unit at cursor position",
                "- [Backspace]: Switch between unit types",
                "- [Y]es: Confirm unit placement (when all units are placed)",
                "",
                "Special rules:",
                "- Player 1's units will be hidden during Player 2's placement",
                "- After both players finish placement, any units overlapping",
                "  will be automatically displaced to nearby positions",
                "- First-placed units will remain in their positions",
                "",
                "Note: The 'y' key works as diagonal movement until all units are placed,",
                "      then it becomes [Y]es confirmation key."
            ]
            
            # Draw instructions
            for i, line in enumerate(instructions):
                y_pos = 5 + i
                if "Player 1" in line and setup_player == 1:
                    self.renderer.draw_text(y_pos, 4, line, 3)  # Player 1 color
                elif "Player 2" in line and setup_player == 2:
                    self.renderer.draw_text(y_pos, 4, line, 4)  # Player 2 color
                else:
                    self.renderer.draw_text(y_pos, 4, line)
            
            # Draw current player indicator
            player_text = f"Player {setup_player}'s turn to place units"
            self.renderer.draw_text(5 + len(instructions) + 2, 4, player_text, player_color, curses.A_BOLD)
            
            # Draw footer
            self.renderer.draw_text(term_height - 3, 2, "Press any key to continue...", 1, curses.A_BOLD)
            
        except Exception as e:
            logger.error(f"Error displaying setup instructions: {str(e)}")

# Debug component
class DebugComponent(UIComponent):
    """Component for handling debug functions."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
    
    def handle_debug_info(self):
        """Toggle message log or show debug info."""
        # Toggle message log when 'l' is pressed
        if self.game_ui.input_handler.action_map.get(ord('l')) == GameAction.DEBUG_INFO:
            self.game_ui.message_log_component.toggle_message_log()
            return
            
        # Otherwise show unit positions
        debug_info = []
        for unit in self.game_ui.game.units:
            if unit.is_alive():
                debug_info.append(f"({unit.y},{unit.x})")
        self.game_ui.message = f"Unit positions: {' '.join(debug_info)}"
        logger.debug(f"Unit positions: {debug_info}")
    
    def handle_debug_toggle(self):
        """Toggle debug mode."""
        debug_enabled = debug_config.toggle()
        self.game_ui.message = f"Debug mode {'ON' if debug_enabled else 'OFF'}"
        
        message_text = f"Debug mode {'enabled' if debug_enabled else 'disabled'}"
        logger.info(message_text)
        # Don't add debug messages to the message log
    
    def handle_debug_overlay(self):
        """Toggle debug overlay."""
        overlay_enabled = debug_config.toggle_overlay()
        self.game_ui.message = f"Debug overlay {'ON' if overlay_enabled else 'OFF'}"
    
    def handle_debug_performance(self):
        """Toggle performance tracking."""
        perf_enabled = debug_config.toggle_perf_tracking()
        self.game_ui.message = f"Performance tracking {'ON' if perf_enabled else 'OFF'}"
    
    def handle_debug_save(self):
        """Save game state to file."""
        if not debug_config.enabled:
            return
            
        try:
            game_state = self.game_ui.game.get_game_state()
            os.makedirs('debug', exist_ok=True)
            filename = f"debug/game_state_turn{self.game_ui.game.turn}.json"
            with open(filename, 'w') as f:
                json.dump(game_state, f, indent=2)
            self.game_ui.message = f"Game state saved to {filename}"
            logger.info(f"Game state saved to {filename}")
        except Exception as e:
            self.game_ui.message = f"Error saving game state: {str(e)}"
            logger.error(f"Error saving game state: {str(e)}")

# Animation component
class AnimationComponent(UIComponent):
    """Component for handling animations."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        
    @measure_perf
    def show_attack_animation(self, attacker, target):
        """Show a visual animation for attacks."""
        # Import required modules
        from boneglaive.utils.constants import UnitType
        import time
        import curses
        
        # Get attack effect from asset manager
        effect_tile = self.game_ui.asset_manager.get_attack_effect(attacker.type)
        
        # Get animation sequence
        animation_sequence = self.game_ui.asset_manager.get_attack_animation_sequence(attacker.type)
        
        # Create start and end positions
        start_pos = Position(attacker.y, attacker.x)
        end_pos = Position(target.y, target.x)
        
        # For ranged attacks (archer and mage), show animation at origin then projectile path
        if attacker.type in [UnitType.ARCHER, UnitType.MAGE]:
            # First show attack preparation at attacker's position
            prep_sequence = animation_sequence[:2]  # First few frames of animation sequence
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x,
                prep_sequence,
                7,  # color ID
                0.2  # quick preparation animation
            )
            
            # Then animate projectile from attacker to target
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                effect_tile,
                7,  # color ID
                0.3  # duration
            )
        # For MANDIBLE_FOREMAN, show a special animation sequence for mandible jaws
        elif attacker.type == UnitType.MANDIBLE_FOREMAN:
            # Show the jaws animation at the attacker's position
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence[:3],  # First three frames - jaws opening
                7,  # color ID
                0.3  # slightly faster animation
            )
            
            # Show a short connecting animation between attacker and target
            # to visualize the mandibles reaching out
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                'Ξ',  # Mandible symbol
                7,    # color ID
                0.2   # quick connection
            )
            
            # Show the final part of the animation at the target position
            self.renderer.animate_attack_sequence(
                end_pos.y, end_pos.x, 
                animation_sequence[3:],  # Last frames - jaws clamping and retracting
                7,  # color ID
                0.4  # duration
            )
        # For GLAIVEMAN attacks, check range and choose the right animation
        elif attacker.type == UnitType.GLAIVEMAN:
            # Calculate distance to target
            distance = self.game_ui.game.chess_distance(start_pos.y, start_pos.x, end_pos.y, end_pos.x)
            
            # For range 2 attacks, use extended animation
            if distance == 2:
                # Get the extended animation sequence
                extended_sequence = self.game_ui.asset_manager.animation_sequences.get('glaiveman_extended_attack', [])
                if extended_sequence:
                    # First show windup animation at attacker's position
                    self.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        extended_sequence[:4],  # First few frames at attacker position
                        7,  # color ID
                        0.3  # duration
                    )
                    
                    # Then animate the glaive extending from attacker to target
                    # Calculate direction from attacker to target
                    from boneglaive.utils.coordinates import get_line
                    path = get_line(start_pos, end_pos)
                    
                    # Get the middle position for the extending animation (if path has at least 3 points)
                    if len(path) >= 3:
                        mid_pos = path[1]  # Second point in the path
                        
                        # Show glaive extending through middle position
                        extension_chars = extended_sequence[4:8]  # Middle frames show extension
                        for i, char in enumerate(extension_chars):
                            self.renderer.draw_tile(mid_pos.y, mid_pos.x, char, 7)
                            self.renderer.refresh()
                            time.sleep(0.1)
                    
                    # Finally show the impact at target position
                    self.renderer.animate_attack_sequence(
                        end_pos.y, end_pos.x, 
                        extended_sequence[8:],  # Last frames at target position
                        7,  # color ID
                        0.3  # duration
                    )
                else:
                    # Fallback to standard animation if extended sequence isn't available
                    self.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        animation_sequence,
                        7,  # color ID
                        0.5  # duration
                    )
            else:
                # For range 1 attacks, use standard animation
                self.renderer.animate_attack_sequence(
                    start_pos.y, start_pos.x, 
                    animation_sequence,
                    7,  # color ID
                    0.5  # duration
                )
        # Special case for FOWL_CONTRIVANCE - rail artillery platform animation
        elif attacker.type == UnitType.FOWL_CONTRIVANCE:
            # Get the rail artillery animation sequence
            fowl_sequence = self.game_ui.asset_manager.animation_sequences.get('fowl_contrivance_attack', [])
            if not fowl_sequence:
                fowl_sequence = ['T', '=', '-', '>', '*', '#', '@']  # Rail artillery fallback
            
            # Use colors appropriate for rail artillery charging/firing
            color_sequence = [7, 6, 3, 1, 1, 7, 7]  # White, yellow, green, red progression
            
            # Show initial charging animation at attacker's position (rail cannon charging)
            for i in range(3):
                frame = fowl_sequence[i % len(fowl_sequence)]
                color = color_sequence[i % len(color_sequence)]
                self.renderer.draw_tile(start_pos.y, start_pos.x, frame, color)
                self.renderer.refresh()
                time.sleep(0.12)  # Slightly slower for mechanical feel
            
            # Create path points between attacker and target
            from boneglaive.game.animations import get_line
            path = get_line(start_pos.y, start_pos.x, end_pos.y, end_pos.x)
            
            # Animate projectile along the path (rail shot traveling)
            for i, (y, x) in enumerate(path[1:-1]):  # Skip first (attacker) and last (target)
                frame_idx = (i + 3) % len(fowl_sequence)  # Continue from where charging left off
                color_idx = (i + 3) % len(color_sequence)
                self.renderer.draw_tile(y, x, fowl_sequence[frame_idx], color_sequence[color_idx])
                self.renderer.refresh()
                time.sleep(0.04)  # Fast projectile movement
            
            # Final impact animation directly at target (rail shot impact)
            final_frames = ['*', '#', '@', 'X', '※']  # Explosive impact sequence
            for i, frame in enumerate(final_frames):
                color = 1 if i % 2 == 0 else 7  # Alternate between red and white
                self.renderer.draw_tile(end_pos.y, end_pos.x, frame, color)
                self.renderer.refresh()
                time.sleep(0.08)
        
        # For all other melee attacks, show standard animation
        else:
            # Show the attack animation at the attacker's position
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence,
                7,  # color ID
                0.5  # duration
            )
        
        # Show impact animation at target position with appropriate ASCII characters based on unit type
        if attacker.type == UnitType.MAGE:
            impact_animation = ['!', '*', '!']  # Magic impact
        elif attacker.type == UnitType.MANDIBLE_FOREMAN:
            impact_animation = ['>', '<', '}', '{', '≡']  # Mandible crushing impact
        elif attacker.type == UnitType.FOWL_CONTRIVANCE:
            impact_animation = ['*', '#', '@', 'X', '*']  # Rail artillery explosive impact
        else:
            impact_animation = ['+', 'x', '+']  # Standard melee/arrow impact
            
        impact_colors = [7] * len(impact_animation)
        impact_durations = [0.05] * len(impact_animation)
        
        # Use renderer's animate_attack_sequence for impact
        self.renderer.animate_attack_sequence(
            target.y, target.x,
            impact_animation,
            7,  # color ID 
            0.25  # duration
        )
        
        # Flash the target to show it was hit
        tile_ids = [self.game_ui.asset_manager.get_unit_tile(target.type)] * 4
        color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 2
        durations = [0.1] * 4
        
        # Use renderer's flash tile method
        self.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Show damage number above target with improved visualization
        # Use effective stats for correct damage display
        effective_attack = attacker.get_effective_stats()['attack']
        effective_defense = target.get_effective_stats()['defense']
        
        # Account for GRAYMAN units that bypass defense
        from boneglaive.utils.constants import UnitType
        if attacker.type == UnitType.GRAYMAN or (hasattr(attacker, 'is_echo') and attacker.is_echo and attacker.type == UnitType.GRAYMAN):
            # GRAYMAN units bypass defense completely
            damage = effective_attack
        else:
            # Normal damage calculation
            damage = max(1, effective_attack - effective_defense)
            
        damage_text = f"-{damage}"
        
        # Make damage text more prominent
        for i in range(3):
            # First clear the area
            self.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
            # Draw with alternating bold/normal for a flashing effect
            attrs = curses.A_BOLD if i % 2 == 0 else 0
            self.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
            self.renderer.refresh()
            time.sleep(0.1)
            
        # Final damage display (stays on screen slightly longer)
        self.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
        self.renderer.refresh()
        time.sleep(0.3)
        
        # Redraw board to clear effects (without cursor, selection, or attack target highlighting)
        self.game_ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

# Action menu component
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
        
        # Check if unit has already taken an action this turn
        unit_has_action = (unit.attack_target or unit.skill_target or unit.selected_skill)
        
        # Add standard actions with consistent labeling
        # Disable move for trapped units, Jawline-affected units, charging units, Neural Shunt, echoes, or units with actions
        unit_can_move = (unit is not None and
                        unit.trapped_by is None and
                        not unit.is_echo and
                        not unit_has_action and
                        not (hasattr(unit, 'jawline_affected') and unit.jawline_affected) and
                        not (hasattr(unit, 'charging_status') and unit.charging_status) and
                        not (hasattr(unit, 'neural_shunt_affected') and unit.neural_shunt_affected))
        self.actions.append({
            'key': 'm',
            'label': 'ove',  # Will be displayed as [M]ove without space
            'action': GameAction.MOVE_MODE,
            'enabled': unit_can_move  # Enabled only if unit can move
        })
        
        # Disable attack for charging units, Neural Shunt, or units with actions
        unit_can_attack = (not unit_has_action and
                          not (hasattr(unit, 'charging_status') and unit.charging_status) and
                          not (hasattr(unit, 'neural_shunt_affected') and unit.neural_shunt_affected))
        self.actions.append({
            'key': 'a',
            'label': 'ttack',  # Will be displayed as [A]ttack without space
            'action': GameAction.ATTACK_MODE,
            'enabled': unit_can_attack
        })
        
        # Add skill action
        unit_has_skills = unit is not None and hasattr(unit, 'active_skills') and len(unit.get_available_skills()) > 0
        # Allow skills to be used even when a move is planned (the unit can cast from the new position)
        # Disable skills when charging (except for Gaussian Dusk auto-firing which is handled differently), under Neural Shunt, or with actions
        unit_can_use_skills = (unit_has_skills and unit.trapped_by is None and not unit.is_echo and
                              not unit_has_action and
                              not (hasattr(unit, 'charging_status') and unit.charging_status) and
                              not (hasattr(unit, 'neural_shunt_affected') and unit.neural_shunt_affected))
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
            
            # Add Judgement skill
            judgement_skill = next((skill for skill in available_skills if skill.name == "Judgement"), None)
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
            
        # MARROW_CONDENSER skills
        elif unit.type == self.UnitType.MARROW_CONDENSER:
            
            # Add Ossify skill
            ossify_skill = next((skill for skill in available_skills if skill.name == "Ossify"), None)
            self.actions.append({
                'key': 'o',
                'label': 'ssify',  # Will be displayed as [O]ssify
                'action': 'ossify_skill',
                'enabled': ossify_skill is not None,
                'skill': ossify_skill
            })
            
            # Add Marrow Dike skill
            marrow_dike_skill = next((skill for skill in available_skills if skill.name == "Marrow Dike"), None)
            self.actions.append({
                'key': 'm',
                'label': 'arrow Dike',  # Will be displayed as [M]arrow Dike
                'action': 'marrow_dike_skill',
                'enabled': marrow_dike_skill is not None,
                'skill': marrow_dike_skill
            })
            
            # Add Bone Tithe skill
            bone_tithe_skill = next((skill for skill in available_skills if skill.name == "Bone Tithe"), None)
            self.actions.append({
                'key': 'b',
                'label': 'one Tithe',  # Will be displayed as [B]one Tithe
                'action': 'bone_tithe_skill',
                'enabled': bone_tithe_skill is not None,
                'skill': bone_tithe_skill
            })
            
        # FOWL_CONTRIVANCE skills
        elif unit.type == self.UnitType.FOWL_CONTRIVANCE:
            
            # Check if unit is charging (affects skill availability)
            is_charging = hasattr(unit, 'charging_status') and unit.charging_status

            # Add Gaussian Dusk skill
            gaussian_dusk_skill = next((skill for skill in available_skills if skill.name == "Gaussian Dusk"), None)
            self.actions.append({
                'key': 'g',
                'label': 'aussian Dusk',  # Will be displayed as [G]aussian Dusk
                'action': 'gaussian_dusk_skill',
                'enabled': gaussian_dusk_skill is not None,
                'skill': gaussian_dusk_skill
            })
            
            # Add Big Arc skill - disabled when charging
            big_arc_skill = next((skill for skill in available_skills if skill.name == "Big Arc"), None)
            self.actions.append({
                'key': 'b',
                'label': 'ig Arc',  # Will be displayed as [B]ig Arc
                'action': 'big_arc_skill',
                'enabled': big_arc_skill is not None and not is_charging,
                'skill': big_arc_skill
            })
            
            # Add Fragcrest skill - disabled when charging
            fragcrest_skill = next((skill for skill in available_skills if skill.name == "Fragcrest"), None)
            self.actions.append({
                'key': 'f',
                'label': 'ragcrest',  # Will be displayed as [F]ragcrest
                'action': 'fragcrest_skill',
                'enabled': fragcrest_skill is not None and not is_charging,
                'skill': fragcrest_skill
            })
            
        # GAS_MACHINIST skills
        elif unit.type == self.UnitType.GAS_MACHINIST:

            # Add Broaching Gas skill
            broaching_gas_skill = next((skill for skill in available_skills if skill.name == "Broaching Gas"), None)
            self.actions.append({
                'key': 'b',
                'label': 'roaching Gas',  # Will be displayed as [B]roaching Gas
                'action': 'broaching_gas_skill',
                'enabled': broaching_gas_skill is not None,
                'skill': broaching_gas_skill
            })

            # Add Saft-E-Gas skill
            saft_e_gas_skill = next((skill for skill in available_skills if skill.name == "Saft-E-Gas"), None)
            self.actions.append({
                'key': 's',
                'label': 'aft-E-Gas',  # Will be displayed as [S]aft-E-Gas
                'action': 'saft_e_gas_skill',
                'enabled': saft_e_gas_skill is not None,
                'skill': saft_e_gas_skill
            })

            # Add Diverge skill
            diverge_skill = next((skill for skill in available_skills if skill.name == "Diverge"), None)
            self.actions.append({
                'key': 'd',
                'label': 'iverge',  # Will be displayed as [D]iverge
                'action': 'diverge_skill',
                'enabled': diverge_skill is not None,
                'skill': diverge_skill
            })

        # DELPHIC_APPRAISER skills
        elif unit.type == self.UnitType.DELPHIC_APPRAISER:

            # Add Market Futures skill
            market_futures_skill = next((skill for skill in available_skills if skill.name == "Market Futures"), None)
            self.actions.append({
                'key': 'm',
                'label': 'arket Futures',  # Will be displayed as [M]arket Futures
                'action': 'market_futures_skill',
                'enabled': market_futures_skill is not None,
                'skill': market_futures_skill
            })

            # Add Auction Curse skill
            auction_curse_skill = next((skill for skill in available_skills if skill.name == "Auction Curse"), None)
            self.actions.append({
                'key': 'a',
                'label': 'uction Curse',  # Will be displayed as [A]uction Curse
                'action': 'auction_curse_skill',
                'enabled': auction_curse_skill is not None,
                'skill': auction_curse_skill
            })

            # Add Divine Depreciation skill
            divine_depreciation_skill = next((skill for skill in available_skills if skill.name == "Divine Depreciation"), None)
            self.actions.append({
                'key': 'd',
                'label': 'ivine Depreciation',  # Will be displayed as [D]ivine Depreciation
                'action': 'divine_depreciation_skill',
                'enabled': divine_depreciation_skill is not None,
                'skill': divine_depreciation_skill
            })

        # INTERFERER skills
        elif unit.type == self.UnitType.INTERFERER:

            # Add Neural Shunt skill
            neural_shunt_skill = next((skill for skill in available_skills if skill.name == "Neural Shunt"), None)
            self.actions.append({
                'key': 'n',
                'label': 'eural Shunt',  # Will be displayed as [N]eural Shunt
                'action': 'neural_shunt_skill',
                'enabled': neural_shunt_skill is not None,
                'skill': neural_shunt_skill
            })

            # Add Karrier Rave skill
            carrier_rave_skill = next((skill for skill in available_skills if skill.name == "Karrier Rave"), None)
            self.actions.append({
                'key': 'k',
                'label': 'arrier Rave',  # Will be displayed as [K]arrier Rave
                'action': 'karrier_rave_skill',
                'enabled': carrier_rave_skill is not None,
                'skill': carrier_rave_skill
            })

            # Add Scalar Node skill
            scalar_node_skill = next((skill for skill in available_skills if skill.name == "Scalar Node"), None)
            self.actions.append({
                'key': 's',
                'label': 'calar Node',  # Will be displayed as [S]calar Node
                'action': 'scalar_node_skill',
                'enabled': scalar_node_skill is not None,
                'skill': scalar_node_skill
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
        
        # Set header text based on menu mode, using shortened name for menus
        if self.menu_mode == "standard":
            header = f" {unit.get_display_name(shortened=True)} Actions "
        else:
            header = f" {unit.get_display_name(shortened=True)} Skills "
        
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
            
            # Handle key matches - both enabled and disabled actions
            if key_match:
                if not action['enabled']:
                    # Action is disabled - consume the key press to prevent fallthrough
                    return True
                    
                # Action is enabled, proceed normally
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
            
            # Log skill input for Gaussian Dusk
            if skill.name == "Gaussian Dusk":
                message_log.add_message(
                    f"{cursor_manager.selected_unit.get_display_name()} prepares Gaussian Dusk.",
                    MessageType.ABILITY,
                    player=cursor_manager.selected_unit.player
                )
            
            # Change to skill targeting mode
            mode_manager.set_mode("skill")
            
            # Highlight valid targets for the skill based on target type
            game = self.game_ui.game
            targets = []
            from boneglaive.utils.constants import HEIGHT, WIDTH
            
            # Get the unit's current or planned position
            from_y = cursor_manager.selected_unit.y
            from_x = cursor_manager.selected_unit.x
            
            # If unit has a planned move, use that position instead
            # This allows skills to be cast from the new position after a move
            if cursor_manager.selected_unit.move_target:
                from_y, from_x = cursor_manager.selected_unit.move_target
            
            # Special visualization for MARROW_CONDENSER area skills
            if skill.name in ["Marrow Dike", "Bone Tithe"]:
                # Special visual indicators for MARROW_CONDENSER's area skills
                area_targets = []
                
                # Get area size from the skill
                area_size = getattr(skill, 'area', 1)  # Default to 1 if not specified
                
                # For Marrow Dike, we want to show the perimeter of the area (the walls)
                if skill.name == "Marrow Dike":
                    # Marrow Dike creates walls in a 5x5 perimeter (area=2)
                    for dy in range(-area_size, area_size+1):
                        for dx in range(-area_size, area_size+1):
                            # Only include perimeter tiles (not the interior)
                            if abs(dy) == area_size or abs(dx) == area_size:
                                tile_y, tile_x = from_y + dy, from_x + dx
                                if game.is_valid_position(tile_y, tile_x):
                                    area_targets.append(Position(tile_y, tile_x))
                    
                    # Also display a special message
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message=f"Marrow Dike will create walls around the perimeter.",
                            message_type=MessageType.ABILITY
                        )
                    )
                # For Bone Tithe, we want to show all adjacent tiles
                elif skill.name == "Bone Tithe":
                    # Bone Tithe affects all tiles in a 3x3 area (area=1)
                    for dy in range(-area_size, area_size+1):
                        for dx in range(-area_size, area_size+1):
                            # Skip the center (MARROW_CONDENSER's position)
                            if dy == 0 and dx == 0:
                                continue
                            
                            tile_y, tile_x = from_y + dy, from_x + dx
                            if game.is_valid_position(tile_y, tile_x):
                                area_targets.append(Position(tile_y, tile_x))
                
                # Set highlighted positions for visualization
                cursor_manager.highlighted_positions = area_targets
                
                # Set skill target to self (it's a self-targeted skill)
                cursor_manager.selected_unit.skill_target = (from_y, from_x)
                
                # IMPORTANT: Use the skill now to properly set the cooldown
                # This is a self-targeted skill, similar to Jawline
                
                # For Marrow Dike, just use normal can_use/use flow
                if skill.name == "Marrow Dike":
                    if skill.can_use(cursor_manager.selected_unit, (from_y, from_x), game):
                        # Store unit reference before clearing selection
                        unit = cursor_manager.selected_unit
                        skill.use(unit, (from_y, from_x), game)
                        # Return to select mode
                        mode_manager.set_mode("select")
                        # Clear selection to prevent further actions
                        cursor_manager.clear_selection()
                # For Bone Tithe, we need to directly set the cooldown since its can_use check
                # may fail if there are no valid targets, but we still want to set cooldown
                elif skill.name == "Bone Tithe":
                    # Store unit reference before clearing selection
                    unit = cursor_manager.selected_unit

                    # Set skill target
                    unit.skill_target = (from_y, from_x)
                    unit.selected_skill = skill

                    # Force set the cooldown directly
                    skill.current_cooldown = skill.cooldown

                    # Log the message (similar to what's in skill.use())
                    message_log.add_message(
                        f"{unit.get_display_name()} prepares to collect the Bone Tithe",
                        MessageType.ABILITY,
                        player=unit.player
                    )

                    # Return to select mode
                    mode_manager.set_mode("select")
                    # Clear selection to prevent further actions
                    cursor_manager.clear_selection()
                
                # Draw the board to show the highlighted area
                self.game_ui.draw_board()
                
                # Wait for user confirmation (handled by handle_select method)
                # The input handler will call handle_select when Space is pressed,
                # which will execute the skill
                
                # Return without requiring additional targeting
                return
            
            # Different targeting logic based on skill target type
            if skill.target_type == TargetType.SELF:
                # Special case for Diverge skill which can target both self and vapors
                if skill.name == "Diverge":
                    # Temporarily change mode to allow targeting
                    mode_manager.mode = "target_vapor"
                    # Set a flag to identify we're in vapor targeting mode
                    mode_manager.targeting_vapor = True
                    
                    # Check if there's a move target set - if so, update cursor to that location
                    if cursor_manager.selected_unit.move_target:
                        # Move cursor to the move target position for easy selection of the new position
                        move_y, move_x = cursor_manager.selected_unit.move_target
                        cursor_manager.cursor_pos = Position(move_y, move_x)
                        
                        # Publish cursor moved event
                        self.publish_event(
                            EventType.CURSOR_MOVED, 
                            CursorMovedEventData(
                                position=cursor_manager.cursor_pos, 
                                previous_position=Position(cursor_manager.selected_unit.y, cursor_manager.selected_unit.x)
                            )
                        )
                                    
                    # Display a message about targeting options
                    self.publish_event(
                        EventType.MESSAGE_DISPLAY_REQUESTED,
                        MessageDisplayEventData(
                            message="Select self or a HEINOUS VAPOR to diverge",
                            message_type=MessageType.ABILITY
                        )
                    )
                    # Exit early to allow targeting
                    return
                
                # For other self-targeted skills like Recalibrate or Jawline, use immediately without targeting
                if skill.can_use(cursor_manager.selected_unit, (from_y, from_x), game):
                    # Set the skill target to self
                    cursor_manager.selected_unit.skill_target = (from_y, from_x)

                    # Store a reference to the unit before clearing selection
                    unit = cursor_manager.selected_unit

                    # Actually use the skill now
                    skill.use(unit, (from_y, from_x), game)

                    # Return to select mode
                    mode_manager.set_mode("select")
                    # Clear the unit selection to prevent multiple actions
                    cursor_manager.clear_selection()
                    
                    # Special message for Jawline skill
                    if skill.name == "Jawline":
                        # We no longer need to show a message here - it's shown in the skill's use() method
                        # Mark that we've shown this message to prevent any legacy code from showing it again
                        unit.jawline_message_shown = True
                    elif skill.name == "Fragcrest":
                        # No need for a message here, as the skill's use() method already adds a message
                        pass
                    else:
                        # No message needed for generic end-of-turn skills
                        pass
                    
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
                                    # Check if target is protected by Saft-E-Gas (same behavior as attacks)
                                    if hasattr(game, 'is_protected_from') and game.is_protected_from(target, cursor_manager.selected_unit):
                                        # Don't add to targets, protection prevents targeting
                                        pass
                                    else:
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
                # No message when there are no valid targets
                
                # Reset selected skill
                cursor_manager.selected_unit.selected_skill = None
                # Return to select mode
                mode_manager.set_mode("select")

# Input manager component
class InputManager(UIComponent):
    """Component for handling input processing."""
    
    def __init__(self, renderer, game_ui, input_handler):
        super().__init__(renderer, game_ui)
        self.input_handler = input_handler
        self.setup_input_callbacks()
    
    def _setup_event_handlers(self):
        """Set up event handlers for input manager."""
        pass
        
    def setup_input_callbacks(self):
        """Set up callbacks for input handling."""
        cursor_manager = self.game_ui.cursor_manager
        mode_manager = self.game_ui.mode_manager
        event_manager = self.event_manager
        
        # Helper function to publish mode requests
        def publish_move_mode_request():
            event_manager.publish(EventType.MOVE_MODE_REQUESTED, EventData())

        def publish_attack_mode_request():
            event_manager.publish(EventType.ATTACK_MODE_REQUESTED, EventData())

        def publish_select_mode_request():
            event_manager.publish(EventType.SELECT_MODE_REQUESTED, EventData())

        def publish_teleport_mode_request():
            event_manager.publish(EventType.TELEPORT_MODE_REQUESTED, EventData())

        def publish_cancel_request():
            event_manager.publish(EventType.CANCEL_REQUESTED, EventData())
        
        self.input_handler.register_action_callbacks({
            # Cardinal directions
            GameAction.MOVE_UP: lambda: cursor_manager.move_cursor(-1, 0),
            GameAction.MOVE_DOWN: lambda: cursor_manager.move_cursor(1, 0),
            GameAction.MOVE_LEFT: lambda: cursor_manager.move_cursor(0, -1),
            GameAction.MOVE_RIGHT: lambda: cursor_manager.move_cursor(0, 1),

            # Diagonal directions
            GameAction.MOVE_UP_LEFT: lambda: cursor_manager.move_cursor_diagonal("up-left"),
            GameAction.MOVE_UP_RIGHT: lambda: cursor_manager.move_cursor_diagonal("up-right"),
            GameAction.MOVE_DOWN_LEFT: lambda: cursor_manager.move_cursor_diagonal("down-left"),
            GameAction.MOVE_DOWN_RIGHT: lambda: cursor_manager.move_cursor_diagonal("down-right"),
            GameAction.SELECT: self.game_ui.handle_select,
            GameAction.CANCEL: publish_cancel_request,
            GameAction.MOVE_MODE: publish_move_mode_request,
            GameAction.ATTACK_MODE: publish_attack_mode_request,
            GameAction.TELEPORT_MODE: publish_teleport_mode_request,
            GameAction.END_TURN: mode_manager.handle_end_turn,
            GameAction.TEST_MODE: mode_manager.handle_test_mode,
            GameAction.DEBUG_INFO: self.game_ui.debug_component.handle_debug_info,
            GameAction.DEBUG_TOGGLE: self.game_ui.debug_component.handle_debug_toggle,
            GameAction.DEBUG_OVERLAY: self.game_ui.debug_component.handle_debug_overlay,
            GameAction.DEBUG_PERFORMANCE: self.game_ui.debug_component.handle_debug_performance,
            GameAction.DEBUG_SAVE: self.game_ui.debug_component.handle_debug_save,
            GameAction.HELP: self._handle_help_request,
            GameAction.CHAT_MODE: self.game_ui.chat_component.toggle_chat_mode,
            GameAction.CYCLE_UNITS: cursor_manager.cycle_units,
            GameAction.CYCLE_UNITS_REVERSE: cursor_manager.cycle_units_reverse,
            GameAction.LOG_HISTORY: self.game_ui.message_log_component.toggle_log_history,
            GameAction.CONFIRM: mode_manager.handle_confirm,  # For setup phase confirmation
            GameAction.SETUP_NEXT_UNIT: mode_manager.navigate_setup_unit_next,  # TAB in setup
            GameAction.SETUP_PREV_UNIT: mode_manager.navigate_setup_unit_prev   # SHIFT+TAB in setup
        })
        
        # Add custom key for toggling message log
        self.input_handler.add_mapping(ord('l'), GameAction.DEBUG_INFO)  # Reuse DEBUG_INFO for log toggle
    
    def _handle_help_request(self):
        """Handle help request - show unit help if appropriate unit selected, otherwise general help."""
        cursor_manager = self.game_ui.cursor_manager
        
        # Check if a unit with help data is currently selected
        if cursor_manager.selected_unit:
            unit_type = cursor_manager.selected_unit.type
            if unit_type == UnitType.GLAIVEMAN:
                # Show GLAIVEMAN unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.GLAIVEMAN)
                return
            elif unit_type == UnitType.MANDIBLE_FOREMAN:
                # Show MANDIBLE_FOREMAN unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.MANDIBLE_FOREMAN)
                return
            elif unit_type == UnitType.GRAYMAN:
                # Check if this is an echo or regular GRAYMAN
                if hasattr(cursor_manager.selected_unit, 'is_echo') and cursor_manager.selected_unit.is_echo:
                    # Show GRAYMAN echo help
                    self.game_ui.unit_help_component.toggle_unit_help('GRAYMAN_ECHO')
                else:
                    # Show regular GRAYMAN unit help
                    self.game_ui.unit_help_component.toggle_unit_help(UnitType.GRAYMAN)
                return
            elif unit_type == UnitType.MARROW_CONDENSER:
                # Show MARROW_CONDENSER unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.MARROW_CONDENSER)
                return
            elif unit_type == UnitType.FOWL_CONTRIVANCE:
                # Show FOWL_CONTRIVANCE unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.FOWL_CONTRIVANCE)
                return
            elif unit_type == UnitType.GAS_MACHINIST:
                # Show GAS_MACHINIST unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.GAS_MACHINIST)
                return
            elif unit_type == UnitType.DELPHIC_APPRAISER:
                # Show DELPHIC_APPRAISER unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.DELPHIC_APPRAISER)
                return
            elif unit_type == UnitType.INTERFERER:
                # Show INTERFERER unit help
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.INTERFERER)
                return
            elif unit_type == UnitType.HEINOUS_VAPOR:
                # Check what type of vapor this is by symbol
                if hasattr(cursor_manager.selected_unit, 'vapor_symbol'):
                    if cursor_manager.selected_unit.vapor_symbol == 'Φ':
                        # Show BROACHING GAS help
                        self.game_ui.unit_help_component.toggle_unit_help('HEINOUS_VAPOR_BROACHING')
                        return
                    elif cursor_manager.selected_unit.vapor_symbol == 'Θ':
                        # Show SAFT-E-GAS help
                        self.game_ui.unit_help_component.toggle_unit_help('HEINOUS_VAPOR_SAFT_E')
                        return
                    elif cursor_manager.selected_unit.vapor_symbol == 'Σ':
                        # Show COOLANT GAS help
                        self.game_ui.unit_help_component.toggle_unit_help('HEINOUS_VAPOR_COOLANT')
                        return
                    elif cursor_manager.selected_unit.vapor_symbol == '%':
                        # Show CUTTING GAS help
                        self.game_ui.unit_help_component.toggle_unit_help('HEINOUS_VAPOR_CUTTING')
                        return
                # Default case for unknown vapor types
                self.game_ui.unit_help_component.toggle_unit_help(UnitType.HEINOUS_VAPOR)
                return
        
        # Show general help screen
        self.game_ui.help_component.toggle_help_screen()
        
    def process_input(self, key: int) -> bool:
        """Process input and delegate to appropriate component."""
        # Handle game over prompt if visible (highest priority)
        if hasattr(self.game_ui, 'game_over_prompt') and self.game_ui.game_over_prompt.visible:
            if key == curses.KEY_UP:
                self.game_ui.game_over_prompt.move_selection(-1)
                return True
            elif key == curses.KEY_DOWN:
                self.game_ui.game_over_prompt.move_selection(1)
                return True
            elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key
                result = self.game_ui.game_over_prompt.select_option()
                if result == "main_menu":
                    # Return special value to indicate main menu should be shown
                    return "main_menu"
                return result
            # No other keys have effect when game over prompt is visible
            return True

        # Handle concede prompt input
        if self.game_ui.concede_prompt.visible:
            if key in [curses.KEY_UP, ord('k')]:  # Move selection up
                self.game_ui.concede_prompt.move_selection(-1)
                return True
            elif key in [curses.KEY_DOWN, ord('j')]:  # Move selection down
                self.game_ui.concede_prompt.move_selection(1)
                return True
            elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key
                result = self.game_ui.concede_prompt.select_option()
                if result == "main_menu":
                    # Return special value to indicate main menu should be shown
                    return "main_menu"
                return result
            elif key == 27 or key == ord('c'):  # Escape or 'c' key - cancel/resume
                self.game_ui.concede_prompt.hide()
                return True
            # No other keys have effect when concede prompt is visible
            return True

        # Handle 'q' key for concede dialog (except in chat mode and setup phase)
        if key == ord('q') and not self.game_ui.chat_component.chat_mode and not self.game_ui.message_log_component.show_log_history and not self.game_ui.game.setup_phase:
            # Show concede prompt instead of immediately quitting
            self.game_ui.concede_prompt.show()
            return True

        # Handle '?' key for context-aware help during setup phase
        if key == ord('?') and self.game_ui.game.setup_phase:
            # During setup phase, show unit-specific help based on cursor position
            selected_unit_type = self.game_ui.unit_selection_menu.get_selected_unit_type()
            self.game_ui.unit_help_component.toggle_unit_help(selected_unit_type)
            return True

        # Handle 'c' key to remove last placed unit during setup phase
        if key == ord('c') and self.game_ui.game.setup_phase:
            # Remove the last unit placed by the current player
            removed = self.game_ui.game.remove_last_setup_unit()
            if removed:
                self.game_ui.message = "Last placed unit removed"
            else:
                self.game_ui.message = "No units to remove"
            return True

        # First check if any components want to handle this input
        if self.game_ui.message_log_component.handle_input(key):
            return True
            
        if self.game_ui.unit_help_component.handle_input(key):
            return True

        # If in chat mode, handle chat input
        if self.game_ui.chat_component.chat_mode:
            return self.game_ui.chat_component.handle_chat_input(key)

        # Update input context based on current state
        self._update_input_context()
        
        # Default processing
        return self.input_handler.process_input(key)
        
    def _update_input_context(self):
        """Update the input handler context based on current game state."""
        # Default context includes all available contexts
        contexts = ["default", "movement", "action", "debug", "ui"]
        
        # In chat mode, only basic controls are active
        if self.game_ui.chat_component.chat_mode:
            self.input_handler.set_context("default")
            return
            
        # If help screen is showing, limit controls
        if self.game_ui.help_component.show_help:
            self.input_handler.set_context("help")
            return
            
        # If unit help screen is showing, limit controls
        if self.game_ui.unit_help_component.show_unit_help:
            self.input_handler.set_context("help")
            return
            
        # If log history is showing, only allow log navigation
        if self.game_ui.message_log_component.show_log_history:
            self.input_handler.set_context("log")
            return
        
        # Create custom context when unit is affected by Jawline (immobilized)
        cursor_manager = self.game_ui.cursor_manager
        if (cursor_manager.selected_unit and 
            hasattr(cursor_manager.selected_unit, 'jawline_affected') and 
            cursor_manager.selected_unit.jawline_affected):
            
            # Create a custom context without move mode
            self.input_handler.set_context("jawline_immobilized")
            return
            
        # If action menu is visible, we want all normal keys to work (menu handles direct key presses)
        # So we just use the default context which includes everything
        if self.game_ui.action_menu_component.visible:
            self.input_handler.set_context("default")
            return
            
        # If in setup phase, enable the setup context
        if self.game_ui.game.setup_phase:
            # Create a special context that includes setup commands and movement, but not 'y' for diagonal
            self.input_handler.set_context("setup_phase")
            return
            
        # Default - all contexts active
        self.input_handler.set_context("default")


# Unit selection menu component for setup phase
class UnitSelectionMenuComponent(UIComponent):
    """Component for displaying unit selection menu during setup phase."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.selected_index = 0  # Index of currently selected unit type
        self.unit_types = [
            UnitType.GLAIVEMAN,
            UnitType.MANDIBLE_FOREMAN,
            UnitType.GRAYMAN,
            UnitType.MARROW_CONDENSER,
            UnitType.FOWL_CONTRIVANCE,
            UnitType.GAS_MACHINIST,
            UnitType.DELPHIC_APPRAISER,
            UnitType.INTERFERER
        ]
        self.unit_names = {
            UnitType.GLAIVEMAN: "GLAIVEMAN",
            UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
            UnitType.GRAYMAN: "GRAYMAN",
            UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
            UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
            UnitType.GAS_MACHINIST: "GAS MACHINIST",
            UnitType.DELPHIC_APPRAISER: "DELPHIC APPRAISER",
            UnitType.INTERFERER: "INTERFERER"
        }
        
    def _setup_event_handlers(self):
        """Set up event handlers for the unit selection menu."""
        pass
    
    def get_selected_unit_type(self):
        """Get the currently selected unit type."""
        return self.unit_types[self.selected_index]
    
    def set_selected_unit_type(self, unit_type):
        """Set the selected unit type."""
        if unit_type in self.unit_types:
            self.selected_index = self.unit_types.index(unit_type)
    
    
    def draw(self):
        """Draw the unit selection menu on the right side of the screen."""
        if not self.game_ui.game.setup_phase:
            return
            
        # Menu positioning - far right to avoid overlap with map and UI elements  
        menu_x = WIDTH + 25  # Move further right to avoid overlap
        menu_y = 2  # Start a bit down from the top
        
        # Draw menu title
        self.renderer.draw_text(menu_y, menu_x, "Unit Selection:", curses.A_BOLD)
        
        # Draw each unit type
        for i, unit_type in enumerate(self.unit_types):
            y_pos = menu_y + 2 + i
            unit_name = self.unit_names[unit_type]
            
            # Highlight selected unit
            if i == self.selected_index:
                # Draw with highlight
                self.renderer.draw_text(y_pos, menu_x, f"> {unit_name}", curses.A_REVERSE)
            else:
                # Draw normally
                self.renderer.draw_text(y_pos, menu_x, f"  {unit_name}")
    
