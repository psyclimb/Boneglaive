#!/usr/bin/env python3
import curses
from typing import Optional, List, Tuple, Dict

from boneglaive.utils.constants import HEIGHT, WIDTH, UnitType
from boneglaive.game.engine import Game
from boneglaive.utils.coordinates import Position
from boneglaive.utils.debug import debug_config, measure_perf, logger
from boneglaive.utils.asset_manager import AssetManager
from boneglaive.utils.config import ConfigManager
from boneglaive.utils.input_handler import InputHandler, GameAction
from boneglaive.renderers.curses_renderer import CursesRenderer
from boneglaive.utils.render_interface import RenderInterface
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.event_system import (
    get_event_manager, EventType, EventData,
    GameOverEventData, TurnEventData, UIRedrawEventData,
    MessageDisplayEventData
)

# Import component classes
from boneglaive.ui.ui_components import (
    MessageLogComponent, HelpComponent, UnitHelpComponent, ChatComponent,
    CursorManager, GameModeManager, DebugComponent,
    AnimationComponent, InputManager, ActionMenuComponent,
    GameOverPrompt, ConcedePrompt, UnitSelectionMenuComponent
)
from boneglaive.ui.ui_renderer import UIRenderer

class GameUI:
    """User interface for the game - refactored to use component architecture."""
    
    def __init__(self, stdscr=None, renderer=None):
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Set up renderer - use provided renderer or create curses renderer
        if renderer is not None:
            self.renderer = renderer
        else:
            self.renderer = CursesRenderer(stdscr)
            self.renderer.initialize()
        
        # Set up asset manager - force text mode if using pygame renderer
        if renderer is not None and hasattr(renderer, '__class__') and 'PygameRenderer' in renderer.__class__.__name__:
            # For pygame renderer, use text mode assets (characters) not sprite paths
            text_config = ConfigManager()
            text_config.set('display_mode', 'text')
            self.asset_manager = AssetManager(text_config)
        else:
            self.asset_manager = AssetManager(self.config_manager)
        
        # Set up input handler
        self.input_handler = InputHandler()
        
        # Initialize event manager
        self.event_manager = get_event_manager()
        self._event_subscriptions = []
        
        # Game state with setup phase by default
        # Get selected map from config, default to lime_foyer
        selected_map = self.config_manager.get('selected_map', 'lime_foyer')
        from boneglaive.utils.debug import logger
        logger.info(f"GameUI: Reading selected_map from config: '{selected_map}'")
        self.game = Game(skip_setup=False, map_name=selected_map)
        
        # Set up multiplayer manager
        from boneglaive.game.multiplayer_manager import MultiplayerManager
        self.multiplayer = MultiplayerManager(self.game)
        
        # Set UI reference in game engine for animations
        self.game.set_ui_reference(self)
        
        # Message buffer for UI feedback
        self.message = ""
        
        # Spinner for showing action execution
        self.spinner_active = False
        self.spinner_frame = 0
        self.spinner_chars = ['|', '/', '-', '\\', '|', '/', '-', '\\']
        
        # Initialize components (order matters due to dependencies)
        self.cursor_manager = CursorManager(self.renderer, self)
        self.help_component = HelpComponent(self.renderer, self)
        self.unit_help_component = UnitHelpComponent(self.renderer, self)
        self.message_log_component = MessageLogComponent(self.renderer, self)
        self.chat_component = ChatComponent(self.renderer, self)
        self.mode_manager = GameModeManager(self.renderer, self)
        self.debug_component = DebugComponent(self.renderer, self)
        self.animation_component = AnimationComponent(self.renderer, self)
        self.action_menu_component = ActionMenuComponent(self.renderer, self)
        self.game_over_prompt = GameOverPrompt(self.renderer, self)  # Add game over prompt
        self.concede_prompt = ConcedePrompt(self.renderer, self)  # Add concede prompt
        self.unit_selection_menu = UnitSelectionMenuComponent(self.renderer, self)
        self.input_manager = InputManager(self.renderer, self, self.input_handler)
        self.ui_renderer = UIRenderer(self.renderer, self)
        
        # Sync unit selection menu with mode manager's initial setup unit type
        if self.game.setup_phase:
            self.unit_selection_menu.set_selected_unit_type(self.mode_manager.setup_unit_type)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Only show welcome message when not in setup phase
        if not self.game.setup_phase:
            # Display map info in UI message, not in log
            self.message = f"Entering {self.game.map.name}"
            
            # Publish game initialized event
            self._publish_event(
                EventType.GAME_INITIALIZED,
                EventData(game=self.game, map_name=self.game.map.name)
            )
        
        # Seasonal messages are now handled when the game starts (after setup phase)
        
        # Only show game mode message when not in setup phase
        if not self.game.setup_phase:
            # Show multiplayer mode information in UI message only
            if self.multiplayer.is_local_multiplayer():
                self.message = "Local multiplayer mode. Players will take turns on this computer."
            elif self.multiplayer.is_network_multiplayer():
                self.message = "LAN multiplayer mode. Connected to remote player."
                
            # Publish turn started event for initial turn
            self._publish_event(
                EventType.TURN_STARTED,
                TurnEventData(
                    player=self.multiplayer.get_current_player(),
                    turn_number=self.game.turn
                )
            )
        
        # Update message with current player
        self.update_player_message()
        
        # Draw the board immediately to avoid black screen
        self.draw_board()
    
    def _setup_event_handlers(self):
        """Set up event handlers for the main UI."""
        # Subscribe to events
        self._subscribe_to_event(EventType.CURSOR_MOVED, self._on_cursor_moved)
        self._subscribe_to_event(EventType.UNIT_SELECTED, self._on_unit_selected)
        self._subscribe_to_event(EventType.UNIT_DESELECTED, self._on_unit_deselected)
        self._subscribe_to_event(EventType.MODE_CHANGED, self._on_mode_changed)
        self._subscribe_to_event(EventType.GAME_OVER, self._on_game_over)
        self._subscribe_to_event(EventType.UI_REDRAW_REQUESTED, self._on_ui_redraw_requested)
        self._subscribe_to_event(EventType.MESSAGE_DISPLAY_REQUESTED, self._on_message_display_requested)
    
    def _subscribe_to_event(self, event_type, handler):
        """Subscribe to an event and track the subscription."""
        self.event_manager.subscribe(event_type, handler)
        self._event_subscriptions.append((event_type, handler))
    
    def _publish_event(self, event_type, event_data=None):
        """Publish an event."""
        self.event_manager.publish(event_type, event_data)
    
    def _on_cursor_moved(self, event_type, event_data):
        """Handle cursor moved events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_unit_selected(self, event_type, event_data):
        """Handle unit selected events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_unit_deselected(self, event_type, event_data):
        """Handle unit deselected events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_mode_changed(self, event_type, event_data):
        """Handle mode changed events."""
        # No specific action needed yet - just provides a hook for future behavior
        pass
    
    def _on_game_over(self, event_type, event_data):
        """Handle game over events."""
        # Display game over message in message log
        winner = event_data.winner
        message_log.add_system_message(f"Game over. Player {winner} wins")
        self.message = f"Player {winner} wins"

        # Show the game over prompt
        self.game_over_prompt.show(winner)
        
    def _on_ui_redraw_requested(self, event_type, event_data):
        """Handle UI redraw requested events."""
        # Extract parameters from event data
        show_cursor = event_data.show_cursor if hasattr(event_data, 'show_cursor') else True
        show_selection = event_data.show_selection if hasattr(event_data, 'show_selection') else True
        show_attack_targets = event_data.show_attack_targets if hasattr(event_data, 'show_attack_targets') else True
        
        # Redraw the board with the specified parameters
        self.draw_board(show_cursor, show_selection, show_attack_targets)
        
    def _on_message_display_requested(self, event_type, event_data):
        """Handle message display requested events."""
        # Update the message display
        self.message = event_data.message
        
        # If message type is provided and log_message is not explicitly set to False, add to message log
        if (hasattr(event_data, 'message_type') and event_data.message_type is not None and
            not (hasattr(event_data, 'log_message') and event_data.log_message is False)):
            message_log.add_message(event_data.message, event_data.message_type)
    
    def update_player_message(self):
        """Update the message showing the current player (only in message log)."""
        # Don't show any player messages during setup phase
        if self.game.setup_phase:
            return
            
        current_player = self.multiplayer.get_current_player()
        
        if self.multiplayer.is_multiplayer():
            if self.multiplayer.is_current_player_turn():
                message_log.add_system_message(f"Player {current_player} - Turn {self.game.turn}")
            else:
                message_log.add_system_message(f"Player {current_player} - Turn {self.game.turn}")
        else:
            message_log.add_system_message(f"Player {self.game.current_player} - Turn {self.game.turn}")
        
        # Keep the message display area clear
        self.message = ""
    
    def handle_select(self):
        """Route selection to appropriate handler based on mode."""
        # In setup phase, the select action places units
        if self.game.setup_phase:
            return self.mode_manager.handle_setup_select()

        # Check if player can act on this turn
        if not self.cursor_manager.can_act_this_turn():
            self.message = "Not your turn"
            message_log.add_message("Not your turn", MessageType.WARNING)
            return

        # Route to appropriate mode handler
        if self.mode_manager.mode == "select":
            self.mode_manager.handle_select_in_select_mode()
        elif self.mode_manager.mode == "move":
            self.mode_manager.handle_select_in_move_mode()
        elif self.mode_manager.mode == "attack":
            self.mode_manager.handle_select_in_attack_mode()
        elif self.mode_manager.mode == "skill":
            self.mode_manager.handle_select_in_skill_mode()
        elif self.mode_manager.mode == "target_vapor":
            self.mode_manager.handle_select_in_vapor_targeting_mode()
        elif self.mode_manager.mode == "teleport":
            self.mode_manager.handle_select_in_teleport_mode()
    
    def draw_board(self, show_cursor=True, show_selection=True, show_attack_targets=True):
        """Delegate board drawing to the UI renderer component."""
        try:
            self.ui_renderer.draw_board(show_cursor, show_selection, show_attack_targets)
        except KeyboardInterrupt:
            # Silently handle Ctrl+C during drawing - let it propagate up
            raise
        except Exception:
            # Log other drawing errors but continue
            from boneglaive.utils.debug import logger
            logger.error("Error drawing board", exc_info=True)

    def reset_game(self):
        """Reset the game to start a new round."""
        # Clear the message log for the new game
        from boneglaive.utils.message_log import message_log
        message_log.clear_log()

        # Create a new game with setup phase
        self.game = Game(skip_setup=False)

        # Update multiplayer manager to use the new game
        self.multiplayer.game = self.game
        
        # Reinitialize the network interface (including AI) with the new game
        if self.multiplayer.network_interface:
            # Clean up old interface
            if hasattr(self.multiplayer.network_interface, 'cleanup'):
                self.multiplayer.network_interface.cleanup()
            
            # Reinitialize with new game
            if hasattr(self.multiplayer.network_interface, 'initialize'):
                success = self.multiplayer.network_interface.initialize(self.game, ui=self)
                if not success:
                    logger.error("Failed to reinitialize network interface after game reset")
                else:
                    logger.info("Network interface successfully reinitialized after game reset")

        # Set UI reference in game engine for animations
        self.game.set_ui_reference(self)

        # Reset message
        self.message = f"New game started. Entering {self.game.map.name}"

        # Add a welcome message to the cleared log
        message_log.add_system_message(f"New game started. Entering {self.game.map.name}")
        
        # Seasonal messages are now handled when the game starts (after setup phase)
        
        message_log.add_system_message(f"Player {self.game.current_player} - Setup Phase")

        # Reset cursor position to center of board
        from boneglaive.utils.constants import HEIGHT, WIDTH
        from boneglaive.utils.coordinates import Position
        self.cursor_manager.cursor_pos = Position(HEIGHT // 2, WIDTH // 2)

        # Clear the screen buffer to prevent flickering from previous game content
        if hasattr(self.renderer, 'clear_screen'):
            self.renderer.clear_screen()

        # Reset game mode
        self.mode_manager.set_mode("select")

        # Publish game initialized event
        self._publish_event(
            EventType.GAME_INITIALIZED,
            EventData(game=self.game, map_name=self.game.map.name)
        )
    
    def show_attack_animation(self, attacker, target):
        """Delegate animation to the animation component."""
        self.animation_component.show_attack_animation(attacker, target)
    
    def start_spinner(self):
        """Start the action execution spinner animation."""
        self.spinner_active = True
        self.spinner_frame = 0
        
    def stop_spinner(self):
        """Stop the action execution spinner animation."""
        self.spinner_active = False
        
    def advance_spinner(self):
        """Advance the spinner to the next frame and redraw."""
        if not self.spinner_active:
            return
            
        self.spinner_frame = (self.spinner_frame + 1) % len(self.spinner_chars)
        self.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        self.renderer.refresh()
        
    def handle_input(self, key: int) -> bool:
        """Handle user input using the input manager."""
        # Handle setup instructions screen
        if self.game.setup_phase and self.mode_manager.show_setup_instructions:
            self.mode_manager.show_setup_instructions = False
            self.draw_board()
            return True
        
            
        # Special handling for 'y' key in setup phase - check if confirmation is needed
        # This resolves the conflict with 'y' for diagonal movement in setup phase
        if self.game.setup_phase and key == ord('y'):
            # If all units are placed, interpret 'y' as confirm
            if self.mode_manager.check_confirmation_needed():
                self.mode_manager.handle_confirm()
                self.draw_board()  # Always draw after handling input
                return True
            # Otherwise, let it pass through as movement
            
        # Check if action menu wants to handle direct key presses first (for m/a/s keys)
        # But this won't block other inputs like movement keys
        if self.action_menu_component.visible:
            handled = self.action_menu_component.handle_input(key)
            if handled:
                self.draw_board()  # Always draw after handling input
                return True
            # If not handled, continue with normal input processing
        
        # Check if message log component wants to handle the input
        if self.message_log_component.handle_input(key):
            self.draw_board()  # Always draw after handling input
            return True
            
        # Check if chat component is in chat mode
        if self.chat_component.chat_mode:
            result = self.chat_component.handle_chat_input(key)
            self.draw_board()  # Always draw after handling input
            return result
        
        # Delegate input handling to the input manager
        try:
            result = self.input_manager.process_input(key)
            self.draw_board()  # Always draw after handling input
            return result
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl+C
            return False